"""
Pydantic schemas for lead management.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    NURTURING = "nurturing"


class LeadActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    NOTE = "note"
    STATUS_CHANGE = "status_change"
    MEETING = "meeting"
    DOCUMENT = "document"


class LeadActivityCreate(BaseModel):
    """Create a new lead activity."""
    activity_type: LeadActivityType
    description: Optional[str] = None
    metadata: Optional[dict] = None


class LeadActivityResponse(BaseModel):
    """Lead activity response."""
    id: str
    lead_id: str
    activity_type: str
    description: Optional[str] = None
    metadata: Optional[dict] = None
    performed_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LeadCreate(BaseModel):
    """Create a new lead."""
    borrower_id: Optional[str] = None
    source_call_id: Optional[str] = None

    contact_name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)

    loan_purpose: Optional[str] = Field(None, max_length=50)
    property_address: Optional[str] = None
    estimated_property_value: Optional[Decimal] = None
    estimated_loan_amount: Optional[Decimal] = None

    notes: Optional[str] = None

    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class LeadUpdate(BaseModel):
    """Update a lead."""
    lead_status: Optional[LeadStatus] = None

    contact_name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)

    loan_purpose: Optional[str] = Field(None, max_length=50)
    property_address: Optional[str] = None
    estimated_property_value: Optional[Decimal] = None
    estimated_loan_amount: Optional[Decimal] = None

    next_followup_at: Optional[datetime] = None
    notes: Optional[str] = None

    estimated_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None


class BorrowerInfo(BaseModel):
    """Borrower info for lead."""
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class SourceCallInfo(BaseModel):
    """Source call info for lead."""
    id: str
    initiated_at: datetime
    duration_seconds: Optional[int] = None
    rating: Optional[int] = None

    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    """Full lead response."""
    id: str
    professional_id: str

    lead_status: LeadStatus

    borrower: Optional[BorrowerInfo] = None
    source_call: Optional[SourceCallInfo] = None

    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    loan_purpose: Optional[str] = None
    property_address: Optional[str] = None
    estimated_property_value: Optional[Decimal] = None
    estimated_loan_amount: Optional[Decimal] = None

    last_contact_at: Optional[datetime] = None
    next_followup_at: Optional[datetime] = None
    notes: Optional[str] = None

    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

    estimated_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None

    activities: List[LeadActivityResponse] = []

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadListItem(BaseModel):
    """Lead list item (summary)."""
    id: str
    lead_status: LeadStatus

    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    loan_purpose: Optional[str] = None
    estimated_loan_amount: Optional[Decimal] = None

    next_followup_at: Optional[datetime] = None
    estimated_value: Optional[Decimal] = None

    last_activity_at: Optional[datetime] = None
    activity_count: int = 0

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    """Paginated lead list response."""
    leads: List[LeadListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class LeadStats(BaseModel):
    """Lead statistics for dashboard."""
    total_leads: int = 0
    leads_by_status: dict[str, int] = {}

    new_leads_today: int = 0
    new_leads_this_week: int = 0
    new_leads_this_month: int = 0

    conversion_rate: float = 0.0  # won / total
    avg_time_to_convert_days: Optional[float] = None

    total_value_won: Decimal = Decimal("0")
    total_value_pipeline: Decimal = Decimal("0")

    leads_needing_followup: int = 0
