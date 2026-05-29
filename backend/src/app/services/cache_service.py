"""
Caching Layer for FaceMortgage.

Provides Redis-based caching with:
- Automatic serialization/deserialization
- TTL management
- Cache invalidation patterns
- Performance metrics

Follows the DNA Strand principle of reproducibility -
cache keys include version hashes for consistency.
"""

import json
import hashlib
import logging
from typing import Optional, TypeVar, Callable, Any
from functools import wraps

import redis.asyncio as redis

from src.app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheConfig:
    """Cache configuration constants."""
    
    # TTL settings (in seconds)
    SHORT = 60  # 1 minute - for highly volatile data
    MEDIUM = 300  # 5 minutes - for moderately fresh data
    LONG = 900  # 15 minutes - for stable data
    VERY_LONG = 3600  # 1 hour - for rarely changing data
    
    # Key prefixes
    PREFIX_GRID = "grid:"
    PREFIX_PROFESSIONAL = "pro:"
    PREFIX_MATCHING = "match:"
    PREFIX_STATS = "stats:"
    PREFIX_BASEBALL = "baseball:"
    PREFIX_INTENT = "intent:"


class CacheService:
    """
    Redis caching service with automatic serialization.
    
    Supports both simple key-value caching and decorated
    function result caching.
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize Redis connection with retry and graceful degradation."""
        if self._client is None:
            import asyncio
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self._client = redis.from_url(
                        self.redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                    )
                    # Verify connection is alive
                    await self._client.ping()
                    self._connected = True
                    logger.info("Cache service connected to Redis")
                    return
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 0.5
                        logger.warning(
                            f"Redis connection attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        self._client = None
                    else:
                        logger.error(
                            f"Redis connection failed after {max_retries} attempts: {e}. "
                            f"Cache operations will be no-ops (graceful degradation)."
                        )
                        self._client = None
                        self._connected = False
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Cache service disconnected")
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if not self._client:
            raise RuntimeError("Cache service not connected")
        return self._client
    
    # ==================== Core Operations ====================
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from cache."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ttl: int = CacheConfig.MEDIUM,
    ) -> bool:
        """Set value in cache with TTL."""
        try:
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: int = CacheConfig.MEDIUM,
    ) -> bool:
        """Set JSON value in cache."""
        try:
            json_str = json.dumps(value, default=str)
            return await self.set(key, json_str, ttl)
        except Exception as e:
            logger.warning(f"Cache set_json error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete_pattern error: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error: {e}")
            return False
    
    # ==================== Cache Key Builders ====================
    
    @staticmethod
    def make_key(*parts: str) -> str:
        """Build cache key from parts."""
        return ":".join(str(p) for p in parts)
    
    @staticmethod
    def hash_params(**kwargs) -> str:
        """Create hash from parameters for cache key."""
        sorted_items = sorted(kwargs.items())
        param_str = json.dumps(sorted_items, sort_keys=True, default=str)
        return hashlib.md5(param_str.encode()).hexdigest()[:12]
    
    # ==================== Domain-Specific Caching ====================
    
    async def cache_grid_results(
        self,
        state: str,
        filters_hash: str,
        results: list,
    ) -> None:
        """Cache grid query results."""
        key = self.make_key(CacheConfig.PREFIX_GRID, state, filters_hash)
        await self.set_json(key, results, CacheConfig.SHORT)
    
    async def get_grid_results(
        self,
        state: str,
        filters_hash: str,
    ) -> Optional[list]:
        """Get cached grid results."""
        key = self.make_key(CacheConfig.PREFIX_GRID, state, filters_hash)
        return await self.get_json(key)
    
    async def cache_baseball_card(
        self,
        professional_id: str,
        card_data: dict,
    ) -> None:
        """Cache baseball card stats."""
        key = self.make_key(CacheConfig.PREFIX_BASEBALL, professional_id)
        await self.set_json(key, card_data, CacheConfig.MEDIUM)
    
    async def get_baseball_card(
        self,
        professional_id: str,
    ) -> Optional[dict]:
        """Get cached baseball card."""
        key = self.make_key(CacheConfig.PREFIX_BASEBALL, professional_id)
        return await self.get_json(key)
    
    async def invalidate_professional(self, professional_id: str) -> None:
        """Invalidate all cache for a professional."""
        await self.delete_pattern(f"*{professional_id}*")
    
    async def cache_matching_results(
        self,
        input_hash: str,
        results: dict,
    ) -> None:
        """Cache matching algorithm results."""
        key = self.make_key(CacheConfig.PREFIX_MATCHING, input_hash)
        await self.set_json(key, results, CacheConfig.SHORT)
    
    async def get_matching_results(
        self,
        input_hash: str,
    ) -> Optional[dict]:
        """Get cached matching results."""
        key = self.make_key(CacheConfig.PREFIX_MATCHING, input_hash)
        return await self.get_json(key)


# ==================== Decorator for Cached Functions ====================

def cached(
    prefix: str,
    ttl: int = CacheConfig.MEDIUM,
    key_builder: Optional[Callable] = None,
):
    """
    Decorator to cache function results in Redis.
    
    Usage:
        @cached("grid", ttl=60)
        async def get_grid_data(state: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                params_hash = CacheService.hash_params(**kwargs)
                cache_key = CacheService.make_key(prefix, func.__name__, params_hash)
            
            # Try cache first
            cached_value = await cache.get_json(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            # Call function and cache result
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache result (handle Pydantic models)
            if hasattr(result, 'model_dump'):
                await cache.set_json(cache_key, result.model_dump(), ttl)
            elif isinstance(result, (dict, list)):
                await cache.set_json(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# ==================== Singleton ====================

_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
