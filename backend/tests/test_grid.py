"""
Tests for the grid ranking and service.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.app.grid.ranking import (
    GridRankingService,
    RankingWeights,
    RankedProfessional,
)
from src.app.models.professional import SubscriptionTier


class TestGridRanking:
    """Tests for the grid ranking algorithm."""

    def test_default_weights_sum_to_one(self):
        """Weights should sum to 1.0."""
        weights = RankingWeights()
        assert weights.validate()

    def test_custom_weights_validation(self):
        """Custom weights that don't sum to 1.0 should fail."""
        weights = RankingWeights(
            bid_amount=0.5,
            subscription_tier=0.5,
            rating=0.5,
            pickup_time=0.5,
            time_online=0.5,
            recency=0.5,
        )
        assert not weights.validate()

    def test_calculate_score_all_zeros(self):
        """Score with all zero inputs should be minimal but valid."""
        service = GridRankingService()
        scores = service.calculate_score(
            bid_amount=Decimal("0"),
            subscription_tier=SubscriptionTier.FREE,
            avg_rating=None,
            avg_pickup_time_seconds=None,
            time_online_today_seconds=0,
            last_activity=None,
        )

        assert scores["total"] >= 0
        assert scores["total"] <= 1
        assert scores["bid"] == 0
        assert scores["tier"] == 0

    def test_calculate_score_max_values(self):
        """Score with max inputs should approach 1.0."""
        service = GridRankingService()
        scores = service.calculate_score(
            bid_amount=Decimal("100.00"),
            subscription_tier=SubscriptionTier.PREMIUM,
            avg_rating=5.0,
            avg_pickup_time_seconds=1.0,  # Very fast
            time_online_today_seconds=8 * 3600,  # 8 hours
            last_activity=datetime.utcnow(),
        )

        assert scores["total"] > 0.9
        assert scores["bid"] == 1.0
        assert scores["tier"] == 1.0
        assert scores["rating"] == 1.0
        assert scores["pickup"] > 0.95
        assert scores["online"] == 1.0
        assert scores["recency"] > 0.99

    def test_tier_scoring(self):
        """Higher tiers should score higher."""
        service = GridRankingService()

        free_scores = service.calculate_score(
            bid_amount=Decimal("0"),
            subscription_tier=SubscriptionTier.FREE,
            avg_rating=4.0,
            avg_pickup_time_seconds=10,
            time_online_today_seconds=3600,
            last_activity=datetime.utcnow(),
        )

        premium_scores = service.calculate_score(
            bid_amount=Decimal("0"),
            subscription_tier=SubscriptionTier.PREMIUM,
            avg_rating=4.0,
            avg_pickup_time_seconds=10,
            time_online_today_seconds=3600,
            last_activity=datetime.utcnow(),
        )

        assert premium_scores["tier"] > free_scores["tier"]
        assert premium_scores["total"] > free_scores["total"]

    def test_bid_scoring(self):
        """Higher bids should score higher."""
        service = GridRankingService()

        low_bid = service.calculate_score(
            bid_amount=Decimal("5.00"),
            subscription_tier=SubscriptionTier.BASIC,
            avg_rating=4.0,
            avg_pickup_time_seconds=10,
            time_online_today_seconds=3600,
            last_activity=datetime.utcnow(),
        )

        high_bid = service.calculate_score(
            bid_amount=Decimal("50.00"),
            subscription_tier=SubscriptionTier.BASIC,
            avg_rating=4.0,
            avg_pickup_time_seconds=10,
            time_online_today_seconds=3600,
            last_activity=datetime.utcnow(),
        )

        assert high_bid["bid"] > low_bid["bid"]
        assert high_bid["total"] > low_bid["total"]

    def test_pickup_time_scoring(self):
        """Faster pickup times should score higher."""
        service = GridRankingService()

        slow = service.calculate_score(
            bid_amount=Decimal("10.00"),
            subscription_tier=SubscriptionTier.BASIC,
            avg_rating=4.0,
            avg_pickup_time_seconds=30,
            time_online_today_seconds=3600,
            last_activity=datetime.utcnow(),
        )

        fast = service.calculate_score(
            bid_amount=Decimal("10.00"),
            subscription_tier=SubscriptionTier.BASIC,
            avg_rating=4.0,
            avg_pickup_time_seconds=5,
            time_online_today_seconds=3600,
            last_activity=datetime.utcnow(),
        )

        assert fast["pickup"] > slow["pickup"]

    def test_recency_decay(self):
        """Recency score should decay over time."""
        service = GridRankingService()

        recent = service.calculate_score(
            bid_amount=Decimal("10.00"),
            subscription_tier=SubscriptionTier.BASIC,
            avg_rating=4.0,
            avg_pickup_time_seconds=10,
            time_online_today_seconds=3600,
            last_activity=datetime.utcnow(),
        )

        old = service.calculate_score(
            bid_amount=Decimal("10.00"),
            subscription_tier=SubscriptionTier.BASIC,
            avg_rating=4.0,
            avg_pickup_time_seconds=10,
            time_online_today_seconds=3600,
            last_activity=datetime.utcnow() - timedelta(hours=12),
        )

        very_old = service.calculate_score(
            bid_amount=Decimal("10.00"),
            subscription_tier=SubscriptionTier.BASIC,
            avg_rating=4.0,
            avg_pickup_time_seconds=10,
            time_online_today_seconds=3600,
            last_activity=datetime.utcnow() - timedelta(hours=48),
        )

        assert recent["recency"] > old["recency"]
        assert old["recency"] > very_old["recency"]
        assert very_old["recency"] == 0  # Beyond 24h window


class TestDataProvider:
    """Tests for the external data provider."""

    @pytest.mark.asyncio
    async def test_datagod_provider_stats(self):
        """Datagod provider should return valid stats."""
        from src.app.integrations.data_providers.datagod import DatagodProvider

        provider = DatagodProvider()
        stats = await provider.get_professional_stats("123456")

        assert stats is not None
        assert stats.nmls_id == "123456"
        assert stats.license is not None
        assert stats.years_in_industry is not None
        assert stats.loans_last_12_months >= 0

    @pytest.mark.asyncio
    async def test_datagod_provider_deterministic(self):
        """Same NMLS ID should return same data."""
        from src.app.integrations.data_providers.datagod import DatagodProvider

        provider = DatagodProvider()

        stats1 = await provider.get_professional_stats("999999")
        stats2 = await provider.get_professional_stats("999999")

        assert stats1.years_in_industry == stats2.years_in_industry
        assert stats1.total_loans_career == stats2.total_loans_career
        assert stats1.license.name == stats2.license.name

    @pytest.mark.asyncio
    async def test_datagod_provider_verify_valid_nmls(self):
        """Valid NMLS should verify successfully."""
        from src.app.integrations.data_providers.datagod import DatagodProvider

        provider = DatagodProvider()
        is_valid = await provider.verify_nmls("123456")
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_datagod_provider_verify_invalid_nmls(self):
        """Invalid NMLS format should fail verification."""
        from src.app.integrations.data_providers.datagod import DatagodProvider

        provider = DatagodProvider()

        # Too short
        assert await provider.verify_nmls("12345") is False

        # Non-numeric
        assert await provider.verify_nmls("ABCDEF") is False

    @pytest.mark.asyncio
    async def test_factory_returns_provider(self):
        """Factory should return configured provider."""
        from src.app.integrations.data_providers.factory import DataProviderFactory

        provider = DataProviderFactory.get_provider("datagod")
        assert provider is not None
        assert provider.provider_name == "Datagod"

    @pytest.mark.asyncio
    async def test_factory_unknown_provider(self):
        """Factory should raise for unknown provider."""
        from src.app.integrations.data_providers.factory import DataProviderFactory

        with pytest.raises(ValueError):
            DataProviderFactory.get_provider("unknown_provider")
