"""Test discovery base module."""

import pytest
import tempfile
from pathlib import Path

from cogitarelink.discovery.base import DiscoveryEngine, DiscoveryResult
from cogitarelink.discovery.cache_manager import CacheManager


def test_discover_wikidata():
    """Test discovering known Wikidata endpoint."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use temporary cache for testing
        from cogitarelink.discovery import cache_manager
        cache_manager.cache_manager.cache_dir = Path(temp_dir)
        
        engine = DiscoveryEngine()
        result = engine.discover("wikidata")
        
        assert result.endpoint == "wikidata"
        assert result.url == "https://query.wikidata.org/sparql"
        assert "wd" in result.prefixes
        assert "wdt" in result.prefixes
        assert "basic_query" in result.patterns
        assert len(result.guidance) > 0


def test_discover_unknown_endpoint():
    """Test discovering unknown endpoint."""
    with tempfile.TemporaryDirectory() as temp_dir:
        from cogitarelink.discovery import cache_manager
        cache_manager.cache_manager.cache_dir = Path(temp_dir)
        
        engine = DiscoveryEngine()
        result = engine.discover("unknown-endpoint")
        
        assert result.endpoint == "unknown-endpoint"
        assert result.url == "https://unknown-endpoint/sparql"
        assert "rdfs" in result.prefixes
        assert "basic_query" in result.patterns
        # Since SPARQL introspection fails, it should use fallback guidance
        assert any("LIMIT" in guidance for guidance in result.guidance)


def test_discover_with_caching():
    """Test discovery uses caching."""
    with tempfile.TemporaryDirectory() as temp_dir:
        from cogitarelink.discovery import cache_manager
        cache_manager.cache_manager.cache_dir = Path(temp_dir)
        
        engine = DiscoveryEngine()
        
        # First discovery should cache
        result1 = engine.discover("wikidata")
        
        # Second discovery should use cache
        result2 = engine.discover("wikidata")
        
        assert result1.endpoint == result2.endpoint
        assert result1.prefixes == result2.prefixes
        
        # Check cache was actually used
        cached_endpoints = cache_manager.cache_manager.list_cached()
        assert "wikidata" in cached_endpoints


def test_discovery_result_dataclass():
    """Test DiscoveryResult dataclass."""
    result = DiscoveryResult(
        endpoint="test",
        url="https://test.org/sparql",
        prefixes={"test": "http://test.org/"},
        patterns={"basic": "SELECT * WHERE { ?s ?p ?o }"},
        guidance=["Use LIMIT clauses"]
    )
    
    assert result.endpoint == "test"
    assert result.url == "https://test.org/sparql"
    assert result.prefixes["test"] == "http://test.org/"
    assert "basic" in result.patterns
    assert len(result.guidance) == 1