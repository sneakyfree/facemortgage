"""
Query Optimization Utilities for FaceMortgage.

Provides optimized query patterns for common operations:
- Eager loading configurations
- Batch fetching
- Query result limiting
- Index usage helpers
"""

import logging
from typing import Optional, Sequence, TypeVar
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.professional import (
    ProfessionalProfile, 
    ProfessionalStatus,
    ProfessionalSpecialty,
    ProfessionalLanguage,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class OptimizedQueries:
    """
    Collection of optimized query patterns.
    
    Uses eager loading to prevent N+1 queries and
    includes commonly needed relations.
    """
    
    # ==================== Professional Queries ====================
    
    @staticmethod
    def professional_with_relations():
        """
        Base query for professional with all commonly needed relations.
        
        Prevents N+1 queries by eager loading:
        - User (name, email, avatar)
        - Specialties
        - Languages
        """
        return (
            select(ProfessionalProfile)
            .options(
                joinedload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.specialties)
                    .joinedload(ProfessionalSpecialty.specialty),
                selectinload(ProfessionalProfile.languages)
                    .joinedload(ProfessionalLanguage.language),
            )
        )
    
    @staticmethod
    async def get_professional_by_id(
        db: AsyncSession,
        professional_id: UUID,
    ) -> Optional[ProfessionalProfile]:
        """Get single professional with all relations."""
        query = (
            OptimizedQueries.professional_with_relations()
            .where(ProfessionalProfile.id == professional_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_online_professionals(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ProfessionalProfile]:
        """Get online professionals with optimized loading."""
        query = (
            OptimizedQueries.professional_with_relations()
            .where(ProfessionalProfile.status.in_([
                ProfessionalStatus.ONLINE_AVAILABLE,
                ProfessionalStatus.ONLINE_BUSY,
            ]))
            .where(ProfessionalProfile.profile_complete == True)
            .order_by(ProfessionalProfile.avg_rating.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_professionals_by_state(
        db: AsyncSession,
        state: str,
        limit: int = 50,
    ) -> Sequence[ProfessionalProfile]:
        """
        Get professionals licensed in a state.
        
        Note: Actual implementation would join with service_areas.
        This is a simplified version for demonstration.
        """
        query = (
            OptimizedQueries.professional_with_relations()
            .where(ProfessionalProfile.profile_complete == True)
            .order_by(
                # Prioritize: online > rating > pickup time
                ProfessionalProfile.status == ProfessionalStatus.ONLINE_AVAILABLE,
                ProfessionalProfile.avg_rating.desc(),
                ProfessionalProfile.avg_pickup_time_seconds.asc(),
            )
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    # ==================== Batch Operations ====================
    
    @staticmethod
    async def get_professionals_batch(
        db: AsyncSession,
        professional_ids: list[UUID],
    ) -> Sequence[ProfessionalProfile]:
        """
        Get multiple professionals in single query.
        
        More efficient than individual fetches for comparison features.
        """
        if not professional_ids:
            return []
        
        query = (
            OptimizedQueries.professional_with_relations()
            .where(ProfessionalProfile.id.in_(professional_ids))
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    # ==================== Aggregation Queries ====================
    
    @staticmethod
    async def get_grid_stats(db: AsyncSession) -> dict:
        """
        Get aggregated grid statistics in single query.
        
        Returns counts for dashboard display.
        """
        stats_query = select(
            func.count(ProfessionalProfile.id).label('total'),
            func.count(ProfessionalProfile.id).filter(
                ProfessionalProfile.status == ProfessionalStatus.ONLINE_AVAILABLE
            ).label('online'),
            func.avg(ProfessionalProfile.avg_rating).label('avg_rating'),
            func.avg(ProfessionalProfile.avg_pickup_time_seconds).label('avg_pickup'),
        ).where(ProfessionalProfile.profile_complete == True)
        
        result = await db.execute(stats_query)
        row = result.one()
        
        return {
            'total_professionals': row.total,
            'online_now': row.online,
            'avg_rating': float(row.avg_rating or 0),
            'avg_pickup_seconds': float(row.avg_pickup or 0),
        }


class QueryPerformanceMonitor:
    """
    Monitor query performance for optimization.
    
    Logs slow queries and tracks execution patterns.
    """
    
    SLOW_QUERY_THRESHOLD_MS = 100
    
    @staticmethod
    def log_query_time(query_name: str, duration_ms: float):
        """Log query execution time."""
        if duration_ms > QueryPerformanceMonitor.SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                f"SLOW QUERY: {query_name} took {duration_ms:.1f}ms "
                f"(threshold: {QueryPerformanceMonitor.SLOW_QUERY_THRESHOLD_MS}ms)"
            )
        else:
            logger.debug(f"Query {query_name}: {duration_ms:.1f}ms")


# ==================== Database Index Recommendations ====================

DATABASE_INDEX_RECOMMENDATIONS = """
-- Recommended indexes for FaceMortgage performance

-- Professional Grid Queries
CREATE INDEX IF NOT EXISTS idx_professional_status 
    ON professional_profiles(status) 
    WHERE profile_complete = true;

CREATE INDEX IF NOT EXISTS idx_professional_rating 
    ON professional_profiles(avg_rating DESC) 
    WHERE profile_complete = true;

CREATE INDEX IF NOT EXISTS idx_professional_pickup 
    ON professional_profiles(avg_pickup_time_seconds ASC NULLS LAST);

-- Matching Queries
CREATE INDEX IF NOT EXISTS idx_professional_nmls_verified 
    ON professional_profiles(nmls_verified) 
    WHERE nmls_verified = true;

-- Call Queries
CREATE INDEX IF NOT EXISTS idx_calls_professional 
    ON video_calls(professional_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_calls_borrower 
    ON video_calls(borrower_id, created_at DESC);

-- Lead Queries
CREATE INDEX IF NOT EXISTS idx_leads_professional 
    ON leads(professional_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_leads_status 
    ON leads(status, created_at DESC);
"""
