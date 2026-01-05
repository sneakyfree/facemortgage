import logging
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.core.database import get_db
from src.app.core.security import decode_token
from src.app.models.user import User, UserType
from src.app.models.professional import ProfessionalProfile

logger = logging.getLogger(__name__)


security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    if payload.type != "access":
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(HTTPBearer(auto_error=False))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def require_professional(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Require professional user type and eager-load the professional_profile.

    This is used by routes that need access to current_user.professional_profile.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    if payload.type != "access":
        raise credentials_exception

    # Eager-load professional_profile
    result = await db.execute(
        select(User)
        .options(selectinload(User.professional_profile))
        .where(User.id == payload.sub)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    if user.user_type not in [
        UserType.LOAN_OFFICER,
        UserType.REALTOR,
        UserType.TITLE_REP,
        UserType.ATTORNEY,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professional account required",
        )

    # Ensure professional profile exists
    if user.professional_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found. Please complete your profile setup.",
        )

    return user


async def require_borrower(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Require borrower user type and eager-load the borrower_profile.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    if payload.type != "access":
        raise credentials_exception

    # Eager-load borrower_profile
    from src.app.models.borrower import BorrowerProfile
    result = await db.execute(
        select(User)
        .options(selectinload(User.borrower_profile))
        .where(User.id == payload.sub)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    if user.user_type != UserType.BORROWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Borrower account required",
        )

    return user


async def get_current_user_ws(
    token: str,
    db: AsyncSession,
    load_professional_profile: bool = False,
) -> Optional[User]:
    """
    Authenticate a user from a WebSocket connection.

    Unlike HTTP auth, WebSocket tokens are passed as query params or in the first message.

    Args:
        token: JWT access token
        db: Database session
        load_professional_profile: Whether to eager-load the professional_profile

    Returns:
        User if valid, None otherwise
    """
    if not token:
        return None

    try:
        payload = decode_token(token)

        if payload is None or payload.type != "access":
            return None

        query = select(User).where(User.id == payload.sub)

        if load_professional_profile:
            query = query.options(selectinload(User.professional_profile))

        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            return None

        return user
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        return None


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require admin role for access."""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]
CurrentProfessional = Annotated[User, Depends(require_professional)]
CurrentBorrower = Annotated[User, Depends(require_borrower)]
CurrentAdmin = Annotated[User, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
