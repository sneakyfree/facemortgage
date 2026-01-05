"""
Soft lead model for the "Get Matched" feature.

Captures borrowers who are not ready to call immediately but want to be
matched with a professional for follow-up.
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base


class SoftLeadStatus(str, Enum):
    NEW = "new"              # Just submitted, awaiting matching
    MATCHED = "matched"      # Matched to a professional
    CONTACTED = "contacted"  # Professional made contact
    CONVERTED = "converted"  # Became a real lead/call
    EXPIRED = "expired"      # No action within 30 days


class SoftLead(Base):
    """
    Represents a 'Get Matched' request from a borrower.

    These are borrowers who aren't ready to call immediately but want
    to be connected with a professional. Auto-matched based on preferences.
    """
    __tablename__ = "soft_leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Contact info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # What they're looking for
    loan_purpose: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    property_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    property_county: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    timeframe: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Preferences
    preferred_professional_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_specialty: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[SoftLeadStatus] = mapped_column(
        SQLEnum(SoftLeadStatus), default=SoftLeadStatus.NEW
    )

    # Matching
    matched_professional_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=True
    )
    matched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Conversion tracking
    converted_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True
    )

    # UTM tracking
    utm_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(100), nullable=True)
    referrer_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    matched_professional: Mapped["ProfessionalProfile"] = relationship(
        "ProfessionalProfile"
    )
    converted_lead: Mapped["Lead"] = relationship("Lead")


# Imports for type hints
from src.app.models.professional import ProfessionalProfile
from src.app.models.lead import Lead
