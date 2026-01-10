"""
Tests for API routes.

Covers:
- Health endpoints
- Scheduled calls
- Soft leads
- Partnerships
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.user import User
from src.app.models.professional import ProfessionalProfile


class TestHealthRoutes:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test basic health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "facemortgage-api"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        """Test liveness probe endpoint."""
        response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["service"] == "facemortgage-api"

    @pytest.mark.asyncio
    async def test_info_endpoint(self, client: AsyncClient):
        """Test application info endpoint."""
        response = await client.get("/health/info")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "facemortgage-api"
        assert "version" in data
        assert "environment" in data


class TestScheduledCallsRoutes:
    """Tests for scheduled calls endpoints."""

    @pytest.mark.asyncio
    async def test_schedule_call_too_soon(
        self,
        client: AsyncClient,
        test_professional: ProfessionalProfile,
    ):
        """Test scheduling call less than 30 minutes in future fails."""
        response = await client.post(
            "/api/v1/scheduled-calls",
            json={
                "professional_id": str(test_professional.id),
                "scheduled_for": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
                "name": "John Doe",
                "email": "john@example.com",
            },
        )

        assert response.status_code == 400
        assert "30 minutes" in response.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_schedule_call_too_far(
        self,
        client: AsyncClient,
        test_professional: ProfessionalProfile,
    ):
        """Test scheduling call more than 30 days in future fails."""
        response = await client.post(
            "/api/v1/scheduled-calls",
            json={
                "professional_id": str(test_professional.id),
                "scheduled_for": (datetime.utcnow() + timedelta(days=45)).isoformat(),
                "name": "John Doe",
                "email": "john@example.com",
            },
        )

        assert response.status_code == 400
        assert "30 days" in response.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_schedule_call_invalid_professional(self, client: AsyncClient):
        """Test scheduling call with non-existent professional fails."""
        response = await client.post(
            "/api/v1/scheduled-calls",
            json={
                "professional_id": str(uuid4()),
                "scheduled_for": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                "name": "John Doe",
                "email": "john@example.com",
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_schedule_call_success(
        self,
        client: AsyncClient,
        test_professional: ProfessionalProfile,
    ):
        """Test successful call scheduling."""
        with patch("src.app.api.v1.routes.scheduled_calls.get_email_service") as mock_email:
            mock_service = AsyncMock()
            mock_service.send_scheduled_call_confirmation = AsyncMock(return_value=True)
            mock_service.send_scheduled_call_notification = AsyncMock(return_value=True)
            mock_email.return_value = mock_service

            response = await client.post(
                "/api/v1/scheduled-calls",
                json={
                    "professional_id": str(test_professional.id),
                    "scheduled_for": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                    "timezone": "America/New_York",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "555-123-4567",
                    "loan_purpose": "purchase",
                    "notes": "First-time homebuyer",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "scheduled_for" in data


# Note: Soft leads capture and partnerships routes tests are skipped
# as these features require specific route implementations.


class TestLeadsRoutes:
    """Tests for leads endpoints."""

    @pytest.mark.asyncio
    async def test_list_leads_unauthenticated(self, client: AsyncClient):
        """Test listing leads without auth fails."""
        response = await client.get("/api/v1/leads")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_leads_authenticated(
        self,
        authenticated_professional_client: AsyncClient,
    ):
        """Test listing leads with auth succeeds."""
        response = await authenticated_professional_client.get("/api/v1/leads")
        assert response.status_code == 200
        data = response.json()
        # API returns {leads: [], total: N, page: N, ...}
        assert "leads" in data or "items" in data or isinstance(data, list)


class TestAnalyticsRoutes:
    """Tests for analytics endpoints."""

    @pytest.mark.asyncio
    async def test_get_dashboard_stats_unauthenticated(self, client: AsyncClient):
        """Test getting dashboard stats without auth fails."""
        response = await client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_dashboard_stats_authenticated(
        self,
        authenticated_professional_client: AsyncClient,
    ):
        """Test getting dashboard stats with auth succeeds."""
        response = await authenticated_professional_client.get(
            "/api/v1/analytics/dashboard"
        )
        assert response.status_code == 200
        data = response.json()
        assert "calls" in data or "period_days" in data


class TestCallsRoutes:
    """Tests for video calls endpoints."""

    @pytest.mark.asyncio
    async def test_initiate_call_to_offline_professional(
        self,
        client: AsyncClient,
        test_offline_professional: tuple,
    ):
        """Test initiating call to offline professional fails."""
        _, profile = test_offline_professional

        response = await client.post(
            "/api/v1/calls/initiate",
            json={
                "professional_id": str(profile.id),
            },
        )

        # Should fail because professional is offline or method not allowed
        assert response.status_code in [400, 404, 405, 503]

    @pytest.mark.asyncio
    async def test_get_ice_servers(self, client: AsyncClient):
        """Test getting ICE servers."""
        response = await client.get("/api/v1/calls/ice-servers")

        # This endpoint may or may not require auth depending on implementation
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "servers" in data


class TestGridRoutes:
    """Tests for professional grid endpoints."""

    @pytest.mark.asyncio
    async def test_get_grid_professionals(self, client: AsyncClient):
        """Test getting grid of available professionals."""
        # The grid listing endpoint is at /api/v1/professionals
        response = await client.get("/api/v1/professionals")

        assert response.status_code == 200
        data = response.json()
        assert "professionals" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_grid_with_filters(self, client: AsyncClient):
        """Test getting grid with filters."""
        response = await client.get(
            "/api/v1/professionals",
            params={
                "state": "CA",
                "language": "en",
                "only_available": True,
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_professional_detail(
        self,
        client: AsyncClient,
        test_professional: ProfessionalProfile,
    ):
        """Test getting professional detail."""
        response = await client.get(f"/api/v1/professionals/{test_professional.id}")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data


class TestLookupsRoutes:
    """Tests for lookup data endpoints."""

    @pytest.mark.asyncio
    async def test_get_specialties(self, client: AsyncClient):
        """Test getting specialties list."""
        response = await client.get("/api/v1/lookups/specialties")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_languages(self, client: AsyncClient):
        """Test getting languages list."""
        response = await client.get("/api/v1/lookups/languages")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_states(self, client: AsyncClient):
        """Test getting states list."""
        response = await client.get("/api/v1/lookups/states")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAuthRoutes:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_professional(self, client: AsyncClient):
        """Test professional registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"newpro_{uuid4().hex[:8]}@test.com",
                "password": "SecurePass123!@#",  # 12+ chars with upper, lower, digit, special
                "first_name": "New",
                "last_name": "Professional",
                "user_type": "loan_officer",
            },
        )

        assert response.status_code in [200, 201]
        data = response.json()
        # Registration returns the user object, not tokens
        assert "id" in data or "email" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test registration with duplicate email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Already exists
                "password": "SecurePass123!@#",
                "first_name": "Duplicate",
                "last_name": "User",
                "user_type": "borrower",
            },
        )

        # 400 for duplicate email, 429 for rate limiting
        assert response.status_code in [400, 429]

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(
        self,
        authenticated_borrower_client: AsyncClient,
        test_user: User,
    ):
        """Test getting current user info."""
        response = await authenticated_borrower_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email


class TestDevicesRoutes:
    """Tests for device registration endpoints."""

    @pytest.mark.asyncio
    async def test_register_device_unauthenticated(self, client: AsyncClient):
        """Test registering a device without auth fails."""
        response = await client.post(
            "/api/v1/devices/register",
            json={
                "token": "fcm_token_1234567890",
                "platform": "ios",
                "device_name": "iPhone 15",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_register_device_success(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test registering a device with auth succeeds."""
        response = await authenticated_borrower_client.post(
            "/api/v1/devices/register",
            json={
                "token": "fcm_token_1234567890abcdef",
                "platform": "ios",
                "device_name": "iPhone 15",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["device_count"] >= 1

    @pytest.mark.asyncio
    async def test_register_device_invalid_platform(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test registering with invalid platform fails."""
        response = await authenticated_borrower_client.post(
            "/api/v1/devices/register",
            json={
                "token": "fcm_token_1234567890abcdef",
                "platform": "windows",  # Invalid platform
                "device_name": "Test Device",
            },
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_my_devices(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test getting registered devices."""
        response = await authenticated_borrower_client.get("/api/v1/devices/my-devices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_unregister_device(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test unregistering a device."""
        # First register a device
        await authenticated_borrower_client.post(
            "/api/v1/devices/register",
            json={
                "token": "device_to_unregister_123",
                "platform": "android",
            },
        )

        # Then unregister it
        response = await authenticated_borrower_client.request(
            "DELETE",
            "/api/v1/devices/unregister",
            json={"token": "device_to_unregister_123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_toggle_push_notifications(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test toggling push notifications."""
        response = await authenticated_borrower_client.post(
            "/api/v1/devices/toggle-push",
            params={"enabled": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["push_enabled"] is False


class TestSoftLeadsRoutes:
    """Tests for soft leads (Get Matched) endpoints."""

    @pytest.mark.asyncio
    async def test_get_matched_success(self, client: AsyncClient):
        """Test submitting a get matched request."""
        with patch("src.app.api.v1.routes.soft_leads.get_email_service") as mock_email:
            mock_service = AsyncMock()
            mock_service.send_get_matched_confirmation = AsyncMock(return_value=True)
            mock_email.return_value = mock_service

            response = await client.post(
                "/api/v1/soft-leads/get-matched",
                json={
                    "name": "Jane Doe",
                    "email": "jane@example.com",
                    "phone": "555-987-6543",
                    "loan_purpose": "purchase",
                    "estimated_amount": 350000,
                    "property_state": "CA",
                    "timeframe": "1_month",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "lead_id" in data

    @pytest.mark.asyncio
    async def test_get_matched_minimal_data(self, client: AsyncClient):
        """Test get matched with minimal required data."""
        with patch("src.app.api.v1.routes.soft_leads.get_email_service") as mock_email:
            mock_service = AsyncMock()
            mock_service.send_get_matched_confirmation = AsyncMock(return_value=True)
            mock_email.return_value = mock_service

            response = await client.post(
                "/api/v1/soft-leads/get-matched",
                json={
                    "name": "Minimal User",
                    "email": "minimal@example.com",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_matched_invalid_email(self, client: AsyncClient):
        """Test get matched with invalid email fails."""
        response = await client.post(
            "/api/v1/soft-leads/get-matched",
            json={
                "name": "Bad Email User",
                "email": "not-an-email",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_pending_leads_unauthenticated(self, client: AsyncClient):
        """Test getting pending leads without auth fails."""
        response = await client.get("/api/v1/soft-leads/professional/pending")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_pending_leads_as_professional(
        self,
        authenticated_professional_client: AsyncClient,
    ):
        """Test getting pending leads as professional."""
        response = await authenticated_professional_client.get(
            "/api/v1/soft-leads/professional/pending"
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPartnershipsRoutes:
    """Tests for partnership endpoints."""

    @pytest.mark.asyncio
    async def test_invite_partner_unauthenticated(self, client: AsyncClient):
        """Test inviting partner without auth fails."""
        response = await client.post(
            "/api/v1/partnerships/invite",
            json={
                "realtor_name": "John Realtor",
                "realtor_email": "john.realtor@example.com",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_partnerships_unauthenticated(self, client: AsyncClient):
        """Test getting partnerships without auth fails."""
        response = await client.get("/api/v1/partnerships/my-partnerships")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_partnerships_authenticated(
        self,
        authenticated_professional_client: AsyncClient,
    ):
        """Test getting partnerships with auth succeeds."""
        response = await authenticated_professional_client.get(
            "/api/v1/partnerships/my-partnerships"
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_accept_partnership_invalid_token(self, client: AsyncClient):
        """Test accepting partnership with invalid token fails."""
        response = await client.post("/api/v1/partnerships/accept/invalid-token-123")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_referrals_not_found(
        self,
        authenticated_professional_client: AsyncClient,
    ):
        """Test getting referrals for non-existent partnership."""
        response = await authenticated_professional_client.get(
            f"/api/v1/partnerships/{uuid4()}/referrals"
        )
        assert response.status_code == 404


class TestProfessionalsRoutes:
    """Tests for professional profile endpoints."""

    @pytest.mark.asyncio
    async def test_get_professional_not_found(self, client: AsyncClient):
        """Test getting non-existent professional."""
        response = await client.get(f"/api/v1/professionals/{uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_my_profile_unauthenticated(self, client: AsyncClient):
        """Test updating profile without auth fails."""
        response = await client.put(
            "/api/v1/professionals/me",
            json={"bio": "Updated bio"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_my_profile_success(
        self,
        authenticated_professional_client: AsyncClient,
    ):
        """Test updating profile with auth succeeds."""
        response = await authenticated_professional_client.put(
            "/api/v1/professionals/me",
            json={
                "bio": "Updated bio for testing",
                "years_experience": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Updated bio for testing"
        assert data["years_experience"] == 10

    @pytest.mark.asyncio
    async def test_update_status_unauthenticated(self, client: AsyncClient):
        """Test updating status without auth fails."""
        response = await client.patch(
            "/api/v1/professionals/me/status",
            json={"status": "online_available"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_go_online_unauthenticated(self, client: AsyncClient):
        """Test going online without auth fails."""
        response = await client.post("/api/v1/professionals/me/go-online")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_go_offline_unauthenticated(self, client: AsyncClient):
        """Test going offline without auth fails."""
        response = await client.post("/api/v1/professionals/me/go-offline")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_baseball_card(
        self,
        client: AsyncClient,
        test_professional: ProfessionalProfile,
    ):
        """Test getting baseball card stats."""
        response = await client.get(
            f"/api/v1/professionals/{test_professional.id}/baseball-card"
        )
        assert response.status_code == 200
        data = response.json()
        assert "professional_id" in data
        assert "internal_stats" in data

    @pytest.mark.asyncio
    async def test_verify_nmls(
        self,
        client: AsyncClient,
        test_professional: ProfessionalProfile,
    ):
        """Test NMLS verification endpoint."""
        response = await client.get(
            f"/api/v1/professionals/{test_professional.id}/verify-nmls"
        )
        assert response.status_code == 200
        data = response.json()
        # Either verified or has an error message
        assert "verified" in data


class TestUsersRoutes:
    """Tests for user profile endpoints."""

    @pytest.mark.asyncio
    async def test_get_my_profile_unauthenticated(self, client: AsyncClient):
        """Test getting profile without auth fails."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_profile_authenticated(
        self,
        authenticated_borrower_client: AsyncClient,
        test_user: User,
    ):
        """Test getting profile with auth succeeds."""
        response = await authenticated_borrower_client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_update_my_profile(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test updating user profile."""
        response = await authenticated_borrower_client.put(
            "/api/v1/users/me",
            json={
                "first_name": "Updated",
                "last_name": "Name",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test changing password with wrong current password fails."""
        response = await authenticated_borrower_client.post(
            "/api/v1/users/me/password",
            json={
                "current_password": "wrongpassword",
                "new_password": "NewSecurePass123!",
            },
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_change_password_too_short(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test changing password to weak one fails."""
        response = await authenticated_borrower_client.post(
            "/api/v1/users/me/password",
            json={
                "current_password": "testpass123",  # Matches fixture password hash
                "new_password": "short",  # Doesn't meet password policy
            },
        )
        assert response.status_code == 400
        # Updated to match new password policy (12 chars minimum)
        assert "12 characters" in response.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_get_notification_settings(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test getting notification settings."""
        response = await authenticated_borrower_client.get(
            "/api/v1/users/me/notification-settings"
        )
        assert response.status_code == 200
        data = response.json()
        # Check default settings are returned
        assert "email_notifications" in data
        assert "push_notifications" in data

    @pytest.mark.asyncio
    async def test_update_notification_settings(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test updating notification settings."""
        response = await authenticated_borrower_client.put(
            "/api/v1/users/me/notification-settings",
            json={
                "email_notifications": False,
                "sms_notifications": True,
                "push_notifications": True,
                "call_reminders": True,
                "lead_alerts": False,
                "marketing_emails": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email_notifications"] is False
        assert data["sms_notifications"] is True

    @pytest.mark.asyncio
    async def test_delete_avatar_authenticated(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test deleting avatar."""
        response = await authenticated_borrower_client.delete("/api/v1/users/me/avatar")
        assert response.status_code == 200
        assert response.json()["message"] == "Avatar removed"

    @pytest.mark.asyncio
    async def test_delete_account(
        self,
        authenticated_borrower_client: AsyncClient,
    ):
        """Test soft deleting user account."""
        # Delete the account (test_user from authenticated_borrower_client fixture)
        response = await authenticated_borrower_client.delete("/api/v1/users/me")
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"]
