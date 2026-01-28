"""
Bid Wallet API Routes.

Provides endpoints for:
- Wallet balance and deposits
- Placement bids for premium grid positioning
- Transaction history
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.core.auth import get_current_user
from src.app.models.user import User
from src.app.models.billing import BidWallet, BidTransaction, PlacementBid
from src.app.models.professional import ProfessionalProfile

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class WalletBalanceResponse(BaseModel):
    """Current wallet balance and stats."""
    available_credits: Decimal
    reserved_credits: Decimal
    total_deposited: Decimal
    total_spent: Decimal
    
    class Config:
        from_attributes = True


class DepositRequest(BaseModel):
    """Request to deposit funds via Stripe."""
    amount: Decimal = Field(..., gt=0, le=10000, description="Amount in USD")


class DepositResponse(BaseModel):
    """Response with Stripe payment intent for deposit."""
    client_secret: str
    amount: Decimal
    payment_intent_id: str


class TransactionResponse(BaseModel):
    """Single wallet transaction."""
    id: UUID
    amount: Decimal
    transaction_type: str
    description: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class PlacementBidRequest(BaseModel):
    """Request to create or update a placement bid."""
    daily_budget: Decimal = Field(..., gt=0, le=1000)
    bid_per_impression: Optional[Decimal] = Field(None, ge=0.01, le=5)
    bid_per_click: Optional[Decimal] = Field(None, ge=0.10, le=50)
    target_counties: Optional[list[str]] = None
    target_languages: Optional[list[str]] = None
    target_specialties: Optional[list[str]] = None


class PlacementBidResponse(BaseModel):
    """Active placement bid details."""
    id: UUID
    daily_budget: Decimal
    bid_per_impression: Optional[Decimal]
    bid_per_click: Optional[Decimal]
    target_counties: Optional[list[str]]
    target_languages: Optional[list[str]]
    target_specialties: Optional[list[str]]
    daily_spent: Decimal
    total_spent: Decimal
    is_active: bool
    estimated_position: Optional[int] = None
    
    class Config:
        from_attributes = True


class PositionPreviewRequest(BaseModel):
    """Request to preview grid position for a bid amount."""
    bid_amount: Decimal = Field(..., gt=0)
    state: Optional[str] = None


class PositionPreviewResponse(BaseModel):
    """Estimated grid position for bid."""
    bid_amount: Decimal
    estimated_position: int
    competing_bids: int
    position_percentile: float


# ============================================================================
# WALLET ENDPOINTS
# ============================================================================

@router.get("/wallet", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current wallet balance for the professional."""
    # Get or create wallet
    result = await db.execute(
        select(BidWallet)
        .join(ProfessionalProfile)
        .where(ProfessionalProfile.user_id == current_user.id)
    )
    wallet = result.scalar_one_or_none()
    
    if not wallet:
        # Create wallet for pro
        pro_result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == current_user.id)
        )
        pro = pro_result.scalar_one_or_none()
        if not pro:
            raise HTTPException(status_code=404, detail="Professional profile not found")
        
        wallet = BidWallet(professional_id=pro.id)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    
    return WalletBalanceResponse(
        available_credits=wallet.available_credits,
        reserved_credits=wallet.reserved_credits,
        total_deposited=wallet.total_deposited,
        total_spent=wallet.total_spent,
    )


@router.post("/wallet/deposit", response_model=DepositResponse)
async def create_deposit(
    request: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe payment intent for depositing funds."""
    import stripe
    from src.app.config import settings
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # Get professional
    pro_result = await db.execute(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == current_user.id)
    )
    pro = pro_result.scalar_one_or_none()
    if not pro:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    
    # Create payment intent
    amount_cents = int(request.amount * 100)
    
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            metadata={
                "type": "bid_wallet_deposit",
                "professional_id": str(pro.id),
                "user_id": str(current_user.id),
            },
        )
        
        return DepositResponse(
            client_secret=payment_intent.client_secret,
            amount=request.amount,
            payment_intent_id=payment_intent.id,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating deposit: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wallet/deposit/confirm")
async def confirm_deposit(
    payment_intent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a deposit after Stripe payment succeeds."""
    import stripe
    from src.app.config import settings
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status != "succeeded":
            raise HTTPException(status_code=400, detail="Payment not completed")
        
        # Get wallet
        result = await db.execute(
            select(BidWallet)
            .join(ProfessionalProfile)
            .where(ProfessionalProfile.user_id == current_user.id)
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Check if already processed
        existing = await db.execute(
            select(BidTransaction).where(
                BidTransaction.stripe_payment_intent_id == payment_intent_id
            )
        )
        if existing.scalar_one_or_none():
            return {"status": "already_processed"}
        
        # Add credits
        amount = Decimal(payment_intent.amount) / 100
        wallet.available_credits += amount
        wallet.total_deposited += amount
        
        # Record transaction
        transaction = BidTransaction(
            wallet_id=wallet.id,
            amount=amount,
            transaction_type="deposit",
            description=f"Deposit via Stripe",
            stripe_payment_intent_id=payment_intent_id,
        )
        db.add(transaction)
        await db.commit()
        
        return {"status": "success", "new_balance": float(wallet.available_credits)}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error confirming deposit: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallet/transactions", response_model=list[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get wallet transaction history."""
    result = await db.execute(
        select(BidTransaction)
        .join(BidWallet)
        .join(ProfessionalProfile)
        .where(ProfessionalProfile.user_id == current_user.id)
        .order_by(desc(BidTransaction.created_at))
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()
    
    return [
        TransactionResponse(
            id=t.id,
            amount=t.amount,
            transaction_type=t.transaction_type,
            description=t.description,
            created_at=t.created_at.isoformat(),
        )
        for t in transactions
    ]


# ============================================================================
# PLACEMENT BID ENDPOINTS
# ============================================================================

@router.get("/placement", response_model=list[PlacementBidResponse])
async def get_placement_bids(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all placement bids for the professional."""
    result = await db.execute(
        select(PlacementBid)
        .join(ProfessionalProfile)
        .where(ProfessionalProfile.user_id == current_user.id)
        .order_by(desc(PlacementBid.created_at))
    )
    bids = result.scalars().all()
    
    return [
        PlacementBidResponse(
            id=b.id,
            daily_budget=b.daily_budget,
            bid_per_impression=b.bid_per_impression,
            bid_per_click=b.bid_per_click,
            target_counties=b.target_counties,
            target_languages=b.target_languages,
            target_specialties=b.target_specialties,
            daily_spent=b.daily_spent,
            total_spent=b.total_spent,
            is_active=b.is_active,
        )
        for b in bids
    ]


@router.post("/placement", response_model=PlacementBidResponse)
async def create_placement_bid(
    request: PlacementBidRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new placement bid."""
    # Get professional
    pro_result = await db.execute(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == current_user.id)
    )
    pro = pro_result.scalar_one_or_none()
    if not pro:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    
    # Check wallet balance
    wallet_result = await db.execute(
        select(BidWallet).where(BidWallet.professional_id == pro.id)
    )
    wallet = wallet_result.scalar_one_or_none()
    
    if not wallet or wallet.available_credits < request.daily_budget:
        raise HTTPException(
            status_code=400, 
            detail="Insufficient wallet balance for daily budget"
        )
    
    # Create bid
    bid = PlacementBid(
        professional_id=pro.id,
        daily_budget=request.daily_budget,
        bid_per_impression=request.bid_per_impression,
        bid_per_click=request.bid_per_click,
        target_counties=request.target_counties,
        target_languages=request.target_languages,
        target_specialties=request.target_specialties,
    )
    db.add(bid)
    
    # Reserve credits
    wallet.available_credits -= request.daily_budget
    wallet.reserved_credits += request.daily_budget
    
    await db.commit()
    await db.refresh(bid)
    
    return PlacementBidResponse(
        id=bid.id,
        daily_budget=bid.daily_budget,
        bid_per_impression=bid.bid_per_impression,
        bid_per_click=bid.bid_per_click,
        target_counties=bid.target_counties,
        target_languages=bid.target_languages,
        target_specialties=bid.target_specialties,
        daily_spent=bid.daily_spent,
        total_spent=bid.total_spent,
        is_active=bid.is_active,
    )


@router.delete("/placement/{bid_id}")
async def cancel_placement_bid(
    bid_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an active placement bid."""
    result = await db.execute(
        select(PlacementBid)
        .join(ProfessionalProfile)
        .where(
            PlacementBid.id == bid_id,
            ProfessionalProfile.user_id == current_user.id,
        )
    )
    bid = result.scalar_one_or_none()
    
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    if not bid.is_active:
        raise HTTPException(status_code=400, detail="Bid already cancelled")
    
    # Refund reserved credits
    wallet_result = await db.execute(
        select(BidWallet).where(BidWallet.professional_id == bid.professional_id)
    )
    wallet = wallet_result.scalar_one_or_none()
    
    if wallet:
        refund_amount = bid.daily_budget - bid.daily_spent
        wallet.reserved_credits -= refund_amount
        wallet.available_credits += refund_amount
    
    bid.is_active = False
    await db.commit()
    
    return {"status": "cancelled", "refunded": float(refund_amount) if wallet else 0}


@router.post("/placement/preview", response_model=PositionPreviewResponse)
async def preview_grid_position(
    request: PositionPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview estimated grid position for a bid amount."""
    # Count competing bids
    query = select(PlacementBid).where(
        PlacementBid.is_active == True,
        PlacementBid.daily_budget >= request.bid_amount,
    )
    
    result = await db.execute(query)
    higher_bids = len(result.scalars().all())
    
    total_result = await db.execute(
        select(PlacementBid).where(PlacementBid.is_active == True)
    )
    total_bids = len(total_result.scalars().all())
    
    # Estimate position (1 = top)
    estimated_position = higher_bids + 1
    percentile = (1 - (estimated_position / max(total_bids, 1))) * 100
    
    return PositionPreviewResponse(
        bid_amount=request.bid_amount,
        estimated_position=estimated_position,
        competing_bids=total_bids,
        position_percentile=round(percentile, 1),
    )
