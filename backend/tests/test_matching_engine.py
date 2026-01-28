"""
Unit tests for the Matching Engine.

Tests:
- Matching engine configuration
- Borrower profile validation
- LOMatch and MatchReason models
"""

import pytest
from pydantic import ValidationError

from src.app.services.matching_engine import (
    MatchingEngine,
    MatchingConfig,
    BorrowerProfile,
    LOMatch,
    MatchReason,
    LoanPurpose,
    PropertyType,
    Timeline,
    SpecialNeed,
    AvailabilityStatus,
)


class TestMatchingEngine:
    """Tests for the matching engine class."""
    
    def test_engine_version_is_set(self):
        """Engine should report version."""
        assert MatchingEngine.VERSION == "2.0.0"
    
    def test_engine_default_config(self):
        """Engine should use default config if none provided."""
        engine = MatchingEngine()
        assert engine.config is not None
        assert engine.config.weight_availability == 0.25
    
    def test_engine_custom_config(self):
        """Engine should accept custom config."""
        config = MatchingConfig(weight_availability=0.40)
        engine = MatchingEngine(config=config)
        assert engine.config.weight_availability == 0.40


class TestMatchingConfig:
    """Tests for matching configuration."""
    
    def test_default_config_weights(self):
        """Should have sensible default weights."""
        config = MatchingConfig()
        
        assert config.weight_availability == 0.25
        assert config.weight_rating == 0.20
        assert config.weight_specialty == 0.20
        assert config.weight_response_time == 0.15
        assert config.weight_experience == 0.10
        assert config.weight_nmls_verified == 0.10
    
    def test_weights_sum_to_one(self):
        """Default weights should sum to 1.0."""
        config = MatchingConfig()
        total = (
            config.weight_availability +
            config.weight_rating +
            config.weight_specialty +
            config.weight_response_time +
            config.weight_experience +
            config.weight_nmls_verified
        )
        assert total == 1.0


class TestBorrowerProfile:
    """Tests for borrower profile model."""
    
    def test_valid_borrower_profile(self):
        """Should create valid borrower profile."""
        profile = BorrowerProfile(
            state="CA",
            loan_purpose=LoanPurpose.PURCHASE,
            property_type=PropertyType.SINGLE_FAMILY,
            timeline=Timeline.IMMEDIATE,
        )
        
        assert profile.state == "CA"
        assert profile.loan_purpose == LoanPurpose.PURCHASE
        assert profile.preferred_language == "en"  # Default
    
    def test_borrower_profile_with_special_needs(self):
        """Should handle special needs list."""
        profile = BorrowerProfile(
            state="TX",
            loan_purpose=LoanPurpose.REFINANCE,
            property_type=PropertyType.CONDO,
            timeline=Timeline.SOON,
            special_needs=[SpecialNeed.FIRST_TIME_BUYER, SpecialNeed.VA_ELIGIBLE],
        )
        
        assert len(profile.special_needs) == 2
        assert SpecialNeed.FIRST_TIME_BUYER in profile.special_needs
    
    def test_borrower_profile_state_validation(self):
        """State must be 2 characters."""
        with pytest.raises(ValidationError):
            BorrowerProfile(
                state="California",  # Too long
                loan_purpose=LoanPurpose.PURCHASE,
                property_type=PropertyType.SINGLE_FAMILY,
                timeline=Timeline.IMMEDIATE,
            )


class TestMatchReason:
    """Tests for match reason model."""
    
    def test_match_reason_creation(self):
        """Should create valid match reason."""
        reason = MatchReason(
            category="verification",
            reason="NMLS credentials verified",
            weight=0.10,
        )
        
        assert reason.category == "verification"
        assert reason.verified is True  # Default
    
    def test_match_reason_unverified(self):
        """Should allow unverified flag."""
        reason = MatchReason(
            category="specialty",
            reason="User reported specialty",
            weight=0.05,
            verified=False,
        )
        
        assert reason.verified is False


class TestLOMatch:
    """Tests for LO match result model."""
    
    def test_lo_match_creation(self):
        """Should create valid LO match."""
        match = LOMatch(
            lo_id="test-123",
            lo_name="John Smith",
            company_name="ABC Mortgage",
            avatar_url=None,
            nmls_id="123456",
            nmls_verified=True,
            match_score=85.5,
            match_reasons=[],
            availability=AvailabilityStatus.ONLINE_NOW,
            avg_pickup_seconds=15.0,
            avg_rating=4.8,
            total_reviews=125,
            years_experience=10,
            has_video=True,
            specialty_names=["FHA", "VA"],
            language_codes=["en", "es"],
        )
        
        assert match.match_score == 85.5
        assert match.nmls_verified is True
    
    def test_lo_match_score_bounds(self):
        """Match score should be 0-100."""
        with pytest.raises(ValidationError):
            LOMatch(
                lo_id="test",
                lo_name="Test",
                company_name=None,
                avatar_url=None,
                nmls_id=None,
                nmls_verified=False,
                match_score=150,  # Invalid - over 100
                match_reasons=[],
                availability=AvailabilityStatus.OFFLINE,
                avg_pickup_seconds=None,
                avg_rating=3.0,
                total_reviews=0,
                years_experience=None,
                has_video=False,
                specialty_names=[],
                language_codes=[],
            )


class TestEnums:
    """Tests for matching enums."""
    
    def test_loan_purpose_values(self):
        """Should have expected loan purpose values."""
        assert LoanPurpose.PURCHASE.value == "purchase"
        assert LoanPurpose.REFINANCE.value == "refinance"
        assert LoanPurpose.HELOC.value == "heloc"
    
    def test_timeline_values(self):
        """Should have expected timeline values."""
        assert Timeline.IMMEDIATE.value == "immediate"
        assert Timeline.SOON.value == "30_days"
        assert Timeline.EXPLORING.value == "exploring"
    
    def test_availability_status_values(self):
        """Should have expected availability values."""
        assert AvailabilityStatus.ONLINE_NOW.value == "online_now"
        assert AvailabilityStatus.BUSY.value == "busy"
        assert AvailabilityStatus.OFFLINE.value == "offline"
