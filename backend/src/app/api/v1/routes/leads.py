"""
API routes for lead management.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.auth import get_current_user
from src.app.core.database import get_db
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.user import User
from src.app.models.lead import Lead, LeadActivity, LeadStatus as LeadStatusModel
from src.app.models.professional import ProfessionalProfile
from src.app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadListItem,
    LeadListResponse,
    LeadActivityCreate,
    LeadActivityResponse,
    LeadStats,
    LeadStatus,
    BorrowerInfo,
    SourceCallInfo,
)

router = APIRouter()


async def get_professional_profile(user: User, db: AsyncSession) -> ProfessionalProfile:
    """Get the professional profile for the current user."""
    result = await db.execute(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Professional profile not found")
    return profile


@router.get("", response_model=LeadListResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def list_leads(
    request: Request,
    status: Optional[LeadStatus] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|estimated_loan_amount|next_followup_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List leads for the current professional."""
    profile = await get_professional_profile(user, db)

    # Build query
    query = select(Lead).where(Lead.professional_id == profile.id)

    # Filter by status
    if status:
        query = query.where(Lead.lead_status == status.value)

    # Search by contact info
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Lead.contact_name.ilike(search_term),
                Lead.contact_email.ilike(search_term),
                Lead.contact_phone.ilike(search_term),
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    sort_column = getattr(Lead, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute
    result = await db.execute(query.options(selectinload(Lead.activities)))
    leads = result.scalars().all()

    # Transform to list items
    lead_items = []
    for lead in leads:
        last_activity_at = None
        if lead.activities:
            last_activity_at = max(a.created_at for a in lead.activities)

        lead_items.append(LeadListItem(
            id=str(lead.id),
            lead_status=LeadStatus(lead.lead_status) if isinstance(lead.lead_status, str) else LeadStatus(lead.lead_status.value),
            contact_name=lead.contact_name,
            contact_email=lead.contact_email,
            contact_phone=lead.contact_phone,
            loan_purpose=lead.loan_purpose,
            estimated_loan_amount=lead.estimated_loan_amount,
            next_followup_at=lead.next_followup_at,
            estimated_value=lead.estimated_value,
            last_activity_at=last_activity_at,
            activity_count=len(lead.activities),
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        ))

    total_pages = (total + page_size - 1) // page_size

    return LeadListResponse(
        leads=lead_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=LeadStats)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_lead_stats(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get lead statistics for dashboard."""
    profile = await get_professional_profile(user, db)

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    # Total leads
    total_result = await db.execute(
        select(func.count()).where(Lead.professional_id == profile.id)
    )
    total_leads = total_result.scalar() or 0

    # Leads by status
    status_result = await db.execute(
        select(Lead.lead_status, func.count())
        .where(Lead.professional_id == profile.id)
        .group_by(Lead.lead_status)
    )
    leads_by_status = {str(row[0].value if hasattr(row[0], 'value') else row[0]): row[1] for row in status_result.all()}

    # New leads today
    today_result = await db.execute(
        select(func.count())
        .where(Lead.professional_id == profile.id)
        .where(Lead.created_at >= today_start)
    )
    new_leads_today = today_result.scalar() or 0

    # New leads this week
    week_result = await db.execute(
        select(func.count())
        .where(Lead.professional_id == profile.id)
        .where(Lead.created_at >= week_start)
    )
    new_leads_this_week = week_result.scalar() or 0

    # New leads this month
    month_result = await db.execute(
        select(func.count())
        .where(Lead.professional_id == profile.id)
        .where(Lead.created_at >= month_start)
    )
    new_leads_this_month = month_result.scalar() or 0

    # Conversion rate
    won_leads = leads_by_status.get("won", 0)
    conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0

    # Total value won
    won_value_result = await db.execute(
        select(func.coalesce(func.sum(Lead.actual_value), 0))
        .where(Lead.professional_id == profile.id)
        .where(Lead.lead_status == LeadStatusModel.WON.value)
    )
    total_value_won = won_value_result.scalar() or 0

    # Pipeline value (non-closed leads)
    pipeline_statuses = [
        LeadStatusModel.NEW.value,
        LeadStatusModel.CONTACTED.value,
        LeadStatusModel.QUALIFIED.value,
        LeadStatusModel.PROPOSAL_SENT.value,
        LeadStatusModel.NEGOTIATION.value,
    ]
    pipeline_result = await db.execute(
        select(func.coalesce(func.sum(Lead.estimated_value), 0))
        .where(Lead.professional_id == profile.id)
        .where(Lead.lead_status.in_(pipeline_statuses))
    )
    total_value_pipeline = pipeline_result.scalar() or 0

    # Leads needing followup
    followup_result = await db.execute(
        select(func.count())
        .where(Lead.professional_id == profile.id)
        .where(Lead.next_followup_at <= now)
        .where(Lead.lead_status.notin_([LeadStatusModel.WON.value, LeadStatusModel.LOST.value]))
    )
    leads_needing_followup = followup_result.scalar() or 0

    return LeadStats(
        total_leads=total_leads,
        leads_by_status=leads_by_status,
        new_leads_today=new_leads_today,
        new_leads_this_week=new_leads_this_week,
        new_leads_this_month=new_leads_this_month,
        conversion_rate=round(conversion_rate, 1),
        total_value_won=total_value_won,
        total_value_pipeline=total_value_pipeline,
        leads_needing_followup=leads_needing_followup,
    )


@router.post("", response_model=LeadResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def create_lead(
    request: Request,
    data: LeadCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new lead."""
    profile = await get_professional_profile(user, db)

    lead = Lead(
        professional_id=profile.id,
        borrower_id=uuid.UUID(data.borrower_id) if data.borrower_id else None,
        source_call_id=uuid.UUID(data.source_call_id) if data.source_call_id else None,
        lead_status=LeadStatusModel.NEW,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        loan_purpose=data.loan_purpose,
        property_address=data.property_address,
        estimated_property_value=data.estimated_property_value,
        estimated_loan_amount=data.estimated_loan_amount,
        notes=data.notes,
        utm_source=data.utm_source,
        utm_medium=data.utm_medium,
        utm_campaign=data.utm_campaign,
    )

    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    return await _build_lead_response(lead, db)


@router.get("/{lead_id}", response_model=LeadResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_lead(
    request: Request,
    lead_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific lead."""
    profile = await get_professional_profile(user, db)

    result = await db.execute(
        select(Lead)
        .where(Lead.id == uuid.UUID(lead_id))
        .where(Lead.professional_id == profile.id)
        .options(selectinload(Lead.activities), selectinload(Lead.borrower), selectinload(Lead.source_call))
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return await _build_lead_response(lead, db)


@router.patch("/{lead_id}", response_model=LeadResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def update_lead(
    request: Request,
    lead_id: str,
    data: LeadUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a lead."""
    profile = await get_professional_profile(user, db)

    result = await db.execute(
        select(Lead)
        .where(Lead.id == uuid.UUID(lead_id))
        .where(Lead.professional_id == profile.id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Track status change for activity
    old_status = lead.lead_status

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "lead_status" and value:
            setattr(lead, field, LeadStatusModel(value))
        else:
            setattr(lead, field, value)

    # If status changed, add activity
    if data.lead_status and old_status != data.lead_status.value:
        activity = LeadActivity(
            lead_id=lead.id,
            activity_type="status_change",
            description=f"Status changed from {old_status} to {data.lead_status.value}",
            performed_by=user.id,
            metadata={"old_status": old_status, "new_status": data.lead_status.value},
        )
        db.add(activity)

    await db.commit()
    await db.refresh(lead)

    return await _build_lead_response(lead, db)


@router.delete("/{lead_id}")
@limiter.limit(RATE_LIMITS["api_write"])
async def delete_lead(
    request: Request,
    lead_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a lead."""
    profile = await get_professional_profile(user, db)

    result = await db.execute(
        select(Lead)
        .where(Lead.id == uuid.UUID(lead_id))
        .where(Lead.professional_id == profile.id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    await db.delete(lead)
    await db.commit()

    return {"message": "Lead deleted successfully"}


@router.post("/{lead_id}/activities", response_model=LeadActivityResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def add_lead_activity(
    request: Request,
    lead_id: str,
    data: LeadActivityCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an activity to a lead."""
    profile = await get_professional_profile(user, db)

    result = await db.execute(
        select(Lead)
        .where(Lead.id == uuid.UUID(lead_id))
        .where(Lead.professional_id == profile.id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    activity = LeadActivity(
        lead_id=lead.id,
        activity_type=data.activity_type.value,
        description=data.description,
        metadata=data.metadata,
        performed_by=user.id,
    )

    # Update last contact
    if data.activity_type.value in ["call", "email", "meeting"]:
        lead.last_contact_at = datetime.utcnow()

    db.add(activity)
    await db.commit()
    await db.refresh(activity)

    return LeadActivityResponse(
        id=str(activity.id),
        lead_id=str(activity.lead_id),
        activity_type=activity.activity_type,
        description=activity.description,
        metadata=activity.metadata,
        performed_by=str(activity.performed_by) if activity.performed_by else None,
        created_at=activity.created_at,
    )


@router.get("/{lead_id}/activities", response_model=list[LeadActivityResponse])
@limiter.limit(RATE_LIMITS["api_read"])
async def get_lead_activities(
    request: Request,
    lead_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all activities for a lead."""
    profile = await get_professional_profile(user, db)

    result = await db.execute(
        select(Lead)
        .where(Lead.id == uuid.UUID(lead_id))
        .where(Lead.professional_id == profile.id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    activities_result = await db.execute(
        select(LeadActivity)
        .where(LeadActivity.lead_id == lead.id)
        .order_by(LeadActivity.created_at.desc())
    )
    activities = activities_result.scalars().all()

    return [
        LeadActivityResponse(
            id=str(a.id),
            lead_id=str(a.lead_id),
            activity_type=a.activity_type,
            description=a.description,
            metadata=a.metadata,
            performed_by=str(a.performed_by) if a.performed_by else None,
            created_at=a.created_at,
        )
        for a in activities
    ]


async def _build_lead_response(lead: Lead, db: AsyncSession) -> LeadResponse:
    """Build a full lead response."""
    # Load relationships if not already loaded
    if not hasattr(lead, '_activities_loaded'):
        await db.refresh(lead, ["activities", "borrower", "source_call"])

    borrower_info = None
    if lead.borrower:
        borrower_info = BorrowerInfo(
            id=str(lead.borrower.id),
            first_name=lead.borrower.first_name,
            last_name=lead.borrower.last_name,
            email=lead.borrower.email,
            phone=lead.borrower.phone,
            avatar_url=lead.borrower.avatar_url,
        )

    source_call_info = None
    if lead.source_call:
        source_call_info = SourceCallInfo(
            id=str(lead.source_call.id),
            initiated_at=lead.source_call.initiated_at,
            duration_seconds=lead.source_call.duration_seconds,
            rating=None,  # Would need to join with review
        )

    activities = [
        LeadActivityResponse(
            id=str(a.id),
            lead_id=str(a.lead_id),
            activity_type=a.activity_type,
            description=a.description,
            metadata=a.metadata,
            performed_by=str(a.performed_by) if a.performed_by else None,
            created_at=a.created_at,
        )
        for a in (lead.activities or [])
    ]

    lead_status_value = lead.lead_status.value if hasattr(lead.lead_status, 'value') else lead.lead_status

    return LeadResponse(
        id=str(lead.id),
        professional_id=str(lead.professional_id),
        lead_status=LeadStatus(lead_status_value),
        borrower=borrower_info,
        source_call=source_call_info,
        contact_name=lead.contact_name,
        contact_email=lead.contact_email,
        contact_phone=lead.contact_phone,
        loan_purpose=lead.loan_purpose,
        property_address=lead.property_address,
        estimated_property_value=lead.estimated_property_value,
        estimated_loan_amount=lead.estimated_loan_amount,
        last_contact_at=lead.last_contact_at,
        next_followup_at=lead.next_followup_at,
        notes=lead.notes,
        utm_source=lead.utm_source,
        utm_medium=lead.utm_medium,
        utm_campaign=lead.utm_campaign,
        estimated_value=lead.estimated_value,
        actual_value=lead.actual_value,
        activities=activities,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )
