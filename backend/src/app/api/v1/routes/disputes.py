"""
Dispute Resolution API routes.

Provides endpoints for:
- Users: Create disputes, view their disputes, add messages
- Admins: View all disputes, assign, update status, resolve
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Request, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentUser, CurrentAdmin
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.dispute import Dispute, DisputeMessage, DisputeStatus, DisputePriority
from src.app.schemas.dispute import (
    CreateDisputeRequest,
    AddMessageRequest,
    ResolveDisputeRequest,
    UpdateDisputeRequest,
    DisputeResponse,
    DisputeMessageResponse,
    DisputeListResponse,
    DisputeStatsResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_dispute_response(dispute: Dispute, include_internal: bool = False) -> DisputeResponse:
    """Build dispute response with user/assignee info and messages."""
    user_name = None
    user_email = None
    if dispute.user:
        user_name = f"{dispute.user.first_name} {dispute.user.last_name}"
        user_email = dispute.user.email

    assignee_name = None
    if dispute.assignee:
        assignee_name = f"{dispute.assignee.first_name} {dispute.assignee.last_name}"

    messages = []
    for msg in dispute.messages:
        if msg.is_internal and not include_internal:
            continue
        sender_name = None
        if msg.sender:
            sender_name = f"{msg.sender.first_name} {msg.sender.last_name}"
        messages.append(DisputeMessageResponse(
            id=msg.id,
            dispute_id=msg.dispute_id,
            sender_id=msg.sender_id,
            sender_name=sender_name,
            message=msg.message,
            is_internal=msg.is_internal,
            created_at=msg.created_at,
        ))

    return DisputeResponse(
        id=dispute.id,
        user_id=dispute.user_id,
        user_name=user_name,
        user_email=user_email,
        dispute_type=dispute.dispute_type,
        subject=dispute.subject,
        description=dispute.description,
        status=dispute.status,
        priority=dispute.priority,
        related_transaction_id=dispute.related_transaction_id,
        assigned_to=dispute.assigned_to,
        assignee_name=assignee_name,
        resolution_notes=dispute.resolution_notes,
        resolved_at=dispute.resolved_at,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
        messages=messages,
    )


# ==================== User Endpoints ====================

@router.post("", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["api_write"])
async def create_dispute(
    request: Request,
    body: CreateDisputeRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Create a new dispute ticket.
    
    Users can submit disputes for billing issues, service complaints,
    technical problems, or other concerns.
    """
    dispute = Dispute(
        user_id=current_user.id,
        dispute_type=body.dispute_type,
        subject=body.subject,
        description=body.description,
        related_transaction_id=body.related_transaction_id,
        status=DisputeStatus.OPEN,
        priority=DisputePriority.MEDIUM,
    )
    db.add(dispute)
    await db.commit()
    await db.refresh(dispute)

    logger.info(f"Dispute {dispute.id} created by user {current_user.id}")

    return DisputeResponse(
        id=dispute.id,
        user_id=dispute.user_id,
        dispute_type=dispute.dispute_type,
        subject=dispute.subject,
        description=dispute.description,
        status=dispute.status,
        priority=dispute.priority,
        related_transaction_id=dispute.related_transaction_id,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
        messages=[],
    )


@router.get("/my", response_model=DisputeListResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def list_my_disputes(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    status_filter: Optional[DisputeStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List current user's disputes."""
    offset = (page - 1) * page_size

    # Build query
    query = select(Dispute).where(Dispute.user_id == current_user.id)
    if status_filter:
        query = query.where(Dispute.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get disputes with messages
    query = (
        query
        .options(
            selectinload(Dispute.messages).selectinload(DisputeMessage.sender),
            selectinload(Dispute.assignee),
        )
        .order_by(Dispute.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    disputes = result.scalars().all()

    items = [_build_dispute_response(d, include_internal=False) for d in disputes]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return DisputeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/my/{dispute_id}", response_model=DisputeResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_my_dispute(
    request: Request,
    dispute_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """Get details of a user's dispute."""
    query = (
        select(Dispute)
        .options(
            selectinload(Dispute.messages).selectinload(DisputeMessage.sender),
            selectinload(Dispute.assignee),
        )
        .where(Dispute.id == dispute_id)
        .where(Dispute.user_id == current_user.id)
    )
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found",
        )

    return _build_dispute_response(dispute, include_internal=False)


@router.post("/my/{dispute_id}/messages", response_model=DisputeMessageResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def add_message_to_my_dispute(
    request: Request,
    dispute_id: UUID,
    body: AddMessageRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Add a message to a user's dispute."""
    # Get dispute
    query = select(Dispute).where(
        Dispute.id == dispute_id,
        Dispute.user_id == current_user.id,
    )
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found",
        )

    if dispute.status in [DisputeStatus.RESOLVED, DisputeStatus.CLOSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add messages to resolved or closed disputes",
        )

    # Create message (users cannot set is_internal)
    message = DisputeMessage(
        dispute_id=dispute.id,
        sender_id=current_user.id,
        message=body.message,
        is_internal=False,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return DisputeMessageResponse(
        id=message.id,
        dispute_id=message.dispute_id,
        sender_id=message.sender_id,
        sender_name=f"{current_user.first_name} {current_user.last_name}",
        message=message.message,
        is_internal=message.is_internal,
        created_at=message.created_at,
    )


# ==================== Admin Endpoints ====================

@router.get("/admin/all", response_model=DisputeListResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def list_all_disputes(
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
    status_filter: Optional[DisputeStatus] = None,
    priority_filter: Optional[DisputePriority] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all disputes (admin only)."""
    offset = (page - 1) * page_size

    # Build query
    query = select(Dispute)
    if status_filter:
        query = query.where(Dispute.status == status_filter)
    if priority_filter:
        query = query.where(Dispute.priority == priority_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get disputes
    query = (
        query
        .options(
            selectinload(Dispute.user),
            selectinload(Dispute.assignee),
            selectinload(Dispute.messages).selectinload(DisputeMessage.sender),
        )
        .order_by(Dispute.priority.desc(), Dispute.created_at.asc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    disputes = result.scalars().all()

    items = [_build_dispute_response(d, include_internal=True) for d in disputes]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return DisputeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/admin/{dispute_id}", response_model=DisputeResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_dispute_admin(
    request: Request,
    dispute_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """Get dispute details (admin only)."""
    query = (
        select(Dispute)
        .options(
            selectinload(Dispute.user),
            selectinload(Dispute.assignee),
            selectinload(Dispute.messages).selectinload(DisputeMessage.sender),
        )
        .where(Dispute.id == dispute_id)
    )
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found",
        )

    return _build_dispute_response(dispute, include_internal=True)


@router.patch("/admin/{dispute_id}", response_model=DisputeResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def update_dispute(
    request: Request,
    dispute_id: UUID,
    body: UpdateDisputeRequest,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """Update dispute properties (admin only)."""
    query = select(Dispute).where(Dispute.id == dispute_id)
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found",
        )

    if body.status is not None:
        dispute.status = body.status
    if body.priority is not None:
        dispute.priority = body.priority
    if body.assigned_to is not None:
        dispute.assigned_to = body.assigned_to

    await db.commit()
    await db.refresh(dispute)

    logger.info(f"Dispute {dispute_id} updated by admin {current_admin.id}")

    return _build_dispute_response(dispute, include_internal=True)


@router.post("/admin/{dispute_id}/messages", response_model=DisputeMessageResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def add_admin_message(
    request: Request,
    dispute_id: UUID,
    body: AddMessageRequest,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """Add a message to a dispute (admin only). Can be internal."""
    query = select(Dispute).where(Dispute.id == dispute_id)
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found",
        )

    # Admin can add messages even to closed disputes (for internal notes)
    message = DisputeMessage(
        dispute_id=dispute.id,
        sender_id=current_admin.id,
        message=body.message,
        is_internal=body.is_internal,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return DisputeMessageResponse(
        id=message.id,
        dispute_id=message.dispute_id,
        sender_id=message.sender_id,
        sender_name=f"{current_admin.first_name} {current_admin.last_name}",
        message=message.message,
        is_internal=message.is_internal,
        created_at=message.created_at,
    )


@router.post("/admin/{dispute_id}/resolve", response_model=DisputeResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def resolve_dispute(
    request: Request,
    dispute_id: UUID,
    body: ResolveDisputeRequest,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """Resolve a dispute (admin only)."""
    query = (
        select(Dispute)
        .options(
            selectinload(Dispute.user),
            selectinload(Dispute.assignee),
            selectinload(Dispute.messages).selectinload(DisputeMessage.sender),
        )
        .where(Dispute.id == dispute_id)
    )
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found",
        )

    if dispute.status == DisputeStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dispute is already resolved",
        )

    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution_notes = body.resolution_notes
    dispute.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(dispute)

    logger.info(f"Dispute {dispute_id} resolved by admin {current_admin.id}")

    # TODO: Send notification to user about resolution

    return _build_dispute_response(dispute, include_internal=True)


@router.get("/admin/stats", response_model=DisputeStatsResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_dispute_stats(
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """Get dispute statistics (admin only)."""
    today = date.today()

    # Open count
    open_result = await db.execute(
        select(func.count(Dispute.id)).where(Dispute.status == DisputeStatus.OPEN)
    )
    open_count = open_result.scalar() or 0

    # In progress count
    in_progress_result = await db.execute(
        select(func.count(Dispute.id)).where(Dispute.status == DisputeStatus.IN_PROGRESS)
    )
    in_progress_count = in_progress_result.scalar() or 0

    # Resolved today
    resolved_result = await db.execute(
        select(func.count(Dispute.id)).where(
            and_(
                Dispute.status == DisputeStatus.RESOLVED,
                func.date(Dispute.resolved_at) == today,
            )
        )
    )
    resolved_today = resolved_result.scalar() or 0

    # Average resolution time (last 30 days)
    month_ago = datetime.utcnow() - timedelta(days=30)
    avg_result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', Dispute.resolved_at) -
                func.extract('epoch', Dispute.created_at)
            ) / 3600
        ).where(
            and_(
                Dispute.resolved_at.isnot(None),
                Dispute.resolved_at >= month_ago,
            )
        )
    )
    avg_hours = avg_result.scalar() or 0.0

    return DisputeStatsResponse(
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_today=resolved_today,
        avg_resolution_time_hours=round(float(avg_hours), 1),
    )
