"""
Redis-backed caching layer for data provider responses.

Features:
- TTL-based caching with configurable expiration
- Stale-while-revalidate pattern for better availability
- Cache invalidation API
- Metrics for cache hit/miss rates
"""
import asyncio
import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union

from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal, datetime, and Enum types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        return super().default(obj)


def json_serialize(obj: Any) -> str:
    """Serialize object to JSON string."""
    return json.dumps(obj, cls=DecimalEncoder)


def json_deserialize(data: str) -> Any:
    """Deserialize JSON string to object."""
    return json.loads(data)


class CacheEntry(Generic[T]):
    """
    Cache entry with value and metadata.

    Supports stale-while-revalidate pattern by tracking
    both data freshness and staleness.
    """

    def __init__(
        self,
        value: T,
        created_at: datetime,
        ttl_seconds: int,
        stale_ttl_seconds: Optional[int] = None,
    ):
        self.value = value
        self.created_at = created_at
        self.ttl_seconds = ttl_seconds
        self.stale_ttl_seconds = stale_ttl_seconds or (ttl_seconds * 2)

    @property
    def is_fresh(self) -> bool:
        """Check if the entry is still fresh."""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age < self.ttl_seconds

    @property
    def is_stale(self) -> bool:
        """Check if the entry is stale but usable."""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return self.ttl_seconds <= age < self.stale_ttl_seconds

    @property
    def is_expired(self) -> bool:
        """Check if the entry is completely expired."""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age >= self.stale_ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "stale_ttl_seconds": self.stale_ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(
            value=data["value"],
            created_at=datetime.fromisoformat(data["created_at"]),
            ttl_seconds=data["ttl_seconds"],
            stale_ttl_seconds=data.get("stale_ttl_seconds"),
        )


class DataProviderCache:
    """
    Redis-backed cache for data provider responses.

    Key format: provider:{provider_name}:nmls:{nmls_id}:{data_type}

    Features:
    - Automatic TTL management
    - Stale-while-revalidate for better availability
    - Background refresh for stale data
    - Metrics tracking
    """

    # Cache key prefixes
    PREFIX = "facemortgage:provider"

    # Default TTLs
    DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours
    DEFAULT_STALE_TTL_SECONDS = 48 * 60 * 60  # 48 hours (stale but usable)

    def __init__(
        self,
        redis: Redis,
        default_ttl_seconds: Optional[int] = None,
        default_stale_ttl_seconds: Optional[int] = None,
    ):
        self.redis = redis
        self.default_ttl = default_ttl_seconds or self.DEFAULT_TTL_SECONDS
        self.default_stale_ttl = default_stale_ttl_seconds or self.DEFAULT_STALE_TTL_SECONDS

        # Metrics
        self._hits = 0
        self._misses = 0
        self._stale_hits = 0

    def _build_key(
        self,
        provider_name: str,
        nmls_id: str,
        data_type: str = "stats",
    ) -> str:
        """Build a cache key."""
        return f"{self.PREFIX}:{provider_name}:nmls:{nmls_id}:{data_type}"

    async def get(
        self,
        provider_name: str,
        nmls_id: str,
        data_type: str = "stats",
    ) -> Optional[CacheEntry]:
        """
        Get a cached entry.

        Returns:
            CacheEntry if found and not completely expired, None otherwise
        """
        key = self._build_key(provider_name, nmls_id, data_type)

        try:
            raw_data = await self.redis.get(key)
            if raw_data is None:
                self._misses += 1
                logger.debug(f"Cache miss for {key}")
                return None

            data = json_deserialize(raw_data)
            entry = CacheEntry.from_dict(data)

            if entry.is_expired:
                self._misses += 1
                logger.debug(f"Cache expired for {key}")
                await self.redis.delete(key)
                return None

            if entry.is_stale:
                self._stale_hits += 1
                logger.debug(f"Cache stale hit for {key}")
            else:
                self._hits += 1
                logger.debug(f"Cache hit for {key}")

            return entry

        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error for {key}: {e}")
            self._misses += 1
            return None

    async def set(
        self,
        provider_name: str,
        nmls_id: str,
        value: Any,
        data_type: str = "stats",
        ttl_seconds: Optional[int] = None,
        stale_ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Set a cache entry.

        Args:
            provider_name: Name of the data provider
            nmls_id: Professional's NMLS ID
            value: Data to cache (must be JSON serializable)
            data_type: Type of data (stats, license, production)
            ttl_seconds: Fresh TTL in seconds
            stale_ttl_seconds: Stale-but-usable TTL in seconds

        Returns:
            True if successful, False otherwise
        """
        key = self._build_key(provider_name, nmls_id, data_type)
        ttl = ttl_seconds or self.default_ttl
        stale_ttl = stale_ttl_seconds or self.default_stale_ttl

        entry = CacheEntry(
            value=value,
            created_at=datetime.utcnow(),
            ttl_seconds=ttl,
            stale_ttl_seconds=stale_ttl,
        )

        try:
            # Store with Redis TTL set to stale TTL (max lifetime)
            await self.redis.setex(
                key,
                stale_ttl,
                json_serialize(entry.to_dict()),
            )
            logger.debug(f"Cache set for {key} with TTL={ttl}s, stale_TTL={stale_ttl}s")
            return True

        except RedisError as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False

    async def invalidate(
        self,
        provider_name: str,
        nmls_id: str,
        data_type: Optional[str] = None,
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            provider_name: Name of the data provider
            nmls_id: Professional's NMLS ID
            data_type: Specific data type to invalidate, or None for all

        Returns:
            Number of keys deleted
        """
        if data_type:
            key = self._build_key(provider_name, nmls_id, data_type)
            deleted = await self.redis.delete(key)
        else:
            # Delete all data types for this NMLS ID
            pattern = f"{self.PREFIX}:{provider_name}:nmls:{nmls_id}:*"
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
            else:
                deleted = 0

        logger.info(f"Cache invalidated: {deleted} keys for {provider_name}/{nmls_id}")
        return deleted

    async def invalidate_provider(self, provider_name: str) -> int:
        """
        Invalidate all cache entries for a provider.

        Useful when a provider's API changes or data needs refresh.
        """
        pattern = f"{self.PREFIX}:{provider_name}:*"
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted = await self.redis.delete(*keys)
        else:
            deleted = 0

        logger.info(f"Cache invalidated: {deleted} keys for provider {provider_name}")
        return deleted

    async def get_or_set(
        self,
        provider_name: str,
        nmls_id: str,
        fetch_func: Callable[[], Any],
        data_type: str = "stats",
        ttl_seconds: Optional[int] = None,
        allow_stale: bool = True,
    ) -> Optional[Any]:
        """
        Get from cache or fetch and cache if missing.

        Implements stale-while-revalidate:
        - Returns fresh data immediately
        - Returns stale data and triggers background refresh
        - Fetches new data only on cache miss

        Args:
            provider_name: Name of the data provider
            nmls_id: Professional's NMLS ID
            fetch_func: Async function to fetch data if cache miss
            data_type: Type of data
            ttl_seconds: Fresh TTL in seconds
            allow_stale: If True, return stale data while revalidating

        Returns:
            Cached or fetched data, or None if unavailable
        """
        entry = await self.get(provider_name, nmls_id, data_type)

        if entry is not None:
            if entry.is_fresh:
                return entry.value

            if entry.is_stale and allow_stale:
                # Return stale data, trigger background refresh
                asyncio.create_task(
                    self._background_refresh(
                        provider_name, nmls_id, fetch_func, data_type, ttl_seconds
                    )
                )
                return entry.value

        # Cache miss or expired - fetch new data
        try:
            value = await fetch_func()
            if value is not None:
                await self.set(
                    provider_name, nmls_id, value, data_type, ttl_seconds
                )
            return value
        except Exception as e:
            logger.error(f"Failed to fetch data for {provider_name}/{nmls_id}: {e}")
            # Return stale data as fallback if available
            if entry is not None and allow_stale:
                return entry.value
            return None

    async def _background_refresh(
        self,
        provider_name: str,
        nmls_id: str,
        fetch_func: Callable[[], Any],
        data_type: str,
        ttl_seconds: Optional[int],
    ) -> None:
        """Background task to refresh stale cache entry."""
        try:
            logger.debug(f"Background refresh for {provider_name}/{nmls_id}/{data_type}")
            value = await fetch_func()
            if value is not None:
                await self.set(provider_name, nmls_id, value, data_type, ttl_seconds)
                logger.debug(f"Background refresh completed for {provider_name}/{nmls_id}")
        except Exception as e:
            logger.warning(f"Background refresh failed for {provider_name}/{nmls_id}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses + self._stale_hits
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        stale_rate = (self._stale_hits / total * 100) if total > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "stale_hits": self._stale_hits,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "stale_hit_rate_percent": round(stale_rate, 2),
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._hits = 0
        self._misses = 0
        self._stale_hits = 0


# Global cache instance (initialized lazily)
_cache_instance: Optional[DataProviderCache] = None


async def get_provider_cache(redis: Redis) -> DataProviderCache:
    """
    Get or create the global cache instance.

    Usage:
        redis = Redis.from_url(settings.redis_url)
        cache = await get_provider_cache(redis)
    """
    global _cache_instance
    if _cache_instance is None:
        ttl_hours = getattr(settings, "data_cache_ttl_hours", 24)
        _cache_instance = DataProviderCache(
            redis=redis,
            default_ttl_seconds=ttl_hours * 3600,
        )
    return _cache_instance
