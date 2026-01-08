"""
CSRF (Cross-Site Request Forgery) protection middleware.

Implements the synchronizer token pattern for CSRF protection:
- Sets a CSRF token cookie on responses
- Validates X-CSRF-Token header against cookie for state-changing requests
- Allows safe methods (GET, HEAD, OPTIONS) without validation

Usage:
    # In main.py:
    from src.app.middleware.csrf import CSRFMiddleware
    app.add_middleware(CSRFMiddleware)

    # In frontend:
    // Read CSRF token from cookie
    const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='))
        ?.split('=')[1];

    // Include in state-changing requests
    fetch('/api/v1/some-endpoint', {
        method: 'POST',
        headers: {
            'X-CSRF-Token': csrfToken,
        },
        credentials: 'include',
    });
"""
import secrets
import logging
from typing import Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from src.app.config import settings

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware that provides CSRF protection for state-changing requests.

    Safe methods (GET, HEAD, OPTIONS) are allowed without CSRF validation.
    All other methods require a valid CSRF token.
    """

    # HTTP methods that don't require CSRF validation
    SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS"}

    # Paths that are exempt from CSRF (e.g., webhook endpoints)
    EXEMPT_PATHS: Set[str] = {
        "/api/v1/billing/webhook",  # Stripe webhook
        "/api/v1/health",
        "/api/v1/health/ready",
        "/api/v1/health/live",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    # Cookie name for CSRF token
    COOKIE_NAME: str = "csrf_token"

    # Header name for CSRF token
    HEADER_NAME: str = "X-CSRF-Token"

    # Token length in bytes (32 bytes = 256 bits)
    TOKEN_LENGTH: int = 32

    async def dispatch(self, request: Request, call_next) -> Response:
        # Check if path is exempt
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # Safe methods don't require CSRF validation
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            # Ensure CSRF token is set in cookie
            return self._ensure_csrf_cookie(request, response)

        # Validate CSRF token for state-changing requests
        if not self._validate_csrf_token(request):
            logger.warning(
                f"CSRF validation failed for {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF validation failed",
                    "type": "csrf_error",
                },
            )

        response = await call_next(request)
        return self._ensure_csrf_cookie(request, response)

    def _is_exempt_path(self, path: str) -> bool:
        """Check if the request path is exempt from CSRF validation."""
        # Exact match
        if path in self.EXEMPT_PATHS:
            return True

        # Prefix match for exempt paths
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True

        return False

    def _validate_csrf_token(self, request: Request) -> bool:
        """
        Validate the CSRF token from header against cookie.

        Returns True if valid, False otherwise.
        """
        # Get token from cookie
        cookie_token = request.cookies.get(self.COOKIE_NAME)
        if not cookie_token:
            logger.debug("No CSRF cookie found")
            return False

        # Get token from header
        header_token = request.headers.get(self.HEADER_NAME)
        if not header_token:
            logger.debug("No CSRF header found")
            return False

        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(cookie_token, header_token)

    def _ensure_csrf_cookie(self, request: Request, response: Response) -> Response:
        """
        Ensure the CSRF token cookie is set on the response.

        Only sets the cookie if not already present.
        """
        # Check if cookie already exists
        if self.COOKIE_NAME in request.cookies:
            return response

        # Generate new CSRF token
        token = secrets.token_urlsafe(self.TOKEN_LENGTH)

        # Set cookie with appropriate security settings
        response.set_cookie(
            key=self.COOKIE_NAME,
            value=token,
            httponly=False,  # JavaScript needs to read this to send in header
            samesite="lax",  # Protects against CSRF from external sites
            secure=settings.cookie_secure,  # Only sent over HTTPS in production
            max_age=86400 * 7,  # 7 days
            path="/",
        )

        return response


def get_csrf_token(request: Request) -> str:
    """
    Get or generate a CSRF token for the current request.

    Useful for server-side rendered templates.
    """
    token = request.cookies.get(CSRFMiddleware.COOKIE_NAME)
    if not token:
        token = secrets.token_urlsafe(CSRFMiddleware.TOKEN_LENGTH)
    return token
