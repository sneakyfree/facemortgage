from datetime import datetime
import uuid
from fastapi import APIRouter, HTTPException, status
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

# Mock users for development when database is unavailable
MOCK_USERS = {
    "superadmin@facemortgage.com": {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "superadmin@facemortgage.com",
        "password": "superadmin123",
        "first_name": "Super",
        "last_name": "Admin",
        "user_type": "loan_officer",
        "is_admin": True,
        "is_super_admin": True,
        "phone": "(555) 000-0001",
    },
    "admin@facemortgage.com": {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "admin@facemortgage.com",
        "password": "admin123",
        "first_name": "Platform",
        "last_name": "Admin",
        "user_type": "loan_officer",
        "is_admin": True,
        "is_super_admin": False,
        "phone": "(555) 000-0002",
    },
    "user@facemortgage.com": {
        "id": "00000000-0000-0000-0000-000000000003",
        "email": "user@facemortgage.com",
        "password": "user123",
        "first_name": "John",
        "last_name": "Borrower",
        "user_type": "borrower",
        "is_admin": False,
        "is_super_admin": False,
        "phone": "(555) 000-0003",
    },
    "sales@facemortgage.com": {
        "id": "00000000-0000-0000-0000-000000000004",
        "email": "sales@facemortgage.com",
        "password": "sales123",
        "first_name": "Sarah",
        "last_name": "Sales",
        "user_type": "loan_officer",
        "is_admin": False,
        "is_super_admin": False,
        "phone": "(555) 000-0004",
    },
}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: DbSession):
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
async def login(login_data: LoginRequest, db: DbSession):
    # Check mock users first (for development)
    if settings.debug and login_data.email in MOCK_USERS:
        mock_user = MOCK_USERS[login_data.email]
        if login_data.password == mock_user["password"]:
            return TokenPair(
                access_token=create_access_token(mock_user["id"]),
                refresh_token=create_refresh_token(mock_user["id"]),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

    # Try database lookup
    try:
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
    except Exception as e:
        # If database fails and we're in debug mode, check mock users
        if settings.debug:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password (mock mode)",
            )
        raise


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


@router.get("/me/mock/{user_id}")
async def get_mock_user_info(user_id: str):
    """Get mock user info for development - bypasses auth."""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")

    # Find mock user by ID
    for email, user in MOCK_USERS.items():
        if user["id"] == user_id:
            return {
                "id": user["id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "user_type": user["user_type"],
                "phone": user.get("phone"),
                "is_admin": user.get("is_admin", False),
                "is_super_admin": user.get("is_super_admin", False),
                "avatar_url": None,
                "email_verified": True,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
            }

    raise HTTPException(status_code=404, detail="User not found")


@router.post("/logout")
async def logout():
    # In a stateless JWT setup, logout is handled client-side
    # For enhanced security, implement token blacklisting with Redis
    return {"message": "Successfully logged out"}
