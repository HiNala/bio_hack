"""
Tests for caching system.
"""

import pytest
import asyncio
from app.cache import SimpleCache, cached


@pytest.mark.asyncio
class TestSimpleCache:
    """Test simple cache functionality."""

    async def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = SimpleCache()

        # Test setting and getting a value
        await cache.set("test_key", "test_value", ttl_seconds=60)
        value = await cache.get("test_key")

        assert value == "test_value"

    async def test_cache_expiration(self):
        """Test cache expiration."""
        cache = SimpleCache()

        # Set value with short TTL
        await cache.set("test_key", "test_value", ttl_seconds=1)

        # Value should exist immediately
        value = await cache.get("test_key")
        assert value == "test_value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Value should be gone
        value = await cache.get("test_key")
        assert value is None

    async def test_cache_nonexistent_key(self):
        """Test getting nonexistent key."""
        cache = SimpleCache()

        value = await cache.get("nonexistent_key")
        assert value is None

    async def test_cache_delete(self):
        """Test cache deletion."""
        cache = SimpleCache()

        await cache.set("test_key", "test_value")
        value = await cache.get("test_key")
        assert value == "test_value"

        await cache.delete("test_key")
        value = await cache.get("test_key")
        assert value is None

    async def test_cache_clear(self):
        """Test cache clearing."""
        cache = SimpleCache()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None


@pytest.mark.asyncio
class TestCachedDecorator:
    """Test cached decorator functionality."""

    async def test_cached_decorator(self):
        """Test that cached decorator works."""
        call_count = 0

        @cached(ttl_seconds=60)
        async def test_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call should execute function
        result1 = await test_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call with same args should use cache
        result2 = await test_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not have incremented

        # Call with different args should execute function
        result3 = await test_function(3)
        assert result3 == 6
        assert call_count == 2