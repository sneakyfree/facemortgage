"""
Request ID middleware for distributed tracing.

Generates a unique request ID for each incoming request and makes it available
throughout the request lifecycle for logging and error tracking.
"""
import uuid
import logging
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request ID - accessible throughout the request lifecycle
request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

logger = logging.getLogger(__name__)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return request_id_context.get()


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid.uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique request ID to each incoming request.

    The request ID is:
    - Generated if not provided in X-Request-ID header
    - Stored in request.state.request_id for access in handlers
    - Set in context variable for access in logging
    - Returned in X-Request-ID response header

    Usage:
        # In a route handler:
        from app.middleware import get_request_id
        request_id = get_request_id()

        # In logging:
        logger.info("Processing request", extra={"request_id": get_request_id()})
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Check for existing request ID in header (e.g., from load balancer)
        request_id = request.headers.get("X-Request-ID")

        # Generate new ID if not provided
        if not request_id:
            request_id = generate_request_id()

        # Store in request state for access in handlers
        request.state.request_id = request_id

        # Store in context variable for access in logging and other places
        token = request_id_context.set(request_id)

        try:
            # Process the request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response
        finally:
            # Reset context variable
            request_id_context.reset(token)


class RequestIdLogFilter(logging.Filter):
    """
    Logging filter that adds request_id to all log records.

    Usage:
        # In logging configuration:
        handler.addFilter(RequestIdLogFilter())

        # In log format:
        formatter = logging.Formatter(
            '%(asctime)s - %(request_id)s - %(name)s - %(message)s'
        )
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "no-request"
        return True
