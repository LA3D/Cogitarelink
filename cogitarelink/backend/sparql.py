"""SPARQL operations and endpoint discovery.

Combined SPARQL utilities: endpoint discovery, query execution, pattern management.
Uses proper libraries (SPARQLWrapper, httpx) and caching for performance.
"""

from __future__ import annotations

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import httpx
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, JSON

from .cache import cache_manager
from ..utils.logging import get_logger

log = get_logger("sparql")


@dataclass
class DiscoveryResult:
    """Simple discovery result."""
    endpoint: str
    url: str
    prefixes: Dict[str, str]
    patterns: Dict[str, str]
    guidance: List[str]


class SPARQLEngine:
    """SPARQL operations using SPARQLWrapper and proper libraries."""
    
    # Known endpoint patterns
    KNOWN_ENDPOINTS = {
        "wikidata": {
            "url": "https://query.wikidata.org/sparql",
            "prefixes": {
                "wd": "http://www.wikidata.org/entity/",
                "wdt": "http://www.wikidata.org/prop/direct/", 
                "p": "http://www.wikidata.org/prop/",
                "ps": "http://www.wikidata.org/prop/statement/",
                "pq": "http://www.wikidata.org/prop/qualifier/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "wikibase": "http://wikiba.se/ontology#",
                "bd": "http://www.bigdata.com/rdf#"
            },
            "patterns": {
                "entity_search": "SELECT ?item ?itemLabel WHERE {{ ?item rdfs:label ?itemLabel . FILTER(CONTAINS(LCASE(?itemLabel), '{query}')) }} LIMIT 10",
                "basic_query": "SELECT ?item ?itemLabel WHERE {{ ?item wdt:P31 ?type . SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'en' }} }} LIMIT 10"
            },
            "guidance": [
                "Use wdt: for direct properties",
                "Always include SERVICE wikibase:label for readable labels",
                "FILTER with CONTAINS for text search"
            ]
        },
        "uniprot": {
            "url": "https://sparql.uniprot.org/sparql",
            "prefixes": {
                "up": "http://purl.uniprot.org/core/",
                "uniprotkb": "http://purl.uniprot.org/uniprot/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "taxon": "http://purl.uniprot.org/taxonomy/"
            },
            "patterns": {
                "protein_search": "SELECT ?protein ?name WHERE {{ ?protein a up:Protein ; up:recommendedName/up:fullName ?name . FILTER(CONTAINS(LCASE(?name), '{query}')) }} LIMIT 10"
            },
            "guidance": [
                "Use up: for UniProt core ontology",
                "Proteins are up:Protein class",
                "Use up:recommendedName for official names"
            ]
        },
        "wikipathways": {
            "url": "https://sparql.wikipathways.org/sparql",
            "prefixes": {
                "wp": "http://vocabularies.wikipathways.org/wp#",
                "gpml": "http://vocabularies.wikipathways.org/gpml#",
                "dcterms": "http://purl.org/dc/terms/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            },
            "patterns": {
                "pathway_search": "SELECT ?pathway ?title WHERE {{ ?pathway a wp:Pathway ; dcterms:title ?title . FILTER(CONTAINS(LCASE(?title), '{query}')) }} LIMIT 10"
            },
            "guidance": [
                "Use wp: for WikiPathways vocabulary",
                "Pathways are wp:Pathway class",
                "Use dcterms:title for pathway names"
            ]
        },
        "dbpedia": {
            "url": "https://dbpedia.org/sparql",
            "prefixes": {
                "dbo": "http://dbpedia.org/ontology/",
                "dbr": "http://dbpedia.org/resource/",
                "dct": "http://purl.org/dc/terms/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "owl": "http://www.w3.org/2002/07/owl#",
                "foaf": "http://xmlns.com/foaf/0.1/"
            },
            "patterns": {
                "entity_search": "SELECT ?entity ?label WHERE {{ ?entity rdfs:label ?label . FILTER(CONTAINS(LCASE(?label), '{query}')) FILTER(LANG(?label) = 'en') }} LIMIT 10",
                "class_search": "SELECT ?class ?label WHERE {{ ?class a owl:Class ; rdfs:label ?label . FILTER(CONTAINS(LCASE(?label), '{query}')) FILTER(LANG(?label) = 'en') }} LIMIT 10"
            },
            "guidance": [
                "Use dbo: for DBpedia ontology classes and properties",
                "Use dbr: for DBpedia resources (entities)",
                "Filter by LANG(?label) = 'en' for English labels",
                "Standard RDFS/OWL vocabulary supported"
            ]
        }
    }


def get_all_endpoints() -> Dict[str, str]:
    """Get all available endpoints: known + discovered + cached."""
    # Start with known endpoints
    all_endpoints = {}
    for name, config in SPARQLEngine.KNOWN_ENDPOINTS.items():
        all_endpoints[name] = config["url"]
    
    # Add dynamically discovered endpoints
    dynamic_endpoints = discover_sparql_endpoints_dynamic()
    all_endpoints.update(dynamic_endpoints)
    
    # Add endpoints from cached service descriptions
    cached_endpoints = get_cached_endpoints()
    all_endpoints.update(cached_endpoints)
    
    return all_endpoints


def resolve_endpoint(endpoint_name: str) -> tuple[str, Dict[str, str]]:
    """Resolve endpoint name to URL and prefixes.
    
    Returns: (endpoint_url, prefixes)
    Raises: ValueError if endpoint not found
    """
    if endpoint_name.startswith("http"):
        return endpoint_name, {}
    
    # Check KNOWN_ENDPOINTS first (highest priority)
    if endpoint_name in SPARQLEngine.KNOWN_ENDPOINTS:
        config = SPARQLEngine.KNOWN_ENDPOINTS[endpoint_name]
        return config["url"], config["prefixes"]
    
    # Check cached endpoints with discovered prefixes
    cached_endpoint = get_cached_endpoint_info(endpoint_name)
    if cached_endpoint:
        return cached_endpoint["url"], cached_endpoint.get("prefixes", {})
    
    # Fall back to dynamic discovery
    dynamic_endpoints = discover_sparql_endpoints_dynamic()
    if endpoint_name in dynamic_endpoints:
        return dynamic_endpoints[endpoint_name], {}
    
    # Not found anywhere
    all_available = list(get_all_endpoints().keys())
    raise ValueError(f"Unknown endpoint: {endpoint_name}. Available: {all_available}")


def get_cached_endpoints() -> Dict[str, str]:
    """Extract endpoint aliases from cached service descriptions."""
    from .cache import cache_manager
    
    cached_endpoints = {}
    
    # Get all cached items with service_description type
    service_keys = cache_manager.list_by_semantic_type("service_description")
    for key in service_keys:
        entry = cache_manager.get_enhanced(key)
        if entry and entry.semantic_metadata:
            # Extract endpoint info from metadata
            if hasattr(entry.semantic_metadata, 'endpoint_info'):
                endpoint_info = entry.semantic_metadata.endpoint_info
                if isinstance(endpoint_info, dict) and "alias" in endpoint_info:
                    alias = endpoint_info["alias"]
                    # Derive URL from cache key or stored info
                    url = endpoint_info.get("url", f"https://{alias}.org/sparql")
                    cached_endpoints[alias] = url
    
    return cached_endpoints


def get_cached_endpoint_info(endpoint_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed endpoint info from cache including prefixes."""
    from .cache import cache_manager
    
    # Look for cached service description
    cache_key = f"rdf:{endpoint_name}_service"
    enhanced_entry = cache_manager.get_enhanced(cache_key)
    
    if enhanced_entry and enhanced_entry.semantic_metadata:
        metadata = enhanced_entry.semantic_metadata
        if hasattr(metadata, 'endpoint_info'):
            return metadata.endpoint_info
    
    return None


def discover_sparql_endpoints_dynamic() -> Dict[str, str]:
    """Discover SPARQL endpoints from Wikidata (original function)."""
    cache_key = "sparql_endpoints_dynamic"
    cached = cache_manager.get(cache_key)
    if cached:
        log.debug("Using cached SPARQL endpoints")
        return cached
    
    try:
        # Query Wikidata for databases with SPARQL endpoints
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
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
            db_label = binding.get("databaseLabel", {}).get("value", "")
            endpoint_url = binding.get("endpoint", {}).get("value", "")
            
            if db_label and endpoint_url:
                # Prioritize main endpoints over language variants
                alias = db_label.lower().replace(" ", "_")
                if "dbpedia" in alias and not alias.startswith("dbpedia"):
                    continue  # Skip language variants like "japanese_dbpedia"
                endpoints[alias] = endpoint_url
        
        # Cache for 24 hours
        cache_manager.set(cache_key, endpoints, ttl=86400)
        log.info(f"Discovered {len(endpoints)} SPARQL endpoints")
        return endpoints
        
    except Exception as e:
        log.error(f"Failed to discover endpoints: {e}")
        return {}


def discover_sparql_endpoints() -> Dict[str, str]:
    """Legacy function - use get_all_endpoints() for new code."""
    return get_all_endpoints()


def build_prefixed_query(query: str, endpoint: str = "wikidata") -> str:
    """Build SPARQL query with appropriate prefixes."""
    if endpoint in SPARQLEngine.KNOWN_ENDPOINTS:
        prefixes = SPARQLEngine.KNOWN_ENDPOINTS[endpoint]["prefixes"]
        prefix_lines = [f"PREFIX {prefix}: <{uri}>" for prefix, uri in prefixes.items()]
        return "\n".join(prefix_lines) + "\n\n" + query
    return query


def get_endpoint_guidance(endpoint: str) -> List[str]:
    """Get usage guidance for a specific endpoint."""
    if endpoint in SPARQLEngine.KNOWN_ENDPOINTS:
        return SPARQLEngine.KNOWN_ENDPOINTS[endpoint]["guidance"]
    return []


def get_entity_uri(entity: str, endpoint_url: str) -> str:
    """Convert entity identifier to full URI based on endpoint."""
    if entity.startswith("http"):
        return entity
    
    # Handle prefixed entities
    if ":" in entity and not entity.startswith("http"):
        prefix, local = entity.split(":", 1)
        
        # Look up prefix in KNOWN_ENDPOINTS
        for config in SPARQLEngine.KNOWN_ENDPOINTS.values():
            if config["url"] == endpoint_url:
                prefixes = config["prefixes"]
                if prefix in prefixes:
                    return f"{prefixes[prefix]}{local}"
                break
    
    # Wikidata entities
    if "wikidata" in endpoint_url.lower():
        if entity.startswith("Q") or entity.startswith("P"):
            return f"http://www.wikidata.org/entity/{entity}"
    
    # UniProt entities  
    if "uniprot" in endpoint_url.lower():
        return f"http://purl.uniprot.org/uniprot/{entity}"
    
    # WikiPathways entities
    if "wikipathways" in endpoint_url.lower():
        return f"http://identifiers.org/wikipathways/{entity}"
    
    # Default: assume it's already a proper URI or local name
    return entity


def find_endpoint_for_entity(entity: str) -> Optional[str]:
    """Find appropriate endpoint for an entity ID."""
    if entity.startswith("Q") or entity.startswith("P"):
        return "https://query.wikidata.org/sparql"
    elif entity.startswith("WP"):
        return "https://sparql.wikipathways.org/sparql"
    elif len(entity) == 6 and entity.isalnum():  # UniProt pattern
        return "https://sparql.uniprot.org/sparql"
    return None


# Create global instances for easy import
sparql_engine = SPARQLEngine()