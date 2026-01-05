import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Numeric, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.core.database import Base
from src.app.models.professional import SubscriptionTier


class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    TRIALING = "trialing"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)

    # Pricing
    monthly_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    annual_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Features
    max_daily_leads: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grid_priority_boost: Mapped[int] = mapped_column(Integer, default=0)
    analytics_access_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    video_recording_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_branding_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Using JSON instead of JSONB for SQLite test compatibility
    features: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    stripe_price_id_monthly: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stripe_price_id_annual: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=False
    )
    plan_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("subscription_plans.id"), nullable=True
    )

    # Tier
    tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE
    )

    # Stripe Integration
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), default=SubscriptionStatus.PENDING
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)

    # Dates
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Payment Method (cached)
    card_brand: Mapped[str | None] = mapped_column(String(20), nullable=True)
    card_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    card_expiry_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    card_expiry_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile")
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")


class BidWallet(Base):
    __tablename__ = "bid_wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=False, unique=True
    )

    available_credits: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    reserved_credits: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # For active bids
    total_deposited: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile")
    transactions: Mapped[list["BidTransaction"]] = relationship("BidTransaction", back_populates="wallet")


class BidTransaction(Base):
    """Individual transactions for bid wallet."""
    __tablename__ = "bid_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bid_wallets.id"), nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)  # deposit, charge, refund
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reference
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    related_call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    wallet: Mapped["BidWallet"] = relationship("BidWallet", back_populates="transactions")


class PlacementBid(Base):
    __tablename__ = "placement_bids"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=False
    )

    # Bid Configuration
    daily_budget: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bid_per_impression: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    bid_per_click: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)

    # Targeting
    # Using JSON instead of ARRAY for SQLite test compatibility
    target_counties: Mapped[list | None] = mapped_column(JSON, nullable=True)
    target_languages: Mapped[list | None] = mapped_column(JSON, nullable=True)
    target_specialties: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Using JSON instead of JSONB for SQLite test compatibility
    target_hours: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Budget Tracking
    daily_spent: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile")


class BillingTransaction(Base):
    __tablename__ = "billing_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id"), nullable=False
    )

    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)  # subscription, bid_charge, refund
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Reference
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stripe_invoice_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Using JSON instead of JSONB for SQLite test compatibility
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile")


# Import for type hints
from src.app.models.professional import ProfessionalProfile
