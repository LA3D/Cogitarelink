"""
Multi-Endpoint SPARQL Client for CogitareLink

Provides unified SPARQL query interface across multiple biological databases
with endpoint-specific optimizations and vocabulary handling.
"""

from __future__ import annotations

import asyncio
import httpx
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from ..core.debug import get_logger

log = get_logger("multi_sparql")


@dataclass
class EndpointConfig:
    """Configuration for a SPARQL endpoint."""
    name: str
    url: str
    default_prefixes: str
    timeout: int = 30
    description: str = ""
    examples: List[str] = None


class MultiSparqlClient:
    """
    Multi-endpoint SPARQL client with biological database specializations.
    
    Supports Wikidata, WikiPathways, UniProt, IDSM, and custom endpoints
    with appropriate vocabulary handling and optimizations.
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.endpoints = self._setup_endpoints()
        
    def _setup_endpoints(self) -> Dict[str, EndpointConfig]:
        """Setup predefined biological SPARQL endpoints."""
        
        return {
            "wikidata": EndpointConfig(
                name="wikidata",
                url="https://query.wikidata.org/sparql",
                timeout=30,
                description="Wikidata knowledge graph with 10+ billion triples",
                default_prefixes="""
                PREFIX wd: <http://www.wikidata.org/entity/>
                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                PREFIX wikibase: <http://wikiba.se/ontology#>
                PREFIX bd: <http://www.bigdata.com/rdf#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX schema: <https://schema.org/>
                """,
                examples=[
                    "SELECT ?protein ?proteinLabel WHERE { ?protein wdt:P31 wd:Q8054 } LIMIT 5",
                    "SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q5 } LIMIT 10"
                ]
            ),
            
            "wikipathways": EndpointConfig(
                name="wikipathways",
                url="https://sparql.wikipathways.org/sparql",
                timeout=30,
                description="WikiPathways - 2300+ biological pathways for 25+ species",
                default_prefixes="""
                PREFIX wp: <http://vocabularies.wikipathways.org/wp#>
                PREFIX dc: <http://purl.org/dc/elements/1.1/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                """,
                examples=[
                    "SELECT ?pathway ?title WHERE { ?pathway a wp:Pathway . ?pathway dc:title ?title } LIMIT 10",
                    "SELECT ?gene ?pathway WHERE { ?gene dcterms:isPartOf ?pathway . ?gene a wp:GeneProduct } LIMIT 10"
                ]
            ),
            
            "uniprot": EndpointConfig(
                name="uniprot",
                url="https://sparql.uniprot.org/sparql",
                timeout=60,  # UniProt queries can be slower
                description="UniProt - 225+ billion triples of protein sequence and function data",
                default_prefixes="""
                PREFIX up: <http://purl.uniprot.org/core/>
                PREFIX taxon: <http://purl.uniprot.org/taxonomy/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                """,
                examples=[
                    "SELECT ?protein ?name WHERE { ?protein a up:Protein . ?protein up:mnemonic ?name } LIMIT 10",
                    "SELECT ?protein ?organism WHERE { ?protein up:organism ?organism . ?protein a up:Protein } LIMIT 10"
                ]
            ),
            
            "idsm": EndpointConfig(
                name="idsm",
                url="https://idsm.elixir-czech.cz/sparql/endpoint/idsm",
                timeout=45,
                description="IDSM - 100+ million chemical compounds from PubChem, ChEBI, ChEMBL",
                default_prefixes="""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                """,
                examples=[
                    "SELECT ?compound ?name WHERE { ?compound rdfs:label ?name . FILTER(CONTAINS(LCASE(?name), 'insulin')) } LIMIT 10"
                ]
            ),
            
            "rhea": EndpointConfig(
                name="rhea",
                url="https://sparql.rhea-db.org/sparql",
                timeout=30,
                description="Rhea - biochemical reactions and enzyme data",
                default_prefixes="""
                PREFIX rh: <http://rdf.rhea-db.org/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                """,
                examples=[
                    "SELECT ?reaction ?equation WHERE { ?reaction rh:equation ?equation } LIMIT 10"
                ]
            )
        }
    
    def add_custom_endpoint(
        self, 
        name: str, 
        url: str, 
        prefixes: str = "", 
        description: str = "",
        timeout: int = 30
    ):
        """Add a custom SPARQL endpoint."""
        self.endpoints[name] = EndpointConfig(
            name=name,
            url=url,
            default_prefixes=prefixes,
            timeout=timeout,
            description=description
        )
        log.info(f"Added custom endpoint: {name} -> {url}")
    
    def get_endpoint_info(self, endpoint: str) -> Optional[EndpointConfig]:
        """Get endpoint configuration information."""
        return self.endpoints.get(endpoint)
    
    def list_endpoints(self) -> Dict[str, str]:
        """List all available endpoints with descriptions."""
        return {
            name: config.description 
            for name, config in self.endpoints.items()
        }
    
    async def sparql_query(
        self, 
        query: str, 
        endpoint: str = "wikidata",
        add_prefixes: bool = True,
        limit: int = None
    ) -> Dict[str, Any]:
        """
        Execute SPARQL query against specified endpoint.
        
        Args:
            query: SPARQL query string
            endpoint: Endpoint name or URL
            add_prefixes: Whether to automatically add default prefixes
            limit: Optional result limit to add if not present
            
        Returns:
            SPARQL results in JSON format
        """
        
        # Handle custom URL endpoints
        if endpoint.startswith("http"):
            config = EndpointConfig(
                name="custom",
                url=endpoint,
                default_prefixes="",
                timeout=self.timeout
            )
        else:
            config = self.endpoints.get(endpoint)
            if not config:
                raise ValueError(f"Unknown endpoint: {endpoint}. Available: {list(self.endpoints.keys())}")
        
        # Add default prefixes if requested and not already present
        final_query = query
        if add_prefixes and config.default_prefixes:
            # Check if any of the default prefixes are missing
            prefixes_needed = []
            for line in config.default_prefixes.strip().split('\n'):
                if line.strip() and line.strip().startswith('PREFIX'):
                    prefix_name = line.split()[1].rstrip(':')
                    if f"{prefix_name}:" not in query:
                        prefixes_needed.append(line.strip())
            
            if prefixes_needed:
                final_query = '\n'.join(prefixes_needed) + '\n\n' + query
        
        # Add LIMIT if not present and limit specified
        if limit and 'LIMIT' not in query.upper():
            final_query = final_query.strip() + f" LIMIT {limit}"
        
        try:
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                headers = {
                    'Accept': 'application/sparql-results+json',
                    'User-Agent': 'CogitareLink/1.0'
                }
                
                log.info(f"Executing SPARQL query on {endpoint}: {query[:100]}...")
                
                # UniProt requires GET requests with query parameters
                if endpoint == "uniprot":
                    params = {'query': final_query, 'format': 'json'}
                    response = await client.get(
                        config.url,
                        params=params,
                        headers=headers
                    )
                else:
                    # Other endpoints use POST
                    response = await client.post(
                        config.url,
                        data={'query': final_query},
                        headers=headers
                    )
                    
                response.raise_for_status()
                result = response.json()
                
                bindings_count = len(result.get('results', {}).get('bindings', []))
                log.info(f"SPARQL query on {endpoint} returned {bindings_count} results")
                
                # Add metadata about the endpoint used
                result['endpoint_info'] = {
                    'name': config.name,
                    'url': config.url,
                    'description': config.description,
                    'query_with_prefixes': final_query
                }
                
                return result
                
        except httpx.TimeoutException:
            log.error(f"SPARQL query timeout on {endpoint} after {config.timeout}s")
            raise
        except httpx.HTTPStatusError as e:
            log.error(f"SPARQL query failed on {endpoint}: HTTP {e.response.status_code}")
            raise
        except Exception as e:
            log.error(f"SPARQL query failed on {endpoint}: {e}")
            raise
    
    def validate_query_for_endpoint(self, query: str, endpoint: str) -> Dict[str, Any]:
        """
        Validate SPARQL query against endpoint vocabulary expectations.
        
        Returns validation result with suggestions.
        """
        config = self.endpoints.get(endpoint)
        if not config:
            return {
                "valid": False,
                "error": f"Unknown endpoint: {endpoint}",
                "suggestions": [f"Available endpoints: {list(self.endpoints.keys())}"]
            }
        
        # Extract expected prefixes from endpoint config
        expected_prefixes = []
        for line in config.default_prefixes.strip().split('\n'):
            if line.strip() and line.strip().startswith('PREFIX'):
                prefix_name = line.split()[1].rstrip(':')
                expected_prefixes.append(f"{prefix_name}:")
        
        # Check for wrong prefixes in query
        import re
        query_prefixes = re.findall(r'(\w+):', query)
        wrong_prefixes = []
        
        for prefix in query_prefixes:
            prefix_with_colon = f"{prefix}:"
            if (prefix_with_colon not in expected_prefixes and 
                prefix.upper() not in ["SELECT", "WHERE", "FILTER", "OPTIONAL", "PREFIX"]):
                wrong_prefixes.append(prefix_with_colon)
        
        if wrong_prefixes:
            return {
                "valid": False,
                "error": f"Query uses wrong vocabulary prefixes for {endpoint}",
                "wrong_prefixes": wrong_prefixes,
                "expected_prefixes": expected_prefixes,
                "suggestions": [
                    f"Use {', '.join(expected_prefixes)} for {endpoint}",
                    f"Check {endpoint} examples for correct patterns",
                    "Consider using a different endpoint for these prefixes"
                ]
            }
        
        # Basic SPARQL syntax validation
        required_keywords = ["SELECT", "WHERE"]
        missing_keywords = [kw for kw in required_keywords if kw not in query.upper()]
        
        if missing_keywords:
            return {
                "valid": False,
                "error": "Query missing required SPARQL keywords",
                "missing_keywords": missing_keywords,
                "suggestions": [
                    "SPARQL queries must contain SELECT and WHERE clauses",
                    "Check query syntax against SPARQL specification"
                ]
            }
        
        return {
            "valid": True,
            "endpoint": endpoint,
            "expected_prefixes": expected_prefixes
        }
    
    def get_endpoint_examples(self, endpoint: str) -> List[str]:
        """Get example queries for an endpoint."""
        config = self.endpoints.get(endpoint)
        if config and config.examples:
            return config.examples
        return []


# Test function
async def test_multi_sparql_client():
    """Test the multi-endpoint SPARQL client."""
    client = MultiSparqlClient()
    
    print("🔍 Testing Multi-Endpoint SPARQL Client...")
    
    # Test endpoint listing
    endpoints = client.list_endpoints()
    print(f"Available endpoints: {list(endpoints.keys())}")
    
    # Test Wikidata query
    try:
        print("\n🧬 Testing Wikidata query...")
        query = "SELECT ?protein ?proteinLabel WHERE { ?protein wdt:P31 wd:Q8054 } LIMIT 3"
        result = await client.sparql_query(query, "wikidata")
        bindings = result.get('results', {}).get('bindings', [])
        print(f"Wikidata returned {len(bindings)} protein results")
        
        if bindings:
            for binding in bindings[:2]:
                protein_uri = binding.get('protein', {}).get('value', '')
                protein_label = binding.get('proteinLabel', {}).get('value', 'No label')
                print(f"  - {protein_label}: {protein_uri}")
    
    except Exception as e:
        print(f"Wikidata test failed: {e}")
    
    # Test query validation
    print("\n🔍 Testing query validation...")
    validation = client.validate_query_for_endpoint(
        "SELECT ?pathway WHERE { ?pathway wdt:P31 wd:Q4915012 }", 
        "wikipathways"
    )
    print(f"Validation result: {validation.get('valid', False)}")
    if not validation.get('valid'):
        print(f"Validation error: {validation.get('error')}")
        print(f"Suggestions: {validation.get('suggestions', [])}")
    
    print("✅ Multi-endpoint SPARQL client test completed!")


if __name__ == "__main__":
    asyncio.run(test_multi_sparql_client())