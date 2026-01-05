from datetime import datetime
import uuid
from fastapi import APIRouter, HTTPException, status, Request
from sqlalchemy import select

from src.app.config import settings
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
async def login(request: Request, login_data: LoginRequest, db: DbSession):
    # Database lookup only - no mock users in any environment
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()

    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(refresh_data: RefreshTokenRequest, db: DbSession):
    payload = decode_token(refresh_data.refresh_token)

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

    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me")
async def get_current_user_info(current_user: CurrentUser):
    return current_user


@router.post("/logout")
async def logout():
    # In a stateless JWT setup, logout is handled client-side
    # For enhanced security, implement token blacklisting with Redis
    return {"message": "Successfully logged out"}
