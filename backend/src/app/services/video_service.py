"""
Video upload and processing service.

Handles:
- Pre-recorded video uploads for professional profiles
- Video validation and processing
- Storage management (local or S3/R2)
"""
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from fastapi import UploadFile, HTTPException

from src.app.config import settings
from src.app.services.storage import get_storage, StorageBackend, LocalStorageBackend

logger = logging.getLogger(__name__)


class VideoService:
    """
    Service for handling video uploads and storage.

    Supports local storage for development and S3/R2 for production.
    """

    ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov"}
    ALLOWED_CONTENT_TYPES = {
        "video/mp4",
        "video/webm",
        "video/quicktime",
    }
    MAX_FILE_SIZE = settings.video_max_size_mb * 1024 * 1024
    MAX_DURATION_SECONDS = settings.video_max_duration_seconds

    def __init__(self, storage: StorageBackend = None):
        self.storage = storage or get_storage()

    def _generate_key(self, professional_id: str, extension: str) -> str:
        """Generate a unique storage key for the video."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"videos/{professional_id}/{timestamp}_{unique_id}{extension}"

    def _validate_file(self, file: UploadFile) -> Tuple[bool, str]:
        """
        Validate the uploaded file.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file.filename:
            return False, "No filename provided"

        # Check extension
        extension = Path(file.filename).suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"

        # Check content type
        if file.content_type and file.content_type not in self.ALLOWED_CONTENT_TYPES:
            return False, f"Invalid content type: {file.content_type}"

        return True, ""

    def _get_content_type(self, extension: str) -> str:
        """Get the MIME type for a file extension."""
        content_types = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mov": "video/quicktime",
        }
        return content_types.get(extension, "video/mp4")

    async def upload_prerecorded_video(
        self,
        file: UploadFile,
        professional_id: str,
        delete_previous: bool = True,
    ) -> str:
        """
        Upload a pre-recorded video for a professional.

        Args:
            file: The uploaded video file
            professional_id: UUID of the professional
            delete_previous: Whether to delete previous videos

        Returns:
            URL to access the video

        Raises:
            HTTPException: If validation fails or upload errors
        """
        # Validate file
        is_valid, error = self._validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        # Read file content
        content = await file.read()

        # Check file size
        if len(content) > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Generate storage key
        extension = Path(file.filename).suffix.lower()
        key = self._generate_key(professional_id, extension)
        content_type = self._get_content_type(extension)

        try:
            # Upload to storage
            url = await self.storage.upload(
                file_data=content,
                key=key,
                content_type=content_type,
            )

            logger.info(f"Uploaded video for professional {professional_id}: {key}")

            return url

        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save video: {str(e)}"
            )

    async def delete_video(self, url_or_key: str) -> bool:
        """
        Delete a video from storage.

        Args:
            url_or_key: The URL or storage key of the video

        Returns:
            True if deleted successfully
        """
        # Extract key from URL if needed
        key = url_or_key
        if url_or_key.startswith("http"):
            # Extract key from URL
            # This handles both S3 URLs and local URLs
            if "/videos/" in url_or_key:
                key = "videos/" + url_or_key.split("/videos/", 1)[1]

        return await self.storage.delete(key)

    async def video_exists(self, url_or_key: str) -> bool:
        """Check if a video exists in storage."""
        key = url_or_key
        if url_or_key.startswith("http"):
            if "/videos/" in url_or_key:
                key = "videos/" + url_or_key.split("/videos/", 1)[1]

        return await self.storage.exists(key)

    def get_local_path(self, key: str) -> Optional[Path]:
        """
        Get the local filesystem path for a video.

        Only works with LocalStorageBackend.
        """
        if isinstance(self.storage, LocalStorageBackend):
            return self.storage.get_local_path(key)
        return None

    def get_video_path(self, professional_id: str, filename: str) -> Optional[Path]:
        """
        Get the filesystem path for a specific video.

        Args:
            professional_id: UUID of the professional
            filename: Name of the video file

        Returns:
            Path to the video file if it exists, None otherwise
        """
        key = f"videos/{professional_id}/{filename}"
        local_path = self.get_local_path(key)

        if local_path and local_path.exists():
            return local_path

        return None

    async def delete_video_by_parts(self, professional_id: str, filename: str) -> bool:
        """
        Delete a video by professional ID and filename.

        Args:
            professional_id: UUID of the professional
            filename: Name of the video file

        Returns:
            True if deleted successfully
        """
        key = f"videos/{professional_id}/{filename}"
        return await self.storage.delete(key)


# Singleton instance
_video_service: Optional[VideoService] = None


def get_video_service() -> VideoService:
    """Get the video service singleton."""
    global _video_service
    if _video_service is None:
        _video_service = VideoService()
    return _video_service
