from typing import List, Optional
from fastapi import APIRouter, Query
from sqlalchemy import select

from src.app.core.dependencies import DbSession
from src.app.models.professional import Specialty, Language, County
from src.app.schemas.professional import SpecialtyResponse, LanguageResponse, CountyResponse

router = APIRouter()


@router.get("/specialties", response_model=List[SpecialtyResponse])
async def list_specialties(
    db: DbSession,
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """List all available specialties."""
    query = select(Specialty)
    if category:
        query = query.where(Specialty.category == category)
    query = query.order_by(Specialty.name)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/languages", response_model=List[LanguageResponse])
async def list_languages(db: DbSession):
    """List all available languages."""
    query = select(Language).order_by(Language.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/counties", response_model=List[CountyResponse])
async def list_counties(
    db: DbSession,
    state_code: Optional[str] = Query(None, description="Filter by state code"),
):
    """List counties, optionally filtered by state."""
    query = select(County)
    if state_code:
        query = query.where(County.state_code == state_code.upper())
    query = query.order_by(County.state_code, County.county_name)

    result = await db.execute(query)
    return result.scalars().all()
