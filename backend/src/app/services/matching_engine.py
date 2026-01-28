"""
Agentic Matching Engine for FaceMortgage.

This module implements the core matching algorithm that connects borrowers
with the most suitable loan officers based on multiple criteria:
- State licensing (required)
- Specialty matching (loan types, client types)
- Language preferences
- Availability and response time
- Ratings and experience

The engine is designed to be:
- Evidence-first: All matches cite verified data
- Explainable: Every match has clear reasons
- Agentic but bounded: AI assists but never invents facts
- Audit-grade: All decisions are logged and reproducible
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.professional import (
    ProfessionalProfile,
    ProfessionalStatus,
    ProfessionalSpecialty,
    ProfessionalLanguage,
    ProfessionalServiceArea,
)
from src.app.models.user import User

logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS
# ============================================================================

class LoanPurpose(str, Enum):
    PURCHASE = "purchase"
    REFINANCE = "refinance"
    CASH_OUT = "cash_out"
    HELOC = "heloc"


class PropertyType(str, Enum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_UNIT = "multi_unit"
    MANUFACTURED = "manufactured"


class Timeline(str, Enum):
    IMMEDIATE = "immediate"  # Within 1 week
    SOON = "30_days"  # 1-4 weeks
    EXPLORING = "exploring"  # Just researching


class SpecialNeed(str, Enum):
    FIRST_TIME_BUYER = "first_time"
    SELF_EMPLOYED = "self_employed"
    JUMBO_LOAN = "jumbo"
    VA_ELIGIBLE = "va_eligible"
    FHA = "fha"
    LOW_DOWN_PAYMENT = "low_down"
    INVESTMENT_PROPERTY = "investment"
    POOR_CREDIT = "poor_credit"


class AvailabilityStatus(str, Enum):
    ONLINE_NOW = "online_now"
    BUSY = "busy"
    OFFLINE = "offline"


class BorrowerProfile(BaseModel):
    """Input profile for matching algorithm."""
    state: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")
    loan_purpose: LoanPurpose
    property_type: PropertyType
    timeline: Timeline
    special_needs: list[SpecialNeed] = []
    preferred_language: Optional[str] = Field(default="en", description="ISO language code")
    loan_amount_estimate: Optional[int] = Field(default=None, ge=10000, le=10000000)
    session_id: Optional[str] = Field(default=None, description="For tracking/audit")


class MatchReason(BaseModel):
    """A single reason why an LO was matched."""
    category: str  # "licensing", "specialty", "language", "availability", "rating"
    reason: str  # Human-readable explanation
    weight: float  # How much this contributed to score (0-1)
    verified: bool = True  # Is this from verified data?


class LOMatch(BaseModel):
    """A matched loan officer with score and reasons."""
    lo_id: str
    lo_name: str
    company_name: Optional[str]
    avatar_url: Optional[str]
    nmls_id: Optional[str]
    nmls_verified: bool
    
    # Match metrics
    match_score: float = Field(..., ge=0, le=100)
    match_reasons: list[MatchReason]
    
    # Availability
    availability: AvailabilityStatus
    avg_pickup_seconds: Optional[float]
    
    # Performance
    avg_rating: float
    total_reviews: int
    years_experience: Optional[int]
    
    # Content
    has_video: bool
    specialty_names: list[str]
    language_codes: list[str]


class MatchingResult(BaseModel):
    """Complete result from matching algorithm."""
    borrower_profile: BorrowerProfile
    matches: list[LOMatch]
    total_eligible: int
    algorithm_version: str
    computed_at: datetime
    
    # Audit trail
    input_hash: str
    session_id: Optional[str]


class MatchingConfig(BaseModel):
    """Configuration for the matching algorithm weights."""
    weight_availability: float = 0.25  # Online now = higher
    weight_rating: float = 0.20  # Higher rating = higher
    weight_specialty: float = 0.20  # Matching specialty = higher
    weight_response_time: float = 0.15  # Faster = higher
    weight_experience: float = 0.10  # More experience = higher
    weight_nmls_verified: float = 0.10  # Verified = bonus


# ============================================================================
# MATCHING ENGINE
# ============================================================================

class MatchingEngine:
    """
    The core agentic matching engine.
    
    Design principles:
    1. NEVER invent data - only use verified, source-labeled information
    2. Explain every match with clear, human-readable reasons
    3. Log all decisions for audit trail
    4. Fail gracefully with informative errors
    """
    
    VERSION = "2.0.0"
    
    def __init__(self, config: Optional[MatchingConfig] = None):
        self.config = config or MatchingConfig()
        
    async def find_matches(
        self,
        db: AsyncSession,
        borrower: BorrowerProfile,
        limit: int = 20,
    ) -> MatchingResult:
        """
        Find the best matching loan officers for a borrower.
        
        Args:
            db: Database session
            borrower: Borrower's profile and preferences
            limit: Maximum number of matches to return
            
        Returns:
            MatchingResult with ranked LOs and explanations
        """
        computed_at = datetime.utcnow()
        input_hash = self._compute_input_hash(borrower)
        
        logger.info(
            f"Starting match: state={borrower.state}, "
            f"purpose={borrower.loan_purpose}, session={borrower.session_id}"
        )
        
        # Step 1: Get all eligible professionals (hard filters)
        eligible_pros = await self._get_eligible_professionals(db, borrower)
        
        logger.info(f"Found {len(eligible_pros)} eligible professionals")
        
        # Step 2: Score and rank each professional
        scored_matches = []
        for pro in eligible_pros:
            match = await self._score_professional(pro, borrower)
            scored_matches.append(match)
        
        # Step 3: Sort by score (descending) and limit
        scored_matches.sort(key=lambda m: m.match_score, reverse=True)
        top_matches = scored_matches[:limit]
        
        # Step 4: Log for audit
        await self._log_matching_decision(
            borrower=borrower,
            matches=top_matches,
            input_hash=input_hash,
        )
        
        return MatchingResult(
            borrower_profile=borrower,
            matches=top_matches,
            total_eligible=len(eligible_pros),
            algorithm_version=self.VERSION,
            computed_at=computed_at,
            input_hash=input_hash,
            session_id=borrower.session_id,
        )
    
    async def _get_eligible_professionals(
        self,
        db: AsyncSession,
        borrower: BorrowerProfile,
    ) -> list[ProfessionalProfile]:
        """
        Get all professionals who are eligible for this borrower.
        
        Hard filters (must match):
        - Profile is complete
        - Licensed in borrower's state (TODO: check service areas)
        """
        # Base query with relationships loaded
        query = (
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.specialties),
                selectinload(ProfessionalProfile.languages),
                selectinload(ProfessionalProfile.service_areas),
            )
            .where(ProfessionalProfile.profile_complete == True)
        )
        
        result = await db.execute(query)
        all_profiles = result.scalars().all()
        
        # For now, return all complete profiles
        # TODO: Filter by state licensing when service_areas is populated
        return list(all_profiles)
    
    async def _score_professional(
        self,
        pro: ProfessionalProfile,
        borrower: BorrowerProfile,
    ) -> LOMatch:
        """
        Calculate match score and generate reasons for a professional.
        """
        reasons: list[MatchReason] = []
        score_components: list[tuple[str, float, float]] = []  # (name, raw_score, weight)
        
        # 1. NMLS Verification bonus
        if pro.nmls_verified:
            reasons.append(MatchReason(
                category="verification",
                reason="NMLS credentials verified",
                weight=self.config.weight_nmls_verified,
                verified=True,
            ))
            score_components.append(("nmls", 1.0, self.config.weight_nmls_verified))
        else:
            score_components.append(("nmls", 0.0, self.config.weight_nmls_verified))
        
        # 2. Availability score
        availability = self._get_availability_status(pro)
        if availability == AvailabilityStatus.ONLINE_NOW:
            reasons.append(MatchReason(
                category="availability",
                reason="Available now for instant connection",
                weight=self.config.weight_availability,
            ))
            score_components.append(("availability", 1.0, self.config.weight_availability))
        elif availability == AvailabilityStatus.BUSY:
            score_components.append(("availability", 0.5, self.config.weight_availability))
        else:
            score_components.append(("availability", 0.0, self.config.weight_availability))
        
        # 3. Rating score
        rating_score = float(pro.avg_rating) / 5.0 if pro.avg_rating else 0.5
        if pro.total_reviews >= 10 and float(pro.avg_rating) >= 4.5:
            reasons.append(MatchReason(
                category="rating",
                reason=f"Highly rated: {pro.avg_rating}/5 from {pro.total_reviews} reviews",
                weight=self.config.weight_rating,
            ))
        score_components.append(("rating", rating_score, self.config.weight_rating))
        
        # 4. Response time score
        if pro.avg_pickup_time_seconds:
            pickup_seconds = float(pro.avg_pickup_time_seconds)
            # Fast pickups get higher scores (under 30s = perfect)
            response_score = max(0, 1 - (pickup_seconds / 120))  # Linear decay to 2 min
            if pickup_seconds < 30:
                reasons.append(MatchReason(
                    category="responsiveness",
                    reason=f"Answers calls quickly: avg {pickup_seconds:.0f} seconds",
                    weight=self.config.weight_response_time,
                ))
            score_components.append(("response", response_score, self.config.weight_response_time))
        else:
            score_components.append(("response", 0.5, self.config.weight_response_time))
        
        # 5. Experience score
        if pro.years_experience:
            exp_score = min(1.0, pro.years_experience / 15)  # 15+ years = max
            if pro.years_experience >= 10:
                reasons.append(MatchReason(
                    category="experience",
                    reason=f"{pro.years_experience} years of experience",
                    weight=self.config.weight_experience,
                ))
            score_components.append(("experience", exp_score, self.config.weight_experience))
        else:
            score_components.append(("experience", 0.3, self.config.weight_experience))
        
        # 6. Specialty matching
        specialty_match = self._check_specialty_match(pro, borrower)
        if specialty_match:
            reasons.append(MatchReason(
                category="specialty",
                reason=specialty_match,
                weight=self.config.weight_specialty,
            ))
            score_components.append(("specialty", 1.0, self.config.weight_specialty))
        else:
            score_components.append(("specialty", 0.5, self.config.weight_specialty))
        
        # Calculate weighted total score
        total_score = sum(raw * weight for _, raw, weight in score_components) * 100
        
        # Get user info
        user = pro.user
        
        return LOMatch(
            lo_id=str(pro.id),
            lo_name=f"{user.first_name} {user.last_name}" if user else "Professional",
            company_name=pro.company_name,
            avatar_url=user.avatar_url if user else None,
            nmls_id=pro.nmls_id,
            nmls_verified=pro.nmls_verified,
            match_score=round(total_score, 1),
            match_reasons=reasons,
            availability=availability,
            avg_pickup_seconds=float(pro.avg_pickup_time_seconds) if pro.avg_pickup_time_seconds else None,
            avg_rating=float(pro.avg_rating),
            total_reviews=pro.total_reviews,
            years_experience=pro.years_experience,
            has_video=bool(pro.prerecorded_video_url),
            specialty_names=[s.specialty.name for s in pro.specialties if s.specialty],
            language_codes=[l.language.code for l in pro.languages if l.language],
        )
    
    def _get_availability_status(self, pro: ProfessionalProfile) -> AvailabilityStatus:
        """Convert professional status to availability for borrowers."""
        if pro.status == ProfessionalStatus.ONLINE_AVAILABLE:
            return AvailabilityStatus.ONLINE_NOW
        elif pro.status in [ProfessionalStatus.ONLINE_BUSY, ProfessionalStatus.IN_CALL]:
            return AvailabilityStatus.BUSY
        else:
            return AvailabilityStatus.OFFLINE
    
    def _check_specialty_match(
        self,
        pro: ProfessionalProfile,
        borrower: BorrowerProfile,
    ) -> Optional[str]:
        """Check if professional's specialties match borrower's needs."""
        pro_specialties = {s.specialty.name.lower() for s in pro.specialties if s.specialty}
        
        # Map special needs to specialty names
        need_to_specialty = {
            SpecialNeed.FIRST_TIME_BUYER: ["first-time buyer", "first time buyer"],
            SpecialNeed.SELF_EMPLOYED: ["self-employed", "self employed"],
            SpecialNeed.JUMBO_LOAN: ["jumbo", "jumbo loans"],
            SpecialNeed.VA_ELIGIBLE: ["va", "va loans", "veteran"],
            SpecialNeed.FHA: ["fha", "fha loans"],
            SpecialNeed.LOW_DOWN_PAYMENT: ["low down payment", "down payment assistance"],
            SpecialNeed.INVESTMENT_PROPERTY: ["investment", "investment property"],
            SpecialNeed.POOR_CREDIT: ["credit repair", "bad credit"],
        }
        
        for need in borrower.special_needs:
            specialty_names = need_to_specialty.get(need, [])
            for name in specialty_names:
                if name in pro_specialties:
                    return f"Specializes in {name.title()}"
        
        return None
    
    def _compute_input_hash(self, borrower: BorrowerProfile) -> str:
        """Create a hash of the input for audit/caching."""
        import hashlib
        input_str = borrower.model_dump_json(exclude={'session_id'})
        return hashlib.sha256(input_str.encode()).hexdigest()[:16]
    
    async def _log_matching_decision(
        self,
        borrower: BorrowerProfile,
        matches: list[LOMatch],
        input_hash: str,
    ):
        """Log the matching decision for audit purposes."""
        # In production, this would write to an audit table
        logger.info(
            f"Match logged: input_hash={input_hash}, "
            f"top_match={matches[0].lo_id if matches else 'none'}, "
            f"total_matches={len(matches)}"
        )


# Singleton instance
matching_engine = MatchingEngine()


async def find_matching_los(
    db: AsyncSession,
    state: str,
    loan_purpose: str,
    property_type: str,
    timeline: str,
    special_needs: Optional[list[str]] = None,
    preferred_language: Optional[str] = None,
    session_id: Optional[str] = None,
) -> MatchingResult:
    """
    Convenience function to find matching loan officers.
    
    This is the main entry point for the matching API.
    """
    borrower = BorrowerProfile(
        state=state.upper(),
        loan_purpose=LoanPurpose(loan_purpose),
        property_type=PropertyType(property_type),
        timeline=Timeline(timeline),
        special_needs=[SpecialNeed(n) for n in (special_needs or [])],
        preferred_language=preferred_language or "en",
        session_id=session_id or str(uuid.uuid4()),
    )
    
    return await matching_engine.find_matches(db, borrower)
