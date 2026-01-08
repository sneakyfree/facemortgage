"""
Modex API integration for professional data.

This is a mock implementation that simulates the Modex API.
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


class ModexProvider(ProfessionalDataProvider):
    """
    Modex API provider for professional mortgage data.

    Modex specializes in mortgage industry intelligence with
    emphasis on competitive analytics and market positioning.

    API docs (hypothetical): https://api.modex.com/v3
    """

    def __init__(self):
        self.api_key = getattr(settings, 'MODEX_API_KEY', None)
        self.client_id = getattr(settings, 'MODEX_CLIENT_ID', None)
        self.base_url = getattr(settings, 'MODEX_BASE_URL', 'https://api.modex.com/v3')
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        return "Modex"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"ApiKey {self.api_key}",
                    "X-Client-ID": self.client_id or "",
                    "Content-Type": "application/json",
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
        Modex emphasizes competitive rankings and market analytics.
        """
        seed = int(hashlib.md5(f"modex_{nmls_id}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        first_names = ["Marcus", "Nicole", "Tyler", "Samantha", "Kevin",
                       "Rachel", "Justin", "Melissa", "Brandon", "Ashley"]
        last_names = ["Thompson", "Martinez", "Robinson", "Taylor", "White",
                      "Lee", "Walker", "Hall", "Allen", "Young"]
        companies = ["Modex Mortgage", "National Lending Corp", "American Home Finance",
                     "Premier Mortgage Services", "Elite Funding Group", "Nationwide Home Loans",
                     "Freedom Mortgage", "NewRez LLC", "loanDepot", "Mr. Cooper"]
        states = ["FL", "TX", "GA", "NC", "SC", "VA", "TN", "AL", "LA", "MS"]
        metros = ["Miami-Fort Lauderdale", "Dallas-Fort Worth", "Atlanta",
                  "Houston", "Tampa Bay", "Charlotte", "Nashville", "Austin"]

        years_in_industry = rng.randint(1, 30)
        total_loans = rng.randint(75, 2500)
        avg_loan = rng.randint(200000, 600000)

        return {
            "name": f"{rng.choice(first_names)} {rng.choice(last_names)}",
            "company": rng.choice(companies),
            "company_nmls": str(rng.randint(100000, 999999)),
            "states": rng.sample(states, k=rng.randint(2, 6)),
            "metros": rng.sample(metros, k=rng.randint(1, 3)),
            "years_in_industry": years_in_industry,
            "total_loans_career": total_loans,
            "total_volume_career": total_loans * avg_loan,
            "loans_12m": rng.randint(25, 180),
            "volume_12m": rng.randint(8000000, 80000000),
            "loans_ytd": rng.randint(8, 90),
            "volume_ytd": rng.randint(2500000, 40000000),
            "conventional_pct": rng.uniform(0.25, 0.55),
            "fha_pct": rng.uniform(0.15, 0.35),
            "va_pct": rng.uniform(0.10, 0.25),
            "purchase_pct": rng.uniform(0.45, 0.75),
            "state_rank": rng.randint(1, 600),
            "national_rank": rng.randint(1, 6000),
            "metro_rank": rng.randint(1, 200),
            "company_rank": rng.randint(1, 50) if rng.random() > 0.3 else None,
            "growth_yoy_pct": round(rng.uniform(-15, 45), 1),
            "market_share_pct": round(rng.uniform(0.05, 3.0), 2),
            "avg_days_to_close": rng.randint(25, 45),
            "status": rng.choice(["active"] * 9 + ["inactive"]),
            "issue_date": date.today() - timedelta(days=365 * years_in_industry + rng.randint(0, 365)),
            "expiry_date": date.today() + timedelta(days=rng.randint(90, 365 * 3)),
        }

    async def get_professional_stats(self, nmls_id: str) -> Optional[ProfessionalStats]:
        """
        Fetch aggregated statistics for a professional.

        Modex provides rich competitive analytics.

        In production, this would call:
        GET /professionals/{nmls_id}/analytics
        """
        await asyncio.sleep(0.10)

        data = self._generate_deterministic_data(nmls_id)
        license_info = await self.get_license_info(nmls_id)

        other_pct = max(0, 1.0 - data["conventional_pct"] - data["fha_pct"] - data["va_pct"])
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
            other_pct=round(other_pct * 100, 1),
            purchase_pct=round(data["purchase_pct"] * 100, 1),
            refinance_pct=round(refinance_pct * 100, 1),
            state_rank=data["state_rank"],
            national_rank=data["national_rank"],
            top_states=data["states"][:3],
            top_counties=[],  # Modex uses metros instead
            raw_data={
                "provider": "modex",
                "nmls_id": nmls_id,
                "metro_rank": data["metro_rank"],
                "company_rank": data["company_rank"],
                "growth_yoy_pct": data["growth_yoy_pct"],
                "market_share_pct": data["market_share_pct"],
                "avg_days_to_close": data["avg_days_to_close"],
                "top_metros": data["metros"],
            },
        )

    async def get_license_info(self, nmls_id: str) -> Optional[LicenseInfo]:
        """
        Fetch license information for a professional.

        In production, this would call:
        GET /professionals/{nmls_id}/license
        """
        await asyncio.sleep(0.05)

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

        Modex provides detailed competitive context.

        In production, this would call:
        GET /professionals/{nmls_id}/production?start={start}&end={end}
        """
        await asyncio.sleep(0.12)

        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()

        data = self._generate_deterministic_data(nmls_id)
        seed = int(hashlib.md5(f"modex_{nmls_id}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        num_loans = data["loans_12m"]
        loans = []

        loan_types = ["Conventional", "FHA", "VA", "USDA", "Non-QM"]
        purposes = ["Purchase", "Rate/Term Refi", "Cash-Out Refi"]
        property_types = ["SFR", "Condo", "Townhouse", "PUD", "2-4 Units"]

        for i in range(min(num_loans, 50)):
            loan_date = start_date + timedelta(days=rng.randint(0, (end_date - start_date).days))
            loans.append(LoanRecord(
                loan_id=f"MDX{nmls_id}{i:05d}",
                loan_amount=Decimal(str(rng.randint(150000, 1200000))),
                loan_type=rng.choice(loan_types),
                property_type=rng.choice(property_types),
                purpose=rng.choice(purposes),
                close_date=loan_date,
                state=rng.choice(data["states"]),
                county=None,
            ))

        conventional_loans = [l for l in loans if l.loan_type == "Conventional"]
        fha_loans = [l for l in loans if l.loan_type == "FHA"]
        va_loans = [l for l in loans if l.loan_type == "VA"]
        usda_loans = [l for l in loans if l.loan_type == "USDA"]
        nonqm_loans = [l for l in loans if l.loan_type == "Non-QM"]
        purchase_loans = [l for l in loans if l.purpose == "Purchase"]
        refi_loans = [l for l in loans if "Refi" in (l.purpose or "")]

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
            jumbo_count=len(nonqm_loans),  # Using jumbo slot for Non-QM
            jumbo_volume=sum(l.loan_amount for l in nonqm_loans),
            purchase_count=len(purchase_loans),
            purchase_volume=sum(l.loan_amount for l in purchase_loans),
            refinance_count=len(refi_loans),
            refinance_volume=sum(l.loan_amount for l in refi_loans),
            state_rank=data["state_rank"],
            national_rank=data["national_rank"],
            company_rank=data["company_rank"],
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
        GET /professionals/search?name={name}&company={company}&state={state}
        """
        await asyncio.sleep(0.15)

        results = []
        seed = hash(f"modex_{name}{company}{state}")
        rng = random.Random(seed)

        num_results = rng.randint(0, min(limit, 18))

        for i in range(num_results):
            mock_nmls = str(300000 + rng.randint(0, 699999))
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
        GET /professionals/{nmls_id}/verify
        """
        await asyncio.sleep(0.04)

        if not nmls_id.isdigit() or not (6 <= len(nmls_id) <= 8):
            return False

        license_info = await self.get_license_info(nmls_id)
        if not license_info:
            return False

        return license_info.status == LicenseStatus.ACTIVE

    async def health_check(self) -> bool:
        """Check if Modex API is available."""
        try:
            await asyncio.sleep(0.01)
            return True
        except (httpx.RequestError, httpx.HTTPStatusError, asyncio.TimeoutError):
            return False
