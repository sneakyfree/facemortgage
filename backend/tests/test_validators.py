"""
Tests for the validators module.

Tests cover:
- NMLS ID validation
- Phone number validation and normalization
- State code validation
- Email validation
- UUID validation
- XSS detection
- HTML sanitization
- Filename sanitization
- URL validation
- Input validation helper
"""
import pytest
import re

from src.app.core.validators import (
    validate_nmls_id,
    validate_phone,
    normalize_phone,
    validate_state_code,
    normalize_state_code,
    validate_email,
    validate_uuid,
    sanitize_html,
    contains_xss,
    sanitize_filename,
    validate_url,
    truncate_string,
    validate_input,
    ValidationError,
    NMLS_PATTERN,
    STATE_CODES,
)


class TestValidateNMLSId:
    """Tests for NMLS ID validation."""

    def test_valid_5_digit_nmls(self):
        """5-digit NMLS ID should be valid."""
        assert validate_nmls_id("12345") is True

    def test_valid_6_digit_nmls(self):
        """6-digit NMLS ID should be valid."""
        assert validate_nmls_id("123456") is True

    def test_valid_10_digit_nmls(self):
        """10-digit NMLS ID should be valid."""
        assert validate_nmls_id("1234567890") is True

    def test_invalid_4_digit_nmls(self):
        """4-digit NMLS ID should be invalid (too short)."""
        assert validate_nmls_id("1234") is False

    def test_invalid_11_digit_nmls(self):
        """11-digit NMLS ID should be invalid (too long)."""
        assert validate_nmls_id("12345678901") is False

    def test_invalid_nmls_with_letters(self):
        """NMLS ID with letters should be invalid."""
        assert validate_nmls_id("12345a") is False
        assert validate_nmls_id("abc123") is False

    def test_invalid_nmls_with_special_chars(self):
        """NMLS ID with special characters should be invalid."""
        assert validate_nmls_id("123-456") is False
        assert validate_nmls_id("123.456") is False
        assert validate_nmls_id("123 456") is False

    def test_empty_nmls(self):
        """Empty NMLS ID should be invalid."""
        assert validate_nmls_id("") is False
        assert validate_nmls_id(None) is False

    def test_nmls_with_whitespace(self):
        """NMLS ID with leading/trailing whitespace should work."""
        assert validate_nmls_id(" 123456 ") is True
        assert validate_nmls_id("  12345  ") is True


class TestValidatePhone:
    """Tests for phone number validation."""

    def test_valid_10_digit_phone(self):
        """10-digit phone should be valid."""
        assert validate_phone("1234567890") is True

    def test_valid_phone_with_country_code(self):
        """Phone with country code should be valid."""
        assert validate_phone("+11234567890") is True
        assert validate_phone("11234567890") is True

    def test_valid_formatted_phone(self):
        """Formatted phone should be valid (normalized internally)."""
        assert validate_phone("(123) 456-7890") is True
        assert validate_phone("123-456-7890") is True
        assert validate_phone("123.456.7890") is True

    def test_invalid_short_phone(self):
        """Phone with less than 10 digits should be invalid."""
        assert validate_phone("123456789") is False  # 9 digits

    def test_invalid_long_phone(self):
        """Phone with more than 15 digits should be invalid."""
        assert validate_phone("1234567890123456") is False  # 16 digits

    def test_none_phone_is_valid(self):
        """None phone is valid (optional field)."""
        assert validate_phone(None) is True

    def test_phone_with_letters(self):
        """Phone with letters should be invalid."""
        assert validate_phone("123-ABC-4567") is False


class TestNormalizePhone:
    """Tests for phone number normalization."""

    def test_normalize_formatted_phone(self):
        """Should remove formatting characters."""
        assert normalize_phone("(123) 456-7890") == "1234567890"
        assert normalize_phone("123-456-7890") == "1234567890"
        assert normalize_phone("123.456.7890") == "1234567890"

    def test_normalize_phone_with_country_code(self):
        """Should preserve country code."""
        assert normalize_phone("+11234567890") == "+11234567890"
        assert normalize_phone("+1 (123) 456-7890") == "+11234567890"

    def test_normalize_phone_removes_plus_in_middle(self):
        """Should only keep + at the start."""
        assert normalize_phone("123+456") == "123456"

    def test_normalize_empty_phone(self):
        """Empty phone should return None."""
        assert normalize_phone("") is None
        assert normalize_phone(None) is None

    def test_normalize_all_formatting(self):
        """Should return None if only formatting chars."""
        assert normalize_phone("() -") is None


class TestValidateStateCode:
    """Tests for state code validation."""

    def test_valid_state_codes(self):
        """Valid US state codes should pass."""
        valid_states = ["CA", "NY", "TX", "FL", "IL"]
        for state in valid_states:
            assert validate_state_code(state) is True

    def test_valid_territory_codes(self):
        """Valid US territory codes should pass."""
        territories = ["DC", "PR", "VI", "GU"]
        for territory in territories:
            assert validate_state_code(territory) is True

    def test_lowercase_state_code(self):
        """Lowercase state codes should pass."""
        assert validate_state_code("ca") is True
        assert validate_state_code("ny") is True

    def test_invalid_state_code(self):
        """Invalid state codes should fail."""
        assert validate_state_code("XX") is False
        assert validate_state_code("ZZ") is False
        assert validate_state_code("USA") is False

    def test_none_state_is_valid(self):
        """None state is valid (optional field)."""
        assert validate_state_code(None) is True

    def test_state_with_whitespace(self):
        """State code with whitespace should work."""
        assert validate_state_code(" CA ") is True


class TestNormalizeStateCode:
    """Tests for state code normalization."""

    def test_normalize_lowercase(self):
        """Should convert to uppercase."""
        assert normalize_state_code("ca") == "CA"
        assert normalize_state_code("ny") == "NY"

    def test_normalize_with_whitespace(self):
        """Should strip whitespace."""
        assert normalize_state_code(" CA ") == "CA"

    def test_normalize_invalid_returns_none(self):
        """Invalid state should return None."""
        assert normalize_state_code("XX") is None
        assert normalize_state_code("ZZ") is None

    def test_normalize_empty_returns_none(self):
        """Empty string should return None."""
        assert normalize_state_code("") is None
        assert normalize_state_code(None) is None


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_emails(self):
        """Valid email formats should pass."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.com",
            "user+tag@domain.com",
            "user@subdomain.domain.com",
            "test123@domain.co",
        ]
        for email in valid_emails:
            assert validate_email(email) is True, f"{email} should be valid"

    def test_invalid_emails(self):
        """Invalid email formats should fail."""
        invalid_emails = [
            "not_an_email",
            "missing@",
            "@domain.com",
            "no.at.sign.com",
            "spaces in@email.com",
        ]
        for email in invalid_emails:
            assert validate_email(email) is False, f"{email} should be invalid"

    def test_empty_email(self):
        """Empty email should be invalid."""
        assert validate_email("") is False
        assert validate_email(None) is False


class TestValidateUUID:
    """Tests for UUID validation."""

    def test_valid_uuid(self):
        """Valid UUID formats should pass."""
        import uuid
        valid_uuids = [
            str(uuid.uuid4()),
            "550e8400-e29b-41d4-a716-446655440000",
            "550E8400-E29B-41D4-A716-446655440000",  # Uppercase
        ]
        for u in valid_uuids:
            assert validate_uuid(u) is True, f"{u} should be valid"

    def test_invalid_uuid(self):
        """Invalid UUID formats should fail."""
        invalid_uuids = [
            "not-a-uuid",
            # Note: Python's uuid.UUID() accepts UUIDs without hyphens
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-4466554400001",  # Too long
            "",
            "gggggggg-gggg-gggg-gggg-gggggggggggg",  # Invalid hex characters
        ]
        for u in invalid_uuids:
            assert validate_uuid(u) is False, f"{u} should be invalid"

    def test_uuid_without_hyphens_is_valid(self):
        """UUID without hyphens is valid (Python's uuid.UUID accepts it)."""
        # This is expected behavior - uuid.UUID() parses 32 hex digits
        assert validate_uuid("550e8400e29b41d4a716446655440000") is True

    def test_none_uuid(self):
        """None should be invalid."""
        assert validate_uuid(None) is False


class TestContainsXSS:
    """Tests for XSS pattern detection."""

    def test_detects_script_tag(self):
        """Should detect script tags."""
        assert contains_xss("<script>alert('xss')</script>") is True
        assert contains_xss("<SCRIPT>alert('xss')</SCRIPT>") is True
        assert contains_xss("<script src='evil.js'>") is True

    def test_detects_javascript_protocol(self):
        """Should detect javascript: protocol."""
        assert contains_xss("javascript:alert(1)") is True
        assert contains_xss("JAVASCRIPT:alert(1)") is True

    def test_detects_event_handlers(self):
        """Should detect inline event handlers."""
        assert contains_xss("<img onerror=alert(1)>") is True
        assert contains_xss("<div onclick=malicious()>") is True
        assert contains_xss("onmouseover=evil()") is True

    def test_detects_data_protocol(self):
        """Should detect data: protocol."""
        assert contains_xss("data:text/html,<script>") is True

    def test_clean_text_passes(self):
        """Clean text should not trigger XSS detection."""
        assert contains_xss("Hello, world!") is False
        assert contains_xss("This is normal <b>text</b>") is False
        assert contains_xss("Price: $50.00") is False
        assert contains_xss("Email: test@example.com") is False

    def test_empty_text(self):
        """Empty text should not trigger XSS detection."""
        assert contains_xss("") is False
        assert contains_xss(None) is False


class TestSanitizeHtml:
    """Tests for HTML sanitization."""

    def test_escapes_html_entities(self):
        """Should escape HTML special characters."""
        assert sanitize_html("<script>") == "&lt;script&gt;"
        assert sanitize_html("&") == "&amp;"
        assert sanitize_html('"quotes"') == "&quot;quotes&quot;"
        assert sanitize_html("'single'") == "&#x27;single&#x27;"

    def test_preserves_normal_text(self):
        """Should preserve normal text."""
        assert sanitize_html("Hello, World!") == "Hello, World!"
        assert sanitize_html("123 Main St") == "123 Main St"

    def test_empty_input(self):
        """Empty input should return empty string."""
        assert sanitize_html("") == ""
        assert sanitize_html(None) == ""


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_removes_path_separators(self):
        """Should remove path separators."""
        assert sanitize_filename("../etc/passwd") == "etcpasswd"
        assert sanitize_filename("..\\windows\\system32") == "windowssystem32"

    def test_removes_leading_dots(self):
        """Should remove leading dots (hidden files)."""
        assert sanitize_filename(".hidden") == "hidden"
        assert sanitize_filename("..double") == "double"

    def test_removes_null_bytes(self):
        """Should remove null bytes."""
        assert sanitize_filename("file\x00.txt") == "file.txt"

    def test_valid_filename_passes(self):
        """Valid filenames should pass through."""
        assert sanitize_filename("document.pdf") == "document.pdf"
        assert sanitize_filename("image-file_v2.png") == "image-file_v2.png"

    def test_invalid_chars_returns_none(self):
        """Filenames with only invalid chars should return None."""
        assert sanitize_filename("...") is None  # Only dots
        assert sanitize_filename("") is None

    def test_special_chars_returns_none(self):
        """Filenames with special chars return None."""
        # Only alphanumeric, dash, underscore, dot allowed
        assert sanitize_filename("file name.txt") is None  # Space
        assert sanitize_filename("file<name>.txt") is None


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_urls(self):
        """Valid URLs should pass."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "https://www.example.com/path",
            "https://example.com/path?query=1",
        ]
        for url in valid_urls:
            assert validate_url(url) is True, f"{url} should be valid"

    def test_invalid_urls(self):
        """Invalid URLs should fail."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Wrong scheme
            "//example.com",  # No scheme
            "",
        ]
        for url in invalid_urls:
            assert validate_url(url) is False, f"{url} should be invalid"

    def test_none_url(self):
        """None URL should be invalid."""
        assert validate_url(None) is False


class TestTruncateString:
    """Tests for string truncation."""

    def test_truncate_long_string(self):
        """Long string should be truncated with suffix."""
        result = truncate_string("Hello, World!", 8)
        assert result == "Hello..."
        assert len(result) == 8

    def test_short_string_unchanged(self):
        """Short string should not be truncated."""
        result = truncate_string("Hello", 10)
        assert result == "Hello"

    def test_custom_suffix(self):
        """Should use custom suffix."""
        result = truncate_string("Hello, World!", 9, suffix="…")
        assert result == "Hello, W…"

    def test_empty_input(self):
        """Empty input should return empty string."""
        assert truncate_string("", 10) == ""
        assert truncate_string(None, 10) == ""


class TestValidateInput:
    """Tests for comprehensive input validation."""

    def test_required_field(self):
        """Required field should raise error if empty."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input(None, "name", required=True)
        assert exc_info.value.field == "name"
        assert "required" in exc_info.value.message.lower()

    def test_min_length(self):
        """Should enforce minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input("ab", "name", min_length=3)
        assert "at least 3" in exc_info.value.message

    def test_max_length(self):
        """Should enforce maximum length."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input("abcdef", "name", max_length=5)
        assert "at most 5" in exc_info.value.message

    def test_pattern_validation(self):
        """Should validate against pattern."""
        pattern = re.compile(r'^\d+$')
        with pytest.raises(ValidationError) as exc_info:
            validate_input("abc", "number", pattern=pattern)
        assert "Invalid format" in exc_info.value.message

    def test_allowed_values(self):
        """Should validate against allowed values."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input("invalid", "status", allowed_values={"active", "inactive"})
        assert "Must be one of" in exc_info.value.message

    def test_xss_detection(self):
        """Should detect XSS patterns."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input("<script>alert(1)</script>", "input")
        assert "dangerous content" in exc_info.value.message.lower()

    def test_sanitization(self):
        """Should sanitize output when requested."""
        result = validate_input("<b>bold</b>", "text", sanitize=True)
        assert result == "&lt;b&gt;bold&lt;/b&gt;"

    def test_no_sanitization(self):
        """Should preserve content when sanitize=False."""
        # Note: XSS check happens before sanitization decision
        result = validate_input("test & value", "text", sanitize=False)
        assert result == "test & value"

    def test_optional_field_none(self):
        """Optional field with None should return None."""
        result = validate_input(None, "name", required=False)
        assert result is None

    def test_optional_field_empty(self):
        """Optional field with empty string should return None."""
        result = validate_input("", "name", required=False)
        assert result is None

    def test_whitespace_stripped(self):
        """Should strip leading/trailing whitespace."""
        result = validate_input("  hello  ", "text")
        assert result == "hello"


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_error_has_field_and_message(self):
        """ValidationError should have field and message."""
        error = ValidationError("email", "Invalid format")
        assert error.field == "email"
        assert error.message == "Invalid format"

    def test_error_string_representation(self):
        """ValidationError str should include field and message."""
        error = ValidationError("email", "Invalid format")
        assert str(error) == "email: Invalid format"
