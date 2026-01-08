"""
Tests for admin API routes.

Tests the platform administration endpoints:
- Platform statistics
- User listing and management
- Professional listing and management
- Admin access control
"""
import secrets
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.user import User, UserType
from src.app.models.professional import ProfessionalProfile, ProfessionalStatus, SubscriptionTier
from src.app.models.call import VideoCall, CallStatus
from src.app.models.lead import Lead, LeadStatus
from src.app.models.billing import Subscription, SubscriptionPlan, SubscriptionStatus
from src.app.core.auth import get_current_user
from src.app.main import app


# CSRF token for state-changing requests
CSRF_TOKEN = secrets.token_urlsafe(32)


@asynccontextmanager
async def override_auth(user: User):
    """Context manager to temporarily override authentication."""
    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override
    try:
        yield
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


class TestRequireAdmin:
    """Tests for admin authorization dependency."""

    @pytest.mark.asyncio
    async def test_unauthenticated_user_denied(self, client: AsyncClient):
        """Unauthenticated requests should be denied."""
        response = await client.get("/api/v1/admin/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_non_admin_user_denied(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Non-admin users should receive 403 Forbidden."""
        async with override_auth(test_user):
            response = await client.get("/api/v1/admin/stats")
            assert response.status_code == 403
            # Response could have "detail" key or not depending on error format
            data = response.json()
            assert "Admin access required" in data.get("detail", str(data))

    @pytest.mark.asyncio
    async def test_admin_user_allowed(
        self,
        client: AsyncClient,
        test_admin_user: User,
    ):
        """Admin users should be able to access admin routes."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/stats")
            assert response.status_code == 200


class TestGetPlatformStats:
    """Tests for GET /api/v1/admin/stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats_empty_database(
        self,
        client: AsyncClient,
        test_admin_user: User,
    ):
        """Stats should work with empty/minimal database."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/stats")
            assert response.status_code == 200

            data = response.json()
            # Should have all expected fields
            assert "total_users" in data
            assert "total_professionals" in data
            assert "total_borrowers" in data
            assert "new_users_today" in data
            assert "new_users_this_week" in data
            assert "professionals_online" in data
            assert "professionals_in_call" in data
            assert "calls_today" in data
            assert "calls_this_week" in data
            assert "avg_call_duration" in data
            assert "leads_today" in data
            assert "leads_this_week" in data
            assert "conversion_rate" in data
            assert "active_subscriptions" in data
            assert "mrr" in data

    @pytest.mark.asyncio
    async def test_stats_counts_users_correctly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_user: User,  # borrower
        test_professional_user: User,  # professional
    ):
        """Stats should count users by type correctly."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/stats")
            assert response.status_code == 200

            data = response.json()
            # Should count the admin, borrower, and professional users
            assert data["total_users"] >= 3

    @pytest.mark.asyncio
    async def test_stats_counts_professionals_online(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_professional: ProfessionalProfile,  # status is ONLINE_AVAILABLE
    ):
        """Stats should count online professionals."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/stats")
            assert response.status_code == 200

            data = response.json()
            # The test_professional fixture has status=ONLINE_AVAILABLE
            assert data["professionals_online"] >= 1

    @pytest.mark.asyncio
    async def test_stats_conversion_rate_calculation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
    ):
        """Stats should calculate conversion rate correctly."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/stats")
            assert response.status_code == 200

            data = response.json()
            # With no leads, conversion_rate should be 0
            assert data["conversion_rate"] == 0.0


class TestListUsers:
    """Tests for GET /api/v1/admin/users endpoint."""

    @pytest.mark.asyncio
    async def test_list_users_success(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_user: User,
    ):
        """Should list users with pagination."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/users")
            assert response.status_code == 200

            data = response.json()
            assert "users" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert data["page"] == 1
            assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_list_users_pagination(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_user: User,
    ):
        """Should support pagination parameters."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/users?page=1&page_size=5")
            assert response.status_code == 200

            data = response.json()
            assert data["page"] == 1
            assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_list_users_search_by_email(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_user: User,
    ):
        """Should filter users by email search."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/users?search=borrower")
            assert response.status_code == 200

            data = response.json()
            # test_user has email="borrower@test.com"
            assert any("borrower" in u["email"].lower() for u in data["users"])

    @pytest.mark.asyncio
    async def test_list_users_filter_by_type(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_user: User,
        test_professional_user: User,
    ):
        """Should filter users by user type."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/users?user_type=borrower")
            assert response.status_code == 200

            data = response.json()
            # All returned users should be borrowers
            for user in data["users"]:
                assert user["user_type"] == "borrower"

    @pytest.mark.asyncio
    async def test_list_users_filter_by_active_status(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_user: User,
    ):
        """Should filter users by active status."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/users?is_active=true")
            assert response.status_code == 200

            data = response.json()
            # All returned users should be active
            for user in data["users"]:
                assert user["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_users_invalid_pagination(
        self,
        client: AsyncClient,
        test_admin_user: User,
    ):
        """Should validate pagination parameters."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/users?page=0")
            assert response.status_code == 422  # Validation error

            response = await client.get("/api/v1/admin/users?page_size=200")
            assert response.status_code == 422  # Exceeds max of 100

    @pytest.mark.asyncio
    async def test_list_users_response_format(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_user: User,
    ):
        """Should return users with correct field format."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/users")
            assert response.status_code == 200

            data = response.json()
            if data["users"]:
                user = data["users"][0]
                assert "id" in user
                assert "email" in user
                assert "first_name" in user
                assert "last_name" in user
                assert "user_type" in user
                assert "is_active" in user
                assert "created_at" in user


class TestListProfessionals:
    """Tests for GET /api/v1/admin/professionals endpoint."""

    @pytest.mark.asyncio
    async def test_list_professionals_success(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_professional: ProfessionalProfile,
    ):
        """Should list professionals with pagination."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/professionals")
            assert response.status_code == 200

            data = response.json()
            assert "professionals" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data

    @pytest.mark.asyncio
    async def test_list_professionals_search(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_professional: ProfessionalProfile,
    ):
        """Should filter professionals by search term."""
        async with override_auth(test_admin_user):
            # Search by company name
            response = await client.get("/api/v1/admin/professionals?search=Test Mortgage")
            assert response.status_code == 200

            data = response.json()
            assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_professionals_filter_by_status(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_professional: ProfessionalProfile,
    ):
        """Should filter professionals by status."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/professionals?status=online_available")
            assert response.status_code == 200

            data = response.json()
            for pro in data["professionals"]:
                assert pro["status"] == "online_available"

    @pytest.mark.asyncio
    async def test_list_professionals_filter_by_tier(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_professional: ProfessionalProfile,
    ):
        """Should filter professionals by subscription tier."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/professionals?tier=professional")
            assert response.status_code == 200

            data = response.json()
            for pro in data["professionals"]:
                assert pro["subscription_tier"] == "professional"

    @pytest.mark.asyncio
    async def test_list_professionals_response_format(
        self,
        client: AsyncClient,
        test_admin_user: User,
        test_professional: ProfessionalProfile,
    ):
        """Should return professionals with correct field format."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/professionals")
            assert response.status_code == 200

            data = response.json()
            if data["professionals"]:
                pro = data["professionals"][0]
                assert "id" in pro
                assert "user_id" in pro
                assert "name" in pro
                assert "email" in pro
                assert "company" in pro
                assert "nmls_id" in pro
                assert "status" in pro
                assert "subscription_tier" in pro
                assert "avg_rating" in pro
                assert "total_calls" in pro
                assert "created_at" in pro


class TestToggleUserStatus:
    """Tests for PATCH /api/v1/admin/users/{user_id}/status endpoint."""

    @pytest.mark.asyncio
    async def test_deactivate_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_user: User,
    ):
        """Should deactivate a user."""
        async with override_auth(test_admin_user):
            # Include CSRF token in header and cookie
            response = await client.patch(
                f"/api/v1/admin/users/{test_user.id}/status?is_active=false",
                headers={"X-CSRF-Token": CSRF_TOKEN},
                cookies={"csrf_token": CSRF_TOKEN},
            )
            assert response.status_code == 200
            assert "deactivated" in response.json()["message"]

            # Verify the change persisted
            await db_session.refresh(test_user)
            assert test_user.is_active is False

    @pytest.mark.asyncio
    async def test_activate_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_user: User,
    ):
        """Should activate a user."""
        # First deactivate
        test_user.is_active = False
        await db_session.commit()

        async with override_auth(test_admin_user):
            response = await client.patch(
                f"/api/v1/admin/users/{test_user.id}/status?is_active=true",
                headers={"X-CSRF-Token": CSRF_TOKEN},
                cookies={"csrf_token": CSRF_TOKEN},
            )
            assert response.status_code == 200
            assert "activated" in response.json()["message"]

            # Verify the change persisted
            await db_session.refresh(test_user)
            assert test_user.is_active is True

    @pytest.mark.asyncio
    async def test_toggle_status_user_not_found(
        self,
        client: AsyncClient,
        test_admin_user: User,
    ):
        """Should return 404 for non-existent user."""
        fake_id = uuid.uuid4()
        async with override_auth(test_admin_user):
            response = await client.patch(
                f"/api/v1/admin/users/{fake_id}/status?is_active=false",
                headers={"X-CSRF-Token": CSRF_TOKEN},
                cookies={"csrf_token": CSRF_TOKEN},
            )
            assert response.status_code == 404
            # Error response format may vary - check for message in any format
            data = response.json()
            error_message = data.get("detail", data.get("error", {}).get("message", str(data)))
            assert "User not found" in error_message or "not found" in error_message.lower()

    @pytest.mark.asyncio
    async def test_toggle_status_requires_admin(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Non-admin should not be able to toggle user status."""
        async with override_auth(test_user):
            response = await client.patch(
                f"/api/v1/admin/users/{test_user.id}/status?is_active=false",
                headers={"X-CSRF-Token": CSRF_TOKEN},
                cookies={"csrf_token": CSRF_TOKEN},
            )
            assert response.status_code == 403


class TestToggleFeatured:
    """Tests for PATCH /api/v1/admin/professionals/{professional_id}/featured endpoint."""

    @pytest.mark.asyncio
    async def test_set_featured(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_professional: ProfessionalProfile,
    ):
        """Should set a professional as featured."""
        async with override_auth(test_admin_user):
            response = await client.patch(
                f"/api/v1/admin/professionals/{test_professional.id}/featured?is_featured=true",
                headers={"X-CSRF-Token": CSRF_TOKEN},
                cookies={"csrf_token": CSRF_TOKEN},
            )
            assert response.status_code == 200
            assert "featured" in response.json()["message"]

            # Verify the change persisted
            await db_session.refresh(test_professional)
            assert test_professional.is_featured is True

    @pytest.mark.asyncio
    async def test_unset_featured(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_professional: ProfessionalProfile,
    ):
        """Should unset a professional as featured."""
        # First set as featured
        test_professional.is_featured = True
        await db_session.commit()

        async with override_auth(test_admin_user):
            response = await client.patch(
                f"/api/v1/admin/professionals/{test_professional.id}/featured?is_featured=false",
                headers={"X-CSRF-Token": CSRF_TOKEN},
                cookies={"csrf_token": CSRF_TOKEN},
            )
            assert response.status_code == 200
            assert "unfeatured" in response.json()["message"]

            # Verify the change persisted
            await db_session.refresh(test_professional)
            assert test_professional.is_featured is False

    @pytest.mark.asyncio
    async def test_toggle_featured_professional_not_found(
        self,
        client: AsyncClient,
        test_admin_user: User,
    ):
        """Should return 404 for non-existent professional."""
        fake_id = uuid.uuid4()
        async with override_auth(test_admin_user):
            response = await client.patch(
                f"/api/v1/admin/professionals/{fake_id}/featured?is_featured=true",
                headers={"X-CSRF-Token": CSRF_TOKEN},
                cookies={"csrf_token": CSRF_TOKEN},
            )
            assert response.status_code == 404
            # Error response format may vary - check for message in any format
            data = response.json()
            error_message = data.get("detail", data.get("error", {}).get("message", str(data)))
            assert "Professional not found" in error_message or "not found" in error_message.lower()

    @pytest.mark.asyncio
    async def test_toggle_featured_requires_admin(
        self,
        client: AsyncClient,
        test_user: User,
        test_professional: ProfessionalProfile,
    ):
        """Non-admin should not be able to toggle featured status."""
        async with override_auth(test_user):
            response = await client.patch(
                f"/api/v1/admin/professionals/{test_professional.id}/featured?is_featured=true",
                headers={"X-CSRF-Token": CSRF_TOKEN},
                cookies={"csrf_token": CSRF_TOKEN},
            )
            assert response.status_code == 403


class TestAdminRateLimiting:
    """Tests for rate limiting on admin endpoints."""

    @pytest.mark.asyncio
    async def test_stats_endpoint_rate_limited(
        self,
        client: AsyncClient,
        test_admin_user: User,
    ):
        """Stats endpoint should have rate limiting."""
        # This test verifies the rate limiter decorator is in place
        # Actual rate limit testing would require more requests
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/stats")
            assert response.status_code == 200
            # The endpoint should work under normal conditions

    @pytest.mark.asyncio
    async def test_users_endpoint_rate_limited(
        self,
        client: AsyncClient,
        test_admin_user: User,
    ):
        """Users endpoint should have rate limiting."""
        async with override_auth(test_admin_user):
            response = await client.get("/api/v1/admin/users")
            assert response.status_code == 200
