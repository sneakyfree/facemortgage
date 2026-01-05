"""
Pydantic schemas for professional statistics from external data providers.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

from src.app.integrations.data_providers.base import LicenseStatus


class LicenseInfoResponse(BaseModel):
    """License information for a professional."""
    nmls_id: str
    name: str
    license_type: str
    status: LicenseStatus
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    state_licenses: List[str] = []
    company_name: Optional[str] = None
    company_nmls_id: Optional[str] = None

    class Config:
        from_attributes = True


class LoanRecordResponse(BaseModel):
    """Individual loan record."""
    loan_id: Optional[str] = None
    loan_amount: Decimal
    loan_type: Optional[str] = None
    property_type: Optional[str] = None
    purpose: Optional[str] = None
    close_date: Optional[date] = None
    state: Optional[str] = None
    county: Optional[str] = None

    class Config:
        from_attributes = True


class ProductionHistoryResponse(BaseModel):
    """Production history for a professional."""
    nmls_id: str
    period_start: date
    period_end: date

    total_loans: int = 0
    total_volume: Decimal = Decimal("0")
    average_loan_size: Decimal = Decimal("0")

    # Breakdown by loan type
    conventional_count: int = 0
    conventional_volume: Decimal = Decimal("0")
    fha_count: int = 0
    fha_volume: Decimal = Decimal("0")
    va_count: int = 0
    va_volume: Decimal = Decimal("0")
    usda_count: int = 0
    usda_volume: Decimal = Decimal("0")
    jumbo_count: int = 0
    jumbo_volume: Decimal = Decimal("0")

    # Breakdown by purpose
    purchase_count: int = 0
    purchase_volume: Decimal = Decimal("0")
    refinance_count: int = 0
    refinance_volume: Decimal = Decimal("0")

    # Rankings
    state_rank: Optional[int] = None
    national_rank: Optional[int] = None

    loans: List[LoanRecordResponse] = []

    class Config:
        from_attributes = True


class ProfessionalStatsResponse(BaseModel):
    """
    Full professional statistics for display on profiles.
    This is the "baseball card" data.
    """
    nmls_id: str
    fetched_at: datetime

    # License info
    license: Optional[LicenseInfoResponse] = None

    # Career metrics
    years_in_industry: Optional[int] = None
    total_loans_career: Optional[int] = None
    total_volume_career: Optional[Decimal] = None

    # Recent production (last 12 months)
    loans_last_12_months: int = 0
    volume_last_12_months: Decimal = Decimal("0")
    avg_loan_size_12_months: Decimal = Decimal("0")

    # YTD production
    loans_ytd: int = 0
    volume_ytd: Decimal = Decimal("0")

    # Loan type breakdown (percentages)
    conventional_pct: float = 0.0
    fha_pct: float = 0.0
    va_pct: float = 0.0
    other_pct: float = 0.0

    # Purchase vs Refi
    purchase_pct: float = 0.0
    refinance_pct: float = 0.0

    # Rankings
    state_rank: Optional[int] = None
    national_rank: Optional[int] = None

    # Top areas served
    top_states: List[str] = []
    top_counties: List[str] = []

    class Config:
        from_attributes = True


class NMLSVerificationResponse(BaseModel):
    """Response for NMLS verification."""
    nmls_id: str
    is_valid: bool
    is_active: bool
    name: Optional[str] = None
    company: Optional[str] = None
    message: str = ""


class ProfessionalSearchRequest(BaseModel):
    """Search request for professionals."""
    name: Optional[str] = None
    company: Optional[str] = None
    state: Optional[str] = Field(None, max_length=2)
    limit: int = Field(20, ge=1, le=100)


class BaseballCardData(BaseModel):
    """
    Formatted baseball card data for frontend display.
    Includes formatted strings and display-ready values.
    """
    nmls_id: str
    name: str
    company: Optional[str] = None
    license_status: str
    license_status_color: str  # 'green', 'yellow', 'red'

    # Formatted display values
    years_experience_display: str  # "5 years"
    total_loans_display: str  # "1,234 loans"
    total_volume_display: str  # "$45.2M"

    # Last 12 months
    loans_12m_display: str  # "87 loans"
    volume_12m_display: str  # "$28.5M"
    avg_loan_display: str  # "$327K"

    # Loan mix (for pie chart)
    loan_mix: List[dict]  # [{"type": "Conventional", "pct": 55.2}, ...]

    # Purpose mix
    purpose_mix: List[dict]  # [{"type": "Purchase", "pct": 65.0}, ...]

    # Rankings
    rankings: List[dict]  # [{"label": "State Rank", "value": "#42"}, ...]

    # States licensed
    states_licensed: List[str]

    # Top markets
    top_markets: List[str]

    class Config:
        from_attributes = True


def format_currency(amount: Decimal, compact: bool = True) -> str:
    """Format currency amount for display."""
    if compact:
        if amount >= 1_000_000_000:
            return f"${amount / 1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"${amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount / 1_000:.0f}K"
    return f"${amount:,.0f}"


def format_number(num: int) -> str:
    """Format number with commas."""
    return f"{num:,}"


def stats_to_baseball_card(stats: ProfessionalStatsResponse) -> BaseballCardData:
    """Convert ProfessionalStats to display-ready BaseballCard format."""

    # Determine license status color
    status_colors = {
        "active": "green",
        "inactive": "yellow",
        "expired": "red",
        "suspended": "red",
        "revoked": "red",
    }
    license_status = stats.license.status.value if stats.license else "unknown"
    status_color = status_colors.get(license_status, "gray")

    # Format loan mix
    loan_mix = []
    if stats.conventional_pct > 0:
        loan_mix.append({"type": "Conventional", "pct": stats.conventional_pct})
    if stats.fha_pct > 0:
        loan_mix.append({"type": "FHA", "pct": stats.fha_pct})
    if stats.va_pct > 0:
        loan_mix.append({"type": "VA", "pct": stats.va_pct})
    if stats.other_pct > 0:
        loan_mix.append({"type": "Other", "pct": stats.other_pct})

    # Format purpose mix
    purpose_mix = []
    if stats.purchase_pct > 0:
        purpose_mix.append({"type": "Purchase", "pct": stats.purchase_pct})
    if stats.refinance_pct > 0:
        purpose_mix.append({"type": "Refinance", "pct": stats.refinance_pct})

    # Format rankings
    rankings = []
    if stats.state_rank:
        rankings.append({"label": "State Rank", "value": f"#{stats.state_rank}"})
    if stats.national_rank:
        rankings.append({"label": "National Rank", "value": f"#{stats.national_rank}"})

    return BaseballCardData(
        nmls_id=stats.nmls_id,
        name=stats.license.name if stats.license else "Unknown",
        company=stats.license.company_name if stats.license else None,
        license_status=license_status.capitalize(),
        license_status_color=status_color,
        years_experience_display=f"{stats.years_in_industry} years" if stats.years_in_industry else "N/A",
        total_loans_display=f"{format_number(stats.total_loans_career)} loans" if stats.total_loans_career else "N/A",
        total_volume_display=format_currency(stats.total_volume_career) if stats.total_volume_career else "N/A",
        loans_12m_display=f"{format_number(stats.loans_last_12_months)} loans",
        volume_12m_display=format_currency(stats.volume_last_12_months),
        avg_loan_display=format_currency(stats.avg_loan_size_12_months),
        loan_mix=loan_mix,
        purpose_mix=purpose_mix,
        rankings=rankings,
        states_licensed=stats.license.state_licenses if stats.license else [],
        top_markets=stats.top_states,
    )
