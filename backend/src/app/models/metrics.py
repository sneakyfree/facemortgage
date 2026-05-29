"""
TimescaleDB Metrics Models

Hypertables for efficient time-series data storage and querying.
These models are stored in a separate TimescaleDB database optimized
for time-series analytics.
"""
from uuid import uuid4
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, 
    Index, text
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base

# Separate base for metrics database
MetricsBase = declarative_base()


class CallMetric(MetricsBase):
    """
    Time-series metrics for individual calls.
    
    Stored as a hypertable with time-based partitioning.
    Optimized for queries like:
    - Calls per hour/day/week
    - Average call duration over time
    - Call quality trends
    """
    __tablename__ = "call_metrics"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Reference to main database (not FK due to separate DB)
    professional_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    borrower_session_id = Column(String(100), nullable=True)
    call_id = Column(PG_UUID(as_uuid=True), nullable=True)
    
    # Call metrics
    duration_seconds = Column(Integer, nullable=False, default=0)
    ring_time_seconds = Column(Float, nullable=True)
    was_answered = Column(Boolean, nullable=False, default=False)
    was_completed = Column(Boolean, nullable=False, default=False)
    
    # Quality metrics
    rating = Column(Float, nullable=True)  # 1-5 scale
    audio_quality_score = Column(Float, nullable=True)
    video_quality_score = Column(Float, nullable=True)
    
    # Source tracking
    source = Column(String(50), nullable=True)  # 'grid', 'embed', 'widget', 'scheduled'
    partner_id = Column(String(100), nullable=True)
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_call_metrics_professional_time', 'professional_id', 'timestamp'),
        Index('idx_call_metrics_time_bucket', text("time_bucket('1 hour', timestamp)")),
    )


class GridViewMetric(MetricsBase):
    """
    Time-series metrics for grid impressions and clicks.
    
    Captures every time a professional appears in search results
    and interaction data.
    """
    __tablename__ = "grid_view_metrics"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # References
    professional_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(String(100), nullable=True)
    
    # Event type
    event_type = Column(String(20), nullable=False)  # 'impression', 'click', 'profile_view'
    
    # Grid context
    grid_position = Column(Integer, nullable=True)  # Position in grid (1-based)
    total_results = Column(Integer, nullable=True)  # Total professionals in results
    
    # Filter context
    state_filter = Column(String(50), nullable=True)
    specialty_filter = Column(String(100), nullable=True)
    language_filter = Column(String(50), nullable=True)
    
    # Attribution
    partner_id = Column(String(100), nullable=True)
    referrer = Column(String(500), nullable=True)
    
    __table_args__ = (
        Index('idx_grid_metrics_professional_time', 'professional_id', 'timestamp'),
        Index('idx_grid_metrics_event_time', 'event_type', 'timestamp'),
    )


class LeadMetric(MetricsBase):
    """
    Time-series metrics for lead generation and conversion.
    """
    __tablename__ = "lead_metrics"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # References
    professional_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    lead_id = Column(PG_UUID(as_uuid=True), nullable=True)
    
    # Lead stage
    status = Column(String(50), nullable=False)  # 'new', 'contacted', 'qualified', 'converted', 'lost'
    previous_status = Column(String(50), nullable=True)
    
    # Conversion tracking
    days_in_funnel = Column(Integer, nullable=True)
    touch_count = Column(Integer, nullable=True)  # Number of interactions
    
    # Value metrics
    estimated_loan_amount = Column(Float, nullable=True)
    loan_purpose = Column(String(50), nullable=True)
    
    # Attribution
    source = Column(String(50), nullable=True)
    partner_id = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index('idx_lead_metrics_professional_time', 'professional_id', 'timestamp'),
        Index('idx_lead_metrics_status_time', 'status', 'timestamp'),
    )


class BillingMetric(MetricsBase):
    """
    Time-series metrics for billing and revenue.
    """
    __tablename__ = "billing_metrics"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # References
    professional_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    # Transaction type
    transaction_type = Column(String(50), nullable=False)  # 'subscription', 'bid', 'deposit', 'refund'
    
    # Amounts
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # Subscription context
    subscription_tier = Column(String(50), nullable=True)
    
    # Bid context
    bid_type = Column(String(50), nullable=True)  # 'grid_placement', 'featured', 'priority'
    
    __table_args__ = (
        Index('idx_billing_metrics_professional_time', 'professional_id', 'timestamp'),
        Index('idx_billing_metrics_type_time', 'transaction_type', 'timestamp'),
    )


class SystemMetric(MetricsBase):
    """
    System-wide metrics for monitoring and capacity planning.
    """
    __tablename__ = "system_metrics"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metric identification
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    
    # Optional dimensions
    dimension_1 = Column(String(100), nullable=True)  # e.g., 'endpoint', 'region'
    dimension_2 = Column(String(100), nullable=True)  # e.g., 'status_code', 'tier'
    
    __table_args__ = (
        Index('idx_system_metrics_name_time', 'metric_name', 'timestamp'),
    )
