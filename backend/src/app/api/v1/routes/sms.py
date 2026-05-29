"""
SMS notification settings and phone verification endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import random
import string

from src.app.core.auth import get_current_user
from src.app.models.user import User
from src.app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users/me", tags=["sms"])


class PhoneVerificationRequest(BaseModel):
    phone: str


class CodeVerificationRequest(BaseModel):
    code: str


class SMSPreferencesUpdate(BaseModel):
    preferences: dict


# In-memory store for verification codes (use Redis in production)
verification_codes: dict = {}


def generate_verification_code() -> str:
    """Generate a 6-digit verification code."""
    return ''.join(random.choices(string.digits, k=6))


@router.get("/sms-preferences")
async def get_sms_preferences(
    current_user: User = Depends(get_current_user),
):
    """Get current user's SMS preferences."""
    return {
        "phone": getattr(current_user, 'phone', None),
        "phone_verified": getattr(current_user, 'phone_verified', False),
        "preferences": getattr(current_user, 'sms_preferences', {
            "sms_new_leads": True,
            "sms_missed_calls": True,
            "sms_scheduled_reminders": True,
        }),
    }


@router.put("/sms-preferences")
async def update_sms_preferences(
    body: SMSPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update SMS notification preferences."""
    # Update user preferences
    if hasattr(current_user, 'sms_preferences'):
        current_user.sms_preferences = body.preferences
    await db.commit()
    
    return {"status": "updated", "preferences": body.preferences}


@router.post("/sms/send-verification")
async def send_sms_verification(
    body: PhoneVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send SMS verification code to phone number."""
    # Validate phone number (basic validation)
    phone = body.phone.strip()
    if len(phone) < 10:
        raise HTTPException(
            status_code=400,
            detail="Invalid phone number"
        )
    
    # Generate verification code
    code = generate_verification_code()
    
    # Store code (with user ID as key)
    verification_codes[str(current_user.id)] = {
        "code": code,
        "phone": phone,
    }
    
    # Update user's phone (unverified)
    if hasattr(current_user, 'phone'):
        current_user.phone = phone
        current_user.phone_verified = False
        await db.commit()
    
    # Send SMS via Twilio
    from src.app.config import settings
    
    # Test mode - return mock response without sending real SMS
    if getattr(settings, 'twilio_test_mode', False) or not settings.twilio_sid:
        print(f"[SMS TEST MODE] Verification code for {phone}: {code}")
        return {"status": "sent", "message": "Verification code sent (test mode)", "test_code": code}
    
    # Production - send real SMS via Twilio
    try:
        from twilio.rest import Client
        client = Client(settings.twilio_sid, settings.twilio_auth_token)
        message = client.messages.create(
            body=f"Your FaceMortgage verification code is: {code}",
            from_=settings.twilio_phone,
            to=phone
        )
        print(f"[SMS] Sent verification to {phone}, SID: {message.sid}")
    except Exception as e:
        print(f"[SMS ERROR] Failed to send: {e}")
        # Fall back to test mode on error
        return {"status": "sent", "message": "Verification code sent (fallback)", "test_code": code}
    
    return {"status": "sent", "message": "Verification code sent"}


@router.post("/sms/verify")
async def verify_sms_code(
    body: CodeVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify SMS code and mark phone as verified."""
    user_id = str(current_user.id)
    
    # Check if we have a pending verification
    if user_id not in verification_codes:
        raise HTTPException(
            status_code=400,
            detail="No pending verification. Please request a new code."
        )
    
    stored = verification_codes[user_id]
    
    # Verify code
    if stored["code"] != body.code:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification code"
        )
    
    # Mark phone as verified
    if hasattr(current_user, 'phone_verified'):
        current_user.phone_verified = True
        await db.commit()
    
    # Clean up
    del verification_codes[user_id]
    
    return {"status": "verified", "message": "Phone number verified"}
