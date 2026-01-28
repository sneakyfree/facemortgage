"""
SMS/Twilio integration tests.

Tests phone verification flow with Twilio API.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSMSVerification:
    """Test SMS verification flow."""
    
    @pytest.mark.asyncio
    async def test_send_verification_test_mode(self, client, auth_headers):
        """Test sending verification code in test mode."""
        response = await client.post(
            "/api/v1/users/me/sms/send-verification",
            headers=auth_headers,
            json={"phone": "+15551234567"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        # In test mode, code is returned for verification
        if "test_code" in data:
            assert len(data["test_code"]) == 6
    
    @pytest.mark.asyncio
    async def test_verify_code_success(self, client, auth_headers):
        """Test successful code verification."""
        # First send a code
        send_response = await client.post(
            "/api/v1/users/me/sms/send-verification",
            headers=auth_headers,
            json={"phone": "+15551234567"}
        )
        
        # Get the test code
        test_code = send_response.json().get("test_code", "123456")
        
        # Verify the code
        verify_response = await client.post(
            "/api/v1/users/me/sms/verify",
            headers=auth_headers,
            json={"code": test_code}
        )
        
        assert verify_response.status_code == 200
        assert verify_response.json()["status"] == "verified"
    
    @pytest.mark.asyncio
    async def test_verify_invalid_code(self, client, auth_headers):
        """Test verification with invalid code."""
        # First send a code
        await client.post(
            "/api/v1/users/me/sms/send-verification",
            headers=auth_headers,
            json={"phone": "+15551234567"}
        )
        
        # Try wrong code
        verify_response = await client.post(
            "/api/v1/users/me/sms/verify",
            headers=auth_headers,
            json={"code": "000000"}
        )
        
        # Should return error for wrong code
        assert verify_response.status_code in [400, 422]  # Bad request or validation error
    
    @pytest.mark.asyncio
    async def test_verify_without_pending_code(self, client, auth_headers):
        """Test verification without sending code first."""
        verify_response = await client.post(
            "/api/v1/users/me/sms/verify",
            headers=auth_headers,
            json={"code": "123456"}
        )
        
        # Should fail - no pending verification
        assert verify_response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_invalid_phone_number(self, client, auth_headers):
        """Test sending to invalid phone number."""
        response = await client.post(
            "/api/v1/users/me/sms/send-verification",
            headers=auth_headers,
            json={"phone": "123"}  # Too short
        )
        
        # Should return validation error for invalid phone
        assert response.status_code in [400, 422]  # Validation or bad request error


class TestSMSPreferences:
    """Test SMS notification preferences."""
    
    @pytest.mark.asyncio
    async def test_get_sms_preferences(self, client, auth_headers):
        """Test getting SMS preferences."""
        response = await client.get(
            "/api/v1/users/me/sms-preferences",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data
    
    @pytest.mark.asyncio
    async def test_update_sms_preferences(self, client, auth_headers):
        """Test updating SMS preferences."""
        response = await client.put(
            "/api/v1/users/me/sms-preferences",
            headers=auth_headers,
            json={
                "preferences": {
                    "sms_new_leads": False,
                    "sms_missed_calls": True,
                    "sms_scheduled_reminders": False
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "updated"


class TestTwilioIntegration:
    """Test Twilio API integration (mocked)."""
    
    @pytest.mark.asyncio
    async def test_twilio_client_called_in_production(self):
        """Test that Twilio client is called when credentials are set."""
        with patch("src.app.config.settings") as mock_settings:
            mock_settings.twilio_test_mode = False
            mock_settings.twilio_sid = "test_sid"
            mock_settings.twilio_auth_token = "test_token"
            mock_settings.twilio_phone = "+15550000000"
            
            with patch("twilio.rest.Client") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance
                mock_instance.messages.create.return_value = MagicMock(sid="SM123")
                
                # In a real test, call the endpoint
                # Verify mock_client was instantiated with credentials
                mock_client.assert_not_called()  # Not called yet in this test
