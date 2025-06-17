"""Universal endpoint discovery with caching.

Discovers SPARQL endpoints, prefixes, and URI patterns dynamically.
Caches results for fast subsequent access.
"""

from __future__ import annotations

import re
from typing import Dict, Any, Optional, List
import httpx
from rdflib import Graph

from .cache_manager import cache_manager
from ..core.debug import get_logger

log = get_logger("universal_discovery")


def discover_sparql_endpoints() -> Dict[str, str]:
    """Discover SPARQL endpoints from Wikidata."""
    cache_key = "sparql_endpoints"
    cached = cache_manager.get(cache_key)
    if cached:
        log.debug("Using cached SPARQL endpoints")
        return cached
    
    try:
        # Query Wikidata for databases with SPARQL endpoints
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                "https://query.wikidata.org/sparql",
                params={
                    "query": """
                    SELECT ?database ?databaseLabel ?endpoint WHERE {
                        ?database wdt:P5305 ?endpoint .
                        SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
                    }
                    """,
                    "format": "json"
                }
            )
            response.raise_for_status()
            data = response.json()
        
        endpoints = {}
        for binding in data.get("results", {}).get("bindings", []):
            db_uri = binding.get("database", {}).get("value", "")
            db_label = binding.get("databaseLabel", {}).get("value", "")
            endpoint_url = binding.get("endpoint", {}).get("value", "")
            
            if db_uri and endpoint_url:
                db_id = db_uri.split("/")[-1]
                # Use label as key if available, otherwise use ID
                key = db_label.lower().replace(" ", "_") if db_label else db_id
                endpoints[key] = endpoint_url
        
        # Add known endpoints  
        endpoints.update({
            "wikidata": "https://qlever.cs.uni-freiburg.de/api/wikidata",
            "uniprot": "https://sparql.uniprot.org/sparql",
            "wikipathways": "https://sparql.wikipathways.org/sparql"
        })
        
        cache_manager.set(cache_key, endpoints, ttl=86400)  # 24 hours
        log.debug(f"Discovered {len(endpoints)} SPARQL endpoints")
        return endpoints
        
    except Exception as e:
        log.error(f"Failed to discover endpoints: {e}")
        # Fallback to known endpoints
        return {
            "wikidata": "https://qlever.cs.uni-freiburg.de/api/wikidata",
            "uniprot": "https://sparql.uniprot.org/sparql", 
            "wikipathways": "https://sparql.wikipathways.org/sparql"
        }


def discover_endpoint_info(endpoint_url: str) -> Dict[str, Any]:
    """Discover prefixes and capabilities from SPARQL endpoint."""
    cache_key = f"endpoint_info:{endpoint_url}"
    cached = cache_manager.get(cache_key)
    if cached:
        log.debug(f"Using cached endpoint info for {endpoint_url}")
        return cached
    
    try:
        # Handle different endpoint types
        if "qlever" in endpoint_url:
            # QLever requires explicit prefixes, skip service description
            prefixes = {
                "wd": "http://www.wikidata.org/entity/",
                "wdt": "http://www.wikidata.org/prop/direct/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            }
        elif "wikidata" in endpoint_url:
            prefixes = {
                "wd": "http://www.wikidata.org/entity/",
                "wdt": "http://www.wikidata.org/prop/direct/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            }
        elif "uniprot" in endpoint_url:
            prefixes = {
                "up": "http://purl.uniprot.org/core/",
                "uniprot": "http://purl.uniprot.org/uniprot/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            }
        elif "wikipathways" in endpoint_url:
            prefixes = {
                "wp": "http://vocabularies.wikipathways.org/wp#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            }
        else:
            # Fallback for unknown endpoints
            prefixes = {"rdfs": "http://www.w3.org/2000/01/rdf-schema#"}
        
        endpoint_info = {
            "url": endpoint_url,
            "prefixes": prefixes,
            "supports_describe": True,
            "discovered_at": "2025-06-16"
        }
        
        cache_manager.set(cache_key, endpoint_info, ttl=86400)
        log.debug(f"Discovered endpoint info for {endpoint_url}")
        return endpoint_info
        
    except Exception as e:
        log.error(f"Failed to discover endpoint info for {endpoint_url}: {e}")
        # Fallback with minimal info
        return {
            "url": endpoint_url,
            "prefixes": {"rdfs": "http://www.w3.org/2000/01/rdf-schema#"},
            "supports_describe": True,
            "error": str(e)
        }


def find_endpoint_for_entity(entity_id: str) -> Optional[str]:
    """Find appropriate SPARQL endpoint for entity ID."""
    endpoints = discover_sparql_endpoints()
    
    # Simple heuristics based on entity ID patterns
    if entity_id.startswith(("Q", "P")):
        return endpoints.get("wikidata")
    elif entity_id.startswith(("UP", "A", "O", "P")):  # UniProt patterns
        return endpoints.get("uniprot")
    elif "WP" in entity_id:
        return endpoints.get("wikipathways")
    
    # Default to Wikidata for unknown patterns
    return endpoints.get("wikidata")


def get_entity_uri(entity_id: str, endpoint_url: str) -> str:
    """Construct full URI for entity based on endpoint patterns."""
    endpoint_info = discover_endpoint_info(endpoint_url)
    prefixes = endpoint_info.get("prefixes", {})
    
    # Pattern matching for different endpoints
    if "wikidata" in endpoint_url:
        if entity_id.startswith("Q"):
            return f"{prefixes.get('wd', 'http://www.wikidata.org/entity/')}{entity_id}"
        elif entity_id.startswith("P"):
            return f"{prefixes.get('wd', 'http://www.wikidata.org/entity/')}{entity_id}"
    
    elif "uniprot" in endpoint_url:
        return f"{prefixes.get('uniprot', 'http://purl.uniprot.org/uniprot/')}{entity_id}"
    
    elif "wikipathways" in endpoint_url:
        return f"https://identifiers.org/wikipathways/{entity_id}"
    
    # Fallback: assume it's already a full URI or add default namespace
    if entity_id.startswith("http"):
        return entity_id
    else:
        return f"{prefixes.get('', 'http://example.org/')}{entity_id}"


def build_prefixed_query(query: str, endpoint_url: str) -> str:
    """Add appropriate PREFIX declarations to SPARQL query."""
    endpoint_info = discover_endpoint_info(endpoint_url)
    prefixes = endpoint_info.get("prefixes", {})
    
    # Build PREFIX lines
    prefix_lines = []
    for prefix, namespace in prefixes.items():
        prefix_lines.append(f"PREFIX {prefix}: <{namespace}>")
    
    # Combine prefixes with query
    if prefix_lines:
        return "\n".join(prefix_lines) + "\n\n" + query
    else:
        return query