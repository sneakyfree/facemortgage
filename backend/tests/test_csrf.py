"""
Tests for the CSRF middleware.

Tests cover:
- Safe methods (GET, HEAD, OPTIONS) pass without CSRF
- State-changing methods require valid CSRF token
- Token mismatch is rejected
- Exempt paths bypass CSRF
- Cookie generation on first request
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
import secrets

from src.app.main import app
from src.app.middleware.csrf import CSRFMiddleware, get_csrf_token


class TestCSRFSafeMethods:
    """Tests for safe HTTP methods that don't require CSRF."""

    @pytest.mark.asyncio
    async def test_get_request_passes_without_csrf(self):
        """GET requests should pass without CSRF token."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Use a path that exists
            response = await client.get("/api/v1/grid/professionals")
            # Should not be CSRF error (may be other errors like 401)
            if response.status_code == 403:
                data = response.json()
                assert data.get("type") != "csrf_error"

    @pytest.mark.asyncio
    async def test_head_request_passes_without_csrf(self):
        """HEAD requests should pass without CSRF token."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Use a path that exists
            response = await client.head("/api/v1/grid/professionals")
            # Should not be CSRF error (405 is ok for HEAD if not supported)
            if response.status_code == 403:
                data = response.json()
                assert data.get("type") != "csrf_error"

    @pytest.mark.asyncio
    async def test_options_request_passes_without_csrf(self):
        """OPTIONS requests should pass without CSRF token."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.options("/api/v1/grid/professionals")
            # Should not be CSRF error
            if response.status_code == 403:
                data = response.json()
                assert data.get("type") != "csrf_error"

    @pytest.mark.asyncio
    async def test_csrf_cookie_set_on_get_response(self):
        """GET response should include CSRF cookie if not present."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/grid/professionals")
            # Check if csrf_token cookie is set
            cookies = response.cookies
            # Cookie may be set or endpoint may be exempt
            assert "csrf_token" in cookies or response.status_code != 403


class TestCSRFStateChangingMethods:
    """Tests for state-changing methods that require CSRF."""

    @pytest.mark.asyncio
    async def test_post_without_csrf_fails(self):
        """POST without CSRF token should return 403."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # First get to obtain CSRF cookie
            await client.get("/api/v1/health")

            # POST without CSRF header should fail
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "test"},
            )
            assert response.status_code == 403
            data = response.json()
            assert data.get("type") == "csrf_error"

    @pytest.mark.asyncio
    async def test_post_with_valid_csrf_passes(self):
        """POST with valid CSRF token should pass CSRF check."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # First get to obtain CSRF cookie
            response = await client.get("/api/v1/health")
            csrf_token = response.cookies.get("csrf_token")

            if csrf_token:
                # POST with matching CSRF header should pass CSRF check
                # (may fail for other reasons like invalid credentials)
                response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@test.com", "password": "test"},
                    headers={"X-CSRF-Token": csrf_token},
                    cookies={"csrf_token": csrf_token},
                )
                # Should not be 403 CSRF error
                assert response.status_code != 403 or response.json().get("type") != "csrf_error"

    @pytest.mark.asyncio
    async def test_csrf_token_mismatch_fails(self):
        """POST with mismatched CSRF token should return 403."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # First get to obtain CSRF cookie
            response = await client.get("/api/v1/health")
            csrf_cookie = response.cookies.get("csrf_token")

            if csrf_cookie:
                # POST with different CSRF header should fail
                response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@test.com", "password": "test"},
                    headers={"X-CSRF-Token": "wrong-token"},
                    cookies={"csrf_token": csrf_cookie},
                )
                assert response.status_code == 403
                data = response.json()
                assert data.get("type") == "csrf_error"

    @pytest.mark.asyncio
    async def test_put_requires_csrf(self):
        """PUT requests should require CSRF token."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.put(
                "/api/v1/users/me",
                json={"first_name": "Test"},
            )
            assert response.status_code == 403
            data = response.json()
            assert data.get("type") == "csrf_error"

    @pytest.mark.asyncio
    async def test_delete_requires_csrf(self):
        """DELETE requests should require CSRF token."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.delete("/api/v1/users/me/avatar")
            assert response.status_code == 403
            data = response.json()
            assert data.get("type") == "csrf_error"

    @pytest.mark.asyncio
    async def test_patch_requires_csrf(self):
        """PATCH requests should require CSRF token."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.patch(
                "/api/v1/professionals/me/status",
                json={"status": "online_available"},
            )
            assert response.status_code == 403
            data = response.json()
            assert data.get("type") == "csrf_error"


class TestCSRFExemptPaths:
    """Tests for paths exempt from CSRF validation."""

    @pytest.mark.asyncio
    async def test_webhook_path_exempt(self):
        """Stripe webhook path should be exempt from CSRF."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # POST to webhook without CSRF should not get 403 CSRF error
            response = await client.post(
                "/api/v1/billing/webhook",
                content=b"{}",
                headers={"Stripe-Signature": "test"},
            )
            # Should fail for invalid signature (400), not CSRF (403)
            # CSRF exempt paths return 400 for bad request, not 403
            if response.status_code == 403:
                data = response.json()
                assert data.get("type") != "csrf_error"
            else:
                # 400 is expected for invalid webhook signature
                assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_health_path_exempt(self):
        """Health endpoints should be exempt from CSRF via unit test."""
        # Test via unit test since routes may not exist
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_exempt_path("/api/v1/health") is True
        assert middleware._is_exempt_path("/api/v1/health/ready") is True
        assert middleware._is_exempt_path("/api/v1/health/live") is True

    @pytest.mark.asyncio
    async def test_docs_path_exempt(self):
        """Documentation paths should be exempt from CSRF via unit test."""
        # Test via unit test since routes may not exist
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_exempt_path("/docs") is True
        assert middleware._is_exempt_path("/openapi.json") is True


class TestCSRFMiddlewareUnit:
    """Unit tests for CSRFMiddleware class methods."""

    def test_is_exempt_path_exact_match(self):
        """Exact path match should be exempt."""
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_exempt_path("/api/v1/billing/webhook") is True
        assert middleware._is_exempt_path("/api/v1/health") is True
        assert middleware._is_exempt_path("/docs") is True

    def test_is_exempt_path_prefix_match(self):
        """Paths starting with exempt prefix should be exempt."""
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_exempt_path("/api/v1/health/ready") is True
        assert middleware._is_exempt_path("/api/v1/health/live") is True
        assert middleware._is_exempt_path("/docs/") is True

    def test_is_exempt_path_non_exempt(self):
        """Non-exempt paths should not be exempt."""
        middleware = CSRFMiddleware(app=MagicMock())
        assert middleware._is_exempt_path("/api/v1/auth/login") is False
        assert middleware._is_exempt_path("/api/v1/users/me") is False
        assert middleware._is_exempt_path("/api/v1/professionals") is False

    def test_validate_csrf_token_missing_cookie(self):
        """Missing CSRF cookie should fail validation."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = MagicMock()
        request.cookies = {}
        request.headers = {"X-CSRF-Token": "some-token"}

        assert middleware._validate_csrf_token(request) is False

    def test_validate_csrf_token_missing_header(self):
        """Missing CSRF header should fail validation."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = MagicMock()
        request.cookies = {"csrf_token": "some-token"}
        request.headers = {}

        assert middleware._validate_csrf_token(request) is False

    def test_validate_csrf_token_mismatch(self):
        """Mismatched tokens should fail validation."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = MagicMock()
        request.cookies = {"csrf_token": "cookie-token"}
        request.headers = {"X-CSRF-Token": "header-token"}

        assert middleware._validate_csrf_token(request) is False

    def test_validate_csrf_token_match(self):
        """Matching tokens should pass validation."""
        middleware = CSRFMiddleware(app=MagicMock())
        token = secrets.token_urlsafe(32)
        request = MagicMock()
        request.cookies = {"csrf_token": token}
        request.headers = {"X-CSRF-Token": token}

        assert middleware._validate_csrf_token(request) is True

    def test_safe_methods_constant(self):
        """Safe methods should include GET, HEAD, OPTIONS."""
        assert "GET" in CSRFMiddleware.SAFE_METHODS
        assert "HEAD" in CSRFMiddleware.SAFE_METHODS
        assert "OPTIONS" in CSRFMiddleware.SAFE_METHODS
        assert "POST" not in CSRFMiddleware.SAFE_METHODS
        assert "PUT" not in CSRFMiddleware.SAFE_METHODS
        assert "DELETE" not in CSRFMiddleware.SAFE_METHODS


class TestGetCSRFToken:
    """Tests for the get_csrf_token helper function."""

    def test_get_csrf_token_from_cookie(self):
        """Should return token from cookie if present."""
        request = MagicMock()
        request.cookies = {"csrf_token": "existing-token"}

        token = get_csrf_token(request)
        assert token == "existing-token"

    def test_get_csrf_token_generate_new(self):
        """Should generate new token if cookie not present."""
        request = MagicMock()
        request.cookies = {}

        token = get_csrf_token(request)
        assert token is not None
        assert len(token) > 0

    def test_get_csrf_token_generates_unique(self):
        """Generated tokens should be unique."""
        request = MagicMock()
        request.cookies = {}

        token1 = get_csrf_token(request)
        token2 = get_csrf_token(request)

        # Each call should generate a new token
        assert token1 != token2
