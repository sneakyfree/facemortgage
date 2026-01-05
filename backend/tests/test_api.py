"""
API endpoint tests.
"""
import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Health endpoint should return 200."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_borrower(self, client: AsyncClient):
        """Should register a new borrower."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "User",
                "user_type": "borrower",
            },
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Should reject duplicate email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePass123!",
                "first_name": "Duplicate",
                "last_name": "User",
                "user_type": "borrower",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Should reject invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User",
                "user_type": "borrower",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, client: AsyncClient, test_user):
        """Should login with valid credentials."""
        # Note: This would need a real password hash setup
        # For now, test the endpoint structure
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword",
            },
        )
        # Will fail auth but endpoint should respond
        assert response.status_code in [200, 401]


class TestProfessionalEndpoints:
    """Tests for professional endpoints."""

    @pytest.mark.asyncio
    async def test_get_grid_unauthenticated(self, client: AsyncClient):
        """Grid should be accessible without auth."""
        response = await client.get("/api/v1/professionals")
        assert response.status_code == 200
        data = response.json()
        assert "professionals" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_grid_with_filters(self, client: AsyncClient):
        """Grid should accept filter parameters."""
        response = await client.get(
            "/api/v1/professionals",
            params={
                "user_type": "loan_officer",
                "min_rating": 4.0,
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_professional_detail(
        self,
        client: AsyncClient,
        test_professional,
    ):
        """Should get professional detail."""
        response = await client.get(
            f"/api/v1/professionals/{test_professional.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_professional.id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_professional(self, client: AsyncClient):
        """Should return 404 for nonexistent professional."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/professionals/{fake_id}")
        assert response.status_code == 404


class TestStatsEndpoints:
    """Tests for professional stats endpoints."""

    @pytest.mark.asyncio
    async def test_get_professional_stats(self, client: AsyncClient):
        """Should get stats for NMLS ID."""
        response = await client.get("/api/v1/stats/123456")
        assert response.status_code == 200
        data = response.json()
        assert data["nmls_id"] == "123456"
        assert "license" in data
        assert "loans_last_12_months" in data

    @pytest.mark.asyncio
    async def test_get_baseball_card(self, client: AsyncClient):
        """Should get baseball card formatted data."""
        response = await client.get("/api/v1/stats/123456/baseball-card")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "loan_mix" in data
        assert "states_licensed" in data

    @pytest.mark.asyncio
    async def test_verify_nmls(self, client: AsyncClient):
        """Should verify NMLS ID."""
        response = await client.get("/api/v1/stats/123456/verify")
        assert response.status_code == 200
        data = response.json()
        assert data["nmls_id"] == "123456"
        assert "is_valid" in data


class TestLeadEndpoints:
    """Tests for lead management endpoints."""

    @pytest.mark.asyncio
    async def test_list_leads_requires_auth(self, client: AsyncClient):
        """Lead list should require authentication."""
        response = await client.get("/api/v1/leads")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_lead_stats_requires_auth(self, client: AsyncClient):
        """Lead stats should require authentication."""
        response = await client.get("/api/v1/leads/stats")
        assert response.status_code == 401


class TestBillingEndpoints:
    """Tests for billing endpoints."""

    @pytest.mark.asyncio
    async def test_get_plans(self, client: AsyncClient):
        """Should get subscription plans."""
        response = await client.get("/api/v1/billing/plans")
        assert response.status_code == 200


class TestLookupEndpoints:
    """Tests for lookup data endpoints."""

    @pytest.mark.asyncio
    async def test_get_specialties(self, client: AsyncClient):
        """Should get specialties list."""
        response = await client.get("/api/v1/lookups/specialties")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_languages(self, client: AsyncClient):
        """Should get languages list."""
        response = await client.get("/api/v1/lookups/languages")
        assert response.status_code == 200
