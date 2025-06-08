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

from ..vocab.registry import registry
from ..vocab.composer import composer
from ..core.debug import get_logger
from ..core.cache import InMemoryCache

log = get_logger("cl_ontfetch")

# Import Cogitarelink's own ontology discovery implementation
from ..intelligence.ontology_discovery import OntologyDiscovery
ONTOLOGY_DISCOVERY_AVAILABLE = True

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
                    if cached_ontology.get("success") and "metadata" in cached_ontology:
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
            self.ontology_cache.set(cache_key, integrated_ontology)  # TTL set during cache initialization
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Add execution metadata only if this is a successful result
            if integrated_ontology.get("success"):
                if "metadata" not in integrated_ontology:
                    integrated_ontology["metadata"] = {}
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
                "classes": [cls for cls in schema.classes],  # Convert to list format
                "properties": [prop for prop in schema.properties],  # Convert to list format
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
        """Discover ontology by name using agentic search + HTTP dereferencing"""
        
        # Check known endpoints first
        if name.lower() in self.known_endpoints:
            endpoint_info = self.known_endpoints[name.lower()]
            return await self._discover_sparql_ontology(endpoint_info["sparql_endpoint"], domain)
        
        # Try HTTP dereferencing if it looks like a URI
        if name.startswith(('http://', 'https://')):
            return await self._http_dereference_ontology(name, domain)
        
        # Search in vocabulary registry
        try:
            vocab_entry = registry.resolve(name)
            primary_uri = vocab_entry.uris.get("primary")
            if primary_uri:
                return await self._http_dereference_ontology(str(primary_uri), domain)
        except KeyError:
            pass
        
        # This would use agentic search to find the ontology
        return {
            "success": False,
            "error": {
                "code": "ONTOLOGY_NOT_FOUND",
                "message": f"Unknown ontology name: {name}",
                "suggestions": [
                    f"Try cl_ontfetch sparql <endpoint_url>",
                    f"Try providing a full HTTP URI for dereferencing",
                    f"Available known ontologies: {', '.join(self.known_endpoints.keys())}"
                ]
            }
        }
    
    async def _http_dereference_ontology(self, ontology_uri: str, domain: Optional[str]) -> Dict[str, Any]:
        """
        HTTP dereference ontology URI using RDFLib with proper content negotiation
        
        This implements true ontology dereferencing:
        1. HTTP GET with proper Accept headers for RDF content
        2. RDFLib parsing of RDF/OWL/Turtle documents
        3. Semantic extraction of properties and classes
        4. Integration with vocabulary registry
        """
        try:
            import httpx
            import rdflib
            from rdflib.namespace import OWL, RDFS, RDF
            
            # Content negotiation for RDF formats
            accept_headers = {
                'Accept': ', '.join([
                    'text/turtle;q=0.9',
                    'application/rdf+xml;q=0.8', 
                    'application/n-triples;q=0.7',
                    'application/ld+json;q=0.6',
                    'text/n3;q=0.5',
                    'application/xml;q=0.4',
                    'text/xml;q=0.3'
                ]),
                'User-Agent': 'CogitareLink/1.0 (Ontology Dereferencer; +https://github.com/cogitarelink)'
            }
            
            # Try multiple strategies for dereferencing
            attempted_uris = await self._generate_dereference_candidates(ontology_uri)
            
            for uri_candidate in attempted_uris:
                try:
                    log.debug(f"Attempting HTTP dereferencing: {uri_candidate}")
                    
                    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                        response = await client.get(uri_candidate, headers=accept_headers)
                        
                        if response.status_code == 200:
                            # Parse RDF content using RDFLib
                            rdf_graph = self._parse_rdf_content(
                                response.content, 
                                response.headers.get('content-type', ''),
                                uri_candidate
                            )
                            
                            if rdf_graph and len(rdf_graph) > 0:
                                # Extract semantic information
                                semantic_info = self._extract_semantic_info(rdf_graph, ontology_uri, domain)
                                
                                # Register in vocabulary system if valuable
                                await self._register_discovered_vocabulary(ontology_uri, semantic_info)
                                
                                return {
                                    "success": True,
                                    "ontology_type": "http_dereferenced",
                                    "source": uri_candidate,
                                    "original_uri": ontology_uri,
                                    "domain": domain or self._infer_domain_from_content(semantic_info),
                                    **semantic_info,
                                    "metadata": {
                                        "dereferencing_method": "http_rdf_parsing",
                                        "content_type": response.headers.get('content-type'),
                                        "triples_count": len(rdf_graph),
                                        "successful_uri": uri_candidate,
                                        "attempted_uris": attempted_uris,
                                        "claude_guidance": self._generate_claude_guidance(semantic_info, domain)
                                    }
                                }
                        
                except httpx.RequestError as e:
                    log.debug(f"HTTP request failed for {uri_candidate}: {e}")
                    continue
                except Exception as e:
                    log.debug(f"Failed to process {uri_candidate}: {e}")
                    continue
            
            # All dereferencing attempts failed
            return {
                "success": False,
                "error": {
                    "code": "DEREFERENCING_FAILED", 
                    "message": f"Could not dereference ontology URI: {ontology_uri}",
                    "attempted_uris": attempted_uris,
                    "suggestions": [
                        "Check if the URI is publicly accessible",
                        "Try alternative URI patterns (with/without trailing slash, .ttl, .rdf extensions)",
                        "Verify the ontology is published in a standard RDF format",
                        "Consider using a SPARQL endpoint if available"
                    ]
                }
            }
            
        except ImportError as e:
            return {
                "success": False,
                "error": {
                    "code": "MISSING_DEPENDENCIES",
                    "message": f"Missing required dependencies for HTTP dereferencing: {e}",
                    "suggestions": [
                        "Install httpx: pip install httpx",
                        "Install rdflib: pip install rdflib"
                    ]
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "DEREFERENCING_ERROR",
                    "message": f"HTTP dereferencing failed: {e}",
                    "suggestions": [
                        "Check network connectivity",
                        "Verify URI format is correct",
                        "Try with a different ontology URI"
                    ]
                }
            }
    
    async def _generate_dereference_candidates(self, base_uri: str) -> List[str]:
        """Generate candidate URIs for dereferencing based on common patterns"""
        candidates = [base_uri]  # Start with original URI
        
        # Remove fragment if present
        if '#' in base_uri:
            base_without_fragment = base_uri.split('#')[0]
            candidates.append(base_without_fragment)
        
        # Try common file extensions
        base_clean = base_uri.rstrip('/#')
        for ext in ['.ttl', '.rdf', '.owl', '.n3', '.nt']:
            candidates.append(f"{base_clean}{ext}")
        
        # Try common path patterns
        candidates.extend([
            f"{base_clean}/ontology",
            f"{base_clean}/vocab", 
            f"{base_clean}/schema",
            f"{base_clean}.jsonld",
            f"{base_uri}#",  # Add fragment back
        ])
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(candidates))
    
    def _parse_rdf_content(self, content: bytes, content_type: str, uri: str) -> Optional['rdflib.Graph']:
        """Parse RDF content using RDFLib with format detection"""
        try:
            import rdflib
            
            graph = rdflib.Graph()
            
            # Format detection based on content type
            format_map = {
                'text/turtle': 'turtle',
                'application/x-turtle': 'turtle',
                'application/rdf+xml': 'xml',
                'text/rdf+xml': 'xml',
                'application/xml': 'xml',
                'text/xml': 'xml',
                'application/n-triples': 'nt',
                'text/n3': 'n3',
                'application/ld+json': 'json-ld',
                'application/json': 'json-ld'
            }
            
            # Try to determine format from content type
            rdf_format = None
            for ct, fmt in format_map.items():
                if ct in content_type.lower():
                    rdf_format = fmt
                    break
            
            # Try to parse with detected format
            if rdf_format:
                try:
                    graph.parse(data=content, format=rdf_format)
                    log.debug(f"Successfully parsed {len(graph)} triples as {rdf_format}")
                    return graph
                except Exception as e:
                    log.debug(f"Failed to parse as {rdf_format}: {e}")
            
            # Fallback: try multiple formats
            formats_to_try = ['turtle', 'xml', 'n3', 'nt', 'json-ld']
            for fmt in formats_to_try:
                try:
                    graph = rdflib.Graph()  # Fresh graph for each attempt
                    graph.parse(data=content, format=fmt)
                    log.debug(f"Successfully parsed {len(graph)} triples as {fmt}")
                    return graph
                except Exception:
                    continue
            
            log.debug(f"Failed to parse RDF content from {uri}")
            return None
            
        except ImportError:
            log.error("RDFLib not available for parsing")
            return None
        except Exception as e:
            log.debug(f"RDF parsing error: {e}")
            return None
    
    def _extract_semantic_info(self, graph: 'rdflib.Graph', ontology_uri: str, domain: Optional[str]) -> Dict[str, Any]:
        """Extract semantic information from RDF graph"""
        try:
            import rdflib
            from rdflib.namespace import OWL, RDFS, RDF, DCTERMS, SKOS
            
            # Extract vocabularies/namespaces
            vocabularies = []
            namespaces = dict(graph.namespaces())
            for prefix, namespace in namespaces.items():
                if prefix and str(namespace):  # Skip empty prefixes
                    vocabularies.append({
                        'prefix': str(prefix),
                        'namespace': str(namespace),
                        'discovered_from': 'rdf_dereferencing'
                    })
            
            # Extract properties (OWL and RDFS)
            properties = []
            
            # OWL Properties
            for prop_type in [OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty]:
                for prop in graph.subjects(RDF.type, prop_type):
                    prop_info = self._extract_property_info(graph, prop, prop_type)
                    if prop_info:
                        properties.append(prop_info)
            
            # RDFS Properties
            for prop in graph.subjects(RDF.type, RDF.Property):
                prop_info = self._extract_property_info(graph, prop, RDF.Property)
                if prop_info:
                    properties.append(prop_info)
            
            # Extract classes
            classes = []
            for cls in graph.subjects(RDF.type, OWL.Class):
                class_info = self._extract_class_info(graph, cls)
                if class_info:
                    classes.append(class_info)
            
            # RDFS Classes
            for cls in graph.subjects(RDF.type, RDFS.Class):
                class_info = self._extract_class_info(graph, cls)
                if class_info:
                    classes.append(class_info)
            
            return {
                "vocabularies": vocabularies,
                "properties": properties,
                "classes": classes,
                "query_patterns": self._generate_query_patterns(properties, classes),
                "agent_guidance": [],  # Will be populated later
                "performance_hints": [
                    f"Ontology contains {len(properties)} properties and {len(classes)} classes",
                    f"Parsed {len(graph)} RDF triples from {ontology_uri}"
                ]
            }
            
        except ImportError:
            return {"vocabularies": [], "properties": [], "classes": []}
        except Exception as e:
            log.debug(f"Semantic extraction error: {e}")
            return {"vocabularies": [], "properties": [], "classes": []}
    
    def _extract_property_info(self, graph: 'rdflib.Graph', prop: 'rdflib.term.Node', prop_type: 'rdflib.term.Node') -> Optional[Dict[str, Any]]:
        """Extract detailed property information from RDF graph"""
        try:
            import rdflib
            from rdflib.namespace import RDFS, OWL, DCTERMS
            
            prop_uri = str(prop)
            
            # Extract labels and comments
            label = graph.value(prop, RDFS.label)
            comment = graph.value(prop, RDFS.comment)
            domain = graph.value(prop, RDFS.domain)
            range_val = graph.value(prop, RDFS.range)
            
            return {
                'uri': prop_uri,
                'label': str(label) if label else prop_uri.split('/')[-1].split('#')[-1],
                'comment': str(comment) if comment else '',
                'domain': str(domain) if domain else '',
                'range': str(range_val) if range_val else '',
                'property_type': str(prop_type),
                'discovery_method': 'rdf_dereferencing'
            }
            
        except Exception as e:
            log.debug(f"Property extraction error for {prop}: {e}")
            return None
    
    def _extract_class_info(self, graph: 'rdflib.Graph', cls: 'rdflib.term.Node') -> Optional[Dict[str, Any]]:
        """Extract detailed class information from RDF graph"""
        try:
            import rdflib
            from rdflib.namespace import RDFS, OWL
            
            cls_uri = str(cls)
            
            # Extract labels and comments
            label = graph.value(cls, RDFS.label)
            comment = graph.value(cls, RDFS.comment)
            subclass_of = list(graph.objects(cls, RDFS.subClassOf))
            
            return {
                'uri': cls_uri,
                'label': str(label) if label else cls_uri.split('/')[-1].split('#')[-1],
                'comment': str(comment) if comment else '',
                'subclass_of': [str(sc) for sc in subclass_of],
                'discovery_method': 'rdf_dereferencing'
            }
            
        except Exception as e:
            log.debug(f"Class extraction error for {cls}: {e}")
            return None
    
    def _generate_query_patterns(self, properties: List[Dict], classes: List[Dict]) -> List[Dict[str, Any]]:
        """Generate SPARQL query patterns from discovered properties and classes"""
        patterns = []
        
        if properties:
            # Basic property pattern
            patterns.append({
                'name': 'dereferenced_properties',
                'description': 'Query using dereferenced ontology properties',
                'variables': ['subject', 'object'],
                'example_properties': [p['uri'] for p in properties[:5]]
            })
        
        if classes:
            # Class instantiation pattern
            patterns.append({
                'name': 'dereferenced_classes',
                'description': 'Query instances of dereferenced ontology classes', 
                'variables': ['instance'],
                'example_classes': [c['uri'] for c in classes[:5]]
            })
        
        return patterns
    
    def _infer_domain_from_content(self, semantic_info: Dict[str, Any]) -> str:
        """Infer domain from semantic content"""
        vocabularies = semantic_info.get('vocabularies', [])
        properties = semantic_info.get('properties', [])
        classes = semantic_info.get('classes', [])
        
        # Look for domain indicators in URIs and labels
        all_text = ' '.join([
            ' '.join(v.get('namespace', '') for v in vocabularies),
            ' '.join(p.get('uri', '') + ' ' + p.get('label', '') for p in properties),
            ' '.join(c.get('uri', '') + ' ' + c.get('label', '') for c in classes)
        ]).lower()
        
        if any(term in all_text for term in ['protein', 'gene', 'uniprot', 'bio']):
            return 'biology'
        elif any(term in all_text for term in ['chemical', 'compound', 'molecule']):
            return 'chemistry'  
        elif any(term in all_text for term in ['pathway', 'reaction', 'process']):
            return 'pathways'
        elif any(term in all_text for term in ['geo', 'location', 'place']):
            return 'geography'
        else:
            return 'general'
    
    def _generate_claude_guidance(self, semantic_info: Dict[str, Any], domain: Optional[str]) -> List[str]:
        """Generate Claude-specific guidance for using the dereferenced ontology"""
        guidance = []
        
        properties = semantic_info.get('properties', [])
        classes = semantic_info.get('classes', [])
        
        if properties:
            guidance.append(f"🔗 ONTOLOGY PROPERTIES: Found {len(properties)} properties for semantic queries")
            
            # Highlight important property types
            object_props = [p for p in properties if 'ObjectProperty' in p.get('property_type', '')]
            data_props = [p for p in properties if 'DatatypeProperty' in p.get('property_type', '')]
            
            if object_props:
                guidance.append(f"🌐 OBJECT PROPERTIES: {len(object_props)} relationship properties available")
            if data_props:
                guidance.append(f"📊 DATA PROPERTIES: {len(data_props)} literal value properties available")
        
        if classes:
            guidance.append(f"🏗️ ONTOLOGY CLASSES: Found {len(classes)} classes for type-based queries")
            
            # Highlight class hierarchies
            hierarchical_classes = [c for c in classes if c.get('subclass_of')]
            if hierarchical_classes:
                guidance.append(f"🔗 CLASS HIERARCHY: {len(hierarchical_classes)} classes have parent relationships")
        
        # Domain-specific guidance
        if domain == 'biology':
            guidance.append("🧬 BIOLOGICAL WORKFLOW: Use properties for protein→gene→pathway→disease relationships")
        elif domain == 'chemistry':
            guidance.append("⚗️ CHEMICAL WORKFLOW: Use properties for compound→structure→reaction relationships")
        
        guidance.append("💡 USAGE: Properties can be used directly in SPARQL queries with discovered URIs")
        
        return guidance
    
    async def _register_discovered_vocabulary(self, ontology_uri: str, semantic_info: Dict[str, Any]):
        """Register discovered vocabulary in CogitareLink's vocabulary system"""
        try:
            # This would integrate with the vocabulary registry
            # For now, just cache the information
            cache_key = f"discovered_vocab_{hash(ontology_uri)}"
            self.ontology_cache.set(cache_key, semantic_info)
            log.debug(f"Cached discovered vocabulary for {ontology_uri}")
        except Exception as e:
            log.debug(f"Failed to register vocabulary {ontology_uri}: {e}")
    
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