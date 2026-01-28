"""
Unit tests for the TimescaleDB Metrics Service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.app.services.metrics_service import MetricsService, get_metrics_service
from src.app.models.metrics import (
    CallMetric, GridViewMetric, LeadMetric, 
    BillingMetric, SystemMetric
)


class TestMetricsService:
    """Tests for MetricsService"""
    
    @pytest.fixture
    def metrics_service(self):
        """Create a metrics service for testing."""
        service = MetricsService(database_url=None)  # Log-only mode
        return service
    
    @pytest.mark.asyncio
    async def test_record_call_log_only_mode(self, metrics_service):
        """Test recording a call in log-only mode (no DB) - should not raise."""
        professional_id = uuid4()
        
        # Should complete without error even when DB is not configured
        await metrics_service.record_call(
            professional_id=professional_id,
            duration_seconds=300,
            was_answered=True,
            was_completed=True,
            rating=4.5,
            source='grid',
        )
        # If we get here, the test passed (no exception)
        assert True
        
    @pytest.mark.asyncio
    async def test_record_grid_event_log_only_mode(self, metrics_service):
        """Test recording a grid event in log-only mode."""
        professional_id = uuid4()
        
        await metrics_service.record_grid_event(
            professional_id=professional_id,
            event_type='impression',
            grid_position=3,
            total_results=20,
        )
        assert True
        
    @pytest.mark.asyncio
    async def test_record_lead_event_log_only_mode(self, metrics_service):
        """Test recording a lead event in log-only mode."""
        professional_id = uuid4()
        lead_id = uuid4()
        
        await metrics_service.record_lead_event(
            professional_id=professional_id,
            status='qualified',
            lead_id=lead_id,
            previous_status='contacted',
            estimated_loan_amount=500000.0,
        )
        assert True
        
    @pytest.mark.asyncio
    async def test_record_billing_event_log_only_mode(self, metrics_service):
        """Test recording a billing event in log-only mode."""
        professional_id = uuid4()
        
        await metrics_service.record_billing_event(
            professional_id=professional_id,
            transaction_type='subscription',
            amount_cents=2999,
            subscription_tier='professional',
        )
        assert True
        
    @pytest.mark.asyncio
    async def test_record_system_metric_log_only_mode(self, metrics_service):
        """Test recording a system metric in log-only mode."""
        await metrics_service.record_system_metric(
            metric_name='api_latency_ms',
            metric_value=42.5,
            dimension_1='/api/v1/professionals',
            dimension_2='200',
        )
        assert True
        
    @pytest.mark.asyncio
    async def test_get_call_stats_returns_empty_when_not_initialized(self, metrics_service):
        """Test that query methods return empty results when not initialized."""
        professional_id = uuid4()
        start_time = datetime.utcnow() - timedelta(days=7)
        
        result = await metrics_service.get_call_stats(
            professional_id=professional_id,
            start_time=start_time,
        )
        
        assert result == []
        
    @pytest.mark.asyncio
    async def test_get_grid_performance_returns_empty_when_not_initialized(self, metrics_service):
        """Test grid performance query returns empty when not initialized."""
        professional_id = uuid4()
        start_time = datetime.utcnow() - timedelta(days=7)
        
        result = await metrics_service.get_grid_performance(
            professional_id=professional_id,
            start_time=start_time,
        )
        
        assert result == {}
        
    @pytest.mark.asyncio
    async def test_get_lead_funnel_returns_empty_when_not_initialized(self, metrics_service):
        """Test lead funnel query returns empty when not initialized."""
        professional_id = uuid4()
        start_time = datetime.utcnow() - timedelta(days=7)
        
        result = await metrics_service.get_lead_funnel(
            professional_id=professional_id,
            start_time=start_time,
        )
        
        assert result == {}


class TestMetricsServiceSingleton:
    """Tests for the singleton pattern."""
    
    def test_get_metrics_service_returns_same_instance(self):
        """Test that get_metrics_service returns the same instance."""
        # Reset singleton for test
        import src.app.services.metrics_service as module
        module._metrics_service = None
        
        service1 = get_metrics_service()
        service2 = get_metrics_service()
        
        assert service1 is service2


class TestMetricsModels:
    """Tests for metrics models."""
    
    def test_call_metric_creation(self):
        """Test CallMetric model creation."""
        metric = CallMetric(
            timestamp=datetime.utcnow(),
            professional_id=uuid4(),
            duration_seconds=180,
            was_answered=True,
            was_completed=True,
        )
        
        assert metric.duration_seconds == 180
        assert metric.was_answered is True
        
    def test_grid_view_metric_creation(self):
        """Test GridViewMetric model creation."""
        metric = GridViewMetric(
            timestamp=datetime.utcnow(),
            professional_id=uuid4(),
            event_type='click',
            grid_position=5,
        )
        
        assert metric.event_type == 'click'
        assert metric.grid_position == 5
        
    def test_lead_metric_creation(self):
        """Test LeadMetric model creation."""
        metric = LeadMetric(
            timestamp=datetime.utcnow(),
            professional_id=uuid4(),
            status='converted',
            estimated_loan_amount=750000.0,
        )
        
        assert metric.status == 'converted'
        assert metric.estimated_loan_amount == 750000.0
        
    def test_billing_metric_creation(self):
        """Test BillingMetric model creation."""
        metric = BillingMetric(
            timestamp=datetime.utcnow(),
            professional_id=uuid4(),
            transaction_type='bid',
            amount_cents=500,
            bid_type='grid_placement',
        )
        
        assert metric.transaction_type == 'bid'
        assert metric.amount_cents == 500
        
    def test_system_metric_creation(self):
        """Test SystemMetric model creation."""
        metric = SystemMetric(
            timestamp=datetime.utcnow(),
            metric_name='concurrent_users',
            metric_value=142.0,
        )
        
        assert metric.metric_name == 'concurrent_users'
        assert metric.metric_value == 142.0
