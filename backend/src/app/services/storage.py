"""
Cloud storage abstraction layer.

Supports:
- Local filesystem storage (development)
- AWS S3 (production)
- Cloudflare R2 (S3-compatible, production alternative)
"""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src.app.config import settings

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def upload(
        self,
        file_data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload a file to storage.

        Args:
            file_data: The file content as bytes
            key: The storage key (path/filename)
            content_type: MIME type of the file

        Returns:
            Public URL to access the file
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a file from storage.

        Args:
            key: The storage key

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        pass

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Get the public URL for a file."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage for development."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.video_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        file_data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Save file to local filesystem."""
        file_path = self.base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(file_data)

        return self.get_url(key)

    async def delete(self, key: str) -> bool:
        """Delete file from local filesystem."""
        file_path = self.base_path / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if file exists locally."""
        file_path = self.base_path / key
        return file_path.exists()

    def get_url(self, key: str) -> str:
        """Get local URL for file."""
        return f"/api/v1/videos/{key}"

    def get_local_path(self, key: str) -> Optional[Path]:
        """Get the local filesystem path for a file."""
        file_path = self.base_path / key
        if file_path.exists():
            return file_path
        return None


class S3StorageBackend(StorageBackend):
    """AWS S3 or S3-compatible storage (e.g., Cloudflare R2)."""

    def __init__(self):
        try:
            import aioboto3
            self._aioboto3 = aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 is required for S3 storage. "
                "Install it with: pip install aioboto3"
            )

        self.bucket_name = settings.s3_bucket_name
        self.region = settings.aws_region
        self.endpoint_url = settings.s3_endpoint_url
        self.public_url_base = settings.s3_public_url_base

        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME must be set for S3 storage")

        # Session configuration
        self.session_config = {
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
            "region_name": self.region,
        }
        if self.endpoint_url:
            self.session_config["endpoint_url"] = self.endpoint_url

    def _get_session(self):
        """Get an aioboto3 session."""
        return self._aioboto3.Session()

    async def upload(
        self,
        file_data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload file to S3."""
        session = self._get_session()

        async with session.client("s3", **self.session_config) as s3:
            await s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                # Make publicly readable
                ACL="public-read",
            )

        logger.info(f"Uploaded {key} to S3 bucket {self.bucket_name}")
        return self.get_url(key)

    async def delete(self, key: str) -> bool:
        """Delete file from S3."""
        session = self._get_session()

        try:
            async with session.client("s3", **self.session_config) as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Deleted {key} from S3 bucket {self.bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {key} from S3: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if file exists in S3."""
        session = self._get_session()

        try:
            async with session.client("s3", **self.session_config) as s3:
                await s3.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

    def get_url(self, key: str) -> str:
        """Get public URL for S3 file."""
        if self.public_url_base:
            # Use custom CDN or public URL
            return f"{self.public_url_base.rstrip('/')}/{key}"

        if self.endpoint_url:
            # S3-compatible endpoint (like R2)
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{key}"

        # Standard S3 URL
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """Generate a presigned URL for temporary access."""
        session = self._get_session()

        async with session.client("s3", **self.session_config) as s3:
            url = await s3.generate_presigned_url(
                "get_object" if http_method == "GET" else "put_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
        return url


def get_storage_backend() -> StorageBackend:
    """
    Get the configured storage backend.

    Returns LocalStorageBackend for development,
    S3StorageBackend for production.
    """
    backend = settings.storage_backend.lower()

    if backend in ("s3", "r2"):
        return S3StorageBackend()
    else:
        return LocalStorageBackend()


# Singleton instance
_storage_backend: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """Get the storage backend singleton."""
    global _storage_backend
    if _storage_backend is None:
        _storage_backend = get_storage_backend()
    return _storage_backend
