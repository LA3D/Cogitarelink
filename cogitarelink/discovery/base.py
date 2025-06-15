"""Discovery base using proper libraries - don't reinvent the wheel!

Uses SPARQLWrapper for SPARQL queries and RDFLib for RDF processing.
"""

from __future__ import annotations

from typing import Dict, Any, List
from dataclasses import dataclass

from SPARQLWrapper import SPARQLWrapper, JSON

from .cache_manager import cache_manager
from ..core.debug import get_logger

log = get_logger("discovery_base")


@dataclass
class DiscoveryResult:
    """Simple discovery result."""
    endpoint: str
    url: str
    prefixes: Dict[str, str]
    patterns: Dict[str, str]
    guidance: List[str]


class DiscoveryEngine:
    """Discovery engine using SPARQLWrapper and proper libraries."""
    
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
                "Always include SERVICE wikibase:label for human-readable labels",
                "Add LIMIT clause for performance"
            ]
        },
        "wikipathways": {
            "url": "https://sparql.wikipathways.org/sparql",
            "prefixes": {
                "wp": "http://vocabularies.wikipathways.org/wp#",
                "dc": "http://purl.org/dc/elements/1.1/",
                "dcterms": "http://purl.org/dc/terms/",
                "foaf": "http://xmlns.com/foaf/0.1/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            },
            "patterns": {
                "pathway_search": "SELECT ?pathway ?title WHERE {{ ?pathway a wp:Pathway . ?pathway dc:title ?title . FILTER(CONTAINS(LCASE(?title), '{query}')) }} LIMIT 10"
            },
            "guidance": [
                "Use wp:Pathway for biological pathways",
                "dc:title contains pathway names",
                "Filter by organism with wp:organism"
            ]
        },
        "uniprot": {
            "url": "https://sparql.uniprot.org/sparql", 
            "prefixes": {
                "up": "http://purl.uniprot.org/core/",
                "taxon": "http://purl.uniprot.org/taxonomy/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "skos": "http://www.w3.org/2004/02/skos/core#"
            },
            "patterns": {
                "protein_search": "SELECT ?protein ?name WHERE {{ ?protein a up:Protein . ?protein up:recommendedName/up:fullName ?name . FILTER(CONTAINS(LCASE(?name), '{query}')) }} LIMIT 10"
            },
            "guidance": [
                "Use up:Protein for protein entities",
                "up:recommendedName/up:fullName for protein names",
                "Filter by organism with up:organism"
            ]
        }
    }
    
    def discover(self, endpoint: str) -> DiscoveryResult:
        """Discover endpoint schema with caching."""
        
        # Check cache first
        cached = cache_manager.get(endpoint)
        if cached:
            log.debug(f"Using cached schema for {endpoint}")
            return DiscoveryResult(
                endpoint=endpoint,
                url=self._get_endpoint_url(endpoint),
                prefixes=cached.prefixes,
                patterns=cached.patterns,
                guidance=self._get_guidance(endpoint)
            )
        
        # Discover schema
        if endpoint in self.KNOWN_ENDPOINTS:
            schema = self.KNOWN_ENDPOINTS[endpoint]
            
            # Cache the result using diskcache
            cache_manager.set(
                endpoint=endpoint,
                prefixes=schema["prefixes"],
                patterns=schema["patterns"],
                ttl_seconds=24*3600  # Cache for 24 hours
            )
            
            return DiscoveryResult(
                endpoint=endpoint,
                url=schema["url"],
                prefixes=schema["prefixes"],
                patterns=schema["patterns"],
                guidance=schema["guidance"]
            )
        else:
            # Try SPARQL introspection for unknown endpoints
            return self._introspect_endpoint(endpoint)
    
    def _get_endpoint_url(self, endpoint: str) -> str:
        """Get endpoint URL."""
        if endpoint in self.KNOWN_ENDPOINTS:
            return self.KNOWN_ENDPOINTS[endpoint]["url"]
        return f"https://{endpoint}/sparql"
    
    def _get_guidance(self, endpoint: str) -> List[str]:
        """Get guidance for endpoint."""
        if endpoint in self.KNOWN_ENDPOINTS:
            return self.KNOWN_ENDPOINTS[endpoint]["guidance"]
        return ["Use LIMIT clauses for performance", "Check endpoint documentation"]
    
    def _introspect_endpoint(self, endpoint: str) -> DiscoveryResult:
        """SPARQL introspection using SPARQLWrapper for unknown endpoints."""
        url = f"https://{endpoint}/sparql"
        
        try:
            # Use SPARQLWrapper for proper SPARQL querying
            sparql = SPARQLWrapper(url)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(10)  # 10 second timeout
            
            # Try a simple query to detect basic capabilities
            sparql.setQuery("""
                SELECT DISTINCT ?predicate WHERE {
                    ?s ?predicate ?o .
                } LIMIT 5
            """)
            
            results = sparql.query().convert()
            log.debug(f"Introspected {endpoint}: found {len(results.get('results', {}).get('bindings', []))} predicates")
            
            # Basic discovered prefixes
            discovered_prefixes = {
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "owl": "http://www.w3.org/2002/07/owl#"
            }
            
        except Exception as e:
            log.warning(f"SPARQL introspection failed for {endpoint}: {e}")
            # Fallback to minimal prefixes
            discovered_prefixes = {
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
            }
        
        basic_patterns = {
            "basic_query": "SELECT ?s ?p ?o WHERE {{ ?s ?p ?o }} LIMIT 10"
        }
        
        basic_guidance = [
            "Unknown endpoint - use basic SPARQL patterns",
            "Add LIMIT clauses for safety",
            "Discover prefixes manually"
        ]
        
        # Cache minimal result using diskcache
        cache_manager.set(
            endpoint=endpoint,
            prefixes=discovered_prefixes,
            patterns=basic_patterns,
            ttl_seconds=1800  # Cache for 30 minutes only
        )
        
        return DiscoveryResult(
            endpoint=endpoint,
            url=url,
            prefixes=discovered_prefixes,
            patterns=basic_patterns,
            guidance=basic_guidance
        )
    
    def query_endpoint(self, endpoint: str, sparql_query: str) -> Dict[str, Any]:
        """Execute SPARQL query using SPARQLWrapper."""
        url = self._get_endpoint_url(endpoint)
        
        try:
            sparql = SPARQLWrapper(url)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(30)  # 30 second timeout
            sparql.setQuery(sparql_query)
            
            results = sparql.query().convert()
            log.debug(f"Query executed on {endpoint}: {len(results.get('results', {}).get('bindings', []))} results")
            
            return {
                "success": True,
                "results": results.get('results', {}).get('bindings', []),
                "head": results.get('head', {}),
                "endpoint": url
            }
            
        except Exception as e:
            log.error(f"SPARQL query failed on {endpoint}: {e}")
            return {
                "success": False,
                "error": str(e),
                "endpoint": url
            }


# Global discovery engine
discovery_engine = DiscoveryEngine()