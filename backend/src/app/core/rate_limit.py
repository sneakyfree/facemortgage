"""
Rate limiting configuration for FaceMortgage API.

Uses slowapi to implement rate limiting on sensitive endpoints.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def get_real_client_ip(request: Request) -> str:
    """
    Get the real client IP, considering X-Forwarded-For header.

    This handles cases where the API is behind a reverse proxy.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, the first is the client
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return get_remote_address(request)


# Create the limiter instance
limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["200/minute"],  # Default rate limit for all endpoints
    storage_uri="memory://",  # Use Redis in production: redis://localhost:6379
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down your requests.",
            "retry_after": exc.detail,
        },
        headers={
            "Retry-After": str(getattr(exc, "retry_after", 60)),
            "X-RateLimit-Limit": str(getattr(exc, "limit", "unknown")),
        }
    )


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    # Authentication - strict limits to prevent brute force
    "auth_login": "5/minute",
    "auth_register": "3/minute",
    "auth_password_reset": "3/minute",

    # API endpoints - moderate limits
    "api_read": "100/minute",
    "api_write": "30/minute",

    # Sensitive operations - strict limits (password change, account deletion)
    "sensitive": "5/minute",

    # WebSocket connections
    "ws_connect": "10/minute",

    # Billing/Payment - strict limits
    "billing": "20/minute",

    # File uploads
    "upload": "10/minute",
}
