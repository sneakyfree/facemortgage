"""
Celery task definitions for background processing.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from celery import shared_task
import stripe

from src.app.config import settings

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run an async coroutine in a sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ==================== Email Templates ====================

EMAIL_TEMPLATES = {
    "welcome": {
        "subject": "Welcome to FaceMortgage!",
        "html": """
            <h1>Welcome to FaceMortgage, {first_name}!</h1>
            <p>Thank you for joining our platform. You're now ready to connect with mortgage professionals instantly.</p>
            <p>Get started by browsing available professionals on our grid.</p>
        """,
    },
    "call_summary": {
        "subject": "Your Call Summary - FaceMortgage",
        "html": """
            <h1>Call Summary</h1>
            <p>Thank you for using FaceMortgage! Here's a summary of your recent call:</p>
            <ul>
                <li><strong>Professional:</strong> {professional_name}</li>
                <li><strong>Duration:</strong> {duration} minutes</li>
                <li><strong>Date:</strong> {call_date}</li>
            </ul>
            <p>We hope your experience was helpful!</p>
        """,
    },
    "lead_notification": {
        "subject": "New Lead from Video Call - FaceMortgage",
        "html": """
            <h1>New Lead!</h1>
            <p>You have a new lead from a video call on FaceMortgage.</p>
            <ul>
                <li><strong>Call ID:</strong> {call_id}</li>
                <li><strong>Date:</strong> {call_date}</li>
            </ul>
            <p>Log in to your dashboard to view the full lead details and follow up.</p>
        """,
    },
    "subscription_activated": {
        "subject": "Your Subscription is Active - FaceMortgage",
        "html": """
            <h1>Subscription Activated!</h1>
            <p>Hi {first_name},</p>
            <p>Your {tier} subscription is now active. Enjoy your enhanced features:</p>
            <ul>
                {features}
            </ul>
            <p>Thank you for upgrading!</p>
        """,
    },
    "payment_failed": {
        "subject": "Payment Failed - Action Required",
        "html": """
            <h1>Payment Failed</h1>
            <p>Hi {first_name},</p>
            <p>We were unable to process your payment for your FaceMortgage subscription.</p>
            <p>Please update your payment method to continue using premium features.</p>
            <p><a href="{portal_url}">Update Payment Method</a></p>
        """,
    },
    "incoming_call_missed": {
        "subject": "Missed Call on FaceMortgage",
        "html": """
            <h1>You Missed a Call</h1>
            <p>Hi {first_name},</p>
            <p>You missed a call from a potential client on FaceMortgage at {call_time}.</p>
            <p>Tip: Keep your status set to "Available" when ready to take calls!</p>
        """,
    },
    "password_reset": {
        "subject": "Reset Your Password - FaceMortgage",
        "html": """
            <h1>Password Reset Request</h1>
            <p>Hi {first_name},</p>
            <p>We received a request to reset your password. Click the link below to create a new password:</p>
            <p><a href="{reset_url}" style="background: #0070f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, you can safely ignore this email.</p>
        """,
    },
}


def render_template(template_name: str, context: Dict[str, Any]) -> tuple[str, str]:
    """Render an email template with context."""
    template = EMAIL_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}")

    subject = template["subject"].format(**context) if "{" in template["subject"] else template["subject"]
    html = template["html"].format(**context)
    return subject, html


# ==================== Email Task ====================

@shared_task(bind=True, max_retries=3)
def send_email_task(
    self,
    to_email: str,
    subject: str,
    template: str,
    context: Dict[str, Any],
) -> bool:
    """
    Send email using SendGrid.

    Args:
        to_email: Recipient email address
        subject: Email subject (overrides template subject if provided)
        template: Template name (e.g., 'welcome', 'call_summary', 'lead_notification')
        context: Template context variables
    """
    try:
        if not settings.sendgrid_api_key:
            logger.warning("SendGrid API key not configured, skipping email")
            return False

        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        # Render template
        template_subject, html_content = render_template(template, context)
        final_subject = subject if subject else template_subject

        logger.info(f"Sending email to {to_email}: {final_subject}")

        message = Mail(
            from_email=Email(settings.from_email, "FaceMortgage"),
            to_emails=To(to_email),
            subject=final_subject,
            html_content=Content("text/html", html_content),
        )

        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)

        if response.status_code >= 400:
            logger.error(f"SendGrid error: {response.status_code} - {response.body}")
            return False

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ==================== SMS Task ====================

@shared_task(bind=True, max_retries=3)
def send_sms_task(
    self,
    to_phone: str,
    message: str,
) -> bool:
    """
    Send SMS using Twilio.

    Args:
        to_phone: Recipient phone number (E.164 format)
        message: SMS message body
    """
    try:
        if not settings.twilio_sid or not settings.twilio_auth_token:
            logger.warning("Twilio credentials not configured, skipping SMS")
            return False

        from twilio.rest import Client

        logger.info(f"Sending SMS to {to_phone}")

        client = Client(settings.twilio_sid, settings.twilio_auth_token)

        result = client.messages.create(
            body=message,
            from_=settings.twilio_phone,
            to=to_phone,
        )

        logger.info(f"SMS sent successfully, SID: {result.sid}")
        return True

    except Exception as exc:
        logger.error(f"Failed to send SMS: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ==================== Webhook Processing ====================

@shared_task(bind=True, max_retries=3)
def process_webhook_task(
    self,
    webhook_type: str,
    payload: Dict[str, Any],
) -> bool:
    """
    Process incoming webhooks from external services.

    Args:
        webhook_type: Type of webhook (e.g., 'stripe', 'sendgrid')
        payload: Webhook payload data
    """
    try:
        logger.info(f"Processing {webhook_type} webhook")

        if webhook_type == "stripe":
            return _process_stripe_webhook(payload)
        elif webhook_type == "sendgrid":
            return _process_sendgrid_webhook(payload)
        else:
            logger.warning(f"Unknown webhook type: {webhook_type}")
            return False

    except Exception as exc:
        logger.error(f"Failed to process webhook: {exc}")
        raise self.retry(exc=exc, countdown=30)


def _process_stripe_webhook(payload: Dict[str, Any]) -> bool:
    """Process Stripe webhook events."""
    event_type = payload.get("type", "")
    data = payload.get("data", {}).get("object", {})

    logger.info(f"Processing Stripe event: {event_type}")

    if event_type == "invoice.payment_succeeded":
        # Handle successful payment - could send confirmation email
        customer_email = data.get("customer_email")
        if customer_email:
            send_email_task.delay(
                to_email=customer_email,
                subject="Payment Successful - FaceMortgage",
                template="subscription_activated",
                context={
                    "first_name": data.get("customer_name", "").split()[0] if data.get("customer_name") else "there",
                    "tier": "Professional",
                    "features": "<li>Premium grid placement</li><li>Unlimited calls</li>",
                },
            )

    elif event_type == "invoice.payment_failed":
        # Handle failed payment - notify customer
        customer_email = data.get("customer_email")
        if customer_email:
            send_email_task.delay(
                to_email=customer_email,
                subject="",
                template="payment_failed",
                context={
                    "first_name": data.get("customer_name", "").split()[0] if data.get("customer_name") else "there",
                    "portal_url": f"{settings.frontend_url}/dashboard/billing",
                },
            )

    elif event_type == "customer.subscription.updated":
        logger.info(f"Subscription updated: {data.get('id')}")

    elif event_type == "customer.subscription.deleted":
        logger.info(f"Subscription deleted: {data.get('id')}")

    return True


def _process_sendgrid_webhook(payload: Dict[str, Any]) -> bool:
    """Process SendGrid webhook events (bounces, opens, clicks)."""
    events = payload if isinstance(payload, list) else [payload]

    for event in events:
        event_type = event.get("event")
        email = event.get("email")

        if event_type == "bounce":
            logger.warning(f"Email bounced for: {email}")
        elif event_type == "dropped":
            logger.warning(f"Email dropped for: {email}")
        elif event_type == "open":
            logger.debug(f"Email opened by: {email}")
        elif event_type == "click":
            logger.debug(f"Email link clicked by: {email}")

    return True


# ==================== Analytics Aggregation ====================

@shared_task
def aggregate_analytics_task() -> bool:
    """
    Aggregate analytics data for reporting.

    Runs hourly to compute:
    - Call statistics
    - Lead conversion rates
    - Grid performance metrics
    """
    try:
        logger.info("Running analytics aggregation")
        return run_async(_aggregate_analytics_async())
    except Exception as exc:
        logger.error(f"Analytics aggregation failed: {exc}")
        return False


async def _aggregate_analytics_async() -> bool:
    """Async implementation of analytics aggregation."""
    from sqlalchemy import select, func
    from src.app.core.database import async_session_maker
    from src.app.models.call import VideoCall, CallStatus
    from src.app.models.professional import ProfessionalProfile

    async with async_session_maker() as db:
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        # Get calls completed in last hour
        calls_result = await db.execute(
            select(func.count(VideoCall.id))
            .where(VideoCall.ended_at >= hour_ago)
            .where(VideoCall.status == CallStatus.COMPLETED)
        )
        hourly_calls = calls_result.scalar() or 0

        # Get average pickup time for the hour
        pickup_result = await db.execute(
            select(func.avg(VideoCall.pickup_time_seconds))
            .where(VideoCall.ended_at >= hour_ago)
            .where(VideoCall.pickup_time_seconds.isnot(None))
        )
        avg_pickup = pickup_result.scalar()

        # Get average call duration
        duration_result = await db.execute(
            select(func.avg(VideoCall.duration_seconds))
            .where(VideoCall.ended_at >= hour_ago)
            .where(VideoCall.duration_seconds.isnot(None))
        )
        avg_duration = duration_result.scalar()

        if avg_pickup and avg_duration:
            logger.info(
                f"Hourly analytics: {hourly_calls} calls, "
                f"avg pickup: {avg_pickup:.1f}s, avg duration: {avg_duration:.1f}s"
            )
        else:
            logger.info(f"Hourly analytics: {hourly_calls} calls")

        # Update professional rolling averages
        professionals = await db.execute(select(ProfessionalProfile))
        for prof in professionals.scalars().all():
            # Recalculate average pickup time
            pickup_avg = await db.execute(
                select(func.avg(VideoCall.pickup_time_seconds))
                .where(VideoCall.professional_id == prof.id)
                .where(VideoCall.pickup_time_seconds.isnot(None))
            )
            new_avg_pickup = pickup_avg.scalar()
            if new_avg_pickup:
                prof.avg_pickup_time_seconds = new_avg_pickup

        await db.commit()
        return True


# ==================== Daily Metrics Reset ====================

@shared_task
def reset_daily_metrics_task() -> bool:
    """
    Reset daily metrics at midnight.

    Resets:
    - time_online_today_seconds for all professionals
    - daily_spent for bid wallets
    """
    try:
        logger.info("Resetting daily metrics")
        return run_async(_reset_daily_metrics_async())
    except Exception as exc:
        logger.error(f"Daily metrics reset failed: {exc}")
        return False


async def _reset_daily_metrics_async() -> bool:
    """Async implementation of daily metrics reset."""
    from sqlalchemy import update
    from src.app.core.database import async_session_maker
    from src.app.models.professional import ProfessionalProfile
    from src.app.models.billing import PlacementBid

    async with async_session_maker() as db:
        # Reset time online for all professionals
        await db.execute(
            update(ProfessionalProfile)
            .values(time_online_today_seconds=0)
        )

        # Reset daily spent for placement bids
        await db.execute(
            update(PlacementBid)
            .values(daily_spent=0)
        )

        await db.commit()
        logger.info("Daily metrics reset completed")
        return True


# ==================== Lead Assignment ====================

@shared_task(bind=True, max_retries=3)
def process_lead_assignment_task(
    self,
    call_id: str,
    professional_id: str,
    borrower_id: Optional[str],
) -> bool:
    """
    Create lead from completed call.

    Args:
        call_id: The video call ID
        professional_id: Professional's profile ID
        borrower_id: Borrower's user ID (if authenticated)
    """
    try:
        logger.info(f"Processing lead assignment for call {call_id}")
        return run_async(_process_lead_assignment_async(call_id, professional_id, borrower_id))
    except Exception as exc:
        logger.error(f"Lead assignment failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


async def _process_lead_assignment_async(
    call_id: str,
    professional_id: str,
    borrower_id: Optional[str],
) -> bool:
    """Async implementation of lead assignment."""
    from sqlalchemy import select
    from src.app.core.database import async_session_maker
    from src.app.models.lead import Lead, LeadStatus
    from src.app.models.call import VideoCall
    from src.app.models.professional import ProfessionalProfile
    from src.app.models.user import User

    async with async_session_maker() as db:
        # Get call details
        call_result = await db.execute(
            select(VideoCall).where(VideoCall.id == UUID(call_id))
        )
        call = call_result.scalar_one_or_none()

        if not call:
            logger.warning(f"Call {call_id} not found")
            return False

        # Get professional email
        prof_result = await db.execute(
            select(ProfessionalProfile, User)
            .join(User, ProfessionalProfile.user_id == User.id)
            .where(ProfessionalProfile.id == UUID(professional_id))
        )
        row = prof_result.one_or_none()
        if not row:
            logger.warning(f"Professional {professional_id} not found")
            return False

        professional, user = row

        # Create lead
        lead = Lead(
            professional_id=UUID(professional_id),
            borrower_id=UUID(borrower_id) if borrower_id else None,
            source_call_id=UUID(call_id),
            lead_status=LeadStatus.NEW,
        )
        db.add(lead)
        await db.commit()

        # Send notification email
        send_email_task.delay(
            to_email=user.email,
            subject="",
            template="lead_notification",
            context={
                "call_id": call_id,
                "call_date": call.initiated_at.strftime("%B %d, %Y at %I:%M %p"),
            },
        )

        logger.info(f"Lead created for call {call_id}")
        return True


# ==================== Subscription Sync ====================

@shared_task
def sync_subscription_status_task() -> bool:
    """
    Sync subscription status with Stripe.

    Runs periodically to ensure local subscription
    data matches Stripe's records.
    """
    try:
        logger.info("Syncing subscription status with Stripe")
        return run_async(_sync_subscription_status_async())
    except Exception as exc:
        logger.error(f"Subscription sync failed: {exc}")
        return False


async def _sync_subscription_status_async() -> bool:
    """Async implementation of subscription sync."""
    if not settings.stripe_secret_key:
        logger.warning("Stripe not configured, skipping subscription sync")
        return False

    from sqlalchemy import select
    from src.app.core.database import async_session_maker
    from src.app.models.billing import Subscription, SubscriptionStatus
    from src.app.models.professional import ProfessionalProfile, SubscriptionTier

    stripe.api_key = settings.stripe_secret_key

    async with async_session_maker() as db:
        # Get all active subscriptions
        result = await db.execute(
            select(Subscription).where(
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.PAST_DUE,
                ])
            )
        )
        subscriptions = result.scalars().all()

        synced = 0
        for sub in subscriptions:
            if not sub.stripe_subscription_id:
                continue

            try:
                # Fetch from Stripe
                stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)

                # Update local status
                status_map = {
                    "active": SubscriptionStatus.ACTIVE,
                    "past_due": SubscriptionStatus.PAST_DUE,
                    "canceled": SubscriptionStatus.CANCELLED,
                    "unpaid": SubscriptionStatus.PAST_DUE,
                }
                new_status = status_map.get(stripe_sub.status)

                if new_status and sub.status != new_status:
                    logger.info(f"Subscription {sub.id} status changed: {sub.status} -> {new_status}")
                    sub.status = new_status

                    # If cancelled, downgrade professional
                    if new_status == SubscriptionStatus.CANCELLED:
                        prof_result = await db.execute(
                            select(ProfessionalProfile)
                            .where(ProfessionalProfile.id == sub.professional_id)
                        )
                        prof = prof_result.scalar_one_or_none()
                        if prof:
                            prof.subscription_tier = SubscriptionTier.FREE

                # Update period end
                sub.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
                sub.cancel_at_period_end = stripe_sub.cancel_at_period_end

                synced += 1

            except stripe.error.InvalidRequestError as e:
                logger.warning(f"Subscription {sub.stripe_subscription_id} not found in Stripe: {e}")
                sub.status = SubscriptionStatus.CANCELLED

        await db.commit()
        logger.info(f"Synced {synced} subscriptions with Stripe")
        return True


# ==================== Call Room Cleanup ====================

@shared_task
def cleanup_expired_call_rooms_task() -> bool:
    """
    Clean up expired call rooms from Redis.

    Removes rooms that have been inactive for too long.
    """
    try:
        logger.info("Cleaning up expired call rooms")
        return run_async(_cleanup_expired_call_rooms_async())
    except Exception as exc:
        logger.error(f"Call room cleanup failed: {exc}")
        return False


async def _cleanup_expired_call_rooms_async() -> bool:
    """Async implementation of call room cleanup."""
    import redis.asyncio as redis

    redis_client = redis.from_url(settings.redis_url)

    try:
        # Get all room keys
        room_keys = await redis_client.keys("call_room:*")

        now = datetime.utcnow()
        expired_count = 0

        for key in room_keys:
            room_data = await redis_client.hgetall(key)
            if not room_data:
                continue

            # Check if room is expired (ended more than 1 hour ago, or inactive for 30+ minutes)
            ended_at = room_data.get(b"ended_at")
            last_activity = room_data.get(b"last_activity")

            should_delete = False

            if ended_at:
                ended_time = datetime.fromisoformat(ended_at.decode())
                if (now - ended_time).total_seconds() > 3600:  # 1 hour
                    should_delete = True

            elif last_activity:
                last_time = datetime.fromisoformat(last_activity.decode())
                if (now - last_time).total_seconds() > 1800:  # 30 minutes
                    should_delete = True

            if should_delete:
                await redis_client.delete(key)
                expired_count += 1

        logger.info(f"Cleaned up {expired_count} expired call rooms")
        return True

    finally:
        await redis_client.close()


# ==================== Notification Tasks ====================

@shared_task
def notify_missed_call_task(
    professional_email: str,
    professional_name: str,
    call_time: str,
) -> bool:
    """Notify professional of a missed incoming call."""
    send_email_task.delay(
        professional_email,
        "",
        "incoming_call_missed",
        {
            "first_name": professional_name.split()[0],
            "call_time": call_time,
        },
    )
    return True


@shared_task
def send_call_summary_task(
    borrower_email: str,
    professional_name: str,
    duration_seconds: int,
    call_date: str,
) -> bool:
    """Send call summary to borrower after call ends."""
    send_email_task.delay(
        borrower_email,
        "",
        "call_summary",
        {
            "professional_name": professional_name,
            "duration": round(duration_seconds / 60, 1),
            "call_date": call_date,
        },
    )
    return True


# ==================== Grid Position Aggregation ====================

@shared_task
def aggregate_grid_positions_task() -> bool:
    """
    Aggregate grid positions for analytics.

    Runs daily to:
    - Calculate average grid position per professional
    - Update GridImpression records with position data
    - Compute click-through rates
    """
    try:
        logger.info("Running grid position aggregation")
        return run_async(_aggregate_grid_positions_async())
    except Exception as exc:
        logger.error(f"Grid position aggregation failed: {exc}")
        return False


async def _aggregate_grid_positions_async() -> bool:
    """Async implementation of grid position aggregation."""
    from datetime import date
    from sqlalchemy import select, func
    from sqlalchemy.dialects.postgresql import insert
    from src.app.core.database import async_session_maker
    from src.app.models.analytics import GridImpression
    from src.app.models.professional import ProfessionalProfile

    async with async_session_maker() as db:
        today = date.today()

        # Get all professionals who were online today
        online_pros = await db.execute(
            select(ProfessionalProfile.id)
            .where(ProfessionalProfile.profile_complete == True)
        )
        professional_ids = [row[0] for row in online_pros.fetchall()]

        if not professional_ids:
            logger.info("No active professionals to aggregate")
            return True

        # For each professional, ensure they have a GridImpression record for today
        # This handles professionals who went online but got no impressions
        for prof_id in professional_ids:
            # Check if record exists
            existing = await db.execute(
                select(GridImpression)
                .where(GridImpression.professional_id == prof_id)
                .where(GridImpression.date == today)
            )
            if existing.scalar_one_or_none() is None:
                # Create empty record for the day
                stmt = insert(GridImpression).values(
                    professional_id=prof_id,
                    date=today,
                    impressions_count=0,
                    clicks_count=0,
                    calls_initiated=0,
                    avg_position=None,
                )
                # Ignore if it was created by another process
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['professional_id', 'date']
                )
                await db.execute(stmt)

        await db.commit()

        # Calculate aggregate statistics for reporting
        stats_result = await db.execute(
            select(
                func.sum(GridImpression.impressions_count).label('total_impressions'),
                func.sum(GridImpression.clicks_count).label('total_clicks'),
                func.sum(GridImpression.calls_initiated).label('total_calls'),
                func.avg(GridImpression.avg_position).label('avg_position'),
                func.count(GridImpression.id).label('unique_professionals'),
            )
            .where(GridImpression.date == today)
        )
        stats = stats_result.one()

        total_impressions = stats.total_impressions or 0
        total_clicks = stats.total_clicks or 0
        total_calls = stats.total_calls or 0
        avg_position = stats.avg_position
        unique_professionals = stats.unique_professionals or 0

        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        call_rate = (total_calls / total_clicks * 100) if total_clicks > 0 else 0

        logger.info(
            f"Grid aggregation for {today}: "
            f"{total_impressions} impressions, {total_clicks} clicks ({ctr:.2f}% CTR), "
            f"{total_calls} calls ({call_rate:.2f}% conversion), "
            f"avg position: {avg_position:.1f if avg_position else 'N/A'}, "
            f"{unique_professionals} professionals shown"
        )

        return True
