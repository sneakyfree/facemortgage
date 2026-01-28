import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base


class ProfessionalStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE_AVAILABLE = "online_available"
    ONLINE_BUSY = "online_busy"
    IN_CALL = "in_call"
    AWAY = "away"


class SubscriptionTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"


class ProfessionalProfile(Base):
    __tablename__ = "professional_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Professional Details
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # NMLS (for loan officers)
    nmls_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    nmls_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    nmls_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Location
    # Using JSON instead of JSONB for SQLite test compatibility
    office_address: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="America/New_York")

    # Video Settings
    prerecorded_video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webcam_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Status & Availability
    status: Mapped[ProfessionalStatus] = mapped_column(
        SQLEnum(ProfessionalStatus), default=ProfessionalStatus.OFFLINE
    )
    status_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Stripe Customer
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Grid Positioning Factors
    current_bid_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    daily_bid_budget: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE
    )
    time_online_today_seconds: Mapped[int] = mapped_column(Integer, default=0)
    total_calls_completed: Mapped[int] = mapped_column(Integer, default=0)

    # Metrics
    avg_pickup_time_seconds: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0.00)

    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="professional_profile")
    specialties: Mapped[List["ProfessionalSpecialty"]] = relationship(
        "ProfessionalSpecialty", back_populates="professional", cascade="all, delete-orphan"
    )
    languages: Mapped[List["ProfessionalLanguage"]] = relationship(
        "ProfessionalLanguage", back_populates="professional", cascade="all, delete-orphan"
    )
    service_areas: Mapped[List["ProfessionalServiceArea"]] = relationship(
        "ProfessionalServiceArea", back_populates="professional", cascade="all, delete-orphan"
    )

    # Partnership relationships
    lo_partnerships: Mapped[List["Partnership"]] = relationship(
        "Partnership",
        foreign_keys="[Partnership.loan_officer_id]",
        back_populates="loan_officer",
    )
    realtor_partnerships: Mapped[List["Partnership"]] = relationship(
        "Partnership",
        foreign_keys="[Partnership.realtor_id]",
        back_populates="realtor",
    )

    # Video moderation records
    video_moderations: Mapped[List["VideoModeration"]] = relationship(
        "VideoModeration",
        back_populates="professional",
        order_by="desc(VideoModeration.created_at)",
        cascade="all, delete-orphan",
    )


class Specialty(Base):
    __tablename__ = "specialties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # loan_type, property_type, client_type
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)  # 'en', 'es', 'zh', etc.
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class County(Base):
    __tablename__ = "counties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    county_name: Mapped[str] = mapped_column(String(100), nullable=False)
    fips_code: Mapped[str | None] = mapped_column(String(5), nullable=True)


class ProfessionalSpecialty(Base):
    __tablename__ = "professional_specialties"

    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), primary_key=True
    )
    specialty_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("specialties.id", ondelete="CASCADE"), primary_key=True
    )

    professional: Mapped["ProfessionalProfile"] = relationship(
        "ProfessionalProfile", back_populates="specialties"
    )
    specialty: Mapped["Specialty"] = relationship("Specialty")


class ProfessionalLanguage(Base):
    __tablename__ = "professional_languages"

    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), primary_key=True
    )
    language_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("languages.id", ondelete="CASCADE"), primary_key=True
    )
    proficiency: Mapped[str] = mapped_column(String(20), default="fluent")  # native, fluent, conversational

    professional: Mapped["ProfessionalProfile"] = relationship(
        "ProfessionalProfile", back_populates="languages"
    )
    language: Mapped["Language"] = relationship("Language")


class ProfessionalServiceArea(Base):
    __tablename__ = "professional_service_areas"

    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), primary_key=True
    )
    county_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("counties.id", ondelete="CASCADE"), primary_key=True
    )

    professional: Mapped["ProfessionalProfile"] = relationship(
        "ProfessionalProfile", back_populates="service_areas"
    )
    county: Mapped["County"] = relationship("County")


# Import for type hints
from src.app.models.user import User
from src.app.models.partnership import Partnership
from src.app.models.moderation import VideoModeration
