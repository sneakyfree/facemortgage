"""
Baseball Card Stats Service.

Provides comprehensive "baseball card" style statistics for professionals,
aggregating verified data from NMLS and internal metrics.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.professional import ProfessionalProfile

logger = logging.getLogger(__name__)


class BaseballCardStats(BaseModel):
    """Comprehensive stats for a professional's 'baseball card' display."""
    
    # Identity
    professional_id: str
    name: str
    company_name: Optional[str]
    avatar_url: Optional[str]
    
    # NMLS Verification
    nmls_id: Optional[str]
    nmls_verified: bool
    nmls_verified_at: Optional[datetime]
    
    # Performance Metrics
    avg_rating: float
    total_reviews: int
    total_calls_completed: int
    years_experience: Optional[int]
    
    # Response Metrics
    avg_pickup_seconds: Optional[float]
    pickup_category: str  # "instant", "fast", "quick", "moderate", "slower"
    
    # Availability
    current_status: str
    time_online_today_seconds: int
    is_featured: bool
    
    # Specializations
    specialties: list[str]
    languages: list[str]
    service_areas: list[str]
    
    # Subscription
    subscription_tier: str
    
    # Derived grades
    overall_grade: str  # A+, A, B+, B, C, etc.
    responsiveness_grade: str
    experience_grade: str
    rating_grade: str


class BaseballCardService:
    """
    Generates comprehensive baseball card stats for professionals.
    
    Aggregates data from multiple sources to create a holistic
    view of a professional's performance and credentials.
    """
    
    @staticmethod
    async def get_baseball_card(
        db: AsyncSession,
        professional_id: UUID,
    ) -> Optional[BaseballCardStats]:
        """
        Get full baseball card stats for a professional.
        """
        from sqlalchemy.orm import selectinload
        
        query = (
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.specialties),
                selectinload(ProfessionalProfile.languages),
                selectinload(ProfessionalProfile.service_areas),
            )
            .where(ProfessionalProfile.id == professional_id)
        )
        
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        
        if not profile:
            return None
        
        user = profile.user
        
        # Calculate pickup category
        pickup_category = BaseballCardService._get_pickup_category(
            float(profile.avg_pickup_time_seconds) if profile.avg_pickup_time_seconds else None
        )
        
        # Calculate grades
        overall_grade = BaseballCardService._calculate_overall_grade(profile)
        responsiveness_grade = BaseballCardService._calculate_responsiveness_grade(profile)
        experience_grade = BaseballCardService._calculate_experience_grade(profile)
        rating_grade = BaseballCardService._calculate_rating_grade(profile)
        
        return BaseballCardStats(
            professional_id=str(profile.id),
            name=f"{user.first_name} {user.last_name}" if user else "Professional",
            company_name=profile.company_name,
            avatar_url=user.avatar_url if user else None,
            nmls_id=profile.nmls_id,
            nmls_verified=profile.nmls_verified,
            nmls_verified_at=profile.nmls_verified_at,
            avg_rating=float(profile.avg_rating),
            total_reviews=profile.total_reviews,
            total_calls_completed=profile.total_calls_completed,
            years_experience=profile.years_experience,
            avg_pickup_seconds=float(profile.avg_pickup_time_seconds) if profile.avg_pickup_time_seconds else None,
            pickup_category=pickup_category,
            current_status=profile.status.value,
            time_online_today_seconds=profile.time_online_today_seconds,
            is_featured=profile.is_featured,
            specialties=[s.specialty.name for s in profile.specialties if s.specialty],
            languages=[l.language.code for l in profile.languages if l.language],
            service_areas=[
                f"{sa.county.county_name}, {sa.county.state_code}" 
                for sa in profile.service_areas 
                if sa.county
            ],
            subscription_tier=profile.subscription_tier.value,
            overall_grade=overall_grade,
            responsiveness_grade=responsiveness_grade,
            experience_grade=experience_grade,
            rating_grade=rating_grade,
        )
    
    @staticmethod
    def _get_pickup_category(avg_seconds: Optional[float]) -> str:
        """Categorize pickup speed."""
        if avg_seconds is None:
            return "unknown"
        if avg_seconds <= 10:
            return "instant"
        elif avg_seconds <= 30:
            return "fast"
        elif avg_seconds <= 60:
            return "quick"
        elif avg_seconds <= 120:
            return "moderate"
        else:
            return "slower"
    
    @staticmethod
    def _calculate_overall_grade(profile: ProfessionalProfile) -> str:
        """Calculate overall grade based on all factors."""
        score = 0
        max_score = 0
        
        # Rating component (40%)
        if profile.avg_rating:
            rating_score = float(profile.avg_rating) / 5.0
            score += rating_score * 40
        max_score += 40
        
        # Responsiveness component (25%)
        if profile.avg_pickup_time_seconds:
            pickup = float(profile.avg_pickup_time_seconds)
            if pickup <= 10:
                score += 25
            elif pickup <= 30:
                score += 20
            elif pickup <= 60:
                score += 15
            elif pickup <= 120:
                score += 10
            else:
                score += 5
        max_score += 25
        
        # Experience component (20%)
        if profile.years_experience:
            exp_score = min(profile.years_experience / 15, 1.0)
            score += exp_score * 20
        max_score += 20
        
        # Verification bonus (15%)
        if profile.nmls_verified:
            score += 15
        max_score += 15
        
        # Calculate percentage and grade
        if max_score > 0:
            percentage = (score / max_score) * 100
        else:
            percentage = 50
        
        return BaseballCardService._percentage_to_grade(percentage)
    
    @staticmethod
    def _calculate_responsiveness_grade(profile: ProfessionalProfile) -> str:
        """Grade for response time only."""
        if not profile.avg_pickup_time_seconds:
            return "N/A"
        
        pickup = float(profile.avg_pickup_time_seconds)
        if pickup <= 10:
            return "A+"
        elif pickup <= 20:
            return "A"
        elif pickup <= 30:
            return "A-"
        elif pickup <= 45:
            return "B+"
        elif pickup <= 60:
            return "B"
        elif pickup <= 90:
            return "B-"
        elif pickup <= 120:
            return "C+"
        else:
            return "C"
    
    @staticmethod
    def _calculate_experience_grade(profile: ProfessionalProfile) -> str:
        """Grade for years of experience."""
        years = profile.years_experience or 0
        if years >= 15:
            return "A+"
        elif years >= 10:
            return "A"
        elif years >= 7:
            return "A-"
        elif years >= 5:
            return "B+"
        elif years >= 3:
            return "B"
        elif years >= 1:
            return "B-"
        else:
            return "C"
    
    @staticmethod
    def _calculate_rating_grade(profile: ProfessionalProfile) -> str:
        """Grade for rating."""
        if not profile.avg_rating or profile.total_reviews < 3:
            return "N/A"
        
        rating = float(profile.avg_rating)
        if rating >= 4.9:
            return "A+"
        elif rating >= 4.7:
            return "A"
        elif rating >= 4.5:
            return "A-"
        elif rating >= 4.2:
            return "B+"
        elif rating >= 4.0:
            return "B"
        elif rating >= 3.7:
            return "B-"
        elif rating >= 3.5:
            return "C+"
        else:
            return "C"
    
    @staticmethod
    def _percentage_to_grade(percentage: float) -> str:
        """Convert percentage to letter grade."""
        if percentage >= 97:
            return "A+"
        elif percentage >= 93:
            return "A"
        elif percentage >= 90:
            return "A-"
        elif percentage >= 87:
            return "B+"
        elif percentage >= 83:
            return "B"
        elif percentage >= 80:
            return "B-"
        elif percentage >= 77:
            return "C+"
        elif percentage >= 73:
            return "C"
        elif percentage >= 70:
            return "C-"
        else:
            return "D"
    
    @staticmethod
    async def get_comparison(
        db: AsyncSession,
        professional_ids: list[UUID],
    ) -> list[BaseballCardStats]:
        """
        Get baseball cards for multiple professionals for comparison.
        """
        cards = []
        for pid in professional_ids:
            card = await BaseballCardService.get_baseball_card(db, pid)
            if card:
                cards.append(card)
        return cards
