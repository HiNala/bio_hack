"""
Simple in-memory cache for performance optimization.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Cache entry with expiration."""
    value: Any
    expires_at: float


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry and time.time() < entry.expires_at:
                return entry.value
            elif entry:
                # Remove expired entry
                del self._cache[key]
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL."""
        async with self._lock:
            expires_at = time.time() + ttl_seconds
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()


# Global cache instance
cache = SimpleCache()


def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorator to cache async function results.

    Args:
        ttl_seconds: Time to live in seconds
        key_prefix: Prefix for cache key generation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args if arg is not None)
            key_parts.extend(f"{k}:{v}" for k, v in kwargs.items() if v is not None)
            cache_key = "|".join(key_parts)

            # Try to get from cache first
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl_seconds)
            return result

        return wrapper
    return decorator