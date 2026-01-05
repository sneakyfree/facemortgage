"""
Soft leads routes.

Handles "Get Matched" functionality for borrowers not ready to call immediately.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentUser
from src.app.models.soft_lead import SoftLead, SoftLeadStatus
from src.app.models.professional import ProfessionalProfile, ProfessionalStatus
from src.app.models.lead import Lead, LeadStatus

router = APIRouter()


# ==================== Schemas ====================

class GetMatchedRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    loan_purpose: Optional[str] = None
    estimated_amount: Optional[int] = None
    property_state: Optional[str] = Field(None, max_length=2)
    preferred_language: Optional[str] = None
    timeframe: Optional[str] = None  # "immediately", "1_month", "1_3_months", etc.
    # UTM tracking
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class GetMatchedResponse(BaseModel):
    success: bool
    message: str
    lead_id: UUID


class SoftLeadDetail(BaseModel):
    id: UUID
    name: str
    email: str
    phone: Optional[str]
    loan_purpose: Optional[str]
    estimated_amount: Optional[int]
    property_state: Optional[str]
    timeframe: Optional[str]
    status: str
    matched_at: Optional[datetime]
    created_at: datetime


# ==================== Routes ====================

@router.post("/get-matched", response_model=GetMatchedResponse)
async def get_matched(
    request: GetMatchedRequest,
    db: DbSession,
):
    """
    Submit a 'Get Matched' request to be connected with a professional.

    This creates a soft lead that will be auto-matched to an available
    professional based on the borrower's preferences and the professional's
    availability/expertise.
    """
    # Create soft lead with 30-day expiration
    soft_lead = SoftLead(
        name=request.name,
        email=request.email,
        phone=request.phone,
        loan_purpose=request.loan_purpose,
        estimated_amount=request.estimated_amount,
        property_state=request.property_state,
        preferred_language=request.preferred_language,
        timeframe=request.timeframe,
        utm_source=request.utm_source,
        utm_medium=request.utm_medium,
        utm_campaign=request.utm_campaign,
        status=SoftLeadStatus.NEW,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(soft_lead)
    await db.commit()
    await db.refresh(soft_lead)

    # Auto-match to best available professional
    matched = await _auto_match_soft_lead(db, soft_lead)

    if matched:
        message = "We've matched you with a qualified professional! They'll reach out within 24 hours."
    else:
        message = "We've received your request! A professional will reach out within 24 hours."

    # TODO: Send confirmation email
    # send_get_matched_confirmation.delay(email=request.email, name=request.name)

    return GetMatchedResponse(
        success=True,
        message=message,
        lead_id=soft_lead.id,
    )


@router.get("/professional/pending", response_model=list[SoftLeadDetail])
async def get_pending_soft_leads(
    current_user: CurrentUser,
    db: DbSession,
):
    """Get soft leads matched to the current professional."""
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

    # Get matched soft leads
    query = (
        select(SoftLead)
        .where(
            SoftLead.matched_professional_id == professional.id,
            SoftLead.status.in_([SoftLeadStatus.MATCHED, SoftLeadStatus.CONTACTED]),
        )
        .order_by(SoftLead.created_at.desc())
        .limit(100)
    )
    result = await db.execute(query)
    soft_leads = result.scalars().all()

    return [
        SoftLeadDetail(
            id=sl.id,
            name=sl.name,
            email=sl.email,
            phone=sl.phone,
            loan_purpose=sl.loan_purpose,
            estimated_amount=sl.estimated_amount,
            property_state=sl.property_state,
            timeframe=sl.timeframe,
            status=sl.status.value,
            matched_at=sl.matched_at,
            created_at=sl.created_at,
        )
        for sl in soft_leads
    ]


@router.post("/{soft_lead_id}/contact")
async def mark_soft_lead_contacted(
    soft_lead_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Mark a soft lead as contacted by the professional."""
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

    # Get soft lead
    soft_lead = await db.get(SoftLead, soft_lead_id)
    if not soft_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soft lead not found",
        )

    # Verify ownership
    if soft_lead.matched_professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this lead",
        )

    # Update status
    soft_lead.status = SoftLeadStatus.CONTACTED
    await db.commit()

    return {"message": "Lead marked as contacted", "status": "contacted"}


@router.post("/{soft_lead_id}/convert")
async def convert_soft_lead(
    soft_lead_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Convert a soft lead to a full lead.

    This creates a Lead record for tracking through the sales pipeline.
    """
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

    # Get soft lead
    soft_lead = await db.get(SoftLead, soft_lead_id)
    if not soft_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soft lead not found",
        )

    # Verify ownership
    if soft_lead.matched_professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to convert this lead",
        )

    # Check if already converted
    if soft_lead.status == SoftLeadStatus.CONVERTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead already converted",
        )

    # Create full lead
    lead = Lead(
        professional_id=professional.id,
        borrower_id=None,  # Soft leads don't have authenticated borrowers
        contact_name=soft_lead.name,
        contact_email=soft_lead.email,
        contact_phone=soft_lead.phone,
        loan_purpose=soft_lead.loan_purpose,
        estimated_loan_amount=soft_lead.estimated_amount,
        lead_status=LeadStatus.QUALIFIED,
        utm_source=soft_lead.utm_source or "get_matched",
        utm_medium=soft_lead.utm_medium,
        utm_campaign=soft_lead.utm_campaign,
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    # Update soft lead
    soft_lead.status = SoftLeadStatus.CONVERTED
    soft_lead.converted_lead_id = lead.id
    await db.commit()

    return {
        "message": "Soft lead converted to full lead",
        "lead_id": str(lead.id),
    }


# ==================== Helper Functions ====================

async def _auto_match_soft_lead(db: DbSession, soft_lead: SoftLead) -> bool:
    """
    Auto-match a soft lead to the best available professional.

    Matching criteria:
    1. Professional is active and accepting leads
    2. Language preference match (if specified)
    3. Service area match (if state specified)
    4. Highest rated within matches

    Returns True if matched, False otherwise.
    """
    # Build query for eligible professionals
    query = (
        select(ProfessionalProfile)
        .options(selectinload(ProfessionalProfile.user))
        .where(
            ProfessionalProfile.status.in_([
                ProfessionalStatus.ONLINE_AVAILABLE,
                ProfessionalStatus.ONLINE_BUSY,
                ProfessionalStatus.AWAY,
            ])
        )
    )

    # TODO: Add language filtering when languages are properly set up
    # TODO: Add service area filtering when areas are properly set up

    # Order by rating (best first)
    query = query.order_by(
        ProfessionalProfile.avg_rating.desc().nullslast(),
        ProfessionalProfile.total_reviews.desc().nullslast(),
    ).limit(1)

    result = await db.execute(query)
    best_match = result.scalar_one_or_none()

    if best_match:
        soft_lead.matched_professional_id = best_match.id
        soft_lead.matched_at = datetime.utcnow()
        soft_lead.status = SoftLeadStatus.MATCHED
        await db.commit()

        # TODO: Notify professional of new matched lead
        # send_new_soft_lead_notification.delay(
        #     professional_email=best_match.user.email,
        #     lead_name=soft_lead.name,
        # )

        return True

    return False
