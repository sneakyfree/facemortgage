import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.app.core.database import Base


class CallStatus(str, Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    CONNECTED = "connected"
    COMPLETED = "completed"
    MISSED = "missed"
    DECLINED = "declined"
    FAILED = "failed"


class VideoCall(Base):
    __tablename__ = "video_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Participants
    borrower_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=False
    )

    # Call Timing
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    ring_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Metrics
    pickup_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[CallStatus] = mapped_column(
        SQLEnum(CallStatus), default=CallStatus.INITIATED
    )
    end_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Technical
    borrower_camera_on: Mapped[bool] = mapped_column(Boolean, default=False)
    professional_camera_on: Mapped[bool] = mapped_column(Boolean, default=True)
    recording_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ice_servers_used: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Quality Metrics
    quality_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Anonymous caller support
    anonymous_session_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    anonymous_device_fingerprint: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )

    # Post-call lead capture (for anonymous callers)
    captured_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    captured_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    captured_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    lead_captured_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    borrower: Mapped["User"] = relationship("User", foreign_keys=[borrower_id])
    professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile")
    review: Mapped["Review"] = relationship("Review", back_populates="video_call", uselist=False)


# Import for type hints
from src.app.models.user import User
from src.app.models.professional import ProfessionalProfile
from src.app.models.review import Review
