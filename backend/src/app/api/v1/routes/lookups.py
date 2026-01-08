from typing import List, Optional
import httpx
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from sqlalchemy import select

from src.app.core.dependencies import DbSession
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.professional import Specialty, Language, County
from src.app.schemas.professional import SpecialtyResponse, LanguageResponse, CountyResponse


# US State mappings
US_STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
    'PR': 'Puerto Rico', 'VI': 'Virgin Islands', 'GU': 'Guam',
    'AS': 'American Samoa', 'MP': 'Northern Mariana Islands'
}

STATE_NAMES_TO_CODES = {v.lower(): k for k, v in US_STATES.items()}


class GeoLocationResponse(BaseModel):
    """Response model for geo-location detection."""
    state_code: Optional[str] = None
    state_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = "unknown"


def normalize_state_code(state_input: Optional[str]) -> Optional[str]:
    """Normalize a state name or code to a valid 2-letter state code."""
    if not state_input:
        return None

    upper = state_input.upper().strip()
    if upper in US_STATES:
        return upper

    lower = state_input.lower().strip()
    return STATE_NAMES_TO_CODES.get(lower)

router = APIRouter()


@router.get("/specialties", response_model=List[SpecialtyResponse])
@limiter.limit(RATE_LIMITS["api_read"])
async def list_specialties(
    request: Request,
    db: DbSession,
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """List all available specialties."""
    query = select(Specialty)
    if category:
        query = query.where(Specialty.category == category)
    query = query.order_by(Specialty.name)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/languages", response_model=List[LanguageResponse])
@limiter.limit(RATE_LIMITS["api_read"])
async def list_languages(request: Request, db: DbSession):
    """List all available languages."""
    query = select(Language).order_by(Language.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/counties", response_model=List[CountyResponse])
@limiter.limit(RATE_LIMITS["api_read"])
async def list_counties(
    request: Request,
    db: DbSession,
    state_code: Optional[str] = Query(None, description="Filter by state code"),
):
    """List counties, optionally filtered by state."""
    query = select(County)
    if state_code:
        query = query.where(County.state_code == state_code.upper())
    query = query.order_by(County.state_code, County.county_name)

    result = await db.execute(query)
    return result.scalars().all()


def get_client_ip(request: Request) -> Optional[str]:
    """Extract the client IP address from the request, handling proxies."""
    # Check common proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first (client IP)
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return None


async def reverse_geocode_coordinates(lat: float, lon: float) -> GeoLocationResponse:
    """Reverse geocode coordinates to get location details."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # Use BigDataCloud free API (no key required)
            response = await client.get(
                "https://api.bigdatacloud.net/data/reverse-geocode-client",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "localityLanguage": "en"
                }
            )

            if response.status_code == 200:
                data = response.json()
                state_code = None

                # Extract state code from principalSubdivisionCode (format: US-CA)
                subdivision_code = data.get("principalSubdivisionCode", "")
                if subdivision_code.startswith("US-"):
                    state_code = subdivision_code[3:]
                else:
                    state_code = normalize_state_code(data.get("principalSubdivision"))

                return GeoLocationResponse(
                    state_code=state_code,
                    state_name=US_STATES.get(state_code) if state_code else data.get("principalSubdivision"),
                    city=data.get("city") or data.get("locality"),
                    country=data.get("countryCode", "US"),
                    latitude=lat,
                    longitude=lon,
                    source="coordinates"
                )
        except Exception:
            pass

    return GeoLocationResponse(
        latitude=lat,
        longitude=lon,
        source="coordinates"
    )


async def geolocate_ip(ip: str) -> GeoLocationResponse:
    """Geolocate an IP address to get location details."""
    # Skip private/local IPs
    if ip in ("127.0.0.1", "localhost", "::1") or ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
        return GeoLocationResponse(source="ip")

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Try ip-api.com first (free, no key required, 45 requests/minute)
        try:
            response = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,country,regionName,region,city,lat,lon"}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    state_code = normalize_state_code(data.get("region"))
                    return GeoLocationResponse(
                        state_code=state_code,
                        state_name=data.get("regionName") or US_STATES.get(state_code),
                        city=data.get("city"),
                        country=data.get("country"),
                        latitude=data.get("lat"),
                        longitude=data.get("lon"),
                        source="ip"
                    )
        except Exception:
            pass

        # Fallback to ipapi.co (free tier)
        try:
            response = await client.get(f"https://ipapi.co/{ip}/json/")

            if response.status_code == 200:
                data = response.json()
                if not data.get("error"):
                    state_code = normalize_state_code(data.get("region_code"))
                    return GeoLocationResponse(
                        state_code=state_code,
                        state_name=data.get("region") or US_STATES.get(state_code),
                        city=data.get("city"),
                        country=data.get("country_name"),
                        latitude=data.get("latitude"),
                        longitude=data.get("longitude"),
                        source="ip"
                    )
        except Exception:
            pass

    return GeoLocationResponse(source="ip")


@router.get("/geo", response_model=GeoLocationResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_geo_location(
    request: Request,
    lat: Optional[float] = Query(None, description="Latitude for reverse geocoding"),
    lon: Optional[float] = Query(None, description="Longitude for reverse geocoding"),
    ip: Optional[str] = Query(None, description="IP address to geolocate (optional, uses client IP if not provided)"),
):
    """
    Detect geographic location based on coordinates or IP address.

    Priority:
    1. If lat/lon are provided, reverse geocode coordinates
    2. If ip is provided, geolocate that IP
    3. Otherwise, use the client's IP address from the request

    Returns state/region information for filtering professionals.
    """
    # Priority 1: Coordinates provided
    if lat is not None and lon is not None:
        return await reverse_geocode_coordinates(lat, lon)

    # Priority 2: Explicit IP provided
    target_ip = ip or get_client_ip(request)

    if target_ip:
        return await geolocate_ip(target_ip)

    # No location data available
    return GeoLocationResponse(source="unknown")


@router.get("/states")
@limiter.limit(RATE_LIMITS["api_read"])
async def list_states(request: Request):
    """List all US states with their codes and names."""
    return [
        {"code": code, "name": name}
        for code, name in sorted(US_STATES.items(), key=lambda x: x[1])
    ]
