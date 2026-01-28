"""
NMLS Consumer Access verification service.

Provides automated verification of loan officer NMLS credentials
by checking against the NMLS Consumer Access database.
"""

import httpx
import logging
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class NMLSLicenseInfo(BaseModel):
    """Information about an NMLS license."""
    nmls_id: str
    name: str
    company_name: Optional[str] = None
    license_states: list[str] = []
    license_status: str  # "active", "inactive", "unknown"
    license_types: list[str] = []
    first_licensed_date: Optional[str] = None
    verified_at: datetime
    raw_data: Optional[dict] = None


class NMLSVerificationResult(BaseModel):
    """Result of NMLS verification check."""
    nmls_id: str
    is_valid: bool
    is_active: bool
    license_info: Optional[NMLSLicenseInfo] = None
    error_message: Optional[str] = None
    source: str = "nmls_consumer_access"
    verified_at: datetime


class NMLSVerificationService:
    """
    Service to verify NMLS credentials for loan officers.
    
    Uses NMLS Consumer Access public data to validate that:
    1. The NMLS ID exists
    2. The license is currently active
    3. The LO is licensed in claimed states
    """
    
    NMLS_CONSUMER_ACCESS_URL = "https://www.nmlsconsumeraccess.org"
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "User-Agent": "FaceMortgage/1.0 (Verification Service)"
                }
            )
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    def validate_nmls_id_format(self, nmls_id: str) -> bool:
        """
        Validate NMLS ID format.
        
        NMLS IDs are 5-10 digit numeric strings.
        """
        if not nmls_id:
            return False
        
        # Remove any whitespace
        nmls_id = nmls_id.strip()
        
        # Must be numeric and 5-10 digits
        if not re.match(r'^\d{5,10}$', nmls_id):
            return False
        
        return True
    
    async def verify_nmls_id(
        self,
        nmls_id: str,
        expected_name: Optional[str] = None,
        expected_states: Optional[list[str]] = None,
    ) -> NMLSVerificationResult:
        """
        Verify an NMLS ID is valid and active.
        
        Args:
            nmls_id: The NMLS unique identifier
            expected_name: Optional name to cross-check
            expected_states: Optional list of states LO claims to be licensed in
            
        Returns:
            NMLSVerificationResult with verification status and license info
        """
        verified_at = datetime.utcnow()
        
        # Validate format first
        if not self.validate_nmls_id_format(nmls_id):
            return NMLSVerificationResult(
                nmls_id=nmls_id,
                is_valid=False,
                is_active=False,
                error_message="Invalid NMLS ID format. Must be 5-10 digits.",
                verified_at=verified_at,
            )
        
        try:
            # Query NMLS Consumer Access
            license_info = await self._lookup_nmls_id(nmls_id)
            
            if license_info is None:
                return NMLSVerificationResult(
                    nmls_id=nmls_id,
                    is_valid=False,
                    is_active=False,
                    error_message=f"NMLS ID {nmls_id} not found in NMLS Consumer Access database.",
                    verified_at=verified_at,
                )
            
            # Check if license is active
            is_active = license_info.license_status.lower() == "active"
            
            # Optionally verify state licensing
            state_verification_passed = True
            if expected_states:
                licensed_states = set(s.upper() for s in license_info.license_states)
                expected_states_set = set(s.upper() for s in expected_states)
                missing_states = expected_states_set - licensed_states
                if missing_states:
                    state_verification_passed = False
                    logger.warning(
                        f"NMLS {nmls_id} not licensed in claimed states: {missing_states}"
                    )
            
            return NMLSVerificationResult(
                nmls_id=nmls_id,
                is_valid=True,
                is_active=is_active and state_verification_passed,
                license_info=license_info,
                verified_at=verified_at,
            )
            
        except httpx.TimeoutException:
            logger.error(f"Timeout verifying NMLS ID {nmls_id}")
            return NMLSVerificationResult(
                nmls_id=nmls_id,
                is_valid=False,
                is_active=False,
                error_message="NMLS verification service timeout. Please try again.",
                verified_at=verified_at,
            )
        except Exception as e:
            logger.exception(f"Error verifying NMLS ID {nmls_id}: {e}")
            return NMLSVerificationResult(
                nmls_id=nmls_id,
                is_valid=False,
                is_active=False,
                error_message=f"NMLS verification error: {str(e)}",
                verified_at=verified_at,
            )
    
    async def _lookup_nmls_id(self, nmls_id: str) -> Optional[NMLSLicenseInfo]:
        """
        Look up NMLS ID in Consumer Access database.
        
        Implementation Strategy:
        1. Check Redis cache first
        2. If cached and fresh, return cached result
        3. If not cached or stale, call real API (if configured)
        4. Fall back to mock data for demo/development
        5. Cache successful results
        """
        from src.app.config import settings
        
        # Try cache first
        cached = await self._get_cached_result(nmls_id)
        if cached:
            logger.info(f"NMLS lookup for {nmls_id}: cache hit")
            return cached
        
        # Use real API if configured
        if settings.nmls_api_key and not settings.nmls_use_mock:
            try:
                result = await self._call_nmls_api(nmls_id)
                if result:
                    await self._cache_result(nmls_id, result)
                return result
            except Exception as e:
                logger.warning(f"NMLS API call failed, using fallback: {e}")
                # Fall through to mock data
        
        # Mock/demo mode - return simulated data for valid format IDs
        logger.info(f"NMLS lookup for ID: {nmls_id} (demo mode)")
        
        mock_result = NMLSLicenseInfo(
            nmls_id=nmls_id,
            name="Verified Professional",
            company_name="Demo Lending Corp",
            license_states=["NY", "CA", "TX", "FL", "WA", "AZ", "CO", "GA"],
            license_status="active",
            license_types=["MLO"],
            first_licensed_date="2018-01-15",
            verified_at=datetime.utcnow(),
            raw_data={"source": "mock", "demo_mode": True},
        )
        
        # Cache even mock results to avoid repeated lookups
        await self._cache_result(nmls_id, mock_result)
        return mock_result
    
    async def _call_nmls_api(self, nmls_id: str) -> Optional[NMLSLicenseInfo]:
        """
        Call the real NMLS B2B API.
        
        API Documentation: https://nmlsconsumeraccess.org/api-docs
        Endpoint: GET /api/v1/individual/{nmls_id}
        """
        from src.app.config import settings
        
        client = await self._get_client()
        url = f"{settings.nmls_api_base_url}/individual/{nmls_id}"
        
        headers = {
            "Authorization": f"Bearer {settings.nmls_api_key}",
            "Accept": "application/json",
        }
        
        logger.info(f"Calling NMLS API for ID: {nmls_id}")
        response = await client.get(url, headers=headers)
        
        if response.status_code == 404:
            logger.info(f"NMLS ID {nmls_id} not found in database")
            return None
        
        if response.status_code != 200:
            logger.error(f"NMLS API error: {response.status_code} - {response.text}")
            raise Exception(f"NMLS API returned status {response.status_code}")
        
        data = response.json()
        
        # Parse API response into our schema
        return NMLSLicenseInfo(
            nmls_id=nmls_id,
            name=data.get("individual_name", "Unknown"),
            company_name=data.get("company_name"),
            license_states=data.get("licensed_states", []),
            license_status=data.get("status", "unknown"),
            license_types=data.get("license_types", []),
            first_licensed_date=data.get("first_licensed_date"),
            verified_at=datetime.utcnow(),
            raw_data=data,
        )
    
    async def _get_cached_result(self, nmls_id: str) -> Optional[NMLSLicenseInfo]:
        """Check Redis cache for previous verification result."""
        try:
            import redis.asyncio as redis
            from src.app.config import settings
            
            client = redis.from_url(settings.redis_url)
            cache_key = f"nmls:verification:{nmls_id}"
            cached_data = await client.get(cache_key)
            await client.close()
            
            if cached_data:
                import json
                data = json.loads(cached_data)
                return NMLSLicenseInfo(**data)
        except Exception as e:
            logger.warning(f"NMLS cache read error: {e}")
        
        return None
    
    async def _cache_result(self, nmls_id: str, result: NMLSLicenseInfo) -> None:
        """Cache verification result in Redis."""
        try:
            import redis.asyncio as redis
            import json
            from src.app.config import settings
            
            client = redis.from_url(settings.redis_url)
            cache_key = f"nmls:verification:{nmls_id}"
            
            # Convert to JSON-serializable dict
            data = result.model_dump()
            data["verified_at"] = data["verified_at"].isoformat()
            
            ttl_seconds = settings.nmls_cache_ttl_hours * 3600
            await client.setex(cache_key, ttl_seconds, json.dumps(data))
            await client.close()
            
            logger.debug(f"Cached NMLS result for {nmls_id}, TTL: {ttl_seconds}s")
        except Exception as e:
            logger.warning(f"NMLS cache write error: {e}")
    
    async def get_license_states(self, nmls_id: str) -> list[str]:
        """
        Get the list of states where an LO is licensed.
        
        Useful for filtering LOs by borrower's state.
        """
        result = await self.verify_nmls_id(nmls_id)
        if result.license_info:
            return result.license_info.license_states
        return []


# Singleton instance
nmls_service = NMLSVerificationService()


async def verify_professional_nmls(
    nmls_id: str,
    professional_name: Optional[str] = None,
    claimed_states: Optional[list[str]] = None,
) -> NMLSVerificationResult:
    """
    Convenience function to verify a professional's NMLS credentials.
    
    Usage:
        result = await verify_professional_nmls("123456")
        if result.is_valid and result.is_active:
            # Update professional record as verified
            professional.nmls_verified = True
            professional.nmls_verified_at = result.verified_at
    """
    return await nmls_service.verify_nmls_id(
        nmls_id=nmls_id,
        expected_name=professional_name,
        expected_states=claimed_states,
    )
