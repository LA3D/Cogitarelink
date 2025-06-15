"""Lightweight, pluggable cache for CogitareLink."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, Dict, Tuple
from dataclasses import dataclass


@dataclass
class CacheStats:
    """Cache statistics for monitoring performance."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    
    def as_dict(self) -> Dict[str, int]:
        return self.__dict__
    
    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class BaseCache:
    """
    Interface backbone—override storage primitives to change backend.
    
    Provides namespace-scoped memoization for function caching.
    """
    
    def __init__(self, maxsize: int = 1024, ttl: float | None = None):
        self.maxsize = maxsize
        self.ttl = ttl
        self.stats = CacheStats()
    
    def _store(self, key: str, val: Any) -> None:
        """Override in subclasses."""
        ...
    
    def _load(self, key: str) -> Any | None:
        """Override in subclasses."""
        ...
    
    def _evict(self) -> None:
        """Override in subclasses."""
        ...
    
    def set(self, key: str, val: Any) -> None:
        """Store value with timestamp."""
        self._store(key, (val, time.time()))
        self.stats.sets += 1
    
    def get(self, key: str) -> Any | None:
        """Get value, checking TTL if configured."""
        item = self._load(key)
        if item is None:
            self.stats.misses += 1
            return None
        
        val, ts = item
        
        # Check TTL expiration
        if self.ttl and time.time() - ts > self.ttl:
            self.delete(key)
            self.stats.misses += 1
            return None
        
        self.stats.hits += 1
        return val
    
    def delete(self, key: str) -> None:
        """Override in subclasses."""
        ...
    
    def clear(self) -> None:
        """Override in subclasses."""
        ...
    
    def memoize(self, ns: str = "default", maxsize: int | None = None):
        """
        Return a decorator that wraps function with namespace-scoped LRU cache.
        
        Args:
            ns: Arbitrary namespace label (e.g. "http", "context", "normalization")
            maxsize: Optional per-namespace cache size
        
        Example:
            >>> cache = InMemoryCache(maxsize=256)
            >>> @cache.memoize("context")
            ... def expensive_context_processing(vocab_list):
            ...     return process_vocabularies(vocab_list)
        """
        if not hasattr(self, "_memo_tables"):
            self._memo_tables: Dict[str, Callable] = {}
        
        if ns not in self._memo_tables:
            # Create independent functools.lru_cache per namespace
            self._memo_tables[ns] = functools.lru_cache(
                maxsize or self.maxsize
            )
        
        def decorator(fn: Callable):
            wrapped = self._memo_tables[ns](fn)
            functools.update_wrapper(wrapped, fn)
            return wrapped
        
        return decorator
    
    def info(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            **self.stats.as_dict(),
            "hit_ratio": self.stats.hit_ratio,
            "maxsize": self.maxsize,
            "ttl": self.ttl
        }


class InMemoryCache(BaseCache):
    """Simple LRU dict backend with FIFO eviction."""
    
    def __init__(self, maxsize: int = 1024, ttl: float | None = None):
        super().__init__(maxsize, ttl)
        from collections import OrderedDict
        self._d: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
    
    def _store(self, key: str, val: Tuple[Any, float]) -> None:
        """Store with LRU ordering."""
        if key in self._d:
            self._d.pop(key)  # Remove old entry
        self._d[key] = val
        
        # FIFO eviction if over maxsize
        if len(self._d) > self.maxsize:
            self._d.popitem(last=False)
    
    def _load(self, key: str) -> Tuple[Any, float] | None:
        """Load value and update LRU ordering."""
        return self._d.get(key)
    
    def _evict(self) -> None:
        """Evict oldest entry."""
        if self._d:
            self._d.popitem(last=False)
    
    def delete(self, key: str) -> None:
        """Delete specific key."""
        self._d.pop(key, None)
    
    def clear(self) -> None:
        """Clear all entries."""
        self._d.clear()
    
    def __len__(self) -> int:
        """Get current cache size."""
        return len(self._d)


class DiskCache(BaseCache):
    """Disk-based cache using diskcache backend."""
    
    def __init__(self, directory: str = ".cog_cache", **kw):
        super().__init__(**kw)
        try:
            from diskcache import Cache as DC
            self._dc = DC(str(directory))
            self._keys: list[str] = []
            self._has_diskcache = True
        except ImportError:
            # Fallback to in-memory if diskcache not available
            self._dc = None
            self._has_diskcache = False
            from collections import OrderedDict
            self._memory_fallback: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
    
    def _k(self, k: str) -> str:
        """Normalize key for storage."""
        return str(k)
    
    def _store(self, k: str, v: Tuple[Any, float]) -> None:
        """Store with disk or memory fallback."""
        k2 = self._k(k)
        
        if self._has_diskcache:
            if k2 in self._keys:
                self._keys.remove(k2)
            self._keys.append(k2)
            self._dc.set(k2, v)
            
            # Evict if over maxsize
            if len(self._keys) > self.maxsize:
                rm = self._keys.pop(0)
                self._dc.pop(rm, None)
        else:
            # Memory fallback
            if k2 in self._memory_fallback:
                self._memory_fallback.pop(k2)
            self._memory_fallback[k2] = v
            if len(self._memory_fallback) > self.maxsize:
                self._memory_fallback.popitem(last=False)
    
    def _load(self, k: str) -> Tuple[Any, float] | None:
        """Load from disk or memory fallback."""
        k2 = self._k(k)
        if self._has_diskcache:
            return self._dc.get(k2, default=None)
        else:
            return self._memory_fallback.get(k2)
    
    def delete(self, k: str) -> None:
        """Delete from disk or memory."""
        k2 = self._k(k)
        if self._has_diskcache:
            self._dc.pop(k2, None)
            if k2 in self._keys:
                self._keys.remove(k2)
        else:
            self._memory_fallback.pop(k2, None)
    
    def clear(self) -> None:
        """Clear all entries."""
        if self._has_diskcache:
            self._dc.clear()
            self._keys = []
        else:
            self._memory_fallback.clear()


# Default cache implementation
Cache = InMemoryCache