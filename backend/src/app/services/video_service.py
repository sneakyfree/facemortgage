"""
Video upload and processing service.

Handles:
- Pre-recorded video uploads for professional profiles
- Video validation and processing
- Storage management (local or S3/R2)

Security features:
- Magic bytes validation (file signature verification)
- Filename sanitization (prevent path traversal)
- Extension and MIME type validation
"""
import uuid
import logging
import re
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from fastapi import UploadFile, HTTPException

from src.app.config import settings
from src.app.services.storage import get_storage, StorageBackend, LocalStorageBackend

logger = logging.getLogger(__name__)

# Filename sanitization pattern - only allow alphanumeric, dash, underscore, dot
SAFE_FILENAME_PATTERN = re.compile(r'^[\w\-\.]+$')


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

    # Magic bytes (file signatures) for video formats
    # These are the first bytes of valid video files
    MAGIC_BYTES = {
        # MP4/MOV containers (ftyp box)
        b'\x00\x00\x00': "video/mp4",  # MP4 (variable offset for ftyp)
        b'ftyp': "video/mp4",  # MP4/MOV ftyp marker
        # WebM (EBML header)
        b'\x1a\x45\xdf\xa3': "video/webm",
    }

    # Extended signatures for MP4/MOV detection
    MP4_FTYP_BRANDS = {
        b'isom', b'iso2', b'mp41', b'mp42',  # MP4
        b'qt  ', b'mqt ',  # QuickTime/MOV
        b'M4V ', b'M4A ',  # Apple variants
        b'avc1', b'hvc1',  # AVC/HEVC
    }

    def __init__(self, storage: StorageBackend = None):
        self.storage = storage or get_storage()

    def _generate_key(self, professional_id: str, extension: str) -> str:
        """Generate a unique storage key for the video."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"videos/{professional_id}/{timestamp}_{unique_id}{extension}"

    def _validate_magic_bytes(self, content: bytes) -> Tuple[bool, str]:
        """
        Validate file content using magic bytes (file signature).

        This prevents attackers from uploading malicious files with
        renamed extensions (e.g., uploading a PHP file as .mp4).

        Args:
            content: First portion of file content (at least 32 bytes)

        Returns:
            Tuple of (is_valid, detected_mime_type)
        """
        if len(content) < 12:
            return False, ""

        # Check for WebM (EBML header)
        if content[:4] == b'\x1a\x45\xdf\xa3':
            return True, "video/webm"

        # Check for MP4/MOV (ftyp box)
        # Structure: [4 bytes size][4 bytes 'ftyp'][4 bytes brand]
        # ftyp can start at offset 0, 4, or 8 depending on the file
        for offset in [0, 4, 8]:
            if len(content) > offset + 8:
                if content[offset:offset + 4] == b'ftyp' or content[offset + 4:offset + 8] == b'ftyp':
                    # Check brand at appropriate offset
                    brand_offset = offset + 8 if content[offset + 4:offset + 8] == b'ftyp' else offset + 4
                    if len(content) > brand_offset + 4:
                        brand = content[brand_offset:brand_offset + 4]
                        if brand in self.MP4_FTYP_BRANDS:
                            # QuickTime brand indicates MOV
                            if brand in {b'qt  ', b'mqt '}:
                                return True, "video/quicktime"
                            return True, "video/mp4"
                        # Accept unknown brands that still have valid ftyp structure
                        return True, "video/mp4"

        return False, ""

    def _validate_file(self, file: UploadFile, content: bytes = None) -> Tuple[bool, str]:
        """
        Validate the uploaded file with comprehensive security checks.

        Security checks performed:
        1. Filename presence and sanitization
        2. Null byte detection (path injection prevention)
        3. Path traversal prevention
        4. Extension validation
        5. Content-Type header validation
        6. Magic bytes validation (if content provided)

        Args:
            file: The uploaded file object
            content: Optional file content for magic bytes validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file.filename:
            return False, "No filename provided"

        # Security: Check for null bytes (path injection attack)
        if '\x00' in file.filename:
            logger.warning(f"Null byte detected in filename: {repr(file.filename)}")
            return False, "Invalid filename"

        # Security: Sanitize filename (prevent path traversal)
        # Extract just the filename, not any path components
        safe_name = Path(file.filename).name
        if not SAFE_FILENAME_PATTERN.match(safe_name):
            logger.warning(f"Unsafe filename rejected: {repr(file.filename)}")
            return False, "Filename contains invalid characters"

        # Security: Check for path traversal attempts
        if '..' in file.filename or file.filename.startswith('/'):
            logger.warning(f"Path traversal attempt detected: {repr(file.filename)}")
            return False, "Invalid filename"

        # Check extension
        extension = Path(file.filename).suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"

        # Check content type header
        if file.content_type and file.content_type not in self.ALLOWED_CONTENT_TYPES:
            return False, f"Invalid content type: {file.content_type}"

        # Security: Validate magic bytes if content is provided
        if content is not None:
            is_valid_magic, detected_type = self._validate_magic_bytes(content[:64])
            if not is_valid_magic:
                logger.warning(
                    f"Magic bytes validation failed for {file.filename}. "
                    f"Claimed type: {file.content_type}"
                )
                return False, "File content does not match a valid video format"

            # Verify detected type matches claimed type
            if file.content_type and detected_type:
                # Allow mp4/quicktime to be somewhat interchangeable
                compatible_types = {
                    "video/mp4": {"video/mp4", "video/quicktime"},
                    "video/quicktime": {"video/mp4", "video/quicktime"},
                    "video/webm": {"video/webm"},
                }
                allowed = compatible_types.get(detected_type, {detected_type})
                if file.content_type not in allowed:
                    logger.warning(
                        f"Content type mismatch for {file.filename}. "
                        f"Claimed: {file.content_type}, Detected: {detected_type}"
                    )
                    return False, "File content does not match claimed type"

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
        # Initial validation (filename, extension, content-type header)
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

        # Full validation including magic bytes check
        is_valid, error = self._validate_file(file, content=content)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

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
