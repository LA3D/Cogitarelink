"""Shared test configuration and fixtures."""

from __future__ import annotations

import pytest
from pathlib import Path
from typing import Dict, Any
import tempfile
import json

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_entity_data() -> Dict[str, Any]:
    """Sample entity data for testing."""
    return {
        "@type": "bioschemas:Protein",
        "name": "Insulin",
        "identifier": "P01308",
        "hasSequence": "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN"
    }


@pytest.fixture
def sample_vocab_list() -> list[str]:
    """Sample vocabulary list for testing."""
    return ["bioschemas", "schema.org"]


@pytest.fixture
def mock_discovery_response() -> Dict[str, Any]:
    """Mock discovery response for testing."""
    return {
        "success": True,
        "data": {
            "endpoints": [
                {
                    "url": "https://query.wikidata.org/sparql",
                    "type": "sparql",
                    "vocabularies": ["wikidata", "schema.org"]
                }
            ],
            "vocabularies": ["wikidata", "schema.org", "bioschemas"]
        },
        "metadata": {
            "execution_time_ms": 1250,
            "discovery_methods_used": ["void", "introspection"],
            "cache_hits": 2
        },
        "suggestions": {
            "next_tools": ["cl_sparql --endpoint wikidata"],
            "reasoning_patterns": ["🧬 PROTEIN → PATHWAY → DISEASE"],
            "workflow_steps": ["1. Query for proteins", "2. Follow pathways"]
        },
        "claude_guidance": {
            "endpoint_capabilities": ["Supports federated queries"],
            "optimization_hints": ["Use LIMIT for large result sets"],
            "domain_context": ["Biological research patterns available"]
        }
    }


@pytest.fixture
def sample_sparql_query() -> str:
    """Sample SPARQL query for testing."""
    return """
    SELECT ?protein ?label WHERE {
        ?protein wdt:P31 wd:Q8054 .
        ?protein rdfs:label ?label .
        FILTER(LANG(?label) = "en")
    } LIMIT 10
    """


# Fast.ai style test utilities
def assert_eq(a, b, msg=""):
    """Assert equality with optional message (fast.ai style)."""
    assert a == b, f"{msg}: {a} != {b}"


def assert_ne(a, b, msg=""):
    """Assert inequality with optional message (fast.ai style)."""
    assert a != b, f"{msg}: {a} == {b}"


def assert_fail(func, msg="", contains=""):
    """Assert function raises exception (fast.ai style)."""
    try:
        func()
        assert False, f"{msg}: Expected exception but none raised"
    except Exception as e:
        if contains:
            assert contains in str(e), f"{msg}: Exception '{e}' doesn't contain '{contains}'"


# Pytest markers for different test types
unit = pytest.mark.unit
integration = pytest.mark.integration
interactive = pytest.mark.interactive
slow = pytest.mark.slow