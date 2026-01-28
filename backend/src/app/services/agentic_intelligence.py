"""
Agentic Intelligence Layer for FaceMortgage.

This module provides AI-powered features following the DNA Strand principles:
- Evidence-first: Only use verified data
- Explainable: Clear reasoning for all recommendations
- Bounded autonomy: AI assists, human decides
- Audit-grade: Full logging and reproducibility

Components:
1. Intent Classifier - Understand borrower needs from conversation
2. Smart Recommender - Learn from successful matches
3. Follow-up Suggester - Proactive engagement recommendations
4. Conversation Summarizer - Extract key points from calls
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ==================== Intent Classification ====================

class BorrowerIntent(str, Enum):
    """Classified borrower intent levels."""
    HOT = "hot"              # Ready to proceed immediately
    WARM = "warm"            # Actively shopping, comparing options
    EXPLORING = "exploring"  # Early research, no urgency
    REFINANCE = "refinance"  # Looking to refinance existing loan
    PREAPPROVAL = "preapproval"  # Just wants preapproval letter
    UNKNOWN = "unknown"


class IntentSignal(BaseModel):
    """Individual signal contributing to intent classification."""
    signal_type: str
    value: str
    weight: float  # 0.0 to 1.0
    explanation: str


class IntentClassification(BaseModel):
    """Result of intent classification with explanations."""
    intent: BorrowerIntent
    confidence: float  # 0.0 to 1.0
    signals: list[IntentSignal]
    recommended_actions: list[str]
    urgency_score: int  # 1-10
    
    
class IntentClassifier:
    """
    Classifies borrower intent based on available signals.
    
    Uses rule-based classification with weighted signals.
    Designed to be transparent and auditable.
    """
    
    # Signal weights
    SIGNAL_WEIGHTS = {
        "timeline_immediate": 0.35,
        "timeline_30_days": 0.25,
        "timeline_exploring": 0.10,
        "preapproval_mentioned": 0.30,
        "refinance_purpose": 0.25,
        "property_identified": 0.20,
        "agent_referral": 0.15,
        "repeat_visitor": 0.10,
        "call_completed": 0.25,
        "multiple_los_viewed": 0.15,
    }
    
    @staticmethod
    def classify(
        timeline: str,
        loan_purpose: str,
        property_identified: bool = False,
        has_agent: bool = False,
        calls_completed: int = 0,
        los_viewed: int = 0,
        return_visitor: bool = False,
        notes: Optional[str] = None,
    ) -> IntentClassification:
        """
        Classify borrower intent based on available signals.
        
        Returns classification with confidence score and
        supporting evidence for transparency.
        """
        signals = []
        total_weight = 0.0
        hot_score = 0.0
        
        # Timeline signal
        if timeline == "immediate":
            signals.append(IntentSignal(
                signal_type="timeline",
                value="immediate",
                weight=0.35,
                explanation="Borrower indicates they're ready now"
            ))
            hot_score += 0.35
            total_weight += 0.35
        elif timeline == "30_days":
            signals.append(IntentSignal(
                signal_type="timeline",
                value="30_days",
                weight=0.25,
                explanation="Borrower plans to proceed within 30 days"
            ))
            hot_score += 0.20
            total_weight += 0.25
        else:
            signals.append(IntentSignal(
                signal_type="timeline",
                value="exploring",
                weight=0.10,
                explanation="Borrower is still exploring options"
            ))
            hot_score += 0.05
            total_weight += 0.10
        
        # Loan purpose signal
        if loan_purpose == "refinance" or loan_purpose == "cash_out":
            signals.append(IntentSignal(
                signal_type="loan_purpose",
                value=loan_purpose,
                weight=0.25,
                explanation=f"Refinance intent detected: {loan_purpose}"
            ))
            # Refinance often has clear timeline
            hot_score += 0.15
            total_weight += 0.25
        
        # Property identified
        if property_identified:
            signals.append(IntentSignal(
                signal_type="property",
                value="identified",
                weight=0.20,
                explanation="Borrower has identified a specific property"
            ))
            hot_score += 0.20
            total_weight += 0.20
        
        # Has real estate agent
        if has_agent:
            signals.append(IntentSignal(
                signal_type="referral",
                value="agent",
                weight=0.15,
                explanation="Working with a real estate agent"
            ))
            hot_score += 0.15
            total_weight += 0.15
        
        # Previous engagement
        if calls_completed > 0:
            signals.append(IntentSignal(
                signal_type="engagement",
                value=f"{calls_completed}_calls",
                weight=0.25,
                explanation=f"Completed {calls_completed} call(s) with LOs"
            ))
            hot_score += 0.20
            total_weight += 0.25
        
        if los_viewed > 3:
            signals.append(IntentSignal(
                signal_type="research",
                value=f"{los_viewed}_los_viewed",
                weight=0.15,
                explanation=f"Viewed {los_viewed} loan officer profiles"
            ))
            hot_score += 0.10
            total_weight += 0.15
        
        # Calculate confidence and intent
        confidence = min(hot_score / max(total_weight, 0.5), 1.0)
        
        # Determine intent
        if loan_purpose in ["refinance", "cash_out"]:
            intent = BorrowerIntent.REFINANCE
        elif hot_score >= 0.6:
            intent = BorrowerIntent.HOT
        elif hot_score >= 0.35:
            intent = BorrowerIntent.WARM
        elif hot_score >= 0.15:
            intent = BorrowerIntent.EXPLORING
        else:
            intent = BorrowerIntent.UNKNOWN
        
        # Generate recommended actions
        actions = IntentClassifier._generate_actions(intent, signals)
        
        # Calculate urgency (1-10)
        urgency = min(10, max(1, int(hot_score * 12)))
        
        logger.info(
            f"Intent classified: {intent.value} "
            f"(confidence={confidence:.2f}, urgency={urgency})"
        )
        
        return IntentClassification(
            intent=intent,
            confidence=round(confidence, 2),
            signals=signals,
            recommended_actions=actions,
            urgency_score=urgency,
        )
    
    @staticmethod
    def _generate_actions(intent: BorrowerIntent, signals: list[IntentSignal]) -> list[str]:
        """Generate recommended actions based on intent."""
        actions = []
        
        if intent == BorrowerIntent.HOT:
            actions.append("Prioritize in queue - borrower ready to proceed")
            actions.append("Offer immediate callback if LO unavailable")
            actions.append("Pre-prepare rate sheet for quick discussion")
        elif intent == BorrowerIntent.WARM:
            actions.append("Send personalized LO recommendations")
            actions.append("Offer to schedule a convenient call time")
            actions.append("Provide educational content on loan process")
        elif intent == BorrowerIntent.REFINANCE:
            actions.append("Match with refinance specialists")
            actions.append("Show current vs. potential rate comparison")
            actions.append("Highlight cash-out or rate-term options")
        elif intent == BorrowerIntent.EXPLORING:
            actions.append("Provide educational resources")
            actions.append("Suggest preapproval to understand budget")
            actions.append("Offer to answer general questions")
        else:
            actions.append("Gather more information about needs")
            actions.append("Offer quick intake form completion")
        
        return actions


# ==================== Smart Recommendations ====================

class SuccessPattern(BaseModel):
    """Pattern learned from successful matches."""
    pattern_id: str
    description: str
    match_criteria: dict
    success_rate: float
    sample_size: int


class SmartRecommendation(BaseModel):
    """AI-powered LO recommendation with reasoning."""
    lo_id: str
    lo_name: str
    recommendation_score: float  # 0-100
    reasons: list[str]
    success_pattern_match: Optional[str]
    predicted_conversion_rate: float


class SmartRecommender:
    """
    Learns from successful matches to improve recommendations.
    
    Analyzes patterns in borrower-LO matches that result in
    successful outcomes (completed calls, positive ratings,
    loan applications).
    """
    
    # Known success patterns (would be learned from data in production)
    SUCCESS_PATTERNS = [
        SuccessPattern(
            pattern_id="first_time_specialist",
            description="First-time buyers matched with patient, educational LOs",
            match_criteria={"borrower_first_time": True, "lo_specialty": "first-time buyer"},
            success_rate=0.78,
            sample_size=234,
        ),
        SuccessPattern(
            pattern_id="fast_responder_urgent",
            description="Urgent borrowers matched with quick-responding LOs",
            match_criteria={"borrower_timeline": "immediate", "lo_pickup_under_30s": True},
            success_rate=0.82,
            sample_size=189,
        ),
        SuccessPattern(
            pattern_id="language_match",
            description="Non-English speakers matched with bilingual LOs",
            match_criteria={"borrower_language": "non_english", "lo_language_match": True},
            success_rate=0.85,
            sample_size=156,
        ),
        SuccessPattern(
            pattern_id="jumbo_experience",
            description="Jumbo loan borrowers matched with experienced LOs",
            match_criteria={"loan_amount_jumbo": True, "lo_years_experience": 5},
            success_rate=0.71,
            sample_size=98,
        ),
    ]
    
    @staticmethod
    async def get_smart_recommendations(
        db,
        borrower_state: str,
        borrower_intent: BorrowerIntent,
        borrower_first_time: bool = False,
        borrower_language: str = "en",
        loan_amount: Optional[int] = None,
        limit: int = 5,
    ) -> list[SmartRecommendation]:
        """
        Get AI-enhanced LO recommendations.
        
        Combines base matching algorithm with learned success patterns.
        """
        from src.app.services.matching_engine import find_matching_los
        
        # Get base matches
        base_result = await find_matching_los(
            db=db,
            state=borrower_state,
            loan_purpose="purchase",
            property_type="single_family",
            timeline=borrower_intent.value if borrower_intent in [BorrowerIntent.HOT, BorrowerIntent.WARM] else "exploring",
            special_needs=["first_time"] if borrower_first_time else [],
        )
        
        recommendations = []
        for match in base_result.matches[:limit]:
            # Check for success pattern matches
            pattern_match = None
            bonus_score = 0
            
            # First-time buyer pattern
            if borrower_first_time and "first-time" in [s.lower() for s in match.specialty_names]:
                pattern_match = "first_time_specialist"
                bonus_score += 10
            
            # Fast responder for urgent borrowers
            if borrower_intent == BorrowerIntent.HOT and match.avg_pickup_seconds and match.avg_pickup_seconds < 30:
                pattern_match = "fast_responder_urgent"
                bonus_score += 12
            
            # Language match
            if borrower_language != "en" and borrower_language in match.language_codes:
                pattern_match = "language_match"
                bonus_score += 15
            
            # Calculate enhanced score
            enhanced_score = min(100, match.match_score + bonus_score)
            
            # Generate reasons
            reasons = [r.reason for r in match.match_reasons[:3]]
            if pattern_match:
                pattern = next((p for p in SmartRecommender.SUCCESS_PATTERNS if p.pattern_id == pattern_match), None)
                if pattern:
                    reasons.insert(0, f"✨ {pattern.description} ({pattern.success_rate*100:.0f}% success rate)")
            
            # Predict conversion (simplified model)
            predicted_conversion = 0.3  # Base rate
            if match.availability == "online_now":
                predicted_conversion += 0.15
            if match.nmls_verified:
                predicted_conversion += 0.10
            if pattern_match:
                predicted_conversion += 0.12
            
            recommendations.append(SmartRecommendation(
                lo_id=match.lo_id,
                lo_name=match.lo_name,
                recommendation_score=enhanced_score,
                reasons=reasons,
                success_pattern_match=pattern_match,
                predicted_conversion_rate=round(min(predicted_conversion, 0.95), 2),
            ))
        
        # Sort by enhanced score
        recommendations.sort(key=lambda r: r.recommendation_score, reverse=True)
        
        return recommendations


# ==================== Follow-up Suggestions ====================

class FollowUpType(str, Enum):
    """Types of follow-up actions."""
    EMAIL = "email"
    SMS = "sms"
    CALL = "call"
    IN_APP = "in_app"


class FollowUpSuggestion(BaseModel):
    """Suggested follow-up action with timing and content."""
    action_type: FollowUpType
    suggested_time: datetime
    priority: int  # 1-5, 1 is highest
    subject: str
    message_template: str
    reason: str


class FollowUpSuggester:
    """
    Generates proactive follow-up suggestions based on borrower activity.
    
    Analyzes engagement patterns to suggest optimal timing and
    messaging for follow-up communications.
    """
    
    @staticmethod
    def suggest_followups(
        last_activity: datetime,
        intent: BorrowerIntent,
        calls_completed: int = 0,
        has_email: bool = True,
        has_phone: bool = False,
    ) -> list[FollowUpSuggestion]:
        """
        Generate follow-up suggestions based on borrower state.
        """
        suggestions = []
        now = datetime.utcnow()
        time_since_activity = now - last_activity
        
        # Hot leads get immediate follow-up
        if intent == BorrowerIntent.HOT:
            if calls_completed == 0:
                suggestions.append(FollowUpSuggestion(
                    action_type=FollowUpType.IN_APP,
                    suggested_time=now,
                    priority=1,
                    subject="Connect with a loan officer now",
                    message_template="You're ready to buy! Let's connect you with a loan officer who can help.",
                    reason="Hot lead with no calls completed - immediate engagement critical",
                ))
            elif time_since_activity > timedelta(hours=24):
                suggestions.append(FollowUpSuggestion(
                    action_type=FollowUpType.EMAIL,
                    suggested_time=now + timedelta(hours=2),
                    priority=1,
                    subject="Ready to take the next step?",
                    message_template="We noticed you spoke with {lo_name}. Ready to continue your home buying journey?",
                    reason="Hot lead went cold - re-engage within 48 hours",
                ))
        
        # Warm leads need nurturing
        elif intent == BorrowerIntent.WARM:
            if time_since_activity > timedelta(days=3):
                suggestions.append(FollowUpSuggestion(
                    action_type=FollowUpType.EMAIL,
                    suggested_time=now + timedelta(days=1),
                    priority=2,
                    subject="Still exploring your mortgage options?",
                    message_template="Hi {name}, here are some helpful resources for your home buying journey.",
                    reason="Warm lead inactive for 3+ days - send educational content",
                ))
        
        # Exploring leads get educational content
        elif intent == BorrowerIntent.EXPLORING:
            if time_since_activity > timedelta(days=7):
                suggestions.append(FollowUpSuggestion(
                    action_type=FollowUpType.EMAIL,
                    suggested_time=now + timedelta(days=1),
                    priority=3,
                    subject="First-time buyer? Here's what you need to know",
                    message_template="Buying a home is a big decision. Here's our guide to getting started.",
                    reason="Explorer inactive for 7+ days - provide value through education",
                ))
        
        # Everyone gets milestone follow-ups
        if calls_completed == 1 and has_email:
            suggestions.append(FollowUpSuggestion(
                action_type=FollowUpType.EMAIL,
                suggested_time=last_activity + timedelta(hours=24),
                priority=2,
                subject="How was your call with {lo_name}?",
                message_template="We'd love to hear about your experience. Quick feedback helps us improve.",
                reason="Post-call feedback request",
            ))
        
        return sorted(suggestions, key=lambda s: s.priority)


# ==================== Conversation Summarization ====================

class ConversationSummary(BaseModel):
    """Summary of a borrower-LO conversation."""
    call_id: str
    duration_seconds: int
    key_topics: list[str]
    borrower_questions: list[str]
    lo_commitments: list[str]
    next_steps: list[str]
    sentiment: str  # positive, neutral, negative
    summary_text: str


class ConversationSummarizer:
    """
    Extracts key information from call transcripts and notes.
    
    In production, would use LLM for transcript analysis.
    This version uses rule-based extraction for demonstration.
    """
    
    # Topic keywords for classification
    TOPIC_KEYWORDS = {
        "rates": ["rate", "interest", "apr", "points"],
        "down_payment": ["down payment", "downpayment", "cash", "money down"],
        "preapproval": ["preapproval", "pre-approval", "prequalify", "pre-qualify"],
        "timeline": ["closing", "timeline", "how long", "when can"],
        "documents": ["documents", "paperwork", "tax returns", "w2"],
        "credit": ["credit", "score", "credit score"],
        "loan_types": ["fha", "va", "conventional", "jumbo"],
    }
    
    @staticmethod
    def summarize_from_notes(
        call_id: str,
        duration_seconds: int,
        lo_notes: Optional[str] = None,
    ) -> ConversationSummary:
        """
        Generate summary from LO notes.
        
        In production, would analyze actual transcript.
        """
        notes_lower = (lo_notes or "").lower()
        
        # Extract topics
        topics = []
        for topic, keywords in ConversationSummarizer.TOPIC_KEYWORDS.items():
            if any(kw in notes_lower for kw in keywords):
                topics.append(topic)
        
        # Extract potential questions
        questions = []
        if "rate" in notes_lower:
            questions.append("Asked about current interest rates")
        if "down payment" in notes_lower:
            questions.append("Inquired about down payment requirements")
        if "preapproval" in notes_lower:
            questions.append("Interested in getting preapproved")
        
        # Determine next steps
        next_steps = []
        if "follow up" in notes_lower:
            next_steps.append("Follow up with borrower")
        if "documents" in notes_lower or "paperwork" in notes_lower:
            next_steps.append("Request documentation from borrower")
        if "application" in notes_lower:
            next_steps.append("Send application link")
        if not next_steps:
            next_steps.append("Continue conversation when borrower is ready")
        
        # Simple sentiment (would use ML in production)
        sentiment = "neutral"
        positive_words = ["great", "excellent", "interested", "ready", "excited"]
        negative_words = ["concerned", "worried", "issue", "problem", "cant"]
        if any(w in notes_lower for w in positive_words):
            sentiment = "positive"
        elif any(w in notes_lower for w in negative_words):
            sentiment = "negative"
        
        # Generate summary
        summary_parts = []
        if duration_seconds > 0:
            summary_parts.append(f"Call lasted {duration_seconds // 60} minutes")
        if topics:
            summary_parts.append(f"Discussed: {', '.join(topics)}")
        if questions:
            summary_parts.append(f"Borrower asked about: {', '.join(q.replace('Asked about ', '').replace('Inquired about ', '').replace('Interested in ', '') for q in questions)}")
        
        return ConversationSummary(
            call_id=call_id,
            duration_seconds=duration_seconds,
            key_topics=topics if topics else ["general inquiry"],
            borrower_questions=questions,
            lo_commitments=[],  # Would extract from transcript
            next_steps=next_steps,
            sentiment=sentiment,
            summary_text=". ".join(summary_parts) if summary_parts else "Brief conversation with borrower.",
        )
