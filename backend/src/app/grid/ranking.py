"""
Grid ranking algorithm for professional positioning.

Implements weighted scoring based on:
- Bid Amount (30%): Higher bid = better position
- Subscription Tier (25%): Paid tiers get boost
- Rating (20%): Average star rating
- Pickup Time (10%): Faster response = higher score
- Time Online (10%): Rewards active professionals
- Recency (5%): Slight boost for recently active

The algorithm ensures fair visibility while rewarding
professionals who invest in the platform and provide good service.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.professional import (
    ProfessionalProfile,
    ProfessionalStatus,
    SubscriptionTier,
    ProfessionalSpecialty,
    ProfessionalLanguage,
    ProfessionalServiceArea,
    Specialty,
    Language,
    County,
)
from src.app.models.user import User


@dataclass
class RankingWeights:
    """Configurable weights for ranking factors."""
    bid_amount: float = 0.30
    subscription_tier: float = 0.25
    rating: float = 0.20
    pickup_time: float = 0.10
    time_online: float = 0.10
    recency: float = 0.05

    def validate(self) -> bool:
        """Ensure weights sum to 1.0."""
        total = (
            self.bid_amount +
            self.subscription_tier +
            self.rating +
            self.pickup_time +
            self.time_online +
            self.recency
        )
        return abs(total - 1.0) < 0.001


@dataclass
class RankedProfessional:
    """Professional with calculated ranking score."""
    professional_id: UUID
    user_id: UUID
    score: float
    position: int

    # Component scores for transparency
    bid_score: float
    tier_score: float
    rating_score: float
    pickup_score: float
    online_score: float
    recency_score: float

    # Raw values
    bid_amount: Decimal
    subscription_tier: SubscriptionTier
    avg_rating: float
    avg_pickup_time_seconds: Optional[float]
    time_online_today_seconds: int
    last_activity: Optional[datetime]


class GridRankingService:
    """
    Service for calculating professional grid positions.

    The ranking algorithm balances multiple factors to create
    a fair and dynamic grid that rewards both paid placement
    and quality of service.
    """

    # Tier multipliers for subscription scoring
    TIER_SCORES = {
        SubscriptionTier.FREE: 0.0,
        SubscriptionTier.BASIC: 0.4,
        SubscriptionTier.PROFESSIONAL: 0.7,
        SubscriptionTier.PREMIUM: 1.0,
    }

    # Maximum values for normalization
    MAX_BID_AMOUNT = Decimal("100.00")  # $100/click max bid
    MAX_PICKUP_TIME = 60  # seconds (slower than this = 0 score)
    MAX_ONLINE_TIME = 8 * 3600  # 8 hours = max score
    RECENCY_WINDOW = timedelta(hours=24)

    def __init__(self, weights: RankingWeights = None):
        self.weights = weights or RankingWeights()
        if not self.weights.validate():
            raise ValueError("Ranking weights must sum to 1.0")

    def calculate_score(
        self,
        bid_amount: Decimal,
        subscription_tier: SubscriptionTier,
        avg_rating: Optional[float],
        avg_pickup_time_seconds: Optional[float],
        time_online_today_seconds: int,
        last_activity: Optional[datetime],
    ) -> Dict[str, float]:
        """
        Calculate ranking score for a professional.

        Returns dict with total score and component scores.
        """
        # 1. Bid Amount Score (0-1)
        bid_score = min(
            float(bid_amount or 0) / float(self.MAX_BID_AMOUNT),
            1.0
        )

        # 2. Subscription Tier Score (0-1)
        tier_score = self.TIER_SCORES.get(subscription_tier, 0.0)

        # 3. Rating Score (0-1)
        # Normalize from 1-5 scale to 0-1
        if avg_rating and avg_rating > 0:
            rating_score = (avg_rating - 1) / 4  # 1 star = 0, 5 stars = 1
        else:
            rating_score = 0.5  # Default for unrated

        # 4. Pickup Time Score (0-1)
        # Faster is better: 0 seconds = 1.0, MAX_PICKUP_TIME+ = 0.0
        if avg_pickup_time_seconds is not None and avg_pickup_time_seconds > 0:
            pickup_score = max(
                1.0 - (avg_pickup_time_seconds / self.MAX_PICKUP_TIME),
                0.0
            )
        else:
            pickup_score = 0.5  # Default for no data

        # 5. Time Online Score (0-1)
        online_score = min(
            time_online_today_seconds / self.MAX_ONLINE_TIME,
            1.0
        )

        # 6. Recency Score (0-1)
        if last_activity:
            time_since = datetime.utcnow() - last_activity
            if time_since < self.RECENCY_WINDOW:
                recency_score = 1.0 - (time_since.total_seconds() / self.RECENCY_WINDOW.total_seconds())
            else:
                recency_score = 0.0
        else:
            recency_score = 0.0

        # Calculate weighted total
        total_score = (
            bid_score * self.weights.bid_amount +
            tier_score * self.weights.subscription_tier +
            rating_score * self.weights.rating +
            pickup_score * self.weights.pickup_time +
            online_score * self.weights.time_online +
            recency_score * self.weights.recency
        )

        return {
            "total": total_score,
            "bid": bid_score,
            "tier": tier_score,
            "rating": rating_score,
            "pickup": pickup_score,
            "online": online_score,
            "recency": recency_score,
        }

    async def get_ranked_professionals(
        self,
        db: AsyncSession,
        filters: Dict[str, Any] = None,
        limit: int = 50,
        offset: int = 0,
        only_available: bool = True,
    ) -> List[RankedProfessional]:
        """
        Get professionals ranked by score.

        Args:
            db: Database session
            filters: Optional filters (language, specialty, county, user_type)
            limit: Max results to return
            offset: Pagination offset
            only_available: Only include ONLINE_AVAILABLE professionals

        Returns:
            List of RankedProfessional objects sorted by score
        """
        # Build base query
        query = (
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.user),
            )
            .join(User)
            .where(User.is_active == True)
            .where(ProfessionalProfile.profile_complete == True)
        )

        if only_available:
            query = query.where(
                ProfessionalProfile.status == ProfessionalStatus.ONLINE_AVAILABLE
            )

        # Apply filters
        filters = filters or {}

        if filters.get("user_type"):
            query = query.where(User.user_type == filters["user_type"])

        if filters.get("min_rating"):
            query = query.where(
                ProfessionalProfile.avg_rating >= filters["min_rating"]
            )

        # Filter by specialty (by ID or name)
        if filters.get("specialty_id"):
            query = query.where(
                ProfessionalProfile.id.in_(
                    select(ProfessionalSpecialty.professional_id)
                    .where(ProfessionalSpecialty.specialty_id == filters["specialty_id"])
                )
            )
        elif filters.get("specialty"):
            # Filter by specialty name (case-insensitive)
            query = query.where(
                ProfessionalProfile.id.in_(
                    select(ProfessionalSpecialty.professional_id)
                    .join(Specialty)
                    .where(func.lower(Specialty.name) == func.lower(filters["specialty"]))
                )
            )

        # Filter by language (by code or ID)
        if filters.get("language_id"):
            query = query.where(
                ProfessionalProfile.id.in_(
                    select(ProfessionalLanguage.professional_id)
                    .where(ProfessionalLanguage.language_id == filters["language_id"])
                )
            )
        elif filters.get("language"):
            # Filter by language code (e.g., 'es', 'zh')
            query = query.where(
                ProfessionalProfile.id.in_(
                    select(ProfessionalLanguage.professional_id)
                    .join(Language)
                    .where(func.lower(Language.code) == func.lower(filters["language"]))
                )
            )

        # Filter by county (service area)
        if filters.get("county_id"):
            query = query.where(
                ProfessionalProfile.id.in_(
                    select(ProfessionalServiceArea.professional_id)
                    .where(ProfessionalServiceArea.county_id == filters["county_id"])
                )
            )
        elif filters.get("state") and filters.get("county"):
            # Filter by state code and county name
            query = query.where(
                ProfessionalProfile.id.in_(
                    select(ProfessionalServiceArea.professional_id)
                    .join(County)
                    .where(
                        and_(
                            func.upper(County.state_code) == func.upper(filters["state"]),
                            func.lower(County.county_name) == func.lower(filters["county"])
                        )
                    )
                )
            )
        elif filters.get("state"):
            # Filter by state only (professionals serving any county in state)
            query = query.where(
                ProfessionalProfile.id.in_(
                    select(ProfessionalServiceArea.professional_id)
                    .join(County)
                    .where(func.upper(County.state_code) == func.upper(filters["state"]))
                )
            )

        # Execute query
        result = await db.execute(query)
        professionals = result.scalars().all()

        # Calculate scores for each professional
        ranked = []
        for prof in professionals:
            scores = self.calculate_score(
                bid_amount=prof.current_bid_amount or Decimal("0"),
                subscription_tier=prof.subscription_tier,
                avg_rating=float(prof.avg_rating) if prof.avg_rating else None,
                avg_pickup_time_seconds=(
                    float(prof.avg_pickup_time_seconds)
                    if prof.avg_pickup_time_seconds else None
                ),
                time_online_today_seconds=prof.time_online_today_seconds or 0,
                last_activity=prof.status_updated_at,
            )

            ranked.append(RankedProfessional(
                professional_id=prof.id,
                user_id=prof.user_id,
                score=scores["total"],
                position=0,  # Will be set after sorting
                bid_score=scores["bid"],
                tier_score=scores["tier"],
                rating_score=scores["rating"],
                pickup_score=scores["pickup"],
                online_score=scores["online"],
                recency_score=scores["recency"],
                bid_amount=prof.current_bid_amount or Decimal("0"),
                subscription_tier=prof.subscription_tier,
                avg_rating=float(prof.avg_rating) if prof.avg_rating else 0.0,
                avg_pickup_time_seconds=(
                    float(prof.avg_pickup_time_seconds)
                    if prof.avg_pickup_time_seconds else None
                ),
                time_online_today_seconds=prof.time_online_today_seconds or 0,
                last_activity=prof.status_updated_at,
            ))

        # Sort by total score descending
        ranked.sort(key=lambda x: x.score, reverse=True)

        # Assign positions
        for i, prof in enumerate(ranked):
            prof.position = i + 1

        # Apply pagination
        return ranked[offset:offset + limit]

    async def get_professional_position(
        self,
        db: AsyncSession,
        professional_id: UUID,
    ) -> Optional[int]:
        """
        Get the current grid position for a specific professional.

        Useful for professionals to see their ranking.
        """
        ranked = await self.get_ranked_professionals(
            db, limit=1000, only_available=False
        )

        for prof in ranked:
            if prof.professional_id == professional_id:
                return prof.position

        return None

    async def estimate_position_with_bid(
        self,
        db: AsyncSession,
        professional_id: UUID,
        proposed_bid: Decimal,
    ) -> int:
        """
        Estimate what position a professional would have with a different bid.

        Useful for bid optimization UI.
        """
        # Get current rankings
        ranked = await self.get_ranked_professionals(
            db, limit=1000, only_available=False
        )

        # Find the professional and recalculate their score
        target = None
        for prof in ranked:
            if prof.professional_id == professional_id:
                target = prof
                break

        if not target:
            return -1

        # Calculate new score with proposed bid
        new_scores = self.calculate_score(
            bid_amount=proposed_bid,
            subscription_tier=target.subscription_tier,
            avg_rating=target.avg_rating,
            avg_pickup_time_seconds=target.avg_pickup_time_seconds,
            time_online_today_seconds=target.time_online_today_seconds,
            last_activity=target.last_activity,
        )

        new_total_score = new_scores["total"]

        # Count how many would be ahead
        position = 1
        for prof in ranked:
            if prof.professional_id != professional_id and prof.score > new_total_score:
                position += 1

        return position


# Singleton instance
_ranking_service: Optional[GridRankingService] = None


def get_ranking_service() -> GridRankingService:
    """Get the grid ranking service singleton."""
    global _ranking_service
    if _ranking_service is None:
        _ranking_service = GridRankingService()
    return _ranking_service
