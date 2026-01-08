"""
Fallback provider chain for data provider resilience.

Implements the chain-of-responsibility pattern to try multiple
data providers in order until one succeeds.
"""
import logging
from datetime import date
from typing import List, Optional

from redis.asyncio import Redis

from src.app.integrations.data_providers.base import (
    LicenseInfo,
    ProductionHistory,
    ProfessionalDataProvider,
    ProfessionalStats,
)
from src.app.integrations.data_providers.cache import (
    DataProviderCache,
    get_provider_cache,
)
from src.app.integrations.data_providers.factory import DataProviderFactory
from src.app.integrations.data_providers.http_client import CircuitOpenError

logger = logging.getLogger(__name__)


class ServiceUnavailableError(Exception):
    """Raised when all providers in the chain are unavailable."""
    pass


class DataProviderChain:
    """
    Chain of data providers with fallback support.

    Tries providers in order until one succeeds. Integrates with
    caching layer to minimize external API calls.

    Usage:
        chain = DataProviderChain(
            provider_names=["datagod", "corelogic"],
            cache=cache_instance,
        )
        stats = await chain.get_stats("123456")
    """

    def __init__(
        self,
        provider_names: List[str],
        cache: Optional[DataProviderCache] = None,
        use_cache: bool = True,
    ):
        """
        Initialize the provider chain.

        Args:
            provider_names: Ordered list of provider names to try
            cache: Optional cache instance for caching results
            use_cache: Whether to use caching (default True)
        """
        if not provider_names:
            raise ValueError("At least one provider must be specified")

        self.provider_names = provider_names
        self.cache = cache
        self.use_cache = use_cache and cache is not None

        # Validate all providers exist
        for name in provider_names:
            try:
                DataProviderFactory.get_provider(name)
            except ValueError as e:
                logger.warning(f"Provider '{name}' not available: {e}")

    def _get_providers(self) -> List[tuple[str, ProfessionalDataProvider]]:
        """Get list of available provider instances."""
        providers = []
        for name in self.provider_names:
            try:
                provider = DataProviderFactory.get_provider(name)
                providers.append((name, provider))
            except ValueError:
                continue
        return providers

    async def get_professional_stats(
        self,
        nmls_id: str,
        skip_cache: bool = False,
    ) -> Optional[ProfessionalStats]:
        """
        Get professional stats, trying providers in order.

        Args:
            nmls_id: NMLS ID of the professional
            skip_cache: If True, bypass cache and fetch fresh data

        Returns:
            ProfessionalStats or None if not found

        Raises:
            ServiceUnavailableError: If all providers fail
        """
        # Try cache first
        if self.use_cache and not skip_cache:
            for provider_name in self.provider_names:
                entry = await self.cache.get(provider_name, nmls_id, "stats")
                if entry is not None and not entry.is_expired:
                    logger.debug(
                        f"Cache hit for stats {nmls_id} from {provider_name}"
                    )
                    # Reconstruct ProfessionalStats from cached dict
                    return self._dict_to_stats(entry.value, nmls_id)

        # Try each provider
        providers = self._get_providers()
        errors = []

        for provider_name, provider in providers:
            try:
                logger.debug(f"Trying {provider_name} for stats {nmls_id}")
                stats = await provider.get_professional_stats(nmls_id)

                if stats is not None:
                    # Cache the result
                    if self.use_cache:
                        await self.cache.set(
                            provider_name,
                            nmls_id,
                            self._stats_to_dict(stats),
                            "stats",
                        )
                    logger.info(
                        f"Got stats for {nmls_id} from {provider_name}"
                    )
                    return stats

                logger.debug(f"No stats found for {nmls_id} in {provider_name}")

            except CircuitOpenError as e:
                logger.warning(
                    f"Circuit open for {provider_name}, skipping: {e}"
                )
                errors.append((provider_name, str(e)))
                continue

            except Exception as e:
                logger.warning(
                    f"Provider {provider_name} failed for {nmls_id}: {e}"
                )
                errors.append((provider_name, str(e)))
                continue

        # All providers failed or returned None
        if errors:
            error_msg = "; ".join(f"{name}: {err}" for name, err in errors)
            raise ServiceUnavailableError(
                f"All providers failed for NMLS {nmls_id}: {error_msg}"
            )

        return None

    async def get_license_info(
        self,
        nmls_id: str,
        skip_cache: bool = False,
    ) -> Optional[LicenseInfo]:
        """
        Get license info, trying providers in order.

        Args:
            nmls_id: NMLS ID of the professional
            skip_cache: If True, bypass cache

        Returns:
            LicenseInfo or None if not found

        Raises:
            ServiceUnavailableError: If all providers fail
        """
        # Try cache first
        if self.use_cache and not skip_cache:
            for provider_name in self.provider_names:
                entry = await self.cache.get(provider_name, nmls_id, "license")
                if entry is not None and not entry.is_expired:
                    logger.debug(
                        f"Cache hit for license {nmls_id} from {provider_name}"
                    )
                    return self._dict_to_license(entry.value, nmls_id)

        # Try each provider
        providers = self._get_providers()
        errors = []

        for provider_name, provider in providers:
            try:
                logger.debug(f"Trying {provider_name} for license {nmls_id}")
                license_info = await provider.get_license_info(nmls_id)

                if license_info is not None:
                    if self.use_cache:
                        await self.cache.set(
                            provider_name,
                            nmls_id,
                            self._license_to_dict(license_info),
                            "license",
                        )
                    logger.info(
                        f"Got license for {nmls_id} from {provider_name}"
                    )
                    return license_info

            except CircuitOpenError as e:
                logger.warning(f"Circuit open for {provider_name}: {e}")
                errors.append((provider_name, str(e)))
                continue

            except Exception as e:
                logger.warning(
                    f"Provider {provider_name} failed for license {nmls_id}: {e}"
                )
                errors.append((provider_name, str(e)))
                continue

        if errors:
            error_msg = "; ".join(f"{name}: {err}" for name, err in errors)
            raise ServiceUnavailableError(
                f"All providers failed for license {nmls_id}: {error_msg}"
            )

        return None

    async def get_production_history(
        self,
        nmls_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip_cache: bool = False,
    ) -> Optional[ProductionHistory]:
        """
        Get production history, trying providers in order.

        Args:
            nmls_id: NMLS ID of the professional
            start_date: Start of period
            end_date: End of period
            skip_cache: If True, bypass cache

        Returns:
            ProductionHistory or None if not found

        Raises:
            ServiceUnavailableError: If all providers fail
        """
        # Production history is time-sensitive, shorter cache key
        cache_key = f"production_{start_date}_{end_date}"

        # Try cache first
        if self.use_cache and not skip_cache:
            for provider_name in self.provider_names:
                entry = await self.cache.get(provider_name, nmls_id, cache_key)
                if entry is not None and not entry.is_expired:
                    logger.debug(
                        f"Cache hit for production {nmls_id} from {provider_name}"
                    )
                    return self._dict_to_production(entry.value, nmls_id)

        # Try each provider
        providers = self._get_providers()
        errors = []

        for provider_name, provider in providers:
            try:
                logger.debug(f"Trying {provider_name} for production {nmls_id}")
                history = await provider.get_production_history(
                    nmls_id, start_date, end_date
                )

                if history is not None:
                    if self.use_cache:
                        # Shorter TTL for production data (more time-sensitive)
                        await self.cache.set(
                            provider_name,
                            nmls_id,
                            self._production_to_dict(history),
                            cache_key,
                            ttl_seconds=6 * 3600,  # 6 hours
                        )
                    logger.info(
                        f"Got production for {nmls_id} from {provider_name}"
                    )
                    return history

            except CircuitOpenError as e:
                logger.warning(f"Circuit open for {provider_name}: {e}")
                errors.append((provider_name, str(e)))
                continue

            except Exception as e:
                logger.warning(
                    f"Provider {provider_name} failed for production {nmls_id}: {e}"
                )
                errors.append((provider_name, str(e)))
                continue

        if errors:
            error_msg = "; ".join(f"{name}: {err}" for name, err in errors)
            raise ServiceUnavailableError(
                f"All providers failed for production {nmls_id}: {error_msg}"
            )

        return None

    async def verify_nmls(self, nmls_id: str) -> bool:
        """
        Verify NMLS ID is valid, trying providers in order.

        Returns True if any provider confirms the NMLS is valid.
        """
        providers = self._get_providers()

        for provider_name, provider in providers:
            try:
                is_valid = await provider.verify_nmls(nmls_id)
                if is_valid:
                    logger.debug(
                        f"NMLS {nmls_id} verified by {provider_name}"
                    )
                    return True
            except Exception as e:
                logger.warning(
                    f"Provider {provider_name} failed NMLS verification: {e}"
                )
                continue

        return False

    async def health_check(self) -> dict:
        """
        Check health of all providers in the chain.

        Returns:
            Dict with provider name -> health status
        """
        results = {}
        providers = self._get_providers()

        for provider_name, provider in providers:
            try:
                is_healthy = await provider.health_check()
                results[provider_name] = {
                    "healthy": is_healthy,
                    "error": None,
                }
            except Exception as e:
                results[provider_name] = {
                    "healthy": False,
                    "error": str(e),
                }

        return results

    # Serialization helpers
    def _stats_to_dict(self, stats: ProfessionalStats) -> dict:
        """Convert ProfessionalStats to dict for caching."""
        from dataclasses import asdict
        return asdict(stats)

    def _dict_to_stats(self, data: dict, nmls_id: str) -> ProfessionalStats:
        """Convert cached dict back to ProfessionalStats."""
        from datetime import datetime
        from decimal import Decimal

        # Handle datetime conversion
        if isinstance(data.get("fetched_at"), str):
            data["fetched_at"] = datetime.fromisoformat(data["fetched_at"])

        # Handle Decimal conversions
        for field in [
            "total_volume_career",
            "volume_last_12_months",
            "avg_loan_size_12_months",
            "volume_ytd",
        ]:
            if field in data and data[field] is not None:
                data[field] = Decimal(str(data[field]))

        return ProfessionalStats(**data)

    def _license_to_dict(self, license_info: LicenseInfo) -> dict:
        """Convert LicenseInfo to dict for caching."""
        from dataclasses import asdict
        return asdict(license_info)

    def _dict_to_license(self, data: dict, nmls_id: str) -> LicenseInfo:
        """Convert cached dict back to LicenseInfo."""
        from datetime import date as date_type
        from src.app.integrations.data_providers.base import LicenseStatus

        # Handle date conversions
        for field in ["issue_date", "expiry_date"]:
            if field in data and data[field] is not None:
                if isinstance(data[field], str):
                    data[field] = date_type.fromisoformat(data[field])

        # Handle enum conversion
        if "status" in data and isinstance(data["status"], str):
            data["status"] = LicenseStatus(data["status"])

        return LicenseInfo(**data)

    def _production_to_dict(self, production: ProductionHistory) -> dict:
        """Convert ProductionHistory to dict for caching."""
        from dataclasses import asdict
        return asdict(production)

    def _dict_to_production(self, data: dict, nmls_id: str) -> ProductionHistory:
        """Convert cached dict back to ProductionHistory."""
        from datetime import date as date_type
        from decimal import Decimal

        # Handle date conversions
        for field in ["period_start", "period_end"]:
            if field in data and isinstance(data[field], str):
                data[field] = date_type.fromisoformat(data[field])

        # Handle Decimal conversions
        decimal_fields = [
            "total_volume",
            "average_loan_size",
            "conventional_volume",
            "fha_volume",
            "va_volume",
            "usda_volume",
            "jumbo_volume",
            "purchase_volume",
            "refinance_volume",
        ]
        for field in decimal_fields:
            if field in data and data[field] is not None:
                data[field] = Decimal(str(data[field]))

        # Handle nested loans if present
        if "loans" in data:
            from src.app.integrations.data_providers.base import LoanRecord
            loans = []
            for loan_data in data["loans"]:
                if "close_date" in loan_data and isinstance(
                    loan_data["close_date"], str
                ):
                    loan_data["close_date"] = date_type.fromisoformat(
                        loan_data["close_date"]
                    )
                if "loan_amount" in loan_data:
                    loan_data["loan_amount"] = Decimal(str(loan_data["loan_amount"]))
                loans.append(LoanRecord(**loan_data))
            data["loans"] = loans

        return ProductionHistory(**data)


async def create_provider_chain(
    redis: Redis,
    provider_names: Optional[List[str]] = None,
) -> DataProviderChain:
    """
    Create a provider chain with caching.

    Args:
        redis: Redis connection
        provider_names: List of provider names, or None for default

    Returns:
        Configured DataProviderChain
    """
    from src.app.config import settings

    if provider_names is None:
        # Use configured default provider, with fallbacks
        default_provider = getattr(settings, "data_provider", "datagod")
        provider_names = [default_provider]

        # Add common fallbacks if not already in list
        fallbacks = ["datagod", "corelogic", "redr", "modex"]
        for fallback in fallbacks:
            if fallback not in provider_names:
                provider_names.append(fallback)

    cache = await get_provider_cache(redis)

    return DataProviderChain(
        provider_names=provider_names,
        cache=cache,
        use_cache=True,
    )
