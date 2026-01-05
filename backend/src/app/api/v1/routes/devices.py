"""
Device registration routes for push notifications.

Handles registering and unregistering mobile devices for push notifications.
"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.app.core.dependencies import DbSession, CurrentUser
from src.app.models.user import User

router = APIRouter()


# ==================== Schemas ====================

class RegisterDeviceRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=500)
    platform: str = Field(..., pattern="^(ios|android|web)$")
    device_name: Optional[str] = Field(None, max_length=100)


class DeviceInfo(BaseModel):
    token: str
    platform: str
    device_name: Optional[str]
    created_at: str


class UnregisterDeviceRequest(BaseModel):
    token: str


# ==================== Routes ====================

@router.post("/register")
async def register_device(
    request: RegisterDeviceRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Register a device for push notifications.

    Call this when the app starts or when the FCM token changes.
    Each user can have multiple devices registered.
    """
    # Get user with device tokens
    user = await db.get(User, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Initialize device_tokens if None
    if user.device_tokens is None:
        user.device_tokens = []

    # Check if token already exists (update it) or add new
    existing_idx = None
    for i, device in enumerate(user.device_tokens):
        if device.get("token") == request.token:
            existing_idx = i
            break

    device_entry = {
        "token": request.token,
        "platform": request.platform,
        "device_name": request.device_name,
        "created_at": datetime.utcnow().isoformat(),
    }

    if existing_idx is not None:
        # Update existing
        user.device_tokens[existing_idx] = device_entry
    else:
        # Add new (limit to 5 devices per user)
        if len(user.device_tokens) >= 5:
            # Remove oldest
            user.device_tokens = user.device_tokens[-4:]
        user.device_tokens.append(device_entry)

    # Update last platform
    user.last_platform = request.platform
    user.push_enabled = True

    # Force the list to be seen as modified
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(user, "device_tokens")

    await db.commit()

    return {
        "success": True,
        "message": "Device registered successfully",
        "device_count": len(user.device_tokens),
    }


@router.delete("/unregister")
async def unregister_device(
    request: UnregisterDeviceRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Unregister a device from push notifications.

    Call this when the user logs out or disables notifications.
    """
    user = await db.get(User, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.device_tokens:
        original_count = len(user.device_tokens)
        user.device_tokens = [
            d for d in user.device_tokens
            if d.get("token") != request.token
        ]

        # Force the list to be seen as modified
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "device_tokens")

        await db.commit()

        removed = original_count - len(user.device_tokens)
        return {
            "success": True,
            "message": f"Removed {removed} device(s)",
            "device_count": len(user.device_tokens),
        }

    return {
        "success": True,
        "message": "No devices to remove",
        "device_count": 0,
    }


@router.get("/my-devices", response_model=List[DeviceInfo])
async def get_my_devices(
    current_user: CurrentUser,
    db: DbSession,
):
    """Get all registered devices for the current user."""
    user = await db.get(User, current_user.id)
    if not user or not user.device_tokens:
        return []

    return [
        DeviceInfo(
            token=d.get("token", "")[-20:] + "...",  # Truncate for privacy
            platform=d.get("platform", "unknown"),
            device_name=d.get("device_name"),
            created_at=d.get("created_at", ""),
        )
        for d in user.device_tokens
    ]


@router.post("/toggle-push")
async def toggle_push_notifications(
    enabled: bool,
    current_user: CurrentUser,
    db: DbSession,
):
    """Enable or disable push notifications for the user."""
    user = await db.get(User, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.push_enabled = enabled
    await db.commit()

    return {
        "success": True,
        "push_enabled": enabled,
    }
