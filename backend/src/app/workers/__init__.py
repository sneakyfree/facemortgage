"""
Background worker tasks using Celery.

This module contains async background tasks for:
- Notification delivery (email, SMS)
- Analytics aggregation
- Webhook processing
- Subscription management
- Lead assignment
"""
from src.app.workers.celery_app import celery_app
from src.app.workers.tasks import (
    send_email_task,
    send_sms_task,
    process_webhook_task,
    aggregate_analytics_task,
    reset_daily_metrics_task,
    process_lead_assignment_task,
    sync_subscription_status_task,
)

__all__ = [
    "celery_app",
    "send_email_task",
    "send_sms_task",
    "process_webhook_task",
    "aggregate_analytics_task",
    "reset_daily_metrics_task",
    "process_lead_assignment_task",
    "sync_subscription_status_task",
]
