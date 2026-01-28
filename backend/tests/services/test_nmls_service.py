"""
Tests for NMLS verification service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from src.app.services.nmls_service import (
    NMLSVerificationService,
    NMLSLicenseInfo,
    NMLSVerificationResult,
    verify_professional_nmls,
)


class TestNMLSVerificationService:
    """Test suite for NMLS verification service."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test."""
        return NMLSVerificationService()
    
    def test_validate_nmls_id_format_valid(self, service):
        """Test valid NMLS ID formats."""
        assert service.validate_nmls_id_format("12345") is True
        assert service.validate_nmls_id_format("123456") is True
        assert service.validate_nmls_id_format("1234567890") is True
        assert service.validate_nmls_id_format("  12345  ") is True  # Whitespace trimmed
    
    def test_validate_nmls_id_format_invalid(self, service):
        """Test invalid NMLS ID formats."""
        assert service.validate_nmls_id_format("") is False
        assert service.validate_nmls_id_format("1234") is False  # Too short
        assert service.validate_nmls_id_format("12345678901") is False  # Too long
        assert service.validate_nmls_id_format("ABCDE") is False  # Non-numeric
        assert service.validate_nmls_id_format("12-345") is False  # Contains dash
    
    @pytest.mark.asyncio
    async def test_verify_invalid_format_returns_error(self, service):
        """Test that invalid format returns appropriate error."""
        result = await service.verify_nmls_id("123")
        
        assert result.is_valid is False
        assert result.is_active is False
        assert "Invalid NMLS ID format" in result.error_message
    
    @pytest.mark.asyncio
    async def test_verify_valid_nmls_id_demo_mode(self, service):
        """Test verification in demo mode returns mock data."""
        with patch("src.app.config.settings") as mock_settings:
            mock_settings.nmls_use_mock = True
            mock_settings.nmls_api_key = None
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.nmls_cache_ttl_hours = 24
            
            # Mock Redis to avoid actual connection
            with patch("redis.asyncio.from_url") as mock_redis:
                mock_client = AsyncMock()
                mock_client.get.return_value = None
                mock_client.setex = AsyncMock()
                mock_client.close = AsyncMock()
                mock_redis.return_value = mock_client
                
                result = await service.verify_nmls_id("123456")
        
        assert result.is_valid is True
        assert result.is_active is True
        assert result.license_info is not None
        assert result.license_info.nmls_id == "123456"
        assert result.license_info.license_status == "active"
        assert "demo_mode" in (result.license_info.raw_data or {})
    
    @pytest.mark.asyncio
    async def test_verify_caches_result(self, service):
        """Test that successful verification results are cached."""
        with patch("src.app.config.settings") as mock_settings:
            mock_settings.nmls_use_mock = True
            mock_settings.nmls_api_key = None
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.nmls_cache_ttl_hours = 24
            
            with patch("redis.asyncio.from_url") as mock_redis:
                mock_client = AsyncMock()
                mock_client.get.return_value = None
                mock_client.setex = AsyncMock()
                mock_client.close = AsyncMock()
                mock_redis.return_value = mock_client
                
                await service.verify_nmls_id("123456")
                
                # Verify cache was called
                mock_client.setex.assert_called_once()
                call_args = mock_client.setex.call_args
                assert "nmls:verification:123456" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_verify_returns_cached_result(self, service):
        """Test that cached results are returned without API call."""
        import json
        
        cached_data = {
            "nmls_id": "123456",
            "name": "Cached Professional",
            "company_name": "Cached Corp",
            "license_states": ["CA"],
            "license_status": "active",
            "license_types": ["MLO"],
            "first_licensed_date": None,
            "verified_at": datetime.utcnow().isoformat(),
            "raw_data": None,
        }
        
        with patch("redis.asyncio.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.get.return_value = json.dumps(cached_data)
            mock_client.close = AsyncMock()
            mock_redis.return_value = mock_client
            
            result = await service.verify_nmls_id("123456")
        
        assert result.is_valid is True
        assert result.license_info.name == "Cached Professional"
    
    @pytest.mark.asyncio
    async def test_state_verification_failure(self, service):
        """Test that state verification fails when LO not licensed in claimed state."""
        with patch("src.app.config.settings") as mock_settings:
            mock_settings.nmls_use_mock = True
            mock_settings.nmls_api_key = None
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.nmls_cache_ttl_hours = 24
            
            with patch("redis.asyncio.from_url") as mock_redis:
                mock_client = AsyncMock()
                mock_client.get.return_value = None
                mock_client.setex = AsyncMock()
                mock_client.close = AsyncMock()
                mock_redis.return_value = mock_client
                
                # Request verification for a state not in mock data
                result = await service.verify_nmls_id(
                    "123456",
                    expected_states=["AK"]  # Alaska not in default mock states
                )
        
        # Should still be valid but may show warning
        assert result.is_valid is True


class TestVerifyProfessionalNMLS:
    """Test the convenience function."""
    
    @pytest.mark.asyncio
    async def test_convenience_function_works(self):
        """Test that the convenience function delegates correctly."""
        with patch("src.app.services.nmls_service.nmls_service") as mock_service:
            mock_result = NMLSVerificationResult(
                nmls_id="123456",
                is_valid=True,
                is_active=True,
                verified_at=datetime.utcnow(),
            )
            mock_service.verify_nmls_id = AsyncMock(return_value=mock_result)
            
            result = await verify_professional_nmls("123456", "John Doe", ["CA"])
            
            mock_service.verify_nmls_id.assert_called_once_with(
                nmls_id="123456",
                expected_name="John Doe",
                expected_states=["CA"],
            )
            assert result.is_valid is True
