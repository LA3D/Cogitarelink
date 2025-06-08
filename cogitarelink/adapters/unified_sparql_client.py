"""
Unified SPARQL Client for CogitareLink

Replaces custom httpx implementations with SPARQLWrapper for reliable,
standards-compliant SPARQL operations across all biological databases.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from SPARQLWrapper import SPARQLWrapper, JSON, CSV, XML, TURTLE
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

from ..core.debug import get_logger
from ..intelligence.ontology_discovery import discovery_engine

log = get_logger("unified_sparql")


@dataclass
class QueryResult:
    """Standardized SPARQL query result."""
    data: Dict[str, Any]
    endpoint: str
    query: str
    format: str
    execution_time_ms: int
    bindings_count: int


class UnifiedSPARQLClient:
    """
    Unified SPARQL client using SPARQLWrapper for all endpoints.
    
    Replaces hardcoded HTTP implementations with standards-compliant
    SPARQL operations that automatically handle GET/POST, formats,
    and endpoint-specific requirements.
    """
    
    def __init__(self, default_timeout: int = 30):
        self.default_timeout = default_timeout
        self.discovered_endpoints: Dict[str, Dict[str, Any]] = {}
        
        # Initialize with basic known prefixes as fallback
        self._init_known_prefixes()
        
        # Schema cache for discovered endpoint information
        self.schema_cache: Dict[str, Any] = {}
        
    async def query(
        self,
        endpoint: str,
        query: str,
        return_format: str = "json",
        timeout: int = None,
        add_prefixes: bool = True
    ) -> QueryResult:
        """
        Execute SPARQL query using SPARQLWrapper.
        
        Args:
            endpoint: SPARQL endpoint URL or name
            query: SPARQL query string
            return_format: Output format (json, csv, xml, turtle)
            timeout: Query timeout in seconds
            add_prefixes: Whether to add discovered prefixes
            
        Returns:
            QueryResult with standardized data structure
        """
        import time
        start_time = time.time()
        
        # Get actual endpoint URL if using name
        endpoint_url = self._resolve_endpoint_url(endpoint)
        
        try:
            # Create SPARQLWrapper instance
            sparql = SPARQLWrapper(endpoint_url)
            
            # Set timeout
            if timeout:
                sparql.setTimeout(timeout)
            else:
                sparql.setTimeout(self.default_timeout)
            
            # Add discovered prefixes if available
            final_query = query
            if add_prefixes:
                # Use sophisticated ontology discovery for prefixes
                prefixes = await self._get_discovered_prefixes(endpoint_url)
                final_query = self._add_prefixes(query, prefixes)
            
            # Auto-add LIMIT if missing
            if 'LIMIT' not in final_query.upper() and final_query.strip().upper().startswith('SELECT'):
                final_query = final_query.strip() + ' LIMIT 100'
            
            # Set query and format
            sparql.setQuery(final_query)
            sparql.setReturnFormat(self._get_sparql_format(return_format))
            
            log.info(f"Executing SPARQL query on {endpoint}: {query[:100]}...")
            
            # Execute query - SPARQLWrapper handles GET/POST automatically
            result = sparql.query().convert()
            
            # Calculate metrics
            execution_time = int((time.time() - start_time) * 1000)
            bindings_count = 0
            
            if isinstance(result, dict) and 'results' in result:
                bindings_count = len(result.get('results', {}).get('bindings', []))
            
            log.info(f"SPARQL query on {endpoint} returned {bindings_count} results in {execution_time}ms")
            
            return QueryResult(
                data=result,
                endpoint=endpoint_url,
                query=final_query,
                format=return_format,
                execution_time_ms=execution_time,
                bindings_count=bindings_count
            )
            
        except SPARQLWrapperException as e:
            log.error(f"SPARQL query failed on {endpoint}: {e}")
            raise
        except Exception as e:
            log.error(f"Unexpected error querying {endpoint}: {e}")
            raise
    
    def _resolve_endpoint_url(self, endpoint: str) -> str:
        """Resolve endpoint name to URL."""
        # If it's already a URL, return as-is
        if endpoint.startswith('http'):
            return endpoint
            
        # Known endpoint mappings
        known_endpoints = {
            'wikidata': 'https://query.wikidata.org/sparql',
            'uniprot': 'https://sparql.uniprot.org/sparql',
            'wikipathways': 'https://sparql.wikipathways.org/sparql',
            'idsm': 'https://idsm.elixir-czech.cz/sparql/endpoint/idsm',
            'rhea': 'https://sparql.rhea-db.org/sparql'
        }
        
        return known_endpoints.get(endpoint, endpoint)
    
    def _get_sparql_format(self, format_name: str):
        """Convert format string to SPARQLWrapper constant."""
        format_map = {
            'json': JSON,
            'csv': CSV,
            'xml': XML,
            'turtle': TURTLE,
            'ttl': TURTLE
        }
        return format_map.get(format_name.lower(), JSON)
    
    def _add_prefixes(self, query: str, prefixes: Dict[str, str]) -> str:
        """Add discovered prefixes to query if not present."""
        prefix_lines = []
        
        for prefix, uri in prefixes.items():
            prefix_declaration = f"PREFIX {prefix}: <{uri}>"
            if prefix_declaration not in query and f"{prefix}:" in query:
                prefix_lines.append(prefix_declaration)
        
        if prefix_lines:
            return '\n'.join(prefix_lines) + '\n\n' + query
        
        return query
    
    async def _get_discovered_prefixes(self, endpoint_url: str) -> Dict[str, str]:
        """
        Get prefixes using sophisticated ontology discovery engine.
        
        Uses multi-method discovery: Service Description → VOID → introspection → documentation → samples
        with intelligent caching and fallback to known prefixes.
        """
        # Skip schema discovery - just return basic known prefixes for fast execution
        log.debug(f"Using fallback prefixes for {endpoint_url} (schema discovery disabled for speed)")
        try:
            # Quick timeout schema discovery - don't block SPARQL queries
            schema = await asyncio.wait_for(
                discovery_engine.discover_schema(endpoint_url, discovery_method="auto"), 
                timeout=2.0
            )
            
            # Extract vocabularies as dict regardless of schema format
            if hasattr(schema, 'vocabularies'):
                if isinstance(schema.vocabularies, dict):
                    vocabularies = schema.vocabularies
                elif isinstance(schema.vocabularies, list):
                    # Convert list format to dict
                    vocabularies = {}
                    for vocab in schema.vocabularies:
                        if isinstance(vocab, dict) and 'prefix' in vocab and 'namespace' in vocab:
                            vocabularies[vocab['prefix']] = vocab['namespace']
                else:
                    vocabularies = {}
            else:
                vocabularies = {}
            
            log.info(f"Quick discovery found {len(vocabularies)} vocabularies for {endpoint_url}")
            return vocabularies
            
        except (Exception, asyncio.TimeoutError) as e:
            log.debug(f"Schema discovery skipped for {endpoint_url}: {e}. Using fallback prefixes.")
            # Fall back to known prefixes
            return self._get_known_prefixes(endpoint_url)
    
    def add_endpoint_discovery(self, endpoint: str, discovery_data: Dict[str, Any]):
        """Add discovered endpoint metadata."""
        self.discovered_endpoints[endpoint] = discovery_data
        log.info(f"Added discovery data for endpoint: {endpoint}")
    
    def _init_known_prefixes(self):
        """Initialize basic known prefixes for common endpoints."""
        self.known_prefixes = {
            'wikidata': {
                'wd': 'http://www.wikidata.org/entity/',
                'wdt': 'http://www.wikidata.org/prop/direct/',
                'wikibase': 'http://wikiba.se/ontology#',
                'bd': 'http://www.bigdata.com/rdf#',
                'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                'schema': 'https://schema.org/'
            },
            'uniprot': {
                'up': 'http://purl.uniprot.org/core/',
                'taxon': 'http://purl.uniprot.org/taxonomy/',
                'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                'skos': 'http://www.w3.org/2004/02/skos/core#',
                'xsd': 'http://www.w3.org/2001/XMLSchema#'
            },
            'wikipathways': {
                'wp': 'http://vocabularies.wikipathways.org/wp#',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'dcterms': 'http://purl.org/dc/terms/',
                'foaf': 'http://xmlns.com/foaf/0.1/',
                'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                'xsd': 'http://www.w3.org/2001/XMLSchema#'
            },
            'idsm': {
                'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                'owl': 'http://www.w3.org/2002/07/owl#',
                'skos': 'http://www.w3.org/2004/02/skos/core#',
                'dcterms': 'http://purl.org/dc/terms/',
                'xsd': 'http://www.w3.org/2001/XMLSchema#'
            },
            'rhea': {
                'rh': 'http://rdf.rhea-db.org/',
                'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                'owl': 'http://www.w3.org/2002/07/owl#',
                'xsd': 'http://www.w3.org/2001/XMLSchema#'
            }
        }
    
    def _get_known_prefixes(self, endpoint: str) -> Dict[str, str]:
        """Get known prefixes for an endpoint."""
        endpoint_name = endpoint
        if endpoint.startswith('http'):
            # Map URL back to name
            url_to_name = {
                'https://query.wikidata.org/sparql': 'wikidata',
                'https://sparql.uniprot.org/sparql': 'uniprot',
                'https://sparql.wikipathways.org/sparql': 'wikipathways',
                'https://idsm.elixir-czech.cz/sparql/endpoint/idsm': 'idsm',
                'https://sparql.rhea-db.org/sparql': 'rhea'
            }
            endpoint_name = url_to_name.get(endpoint, endpoint)
        
        return self.known_prefixes.get(endpoint_name, {})
    
    def list_known_endpoints(self) -> List[str]:
        """List all known endpoint names."""
        return ['wikidata', 'uniprot', 'wikipathways', 'idsm', 'rhea']
    
    async def test_endpoint(self, endpoint: str) -> bool:
        """Test if endpoint is responsive with a simple query."""
        try:
            test_query = "SELECT ?s WHERE { ?s ?p ?o } LIMIT 1"
            result = await self.query(endpoint, test_query, timeout=10)
            return True
        except Exception as e:
            log.warning(f"Endpoint {endpoint} test failed: {e}")
            return False


# Global client instance
_client = None

def get_sparql_client() -> UnifiedSPARQLClient:
    """Get the global SPARQL client instance."""
    global _client
    if _client is None:
        _client = UnifiedSPARQLClient()
    return _client


# Async wrapper for backward compatibility
async def sparql_query(
    endpoint: str,
    query: str,
    return_format: str = "json",
    **kwargs
) -> QueryResult:
    """Async wrapper for SPARQL queries."""
    client = get_sparql_client()
    
    # Direct async call - no need for executor since client.query is already async
    return await client.query(endpoint, query, return_format, **kwargs)