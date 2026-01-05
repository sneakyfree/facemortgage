"""
Authentication module - re-exports from dependencies and security modules.

This module provides backward-compatible imports for authentication-related
functions that are used throughout the application.
"""
from src.app.core.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_current_user_ws,
    require_professional,
    require_borrower,
    require_admin,
    CurrentUser,
    CurrentUserOptional,
    CurrentProfessional,
    CurrentBorrower,
    CurrentAdmin,
)

from src.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    get_password_hash,
    TokenPayload,
)

__all__ = [
    # Dependencies
    "get_current_user",
    "get_current_user_optional",
    "get_current_user_ws",
    "require_professional",
    "require_borrower",
    "require_admin",
    # Type aliases
    "CurrentUser",
    "CurrentUserOptional",
    "CurrentProfessional",
    "CurrentBorrower",
    "CurrentAdmin",
    # Security functions
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_password",
    "get_password_hash",
    "TokenPayload",
]
