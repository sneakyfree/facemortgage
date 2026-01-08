"""
Input validation utilities for FaceMortgage.

Provides consistent validation patterns for common inputs:
- NMLS IDs
- Phone numbers
- State codes
- Email addresses
- UUID formats

Security features:
- HTML sanitization
- XSS prevention
- Input normalization
"""
import re
import html
from typing import Optional, Set
from uuid import UUID


# NMLS ID pattern: 5-10 digits
NMLS_PATTERN = re.compile(r'^\d{5,10}$')

# Phone pattern: 10-14 digits, optional country code
PHONE_PATTERN = re.compile(r'^\+?1?\d{10,14}$')

# Email pattern (simplified, use Pydantic EmailStr for strict validation)
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# UUID pattern
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# Valid US state/territory codes
STATE_CODES: Set[str] = {
    # 50 states
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    # Territories
    "DC", "PR", "VI", "GU", "AS", "MP",
}

# Dangerous patterns for XSS prevention
XSS_PATTERNS = [
    re.compile(r'<script[^>]*>', re.IGNORECASE),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),  # onclick, onerror, etc.
    re.compile(r'data:', re.IGNORECASE),
]


def validate_nmls_id(nmls_id: Optional[str]) -> bool:
    """
    Validate NMLS ID format.

    Args:
        nmls_id: The NMLS ID to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_nmls_id("123456")
        True
        >>> validate_nmls_id("12345")
        True
        >>> validate_nmls_id("1234")  # Too short
        False
        >>> validate_nmls_id("12345678901")  # Too long
        False
    """
    if not nmls_id:
        return False
    return bool(NMLS_PATTERN.match(nmls_id.strip()))


def validate_phone(phone: Optional[str]) -> bool:
    """
    Validate phone number format.

    Accepts formats like:
    - 1234567890
    - +11234567890
    - (123) 456-7890 (after normalization)

    Args:
        phone: The phone number to validate

    Returns:
        True if valid, False otherwise
    """
    if phone is None:
        return True  # Optional field

    # Remove formatting characters
    cleaned = normalize_phone(phone)
    if not cleaned:
        return False

    return bool(PHONE_PATTERN.match(cleaned))


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalize phone number to digits only.

    Args:
        phone: The phone number to normalize

    Returns:
        Normalized phone number (digits only, with optional +)
    """
    if not phone:
        return None

    # Keep only digits and leading +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Ensure + is only at the start
    if '+' in cleaned:
        if cleaned.startswith('+'):
            cleaned = '+' + cleaned[1:].replace('+', '')
        else:
            cleaned = cleaned.replace('+', '')

    return cleaned if cleaned else None


def validate_state_code(state: Optional[str]) -> bool:
    """
    Validate US state code.

    Args:
        state: The state code to validate (2 letters)

    Returns:
        True if valid, False otherwise
    """
    if state is None:
        return True  # Optional field

    return state.strip().upper() in STATE_CODES


def normalize_state_code(state: Optional[str]) -> Optional[str]:
    """
    Normalize state code to uppercase.

    Args:
        state: The state code to normalize

    Returns:
        Uppercase state code or None
    """
    if not state:
        return None

    normalized = state.strip().upper()
    return normalized if normalized in STATE_CODES else None


def validate_email(email: Optional[str]) -> bool:
    """
    Basic email format validation.

    For strict validation, use Pydantic's EmailStr type.

    Args:
        email: The email to validate

    Returns:
        True if valid format, False otherwise
    """
    if not email:
        return False

    return bool(EMAIL_PATTERN.match(email.strip()))


def validate_uuid(value: Optional[str]) -> bool:
    """
    Validate UUID format.

    Args:
        value: The string to validate as UUID

    Returns:
        True if valid UUID format, False otherwise
    """
    if not value:
        return False

    try:
        UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_html(text: Optional[str]) -> str:
    """
    Sanitize text by escaping HTML entities.

    Prevents XSS attacks by escaping special characters.

    Args:
        text: The text to sanitize

    Returns:
        HTML-escaped text
    """
    if not text:
        return ""

    return html.escape(text)


def contains_xss(text: Optional[str]) -> bool:
    """
    Check if text contains potential XSS patterns.

    Args:
        text: The text to check

    Returns:
        True if XSS patterns detected, False otherwise
    """
    if not text:
        return False

    for pattern in XSS_PATTERNS:
        if pattern.search(text):
            return True

    return False


def sanitize_filename(filename: Optional[str]) -> Optional[str]:
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename or None if invalid
    """
    if not filename:
        return None

    # Remove path separators and null bytes
    sanitized = filename.replace('/', '').replace('\\', '').replace('\x00', '')

    # Remove leading dots (hidden files, parent directory)
    sanitized = sanitized.lstrip('.')

    # Only allow alphanumeric, dash, underscore, dot
    if not re.match(r'^[\w\-\.]+$', sanitized):
        return None

    return sanitized if sanitized else None


def validate_url(url: Optional[str]) -> bool:
    """
    Basic URL validation.

    Args:
        url: The URL to validate

    Returns:
        True if valid URL format, False otherwise
    """
    if not url:
        return False

    # Simple URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'[a-zA-Z0-9]+'  # domain
        r'(\.[a-zA-Z0-9]+)*'  # additional domain parts
        r'(/.*)?$'  # optional path
    )

    return bool(url_pattern.match(url))


def truncate_string(text: Optional[str], max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: The text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


class ValidationError(Exception):
    """Custom validation error with field information."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_input(
    value: Optional[str],
    field_name: str,
    required: bool = False,
    min_length: int = 0,
    max_length: int = 0,
    pattern: Optional[re.Pattern] = None,
    allowed_values: Optional[Set[str]] = None,
    sanitize: bool = True,
) -> Optional[str]:
    """
    Comprehensive input validation.

    Args:
        value: The value to validate
        field_name: Name of the field (for error messages)
        required: Whether the field is required
        min_length: Minimum string length
        max_length: Maximum string length (0 = no limit)
        pattern: Regex pattern to match
        allowed_values: Set of allowed values
        sanitize: Whether to sanitize the output

    Returns:
        Validated and optionally sanitized value

    Raises:
        ValidationError: If validation fails
    """
    # Handle None/empty
    if value is None or value.strip() == "":
        if required:
            raise ValidationError(field_name, "This field is required")
        return None

    value = value.strip()

    # Length checks
    if min_length and len(value) < min_length:
        raise ValidationError(
            field_name, f"Must be at least {min_length} characters"
        )

    if max_length and len(value) > max_length:
        raise ValidationError(
            field_name, f"Must be at most {max_length} characters"
        )

    # Pattern check
    if pattern and not pattern.match(value):
        raise ValidationError(field_name, "Invalid format")

    # Allowed values check
    if allowed_values and value not in allowed_values:
        raise ValidationError(
            field_name, f"Must be one of: {', '.join(sorted(allowed_values))}"
        )

    # XSS check
    if contains_xss(value):
        raise ValidationError(field_name, "Contains potentially dangerous content")

    # Sanitize if requested
    if sanitize:
        value = sanitize_html(value)

    return value
