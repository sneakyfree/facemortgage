"""
Tests for the data provider caching layer.

Tests cover:
- CacheEntry freshness and staleness detection
- DataProviderCache get/set operations
- Stale-while-revalidate pattern
- Cache invalidation
- Cache statistics
"""
import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.exceptions import RedisError

from src.app.integrations.data_providers.cache import (
    CacheEntry,
    DataProviderCache,
    DecimalEncoder,
    json_serialize,
    json_deserialize,
)


class TestDecimalEncoder:
    """Tests for the DecimalEncoder class."""

    def test_encodes_decimal(self):
        """Should encode Decimal values as strings."""
        data = {"amount": Decimal("123.45")}
        result = json.dumps(data, cls=DecimalEncoder)
        assert result == '{"amount": "123.45"}'

    def test_encodes_datetime(self):
        """Should encode datetime values as ISO format strings."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        data = {"timestamp": dt}
        result = json.dumps(data, cls=DecimalEncoder)
        assert '"2024-01-15T10:30:00"' in result

    def test_encodes_enum(self):
        """Should encode Enum values by their value."""
        class Status(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        data = {"status": Status.ACTIVE}
        result = json.dumps(data, cls=DecimalEncoder)
        assert result == '{"status": "active"}'

    def test_encodes_complex_nested(self):
        """Should handle complex nested structures."""
        data = {
            "amount": Decimal("100.00"),
            "timestamp": datetime(2024, 1, 1),
            "nested": {
                "value": Decimal("50.00"),
            },
        }
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        assert parsed["amount"] == "100.00"
        assert parsed["nested"]["value"] == "50.00"


class TestCacheEntry:
    """Tests for the CacheEntry class."""

    def test_fresh_entry(self):
        """Entry should be fresh when within TTL."""
        entry = CacheEntry(
            value={"data": "test"},
            created_at=datetime.utcnow(),
            ttl_seconds=3600,
        )
        assert entry.is_fresh is True
        assert entry.is_stale is False
        assert entry.is_expired is False

    def test_stale_entry(self):
        """Entry should be stale when past TTL but within stale TTL."""
        created_at = datetime.utcnow() - timedelta(seconds=3700)
        entry = CacheEntry(
            value={"data": "test"},
            created_at=created_at,
            ttl_seconds=3600,
            stale_ttl_seconds=7200,
        )
        assert entry.is_fresh is False
        assert entry.is_stale is True
        assert entry.is_expired is False

    def test_expired_entry(self):
        """Entry should be expired when past stale TTL."""
        created_at = datetime.utcnow() - timedelta(seconds=8000)
        entry = CacheEntry(
            value={"data": "test"},
            created_at=created_at,
            ttl_seconds=3600,
            stale_ttl_seconds=7200,
        )
        assert entry.is_fresh is False
        assert entry.is_stale is False
        assert entry.is_expired is True

    def test_default_stale_ttl(self):
        """Stale TTL should default to 2x TTL."""
        entry = CacheEntry(
            value={"data": "test"},
            created_at=datetime.utcnow(),
            ttl_seconds=3600,
        )
        assert entry.stale_ttl_seconds == 7200

    def test_to_dict_and_from_dict(self):
        """Entry should round-trip through dict serialization."""
        original = CacheEntry(
            value={"data": "test"},
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            ttl_seconds=3600,
            stale_ttl_seconds=7200,
        )

        as_dict = original.to_dict()
        restored = CacheEntry.from_dict(as_dict)

        assert restored.value == original.value
        assert restored.ttl_seconds == original.ttl_seconds
        assert restored.stale_ttl_seconds == original.stale_ttl_seconds


class TestDataProviderCache:
    """Tests for the DataProviderCache class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()
        redis.delete = AsyncMock(return_value=1)
        redis.scan_iter = MagicMock()
        return redis

    @pytest.fixture
    def cache(self, mock_redis):
        """Create a DataProviderCache instance."""
        return DataProviderCache(
            redis=mock_redis,
            default_ttl_seconds=3600,
            default_stale_ttl_seconds=7200,
        )

    @pytest.mark.asyncio
    async def test_build_key(self, cache):
        """Should build correct cache keys."""
        key = cache._build_key("datagod", "123456", "stats")
        assert key == "facemortgage:provider:datagod:nmls:123456:stats"

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache, mock_redis):
        """Should return None on cache miss."""
        mock_redis.get.return_value = None

        result = await cache.get("datagod", "123456", "stats")

        assert result is None
        assert cache._misses == 1

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache, mock_redis):
        """Should return entry on cache hit."""
        entry_data = {
            "value": {"loan_count": 100},
            "created_at": datetime.utcnow().isoformat(),
            "ttl_seconds": 3600,
            "stale_ttl_seconds": 7200,
        }
        mock_redis.get.return_value = json_serialize(entry_data)

        result = await cache.get("datagod", "123456", "stats")

        assert result is not None
        assert result.value == {"loan_count": 100}
        assert cache._hits == 1

    @pytest.mark.asyncio
    async def test_get_stale_hit(self, cache, mock_redis):
        """Should return stale entry and increment stale hits."""
        created_at = datetime.utcnow() - timedelta(seconds=4000)
        entry_data = {
            "value": {"loan_count": 100},
            "created_at": created_at.isoformat(),
            "ttl_seconds": 3600,
            "stale_ttl_seconds": 7200,
        }
        mock_redis.get.return_value = json_serialize(entry_data)

        result = await cache.get("datagod", "123456", "stats")

        assert result is not None
        assert result.is_stale is True
        assert cache._stale_hits == 1

    @pytest.mark.asyncio
    async def test_get_expired_deletes_key(self, cache, mock_redis):
        """Should delete expired entries and return None."""
        created_at = datetime.utcnow() - timedelta(seconds=10000)
        entry_data = {
            "value": {"loan_count": 100},
            "created_at": created_at.isoformat(),
            "ttl_seconds": 3600,
            "stale_ttl_seconds": 7200,
        }
        mock_redis.get.return_value = json_serialize(entry_data)

        result = await cache.get("datagod", "123456", "stats")

        assert result is None
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_handles_redis_error(self, cache, mock_redis):
        """Should handle Redis errors gracefully."""
        mock_redis.get.side_effect = RedisError("Connection failed")

        result = await cache.get("datagod", "123456", "stats")

        assert result is None
        assert cache._misses == 1

    @pytest.mark.asyncio
    async def test_set_success(self, cache, mock_redis):
        """Should successfully set cache entries."""
        result = await cache.set(
            "datagod",
            "123456",
            {"loan_count": 100},
            "stats",
        )

        assert result is True
        mock_redis.setex.assert_called_once()

        # Verify the key and TTL
        call_args = mock_redis.setex.call_args
        assert "facemortgage:provider:datagod:nmls:123456:stats" in call_args[0][0]
        assert call_args[0][1] == 7200  # stale_ttl

    @pytest.mark.asyncio
    async def test_set_handles_redis_error(self, cache, mock_redis):
        """Should handle Redis errors on set."""
        mock_redis.setex.side_effect = RedisError("Connection failed")

        result = await cache.set(
            "datagod",
            "123456",
            {"loan_count": 100},
            "stats",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_single_key(self, cache, mock_redis):
        """Should invalidate a single cache key."""
        mock_redis.delete.return_value = 1

        deleted = await cache.invalidate("datagod", "123456", "stats")

        assert deleted == 1
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_all_for_nmls(self, cache, mock_redis):
        """Should invalidate all keys for an NMLS ID."""
        # Mock scan_iter to return keys
        async def mock_scan_iter(match):
            yield b"facemortgage:provider:datagod:nmls:123456:stats"
            yield b"facemortgage:provider:datagod:nmls:123456:license"

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 2

        deleted = await cache.invalidate("datagod", "123456")

        assert deleted == 2

    @pytest.mark.asyncio
    async def test_invalidate_provider(self, cache, mock_redis):
        """Should invalidate all keys for a provider."""
        async def mock_scan_iter(match):
            yield b"facemortgage:provider:datagod:nmls:111:stats"
            yield b"facemortgage:provider:datagod:nmls:222:stats"
            yield b"facemortgage:provider:datagod:nmls:333:stats"

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 3

        deleted = await cache.invalidate_provider("datagod")

        assert deleted == 3

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, cache, mock_redis):
        """Should return cached value without calling fetch function."""
        entry_data = {
            "value": {"loan_count": 100},
            "created_at": datetime.utcnow().isoformat(),
            "ttl_seconds": 3600,
            "stale_ttl_seconds": 7200,
        }
        mock_redis.get.return_value = json_serialize(entry_data)

        fetch_func = AsyncMock(return_value={"loan_count": 200})

        result = await cache.get_or_set(
            "datagod",
            "123456",
            fetch_func,
            "stats",
        )

        assert result == {"loan_count": 100}
        fetch_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, cache, mock_redis):
        """Should fetch and cache on miss."""
        mock_redis.get.return_value = None

        fetch_func = AsyncMock(return_value={"loan_count": 200})

        result = await cache.get_or_set(
            "datagod",
            "123456",
            fetch_func,
            "stats",
        )

        assert result == {"loan_count": 200}
        fetch_func.assert_called_once()
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_stale_triggers_refresh(self, cache, mock_redis):
        """Should return stale data and trigger background refresh."""
        created_at = datetime.utcnow() - timedelta(seconds=4000)
        entry_data = {
            "value": {"loan_count": 100},
            "created_at": created_at.isoformat(),
            "ttl_seconds": 3600,
            "stale_ttl_seconds": 7200,
        }
        mock_redis.get.return_value = json_serialize(entry_data)

        fetch_func = AsyncMock(return_value={"loan_count": 200})

        result = await cache.get_or_set(
            "datagod",
            "123456",
            fetch_func,
            "stats",
            allow_stale=True,
        )

        # Should return stale data immediately
        assert result == {"loan_count": 100}

        # Give background task time to run
        await asyncio.sleep(0.1)

        # Background refresh should have been called
        fetch_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_fetch_error_returns_stale(self, cache, mock_redis):
        """Should return stale data if fetch fails."""
        created_at = datetime.utcnow() - timedelta(seconds=8000)  # Expired
        entry_data = {
            "value": {"loan_count": 100},
            "created_at": created_at.isoformat(),
            "ttl_seconds": 3600,
            "stale_ttl_seconds": 10000,  # Still within stale window
        }
        # First call returns expired data, triggering fetch
        mock_redis.get.return_value = json_serialize(entry_data)

        fetch_func = AsyncMock(side_effect=Exception("API Error"))

        # Since our entry is not fresh, but is_stale would be True
        # We need to adjust the entry to be stale, not expired
        created_at = datetime.utcnow() - timedelta(seconds=4000)
        entry_data["created_at"] = created_at.isoformat()
        mock_redis.get.return_value = json_serialize(entry_data)

        result = await cache.get_or_set(
            "datagod",
            "123456",
            fetch_func,
            "stats",
            allow_stale=True,
        )

        # Should return stale data since fetch failed
        assert result == {"loan_count": 100}

    def test_get_stats(self, cache):
        """Should return correct cache statistics."""
        cache._hits = 80
        cache._misses = 15
        cache._stale_hits = 5

        stats = cache.get_stats()

        assert stats["hits"] == 80
        assert stats["misses"] == 15
        assert stats["stale_hits"] == 5
        assert stats["total_requests"] == 100
        assert stats["hit_rate_percent"] == 80.0
        assert stats["stale_hit_rate_percent"] == 5.0

    def test_reset_stats(self, cache):
        """Should reset all statistics."""
        cache._hits = 100
        cache._misses = 50
        cache._stale_hits = 25

        cache.reset_stats()

        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._stale_hits == 0


class TestJsonSerialization:
    """Tests for JSON serialization utilities."""

    def test_json_serialize_deserialize_roundtrip(self):
        """Data should survive serialization/deserialization."""
        original = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        serialized = json_serialize(original)
        deserialized = json_deserialize(serialized)

        assert deserialized == original

    def test_json_serialize_handles_special_types(self):
        """Should serialize Decimal and datetime correctly."""
        data = {
            "amount": Decimal("123.45"),
            "timestamp": datetime(2024, 1, 15, 10, 30, 0),
        }

        serialized = json_serialize(data)
        deserialized = json_deserialize(serialized)

        assert deserialized["amount"] == "123.45"
        assert deserialized["timestamp"] == "2024-01-15T10:30:00"
