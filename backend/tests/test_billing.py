"""
Tests for billing and subscription endpoints.

Tests cover:
- Checkout session creation
- Subscription management
- Bid wallet operations
- Stripe webhook handling
"""
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.billing import Subscription, BidWallet, BidTransaction, SubscriptionStatus
from src.app.models.professional import ProfessionalProfile, SubscriptionTier
from src.app.models.user import User
from src.app.core.dependencies import require_professional


class TestSubscriptionPlans:
    """Tests for subscription plan listing."""

    @pytest.mark.asyncio
    async def test_get_subscription_plans(
        self,
        client: AsyncClient,
        mock_stripe_service,
    ):
        """Should return list of subscription plans."""
        with patch("src.app.api.v1.routes.billing.get_stripe_service", return_value=mock_stripe_service):
            response = await client.get("/api/v1/billing/plans")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Check structure of first plan
        if data:
            plan = data[0]
            assert "tier" in plan
            assert "name" in plan
            assert "price" in plan
            assert "features" in plan

    @pytest.mark.asyncio
    async def test_get_subscription_plans_no_auth_required(
        self,
        client: AsyncClient,
        mock_stripe_service,
    ):
        """Subscription plans should be publicly accessible."""
        with patch("src.app.api.v1.routes.billing.get_stripe_service", return_value=mock_stripe_service):
            response = await client.get("/api/v1/billing/plans")

        assert response.status_code == 200


class TestCheckoutSessionCreation:
    """Tests for checkout session creation."""

    @pytest.mark.asyncio
    async def test_deposit_requires_authentication(
        self,
        client: AsyncClient,
    ):
        """Deposit endpoint should require authentication."""
        response = await client.post(
            "/api/v1/billing/wallet/deposit",
            json={"amount": 50.00},
        )

        assert response.status_code == 401


class TestWebhookHandling:
    """Tests for Stripe webhook handling."""

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(
        self,
        client: AsyncClient,
        mock_stripe_service,
    ):
        """Should reject webhook with invalid signature."""
        # Use ValueError which is caught by the route handler
        mock_stripe_service.construct_webhook_event = MagicMock(
            side_effect=ValueError("Invalid signature")
        )

        with patch("src.app.api.v1.routes.billing.get_stripe_service", return_value=mock_stripe_service):
            response = await client.post(
                "/api/v1/billing/webhook",
                content=json.dumps({"type": "test.event", "data": {}}),
                headers={
                    "Stripe-Signature": "invalid_signature",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 400


class TestBidWallet:
    """Tests for bid wallet operations."""

    @pytest.mark.asyncio
    async def test_wallet_requires_auth(
        self,
        client: AsyncClient,
    ):
        """Wallet endpoint should require authentication."""
        response = await client.get("/api/v1/billing/wallet")
        assert response.status_code == 401
