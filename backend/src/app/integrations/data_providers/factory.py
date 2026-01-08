"""
Factory for creating data provider instances.

Supports pluggable providers via configuration, with fallback chain support.
"""
import logging
from typing import Optional, Dict, List, Type
from functools import lru_cache

from src.app.config import settings
from src.app.integrations.data_providers.base import ProfessionalDataProvider
from src.app.integrations.data_providers.datagod import DatagodProvider
from src.app.integrations.data_providers.redr import RedrProvider
from src.app.integrations.data_providers.modex import ModexProvider
from src.app.integrations.data_providers.corelogic import CoreLogicProvider

logger = logging.getLogger(__name__)


# Registry of available providers
PROVIDER_REGISTRY: Dict[str, Type[ProfessionalDataProvider]] = {
    "datagod": DatagodProvider,
    "redr": RedrProvider,
    "modex": ModexProvider,
    "corelogic": CoreLogicProvider,
}

# Default fallback order when primary provider fails
DEFAULT_FALLBACK_ORDER: List[str] = ["datagod", "corelogic", "redr", "modex"]


class DataProviderFactory:
    """Factory for creating and managing data provider instances."""

    _instances: Dict[str, ProfessionalDataProvider] = {}

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> ProfessionalDataProvider:
        """
        Get a data provider instance.

        Args:
            provider_name: Name of the provider. If None, uses default from settings.

        Returns:
            ProfessionalDataProvider instance

        Raises:
            ValueError: If provider is not registered
        """
        if provider_name is None:
            provider_name = getattr(settings, 'DATA_PROVIDER', 'datagod')

        provider_name = provider_name.lower()

        # Return cached instance if available
        if provider_name in cls._instances:
            return cls._instances[provider_name]

        # Create new instance
        if provider_name not in PROVIDER_REGISTRY:
            available = ", ".join(PROVIDER_REGISTRY.keys())
            raise ValueError(
                f"Unknown data provider: {provider_name}. "
                f"Available providers: {available}"
            )

        provider_class = PROVIDER_REGISTRY[provider_name]
        instance = provider_class()
        cls._instances[provider_name] = instance

        return instance

    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: Type[ProfessionalDataProvider]
    ) -> None:
        """
        Register a new data provider.

        Args:
            name: Provider name (lowercase)
            provider_class: Provider class implementing ProfessionalDataProvider
        """
        PROVIDER_REGISTRY[name.lower()] = provider_class

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider names."""
        return list(PROVIDER_REGISTRY.keys())

    @classmethod
    async def close_all(cls) -> None:
        """Close all provider connections."""
        for provider in cls._instances.values():
            if hasattr(provider, 'close'):
                await provider.close()
        cls._instances.clear()


@lru_cache(maxsize=1)
def get_data_provider() -> ProfessionalDataProvider:
    """
    Dependency injection helper for FastAPI.

    Usage:
        @router.get("/stats/{nmls_id}")
        async def get_stats(
            nmls_id: str,
            provider: ProfessionalDataProvider = Depends(get_data_provider)
        ):
            return await provider.get_professional_stats(nmls_id)
    """
    return DataProviderFactory.get_provider()


def get_provider_fallback_order() -> List[str]:
    """
    Get the fallback order for providers.

    Returns configured primary provider first, then remaining providers
    in default order.
    """
    primary = getattr(settings, "data_provider", "datagod").lower()

    # Start with primary provider
    order = [primary]

    # Add remaining providers from default order
    for provider in DEFAULT_FALLBACK_ORDER:
        if provider not in order:
            order.append(provider)

    return order


def is_provider_configured(provider_name: str) -> bool:
    """
    Check if a provider has API credentials configured.

    Providers without credentials will be skipped in the fallback chain.
    """
    provider_name = provider_name.lower()

    # Check for provider-specific API key
    api_key_attr = f"{provider_name}_api_key"
    if hasattr(settings, api_key_attr):
        api_key = getattr(settings, api_key_attr)
        if api_key:
            return True

    # Fall back to generic API key for primary provider
    primary = getattr(settings, "data_provider", "datagod").lower()
    if provider_name == primary:
        generic_key = getattr(settings, "data_provider_api_key", None)
        if generic_key:
            return True

    return False


def get_configured_providers() -> List[str]:
    """
    Get list of providers that have API credentials configured.

    Useful for determining which providers can actually be used.
    """
    configured = []
    for provider_name in PROVIDER_REGISTRY.keys():
        if is_provider_configured(provider_name):
            configured.append(provider_name)

    # If no providers are configured, return all (for testing/mock mode)
    if not configured:
        logger.warning(
            "No data providers have API keys configured. "
            "Using all providers (mock mode)."
        )
        return list(PROVIDER_REGISTRY.keys())

    return configured
