"""
Tests for the security module (JWT tokens, password hashing).

Tests cover:
- Password verification and hashing
- Access token creation and validation
- Refresh token creation and validation
- Token decoding and expiration
"""
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock
import time

from src.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    TokenPayload,
)


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_verify_password_valid(self):
        """Correct password should return True."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_invalid(self):
        """Wrong password should return False."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_get_password_hash_unique(self):
        """Each hash should be unique due to bcrypt salt."""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # Hashes should be different (different salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_get_password_hash_empty_password(self):
        """Empty password should still hash correctly."""
        password = ""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_get_password_hash_long_password(self):
        """Long passwords should hash correctly."""
        password = "a" * 200  # 200 character password
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_special_characters(self):
        """Passwords with special characters should work."""
        password = "Test!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_unicode(self):
        """Passwords with unicode characters should work."""
        password = "пароль密码🔐"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestAccessToken:
    """Tests for access token creation and validation."""

    def test_create_access_token_payload(self):
        """Access token should contain correct subject and type."""
        subject = "test-user-id-123"
        token = create_access_token(subject)
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == subject
        assert payload.type == "access"

    def test_create_access_token_default_expiration(self):
        """Access token should use default expiration from settings."""
        subject = "test-user-id"
        token = create_access_token(subject)
        payload = decode_token(token)

        assert payload is not None
        assert payload.exp is not None
        # Token should expire in the future
        from datetime import datetime, timezone
        assert payload.exp > datetime.now(timezone.utc)

    def test_create_access_token_custom_expiration(self):
        """Access token should accept custom expiration delta."""
        subject = "test-user-id"
        expires_delta = timedelta(hours=2)
        token = create_access_token(subject, expires_delta=expires_delta)
        payload = decode_token(token)

        assert payload is not None
        from datetime import datetime, timezone
        # Check token expires approximately 2 hours from now
        expected_exp = datetime.now(timezone.utc) + expires_delta
        # Allow 5 second tolerance
        diff = abs((payload.exp - expected_exp).total_seconds())
        assert diff < 5

    def test_create_access_token_uuid_subject(self):
        """Access token should handle UUID subjects."""
        import uuid
        subject = str(uuid.uuid4())
        token = create_access_token(subject)
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == subject


class TestRefreshToken:
    """Tests for refresh token creation and validation."""

    def test_create_refresh_token_type(self):
        """Refresh token should have type='refresh'."""
        subject = "test-user-id"
        token = create_refresh_token(subject)
        payload = decode_token(token)

        assert payload is not None
        assert payload.type == "refresh"

    def test_create_refresh_token_payload(self):
        """Refresh token should contain correct subject."""
        subject = "test-user-id-456"
        token = create_refresh_token(subject)
        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == subject

    def test_refresh_token_longer_expiration_than_access(self):
        """Refresh token should expire later than access token."""
        subject = "test-user-id"
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        assert access_payload is not None
        assert refresh_payload is not None
        assert refresh_payload.exp > access_payload.exp


class TestTokenDecoding:
    """Tests for token decoding."""

    def test_decode_token_valid(self):
        """Valid token should return TokenPayload."""
        subject = "test-user-id"
        token = create_access_token(subject)
        payload = decode_token(token)

        assert payload is not None
        assert isinstance(payload, TokenPayload)
        assert payload.sub == subject
        assert payload.type == "access"

    def test_decode_token_expired(self):
        """Expired token should return None."""
        subject = "test-user-id"
        # Create token that expires immediately
        token = create_access_token(subject, expires_delta=timedelta(seconds=-1))
        payload = decode_token(token)

        assert payload is None

    def test_decode_token_invalid(self):
        """Malformed token should return None."""
        invalid_tokens = [
            "not-a-valid-token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            "",
            "...",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.wrong_signature",
        ]

        for token in invalid_tokens:
            payload = decode_token(token)
            assert payload is None, f"Expected None for invalid token: {token}"

    def test_decode_token_wrong_secret(self):
        """Token signed with different secret should return None."""
        from jose import jwt
        from src.app.config import settings

        # Create token with different secret
        to_encode = {
            "sub": "test-user",
            "exp": 9999999999,  # Far future
            "type": "access",
        }
        token = jwt.encode(to_encode, "wrong-secret-key", algorithm=settings.algorithm)

        payload = decode_token(token)
        assert payload is None

    def test_decode_token_missing_fields(self):
        """Token missing required fields should raise validation error."""
        from jose import jwt
        from src.app.config import settings

        # Token missing 'type' field
        to_encode = {
            "sub": "test-user",
            "exp": 9999999999,
        }
        token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

        # Should raise pydantic validation error for missing 'type' field
        with pytest.raises(Exception):  # ValidationError
            decode_token(token)


class TestTokenSecurity:
    """Security-related token tests."""

    def test_tokens_are_different_for_same_user(self):
        """Multiple tokens for same user created at different times should differ."""
        import time
        subject = "same-user"
        token1 = create_access_token(subject)
        time.sleep(1.1)  # Wait for different exp timestamp
        token2 = create_access_token(subject)

        # Tokens should differ due to different exp times
        assert token1 != token2

    def test_access_and_refresh_tokens_differ(self):
        """Access and refresh tokens for same user should differ."""
        subject = "test-user"
        access = create_access_token(subject)
        refresh = create_refresh_token(subject)

        assert access != refresh

    def test_token_type_cannot_be_forged(self):
        """Token type should be embedded and verified."""
        # Create access token
        access_token = create_access_token("user")
        access_payload = decode_token(access_token)

        # Create refresh token
        refresh_token = create_refresh_token("user")
        refresh_payload = decode_token(refresh_token)

        # Types should be correct and different
        assert access_payload.type == "access"
        assert refresh_payload.type == "refresh"
