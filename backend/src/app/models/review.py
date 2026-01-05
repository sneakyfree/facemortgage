import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, SmallInteger, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    video_call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("video_calls.id"), nullable=True
    )

    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reviewed_professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=False
    )

    # Ratings (1-5)
    overall_rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    knowledge_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    communication_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    responsiveness_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # Written Review
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Moderation
    is_verified_call: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_status: Mapped[str] = mapped_column(String(20), default="approved")  # pending, approved, rejected

    # Response
    professional_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    professional_responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    helpful_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint('overall_rating >= 1 AND overall_rating <= 5', name='check_overall_rating'),
        CheckConstraint('knowledge_rating IS NULL OR (knowledge_rating >= 1 AND knowledge_rating <= 5)', name='check_knowledge_rating'),
        CheckConstraint('communication_rating IS NULL OR (communication_rating >= 1 AND communication_rating <= 5)', name='check_communication_rating'),
        CheckConstraint('responsiveness_rating IS NULL OR (responsiveness_rating >= 1 AND responsiveness_rating <= 5)', name='check_responsiveness_rating'),
    )

    # Relationships
    video_call: Mapped["VideoCall"] = relationship("VideoCall", back_populates="review")
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewer_id])
    reviewed_professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile")


# Import for type hints
from src.app.models.call import VideoCall
from src.app.models.user import User
from src.app.models.professional import ProfessionalProfile
