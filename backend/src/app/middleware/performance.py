"""
Performance Monitoring Middleware for FaceMortgage.

Provides:
- Request timing
- Slow request logging
- Performance metrics collection
- Health check endpoints
"""

import time
import logging
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Simple in-memory performance metrics collector."""
    
    def __init__(self):
        self.request_count = 0
        self.total_time_ms = 0.0
        self.slow_requests = 0
        self.errors = 0
        self._by_endpoint: dict = {}
    
    def record(self, endpoint: str, duration_ms: float, status_code: int):
        """Record a request."""
        self.request_count += 1
        self.total_time_ms += duration_ms
        
        if duration_ms > 200:  # Slow request threshold
            self.slow_requests += 1
        
        if status_code >= 500:
            self.errors += 1
        
        # Per-endpoint tracking
        if endpoint not in self._by_endpoint:
            self._by_endpoint[endpoint] = {
                'count': 0,
                'total_ms': 0.0,
                'max_ms': 0.0,
            }
        
        ep = self._by_endpoint[endpoint]
        ep['count'] += 1
        ep['total_ms'] += duration_ms
        ep['max_ms'] = max(ep['max_ms'], duration_ms)
    
    def get_summary(self) -> dict:
        """Get performance summary."""
        avg_ms = self.total_time_ms / self.request_count if self.request_count > 0 else 0
        
        # Top 5 slowest endpoints
        slowest = sorted(
            [(k, v['total_ms'] / v['count']) for k, v in self._by_endpoint.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_requests': self.request_count,
            'avg_response_ms': round(avg_ms, 2),
            'slow_requests': self.slow_requests,
            'error_count': self.errors,
            'slowest_endpoints': [
                {'endpoint': ep, 'avg_ms': round(ms, 2)} 
                for ep, ms in slowest
            ],
        }
    
    def reset(self):
        """Reset all metrics."""
        self.request_count = 0
        self.total_time_ms = 0.0
        self.slow_requests = 0
        self.errors = 0
        self._by_endpoint = {}


# Global metrics instance
_metrics = PerformanceMetrics()


def get_metrics() -> PerformanceMetrics:
    """Get global metrics instance."""
    return _metrics


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request performance.
    
    Logs timing information and collects metrics
    for monitoring and optimization.
    """
    
    SLOW_REQUEST_THRESHOLD_MS = 200
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid4())[:8]
        
        # Record start time
        start_time = time.perf_counter()
        
        # Add request ID to state
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Log error and re-raise
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"ERROR after {duration_ms:.1f}ms: {e}"
            )
            raise
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Get endpoint pattern (strip IDs for grouping)
        endpoint = self._normalize_endpoint(request.url.path)
        
        # Record metrics
        _metrics.record(endpoint, duration_ms, status_code)
        
        # Log slow requests
        if duration_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                f"[{request_id}] SLOW REQUEST: {request.method} {request.url.path} "
                f"took {duration_ms:.1f}ms (threshold: {self.SLOW_REQUEST_THRESHOLD_MS}ms)"
            )
        else:
            logger.debug(
                f"[{request_id}] {request.method} {request.url.path} "
                f"{status_code} {duration_ms:.1f}ms"
            )
        
        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
        response.headers["X-Request-Id"] = request_id
        
        return response
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for grouping (replace UUIDs)."""
        import re
        # Replace UUIDs with placeholder
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        return re.sub(uuid_pattern, '{id}', path)


# ==================== Health Check Data ====================

async def get_health_status() -> dict:
    """
    Get comprehensive health status.
    
    Checks database, cache, and external services.
    """
    from src.app.core.database import get_async_engine
    
    checks = {
        'database': 'unknown',
        'cache': 'unknown',
        'overall': 'healthy',
    }
    
    # Check database
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        checks['database'] = 'healthy'
    except Exception as e:
        checks['database'] = f'unhealthy: {str(e)[:50]}'
        checks['overall'] = 'degraded'
    
    # Check cache (Redis)
    try:
        from src.app.services.cache_service import get_cache_service
        cache = get_cache_service()
        await cache.set('health_check', 'ok', ttl=10)
        result = await cache.get('health_check')
        if result == 'ok':
            checks['cache'] = 'healthy'
        else:
            checks['cache'] = 'unhealthy: read mismatch'
            checks['overall'] = 'degraded'
    except Exception as e:
        checks['cache'] = f'unavailable: {str(e)[:50]}'
        # Cache can be optional, don't mark as degraded
    
    return {
        'status': checks['overall'],
        'checks': checks,
        'metrics': _metrics.get_summary(),
        'timestamp': time.time(),
    }
