"""
Unified SPARQL Client - Simplified from multiple adapter classes

Based on wikidata-mcp's successful client pattern.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import quote_plus, urljoin

class UnifiedSparqlClient:
    """
    Simplified SPARQL client supporting multiple endpoints.
    
    Following wikidata-mcp pattern: one client, multiple endpoints.
    """
    
    # Standard SPARQL endpoints with their characteristics
    ENDPOINTS = {
        "wikidata": {
            "url": "https://query.wikidata.org/sparql",
            "search_url": "https://www.wikidata.org/w/api.php",
            "timeout": 30,
            "max_results": 1000
        },
        "uniprot": {
            "url": "https://sparql.uniprot.org/sparql",
            "timeout": 30,
            "max_results": 1000
        },
        "wikipathways": {
            "url": "https://sparql.wikipathways.org/sparql", 
            "timeout": 30,
            "max_results": 1000
        },
        "idsm": {
            "url": "https://idsm.elixir-czech.cz/sparql/endpoint/idsm",
            "timeout": 60,
            "max_results": 1000
        }
    }
    
    def __init__(self, default_endpoint: str = "wikidata"):
        self.default_endpoint = default_endpoint
        self.session = None
        
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=60.0,
                headers={
                    "User-Agent": "Cogitarelink/0.2.0 (https://github.com/LA3D/cogitarelink) Universal Knowledge Discovery"
                }
            )
        return self.session
        
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def search_entities(
        self,
        query: str, 
        endpoint: str = None,
        language: str = "en",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search for entities (currently Wikidata only).
        """
        endpoint = endpoint or self.default_endpoint
        
        if endpoint != "wikidata":
            raise ValueError("Entity search currently only supported for Wikidata")
            
        session = await self._get_session()
        
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": language,
            "limit": limit,
            "format": "json"
        }
        
        search_url = self.ENDPOINTS["wikidata"]["search_url"]
        response = await session.get(search_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return {
            "results": data.get("search", []),
            "query": query,
            "language": language,
            "limit": limit
        }
    
    
    def _add_prefixes_for_endpoint(self, query: str, endpoint: str) -> str:
        """
        Add required SPARQL prefixes for endpoint if not already present.
        """
        query_upper = query.upper()
        
        # Check if prefixes already exist
        if "PREFIX" in query_upper:
            return query
        
        prefixes = {
            "wikidata": [
                "PREFIX wd: <http://www.wikidata.org/entity/>",
                "PREFIX wdt: <http://www.wikidata.org/prop/direct/>",
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
                "PREFIX wikibase: <http://wikiba.se/ontology#>",
                "PREFIX bd: <http://www.bigdata.com/rdf#>"
            ],
            "uniprot": [
                "PREFIX up: <http://purl.uniprot.org/core/>",
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
                "PREFIX taxon: <http://purl.uniprot.org/taxonomy/>"
            ],
            "wikipathways": [
                "PREFIX wp: <http://vocabularies.wikipathways.org/wp#>",
                "PREFIX dc: <http://purl.org/dc/elements/1.1/>",
                "PREFIX foaf: <http://xmlns.com/foaf/0.1/>"
            ]
        }
        
        endpoint_prefixes = prefixes.get(endpoint, [
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"
        ])
        
        prefix_block = "\n".join(endpoint_prefixes) + "\n\n"
        return prefix_block + query
    
    async def sparql_query(
        self,
        query: str,
        endpoint: str = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute SPARQL query against specified endpoint with automatic prefix handling.
        """
        endpoint = endpoint or self.default_endpoint
        
        if endpoint not in self.ENDPOINTS:
            raise ValueError(f"Unknown endpoint: {endpoint}")
            
        endpoint_config = self.ENDPOINTS[endpoint]
        timeout = timeout or endpoint_config["timeout"]
        
        session = await self._get_session()
        
        # Add prefixes for endpoint
        query_with_prefixes = self._add_prefixes_for_endpoint(query, endpoint)
        
        # Add LIMIT if missing
        query_upper = query_with_prefixes.upper()
        if "LIMIT" not in query_upper and "COUNT" not in query_upper and "ASK" not in query_upper:
            query_with_prefixes = query_with_prefixes.rstrip() + f" LIMIT {endpoint_config['max_results']}"
        
        headers = {
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"query": query_with_prefixes}
        
        start_time = time.time()
        
        try:
            response = await session.post(
                endpoint_config["url"],
                headers=headers,
                data=data,
                timeout=timeout
            )
            response.raise_for_status()
            
            result_data = response.json()
            execution_time = int((time.time() - start_time) * 1000)
            
            return {
                "results": result_data,
                "query": query,
                "query_with_prefixes": query_with_prefixes,
                "endpoint": endpoint,
                "execution_time_ms": execution_time,
                "status": "success"
            }
            
        except httpx.TimeoutException:
            return {
                "error": f"Query timeout after {timeout}s",
                "query": query,
                "query_with_prefixes": query_with_prefixes,
                "endpoint": endpoint,
                "status": "timeout"
            }
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "query_with_prefixes": query_with_prefixes,
                "endpoint": endpoint,
                "status": "error"
            }