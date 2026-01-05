"""
Email notification service using SendGrid.

Handles transactional emails for:
- Welcome emails
- New lead notifications
- Scheduled call reminders
- Payment notifications
- Partnership invitations
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from src.app.config import settings

logger = logging.getLogger(__name__)


# Email Templates
EMAIL_TEMPLATES: Dict[str, Dict[str, str]] = {
    "welcome_professional": {
        "subject": "Welcome to FaceMortgage!",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">Welcome to FaceMortgage!</h1>
    </div>
    <p>Hi {{name}},</p>
    <p>Thank you for joining FaceMortgage! You're now ready to connect with borrowers instantly via video.</p>
    <p>Here's what to do next:</p>
    <ol>
        <li><strong>Complete your profile</strong> - Add your bio, specialties, and a professional photo</li>
        <li><strong>Upload an intro video</strong> - Let borrowers get to know you before they call</li>
        <li><strong>Go online</strong> - Start appearing in the grid and receive calls</li>
    </ol>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{dashboard_url}}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Go to Dashboard</a>
    </div>
    <p>If you have any questions, our support team is here to help.</p>
    <p>Best,<br>The FaceMortgage Team</p>
</body>
</html>
""",
    },
    "welcome_borrower": {
        "subject": "Welcome to FaceMortgage!",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">Welcome to FaceMortgage!</h1>
    </div>
    <p>Hi {{name}},</p>
    <p>Thank you for creating an account! You can now connect with mortgage professionals instantly via video call.</p>
    <p>With FaceMortgage, you can:</p>
    <ul>
        <li>Talk face-to-face with licensed professionals</li>
        <li>Get answers to your mortgage questions in real-time</li>
        <li>Compare multiple professionals before committing</li>
    </ul>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{home_url}}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Browse Professionals</a>
    </div>
    <p>Best,<br>The FaceMortgage Team</p>
</body>
</html>
""",
    },
    "new_lead": {
        "subject": "New Lead: {{lead_name}}",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #166534;">You have a new lead!</h2>
    </div>
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Name:</strong></td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{{lead_name}}</td>
        </tr>
        <tr>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><a href="mailto:{{lead_email}}">{{lead_email}}</a></td>
        </tr>
        <tr>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Phone:</strong></td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{{lead_phone}}</td>
        </tr>
        <tr>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Loan Purpose:</strong></td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{{loan_purpose}}</td>
        </tr>
        <tr>
            <td style="padding: 10px 0;"><strong>Source:</strong></td>
            <td style="padding: 10px 0;">{{source}}</td>
        </tr>
    </table>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{lead_url}}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Lead Details</a>
    </div>
    <p style="color: #6b7280; font-size: 14px;">
        Tip: Reach out within 5 minutes to maximize your conversion rate!
    </p>
</body>
</html>
""",
    },
    "scheduled_call_confirmation_borrower": {
        "subject": "Your call with {{professional_name}} is scheduled!",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">Call Scheduled!</h1>
    </div>
    <p>Hi {{borrower_name}},</p>
    <p>Your video call with <strong>{{professional_name}}</strong> has been scheduled.</p>
    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0;"><strong>Date:</strong> {{scheduled_date}}</p>
        <p style="margin: 10px 0 0;"><strong>Time:</strong> {{scheduled_time}} ({{timezone}})</p>
    </div>
    <p>You'll receive a reminder 15 minutes before your call.</p>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{calendar_link}}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Add to Calendar</a>
    </div>
    <p>Best,<br>The FaceMortgage Team</p>
</body>
</html>
""",
    },
    "scheduled_call_notification_professional": {
        "subject": "New scheduled call with {{borrower_name}}",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 15px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #1e40af;">New Scheduled Call</h2>
    </div>
    <p>You have a new video call scheduled with <strong>{{borrower_name}}</strong>.</p>
    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0;"><strong>Date:</strong> {{scheduled_date}}</p>
        <p style="margin: 10px 0;"><strong>Time:</strong> {{scheduled_time}} ({{timezone}})</p>
        <p style="margin: 10px 0 0;"><strong>Contact:</strong> {{borrower_email}}</p>
    </div>
    {{#if notes}}
    <p><strong>Notes from borrower:</strong><br>{{notes}}</p>
    {{/if}}
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{dashboard_url}}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View in Dashboard</a>
    </div>
</body>
</html>
""",
    },
    "scheduled_call_reminder": {
        "subject": "Reminder: Call with {{contact_name}} in 15 minutes",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #92400e;">Upcoming Call Reminder</h2>
    </div>
    <p>Your scheduled call with <strong>{{contact_name}}</strong> starts in 15 minutes.</p>
    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0;"><strong>Time:</strong> {{scheduled_time}} ({{timezone}})</p>
    </div>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{call_url}}" style="background: #22c55e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Join Call Now</a>
    </div>
</body>
</html>
""",
    },
    "payment_failed": {
        "subject": "Payment Failed - Action Required",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #991b1b;">Payment Issue</h2>
    </div>
    <p>Hi {{name}},</p>
    <p>We were unable to process your payment for your FaceMortgage subscription.</p>
    <p><strong>What this means:</strong></p>
    <ul>
        <li>Your placement bids have been paused</li>
        <li>You may not appear at the top of the grid</li>
    </ul>
    <p>Please update your payment method to restore full service.</p>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{billing_url}}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Update Payment Method</a>
    </div>
    <p>If you have questions, please contact support.</p>
    <p>Best,<br>The FaceMortgage Team</p>
</body>
</html>
""",
    },
    "partnership_invitation": {
        "subject": "{{lo_name}} invited you to partner on FaceMortgage",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">Partnership Invitation</h1>
    </div>
    <p>Hi {{realtor_name}},</p>
    <p><strong>{{lo_name}}</strong> from {{lo_company}} has invited you to partner with them on FaceMortgage.</p>
    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0 0 10px;"><strong>As partners, you can:</strong></p>
        <ul style="margin: 0;">
            <li>Refer clients directly to {{lo_name}}</li>
            <li>Track referral status and outcomes</li>
            <li>Add a financing widget to your listings</li>
            <li>Earn referral bonuses on closed deals</li>
        </ul>
    </div>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{accept_url}}" style="background: #22c55e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Accept Invitation</a>
    </div>
    <p style="color: #6b7280; font-size: 14px;">
        This invitation expires in 7 days.
    </p>
</body>
</html>
""",
    },
    "new_referral": {
        "subject": "New Referral from {{realtor_name}}: {{borrower_name}}",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #166534;">New Partner Referral!</h2>
    </div>
    <p>Your partner <strong>{{realtor_name}}</strong> has referred a new client to you.</p>
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Client Name:</strong></td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{{borrower_name}}</td>
        </tr>
        <tr>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><a href="mailto:{{borrower_email}}">{{borrower_email}}</a></td>
        </tr>
        <tr>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Phone:</strong></td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{{borrower_phone}}</td>
        </tr>
        <tr>
            <td style="padding: 10px 0;"><strong>Property:</strong></td>
            <td style="padding: 10px 0;">{{property_address}}</td>
        </tr>
    </table>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{lead_url}}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Referral</a>
    </div>
</body>
</html>
""",
    },
    "get_matched_confirmation": {
        "subject": "We're finding you the perfect mortgage professional!",
        "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">We Got Your Request!</h1>
    </div>
    <p>Hi {{name}},</p>
    <p>Thank you for using FaceMortgage! We're finding the perfect mortgage professional based on your preferences.</p>
    <div style="background: #eff6ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0;"><strong>What happens next:</strong></p>
        <ol style="margin: 10px 0 0;">
            <li>We'll match you with a qualified professional</li>
            <li>They'll reach out within 24 hours</li>
            <li>No obligation - take your time to decide</li>
        </ol>
    </div>
    <p>In the meantime, you can browse professionals and connect instantly:</p>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{browse_url}}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Browse Professionals</a>
    </div>
    <p>Best,<br>The FaceMortgage Team</p>
</body>
</html>
""",
    },
}


class EmailService:
    """Email service using SendGrid for transactional emails."""

    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        self.from_email = settings.from_email
        self._client = None

    @property
    def client(self):
        """Lazy-load SendGrid client."""
        if self._client is None and self.api_key:
            try:
                from sendgrid import SendGridAPIClient
                self._client = SendGridAPIClient(self.api_key)
            except ImportError:
                logger.warning("SendGrid not installed. Email sending disabled.")
        return self._client

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> tuple:
        """Render an email template with context variables."""
        template = EMAIL_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Unknown email template: {template_name}")

        subject = template["subject"]
        html = template["html"]

        # Simple template variable replacement
        for key, value in context.items():
            subject = subject.replace(f"{{{{{key}}}}}", str(value) if value else "")
            html = html.replace(f"{{{{{key}}}}}", str(value) if value else "")

        return subject, html

    async def send_email(
        self,
        to_email: str,
        template_name: str,
        context: Dict[str, Any],
    ) -> bool:
        """
        Send a templated email.

        Args:
            to_email: Recipient email address
            template_name: Name of the template to use
            context: Variables to substitute in the template

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.client:
            logger.warning(f"Email not sent (no client): {template_name} to {to_email}")
            return False

        try:
            from sendgrid.helpers.mail import Mail

            subject, html_content = self._render_template(template_name, context)

            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
            )

            response = self.client.send(message)
            success = response.status_code in (200, 201, 202)

            if success:
                logger.info(f"Email sent: {template_name} to {to_email}")
            else:
                logger.error(f"Email failed: {template_name} to {to_email}, status={response.status_code}")

            return success

        except Exception as e:
            logger.error(f"Email send error: {template_name} to {to_email}: {e}")
            return False

    # Convenience methods for common email types

    async def send_welcome_professional(self, email: str, name: str) -> bool:
        """Send welcome email to new professional."""
        return await self.send_email(
            to_email=email,
            template_name="welcome_professional",
            context={
                "name": name,
                "dashboard_url": f"{settings.frontend_url}/dashboard",
            },
        )

    async def send_welcome_borrower(self, email: str, name: str) -> bool:
        """Send welcome email to new borrower."""
        return await self.send_email(
            to_email=email,
            template_name="welcome_borrower",
            context={
                "name": name,
                "home_url": settings.frontend_url,
            },
        )

    async def send_new_lead_notification(
        self,
        professional_email: str,
        lead_name: str,
        lead_email: str,
        lead_phone: Optional[str],
        loan_purpose: Optional[str],
        source: str,
        lead_id: str,
    ) -> bool:
        """Notify professional of new lead."""
        return await self.send_email(
            to_email=professional_email,
            template_name="new_lead",
            context={
                "lead_name": lead_name,
                "lead_email": lead_email,
                "lead_phone": lead_phone or "Not provided",
                "loan_purpose": loan_purpose or "Not specified",
                "source": source,
                "lead_url": f"{settings.frontend_url}/dashboard/leads/{lead_id}",
            },
        )

    async def send_scheduled_call_confirmation(
        self,
        borrower_email: str,
        borrower_name: str,
        professional_name: str,
        scheduled_date: str,
        scheduled_time: str,
        timezone: str,
    ) -> bool:
        """Send confirmation to borrower for scheduled call."""
        return await self.send_email(
            to_email=borrower_email,
            template_name="scheduled_call_confirmation_borrower",
            context={
                "borrower_name": borrower_name,
                "professional_name": professional_name,
                "scheduled_date": scheduled_date,
                "scheduled_time": scheduled_time,
                "timezone": timezone,
                "calendar_link": settings.frontend_url,  # Could generate iCal link
            },
        )

    async def send_scheduled_call_notification(
        self,
        professional_email: str,
        borrower_name: str,
        borrower_email: str,
        scheduled_date: str,
        scheduled_time: str,
        timezone: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Notify professional of new scheduled call."""
        return await self.send_email(
            to_email=professional_email,
            template_name="scheduled_call_notification_professional",
            context={
                "borrower_name": borrower_name,
                "borrower_email": borrower_email,
                "scheduled_date": scheduled_date,
                "scheduled_time": scheduled_time,
                "timezone": timezone,
                "notes": notes,
                "dashboard_url": f"{settings.frontend_url}/dashboard",
            },
        )

    async def send_call_reminder(
        self,
        email: str,
        contact_name: str,
        scheduled_time: str,
        timezone: str,
        call_id: str,
    ) -> bool:
        """Send 15-minute reminder for scheduled call."""
        return await self.send_email(
            to_email=email,
            template_name="scheduled_call_reminder",
            context={
                "contact_name": contact_name,
                "scheduled_time": scheduled_time,
                "timezone": timezone,
                "call_url": f"{settings.frontend_url}/call/scheduled/{call_id}",
            },
        )

    async def send_payment_failed(self, email: str, name: str) -> bool:
        """Notify professional of failed payment."""
        return await self.send_email(
            to_email=email,
            template_name="payment_failed",
            context={
                "name": name,
                "billing_url": f"{settings.frontend_url}/dashboard/billing",
            },
        )

    async def send_partnership_invitation(
        self,
        realtor_email: str,
        realtor_name: str,
        lo_name: str,
        lo_company: str,
        invitation_token: str,
    ) -> bool:
        """Send partnership invitation to realtor."""
        return await self.send_email(
            to_email=realtor_email,
            template_name="partnership_invitation",
            context={
                "realtor_name": realtor_name,
                "lo_name": lo_name,
                "lo_company": lo_company,
                "accept_url": f"{settings.frontend_url}/partner/accept/{invitation_token}",
            },
        )

    async def send_new_referral_notification(
        self,
        professional_email: str,
        realtor_name: str,
        borrower_name: str,
        borrower_email: str,
        borrower_phone: Optional[str],
        property_address: Optional[str],
        lead_id: str,
    ) -> bool:
        """Notify professional of new partner referral."""
        return await self.send_email(
            to_email=professional_email,
            template_name="new_referral",
            context={
                "realtor_name": realtor_name,
                "borrower_name": borrower_name,
                "borrower_email": borrower_email,
                "borrower_phone": borrower_phone or "Not provided",
                "property_address": property_address or "Not specified",
                "lead_url": f"{settings.frontend_url}/dashboard/leads/{lead_id}",
            },
        )

    async def send_get_matched_confirmation(self, email: str, name: str) -> bool:
        """Send confirmation for Get Matched submission."""
        return await self.send_email(
            to_email=email,
            template_name="get_matched_confirmation",
            context={
                "name": name,
                "browse_url": settings.frontend_url,
            },
        )


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
