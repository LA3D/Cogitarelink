"""Test cache manager following Jeremy Howard's test-as-you-go approach."""

import pytest
import tempfile
from pathlib import Path
import time

from cogitarelink.discovery.cache_manager import CacheManager, CachedSchema


def test_cache_basic_operations():
    """Test basic cache operations."""
    # Use temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        with CacheManager(Path(temp_dir)) as cache:
            # Test cache miss
            result = cache.get("test_endpoint")
            assert result is None
            
            # Test cache set and hit
            test_prefixes = {"wd": "http://example.org/"}
            cache.set("test_endpoint", test_prefixes)
            
            result = cache.get("test_endpoint")
            assert result is not None
            assert result.endpoint == "test_endpoint"
            assert result.prefixes == test_prefixes


def test_cache_expiration():
    """Test cache TTL expiration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with CacheManager(Path(temp_dir)) as cache:
            # Set cache with 1-second TTL
            test_prefixes = {"wd": "http://example.org/"}
            cache.set("test_endpoint", test_prefixes, ttl_seconds=1)
            
            # Should be available immediately
            result = cache.get("test_endpoint")
            assert result is not None
            
            # Wait for expiration
            time.sleep(1.1)
            
            # Should be expired and removed
            result = cache.get("test_endpoint")
            assert result is None


def test_cached_schema_dataclass():
    """Test CachedSchema dataclass."""
    from dataclasses import asdict
    
    schema = CachedSchema(
        endpoint="test",
        prefixes={"wd": "http://example.org/"},
        classes={},
        properties={},
        patterns={},
        cached_at=time.time(),
        ttl_seconds=3600
    )
    
    # Test serialization using asdict (dataclass standard)
    data = asdict(schema)
    assert data["endpoint"] == "test"
    assert data["prefixes"]["wd"] == "http://example.org/"
    
    # Test deserialization
    schema2 = CachedSchema(**data)
    assert schema2.endpoint == schema.endpoint
    assert schema2.prefixes == schema.prefixes


def test_cache_clear():
    """Test cache clearing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with CacheManager(Path(temp_dir)) as cache:
            # Add multiple cache entries
            cache.set("endpoint1", {"wd": "http://example.org/"})
            cache.set("endpoint2", {"wp": "http://example.org/"})
            
            # Check both exist
            assert cache.get("endpoint1") is not None
            assert cache.get("endpoint2") is not None
            
            # Clear specific endpoint
            cache.clear("endpoint1")
            assert cache.get("endpoint1") is None
            assert cache.get("endpoint2") is not None
            
            # Clear all
            cache.clear()
            assert cache.get("endpoint2") is None


def test_list_cached():
    """Test listing cached endpoints."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with CacheManager(Path(temp_dir)) as cache:
            # Initially empty
            assert cache.list_cached() == []
            
            # Add some entries
            cache.set("wikidata", {"wd": "http://example.org/"})
            cache.set("uniprot", {"up": "http://example.org/"})
            
            cached = cache.list_cached()
            assert len(cached) == 2
            assert "wikidata" in cached
            assert "uniprot" in cached