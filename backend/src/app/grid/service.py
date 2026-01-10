"""
Optimized grid service with caching and efficient queries.

Provides fast grid retrieval for the professional listing page.
"""
import json
from datetime import timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from dataclasses import asdict

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from src.app.core.cache import CacheService, get_redis
from src.app.models.professional import (
    ProfessionalProfile,
    ProfessionalStatus,
    ProfessionalSpecialty,
    ProfessionalLanguage,
    ProfessionalServiceArea,
)
from src.app.models.user import User
from src.app.grid.ranking import get_ranking_service, RankedProfessional
from src.app.config import settings


# Cache configuration
GRID_CACHE_TTL = timedelta(seconds=settings.grid_cache_ttl_seconds)
FILTER_CACHE_TTL = timedelta(seconds=settings.filter_cache_ttl_seconds)

grid_cache = CacheService("grid")


class GridService:
    """
    High-performance grid service with caching.

    Features:
    - Redis caching for grid results
    - Efficient batch queries
    - Real-time presence integration
    - Optimized for high concurrency
    """

    def __init__(self):
        self.ranking_service = get_ranking_service()

    async def get_grid(
        self,
        db: AsyncSession,
        filters: Dict[str, Any] = None,
        page: int = 1,
        page_size: int = 24,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Get paginated grid of professionals.

        Args:
            db: Database session
            filters: Filter criteria
            page: Page number (1-indexed)
            page_size: Items per page
            use_cache: Whether to use cache

        Returns:
            Dict with professionals list, total count, and metadata
        """
        filters = filters or {}
        cache_key = self._build_cache_key(filters, page, page_size)

        # Try cache first
        if use_cache:
            cached = await grid_cache.get(cache_key)
            if cached:
                # Update presence data from Redis
                await self._update_presence(cached.get("professionals", []))
                return cached

        # Build and execute query
        offset = (page - 1) * page_size

        # Get ranked professionals
        ranked = await self.ranking_service.get_ranked_professionals(
            db=db,
            filters=filters,
            limit=page_size,
            offset=offset,
            only_available=filters.get("only_available", True),
        )

        # Get total count for pagination
        total = await self._get_total_count(db, filters)

        # Fetch full professional data
        professionals = await self._hydrate_professionals(
            db, [r.professional_id for r in ranked], ranked
        )

        result = {
            "professionals": professionals,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "filters_applied": filters,
        }

        # Cache result
        if use_cache:
            await grid_cache.set(cache_key, result, GRID_CACHE_TTL)

        return result

    async def get_professional_detail(
        self,
        db: AsyncSession,
        professional_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed professional data for profile view."""
        cache_key = f"pro:{professional_id}"
        cached = await grid_cache.get(cache_key)
        if cached:
            return cached

        result = await db.execute(
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.specialties).selectinload(ProfessionalSpecialty.specialty),
                selectinload(ProfessionalProfile.languages).selectinload(ProfessionalLanguage.language),
                selectinload(ProfessionalProfile.service_areas).selectinload(ProfessionalServiceArea.county),
            )
            .where(ProfessionalProfile.id == professional_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return None

        data = self._serialize_professional_detail(profile)
        await grid_cache.set(cache_key, data, timedelta(minutes=5))
        return data

    async def invalidate_professional_cache(self, professional_id: UUID):
        """Invalidate cache for a specific professional."""
        await grid_cache.delete(f"pro:{professional_id}")
        # Also invalidate grid pages (they'll rebuild on next request)
        await grid_cache.delete_pattern("grid:*")

    async def invalidate_grid_cache(self):
        """Invalidate all grid caches."""
        await grid_cache.delete_pattern("grid:*")

    def _build_cache_key(
        self,
        filters: Dict[str, Any],
        page: int,
        page_size: int,
    ) -> str:
        """Build cache key from filters and pagination."""
        filter_str = json.dumps(filters, sort_keys=True, default=str)
        return f"grid:{filter_str}:p{page}:s{page_size}"

    async def _get_total_count(
        self,
        db: AsyncSession,
        filters: Dict[str, Any],
    ) -> int:
        """Get total count of professionals matching filters."""
        query = (
            select(func.count())
            .select_from(ProfessionalProfile)
            .join(User)
            .where(User.is_active == True)
            .where(ProfessionalProfile.profile_complete == True)
        )

        if filters.get("only_available", True):
            query = query.where(
                ProfessionalProfile.status == ProfessionalStatus.ONLINE_AVAILABLE
            )

        if filters.get("user_type"):
            query = query.where(User.user_type == filters["user_type"])

        if filters.get("min_rating"):
            query = query.where(
                ProfessionalProfile.avg_rating >= filters["min_rating"]
            )

        result = await db.execute(query)
        return result.scalar() or 0

    async def _hydrate_professionals(
        self,
        db: AsyncSession,
        professional_ids: List[UUID],
        rankings: List[RankedProfessional],
    ) -> List[Dict[str, Any]]:
        """Fetch full professional data and merge with rankings."""
        if not professional_ids:
            return []

        # Batch query all professionals
        result = await db.execute(
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.specialties).selectinload(ProfessionalSpecialty.specialty),
                selectinload(ProfessionalProfile.languages).selectinload(ProfessionalLanguage.language),
            )
            .where(ProfessionalProfile.id.in_(professional_ids))
        )
        profiles = {p.id: p for p in result.scalars().all()}

        # Build ranking lookup
        ranking_lookup = {r.professional_id: r for r in rankings}

        # Merge data maintaining ranking order
        professionals = []
        for prof_id in professional_ids:
            profile = profiles.get(prof_id)
            ranking = ranking_lookup.get(prof_id)
            if profile and ranking:
                professionals.append(
                    self._serialize_professional_grid(profile, ranking)
                )

        return professionals

    def _serialize_professional_grid(
        self,
        profile: ProfessionalProfile,
        ranking: RankedProfessional,
    ) -> Dict[str, Any]:
        """Serialize professional for grid display."""
        return {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "first_name": profile.user.first_name,
            "last_name": profile.user.last_name,
            "avatar_url": profile.user.avatar_url,
            "user_type": profile.user.user_type.value if profile.user.user_type else None,
            "company_name": profile.company_name,
            "job_title": profile.job_title,
            "bio": profile.bio,
            "nmls_id": profile.nmls_id,
            "status": profile.status.value if profile.status else "offline",
            "subscription_tier": profile.subscription_tier.value if profile.subscription_tier else "free",
            "prerecorded_video_url": profile.prerecorded_video_url,
            "video_type": "live" if profile.status == ProfessionalStatus.ONLINE_AVAILABLE else "recorded",
            "avg_rating": float(profile.avg_rating) if profile.avg_rating else 0.0,
            "total_reviews": profile.total_reviews or 0,
            "avg_pickup_time_seconds": float(profile.avg_pickup_time_seconds) if profile.avg_pickup_time_seconds else None,
            "years_experience": profile.years_experience,
            "specialty_names": [
                ps.specialty.name for ps in (profile.specialties or [])
            ],
            "language_codes": [
                pl.language.code for pl in (profile.languages or [])
            ],
            "grid_position": ranking.position,
            "score": round(ranking.score, 4),
        }

    def _serialize_professional_detail(
        self,
        profile: ProfessionalProfile,
    ) -> Dict[str, Any]:
        """Serialize professional for detail view."""
        base = {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "first_name": profile.user.first_name,
            "last_name": profile.user.last_name,
            "email": profile.user.email,
            "phone": profile.user.phone,
            "avatar_url": profile.user.avatar_url,
            "user_type": profile.user.user_type.value if profile.user.user_type else None,
            "company_name": profile.company_name,
            "job_title": profile.job_title,
            "bio": profile.bio,
            "years_experience": profile.years_experience,
            "nmls_id": profile.nmls_id,
            "nmls_verified": profile.nmls_verified,
            "timezone": profile.timezone,
            "office_address": profile.office_address,
            "status": profile.status.value if profile.status else "offline",
            "subscription_tier": profile.subscription_tier.value if profile.subscription_tier else "free",
            "prerecorded_video_url": profile.prerecorded_video_url,
            "webcam_enabled": profile.webcam_enabled,
            "avg_rating": float(profile.avg_rating) if profile.avg_rating else 0.0,
            "total_reviews": profile.total_reviews or 0,
            "avg_pickup_time_seconds": float(profile.avg_pickup_time_seconds) if profile.avg_pickup_time_seconds else None,
            "total_calls_completed": profile.total_calls_completed or 0,
            "is_featured": profile.is_featured,
            "profile_complete": profile.profile_complete,
            "specialties": [
                {"id": ps.specialty_id, "name": ps.specialty.name, "category": ps.specialty.category}
                for ps in (profile.specialties or [])
            ],
            "languages": [
                {"code": pl.language.code, "name": pl.language.name, "proficiency": pl.proficiency}
                for pl in (profile.languages or [])
            ],
            "service_areas": [
                {"id": sa.county_id, "state": sa.county.state_code, "county": sa.county.county_name}
                for sa in (profile.service_areas or [])
            ],
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
        }
        return base

    async def _update_presence(self, professionals: List[Dict[str, Any]]):
        """Update real-time presence status from Redis."""
        if not professionals:
            return

        try:
            redis = await get_redis()
            user_ids = [p["user_id"] for p in professionals]

            # Batch fetch presence data
            pipe = redis.pipeline()
            for user_id in user_ids:
                pipe.hget("presence:status", user_id)
            statuses = await pipe.execute()

            # Update status in results
            for prof, status in zip(professionals, statuses):
                if status:
                    prof["status"] = status
                    prof["video_type"] = "live" if status == "online_available" else "recorded"
        except Exception as e:
            # Log the error but continue with cached status
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to update presence status from Redis: {e}")


# Singleton
_grid_service: Optional[GridService] = None


def get_grid_service() -> GridService:
    """Get grid service singleton."""
    global _grid_service
    if _grid_service is None:
        _grid_service = GridService()
    return _grid_service
