"""
Performance and Health API endpoints.

Provides:
- Health check endpoint
- Performance metrics
- Cache stats
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.middleware.performance import get_metrics, get_health_status

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    checks: dict
    metrics: dict
    timestamp: float


@router.get("/", response_model=HealthResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def health_check(request: Request):
    """
    Comprehensive health check.
    
    Returns status of:
    - Database connection
    - Cache (Redis) connection
    - Performance metrics summary
    """
    status = await get_health_status()
    return status


@router.get("/metrics")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_performance_metrics(request: Request):
    """
    Get detailed performance metrics.
    
    Returns:
    - Total request count
    - Average response time
    - Slow request count
    - Error count
    - Slowest endpoints
    """
    metrics = get_metrics()
    return metrics.get_summary()


@router.get("/ready")
async def readiness_check(request: Request):
    """
    Simple readiness check for load balancers.
    
    Returns 200 if service is ready to accept traffic.
    """
    return {"ready": True}


@router.get("/live")
async def liveness_check(request: Request):
    """
    Simple liveness check for orchestrators.
    
    Returns 200 if process is alive.
    """
    return {"alive": True}
