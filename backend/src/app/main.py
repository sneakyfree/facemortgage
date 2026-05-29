import asyncio
import logging
import uuid
from fastapi import FastAPI, WebSocket, status, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from typing import Optional

from src.app.config import settings
from src.app.core.logging import setup_logging
from src.app.core.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.app.api.v1.router import api_router
from src.app.api.v1.routes import health
from src.app.core.exceptions import register_exception_handlers
from src.app.middleware.request_id import RequestIdMiddleware
from src.app.middleware.csrf import CSRFMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Only add HSTS in production
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy - adjust based on your frontend needs
        if settings.environment == "production":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss: https:; "
                "frame-ancestors 'none';"
            )

        return response


# Initialize Sentry if DSN is configured
def init_sentry() -> None:
    """Initialize Sentry error tracking if SENTRY_DSN is configured."""
    if settings.sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            from sentry_sdk.integrations.redis import RedisIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration

            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.environment,
                traces_sample_rate=settings.sentry_traces_sample_rate,
                profiles_sample_rate=settings.sentry_profiles_sample_rate,
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    LoggingIntegration(
                        level=logging.INFO,
                        event_level=logging.ERROR,
                    ),
                ],
                send_default_pii=False,  # Don't send personally identifiable information
            )
            logging.getLogger(__name__).info("Sentry initialized successfully")
        except ImportError:
            logging.getLogger(__name__).warning(
                "Sentry SDK not installed. Install with: pip install sentry-sdk[fastapi]"
            )
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to initialize Sentry: {e}")
from src.app.core.database import engine, async_session_maker
from src.app.core.dependencies import get_current_user_ws
from src.app.presence import (
    get_presence_service,
    heartbeat_checker_task,
    redis_subscriber_task,
    professional_presence_handler,
    grid_updates_handler,
    connection_manager,
)
from src.app.signaling import get_signaling_service, signaling_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Configure logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting FaceMortgage API...")

    # Initialize Sentry error tracking
    init_sentry()

    # Initialize presence service connection
    presence = get_presence_service()
    await presence.connect()

    # Initialize signaling service
    signaling = get_signaling_service()
    await signaling.connect()

    # Start background tasks
    heartbeat_task = asyncio.create_task(heartbeat_checker_task())
    redis_sub_task = asyncio.create_task(redis_subscriber_task())

    logger.info("FaceMortgage API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down FaceMortgage API...")
    heartbeat_task.cancel()
    redis_sub_task.cancel()
    await presence.disconnect()
    await signaling.disconnect()
    await engine.dispose()
    logger.info("FaceMortgage API shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="""
## Overview

FaceMortgage connects borrowers with mortgage professionals through real-time video calls.
This API powers the entire platform including professional discovery, video calling,
lead management, and subscription billing.

## Authentication

Most endpoints require authentication via JWT tokens.

### For API Clients
Include the token in the Authorization header:
```
Authorization: Bearer <your-token>
```

### For Browser Clients
Tokens are automatically managed via httpOnly cookies after login.

## Rate Limits

To ensure fair usage and platform stability:
- **Auth endpoints**: 5 requests/minute
- **Read endpoints**: 100 requests/minute
- **Write endpoints**: 30 requests/minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## WebSocket Endpoints

Real-time features use WebSocket connections:
- `/ws/presence/{professional_id}` - Professional online status
- `/ws/grid` - Real-time grid updates (no auth required)
- `/ws/signaling/{room_id}/{user_id}` - WebRTC call signaling

## Error Responses

All errors follow a consistent format:
```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE"
}
```

## Support

For API questions or issues, contact support@facemortgage.com
    """,
    version="1.0.0",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check endpoints for monitoring and load balancer probes.",
        },
        {
            "name": "auth",
            "description": "Authentication and registration endpoints. Use these to register users and obtain access tokens.",
        },
        {
            "name": "grid",
            "description": "Professional grid endpoints for discovering and filtering mortgage professionals.",
        },
        {
            "name": "professionals",
            "description": "Professional profile and management endpoints.",
        },
        {
            "name": "calls",
            "description": "Video call management including initiation, status, and ratings.",
        },
        {
            "name": "scheduled-calls",
            "description": "Schedule calls for later with professionals.",
        },
        {
            "name": "billing",
            "description": "Subscription management and Stripe integration for professionals.",
        },
        {
            "name": "data",
            "description": "External data provider integration for professional statistics.",
        },
        {
            "name": "partnerships",
            "description": "Referral and partnership management for professionals.",
        },
    ],
    contact={
        "name": "FaceMortgage Support",
        "email": "support@facemortgage.com",
    },
    license_info={
        "name": "Proprietary",
    },
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Register custom exception handlers for standardized error responses
register_exception_handlers(app)

# Request ID middleware (must be added before other middleware to capture all requests)
app.add_middleware(RequestIdMiddleware)

# CSRF protection middleware
app.add_middleware(CSRFMiddleware)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware - restrict methods and headers for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "X-CSRF-Token"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_prefix)

# Include health check routes at root level (not under /api/v1)
app.include_router(health.router, tags=["health"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to FaceMortgage API",
        "docs": f"{settings.api_v1_prefix}/docs",
    }


# ==================== WebSocket Endpoints ====================

def get_ws_token(websocket: WebSocket) -> Optional[str]:
    """
    Extract authentication token from WebSocket connection.

    Security priority (from most to least secure):
    1. Cookie (httpOnly, secure) - preferred for browser clients
    2. Sec-WebSocket-Protocol header - for clients that can't use cookies

    Note: Query params are NOT supported to prevent token leakage in logs/URLs.
    """
    # Try cookie first (most secure for browser clients)
    token = websocket.cookies.get("access_token")
    if token:
        return token

    # Try Sec-WebSocket-Protocol header
    # Client sends: Sec-WebSocket-Protocol: auth, <token>
    # Server responds with: Sec-WebSocket-Protocol: auth
    protocols = websocket.headers.get("sec-websocket-protocol", "")
    if protocols:
        parts = [p.strip() for p in protocols.split(",")]
        if len(parts) >= 2 and parts[0] == "auth":
            return parts[1]

    return None


@app.websocket("/ws/presence/{professional_id}")
async def websocket_professional_presence(
    websocket: WebSocket,
    professional_id: str,
):
    """
    WebSocket endpoint for professional presence.

    Professionals connect here to:
    - Mark themselves as online/available
    - Send heartbeats
    - Update their status (busy, in_call, away)
    - Toggle camera state

    Authentication:
        - Cookie: access_token (preferred for browsers)
        - Header: Sec-WebSocket-Protocol: auth, <token>
    """
    # Extract token from secure sources only
    token = get_ws_token(websocket)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Accept with protocol if using Sec-WebSocket-Protocol
    protocols = websocket.headers.get("sec-websocket-protocol", "")
    subprotocol = "auth" if protocols.startswith("auth") else None

    async with async_session_maker() as db:
        user = await get_current_user_ws(token, db)
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Verify user owns this professional profile
        from sqlalchemy import select
        from src.app.models.professional import ProfessionalProfile
        result = await db.execute(
            select(ProfessionalProfile)
            .where(ProfessionalProfile.id == uuid.UUID(professional_id))
            .where(ProfessionalProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await professional_presence_handler(websocket, professional_id, subprotocol)


@app.websocket("/ws/grid")
async def websocket_grid_updates(websocket: WebSocket):
    """
    WebSocket endpoint for grid update subscriptions.

    Borrowers/viewers connect here to receive real-time updates:
    - Professional online/offline events
    - Professional busy/available status changes
    - Camera toggle events

    No authentication required for viewing the grid.
    """
    await grid_updates_handler(websocket)


@app.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "online_professionals": connection_manager.get_online_count(),
        "grid_subscribers": connection_manager.get_subscriber_count(),
    }


@app.websocket("/ws/signaling/{room_id}/{user_id}")
async def websocket_signaling(
    websocket: WebSocket,
    room_id: str,
    user_id: str,
):
    """
    WebSocket endpoint for WebRTC signaling.

    Both borrower and professional connect here during a call to exchange:
    - SDP offers/answers
    - ICE candidates
    - Call control actions (answer, decline, end, mute, camera)

    Path params:
        room_id: The call room ID
        user_id: The connecting user's ID

    Authentication:
        - Cookie: access_token (preferred for browsers)
        - Header: Sec-WebSocket-Protocol: auth, <token>
    """
    # Extract token from secure sources only
    token = get_ws_token(websocket)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Accept with protocol if using Sec-WebSocket-Protocol
    protocols = websocket.headers.get("sec-websocket-protocol", "")
    subprotocol = "auth" if protocols.startswith("auth") else None

    async with async_session_maker() as db:
        user = await get_current_user_ws(token, db)
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Verify user_id matches authenticated user
        if str(user.id) != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Verify user is part of this call room
        signaling = get_signaling_service()
        room = await signaling.get_room(room_id)
        if room is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check if user is borrower or professional for this room
        if str(user.id) not in [room.borrower_id, room.professional_id]:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await signaling_handler(websocket, room_id, user_id, subprotocol)
