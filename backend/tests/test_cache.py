"""
Unit tests for the Cache Service.

Tests:
- Cache key generation
- TTL configuration
- JSON serialization
- Cache decorator
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from src.app.services.cache_service import (
    CacheService,
    CacheConfig,
    cached,
    get_cache_service,
)


class TestCacheConfig:
    """Tests for cache configuration."""
    
    def test_ttl_short(self):
        """SHORT TTL should be 60 seconds."""
        assert CacheConfig.SHORT == 60
    
    def test_ttl_medium(self):
        """MEDIUM TTL should be 300 seconds (5 min)."""
        assert CacheConfig.MEDIUM == 300
    
    def test_ttl_long(self):
        """LONG TTL should be 900 seconds (15 min)."""
        assert CacheConfig.LONG == 900
    
    def test_ttl_very_long(self):
        """VERY_LONG TTL should be 3600 seconds (1 hour)."""
        assert CacheConfig.VERY_LONG == 3600
    
    def test_prefixes_defined(self):
        """Should have key prefixes defined."""
        assert CacheConfig.PREFIX_GRID == "grid:"
        assert CacheConfig.PREFIX_PROFESSIONAL == "pro:"
        assert CacheConfig.PREFIX_MATCHING == "match:"


class TestCacheService:
    """Tests for cache service methods."""
    
    def test_make_key_single_part(self):
        """Should create key from single part."""
        key = CacheService.make_key("prefix")
        assert key == "prefix"
    
    def test_make_key_multiple_parts(self):
        """Should join multiple parts with colon."""
        key = CacheService.make_key("grid", "CA", "abc123")
        assert key == "grid:CA:abc123"
    
    def test_hash_params_deterministic(self):
        """Same params should produce same hash."""
        hash1 = CacheService.hash_params(state="CA", specialty="FHA")
        hash2 = CacheService.hash_params(state="CA", specialty="FHA")
        assert hash1 == hash2
    
    def test_hash_params_different_for_different_input(self):
        """Different params should produce different hash."""
        hash1 = CacheService.hash_params(state="CA")
        hash2 = CacheService.hash_params(state="TX")
        assert hash1 != hash2
    
    def test_hash_params_order_independent(self):
        """Hash should be same regardless of param order."""
        hash1 = CacheService.hash_params(a="1", b="2")
        hash2 = CacheService.hash_params(b="2", a="1")
        assert hash1 == hash2
    
    def test_hash_params_length(self):
        """Hash should be 12 characters."""
        hash_result = CacheService.hash_params(test="value")
        assert len(hash_result) == 12


class TestCacheServiceAsync:
    """Tests for async cache operations."""
    
    @pytest.mark.asyncio
    async def test_get_returns_none_on_miss(self):
        """Should return None when key doesn't exist."""
        cache = CacheService()
        cache._client = AsyncMock()
        cache._client.get = AsyncMock(return_value=None)
        
        result = await cache.get("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_json_parses_json(self):
        """Should parse JSON from cache."""
        cache = CacheService()
        cache._client = AsyncMock()
        cache._client.get = AsyncMock(return_value='{"name": "test"}')
        
        result = await cache.get_json("test_key")
        assert result == {"name": "test"}
    
    @pytest.mark.asyncio
    async def test_set_json_serializes(self):
        """Should serialize dict to JSON."""
        cache = CacheService()
        cache._client = AsyncMock()
        cache._client.setex = AsyncMock()
        
        await cache.set_json("key", {"test": True}, ttl=60)
        
        cache._client.setex.assert_called_once()
        call_args = cache._client.setex.call_args
        assert call_args[0][0] == "key"
        assert call_args[0][1] == 60
        assert json.loads(call_args[0][2]) == {"test": True}
    
    @pytest.mark.asyncio
    async def test_delete_calls_client(self):
        """Should call Redis delete."""
        cache = CacheService()
        cache._client = AsyncMock()
        cache._client.delete = AsyncMock()
        
        await cache.delete("key_to_delete")
        
        cache._client.delete.assert_called_once_with("key_to_delete")
    
    @pytest.mark.asyncio
    async def test_exists_returns_bool(self):
        """Should return boolean for exists check."""
        cache = CacheService()
        cache._client = AsyncMock()
        cache._client.exists = AsyncMock(return_value=1)
        
        result = await cache.exists("existing_key")
        assert result is True


class TestDomainCaching:
    """Tests for domain-specific caching methods."""
    
    @pytest.mark.asyncio
    async def test_cache_grid_results(self):
        """Should cache grid results with correct key."""
        cache = CacheService()
        cache.set_json = AsyncMock()
        
        await cache.cache_grid_results("CA", "abc123", [{"id": "1"}])
        
        cache.set_json.assert_called_once()
        call_args = cache.set_json.call_args
        assert "grid:" in call_args[0][0]
        assert "CA" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cache_baseball_card(self):
        """Should cache baseball card with correct key."""
        cache = CacheService()
        cache.set_json = AsyncMock()
        
        await cache.cache_baseball_card("pro-123", {"grade": "A+"})
        
        cache.set_json.assert_called_once()
        call_args = cache.set_json.call_args
        assert "baseball:" in call_args[0][0]
        assert "pro-123" in call_args[0][0]


class TestCachedDecorator:
    """Tests for the @cached decorator."""
    
    def test_decorator_returns_callable(self):
        """Decorator should return a callable."""
        @cached("test", ttl=60)
        async def test_func():
            return {"data": True}
        
        assert callable(test_func)


class TestSingleton:
    """Tests for cache service singleton."""
    
    def test_get_cache_service_returns_same_instance(self):
        """Should return same instance on multiple calls."""
        # Note: In actual test, we'd reset the singleton first
        service1 = get_cache_service()
        service2 = get_cache_service()
        
        assert service1 is service2
