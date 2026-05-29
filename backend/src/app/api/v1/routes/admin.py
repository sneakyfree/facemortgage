"""
Admin API routes for platform management.

Requires admin role for access.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.app.core.auth import get_current_user
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.core.database import get_db
from src.app.models.user import User, UserType
from src.app.models.professional import ProfessionalProfile, ProfessionalStatus
from src.app.models.call import VideoCall, CallStatus
from src.app.models.lead import Lead, LeadStatus
from src.app.models.billing import Subscription, SubscriptionStatus, SubscriptionPlan

router = APIRouter()


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role."""
    # Check if user has admin flag (you'd add this to User model)
    if not getattr(user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


class PlatformStats(BaseModel):
    """Platform-wide statistics."""
    # Users
    total_users: int = 0
    total_professionals: int = 0
    total_borrowers: int = 0
    new_users_today: int = 0
    new_users_this_week: int = 0

    # Activity
    professionals_online: int = 0
    professionals_in_call: int = 0
    calls_today: int = 0
    calls_this_week: int = 0
    avg_call_duration: float = 0.0

    # Leads
    leads_today: int = 0
    leads_this_week: int = 0
    conversion_rate: float = 0.0

    # Revenue
    active_subscriptions: int = 0
    mrr: float = 0.0  # Monthly recurring revenue


class UserListItem(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    user_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserListItem]
    total: int
    page: int
    page_size: int


class ProfessionalListItem(BaseModel):
    id: str
    user_id: str
    name: str
    email: str
    company: Optional[str] = None
    nmls_id: Optional[str] = None
    status: str
    subscription_tier: str
    avg_rating: float
    total_calls: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProfessionalListResponse(BaseModel):
    professionals: list[ProfessionalListItem]
    total: int
    page: int
    page_size: int


@router.get("/stats", response_model=PlatformStats)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_platform_stats(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get platform-wide statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    # User counts
    total_users = (await db.execute(
        select(func.count()).where(User.is_active == True)
    )).scalar() or 0

    professional_types = [UserType.LOAN_OFFICER, UserType.REALTOR, UserType.TITLE_REP, UserType.ATTORNEY]
    total_professionals = (await db.execute(
        select(func.count())
        .where(User.is_active == True)
        .where(User.user_type.in_(professional_types))
    )).scalar() or 0

    total_borrowers = (await db.execute(
        select(func.count())
        .where(User.is_active == True)
        .where(User.user_type == UserType.BORROWER)
    )).scalar() or 0

    new_users_today = (await db.execute(
        select(func.count())
        .where(User.created_at >= today_start)
    )).scalar() or 0

    new_users_week = (await db.execute(
        select(func.count())
        .where(User.created_at >= week_start)
    )).scalar() or 0

    # Professional status
    professionals_online = (await db.execute(
        select(func.count())
        .where(ProfessionalProfile.status == ProfessionalStatus.ONLINE_AVAILABLE)
    )).scalar() or 0

    professionals_in_call = (await db.execute(
        select(func.count())
        .where(ProfessionalProfile.status == ProfessionalStatus.IN_CALL)
    )).scalar() or 0

    # Calls
    calls_today = (await db.execute(
        select(func.count())
        .where(VideoCall.initiated_at >= today_start)
    )).scalar() or 0

    calls_week = (await db.execute(
        select(func.count())
        .where(VideoCall.initiated_at >= week_start)
    )).scalar() or 0

    avg_duration = (await db.execute(
        select(func.avg(VideoCall.duration_seconds))
        .where(VideoCall.status == CallStatus.COMPLETED)
        .where(VideoCall.initiated_at >= week_start)
    )).scalar() or 0

    # Leads
    leads_today = (await db.execute(
        select(func.count())
        .where(Lead.created_at >= today_start)
    )).scalar() or 0

    leads_week = (await db.execute(
        select(func.count())
        .where(Lead.created_at >= week_start)
    )).scalar() or 0

    total_leads = (await db.execute(
        select(func.count()).select_from(Lead)
    )).scalar() or 0

    won_leads = (await db.execute(
        select(func.count())
        .where(Lead.lead_status == LeadStatus.WON.value)
    )).scalar() or 0

    conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0

    # Subscriptions and MRR calculation
    active_subs = (await db.execute(
        select(func.count())
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
    )).scalar() or 0

    # Calculate MRR by summing monthly prices of active subscriptions
    mrr_result = (await db.execute(
        select(func.coalesce(func.sum(SubscriptionPlan.monthly_price), 0))
        .select_from(Subscription)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
        .where(Subscription.plan_id.isnot(None))
    )).scalar() or 0

    return PlatformStats(
        total_users=total_users,
        total_professionals=total_professionals,
        total_borrowers=total_borrowers,
        new_users_today=new_users_today,
        new_users_this_week=new_users_week,
        professionals_online=professionals_online,
        professionals_in_call=professionals_in_call,
        calls_today=calls_today,
        calls_this_week=calls_week,
        avg_call_duration=float(avg_duration or 0),
        leads_today=leads_today,
        leads_this_week=leads_week,
        conversion_rate=round(conversion_rate, 1),
        active_subscriptions=active_subs,
        mrr=float(mrr_result),
    )


@router.get("/users", response_model=UserListResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def list_users(
    request: Request,
    search: Optional[str] = None,
    user_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with filtering."""
    query = select(User)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term))
        )

    if user_type:
        query = query.where(User.user_type == user_type)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        users=[
            UserListItem(
                id=str(u.id),
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                user_type=u.user_type.value if u.user_type else "unknown",
                is_active=u.is_active,
                created_at=u.created_at,
            )
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/professionals", response_model=ProfessionalListResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def list_professionals(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all professionals with filtering."""
    query = select(ProfessionalProfile, User).join(User)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term)) |
            (ProfessionalProfile.company_name.ilike(search_term)) |
            (ProfessionalProfile.nmls_id.ilike(search_term))
        )

    if status:
        query = query.where(ProfessionalProfile.status == status)

    if tier:
        query = query.where(ProfessionalProfile.subscription_tier == tier)

    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(ProfessionalProfile.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    professionals = []
    for profile, user in rows:
        professionals.append(ProfessionalListItem(
            id=str(profile.id),
            user_id=str(user.id),
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
            company=profile.company_name,
            nmls_id=profile.nmls_id,
            status=profile.status.value if profile.status else "offline",
            subscription_tier=profile.subscription_tier.value if profile.subscription_tier else "free",
            avg_rating=float(profile.avg_rating) if profile.avg_rating else 0.0,
            total_calls=profile.total_calls_completed or 0,
            created_at=profile.created_at,
        ))

    return ProfessionalListResponse(
        professionals=professionals,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{user_id}/status")
@limiter.limit(RATE_LIMITS["api_write"])
async def toggle_user_status(
    request: Request,
    user_id: str,
    is_active: bool,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a user."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = is_active
    await db.commit()

    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}


@router.patch("/professionals/{professional_id}/featured")
@limiter.limit(RATE_LIMITS["api_write"])
async def toggle_featured(
    request: Request,
    professional_id: str,
    is_featured: bool,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Toggle featured status for a professional."""
    result = await db.execute(
        select(ProfessionalProfile).where(ProfessionalProfile.id == uuid.UUID(professional_id))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")

    profile.is_featured = is_featured
    await db.commit()

    return {"message": f"Professional {'featured' if is_featured else 'unfeatured'} successfully"}
