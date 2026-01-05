"""
API routes for professional statistics from external data providers.
"""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from src.app.integrations.data_providers import get_data_provider, ProfessionalDataProvider
from src.app.schemas.professional_stats import (
    ProfessionalStatsResponse,
    LicenseInfoResponse,
    ProductionHistoryResponse,
    NMLSVerificationResponse,
    ProfessionalSearchRequest,
    BaseballCardData,
    stats_to_baseball_card,
)

router = APIRouter()


@router.get(
    "/{nmls_id}",
    response_model=ProfessionalStatsResponse,
    summary="Get professional statistics",
    description="Fetch full statistics for a professional by NMLS ID.",
)
async def get_professional_stats(
    nmls_id: str,
    provider: ProfessionalDataProvider = Depends(get_data_provider),
):
    """Get aggregated professional statistics."""
    stats = await provider.get_professional_stats(nmls_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Professional not found")

    # Convert dataclass to dict for Pydantic
    return ProfessionalStatsResponse(
        nmls_id=stats.nmls_id,
        fetched_at=stats.fetched_at,
        license=LicenseInfoResponse(
            nmls_id=stats.license.nmls_id,
            name=stats.license.name,
            license_type=stats.license.license_type,
            status=stats.license.status,
            issue_date=stats.license.issue_date,
            expiry_date=stats.license.expiry_date,
            state_licenses=stats.license.state_licenses,
            company_name=stats.license.company_name,
            company_nmls_id=stats.license.company_nmls_id,
        ) if stats.license else None,
        years_in_industry=stats.years_in_industry,
        total_loans_career=stats.total_loans_career,
        total_volume_career=stats.total_volume_career,
        loans_last_12_months=stats.loans_last_12_months,
        volume_last_12_months=stats.volume_last_12_months,
        avg_loan_size_12_months=stats.avg_loan_size_12_months,
        loans_ytd=stats.loans_ytd,
        volume_ytd=stats.volume_ytd,
        conventional_pct=stats.conventional_pct,
        fha_pct=stats.fha_pct,
        va_pct=stats.va_pct,
        other_pct=stats.other_pct,
        purchase_pct=stats.purchase_pct,
        refinance_pct=stats.refinance_pct,
        state_rank=stats.state_rank,
        national_rank=stats.national_rank,
        top_states=stats.top_states,
        top_counties=stats.top_counties,
    )


@router.get(
    "/{nmls_id}/baseball-card",
    response_model=BaseballCardData,
    summary="Get baseball card data",
    description="Fetch formatted baseball card data for display.",
)
async def get_baseball_card(
    nmls_id: str,
    provider: ProfessionalDataProvider = Depends(get_data_provider),
):
    """Get baseball card formatted data for a professional."""
    stats = await provider.get_professional_stats(nmls_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Professional not found")

    # Convert to response model first
    stats_response = ProfessionalStatsResponse(
        nmls_id=stats.nmls_id,
        fetched_at=stats.fetched_at,
        license=LicenseInfoResponse(
            nmls_id=stats.license.nmls_id,
            name=stats.license.name,
            license_type=stats.license.license_type,
            status=stats.license.status,
            issue_date=stats.license.issue_date,
            expiry_date=stats.license.expiry_date,
            state_licenses=stats.license.state_licenses,
            company_name=stats.license.company_name,
            company_nmls_id=stats.license.company_nmls_id,
        ) if stats.license else None,
        years_in_industry=stats.years_in_industry,
        total_loans_career=stats.total_loans_career,
        total_volume_career=stats.total_volume_career,
        loans_last_12_months=stats.loans_last_12_months,
        volume_last_12_months=stats.volume_last_12_months,
        avg_loan_size_12_months=stats.avg_loan_size_12_months,
        loans_ytd=stats.loans_ytd,
        volume_ytd=stats.volume_ytd,
        conventional_pct=stats.conventional_pct,
        fha_pct=stats.fha_pct,
        va_pct=stats.va_pct,
        other_pct=stats.other_pct,
        purchase_pct=stats.purchase_pct,
        refinance_pct=stats.refinance_pct,
        state_rank=stats.state_rank,
        national_rank=stats.national_rank,
        top_states=stats.top_states,
        top_counties=stats.top_counties,
    )

    return stats_to_baseball_card(stats_response)


@router.get(
    "/{nmls_id}/license",
    response_model=LicenseInfoResponse,
    summary="Get license information",
    description="Fetch license details for a professional.",
)
async def get_license_info(
    nmls_id: str,
    provider: ProfessionalDataProvider = Depends(get_data_provider),
):
    """Get license information for a professional."""
    license_info = await provider.get_license_info(nmls_id)
    if not license_info:
        raise HTTPException(status_code=404, detail="License not found")

    return LicenseInfoResponse(
        nmls_id=license_info.nmls_id,
        name=license_info.name,
        license_type=license_info.license_type,
        status=license_info.status,
        issue_date=license_info.issue_date,
        expiry_date=license_info.expiry_date,
        state_licenses=license_info.state_licenses,
        company_name=license_info.company_name,
        company_nmls_id=license_info.company_nmls_id,
    )


@router.get(
    "/{nmls_id}/production",
    response_model=ProductionHistoryResponse,
    summary="Get production history",
    description="Fetch loan production history for a professional.",
)
async def get_production_history(
    nmls_id: str,
    start_date: Optional[date] = Query(None, description="Start of period"),
    end_date: Optional[date] = Query(None, description="End of period"),
    provider: ProfessionalDataProvider = Depends(get_data_provider),
):
    """Get production history for a professional."""
    history = await provider.get_production_history(nmls_id, start_date, end_date)
    if not history:
        raise HTTPException(status_code=404, detail="Production history not found")

    return ProductionHistoryResponse(
        nmls_id=history.nmls_id,
        period_start=history.period_start,
        period_end=history.period_end,
        total_loans=history.total_loans,
        total_volume=history.total_volume,
        average_loan_size=history.average_loan_size,
        conventional_count=history.conventional_count,
        conventional_volume=history.conventional_volume,
        fha_count=history.fha_count,
        fha_volume=history.fha_volume,
        va_count=history.va_count,
        va_volume=history.va_volume,
        usda_count=history.usda_count,
        usda_volume=history.usda_volume,
        jumbo_count=history.jumbo_count,
        jumbo_volume=history.jumbo_volume,
        purchase_count=history.purchase_count,
        purchase_volume=history.purchase_volume,
        refinance_count=history.refinance_count,
        refinance_volume=history.refinance_volume,
        state_rank=history.state_rank,
        national_rank=history.national_rank,
        loans=[],  # Don't include individual loans by default
    )


@router.get(
    "/{nmls_id}/verify",
    response_model=NMLSVerificationResponse,
    summary="Verify NMLS ID",
    description="Verify an NMLS ID is valid and active.",
)
async def verify_nmls(
    nmls_id: str,
    provider: ProfessionalDataProvider = Depends(get_data_provider),
):
    """Verify an NMLS ID."""
    is_valid = await provider.verify_nmls(nmls_id)

    if is_valid:
        license_info = await provider.get_license_info(nmls_id)
        return NMLSVerificationResponse(
            nmls_id=nmls_id,
            is_valid=True,
            is_active=license_info.status.value == "active" if license_info else False,
            name=license_info.name if license_info else None,
            company=license_info.company_name if license_info else None,
            message="NMLS ID verified successfully",
        )

    return NMLSVerificationResponse(
        nmls_id=nmls_id,
        is_valid=False,
        is_active=False,
        message="NMLS ID not found or invalid format",
    )


@router.post(
    "/search",
    response_model=List[LicenseInfoResponse],
    summary="Search professionals",
    description="Search for professionals by name, company, or state.",
)
async def search_professionals(
    request: ProfessionalSearchRequest,
    provider: ProfessionalDataProvider = Depends(get_data_provider),
):
    """Search for professionals."""
    results = await provider.search_professionals(
        name=request.name,
        company=request.company,
        state=request.state,
        limit=request.limit,
    )

    return [
        LicenseInfoResponse(
            nmls_id=r.nmls_id,
            name=r.name,
            license_type=r.license_type,
            status=r.status,
            issue_date=r.issue_date,
            expiry_date=r.expiry_date,
            state_licenses=r.state_licenses,
            company_name=r.company_name,
            company_nmls_id=r.company_nmls_id,
        )
        for r in results
    ]


@router.get(
    "/health",
    summary="Check provider health",
    description="Check if the data provider API is available.",
)
async def check_provider_health(
    provider: ProfessionalDataProvider = Depends(get_data_provider),
):
    """Check data provider health."""
    is_healthy = await provider.health_check()
    return {
        "provider": provider.provider_name,
        "healthy": is_healthy,
    }
