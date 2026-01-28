"""
Pydantic schemas for video moderation.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from src.app.models.moderation import ModerationStatus


class VideoModerationCreate(BaseModel):
    """Create a new moderation record (internal use only)."""
    professional_id: UUID
    video_url: str


class VideoModerationResponse(BaseModel):
    """Video moderation record response."""
    id: UUID
    professional_id: UUID
    video_url: str
    status: ModerationStatus
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Professional info for admin display
    professional_name: Optional[str] = None
    professional_email: Optional[str] = None

    class Config:
        from_attributes = True


class ApproveVideoRequest(BaseModel):
    """Empty request body for video approval."""
    pass


class RejectVideoRequest(BaseModel):
    """Request body for video rejection."""
    reason: str = Field(
        ..., 
        min_length=10, 
        max_length=500, 
        description="Rejection reason must be 10-500 characters"
    )


class ModerationListResponse(BaseModel):
    """Paginated list of moderation records."""
    items: List[VideoModerationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ModerationStatsResponse(BaseModel):
    """Moderation queue statistics."""
    pending_count: int
    approved_today: int
    rejected_today: int
    avg_review_time_hours: float
