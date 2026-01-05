"""
Video upload and serving routes.

Handles pre-recorded video uploads for professional profiles.
"""
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from src.app.core.dependencies import DbSession, CurrentProfessional
from src.app.models.professional import ProfessionalProfile
from src.app.services.video_service import get_video_service

router = APIRouter()


@router.post("/me/prerecorded")
async def upload_prerecorded_video(
    current_user: CurrentProfessional,
    db: DbSession,
    file: UploadFile = File(..., description="Video file (MP4, WebM, or MOV)"),
):
    """
    Upload a pre-recorded video for the authenticated professional.

    This video will be shown on the grid when the professional is:
    - Busy with another call
    - Set to away status

    Maximum file size: 100MB
    Maximum duration: 60 seconds
    Allowed formats: MP4, WebM, MOV
    """
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found",
        )

    # Upload video
    video_service = get_video_service()
    video_url = await video_service.upload_prerecorded_video(
        file=file,
        professional_id=str(professional.id),
    )

    # Update professional profile with video URL
    professional.prerecorded_video_url = video_url
    await db.commit()

    return {
        "message": "Video uploaded successfully",
        "video_url": video_url,
    }


@router.delete("/me/prerecorded")
async def delete_prerecorded_video(
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Delete the pre-recorded video for the authenticated professional.
    """
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found",
        )

    if not professional.prerecorded_video_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pre-recorded video found",
        )

    # Delete the video from storage
    video_service = get_video_service()
    await video_service.delete_video(professional.prerecorded_video_url)

    # Clear URL from profile
    professional.prerecorded_video_url = None
    await db.commit()

    return {"message": "Video deleted successfully"}


@router.get("/{professional_id}/{filename}")
async def get_video(
    professional_id: str,
    filename: str,
):
    """
    Serve a video file.

    This endpoint serves pre-recorded videos for display on the grid.
    In production, this would typically be handled by a CDN or S3.
    """
    video_service = get_video_service()
    file_path = video_service.get_video_path(professional_id, filename)

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Determine media type
    extension = file_path.suffix.lower()
    media_types = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
    }
    media_type = media_types.get(extension, "video/mp4")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )
