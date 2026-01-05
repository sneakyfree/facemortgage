import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base


class BorrowerProfile(Base):
    __tablename__ = "borrower_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Preferences (for matching)
    # Using JSON instead of JSONB for SQLite test compatibility
    preferred_languages: Mapped[list | None] = mapped_column(JSON, default=["en"])
    preferred_counties: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Loan interest
    loan_purpose: Mapped[str | None] = mapped_column(String(50), nullable=True)  # purchase, refinance, heloc
    property_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_credit_score: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Contact preferences
    contact_preference: Mapped[str] = mapped_column(String(20), default="any")  # video, phone, chat, any

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="borrower_profile")


# Import for type hints
from src.app.models.user import User
