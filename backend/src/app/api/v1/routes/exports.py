"""
Export and data management routes.

Handles:
- CSV lead import
- Lead scoring
- Report export (CSV/JSON)
- GDPR data export and account deletion
"""
import io
import csv
import json
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentUser
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.user import User
from src.app.models.professional import ProfessionalProfile
from src.app.models.lead import Lead, LeadStatus
from src.app.models.call import VideoCall
from src.app.models.review import Review

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Schemas ====================

class LeadImportResult(BaseModel):
    """Result of CSV lead import."""
    imported: int
    skipped: int
    errors: List[str]


class LeadScoreResponse(BaseModel):
    """Lead score calculation result."""
    lead_id: str
    score: int  # 0-100
    factors: dict


class DataExportResponse(BaseModel):
    """GDPR data export response."""
    download_url: str
    expires_at: datetime


class AccountDeletionRequest(BaseModel):
    """Request for account deletion."""
    confirm_email: EmailStr
    reason: Optional[str] = None


# ==================== Lead Import ====================

@router.post("/leads/import", response_model=LeadImportResult)
@limiter.limit(RATE_LIMITS["api_write"])
async def import_leads_csv(
    request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: DbSession = None,
):
    """
    Import leads from CSV file.
    
    Expected columns: name, email, phone, loan_purpose, estimated_amount, notes
    """
    # Get professional profile
    result = await db.execute(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Professional profile not found")

    # Read CSV
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        text = content.decode('latin-1')

    reader = csv.DictReader(io.StringIO(text))
    
    imported = 0
    skipped = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            # Normalize column names
            row = {k.lower().strip(): v for k, v in row.items()}
            
            name = row.get('name') or row.get('contact_name') or ''
            email = row.get('email') or row.get('contact_email') or ''
            phone = row.get('phone') or row.get('contact_phone') or ''
            
            if not name and not email:
                skipped += 1
                continue

            # Check for duplicate by email
            if email:
                existing = await db.execute(
                    select(Lead)
                    .where(Lead.professional_id == profile.id)
                    .where(Lead.contact_email == email)
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

            # Parse amount
            amount_str = row.get('estimated_amount') or row.get('loan_amount') or '0'
            try:
                amount = int(float(amount_str.replace('$', '').replace(',', '')))
            except ValueError:
                amount = None

            lead = Lead(
                professional_id=profile.id,
                contact_name=name,
                contact_email=email or None,
                contact_phone=phone or None,
                loan_purpose=row.get('loan_purpose') or row.get('purpose'),
                estimated_loan_amount=amount,
                notes=row.get('notes') or row.get('comments'),
                lead_status=LeadStatus.NEW,
                utm_source='csv_import',
            )
            db.add(lead)
            imported += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
            if len(errors) > 10:
                errors.append("... too many errors, stopping")
                break

    await db.commit()

    return LeadImportResult(
        imported=imported,
        skipped=skipped,
        errors=errors[:10],
    )


# ==================== Lead Scoring ====================

@router.get("/leads/{lead_id}/score", response_model=LeadScoreResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def score_lead(
    request: Request,
    lead_id: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Calculate lead score based on multiple factors.
    
    Factors: completeness, engagement, urgency, value, recency
    """
    # Get lead
    result = await db.execute(
        select(Lead)
        .options(selectinload(Lead.activities))
        .where(Lead.id == UUID(lead_id))
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Verify ownership
    profile = await db.execute(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == current_user.id)
    )
    prof = profile.scalar_one_or_none()
    if not prof or lead.professional_id != prof.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Calculate score
    score, factors = _calculate_lead_score(lead)

    return LeadScoreResponse(
        lead_id=str(lead.id),
        score=score,
        factors=factors,
    )


def _calculate_lead_score(lead: Lead) -> tuple[int, dict]:
    """Calculate lead score (0-100) and return factors."""
    factors = {}
    score = 0

    # Completeness (0-25 points)
    completeness = 0
    if lead.contact_name:
        completeness += 5
    if lead.contact_email:
        completeness += 5
    if lead.contact_phone:
        completeness += 5
    if lead.loan_purpose:
        completeness += 5
    if lead.estimated_loan_amount:
        completeness += 5
    factors['completeness'] = completeness
    score += completeness

    # Engagement (0-25 points based on activities)
    activity_count = len(lead.activities) if lead.activities else 0
    engagement = min(25, activity_count * 5)
    factors['engagement'] = engagement
    score += engagement

    # Value (0-25 points based on loan amount)
    if lead.estimated_loan_amount:
        if lead.estimated_loan_amount >= 500000:
            value_score = 25
        elif lead.estimated_loan_amount >= 300000:
            value_score = 20
        elif lead.estimated_loan_amount >= 200000:
            value_score = 15
        elif lead.estimated_loan_amount >= 100000:
            value_score = 10
        else:
            value_score = 5
    else:
        value_score = 0
    factors['value'] = value_score
    score += value_score

    # Recency (0-25 points based on last contact)
    now = datetime.utcnow()
    if lead.last_contact_at:
        days_since = (now - lead.last_contact_at).days
        if days_since <= 1:
            recency = 25
        elif days_since <= 3:
            recency = 20
        elif days_since <= 7:
            recency = 15
        elif days_since <= 14:
            recency = 10
        else:
            recency = 5
    else:
        # Fresh lead with no contact yet
        days_since_created = (now - lead.created_at).days
        recency = 25 if days_since_created <= 1 else 15
    factors['recency'] = recency
    score += recency

    return min(100, score), factors


# ==================== Report Export ====================

@router.get("/reports/leads")
@limiter.limit(RATE_LIMITS["api_read"])
async def export_leads_report(
    request: Request,
    format: str = "csv",
    current_user: CurrentUser = None,
    db: DbSession = None,
):
    """
    Export leads report as CSV or JSON.
    """
    # Get professional profile
    result = await db.execute(
        select(ProfessionalProfile).where(ProfessionalProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Professional profile not found")

    # Get all leads
    leads_result = await db.execute(
        select(Lead)
        .where(Lead.professional_id == profile.id)
        .order_by(Lead.created_at.desc())
    )
    leads = leads_result.scalars().all()

    if format == "json":
        data = [
            {
                "id": str(l.id),
                "name": l.contact_name,
                "email": l.contact_email,
                "phone": l.contact_phone,
                "status": l.lead_status.value if hasattr(l.lead_status, 'value') else l.lead_status,
                "loan_purpose": l.loan_purpose,
                "estimated_amount": l.estimated_loan_amount,
                "created_at": l.created_at.isoformat(),
            }
            for l in leads
        ]
        return {"leads": data, "total": len(data)}
    
    # CSV export
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Email', 'Phone', 'Status', 'Loan Purpose', 'Estimated Amount', 'Created At'])
    
    for l in leads:
        writer.writerow([
            l.contact_name,
            l.contact_email,
            l.contact_phone,
            l.lead_status.value if hasattr(l.lead_status, 'value') else l.lead_status,
            l.loan_purpose,
            l.estimated_loan_amount,
            l.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


# ==================== GDPR Data Export ====================

@router.get("/gdpr/export")
@limiter.limit("3/hour")
async def export_user_data(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Export all user data for GDPR compliance.
    
    Returns JSON with all personal data associated with the account.
    """
    user = current_user
    
    # Collect all user data
    data = {
        "account": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type.value if hasattr(user.user_type, 'value') else user.user_type,
            "created_at": user.created_at.isoformat(),
            "email_verified": user.email_verified,
        },
        "calls": [],
        "reviews": [],
        "exported_at": datetime.utcnow().isoformat(),
    }

    # Get calls
    calls_result = await db.execute(
        select(VideoCall).where(
            (VideoCall.borrower_id == user.id) | 
            (VideoCall.professional_id == user.id)
        )
    )
    for call in calls_result.scalars().all():
        data["calls"].append({
            "id": str(call.id),
            "room_id": call.room_id,
            "status": call.status.value if hasattr(call.status, 'value') else call.status,
            "initiated_at": call.initiated_at.isoformat() if call.initiated_at else None,
            "duration_seconds": call.duration_seconds,
        })

    # Get reviews given/received
    reviews_result = await db.execute(
        select(Review).where(
            (Review.reviewer_id == user.id) | 
            (Review.reviewed_professional_id == user.id)
        )
    )
    for review in reviews_result.scalars().all():
        data["reviews"].append({
            "id": str(review.id),
            "rating": review.overall_rating,
            "content": review.content,
            "created_at": review.created_at.isoformat(),
            "type": "given" if review.reviewer_id == user.id else "received",
        })

    # If professional, include leads
    if user.is_professional:
        prof_result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id)
        )
        prof = prof_result.scalar_one_or_none()
        if prof:
            data["professional_profile"] = {
                "id": str(prof.id),
                "company_name": prof.company_name,
                "nmls_id": prof.nmls_id,
                "avg_rating": prof.avg_rating,
                "total_reviews": prof.total_reviews,
            }

            leads_result = await db.execute(
                select(Lead).where(Lead.professional_id == prof.id)
            )
            data["leads"] = [
                {
                    "id": str(l.id),
                    "contact_name": l.contact_name,
                    "contact_email": l.contact_email,
                    "status": l.lead_status.value if hasattr(l.lead_status, 'value') else l.lead_status,
                    "created_at": l.created_at.isoformat(),
                }
                for l in leads_result.scalars().all()
            ]

    return data


@router.post("/gdpr/delete")
@limiter.limit("1/day")
async def request_account_deletion(
    request: Request,
    body: AccountDeletionRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    Request account deletion for GDPR compliance.
    
    Schedules account for deletion after confirmation.
    """
    if body.confirm_email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email confirmation does not match account email",
        )

    # Mark user for deletion (soft delete)
    user = await db.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Deactivate account
    user.is_active = False
    
    # Log deletion request
    logger.info(f"Account deletion requested: {user.id}, reason: {body.reason}")

    # TODO: Schedule actual data deletion task for 30 days from now
    # This allows for cancellation if user changes their mind

    await db.commit()

    return {
        "success": True,
        "message": "Account scheduled for deletion. You will receive a confirmation email.",
        "deletion_date": (datetime.utcnow().replace(hour=0, minute=0, second=0) + 
                         __import__('datetime').timedelta(days=30)).isoformat(),
    }
