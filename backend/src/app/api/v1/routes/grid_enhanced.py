"""
Enhanced Grid API with advanced filtering and baseball card stats.

Provides Phase 2 Core Experience features:
- Advanced multi-criteria filtering
- Baseball card stats endpoint
- Pickup time display helpers
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Request, Query, HTTPException, status
from pydantic import BaseModel, Field

from src.app.core.dependencies import DbSession
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.services.pickup_tracker import AdvancedFilterService, PickupTimeTracker
from src.app.services.baseball_card import BaseballCardService, BaseballCardStats

router = APIRouter()
logger = logging.getLogger(__name__)


class FilterRequest(BaseModel):
    """Request body for advanced grid filtering."""
    state: Optional[str] = Field(default=None, max_length=2)
    specialties: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    max_pickup_seconds: Optional[float] = Field(default=None, ge=0)
    nmls_verified_only: bool = False
    online_only: bool = False
    available_only: bool = False
    has_video: bool = False
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class GridFiltersMetadata(BaseModel):
    """Metadata about available filters for the UI."""
    specialties: dict
    languages: dict
    pickup_speed: dict
    min_rating: dict


@router.post("/filter")
@limiter.limit(RATE_LIMITS["api_read"])
async def filter_professionals(
    request: Request,
    body: FilterRequest,
    db: DbSession,
):
    """
    Filter professionals with advanced criteria.
    
    Supports filtering by:
    - State licensing
    - Specialties (FHA, VA, Jumbo, etc.)
    - Languages
    - Minimum rating
    - Maximum pickup time
    - NMLS verification status
    - Online/available status
    - Has video intro
    
    Returns list of matching professionals with pickup badges.
    """
    results = await AdvancedFilterService.filter_professionals(
        db,
        state=body.state,
        specialties=body.specialties,
        languages=body.languages,
        min_rating=body.min_rating,
        max_pickup_seconds=body.max_pickup_seconds,
        nmls_verified_only=body.nmls_verified_only,
        online_only=body.online_only,
        available_only=body.available_only,
        has_video=body.has_video,
        limit=body.limit,
        offset=body.offset,
    )
    
    return {
        "professionals": results,
        "count": len(results),
        "offset": body.offset,
        "limit": body.limit,
    }


@router.get("/filters")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_filter_options(request: Request):
    """
    Get available filter options for the UI.
    
    Returns metadata about all filterable fields including
    their options and display labels.
    """
    return AdvancedFilterService.get_available_filters()


@router.get("/card/{professional_id}", response_model=BaseballCardStats)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_baseball_card(
    request: Request,
    professional_id: UUID,
    db: DbSession,
):
    """
    Get baseball card stats for a professional.
    
    Returns comprehensive stats including:
    - NMLS verification status
    - Performance metrics (rating, reviews, calls)
    - Response metrics (pickup time, category)
    - Derived grades (overall, responsiveness, experience, rating)
    - Specializations and service areas
    
    Great for detailed profile views and comparison features.
    """
    card = await BaseballCardService.get_baseball_card(db, professional_id)
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found"
        )
    
    return card


@router.post("/compare")
@limiter.limit(RATE_LIMITS["api_read"])
async def compare_professionals(
    request: Request,
    professional_ids: list[UUID] = [],
    db: DbSession = None,
):
    """
    Compare multiple professionals side by side.
    
    Returns baseball cards for up to 5 professionals
    for easy comparison.
    """
    if len(professional_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 professionals can be compared"
        )
    
    if len(professional_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 professionals required for comparison"
        )
    
    cards = await BaseballCardService.get_comparison(db, professional_ids)
    
    return {
        "professionals": cards,
        "count": len(cards),
    }


@router.get("/pickup/{professional_id}")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_pickup_stats(
    request: Request,
    professional_id: UUID,
    db: DbSession,
):
    """
    Get detailed pickup time statistics for a professional.
    
    Returns:
    - Average pickup time in seconds
    - Human-readable display text
    - Category (instant, fast, quick, moderate, slower)
    - Badge info for UI display
    """
    stats = await PickupTimeTracker.get_pickup_stats(db, professional_id)
    
    badge = PickupTimeTracker.get_pickup_badge(stats.get("avg_seconds"))
    
    return {
        **stats,
        "badge": badge,
    }


@router.get("/online-now")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_online_professionals(
    request: Request,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Get professionals who are currently online and available.
    
    Quick endpoint for the "Available Now" section of the grid.
    """
    results = await AdvancedFilterService.filter_professionals(
        db,
        available_only=True,
        limit=limit,
    )
    
    return {
        "professionals": results,
        "count": len(results),
    }


@router.get("/featured")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_featured_professionals(
    request: Request,
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Get featured professionals for homepage display.
    
    Returns professionals marked as featured, sorted by rating.
    """
    from sqlalchemy import select
    from src.app.models.professional import ProfessionalProfile
    from sqlalchemy.orm import selectinload
    
    query = (
        select(ProfessionalProfile)
        .options(selectinload(ProfessionalProfile.user))
        .where(ProfessionalProfile.is_featured == True)
        .where(ProfessionalProfile.profile_complete == True)
        .order_by(ProfessionalProfile.avg_rating.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    profiles = result.scalars().all()
    
    featured = []
    for profile in profiles:
        pickup_badge = PickupTimeTracker.get_pickup_badge(
            float(profile.avg_pickup_time_seconds) if profile.avg_pickup_time_seconds else None
        )
        featured.append({
            "id": str(profile.id),
            "name": f"{profile.user.first_name} {profile.user.last_name}" if profile.user else "Professional",
            "company_name": profile.company_name,
            "avatar_url": profile.user.avatar_url if profile.user else None,
            "avg_rating": float(profile.avg_rating),
            "total_reviews": profile.total_reviews,
            "nmls_verified": profile.nmls_verified,
            "pickup_badge": pickup_badge,
            "has_video": bool(profile.prerecorded_video_url),
        })
    
    return {"featured": featured, "count": len(featured)}
