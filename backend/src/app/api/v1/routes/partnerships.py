"""
Partnership routes for the Realtor Partnership Module.

Handles LO-Realtor partnerships, referral tracking, and widget management.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentUser
from src.app.models.partnership import Partnership, PartnershipStatus, PartnershipTier, PartnershipReferral
from src.app.models.professional import ProfessionalProfile
from src.app.models.user import UserType
from src.app.models.lead import Lead, LeadStatus, LeadActivity
from src.app.services.email_service import get_email_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Schemas ====================

class InvitePartnerRequest(BaseModel):
    realtor_name: str = Field(..., min_length=1, max_length=100)
    realtor_email: EmailStr
    realtor_phone: Optional[str] = Field(None, max_length=20)
    realtor_company: Optional[str] = Field(None, max_length=200)


class InvitePartnerResponse(BaseModel):
    partnership_id: UUID
    invitation_sent: bool


class AcceptPartnershipRequest(BaseModel):
    """Used when realtor accepts partnership invitation."""
    pass  # Token comes from URL


class PartnershipDetail(BaseModel):
    id: UUID
    status: str
    tier: str
    loan_officer_name: Optional[str] = None
    loan_officer_company: Optional[str] = None
    realtor_name: Optional[str] = None
    realtor_email: Optional[str] = None
    referral_count: int = 0
    created_at: datetime
    accepted_at: Optional[datetime] = None


class SubmitReferralRequest(BaseModel):
    borrower_name: str = Field(..., min_length=1, max_length=100)
    borrower_email: EmailStr
    borrower_phone: Optional[str] = Field(None, max_length=20)
    property_address: Optional[str] = None
    loan_purpose: Optional[str] = None
    estimated_amount: Optional[int] = None
    notes: Optional[str] = None


class ReferralDetail(BaseModel):
    id: UUID
    borrower_name: str
    borrower_email: str
    borrower_phone: Optional[str]
    property_address: Optional[str]
    loan_purpose: Optional[str]
    status: str
    source: str
    created_at: datetime


# ==================== Loan Officer Endpoints ====================

@router.post("/invite", response_model=InvitePartnerResponse)
async def invite_partner(
    request: InvitePartnerRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Loan officer invites a realtor to form a partnership.

    Creates a partnership in PENDING status and sends invitation email.
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

    # Verify user is a loan officer
    if current_user.user_type != UserType.LOAN_OFFICER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only loan officers can invite partners",
        )

    # Check if partnership already exists with this email
    existing = await db.execute(
        select(Partnership).where(
            Partnership.loan_officer_id == professional.id,
            Partnership.external_realtor_email == request.realtor_email,
            Partnership.status.in_([PartnershipStatus.PENDING, PartnershipStatus.ACTIVE]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Partnership with this realtor already exists",
        )

    # Create partnership
    partnership = Partnership(
        loan_officer_id=professional.id,
        external_realtor_name=request.realtor_name,
        external_realtor_email=request.realtor_email,
        external_realtor_phone=request.realtor_phone,
        external_realtor_company=request.realtor_company,
        status=PartnershipStatus.PENDING,
        tier=PartnershipTier.BASIC,
    )
    partnership.generate_invitation_token()

    db.add(partnership)
    await db.commit()
    await db.refresh(partnership)

    # Send invitation email
    invitation_sent = False
    try:
        email_service = get_email_service()
        invitation_sent = await email_service.send_partnership_invitation(
            realtor_email=request.realtor_email,
            realtor_name=request.realtor_name,
            lo_name=f"{current_user.first_name} {current_user.last_name}",
            lo_company=professional.company_name or "FaceMortgage",
            invitation_token=partnership.invitation_token,
        )
    except Exception as e:
        logger.error(f"Failed to send partnership invitation email: {e}")

    return InvitePartnerResponse(
        partnership_id=partnership.id,
        invitation_sent=invitation_sent,
    )


@router.get("/my-partnerships", response_model=List[PartnershipDetail])
async def get_my_partnerships(
    current_user: CurrentUser,
    db: DbSession,
):
    """Get all partnerships for the current professional."""
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_user.id
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        return []

    # Get partnerships based on user type
    if current_user.user_type == UserType.LOAN_OFFICER:
        query = (
            select(Partnership)
            .options(
                selectinload(Partnership.loan_officer).selectinload(ProfessionalProfile.user),
                selectinload(Partnership.referrals),
            )
            .where(Partnership.loan_officer_id == professional.id)
            .order_by(Partnership.created_at.desc())
        )
    elif current_user.user_type == UserType.REALTOR:
        query = (
            select(Partnership)
            .options(
                selectinload(Partnership.loan_officer).selectinload(ProfessionalProfile.user),
                selectinload(Partnership.referrals),
            )
            .where(Partnership.realtor_id == professional.id)
            .order_by(Partnership.created_at.desc())
        )
    else:
        return []

    result = await db.execute(query)
    partnerships = result.scalars().all()

    return [
        PartnershipDetail(
            id=p.id,
            status=p.status.value,
            tier=p.tier.value,
            loan_officer_name=f"{p.loan_officer.user.first_name} {p.loan_officer.user.last_name}" if p.loan_officer else None,
            loan_officer_company=p.loan_officer.company_name if p.loan_officer else None,
            realtor_name=p.external_realtor_name or (f"{p.realtor.user.first_name} {p.realtor.user.last_name}" if p.realtor else None),
            realtor_email=p.external_realtor_email or (p.realtor.user.email if p.realtor else None),
            referral_count=len(p.referrals),
            created_at=p.created_at,
            accepted_at=p.accepted_at,
        )
        for p in partnerships
    ]


@router.get("/{partnership_id}/referrals", response_model=List[ReferralDetail])
async def get_partnership_referrals(
    partnership_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get all referrals for a specific partnership."""
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

    # Get partnership with referrals
    query = (
        select(Partnership)
        .options(selectinload(Partnership.referrals))
        .where(Partnership.id == partnership_id)
    )
    result = await db.execute(query)
    partnership = result.scalar_one_or_none()

    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partnership not found",
        )

    # Verify access
    if (partnership.loan_officer_id != professional.id and
        partnership.realtor_id != professional.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this partnership",
        )

    return [
        ReferralDetail(
            id=r.id,
            borrower_name=r.borrower_name,
            borrower_email=r.borrower_email,
            borrower_phone=r.borrower_phone,
            property_address=r.property_address,
            loan_purpose=r.loan_purpose,
            status=r.status,
            source=r.source,
            created_at=r.created_at,
        )
        for r in partnership.referrals
    ]


# ==================== Realtor/Partner Endpoints ====================

@router.post("/accept/{token}")
async def accept_partnership(
    token: str,
    db: DbSession,
):
    """
    Realtor accepts a partnership invitation via token.

    This can be called without authentication - the token provides validation.
    """
    # Find partnership by token
    query = select(Partnership).where(Partnership.invitation_token == token)
    result = await db.execute(query)
    partnership = result.scalar_one_or_none()

    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation",
        )

    if partnership.status != PartnershipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already processed",
        )

    # Activate partnership
    partnership.status = PartnershipStatus.ACTIVE
    partnership.accepted_at = datetime.utcnow()
    partnership.generate_widget_token()

    await db.commit()

    return {
        "success": True,
        "partnership_id": str(partnership.id),
        "message": "Partnership activated successfully",
    }


@router.post("/{partnership_id}/refer", response_model=ReferralDetail)
async def submit_referral(
    partnership_id: UUID,
    request: SubmitReferralRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Realtor submits a referral through the partnership.

    Creates a referral and automatically creates a lead for the loan officer.
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

    # Get partnership
    partnership = await db.get(Partnership, partnership_id)
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partnership not found",
        )

    if partnership.status != PartnershipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Partnership is not active",
        )

    # Verify the user is the realtor in this partnership
    if partnership.realtor_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit referrals for this partnership",
        )

    # Create referral
    referral = PartnershipReferral(
        partnership_id=partnership_id,
        borrower_name=request.borrower_name,
        borrower_email=request.borrower_email,
        borrower_phone=request.borrower_phone,
        property_address=request.property_address,
        loan_purpose=request.loan_purpose,
        estimated_amount=request.estimated_amount,
        notes=request.notes,
        source="manual",
        status="new",
    )
    db.add(referral)

    # Create lead for loan officer
    lead = Lead(
        professional_id=partnership.loan_officer_id,
        borrower_id=None,  # Partner referral
        contact_name=request.borrower_name,
        contact_email=request.borrower_email,
        contact_phone=request.borrower_phone,
        property_address=request.property_address,
        loan_purpose=request.loan_purpose,
        estimated_loan_amount=request.estimated_amount,
        notes=request.notes,
        lead_status=LeadStatus.NEW,
        utm_source="partnership",
        utm_medium="realtor_referral",
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    await db.refresh(referral)

    # Link referral to lead
    referral.converted_to_lead_id = lead.id
    await db.commit()

    # Add activity to lead
    activity = LeadActivity(
        lead_id=lead.id,
        activity_type="referral_received",
        description=f"Referred by partner: {professional.user.first_name} {professional.user.last_name}",
        metadata={"partnership_id": str(partnership_id), "referral_id": str(referral.id)},
    )
    db.add(activity)
    await db.commit()

    # Notify loan officer of new referral
    try:
        # Get loan officer's profile and email
        lo_query = (
            select(ProfessionalProfile)
            .options(selectinload(ProfessionalProfile.user))
            .where(ProfessionalProfile.id == partnership.loan_officer_id)
        )
        lo_result = await db.execute(lo_query)
        loan_officer = lo_result.scalar_one_or_none()

        if loan_officer:
            email_service = get_email_service()
            await email_service.send_new_referral_notification(
                professional_email=loan_officer.user.email,
                realtor_name=f"{professional.user.first_name} {professional.user.last_name}",
                borrower_name=request.borrower_name,
                borrower_email=request.borrower_email,
                borrower_phone=request.borrower_phone,
                property_address=request.property_address,
                lead_id=str(lead.id),
            )
    except Exception as e:
        logger.error(f"Failed to send referral notification email: {e}")

    return ReferralDetail(
        id=referral.id,
        borrower_name=referral.borrower_name,
        borrower_email=referral.borrower_email,
        borrower_phone=referral.borrower_phone,
        property_address=referral.property_address,
        loan_purpose=referral.loan_purpose,
        status=referral.status,
        source=referral.source,
        created_at=referral.created_at,
    )


@router.post("/{partnership_id}/terminate")
async def terminate_partnership(
    partnership_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Terminate a partnership (either party can do this).
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

    # Get partnership
    partnership = await db.get(Partnership, partnership_id)
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partnership not found",
        )

    # Verify access
    if (partnership.loan_officer_id != professional.id and
        partnership.realtor_id != professional.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to terminate this partnership",
        )

    # Terminate
    partnership.status = PartnershipStatus.TERMINATED
    partnership.terminated_at = datetime.utcnow()
    partnership.widget_enabled = False

    await db.commit()

    return {"message": "Partnership terminated", "status": "terminated"}


# ==================== Widget Endpoints ====================

@router.get("/{partnership_id}/widget-code")
async def get_widget_embed_code(
    partnership_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get the embed code for the partnership widget."""
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

    # Get partnership
    partnership = await db.get(Partnership, partnership_id)
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partnership not found",
        )

    # Verify access
    if (partnership.loan_officer_id != professional.id and
        partnership.realtor_id != professional.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this widget",
        )

    if not partnership.widget_token:
        partnership.generate_widget_token()
        await db.commit()

    # Generate embed code
    embed_code = f"""<script src="https://facemortgage.com/widget/fm-widget.js"></script>
<script>
  new FMWidget({{
    partnerToken: '{partnership.widget_token}',
    loanOfficerId: '{partnership.loan_officer_id}',
    buttonText: 'Get Pre-Approved',
  }}).init();
</script>"""

    return {
        "widget_token": partnership.widget_token,
        "embed_code": embed_code,
    }


@router.post("/{partnership_id}/widget/enable")
async def enable_widget(
    partnership_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Enable the widget for embedding."""
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

    # Get partnership
    partnership = await db.get(Partnership, partnership_id)
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partnership not found",
        )

    # Only loan officer can enable widget
    if partnership.loan_officer_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the loan officer can enable the widget",
        )

    partnership.widget_enabled = True
    if not partnership.widget_token:
        partnership.generate_widget_token()

    await db.commit()

    return {"message": "Widget enabled", "widget_token": partnership.widget_token}
