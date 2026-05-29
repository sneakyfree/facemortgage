"""
Invoice and Usage Analytics API endpoints.

Provides Phase 3 monetization features:
- Invoice history from Stripe
- Bid transaction history
- Usage analytics dashboard data
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request, Query, HTTPException, status

from src.app.core.dependencies import DbSession, CurrentProfessional
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.services.invoice_service import (
    InvoiceService,
    UsageAnalyticsService,
    InvoiceHistoryResponse,
    UsageStats,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/invoices", response_model=InvoiceHistoryResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_invoice_history(
    request: Request,
    current_user: CurrentProfessional,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    starting_after: Optional[str] = None,
):
    """
    Get invoice history for the current professional.
    
    Returns paginated list of invoices from Stripe including:
    - Invoice ID and number
    - Amount and currency
    - Status (paid, unpaid, void)
    - PDF download URL
    - Hosted payment URL (for unpaid)
    """
    from sqlalchemy import select
    from src.app.models.professional import ProfessionalProfile
    
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    if not profile.stripe_customer_id:
        # No Stripe customer yet - return empty
        return InvoiceHistoryResponse(
            invoices=[],
            total_count=0,
            has_more=False,
        )
    
    return await InvoiceService.get_stripe_invoices(
        stripe_customer_id=profile.stripe_customer_id,
        limit=limit,
        starting_after=starting_after,
    )


@router.get("/transactions")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_bid_transactions(
    request: Request,
    current_user: CurrentProfessional,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    Get bid wallet transaction history.
    
    Returns list of bid deposits, spends, and refunds.
    """
    from sqlalchemy import select
    from src.app.models.professional import ProfessionalProfile
    
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    transactions = await InvoiceService.get_bid_transactions(
        db=db,
        professional_id=profile.id,
        limit=limit,
        offset=offset,
    )
    
    return {
        "transactions": transactions,
        "count": len(transactions),
        "offset": offset,
    }


@router.get("/usage", response_model=UsageStats)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_usage_analytics(
    request: Request,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Get comprehensive usage analytics for the professional dashboard.
    
    Returns aggregated statistics including:
    - Call metrics (total, this month, avg duration)
    - Lead metrics (total, conversion rate)
    - Grid performance (views, click-through rate)
    - Spending (total, cost per lead/call)
    - Online time tracking
    
    Use this endpoint to power the usage analytics dashboard.
    """
    from sqlalchemy import select
    from src.app.models.professional import ProfessionalProfile
    
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    return await UsageAnalyticsService.get_usage_stats(
        db=db,
        professional_id=profile.id,
    )


@router.get("/summary")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_billing_summary(
    request: Request,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Get a quick billing summary for dashboard cards.
    
    Returns high-level billing status including:
    - Current subscription tier
    - Next billing date
    - Wallet balance
    - Month spend
    """
    from sqlalchemy import select
    from src.app.models.professional import ProfessionalProfile
    from src.app.models.billing import Subscription, BidWallet
    
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    # Get subscription
    sub_query = select(Subscription).where(
        Subscription.professional_id == profile.id
    )
    sub_result = await db.execute(sub_query)
    subscription = sub_result.scalar_one_or_none()
    
    # Get wallet
    wallet_query = select(BidWallet).where(
        BidWallet.professional_id == profile.id
    )
    wallet_result = await db.execute(wallet_query)
    wallet = wallet_result.scalar_one_or_none()
    
    return {
        "subscription": {
            "tier": profile.subscription_tier.value,
            "status": subscription.status.value if subscription else "none",
            "current_period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
            "cancel_at_period_end": subscription.cancel_at_period_end if subscription else False,
        },
        "wallet": {
            "balance": float(wallet.available_credits) if wallet else 0,
            "reserved": float(wallet.reserved_credits) if wallet else 0,
            "current_bid": float(profile.current_bid_amount),
            "daily_budget": float(profile.daily_bid_budget) if profile.daily_bid_budget else None,
        },
    }
