"""
Invoice and Transaction History Service.

Provides professional invoice history from Stripe and internal transactions.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from src.app.config import settings

logger = logging.getLogger(__name__)


class InvoiceItem(BaseModel):
    """Individual invoice line item."""
    id: str
    invoice_id: str
    amount: float  # In dollars
    currency: str
    description: str
    date: datetime
    status: str  # paid, unpaid, void
    pdf_url: Optional[str] = None
    hosted_url: Optional[str] = None


class InvoiceHistoryResponse(BaseModel):
    """Response for invoice history request."""
    invoices: list[InvoiceItem]
    total_count: int
    has_more: bool


class UsageStats(BaseModel):
    """Usage statistics for a professional."""
    # Calls
    total_calls: int
    calls_this_month: int
    avg_call_duration_seconds: float
    
    # Leads
    total_leads: int
    leads_this_month: int
    lead_conversion_rate: float  # Leads that became calls
    
    # Grid Performance
    profile_views: int
    click_through_rate: float
    avg_grid_position: float
    
    # Spending
    total_bid_spent: float
    bid_spent_this_month: float
    cost_per_lead: float
    cost_per_call: float
    
    # Time
    time_online_today_seconds: int
    time_online_this_month_hours: float


class InvoiceService:
    """
    Service for retrieving invoice and transaction history.
    
    Fetches from Stripe API for subscription invoices
    and from internal database for bid transactions.
    """
    
    @staticmethod
    async def get_stripe_invoices(
        stripe_customer_id: str,
        limit: int = 20,
        starting_after: Optional[str] = None,
    ) -> InvoiceHistoryResponse:
        """
        Get invoice history from Stripe.
        
        Requires the professional to have a Stripe customer ID.
        """
        try:
            import stripe
            stripe.api_key = settings.stripe_secret_key
            
            params = {
                "customer": stripe_customer_id,
                "limit": limit,
            }
            if starting_after:
                params["starting_after"] = starting_after
            
            result = stripe.Invoice.list(**params)
            
            invoices = []
            for inv in result.data:
                invoices.append(InvoiceItem(
                    id=inv.id,
                    invoice_id=inv.number or inv.id,
                    amount=inv.amount_due / 100,  # Convert from cents
                    currency=inv.currency.upper(),
                    description=f"Subscription - {inv.lines.data[0].description if inv.lines.data else 'FaceMortgage'}",
                    date=datetime.fromtimestamp(inv.created),
                    status=inv.status,
                    pdf_url=inv.invoice_pdf,
                    hosted_url=inv.hosted_invoice_url,
                ))
            
            return InvoiceHistoryResponse(
                invoices=invoices,
                total_count=len(invoices),
                has_more=result.has_more,
            )
            
        except Exception as e:
            logger.error(f"Error fetching Stripe invoices: {e}")
            return InvoiceHistoryResponse(
                invoices=[],
                total_count=0,
                has_more=False,
            )
    
    @staticmethod
    async def get_bid_transactions(
        db,
        professional_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """
        Get bid wallet transaction history.
        """
        from sqlalchemy import select
        from src.app.models.billing import BidTransaction
        
        query = (
            select(BidTransaction)
            .where(BidTransaction.professional_id == professional_id)
            .order_by(BidTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return [
            {
                "id": str(tx.id),
                "type": tx.transaction_type,
                "amount": float(tx.amount),
                "description": tx.description,
                "created_at": tx.created_at.isoformat(),
            }
            for tx in transactions
        ]


class UsageAnalyticsService:
    """
    Service for calculating usage analytics for professionals.
    
    Aggregates data from calls, leads, grid tracking,
    and billing to provide comprehensive usage statistics.
    """
    
    @staticmethod
    async def get_usage_stats(
        db,
        professional_id: UUID,
    ) -> UsageStats:
        """
        Get comprehensive usage statistics for a professional.
        """
        from sqlalchemy import select, func
        from src.app.models.professional import ProfessionalProfile
        from src.app.models.call import VideoCall
        from src.app.models.lead import Lead
        from src.app.models.billing import BidTransaction, BidWallet
        
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get professional profile
        profile_query = select(ProfessionalProfile).where(
            ProfessionalProfile.id == professional_id
        )
        profile_result = await db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            # Return empty stats
            return UsageStats(
                total_calls=0,
                calls_this_month=0,
                avg_call_duration_seconds=0,
                total_leads=0,
                leads_this_month=0,
                lead_conversion_rate=0,
                profile_views=0,
                click_through_rate=0,
                avg_grid_position=0,
                total_bid_spent=0,
                bid_spent_this_month=0,
                cost_per_lead=0,
                cost_per_call=0,
                time_online_today_seconds=0,
                time_online_this_month_hours=0,
            )
        
        # Total calls
        total_calls_query = select(func.count(VideoCall.id)).where(
            VideoCall.professional_id == professional_id
        )
        total_calls = (await db.execute(total_calls_query)).scalar() or 0
        
        # Calls this month
        month_calls_query = select(func.count(VideoCall.id)).where(
            VideoCall.professional_id == professional_id,
            VideoCall.created_at >= month_start
        )
        calls_this_month = (await db.execute(month_calls_query)).scalar() or 0
        
        # Avg call duration
        duration_query = select(func.avg(VideoCall.duration_seconds)).where(
            VideoCall.professional_id == professional_id,
            VideoCall.duration_seconds != None
        )
        avg_duration = (await db.execute(duration_query)).scalar() or 0
        
        # Total leads
        total_leads_query = select(func.count(Lead.id)).where(
            Lead.professional_id == professional_id
        )
        total_leads = (await db.execute(total_leads_query)).scalar() or 0
        
        # Leads this month
        month_leads_query = select(func.count(Lead.id)).where(
            Lead.professional_id == professional_id,
            Lead.created_at >= month_start
        )
        leads_this_month = (await db.execute(month_leads_query)).scalar() or 0
        
        # Lead conversion rate
        conversion_rate = 0.0
        if total_leads > 0:
            conversion_rate = (total_calls / total_leads) * 100 if total_leads > 0 else 0
        
        # Bid wallet spending
        wallet_query = select(BidWallet).where(
            BidWallet.professional_id == professional_id
        )
        wallet_result = await db.execute(wallet_query)
        wallet = wallet_result.scalar_one_or_none()
        
        total_spent = float(wallet.total_spent) if wallet else 0
        
        # Month spend
        month_spend_query = select(func.sum(BidTransaction.amount)).where(
            BidTransaction.professional_id == professional_id,
            BidTransaction.transaction_type == "spend",
            BidTransaction.created_at >= month_start
        )
        month_spend = (await db.execute(month_spend_query)).scalar() or 0
        
        # Cost per lead/call
        cost_per_lead = total_spent / total_leads if total_leads > 0 else 0
        cost_per_call = total_spent / total_calls if total_calls > 0 else 0
        
        return UsageStats(
            total_calls=total_calls,
            calls_this_month=calls_this_month,
            avg_call_duration_seconds=float(avg_duration),
            total_leads=total_leads,
            leads_this_month=leads_this_month,
            lead_conversion_rate=round(conversion_rate, 1),
            profile_views=0,  # Would come from analytics tracking
            click_through_rate=0,  # Would come from analytics tracking
            avg_grid_position=0,  # Would come from grid tracking
            total_bid_spent=total_spent,
            bid_spent_this_month=float(month_spend),
            cost_per_lead=round(cost_per_lead, 2),
            cost_per_call=round(cost_per_call, 2),
            time_online_today_seconds=profile.time_online_today_seconds,
            time_online_this_month_hours=0,  # Would aggregate from daily tracking
        )
