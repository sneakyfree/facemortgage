"""
Analytics service for aggregating professional performance metrics.

Provides:
- Dashboard statistics
- Daily/weekly/monthly trends
- ROI calculations
- Conversion funnel metrics
"""
import logging
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.call import VideoCall, CallStatus
from src.app.models.lead import Lead, LeadStatus
from src.app.models.analytics import GridImpression, GridClick
from src.app.models.billing import Subscription, BillingTransaction

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for aggregating and computing analytics metrics."""

    async def get_dashboard_stats(
        self,
        professional_id: UUID,
        db: AsyncSession,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics for a professional.

        Args:
            professional_id: UUID of the professional
            db: Database session
            days: Number of days to look back (default: 30)

        Returns:
            Dictionary with calls, leads, and grid performance stats
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Call statistics
        call_stats = await self._get_call_stats(db, professional_id, start_date)

        # Lead statistics
        lead_stats = await self._get_lead_stats(db, professional_id, start_date)

        # Grid performance
        grid_stats = await self._get_grid_stats(db, professional_id, start_date)

        return {
            "period_days": days,
            "period_start": start_date.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "calls": call_stats,
            "leads": lead_stats,
            "grid": grid_stats,
        }

    async def _get_call_stats(
        self,
        db: AsyncSession,
        professional_id: UUID,
        start_date: datetime,
    ) -> Dict[str, Any]:
        """Get call-related statistics."""
        query = select(
            func.count(VideoCall.id).label("total_calls"),
            func.count(VideoCall.id).filter(
                VideoCall.status == CallStatus.COMPLETED
            ).label("completed_calls"),
            func.count(VideoCall.id).filter(
                VideoCall.status == CallStatus.MISSED
            ).label("missed_calls"),
            func.count(VideoCall.id).filter(
                VideoCall.status == CallStatus.DECLINED
            ).label("declined_calls"),
            func.avg(VideoCall.pickup_time_seconds).filter(
                VideoCall.status == CallStatus.COMPLETED
            ).label("avg_pickup_time"),
            func.avg(VideoCall.duration_seconds).filter(
                VideoCall.status == CallStatus.COMPLETED
            ).label("avg_duration"),
            func.sum(VideoCall.duration_seconds).filter(
                VideoCall.status == CallStatus.COMPLETED
            ).label("total_talk_time"),
        ).where(
            VideoCall.professional_id == professional_id,
            VideoCall.initiated_at >= start_date,
        )

        result = await db.execute(query)
        row = result.one()

        total = row.total_calls or 0
        completed = row.completed_calls or 0

        return {
            "total": total,
            "completed": completed,
            "missed": row.missed_calls or 0,
            "declined": row.declined_calls or 0,
            "answer_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "avg_pickup_time_seconds": round(float(row.avg_pickup_time or 0), 1),
            "avg_duration_seconds": round(float(row.avg_duration or 0), 0),
            "total_talk_time_minutes": round(float(row.total_talk_time or 0) / 60, 0),
        }

    async def _get_lead_stats(
        self,
        db: AsyncSession,
        professional_id: UUID,
        start_date: datetime,
    ) -> Dict[str, Any]:
        """Get lead-related statistics."""
        query = select(
            func.count(Lead.id).label("total_leads"),
            func.count(Lead.id).filter(Lead.lead_status == LeadStatus.NEW).label("new_leads"),
            func.count(Lead.id).filter(Lead.lead_status == LeadStatus.CONTACTED).label("contacted_leads"),
            func.count(Lead.id).filter(Lead.lead_status == LeadStatus.QUALIFIED).label("qualified_leads"),
            func.count(Lead.id).filter(Lead.lead_status == LeadStatus.WON).label("won_leads"),
            func.count(Lead.id).filter(Lead.lead_status == LeadStatus.LOST).label("lost_leads"),
            func.sum(Lead.estimated_loan_amount).filter(Lead.lead_status == LeadStatus.WON).label("won_volume"),
        ).where(
            Lead.professional_id == professional_id,
            Lead.created_at >= start_date,
        )

        result = await db.execute(query)
        row = result.one()

        total = row.total_leads or 0
        won = row.won_leads or 0

        return {
            "total": total,
            "new": row.new_leads or 0,
            "contacted": row.contacted_leads or 0,
            "qualified": row.qualified_leads or 0,
            "won": won,
            "lost": row.lost_leads or 0,
            "won_volume": float(row.won_volume or 0),
            "conversion_rate": round(won / total * 100, 1) if total > 0 else 0,
        }

    async def _get_grid_stats(
        self,
        db: AsyncSession,
        professional_id: UUID,
        start_date: datetime,
    ) -> Dict[str, Any]:
        """Get grid performance statistics."""
        # Impressions
        impressions_query = select(
            func.sum(GridImpression.impressions_count).label("total_impressions"),
        ).where(
            GridImpression.professional_id == professional_id,
            GridImpression.date >= start_date.date(),
        )
        imp_result = await db.execute(impressions_query)
        impressions = imp_result.scalar() or 0

        # Clicks
        clicks_query = select(
            func.count(GridClick.id).label("total_clicks"),
            func.count(GridClick.id).filter(GridClick.click_type == "call_initiated").label("call_clicks"),
            func.count(GridClick.id).filter(GridClick.click_type == "profile_view").label("profile_clicks"),
            func.count(GridClick.id).filter(GridClick.click_type == "schedule_click").label("schedule_clicks"),
        ).where(
            GridClick.professional_id == professional_id,
            GridClick.created_at >= start_date,
        )
        click_result = await db.execute(clicks_query)
        click_row = click_result.one()

        clicks = click_row.total_clicks or 0

        # Get call count for click-to-call rate
        call_count_query = select(func.count(VideoCall.id)).where(
            VideoCall.professional_id == professional_id,
            VideoCall.initiated_at >= start_date,
        )
        call_result = await db.execute(call_count_query)
        calls = call_result.scalar() or 0

        return {
            "impressions": impressions,
            "clicks": clicks,
            "profile_views": click_row.profile_clicks or 0,
            "call_clicks": click_row.call_clicks or 0,
            "schedule_clicks": click_row.schedule_clicks or 0,
            "ctr": round(clicks / impressions * 100, 2) if impressions > 0 else 0,
            "click_to_call_rate": round(calls / clicks * 100, 1) if clicks > 0 else 0,
        }

    async def get_daily_trends(
        self,
        professional_id: UUID,
        db: AsyncSession,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get daily trend data for charts.

        Returns list of daily metrics for the specified period.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Daily calls
        query = select(
            func.date(VideoCall.initiated_at).label("date"),
            func.count(VideoCall.id).label("calls"),
            func.count(VideoCall.id).filter(VideoCall.status == CallStatus.COMPLETED).label("completed"),
            func.count(VideoCall.id).filter(VideoCall.status == CallStatus.MISSED).label("missed"),
        ).where(
            VideoCall.professional_id == professional_id,
            VideoCall.initiated_at >= start_date,
        ).group_by(
            func.date(VideoCall.initiated_at)
        ).order_by(
            func.date(VideoCall.initiated_at)
        )

        result = await db.execute(query)

        # Build complete date range with zeros for missing days
        date_data = {}
        for row in result:
            date_str = row.date.isoformat() if isinstance(row.date, date) else str(row.date)
            date_data[date_str] = {
                "date": date_str,
                "calls": row.calls,
                "completed": row.completed,
                "missed": row.missed,
            }

        # Fill in missing dates
        trends = []
        current = start_date.date()
        end = datetime.utcnow().date()

        while current <= end:
            date_str = current.isoformat()
            if date_str in date_data:
                trends.append(date_data[date_str])
            else:
                trends.append({
                    "date": date_str,
                    "calls": 0,
                    "completed": 0,
                    "missed": 0,
                })
            current += timedelta(days=1)

        return trends

    async def get_hourly_distribution(
        self,
        professional_id: UUID,
        db: AsyncSession,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get call distribution by hour of day.

        Useful for understanding peak call times.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = select(
            func.extract('hour', VideoCall.initiated_at).label("hour"),
            func.count(VideoCall.id).label("calls"),
            func.count(VideoCall.id).filter(VideoCall.status == CallStatus.COMPLETED).label("completed"),
        ).where(
            VideoCall.professional_id == professional_id,
            VideoCall.initiated_at >= start_date,
        ).group_by(
            func.extract('hour', VideoCall.initiated_at)
        ).order_by(
            func.extract('hour', VideoCall.initiated_at)
        )

        result = await db.execute(query)

        # Build complete 24-hour distribution
        hour_data = {int(row.hour): {"calls": row.calls, "completed": row.completed} for row in result}

        distribution = []
        for hour in range(24):
            data = hour_data.get(hour, {"calls": 0, "completed": 0})
            distribution.append({
                "hour": hour,
                "label": f"{hour:02d}:00",
                "calls": data["calls"],
                "completed": data["completed"],
            })

        return distribution

    async def get_roi_metrics(
        self,
        professional_id: UUID,
        db: AsyncSession,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Calculate ROI metrics for the professional.

        Computes cost per lead, estimated commission, and ROI percentage.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get subscription cost
        sub_query = select(Subscription).where(
            Subscription.professional_id == professional_id
        )
        sub_result = await db.execute(sub_query)
        subscription = sub_result.scalar_one_or_none()

        # Get subscription price (simplified - would normally look up plan)
        tier_prices = {
            "free": 0,
            "basic": 49,
            "professional": 99,
            "premium": 199,
        }
        monthly_subscription = 0
        if subscription and subscription.tier:
            monthly_subscription = tier_prices.get(subscription.tier.value, 0)

        # Get bid spend
        bid_query = select(
            func.sum(BillingTransaction.amount).label("bid_spend")
        ).where(
            BillingTransaction.professional_id == professional_id,
            BillingTransaction.transaction_type == "bid_charge",
            BillingTransaction.created_at >= start_date,
        )
        bid_result = await db.execute(bid_query)
        monthly_bid_spend = float(bid_result.scalar() or 0)

        # Get leads won and volume
        leads_query = select(
            func.count(Lead.id).label("won_count"),
            func.sum(Lead.estimated_loan_amount).label("total_volume"),
        ).where(
            Lead.professional_id == professional_id,
            Lead.lead_status == LeadStatus.WON,
            Lead.updated_at >= start_date,
        )
        leads_result = await db.execute(leads_query)
        leads_row = leads_result.one()

        won_count = leads_row.won_count or 0
        total_volume = float(leads_row.total_volume or 0)

        # Calculate metrics
        total_cost = monthly_subscription + monthly_bid_spend
        estimated_commission = total_volume * 0.01  # Assume 1% average commission
        profit = estimated_commission - total_cost
        roi_percentage = (profit / total_cost * 100) if total_cost > 0 else 0

        return {
            "period_days": days,
            "costs": {
                "subscription": monthly_subscription,
                "bid_spend": round(monthly_bid_spend, 2),
                "total": round(total_cost, 2),
            },
            "results": {
                "leads_won": won_count,
                "total_volume": total_volume,
                "estimated_commission": round(estimated_commission, 2),
            },
            "metrics": {
                "cost_per_lead": round(total_cost / won_count, 2) if won_count > 0 else 0,
                "profit": round(profit, 2),
                "roi_percentage": round(roi_percentage, 1),
            },
        }

    async def get_conversion_funnel(
        self,
        professional_id: UUID,
        db: AsyncSession,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get conversion funnel metrics.

        Shows progression from impressions -> clicks -> calls -> leads -> conversions.
        """
        stats = await self.get_dashboard_stats(professional_id, db, days)

        impressions = stats["grid"]["impressions"]
        clicks = stats["grid"]["clicks"]
        calls = stats["calls"]["total"]
        completed_calls = stats["calls"]["completed"]
        leads = stats["leads"]["total"]
        won = stats["leads"]["won"]

        return {
            "stages": [
                {
                    "name": "Impressions",
                    "count": impressions,
                    "percentage": 100,
                },
                {
                    "name": "Clicks",
                    "count": clicks,
                    "percentage": round(clicks / impressions * 100, 1) if impressions > 0 else 0,
                },
                {
                    "name": "Calls",
                    "count": calls,
                    "percentage": round(calls / clicks * 100, 1) if clicks > 0 else 0,
                },
                {
                    "name": "Completed Calls",
                    "count": completed_calls,
                    "percentage": round(completed_calls / calls * 100, 1) if calls > 0 else 0,
                },
                {
                    "name": "Leads",
                    "count": leads,
                    "percentage": round(leads / completed_calls * 100, 1) if completed_calls > 0 else 0,
                },
                {
                    "name": "Conversions",
                    "count": won,
                    "percentage": round(won / leads * 100, 1) if leads > 0 else 0,
                },
            ],
            "overall_conversion": round(won / impressions * 100, 3) if impressions > 0 else 0,
        }

    async def get_lead_sources(
        self,
        professional_id: UUID,
        db: AsyncSession,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get breakdown of lead sources."""
        start_date = datetime.utcnow() - timedelta(days=days)

        query = select(
            Lead.utm_source,
            func.count(Lead.id).label("count"),
            func.count(Lead.id).filter(Lead.lead_status == LeadStatus.WON).label("won"),
        ).where(
            Lead.professional_id == professional_id,
            Lead.created_at >= start_date,
        ).group_by(
            Lead.utm_source
        ).order_by(
            func.count(Lead.id).desc()
        )

        result = await db.execute(query)

        sources = []
        for row in result:
            source_name = row.utm_source or "Direct"
            sources.append({
                "source": source_name,
                "count": row.count,
                "won": row.won or 0,
                "conversion_rate": round((row.won or 0) / row.count * 100, 1) if row.count > 0 else 0,
            })

        return sources


# Singleton instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get the analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
