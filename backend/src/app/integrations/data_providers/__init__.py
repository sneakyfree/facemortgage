"""
External data provider integrations for professional statistics.

Supports pluggable providers: Datagod, Redr, Modex, CoreLogic

Features:
- Factory pattern for provider instantiation
- Fallback chain for high availability
- Redis-backed caching with stale-while-revalidate
- Circuit breaker for fail-fast behavior
- Exponential backoff retry logic
"""
from src.app.integrations.data_providers.base import (
    ProfessionalDataProvider,
    ProfessionalStats,
    LicenseInfo,
    LicenseStatus,
    ProductionHistory,
    LoanRecord,
)
from src.app.integrations.data_providers.factory import (
    DataProviderFactory,
    get_data_provider,
    get_provider_fallback_order,
    get_configured_providers,
    is_provider_configured,
)
from src.app.integrations.data_providers.datagod import DatagodProvider
from src.app.integrations.data_providers.http_client import (
    DataProviderHttpClient,
    CircuitBreaker,
    CircuitOpenError,
    RetryConfig,
    create_provider_client,
)
from src.app.integrations.data_providers.cache import (
    DataProviderCache,
    CacheEntry,
    get_provider_cache,
)
from src.app.integrations.data_providers.chain import (
    DataProviderChain,
    ServiceUnavailableError,
    create_provider_chain,
)
from src.app.integrations.data_providers.normalizer import (
    DataNormalizer,
    normalize_loan_type,
    normalize_loan_purpose,
    normalize_state,
    normalize_state_name,
    normalize_county,
    normalize_currency,
    normalize_percentage,
    normalize_ranking,
)

__all__ = [
    # Base classes
    "ProfessionalDataProvider",
    "ProfessionalStats",
    "LicenseInfo",
    "LicenseStatus",
    "ProductionHistory",
    "LoanRecord",
    # Factory
    "DataProviderFactory",
    "get_data_provider",
    "get_provider_fallback_order",
    "get_configured_providers",
    "is_provider_configured",
    # HTTP client
    "DataProviderHttpClient",
    "CircuitBreaker",
    "CircuitOpenError",
    "RetryConfig",
    "create_provider_client",
    # Cache
    "DataProviderCache",
    "CacheEntry",
    "get_provider_cache",
    # Chain
    "DataProviderChain",
    "ServiceUnavailableError",
    "create_provider_chain",
    # Normalizer
    "DataNormalizer",
    "normalize_loan_type",
    "normalize_loan_purpose",
    "normalize_state",
    "normalize_state_name",
    "normalize_county",
    "normalize_currency",
    "normalize_percentage",
    "normalize_ranking",
    # Providers
    "DatagodProvider",
]
