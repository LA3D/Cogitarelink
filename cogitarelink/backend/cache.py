"""Cache manager using diskcache - don't reinvent the wheel!

Uses diskcache for efficient disk-based caching with TTL support.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from typing import Set

import diskcache as dc

from ..utils.logging import get_logger

log = get_logger("cache_manager")


@dataclass
class SemanticMetadata:
    """Semantic metadata for cached RDF resources."""
    semantic_type: str  # "vocabulary", "context", "service", "schema"
    domains: List[str]  # ["biology", "chemistry", "general"]
    format_type: str    # "turtle", "json-ld", "rdf-xml"
    purpose: str        # "schema_definition", "term_mapping", "endpoint_capability"
    dependencies: List[str]  # Other vocabularies this builds on
    provides: Dict[str, int]  # {"classes": 45, "properties": 120, "contexts": 1}
    confidence_scores: Dict[str, float]  # Classification confidence
    vocabulary_size: int  # Number of terms/triples
    learned_at: float  # When semantic analysis was performed
    usage_patterns: List[str]  # Common usage patterns discovered


@dataclass 
class EnhancedCacheEntry:
    """Cache entry with semantic metadata."""
    data: Dict[str, Any]
    semantic_metadata: Optional[SemanticMetadata]
    cached_at: float
    ttl_seconds: int = 86400  # 24 hours default for RDF data
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > (self.cached_at + self.ttl_seconds)


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
        """Get cached data by key (delegates to enhanced pathway for consistency)."""
        try:
            # Special handling for schema entries (keep existing behavior)
            if key.startswith("schema:"):
                data = self.cache.get(key)
                if data is None:
                    log.debug(f"No cache entry for {key}")
                    return None
                schema = CachedSchema(**data)
                if schema.is_expired:
                    log.debug(f"Cache expired for {key}")
                    self.cache.delete(key)
                    return None
                log.debug(f"Cache hit for {key}")
                return schema
            
            # For all other entries, delegate to enhanced pathway
            enhanced_entry = self.get_enhanced(key)
            if enhanced_entry:
                return enhanced_entry.data
            else:
                return None
            
        except Exception as e:
            log.warning(f"Failed to load cache for {key}: {e}")
            return None

    def get_schema(self, endpoint: str) -> Optional[CachedSchema]:
        """Get cached schema if available and not expired."""
        return self.get(f"schema:{endpoint}")

    def set(self, key: str, data: Any, ttl: int = 3600) -> None:
        """Set cached data by key (delegates to enhanced pathway for consistency)."""
        try:
            # Special handling for schema entries (keep existing behavior)
            if key.startswith("schema:"):
                self.cache.set(key, data, expire=ttl)
                log.debug(f"Cached schema data for {key}")
                return
            
            # For all other entries, delegate to enhanced pathway
            # Initialize with no semantic metadata (can be added later)
            self.set_enhanced(key, data, semantic_metadata=None, ttl=ttl)
            
        except Exception as e:
            log.error(f"Failed to cache data for {key}: {e}")

    def set_enhanced(self, key: str, data: Dict[str, Any], 
                    semantic_metadata: Optional[SemanticMetadata] = None, 
                    ttl: int = 86400) -> None:
        """Set enhanced cache entry with optional semantic metadata."""
        try:
            entry = EnhancedCacheEntry(
                data=data,
                semantic_metadata=semantic_metadata,
                cached_at=time.time(),
                ttl_seconds=ttl
            )
            self.cache.set(key, asdict(entry), expire=ttl)
            log.debug(f"Cached enhanced data for {key}")
        except Exception as e:
            log.error(f"Failed to cache enhanced data for {key}: {e}")

    def get_enhanced(self, key: str) -> Optional[EnhancedCacheEntry]:
        """Get enhanced cache entry with semantic metadata."""
        try:
            data = self.cache.get(key)
            if data is None:
                log.debug(f"No enhanced cache entry for {key}")
                return None
            
            # Handle legacy cache format compatibility (temporary during migration)
            if isinstance(data, dict) and 'data' not in data and 'cached_at' not in data:
                # This is legacy format - any dict that's not an EnhancedCacheEntry
                log.debug(f"Migrating legacy cache format for {key}")
                entry = EnhancedCacheEntry(
                    data=data,  # Use the whole dict as data
                    semantic_metadata=None,  # No metadata in legacy format
                    cached_at=time.time(),  # Assume recent
                    ttl_seconds=86400
                )
                # Save in new format immediately
                self.cache.set(key, asdict(entry), expire=entry.ttl_seconds)
                log.debug(f"Migrated {key} to enhanced format")
            else:
                # This is enhanced format - deserialize properly
                try:
                    if 'semantic_metadata' in data and data['semantic_metadata'] is not None:
                        # Convert dict back to SemanticMetadata object
                        metadata_dict = data['semantic_metadata']
                        data['semantic_metadata'] = SemanticMetadata(**metadata_dict)
                    
                    entry = EnhancedCacheEntry(**data)
                except TypeError as e:
                    # Fallback: treat as legacy format if deserialization fails
                    log.debug(f"Falling back to legacy migration for {key}: {e}")
                    entry = EnhancedCacheEntry(
                        data=data,  # Use the whole dict as data
                        semantic_metadata=None,  # No metadata in legacy format
                        cached_at=time.time(),  # Assume recent
                        ttl_seconds=86400
                    )
                    # Save in new format immediately
                    self.cache.set(key, asdict(entry), expire=entry.ttl_seconds)
                    log.debug(f"Migrated {key} to enhanced format via fallback")
            
            if entry.is_expired:
                log.debug(f"Enhanced cache expired for {key}")
                self.cache.delete(key)
                return None
                
            log.debug(f"Enhanced cache hit for {key}")
            return entry
            
        except Exception as e:
            log.warning(f"Failed to load enhanced cache for {key}: {e}")
            return None

    def update_semantic_metadata(self, key: str, semantic_metadata: SemanticMetadata) -> bool:
        """Update semantic metadata for existing cache entry."""
        try:
            entry = self.get_enhanced(key)
            if entry is None:
                log.warning(f"Cannot update metadata for non-existent key: {key}")
                return False
            
            entry.semantic_metadata = semantic_metadata
            self.cache.set(key, asdict(entry), expire=entry.ttl_seconds)
            log.debug(f"Updated semantic metadata for {key}")
            return True
            
        except Exception as e:
            log.error(f"Failed to update semantic metadata for {key}: {e}")
            return False

    def list_by_semantic_type(self, semantic_type: str) -> List[str]:
        """List cached entries by semantic type (vocabulary, context, service)."""
        try:
            matching_keys = []
            for key in self.cache:
                if key.startswith("rdf:"):
                    entry = self.get_enhanced(key)
                    if (entry and entry.semantic_metadata and 
                        entry.semantic_metadata.semantic_type == semantic_type):
                        matching_keys.append(key)
            return matching_keys
        except Exception as e:
            log.error(f"Failed to list by semantic type {semantic_type}: {e}")
            return []

    def list_by_domain(self, domain: str) -> List[str]:
        """List cached entries by domain (biology, chemistry, etc.)."""
        try:
            matching_keys = []
            for key in self.cache:
                if key.startswith("rdf:"):
                    entry = self.get_enhanced(key)
                    if (entry and entry.semantic_metadata and 
                        domain in entry.semantic_metadata.domains):
                        matching_keys.append(key)
            return matching_keys
        except Exception as e:
            log.error(f"Failed to list by domain {domain}: {e}")
            return []

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