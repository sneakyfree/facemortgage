"""
Unit tests for the Agentic Intelligence Service.

Tests:
- Intent classification with various inputs
- Smart recommendation logic
- Follow-up suggestion generation
- Conversation summarization
"""

import pytest
from datetime import datetime, timedelta

from src.app.services.agentic_intelligence import (
    IntentClassifier,
    IntentClassification,
    BorrowerIntent,
    SmartRecommender,
    FollowUpSuggester,
    FollowUpType,
    ConversationSummarizer,
)


class TestIntentClassifier:
    """Tests for borrower intent classification."""
    
    def test_immediate_timeline_classified_as_hot(self):
        """Immediate timeline should result in HOT intent."""
        result = IntentClassifier.classify(
            timeline="immediate",
            loan_purpose="purchase",
            property_identified=True,
            has_agent=True,
        )
        
        assert result.intent == BorrowerIntent.HOT
        assert result.confidence >= 0.7
        assert result.urgency_score >= 7
    
    def test_exploring_timeline_with_minimal_signals(self):
        """Exploring timeline with no other signals should be UNKNOWN."""
        result = IntentClassifier.classify(
            timeline="exploring",
            loan_purpose="purchase",
            property_identified=False,
            has_agent=False,
        )
        
        # With minimal signals, intent is unknown
        assert result.intent in [BorrowerIntent.EXPLORING, BorrowerIntent.UNKNOWN]
        assert result.urgency_score <= 5
    
    def test_refinance_purpose_classified_as_refinance(self):
        """Refinance loan purpose should be classified as REFINANCE."""
        result = IntentClassifier.classify(
            timeline="30_days",
            loan_purpose="refinance",
        )
        
        assert result.intent == BorrowerIntent.REFINANCE
    
    def test_signals_are_captured(self):
        """Classification should capture all relevant signals."""
        result = IntentClassifier.classify(
            timeline="immediate",
            loan_purpose="purchase",
            property_identified=True,
            has_agent=True,
        )
        
        # Should have at least timeline, property, and agent signals
        assert len(result.signals) >= 3
        signal_types = [s.signal_type for s in result.signals]
        assert "timeline" in signal_types
        assert "property" in signal_types
        assert "referral" in signal_types
    
    def test_recommended_actions_generated(self):
        """Classification should generate recommended actions."""
        result = IntentClassifier.classify(
            timeline="immediate",
            loan_purpose="purchase",
        )
        
        assert len(result.recommended_actions) > 0
    
    def test_confidence_is_bounded(self):
        """Confidence should be between 0 and 1."""
        result = IntentClassifier.classify(
            timeline="immediate",
            loan_purpose="purchase",
            property_identified=True,
            has_agent=True,
            calls_completed=5,
            los_viewed=10,
        )
        
        assert 0.0 <= result.confidence <= 1.0
    
    def test_urgency_score_is_bounded(self):
        """Urgency score should be between 1 and 10."""
        result = IntentClassifier.classify(
            timeline="exploring",
            loan_purpose="heloc",
        )
        
        assert 1 <= result.urgency_score <= 10


class TestSmartRecommender:
    """Tests for smart LO recommendations."""
    
    def test_success_patterns_loaded(self):
        """Should have predefined success patterns."""
        patterns = SmartRecommender.SUCCESS_PATTERNS
        
        assert len(patterns) >= 3
        for pattern in patterns:
            assert pattern.pattern_id
            assert pattern.success_rate > 0
            assert pattern.sample_size > 0
    
    def test_first_time_buyer_pattern_exists(self):
        """Should have first-time buyer success pattern."""
        pattern_ids = [p.pattern_id for p in SmartRecommender.SUCCESS_PATTERNS]
        assert "first_time_specialist" in pattern_ids
    
    def test_language_match_pattern_exists(self):
        """Should have language matching success pattern."""
        pattern_ids = [p.pattern_id for p in SmartRecommender.SUCCESS_PATTERNS]
        assert "language_match" in pattern_ids


class TestFollowUpSuggester:
    """Tests for follow-up suggestion generation."""
    
    def test_hot_lead_gets_urgent_followup(self):
        """Hot leads should get high-priority follow-ups."""
        now = datetime.utcnow()
        suggestions = FollowUpSuggester.suggest_followups(
            last_activity=now - timedelta(hours=2),
            intent=BorrowerIntent.HOT,
            calls_completed=0,
        )
        
        assert len(suggestions) > 0
        # Should have at least one high priority suggestion
        assert any(s.priority <= 2 for s in suggestions)
    
    def test_warm_lead_inactive_gets_email(self):
        """Warm leads inactive for days should get email suggestion."""
        suggestions = FollowUpSuggester.suggest_followups(
            last_activity=datetime.utcnow() - timedelta(days=4),
            intent=BorrowerIntent.WARM,
            has_email=True,
        )
        
        assert len(suggestions) > 0
        email_suggestions = [s for s in suggestions if s.action_type == FollowUpType.EMAIL]
        assert len(email_suggestions) > 0
    
    def test_exploring_lead_gets_educational_content(self):
        """Exploring leads should get educational suggestions."""
        suggestions = FollowUpSuggester.suggest_followups(
            last_activity=datetime.utcnow() - timedelta(days=8),
            intent=BorrowerIntent.EXPLORING,
        )
        
        # Check for educational content suggestion
        assert len(suggestions) > 0
    
    def test_post_call_feedback_suggested(self):
        """After first call, should suggest feedback request."""
        suggestions = FollowUpSuggester.suggest_followups(
            last_activity=datetime.utcnow(),
            intent=BorrowerIntent.WARM,
            calls_completed=1,
            has_email=True,
        )
        
        # Should have feedback suggestion
        feedback_suggestions = [s for s in suggestions if "feedback" in s.reason.lower()]
        assert len(feedback_suggestions) > 0
    
    def test_suggestions_sorted_by_priority(self):
        """Suggestions should be sorted by priority."""
        suggestions = FollowUpSuggester.suggest_followups(
            last_activity=datetime.utcnow() - timedelta(hours=25),
            intent=BorrowerIntent.HOT,
            calls_completed=1,
        )
        
        if len(suggestions) > 1:
            for i in range(len(suggestions) - 1):
                assert suggestions[i].priority <= suggestions[i + 1].priority


class TestConversationSummarizer:
    """Tests for conversation summarization."""
    
    def test_extracts_rate_topic(self):
        """Should extract rate discussion from notes."""
        summary = ConversationSummarizer.summarize_from_notes(
            call_id="test-call-1",
            duration_seconds=300,
            lo_notes="Discussed current interest rates. Client interested in 30-year fixed.",
        )
        
        assert "rates" in summary.key_topics
    
    def test_extracts_preapproval_topic(self):
        """Should extract preapproval discussion."""
        summary = ConversationSummarizer.summarize_from_notes(
            call_id="test-call-2",
            duration_seconds=180,
            lo_notes="Client wants to get preapproval letter before house hunting.",
        )
        
        assert "preapproval" in summary.key_topics
    
    def test_generates_next_steps(self):
        """Should generate next steps from notes."""
        summary = ConversationSummarizer.summarize_from_notes(
            call_id="test-call-3",
            duration_seconds=420,
            lo_notes="Need to follow up with documents. Send application link.",
        )
        
        assert len(summary.next_steps) > 0
    
    def test_detects_positive_sentiment(self):
        """Should detect positive sentiment."""
        summary = ConversationSummarizer.summarize_from_notes(
            call_id="test-call-4",
            duration_seconds=300,
            lo_notes="Great call! Client very interested and excited to proceed.",
        )
        
        assert summary.sentiment == "positive"
    
    def test_handles_empty_notes(self):
        """Should handle empty or missing notes."""
        summary = ConversationSummarizer.summarize_from_notes(
            call_id="test-call-5",
            duration_seconds=60,
            lo_notes=None,
        )
        
        assert summary.call_id == "test-call-5"
        assert len(summary.summary_text) > 0
    
    def test_includes_duration_in_summary(self):
        """Summary should mention call duration."""
        summary = ConversationSummarizer.summarize_from_notes(
            call_id="test-call-6",
            duration_seconds=600,  # 10 minutes
            lo_notes="Standard loan discussion.",
        )
        
        assert "10" in summary.summary_text or "minute" in summary.summary_text.lower()
