"""
Video Moderation API routes for admin content review.

Admins can:
- List pending videos for review
- Approve videos (makes them visible in grid)
- Reject videos with a reason (professional is notified)
- View moderation statistics
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Request, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentAdmin
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.moderation import VideoModeration, ModerationStatus
from src.app.models.professional import ProfessionalProfile
from src.app.schemas.moderation import (
    VideoModerationResponse,
    RejectVideoRequest,
    ModerationListResponse,
    ModerationStatsResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/pending", response_model=ModerationListResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def list_pending_videos(
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List all videos pending moderation review.

    Returns paginated list sorted by oldest first (FIFO queue).
    Only accessible by admin users.
    """
    offset = (page - 1) * page_size

    # Count total pending
    count_query = select(func.count(VideoModeration.id)).where(
        VideoModeration.status == ModerationStatus.PENDING
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get pending videos with professional info
    query = (
        select(VideoModeration)
        .options(selectinload(VideoModeration.professional).selectinload(ProfessionalProfile.user))
        .where(VideoModeration.status == ModerationStatus.PENDING)
        .order_by(VideoModeration.created_at.asc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    moderations = result.scalars().all()

    # Build response with professional info
    items = []
    for mod in moderations:
        prof_name = None
        prof_email = None
        if mod.professional and mod.professional.user:
            prof_name = f"{mod.professional.user.first_name} {mod.professional.user.last_name}"
            prof_email = mod.professional.user.email

        items.append(VideoModerationResponse(
            id=mod.id,
            professional_id=mod.professional_id,
            video_url=mod.video_url,
            status=mod.status,
            reviewed_by=mod.reviewed_by,
            reviewed_at=mod.reviewed_at,
            rejection_reason=mod.rejection_reason,
            created_at=mod.created_at,
            updated_at=mod.updated_at,
            professional_name=prof_name,
            professional_email=prof_email,
        ))

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ModerationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/{moderation_id}/approve", response_model=VideoModerationResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def approve_video(
    request: Request,
    moderation_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Approve a video for display in the grid.

    Updates moderation status to 'approved' and records reviewer.
    Video becomes visible in grid immediately.
    """
    # Get moderation record
    query = select(VideoModeration).where(VideoModeration.id == moderation_id)
    result = await db.execute(query)
    moderation = result.scalar_one_or_none()

    if not moderation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation record not found",
        )

    if moderation.status != ModerationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video already {moderation.status.value}. Cannot approve.",
        )

    # Update status
    moderation.status = ModerationStatus.APPROVED
    moderation.reviewed_by = current_admin.id
    moderation.reviewed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(moderation)

    logger.info(f"Video {moderation_id} approved by admin {current_admin.id}")

    return VideoModerationResponse(
        id=moderation.id,
        professional_id=moderation.professional_id,
        video_url=moderation.video_url,
        status=moderation.status,
        reviewed_by=moderation.reviewed_by,
        reviewed_at=moderation.reviewed_at,
        rejection_reason=moderation.rejection_reason,
        created_at=moderation.created_at,
        updated_at=moderation.updated_at,
    )


@router.post("/{moderation_id}/reject", response_model=VideoModerationResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def reject_video(
    request: Request,
    moderation_id: UUID,
    body: RejectVideoRequest,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Reject a video with a reason.

    Updates moderation status to 'rejected' and stores reason.
    Professional receives notification with rejection reason.
    """
    # Get moderation record
    query = select(VideoModeration).where(VideoModeration.id == moderation_id)
    result = await db.execute(query)
    moderation = result.scalar_one_or_none()

    if not moderation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation record not found",
        )

    if moderation.status != ModerationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video already {moderation.status.value}. Cannot reject.",
        )

    # Update status
    moderation.status = ModerationStatus.REJECTED
    moderation.reviewed_by = current_admin.id
    moderation.reviewed_at = datetime.utcnow()
    moderation.rejection_reason = body.reason

    await db.commit()
    await db.refresh(moderation)

    logger.info(f"Video {moderation_id} rejected by admin {current_admin.id}: {body.reason}")

    # TODO: Send notification to professional about rejection

    return VideoModerationResponse(
        id=moderation.id,
        professional_id=moderation.professional_id,
        video_url=moderation.video_url,
        status=moderation.status,
        reviewed_by=moderation.reviewed_by,
        reviewed_at=moderation.reviewed_at,
        rejection_reason=moderation.rejection_reason,
        created_at=moderation.created_at,
        updated_at=moderation.updated_at,
    )


@router.get("/stats", response_model=ModerationStatsResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_moderation_stats(
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Get moderation queue statistics.

    Returns counts for pending, approved today, rejected today,
    and average review time.
    """
    today = date.today()

    # Pending count
    pending_result = await db.execute(
        select(func.count(VideoModeration.id)).where(
            VideoModeration.status == ModerationStatus.PENDING
        )
    )
    pending_count = pending_result.scalar() or 0

    # Approved today
    approved_result = await db.execute(
        select(func.count(VideoModeration.id)).where(
            and_(
                VideoModeration.status == ModerationStatus.APPROVED,
                func.date(VideoModeration.reviewed_at) == today,
            )
        )
    )
    approved_today = approved_result.scalar() or 0

    # Rejected today
    rejected_result = await db.execute(
        select(func.count(VideoModeration.id)).where(
            and_(
                VideoModeration.status == ModerationStatus.REJECTED,
                func.date(VideoModeration.reviewed_at) == today,
            )
        )
    )
    rejected_today = rejected_result.scalar() or 0

    # Average review time (for items reviewed in last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)

    avg_result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', VideoModeration.reviewed_at) -
                func.extract('epoch', VideoModeration.created_at)
            ) / 3600  # Convert to hours
        ).where(
            and_(
                VideoModeration.reviewed_at.isnot(None),
                VideoModeration.reviewed_at >= week_ago,
            )
        )
    )
    avg_hours = avg_result.scalar() or 0.0

    return ModerationStatsResponse(
        pending_count=pending_count,
        approved_today=approved_today,
        rejected_today=rejected_today,
        avg_review_time_hours=round(float(avg_hours), 1),
    )


@router.get("/{moderation_id}", response_model=VideoModerationResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_moderation_detail(
    request: Request,
    moderation_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Get details of a specific moderation record.
    """
    query = (
        select(VideoModeration)
        .options(selectinload(VideoModeration.professional).selectinload(ProfessionalProfile.user))
        .where(VideoModeration.id == moderation_id)
    )
    result = await db.execute(query)
    moderation = result.scalar_one_or_none()

    if not moderation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation record not found",
        )

    prof_name = None
    prof_email = None
    if moderation.professional and moderation.professional.user:
        prof_name = f"{moderation.professional.user.first_name} {moderation.professional.user.last_name}"
        prof_email = moderation.professional.user.email

    return VideoModerationResponse(
        id=moderation.id,
        professional_id=moderation.professional_id,
        video_url=moderation.video_url,
        status=moderation.status,
        reviewed_by=moderation.reviewed_by,
        reviewed_at=moderation.reviewed_at,
        rejection_reason=moderation.rejection_reason,
        created_at=moderation.created_at,
        updated_at=moderation.updated_at,
        professional_name=prof_name,
        professional_email=prof_email,
    )
