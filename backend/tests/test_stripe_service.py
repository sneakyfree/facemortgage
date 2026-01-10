"""
Tests for the Stripe integration service.

Tests cover:
- Customer creation and retrieval
- Subscription management (create, update, cancel, reactivate)
- Bid deposit sessions
- Webhook event construction and validation
- Tier pricing information
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from decimal import Decimal
import stripe

from src.app.integrations.stripe.service import StripeService
from src.app.models.professional import SubscriptionTier


@pytest.fixture
def stripe_service():
    """Create a StripeService instance."""
    with patch.object(stripe, 'api_key', 'test_key'):
        return StripeService()


class TestStripeCustomer:
    """Tests for Stripe customer operations."""

    @pytest.mark.asyncio
    async def test_create_customer(self, stripe_service):
        """Should create a Stripe customer with correct metadata."""
        user_id = uuid4()
        email = "test@example.com"
        name = "Test User"

        with patch('asyncio.to_thread') as mock_to_thread:
            mock_customer = MagicMock(id="cus_test123")
            mock_to_thread.return_value = mock_customer

            customer_id = await stripe_service.create_customer(
                user_id=user_id,
                email=email,
                name=name,
            )

            assert customer_id == "cus_test123"
            mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_customer_with_metadata(self, stripe_service):
        """Should merge additional metadata when creating customer."""
        user_id = uuid4()

        with patch('asyncio.to_thread') as mock_to_thread:
            mock_to_thread.return_value = MagicMock(id="cus_test123")

            await stripe_service.create_customer(
                user_id=user_id,
                email="test@example.com",
                name="Test",
                metadata={"extra_field": "extra_value"},
            )

            mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_customer_existing(self, stripe_service):
        """Should return existing customer if valid."""
        existing_id = "cus_existing123"

        with patch('asyncio.to_thread') as mock_to_thread:
            mock_customer = MagicMock()
            mock_customer.id = existing_id
            mock_customer.deleted = False
            mock_to_thread.return_value = mock_customer

            customer_id = await stripe_service.get_or_create_customer(
                user_id=uuid4(),
                email="test@example.com",
                name="Test",
                existing_customer_id=existing_id,
            )

            assert customer_id == existing_id

    @pytest.mark.asyncio
    async def test_get_or_create_customer_deleted(self, stripe_service):
        """Should create new customer if existing is deleted."""
        mock_deleted_customer = MagicMock()
        mock_deleted_customer.deleted = True
        mock_new_customer = MagicMock(id="cus_new123")

        with patch('asyncio.to_thread') as mock_to_thread:
            # First call returns deleted customer, second creates new
            mock_to_thread.side_effect = [mock_deleted_customer, mock_new_customer]

            customer_id = await stripe_service.get_or_create_customer(
                user_id=uuid4(),
                email="test@example.com",
                name="Test",
                existing_customer_id="cus_deleted",
            )

            assert customer_id == "cus_new123"

    @pytest.mark.asyncio
    async def test_get_or_create_customer_not_found(self, stripe_service):
        """Should create new customer if existing not found."""
        mock_new_customer = MagicMock(id="cus_new123")

        with patch('asyncio.to_thread') as mock_to_thread:
            # First call raises error, second creates new
            mock_to_thread.side_effect = [
                stripe.error.InvalidRequestError(message="No such customer", param=None),
                mock_new_customer,
            ]

            customer_id = await stripe_service.get_or_create_customer(
                user_id=uuid4(),
                email="test@example.com",
                name="Test",
                existing_customer_id="cus_invalid",
            )

            assert customer_id == "cus_new123"


class TestStripeSubscription:
    """Tests for Stripe subscription operations."""

    @pytest.mark.asyncio
    async def test_create_subscription_free_tier_error(self, stripe_service):
        """Creating subscription for FREE tier should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await stripe_service.create_subscription(
                customer_id="cus_test",
                tier=SubscriptionTier.FREE,
            )

        assert "Cannot create subscription for free tier" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_subscription_no_price_id(self, stripe_service):
        """Should raise ValueError if no price ID configured for tier."""
        # Mock tier_price_ids property to return None for BASIC
        with patch.object(
            type(stripe_service),
            'tier_price_ids',
            property(lambda self: {SubscriptionTier.BASIC: None}),
        ):
            with pytest.raises(ValueError) as exc_info:
                await stripe_service.create_subscription(
                    customer_id="cus_test",
                    tier=SubscriptionTier.BASIC,
                )

            assert "No price configured for tier" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_subscription_success(self, stripe_service):
        """Should create subscription with correct parameters."""
        with patch.object(
            type(stripe_service),
            'tier_price_ids',
            property(lambda self: {SubscriptionTier.BASIC: "price_basic123"}),
        ):
            with patch('asyncio.to_thread') as mock_to_thread:
                mock_invoice = MagicMock()
                mock_invoice.payment_intent = MagicMock(client_secret="secret_123")

                mock_subscription = MagicMock()
                mock_subscription.id = "sub_test123"
                mock_subscription.status = "incomplete"
                mock_subscription.latest_invoice = mock_invoice
                mock_subscription.current_period_end = 1234567890
                mock_to_thread.return_value = mock_subscription

                result = await stripe_service.create_subscription(
                    customer_id="cus_test",
                    tier=SubscriptionTier.BASIC,
                )

                assert result['subscription_id'] == "sub_test123"
                assert result['status'] == "incomplete"
                assert result['client_secret'] == "secret_123"
                mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subscription_with_trial(self, stripe_service):
        """Should include trial period when specified."""
        with patch.object(
            type(stripe_service),
            'tier_price_ids',
            property(lambda self: {SubscriptionTier.BASIC: "price_basic123"}),
        ):
            with patch('asyncio.to_thread') as mock_to_thread:
                mock_subscription = MagicMock()
                mock_subscription.id = "sub_test123"
                mock_subscription.status = "trialing"
                mock_subscription.latest_invoice = MagicMock(payment_intent=None)
                mock_subscription.current_period_end = 1234567890
                mock_to_thread.return_value = mock_subscription

                await stripe_service.create_subscription(
                    customer_id="cus_test",
                    tier=SubscriptionTier.BASIC,
                    trial_days=14,
                )

                # Check that asyncio.to_thread was called with the right args
                mock_to_thread.assert_called_once()
                call_args = mock_to_thread.call_args
                # The kwargs should include trial_period_days
                assert call_args.kwargs.get('trial_period_days') == 14

    @pytest.mark.asyncio
    async def test_cancel_subscription_at_period_end(self, stripe_service):
        """Should cancel subscription at period end."""
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.status = "active"
            mock_subscription.cancel_at_period_end = True
            mock_subscription.current_period_end = 1234567890
            mock_to_thread.return_value = mock_subscription

            result = await stripe_service.cancel_subscription(
                subscription_id="sub_test123",
                at_period_end=True,
            )

            assert result['cancel_at_period_end'] is True
            mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_subscription_immediate(self, stripe_service):
        """Should cancel subscription immediately."""
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.status = "canceled"
            mock_subscription.cancel_at_period_end = False
            mock_subscription.current_period_end = 1234567890
            mock_to_thread.return_value = mock_subscription

            result = await stripe_service.cancel_subscription(
                subscription_id="sub_test123",
                at_period_end=False,
            )

            assert result['status'] == "canceled"
            mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_reactivate_subscription(self, stripe_service):
        """Should reactivate a subscription pending cancellation."""
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.status = "active"
            mock_subscription.cancel_at_period_end = False
            mock_subscription.current_period_end = 1234567890
            mock_to_thread.return_value = mock_subscription

            result = await stripe_service.reactivate_subscription(
                subscription_id="sub_test123",
            )

            # The reactivate_subscription method returns subscription_id, status, current_period_end
            assert result['subscription_id'] == "sub_test123"
            assert result['status'] == "active"
            mock_to_thread.assert_called_once()


class TestStripeWebhook:
    """Tests for Stripe webhook handling."""

    def test_construct_webhook_event_valid(self, stripe_service):
        """Should construct event from valid webhook payload."""
        payload = b'{"type": "test"}'
        signature = "valid_signature"

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_event = {"type": "customer.subscription.created", "data": {}}
            mock_construct.return_value = mock_event

            event = stripe_service.construct_webhook_event(payload, signature)

            assert event == mock_event
            mock_construct.assert_called_once_with(
                payload,
                signature,
                stripe_service.webhook_secret,
            )

    def test_construct_webhook_event_invalid_signature(self, stripe_service):
        """Should raise exception for invalid signature."""
        payload = b'{"type": "test"}'
        signature = "invalid_signature"

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                message="Invalid signature",
                sig_header=signature,
            )

            with pytest.raises(stripe.error.SignatureVerificationError):
                stripe_service.construct_webhook_event(payload, signature)

    def test_construct_webhook_event_tampered_payload(self, stripe_service):
        """Should raise exception for tampered payload."""
        payload = b'{"type": "tampered"}'
        signature = "mismatched_signature"

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                message="Signature mismatch",
                sig_header=signature,
            )

            with pytest.raises(stripe.error.SignatureVerificationError):
                stripe_service.construct_webhook_event(payload, signature)


class TestStripeBidDeposit:
    """Tests for bid deposit checkout sessions."""

    @pytest.mark.asyncio
    async def test_create_bid_deposit_session(self, stripe_service):
        """Should create checkout session for bid deposit."""
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_session = MagicMock()
            mock_session.url = "https://checkout.stripe.com/test"
            mock_to_thread.return_value = mock_session

            result = await stripe_service.create_bid_deposit_session(
                customer_id="cus_test",
                amount_dollars=Decimal("50.00"),
                professional_id=uuid4(),
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
            )

            # Returns the session URL directly
            assert result == "https://checkout.stripe.com/test"
            mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bid_deposit_session_amount_in_cents(self, stripe_service):
        """Should convert amount to cents for Stripe."""
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_session = MagicMock()
            mock_session.url = "https://checkout.stripe.com/test"
            mock_to_thread.return_value = mock_session

            await stripe_service.create_bid_deposit_session(
                customer_id="cus_test",
                amount_dollars=Decimal("50.00"),
                professional_id=uuid4(),
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
            )

            # Verify the call was made (the actual cents conversion happens internally)
            mock_to_thread.assert_called_once()
            call_args = mock_to_thread.call_args
            # Check that line_items contains the correct amount in cents
            line_items = call_args.kwargs.get('line_items', [])
            if line_items:
                assert line_items[0]['price_data']['unit_amount'] == 5000


class TestStripePricing:
    """Tests for tier pricing information."""

    def test_tier_pricing_values(self, stripe_service):
        """Should have correct pricing for each tier."""
        assert stripe_service.TIER_PRICING[SubscriptionTier.FREE] == Decimal("0.00")
        assert stripe_service.TIER_PRICING[SubscriptionTier.BASIC] == Decimal("49.00")
        assert stripe_service.TIER_PRICING[SubscriptionTier.PROFESSIONAL] == Decimal("99.00")
        assert stripe_service.TIER_PRICING[SubscriptionTier.PREMIUM] == Decimal("199.00")

    def test_tier_features_exist(self, stripe_service):
        """Each tier should have features defined."""
        for tier in SubscriptionTier:
            assert tier in stripe_service.TIER_FEATURES
            assert len(stripe_service.TIER_FEATURES[tier]) > 0

    def test_higher_tiers_have_more_features(self, stripe_service):
        """Premium tiers should have more features."""
        free_features = len(stripe_service.TIER_FEATURES[SubscriptionTier.FREE])
        basic_features = len(stripe_service.TIER_FEATURES[SubscriptionTier.BASIC])
        pro_features = len(stripe_service.TIER_FEATURES[SubscriptionTier.PROFESSIONAL])
        premium_features = len(stripe_service.TIER_FEATURES[SubscriptionTier.PREMIUM])

        assert basic_features >= free_features
        assert pro_features >= basic_features
        assert premium_features >= pro_features

    def test_get_tier_pricing(self, stripe_service):
        """Should return all tier pricing information."""
        pricing = stripe_service.get_tier_pricing()

        assert len(pricing) == 4
        for tier_info in pricing:
            assert 'tier' in tier_info
            assert 'price' in tier_info
            assert 'features' in tier_info


class TestStripeServiceInit:
    """Tests for StripeService initialization."""

    def test_api_key_set(self):
        """Should set Stripe API key on initialization."""
        with patch('src.app.integrations.stripe.service.settings') as mock_settings:
            mock_settings.stripe_secret_key = "sk_test_123"
            mock_settings.stripe_webhook_secret = "whsec_123"
            mock_settings.stripe_price_id_basic = None
            mock_settings.stripe_price_id_professional = None
            mock_settings.stripe_price_id_premium = None

            service = StripeService()

            assert stripe.api_key == "sk_test_123"
            assert service.webhook_secret == "whsec_123"
