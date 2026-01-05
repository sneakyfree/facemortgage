"""
Redr.com API integration for professional data.

This is a mock implementation that simulates the Redr API.
Replace with actual API calls when credentials are available.
"""
import asyncio
import hashlib
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List
import httpx

from src.app.config import settings
from src.app.integrations.data_providers.base import (
    ProfessionalDataProvider,
    ProfessionalStats,
    LicenseInfo,
    LicenseStatus,
    ProductionHistory,
    LoanRecord,
)


class RedrProvider(ProfessionalDataProvider):
    """
    Redr.com API provider for professional mortgage data.

    Redr focuses on real estate and mortgage transaction data
    with emphasis on geographic market analysis.

    API docs: https://api.redr.com/docs
    """

    def __init__(self):
        self.api_key = getattr(settings, 'REDR_API_KEY', None)
        self.base_url = getattr(settings, 'REDR_BASE_URL', 'https://api.redr.com/v2')
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        return "Redr"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-API-Key": self.api_key or "",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _generate_deterministic_data(self, nmls_id: str) -> dict:
        """
        Generate deterministic mock data based on NMLS ID.
        Redr uses different data patterns than Datagod.
        """
        # Use hash with Redr-specific salt
        seed = int(hashlib.md5(f"redr_{nmls_id}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        first_names = ["Amanda", "Brian", "Christine", "Derek", "Emily",
                       "Frank", "Grace", "Henry", "Irene", "Jason"]
        last_names = ["Anderson", "Baker", "Clark", "Davis", "Edwards",
                      "Foster", "Green", "Harris", "Irving", "Jackson"]
        companies = ["Redr Mortgage Group", "Pacific Home Lending", "Summit Funding",
                     "CMG Financial", "Fairway Independent", "Guild Mortgage",
                     "Caliber Home Loans", "Movement Mortgage", "CrossCountry Mortgage"]
        states = ["CA", "WA", "OR", "AZ", "NV", "CO", "UT", "ID", "TX", "FL"]
        counties = ["Los Angeles", "Maricopa", "San Diego", "Orange", "King",
                    "Clark", "Santa Clara", "Alameda", "Riverside", "Denver"]

        years_in_industry = rng.randint(3, 20)
        total_loans = rng.randint(100, 1500)
        avg_loan = rng.randint(300000, 850000)

        return {
            "name": f"{rng.choice(first_names)} {rng.choice(last_names)}",
            "company": rng.choice(companies),
            "company_nmls": str(rng.randint(100000, 999999)),
            "states": rng.sample(states, k=rng.randint(1, 4)),
            "counties": rng.sample(counties, k=rng.randint(2, 5)),
            "years_in_industry": years_in_industry,
            "total_loans_career": total_loans,
            "total_volume_career": total_loans * avg_loan,
            "loans_12m": rng.randint(30, 120),
            "volume_12m": rng.randint(10000000, 60000000),
            "loans_ytd": rng.randint(10, 60),
            "volume_ytd": rng.randint(3000000, 30000000),
            "conventional_pct": rng.uniform(0.35, 0.65),
            "fha_pct": rng.uniform(0.08, 0.25),
            "va_pct": rng.uniform(0.03, 0.15),
            "jumbo_pct": rng.uniform(0.05, 0.25),
            "purchase_pct": rng.uniform(0.5, 0.85),
            "state_rank": rng.randint(1, 400) if rng.random() > 0.25 else None,
            "national_rank": rng.randint(1, 4000) if rng.random() > 0.4 else None,
            "market_share_pct": round(rng.uniform(0.1, 2.5), 2),
            "status": rng.choice(["active", "active", "active", "active", "inactive"]),
            "issue_date": date.today() - timedelta(days=365 * years_in_industry + rng.randint(0, 365)),
            "expiry_date": date.today() + timedelta(days=rng.randint(60, 365 * 2)),
        }

    async def get_professional_stats(self, nmls_id: str) -> Optional[ProfessionalStats]:
        """
        Fetch aggregated statistics for a professional.

        In production, this would call:
        GET /originators/{nmls_id}/summary
        """
        await asyncio.sleep(0.12)

        data = self._generate_deterministic_data(nmls_id)
        license_info = await self.get_license_info(nmls_id)

        # Reeder provides jumbo separately, calculate other
        other_pct = max(0, 1.0 - data["conventional_pct"] - data["fha_pct"] - data["va_pct"] - data["jumbo_pct"])
        refinance_pct = 1.0 - data["purchase_pct"]

        return ProfessionalStats(
            nmls_id=nmls_id,
            fetched_at=datetime.utcnow(),
            license=license_info,
            years_in_industry=data["years_in_industry"],
            total_loans_career=data["total_loans_career"],
            total_volume_career=Decimal(str(data["total_volume_career"])),
            loans_last_12_months=data["loans_12m"],
            volume_last_12_months=Decimal(str(data["volume_12m"])),
            avg_loan_size_12_months=Decimal(str(data["volume_12m"] // max(1, data["loans_12m"]))),
            loans_ytd=data["loans_ytd"],
            volume_ytd=Decimal(str(data["volume_ytd"])),
            conventional_pct=round(data["conventional_pct"] * 100, 1),
            fha_pct=round(data["fha_pct"] * 100, 1),
            va_pct=round(data["va_pct"] * 100, 1),
            other_pct=round((other_pct + data["jumbo_pct"]) * 100, 1),
            purchase_pct=round(data["purchase_pct"] * 100, 1),
            refinance_pct=round(refinance_pct * 100, 1),
            state_rank=data["state_rank"],
            national_rank=data["national_rank"],
            top_states=data["states"][:3],
            top_counties=data["counties"][:3],
            raw_data={
                "provider": "redr",
                "nmls_id": nmls_id,
                "market_share_pct": data["market_share_pct"],
                "jumbo_pct": round(data["jumbo_pct"] * 100, 1),
            },
        )

    async def get_license_info(self, nmls_id: str) -> Optional[LicenseInfo]:
        """
        Fetch license information for a professional.

        In production, this would call:
        GET /originators/{nmls_id}/license
        """
        await asyncio.sleep(0.06)

        data = self._generate_deterministic_data(nmls_id)

        status_map = {
            "active": LicenseStatus.ACTIVE,
            "inactive": LicenseStatus.INACTIVE,
            "expired": LicenseStatus.EXPIRED,
            "suspended": LicenseStatus.SUSPENDED,
        }

        return LicenseInfo(
            nmls_id=nmls_id,
            name=data["name"],
            license_type="MLO",
            status=status_map.get(data["status"], LicenseStatus.INACTIVE),
            issue_date=data["issue_date"],
            expiry_date=data["expiry_date"],
            state_licenses=data["states"],
            company_name=data["company"],
            company_nmls_id=data["company_nmls"],
        )

    async def get_production_history(
        self,
        nmls_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Optional[ProductionHistory]:
        """
        Fetch production history for a professional.

        Reeder emphasizes geographic market data.

        In production, this would call:
        GET /originators/{nmls_id}/transactions?from={start}&to={end}
        """
        await asyncio.sleep(0.15)

        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()

        data = self._generate_deterministic_data(nmls_id)
        seed = int(hashlib.md5(f"redr_{nmls_id}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        num_loans = data["loans_12m"]
        loans = []

        loan_types = ["Conventional", "FHA", "VA", "Jumbo", "USDA"]
        purposes = ["Purchase", "Refinance", "Cash-out Refinance"]
        property_types = ["Single Family", "Condo", "Townhome", "2-4 Unit"]

        for i in range(min(num_loans, 50)):
            loan_date = start_date + timedelta(days=rng.randint(0, (end_date - start_date).days))
            loans.append(LoanRecord(
                loan_id=f"REDR{nmls_id}{i:05d}",
                loan_amount=Decimal(str(rng.randint(200000, 1800000))),
                loan_type=rng.choice(loan_types),
                property_type=rng.choice(property_types),
                purpose=rng.choice(purposes),
                close_date=loan_date,
                state=rng.choice(data["states"]),
                county=rng.choice(data["counties"]),
            ))

        # Calculate breakdown
        conventional_loans = [l for l in loans if l.loan_type == "Conventional"]
        fha_loans = [l for l in loans if l.loan_type == "FHA"]
        va_loans = [l for l in loans if l.loan_type == "VA"]
        usda_loans = [l for l in loans if l.loan_type == "USDA"]
        jumbo_loans = [l for l in loans if l.loan_type == "Jumbo"]
        purchase_loans = [l for l in loans if l.purpose == "Purchase"]
        refi_loans = [l for l in loans if "Refinance" in (l.purpose or "")]

        total_volume = sum(l.loan_amount for l in loans)

        return ProductionHistory(
            nmls_id=nmls_id,
            period_start=start_date,
            period_end=end_date,
            total_loans=len(loans),
            total_volume=total_volume,
            average_loan_size=total_volume / len(loans) if loans else Decimal("0"),
            conventional_count=len(conventional_loans),
            conventional_volume=sum(l.loan_amount for l in conventional_loans),
            fha_count=len(fha_loans),
            fha_volume=sum(l.loan_amount for l in fha_loans),
            va_count=len(va_loans),
            va_volume=sum(l.loan_amount for l in va_loans),
            usda_count=len(usda_loans),
            usda_volume=sum(l.loan_amount for l in usda_loans),
            jumbo_count=len(jumbo_loans),
            jumbo_volume=sum(l.loan_amount for l in jumbo_loans),
            purchase_count=len(purchase_loans),
            purchase_volume=sum(l.loan_amount for l in purchase_loans),
            refinance_count=len(refi_loans),
            refinance_volume=sum(l.loan_amount for l in refi_loans),
            state_rank=data["state_rank"],
            national_rank=data["national_rank"],
            loans=loans,
        )

    async def search_professionals(
        self,
        name: Optional[str] = None,
        company: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 20,
    ) -> List[LicenseInfo]:
        """
        Search for professionals by criteria.

        In production, this would call:
        GET /originators/search?q={name}&company={company}&state={state}
        """
        await asyncio.sleep(0.18)

        results = []
        seed = hash(f"redr_{name}{company}{state}")
        rng = random.Random(seed)

        num_results = rng.randint(0, min(limit, 15))

        for i in range(num_results):
            mock_nmls = str(200000 + rng.randint(0, 799999))
            info = await self.get_license_info(mock_nmls)
            if info:
                if state and state not in info.state_licenses:
                    continue
                results.append(info)
                if len(results) >= limit:
                    break

        return results

    async def verify_nmls(self, nmls_id: str) -> bool:
        """
        Verify that an NMLS ID is valid and active.

        In production, this would call:
        GET /originators/{nmls_id}/verify
        """
        await asyncio.sleep(0.05)

        if not nmls_id.isdigit() or not (6 <= len(nmls_id) <= 8):
            return False

        license_info = await self.get_license_info(nmls_id)
        if not license_info:
            return False

        return license_info.status == LicenseStatus.ACTIVE

    async def health_check(self) -> bool:
        """Check if Redr API is available."""
        try:
            await asyncio.sleep(0.01)
            return True
        except Exception:
            return False
