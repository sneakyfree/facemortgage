"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from src.app.config import settings

# Create Celery app
celery_app = Celery(
    "facemortgage",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.app.workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # Result backend settings
    result_expires=3600,  # 1 hour

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Beat schedule for periodic tasks
    beat_schedule={
        "reset-daily-metrics": {
            "task": "src.app.workers.tasks.reset_daily_metrics_task",
            "schedule": crontab(hour=0, minute=0),  # Midnight UTC
        },
        "aggregate-analytics-hourly": {
            "task": "src.app.workers.tasks.aggregate_analytics_task",
            "schedule": crontab(minute=0),  # Every hour
        },
        "sync-subscriptions": {
            "task": "src.app.workers.tasks.sync_subscription_status_task",
            "schedule": crontab(hour="*/6"),  # Every 6 hours
        },
        "cleanup-call-rooms": {
            "task": "src.app.workers.tasks.cleanup_expired_call_rooms_task",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        "aggregate-grid-positions": {
            "task": "src.app.workers.tasks.aggregate_grid_positions_task",
            "schedule": crontab(hour=23, minute=55),  # End of day (11:55 PM UTC)
        },
    },
)
