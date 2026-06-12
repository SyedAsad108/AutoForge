import asyncio
import time
from typing import Any, Callable, Dict, Optional, Coroutine

from backend.core.logger import get_logger

logger = get_logger("CacheService")


class CacheEntry:
    def __init__(self, data: Any, ttl: float, max_stale: float = 3600.0):
        self.data = data
        self.cached_at = time.time()
        self.expires_at = self.cached_at + ttl
        self.max_stale_at = self.expires_at + max_stale

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def is_too_stale(self) -> bool:
        return time.time() > self.max_stale_at


class CacheService:
    """
    In-memory caching service supporting stale-while-revalidate.
    """

    _instance = None
    _cache: Dict[str, CacheEntry] = {}
    _in_flight: Dict[str, asyncio.Task] = {}
    
    # Observability metrics
    hits = 0
    misses = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
            cls._cache = {}
            cls._in_flight = {}
        return cls._instance

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        total = cls.hits + cls.misses
        hit_rate = (cls.hits / total) if total > 0 else 0.0
        return {
            "keys_in_cache": len(cls._cache),
            "hits": cls.hits,
            "misses": cls.misses,
            "hit_rate_pct": round(hit_rate * 100, 2),
        }

    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable[[], Coroutine[Any, Any, Any]],
        ttl: float = 60.0,
        max_stale: float = 3600.0,
    ) -> Any:
        """
        Retrieves a value from cache.
        - If missing or too stale: awaits fetch_func() and caches it.
        - If expired but within max_stale: returns cached data immediately, and spawns a background task to refresh.
        - If valid: returns cached data immediately.
        """
        entry = self._cache.get(key)

        if not entry:
            self.misses += 1
            logger.debug(f"[CACHE MISS] {key}")
            return await self._fetch_and_set(key, fetch_func, ttl, max_stale)

        if not entry.is_expired():
            self.hits += 1
            logger.debug(f"[CACHE HIT] {key}")
            return entry.data

        if entry.is_too_stale():
            self.misses += 1
            logger.debug(f"[CACHE TOO STALE] {key} - blocking for fresh data")
            return await self._fetch_and_set(key, fetch_func, ttl, max_stale)

        # Stale-while-revalidate
        self.hits += 1
        logger.debug(f"[CACHE HIT (STALE)] {key} - triggering background refresh")
        if key not in self._in_flight:
            asyncio.create_task(self._fetch_and_set(key, fetch_func, ttl, max_stale))
        
        return entry.data

    def get(self, key: str) -> Optional[Any]:
        """Simple get for metrics that are refreshed by a background worker."""
        entry = self._cache.get(key)
        if entry:
            self.hits += 1
            return entry.data
        self.misses += 1
        return None

    def set(self, key: str, data: Any, ttl: float = 60.0, max_stale: float = 3600.0) -> None:
        """Manually set a cache value."""
        self._cache[key] = CacheEntry(data, ttl, max_stale)

    async def _fetch_and_set(
        self,
        key: str,
        fetch_func: Callable[[], Coroutine[Any, Any, Any]],
        ttl: float,
        max_stale: float,
    ) -> Any:
        try:
            # If there's already an in-flight fetch for this key, wait for it
            if key in self._in_flight and not self._in_flight[key].done():
                return await self._in_flight[key]
                
            task = asyncio.create_task(fetch_func())
            self._in_flight[key] = task
            
            data = await task
            self._cache[key] = CacheEntry(data, ttl, max_stale)
            return data
        except Exception as e:
            logger.error(f"[CACHE FETCH ERROR] Failed to fetch key {key}: {e}")
            # If we fail but have old data, we could technically keep the old data by not overwriting, 
            # but for now we just raise the exception so the caller knows it failed (if blocking).
            raise
        finally:
            if key in self._in_flight:
                del self._in_flight[key]

# Global singleton instance
cache_service = CacheService()

def with_cache(key_pattern: str, ttl: float = 60.0, max_stale: float = 3600.0):
    """
    Decorator to cache class methods.
    key_pattern can use {arg_name} for formatting based on method arguments.
    """
    from functools import wraps
    import inspect

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(self, *args, **kwargs)
            bound.apply_defaults()
            # Remove 'self' from arguments for key formatting if needed, but kwargs and args are safe.
            fmt_args = bound.arguments.copy()
            if 'self' in fmt_args:
                del fmt_args['self']
            
            key = key_pattern.format(**fmt_args)
            
            async def fetch_func():
                return await func(self, *args, **kwargs)
                
            return await cache_service.get_or_fetch(key, fetch_func, ttl=ttl, max_stale=max_stale)
        return wrapper
    return decorator
