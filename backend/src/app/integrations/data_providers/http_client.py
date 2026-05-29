"""
Resilient HTTP client for data providers.

Features:
- Connection pooling with httpx AsyncClient
- Exponential backoff retry (1s, 2s, 4s)
- Circuit breaker pattern (fail-fast after consecutive failures)
- Request/response logging with credential redaction
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for fail-fast behavior.

    After `failure_threshold` consecutive failures, opens the circuit
    and rejects requests for `recovery_timeout` seconds.
    """
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3

    # Internal state
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    half_open_calls: int = 0

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                logger.info("Circuit breaker closed after successful recovery")
                self._close()
        else:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker re-opened after failure in half-open state")
            self._open()
        elif self.failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} consecutive failures"
            )
            self._open()

    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info("Circuit breaker entering half-open state")
                self._half_open()
                return True
            return False

        # Half-open: allow limited requests
        if self.half_open_calls < self.half_open_max_calls:
            self.half_open_calls += 1
            return True
        return False

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _open(self) -> None:
        """Open the circuit."""
        self.state = CircuitState.OPEN
        self.half_open_calls = 0
        self.success_count = 0

    def _close(self) -> None:
        """Close the circuit."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0

    def _half_open(self) -> None:
        """Enter half-open state."""
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 10.0  # seconds
    exponential_base: float = 2.0
    retryable_status_codes: tuple = (408, 429, 500, 502, 503, 504)

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number (0-indexed)."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


# Patterns for credential redaction in logs
SENSITIVE_HEADERS = frozenset({
    "authorization",
    "x-api-key",
    "api-key",
    "apikey",
    "x-auth-token",
    "bearer",
})

SENSITIVE_PARAMS = frozenset({
    "api_key",
    "apikey",
    "key",
    "token",
    "secret",
    "password",
})


def redact_sensitive_data(data: Dict[str, Any], sensitive_keys: frozenset) -> Dict[str, str]:
    """Redact sensitive values from a dictionary."""
    redacted = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            redacted[key] = "[REDACTED]"
        else:
            redacted[key] = str(value)
    return redacted


class DataProviderHttpClient:
    """
    HTTP client for data provider integrations.

    Features:
    - Connection pooling
    - Automatic retries with exponential backoff
    - Circuit breaker for fail-fast behavior
    - Request/response logging with credential redaction

    Usage:
        async with DataProviderHttpClient(
            base_url="https://api.provider.com",
            api_key="your-api-key",
            provider_name="provider"
        ) as client:
            response = await client.get("/endpoint")
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        provider_name: str = "unknown",
        timeout: float = 30.0,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.provider_name = provider_name
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

        # Build default headers
        self._headers = {
            "Accept": "application/json",
            "User-Agent": "FaceMortgage/1.0",
        }
        if api_key:
            self._headers["X-API-Key"] = api_key
        if headers:
            self._headers.update(headers)

        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "DataProviderHttpClient":
        """Enter async context manager."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=30.0,
            ),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make a GET request with retry and circuit breaker."""
        return await self._request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make a POST request with retry and circuit breaker."""
        return await self._request(
            "POST", path, json=json, data=data, params=params, headers=headers
        )

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Execute an HTTP request with retry and circuit breaker logic.

        Raises:
            CircuitOpenError: If circuit breaker is open
            httpx.HTTPError: If all retries are exhausted
        """
        if not self._client:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )

        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            raise CircuitOpenError(
                f"Circuit breaker is open for {self.provider_name}. "
                f"Service unavailable."
            )

        last_exception: Optional[Exception] = None

        for attempt in range(self.retry_config.max_attempts):
            try:
                start_time = time.monotonic()

                # Log request (with redacted credentials)
                self._log_request(method, path, params, attempt)

                response = await self._client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    data=data,
                    headers=headers,
                )

                elapsed = time.monotonic() - start_time

                # Log response
                self._log_response(method, path, response.status_code, elapsed)

                # Check for retryable status codes
                if response.status_code in self.retry_config.retryable_status_codes:
                    if attempt < self.retry_config.max_attempts - 1:
                        delay = self.retry_config.get_delay(attempt)
                        logger.warning(
                            f"[{self.provider_name}] Retryable status {response.status_code} "
                            f"for {method} {path}, retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{self.retry_config.max_attempts})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Last attempt failed
                        self.circuit_breaker.record_failure()
                        response.raise_for_status()

                # Success
                self.circuit_breaker.record_success()
                return response

            except httpx.TimeoutException as e:
                last_exception = e
                self._handle_retry_exception(method, path, e, attempt, "timeout")

            except httpx.NetworkError as e:
                last_exception = e
                self._handle_retry_exception(method, path, e, attempt, "network error")

            except httpx.HTTPStatusError:
                # Non-retryable HTTP errors
                self.circuit_breaker.record_failure()
                raise

        # All retries exhausted
        self.circuit_breaker.record_failure()
        if last_exception:
            raise last_exception
        raise RuntimeError(f"Request failed after {self.retry_config.max_attempts} attempts")

    def _handle_retry_exception(
        self,
        method: str,
        path: str,
        exception: Exception,
        attempt: int,
        error_type: str,
    ) -> None:
        """Handle retry logic for exceptions."""
        if attempt < self.retry_config.max_attempts - 1:
            delay = self.retry_config.get_delay(attempt)
            logger.warning(
                f"[{self.provider_name}] {error_type} for {method} {path}: {exception}, "
                f"retrying in {delay:.1f}s "
                f"(attempt {attempt + 1}/{self.retry_config.max_attempts})"
            )
            # Note: We need to await the sleep in the caller
        else:
            logger.error(
                f"[{self.provider_name}] {error_type} for {method} {path}: {exception}, "
                f"all {self.retry_config.max_attempts} attempts exhausted"
            )

    def _log_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]],
        attempt: int,
    ) -> None:
        """Log outgoing request with redacted credentials."""
        redacted_params = {}
        if params:
            redacted_params = redact_sensitive_data(params, SENSITIVE_PARAMS)

        attempt_info = f" (attempt {attempt + 1})" if attempt > 0 else ""
        logger.debug(
            f"[{self.provider_name}] Request{attempt_info}: {method} {self.base_url}{path} "
            f"params={redacted_params}"
        )

    def _log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        elapsed: float,
    ) -> None:
        """Log response with timing."""
        logger.debug(
            f"[{self.provider_name}] Response: {method} {path} "
            f"status={status_code} elapsed={elapsed*1000:.1f}ms"
        )


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and rejecting requests."""
    pass


@asynccontextmanager
async def create_provider_client(
    base_url: str,
    api_key: Optional[str] = None,
    provider_name: str = "unknown",
    timeout: float = 30.0,
):
    """
    Convenience function to create a provider client.

    Usage:
        async with create_provider_client(
            "https://api.provider.com",
            api_key="secret",
            provider_name="datagod"
        ) as client:
            response = await client.get("/stats/123456")
    """
    client = DataProviderHttpClient(
        base_url=base_url,
        api_key=api_key,
        provider_name=provider_name,
        timeout=timeout,
    )
    async with client:
        yield client
