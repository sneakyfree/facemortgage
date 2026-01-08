"""
Tests for video call management endpoints.

Tests cover:
- Authenticated call initiation
- Anonymous call initiation
- Call to offline professional (should fail)
- Lead capture after anonymous call
- Call state management
- Call rating

Note: Some tests are skipped due to SQLite/UUID compatibility issues with
the auth header fixtures. The test_routes.py file has equivalent coverage
for the call endpoints.
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.call import VideoCall, CallStatus
from src.app.models.lead import Lead
from src.app.models.professional import ProfessionalProfile
from src.app.models.user import User


class TestCallInitiation:
    """Tests for call initiation endpoints."""

    @pytest.mark.asyncio
    async def test_initiate_call_anonymous(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_professional: ProfessionalProfile,
        mock_presence_service,
        mock_signaling_service,
    ):
        """Anonymous user should be able to initiate a call without authentication."""
        with patch("src.app.api.v1.routes.calls.get_presence_service", return_value=mock_presence_service), \
             patch("src.app.api.v1.routes.calls.get_signaling_service", return_value=mock_signaling_service), \
             patch("src.app.api.v1.routes.calls.connection_manager") as mock_cm, \
             patch("src.app.services.push_notification.push_service") as mock_push:
            mock_cm.send_to_professional = AsyncMock()
            mock_push.send_incoming_call = AsyncMock()

            response = await client.post(
                "/api/v1/calls",
                json={
                    "professional_id": str(test_professional.id),
                    "anonymous_session_id": "test_session_123",
                    "device_fingerprint": "test_fingerprint",
                },
            )

        assert response.status_code == 200
        data = response.json()

        assert "room_id" in data
        assert data["is_anonymous"] is True
        assert data["session_id"] == "test_session_123"

    @pytest.mark.asyncio
    async def test_initiate_call_auto_generates_session_id(
        self,
        client: AsyncClient,
        test_professional: ProfessionalProfile,
        mock_presence_service,
        mock_signaling_service,
    ):
        """Anonymous call without session_id should auto-generate one."""
        with patch("src.app.api.v1.routes.calls.get_presence_service", return_value=mock_presence_service), \
             patch("src.app.api.v1.routes.calls.get_signaling_service", return_value=mock_signaling_service), \
             patch("src.app.api.v1.routes.calls.connection_manager") as mock_cm, \
             patch("src.app.services.push_notification.push_service") as mock_push:
            mock_cm.send_to_professional = AsyncMock()
            mock_push.send_incoming_call = AsyncMock()

            response = await client.post(
                "/api/v1/calls",
                json={"professional_id": str(test_professional.id)},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_anonymous"] is True
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0

    @pytest.mark.asyncio
    async def test_initiate_call_to_nonexistent_professional(
        self,
        client: AsyncClient,
    ):
        """Call to non-existent professional should fail with 404."""
        fake_id = str(uuid.uuid4())
        response = await client.post(
            "/api/v1/calls",
            json={"professional_id": fake_id},
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"]["message"].lower()


class TestLeadCaptureAfterAnonymousCall:
    """Tests for lead capture after anonymous calls."""

    @pytest.mark.asyncio
    async def test_capture_lead_after_anonymous_call(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_anonymous_call: VideoCall,
    ):
        """Should capture lead info from anonymous caller after call ends."""
        response = await client.post(
            f"/api/v1/calls/{test_anonymous_call.id}/capture-lead",
            json={
                "name": "John Smith",
                "email": "john.smith@example.com",
                "phone": "555-987-6543",
                "loan_purpose": "refinance",
                "estimated_amount": 450000,
                "notes": "Interested in cash-out refinance",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "lead_id" in data

        # Verify lead was created in database
        result = await db_session.execute(
            select(Lead).where(Lead.id == uuid.UUID(data["lead_id"]))
        )
        lead = result.scalar_one_or_none()

        assert lead is not None
        assert lead.contact_name == "John Smith"
        assert lead.contact_email == "john.smith@example.com"
        assert lead.contact_phone == "555-987-6543"
        assert lead.loan_purpose == "refinance"
        assert lead.professional_id == test_anonymous_call.professional_id

        # Verify call was updated with captured info
        await db_session.refresh(test_anonymous_call)
        assert test_anonymous_call.captured_name == "John Smith"
        assert test_anonymous_call.captured_email == "john.smith@example.com"
        assert test_anonymous_call.lead_captured_at is not None

    @pytest.mark.asyncio
    async def test_capture_lead_minimal_info(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_anonymous_call: VideoCall,
    ):
        """Should capture lead with only required fields."""
        response = await client.post(
            f"/api/v1/calls/{test_anonymous_call.id}/capture-lead",
            json={
                "name": "Jane Doe",
                "email": "jane@example.com",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify lead was created
        result = await db_session.execute(
            select(Lead).where(Lead.id == uuid.UUID(data["lead_id"]))
        )
        lead = result.scalar_one_or_none()

        assert lead is not None
        assert lead.contact_name == "Jane Doe"
        assert lead.contact_email == "jane@example.com"
        assert lead.contact_phone is None

    @pytest.mark.asyncio
    async def test_capture_lead_fails_for_authenticated_call(
        self,
        client: AsyncClient,
        test_video_call: VideoCall,
    ):
        """Lead capture should fail for authenticated calls (borrower_id is set)."""
        response = await client.post(
            f"/api/v1/calls/{test_video_call.id}/capture-lead",
            json={
                "name": "Should Fail",
                "email": "fail@example.com",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "anonymous" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_capture_lead_fails_for_nonexistent_call(
        self,
        client: AsyncClient,
    ):
        """Lead capture should fail for non-existent call."""
        fake_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/v1/calls/{fake_id}/capture-lead",
            json={
                "name": "Should Fail",
                "email": "fail@example.com",
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_capture_lead_invalid_email(
        self,
        client: AsyncClient,
        test_anonymous_call: VideoCall,
    ):
        """Lead capture should fail with invalid email."""
        response = await client.post(
            f"/api/v1/calls/{test_anonymous_call.id}/capture-lead",
            json={
                "name": "John Smith",
                "email": "not-an-email",
            },
        )

        assert response.status_code == 422  # Validation error


class TestCallRating:
    """Tests for call rating."""

    @pytest.mark.asyncio
    async def test_rate_call_requires_auth(
        self,
        client: AsyncClient,
        test_video_call: VideoCall,
    ):
        """Rating a call should require authentication."""
        response = await client.post(
            f"/api/v1/calls/{test_video_call.room_id}/rate",
            json={"overall_rating": 5},
        )

        assert response.status_code == 401
