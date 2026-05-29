"""
Prometheus metrics for FaceMortgage API.

Provides custom business metrics and integrates with prometheus-fastapi-instrumentator
for automatic HTTP metrics collection.
"""
import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Metrics state tracking
_metrics_initialized = False

# Custom metric values (in-memory tracking for simplicity)
# In production, these would be proper Prometheus metrics
_metric_values = {
    "active_calls": 0,
    "lead_captures_total": 0,
    "successful_matches_total": 0,
}


def increment_metric(name: str, value: int = 1) -> None:
    """Increment a counter metric."""
    if name in _metric_values:
        _metric_values[name] += value


def set_metric(name: str, value: float) -> None:
    """Set a gauge metric value."""
    _metric_values[name] = value


def get_metric(name: str) -> float:
    """Get current metric value."""
    return _metric_values.get(name, 0)


def setup_metrics(app: FastAPI) -> None:
    """
    Configure Prometheus metrics for the FastAPI application.

    This function attempts to use prometheus-fastapi-instrumentator if available,
    and falls back to a simple custom metrics endpoint if not installed.
    """
    global _metrics_initialized

    if _metrics_initialized:
        return

    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        from prometheus_fastapi_instrumentator.metrics import Info
        from prometheus_client import Counter, Gauge, Histogram

        # Create custom metrics
        Gauge(
            "facemortgage_active_calls_total",
            "Number of currently active video calls",
        )

        Counter(
            "facemortgage_lead_captures_total",
            "Total number of leads captured",
            ["professional_type"],
        )

        Counter(
            "facemortgage_successful_matches_total",
            "Total number of successful borrower-professional matches",
        )

        Histogram(
            "facemortgage_data_provider_latency_seconds",
            "Latency of data provider API calls",
            ["provider", "operation"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        Histogram(
            "facemortgage_stripe_webhook_duration_seconds",
            "Duration of Stripe webhook processing",
            ["event_type"],
            buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
        )

        Counter(
            "facemortgage_cache_operations_total",
            "Total cache operations",
            ["operation", "result"],  # operation: get/set, result: hit/miss/error
        )

        # Custom instrumentation function
        def custom_metrics(info: Info) -> None:
            """Add custom labels based on request info."""
            pass  # Can be extended for custom per-request metrics

        # Initialize instrumentator
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/health", "/health/ready", "/health/live", "/metrics"],
            inprogress_name="facemortgage_requests_inprogress",
            inprogress_labels=True,
        )

        # Instrument the app and expose metrics
        instrumentator.instrument(app).expose(app, endpoint="/metrics")

        logger.info("Prometheus metrics initialized with prometheus-fastapi-instrumentator")
        _metrics_initialized = True

    except ImportError:
        # Fallback to simple custom metrics endpoint
        logger.warning(
            "prometheus-fastapi-instrumentator not installed. "
            "Using simple metrics endpoint. "
            "Install with: pip install prometheus-fastapi-instrumentator"
        )

        @app.get("/metrics", include_in_schema=False)
        async def simple_metrics():
            """Simple metrics endpoint when Prometheus client is not available."""
            from src.app.presence import connection_manager

            return {
                "facemortgage_active_calls_total": _metric_values["active_calls"],
                "facemortgage_lead_captures_total": _metric_values["lead_captures_total"],
                "facemortgage_successful_matches_total": _metric_values["successful_matches_total"],
                "facemortgage_online_professionals": connection_manager.get_online_count(),
                "facemortgage_grid_subscribers": connection_manager.get_subscriber_count(),
            }

        _metrics_initialized = True
        logger.info("Simple metrics endpoint configured at /metrics")


# Metric helper functions for use throughout the application
def record_lead_capture(professional_type: str) -> None:
    """Record a lead capture event."""
    increment_metric("lead_captures_total")
    try:
        # prometheus_client metrics are recorded via increment_metric
        pass
    except ImportError:
        pass


def record_active_calls(count: int) -> None:
    """Update the active calls gauge."""
    set_metric("active_calls", count)


def record_data_provider_latency(provider: str, operation: str, duration: float) -> None:
    """Record data provider API latency."""
    try:
        from prometheus_client import REGISTRY
        histogram = REGISTRY._names_to_collectors.get("facemortgage_data_provider_latency_seconds")
        if histogram:
            histogram.labels(provider=provider, operation=operation).observe(duration)
    except (ImportError, KeyError, AttributeError):
        pass


def record_cache_operation(operation: str, result: str) -> None:
    """Record a cache operation (hit/miss/error)."""
    try:
        from prometheus_client import REGISTRY
        counter = REGISTRY._names_to_collectors.get("facemortgage_cache_operations_total")
        if counter:
            counter.labels(operation=operation, result=result).inc()
    except (ImportError, KeyError, AttributeError):
        pass
