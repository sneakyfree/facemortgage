"""
Tests for the data provider HTTP client.

Tests cover:
- CircuitBreaker state transitions
- RetryConfig delay calculations
- DataProviderHttpClient retry behavior
- Sensitive data redaction
"""
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.app.integrations.data_providers.http_client import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    DataProviderHttpClient,
    RetryConfig,
    redact_sensitive_data,
    SENSITIVE_HEADERS,
    SENSITIVE_PARAMS,
)


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    def test_circuit_starts_closed(self):
        """Circuit breaker should start in closed state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_allows_execution_when_closed(self):
        """Circuit should allow execution when closed."""
        cb = CircuitBreaker()
        assert cb.can_execute() is True

    def test_circuit_opens_after_threshold_failures(self):
        """Circuit should open after failure_threshold consecutive failures."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_circuit_rejects_when_open(self):
        """Circuit should reject requests when open."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
        cb.record_failure()  # Opens circuit
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_success_resets_failure_count(self):
        """Recording success should reset failure count in closed state."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_circuit_enters_half_open_after_timeout(self):
        """Circuit should enter half-open state after recovery timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.0)
        cb.record_failure()  # Opens circuit
        assert cb.state == CircuitState.OPEN

        # With recovery_timeout=0.0, should immediately allow
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_circuit_closes_after_successful_recovery(self):
        """Circuit should close after successful calls in half-open state."""
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.0,
            half_open_max_calls=2,
        )
        cb.record_failure()  # Opens circuit

        # Enter half-open
        cb.can_execute()
        assert cb.state == CircuitState.HALF_OPEN

        # Successful calls in half-open
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN  # Still half-open
        cb.record_success()
        assert cb.state == CircuitState.CLOSED  # Now closed

    def test_circuit_reopens_on_failure_in_half_open(self):
        """Circuit should reopen if failure occurs in half-open state."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.0)
        cb.record_failure()  # Opens circuit

        # Enter half-open
        cb.can_execute()
        assert cb.state == CircuitState.HALF_OPEN

        # Failure in half-open reopens
        cb.record_failure()
        assert cb.state == CircuitState.OPEN


class TestRetryConfig:
    """Tests for the RetryConfig class."""

    def test_default_values(self):
        """RetryConfig should have sensible defaults."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 10.0
        assert config.exponential_base == 2.0

    def test_exponential_delay_calculation(self):
        """get_delay should calculate exponential backoff correctly."""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=100.0)

        assert config.get_delay(0) == 1.0   # 1 * 2^0 = 1
        assert config.get_delay(1) == 2.0   # 1 * 2^1 = 2
        assert config.get_delay(2) == 4.0   # 1 * 2^2 = 4
        assert config.get_delay(3) == 8.0   # 1 * 2^3 = 8

    def test_delay_capped_at_max(self):
        """get_delay should not exceed max_delay."""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=5.0)

        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(3) == 5.0  # Would be 8, capped at 5
        assert config.get_delay(10) == 5.0  # Would be huge, capped at 5


class TestSensitiveDataRedaction:
    """Tests for the redact_sensitive_data function."""

    def test_redacts_sensitive_headers(self):
        """Should redact sensitive header values."""
        headers = {
            "Authorization": "Bearer secret123",
            "Content-Type": "application/json",
            "X-API-Key": "my-api-key",
        }

        redacted = redact_sensitive_data(headers, SENSITIVE_HEADERS)

        assert redacted["Authorization"] == "[REDACTED]"
        assert redacted["Content-Type"] == "application/json"
        assert redacted["X-API-Key"] == "[REDACTED]"

    def test_redacts_sensitive_params(self):
        """Should redact sensitive parameter values."""
        params = {
            "api_key": "secret",
            "address": "123 Main St",
            "token": "jwt-token",
        }

        redacted = redact_sensitive_data(params, SENSITIVE_PARAMS)

        assert redacted["api_key"] == "[REDACTED]"
        assert redacted["address"] == "123 Main St"
        assert redacted["token"] == "[REDACTED]"

    def test_handles_empty_dict(self):
        """Should handle empty dictionaries."""
        result = redact_sensitive_data({}, SENSITIVE_PARAMS)
        assert result == {}


class TestDataProviderHttpClient:
    """Tests for the DataProviderHttpClient class."""

    @pytest.mark.asyncio
    async def test_client_requires_context_manager(self):
        """Client should raise error if not used with context manager."""
        client = DataProviderHttpClient(
            base_url="https://api.test.com",
            provider_name="test",
        )

        with pytest.raises(RuntimeError, match="not initialized"):
            await client.get("/test")

    @pytest.mark.asyncio
    async def test_successful_get_request(self):
        """Client should handle successful GET requests."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            async with DataProviderHttpClient(
                base_url="https://api.test.com",
                provider_name="test",
            ) as client:
                # Replace internal client with mock
                client._client = mock_client
                response = await client.get("/endpoint", params={"key": "value"})

                assert response.status_code == 200
                mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_retries_on_timeout(self):
        """Client should retry on timeout exceptions."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            # First call times out, second succeeds
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.request = AsyncMock(
                side_effect=[
                    httpx.TimeoutException("timeout"),
                    mock_response,
                ]
            )
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            async with DataProviderHttpClient(
                base_url="https://api.test.com",
                provider_name="test",
                retry_config=RetryConfig(max_attempts=3, initial_delay=0.01),
            ) as client:
                client._client = mock_client
                response = await client.get("/endpoint")

                assert response.status_code == 200
                assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_retryable_status_codes(self):
        """Client should retry on retryable HTTP status codes."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            mock_503_response = MagicMock()
            mock_503_response.status_code = 503

            mock_200_response = MagicMock()
            mock_200_response.status_code = 200

            mock_client.request = AsyncMock(
                side_effect=[mock_503_response, mock_200_response]
            )
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            async with DataProviderHttpClient(
                base_url="https://api.test.com",
                provider_name="test",
                retry_config=RetryConfig(max_attempts=3, initial_delay=0.01),
            ) as client:
                client._client = mock_client
                response = await client.get("/endpoint")

                assert response.status_code == 200
                assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_requests(self):
        """Client should fail fast when circuit breaker is open."""
        circuit_breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
        circuit_breaker.record_failure()  # Open the circuit

        async with DataProviderHttpClient(
            base_url="https://api.test.com",
            provider_name="test",
            circuit_breaker=circuit_breaker,
        ) as client:
            with pytest.raises(CircuitOpenError):
                await client.get("/endpoint")

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises_exception(self):
        """Client should raise exception after exhausting retries."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            async with DataProviderHttpClient(
                base_url="https://api.test.com",
                provider_name="test",
                retry_config=RetryConfig(max_attempts=2, initial_delay=0.01),
            ) as client:
                client._client = mock_client

                with pytest.raises(httpx.TimeoutException):
                    await client.get("/endpoint")

                assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_post_request(self):
        """Client should handle POST requests."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 201

            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            async with DataProviderHttpClient(
                base_url="https://api.test.com",
                provider_name="test",
            ) as client:
                client._client = mock_client
                response = await client.post(
                    "/endpoint",
                    json={"key": "value"},
                )

                assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_headers_include_api_key(self):
        """Client should include API key in headers."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            async with DataProviderHttpClient(
                base_url="https://api.test.com",
                api_key="test-api-key",
                provider_name="test",
            ) as client:
                pass

            # Check that headers were passed to client
            call_kwargs = mock_client_class.call_args.kwargs
            assert "X-API-Key" in call_kwargs["headers"]
            assert call_kwargs["headers"]["X-API-Key"] == "test-api-key"

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Client close method should close the underlying client."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = DataProviderHttpClient(
                base_url="https://api.test.com",
                provider_name="test",
            )
            await client.__aenter__()
            await client.close()

            mock_client.aclose.assert_called_once()
            assert client._client is None
