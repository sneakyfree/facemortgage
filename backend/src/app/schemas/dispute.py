"""
Pydantic schemas for dispute resolution.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from src.app.models.dispute import DisputeType, DisputeStatus, DisputePriority


class CreateDisputeRequest(BaseModel):
    """Create a new dispute."""
    dispute_type: DisputeType
    subject: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=5000)
    related_transaction_id: Optional[str] = None


class AddMessageRequest(BaseModel):
    """Add a message to a dispute thread."""
    message: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = False  # Only admins can set this to True


class ResolveDisputeRequest(BaseModel):
    """Resolve a dispute."""
    resolution_notes: str = Field(..., min_length=10, max_length=2000)


class UpdateDisputeRequest(BaseModel):
    """Update dispute properties (admin only)."""
    status: Optional[DisputeStatus] = None
    priority: Optional[DisputePriority] = None
    assigned_to: Optional[UUID] = None


class DisputeMessageResponse(BaseModel):
    """Dispute message response."""
    id: UUID
    dispute_id: UUID
    sender_id: UUID
    sender_name: Optional[str] = None
    message: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DisputeResponse(BaseModel):
    """Dispute response."""
    id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    dispute_type: DisputeType
    subject: str
    description: str
    status: DisputeStatus
    priority: DisputePriority
    related_transaction_id: Optional[str] = None
    assigned_to: Optional[UUID] = None
    assignee_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    messages: List[DisputeMessageResponse] = []

    class Config:
        from_attributes = True


class DisputeListResponse(BaseModel):
    """Paginated dispute list."""
    items: List[DisputeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DisputeStatsResponse(BaseModel):
    """Dispute statistics for admin dashboard."""
    open_count: int
    in_progress_count: int
    resolved_today: int
    avg_resolution_time_hours: float
