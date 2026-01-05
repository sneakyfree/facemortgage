"""
Health check endpoints for FaceMortgage API.

Provides endpoints for monitoring systems, load balancers, and Kubernetes
probes to determine application health status.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.app.core.database import async_session_maker
from src.app.core.cache import get_redis
from src.app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    summary="Basic health check",
    description="Returns basic health status. Does not check dependencies.",
    response_description="Health status",
)
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    This endpoint returns immediately and indicates that the API server
    is running and accepting requests. It does not verify database or
    Redis connectivity.

    Use this for simple uptime monitoring.
    """
    return {
        "status": "healthy",
        "service": "facemortgage-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/health/ready",
    summary="Readiness check",
    description="Checks if the application is ready to serve traffic by verifying database and Redis connections.",
    response_description="Readiness status with dependency details",
)
async def readiness_check() -> JSONResponse:
    """
    Readiness probe endpoint.

    Verifies that all critical dependencies are available:
    - Database (PostgreSQL) connection
    - Redis connection

    This endpoint should be used by Kubernetes readiness probes or
    load balancers to determine if the instance should receive traffic.

    Returns 200 if all dependencies are healthy, 503 otherwise.
    """
    checks: dict[str, dict[str, Any]] = {
        "database": {"status": "unknown"},
        "redis": {"status": "unknown"},
    }
    all_healthy = True

    # Check database connection
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            checks["database"] = {
                "status": "healthy",
                "latency_ms": None,  # Could add timing here if needed
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_healthy = False

    # Check Redis connection
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        checks["redis"] = {
            "status": "healthy",
            "latency_ms": None,
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_healthy = False

    response_data = {
        "status": "ready" if all_healthy else "not_ready",
        "service": "facemortgage-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        content=response_data,
        status_code=status_code,
    )


@router.get(
    "/health/live",
    summary="Liveness check",
    description="Indicates if the application is alive and should not be restarted.",
    response_description="Liveness status",
)
async def liveness_check() -> dict[str, Any]:
    """
    Liveness probe endpoint.

    This endpoint indicates whether the application process is alive
    and functioning. It should return successfully even if dependencies
    are temporarily unavailable.

    This endpoint should be used by Kubernetes liveness probes. If this
    endpoint fails, the container should be restarted.

    Unlike the readiness probe, this only checks if the Python process
    is responsive, not if it can serve traffic.
    """
    return {
        "status": "alive",
        "service": "facemortgage-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/health/info",
    summary="Application info",
    description="Returns application version and environment information.",
    response_description="Application information",
)
async def info() -> dict[str, Any]:
    """
    Application information endpoint.

    Returns metadata about the running application instance,
    useful for debugging and monitoring dashboards.
    """
    return {
        "service": "facemortgage-api",
        "version": "0.1.0",
        "environment": getattr(settings, "environment", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
