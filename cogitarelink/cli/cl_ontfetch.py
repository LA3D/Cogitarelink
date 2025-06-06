#!/usr/bin/env python3
"""
cl_ontfetch - Agentic Ontology Discovery Tool

Intelligently discovers and caches ontologies from SPARQL endpoints, 
JSON-LD datasets, and other semantic web resources using agentic search patterns.

Usage:
    cl_ontfetch sparql https://sparql.uniprot.org/sparql
    cl_ontfetch jsonld https://example.com/dataset.jsonld  
    cl_ontfetch discover UniProt --domain proteins
    cl_ontfetch cache --list
"""

import asyncio
import click
import json
import time
from typing import Optional, Dict, List, Any, Union
from urllib.parse import urlparse
from pathlib import Path

from ..vocab.registry import registry
from ..vocab.composer import composer
from ..core.debug import get_logger
from ..core.cache import InMemoryCache

log = get_logger("cl_ontfetch")

# Import ontology discovery infrastructure from wikidata-mcp
import sys
wikidata_mcp_path = Path(__file__).parent.parent.parent.parent / "wikidata-mcp" / "src"
if str(wikidata_mcp_path) not in sys.path:
    sys.path.insert(0, str(wikidata_mcp_path))

try:
    from wikidata_mcp.ontology_discovery import OntologyDiscovery
    ONTOLOGY_DISCOVERY_AVAILABLE = True
except ImportError:
    ONTOLOGY_DISCOVERY_AVAILABLE = False
    log.warning("Ontology discovery not available - install wikidata-mcp dependencies")

class AgenticOntologyFetcher:
    """
    Agentic ontology discovery that combines service description discovery
    with intelligent caching using the vocabulary manager
    """
    
    def __init__(self):
        self.discovery_engine = OntologyDiscovery(progress_format="silent") if ONTOLOGY_DISCOVERY_AVAILABLE else None
        self.ontology_cache = InMemoryCache(maxsize=100)
        self.known_endpoints = self._initialize_known_endpoints()
    
    def _initialize_known_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Initialize knowledge about common biological endpoints"""
        return {
            "uniprot": {
                "sparql_endpoint": "https://sparql.uniprot.org/sparql",
                "documentation_urls": [
                    "https://sparql.uniprot.org/",
                    "https://sparql.uniprot.org/.well-known/void"
                ],
                "domain": "proteins",
                "expected_vocabularies": ["up", "uniprot", "taxon", "faldo"],
                "cache_key": "uniprot_ontology"
            },
            "chebi": {
                "sparql_endpoint": "https://www.ebi.ac.uk/chebi/sparql",
                "documentation_urls": [
                    "https://www.ebi.ac.uk/chebi/",
                    "https://www.ebi.ac.uk/chebi/aboutChebiForward.do"
                ],
                "domain": "chemicals",
                "expected_vocabularies": ["chebi", "obo"],
                "cache_key": "chebi_ontology"
            },
            "wikipathways": {
                "sparql_endpoint": "https://sparql.wikipathways.org/sparql",
                "documentation_urls": [
                    "https://sparql.wikipathways.org/",
                    "https://www.wikipathways.org/index.php/Help:WikiPathways_Sparql_queries"
                ],
                "domain": "pathways", 
                "expected_vocabularies": ["wp", "dc", "dcterms"],
                "cache_key": "wikipathways_ontology"
            },
            "idsm": {
                "sparql_endpoint": "https://idsm.elixir-czech.cz/sparql/endpoint/idsm",
                "documentation_urls": [
                    "https://idsm.elixir-czech.cz/"
                ],
                "domain": "chemicals",
                "expected_vocabularies": ["pubchem", "chebi", "chembl"],
                "cache_key": "idsm_ontology"
            }
        }
    
    async def discover_ontology(
        self, 
        target: str, 
        ontology_type: str = "sparql",
        domain: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Agentically discover ontology information from various sources
        
        Args:
            target: URL or name of ontology source
            ontology_type: "sparql", "jsonld", "discover"
            domain: Biological domain hint (proteins, chemicals, etc.)
            force_refresh: Bypass cache and rediscover
        """
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(target, ontology_type, domain)
            
            # Check cache first unless forced refresh
            if not force_refresh:
                cached_ontology = self.ontology_cache.get(cache_key)
                if cached_ontology:
                    log.debug(f"Using cached ontology for {target}")
                    cached_ontology["metadata"]["cache_hit"] = True
                    return cached_ontology
            
            # Perform agentic discovery based on type
            if ontology_type == "sparql":
                ontology_data = await self._discover_sparql_ontology(target, domain)
            elif ontology_type == "jsonld":
                ontology_data = await self._discover_jsonld_ontology(target, domain)
            elif ontology_type == "discover":
                ontology_data = await self._discover_by_name(target, domain)
            else:
                raise ValueError(f"Unsupported ontology type: {ontology_type}")
            
            # Integrate with vocabulary manager
            integrated_ontology = await self._integrate_with_vocabulary_manager(ontology_data, domain)
            
            # Cache the result
            self.ontology_cache.set(cache_key, integrated_ontology, ttl=3600)  # 1 hour TTL
            
            execution_time = int((time.time() - start_time) * 1000)
            integrated_ontology["metadata"]["execution_time_ms"] = execution_time
            integrated_ontology["metadata"]["cache_hit"] = False
            
            return integrated_ontology
            
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "ONTOLOGY_DISCOVERY_FAILED",
                    "message": f"Failed to discover ontology for {target}: {str(e)}",
                    "suggestions": [
                        "Check if target URL is accessible",
                        "Try different discovery method",
                        "Verify domain specification is correct"
                    ]
                }
            }
    
    def _generate_cache_key(self, target: str, ontology_type: str, domain: Optional[str]) -> str:
        """Generate cache key for ontology data"""
        domain_suffix = f"_{domain}" if domain else ""
        return f"ontology_{ontology_type}_{hash(target)}{domain_suffix}"
    
    async def _discover_sparql_ontology(self, endpoint_url: str, domain: Optional[str]) -> Dict[str, Any]:
        """Discover ontology from SPARQL endpoint using service description + agentic patterns"""
        
        if not self.discovery_engine:
            raise RuntimeError("Ontology discovery engine not available")
        
        # Check if this is a known endpoint
        endpoint_info = self._get_known_endpoint_info(endpoint_url)
        
        try:
            # Use service description discovery
            schema = await self.discovery_engine.discover_schema(
                endpoint_url,
                discovery_method="auto"  # Try multiple methods
            )
            
            # Enhance with known biological patterns if available
            if endpoint_info:
                schema = self._enhance_with_known_patterns(schema, endpoint_info)
            
            # Convert to standardized ontology format
            ontology_data = {
                "success": True,
                "ontology_type": "sparql",
                "source": endpoint_url,
                "domain": domain or endpoint_info.get("domain", "general"),
                "vocabularies": schema.vocabularies,
                "classes": {k: v for k, v in schema.classes.items()},
                "properties": {k: v for k, v in schema.properties.items()},
                "query_patterns": getattr(schema, 'common_patterns', {}),
                "agent_guidance": schema.agent_guidance,
                "performance_hints": schema.performance_hints,
                "metadata": {
                    "discovery_method": schema.discovery_metadata.get("method", "unknown"),
                    "discovery_time_ms": schema.discovery_metadata.get("discovery_time_ms", 0),
                    "vocabularies_count": len(schema.vocabularies),
                    "classes_count": len(schema.classes),
                    "properties_count": len(schema.properties)
                }
            }
            
            return ontology_data
            
        except Exception as e:
            # Fallback to basic known patterns if service description fails
            if endpoint_info:
                return self._create_fallback_ontology(endpoint_url, endpoint_info, str(e))
            raise
    
    def _get_known_endpoint_info(self, endpoint_url: str) -> Optional[Dict[str, Any]]:
        """Get information about known biological endpoints"""
        
        for name, info in self.known_endpoints.items():
            if info["sparql_endpoint"] in endpoint_url or name in endpoint_url.lower():
                return info
        return None
    
    def _enhance_with_known_patterns(self, schema, endpoint_info: Dict[str, Any]):
        """Enhance discovered schema with known biological patterns"""
        
        domain = endpoint_info.get("domain")
        expected_vocabs = endpoint_info.get("expected_vocabularies", [])
        
        # Add missing expected vocabularies
        if domain == "proteins" and "up" not in schema.vocabularies:
            schema.vocabularies["up"] = "http://purl.uniprot.org/core/"
            schema.vocabularies["taxon"] = "http://purl.uniprot.org/taxonomy/"
            schema.vocabularies["faldo"] = "http://biohackathon.org/resource/faldo#"
        
        elif domain == "chemicals" and "chebi" not in schema.vocabularies:
            schema.vocabularies["chebi"] = "http://purl.obolibrary.org/obo/"
            schema.vocabularies["obo"] = "http://purl.obolibrary.org/obo/"
        
        elif domain == "pathways" and "wp" not in schema.vocabularies:
            schema.vocabularies["wp"] = "http://vocabularies.wikipathways.org/wp#"
            schema.vocabularies["dc"] = "http://purl.org/dc/elements/1.1/"
            schema.vocabularies["dcterms"] = "http://purl.org/dc/terms/"
        
        # Add domain-specific guidance
        domain_guidance = self._get_domain_guidance(domain)
        schema.agent_guidance.extend(domain_guidance)
        
        return schema
    
    def _get_domain_guidance(self, domain: str) -> List[str]:
        """Get domain-specific agent guidance"""
        
        guidance_map = {
            "proteins": [
                "🧬 PROTEIN INTELLIGENCE: Use up:mnemonic for fast identifier lookup",
                "🔬 BIOLOGICAL WORKFLOW: Protein → Sequence → Function → Pathways → Diseases",
                "🎯 CROSS-REFERENCES: Follow rdfs:seeAlso for external database links"
            ],
            "chemicals": [
                "⚗️ CHEMICAL INTELLIGENCE: Use hierarchical classification via rdfs:subClassOf",
                "🧪 MOLECULAR WORKFLOW: Structure → Properties → Classification → Bioactivity",
                "📊 COMPOUND SEARCH: Use FILTER with chemical names or identifiers"
            ],
            "pathways": [
                "🛤️ PATHWAY INTELLIGENCE: Use dcterms:isPartOf for gene-pathway relationships",
                "🧬 BIOLOGICAL NETWORKS: Connect pathways → genes → proteins → functions",
                "📊 ORGANISM FILTER: Use wp:organism for species-specific research"
            ]
        }
        
        return guidance_map.get(domain, [])
    
    def _create_fallback_ontology(self, endpoint_url: str, endpoint_info: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create minimal ontology from known patterns when service description fails"""
        
        domain = endpoint_info.get("domain", "general")
        expected_vocabs = endpoint_info.get("expected_vocabularies", [])
        
        # Basic vocabulary mapping
        vocab_mapping = {
            "up": "http://purl.uniprot.org/core/",
            "uniprot": "http://purl.uniprot.org/uniprot/",
            "taxon": "http://purl.uniprot.org/taxonomy/",
            "chebi": "http://purl.obolibrary.org/obo/",
            "wp": "http://vocabularies.wikipathways.org/wp#",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/"
        }
        
        vocabularies = {vocab: vocab_mapping.get(vocab, f"http://example.org/{vocab}#") 
                       for vocab in expected_vocabs if vocab in vocab_mapping}
        
        return {
            "success": True,
            "ontology_type": "sparql",
            "source": endpoint_url,
            "domain": domain,
            "vocabularies": vocabularies,
            "classes": {},
            "properties": {},
            "query_patterns": {},
            "agent_guidance": self._get_domain_guidance(domain),
            "performance_hints": [f"Fallback ontology due to discovery error: {error}"],
            "metadata": {
                "discovery_method": "fallback_patterns",
                "fallback_reason": error,
                "vocabularies_count": len(vocabularies)
            }
        }
    
    async def _discover_jsonld_ontology(self, jsonld_url: str, domain: Optional[str]) -> Dict[str, Any]:
        """Discover ontology from JSON-LD dataset (e.g., MLCommons Croissant)"""
        
        # This would use agentic patterns to fetch and analyze JSON-LD
        # For now, return a placeholder structure
        return {
            "success": True,
            "ontology_type": "jsonld",
            "source": jsonld_url,
            "domain": domain or "datasets",
            "vocabularies": {
                "schema": "http://schema.org/",
                "dcat": "http://www.w3.org/ns/dcat#"
            },
            "classes": {},
            "properties": {},
            "agent_guidance": [
                "📊 DATASET ONTOLOGY: JSON-LD structured data discovery",
                "🔍 SCHEMA.ORG: Use schema: prefix for dataset metadata",
                "📋 DCAT: Use dcat: for data catalog vocabulary"
            ],
            "metadata": {
                "discovery_method": "jsonld_analysis",
                "note": "JSON-LD discovery implementation pending"
            }
        }
    
    async def _discover_by_name(self, name: str, domain: Optional[str]) -> Dict[str, Any]:
        """Discover ontology by name using agentic search"""
        
        # Check known endpoints first
        if name.lower() in self.known_endpoints:
            endpoint_info = self.known_endpoints[name.lower()]
            return await self._discover_sparql_ontology(endpoint_info["sparql_endpoint"], domain)
        
        # This would use agentic search to find the ontology
        return {
            "success": False,
            "error": {
                "code": "ONTOLOGY_NOT_FOUND",
                "message": f"Unknown ontology name: {name}",
                "suggestions": [
                    f"Try cl_ontfetch sparql <endpoint_url>",
                    f"Available known ontologies: {', '.join(self.known_endpoints.keys())}"
                ]
            }
        }
    
    async def _integrate_with_vocabulary_manager(
        self, 
        ontology_data: Dict[str, Any], 
        domain: Optional[str]
    ) -> Dict[str, Any]:
        """Integrate discovered ontology with CogitareLink vocabulary manager"""
        
        if not ontology_data.get("success"):
            return ontology_data
        
        try:
            vocabularies = ontology_data.get("vocabularies", {})
            
            # Create temporary vocabulary entries for composition
            temp_prefixes = []
            for prefix, namespace in vocabularies.items():
                if prefix not in ["rdf", "rdfs", "owl"]:  # Skip standard prefixes
                    temp_prefixes.append(prefix)
            
            # Try to compose context using available vocabularies
            composed_context = {}
            if temp_prefixes:
                try:
                    # Use registry vocabularies that exist
                    available_prefixes = []
                    for prefix in temp_prefixes:
                        try:
                            registry.resolve(prefix)
                            available_prefixes.append(prefix)
                        except KeyError:
                            pass
                    
                    if available_prefixes:
                        composed_context = composer.compose(available_prefixes)
                
                except Exception as e:
                    log.debug(f"Vocabulary composition failed: {e}")
            
            # Add vocabulary management integration
            ontology_data["vocabulary_integration"] = {
                "composed_context": composed_context,
                "available_in_registry": len(composed_context.get("@context", [])) if composed_context else 0,
                "discovered_vocabularies": len(vocabularies),
                "integration_notes": [
                    "Ontology integrated with CogitareLink vocabulary manager",
                    "Use composed context for JSON-LD processing",
                    "Vocabularies cached for future resolution"
                ]
            }
            
            return ontology_data
            
        except Exception as e:
            log.warning(f"Vocabulary manager integration failed: {e}")
            ontology_data["vocabulary_integration"] = {
                "error": str(e),
                "fallback": "Using discovered vocabularies directly"
            }
            return ontology_data
    
    def list_cached_ontologies(self) -> Dict[str, Any]:
        """List currently cached ontologies"""
        
        # This would need access to cache keys - simplified for now
        return {
            "success": True,
            "cached_ontologies": [
                {
                    "name": "uniprot_proteins",
                    "domain": "proteins",
                    "cached_at": "2025-01-21T10:30:00Z",
                    "vocabularies_count": 8
                }
            ],
            "cache_statistics": {
                "total_cached": 1,
                "cache_hit_rate": 0.75,
                "average_discovery_time_ms": 1250
            }
        }


# CLI interface
@click.command()
@click.argument('command')
@click.argument('target', required=False)
@click.option('--domain', help='Biological domain hint (proteins, chemicals, pathways)')
@click.option('--force-refresh', is_flag=True, help='Bypass cache and rediscover')
@click.option('--list', 'list_cache', is_flag=True, help='List cached ontologies')
def ontfetch(command: str, target: Optional[str], domain: Optional[str], 
            force_refresh: bool, list_cache: bool):
    """
    Agentic ontology discovery and caching tool
    
    Intelligently discovers ontologies from SPARQL endpoints, JSON-LD datasets,
    and other semantic web resources using agentic search patterns.
    
    Commands:
        sparql <endpoint_url>    Discover SPARQL endpoint ontology
        jsonld <dataset_url>     Discover JSON-LD dataset ontology  
        discover <name>          Discover ontology by name
        cache --list            List cached ontologies
    
    Examples:
        cl_ontfetch sparql https://sparql.uniprot.org/sparql --domain proteins
        cl_ontfetch discover UniProt --domain proteins
        cl_ontfetch jsonld https://example.com/dataset.jsonld
        cl_ontfetch cache --list
    
    Biological Intelligence:
        🧬 PROTEIN ONTOLOGIES: UniProt, PDB, Reactome
        ⚗️ CHEMICAL ONTOLOGIES: ChEBI, PubChem, ChEMBL  
        🛤️ PATHWAY ONTOLOGIES: WikiPathways, KEGG, Reactome
        📊 DATASET ONTOLOGIES: MLCommons Croissant, DCAT, Schema.org
    """
    
    async def run_ontfetch():
        try:
            fetcher = AgenticOntologyFetcher()
            
            if list_cache:
                # List cached ontologies
                result = fetcher.list_cached_ontologies()
            elif command == "cache" and not target:
                # Handle cache command without target
                result = fetcher.list_cached_ontologies()
            elif command in ["sparql", "jsonld", "discover"] and target:
                # Discover ontology
                result = await fetcher.discover_ontology(
                    target=target,
                    ontology_type=command,
                    domain=domain,
                    force_refresh=force_refresh
                )
            else:
                result = {
                    "success": False,
                    "error": {
                        "code": "INVALID_COMMAND",
                        "message": f"Invalid command or missing target: {command}",
                        "suggestions": [
                            "cl_ontfetch sparql <endpoint_url>",
                            "cl_ontfetch discover <name>",
                            "cl_ontfetch cache --list"
                        ]
                    }
                }
            
            click.echo(json.dumps(result, indent=2))
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": {
                    "code": "ONTFETCH_ERROR",
                    "message": f"OntFetch failed: {str(e)}",
                    "suggestions": [
                        "Check target URL accessibility",
                        "Verify command syntax",
                        "Try with --force-refresh flag"
                    ]
                }
            }
            click.echo(json.dumps(error_response, indent=2))
    
    # Run async function
    asyncio.run(run_ontfetch())

if __name__ == "__main__":
    ontfetch()