from datetime import datetime, timedelta
import uuid
from fastapi import APIRouter, HTTPException, status, Request, Response
from pydantic import BaseModel
from sqlalchemy import select

from src.app.config import settings

# Account lockout settings
LOCKOUT_THRESHOLD = 5  # Number of failed attempts before lockout
LOCKOUT_DURATION = timedelta(minutes=15)  # Duration of account lockout
from src.app.core.dependencies import DbSession, CurrentUser
from src.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.user import User, UserType
from src.app.models.professional import ProfessionalProfile
from src.app.models.borrower import BorrowerProfile
from src.app.schemas.user import (
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenPair,
    RefreshTokenRequest,
)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set httpOnly cookies for authentication tokens."""
    # Access token cookie (30 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
        domain=settings.cookie_domain,
    )
    # Refresh token cookie (7 days)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",  # Only sent to auth endpoints
        domain=settings.cookie_domain,
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies on logout."""
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.cookie_domain,
    )
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
        domain=settings.cookie_domain,
    )

router = APIRouter()


# Password validation helper
def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets minimum security requirements."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, ""


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["auth_register"])
async def register(request: Request, user_in: UserCreate, db: DbSession):
    """
    Register a new user account.

    Creates a user with the specified type (loan_officer, realtor, title_rep,
    attorney, or borrower) and automatically creates the corresponding profile.

    Password requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character

    Returns the created user (without password).
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_in.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        user_type=user_in.user_type,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone=user_in.phone,
    )
    db.add(user)
    await db.flush()

    # Create corresponding profile
    if user.is_professional:
        profile = ProfessionalProfile(user_id=user.id)
        db.add(profile)
    else:
        profile = BorrowerProfile(user_id=user.id)
        db.add(profile)

    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=TokenPair)
@limiter.limit(RATE_LIMITS["auth_login"])
async def login(request: Request, response: Response, login_data: LoginRequest, db: DbSession):
    """
    Authenticate a user and return access tokens.

    Sets httpOnly cookies containing access_token and refresh_token for
    secure browser-based authentication. Also returns tokens in response
    body for API clients.

    Account lockout: After 5 failed attempts, account is locked for 15 minutes.

    Returns access_token (30 min) and refresh_token (7 days).
    """
    # Database lookup only - no mock users in any environment
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    # Check if account is locked
    if user and user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed login attempts. Please try again later.",
        )

    # Verify credentials
    if not user or not verify_password(login_data.password, user.password_hash):
        # Track failed login attempt if user exists
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = datetime.utcnow() + LOCKOUT_DURATION
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Reset failed attempts and lockout on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    await db.commit()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # Set httpOnly cookies for secure token storage
    set_auth_cookies(response, access_token, refresh_token)

    # Also return tokens in body for backwards compatibility with existing clients
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: DbSession,
    refresh_data: RefreshTokenRequest = None,
):
    # Try to get refresh token from cookie first, then from body
    token = request.cookies.get("refresh_token")
    if not token and refresh_data:
        token = refresh_data.refresh_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    payload = decode_token(token)

    if payload is None or payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))

    # Set new cookies
    set_auth_cookies(response, new_access_token, new_refresh_token)

    return TokenPair(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get the current authenticated user's information.

    Returns the full user profile including account status and timestamps.
    Requires valid authentication via access_token cookie or Authorization header.
    """
    return current_user


class LogoutResponse(BaseModel):
    """Response schema for logout endpoint."""
    message: str


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response):
    """
    Log out the current user.

    Clears authentication cookies (access_token and refresh_token).
    After logout, the user must log in again to access protected resources.
    """
    # Clear auth cookies
    clear_auth_cookies(response)
    return LogoutResponse(message="Successfully logged out")


class ResendVerificationResponse(BaseModel):
    """Response for resend verification endpoint."""
    message: str
    success: bool


@router.post("/resend-verification", response_model=ResendVerificationResponse)
@limiter.limit("3/hour")  # Rate limit to prevent abuse
async def resend_verification_email(request: Request, current_user: CurrentUser, db: DbSession):
    """
    Resend email verification email.
    
    Sends a new verification email to the user's registered email address.
    Rate limited to 3 attempts per hour.
    """
    if current_user.email_verified:
        return ResendVerificationResponse(
            message="Email is already verified",
            success=False,
        )
    
    import secrets
    import logging
    from src.app.services.email_service import get_email_service
    
    logger = logging.getLogger(__name__)
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    
    # Store token hash in user record (expires in 24 hours)
    user = await db.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.email_verification_token = get_password_hash(verification_token)
    user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
    await db.commit()
    
    # Send verification email
    verification_url = f"{settings.frontend_url}/auth/verify-email?token={verification_token}"
    
    email_service = get_email_service()
    sent = await email_service.send_email(
        to_email=user.email,
        template_name="email_verification",
        template_data={
            "name": user.first_name or "User",
            "verification_url": verification_url,
        }
    )
    
    if not sent:
        logger.warning(f"Failed to send verification email to {user.email}")
    else:
        logger.info(f"Verification email sent to {user.email}")
    
    return ResendVerificationResponse(
        message="Verification email sent! Please check your inbox.",
        success=True,
    )


# ==================== Password Reset ====================

class ForgotPasswordRequest(BaseModel):
    """Request for forgot password."""
    email: str


class ForgotPasswordResponse(BaseModel):
    """Response for forgot password."""
    message: str
    success: bool


class ResetPasswordRequest(BaseModel):
    """Request to reset password with token."""
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    """Response for password reset."""
    message: str
    success: bool


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("5/hour")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: DbSession,
):
    """
    Request password reset email.
    
    Sends an email with a reset token if the email exists.
    Always returns success to prevent email enumeration.
    """
    import secrets
    import logging
    logger = logging.getLogger(__name__)

    # Find user
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()

    if user:
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Store token hash in user record (expires in 1 hour)
        user.password_reset_token = get_password_hash(reset_token)
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        await db.commit()

        # Send email with reset link
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
        
        # Queue email task
        try:
            from src.app.workers.tasks import send_email_task
            send_email_task.delay(
                to_email=user.email,
                subject="Reset Your Password - FaceMortgage",
                template="password_reset",
                context={
                    "first_name": user.first_name,
                    "reset_url": reset_url,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to queue password reset email: {e}")

        logger.info(f"Password reset requested for: {user.email}")

    # Always return success to prevent email enumeration
    return ForgotPasswordResponse(
        message="If an account with that email exists, we've sent a password reset link.",
        success=True,
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit("10/hour")
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: DbSession,
):
    """
    Reset password using token from forgot-password email.
    
    Validates the token and updates the password if valid.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Validate password strength
    validate_password_strength(body.new_password)

    # Find users with unexpired reset tokens
    result = await db.execute(
        select(User).where(
            User.password_reset_expires > datetime.utcnow()
        )
    )
    users = result.scalars().all()

    # Check token against each user (secure comparison)
    target_user = None
    for user in users:
        if user.password_reset_token and verify_password(body.token, user.password_reset_token):
            target_user = user
            break

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Update password
    target_user.password_hash = get_password_hash(body.new_password)
    target_user.password_reset_token = None
    target_user.password_reset_expires = None
    target_user.failed_login_attempts = 0
    target_user.locked_until = None
    
    await db.commit()

    logger.info(f"Password reset successful for: {target_user.email}")

    return ResetPasswordResponse(
        message="Password reset successful! You can now log in with your new password.",
        success=True,
    )
