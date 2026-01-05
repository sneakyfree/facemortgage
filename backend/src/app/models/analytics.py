"""
Analytics models for tracking grid impressions and user interactions.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.app.core.database import Base


class GridImpression(Base):
    """
    Tracks when a professional's card is viewed in the grid.

    Aggregated daily to reduce storage while maintaining useful metrics.
    """
    __tablename__ = "grid_impressions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Aggregation date
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Metrics
    impressions_count: Mapped[int] = mapped_column(Integer, default=0)
    clicks_count: Mapped[int] = mapped_column(Integer, default=0)
    calls_initiated: Mapped[int] = mapped_column(Integer, default=0)

    # Average position when shown (for bid optimization)
    avg_position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Composite index for efficient querying
    __table_args__ = (
        Index("ix_grid_impressions_pro_date", "professional_id", "date", unique=True),
        Index("ix_grid_impressions_date", "date"),
    )

    # Relationships
    professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile")


class GridClick(Base):
    """
    Tracks individual clicks on professional cards.

    More granular than impressions for detailed analytics.
    """
    __tablename__ = "grid_clicks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False
    )
    borrower_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Session tracking (for attribution)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Click context
    click_type: Mapped[str] = mapped_column(String(30), nullable=False)  # 'profile_view', 'call_initiated', 'video_preview'
    grid_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filter_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # What filters were active

    # Request metadata
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 compatible

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_grid_clicks_pro_created", "professional_id", "created_at"),
        Index("ix_grid_clicks_click_type", "click_type"),
    )


# Import for type hints
from src.app.models.professional import ProfessionalProfile
