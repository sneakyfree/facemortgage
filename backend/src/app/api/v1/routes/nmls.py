"""
NMLS verification API endpoints.

Provides endpoints for verifying and managing NMLS credentials
for loan officers on the platform.
"""

import logging
from datetime import datetime
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.app.core.dependencies import DbSession, CurrentProfessional, CurrentAdmin
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.professional import ProfessionalProfile
from src.app.services.nmls_service import verify_professional_nmls, NMLSVerificationResult

router = APIRouter()
logger = logging.getLogger(__name__)


class VerifyNMLSRequest(BaseModel):
    """Request to verify an NMLS ID."""
    nmls_id: str = Field(..., min_length=5, max_length=10, pattern=r'^\d{5,10}$')
    claimed_states: Optional[list[str]] = Field(
        default=None,
        description="Optional list of states the professional claims to be licensed in"
    )


class NMLSVerificationResponse(BaseModel):
    """Response from NMLS verification."""
    nmls_id: str
    is_valid: bool
    is_active: bool
    license_states: list[str] = []
    error_message: Optional[str] = None
    verified_at: datetime


class ProfessionalNMLSStatus(BaseModel):
    """Current NMLS verification status for a professional."""
    nmls_id: Optional[str] = None
    nmls_verified: bool = False
    nmls_verified_at: Optional[datetime] = None
    license_states: list[str] = []


@router.post("/verify", response_model=NMLSVerificationResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def verify_nmls(
    request: Request,
    body: VerifyNMLSRequest,
    db: DbSession,
    current_professional: CurrentProfessional,
):
    """
    Verify an NMLS ID for the current professional.
    
    This endpoint validates the NMLS ID against the NMLS Consumer Access
    database and optionally verifies state licensing claims.
    
    If verification succeeds, the professional's profile is updated with
    the verified status and timestamp.
    """
    # Get professional profile
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_professional.id
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    # Verify the NMLS ID
    verification = await verify_professional_nmls(
        nmls_id=body.nmls_id,
        professional_name=f"{current_professional.first_name} {current_professional.last_name}",
        claimed_states=body.claimed_states,
    )
    
    # Update profile based on result
    if verification.is_valid and verification.is_active:
        profile.nmls_id = body.nmls_id
        profile.nmls_verified = True
        profile.nmls_verified_at = verification.verified_at
        await db.commit()
        await db.refresh(profile)
        
        logger.info(f"NMLS verification successful for professional {profile.id}")
    else:
        logger.warning(
            f"NMLS verification failed for professional {profile.id}: "
            f"{verification.error_message}"
        )
    
    return NMLSVerificationResponse(
        nmls_id=body.nmls_id,
        is_valid=verification.is_valid,
        is_active=verification.is_active,
        license_states=verification.license_info.license_states if verification.license_info else [],
        error_message=verification.error_message,
        verified_at=verification.verified_at,
    )


@router.get("/status", response_model=ProfessionalNMLSStatus)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_nmls_status(
    request: Request,
    db: DbSession,
    current_professional: CurrentProfessional,
):
    """
    Get the current NMLS verification status for the logged-in professional.
    """
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_professional.id
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    # If verified, get license states
    license_states = []
    if profile.nmls_verified and profile.nmls_id:
        # Could re-fetch from NMLS or cache - using mock for now
        license_states = ["NY", "CA", "TX", "FL"]  # Would come from cached verification
    
    return ProfessionalNMLSStatus(
        nmls_id=profile.nmls_id,
        nmls_verified=profile.nmls_verified,
        nmls_verified_at=profile.nmls_verified_at,
        license_states=license_states,
    )


@router.post("/admin/verify/{professional_id}", response_model=NMLSVerificationResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def admin_verify_nmls(
    request: Request,
    professional_id: UUID,
    body: VerifyNMLSRequest,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Admin endpoint to verify NMLS for any professional.
    
    Useful for bulk verification or when professionals need assistance.
    """
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.id == professional_id
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found"
        )
    
    # Verify the NMLS ID
    verification = await verify_professional_nmls(
        nmls_id=body.nmls_id,
        claimed_states=body.claimed_states,
    )
    
    # Update profile based on result
    if verification.is_valid and verification.is_active:
        profile.nmls_id = body.nmls_id
        profile.nmls_verified = True
        profile.nmls_verified_at = verification.verified_at
        await db.commit()
        await db.refresh(profile)
        
        logger.info(
            f"Admin NMLS verification successful for professional {profile.id} "
            f"by admin {current_admin.id}"
        )
    
    return NMLSVerificationResponse(
        nmls_id=body.nmls_id,
        is_valid=verification.is_valid,
        is_active=verification.is_active,
        license_states=verification.license_info.license_states if verification.license_info else [],
        error_message=verification.error_message,
        verified_at=verification.verified_at,
    )


@router.delete("/revoke")
@limiter.limit(RATE_LIMITS["api_write"])
async def revoke_nmls_verification(
    request: Request,
    db: DbSession,
    current_professional: CurrentProfessional,
):
    """
    Revoke NMLS verification for the current professional.
    
    This might be needed if the professional's license lapses
    or they move to a new company.
    """
    query = select(ProfessionalProfile).where(
        ProfessionalProfile.user_id == current_professional.id
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    # Clear verification
    profile.nmls_verified = False
    profile.nmls_verified_at = None
    # Keep nmls_id for reference
    
    await db.commit()
    
    logger.info(f"NMLS verification revoked for professional {profile.id}")
    
    return {"status": "revoked", "message": "NMLS verification has been revoked"}
