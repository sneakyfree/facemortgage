"""
Abstract base class for professional data providers.

Defines the interface for fetching professional statistics,
license information, and production history from external APIs.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum


class LicenseStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class LicenseInfo:
    """License information for a professional."""
    nmls_id: str
    name: str
    license_type: str  # MLO, Broker, etc.
    status: LicenseStatus
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    state_licenses: List[str] = field(default_factory=list)
    company_name: Optional[str] = None
    company_nmls_id: Optional[str] = None


@dataclass
class LoanRecord:
    """Individual loan record from production history."""
    loan_id: Optional[str] = None
    loan_amount: Decimal = Decimal("0")
    loan_type: Optional[str] = None  # Conventional, FHA, VA, USDA, Jumbo
    property_type: Optional[str] = None  # SFR, Condo, Multi-family
    purpose: Optional[str] = None  # Purchase, Refinance, Cash-out
    close_date: Optional[date] = None
    state: Optional[str] = None
    county: Optional[str] = None


@dataclass
class ProductionHistory:
    """Production history and metrics for a professional."""
    nmls_id: str
    period_start: date
    period_end: date

    # Volume metrics
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

    # Rankings (optional, provider-specific)
    state_rank: Optional[int] = None
    national_rank: Optional[int] = None
    company_rank: Optional[int] = None

    # Individual loans (if available)
    loans: List[LoanRecord] = field(default_factory=list)


@dataclass
class ProfessionalStats:
    """
    Aggregated professional statistics for display.

    This is the "baseball card" data shown on professional profiles.
    """
    nmls_id: str
    fetched_at: datetime

    # License info
    license: Optional[LicenseInfo] = None

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

    # Top states/counties served
    top_states: List[str] = field(default_factory=list)
    top_counties: List[str] = field(default_factory=list)

    # Additional provider-specific data
    raw_data: Dict[str, Any] = field(default_factory=dict)


class ProfessionalDataProvider(ABC):
    """
    Abstract interface for professional data providers.

    Implementations should handle:
    - API authentication
    - Rate limiting
    - Error handling
    - Response parsing
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass

    @abstractmethod
    async def get_professional_stats(self, nmls_id: str) -> Optional[ProfessionalStats]:
        """
        Fetch aggregated statistics for a professional.

        Args:
            nmls_id: The NMLS ID of the professional

        Returns:
            ProfessionalStats object or None if not found
        """
        pass

    @abstractmethod
    async def get_license_info(self, nmls_id: str) -> Optional[LicenseInfo]:
        """
        Fetch license information for a professional.

        Args:
            nmls_id: The NMLS ID of the professional

        Returns:
            LicenseInfo object or None if not found
        """
        pass

    @abstractmethod
    async def get_production_history(
        self,
        nmls_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Optional[ProductionHistory]:
        """
        Fetch production history for a professional.

        Args:
            nmls_id: The NMLS ID of the professional
            start_date: Start of period (default: 12 months ago)
            end_date: End of period (default: today)

        Returns:
            ProductionHistory object or None if not found
        """
        pass

    @abstractmethod
    async def search_professionals(
        self,
        name: Optional[str] = None,
        company: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 20,
    ) -> List[LicenseInfo]:
        """
        Search for professionals by criteria.

        Args:
            name: Professional name (partial match)
            company: Company name (partial match)
            state: State code
            limit: Maximum results to return

        Returns:
            List of matching LicenseInfo objects
        """
        pass

    @abstractmethod
    async def verify_nmls(self, nmls_id: str) -> bool:
        """
        Verify that an NMLS ID is valid and active.

        Args:
            nmls_id: The NMLS ID to verify

        Returns:
            True if valid and active, False otherwise
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the provider API is available.

        Returns:
            True if API is responding, False otherwise
        """
        return True
