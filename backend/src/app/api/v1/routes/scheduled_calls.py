"""
Scheduled calls routes.

Handles scheduling calls for later instead of immediate connection.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentUserOptional, CurrentUser
from src.app.models.scheduled_call import ScheduledCall, ScheduledCallStatus
from src.app.models.professional import ProfessionalProfile
from src.app.services.email_service import get_email_service
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Schemas ====================

class ScheduleCallRequest(BaseModel):
    professional_id: UUID
    scheduled_for: datetime  # ISO format datetime
    timezone: str = "America/New_York"
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    loan_purpose: Optional[str] = None
    notes: Optional[str] = None


class ScheduleCallResponse(BaseModel):
    id: UUID
    scheduled_for: datetime
    professional_name: str
    confirmation_sent: bool


class ScheduledCallDetail(BaseModel):
    id: UUID
    contact_name: str
    contact_email: str
    contact_phone: Optional[str]
    scheduled_for: datetime
    timezone: str
    loan_purpose: Optional[str]
    notes: Optional[str]
    status: str
    created_at: datetime


class CancelScheduledCallRequest(BaseModel):
    reason: Optional[str] = None


# ==================== Routes ====================

@router.post("", response_model=ScheduleCallResponse)
async def schedule_call(
    request: ScheduleCallRequest,
    current_user: CurrentUserOptional,
    db: DbSession,
):
    """
    Schedule a call with a professional for a future time.

    Both authenticated and anonymous users can schedule calls.
    Confirmation emails will be sent to both parties.
    """
    # Validate scheduled time is in the future (at least 30 minutes)
    min_time = datetime.utcnow() + timedelta(minutes=30)
    if request.scheduled_for < min_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be at least 30 minutes in the future",
        )

    # Validate not too far in the future (max 30 days)
    max_time = datetime.utcnow() + timedelta(days=30)
    if request.scheduled_for > max_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule more than 30 days in advance",
        )

    # Get professional
    query = (
        select(ProfessionalProfile)
        .options(selectinload(ProfessionalProfile.user))
        .where(ProfessionalProfile.id == request.professional_id)
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found",
        )

    # Create scheduled call
    scheduled_call = ScheduledCall(
        borrower_id=current_user.id if current_user else None,
        professional_id=request.professional_id,
        contact_name=request.name,
        contact_email=request.email,
        contact_phone=request.phone,
        scheduled_for=request.scheduled_for,
        timezone=request.timezone,
        loan_purpose=request.loan_purpose,
        notes=request.notes,
        status=ScheduledCallStatus.PENDING,
    )
    db.add(scheduled_call)
    await db.commit()
    await db.refresh(scheduled_call)

    professional_name = f"{professional.user.first_name} {professional.user.last_name}"

    # Send confirmation emails
    email_service = get_email_service()
    confirmation_sent = False

    try:
        # Format date/time for display
        scheduled_date = scheduled_call.scheduled_for.strftime("%B %d, %Y")
        scheduled_time = scheduled_call.scheduled_for.strftime("%I:%M %p")

        # Send emails concurrently
        borrower_email_task = email_service.send_scheduled_call_confirmation(
            borrower_email=request.email,
            borrower_name=request.name,
            professional_name=professional_name,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            timezone=request.timezone,
        )
        professional_email_task = email_service.send_scheduled_call_notification(
            professional_email=professional.user.email,
            borrower_name=request.name,
            borrower_email=request.email,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            timezone=request.timezone,
            notes=request.notes,
        )

        results = await asyncio.gather(borrower_email_task, professional_email_task, return_exceptions=True)
        confirmation_sent = all(r is True for r in results if not isinstance(r, Exception))

        if not confirmation_sent:
            logger.warning(f"Some confirmation emails failed for scheduled call {scheduled_call.id}")
    except Exception as e:
        logger.error(f"Failed to send confirmation emails for scheduled call {scheduled_call.id}: {e}")

    return ScheduleCallResponse(
        id=scheduled_call.id,
        scheduled_for=scheduled_call.scheduled_for,
        professional_name=professional_name,
        confirmation_sent=confirmation_sent,
    )


@router.get("/my-scheduled", response_model=list[ScheduledCallDetail])
async def get_my_scheduled_calls(
    current_user: CurrentUser,
    db: DbSession,
):
    """Get upcoming scheduled calls for the current authenticated borrower."""
    query = (
        select(ScheduledCall)
        .where(
            ScheduledCall.borrower_id == current_user.id,
            ScheduledCall.scheduled_for >= datetime.utcnow(),
            ScheduledCall.status.in_([
                ScheduledCallStatus.PENDING,
                ScheduledCallStatus.CONFIRMED,
            ]),
        )
        .order_by(ScheduledCall.scheduled_for.asc())
        .limit(50)
    )
    result = await db.execute(query)
    scheduled_calls = result.scalars().all()

    return [
        ScheduledCallDetail(
            id=sc.id,
            contact_name=sc.contact_name,
            contact_email=sc.contact_email,
            contact_phone=sc.contact_phone,
            scheduled_for=sc.scheduled_for,
            timezone=sc.timezone,
            loan_purpose=sc.loan_purpose,
            notes=sc.notes,
            status=sc.status.value,
            created_at=sc.created_at,
        )
        for sc in scheduled_calls
    ]


@router.get("/professional/upcoming", response_model=list[ScheduledCallDetail])
async def get_professional_scheduled_calls(
    current_user: CurrentUser,
    db: DbSession,
):
    """Get upcoming scheduled calls for the current professional."""
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a professional account",
        )

    # Get scheduled calls
    query = (
        select(ScheduledCall)
        .where(
            ScheduledCall.professional_id == professional.id,
            ScheduledCall.scheduled_for >= datetime.utcnow(),
            ScheduledCall.status.in_([
                ScheduledCallStatus.PENDING,
                ScheduledCallStatus.CONFIRMED,
            ]),
        )
        .order_by(ScheduledCall.scheduled_for.asc())
        .limit(50)
    )
    result = await db.execute(query)
    scheduled_calls = result.scalars().all()

    return [
        ScheduledCallDetail(
            id=sc.id,
            contact_name=sc.contact_name,
            contact_email=sc.contact_email,
            contact_phone=sc.contact_phone,
            scheduled_for=sc.scheduled_for,
            timezone=sc.timezone,
            loan_purpose=sc.loan_purpose,
            notes=sc.notes,
            status=sc.status.value,
            created_at=sc.created_at,
        )
        for sc in scheduled_calls
    ]


@router.post("/{scheduled_call_id}/confirm")
async def confirm_scheduled_call(
    scheduled_call_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Professional confirms a scheduled call."""
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a professional account",
        )

    # Get scheduled call
    scheduled_call = await db.get(ScheduledCall, scheduled_call_id)
    if not scheduled_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled call not found",
        )

    # Verify ownership
    if scheduled_call.professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to confirm this call",
        )

    # Update status
    scheduled_call.status = ScheduledCallStatus.CONFIRMED
    await db.commit()

    return {"message": "Scheduled call confirmed", "status": "confirmed"}


@router.post("/{scheduled_call_id}/cancel")
async def cancel_scheduled_call(
    scheduled_call_id: UUID,
    request: CancelScheduledCallRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Cancel a scheduled call (either party can cancel)."""
    scheduled_call = await db.get(ScheduledCall, scheduled_call_id)
    if not scheduled_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled call not found",
        )

    # Check if user is authorized (borrower or professional)
    is_borrower = scheduled_call.borrower_id == current_user.id

    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()
    is_professional = professional and scheduled_call.professional_id == professional.id

    if not is_borrower and not is_professional:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this call",
        )

    # Update status
    scheduled_call.status = ScheduledCallStatus.CANCELLED
    if request.reason:
        scheduled_call.notes = f"[CANCELLED] {request.reason}\n\n{scheduled_call.notes or ''}"
    await db.commit()

    return {"message": "Scheduled call cancelled", "status": "cancelled"}
