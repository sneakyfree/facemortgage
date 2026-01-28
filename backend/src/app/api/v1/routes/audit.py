"""
Audit Log API routes.

Provides admin endpoints for viewing system audit logs.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentAdmin
from src.app.models.audit import AuditLog, AuditEventType

router = APIRouter()
logger = logging.getLogger(__name__)


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: UUID
    user_id: Optional[UUID]
    user_email: Optional[str]
    user_name: Optional[str]
    event_type: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    description: str
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated audit log list."""
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    db: DbSession,
    current_admin: CurrentAdmin,
    event_type: Optional[AuditEventType] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """
    List audit logs with filtering (admin only).
    
    Supports filtering by event type, user, date range, and search.
    """
    offset = (page - 1) * page_size

    # Build query
    query = select(AuditLog)
    
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    if search:
        query = query.where(AuditLog.description.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get logs
    query = (
        query
        .options(selectinload(AuditLog.user))
        .order_by(desc(AuditLog.created_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    items = []
    for log in logs:
        user_email = None
        user_name = None
        if log.user:
            user_email = log.user.email
            user_name = f"{log.user.first_name} {log.user.last_name}"
        
        items.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_email=user_email,
            user_name=user_name,
            event_type=log.event_type.value,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            description=log.description,
            ip_address=log.ip_address,
            created_at=log.created_at,
        ))

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


class AuditStatsResponse(BaseModel):
    """Audit log statistics."""
    total_events_today: int
    login_events_today: int
    admin_actions_today: int
    failed_logins_today: int


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """Get audit log statistics (admin only)."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Total events today
    total_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= today_start)
    )
    total_events = total_result.scalar() or 0

    # Login events
    login_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= today_start,
            AuditLog.event_type == AuditEventType.LOGIN,
        )
    )
    logins = login_result.scalar() or 0

    # Admin actions
    admin_types = [
        AuditEventType.ADMIN_USER_STATUS_CHANGE,
        AuditEventType.ADMIN_VIDEO_APPROVED,
        AuditEventType.ADMIN_VIDEO_REJECTED,
        AuditEventType.ADMIN_DISPUTE_RESOLVED,
    ]
    admin_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= today_start,
            AuditLog.event_type.in_(admin_types),
        )
    )
    admin_actions = admin_result.scalar() or 0

    # Failed logins
    failed_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= today_start,
            AuditLog.event_type == AuditEventType.LOGIN_FAILED,
        )
    )
    failed_logins = failed_result.scalar() or 0

    return AuditStatsResponse(
        total_events_today=total_events,
        login_events_today=logins,
        admin_actions_today=admin_actions,
        failed_logins_today=failed_logins,
    )
