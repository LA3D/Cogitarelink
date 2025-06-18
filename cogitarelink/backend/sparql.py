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
        }
    }


def discover_sparql_endpoints() -> Dict[str, str]:
    """Discover SPARQL endpoints from Wikidata."""
    cache_key = "sparql_endpoints"
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
            db_uri = binding.get("database", {}).get("value", "")
            db_label = binding.get("databaseLabel", {}).get("value", "")
            endpoint_url = binding.get("endpoint", {}).get("value", "")
            
            if db_label and endpoint_url:
                endpoints[db_label.lower().replace(" ", "_")] = endpoint_url
        
        # Cache for 24 hours
        cache_manager.set(cache_key, endpoints, ttl=86400)
        log.info(f"Discovered {len(endpoints)} SPARQL endpoints")
        return endpoints
        
    except Exception as e:
        log.error(f"Failed to discover endpoints: {e}")
        return {}


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