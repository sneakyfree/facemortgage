"""
Video call management routes.

Handles:
- Call initiation (authenticated and anonymous)
- Call state management
- Post-call actions (rating, lead creation, lead capture for anonymous)
- LiveKit integration (optional, for scalable video infrastructure)
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentUser, CurrentUserOptional
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.config import settings
from src.app.models.user import User
from src.app.models.professional import ProfessionalProfile, ProfessionalStatus
from src.app.models.call import VideoCall, CallStatus
from src.app.models.review import Review
from src.app.models.lead import Lead, LeadActivity, LeadStatus
from src.app.signaling import get_signaling_service
from src.app.signaling.service import CallState
from src.app.presence import get_presence_service, connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Schemas ====================

class InitiateCallRequest(BaseModel):
    professional_id: UUID
    # For anonymous callers
    anonymous_session_id: Optional[str] = None
    device_fingerprint: Optional[str] = None


class InitiateCallResponse(BaseModel):
    room_id: str
    signaling_url: str
    ice_servers: list
    professional_name: str
    professional_avatar: Optional[str] = None
    call_id: UUID
    is_anonymous: bool = False
    session_id: Optional[str] = None
    # LiveKit fields (only present when using LiveKit)
    use_livekit: bool = False
    livekit_url: Optional[str] = None
    livekit_token: Optional[str] = None


class CaptureLeadRequest(BaseModel):
    """Request to capture lead info from anonymous caller after call."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    loan_purpose: Optional[str] = None
    estimated_amount: Optional[int] = None
    notes: Optional[str] = None


class CaptureLeadResponse(BaseModel):
    success: bool
    lead_id: UUID


class CallStateResponse(BaseModel):
    room_id: str
    state: str
    borrower_id: str
    professional_id: str
    created_at: str
    answered_at: Optional[str] = None
    ended_at: Optional[str] = None


class RateCallRequest(BaseModel):
    overall_rating: int  # 1-5
    communication_rating: Optional[int] = None
    knowledge_rating: Optional[int] = None
    responsiveness_rating: Optional[int] = None
    content: Optional[str] = None


class RateCallResponse(BaseModel):
    message: str
    review_id: UUID


# ==================== Routes ====================

@router.post("", response_model=InitiateCallResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def initiate_call(
    request: Request,
    body: InitiateCallRequest,
    current_user: CurrentUserOptional,  # Optional - allows anonymous calls
    db: DbSession,
):
    """
    Initiate a video call with a professional.

    This creates a call room and returns connection info.
    The borrower should then connect to the signaling WebSocket (or LiveKit if enabled).

    Supports both authenticated and anonymous callers:
    - Authenticated: Uses user ID for tracking
    - Anonymous: Uses session ID for tracking, prompts for info after call

    When USE_LIVEKIT=true, returns LiveKit connection info for SFU-based video.
    Otherwise, uses custom WebRTC signaling for peer-to-peer video.
    """
    signaling = get_signaling_service()
    presence = get_presence_service()

    # Determine caller identity
    if current_user:
        borrower_id = current_user.id
        anonymous_session_id = None
        is_anonymous = False
        caller_id = str(current_user.id)
        caller_name = f"{current_user.first_name} {current_user.last_name}"
    else:
        borrower_id = None
        anonymous_session_id = body.anonymous_session_id or str(uuid.uuid4())
        is_anonymous = True
        caller_id = f"anon:{anonymous_session_id}"
        caller_name = "Anonymous Caller"

    # Get professional
    query = (
        select(ProfessionalProfile)
        .options(selectinload(ProfessionalProfile.user))
        .where(ProfessionalProfile.id == body.professional_id)
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found",
        )

    # Check if professional is available
    is_available = await presence.is_available(str(professional.id))
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Professional is not available",
        )

    # Check if LiveKit is enabled
    use_livekit = settings.use_livekit
    livekit_url = None
    livekit_token = None
    room_id = None

    if use_livekit:
        # Use LiveKit for scalable video
        try:
            from src.app.integrations.livekit import get_livekit_service
            from src.app.integrations.livekit.service import ParticipantRole

            livekit = get_livekit_service()

            if not livekit.is_configured:
                logger.warning("LiveKit enabled but not configured, falling back to custom signaling")
                use_livekit = False
            else:
                # Generate room name
                room_id = livekit.generate_room_name(
                    caller_id[:8] if len(caller_id) > 8 else caller_id,
                    str(professional.id)[:8],
                )

                # Create LiveKit room
                await livekit.create_room(room_id)

                # Generate token for borrower
                borrower_token = livekit.create_token(
                    room_name=room_id,
                    participant_identity=caller_id,
                    participant_name=caller_name,
                    role=ParticipantRole.BORROWER,
                    metadata={
                        "is_anonymous": is_anonymous,
                        "professional_id": str(professional.id),
                    },
                )
                livekit_token = borrower_token.token
                livekit_url = settings.livekit_url

                # Also create token for professional (will be sent via notification)
                professional_token = livekit.create_token(
                    room_name=room_id,
                    participant_identity=str(professional.id),
                    participant_name=f"{professional.user.first_name} {professional.user.last_name}",
                    role=ParticipantRole.PROFESSIONAL,
                )

                logger.info(f"LiveKit room created: {room_id}")

        except ImportError:
            logger.warning("LiveKit SDK not installed, falling back to custom signaling")
            use_livekit = False
        except Exception as e:
            logger.error(f"LiveKit initialization failed: {e}, falling back to custom signaling")
            use_livekit = False

    # Use custom signaling if LiveKit is not enabled/available
    if not use_livekit:
        # Create call room with custom signaling
        try:
            room = await signaling.create_room(
                borrower_id=caller_id,
                professional_id=str(professional.id),
            )
            room_id = room.room_id
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

        # Update room state to ringing
        await signaling.update_room_state(room_id, CallState.RINGING)

    # Mark professional as busy
    await presence.set_busy(str(professional.id), room_id)

    # Create video call record in database
    video_call = VideoCall(
        room_id=room_id,
        borrower_id=borrower_id,  # None for anonymous
        professional_id=professional.id,
        anonymous_session_id=anonymous_session_id if is_anonymous else None,
        anonymous_device_fingerprint=body.device_fingerprint if is_anonymous else None,
        status=CallStatus.RINGING,
        initiated_at=datetime.utcnow(),
    )
    db.add(video_call)
    await db.commit()
    await db.refresh(video_call)

    # Prepare notification payload
    notification_payload = {
        "room_id": room_id,
        "caller_id": caller_id,
        "caller_name": caller_name,
        "is_anonymous": is_anonymous,
        "use_livekit": use_livekit,
    }

    # Include LiveKit token for professional if using LiveKit
    if use_livekit and 'professional_token' in dir():
        notification_payload["livekit_url"] = livekit_url
        notification_payload["livekit_token"] = professional_token.token

    # Notify professional via presence WebSocket
    await connection_manager.send_to_professional(str(professional.id), {
        "type": "incoming_call",
        "payload": notification_payload,
    })

    # Send push notification for mobile (in addition to WebSocket)
    # This ensures professionals get notified even if not connected to WebSocket
    try:
        from src.app.services.push_notification import push_service
        await push_service.send_incoming_call(
            professional_user_id=str(professional.user_id),
            caller_name=caller_name,
            room_id=room_id,
            call_id=str(video_call.id),
        )
    except Exception as e:
        # Don't fail the call if push fails - WebSocket is primary
        logger.warning(f"Push notification failed: {e}")

    # Get ICE servers (only needed for custom signaling)
    ice_servers = await signaling.get_ice_servers() if not use_livekit else []

    return InitiateCallResponse(
        room_id=room_id,
        signaling_url=f"/ws/signaling/{room_id}/{caller_id}" if not use_livekit else "",
        ice_servers=ice_servers,
        professional_name=f"{professional.user.first_name} {professional.user.last_name}",
        professional_avatar=professional.user.avatar_url,
        call_id=video_call.id,
        is_anonymous=is_anonymous,
        session_id=anonymous_session_id,
        use_livekit=use_livekit,
        livekit_url=livekit_url,
        livekit_token=livekit_token,
    )


@router.get("/{room_id}", response_model=CallStateResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_call_state(
    request: Request,
    room_id: str,
    current_user: CurrentUser,
):
    """Get the current state of a call."""
    signaling = get_signaling_service()

    room = await signaling.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found",
        )

    # Verify user is a participant
    if str(current_user.id) not in (room.borrower_id, room.professional_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this call",
        )

    return CallStateResponse(
        room_id=room.room_id,
        state=room.state.value,
        borrower_id=room.borrower_id,
        professional_id=room.professional_id,
        created_at=room.created_at.isoformat(),
        answered_at=room.answered_at.isoformat() if room.answered_at else None,
        ended_at=room.ended_at.isoformat() if room.ended_at else None,
    )


@router.post("/{room_id}/end")
@limiter.limit(RATE_LIMITS["api_write"])
async def end_call(
    request: Request,
    room_id: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """End an active call."""
    signaling = get_signaling_service()
    presence = get_presence_service()

    room = await signaling.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found",
        )

    # Verify user is a participant
    if str(current_user.id) not in (room.borrower_id, room.professional_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to end this call",
        )

    # Update room state
    room = await signaling.update_room_state(
        room_id,
        CallState.ENDED,
        f"ended_by_{current_user.id}",
    )

    # Calculate pickup time
    pickup_time = signaling.calculate_pickup_time(room)

    # Update database record
    query = select(VideoCall).where(VideoCall.room_id == room_id)
    result = await db.execute(query)
    video_call = result.scalar_one_or_none()

    if video_call:
        video_call.status = CallStatus.COMPLETED
        video_call.ended_at = datetime.utcnow()
        if pickup_time:
            video_call.pickup_time_seconds = pickup_time
        if video_call.answered_at:
            video_call.duration_seconds = int(
                (video_call.ended_at - video_call.answered_at).total_seconds()
            )
        await db.commit()

        # Update professional's average pickup time
        await _update_professional_pickup_time(db, UUID(room.professional_id))

    # Set professional back to available
    await presence.set_available(room.professional_id)

    return {
        "message": "Call ended",
        "duration_seconds": video_call.duration_seconds if video_call else None,
        "pickup_time_seconds": pickup_time,
    }


@router.post("/{room_id}/rate", response_model=RateCallResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def rate_call(
    request: Request,
    room_id: str,
    rating: RateCallRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Rate a completed call.

    Only borrowers can rate calls. Rating must be submitted
    within 24 hours of call completion.
    """
    # Get video call
    query = select(VideoCall).where(VideoCall.room_id == room_id)
    result = await db.execute(query)
    video_call = result.scalar_one_or_none()

    if not video_call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found",
        )

    # Verify current user is the borrower
    if video_call.borrower_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the borrower can rate the call",
        )

    # Check if call is completed
    if video_call.status != CallStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only rate completed calls",
        )

    # Check if already rated
    existing_review = await db.execute(
        select(Review).where(Review.video_call_id == video_call.id)
    )
    if existing_review.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Call already rated",
        )

    # Validate rating
    if not 1 <= rating.overall_rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5",
        )

    # Create review
    review = Review(
        video_call_id=video_call.id,
        reviewer_id=current_user.id,
        reviewed_professional_id=video_call.professional_id,
        overall_rating=rating.overall_rating,
        communication_rating=rating.communication_rating,
        knowledge_rating=rating.knowledge_rating,
        responsiveness_rating=rating.responsiveness_rating,
        content=rating.content,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    # Update professional's average rating
    await _update_professional_rating(db, video_call.professional_id)

    return RateCallResponse(
        message="Thank you for your feedback!",
        review_id=review.id,
    )


@router.post("/{call_id}/capture-lead", response_model=CaptureLeadResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def capture_anonymous_lead(
    request: Request,
    call_id: UUID,
    body: CaptureLeadRequest,
    db: DbSession,
):
    """
    Capture contact info from anonymous caller after call ends.

    This creates a lead for the professional from the anonymous call.
    Only works for calls where borrower_id is None (anonymous calls).
    """
    # Get the call
    query = select(VideoCall).where(VideoCall.id == call_id)
    result = await db.execute(query)
    call = result.scalar_one_or_none()

    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found",
        )

    # Must be anonymous call (borrower_id is None)
    if call.borrower_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not an anonymous call - lead capture not applicable",
        )

    # Update call with captured info
    call.captured_name = body.name
    call.captured_email = body.email
    call.captured_phone = body.phone
    call.lead_captured_at = datetime.utcnow()

    # Create lead for professional
    lead = Lead(
        professional_id=call.professional_id,
        borrower_id=None,  # Anonymous
        source_call_id=call.id,
        contact_name=body.name,
        contact_email=body.email,
        contact_phone=body.phone,
        loan_purpose=body.loan_purpose,
        estimated_loan_amount=body.estimated_amount,
        notes=body.notes,
        lead_status=LeadStatus.NEW,
        utm_source="anonymous_call",
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    # Add activity
    activity = LeadActivity(
        lead_id=lead.id,
        activity_type="call_completed",
        description=f"Video call completed - {call.duration_seconds or 0}s",
        metadata={"call_id": str(call.id), "anonymous": True},
    )
    db.add(activity)
    await db.commit()

    return CaptureLeadResponse(
        success=True,
        lead_id=lead.id,
    )


# ==================== Helper Functions ====================

async def _update_professional_rating(db: DbSession, professional_id: UUID):
    """Update a professional's average rating based on all reviews."""
    from sqlalchemy import func

    # Get average rating
    result = await db.execute(
        select(func.avg(Review.overall_rating), func.count(Review.id))
        .where(Review.reviewed_professional_id == professional_id)
    )
    row = result.one()
    avg_rating, total_reviews = row

    # Update professional profile
    query = select(ProfessionalProfile).where(ProfessionalProfile.id == professional_id)
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if professional:
        professional.avg_rating = avg_rating or 0
        professional.total_reviews = total_reviews or 0
        await db.commit()


async def _update_professional_pickup_time(db: DbSession, professional_id: UUID):
    """Update a professional's average pickup time."""
    from sqlalchemy import func

    # Get average pickup time from completed calls
    result = await db.execute(
        select(func.avg(VideoCall.pickup_time_seconds))
        .where(VideoCall.professional_id == professional_id)
        .where(VideoCall.status == CallStatus.COMPLETED)
        .where(VideoCall.pickup_time_seconds.isnot(None))
    )
    avg_pickup = result.scalar()

    # Update professional profile
    query = select(ProfessionalProfile).where(ProfessionalProfile.id == professional_id)
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if professional and avg_pickup:
        professional.avg_pickup_time_seconds = avg_pickup
        professional.total_calls_completed = (professional.total_calls_completed or 0) + 1
        await db.commit()
