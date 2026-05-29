"""Video Moderation model for content review.

This module defines the data model for video content moderation,
enabling admins to review, approve, or reject professional video content.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base

if TYPE_CHECKING:
    from src.app.models.professional import ProfessionalProfile
    from src.app.models.user import User


class ModerationStatus(str, Enum):
    """Status of a video moderation request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class VideoModeration(Base):
    """
    Video moderation record for content review.
    
    When professionals upload intro videos, a moderation record is created
    in PENDING status. Admins can then approve or reject the video.
    Only approved videos appear in the public grid.
    """
    __tablename__ = "video_moderations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("professional_profiles.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ModerationStatus] = mapped_column(
        SQLEnum(ModerationStatus), 
        nullable=False, 
        default=ModerationStatus.PENDING,
        index=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id"), 
        nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    professional: Mapped["ProfessionalProfile"] = relationship(
        "ProfessionalProfile", back_populates="video_moderations"
    )
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by])
