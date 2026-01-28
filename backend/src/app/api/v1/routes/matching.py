"""
Matching API endpoints for FaceMortgage.

Provides endpoints for borrowers to find matching loan officers
based on their profile and preferences.
"""

import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Request, Query
from pydantic import BaseModel, Field

from src.app.core.dependencies import DbSession
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.services.matching_engine import (
    find_matching_los,
    MatchingResult,
    LoanPurpose,
    PropertyType,
    Timeline,
    SpecialNeed,
)
from src.app.services.blockers_engine import BlockersUnlockersEngine, BlockerAnalysis

router = APIRouter()
logger = logging.getLogger(__name__)


class MatchingRequest(BaseModel):
    """Request body for matching endpoint."""
    state: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")
    loan_purpose: LoanPurpose
    property_type: PropertyType
    timeline: Timeline
    special_needs: list[SpecialNeed] = []
    preferred_language: Optional[str] = Field(default="en")
    loan_amount_estimate: Optional[int] = Field(default=None, ge=10000, le=10000000)


class QuickMatchRequest(BaseModel):
    """Simplified matching request for quick searches."""
    state: str = Field(..., min_length=2, max_length=2)
    loan_purpose: LoanPurpose = LoanPurpose.PURCHASE


@router.post("/find", response_model=MatchingResult)
@limiter.limit(RATE_LIMITS["api_read"])
async def find_matches(
    request: Request,
    body: MatchingRequest,
    db: DbSession,
):
    """
    Find matching loan officers for a borrower.
    
    This is the primary matching endpoint. It returns a ranked list
    of loan officers with match scores and explanations for why
    each LO was matched.
    
    The matching algorithm considers:
    - State licensing (required)
    - Specialty alignment  
    - Current availability
    - Response time history
    - Ratings and experience
    - NMLS verification status
    
    Each match includes clear, human-readable reasons explaining
    why the LO was selected, following our evidence-first design.
    """
    session_id = str(uuid4())
    
    logger.info(f"Match request from session {session_id}: state={body.state}")
    
    result = await find_matching_los(
        db=db,
        state=body.state,
        loan_purpose=body.loan_purpose.value,
        property_type=body.property_type.value,
        timeline=body.timeline.value,
        special_needs=[n.value for n in body.special_needs],
        preferred_language=body.preferred_language,
        session_id=session_id,
    )
    
    logger.info(
        f"Match complete for session {session_id}: "
        f"{len(result.matches)} matches from {result.total_eligible} eligible"
    )
    
    return result


@router.post("/quick", response_model=MatchingResult)
@limiter.limit(RATE_LIMITS["api_read"])
async def quick_match(
    request: Request,
    body: QuickMatchRequest,
    db: DbSession,
):
    """
    Quick matching for borrowers who want to browse immediately.
    
    Uses minimal inputs (state + purpose) and defaults for everything else.
    Great for embedding on partner sites or initial exploration.
    """
    session_id = str(uuid4())
    
    result = await find_matching_los(
        db=db,
        state=body.state,
        loan_purpose=body.loan_purpose.value,
        property_type=PropertyType.SINGLE_FAMILY.value,
        timeline=Timeline.EXPLORING.value,
        special_needs=[],
        session_id=session_id,
    )
    
    return result


@router.get("/explain/{lo_id}")
@limiter.limit(RATE_LIMITS["api_read"])
async def explain_match(
    request: Request,
    lo_id: str,
    state: str = Query(..., min_length=2, max_length=2),
    loan_purpose: LoanPurpose = Query(default=LoanPurpose.PURCHASE),
    db: DbSession = None,
):
    """
    Get detailed explanation for why a specific LO matches.
    
    Useful for the "Why this LO?" feature in the UI where
    borrowers want to understand the recommendation.
    """
    # Run matching for this specific state/purpose
    result = await find_matching_los(
        db=db,
        state=state,
        loan_purpose=loan_purpose.value,
        property_type=PropertyType.SINGLE_FAMILY.value,
        timeline=Timeline.EXPLORING.value,
        special_needs=[],
        session_id=str(uuid4()),
    )
    
    # Find the specific LO in results
    for match in result.matches:
        if match.lo_id == lo_id:
            return {
                "lo_id": lo_id,
                "match_score": match.match_score,
                "reasons": [
                    {
                        "category": r.category,
                        "explanation": r.reason,
                        "importance": "high" if r.weight > 0.15 else "medium",
                        "verified": r.verified,
                    }
                    for r in match.match_reasons
                ],
                "algorithm_version": result.algorithm_version,
            }
    
    return {
        "lo_id": lo_id,
        "error": "LO not found in eligible matches for this criteria",
    }


class BlockersRequest(BaseModel):
    """Request body for blockers analysis."""
    credit_score: Optional[int] = Field(default=None, ge=300, le=850)
    dti_ratio: Optional[float] = Field(default=None, ge=0, le=100)
    timeline_days: Optional[int] = Field(default=None, ge=1, le=365)
    employment_type: Optional[str] = Field(default=None)
    years_employment: Optional[int] = Field(default=None, ge=0, le=50)
    has_gift_funds: bool = False
    property_type: Optional[str] = Field(default=None)
    loan_purpose: str = "purchase"
    loan_amount: Optional[int] = Field(default=None, ge=10000, le=10000000)
    state: Optional[str] = Field(default=None, min_length=2, max_length=2)


@router.post("/blockers", response_model=BlockerAnalysis)
@limiter.limit(RATE_LIMITS["api_read"])
async def analyze_blockers(
    request: Request,
    body: BlockersRequest,
):
    """
    Analyze borrower profile for potential loan approval blockers.
    
    Returns a prioritized list of issues that may block or limit
    loan approval, with actionable steps to resolve each one.
    
    Implements the DNA Strand "Blockers/Unlockers" pattern:
    - Quick Wins: Can be fixed in 24 hours
    - 30 Day Actions: Require about a month
    - Long-Term: May take 90+ days
    
    Each blocker includes:
    - What the issue is
    - Why it matters
    - Exactly how to fix it
    - Expected success rate
    """
    analysis = BlockersUnlockersEngine.analyze(
        credit_score=body.credit_score,
        dti_ratio=body.dti_ratio,
        state=body.state,
        timeline_days=body.timeline_days,
        employment_type=body.employment_type,
        years_employment=body.years_employment,
        has_gift_funds=body.has_gift_funds,
        property_type=body.property_type,
        loan_purpose=body.loan_purpose,
        loan_amount=body.loan_amount,
    )
    
    logger.info(
        f"Blockers analysis complete: {analysis.total_blockers} blockers, "
        f"{analysis.blocking_approval} blocking, score={analysis.overall_readiness_score}"
    )
    
    return analysis
