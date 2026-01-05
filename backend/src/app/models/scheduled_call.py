"""
Scheduled call model for the "Schedule a Call" feature.

Allows borrowers to schedule video calls with professionals for a future time
instead of calling immediately.
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base


class ScheduledCallStatus(str, Enum):
    PENDING = "pending"       # Scheduled but not confirmed
    CONFIRMED = "confirmed"   # Both parties confirmed
    COMPLETED = "completed"   # Call happened
    CANCELLED = "cancelled"   # Cancelled by either party
    NO_SHOW = "no_show"       # Neither party showed up


class ScheduledCall(Base):
    """Represents a scheduled video call between a borrower and professional."""
    __tablename__ = "scheduled_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Who scheduled (optional - can be anonymous)
    borrower_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Contact info (required even for authenticated users for reminders)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Who they want to meet
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=False
    )

    # When
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(50), default="America/New_York")

    # Status
    status: Mapped[ScheduledCallStatus] = mapped_column(
        SQLEnum(ScheduledCallStatus), default=ScheduledCallStatus.PENDING
    )

    # Optional details
    loan_purpose: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tracking
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("video_calls.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    borrower: Mapped["User"] = relationship("User", foreign_keys=[borrower_id])
    professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile")
    completed_call: Mapped["VideoCall"] = relationship("VideoCall")


# Imports for type hints
from src.app.models.user import User
from src.app.models.professional import ProfessionalProfile
from src.app.models.call import VideoCall
