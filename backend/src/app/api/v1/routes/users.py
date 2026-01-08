import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, status, Request
from pydantic import BaseModel
from typing import Optional

from src.app.core.dependencies import DbSession, CurrentUser
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.core.security import verify_password, get_password_hash
from src.app.schemas.user import UserResponse, UserUpdate
from src.app.services.storage import get_storage

router = APIRouter()


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class NotificationSettings(BaseModel):
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    call_reminders: bool = True
    lead_alerts: bool = True
    marketing_emails: bool = False


@router.get("/me", response_model=UserResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_my_profile(request: Request, current_user: CurrentUser):
    """Get current user's profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def update_my_profile(
    request: Request,
    updates: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update current user's profile"""
    update_data = updates.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/me/password")
@limiter.limit(RATE_LIMITS["sensitive"])
async def change_password(
    request: Request,
    password_change: PasswordChange,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Change the current user's password.

    Requires the current password for verification.
    """
    # Verify current password
    if not verify_password(password_change.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password
    if len(password_change.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    # Update password
    current_user.password_hash = get_password_hash(password_change.new_password)
    await db.commit()

    return {"message": "Password updated successfully"}


@router.delete("/me")
@limiter.limit(RATE_LIMITS["sensitive"])
async def delete_my_account(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Soft delete the current user's account.

    This deactivates the account but preserves data for legal/audit purposes.
    """
    current_user.is_active = False
    await db.commit()

    return {"message": "Account deactivated successfully"}


@router.get("/me/notification-settings")
@limiter.limit(RATE_LIMITS["api_read"])
async def get_notification_settings(request: Request, current_user: CurrentUser):
    """
    Get the user's notification preferences.

    Returns default settings if none are configured.
    """
    # In a full implementation, these would be stored in a separate table
    # For now, return defaults
    return NotificationSettings()


@router.put("/me/notification-settings")
@limiter.limit(RATE_LIMITS["api_write"])
async def update_notification_settings(
    request: Request,
    settings: NotificationSettings,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Update the user's notification preferences.
    """
    # In a full implementation, save to database
    # For now, just return the settings as confirmation
    return settings


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/me/avatar")
@limiter.limit(RATE_LIMITS["api_write"])
async def upload_avatar(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(..., description="Avatar image (JPEG, PNG, GIF, or WebP)"),
):
    """
    Upload a new avatar image.

    Supported formats: JPEG, PNG, GIF, WebP
    Maximum file size: 5MB
    """
    # Validate content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: JPEG, PNG, GIF, WebP",
        )

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_AVATAR_SIZE // (1024*1024)}MB",
        )

    # Generate storage key
    extension = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if extension not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        extension = ".jpg"
    unique_id = str(uuid.uuid4())[:8]
    key = f"avatars/{current_user.id}/{unique_id}{extension}"

    # Delete old avatar if exists
    storage = get_storage()
    if current_user.avatar_url and "/avatars/" in current_user.avatar_url:
        old_key = "avatars/" + current_user.avatar_url.split("/avatars/", 1)[1]
        await storage.delete(old_key)

    # Upload new avatar
    avatar_url = await storage.upload(
        file_data=content,
        key=key,
        content_type=file.content_type or "image/jpeg",
    )

    # Update user record
    current_user.avatar_url = avatar_url
    await db.commit()

    return {"message": "Avatar uploaded successfully", "avatar_url": avatar_url}


@router.delete("/me/avatar")
@limiter.limit(RATE_LIMITS["api_write"])
async def delete_avatar(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    """Remove the user's avatar."""
    if current_user.avatar_url:
        current_user.avatar_url = None
        await db.commit()

    return {"message": "Avatar removed"}
