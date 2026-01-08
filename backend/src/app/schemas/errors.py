"""
RFC 7807 Problem Details error response schemas.

Provides standardized error responses for the API with:
- Consistent error format across all endpoints
- Type URIs for error categorization
- Optional field-level validation errors
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ValidationErrorItem(BaseModel):
    """Individual field validation error."""

    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "email",
                "message": "Invalid email format",
                "code": "invalid_format",
            }
        }


class ErrorResponse(BaseModel):
    """
    RFC 7807 Problem Details error response.

    Provides a standardized error format for all API errors.
    """

    type: str = Field(
        default="about:blank",
        description="URI reference identifying the error type",
    )
    title: str = Field(
        ...,
        description="Short, human-readable summary of the problem",
    )
    status: int = Field(
        ...,
        description="HTTP status code",
    )
    detail: Optional[str] = Field(
        default=None,
        description="Human-readable explanation specific to this occurrence",
    )
    instance: Optional[str] = Field(
        default=None,
        description="URI reference identifying this specific occurrence",
    )
    errors: Optional[List[ValidationErrorItem]] = Field(
        default=None,
        description="Field-level validation errors (for 422 responses)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://facemortgage.com/errors/not-found",
                "title": "Resource Not Found",
                "status": 404,
                "detail": "Professional with ID 550e8400-e29b-41d4-a716-446655440000 not found",
                "instance": "/api/v1/professionals/550e8400-e29b-41d4-a716-446655440000",
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-level errors."""

    title: str = Field(default="Validation Error")
    status: int = Field(default=422)
    errors: List[ValidationErrorItem] = Field(
        ...,
        description="Field-level validation errors",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://facemortgage.com/errors/validation",
                "title": "Validation Error",
                "status": 422,
                "detail": "Request validation failed",
                "errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "invalid_format",
                    },
                    {
                        "field": "nmls_id",
                        "message": "NMLS ID must be 5-10 digits",
                        "code": "invalid_length",
                    },
                ],
            }
        }


class AuthenticationErrorResponse(ErrorResponse):
    """Authentication error response."""

    type: str = Field(default="https://facemortgage.com/errors/authentication")
    title: str = Field(default="Authentication Required")
    status: int = Field(default=401)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://facemortgage.com/errors/authentication",
                "title": "Authentication Required",
                "status": 401,
                "detail": "Missing or invalid authentication token",
            }
        }


class AuthorizationErrorResponse(ErrorResponse):
    """Authorization error response."""

    type: str = Field(default="https://facemortgage.com/errors/authorization")
    title: str = Field(default="Not Authorized")
    status: int = Field(default=403)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://facemortgage.com/errors/authorization",
                "title": "Not Authorized",
                "status": 403,
                "detail": "You do not have permission to access this resource",
            }
        }


class NotFoundErrorResponse(ErrorResponse):
    """Not found error response."""

    type: str = Field(default="https://facemortgage.com/errors/not-found")
    title: str = Field(default="Resource Not Found")
    status: int = Field(default=404)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://facemortgage.com/errors/not-found",
                "title": "Resource Not Found",
                "status": 404,
                "detail": "The requested resource was not found",
            }
        }


class RateLimitErrorResponse(ErrorResponse):
    """Rate limit exceeded error response."""

    type: str = Field(default="https://facemortgage.com/errors/rate-limit")
    title: str = Field(default="Rate Limit Exceeded")
    status: int = Field(default=429)
    retry_after: Optional[int] = Field(
        default=None,
        description="Seconds until the rate limit resets",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://facemortgage.com/errors/rate-limit",
                "title": "Rate Limit Exceeded",
                "status": 429,
                "detail": "Too many requests. Please try again later.",
                "retry_after": 60,
            }
        }


class ServerErrorResponse(ErrorResponse):
    """Internal server error response."""

    type: str = Field(default="https://facemortgage.com/errors/server-error")
    title: str = Field(default="Internal Server Error")
    status: int = Field(default=500)
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for debugging",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://facemortgage.com/errors/server-error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred. Please try again later.",
                "request_id": "req_abc123xyz",
            }
        }


class ConflictErrorResponse(ErrorResponse):
    """Conflict error response."""

    type: str = Field(default="https://facemortgage.com/errors/conflict")
    title: str = Field(default="Resource Conflict")
    status: int = Field(default=409)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://facemortgage.com/errors/conflict",
                "title": "Resource Conflict",
                "status": 409,
                "detail": "A resource with this identifier already exists",
            }
        }


class ServiceUnavailableErrorResponse(ErrorResponse):
    """Service unavailable error response."""

    type: str = Field(default="https://facemortgage.com/errors/service-unavailable")
    title: str = Field(default="Service Unavailable")
    status: int = Field(default=503)
    retry_after: Optional[int] = Field(
        default=None,
        description="Estimated seconds until service is available",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://facemortgage.com/errors/service-unavailable",
                "title": "Service Unavailable",
                "status": 503,
                "detail": "The service is temporarily unavailable. Please try again later.",
                "retry_after": 300,
            }
        }


# Common response definitions for use in route decorators
ERROR_RESPONSES: Dict[int, Dict[str, Any]] = {
    400: {
        "model": ErrorResponse,
        "description": "Bad Request - Invalid input data",
    },
    401: {
        "model": AuthenticationErrorResponse,
        "description": "Authentication Required",
    },
    403: {
        "model": AuthorizationErrorResponse,
        "description": "Not Authorized",
    },
    404: {
        "model": NotFoundErrorResponse,
        "description": "Resource Not Found",
    },
    409: {
        "model": ConflictErrorResponse,
        "description": "Resource Conflict",
    },
    422: {
        "model": ValidationErrorResponse,
        "description": "Validation Error",
    },
    429: {
        "model": RateLimitErrorResponse,
        "description": "Rate Limit Exceeded",
    },
    500: {
        "model": ServerErrorResponse,
        "description": "Internal Server Error",
    },
    503: {
        "model": ServiceUnavailableErrorResponse,
        "description": "Service Unavailable",
    },
}


def get_error_responses(*status_codes: int) -> Dict[int, Dict[str, Any]]:
    """
    Get error response definitions for specific status codes.

    Usage in route decorators:
        @router.get(
            "/resource/{id}",
            responses=get_error_responses(401, 403, 404),
        )
    """
    return {code: ERROR_RESPONSES[code] for code in status_codes if code in ERROR_RESPONSES}
