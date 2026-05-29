"""
Soft leads routes.

Handles "Get Matched" functionality for borrowers not ready to call immediately.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentUser
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.soft_lead import SoftLead, SoftLeadStatus
from src.app.models.professional import (
    ProfessionalProfile,
    ProfessionalStatus,
    ProfessionalLanguage,
    ProfessionalServiceArea,
    Language,
    County,
)
from src.app.models.lead import Lead, LeadStatus
from src.app.services.email_service import get_email_service
import logging

logger = logging.getLogger(__name__)
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
@limiter.limit(RATE_LIMITS["api_write"])
async def get_matched(
    request: Request,
    body: GetMatchedRequest,
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
        name=body.name,
        email=body.email,
        phone=body.phone,
        loan_purpose=body.loan_purpose,
        estimated_amount=body.estimated_amount,
        property_state=body.property_state,
        preferred_language=body.preferred_language,
        timeframe=body.timeframe,
        utm_source=body.utm_source,
        utm_medium=body.utm_medium,
        utm_campaign=body.utm_campaign,
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

    # Send confirmation email to borrower
    try:
        email_service = get_email_service()
        await email_service.send_get_matched_confirmation(
            email=body.email,
            name=body.name,
        )
    except Exception as e:
        logger.error(f"Failed to send get-matched confirmation email: {e}")

    return GetMatchedResponse(
        success=True,
        message=message,
        lead_id=soft_lead.id,
    )


@router.get("/professional/pending", response_model=list[SoftLeadDetail])
@limiter.limit(RATE_LIMITS["api_read"])
async def get_pending_soft_leads(
    request: Request,
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
@limiter.limit(RATE_LIMITS["api_write"])
async def mark_soft_lead_contacted(
    request: Request,
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
@limiter.limit(RATE_LIMITS["api_write"])
async def convert_soft_lead(
    request: Request,
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

    # Language preference filtering
    # Find professionals who speak the preferred language
    if soft_lead.preferred_language:
        # Subquery to find professionals with matching language
        lang_subquery = (
            select(ProfessionalLanguage.professional_id)
            .join(Language, ProfessionalLanguage.language_id == Language.id)
            .where(Language.code == soft_lead.preferred_language)
        )
        query = query.where(ProfessionalProfile.id.in_(lang_subquery))

    # Service area filtering by state
    # Find professionals who service the borrower's state
    if soft_lead.property_state:
        # Subquery to find professionals with matching service area (by state)
        area_subquery = (
            select(ProfessionalServiceArea.professional_id)
            .join(County, ProfessionalServiceArea.county_id == County.id)
            .where(County.state_code == soft_lead.property_state.upper())
        )
        query = query.where(ProfessionalProfile.id.in_(area_subquery))

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

        # Notify professional of new matched lead
        try:
            email_service = get_email_service()
            await email_service.send_new_lead_notification(
                professional_email=best_match.user.email,
                lead_name=soft_lead.name,
                lead_email=soft_lead.email,
                lead_phone=soft_lead.phone,
                loan_purpose=soft_lead.loan_purpose,
                source="Get Matched",
                lead_id=str(soft_lead.id),
            )
        except Exception as e:
            logger.error(f"Failed to send new lead notification to professional: {e}")

        return True

    return False
