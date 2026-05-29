"""
Real-time Pickup Time Tracker.

Tracks and calculates call pickup metrics for professionals with:
- Rolling average pickup time
- Real-time updates on call events
- Historical trend analysis
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.professional import ProfessionalProfile

logger = logging.getLogger(__name__)


class PickupTimeTracker:
    """
    Tracks and updates average pickup times for professionals.
    
    Uses a rolling average based on recent calls to provide
    accurate, responsive pickup time metrics.
    """
    
    # Configuration
    ROLLING_WINDOW_DAYS = 30  # Use last 30 days of calls
    MIN_CALLS_FOR_DISPLAY = 3  # Minimum calls before showing estimate
    MAX_PICKUP_SECONDS = 300  # 5 minutes max (beyond this is likely abandoned)
    
    @staticmethod
    async def record_pickup(
        db: AsyncSession,
        professional_id: UUID,
        pickup_seconds: float,
    ) -> Optional[float]:
        """
        Record a new pickup event and update the rolling average.
        
        Args:
            db: Database session
            professional_id: The professional's ID
            pickup_seconds: Time in seconds from call initiation to answer
            
        Returns:
            New average pickup time, or None if update failed
        """
        if pickup_seconds <= 0 or pickup_seconds > PickupTimeTracker.MAX_PICKUP_SECONDS:
            logger.warning(
                f"Invalid pickup time {pickup_seconds}s for professional {professional_id}"
            )
            return None
        
        # Get professional profile
        query = select(ProfessionalProfile).where(
            ProfessionalProfile.id == professional_id
        )
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        
        if not profile:
            logger.warning(f"Professional {professional_id} not found")
            return None
        
        # Calculate new rolling average
        # Using exponential moving average for smooth updates
        alpha = 0.3  # Weight for new data (higher = more responsive to recent calls)
        
        if profile.avg_pickup_time_seconds:
            current_avg = float(profile.avg_pickup_time_seconds)
            new_avg = (alpha * pickup_seconds) + ((1 - alpha) * current_avg)
        else:
            # First pickup - use direct value
            new_avg = pickup_seconds
        
        # Update profile
        profile.avg_pickup_time_seconds = Decimal(str(round(new_avg, 2)))
        await db.commit()
        
        logger.info(
            f"Updated pickup time for {professional_id}: "
            f"{pickup_seconds:.1f}s -> avg {new_avg:.1f}s"
        )
        
        return new_avg
    
    @staticmethod
    async def get_pickup_stats(
        db: AsyncSession,
        professional_id: UUID,
    ) -> dict:
        """
        Get detailed pickup time statistics for a professional.
        
        Returns:
            Dict with avg_seconds, display_text, category, etc.
        """
        query = select(ProfessionalProfile).where(
            ProfessionalProfile.id == professional_id
        )
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        
        if not profile or not profile.avg_pickup_time_seconds:
            return {
                "avg_seconds": None,
                "display_text": "Not enough data",
                "category": "unknown",
                "has_data": False,
            }
        
        avg_seconds = float(profile.avg_pickup_time_seconds)
        
        # Categorize pickup speed
        if avg_seconds <= 10:
            category = "instant"
            display_text = "Answers instantly"
        elif avg_seconds <= 30:
            category = "fast"
            display_text = f"Responds in ~{int(avg_seconds)}s"
        elif avg_seconds <= 60:
            category = "quick"
            display_text = "Responds within a minute"
        elif avg_seconds <= 120:
            category = "moderate"
            display_text = "Usually responds in 1-2 min"
        else:
            category = "slower"
            display_text = "May take a few minutes"
        
        return {
            "avg_seconds": avg_seconds,
            "display_text": display_text,
            "category": category,
            "has_data": True,
        }
    
    @staticmethod
    def get_pickup_badge(avg_seconds: Optional[float]) -> dict:
        """
        Get a badge/label for pickup time display in the grid.
        
        Returns colorized badge info for the UI.
        """
        if avg_seconds is None:
            return {
                "text": "New",
                "color": "gray",
                "icon": "🆕",
            }
        
        if avg_seconds <= 10:
            return {
                "text": "<10s",
                "color": "green",
                "icon": "⚡",
            }
        elif avg_seconds <= 30:
            return {
                "text": f"~{int(avg_seconds)}s",
                "color": "green",
                "icon": "🟢",
            }
        elif avg_seconds <= 60:
            return {
                "text": "<1min",
                "color": "yellow",
                "icon": "🟡",
            }
        else:
            return {
                "text": ">1min",
                "color": "orange",
                "icon": "🟠",
            }


class AdvancedFilterService:
    """
    Enhanced filtering service for the professional grid.
    
    Supports filtering by:
    - State licensing
    - Specialty (loan types, client types)
    - Language
    - Pickup time range
    - Rating threshold
    - Availability status
    - NMLS verification
    """
    
    @staticmethod
    async def filter_professionals(
        db: AsyncSession,
        *,
        state: Optional[str] = None,
        specialties: Optional[list[str]] = None,
        languages: Optional[list[str]] = None,
        min_rating: Optional[float] = None,
        max_pickup_seconds: Optional[float] = None,
        nmls_verified_only: bool = False,
        online_only: bool = False,
        available_only: bool = False,
        has_video: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """
        Apply advanced filters to professional grid.
        
        All filters are optional and combinable.
        """
        from src.app.models.professional import (
            ProfessionalProfile,
            ProfessionalStatus,
        )
        from sqlalchemy.orm import selectinload
        from sqlalchemy import and_, or_
        
        # Base query with eager loading
        query = (
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.specialties),
                selectinload(ProfessionalProfile.languages),
            )
            .where(ProfessionalProfile.profile_complete == True)
        )
        
        # Apply filters
        filters = []
        
        # NMLS verification
        if nmls_verified_only:
            filters.append(ProfessionalProfile.nmls_verified == True)
        
        # Rating threshold
        if min_rating is not None:
            filters.append(ProfessionalProfile.avg_rating >= min_rating)
        
        # Pickup time threshold
        if max_pickup_seconds is not None:
            filters.append(
                or_(
                    ProfessionalProfile.avg_pickup_time_seconds == None,  # Include new professionals
                    ProfessionalProfile.avg_pickup_time_seconds <= max_pickup_seconds
                )
            )
        
        # Online status
        if online_only:
            filters.append(
                ProfessionalProfile.status.in_([
                    ProfessionalStatus.ONLINE_AVAILABLE,
                    ProfessionalStatus.ONLINE_BUSY,
                    ProfessionalStatus.IN_CALL,
                ])
            )
        
        # Available status
        if available_only:
            filters.append(
                ProfessionalProfile.status == ProfessionalStatus.ONLINE_AVAILABLE
            )
        
        # Has video
        if has_video:
            filters.append(ProfessionalProfile.prerecorded_video_url != None)
        
        # Apply all filters
        if filters:
            query = query.where(and_(*filters))
        
        # Pagination
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        profiles = result.scalars().all()
        
        # Further filter by specialties/languages (requires joining)
        filtered_profiles = []
        for profile in profiles:
            # Specialty filter
            if specialties:
                profile_specialties = {
                    s.specialty.name.lower() 
                    for s in profile.specialties 
                    if s.specialty
                }
                if not any(s.lower() in profile_specialties for s in specialties):
                    continue
            
            # Language filter
            if languages:
                profile_languages = {
                    l.language.code.lower() 
                    for l in profile.languages 
                    if l.language
                }
                if not any(lang.lower() in profile_languages for lang in languages):
                    continue
            
            # Get pickup badge
            pickup_badge = PickupTimeTracker.get_pickup_badge(
                float(profile.avg_pickup_time_seconds) 
                if profile.avg_pickup_time_seconds else None
            )
            
            filtered_profiles.append({
                "id": str(profile.id),
                "user_id": str(profile.user_id),
                "name": f"{profile.user.first_name} {profile.user.last_name}" if profile.user else "Professional",
                "company_name": profile.company_name,
                "avatar_url": profile.user.avatar_url if profile.user else None,
                "status": profile.status.value,
                "nmls_id": profile.nmls_id,
                "nmls_verified": profile.nmls_verified,
                "avg_rating": float(profile.avg_rating),
                "total_reviews": profile.total_reviews,
                "years_experience": profile.years_experience,
                "has_video": bool(profile.prerecorded_video_url),
                "pickup_badge": pickup_badge,
                "avg_pickup_seconds": float(profile.avg_pickup_time_seconds) if profile.avg_pickup_time_seconds else None,
                "specialties": [s.specialty.name for s in profile.specialties if s.specialty],
                "languages": [l.language.code for l in profile.languages if l.language],
            })
        
        return filtered_profiles
    
    @staticmethod
    def get_available_filters() -> dict:
        """
        Get metadata about available filters for the UI.
        """
        return {
            "specialties": {
                "label": "Loan Specialty",
                "options": [
                    {"value": "fha", "label": "FHA Loans"},
                    {"value": "va", "label": "VA Loans"},
                    {"value": "jumbo", "label": "Jumbo Loans"},
                    {"value": "conventional", "label": "Conventional"},
                    {"value": "first-time buyer", "label": "First-Time Buyers"},
                    {"value": "refinance", "label": "Refinance"},
                    {"value": "investment", "label": "Investment Properties"},
                    {"value": "self-employed", "label": "Self-Employed"},
                ],
            },
            "languages": {
                "label": "Language",
                "options": [
                    {"value": "en", "label": "English"},
                    {"value": "es", "label": "Spanish"},
                    {"value": "zh", "label": "Chinese"},
                    {"value": "vi", "label": "Vietnamese"},
                    {"value": "ko", "label": "Korean"},
                    {"value": "tl", "label": "Tagalog"},
                ],
            },
            "pickup_speed": {
                "label": "Response Time",
                "options": [
                    {"value": 10, "label": "Instant (<10s)"},
                    {"value": 30, "label": "Fast (<30s)"},
                    {"value": 60, "label": "Quick (<1min)"},
                    {"value": 120, "label": "Any"},
                ],
            },
            "min_rating": {
                "label": "Minimum Rating",
                "options": [
                    {"value": 4.5, "label": "4.5+ stars"},
                    {"value": 4.0, "label": "4.0+ stars"},
                    {"value": 3.5, "label": "3.5+ stars"},
                    {"value": 0, "label": "Any rating"},
                ],
            },
        }
