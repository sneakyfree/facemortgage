"""
API routes for professional analytics dashboard.
"""
import uuid
from datetime import datetime, date, timedelta
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, and_, extract, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.auth import get_current_user
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.core.database import get_db
from src.app.models.user import User
from src.app.models.professional import ProfessionalProfile
from src.app.models.call import VideoCall, CallStatus
from src.app.models.review import Review
from src.app.models.lead import Lead, LeadStatus
from src.app.models.billing import Subscription, BidWallet, BidTransaction
from src.app.models.analytics import GridImpression, GridClick
from src.app.schemas.analytics import (
    AnalyticsDashboard,
    PerformanceMetrics,
    CallAnalytics,
    RatingAnalytics,
    LeadAnalytics,
    BillingAnalytics,
    GridAnalytics,
    PeerComparison,
    ComparisonMetrics,
    TimeSeriesPoint,
)

router = APIRouter()


# ==================== Simple Overview Schema ====================

from pydantic import BaseModel

class AnalyticsOverviewResponse(BaseModel):
    total_calls: int
    total_leads: int
    total_reviews: int
    avg_rating: float
    avg_pickup_time_seconds: float
    total_time_online_seconds: int
    revenue_this_month: Optional[float] = None


async def get_professional_profile(user: User, db: AsyncSession) -> ProfessionalProfile:
    """Get the professional profile for the current user."""
    result = await db.execute(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    return profile


@router.get("/overview", response_model=AnalyticsOverviewResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_analytics_overview(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a simple overview of professional analytics."""
    profile = await get_professional_profile(user, db)

    # Total calls
    calls_result = await db.execute(
        select(func.count(VideoCall.id))
        .where(VideoCall.professional_id == profile.id)
    )
    total_calls = calls_result.scalar() or 0

    # Total leads
    leads_result = await db.execute(
        select(func.count(Lead.id))
        .where(Lead.professional_id == profile.id)
    )
    total_leads = leads_result.scalar() or 0

    # Reviews and average rating
    reviews_result = await db.execute(
        select(
            func.count(Review.id).label("total"),
            func.coalesce(func.avg(Review.overall_rating), 0).label("avg"),
        )
        .where(Review.reviewed_professional_id == profile.id)
    )
    reviews_stats = reviews_result.one()

    # Average pickup time
    pickup_result = await db.execute(
        select(func.coalesce(func.avg(VideoCall.pickup_time_seconds), 0))
        .where(VideoCall.professional_id == profile.id)
        .where(VideoCall.pickup_time_seconds.isnot(None))
    )
    avg_pickup = pickup_result.scalar() or 0

    # Time online today (from profile)
    time_online = profile.time_online_today_seconds or 0

    return AnalyticsOverviewResponse(
        total_calls=total_calls,
        total_leads=total_leads,
        total_reviews=reviews_stats.total or 0,
        avg_rating=float(reviews_stats.avg or 0),
        avg_pickup_time_seconds=float(avg_pickup),
        total_time_online_seconds=time_online,
        revenue_this_month=None,
    )


class RecentActivityItem(BaseModel):
    id: str
    type: str  # 'call', 'lead', 'review'
    title: str
    description: str
    time: str
    created_at: datetime


class RecentActivityResponse(BaseModel):
    activities: list[RecentActivityItem]


@router.get("/recent-activity", response_model=RecentActivityResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_recent_activity(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent activity for the professional dashboard."""
    profile = await get_professional_profile(user, db)
    activities = []

    # Get recent calls
    calls_result = await db.execute(
        select(VideoCall)
        .where(VideoCall.professional_id == profile.id)
        .order_by(VideoCall.initiated_at.desc())
        .limit(limit)
    )
    for call in calls_result.scalars():
        activities.append(RecentActivityItem(
            id=str(call.id),
            type="call",
            title=f"Video call" + (f" - {call.duration_seconds}s" if call.duration_seconds else ""),
            description=f"Status: {call.status.value if call.status else 'unknown'}",
            time=_format_relative_time(call.initiated_at),
            created_at=call.initiated_at,
        ))

    # Get recent leads
    leads_result = await db.execute(
        select(Lead)
        .where(Lead.professional_id == profile.id)
        .order_by(Lead.created_at.desc())
        .limit(limit)
    )
    for lead in leads_result.scalars():
        activities.append(RecentActivityItem(
            id=str(lead.id),
            type="lead",
            title=f"New lead" + (f" - {lead.contact_name}" if lead.contact_name else ""),
            description=f"Status: {lead.lead_status.value if lead.lead_status else 'new'}",
            time=_format_relative_time(lead.created_at),
            created_at=lead.created_at,
        ))

    # Get recent reviews
    reviews_result = await db.execute(
        select(Review)
        .where(Review.reviewed_professional_id == profile.id)
        .order_by(Review.created_at.desc())
        .limit(limit)
    )
    for review in reviews_result.scalars():
        stars = int(review.overall_rating) if review.overall_rating else 0
        activities.append(RecentActivityItem(
            id=str(review.id),
            type="review",
            title=f"New {stars}-star review",
            description=f'"{review.content[:50]}..."' if review.content and len(review.content) > 50 else (review.content or "No comment"),
            time=_format_relative_time(review.created_at),
            created_at=review.created_at,
        ))

    # Sort all activities by created_at and limit
    activities.sort(key=lambda x: x.created_at, reverse=True)
    activities = activities[:limit]

    return RecentActivityResponse(activities=activities)


def _format_relative_time(dt: datetime) -> str:
    """Format a datetime as a relative time string."""
    if not dt:
        return "Unknown"
    now = datetime.utcnow()
    diff = now - dt

    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.days < 7:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    else:
        return dt.strftime("%b %d, %Y")


@router.get("/dashboard", response_model=AnalyticsDashboard)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_analytics_dashboard(
    request: Request,
    period: str = Query("30d", pattern="^(7d|30d|90d|12m)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the full analytics dashboard."""
    profile = await get_professional_profile(user, db)

    # Calculate date range
    end_date = date.today()
    if period == "7d":
        start_date = end_date - timedelta(days=7)
    elif period == "30d":
        start_date = end_date - timedelta(days=30)
    elif period == "90d":
        start_date = end_date - timedelta(days=90)
    else:  # 12m
        start_date = end_date - timedelta(days=365)

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # Gather all analytics
    performance = await _get_performance_metrics(profile.id, start_datetime, end_datetime, db)
    calls = await _get_call_analytics(profile.id, start_datetime, end_datetime, db)
    ratings = await _get_rating_analytics(profile.id, start_datetime, end_datetime, db)
    leads = await _get_lead_analytics(profile.id, start_datetime, end_datetime, db)
    billing = await _get_billing_analytics(profile.id, start_datetime, end_datetime, db)
    grid = await _get_grid_analytics(profile.id, db)

    # Generate insights
    insights = _generate_insights(performance, calls, ratings, leads)
    recommendations = _generate_recommendations(performance, calls, ratings, leads, grid)

    return AnalyticsDashboard(
        period_start=start_date,
        period_end=end_date,
        performance=performance,
        calls=calls,
        ratings=ratings,
        leads=leads,
        billing=billing,
        grid=grid,
        insights=insights,
        recommendations=recommendations,
    )


@router.get("/performance", response_model=PerformanceMetrics)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_performance_metrics(
    request: Request,
    period: str = Query("30d", pattern="^(7d|30d|90d|12m)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get performance metrics."""
    profile = await get_professional_profile(user, db)

    end_date = date.today()
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}[period]
    start_date = end_date - timedelta(days=days)

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    return await _get_performance_metrics(profile.id, start_datetime, end_datetime, db)


async def _get_performance_metrics(
    professional_id: uuid.UUID,
    start: datetime,
    end: datetime,
    db: AsyncSession,
) -> PerformanceMetrics:
    """Calculate performance metrics."""
    # Call metrics
    call_result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(VideoCall.status == CallStatus.COMPLETED).label("completed"),
            func.count().filter(VideoCall.status == CallStatus.MISSED).label("missed"),
            func.avg(VideoCall.duration_seconds).filter(VideoCall.status == CallStatus.COMPLETED).label("avg_duration"),
            func.avg(VideoCall.pickup_time_seconds).filter(VideoCall.status == CallStatus.COMPLETED).label("avg_pickup"),
        )
        .where(VideoCall.professional_id == professional_id)
        .where(VideoCall.initiated_at.between(start, end))
    )
    call_stats = call_result.one()

    # Rating metrics
    rating_result = await db.execute(
        select(
            func.count().label("total"),
            func.avg(Review.overall_rating).label("avg"),
            func.count().filter(Review.overall_rating == 5).label("five_star"),
        )
        .where(Review.reviewed_professional_id == professional_id)
        .where(Review.created_at.between(start, end))
    )
    rating_stats = rating_result.one()

    # Lead metrics
    lead_result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(Lead.lead_status == LeadStatus.WON.value).label("converted"),
        )
        .where(Lead.professional_id == professional_id)
        .where(Lead.created_at.between(start, end))
    )
    lead_stats = lead_result.one()

    conversion_rate = 0.0
    if lead_stats.total > 0:
        conversion_rate = (lead_stats.converted / lead_stats.total) * 100

    return PerformanceMetrics(
        total_calls=call_stats.total or 0,
        completed_calls=call_stats.completed or 0,
        missed_calls=call_stats.missed or 0,
        avg_call_duration_seconds=float(call_stats.avg_duration or 0),
        avg_pickup_time_seconds=float(call_stats.avg_pickup or 0),
        total_reviews=rating_stats.total or 0,
        avg_rating=float(rating_stats.avg or 0),
        five_star_count=rating_stats.five_star or 0,
        total_leads_generated=lead_stats.total or 0,
        leads_converted=lead_stats.converted or 0,
        conversion_rate=round(conversion_rate, 1),
    )


async def _get_call_analytics(
    professional_id: uuid.UUID,
    start: datetime,
    end: datetime,
    db: AsyncSession,
) -> CallAnalytics:
    """Get detailed call analytics."""
    # Calls by day
    daily_result = await db.execute(
        select(
            func.date(VideoCall.initiated_at).label("day"),
            func.count().label("count"),
        )
        .where(VideoCall.professional_id == professional_id)
        .where(VideoCall.initiated_at.between(start, end))
        .group_by(func.date(VideoCall.initiated_at))
        .order_by(func.date(VideoCall.initiated_at))
    )
    calls_by_day = [
        TimeSeriesPoint(date=row.day, value=row.count)
        for row in daily_result.all()
    ]

    # Calls by hour
    hourly_result = await db.execute(
        select(
            extract("hour", VideoCall.initiated_at).label("hour"),
            func.count().label("count"),
        )
        .where(VideoCall.professional_id == professional_id)
        .where(VideoCall.initiated_at.between(start, end))
        .group_by(extract("hour", VideoCall.initiated_at))
    )
    calls_by_hour = {int(row.hour): row.count for row in hourly_result.all()}

    # Find busiest hour
    busiest_hour = None
    if calls_by_hour:
        busiest_hour = max(calls_by_hour, key=calls_by_hour.get)

    # Calls by day of week
    dow_result = await db.execute(
        select(
            extract("dow", VideoCall.initiated_at).label("dow"),
            func.count().label("count"),
        )
        .where(VideoCall.professional_id == professional_id)
        .where(VideoCall.initiated_at.between(start, end))
        .group_by(extract("dow", VideoCall.initiated_at))
    )

    dow_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    calls_by_dow = {dow_names[int(row.dow)]: row.count for row in dow_result.all()}

    busiest_day = None
    if calls_by_dow:
        busiest_day = max(calls_by_dow, key=calls_by_dow.get)

    return CallAnalytics(
        calls_by_day=calls_by_day,
        calls_by_hour=calls_by_hour,
        calls_by_day_of_week=calls_by_dow,
        busiest_hour=busiest_hour,
        busiest_day=busiest_day,
    )


async def _get_rating_analytics(
    professional_id: uuid.UUID,
    start: datetime,
    end: datetime,
    db: AsyncSession,
) -> RatingAnalytics:
    """Get detailed rating analytics."""
    # Rating distribution
    dist_result = await db.execute(
        select(
            Review.overall_rating.label("rating"),
            func.count().label("count"),
        )
        .where(Review.reviewed_professional_id == professional_id)
        .where(Review.created_at.between(start, end))
        .group_by(Review.overall_rating)
    )
    rating_distribution = {row.rating: row.count for row in dist_result.all()}

    # Ratings over time
    daily_result = await db.execute(
        select(
            func.date(Review.created_at).label("day"),
            func.avg(Review.overall_rating).label("avg_rating"),
        )
        .where(Review.reviewed_professional_id == professional_id)
        .where(Review.created_at.between(start, end))
        .group_by(func.date(Review.created_at))
        .order_by(func.date(Review.created_at))
    )
    ratings_over_time = [
        TimeSeriesPoint(date=row.day, value=float(row.avg_rating))
        for row in daily_result.all()
    ]

    # Recent reviews
    recent_result = await db.execute(
        select(Review)
        .where(Review.reviewed_professional_id == professional_id)
        .order_by(Review.created_at.desc())
        .limit(5)
    )
    recent_reviews = [
        {
            "rating": r.overall_rating,
            "content": r.content,
            "created_at": r.created_at.isoformat(),
        }
        for r in recent_result.scalars().all()
    ]

    return RatingAnalytics(
        rating_distribution=rating_distribution,
        ratings_over_time=ratings_over_time,
        recent_reviews=recent_reviews,
    )


async def _get_lead_analytics(
    professional_id: uuid.UUID,
    start: datetime,
    end: datetime,
    db: AsyncSession,
) -> LeadAnalytics:
    """Get lead analytics."""
    # Leads by status
    status_result = await db.execute(
        select(
            Lead.lead_status.label("status"),
            func.count().label("count"),
        )
        .where(Lead.professional_id == professional_id)
        .where(Lead.created_at.between(start, end))
        .group_by(Lead.lead_status)
    )
    leads_by_status = {str(row.status): row.count for row in status_result.all()}

    # Leads by day
    daily_result = await db.execute(
        select(
            func.date(Lead.created_at).label("day"),
            func.count().label("count"),
        )
        .where(Lead.professional_id == professional_id)
        .where(Lead.created_at.between(start, end))
        .group_by(func.date(Lead.created_at))
        .order_by(func.date(Lead.created_at))
    )
    leads_by_day = [
        TimeSeriesPoint(date=row.day, value=row.count)
        for row in daily_result.all()
    ]

    # Pipeline value
    pipeline_result = await db.execute(
        select(func.coalesce(func.sum(Lead.estimated_value), 0))
        .where(Lead.professional_id == professional_id)
        .where(Lead.lead_status.notin_([LeadStatus.WON.value, LeadStatus.LOST.value]))
    )
    total_pipeline_value = pipeline_result.scalar() or 0

    return LeadAnalytics(
        leads_by_status=leads_by_status,
        leads_by_day=leads_by_day,
        total_pipeline_value=Decimal(str(total_pipeline_value)),
    )


async def _get_billing_analytics(
    professional_id: uuid.UUID,
    start: datetime,
    end: datetime,
    db: AsyncSession,
) -> BillingAnalytics:
    """Get billing analytics."""
    # Get subscription
    sub_result = await db.execute(
        select(Subscription)
        .where(Subscription.professional_id == professional_id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    subscription = sub_result.scalar_one_or_none()

    # Get wallet
    wallet_result = await db.execute(
        select(BidWallet).where(BidWallet.professional_id == professional_id)
    )
    wallet = wallet_result.scalar_one_or_none()

    # Spending this month
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spending_result = await db.execute(
        select(func.coalesce(func.sum(BidTransaction.amount), 0))
        .join(BidWallet)
        .where(BidWallet.professional_id == professional_id)
        .where(BidTransaction.transaction_type == "charge")
        .where(BidTransaction.created_at >= month_start)
    )
    total_bid_spend_month = spending_result.scalar() or 0

    return BillingAnalytics(
        current_subscription_tier=subscription.tier.value if subscription else "free",
        bid_wallet_balance=wallet.available_credits if wallet else Decimal("0"),
        total_bid_spend_month=Decimal(str(total_bid_spend_month)),
    )


async def _get_grid_analytics(
    professional_id: uuid.UUID,
    db: AsyncSession,
) -> GridAnalytics:
    """Get grid positioning analytics from GridImpression table."""
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Get today's stats (impressions, clicks, position)
    today_result = await db.execute(
        select(
            func.coalesce(func.sum(GridImpression.impressions_count), 0).label("impressions"),
            func.coalesce(func.sum(GridImpression.clicks_count), 0).label("clicks"),
            func.avg(GridImpression.avg_position).label("avg_position"),
        )
        .where(GridImpression.professional_id == professional_id)
        .where(GridImpression.date == today)
    )
    today_stats = today_result.one()
    impressions_today = today_stats.impressions or 0
    clicks_today = today_stats.clicks or 0
    avg_position_today = float(today_stats.avg_position) if today_stats.avg_position else None

    # Get this week's stats
    week_result = await db.execute(
        select(
            func.coalesce(func.sum(GridImpression.impressions_count), 0).label("impressions"),
            func.coalesce(func.sum(GridImpression.clicks_count), 0).label("clicks"),
            func.avg(GridImpression.avg_position).label("avg_position"),
        )
        .where(GridImpression.professional_id == professional_id)
        .where(GridImpression.date >= week_ago)
    )
    week_stats = week_result.one()
    impressions_week = week_stats.impressions or 0
    clicks_week = week_stats.clicks or 0
    avg_position_week = float(week_stats.avg_position) if week_stats.avg_position else None

    # Get this month's impressions
    month_result = await db.execute(
        select(func.coalesce(func.sum(GridImpression.impressions_count), 0))
        .where(GridImpression.professional_id == professional_id)
        .where(GridImpression.date >= month_ago)
    )
    impressions_month = month_result.scalar() or 0

    # Get current grid position (most recent average)
    position_result = await db.execute(
        select(GridImpression.avg_position)
        .where(GridImpression.professional_id == professional_id)
        .where(GridImpression.date == today)
    )
    current_position = position_result.scalar()

    # Get position history for the last 30 days
    position_history_result = await db.execute(
        select(GridImpression.date, GridImpression.avg_position)
        .where(GridImpression.professional_id == professional_id)
        .where(GridImpression.date >= month_ago)
        .where(GridImpression.avg_position.isnot(None))
        .order_by(GridImpression.date)
    )
    position_history = [
        TimeSeriesPoint(date=row.date, value=float(row.avg_position))
        for row in position_history_result.all()
    ]

    # Calculate click-through rate (clicks / impressions * 100)
    click_through_rate = 0.0
    if impressions_week > 0:
        click_through_rate = round((clicks_week / impressions_week) * 100, 2)

    return GridAnalytics(
        current_position=current_position,
        avg_position_today=avg_position_today,
        avg_position_week=avg_position_week,
        position_history=position_history,
        impressions_today=impressions_today,
        impressions_week=impressions_week,
        impressions_month=impressions_month,
        click_through_rate=click_through_rate,
    )


def _generate_insights(
    performance: PerformanceMetrics,
    calls: CallAnalytics,
    ratings: RatingAnalytics,
    leads: LeadAnalytics,
) -> list[str]:
    """Generate insights based on analytics data."""
    insights = []

    if performance.avg_rating >= 4.5:
        insights.append(f"Your {performance.avg_rating:.1f} star rating is excellent! Keep up the great work.")
    elif performance.avg_rating < 4.0 and performance.total_reviews > 5:
        insights.append("Your rating is below 4 stars. Consider improving response time and service quality.")

    if performance.avg_pickup_time_seconds > 15:
        insights.append(f"Average pickup time of {performance.avg_pickup_time_seconds:.0f}s could be improved. Aim for under 10 seconds.")

    if calls.busiest_hour is not None:
        insights.append(f"Your busiest hour is {calls.busiest_hour}:00. Consider being online during this time.")

    if performance.conversion_rate > 20:
        insights.append(f"Your {performance.conversion_rate:.0f}% lead conversion rate is above average!")

    return insights


def _generate_recommendations(
    performance: PerformanceMetrics,
    calls: CallAnalytics,
    ratings: RatingAnalytics,
    leads: LeadAnalytics,
    grid: GridAnalytics,
) -> list[str]:
    """Generate recommendations based on analytics."""
    recommendations = []

    if performance.missed_calls > performance.completed_calls * 0.2:
        recommendations.append("Consider extending your online hours to reduce missed calls.")

    if performance.total_reviews < 10:
        recommendations.append("Ask satisfied clients to leave reviews to build credibility.")

    if grid.impressions_today == 0:
        recommendations.append("Increase your bid amount or subscription tier for more visibility.")

    if performance.avg_pickup_time_seconds > 12:
        recommendations.append("Enable notifications to answer calls faster and improve pickup time.")

    return recommendations
