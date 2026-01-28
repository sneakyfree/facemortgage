"""
Video thumbnail API endpoints.

Provides endpoints for generating and retrieving video thumbnails.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from src.app.core.auth import get_current_user
from src.app.services.thumbnail_service import thumbnail_service
from src.app.models.user import User

router = APIRouter(prefix="/thumbnails", tags=["thumbnails"])


class ThumbnailRequest(BaseModel):
    """Request to generate a thumbnail."""
    video_path: str
    timestamp: Optional[str] = None


class ThumbnailResponse(BaseModel):
    """Response with thumbnail information."""
    thumbnail_url: str
    video_path: str


class VideoMetadataResponse(BaseModel):
    """Response with video metadata."""
    duration_seconds: Optional[float]
    width: Optional[int]
    height: Optional[int]


@router.post("/generate", response_model=ThumbnailResponse)
async def generate_thumbnail(
    request: ThumbnailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a thumbnail for a video.

    The thumbnail is generated asynchronously. Returns the URL where
    the thumbnail will be available once generated.
    """
    # Validate video path exists
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    # Generate thumbnail
    thumbnail_path = await thumbnail_service.generate_thumbnail(
        video_path=request.video_path,
        timestamp=request.timestamp,
    )

    if not thumbnail_path:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate thumbnail. Ensure FFmpeg is installed."
        )

    # Convert path to URL
    thumbnail_url = f"/static/thumbnails/{os.path.basename(thumbnail_path)}"

    return ThumbnailResponse(
        thumbnail_url=thumbnail_url,
        video_path=request.video_path,
    )


@router.post("/preview/generate")
async def generate_preview_gif(
    request: ThumbnailRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate an animated GIF preview for a video.

    Returns the URL where the GIF will be available.
    """
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    preview_path = await thumbnail_service.generate_video_preview(
        video_path=request.video_path,
        duration=5,
        fps=10,
    )

    if not preview_path:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate preview GIF"
        )

    preview_url = f"/static/thumbnails/{os.path.basename(preview_path)}"

    return {"preview_url": preview_url}


@router.get("/metadata")
async def get_video_metadata(
    video_path: str,
    current_user: User = Depends(get_current_user),
) -> VideoMetadataResponse:
    """
    Get metadata for a video file.

    Returns duration and resolution information.
    """
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    duration = await thumbnail_service.get_video_duration(video_path)
    resolution = await thumbnail_service.get_video_resolution(video_path)

    return VideoMetadataResponse(
        duration_seconds=duration,
        width=resolution[0] if resolution else None,
        height=resolution[1] if resolution else None,
    )


@router.get("/{filename}")
async def get_thumbnail(filename: str):
    """
    Retrieve a generated thumbnail file.
    """
    thumbnail_path = thumbnail_service.thumbnail_dir / filename

    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(
        path=str(thumbnail_path),
        media_type="image/jpeg" if filename.endswith(".jpg") else "image/gif",
    )
