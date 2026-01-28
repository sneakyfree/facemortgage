"""
OAuth authentication routes.

Provides Google OAuth login/registration endpoints.
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
import httpx

from src.app.config import settings
from src.app.core.dependencies import DbSession
from src.app.core.security import create_access_token, create_refresh_token
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.user import User, UserType
from src.app.models.professional import ProfessionalProfile
from src.app.models.borrower import BorrowerProfile
from src.app.api.v1.routes.auth import set_auth_cookies

router = APIRouter()
logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleAuthRequest(BaseModel):
    """Request for Google OAuth login."""
    code: str  # Authorization code from Google
    redirect_uri: str
    user_type: Optional[UserType] = None  # For new user registration


class OAuthTokenResponse(BaseModel):
    """OAuth token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


class GoogleUserInfo(BaseModel):
    """User info from Google."""
    id: str
    email: EmailStr
    verified_email: bool
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None


async def exchange_google_code(code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for Google access token."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if response.status_code != 200:
            logger.error(f"Google token exchange failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to authenticate with Google",
            )
        return response.json()


async def get_google_user_info(access_token: str) -> GoogleUserInfo:
    """Get user info from Google."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            logger.error(f"Google user info failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info from Google",
            )
        return GoogleUserInfo(**response.json())


@router.post("/google", response_model=OAuthTokenResponse)
@limiter.limit(RATE_LIMITS["auth_login"])
async def google_auth(
    request: Request,
    response: Response,
    body: GoogleAuthRequest,
    db: DbSession,
):
    """
    Authenticate with Google OAuth.
    
    If the user exists, logs them in.
    If not, creates a new account with the provided user_type.
    """
    # Exchange code for token
    token_data = await exchange_google_code(body.code, body.redirect_uri)
    google_access_token = token_data.get("access_token")
    
    if not google_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access token received from Google",
        )

    # Get user info from Google
    google_user = await get_google_user_info(google_access_token)

    # Check if user exists
    result = await db.execute(select(User).where(User.email == google_user.email))
    user = result.scalar_one_or_none()

    is_new_user = False

    if not user:
        # Create new user
        if not body.user_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_type is required for new users",
            )

        user = User(
            email=google_user.email,
            password_hash="",  # No password for OAuth users
            user_type=body.user_type,
            first_name=google_user.given_name or google_user.name.split()[0],
            last_name=google_user.family_name or (google_user.name.split()[-1] if len(google_user.name.split()) > 1 else ""),
            avatar_url=google_user.picture,
            email_verified=google_user.verified_email,
            google_id=google_user.id,
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
        is_new_user = True
        logger.info(f"Created new user via Google OAuth: {user.id}")
    else:
        # Update Google ID if not set
        if not user.google_id:
            user.google_id = google_user.id
        
        # Update avatar if user doesn't have one
        if not user.avatar_url and google_user.picture:
            user.avatar_url = google_user.picture

        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.commit()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Generate tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)

    return OAuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        is_new_user=is_new_user,
    )


@router.get("/google/url")
async def get_google_oauth_url(
    redirect_uri: str,
    user_type: Optional[UserType] = None,
):
    """
    Get Google OAuth authorization URL.
    
    Frontend should redirect user to this URL to initiate OAuth flow.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )

    state = f"user_type={user_type.value}" if user_type else ""
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state,
    }
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items() if v)
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    return {"auth_url": auth_url}
