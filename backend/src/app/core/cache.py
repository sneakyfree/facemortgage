"""
Caching utilities for the application.

Provides Redis-based caching with configurable TTL.
"""
import json
import hashlib
import logging
from datetime import timedelta
from typing import Optional, Any, Callable, TypeVar
from functools import wraps
import redis.asyncio as redis

from src.app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client with connection pooling."""
    global _redis_pool, _redis_client

    if _redis_client is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,
            decode_responses=True,
        )
        _redis_client = redis.Redis(connection_pool=_redis_pool)

    return _redis_client


async def close_redis():
    """Close Redis connection pool."""
    global _redis_pool, _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None

    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None


class CacheService:
    """Service for caching data in Redis."""

    def __init__(self, prefix: str = "cache"):
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            client = await get_redis()
            value = await client.get(self._make_key(key))
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.debug(f"Cache get failed for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
    ) -> bool:
        """Set a value in cache with optional TTL."""
        try:
            client = await get_redis()
            serialized = json.dumps(value, default=str)
            if ttl:
                await client.setex(self._make_key(key), ttl, serialized)
            else:
                await client.set(self._make_key(key), serialized)
            return True
        except Exception as e:
            logger.debug(f"Cache set failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            client = await get_redis()
            await client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.debug(f"Cache delete failed for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            client = await get_redis()
            keys = []
            async for key in client.scan_iter(match=self._make_key(pattern)):
                keys.append(key)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Cache delete pattern failed for pattern {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            client = await get_redis()
            return await client.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.debug(f"Cache exists check failed for key {key}: {e}")
            return False


# Decorator for caching function results
def cached(
    prefix: str,
    ttl: timedelta = timedelta(hours=1),
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator to cache function results.

    Usage:
        @cached(prefix="stats", ttl=timedelta(hours=24))
        async def get_professional_stats(nmls_id: str):
            ...
    """
    cache = CacheService(prefix)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default: hash of function name + args
                key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


# Specialized caches
professional_stats_cache = CacheService("pro_stats")
grid_cache = CacheService("grid")
presence_cache = CacheService("presence")
