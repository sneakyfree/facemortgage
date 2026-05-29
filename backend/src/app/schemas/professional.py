from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from src.app.models.professional import ProfessionalStatus, SubscriptionTier
from src.app.models.user import UserType


class SpecialtyResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None

    class Config:
        from_attributes = True


class LanguageResponse(BaseModel):
    id: int
    code: str
    name: str
    proficiency: Optional[str] = "fluent"

    class Config:
        from_attributes = True


class CountyResponse(BaseModel):
    id: int
    state_code: str
    county_name: str

    class Config:
        from_attributes = True


class ProfessionalBase(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    nmls_id: Optional[str] = None
    timezone: str = "America/New_York"


class ProfessionalCreate(ProfessionalBase):
    specialty_ids: List[int] = []
    language_ids: List[int] = []
    county_ids: List[int] = []


class ProfessionalUpdate(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    nmls_id: Optional[str] = None
    timezone: Optional[str] = None
    prerecorded_video_url: Optional[str] = None
    webcam_enabled: Optional[bool] = None
    specialty_ids: Optional[List[int]] = None
    language_ids: Optional[List[int]] = None
    county_ids: Optional[List[int]] = None


class ProfessionalStatsResponse(BaseModel):
    total_calls_completed: int
    avg_pickup_time_seconds: Optional[float] = None
    total_reviews: int
    avg_rating: float
    time_online_today_seconds: int


class ProfessionalResponse(ProfessionalBase):
    id: UUID
    user_id: UUID
    status: ProfessionalStatus
    subscription_tier: SubscriptionTier
    prerecorded_video_url: Optional[str] = None
    webcam_enabled: bool
    nmls_verified: bool
    is_featured: bool
    profile_complete: bool
    created_at: datetime
    updated_at: datetime

    # User info
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    user_type: Optional[UserType] = None

    # Stats
    stats: Optional[ProfessionalStatsResponse] = None

    # Related data
    specialties: List[SpecialtyResponse] = []
    languages: List[LanguageResponse] = []
    service_areas: List[CountyResponse] = []

    class Config:
        from_attributes = True


class ProfessionalGridItem(BaseModel):
    """Simplified professional data for the grid view"""
    id: UUID
    user_id: UUID
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None
    user_type: UserType

    company_name: Optional[str] = None
    job_title: Optional[str] = None
    bio: Optional[str] = None

    status: ProfessionalStatus
    subscription_tier: SubscriptionTier

    # Video
    prerecorded_video_url: Optional[str] = None
    video_type: str = "live"  # "live" or "recorded"
    video_stream_url: Optional[str] = None

    # Quick stats
    avg_rating: float = 0.0
    total_reviews: int = 0
    avg_pickup_time_seconds: Optional[float] = None
    years_experience: Optional[int] = None

    # Specialties and languages for filtering
    specialty_names: List[str] = []
    language_codes: List[str] = []

    # Grid positioning
    grid_position: int = 0
    score: float = 0.0


class ProfessionalGridResponse(BaseModel):
    professionals: List[ProfessionalGridItem]
    total: int
    filters_applied: dict = {}


class StatusUpdateRequest(BaseModel):
    status: ProfessionalStatus
    room_id: Optional[str] = None  # Required when status is IN_CALL
