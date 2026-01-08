"""
Data normalization layer for external data providers.

Standardizes data from different providers into consistent formats:
- Loan type names
- State/county formats
- Currency decimals
- Ranking systems
"""
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any


# Standard loan type mappings
LOAN_TYPE_MAPPINGS: Dict[str, str] = {
    # Conventional variations
    "conventional": "Conventional",
    "conv": "Conventional",
    "conforming": "Conventional",
    "fnma": "Conventional",
    "fhlmc": "Conventional",
    "fannie mae": "Conventional",
    "freddie mac": "Conventional",

    # FHA variations
    "fha": "FHA",
    "federal housing administration": "FHA",
    "fha 203b": "FHA",
    "fha 203k": "FHA",

    # VA variations
    "va": "VA",
    "veterans affairs": "VA",
    "veteran": "VA",
    "veterans": "VA",

    # USDA variations
    "usda": "USDA",
    "rural development": "USDA",
    "rd": "USDA",
    "rural housing": "USDA",

    # Jumbo variations
    "jumbo": "Jumbo",
    "non-conforming": "Jumbo",
    "nonconforming": "Jumbo",
    "super conforming": "Jumbo",

    # Other types
    "heloc": "HELOC",
    "home equity": "HELOC",
    "reverse": "Reverse",
    "hecm": "Reverse",
    "construction": "Construction",
    "renovation": "Renovation",
    "bridge": "Bridge",
}

# Standard loan purpose mappings
LOAN_PURPOSE_MAPPINGS: Dict[str, str] = {
    "purchase": "Purchase",
    "buy": "Purchase",
    "acquisition": "Purchase",

    "refinance": "Refinance",
    "refi": "Refinance",
    "rate/term": "Refinance",
    "rate and term": "Refinance",

    "cash-out": "Cash-Out Refinance",
    "cashout": "Cash-Out Refinance",
    "cash out": "Cash-Out Refinance",
    "cash out refinance": "Cash-Out Refinance",

    "heloc": "HELOC",
    "home equity line": "HELOC",

    "construction": "Construction",
    "new construction": "Construction",
}

# State code to full name mapping
STATE_NAMES: Dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
    "PR": "Puerto Rico", "VI": "Virgin Islands", "GU": "Guam",
}

# Reverse mapping: full name to state code
STATE_CODES: Dict[str, str] = {v.lower(): k for k, v in STATE_NAMES.items()}


def normalize_loan_type(loan_type: Optional[str]) -> Optional[str]:
    """
    Normalize loan type to standard format.

    Args:
        loan_type: Raw loan type string from provider

    Returns:
        Standardized loan type or original if no mapping found
    """
    if not loan_type:
        return None

    normalized = loan_type.lower().strip()
    return LOAN_TYPE_MAPPINGS.get(normalized, loan_type.title())


def normalize_loan_purpose(purpose: Optional[str]) -> Optional[str]:
    """
    Normalize loan purpose to standard format.

    Args:
        purpose: Raw loan purpose string from provider

    Returns:
        Standardized loan purpose or original if no mapping found
    """
    if not purpose:
        return None

    normalized = purpose.lower().strip()
    return LOAN_PURPOSE_MAPPINGS.get(normalized, purpose.title())


def normalize_state(state: Optional[str]) -> Optional[str]:
    """
    Normalize state to 2-letter code.

    Args:
        state: State name or code

    Returns:
        2-letter state code or original if not recognized
    """
    if not state:
        return None

    state = state.strip()

    # Already a code?
    if len(state) == 2:
        return state.upper()

    # Try to find by name
    state_lower = state.lower()
    if state_lower in STATE_CODES:
        return STATE_CODES[state_lower]

    return state


def normalize_state_name(state: Optional[str]) -> Optional[str]:
    """
    Convert state code to full name.

    Args:
        state: State code or name

    Returns:
        Full state name
    """
    if not state:
        return None

    state = state.strip().upper()

    # Already a full name?
    if state.lower() in STATE_CODES:
        return state.title()

    # Try to find by code
    return STATE_NAMES.get(state, state)


def normalize_county(county: Optional[str], state: Optional[str] = None) -> Optional[str]:
    """
    Normalize county name to consistent format.

    Args:
        county: Raw county name
        state: Optional state for disambiguation

    Returns:
        Normalized county name
    """
    if not county:
        return None

    county = county.strip()

    # Remove common suffixes
    county = re.sub(r'\s+county$', '', county, flags=re.IGNORECASE)
    county = re.sub(r'\s+parish$', '', county, flags=re.IGNORECASE)
    county = re.sub(r'\s+borough$', '', county, flags=re.IGNORECASE)

    # Title case
    county = county.title()

    return county


def normalize_currency(
    amount: Any,
    decimal_places: int = 2,
    round_to_nearest: Optional[int] = None,
) -> Decimal:
    """
    Normalize currency amount to consistent decimal format.

    Args:
        amount: Raw amount (int, float, str, or Decimal)
        decimal_places: Number of decimal places
        round_to_nearest: Round to nearest N (e.g., 1000 for thousands)

    Returns:
        Normalized Decimal amount
    """
    if amount is None:
        return Decimal("0")

    # Convert to Decimal
    if isinstance(amount, Decimal):
        result = amount
    elif isinstance(amount, str):
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,\s]', '', amount)
        result = Decimal(cleaned) if cleaned else Decimal("0")
    else:
        result = Decimal(str(amount))

    # Round to nearest if specified
    if round_to_nearest:
        result = (result / round_to_nearest).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * round_to_nearest

    # Apply decimal places
    quantize_str = f"0.{'0' * decimal_places}"
    result = result.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

    return result


def normalize_percentage(value: Any, decimal_places: int = 1) -> float:
    """
    Normalize percentage to consistent format.

    Handles both 0.45 (45%) and 45 (45%) formats.

    Args:
        value: Raw percentage value
        decimal_places: Number of decimal places

    Returns:
        Normalized percentage (0-100 scale)
    """
    if value is None:
        return 0.0

    try:
        num = float(value)
    except (ValueError, TypeError):
        return 0.0

    # If value is less than 1, assume it's a decimal (0.45 = 45%)
    if 0 < num < 1:
        num = num * 100

    return round(num, decimal_places)


@dataclass
class RankingScale:
    """Configuration for normalizing ranking systems."""
    min_rank: int  # Best rank (usually 1)
    max_rank: int  # Worst rank (varies by provider)
    label: str  # Human-readable label


# Known ranking scales from different providers
RANKING_SCALES: Dict[str, RankingScale] = {
    "datagod": RankingScale(min_rank=1, max_rank=100, label="Top 100"),
    "corelogic": RankingScale(min_rank=1, max_rank=1000, label="Top 1000"),
    "redr": RankingScale(min_rank=1, max_rank=500, label="Top 500"),
    "modex": RankingScale(min_rank=1, max_rank=100, label="Percentile"),
}


def normalize_ranking(
    rank: Optional[int],
    source_provider: str,
    target_scale: int = 100,
) -> Optional[int]:
    """
    Normalize ranking to unified scale.

    Different providers use different ranking scales.
    This normalizes to a consistent 1-100 scale.

    Args:
        rank: Raw rank from provider
        source_provider: Name of the source provider
        target_scale: Target scale maximum (default 100)

    Returns:
        Normalized rank (1-100) or None if invalid
    """
    if rank is None:
        return None

    source_provider = source_provider.lower()

    if source_provider not in RANKING_SCALES:
        # Unknown provider, return as-is if within target scale
        return rank if rank <= target_scale else None

    scale = RANKING_SCALES[source_provider]

    # Normalize to 0-1 range then scale to target
    normalized = (rank - scale.min_rank) / (scale.max_rank - scale.min_rank)
    result = int(normalized * (target_scale - 1)) + 1

    return min(max(result, 1), target_scale)


def get_ranking_percentile(rank: int, total: int) -> float:
    """
    Calculate percentile from rank.

    Args:
        rank: Current rank (1 = best)
        total: Total population size

    Returns:
        Percentile (0-100, higher = better)
    """
    if total <= 0:
        return 0.0

    # Rank 1 out of 100 = 99th percentile
    percentile = ((total - rank) / total) * 100
    return round(max(0, min(100, percentile)), 1)


class DataNormalizer:
    """
    Utility class for normalizing provider data.

    Usage:
        normalizer = DataNormalizer(provider_name="datagod")
        stats = normalizer.normalize_stats(raw_data)
    """

    def __init__(self, provider_name: str):
        self.provider_name = provider_name.lower()

    def normalize_loan_types(self, types: List[str]) -> List[str]:
        """Normalize a list of loan types."""
        normalized = []
        seen = set()

        for t in types:
            norm_type = normalize_loan_type(t)
            if norm_type and norm_type not in seen:
                normalized.append(norm_type)
                seen.add(norm_type)

        return normalized

    def normalize_states(self, states: List[str]) -> List[str]:
        """Normalize a list of states to codes."""
        normalized = []
        seen = set()

        for s in states:
            norm_state = normalize_state(s)
            if norm_state and norm_state not in seen:
                normalized.append(norm_state)
                seen.add(norm_state)

        return normalized

    def normalize_volume(self, amount: Any) -> Decimal:
        """Normalize loan volume to standard format."""
        return normalize_currency(amount, decimal_places=2)

    def normalize_rank(self, rank: Optional[int]) -> Optional[int]:
        """Normalize ranking to 1-100 scale."""
        return normalize_ranking(rank, self.provider_name)

    def normalize_loan_breakdown(
        self,
        breakdown: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Normalize loan type breakdown.

        Args:
            breakdown: Dict mapping loan types to counts/volumes

        Returns:
            Normalized breakdown with standard loan type names
        """
        result: Dict[str, Dict[str, Any]] = {}

        for loan_type, data in breakdown.items():
            norm_type = normalize_loan_type(loan_type)
            if not norm_type:
                continue

            if norm_type not in result:
                result[norm_type] = {"count": 0, "volume": Decimal("0")}

            if isinstance(data, dict):
                result[norm_type]["count"] += data.get("count", 0)
                result[norm_type]["volume"] += normalize_currency(
                    data.get("volume", 0)
                )
            else:
                # Assume it's just a count
                result[norm_type]["count"] += int(data)

        return result

    def normalize_state_breakdown(
        self,
        breakdown: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Normalize state breakdown.

        Args:
            breakdown: Dict mapping states to counts/volumes

        Returns:
            Normalized breakdown with standard state codes
        """
        result: Dict[str, Dict[str, Any]] = {}

        for state, data in breakdown.items():
            norm_state = normalize_state(state)
            if not norm_state:
                continue

            if norm_state not in result:
                result[norm_state] = {"count": 0, "volume": Decimal("0")}

            if isinstance(data, dict):
                result[norm_state]["count"] += data.get("count", 0)
                result[norm_state]["volume"] += normalize_currency(
                    data.get("volume", 0)
                )
            else:
                result[norm_state]["count"] += int(data)

        return result
