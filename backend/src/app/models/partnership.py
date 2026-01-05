"""
Partnership models for the Realtor Partnership Module.

Allows loan officers and realtors to form partnerships for referral tracking
and co-marketing.
"""
import uuid
import secrets
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.app.core.database import Base


class PartnershipStatus(str, Enum):
    PENDING = "pending"       # Invitation sent, awaiting acceptance
    ACTIVE = "active"         # Both parties accepted
    PAUSED = "paused"         # Temporarily disabled
    TERMINATED = "terminated" # Ended by either party


class PartnershipTier(str, Enum):
    BASIC = "basic"         # Simple referral tracking
    SILVER = "silver"       # + Co-marketing materials
    GOLD = "gold"           # + Embeddable widgets
    PLATINUM = "platinum"   # + Revenue sharing


class Partnership(Base):
    """
    Represents a partnership between a loan officer and a realtor.

    The loan officer initiates the partnership by inviting a realtor.
    The realtor can be an existing platform user or external (invited via email).
    """
    __tablename__ = "partnerships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # The loan officer (must be a professional with loan_officer type)
    loan_officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=False, index=True
    )

    # The realtor - can be platform user or external
    realtor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=True
    )

    # For external realtors (not on platform yet)
    external_realtor_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_realtor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_realtor_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    external_realtor_company: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Status
    status: Mapped[PartnershipStatus] = mapped_column(
        SQLEnum(PartnershipStatus), default=PartnershipStatus.PENDING
    )
    tier: Mapped[PartnershipTier] = mapped_column(
        SQLEnum(PartnershipTier), default=PartnershipTier.BASIC
    )

    # Revenue sharing (if applicable)
    revenue_share_percent: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    # Invitation
    invitation_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )
    invited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Widget/embedding
    widget_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    widget_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )
    widget_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    loan_officer: Mapped["ProfessionalProfile"] = relationship(
        "ProfessionalProfile",
        foreign_keys=[loan_officer_id],
        back_populates="lo_partnerships",
    )
    realtor: Mapped["ProfessionalProfile"] = relationship(
        "ProfessionalProfile",
        foreign_keys=[realtor_id],
        back_populates="realtor_partnerships",
    )
    referrals: Mapped[list["PartnershipReferral"]] = relationship(
        "PartnershipReferral",
        back_populates="partnership",
        cascade="all, delete-orphan",
    )

    def generate_invitation_token(self) -> str:
        """Generate a secure invitation token."""
        self.invitation_token = secrets.token_urlsafe(32)
        self.invited_at = datetime.utcnow()
        return self.invitation_token

    def generate_widget_token(self) -> str:
        """Generate a secure widget embed token."""
        self.widget_token = secrets.token_urlsafe(16)
        return self.widget_token


class PartnershipReferral(Base):
    """
    Tracks referrals made through a partnership.

    When a realtor refers a client to their loan officer partner,
    this tracks the referral through the pipeline.
    """
    __tablename__ = "partnership_referrals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    partnership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partnerships.id"), nullable=False, index=True
    )

    # The referred borrower
    borrower_name: Mapped[str] = mapped_column(String(100), nullable=False)
    borrower_email: Mapped[str] = mapped_column(String(255), nullable=False)
    borrower_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Referral details
    property_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    loan_purpose: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_amount: Mapped[int | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), default="new"
    )  # new, contacted, qualified, closed, lost

    # Conversion tracking
    converted_to_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True
    )
    converted_to_call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("video_calls.id"), nullable=True
    )

    # Source
    source: Mapped[str] = mapped_column(
        String(50), default="manual"
    )  # manual, widget, api

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    partnership: Mapped["Partnership"] = relationship(
        "Partnership", back_populates="referrals"
    )
    converted_lead: Mapped["Lead"] = relationship("Lead")
    converted_call: Mapped["VideoCall"] = relationship("VideoCall")


# Imports for type hints
from src.app.models.professional import ProfessionalProfile
from src.app.models.lead import Lead
from src.app.models.call import VideoCall
