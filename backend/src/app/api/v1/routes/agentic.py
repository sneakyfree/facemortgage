"""
Agentic Intelligence API endpoints.

Provides Phase 4 AI-powered features:
- Borrower intent classification
- Smart LO recommendations
- Follow-up suggestions
- Conversation summarization
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

from src.app.core.dependencies import DbSession, CurrentUser, CurrentProfessional
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.services.agentic_intelligence import (
    IntentClassifier,
    IntentClassification,
    BorrowerIntent,
    SmartRecommender,
    SmartRecommendation,
    FollowUpSuggester,
    FollowUpSuggestion,
    ConversationSummarizer,
    ConversationSummary,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Request/Response Schemas ====================

class ClassifyIntentRequest(BaseModel):
    """Request to classify borrower intent."""
    timeline: str = Field(..., description="immediate, 30_days, or exploring")
    loan_purpose: str = Field(..., description="purchase, refinance, cash_out, heloc")
    property_identified: bool = False
    has_agent: bool = False
    notes: Optional[str] = None


class SmartMatchRequest(BaseModel):
    """Request for smart LO recommendations."""
    state: str = Field(..., min_length=2, max_length=2)
    first_time_buyer: bool = False
    preferred_language: str = "en"
    loan_amount: Optional[int] = None
    limit: int = Field(default=5, ge=1, le=10)


class FollowUpRequest(BaseModel):
    """Request for follow-up suggestions."""
    borrower_id: Optional[str] = None
    last_activity_iso: Optional[str] = None  # ISO timestamp
    intent: Optional[str] = None
    calls_completed: int = 0
    has_email: bool = True
    has_phone: bool = False


class SummarizeRequest(BaseModel):
    """Request to summarize a call."""
    call_id: str
    duration_seconds: int
    lo_notes: Optional[str] = None


# ==================== Endpoints ====================

@router.post("/classify-intent", response_model=IntentClassification)
@limiter.limit(RATE_LIMITS["api_read"])
async def classify_borrower_intent(
    request: Request,
    body: ClassifyIntentRequest,
):
    """
    Classify borrower intent from available signals.
    
    Returns:
    - Intent category (hot, warm, exploring, refinance)
    - Confidence score (0-1)
    - Supporting signals with explanations
    - Recommended actions
    - Urgency score (1-10)
    
    Use this to prioritize leads and personalize engagement.
    """
    result = IntentClassifier.classify(
        timeline=body.timeline,
        loan_purpose=body.loan_purpose,
        property_identified=body.property_identified,
        has_agent=body.has_agent,
        notes=body.notes,
    )
    
    logger.info(f"Intent classified: {result.intent.value} (confidence={result.confidence})")
    
    return result


@router.post("/smart-recommend")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_smart_recommendations(
    request: Request,
    body: SmartMatchRequest,
    db: DbSession,
):
    """
    Get AI-enhanced LO recommendations.
    
    Combines base matching algorithm with learned success patterns:
    - First-time buyer specialists for new homebuyers
    - Fast responders for urgent borrowers
    - Language-matched LOs for non-English speakers
    - Experienced LOs for jumbo loans
    
    Each recommendation includes:
    - Enhanced score incorporating success patterns
    - Predicted conversion rate
    - Explainable reasons
    """
    # First classify intent based on request
    intent = BorrowerIntent.WARM  # Default for smart match requests
    
    recommendations = await SmartRecommender.get_smart_recommendations(
        db=db,
        borrower_state=body.state,
        borrower_intent=intent,
        borrower_first_time=body.first_time_buyer,
        borrower_language=body.preferred_language,
        loan_amount=body.loan_amount,
        limit=body.limit,
    )
    
    return {
        "recommendations": [r.model_dump() for r in recommendations],
        "count": len(recommendations),
        "algorithm": "smart_v1",
    }


@router.post("/suggest-followups")
@limiter.limit(RATE_LIMITS["api_read"])
async def suggest_followups(
    request: Request,
    body: FollowUpRequest,
    current_user: CurrentProfessional,
):
    """
    Get AI-generated follow-up suggestions for a borrower.
    
    Analyzes engagement patterns to suggest:
    - Optimal timing for follow-up
    - Best channel (email, SMS, call, in-app)
    - Personalized message templates
    - Priority ranking
    
    Great for LO dashboard "next actions" widget.
    """
    # Parse last activity
    if body.last_activity_iso:
        try:
            last_activity = datetime.fromisoformat(body.last_activity_iso.replace('Z', '+00:00'))
        except ValueError:
            last_activity = datetime.utcnow() - timedelta(days=1)
    else:
        last_activity = datetime.utcnow() - timedelta(days=1)
    
    # Parse intent
    try:
        intent = BorrowerIntent(body.intent) if body.intent else BorrowerIntent.WARM
    except ValueError:
        intent = BorrowerIntent.WARM
    
    suggestions = FollowUpSuggester.suggest_followups(
        last_activity=last_activity,
        intent=intent,
        calls_completed=body.calls_completed,
        has_email=body.has_email,
        has_phone=body.has_phone,
    )
    
    return {
        "suggestions": [s.model_dump() for s in suggestions],
        "count": len(suggestions),
    }


@router.post("/summarize-call", response_model=ConversationSummary)
@limiter.limit(RATE_LIMITS["api_write"])
async def summarize_conversation(
    request: Request,
    body: SummarizeRequest,
    current_user: CurrentProfessional,
):
    """
    Generate an AI summary of a call conversation.
    
    Extracts from LO notes (or transcript in future):
    - Key topics discussed
    - Borrower questions
    - LO commitments
    - Recommended next steps
    - Overall sentiment
    
    Helps LOs and admins quickly understand call outcomes.
    """
    summary = ConversationSummarizer.summarize_from_notes(
        call_id=body.call_id,
        duration_seconds=body.duration_seconds,
        lo_notes=body.lo_notes,
    )
    
    return summary


@router.get("/intent-signals")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_intent_signal_weights(request: Request):
    """
    Get the current intent classification signal weights.
    
    Useful for understanding how intent is calculated
    and for building explanation UIs.
    """
    return {
        "signals": IntentClassifier.SIGNAL_WEIGHTS,
        "intents": [i.value for i in BorrowerIntent],
        "version": "1.0.0",
    }


@router.get("/success-patterns")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_success_patterns(request: Request):
    """
    Get learned success patterns used for smart recommendations.
    
    Shows the patterns the AI uses to enhance matching,
    supporting the "explainability" principle.
    """
    patterns = [
        {
            "id": p.pattern_id,
            "description": p.description,
            "success_rate": p.success_rate,
            "sample_size": p.sample_size,
        }
        for p in SmartRecommender.SUCCESS_PATTERNS
    ]
    
    return {
        "patterns": patterns,
        "count": len(patterns),
    }


# Import timedelta for the endpoint
from datetime import timedelta


# ==================== Crew Status Endpoint ====================

class CrewAgentStatus(BaseModel):
    """Status of an individual agent in the crew."""
    name: str
    status: str  # idle, processing, complete, error
    lastAction: Optional[str] = None
    confidence: Optional[float] = None
    duration_ms: Optional[int] = None


class CrewStatusResponse(BaseModel):
    """Full crew status for visualization."""
    session_id: str
    orchestrator_status: str  # idle, active, complete
    agents: list[CrewAgentStatus]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@router.get("/crew/status/{session_id}", response_model=CrewStatusResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_crew_status(
    request: Request,
    session_id: str,
):
    """
    Get real-time status of the agentic crew for a matching session.
    
    Returns status for each agent in the pipeline:
    - Qualifier: Validates borrower information
    - Matcher: Finds best LO matches
    - Explainer: Generates match explanations
    - Notifier: Sends notifications
    
    Use for real-time visualization during matching flow.
    """
    # In production, this would check Redis for actual session state
    # For now, return simulated state based on session_id hash
    
    import hashlib
    hash_val = int(hashlib.md5(session_id.encode()).hexdigest()[:8], 16)
    progress = (hash_val % 5)  # 0-4 stages
    
    agents = []
    agent_names = ["Qualifier", "Matcher", "Explainer", "Notifier"]
    agent_actions = [
        "Validated loan parameters",
        "Scored 12 eligible professionals",
        "Generated 5 match explanations",
        "Queued email notification",
    ]
    
    for i, name in enumerate(agent_names):
        if i < progress:
            # Completed
            agents.append(CrewAgentStatus(
                name=name,
                status="complete",
                lastAction=agent_actions[i],
                confidence=0.85 + (hash_val % 15) / 100,
                duration_ms=50 + (hash_val % 200),
            ))
        elif i == progress:
            # Currently processing
            agents.append(CrewAgentStatus(
                name=name,
                status="processing",
                lastAction=f"Processing {name.lower()}...",
            ))
        else:
            # Waiting
            agents.append(CrewAgentStatus(
                name=name,
                status="idle",
            ))
    
    orchestrator_status = "complete" if progress >= 4 else "active" if progress > 0 else "idle"
    
    return CrewStatusResponse(
        session_id=session_id,
        orchestrator_status=orchestrator_status,
        agents=agents,
        started_at=datetime.utcnow().isoformat() if progress > 0 else None,
        completed_at=datetime.utcnow().isoformat() if progress >= 4 else None,
    )
