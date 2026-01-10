"""
Billing routes for subscriptions and bid wallet management.

Handles:
- Subscription plans listing
- Subscription creation/upgrade/cancel
- Bid wallet deposits
- Billing portal access
- Stripe webhooks
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request, Header, status
from pydantic import BaseModel, Field
from sqlalchemy import select

import stripe
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

from src.app.config import settings
from src.app.core.dependencies import DbSession, CurrentProfessional
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.professional import ProfessionalProfile, SubscriptionTier
from src.app.models.billing import Subscription, BidWallet, BidTransaction, SubscriptionStatus
from src.app.integrations.stripe import get_stripe_service

router = APIRouter()


# ==================== Schemas ====================

class SubscriptionPlanResponse(BaseModel):
    tier: str
    name: str
    price: float
    features: List[str]


class CreateSubscriptionRequest(BaseModel):
    tier: SubscriptionTier


class CreateSubscriptionResponse(BaseModel):
    subscription_id: str
    status: str
    client_secret: Optional[str] = None
    current_period_end: datetime


class SubscriptionResponse(BaseModel):
    id: UUID
    tier: SubscriptionTier
    status: SubscriptionStatus
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False


class BidWalletResponse(BaseModel):
    available_credits: float
    reserved_credits: float
    total_deposited: float
    total_spent: float


class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, le=10000, description="Amount in dollars")


class DepositResponse(BaseModel):
    checkout_url: str


class UpdateBidRequest(BaseModel):
    bid_amount: Decimal = Field(..., ge=0, le=100, description="Bid per click in dollars")
    daily_budget: Optional[Decimal] = Field(None, ge=0, le=1000, description="Daily budget limit")


class BillingPortalResponse(BaseModel):
    portal_url: str


# ==================== Routes ====================

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
@limiter.limit(RATE_LIMITS["api_read"])
async def list_subscription_plans(request: Request):
    """Get all available subscription plans with pricing and features."""
    stripe_service = get_stripe_service()
    return stripe_service.get_tier_pricing()


@router.get("/subscription", response_model=Optional[SubscriptionResponse])
@limiter.limit(RATE_LIMITS["api_read"])
async def get_my_subscription(
    request: Request,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """Get the current user's subscription details."""
    query = select(Subscription).where(
        Subscription.professional_id == current_user.professional_profile.id
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()

    if not subscription:
        return None

    return SubscriptionResponse(
        id=subscription.id,
        tier=subscription.tier,
        status=subscription.status,
        stripe_subscription_id=subscription.stripe_subscription_id,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
    )


@router.post("/subscription", response_model=CreateSubscriptionResponse)
@limiter.limit(RATE_LIMITS["billing"])
async def create_subscription(
    request: Request,
    body: CreateSubscriptionRequest,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Create or upgrade a subscription.

    Returns client_secret for Stripe Elements payment confirmation.
    """
    stripe_service = get_stripe_service()
    professional = current_user.professional_profile

    # Check for existing subscription
    query = select(Subscription).where(
        Subscription.professional_id == professional.id
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing and existing.status == SubscriptionStatus.ACTIVE:
        # Upgrade existing subscription
        if existing.stripe_subscription_id:
            upgrade_result = await stripe_service.update_subscription(
                existing.stripe_subscription_id,
                body.tier,
            )

            existing.tier = body.tier
            existing.current_period_end = upgrade_result["current_period_end"]
            await db.commit()

            return CreateSubscriptionResponse(
                subscription_id=upgrade_result["subscription_id"],
                status=upgrade_result["status"],
                current_period_end=upgrade_result["current_period_end"],
            )

    # Get or create Stripe customer
    customer_id = await stripe_service.get_or_create_customer(
        user_id=current_user.id,
        email=current_user.email,
        name=f"{current_user.first_name} {current_user.last_name}",
        existing_customer_id=professional.stripe_customer_id,
    )

    # Save customer ID if new
    if not professional.stripe_customer_id:
        professional.stripe_customer_id = customer_id
        await db.commit()

    # Create subscription in Stripe
    sub_result = await stripe_service.create_subscription(
        customer_id=customer_id,
        tier=body.tier,
        trial_days=settings.trial_period_days if not existing else 0,  # Trial only for first subscription
    )

    # Create or update subscription record
    if existing:
        existing.tier = body.tier
        existing.stripe_subscription_id = sub_result["subscription_id"]
        existing.status = SubscriptionStatus.PENDING
        existing.current_period_end = sub_result["current_period_end"]
    else:
        subscription = Subscription(
            professional_id=professional.id,
            stripe_subscription_id=sub_result["subscription_id"],
            tier=body.tier,
            status=SubscriptionStatus.PENDING,
            current_period_end=sub_result["current_period_end"],
        )
        db.add(subscription)

    await db.commit()

    return CreateSubscriptionResponse(
        subscription_id=sub_result["subscription_id"],
        status=sub_result["status"],
        client_secret=sub_result["client_secret"],
        current_period_end=sub_result["current_period_end"],
    )


@router.post("/subscription/cancel")
@limiter.limit(RATE_LIMITS["billing"])
async def cancel_subscription(
    request: Request,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Cancel subscription at the end of the billing period.
    """
    stripe_service = get_stripe_service()

    query = select(Subscription).where(
        Subscription.professional_id == current_user.professional_profile.id
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()

    if not subscription or not subscription.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )

    cancel_result = await stripe_service.cancel_subscription(
        subscription.stripe_subscription_id,
        at_period_end=True,
    )

    subscription.cancel_at_period_end = True
    await db.commit()

    return {
        "message": "Subscription will be cancelled at the end of the billing period",
        "current_period_end": cancel_result["current_period_end"],
    }


@router.post("/subscription/reactivate")
@limiter.limit(RATE_LIMITS["billing"])
async def reactivate_subscription(
    request: Request,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Reactivate a subscription that was set to cancel.
    """
    stripe_service = get_stripe_service()

    query = select(Subscription).where(
        Subscription.professional_id == current_user.professional_profile.id
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()

    if not subscription or not subscription.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found",
        )

    if not subscription.cancel_at_period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is not set to cancel",
        )

    await stripe_service.reactivate_subscription(subscription.stripe_subscription_id)

    subscription.cancel_at_period_end = False
    await db.commit()

    return {"message": "Subscription reactivated"}


# ==================== Bid Wallet ====================

@router.get("/wallet", response_model=BidWalletResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_bid_wallet(
    request: Request,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """Get the professional's bid wallet balance."""
    query = select(BidWallet).where(
        BidWallet.professional_id == current_user.professional_profile.id
    )
    result = await db.execute(query)
    wallet = result.scalar_one_or_none()

    if not wallet:
        # Create wallet if doesn't exist
        wallet = BidWallet(
            professional_id=current_user.professional_profile.id,
            available_credits=Decimal("0"),
            reserved_credits=Decimal("0"),
            total_deposited=Decimal("0"),
            total_spent=Decimal("0"),
        )
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)

    return BidWalletResponse(
        available_credits=float(wallet.available_credits),
        reserved_credits=float(wallet.reserved_credits),
        total_deposited=float(wallet.total_deposited),
        total_spent=float(wallet.total_spent),
    )


@router.post("/wallet/deposit", response_model=DepositResponse)
@limiter.limit(RATE_LIMITS["billing"])
async def create_deposit(
    request: Request,
    body: DepositRequest,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Create a checkout session for depositing bid credits.

    Returns a URL to redirect the user to Stripe Checkout.
    """
    stripe_service = get_stripe_service()
    professional = current_user.professional_profile

    # Ensure customer exists
    customer_id = await stripe_service.get_or_create_customer(
        user_id=current_user.id,
        email=current_user.email,
        name=f"{current_user.first_name} {current_user.last_name}",
        existing_customer_id=professional.stripe_customer_id,
    )

    if not professional.stripe_customer_id:
        professional.stripe_customer_id = customer_id
        await db.commit()

    # Create checkout session
    checkout_url = await stripe_service.create_bid_deposit_session(
        customer_id=customer_id,
        amount_dollars=body.amount,
        professional_id=professional.id,
        success_url=f"{settings.frontend_url}/dashboard/billing?deposit=success",
        cancel_url=f"{settings.frontend_url}/dashboard/billing?deposit=cancelled",
    )

    return DepositResponse(checkout_url=checkout_url)


@router.put("/bid-settings")
@limiter.limit(RATE_LIMITS["billing"])
async def update_bid_settings(
    request: Request,
    body: UpdateBidRequest,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Update bid amount and daily budget settings.
    """
    professional = current_user.professional_profile

    # Check wallet balance
    query = select(BidWallet).where(BidWallet.professional_id == professional.id)
    result = await db.execute(query)
    wallet = result.scalar_one_or_none()

    if body.bid_amount > 0:
        if not wallet or wallet.available_credits < body.bid_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient wallet balance to set this bid amount",
            )

    # Update professional's bid settings
    professional.current_bid_amount = body.bid_amount
    if body.daily_budget is not None:
        professional.daily_bid_budget = body.daily_budget

    await db.commit()

    # Invalidate grid cache so updated bid is reflected in ranking
    try:
        from src.app.core.cache import grid_cache
        await grid_cache.delete_pattern("*")  # Clear all grid cache entries
    except RedisError:
        pass  # Cache invalidation is best-effort

    return {
        "bid_amount": float(professional.current_bid_amount),
        "daily_budget": float(professional.daily_bid_budget) if professional.daily_bid_budget else None,
    }


@router.post("/portal", response_model=BillingPortalResponse)
@limiter.limit(RATE_LIMITS["billing"])
async def create_billing_portal_session(
    request: Request,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Create a Stripe Customer Portal session for billing management.
    """
    stripe_service = get_stripe_service()
    professional = current_user.professional_profile

    if not professional.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No billing account found. Please create a subscription first.",
        )

    portal_url = await stripe_service.create_customer_portal_session(
        customer_id=professional.stripe_customer_id,
        return_url=f"{settings.frontend_url}/dashboard/billing",
    )

    return BillingPortalResponse(portal_url=portal_url)


# ==================== Webhooks ====================

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: DbSession,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events.

    Events handled:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    - checkout.session.completed (for bid deposits)
    """
    stripe_service = get_stripe_service()

    payload = await request.body()

    try:
        event = stripe_service.construct_webhook_event(payload, stripe_signature)
    except (stripe.error.SignatureVerificationError, ValueError) as e:
        # Log detailed error internally, return generic message to client
        logger.error(f"Webhook signature verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "customer.subscription.created":
        await _handle_subscription_created(db, data)

    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(db, data)

    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data)

    elif event_type == "invoice.payment_succeeded":
        await _handle_payment_succeeded(db, data)

    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(db, data)

    elif event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data)

    return {"received": True}


# ==================== Webhook Handlers ====================

async def _handle_subscription_created(db: DbSession, data: dict):
    """Handle subscription creation."""
    subscription_id = data["id"]
    query = select(Subscription).where(
        Subscription.stripe_subscription_id == subscription_id
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.current_period_start = datetime.fromtimestamp(data["current_period_start"])
        subscription.current_period_end = datetime.fromtimestamp(data["current_period_end"])
        await db.commit()


async def _handle_subscription_updated(db: DbSession, data: dict):
    """Handle subscription updates."""
    subscription_id = data["id"]
    query = select(Subscription).where(
        Subscription.stripe_subscription_id == subscription_id
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.current_period_start = datetime.fromtimestamp(data["current_period_start"])
        subscription.current_period_end = datetime.fromtimestamp(data["current_period_end"])
        subscription.cancel_at_period_end = data.get("cancel_at_period_end", False)

        if data["status"] == "active":
            subscription.status = SubscriptionStatus.ACTIVE
        elif data["status"] == "past_due":
            subscription.status = SubscriptionStatus.PAST_DUE
        elif data["status"] == "canceled":
            subscription.status = SubscriptionStatus.CANCELLED

        await db.commit()

        # Update professional's subscription tier
        prof_query = select(ProfessionalProfile).where(
            ProfessionalProfile.id == subscription.professional_id
        )
        prof_result = await db.execute(prof_query)
        professional = prof_result.scalar_one_or_none()

        if professional:
            professional.subscription_tier = subscription.tier
            await db.commit()

            # Invalidate grid cache - tier change affects ranking
            try:
                from src.app.core.cache import grid_cache
                await grid_cache.delete_pattern("*")
            except RedisError:
                pass


async def _handle_subscription_deleted(db: DbSession, data: dict):
    """Handle subscription cancellation."""
    subscription_id = data["id"]
    query = select(Subscription).where(
        Subscription.stripe_subscription_id == subscription_id
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.status = SubscriptionStatus.CANCELLED
        await db.commit()

        # Downgrade professional to free tier
        prof_query = select(ProfessionalProfile).where(
            ProfessionalProfile.id == subscription.professional_id
        )
        prof_result = await db.execute(prof_query)
        professional = prof_result.scalar_one_or_none()

        if professional:
            professional.subscription_tier = SubscriptionTier.FREE
            await db.commit()

            # Invalidate grid cache - downgrade affects ranking
            try:
                from src.app.core.cache import grid_cache
                await grid_cache.delete_pattern("*")
            except RedisError:
                pass


async def _handle_payment_succeeded(db: DbSession, data: dict):
    """Handle successful invoice payment."""
    # Update subscription status if needed
    subscription_id = data.get("subscription")
    if subscription_id:
        query = select(Subscription).where(
            Subscription.stripe_subscription_id == subscription_id
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if subscription and subscription.status == SubscriptionStatus.PAST_DUE:
            subscription.status = SubscriptionStatus.ACTIVE
            await db.commit()


async def _handle_payment_failed(db: DbSession, data: dict):
    """Handle failed invoice payment."""
    subscription_id = data.get("subscription")
    if subscription_id:
        query = select(Subscription).where(
            Subscription.stripe_subscription_id == subscription_id
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus.PAST_DUE
            await db.commit()

            # Pause bids for professional
            prof_query = select(ProfessionalProfile).where(
                ProfessionalProfile.id == subscription.professional_id
            )
            prof_result = await db.execute(prof_query)
            professional = prof_result.scalar_one_or_none()

            if professional:
                professional.current_bid_amount = Decimal("0")
                await db.commit()


async def _handle_checkout_completed(db: DbSession, data: dict):
    """Handle completed checkout session (bid deposits)."""
    metadata = data.get("metadata", {})

    if metadata.get("type") == "bid_deposit":
        professional_id = metadata.get("professional_id")
        amount = Decimal(metadata.get("amount", "0"))

        if professional_id and amount > 0:
            # Update wallet
            query = select(BidWallet).where(
                BidWallet.professional_id == UUID(professional_id)
            )
            result = await db.execute(query)
            wallet = result.scalar_one_or_none()

            if wallet:
                wallet.available_credits += amount
                wallet.total_deposited += amount
            else:
                wallet = BidWallet(
                    professional_id=UUID(professional_id),
                    available_credits=amount,
                    reserved_credits=Decimal("0"),
                    total_deposited=amount,
                    total_spent=Decimal("0"),
                )
                db.add(wallet)

            # Record transaction
            transaction = BidTransaction(
                wallet_id=wallet.id,
                amount=amount,
                transaction_type="deposit",
                description=f"Deposited ${amount} via Stripe Checkout",
                stripe_payment_intent_id=data.get("payment_intent"),
            )
            db.add(transaction)

            await db.commit()
