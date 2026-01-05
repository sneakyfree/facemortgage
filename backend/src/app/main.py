import asyncio
import logging
import uuid
from fastapi import FastAPI, WebSocket, WebSocketException, Depends, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from typing import Optional

from src.app.config import settings
from src.app.core.logging import setup_logging
from src.app.core.rate_limit import limiter, rate_limit_exceeded_handler, RATE_LIMITS
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.app.api.v1.router import api_router
from src.app.api.v1.routes import health


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
from src.app.core.database import engine, Base, async_session_maker
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
    description="FaceMortgage - Real-time video lead generation platform for mortgage professionals",
    version="0.1.0",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware - restrict methods and headers for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
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

@app.websocket("/ws/presence/{professional_id}")
async def websocket_professional_presence(
    websocket: WebSocket,
    professional_id: str,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for professional presence.

    Professionals connect here to:
    - Mark themselves as online/available
    - Send heartbeats
    - Update their status (busy, in_call, away)
    - Toggle camera state

    Query params:
        token: JWT access token for authentication
    """
    # Validate token and authorize professional
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

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

    await professional_presence_handler(websocket, professional_id)


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
    token: Optional[str] = Query(None),
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

    Query params:
        token: JWT access token for authentication
    """
    # Validate token and user authorization
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

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

    await signaling_handler(websocket, room_id, user_id)
