"""
Tests for the authentication dependencies module.

Tests cover:
- Token extraction from requests (header and cookie)
- get_current_user dependency
- get_current_user_optional dependency
- require_professional dependency
- require_admin dependency
- require_borrower dependency
- WebSocket authentication
"""
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import timedelta
import uuid

from fastapi import HTTPException

from src.app.core.dependencies import (
    get_token_from_request,
    get_current_user,
    get_current_user_optional,
    require_professional,
    require_borrower,
    require_admin,
    get_current_user_ws,
)
from src.app.core.security import create_access_token, create_refresh_token
from src.app.models.user import User, UserType


class TestGetTokenFromRequest:
    """Tests for token extraction from requests."""

    def test_token_from_bearer_header(self):
        """Should extract token from Authorization Bearer header."""
        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = "test_token_from_header"

        token = get_token_from_request(mock_request, mock_credentials)
        assert token == "test_token_from_header"

    def test_token_from_cookie(self):
        """Should extract token from cookie when no bearer header."""
        mock_request = MagicMock()
        mock_request.cookies = {"access_token": "test_token_from_cookie"}
        mock_credentials = None

        token = get_token_from_request(mock_request, mock_credentials)
        assert token == "test_token_from_cookie"

    def test_bearer_header_takes_priority(self):
        """Bearer header should take priority over cookie."""
        mock_request = MagicMock()
        mock_request.cookies = {"access_token": "cookie_token"}
        mock_credentials = MagicMock()
        mock_credentials.credentials = "header_token"

        token = get_token_from_request(mock_request, mock_credentials)
        assert token == "header_token"

    def test_returns_none_when_no_token(self):
        """Should return None when no token found."""
        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = None

        token = get_token_from_request(mock_request, mock_credentials)
        assert token is None

    def test_empty_bearer_header(self):
        """Should fall back to cookie when bearer header is empty."""
        mock_request = MagicMock()
        mock_request.cookies = {"access_token": "cookie_token"}
        mock_credentials = MagicMock()
        mock_credentials.credentials = ""  # Empty string

        token = get_token_from_request(mock_request, mock_credentials)
        assert token == "cookie_token"


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, db_session, test_user):
        """Valid token should return the user."""
        token = create_access_token(str(test_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        user = await get_current_user(mock_request, mock_credentials, db_session)
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_missing_token_raises_401(self, db_session):
        """Missing token should raise 401 Unauthorized."""
        mock_request = MagicMock()
        mock_request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, None, db_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self, db_session, test_user):
        """Expired token should raise 401 Unauthorized."""
        # Create token that expires immediately
        token = create_access_token(str(test_user.id), expires_delta=timedelta(seconds=-1))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials, db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self, db_session):
        """Invalid/malformed token should raise 401 Unauthorized."""
        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token_format"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials, db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_raises_401(self, db_session, test_user):
        """Refresh token should not be accepted (type != 'access')."""
        token = create_refresh_token(str(test_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials, db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_raises_403(self, db_session, test_user):
        """Inactive user should raise 403 Forbidden."""
        # Make user inactive
        test_user.is_active = False
        await db_session.commit()

        token = create_access_token(str(test_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials, db_session)

        assert exc_info.value.status_code == 403
        assert "disabled" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_nonexistent_user_raises_401(self, db_session):
        """Token for nonexistent user should raise 401."""
        # Create token for non-existent user
        fake_user_id = str(uuid.uuid4())
        token = create_access_token(fake_user_id)

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials, db_session)

        assert exc_info.value.status_code == 401


class TestGetCurrentUserOptional:
    """Tests for get_current_user_optional dependency."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, db_session, test_user):
        """Valid token should return the user."""
        token = create_access_token(str(test_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        user = await get_current_user_optional(mock_request, mock_credentials, db_session)
        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_missing_token_returns_none(self, db_session):
        """Missing token should return None (not raise)."""
        mock_request = MagicMock()
        mock_request.cookies = {}

        user = await get_current_user_optional(mock_request, None, db_session)
        assert user is None

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self, db_session):
        """Invalid token should return None (not raise)."""
        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"

        user = await get_current_user_optional(mock_request, mock_credentials, db_session)
        assert user is None

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(self, db_session, test_user):
        """Expired token should return None."""
        token = create_access_token(str(test_user.id), expires_delta=timedelta(seconds=-1))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        user = await get_current_user_optional(mock_request, mock_credentials, db_session)
        assert user is None

    @pytest.mark.asyncio
    async def test_inactive_user_returns_none(self, db_session, test_user):
        """Inactive user should return None."""
        test_user.is_active = False
        await db_session.commit()

        token = create_access_token(str(test_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        user = await get_current_user_optional(mock_request, mock_credentials, db_session)
        assert user is None


class TestRequireProfessional:
    """Tests for require_professional dependency."""

    @pytest.mark.asyncio
    async def test_professional_user_passes(
        self, db_session, test_professional_user, test_professional
    ):
        """Professional user with profile should pass."""
        token = create_access_token(str(test_professional_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        user = await require_professional(mock_request, mock_credentials, db_session)
        assert user.id == test_professional_user.id
        assert user.professional_profile is not None

    @pytest.mark.asyncio
    async def test_non_professional_raises_403(self, db_session, test_user):
        """Non-professional user (borrower) should raise 403."""
        token = create_access_token(str(test_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await require_professional(mock_request, mock_credentials, db_session)

        assert exc_info.value.status_code == 403
        assert "Professional account required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_professional_without_profile_raises_404(
        self, db_session, test_professional_user
    ):
        """Professional user type but no profile should raise 404."""
        # Note: test_professional_user is created without a profile by default
        # Need to not use test_professional fixture to test this case
        token = create_access_token(str(test_professional_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await require_professional(mock_request, mock_credentials, db_session)

        assert exc_info.value.status_code == 404
        assert "Professional profile not found" in exc_info.value.detail


class TestRequireAdmin:
    """Tests for require_admin dependency."""

    @pytest.mark.asyncio
    async def test_admin_user_passes(self, test_admin_user):
        """Admin user should pass."""
        user = await require_admin(test_admin_user)
        assert user.id == test_admin_user.id
        assert user.is_admin is True

    @pytest.mark.asyncio
    async def test_non_admin_raises_403(self, test_user):
        """Non-admin user should raise 403."""
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(test_user)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_user_without_is_admin_attribute(self):
        """User object without is_admin attribute should raise 403."""
        mock_user = MagicMock()
        del mock_user.is_admin  # Remove attribute

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_user)

        assert exc_info.value.status_code == 403


class TestGetCurrentUserWS:
    """Tests for WebSocket authentication."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, db_session, test_user):
        """Valid token should return user for WebSocket."""
        token = create_access_token(str(test_user.id))

        user = await get_current_user_ws(token, db_session)
        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_empty_token_returns_none(self, db_session):
        """Empty token should return None."""
        user = await get_current_user_ws("", db_session)
        assert user is None

    @pytest.mark.asyncio
    async def test_none_token_returns_none(self, db_session):
        """None token should return None."""
        user = await get_current_user_ws(None, db_session)
        assert user is None

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self, db_session):
        """Invalid token should return None."""
        user = await get_current_user_ws("invalid_token", db_session)
        assert user is None

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(self, db_session, test_user):
        """Expired token should return None."""
        token = create_access_token(str(test_user.id), expires_delta=timedelta(seconds=-1))

        user = await get_current_user_ws(token, db_session)
        assert user is None

    @pytest.mark.asyncio
    async def test_refresh_token_returns_none(self, db_session, test_user):
        """Refresh token should return None (wrong type)."""
        token = create_refresh_token(str(test_user.id))

        user = await get_current_user_ws(token, db_session)
        assert user is None

    @pytest.mark.asyncio
    async def test_inactive_user_returns_none(self, db_session, test_user):
        """Inactive user should return None."""
        test_user.is_active = False
        await db_session.commit()

        token = create_access_token(str(test_user.id))

        user = await get_current_user_ws(token, db_session)
        assert user is None

    @pytest.mark.asyncio
    async def test_load_professional_profile_option(
        self, db_session, test_professional_user, test_professional
    ):
        """Should load professional profile when requested."""
        token = create_access_token(str(test_professional_user.id))

        user = await get_current_user_ws(
            token, db_session, load_professional_profile=True
        )
        assert user is not None
        assert user.professional_profile is not None
        assert user.professional_profile.id == test_professional.id


class TestRequireBorrower:
    """Tests for require_borrower dependency."""

    @pytest.mark.asyncio
    async def test_borrower_user_passes(self, db_session, test_user):
        """Borrower user should pass."""
        token = create_access_token(str(test_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        user = await require_borrower(mock_request, mock_credentials, db_session)
        assert user.id == test_user.id
        assert user.user_type == UserType.BORROWER

    @pytest.mark.asyncio
    async def test_professional_raises_403(
        self, db_session, test_professional_user
    ):
        """Professional user should raise 403."""
        token = create_access_token(str(test_professional_user.id))

        mock_request = MagicMock()
        mock_request.cookies = {}
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await require_borrower(mock_request, mock_credentials, db_session)

        assert exc_info.value.status_code == 403
        assert "Borrower account required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_missing_token_raises_401(self, db_session):
        """Missing token should raise 401."""
        mock_request = MagicMock()
        mock_request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            await require_borrower(mock_request, None, db_session)

        assert exc_info.value.status_code == 401
