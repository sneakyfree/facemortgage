"""
Metrics Service for TimescaleDB

Handles recording and querying time-series metrics from the 
dedicated TimescaleDB instance.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.app.config import settings
from src.app.models.metrics import (
    MetricsBase, CallMetric, GridViewMetric, 
    LeadMetric, BillingMetric, SystemMetric
)

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service for recording and querying time-series metrics.
    
    Uses TimescaleDB for efficient time-series storage and queries.
    Falls back to logging if TimescaleDB is not available.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the metrics service with a database connection."""
        self.database_url = database_url or getattr(settings, 'TIMESCALE_DATABASE_URL', None)
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize database connection and create tables if needed."""
        if self._initialized:
            return
            
        if not self.database_url:
            logger.warning("TimescaleDB URL not configured, metrics will be logged only")
            return
            
        try:
            # Create async engine for TimescaleDB
            self.async_engine = create_async_engine(
                self.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
                poolclass=NullPool,
            )
            
            # Create sync engine for table creation
            sync_url = self.database_url
            self.engine = create_engine(sync_url)
            
            # Create tables
            MetricsBase.metadata.create_all(self.engine)
            
            # Create hypertables (TimescaleDB specific)
            await self._create_hypertables()
            
            self.session_factory = sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("MetricsService initialized with TimescaleDB")
            
        except Exception as e:
            logger.error(f"Failed to initialize MetricsService: {e}")
            self._initialized = False
            
    async def _create_hypertables(self):
        """Create TimescaleDB hypertables if they don't exist."""
        if not self.async_engine:
            return
            
        hypertable_configs = [
            ('call_metrics', 'timestamp', '1 day'),
            ('grid_view_metrics', 'timestamp', '1 day'),
            ('lead_metrics', 'timestamp', '1 day'),
            ('billing_metrics', 'timestamp', '1 week'),
            ('system_metrics', 'timestamp', '1 hour'),
        ]
        
        async with self.async_engine.begin() as conn:
            for table_name, time_column, chunk_interval in hypertable_configs:
                try:
                    # Check if already a hypertable
                    result = await conn.execute(text(f"""
                        SELECT EXISTS (
                            SELECT 1 FROM timescaledb_information.hypertables 
                            WHERE hypertable_name = '{table_name}'
                        )
                    """))
                    is_hypertable = result.scalar()
                    
                    if not is_hypertable:
                        await conn.execute(text(f"""
                            SELECT create_hypertable(
                                '{table_name}', 
                                '{time_column}',
                                chunk_time_interval => INTERVAL '{chunk_interval}',
                                if_not_exists => TRUE
                            )
                        """))
                        logger.info(f"Created hypertable: {table_name}")
                        
                except Exception as e:
                    logger.warning(f"Could not create hypertable {table_name}: {e}")
                    
    async def record_call(
        self,
        professional_id: UUID,
        duration_seconds: int,
        was_answered: bool = True,
        was_completed: bool = True,
        rating: Optional[float] = None,
        source: Optional[str] = None,
        partner_id: Optional[str] = None,
        call_id: Optional[UUID] = None,
        ring_time_seconds: Optional[float] = None,
        borrower_session_id: Optional[str] = None,
    ):
        """Record a call metric."""
        metric = CallMetric(
            timestamp=datetime.utcnow(),
            professional_id=professional_id,
            duration_seconds=duration_seconds,
            was_answered=was_answered,
            was_completed=was_completed,
            rating=rating,
            source=source,
            partner_id=partner_id,
            call_id=call_id,
            ring_time_seconds=ring_time_seconds,
            borrower_session_id=borrower_session_id,
        )
        await self._record(metric)
        
    async def record_grid_event(
        self,
        professional_id: UUID,
        event_type: str,
        grid_position: Optional[int] = None,
        total_results: Optional[int] = None,
        session_id: Optional[str] = None,
        state_filter: Optional[str] = None,
        specialty_filter: Optional[str] = None,
        partner_id: Optional[str] = None,
    ):
        """Record a grid impression, click, or profile view."""
        metric = GridViewMetric(
            timestamp=datetime.utcnow(),
            professional_id=professional_id,
            event_type=event_type,
            grid_position=grid_position,
            total_results=total_results,
            session_id=session_id,
            state_filter=state_filter,
            specialty_filter=specialty_filter,
            partner_id=partner_id,
        )
        await self._record(metric)
        
    async def record_lead_event(
        self,
        professional_id: UUID,
        status: str,
        lead_id: Optional[UUID] = None,
        previous_status: Optional[str] = None,
        days_in_funnel: Optional[int] = None,
        estimated_loan_amount: Optional[float] = None,
        source: Optional[str] = None,
        partner_id: Optional[str] = None,
    ):
        """Record a lead status change."""
        metric = LeadMetric(
            timestamp=datetime.utcnow(),
            professional_id=professional_id,
            status=status,
            lead_id=lead_id,
            previous_status=previous_status,
            days_in_funnel=days_in_funnel,
            estimated_loan_amount=estimated_loan_amount,
            source=source,
            partner_id=partner_id,
        )
        await self._record(metric)
        
    async def record_billing_event(
        self,
        professional_id: UUID,
        transaction_type: str,
        amount_cents: int,
        currency: str = 'USD',
        subscription_tier: Optional[str] = None,
        bid_type: Optional[str] = None,
    ):
        """Record a billing transaction."""
        metric = BillingMetric(
            timestamp=datetime.utcnow(),
            professional_id=professional_id,
            transaction_type=transaction_type,
            amount_cents=amount_cents,
            currency=currency,
            subscription_tier=subscription_tier,
            bid_type=bid_type,
        )
        await self._record(metric)
        
    async def record_system_metric(
        self,
        metric_name: str,
        metric_value: float,
        dimension_1: Optional[str] = None,
        dimension_2: Optional[str] = None,
    ):
        """Record a system performance metric."""
        metric = SystemMetric(
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            metric_value=metric_value,
            dimension_1=dimension_1,
            dimension_2=dimension_2,
        )
        await self._record(metric)
        
    async def _record(self, metric):
        """Internal method to record a metric."""
        if not self._initialized or not self.session_factory:
            # Log-only fallback
            logger.info(f"Metric: {type(metric).__name__} - {metric.__dict__}")
            return
            
        try:
            async with self.session_factory() as session:
                session.add(metric)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            
    # Query methods
    
    async def get_call_stats(
        self,
        professional_id: UUID,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        bucket_interval: str = '1 hour',
    ) -> List[Dict[str, Any]]:
        """Get aggregated call stats by time bucket."""
        if not self._initialized:
            return []
            
        end_time = end_time or datetime.utcnow()
        
        query = text(f"""
            SELECT 
                time_bucket('{bucket_interval}', timestamp) as bucket,
                COUNT(*) as total_calls,
                COUNT(*) FILTER (WHERE was_answered) as answered_calls,
                AVG(duration_seconds) as avg_duration,
                AVG(rating) FILTER (WHERE rating IS NOT NULL) as avg_rating
            FROM call_metrics
            WHERE professional_id = :professional_id
              AND timestamp >= :start_time
              AND timestamp <= :end_time
            GROUP BY bucket
            ORDER BY bucket
        """)
        
        async with self.session_factory() as session:
            result = await session.execute(
                query,
                {
                    'professional_id': professional_id,
                    'start_time': start_time,
                    'end_time': end_time,
                }
            )
            return [dict(row._mapping) for row in result.fetchall()]
            
    async def get_grid_performance(
        self,
        professional_id: UUID,
        start_time: datetime,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get grid performance metrics (impressions, clicks, CTR)."""
        if not self._initialized:
            return {}
            
        end_time = end_time or datetime.utcnow()
        
        query = text("""
            SELECT 
                COUNT(*) FILTER (WHERE event_type = 'impression') as impressions,
                COUNT(*) FILTER (WHERE event_type = 'click') as clicks,
                COUNT(*) FILTER (WHERE event_type = 'profile_view') as profile_views,
                AVG(grid_position) FILTER (WHERE event_type = 'impression') as avg_position
            FROM grid_view_metrics
            WHERE professional_id = :professional_id
              AND timestamp >= :start_time
              AND timestamp <= :end_time
        """)
        
        async with self.session_factory() as session:
            result = await session.execute(
                query,
                {
                    'professional_id': professional_id,
                    'start_time': start_time,
                    'end_time': end_time,
                }
            )
            row = result.fetchone()
            if row:
                data = dict(row._mapping)
                impressions = data.get('impressions', 0) or 0
                clicks = data.get('clicks', 0) or 0
                data['ctr'] = (clicks / impressions * 100) if impressions > 0 else 0
                return data
            return {}
            
    async def get_lead_funnel(
        self,
        professional_id: UUID,
        start_time: datetime,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """Get lead funnel metrics by status."""
        if not self._initialized:
            return {}
            
        end_time = end_time or datetime.utcnow()
        
        query = text("""
            SELECT status, COUNT(DISTINCT lead_id) as count
            FROM lead_metrics
            WHERE professional_id = :professional_id
              AND timestamp >= :start_time
              AND timestamp <= :end_time
            GROUP BY status
        """)
        
        async with self.session_factory() as session:
            result = await session.execute(
                query,
                {
                    'professional_id': professional_id,
                    'start_time': start_time,
                    'end_time': end_time,
                }
            )
            return {row.status: row.count for row in result.fetchall()}


# Singleton instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get the metrics service singleton."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service
