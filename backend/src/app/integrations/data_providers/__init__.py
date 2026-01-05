"""
External data provider integrations for professional statistics.

Supports pluggable providers: Datagod, Reeder, Modex, CoreLogic
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
)
from src.app.integrations.data_providers.datagod import DatagodProvider

__all__ = [
    "ProfessionalDataProvider",
    "ProfessionalStats",
    "LicenseInfo",
    "LicenseStatus",
    "ProductionHistory",
    "LoanRecord",
    "DataProviderFactory",
    "get_data_provider",
    "DatagodProvider",
]
