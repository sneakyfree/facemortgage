from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentUser, CurrentProfessional, CurrentUserOptional
from src.app.models.user import User
from src.app.models.professional import (
    ProfessionalProfile,
    ProfessionalStatus,
    Specialty,
    Language,
    County,
    ProfessionalSpecialty,
    ProfessionalLanguage,
    ProfessionalServiceArea,
)
from src.app.schemas.professional import (
    ProfessionalResponse,
    ProfessionalUpdate,
    ProfessionalGridItem,
    ProfessionalGridResponse,
    ProfessionalStatsResponse,
    StatusUpdateRequest,
    SpecialtyResponse,
    LanguageResponse,
    CountyResponse,
)

router = APIRouter()


@router.get("", response_model=ProfessionalGridResponse)
async def list_professionals(
    db: DbSession,
    current_user: CurrentUserOptional,
    # Filtering
    language: Optional[str] = Query(None, description="Language code (e.g., 'en', 'es')"),
    language_id: Optional[int] = Query(None, description="Language ID"),
    specialty: Optional[str] = Query(None, description="Specialty name"),
    specialty_id: Optional[int] = Query(None, description="Specialty ID"),
    county_id: Optional[int] = Query(None, description="County ID"),
    state: Optional[str] = Query(None, max_length=2, description="State code (e.g., 'CA', 'TX')"),
    county_name: Optional[str] = Query(None, description="County name (use with state)"),
    user_type: Optional[str] = Query(None, description="loan_officer, realtor, title_rep, attorney"),
    min_rating: Optional[float] = Query(None, ge=1.0, le=5.0),
    only_available: bool = Query(False, description="Only show available professionals"),
    # Pagination
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Get the grid of available professionals.

    Returns a ranked, filtered list of professionals.
    Ranking is based on weighted algorithm:
    - Bid Amount (30%)
    - Subscription Tier (25%)
    - Rating (20%)
    - Pickup Time (10%)
    - Time Online (10%)
    - Recency (5%)
    """
    from src.app.grid import get_ranking_service

    # Build filters dict
    filters = {}
    if user_type:
        filters["user_type"] = user_type
    if min_rating:
        filters["min_rating"] = min_rating
    # Language filtering (prefer ID over code)
    if language_id:
        filters["language_id"] = language_id
    elif language:
        filters["language"] = language
    # Specialty filtering (prefer ID over name)
    if specialty_id:
        filters["specialty_id"] = specialty_id
    elif specialty:
        filters["specialty"] = specialty
    # County/location filtering (prefer county_id, then state+county, then state only)
    if county_id:
        filters["county_id"] = county_id
    elif state and county_name:
        filters["state"] = state
        filters["county"] = county_name
    elif state:
        filters["state"] = state

    # Get ranked professionals
    ranking_service = get_ranking_service()
    ranked = await ranking_service.get_ranked_professionals(
        db=db,
        filters=filters,
        limit=limit,
        offset=offset,
        only_available=only_available,
    )

    # Get full professional data for the ranked results
    professional_ids = [r.professional_id for r in ranked]

    if professional_ids:
        query = (
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.specialties).selectinload(ProfessionalSpecialty.specialty),
                selectinload(ProfessionalProfile.languages).selectinload(ProfessionalLanguage.language),
            )
            .where(ProfessionalProfile.id.in_(professional_ids))
        )

        result = await db.execute(query)
        professionals_map = {p.id: p for p in result.scalars().all()}
    else:
        professionals_map = {}

    # Build grid items in ranked order
    grid_items = []
    for ranked_prof in ranked:
        prof = professionals_map.get(ranked_prof.professional_id)
        if not prof:
            continue

        user = prof.user
        item = ProfessionalGridItem(
            id=prof.id,
            user_id=prof.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
            user_type=user.user_type,
            company_name=prof.company_name,
            job_title=prof.job_title,
            bio=prof.bio,
            status=prof.status,
            subscription_tier=prof.subscription_tier,
            prerecorded_video_url=prof.prerecorded_video_url,
            video_type="live" if prof.status == ProfessionalStatus.ONLINE_AVAILABLE else "recorded",
            avg_rating=float(prof.avg_rating) if prof.avg_rating else 0.0,
            total_reviews=prof.total_reviews,
            avg_pickup_time_seconds=float(prof.avg_pickup_time_seconds) if prof.avg_pickup_time_seconds else None,
            years_experience=prof.years_experience,
            specialty_names=[ps.specialty.name for ps in prof.specialties],
            language_codes=[pl.language.code for pl in prof.languages],
            grid_position=ranked_prof.position,
            score=ranked_prof.score * 100,  # Convert to 0-100 scale
        )
        grid_items.append(item)

    # Get total count
    count_query = (
        select(func.count(ProfessionalProfile.id))
        .join(User)
        .where(User.is_active == True)
        .where(ProfessionalProfile.profile_complete == True)
    )
    if only_available:
        count_query = count_query.where(
            ProfessionalProfile.status == ProfessionalStatus.ONLINE_AVAILABLE
        )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    filters_applied = {}
    if language:
        filters_applied["language"] = language
    if language_id:
        filters_applied["language_id"] = language_id
    if specialty:
        filters_applied["specialty"] = specialty
    if specialty_id:
        filters_applied["specialty_id"] = specialty_id
    if county_id:
        filters_applied["county_id"] = county_id
    if state:
        filters_applied["state"] = state
    if county_name:
        filters_applied["county_name"] = county_name
    if user_type:
        filters_applied["user_type"] = user_type
    if min_rating:
        filters_applied["min_rating"] = min_rating
    if only_available:
        filters_applied["only_available"] = only_available

    return ProfessionalGridResponse(
        professionals=grid_items,
        total=total,
        filters_applied=filters_applied,
    )


@router.get("/{professional_id}", response_model=ProfessionalResponse)
async def get_professional(professional_id: UUID, db: DbSession):
    """Get detailed profile for a specific professional."""
    query = (
        select(ProfessionalProfile)
        .options(
            selectinload(ProfessionalProfile.user),
            selectinload(ProfessionalProfile.specialties).selectinload(ProfessionalSpecialty.specialty),
            selectinload(ProfessionalProfile.languages).selectinload(ProfessionalLanguage.language),
            selectinload(ProfessionalProfile.service_areas).selectinload(ProfessionalServiceArea.county),
        )
        .where(ProfessionalProfile.id == professional_id)
    )

    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found",
        )

    # Build response
    user = professional.user
    return ProfessionalResponse(
        id=professional.id,
        user_id=professional.user_id,
        company_name=professional.company_name,
        job_title=professional.job_title,
        bio=professional.bio,
        years_experience=professional.years_experience,
        nmls_id=professional.nmls_id,
        timezone=professional.timezone,
        status=professional.status,
        subscription_tier=professional.subscription_tier,
        prerecorded_video_url=professional.prerecorded_video_url,
        webcam_enabled=professional.webcam_enabled,
        nmls_verified=professional.nmls_verified,
        is_featured=professional.is_featured,
        profile_complete=professional.profile_complete,
        created_at=professional.created_at,
        updated_at=professional.updated_at,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        avatar_url=user.avatar_url,
        user_type=user.user_type,
        stats=ProfessionalStatsResponse(
            total_calls_completed=professional.total_calls_completed,
            avg_pickup_time_seconds=float(professional.avg_pickup_time_seconds) if professional.avg_pickup_time_seconds else None,
            total_reviews=professional.total_reviews,
            avg_rating=float(professional.avg_rating) if professional.avg_rating else 0.0,
            time_online_today_seconds=professional.time_online_today_seconds,
        ),
        specialties=[
            SpecialtyResponse(id=ps.specialty.id, name=ps.specialty.name, category=ps.specialty.category)
            for ps in professional.specialties
        ],
        languages=[
            LanguageResponse(id=pl.language.id, code=pl.language.code, name=pl.language.name, proficiency=pl.proficiency)
            for pl in professional.languages
        ],
        service_areas=[
            CountyResponse(id=psa.county.id, state_code=psa.county.state_code, county_name=psa.county.county_name)
            for psa in professional.service_areas
        ],
    )


@router.put("/me", response_model=ProfessionalResponse)
async def update_my_profile(
    updates: ProfessionalUpdate,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """Update the authenticated professional's profile."""
    # Get professional profile
    query = (
        select(ProfessionalProfile)
        .options(
            selectinload(ProfessionalProfile.user),
            selectinload(ProfessionalProfile.specialties),
            selectinload(ProfessionalProfile.languages),
            selectinload(ProfessionalProfile.service_areas),
        )
        .where(ProfessionalProfile.user_id == current_user.id)
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found",
        )

    update_data = updates.model_dump(exclude_unset=True)

    # Handle specialty_ids
    if "specialty_ids" in update_data:
        specialty_ids = update_data.pop("specialty_ids")
        # Clear existing
        for ps in professional.specialties:
            await db.delete(ps)
        # Add new
        for specialty_id in specialty_ids:
            ps = ProfessionalSpecialty(professional_id=professional.id, specialty_id=specialty_id)
            db.add(ps)

    # Handle language_ids
    if "language_ids" in update_data:
        language_ids = update_data.pop("language_ids")
        for pl in professional.languages:
            await db.delete(pl)
        for language_id in language_ids:
            pl = ProfessionalLanguage(professional_id=professional.id, language_id=language_id)
            db.add(pl)

    # Handle county_ids
    if "county_ids" in update_data:
        county_ids = update_data.pop("county_ids")
        for psa in professional.service_areas:
            await db.delete(psa)
        for county_id in county_ids:
            psa = ProfessionalServiceArea(professional_id=professional.id, county_id=county_id)
            db.add(psa)

    # Update other fields
    for field, value in update_data.items():
        setattr(professional, field, value)

    # Check if profile is complete
    professional.profile_complete = bool(
        professional.bio and
        professional.years_experience and
        len(professional.specialties) > 0
    )

    await db.commit()

    # Return updated profile
    return await get_professional(professional.id, db)


@router.patch("/me/status")
async def update_my_status(
    status_update: StatusUpdateRequest,
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Update the authenticated professional's availability status.

    This updates both the database and Redis presence system.
    The WebSocket connection will broadcast the change to all grid subscribers.
    """
    from datetime import datetime
    from src.app.presence import get_presence_service

    query = select(ProfessionalProfile).where(ProfessionalProfile.user_id == current_user.id)
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found",
        )

    # Update database
    professional.status = status_update.status
    professional.status_updated_at = datetime.utcnow()
    await db.commit()

    # Update Redis presence
    presence = get_presence_service()
    professional_id = str(professional.id)

    if status_update.status == ProfessionalStatus.ONLINE_AVAILABLE:
        await presence.set_available(professional_id)
    elif status_update.status == ProfessionalStatus.ONLINE_BUSY:
        await presence.set_busy(professional_id)
    elif status_update.status == ProfessionalStatus.IN_CALL:
        await presence.set_in_call(professional_id, status_update.room_id or "")
    elif status_update.status == ProfessionalStatus.AWAY:
        await presence.set_away(professional_id)
    elif status_update.status == ProfessionalStatus.OFFLINE:
        await presence.set_offline(professional_id, "status_change")

    return {"status": status_update.status, "updated": True}


@router.post("/me/go-online")
async def go_online(
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Mark the professional as online and available.

    This is a convenience endpoint that:
    1. Updates database status to ONLINE_AVAILABLE
    2. Registers with Redis presence system
    3. Broadcasts to grid subscribers
    """
    from datetime import datetime
    from src.app.presence import get_presence_service

    query = (
        select(ProfessionalProfile)
        .options(selectinload(ProfessionalProfile.user))
        .where(ProfessionalProfile.user_id == current_user.id)
    )
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found",
        )

    if not professional.profile_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be complete before going online",
        )

    # Update database
    professional.status = ProfessionalStatus.ONLINE_AVAILABLE
    professional.status_updated_at = datetime.utcnow()
    await db.commit()

    # Update Redis presence with metadata
    presence = get_presence_service()
    await presence.set_online(
        str(professional.id),
        metadata={
            "user_id": str(professional.user_id),
            "name": f"{professional.user.first_name} {professional.user.last_name}",
            "subscription_tier": professional.subscription_tier.value,
        }
    )

    return {
        "status": ProfessionalStatus.ONLINE_AVAILABLE.value,
        "message": "You are now online and visible to borrowers",
    }


@router.post("/me/go-offline")
async def go_offline(
    current_user: CurrentProfessional,
    db: DbSession,
):
    """
    Mark the professional as offline.

    This removes them from the grid and presence system.
    """
    from datetime import datetime
    from src.app.presence import get_presence_service

    query = select(ProfessionalProfile).where(ProfessionalProfile.user_id == current_user.id)
    result = await db.execute(query)
    professional = result.scalar_one_or_none()

    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found",
        )

    # Update database
    professional.status = ProfessionalStatus.OFFLINE
    professional.status_updated_at = datetime.utcnow()
    await db.commit()

    # Update Redis presence
    presence = get_presence_service()
    await presence.set_offline(str(professional.id), "user_action")

    return {
        "status": ProfessionalStatus.OFFLINE.value,
        "message": "You are now offline",
    }
