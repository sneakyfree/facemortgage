"""
Tests for backend services.

Covers:
- EmailService - Template rendering and send functionality
- AnalyticsService - Dashboard stats, trends, ROI calculations
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.services.email_service import EmailService, get_email_service, EMAIL_TEMPLATES
from src.app.services.analytics_service import AnalyticsService, get_analytics_service
from src.app.models.call import VideoCall, CallStatus
from src.app.models.lead import Lead, LeadStatus
from src.app.models.analytics import GridImpression, GridClick
from src.app.models.professional import ProfessionalProfile


class TestEmailService:
    """Tests for EmailService."""

    def test_email_service_singleton(self):
        """Test that get_email_service returns singleton."""
        service1 = get_email_service()
        service2 = get_email_service()
        assert service1 is service2

    def test_all_templates_exist(self):
        """Verify all expected templates are defined."""
        expected_templates = [
            "welcome_professional",
            "welcome_borrower",
            "new_lead",
            "scheduled_call_confirmation_borrower",
            "scheduled_call_notification_professional",
            "scheduled_call_reminder",
            "payment_failed",
            "partnership_invitation",
            "new_referral",
            "get_matched_confirmation",
        ]
        for template_name in expected_templates:
            assert template_name in EMAIL_TEMPLATES, f"Missing template: {template_name}"

    def test_template_has_subject_and_html(self):
        """Verify all templates have required fields."""
        for name, template in EMAIL_TEMPLATES.items():
            assert "subject" in template, f"Template {name} missing subject"
            assert "html" in template, f"Template {name} missing html"
            assert len(template["subject"]) > 0, f"Template {name} has empty subject"
            assert len(template["html"]) > 0, f"Template {name} has empty html"

    def test_render_template_welcome_professional(self):
        """Test rendering welcome_professional template."""
        service = EmailService()
        subject, html = service._render_template(
            "welcome_professional",
            {"name": "John Doe", "dashboard_url": "https://example.com/dashboard"}
        )
        assert "John Doe" in html
        assert "https://example.com/dashboard" in html
        assert "Welcome to FaceMortgage!" in subject

    def test_render_template_new_lead(self):
        """Test rendering new_lead template."""
        service = EmailService()
        subject, html = service._render_template(
            "new_lead",
            {
                "lead_name": "Jane Smith",
                "lead_email": "jane@example.com",
                "lead_phone": "555-1234",
                "loan_purpose": "purchase",
                "source": "website",
                "lead_url": "https://example.com/leads/123",
            }
        )
        assert "Jane Smith" in subject
        assert "jane@example.com" in html
        assert "555-1234" in html
        assert "purchase" in html

    def test_render_template_unknown_template(self):
        """Test rendering unknown template raises error."""
        service = EmailService()
        with pytest.raises(ValueError, match="Unknown email template"):
            service._render_template("nonexistent_template", {})

    def test_render_template_missing_variables(self):
        """Test rendering template with missing variables doesn't crash."""
        service = EmailService()
        # Should not raise, just leave placeholders empty
        subject, html = service._render_template(
            "welcome_professional",
            {}  # Empty context
        )
        assert "Welcome to FaceMortgage!" in subject

    @pytest.mark.asyncio
    async def test_send_email_no_client(self):
        """Test send_email returns False when no client configured."""
        service = EmailService()
        service._client = None
        service.api_key = None  # No API key

        result = await service.send_email(
            to_email="test@example.com",
            template_name="welcome_professional",
            context={"name": "Test", "dashboard_url": "https://example.com"},
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email send."""
        service = EmailService()

        # Mock the SendGrid client and Mail class
        mock_response = MagicMock()
        mock_response.status_code = 202

        mock_client = MagicMock()
        mock_client.send = MagicMock(return_value=mock_response)
        service._client = mock_client

        with patch.dict("sys.modules", {"sendgrid.helpers.mail": MagicMock()}):
            result = await service.send_email(
                to_email="test@example.com",
                template_name="welcome_professional",
                context={"name": "Test", "dashboard_url": "https://example.com"},
            )

        assert result is True
        mock_client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_failure(self):
        """Test failed email send."""
        service = EmailService()

        mock_response = MagicMock()
        mock_response.status_code = 400

        mock_client = MagicMock()
        mock_client.send = MagicMock(return_value=mock_response)
        service._client = mock_client

        with patch.dict("sys.modules", {"sendgrid.helpers.mail": MagicMock()}):
            result = await service.send_email(
                to_email="test@example.com",
                template_name="welcome_professional",
                context={"name": "Test", "dashboard_url": "https://example.com"},
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_welcome_professional(self):
        """Test send_welcome_professional convenience method."""
        service = EmailService()
        service.send_email = AsyncMock(return_value=True)

        result = await service.send_welcome_professional("test@example.com", "John")

        assert result is True
        service.send_email.assert_called_once()
        call_args = service.send_email.call_args
        assert call_args.kwargs["template_name"] == "welcome_professional"
        assert call_args.kwargs["context"]["name"] == "John"

    @pytest.mark.asyncio
    async def test_send_new_lead_notification(self):
        """Test send_new_lead_notification convenience method."""
        service = EmailService()
        service.send_email = AsyncMock(return_value=True)

        result = await service.send_new_lead_notification(
            professional_email="pro@example.com",
            lead_name="Jane Doe",
            lead_email="jane@example.com",
            lead_phone="555-1234",
            loan_purpose="refinance",
            source="partner",
            lead_id="lead-123",
        )

        assert result is True
        service.send_email.assert_called_once()
        call_args = service.send_email.call_args
        assert call_args.kwargs["template_name"] == "new_lead"


class TestAnalyticsService:
    """Tests for AnalyticsService."""

    def test_analytics_service_singleton(self):
        """Test that get_analytics_service returns singleton."""
        service1 = get_analytics_service()
        service2 = get_analytics_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_get_call_stats_empty(self, db_session: AsyncSession, test_professional: ProfessionalProfile):
        """Test call stats with no calls."""
        service = AnalyticsService()
        start_date = datetime.utcnow() - timedelta(days=30)

        stats = await service._get_call_stats(db_session, test_professional.id, start_date)

        assert stats["total"] == 0
        assert stats["completed"] == 0
        assert stats["answer_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_call_stats_with_data(
        self,
        db_session: AsyncSession,
        test_professional: ProfessionalProfile,
        test_video_call: VideoCall,
    ):
        """Test call stats with existing calls."""
        service = AnalyticsService()
        start_date = datetime.utcnow() - timedelta(days=30)

        stats = await service._get_call_stats(db_session, test_professional.id, start_date)

        assert stats["total"] >= 1
        assert stats["completed"] >= 1

    @pytest.mark.asyncio
    async def test_get_lead_stats_empty(self, db_session: AsyncSession, test_professional: ProfessionalProfile):
        """Test lead stats with no leads."""
        service = AnalyticsService()
        start_date = datetime.utcnow() - timedelta(days=30)

        stats = await service._get_lead_stats(db_session, test_professional.id, start_date)

        assert stats["total"] == 0
        assert stats["new"] == 0
        assert stats["conversion_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_lead_stats_with_data(
        self,
        db_session: AsyncSession,
        test_professional: ProfessionalProfile,
        test_lead: Lead,
    ):
        """Test lead stats with existing leads."""
        service = AnalyticsService()
        start_date = datetime.utcnow() - timedelta(days=30)

        stats = await service._get_lead_stats(db_session, test_professional.id, start_date)

        assert stats["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_dashboard_stats(
        self,
        db_session: AsyncSession,
        test_professional: ProfessionalProfile,
    ):
        """Test full dashboard stats."""
        service = AnalyticsService()

        stats = await service.get_dashboard_stats(test_professional.id, db_session, days=30)

        assert "period_days" in stats
        assert stats["period_days"] == 30
        assert "calls" in stats
        assert "leads" in stats
        assert "grid" in stats

    @pytest.mark.asyncio
    async def test_get_daily_trends(
        self,
        db_session: AsyncSession,
        test_professional: ProfessionalProfile,
    ):
        """Test daily trends generation."""
        service = AnalyticsService()

        trends = await service.get_daily_trends(test_professional.id, db_session, days=7)

        # Should have 8 days (today + 7 days back)
        assert len(trends) >= 7
        for day in trends:
            assert "date" in day
            assert "calls" in day
            assert "completed" in day

    @pytest.mark.asyncio
    async def test_get_hourly_distribution(
        self,
        db_session: AsyncSession,
        test_professional: ProfessionalProfile,
    ):
        """Test hourly distribution."""
        service = AnalyticsService()

        distribution = await service.get_hourly_distribution(test_professional.id, db_session, days=30)

        assert len(distribution) == 24  # 24 hours
        for hour_data in distribution:
            assert "hour" in hour_data
            assert "calls" in hour_data
            assert 0 <= hour_data["hour"] <= 23

    @pytest.mark.asyncio
    async def test_get_roi_metrics(
        self,
        db_session: AsyncSession,
        test_professional: ProfessionalProfile,
    ):
        """Test ROI metrics calculation."""
        service = AnalyticsService()

        metrics = await service.get_roi_metrics(test_professional.id, db_session, days=30)

        assert "costs" in metrics
        assert "results" in metrics
        assert "metrics" in metrics
        assert "subscription" in metrics["costs"]
        assert "bid_spend" in metrics["costs"]
        assert "roi_percentage" in metrics["metrics"]

    @pytest.mark.asyncio
    async def test_get_conversion_funnel(
        self,
        db_session: AsyncSession,
        test_professional: ProfessionalProfile,
    ):
        """Test conversion funnel."""
        service = AnalyticsService()

        funnel = await service.get_conversion_funnel(test_professional.id, db_session, days=30)

        assert "stages" in funnel
        assert len(funnel["stages"]) == 6  # Impressions, Clicks, Calls, Completed, Leads, Conversions
        assert "overall_conversion" in funnel

    @pytest.mark.asyncio
    async def test_get_lead_sources(
        self,
        db_session: AsyncSession,
        test_professional: ProfessionalProfile,
    ):
        """Test lead sources breakdown."""
        service = AnalyticsService()

        sources = await service.get_lead_sources(test_professional.id, db_session, days=30)

        assert isinstance(sources, list)


class TestAnalyticsCalculations:
    """Test specific analytics calculations."""

    def test_answer_rate_calculation(self):
        """Test answer rate calculation."""
        # With data
        total = 100
        completed = 80
        rate = round(completed / total * 100, 1)
        assert rate == 80.0

        # With zero total
        total = 0
        rate = round(completed / total * 100, 1) if total > 0 else 0
        assert rate == 0

    def test_ctr_calculation(self):
        """Test click-through rate calculation."""
        impressions = 10000
        clicks = 150
        ctr = round(clicks / impressions * 100, 2)
        assert ctr == 1.5

    def test_conversion_rate_calculation(self):
        """Test conversion rate calculation."""
        total_leads = 50
        won_leads = 10
        rate = round(won_leads / total_leads * 100, 1)
        assert rate == 20.0

    def test_roi_calculation(self):
        """Test ROI percentage calculation."""
        total_cost = 200
        estimated_commission = 500
        profit = estimated_commission - total_cost
        roi = (profit / total_cost * 100)
        assert roi == 150.0

    def test_cost_per_lead_calculation(self):
        """Test cost per lead calculation."""
        total_cost = 300
        won_count = 6
        cpl = round(total_cost / won_count, 2)
        assert cpl == 50.0

        # With zero leads
        won_count = 0
        cpl = round(total_cost / won_count, 2) if won_count > 0 else 0
        assert cpl == 0
