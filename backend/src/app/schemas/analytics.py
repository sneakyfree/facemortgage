"""
Pydantic schemas for professional analytics.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel


class TimeSeriesPoint(BaseModel):
    """A single point in a time series."""
    date: date
    value: float


class PerformanceMetrics(BaseModel):
    """Core performance metrics for a professional."""
    # Call metrics
    total_calls: int = 0
    completed_calls: int = 0
    missed_calls: int = 0
    avg_call_duration_seconds: float = 0.0
    avg_pickup_time_seconds: float = 0.0

    # Rating metrics
    total_reviews: int = 0
    avg_rating: float = 0.0
    five_star_count: int = 0
    rating_trend: float = 0.0  # Change from previous period

    # Time online
    total_online_hours: float = 0.0
    avg_daily_online_hours: float = 0.0

    # Conversion
    total_leads_generated: int = 0
    leads_converted: int = 0
    conversion_rate: float = 0.0


class CallAnalytics(BaseModel):
    """Detailed call analytics."""
    calls_by_day: List[TimeSeriesPoint] = []
    calls_by_hour: dict[int, int] = {}  # Hour -> count
    calls_by_day_of_week: dict[str, int] = {}  # Mon, Tue, etc.

    avg_duration_by_day: List[TimeSeriesPoint] = []
    pickup_time_trend: List[TimeSeriesPoint] = []

    busiest_hour: Optional[int] = None
    busiest_day: Optional[str] = None


class RatingAnalytics(BaseModel):
    """Detailed rating analytics."""
    rating_distribution: dict[int, int] = {}  # 1-5 -> count
    ratings_over_time: List[TimeSeriesPoint] = []
    avg_rating_by_month: List[TimeSeriesPoint] = []

    recent_reviews: List[dict] = []  # Last 5 reviews


class LeadAnalytics(BaseModel):
    """Lead conversion analytics."""
    leads_by_status: dict[str, int] = {}
    leads_by_source: dict[str, int] = {}  # call, organic, referral

    leads_by_day: List[TimeSeriesPoint] = []
    conversion_by_month: List[TimeSeriesPoint] = []

    avg_lead_value: Decimal = Decimal("0")
    total_pipeline_value: Decimal = Decimal("0")


class BillingAnalytics(BaseModel):
    """Billing and spending analytics."""
    current_subscription_tier: str = "free"
    subscription_cost_monthly: Decimal = Decimal("0")

    bid_wallet_balance: Decimal = Decimal("0")
    total_bid_spend_month: Decimal = Decimal("0")
    avg_cost_per_lead: Decimal = Decimal("0")

    spending_by_day: List[TimeSeriesPoint] = []


class GridAnalytics(BaseModel):
    """Grid positioning analytics."""
    current_position: Optional[int] = None
    avg_position_today: Optional[float] = None
    avg_position_week: Optional[float] = None

    position_history: List[TimeSeriesPoint] = []

    impressions_today: int = 0
    impressions_week: int = 0
    impressions_month: int = 0

    click_through_rate: float = 0.0


class ComparisonMetrics(BaseModel):
    """Comparison with peers."""
    your_value: float
    avg_value: float
    percentile: int  # 0-100
    trend: str  # 'up', 'down', 'stable'


class PeerComparison(BaseModel):
    """Comparison with other professionals."""
    rating_comparison: ComparisonMetrics
    pickup_time_comparison: ComparisonMetrics
    calls_comparison: ComparisonMetrics
    conversion_comparison: ComparisonMetrics


class AnalyticsDashboard(BaseModel):
    """Complete analytics dashboard data."""
    period_start: date
    period_end: date

    performance: PerformanceMetrics
    calls: CallAnalytics
    ratings: RatingAnalytics
    leads: LeadAnalytics
    billing: BillingAnalytics
    grid: GridAnalytics
    peer_comparison: Optional[PeerComparison] = None

    # Insights
    insights: List[str] = []
    recommendations: List[str] = []
