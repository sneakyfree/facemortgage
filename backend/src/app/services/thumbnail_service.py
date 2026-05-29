"""
Video thumbnail generation service using FFmpeg.

This service extracts thumbnails from uploaded videos for preview purposes.
Requires FFmpeg to be installed on the system.
"""

import asyncio
import os
import shutil
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ThumbnailService:
    """Service for generating video thumbnails using FFmpeg."""

    def __init__(
        self,
        thumbnail_dir: str | None = None,
        default_timestamp: str = "00:00:02",
        thumbnail_width: int = 640,
    ):
        # Use env var, then explicit param, then safe fallback
        if thumbnail_dir is None:
            thumbnail_dir = os.environ.get("THUMBNAIL_DIR", "/tmp/thumbnails")
        self.thumbnail_dir = Path(thumbnail_dir)
        self.default_timestamp = default_timestamp
        self.thumbnail_width = thumbnail_width
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure thumbnail directory exists."""
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        return shutil.which("ffmpeg") is not None

    async def generate_thumbnail(
        self,
        video_path: str,
        output_name: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a thumbnail from a video file.

        Args:
            video_path: Path to the source video file
            output_name: Optional name for the output file (without extension)
            timestamp: Optional timestamp to extract frame from (HH:MM:SS format)

        Returns:
            Path to the generated thumbnail, or None if generation failed
        """
        if not self._check_ffmpeg():
            logger.error("FFmpeg not found. Cannot generate thumbnail.")
            return None

        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None

        # Generate output filename
        if output_name is None:
            video_name = Path(video_path).stem
            output_name = f"{video_name}_thumb"

        output_path = self.thumbnail_dir / f"{output_name}.jpg"
        timestamp = timestamp or self.default_timestamp

        # FFmpeg command to extract a frame
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-ss", timestamp,  # Seek to timestamp
            "-i", video_path,  # Input file
            "-vframes", "1",  # Extract 1 frame
            "-vf", f"scale={self.thumbnail_width}:-1",  # Scale width, maintain aspect
            "-q:v", "2",  # High quality JPEG
            str(output_path),
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                return None

            logger.info(f"Generated thumbnail: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.exception(f"Failed to generate thumbnail: {e}")
            return None

    async def generate_video_preview(
        self,
        video_path: str,
        output_name: Optional[str] = None,
        duration: int = 5,
        fps: int = 10,
    ) -> Optional[str]:
        """
        Generate an animated GIF preview from a video.

        Args:
            video_path: Path to the source video file
            output_name: Optional name for the output file
            duration: Duration of the preview in seconds
            fps: Frames per second for the GIF

        Returns:
            Path to the generated GIF, or None if generation failed
        """
        if not self._check_ffmpeg():
            logger.error("FFmpeg not found. Cannot generate preview.")
            return None

        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None

        if output_name is None:
            video_name = Path(video_path).stem
            output_name = f"{video_name}_preview"

        output_path = self.thumbnail_dir / f"{output_name}.gif"

        # FFmpeg command to create GIF
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", "00:00:00",
            "-t", str(duration),
            "-i", video_path,
            "-vf", f"fps={fps},scale={self.thumbnail_width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", "0",
            str(output_path),
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                return None

            logger.info(f"Generated preview GIF: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.exception(f"Failed to generate preview: {e}")
            return None

    async def get_video_duration(self, video_path: str) -> Optional[float]:
        """
        Get the duration of a video file in seconds.

        Args:
            video_path: Path to the video file

        Returns:
            Duration in seconds, or None if extraction failed
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return None

            return float(stdout.decode().strip())

        except Exception:
            return None

    async def get_video_resolution(self, video_path: str) -> Optional[tuple[int, int]]:
        """
        Get the resolution of a video file.

        Args:
            video_path: Path to the video file

        Returns:
            Tuple of (width, height), or None if extraction failed
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            video_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return None

            parts = stdout.decode().strip().split("x")
            return (int(parts[0]), int(parts[1]))

        except Exception:
            return None


# Singleton instance
thumbnail_service = ThumbnailService()
