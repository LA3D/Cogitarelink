"""Cache manager using diskcache - don't reinvent the wheel!

Uses diskcache for efficient disk-based caching with TTL support.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

import diskcache as dc

from ..core.debug import get_logger

log = get_logger("cache_manager")


@dataclass
class CachedSchema:
    """Cached endpoint schema with TTL."""
    endpoint: str
    prefixes: Dict[str, str]
    classes: Dict[str, Any] 
    properties: Dict[str, Any]
    patterns: Dict[str, str]
    cached_at: float
    ttl_seconds: int = 3600  # 1 hour default

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > (self.cached_at + self.ttl_seconds)


class CacheManager:
    """Cache manager using diskcache for efficient caching.
    
    Uses diskcache instead of reinventing JSON file caching.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".cogitarelink" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Use diskcache for efficient disk-based caching
        self.cache = dc.Cache(str(self.cache_dir))
        log.debug(f"Cache directory: {self.cache_dir}")

    def get(self, key: str) -> Optional[Any]:
        """Get cached data by key (general interface)."""
        try:
            data = self.cache.get(key)
            if data is None:
                log.debug(f"No cache entry for {key}")
                return None
                
            # If it's a schema entry, check expiration
            if key.startswith("schema:"):
                schema = CachedSchema(**data)
                if schema.is_expired:
                    log.debug(f"Cache expired for {key}")
                    self.cache.delete(key)
                    return None
                log.debug(f"Cache hit for {key}")
                return schema
            else:
                # For non-schema entries, return data directly
                log.debug(f"Cache hit for {key}")
                return data
            
        except Exception as e:
            log.warning(f"Failed to load cache for {key}: {e}")
            return None

    def get_schema(self, endpoint: str) -> Optional[CachedSchema]:
        """Get cached schema if available and not expired."""
        return self.get(f"schema:{endpoint}")

    def set(self, key: str, data: Any, ttl: int = 3600) -> None:
        """Set cached data by key (general interface)."""
        try:
            # Use diskcache's built-in expiration
            self.cache.set(key, data, expire=ttl)
            log.debug(f"Cached data for {key}")
        except Exception as e:
            log.error(f"Failed to cache data for {key}: {e}")

    def set_schema(self, endpoint: str, prefixes: Dict[str, str], 
            classes: Dict[str, Any] = None, 
            properties: Dict[str, Any] = None,
            patterns: Dict[str, str] = None,
            ttl_seconds: int = 3600) -> None:
        """Cache schema for endpoint."""
        
        schema = CachedSchema(
            endpoint=endpoint,
            prefixes=prefixes,
            classes=classes or {},
            properties=properties or {},
            patterns=patterns or {},
            cached_at=time.time(),
            ttl_seconds=ttl_seconds
        )
        
        try:
            # Use diskcache's built-in expiration
            self.cache.set(
                f"schema:{endpoint}", 
                asdict(schema), 
                expire=ttl_seconds
            )
            log.debug(f"Cached schema for {endpoint}")
            
        except Exception as e:
            log.error(f"Failed to cache schema for {endpoint}: {e}")

    def clear(self, endpoint: Optional[str] = None) -> None:
        """Clear cache for specific endpoint or all."""
        try:
            if endpoint:
                self.cache.delete(f"schema:{endpoint}")
                log.debug(f"Cleared cache for {endpoint}")
            else:
                self.cache.clear()
                log.debug("Cleared all cache")
        except Exception as e:
            log.error(f"Failed to clear cache: {e}")

    def list_cached(self) -> List[str]:
        """List all cached endpoints."""
        try:
            # Get all keys with schema: prefix
            keys = [k for k in self.cache if k.startswith("schema:")]
            return [k.replace("schema:", "") for k in keys]
        except Exception as e:
            log.error(f"Failed to list cached endpoints: {e}")
            return []

    def close(self) -> None:
        """Close the cache."""
        try:
            self.cache.close()
        except Exception as e:
            log.error(f"Failed to close cache: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _ = exc_type, exc_val, exc_tb  # Unused but required for context manager
        self.close()


# Global cache instance
cache_manager = CacheManager()