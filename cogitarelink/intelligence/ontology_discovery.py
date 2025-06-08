"""
Ontology Discovery Tool for Informed SPARQL Composition

Re-implementation of the sophisticated ontology discovery from wikidata-mcp
directly in Cogitarelink for independence and integration with core architecture.

This module implements automatic schema discovery for SPARQL endpoints,
enabling intelligent query composition by understanding available vocabularies,
classes, properties, and query patterns.

Discovery Methods:
1. VoID (Vocabulary of Interlinked Datasets) - Standard endpoint metadata
2. SPARQL Introspection - Schema discovery through introspective queries  
3. Documentation Discovery - Leveraging search tools for endpoint docs
4. Sample Analysis - Pattern extraction from endpoint data

The output is optimized for LLM consumption, providing rich context for
intelligent SPARQL query composition.
"""

import asyncio
import json
import time
import httpx
from urllib.parse import urlparse, urlencode
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, field

from ..core.debug import get_logger
from ..core.cache import InMemoryCache

log = get_logger("ontology_discovery")


class ProgressTracker:
    """Progress tracking for long-running ontology discovery operations"""
    
    def __init__(self, output_format: str = "human"):
        self.output_format = output_format  # "human", "json", "silent"
        self.start_time = None
        self.operation_name = None
        self.estimated_duration = None
        
    def start_operation(self, operation_name: str, estimated_duration: Optional[float] = None):
        """Start tracking a long operation"""
        self.start_time = time.time()
        self.operation_name = operation_name
        self.estimated_duration = estimated_duration
        
        if self.output_format == "human":
            print(f"🔄 Starting {operation_name}...")
            if estimated_duration:
                print(f"   Estimated time: ~{estimated_duration:.0f}s")
        elif self.output_format == "json":
            progress = {
                "type": "progress_start",
                "operation": operation_name,
                "estimated_duration": estimated_duration,
                "timestamp": time.time()
            }
            print(json.dumps(progress))
    
    def update_progress(self, step: str, progress: float = None, details: str = None):
        """Update progress during operation"""
        if self.start_time is None:
            return
            
        elapsed = time.time() - self.start_time
        
        if self.output_format == "human":
            progress_str = f" ({progress:.0%})" if progress is not None else ""
            details_str = f" - {details}" if details else ""
            print(f"   ⏳ {step}{progress_str}{details_str} [{elapsed:.1f}s]")
        elif self.output_format == "json":
            progress_obj = {
                "type": "progress_update", 
                "operation": self.operation_name,
                "step": step,
                "progress": progress,
                "details": details,
                "elapsed_time": elapsed,
                "timestamp": time.time()
            }
            print(json.dumps(progress_obj))
    
    def complete_operation(self, result_summary: str = None):
        """Complete the operation"""
        if self.start_time is None:
            return
            
        elapsed = time.time() - self.start_time
        
        if self.output_format == "human":
            result_str = f" - {result_summary}" if result_summary else ""
            print(f"✅ {self.operation_name} completed{result_str} [{elapsed:.1f}s]")
        elif self.output_format == "json":
            progress = {
                "type": "progress_complete",
                "operation": self.operation_name,
                "result_summary": result_summary,
                "total_time": elapsed,
                "timestamp": time.time()
            }
            print(json.dumps(progress))


@dataclass
@dataclass
class EndpointSchema:
    """Schema information for a SPARQL endpoint"""
    endpoint: str
    vocabularies: List[Dict[str, Any]]  # List of vocabulary info
    classes: List[Dict[str, Any]]  # List of class info
    properties: List[Dict[str, Any]]  # List of property info
    query_patterns: List[Dict[str, Any]]  # List of query patterns
    performance_hints: List[str] = None
    agent_guidance: List[str] = None
    discovery_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.performance_hints is None:
            self.performance_hints = []
        if self.agent_guidance is None:
            self.agent_guidance = []
        if self.discovery_metadata is None:
            self.discovery_metadata = {}


class OntologyDiscovery:
    """
    Ontology discovery service for SPARQL endpoints integrated with Cogitarelink.
    
    Supports multiple discovery methods and caches results for performance.
    Designed to work with Cogitarelink's caching and entity systems.
    """
    
    def __init__(self, progress_format: str = "silent"):
        self.cache = InMemoryCache(maxsize=100, ttl=3600)  # Use Cogitarelink's cache
        self.progress_format = progress_format  # "human", "json", "silent"
        
        # Known endpoint configurations  
        self.known_endpoints = {
            "wikidata": "https://query.wikidata.org/sparql",
            "uniprot": "https://sparql.uniprot.org/sparql", 
            "wikipathways": "https://sparql.wikipathways.org/sparql",
            "idsm": "https://idsm.elixir-czech.cz/sparql/endpoint/idsm",
            "rhea": "https://sparql.rhea-db.org/sparql",
            "pubchem": "https://qlever.cs.uni-freiburg.de/api/pubchem"
        }
    
    async def discover_schema(
        self, 
        endpoint: str, 
        discovery_method: str = "auto",
        cache_duration: Optional[int] = None,
        known_entity_id: Optional[str] = None
    ) -> EndpointSchema:
        """
        Discover schema information for a SPARQL endpoint with progress tracking
        
        Args:
            endpoint: SPARQL endpoint URL or known alias
            discovery_method: Discovery strategy (auto, void, introspection, documentation, samples)
            cache_duration: Override default cache duration
            
        Returns:
            EndpointSchema with comprehensive schema information
        """
        # Initialize progress tracker
        tracker = ProgressTracker(self.progress_format)
        tracker.start_operation("Schema Discovery", estimated_duration=60)
        
        # Resolve endpoint alias
        resolved_endpoint = self.known_endpoints.get(endpoint.lower(), endpoint)
        tracker.update_progress("Resolving endpoint", 0.05, f"Using {resolved_endpoint}")
        
        # Check cache
        cache_key = f"schema:{resolved_endpoint}:{discovery_method}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            tracker.complete_operation("Using cached schema")
            return cached
        
        tracker.update_progress("Cache miss, starting discovery", 0.1, f"Method: {discovery_method}")
        
        # Discover schema using specified method
        start_time = time.time()
        
        try:
            if discovery_method == "auto":
                schema = await self._discover_auto(resolved_endpoint, tracker, known_entity_id)
            elif discovery_method == "service_description":
                schema = await self._discover_service_description(resolved_endpoint)
            elif discovery_method == "void":
                schema = await self._discover_void_with_progress(resolved_endpoint, tracker)
            elif discovery_method == "introspection":
                schema = await self._discover_introspection_with_progress(resolved_endpoint, tracker)
            elif discovery_method == "documentation":
                schema = await self._discover_documentation_with_progress(resolved_endpoint, tracker)
            elif discovery_method == "samples":
                schema = await self._discover_samples_with_progress(resolved_endpoint, tracker)
            else:
                raise ValueError(f"Unknown discovery method: {discovery_method}")
            
            # Enhancement step: Ontology dereferencing (non-blocking)
            tracker.update_progress("Enhancement: Ontology dereferencing", 0.9, "Enriching schema with dereferenced ontologies")
            enhanced_schema = await self._enhance_with_ontology_dereferencing(schema)
            
            # Add discovery metadata
            tracker.update_progress("Adding metadata", 0.95, "Finalizing schema")
            enhanced_schema.discovery_metadata.update({
                "discovery_time_ms": int((time.time() - start_time) * 1000),
                "discovery_method": discovery_method,
                "cached_until": time.time() + (cache_duration or 3600)
            })
            
            # Cache result
            self.cache.set(cache_key, enhanced_schema)
            
            # Complete progress tracking
            vocab_count = len(enhanced_schema.vocabularies)
            class_count = len(enhanced_schema.classes)
            prop_count = len(enhanced_schema.properties)
            tracker.complete_operation(f"Found {vocab_count} vocabularies, {class_count} classes, {prop_count} properties")
            
            return enhanced_schema
            
        except Exception as e:
            elapsed = time.time() - start_time
            if self.progress_format == "human":
                print(f"❌ Schema discovery failed: {str(e)} [{elapsed:.1f}s]")
                print(f"   💡 Suggestion: Try a different discovery method or check endpoint accessibility")
            elif self.progress_format == "json":
                error_obj = {
                    "type": "progress_error",
                    "operation": "Schema Discovery",
                    "error": str(e),
                    "elapsed_time": elapsed,
                    "suggestions": ["Try different discovery method", "Check endpoint accessibility"]
                }
                print(json.dumps(error_obj))
            raise
    
    async def _discover_auto(self, endpoint: str, tracker: Optional[ProgressTracker] = None, known_entity_id: Optional[str] = None) -> EndpointSchema:
        """Semantic hierarchy discovery: authoritative semantics → entity affordances → statistical fallback"""
        
        # Step 1: Service Description/VoID Discovery (Authoritative Semantics)
        if tracker:
            tracker.update_progress("Phase 1: Authoritative semantics discovery", 0.1, "Service Description + VoID")
        
        try:
            # First try specialized endpoint discovery for known patterns
            if "qlever.cs.uni-freiburg.de/api/osm" in endpoint or "osm-planet" in endpoint:
                if tracker:
                    tracker.update_progress("Using specialized OSM QLever discovery", 0.15, "Enhanced spatial intelligence patterns")
                schema = await self._discover_osm_qlever_specialized(endpoint)
                if self._is_schema_sufficient(schema):
                    schema.discovery_metadata["primary_method"] = "osm_qlever_specialized"
                    if tracker:
                        tracker.update_progress("Success with specialized OSM discovery", 0.9, "CoT patterns loaded")
                    return schema
            
            # Check for other known endpoints
            if tracker:
                tracker.update_progress("Checking known endpoint patterns", 0.2, "Looking for pre-configured schemas")
            known_schema = self._create_known_endpoint_schema(endpoint)
            if known_schema.discovery_metadata.get("method") == "known_patterns":
                if tracker:
                    tracker.update_progress("Success with known patterns", 0.9, "Schema from knowledge base")
                return known_schema
            
            # Try Service Description (W3C SPARQL 1.1 standard)
            if tracker:
                tracker.update_progress("Trying Service Description", 0.25, "W3C SPARQL 1.1 standard metadata")
            schema = await self._discover_service_description(endpoint)
            if self._is_schema_sufficient(schema):
                schema.discovery_metadata["primary_method"] = "service_description"
                if tracker:
                    tracker.update_progress("Success with Service Description", 0.9, "Authoritative semantics discovered")
                return schema
            
            # Try VoID (Vocabulary of Interlinked Datasets)
            if tracker:
                tracker.update_progress("Trying VoID discovery", 0.3, "Looking for dataset descriptions")
            schema = await self._discover_void(endpoint)
            if self._is_schema_sufficient(schema):
                schema.discovery_metadata["primary_method"] = "void"
                if tracker:
                    tracker.update_progress("Success with VoID", 0.9, "Dataset semantics discovered")
                return schema
                
        except Exception as e:
            if tracker:
                tracker.update_progress("Authoritative discovery failed", 0.35, f"Error: {str(e)[:50]}...")
        
        # Step 2: Entity Availability Check → Branching Structure
        if tracker:
            tracker.update_progress("Phase 2: Entity availability check", 0.4, "Determining discovery pathway")
        
        # Branch A: Entity-Known Discovery Pathway
        if known_entity_id:
            try:
                if tracker:
                    tracker.update_progress("Branch A: Entity-Known Discovery", 0.45, f"Using entity: {known_entity_id}")
                schema = await self._discover_entity_known_pathway(endpoint, known_entity_id, tracker)
                if self._is_schema_sufficient(schema):
                    schema.discovery_metadata["primary_method"] = "entity_known_pathway"
                    schema.discovery_metadata["known_entity"] = known_entity_id
                    if tracker:
                        tracker.update_progress("Success with Entity-Known pathway", 0.9, "Entity affordances discovered")
                    return schema
            except Exception as e:
                if tracker:
                    tracker.update_progress("Entity-Known pathway failed", 0.5, f"Error: {str(e)[:50]}...")
        
        # Branch B: Property Affordance Discovery Pathway
        try:
            if tracker:
                tracker.update_progress("Branch B: Property Affordance Discovery", 0.55, "Exploring endpoint capabilities")
            schema = await self._discover_property_affordance_pathway(endpoint, tracker)
            if self._is_schema_sufficient(schema):
                schema.discovery_metadata["primary_method"] = "property_affordance_pathway"
                if tracker:
                    tracker.update_progress("Success with Property Affordance pathway", 0.9, "Endpoint capabilities discovered")
                return schema
        except Exception as e:
            if tracker:
                tracker.update_progress("Property Affordance pathway failed", 0.65, f"Error: {str(e)[:50]}...")
        
        # Step 3: Statistical Fallback (Last Resort)
        if tracker:
            tracker.update_progress("Phase 3: Statistical fallback", 0.7, "Last resort methods")
        
        statistical_methods = ["introspection", "documentation", "samples"]
        last_error = None
        
        for i, method in enumerate(statistical_methods):
            progress = 0.75 + (i * 0.05)  # Progress from 0.75 to 0.85
            if tracker:
                tracker.update_progress(f"Trying {method} discovery", progress, f"Statistical method {i+1}/{len(statistical_methods)}")
            
            try:
                schema = await getattr(self, f"_discover_{method}")(endpoint)
                if self._is_schema_sufficient(schema):
                    schema.discovery_metadata["primary_method"] = method
                    schema.discovery_metadata["fallback_level"] = "statistical"
                    if tracker:
                        tracker.update_progress(f"Success with {method}", 0.9, f"Statistical discovery succeeded")
                    return schema
            except Exception as e:
                last_error = e
                if tracker:
                    tracker.update_progress(f"{method} failed", progress + 0.02, f"Error: {str(e)[:50]}...")
                continue
        
        # If all methods fail, create minimal schema
        if tracker:
            tracker.update_progress("All methods failed, creating minimal schema", 0.85, "Fallback mode")
        if last_error:
            return self._create_minimal_schema(endpoint, str(last_error))
        
        return self._create_minimal_schema(endpoint, "All discovery methods failed")
    
    # Progress-aware discovery method fallbacks
    async def _discover_void_with_progress(self, endpoint: str, tracker: ProgressTracker) -> EndpointSchema:
        """VoID discovery with progress tracking"""
        tracker.update_progress("Checking VoID locations", 0.3, "Looking for VoID descriptions")
        return await self._discover_void(endpoint)
    
    async def _discover_introspection_with_progress(self, endpoint: str, tracker: ProgressTracker) -> EndpointSchema:
        """Introspection discovery with progress tracking"""
        tracker.update_progress("Executing introspection queries", 0.5, "Analyzing endpoint schema")
        return await self._discover_introspection(endpoint)
    
    async def _discover_documentation_with_progress(self, endpoint: str, tracker: ProgressTracker) -> EndpointSchema:
        """Documentation discovery with progress tracking"""
        tracker.update_progress("Fetching endpoint documentation", 0.4, "Searching for schema docs")
        return await self._discover_documentation(endpoint)
    
    async def _discover_samples_with_progress(self, endpoint: str, tracker: ProgressTracker) -> EndpointSchema:
        """Sample-based discovery with progress tracking"""
        tracker.update_progress("Analyzing sample data", 0.6, "Extracting patterns from samples")
        return await self._discover_samples(endpoint)
    
    async def _discover_entity_known_pathway(self, endpoint: str, known_entity_id: str, tracker: Optional[ProgressTracker] = None) -> EndpointSchema:
        """
        Entity-Known Discovery Pathway: External ID → DESCRIBE entity → Extract affordances
        
        When we have a known entity (e.g., from external identifier discovery),
        use DESCRIBE queries to understand what this specific entity type can do.
        
        Args:
            endpoint: SPARQL endpoint URL
            known_entity_id: Known entity identifier (URI or external ID)
            tracker: Progress tracking
            
        Returns:
            EndpointSchema with entity-specific affordances
        """
        try:
            if tracker:
                tracker.update_progress("Converting entity ID to URI", 0.1, f"Processing: {known_entity_id}")
            
            # Convert external ID to entity URI if needed
            entity_uri = await self._resolve_entity_uri(endpoint, known_entity_id)
            
            if tracker:
                tracker.update_progress("DESCRIBE entity for affordances", 0.3, f"URI: {entity_uri}")
            
            # DESCRIBE the entity to understand its affordances
            describe_query = f"DESCRIBE <{entity_uri}>"
            describe_results = await self._execute_sparql(endpoint, describe_query)
            
            if tracker:
                tracker.update_progress("Extracting affordances from DESCRIBE", 0.6, f"Processing {len(describe_results.get('results', {}).get('bindings', []))} triples")
            
            # Extract affordances (properties, types, relationships)
            affordances = self._extract_entity_affordances(describe_results, entity_uri)
            
            if tracker:
                tracker.update_progress("Building patterns from affordances", 0.8, f"Found {len(affordances.get('properties', []))} properties")
            
            # Build schema based on discovered affordances
            schema = self._build_schema_from_affordances(endpoint, entity_uri, affordances)
            
            # Add discovery metadata
            schema.discovery_metadata.update({
                "method": "entity_known_pathway",
                "known_entity": known_entity_id,
                "entity_uri": entity_uri,
                "affordances_discovered": len(affordances.get('properties', [])),
                "semantic_approach": True
            })
            
            if tracker:
                tracker.update_progress("Entity-Known pathway complete", 0.9, f"Schema built from entity affordances")
            
            return schema
            
        except Exception as e:
            # Create minimal schema with error information
            if tracker:
                tracker.update_progress("Entity-Known pathway failed", 0.5, f"Error: {str(e)[:50]}")
            return self._create_minimal_schema(endpoint, f"Entity-Known discovery failed: {str(e)}")
    
    async def _discover_property_affordance_pathway(self, endpoint: str, tracker: Optional[ProgressTracker] = None) -> EndpointSchema:
        """
        Property Affordance Discovery Pathway: Progressive ontology → usage → statistical approach
        
        When we don't have known entities to anchor discovery, explore endpoint capabilities
        using a progressive approach that adapts to endpoint ontology support.
        
        Args:
            endpoint: SPARQL endpoint URL
            tracker: Progress tracking
            
        Returns:
            EndpointSchema with discovered capabilities
        """
        try:
            if tracker:
                tracker.update_progress("Phase 1: Ontology introspection", 0.1, "Looking for explicit property declarations")
            
            # Phase 1: Try ontology introspection (OWL/RDFS property declarations)
            ontology_properties = await self._discover_ontology_properties(endpoint)
            
            if ontology_properties:
                if tracker:
                    tracker.update_progress("Success with ontology introspection", 0.8, f"Found {len(ontology_properties)} declared properties")
                
                schema = await self._build_schema_from_ontology_properties(endpoint, ontology_properties)
                schema.discovery_metadata.update({
                    "method": "property_affordance_pathway",
                    "approach": "ontology_introspection", 
                    "properties_discovered": len(ontology_properties),
                    "semantic_approach": True
                })
                return schema
            
            if tracker:
                tracker.update_progress("Phase 2: Usage-based discovery", 0.3, "Ontology introspection failed, trying usage analysis")
            
            # Phase 2: Usage-based property discovery (brute force)
            usage_properties = await self._discover_usage_properties(endpoint)
            
            if usage_properties:
                if tracker:
                    tracker.update_progress("Success with usage-based discovery", 0.8, f"Found {len(usage_properties)} used properties")
                
                schema = await self._build_schema_from_usage_properties(endpoint, usage_properties)
                schema.discovery_metadata.update({
                    "method": "property_affordance_pathway",
                    "approach": "usage_based",
                    "properties_discovered": len(usage_properties),
                    "semantic_approach": True
                })
                return schema
            
            if tracker:
                tracker.update_progress("Phase 3: Statistical fallback", 0.6, "Usage discovery failed, using statistical analysis")
            
            # Phase 3: Statistical fallback (property frequency analysis)
            return await self.discover_properties_first(endpoint, progress_format="silent")
            
        except Exception as e:
            # Final fallback to statistical property discovery
            if tracker:
                tracker.update_progress("All phases failed, statistical fallback", 0.7, f"Error: {str(e)[:50]}")
            
            try:
                return await self.discover_properties_first(endpoint, progress_format="silent")
            except:
                # Create minimal schema if everything fails
                return self._create_minimal_schema(endpoint, f"Property affordance discovery failed: {str(e)}")
    
    async def _discover_service_description(self, endpoint: str) -> EndpointSchema:
        """Discover schema through SPARQL 1.1 Service Description (W3C standard)"""
        
        try:
            # Request service description from SPARQL endpoint per W3C spec
            headers = {
                'User-Agent': 'Cogitarelink/1.0 (SPARQL Service Description Discovery)',
                'Accept': 'text/turtle, application/rdf+xml, application/n-triples'
            }
            
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                response = await client.get(endpoint, headers=headers)
                
                if response.status_code == 200:
                    service_desc_content = response.text
                    return self._parse_service_description(endpoint, service_desc_content)
                else:
                    raise Exception(f"Service description request failed: HTTP {response.status_code}")
                    
        except Exception as e:
            raise Exception(f"Service description discovery failed: {str(e)}")

    async def _discover_void(self, endpoint: str) -> EndpointSchema:
        """Discover schema through VoID (Vocabulary of Interlinked Datasets) descriptions"""
        
        # Common VoID locations
        base_url = endpoint.replace("/sparql", "").replace("/query", "")
        void_locations = [
            f"{base_url}/.well-known/void",
            f"{base_url}/void.ttl",
            f"{base_url}/void",
            f"{endpoint}/.well-known/void",
            f"{endpoint}/void.ttl"
        ]
        
        for void_url in void_locations:
            try:
                # Attempt to fetch VoID description
                headers = {
                    'User-Agent': 'Cogitarelink/1.0 (SPARQL Schema Discovery)',
                    'Accept': 'text/turtle, application/rdf+xml, application/n-triples, text/html, */*'
                }
                
                async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                    response = await client.get(void_url, headers=headers)
                    
                    if response.status_code == 200:
                        void_content = response.text
                        return await self._parse_void_content(endpoint, void_content)
                        
            except Exception:
                continue
        
        raise Exception("No VoID description found")
    
    async def _discover_introspection(self, endpoint: str) -> EndpointSchema:
        """Discover schema through introspective SPARQL queries"""
        
        introspection_queries = {
            "classes": """
                SELECT DISTINCT ?class (COUNT(?instance) as ?count) WHERE {
                    ?instance a ?class .
                } GROUP BY ?class ORDER BY DESC(?count) LIMIT 20
            """,
            
            "properties": """
                SELECT DISTINCT ?property (COUNT(?usage) as ?count) WHERE {
                    ?s ?property ?o .
                } GROUP BY ?property ORDER BY DESC(?count) LIMIT 50
            """,
            
            "vocabularies": """
                SELECT DISTINCT ?prefix WHERE {
                    ?s ?p ?o .
                    BIND(REPLACE(STR(?p), "(#|/)[^#/]*$", "") AS ?prefix)
                } GROUP BY ?prefix ORDER BY ?prefix LIMIT 20
            """,
            
            "sample_data": """
                SELECT ?s ?p ?o WHERE {
                    ?s ?p ?o .
                } LIMIT 100
            """
        }
        
        results = {}
        for query_name, query in introspection_queries.items():
            try:
                result = await self._execute_sparql(endpoint, query)
                results[query_name] = result
            except Exception as e:
                results[query_name] = {"error": str(e)}
        
        return self._analyze_introspection_results(endpoint, results)
    
    async def _discover_documentation(self, endpoint: str) -> EndpointSchema:
        """Discover schema through web search and documentation analysis"""
        
        # Extract domain and service name for search
        parsed = urlparse(endpoint)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        service_name = self._extract_service_name(endpoint)
        
        # Comprehensive documentation search strategy - execute sequentially
        try:
            # Direct documentation patterns
            schema = await self._try_direct_documentation_urls(base_domain)
            if self._is_schema_sufficient(schema):
                return schema
        except Exception:
            pass
            
        try:
            # Web search for ontology/vocabulary documentation  
            schema = await self._web_search_for_documentation(service_name, base_domain)
            if self._is_schema_sufficient(schema):
                return schema
        except Exception:
            pass
            
        try:
            # Known endpoint patterns
            schema = self._create_known_endpoint_schema(endpoint)
            if self._is_schema_sufficient(schema):
                return schema
        except Exception:
            pass
        
        # Fallback to known patterns
        return self._create_known_endpoint_schema(endpoint)
    
    async def _discover_samples(self, endpoint: str) -> EndpointSchema:
        """Discover schema by analyzing sample data patterns"""
        
        # Check if this is OSM QLever endpoint - use specialized discovery
        if "qlever.cs.uni-freiburg.de/osm-planet" in endpoint:
            return await self._discover_osm_qlever_specialized(endpoint)
        
        sample_queries = [
            "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 100",
            "SELECT DISTINCT ?type WHERE { ?s a ?type } LIMIT 20", 
            "SELECT DISTINCT ?pred WHERE { ?s ?pred ?o } LIMIT 30"
        ]
        
        samples = []
        for query in sample_queries:
            try:
                result = await self._execute_sparql(endpoint, query)
                samples.append(result)
            except Exception:
                continue
        
        return self._analyze_sample_patterns(endpoint, samples)
    
    async def _discover_osm_qlever_specialized(self, endpoint: str) -> EndpointSchema:
        """Specialized discovery for OSM QLever endpoint using known patterns from examples"""
        
        # Use actual OSM QLever vocabulary patterns from real examples
        osm_vocabularies = {
            "geo": "http://www.opengis.net/ont/geosparql#",
            "ogc": "http://www.opengis.net/rdf#", 
            "osm": "https://www.openstreetmap.org/",
            "osmkey": "https://www.openstreetmap.org/wiki/Key:",
            "osmrel": "https://www.openstreetmap.org/relation/",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "wd": "http://www.wikidata.org/entity/",
            "wdt": "http://www.wikidata.org/prop/direct/"
        }
        
        # OSM-specific classes and properties from actual examples
        osm_classes = {
            "osm:relation": "OpenStreetMap relation object",
            "geo:Geometry": "Geographic geometry object"
        }
        
        osm_properties = {
            "geo:hasGeometry": "Links object to its geometric representation",
            "geo:asWKT": "Well-Known Text representation of geometry",
            "ogc:sfContains": "Spatial contains relationship",
            "osm:wikidata": "Link to corresponding Wikidata entity",
            "osmkey:name": "Name of the geographic feature",
            "osmkey:amenity": "Amenity type (e.g., post_box)",
            "osmkey:building": "Building type information",
            "osmkey:waterway": "Waterway type (e.g., river)"
        }
        
        # Enhanced Spatial Intelligence Chain of Thinking guidance
        osm_guidance = [
            "🗺️ SPATIAL REASONING: Think spatially - What contains what? What's nearby? What are the boundaries?",
            "🏗️ CONTAINMENT HIERARCHY: Start with spatial containers (relations), then find contained objects",
            "📍 PROGRESSIVE COMPLEXITY: Begin with simple queries, then add spatial containment, geometry extraction",
            "🔗 CROSS-DOMAIN INTEGRATION: Follow osm:wikidata links for encyclopedic enrichment",
            "🎯 SPATIAL WORKFLOW: (1) Identify container → (2) Query contents → (3) Extract geometry → (4) Follow links",
            "🧠 SPATIAL PATTERNS: Use ogc:sfContains for containment, geo:hasGeometry for coordinates",
            "📊 FEATURE DISCOVERY: Search by osmkey:name, osmkey:building, osmkey:amenity for classification",
            "🌐 KNOWLEDGE INTEGRATION: Combine OSM spatial data with Wikidata semantic information",
            "⚡ CRITICAL HEURISTIC: Always use osmrel:RELATION_ID as spatial anchor before filtering by name",
            "🚨 PERFORMANCE RULE: Simple queries work, complex OPTIONAL clauses cause 30s+ timeouts",
            "🎯 RELATION DISCOVERY: Use name-based search as primary method (osm:wikidata links often missing)",
            "🔄 ERROR RECOVERY: If timeout → Remove OPTIONAL clauses → Use progressive building",
            "📍 KNOWN RELATIONS: Notre Dame=16066037, use as examples for spatial container patterns"
        ]
        
        # Spatial Intelligence Query Patterns - Enhanced with Performance Heuristics
        osm_patterns = {
            "basic_spatial_discovery": """
                # Level 1: Basic Discovery - Explore available features
                PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
                SELECT ?feature ?name WHERE {
                    ?feature osmkey:name ?name .
                } LIMIT 10
            """,
            
            "relation_discovery": """
                # CRITICAL: Find spatial containers (relation IDs) for target area
                # Strategy: Search for university/campus relations first
                PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
                PREFIX osm: <https://www.openstreetmap.org/>
                SELECT ?relation ?name ?wikidata WHERE {
                    ?relation a osm:relation .
                    ?relation osmkey:name ?name .
                    OPTIONAL { ?relation osm:wikidata ?wikidata }
                    FILTER(CONTAINS(LCASE(?name), "TARGET_INSTITUTION"))
                } LIMIT 5
            """,
            
            "optimized_building_search": """
                # PROVEN PATTERN: Successful Flanner Hall discovery method
                # Use known relation ID + spatial containment + text filter
                PREFIX osmrel: <https://www.openstreetmap.org/relation/>
                PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
                PREFIX ogc: <http://www.opengis.net/rdf#>
                SELECT ?building ?name WHERE {
                    osmrel:RELATION_ID ogc:sfContains ?building .
                    ?building osmkey:name ?name .
                    FILTER(CONTAINS(LCASE(?name), "BUILDING_NAME"))
                } LIMIT 5
            """
        }
        
        performance_hints = [
            "🚀 SPATIAL PERFORMANCE: Use specific osmrel: relations instead of global searches",
            "📐 GEOMETRIC OPTIMIZATION: Add LIMIT clauses for initial spatial exploration", 
            "🎯 CONTAINMENT FIRST: Identify spatial boundaries before querying contents",
            "🌐 FEDERATED ENRICHMENT: Use Wikidata SERVICE for cross-domain context",
            "📊 PROGRESSIVE QUERYING: Start simple, add complexity gradually",
            "🔍 VOCABULARY HINTS: OSM identifiers: way/XXXXXX, node/XXXXXX, relation/XXXXXX",
            "⚠️ TIMEOUT PREVENTION: Complex OPTIONAL clauses cause 30+ second timeouts - avoid them",
            "🎯 RELATION ID STRATEGY: Find osmrel:XXXXXX first, then use as spatial anchor",
            "🔄 ERROR RECOVERY PATTERN: Timeout → Remove OPTIONAL → Use direct properties only",
            "📍 CROSS-DOMAIN REALITY: osm:wikidata links often missing, use federated SERVICE queries",
            "⚡ PROVEN PATTERN: osmrel:ID + ogc:sfContains + FILTER(name) = fastest building search",
            "🚨 CRITICAL: Never use global text search without spatial containment anchor"
        ]
        
        return EndpointSchema(
            endpoint=endpoint,
            vocabularies=osm_vocabularies,
            classes=osm_classes,
            properties=osm_properties,
            agent_guidance=osm_guidance,
            common_patterns=osm_patterns,
            performance_hints=performance_hints,
            discovery_metadata={
                "method": "osm_qlever_specialized",
                "discovery_time_ms": 50,  # Fast specialized discovery
                "patterns_count": len(osm_patterns),
                "specialized_endpoint": True,
                "software2_adaptation": "Adapted to OSM QLever using real examples"
            }
        )
    
    async def _execute_sparql(self, endpoint: str, query: str) -> dict:
        """Execute SPARQL query against endpoint with proper endpoint resolution"""
        
        # Resolve endpoint alias to full URL
        resolved_endpoint = self.known_endpoints.get(endpoint.lower(), endpoint)
        
        encoded_query = urlencode({
            'query': query,
            'format': 'json'
        })
        
        headers = {
            'User-Agent': 'Cogitarelink/1.0 (Schema Introspection)',
            'Accept': 'application/sparql-results+json, application/json'
        }
        
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(
                f"{resolved_endpoint}?{encoded_query}",
                headers=headers
            )
            
            if response.status_code == 200:
                # Add content-type validation before JSON parsing
                content_type = response.headers.get('content-type', '').lower()
                if ('application/json' in content_type or 
                    'sparql-results+json' in content_type):
                    return response.json()
                elif ('sparql-results+xml' in content_type or 
                      'application/sparql-results+xml' in content_type):
                    # Try to parse as JSON anyway - some endpoints return wrong content-type
                    try:
                        return response.json()
                    except:
                        raise Exception(f"SPARQL query returned XML format which is not supported: {content_type}")
                else:
                    raise Exception(f"SPARQL query returned unsupported content-type: {content_type}")
            else:
                raise Exception(f"SPARQL query failed: HTTP {response.status_code}")
    
    async def _parse_void_content(self, endpoint: str, void_content: str) -> EndpointSchema:
        """Parse VoID RDF content using RDFLib with fallback to regex"""
        
        vocabularies = {}
        classes = {}
        properties = {}
        performance_hints = []
        agent_guidance = []
        total_triples = 0
        
        # First attempt: Parse as RDF using RDFLib
        try:
            import rdflib
            from rdflib.namespace import VOID, RDF, RDFS
            
            # Try to parse as RDF (Turtle, RDF/XML, N-Triples)
            g = rdflib.Graph()
            
            # Try different RDF formats
            formats_to_try = ['turtle', 'xml', 'n3', 'nt', 'json-ld']
            parsed = False
            
            for fmt in formats_to_try:
                try:
                    g.parse(data=void_content, format=fmt)
                    parsed = True
                    log.info(f"Successfully parsed VoID as {fmt}")
                    break
                except Exception:
                    continue
            
            if parsed:
                # Extract vocabularies from RDFLib's namespace manager (includes built-ins + document prefixes)
                for prefix, namespace in g.namespace_manager.namespaces():
                    if prefix and str(namespace):
                        vocabularies[str(prefix)] = str(namespace)
                
                # Enhance with missing scientific prefixes from prefixes.cc
                missing_prefixes = await self._get_missing_scientific_prefixes(vocabularies)
                vocabularies.update(missing_prefixes)
                
                # Extract triple counts using SPARQL on the VoID graph
                triple_query = """
                    SELECT ?dataset ?triples WHERE {
                        ?dataset void:triples ?triples .
                    }
                """
                
                try:
                    for row in g.query(triple_query):
                        triples = int(row[1])  # row.triples -> row[1]
                        total_triples = max(total_triples, triples)
                except Exception as e:
                    log.debug(f"Could not extract triple counts from VoID: {e}")
                
                # Extract classes and their counts
                class_query = """
                    SELECT ?class ?instances WHERE {
                        ?partition void:class ?class .
                        ?partition void:entities ?instances .
                    }
                """
                
                try:
                    for row in g.query(class_query):
                        class_uri = str(row[0])  # row.class -> row[0] (avoid keyword)
                        instances = int(row[1]) if row[1] else 0  # row.instances -> row[1]
                        classes[class_uri] = {
                            "usage_count": instances,
                            "description": f"Class with {instances} instances"
                        }
                except Exception as e:
                    log.debug(f"Could not extract class information from VoID: {e}")
                
                # Extract properties and their counts
                property_query = """
                    SELECT ?property ?triples WHERE {
                        ?partition void:property ?property .
                        ?partition void:triples ?triples .
                    }
                """
                
                try:
                    for row in g.query(property_query):
                        prop_uri = str(row[0])  # row.property -> row[0]
                        triples = int(row[1]) if row[1] else 0  # row.triples -> row[1]
                        properties[prop_uri] = {
                            "usage_count": triples,
                            "description": f"Property with {triples} usages"
                        }
                except Exception as e:
                    log.debug(f"Could not extract property information from VoID: {e}")
                
                agent_guidance.append("✅ RDF parsing successful - comprehensive VoID schema extracted")
                
            else:
                raise Exception("Could not parse as RDF - falling back to regex")
                
        except Exception as e:
            log.debug(f"RDF parsing failed ({e}), falling back to regex patterns")
            
            # Fallback: Use improved regex patterns for HTML/text content
            import re
            
            # Extract dataset size information
            triple_patterns = [
                r'void:triples\s+(\d+)',
                r'"triples":\s*(\d+)',
                r'Triples:\s*(\d+)',
                r'Total.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:billion|million|thousand)?.*?triples',
                r'Total triples:\s*(\d{1,3}(?:,\d{3})*)',  # HTML format
                r'(\d{1,3}(?:,\d{3})*)\s*</td>',  # HTML table cells with numbers
                r'(\d{9,})',  # Large numbers (likely triple counts)
            ]
            
            for pattern in triple_patterns:
                matches = re.findall(pattern, void_content, re.IGNORECASE)
                if matches:
                    try:
                        # Extract largest number found
                        numbers = [int(m.replace(',', '')) for m in matches if m.replace(',', '').isdigit()]
                        if numbers:
                            total_triples = max(total_triples, max(numbers))
                    except ValueError:
                        continue
            
            # Look for vocabulary/namespace declarations (including HTML links)
            namespace_patterns = [
                r'@prefix\s+(\w+):\s+<([^>]+)>',
                r'xmlns:(\w+)="([^"]+)"',
                r'PREFIX\s+(\w+):\s+<([^>]+)>',
                r'href="([^"]*purl\.uniprot\.org[^"]*)"',  # UniProt namespace links
                r'href="([^"]*www\.w3\.org[^"]*)"',  # W3C standard namespaces
            ]
            
            for pattern in namespace_patterns:
                matches = re.findall(pattern, void_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) == 2:
                        prefix, uri = match
                        if prefix and uri and not prefix.startswith('_'):
                            vocabularies[prefix] = uri
                    elif isinstance(match, str) and match.startswith('http'):
                        # Extract prefix from URI for single-group patterns
                        if 'purl.uniprot.org' in match:
                            vocabularies['up'] = 'http://purl.uniprot.org/core/'
                        elif 'w3.org' in match and 'rdf-schema' in match:
                            vocabularies['rdfs'] = 'http://www.w3.org/2000/01/rdf-schema#'
                        elif 'w3.org' in match and 'rdf-syntax' in match:
                            vocabularies['rdf'] = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
            
            agent_guidance.append("⚠️ RDF parsing failed - using regex fallback (limited capabilities)")
        
        # Register discovered vocabularies with the vocabulary system
        try:
            from ..vocab.registry import registry
            
            for prefix, uri in vocabularies.items():
                try:
                    # Create a dynamic vocabulary entry
                    from ..vocab.registry import VocabEntry, ContextBlock, Versions
                    
                    # Check if this vocabulary is already registered
                    try:
                        existing = registry.resolve(prefix)
                        log.debug(f"Vocabulary {prefix} already registered, skipping")
                        continue
                    except KeyError:
                        pass
                    
                    # Register new vocabulary
                    vocab_entry = VocabEntry(
                        prefix=prefix,
                        uris={"primary": uri},
                        context=ContextBlock(inline={"@context": {prefix: uri}}),
                        versions=Versions(current="discovered", supported=["discovered"]),
                        features={"discovered_from_void"},
                        tags={"void_discovery", "sparql_endpoint"}
                    )
                    
                    # Add to registry (note: registry._v is internal but needed for dynamic addition)
                    registry._v[prefix] = vocab_entry
                    registry._alias[registry._norm(uri)] = prefix
                    
                    log.debug(f"Registered vocabulary {prefix} → {uri}")
                    
                except Exception as e:
                    log.debug(f"Could not register vocabulary {prefix}: {e}")
                    
        except Exception as e:
            log.debug(f"Vocabulary registration failed: {e}")
            agent_guidance.append("⚠️ Could not register vocabularies with vocab system")
        
        # Generate performance hints based on dataset size
        if total_triples > 100_000_000_000:  # 100+ billion
            performance_hints.extend([
                f"⚠️ MASSIVE ENDPOINT: {total_triples:,} triples - NEVER scan without constraints!",
                "CRITICAL: Always use specific IDs, types, or narrow searches",
                "Unconstrained queries will timeout - add strong filters",
                "Use LIMIT 10-100 for exploration, no exceptions"
            ])
        elif total_triples > 1_000_000_000:  # 1+ billion
            performance_hints.extend([
                f"⚠️ LARGE ENDPOINT: {total_triples:,} triples - use constraints",
                "Add type filters and LIMIT clauses",
                "Avoid broad text searches"
            ])
        elif total_triples > 0:
            performance_hints.append(f"📊 DATASET SIZE: {total_triples:,} triples")
        
        # Generate agent guidance based on discovered vocabularies
        if vocabularies:
            common_prefixes = list(vocabularies.keys())[:5]
            agent_guidance.extend([
                f"🔍 VOCABULARIES DISCOVERED: {', '.join(common_prefixes)}",
                "Use discovered prefixes for query construction",
                "Schema-aware queries perform better than generic patterns"
            ])
        
        # Add VoID-specific guidance
        agent_guidance.extend([
            "✅ VoID discovery successful - authoritative schema information",
            "Use discovered classes and properties for optimal queries",
            "Performance hints based on actual dataset characteristics"
        ])
        
        return EndpointSchema(
            endpoint=endpoint,
            vocabularies=vocabularies,
            classes=classes, 
            properties=properties,
            common_patterns={},
            performance_hints=performance_hints,
            agent_guidance=agent_guidance,
            discovery_metadata={
                "method": "void", 
                "source": "void_description",
                "total_triples": total_triples,
                "vocabularies_found": len(vocabularies)
            }
        )
    
    def _parse_service_description(self, endpoint: str, service_desc_content: str) -> EndpointSchema:
        """Parse SPARQL 1.1 Service Description using basic parsing"""
        
        vocabularies = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}
        classes = {}
        properties = {}
        
        # Try to extract at least the triple count with regex as fallback
        import re
        total_triples = 0
        
        triple_patterns = [
            r'void:triples\s+"(\d+)"',
            r'(\d{9,})',  # Large numbers
        ]
        
        for pattern in triple_patterns:
            matches = re.findall(pattern, service_desc_content)
            for match in matches:
                try:
                    count = int(match.replace(',', ''))
                    total_triples = max(total_triples, count)
                except ValueError:
                    continue
        
        return EndpointSchema(
            endpoint=endpoint,
            vocabularies=vocabularies,
            classes=classes,
            properties=properties,
            common_patterns={},
            performance_hints=[f"📊 DATASET SIZE: {total_triples:,} triples" if total_triples > 0 else "Service description parsing limited"],
            agent_guidance=["Service description parsing - consider full RDF parsing for complete capabilities"],
            discovery_metadata={
                "method": "service_description",
                "source": "basic_parsing", 
                "total_triples": total_triples,
                "vocabularies_found": len(vocabularies)
            }
        )
    
    def _analyze_introspection_results(self, endpoint: str, results: dict) -> EndpointSchema:
        """Analyze introspection query results to build schema"""
        
        vocabularies = {}
        classes = {}
        properties = {}
        
        # Process vocabulary results
        if "vocabularies" in results and "results" in results["vocabularies"]:
            for binding in results["vocabularies"]["results"]["bindings"]:
                prefix_uri = binding.get("prefix", {}).get("value", "")
                if prefix_uri:
                    # Extract potential prefix
                    prefix = prefix_uri.split("/")[-1] or prefix_uri.split("#")[0].split("/")[-1]
                    vocabularies[prefix] = prefix_uri
        
        # Process class results  
        if "classes" in results and "results" in results["classes"]:
            for binding in results["classes"]["results"]["bindings"]:
                class_uri = binding.get("class", {}).get("value", "")
                count = binding.get("count", {}).get("value", "0")
                if class_uri:
                    classes[class_uri] = {
                        "usage_count": int(count),
                        "description": f"Class with {count} instances"
                    }
        
        # Process property results
        if "properties" in results and "results" in results["properties"]:
            for binding in results["properties"]["results"]["bindings"]:
                prop_uri = binding.get("property", {}).get("value", "")
                count = binding.get("count", {}).get("value", "0")
                if prop_uri:
                    properties[prop_uri] = {
                        "usage_count": int(count),
                        "description": f"Property with {count} usages"
                    }
        
        return EndpointSchema(
            endpoint=endpoint,
            vocabularies=vocabularies,
            classes=classes,
            properties=properties,
            common_patterns=self._generate_common_patterns(vocabularies, classes, properties),
            performance_hints=[
                "Use discovered high-usage classes and properties for efficient queries",
                "Add LIMIT clauses to prevent timeouts",
                "Filter early in query execution for better performance"
            ],
            agent_guidance=[
                "Start queries with most common classes and properties",
                "Use vocabulary prefixes for readable query construction", 
                "Combine introspection data with sample queries for validation"
            ],
            discovery_metadata={"method": "introspection", "queries_executed": len(results)}
        )
    
    def _create_known_endpoint_schema(self, endpoint: str) -> EndpointSchema:
        """Create schema for known endpoints with pre-defined patterns"""
        
        # Wikidata schema
        if "wikidata" in endpoint:
            return EndpointSchema(
                endpoint=endpoint,
                vocabularies={
                    "wd": "http://www.wikidata.org/entity/",
                    "wdt": "http://www.wikidata.org/prop/direct/",
                    "p": "http://www.wikidata.org/prop/",
                    "ps": "http://www.wikidata.org/prop/statement/",
                    "pq": "http://www.wikidata.org/prop/qualifier/",
                    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
                },
                classes={
                    "Q5": {"description": "human", "usage_count": 1000000},
                    "Q8054": {"description": "protein", "usage_count": 50000},
                    "Q11173": {"description": "chemical compound", "usage_count": 100000}
                },
                properties={
                    "P31": {"description": "instance of", "usage_count": 50000000},
                    "P352": {"description": "UniProt protein ID", "usage_count": 45000},
                    "P683": {"description": "ChEBI ID", "usage_count": 25000}
                },
                common_patterns={
                    "entity_search": "SELECT ?item ?itemLabel WHERE { ?item rdfs:label ?label . FILTER(CONTAINS(?label, '{search_term}')) SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' } }",
                    "instance_query": "SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:{class_id} . SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' } }"
                },
                performance_hints=[
                    "⚠️ ENDPOINT SIZE: ~10+ billion triples - always use specific constraints!",
                    "Always use SERVICE wikibase:label for human-readable labels",
                    "Use LIMIT to prevent timeouts (recommended: 10-1000)",
                    "Filter early with wdt: properties for better performance",
                    "NEVER use SELECT ?s ?p ?o without type/property constraints"
                ],
                agent_guidance=[
                    "Start entity discovery with rdfs:label or wdt:P31 (instance of)",
                    "Use P352 (UniProt), P683 (ChEBI), P662 (PubChem) for biological cross-references",
                    "Always include SERVICE wikibase:label for readable results"
                ],
                discovery_metadata={"method": "known_patterns", "source": "wikidata_knowledge_base"}
            )
        
        # UniProt schema
        elif "uniprot" in endpoint:
            return EndpointSchema(
                endpoint=endpoint,
                vocabularies={
                    "up": "http://purl.uniprot.org/core/",
                    "taxon": "http://purl.uniprot.org/taxonomy/",
                    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                    "skos": "http://www.w3.org/2004/02/skos/core#",
                    "xsd": "http://www.w3.org/2001/XMLSchema#"
                },
                classes={
                    "up:Protein": {"description": "UniProt protein entry", "usage_count": 220000000},
                    "up:Enzyme": {"description": "Enzyme classification", "usage_count": 10000000},
                    "taxon:Taxon": {"description": "Taxonomic classification", "usage_count": 2000000}
                },
                properties={
                    "up:mnemonic": {"description": "Protein mnemonic identifier", "usage_count": 220000000},
                    "up:sequence": {"description": "Protein sequence", "usage_count": 220000000},
                    "rdfs:label": {"description": "Human-readable label", "usage_count": 300000000}
                },
                common_patterns={
                    "protein_search": "SELECT ?protein ?label WHERE { ?protein a up:Protein . ?protein rdfs:label ?label . FILTER(CONTAINS(LCASE(?label), '{search_term}')) } LIMIT 10",
                    "enzyme_search": "SELECT ?protein ?enzyme WHERE { ?protein a up:Protein . ?protein up:enzyme ?enzyme } LIMIT 10"
                },
                performance_hints=[
                    "⚠️ ENDPOINT SIZE: ~100+ billion triples - always use specific constraints!",
                    "Always add LIMIT clauses (recommended: 10-100)",
                    "Use up:mnemonic or specific protein IDs for targeted queries",
                    "Text searches on rdfs:label are indexed but use sparingly",
                    "NEVER use SELECT ?s ?p ?o without type/property constraints"
                ],
                agent_guidance=[
                    "Start protein discovery with up:Protein and rdfs:label",
                    "Use up:mnemonic for specific protein identification",
                    "Connect to pathways and diseases via cross-references"
                ],
                discovery_metadata={"method": "known_patterns", "source": "uniprot_knowledge_base"}
            )
        
        # WikiPathways schema
        elif "wikipathways" in endpoint:
            return EndpointSchema(
                endpoint=endpoint,
                vocabularies={
                    "wp": "http://vocabularies.wikipathways.org/wp#",
                    "dcterms": "http://purl.org/dc/terms/",
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "foaf": "http://xmlns.com/foaf/0.1/"
                },
                classes={
                    "wp:Pathway": {"description": "Biological pathway", "usage_count": 2300},
                    "wp:GeneProduct": {"description": "Gene or protein in pathway", "usage_count": 45000}
                },
                properties={
                    "dc:title": {"description": "Pathway title", "usage_count": 2300},
                    "dcterms:isPartOf": {"description": "Part of pathway relationship", "usage_count": 45000},
                    "wp:organism": {"description": "Organism taxonomy", "usage_count": 2300}
                },
                common_patterns={
                    "pathway_search": "SELECT ?pathway ?title WHERE { ?pathway a wp:Pathway . ?pathway dc:title ?title . FILTER(CONTAINS(LCASE(?title), '{search_term}')) }",
                    "gene_in_pathway": "SELECT ?gene ?pathway WHERE { ?gene a wp:GeneProduct . ?gene dcterms:isPartOf ?pathway . ?gene rdfs:label ?label . FILTER(CONTAINS(LCASE(?label), '{gene_name}')) }"
                },
                performance_hints=[
                    "Use wp:organism filter for species-specific queries",
                    "Text searches on dc:title and rdfs:label are indexed",
                    "Limit results to avoid timeout (default: 1000)"
                ],
                agent_guidance=[
                    "Start pathway discovery with wp:Pathway and dc:title",
                    "Connect genes to pathways via dcterms:isPartOf",
                    "Use wp:organism for cross-species analysis"
                ],
                discovery_metadata={"method": "known_patterns", "source": "wikipathways_knowledge_base"}
            )
        
        # Default minimal schema
        return self._create_minimal_schema(endpoint, "Unknown endpoint")
    
    def _create_minimal_schema(self, endpoint: str, reason: str) -> EndpointSchema:
        """Create minimal schema when discovery fails"""
        
        return EndpointSchema(
            endpoint=endpoint,
            vocabularies={
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "owl": "http://www.w3.org/2002/07/owl#"
            },
            classes={},
            properties={},
            common_patterns={
                "basic_query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
                "explore_classes": "SELECT DISTINCT ?class WHERE { ?s a ?class } LIMIT 10",
                "explore_properties": "SELECT DISTINCT ?property WHERE { ?s ?property ?o } LIMIT 20"
            },
            performance_hints=[
                "Use LIMIT clauses to prevent timeouts",
                "Start with simple queries to explore schema", 
                "Try introspective queries to discover structure"
            ],
            agent_guidance=[
                "Schema discovery failed - use basic RDF patterns",
                "Try sample queries to understand endpoint structure",
                "Use introspective queries to discover available classes and properties"
            ],
            discovery_metadata={"method": "minimal", "reason": reason}
        )
    
    def _generate_common_patterns(self, vocabularies: dict, classes: dict, properties: dict) -> dict:
        """Generate common SPARQL patterns based on discovered schema"""
        
        patterns = {}
        
        # Basic exploration patterns
        if classes:
            top_class = max(classes.items(), key=lambda x: x[1].get("usage_count", 0))
            patterns["explore_top_class"] = f"SELECT ?item WHERE {{ ?item a <{top_class[0]}> }} LIMIT 10"
        
        if properties:
            top_property = max(properties.items(), key=lambda x: x[1].get("usage_count", 0))
            patterns["explore_top_property"] = f"SELECT ?s ?o WHERE {{ ?s <{top_property[0]}> ?o }} LIMIT 10"
        
        return patterns
    
    async def _get_missing_scientific_prefixes(self, existing_vocabularies: dict) -> dict:
        """Get common scientific prefixes from prefixes.cc that are missing from current vocabularies"""
        
        missing_prefixes = {}
        
        # Common scientific/biological prefixes we want to ensure are available
        desired_scientific_prefixes = [
            'up', 'uniprot', 'faldo', 'go', 'chebi', 'pubmed', 'doi', 'orcid',
            'ncbitaxon', 'mesh', 'reactome', 'kegg', 'ensembl', 'pfam'
        ]
        
        try:
            # Check which desired prefixes are missing
            missing = [p for p in desired_scientific_prefixes if p not in existing_vocabularies]
            
            if missing:
                # Fetch from prefixes.cc
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get('https://prefix.cc/context.jsonld')
                    
                    if response.status_code == 200:
                        data = response.json()
                        context = data.get('@context', {})
                        
                        # Add missing scientific prefixes
                        for prefix in missing:
                            if prefix in context:
                                missing_prefixes[prefix] = context[prefix]
                                log.debug(f"Added scientific prefix from prefixes.cc: {prefix} → {context[prefix]}")
                        
                        log.info(f"Enhanced vocabularies with {len(missing_prefixes)} scientific prefixes from prefixes.cc")
                    else:
                        log.debug(f"Could not fetch prefixes.cc: HTTP {response.status_code}")
                        
        except Exception as e:
            log.debug(f"Could not enhance with prefixes.cc: {e}")
        
        return missing_prefixes
    
    def _is_schema_sufficient(self, schema: EndpointSchema) -> bool:
        """Check if discovered schema has sufficient information"""
        return (
            len(schema.vocabularies) > 0 and 
            (len(schema.classes) > 0 or len(schema.properties) > 0)
        )
    
    def _extract_service_name(self, endpoint: str) -> str:
        """Extract service name from endpoint URL for search queries"""
        parsed = urlparse(endpoint)
        
        # Common patterns to extract service names
        if "wikidata" in endpoint:
            return "wikidata"
        elif "wikipathways" in endpoint:
            return "wikipathways"
        elif "uniprot" in endpoint:
            return "uniprot"
        elif "idsm" in endpoint:
            return "idsm"
        elif "rhea" in endpoint:
            return "rhea"
        else:
            # Extract from domain
            domain_parts = parsed.netloc.split('.')
            return domain_parts[0] if domain_parts else "sparql_endpoint"
    
    async def _try_direct_documentation_urls(self, base_domain: str) -> EndpointSchema:
        """Try common documentation URL patterns"""
        doc_patterns = [
            f"{base_domain}/documentation",
            f"{base_domain}/docs", 
            f"{base_domain}/ontology",
            f"{base_domain}/vocabulary",
            f"{base_domain}/schema",
            f"{base_domain}/api/docs",
            f"{base_domain}/sparql/docs"
        ]
        
        for doc_url in doc_patterns:
            try:
                headers = {
                    'User-Agent': 'Cogitarelink/1.0 (Documentation Search)',
                    'Accept': 'text/html, application/xhtml+xml, text/turtle, application/rdf+xml'
                }
                
                async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                    response = await client.get(doc_url, headers=headers)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        doc_content = response.text
                        
                        if 'html' in content_type:
                            return await self._parse_html_documentation(doc_url, doc_content)
                        elif any(rdf_type in content_type for rdf_type in ['turtle', 'rdf+xml', 'n-triples']):
                            return await self._parse_rdf_documentation(doc_url, doc_content)
                        
            except Exception:
                continue
        
        raise Exception("No direct documentation found")
    
    async def _web_search_for_documentation(self, service_name: str, base_domain: str) -> EndpointSchema:
        """Use web search to find documentation"""
        
        # For now, implement intelligent URL guessing based on search patterns
        discovered_urls = []
        
        # WikiPathways specific search patterns
        if service_name == "wikipathways":
            potential_urls = [
                "https://vocabularies.wikipathways.org/wp",
                "https://www.wikipathways.org/index.php/Help:WikiPathways_Sparql_queries",
                "https://github.com/wikipathways/vocabularies", 
                "https://vocabularies.wikipathways.org/wp.owl"
            ]
            discovered_urls.extend(potential_urls)
        
        # UniProt specific patterns
        elif service_name == "uniprot":
            potential_urls = [
                "https://sparql.uniprot.org/",
                "https://www.uniprot.org/help/api_queries",
                "https://ftp.uniprot.org/pub/databases/uniprot/current_release/rdf/",
                "https://www.uniprot.org/help/sparql"
            ]
            discovered_urls.extend(potential_urls)
        
        # Try to fetch and analyze discovered URLs
        for url in discovered_urls:
            try:
                schema = await self._fetch_and_analyze_documentation(url, service_name)
                if self._is_schema_sufficient(schema):
                    return schema
            except Exception:
                continue
        
        raise Exception(f"No documentation found via web search for {service_name}")
    
    async def _fetch_and_analyze_documentation(self, url: str, service_name: str) -> EndpointSchema:
        """Fetch and analyze documentation from discovered URLs"""
        
        headers = {
            'User-Agent': 'Cogitarelink/1.0 (Documentation Analysis)',
            'Accept': 'text/html, application/xhtml+xml, text/turtle, application/rdf+xml, application/owl+xml'
        }
        
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    content = response.text
                    
                    if any(rdf_type in content_type for rdf_type in ['turtle', 'rdf+xml', 'owl+xml']):
                        # Parse RDF/OWL directly
                        return await self._parse_rdf_ontology(url, content, service_name)
                    elif 'html' in content_type:
                        # Parse HTML documentation and extract schema info
                        return await self._parse_html_documentation(url, content, service_name)
                    
        except Exception as e:
            raise Exception(f"Failed to fetch {url}: {str(e)}")
        
        raise Exception(f"No usable content found at {url}")
    
    async def _parse_html_documentation(self, url: str, html_content: str, service_name: str = "") -> EndpointSchema:
        """Parse HTML documentation to extract vocabulary and schema information"""
        
        vocabularies = {}
        classes = {}
        properties = {}
        patterns = {}
        
        # Extract vocabulary URLs and prefixes from HTML
        import re
        
        # Find vocabulary/namespace declarations
        namespace_patterns = [
            r'@prefix\s+(\w+):\s+<([^>]+)>',  # Turtle prefixes
            r'PREFIX\s+(\w+):\s+<([^>]+)>',   # SPARQL prefixes  
            r'xmlns:(\w+)="([^"]+)"',         # XML namespaces
            r'Namespace:\s*([^\s]+)',         # Documentation namespace declarations
        ]
        
        for pattern in namespace_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for prefix, namespace in matches:
                vocabularies[prefix] = namespace
        
        # Service-specific enhancements
        if service_name == "wikipathways":
            # Add known WikiPathways vocabulary if found
            if not vocabularies.get("wp"):
                vocabularies["wp"] = "http://vocabularies.wikipathways.org/wp#"
            if not vocabularies.get("dcterms"):
                vocabularies["dcterms"] = "http://purl.org/dc/terms/"
        elif service_name == "uniprot" or "uniprot" in url.lower():
            # Add known UniProt vocabularies for HTML VoID content
            if not vocabularies.get("up"):
                vocabularies["up"] = "http://purl.uniprot.org/core/"
            if not vocabularies.get("taxon"):
                vocabularies["taxon"] = "http://purl.uniprot.org/taxonomy/"
            if not vocabularies.get("rdfs"):
                vocabularies["rdfs"] = "http://www.w3.org/2000/01/rdf-schema#"
            if not vocabularies.get("skos"):
                vocabularies["skos"] = "http://www.w3.org/2004/02/skos/core#"
            if not vocabularies.get("xsd"):
                vocabularies["xsd"] = "http://www.w3.org/2001/XMLSchema#"
        
        return EndpointSchema(
            endpoint=f"schema_from_{service_name}_documentation",
            vocabularies=vocabularies,
            classes=classes,
            properties=properties,
            common_patterns=patterns,
            performance_hints=[
                "Schema extracted from HTML documentation",
                "May require validation against actual endpoint",
                "Check documentation for query examples and best practices"
            ],
            agent_guidance=[
                "Use discovered vocabularies for query construction",
                "Validate schema elements against live endpoint",
                "Refer to documentation for additional context and examples"
            ],
            discovery_metadata={
                "method": "html_documentation",
                "source_url": url,
                "vocabularies_found": len(vocabularies)
            }
        )
    
    async def _parse_rdf_ontology(self, url: str, rdf_content: str, service_name: str) -> EndpointSchema:
        """Parse RDF/OWL ontology files to extract comprehensive schema information"""
        
        vocabularies = {}
        classes = {}
        properties = {}
        
        import re
        
        # Extract namespace declarations
        namespace_patterns = [
            r'@prefix\s+(\w+):\s+<([^>]+)>',
            r'xmlns:(\w+)="([^"]+)"'
        ]
        
        for pattern in namespace_patterns:
            matches = re.findall(pattern, rdf_content)
            for prefix, namespace in matches:
                vocabularies[prefix] = namespace
        
        # Extract OWL classes
        class_pattern = r'<owl:Class[^>]*rdf:about="([^"]+)"[^>]*>'
        class_matches = re.findall(class_pattern, rdf_content)
        for class_uri in class_matches:
            classes[class_uri] = {
                "description": "OWL Class from ontology",
                "type": "owl:Class"
            }
        
        # Extract properties
        property_patterns = [
            r'<owl:ObjectProperty[^>]*rdf:about="([^"]+)"[^>]*>',
            r'<owl:DatatypeProperty[^>]*rdf:about="([^"]+)"[^>]*>'
        ]
        
        for pattern in property_patterns:
            prop_matches = re.findall(pattern, rdf_content)
            for prop_uri in prop_matches:
                properties[prop_uri] = {
                    "description": "OWL Property from ontology",
                    "type": "owl:Property"
                }
        
        return EndpointSchema(
            endpoint=f"schema_from_{service_name}_ontology",
            vocabularies=vocabularies,
            classes=classes,
            properties=properties,
            common_patterns={},
            performance_hints=[
                "Schema extracted from OWL/RDF ontology",
                "Authoritative vocabulary definitions",
                "Use for precise query construction"
            ],
            agent_guidance=[
                "High-quality schema from formal ontology",
                "Use class and property URIs for precise queries",
                "Combine with endpoint introspection for usage patterns"
            ],
            discovery_metadata={
                "method": "rdf_ontology", 
                "source_url": url,
                "ontology_type": "owl"
            }
        )
    
    async def _parse_rdf_documentation(self, url: str, rdf_content: str) -> EndpointSchema:
        """Parse RDF documentation content"""
        return await self._parse_rdf_ontology(url, rdf_content, "documentation")
    
    def _analyze_sample_patterns(self, endpoint: str, samples: list) -> EndpointSchema:
        """Analyze sample data to build schema"""
        
        vocabularies = {}
        classes = {}
        properties = {}
        
        # Basic analysis of sample data
        for sample in samples:
            if "results" in sample and "bindings" in sample["results"]:
                for binding in sample["results"]["bindings"]:
                    for var, value in binding.items():
                        if value.get("type") == "uri":
                            uri = value.get("value", "")
                            if "#" in uri:
                                namespace, term = uri.rsplit("#", 1)
                                vocabularies[term.lower()] = namespace + "#"
                            elif "/" in uri:
                                namespace, term = uri.rsplit("/", 1)
                                vocabularies[term.lower()] = namespace + "/"
        
        return EndpointSchema(
            endpoint=endpoint,
            vocabularies=vocabularies,
            classes=classes,
            properties=properties,
            common_patterns={},
            performance_hints=["Schema based on sample data analysis"],
            agent_guidance=["Use discovered patterns as starting points for exploration"],
            discovery_metadata={"method": "sample_analysis", "samples_analyzed": len(samples)}
        )
    
    async def discover_external_identifier_patterns(
        self, 
        endpoint: str, 
        external_id: str, 
        id_property: str = None,
        progress_format: str = "silent"
    ) -> Dict[str, Any]:
        """
        Discover URI patterns for external identifiers in SPARQL endpoints.
        
        This implements the discovery state machine from the experimental workflow:
        1. External Identifier Anchor - Use known external ID (e.g. P01308)
        2. URI Pattern Discovery - Find how the endpoint constructs URIs
        3. Property Enumeration - Discover available properties
        4. Schema Validation - Test basic patterns work
        5. Query Construction - Build informed queries
        
        Args:
            endpoint: SPARQL endpoint URL or name
            external_id: External identifier (e.g. "P01308", "CHEBI:15551")
            id_property: Optional hint about the identifier type (e.g. "uniprot", "chebi")
            progress_format: Progress tracking format
            
        Returns:
            Discovery results with URI patterns, properties, and query templates
        """
        # Initialize progress tracker
        tracker = ProgressTracker(progress_format)
        tracker.start_operation("External Identifier Pattern Discovery", estimated_duration=30)
        
        # Resolve endpoint alias
        resolved_endpoint = self.known_endpoints.get(endpoint.lower(), endpoint)
        tracker.update_progress("Resolving endpoint", 0.05, f"Using {resolved_endpoint}")
        
        discovery_results = {
            "endpoint": resolved_endpoint,
            "external_id": external_id,
            "id_property": id_property,
            "uri_patterns": [],
            "properties": [],
            "validated_patterns": [],
            "query_templates": {},
            "discovery_metadata": {
                "method": "external_identifier_pattern_discovery",
                "discovery_steps": []
            }
        }
        
        try:
            # Step 1: External Identifier Anchor
            tracker.update_progress("Step 1: External identifier anchor", 0.1, f"Anchoring on {external_id}")
            anchor_step = await self._discover_external_id_anchor(resolved_endpoint, external_id, id_property)
            discovery_results["uri_patterns"] = anchor_step["uri_patterns"]
            discovery_results["discovery_metadata"]["discovery_steps"].append(anchor_step)
            
            if not anchor_step["uri_patterns"]:
                raise Exception(f"No URI patterns found for external ID {external_id}")
            
            # Step 2: URI Pattern Discovery  
            tracker.update_progress("Step 2: URI pattern analysis", 0.3, f"Found {len(anchor_step['uri_patterns'])} patterns")
            pattern_step = await self._analyze_uri_patterns(resolved_endpoint, anchor_step["uri_patterns"])
            discovery_results["validated_patterns"] = pattern_step["validated_patterns"]
            discovery_results["discovery_metadata"]["discovery_steps"].append(pattern_step)
            
            # Step 3: Property Enumeration
            tracker.update_progress("Step 3: Property enumeration", 0.5, "Discovering available properties")
            if discovery_results["validated_patterns"]:
                best_pattern = discovery_results["validated_patterns"][0]
                prop_step = await self._enumerate_entity_properties(resolved_endpoint, best_pattern["example_uri"])
                discovery_results["properties"] = prop_step["properties"]
                discovery_results["discovery_metadata"]["discovery_steps"].append(prop_step)
                
                # Step 4: Schema Validation
                tracker.update_progress("Step 4: Schema validation", 0.7, "Testing query patterns")
                validation_step = await self._validate_discovery_patterns(
                    resolved_endpoint, 
                    best_pattern["example_uri"], 
                    prop_step["properties"][:5]  # Test top 5 properties
                )
                discovery_results["discovery_metadata"]["discovery_steps"].append(validation_step)
                
                # Step 5: Query Construction
                tracker.update_progress("Step 5: Query template generation", 0.9, "Building query templates")
                template_step = self._generate_query_templates(
                    best_pattern, 
                    prop_step["properties"], 
                    external_id
                )
                discovery_results["query_templates"] = template_step["templates"]
                discovery_results["discovery_metadata"]["discovery_steps"].append(template_step)
            
            tracker.complete_operation(f"Discovered {len(discovery_results['uri_patterns'])} URI patterns, {len(discovery_results['properties'])} properties")
            return discovery_results
            
        except Exception as e:
            tracker.complete_operation(f"Discovery failed: {str(e)}")
            discovery_results["error"] = str(e)
            return discovery_results
    
    async def _discover_external_id_anchor(self, endpoint: str, external_id: str, id_property: str = None) -> Dict[str, Any]:
        """Step 1: Use external identifier to find URI patterns"""
        
        # Try different search strategies to find the external identifier in the endpoint
        search_queries = []
        
        # Strategy 1: Direct identifier search (works for most biological databases)
        search_queries.append({
            "name": "direct_identifier_search",
            "query": f"""
                SELECT DISTINCT ?entity WHERE {{
                    ?entity ?property "{external_id}" .
                }} LIMIT 10
            """,
            "expected_pattern": f"Contains {external_id} as literal value"
        })
        
        # Strategy 2: URI construction search (common pattern) - prioritize this
        if id_property:
            # Known patterns for common databases
            common_patterns = {
                "uniprot": f"http://purl.uniprot.org/uniprot/{external_id}",
                "chebi": f"http://purl.obolibrary.org/obo/CHEBI_{external_id.replace('CHEBI:', '')}",
                "pubchem": f"http://rdf.ncbi.nlm.nih.gov/pubchem/compound/CID{external_id}",
                "mesh": f"http://id.nlm.nih.gov/mesh/{external_id}",
                "go": f"http://purl.obolibrary.org/obo/GO_{external_id.replace('GO:', '')}"
            }
            
            if id_property.lower() in common_patterns:
                test_uri = common_patterns[id_property.lower()]
                # Insert at beginning - prioritize known patterns
                search_queries.insert(0, {
                    "name": "known_pattern_test",
                    "query": f"""
                        SELECT DISTINCT ?property ?value WHERE {{
                            <{test_uri}> ?property ?value .
                        }} LIMIT 10
                    """,
                    "expected_pattern": test_uri,
                    "test_uri": test_uri  # Store for easier extraction
                })
        
        # Strategy 3: Substring search in URIs (fallback)
        search_queries.append({
            "name": "uri_substring_search", 
            "query": f"""
                SELECT DISTINCT ?entity WHERE {{
                    ?entity ?property ?value .
                    FILTER(CONTAINS(STR(?entity), "{external_id}"))
                }} LIMIT 10
            """,
            "expected_pattern": f"URI contains {external_id}"
        })
        
        # Execute search queries
        uri_patterns = []
        successful_searches = []
        
        for search in search_queries:
            try:
                result = await self._execute_sparql(endpoint, search["query"])
                
                if "results" in result and result["results"]["bindings"]:
                    # Special handling for known pattern test - directly use the test URI
                    if search["name"] == "known_pattern_test" and "test_uri" in search:
                        test_uri = search["test_uri"]
                        pattern = self._extract_uri_pattern(test_uri, external_id)
                        uri_patterns.append({
                            "pattern": pattern,
                            "example_uri": test_uri,
                            "search_method": search["name"],
                            "confidence": 0.95  # High confidence for known patterns
                        })
                        successful_searches.append(search["name"])
                        continue
                    
                    # Extract URI patterns from results for other searches
                    for binding in result["results"]["bindings"]:
                        for var, value in binding.items():
                            if value.get("type") == "uri":
                                uri = value.get("value", "")
                                if external_id in uri or (id_property and id_property.lower() in uri.lower()):
                                    pattern = self._extract_uri_pattern(uri, external_id)
                                    if pattern not in [p["pattern"] for p in uri_patterns]:
                                        uri_patterns.append({
                                            "pattern": pattern,
                                            "example_uri": uri,
                                            "search_method": search["name"],
                                            "confidence": 0.7
                                        })
                    
                    successful_searches.append(search["name"])
                    
            except Exception as e:
                log.debug(f"Search strategy {search['name']} failed: {e}")
                continue
        
        return {
            "step": "external_id_anchor",
            "external_id": external_id,
            "successful_searches": successful_searches,
            "uri_patterns": uri_patterns,
            "queries_attempted": len(search_queries)
        }
    
    async def _analyze_uri_patterns(self, endpoint: str, uri_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Step 2: Analyze and validate discovered URI patterns"""
        
        validated_patterns = []
        
        for pattern_info in uri_patterns:
            try:
                # Test if the pattern URI actually exists and has data
                test_query = f"""
                    SELECT (COUNT(*) as ?count) WHERE {{
                        <{pattern_info['example_uri']}> ?property ?value .
                    }}
                """
                
                result = await self._execute_sparql(endpoint, test_query)
                
                if "results" in result and result["results"]["bindings"]:
                    count_binding = result["results"]["bindings"][0]
                    count = int(count_binding.get("count", {}).get("value", "0"))
                    
                    if count > 0:
                        validated_patterns.append({
                            **pattern_info,
                            "property_count": count,
                            "validation_status": "confirmed"
                        })
                        
            except Exception as e:
                log.debug(f"Pattern validation failed for {pattern_info['example_uri']}: {e}")
                continue
        
        # Sort by confidence and property count
        validated_patterns.sort(key=lambda x: (x["confidence"], x.get("property_count", 0)), reverse=True)
        
        return {
            "step": "uri_pattern_analysis",
            "patterns_tested": len(uri_patterns),
            "validated_patterns": validated_patterns
        }
    
    async def _enumerate_entity_properties(self, endpoint: str, entity_uri: str) -> Dict[str, Any]:
        """Step 3: Enumerate available properties for the entity"""
        
        # Query to find all properties used by this entity
        property_query = f"""
            SELECT DISTINCT ?property (COUNT(*) as ?usage_count) WHERE {{
                <{entity_uri}> ?property ?value .
            }} GROUP BY ?property ORDER BY DESC(?usage_count) LIMIT 50
        """
        
        properties = []
        
        try:
            result = await self._execute_sparql(endpoint, property_query)
            
            if "results" in result and result["results"]["bindings"]:
                for binding in result["results"]["bindings"]:
                    prop_uri = binding.get("property", {}).get("value", "")
                    usage_count = int(binding.get("usage_count", {}).get("value", "0"))
                    
                    if prop_uri:
                        # Extract prefix and local name
                        if "#" in prop_uri:
                            namespace, local_name = prop_uri.rsplit("#", 1)
                            prefix = self._extract_prefix_from_namespace(namespace + "#")
                        elif "/" in prop_uri:
                            namespace, local_name = prop_uri.rsplit("/", 1)
                            prefix = self._extract_prefix_from_namespace(namespace + "/")
                        else:
                            prefix = "unknown"
                            local_name = prop_uri
                        
                        properties.append({
                            "uri": prop_uri,
                            "prefix": prefix,
                            "local_name": local_name,
                            "usage_count": usage_count,
                            "prefixed_form": f"{prefix}:{local_name}" if prefix != "unknown" else local_name
                        })
                        
        except Exception as e:
            log.debug(f"Property enumeration failed for {entity_uri}: {e}")
        
        return {
            "step": "property_enumeration",
            "entity_uri": entity_uri,
            "properties": properties,
            "property_count": len(properties)
        }
    
    async def _validate_discovery_patterns(self, endpoint: str, entity_uri: str, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Step 4: Validate that discovered patterns work with real queries"""
        
        validation_results = []
        
        # Test basic property access
        for prop in properties[:3]:  # Test top 3 properties
            test_query = f"""
                SELECT ?value WHERE {{
                    <{entity_uri}> <{prop['uri']}> ?value .
                }} LIMIT 5
            """
            
            try:
                result = await self._execute_sparql(endpoint, test_query)
                
                if "results" in result and result["results"]["bindings"]:
                    values = [b.get("value", {}).get("value", "") for b in result["results"]["bindings"]]
                    validation_results.append({
                        "property": prop["prefixed_form"],
                        "property_uri": prop["uri"],
                        "test_status": "success",
                        "sample_values": values[:3],
                        "value_count": len(values)
                    })
                else:
                    validation_results.append({
                        "property": prop["prefixed_form"],
                        "property_uri": prop["uri"], 
                        "test_status": "no_results",
                        "sample_values": [],
                        "value_count": 0
                    })
                    
            except Exception as e:
                validation_results.append({
                    "property": prop["prefixed_form"],
                    "property_uri": prop["uri"],
                    "test_status": "failed",
                    "error": str(e),
                    "sample_values": [],
                    "value_count": 0
                })
        
        successful_tests = len([r for r in validation_results if r["test_status"] == "success"])
        
        return {
            "step": "schema_validation",
            "entity_uri": entity_uri,
            "tests_performed": len(validation_results),
            "successful_tests": successful_tests,
            "validation_results": validation_results,
            "success_rate": successful_tests / len(validation_results) if validation_results else 0
        }
    
    def _generate_query_templates(self, uri_pattern: Dict[str, Any], properties: List[Dict[str, Any]], external_id: str) -> Dict[str, Any]:
        """Step 5: Generate query templates based on discovered patterns"""
        
        templates = {}
        
        # Basic entity information template
        if properties:
            top_properties = properties[:5]
            select_vars = " ".join([f"?{prop['local_name']}" for prop in top_properties])
            where_clauses = " . ".join([f"<{uri_pattern['example_uri']}> <{prop['uri']}> ?{prop['local_name']}" for prop in top_properties])
            
            templates["entity_details"] = {
                "description": f"Get basic details for {external_id}",
                "query": f"""
                    SELECT {select_vars} WHERE {{
                        {where_clauses} .
                    }}
                """,
                "variables": [prop['local_name'] for prop in top_properties]
            }
        
        # General exploration template
        templates["explore_entity"] = {
            "description": f"Explore all properties of {external_id}",
            "query": f"""
                SELECT DISTINCT ?property ?value WHERE {{
                    <{uri_pattern['example_uri']}> ?property ?value .
                }} LIMIT 20
            """,
            "variables": ["property", "value"]
        }
        
        # Pattern-based template for finding similar entities
        if uri_pattern.get("pattern"):
            base_pattern = uri_pattern["pattern"].replace(external_id, "{EXTERNAL_ID}")
            templates["similar_entities"] = {
                "description": f"Find entities with similar URI pattern to {external_id}",
                "query": f"""
                    SELECT DISTINCT ?entity WHERE {{
                        ?entity ?property ?value .
                        FILTER(REGEX(STR(?entity), "{base_pattern.replace('{EXTERNAL_ID}', '.*')}"))
                    }} LIMIT 10
                """,
                "variables": ["entity"],
                "pattern_template": base_pattern
            }
        
        return {
            "step": "query_template_generation",
            "external_id": external_id,
            "templates": templates,
            "template_count": len(templates)
        }
    
    def _extract_uri_pattern(self, uri: str, external_id: str) -> str:
        """Extract a generalized URI pattern from a specific URI"""
        # Simple pattern extraction - replace the external ID with a placeholder
        return uri.replace(external_id, "{EXTERNAL_ID}")
    
    def _extract_prefix_from_namespace(self, namespace: str) -> str:
        """Extract or generate a prefix from a namespace URI"""
        # Try to find known prefixes for common namespaces
        common_prefixes = {
            "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
            "http://purl.uniprot.org/core/": "up",
            "http://purl.uniprot.org/taxonomy/": "taxon",
            "http://www.w3.org/2004/02/skos/core#": "skos",
            "http://purl.org/dc/terms/": "dcterms",
            "http://purl.org/dc/elements/1.1/": "dc",
            "http://xmlns.com/foaf/0.1/": "foaf"
        }
        
        if namespace in common_prefixes:
            return common_prefixes[namespace]
        
        # Generate prefix from domain name
        try:
            from urllib.parse import urlparse
            parsed = urlparse(namespace)
            domain_parts = parsed.netloc.split('.')
            if len(domain_parts) >= 2:
                return domain_parts[-2]  # e.g., "uniprot" from "purl.uniprot.org"
            return "unknown"
        except:
            return "unknown"
    
    async def discover_properties_first(
        self,
        endpoint: str,
        progress_format: str = "silent",
        property_limit: int = 100,
        co_occurrence_limit: int = 20
    ) -> Dict[str, Any]:
        """
        Property-first discovery pattern using Claude Code async generator architecture.
        
        Implements progressive discovery phases:
        1. Basic Property Enumeration - Find most used properties
        2. Usage Pattern Analysis - Understand property frequency and types
        3. Co-occurrence Analysis - Discover which properties are used together  
        4. Query Template Generation - Build informed query patterns
        
        This follows Claude Code's async generator pattern with streaming progress updates
        and performance optimization through chunked results and intelligent caching.
        
        Args:
            endpoint: SPARQL endpoint URL or name
            progress_format: Progress tracking format ('silent', 'human', 'json')
            property_limit: Maximum properties to discover (default: 100)
            co_occurrence_limit: Limit for co-occurrence analysis (default: 20)
            
        Returns:
            Comprehensive property analysis with query templates and usage patterns
        """
        # Initialize progress tracker following Claude Code pattern
        tracker = ProgressTracker(progress_format)
        tracker.start_operation("Property-First Discovery", estimated_duration=45)
        
        # Resolve endpoint alias
        resolved_endpoint = self.known_endpoints.get(endpoint.lower(), endpoint)
        tracker.update_progress("Resolving endpoint", 0.05, f"Using {resolved_endpoint}")
        
        # Initialize discovery results structure
        discovery_results = {
            "endpoint": resolved_endpoint,
            "discovery_method": "property_first",
            "phases": [],
            "properties": [],
            "usage_patterns": {},
            "co_occurrence_patterns": {},
            "query_templates": {},
            "performance_metrics": {
                "total_time_ms": 0,
                "properties_discovered": 0,
                "queries_executed": 0,
                "cache_hits": 0
            }
        }
        
        start_time = time.time()
        
        try:
            # Phase 1: Basic Property Enumeration
            tracker.update_progress("Phase 1: Property enumeration", 0.1, "Discovering most used properties")
            enumeration_result = await self._enumerate_properties_phase(
                resolved_endpoint, property_limit, tracker
            )
            discovery_results["phases"].append(enumeration_result)
            discovery_results["properties"] = enumeration_result["properties"]
            discovery_results["performance_metrics"]["queries_executed"] += enumeration_result.get("queries_executed", 0)
            
            # Phase 2: Usage Pattern Analysis
            tracker.update_progress("Phase 2: Usage pattern analysis", 0.4, "Analyzing property types and frequency")
            pattern_result = await self._analyze_usage_patterns_phase(
                resolved_endpoint, discovery_results["properties"][:50], tracker  # Top 50 for pattern analysis
            )
            discovery_results["phases"].append(pattern_result)
            discovery_results["usage_patterns"] = pattern_result["patterns"]
            discovery_results["performance_metrics"]["queries_executed"] += pattern_result.get("queries_executed", 0)
            
            # Phase 3: Co-occurrence Analysis
            tracker.update_progress("Phase 3: Co-occurrence analysis", 0.7, "Finding properties used together")
            cooccurrence_result = await self._analyze_cooccurrence_phase(
                resolved_endpoint, discovery_results["properties"][:co_occurrence_limit], tracker
            )
            discovery_results["phases"].append(cooccurrence_result)
            discovery_results["co_occurrence_patterns"] = cooccurrence_result["patterns"]
            discovery_results["performance_metrics"]["queries_executed"] += cooccurrence_result.get("queries_executed", 0)
            
            # Phase 4: Query Template Generation
            tracker.update_progress("Phase 4: Template generation", 0.9, "Creating query templates")
            template_result = self._generate_property_templates_phase(
                discovery_results["properties"], 
                discovery_results["usage_patterns"],
                discovery_results["co_occurrence_patterns"]
            )
            discovery_results["phases"].append(template_result)
            discovery_results["query_templates"] = template_result["templates"]
            
            # Finalize metrics
            total_time = int((time.time() - start_time) * 1000)
            discovery_results["performance_metrics"]["total_time_ms"] = total_time
            discovery_results["performance_metrics"]["properties_discovered"] = len(discovery_results["properties"])
            
            tracker.complete_operation(
                f"Discovered {len(discovery_results['properties'])} properties, "
                f"{len(discovery_results['query_templates'])} templates"
            )
            
            return discovery_results
            
        except Exception as e:
            tracker.complete_operation(f"Discovery failed: {str(e)}")
            discovery_results["error"] = str(e)
            discovery_results["performance_metrics"]["total_time_ms"] = int((time.time() - start_time) * 1000)
            return discovery_results
    
    async def _enumerate_properties_phase(
        self, 
        endpoint: str, 
        limit: int,
        tracker: ProgressTracker
    ) -> Dict[str, Any]:
        """Phase 1: Basic property enumeration with usage frequency"""
        
        tracker.update_progress("Enumerating properties", 0.15, "Finding most used properties")
        
        # Query to find all properties with usage counts
        # Use a more conservative approach for large endpoints
        property_query = f"""
            SELECT DISTINCT ?property (COUNT(*) as ?usage_count) WHERE {{
                ?subject ?property ?object .
            }} GROUP BY ?property 
            ORDER BY DESC(?usage_count) 
            LIMIT {limit}
        """
        
        # For large endpoints like UniProt, use a simpler sampling approach
        if "uniprot" in endpoint.lower():
            property_query = f"""
                SELECT DISTINCT ?property WHERE {{
                    ?subject ?property ?object .
                }} LIMIT {limit}
            """
        
        properties = []
        queries_executed = 0
        
        try:
            result = await self._execute_sparql(endpoint, property_query)
            queries_executed += 1
            
            if "results" in result and result["results"]["bindings"]:
                for binding in result["results"]["bindings"]:
                    prop_uri = binding.get("property", {}).get("value", "")
                    # Handle both counted and simple queries
                    usage_count = int(binding.get("usage_count", {}).get("value", "1"))
                    
                    if prop_uri:
                        # Extract namespace and prefix information
                        namespace, local_name = self._split_uri(prop_uri)
                        prefix = self._extract_prefix_from_namespace(namespace)
                        
                        property_info = {
                            "uri": prop_uri,
                            "namespace": namespace,
                            "local_name": local_name,
                            "prefix": prefix,
                            "prefixed_form": f"{prefix}:{local_name}" if prefix != "unknown" else local_name,
                            "usage_count": usage_count,
                            "rank": len(properties) + 1
                        }
                        properties.append(property_info)
            
            tracker.update_progress("Property enumeration complete", 0.25, f"Found {len(properties)} properties")
            
        except Exception as e:
            log.error(f"Property enumeration failed: {e}")
            # Try even simpler query as fallback
            try:
                simple_query = f"""
                    SELECT DISTINCT ?property WHERE {{
                        ?s ?property ?o .
                    }} LIMIT {min(limit, 20)}
                """
                result = await self._execute_sparql(endpoint, simple_query)
                queries_executed += 1
                
                if "results" in result and result["results"]["bindings"]:
                    for binding in result["results"]["bindings"]:
                        prop_uri = binding.get("property", {}).get("value", "")
                        if prop_uri:
                            namespace, local_name = self._split_uri(prop_uri)
                            prefix = self._extract_prefix_from_namespace(namespace)
                            
                            property_info = {
                                "uri": prop_uri,
                                "namespace": namespace,
                                "local_name": local_name,
                                "prefix": prefix,
                                "prefixed_form": f"{prefix}:{local_name}" if prefix != "unknown" else local_name,
                                "usage_count": 1,  # Default value for simple query
                                "rank": len(properties) + 1
                            }
                            properties.append(property_info)
                
                tracker.update_progress("Fallback enumeration complete", 0.25, f"Found {len(properties)} properties")
                
            except Exception as e2:
                log.error(f"Fallback property enumeration also failed: {e2}")
                properties = []
        
        return {
            "phase": "property_enumeration",
            "properties": properties,
            "queries_executed": queries_executed,
            "property_count": len(properties)
        }
    
    async def _analyze_usage_patterns_phase(
        self,
        endpoint: str,
        properties: List[Dict[str, Any]],
        tracker: ProgressTracker
    ) -> Dict[str, Any]:
        """Phase 2: Analyze usage patterns for top properties"""
        
        tracker.update_progress("Analyzing usage patterns", 0.45, "Examining property types and frequency")
        
        patterns = {}
        queries_executed = 0
        
        # Analyze top properties in batches for performance
        batch_size = 10
        for i in range(0, min(len(properties), 30), batch_size):  # Analyze top 30 properties
            batch = properties[i:i + batch_size]
            batch_patterns = await self._analyze_property_batch(endpoint, batch)
            patterns.update(batch_patterns)
            queries_executed += len(batch)
            
            progress = 0.45 + (i / min(len(properties), 30)) * 0.2
            tracker.update_progress(
                f"Analyzed {i + len(batch)} properties", 
                progress, 
                f"Batch {i//batch_size + 1}"
            )
        
        # Generate pattern summary
        pattern_summary = self._summarize_usage_patterns(patterns)
        
        return {
            "phase": "usage_pattern_analysis",
            "patterns": patterns,
            "summary": pattern_summary,
            "queries_executed": queries_executed,
            "properties_analyzed": len(patterns)
        }
    
    async def _analyze_property_batch(
        self,
        endpoint: str,
        properties: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze a batch of properties for performance optimization"""
        
        batch_patterns = {}
        
        for prop in properties:
            try:
                # Query to analyze object types for this property
                type_query = f"""
                    SELECT ?object_type (COUNT(*) as ?count) WHERE {{
                        ?subject <{prop['uri']}> ?object .
                        OPTIONAL {{ ?object a ?object_type }}
                    }} GROUP BY ?object_type 
                    ORDER BY DESC(?count) 
                    LIMIT 10
                """
                
                result = await self._execute_sparql(endpoint, type_query)
                
                object_types = []
                if "results" in result and result["results"]["bindings"]:
                    for binding in result["results"]["bindings"]:
                        obj_type = binding.get("object_type", {}).get("value", "")
                        count = int(binding.get("count", {}).get("value", "0"))
                        if obj_type:
                            object_types.append({"type": obj_type, "count": count})
                        elif count > 0:  # Literal values (no type)
                            object_types.append({"type": "literal", "count": count})
                
                batch_patterns[prop["uri"]] = {
                    "property": prop,
                    "object_types": object_types,
                    "is_object_property": any(t["type"] != "literal" for t in object_types),
                    "is_datatype_property": any(t["type"] == "literal" for t in object_types)
                }
                
            except Exception as e:
                log.debug(f"Pattern analysis failed for {prop['uri']}: {e}")
                batch_patterns[prop["uri"]] = {
                    "property": prop,
                    "object_types": [],
                    "analysis_error": str(e)
                }
        
        return batch_patterns
    
    async def _analyze_cooccurrence_phase(
        self,
        endpoint: str,
        properties: List[Dict[str, Any]],
        tracker: ProgressTracker
    ) -> Dict[str, Any]:
        """Phase 3: Analyze which properties are commonly used together"""
        
        tracker.update_progress("Analyzing co-occurrence", 0.75, "Finding properties used together")
        
        cooccurrence_patterns = {}
        queries_executed = 0
        
        # Analyze co-occurrence for top properties
        top_properties = properties[:15]  # Limit for performance
        
        for i, prop in enumerate(top_properties):
            try:
                # Query to find properties that co-occur with this one
                cooccur_query = f"""
                    SELECT ?other_property (COUNT(DISTINCT ?subject) as ?cooccur_count) WHERE {{
                        ?subject <{prop['uri']}> ?value1 .
                        ?subject ?other_property ?value2 .
                        FILTER(?other_property != <{prop['uri']}>)
                    }} GROUP BY ?other_property 
                    ORDER BY DESC(?cooccur_count) 
                    LIMIT 15
                """
                
                result = await self._execute_sparql(endpoint, cooccur_query)
                queries_executed += 1
                
                cooccurrences = []
                if "results" in result and result["results"]["bindings"]:
                    for binding in result["results"]["bindings"]:
                        other_prop = binding.get("other_property", {}).get("value", "")
                        count = int(binding.get("cooccur_count", {}).get("value", "0"))
                        
                        if other_prop and count > 0:
                            # Find the other property in our discovered list
                            other_prop_info = next(
                                (p for p in properties if p["uri"] == other_prop), 
                                {"uri": other_prop, "prefixed_form": other_prop}
                            )
                            
                            cooccurrences.append({
                                "property": other_prop_info,
                                "cooccurrence_count": count
                            })
                
                cooccurrence_patterns[prop["uri"]] = {
                    "property": prop,
                    "cooccurrences": cooccurrences
                }
                
                progress = 0.75 + (i / len(top_properties)) * 0.1
                tracker.update_progress(
                    f"Co-occurrence analysis", 
                    progress, 
                    f"Property {i+1}/{len(top_properties)}"
                )
                
            except Exception as e:
                log.debug(f"Co-occurrence analysis failed for {prop['uri']}: {e}")
                cooccurrence_patterns[prop["uri"]] = {
                    "property": prop,
                    "cooccurrences": [],
                    "analysis_error": str(e)
                }
        
        return {
            "phase": "cooccurrence_analysis",
            "patterns": cooccurrence_patterns,
            "queries_executed": queries_executed,
            "properties_analyzed": len(cooccurrence_patterns)
        }
    
    def _generate_property_templates_phase(
        self,
        properties: List[Dict[str, Any]],
        usage_patterns: Dict[str, Any],
        cooccurrence_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Phase 4: Generate query templates based on discovered patterns"""
        
        templates = {}
        
        # Template 1: Basic property exploration
        if properties:
            top_props = properties[:5]
            select_vars = " ".join([f"?{prop['local_name']}" for prop in top_props])
            optional_clauses = " ".join([
                f"OPTIONAL {{ ?entity <{prop['uri']}> ?{prop['local_name']} }}" 
                for prop in top_props
            ])
            
            templates["explore_top_properties"] = {
                "description": "Explore entities using top 5 most common properties",
                "query": f"""
                    SELECT ?entity {select_vars} WHERE {{
                        ?entity ?any_property ?any_value .
                        {optional_clauses}
                    }} LIMIT 20
                """,
                "variables": ["entity"] + [prop['local_name'] for prop in top_props]
            }
        
        # Template 2: Property frequency analysis
        templates["property_frequency"] = {
            "description": "Analyze property usage frequency across the endpoint",
            "query": """
                SELECT ?property (COUNT(*) as ?usage_count) WHERE {
                    ?subject ?property ?object .
                } GROUP BY ?property 
                ORDER BY DESC(?usage_count) 
                LIMIT 50
            """,
            "variables": ["property", "usage_count"]
        }
        
        # Template 3: Co-occurrence patterns
        if cooccurrence_patterns:
            # Find a property with good co-occurrence data
            best_cooccur = max(
                cooccurrence_patterns.values(),
                key=lambda x: len(x.get("cooccurrences", [])),
                default=None
            )
            
            if best_cooccur and best_cooccur.get("cooccurrences"):
                prop = best_cooccur["property"]
                top_cooccur = best_cooccur["cooccurrences"][0]
                
                templates["property_cooccurrence"] = {
                    "description": f"Find entities with both {prop['prefixed_form']} and related properties",
                    "query": f"""
                        SELECT ?entity ?value1 ?value2 WHERE {{
                            ?entity <{prop['uri']}> ?value1 .
                            ?entity <{top_cooccur['property']['uri']}> ?value2 .
                        }} LIMIT 20
                    """,
                    "variables": ["entity", "value1", "value2"],
                    "pattern_properties": [prop['prefixed_form'], top_cooccur['property'].get('prefixed_form', 'related')]
                }
        
        # Template 4: Type-based exploration
        object_properties = [
            uri for uri, pattern in usage_patterns.items() 
            if pattern.get("is_object_property", False)
        ]
        
        if object_properties:
            example_prop = next(
                (p for p in properties if p["uri"] == object_properties[0]), 
                properties[0] if properties else None
            )
            
            if example_prop:
                templates["type_exploration"] = {
                    "description": f"Explore entity types connected via {example_prop['prefixed_form']}",
                    "query": f"""
                        SELECT ?subject_type ?object_type (COUNT(*) as ?connection_count) WHERE {{
                            ?subject <{example_prop['uri']}> ?object .
                            OPTIONAL {{ ?subject a ?subject_type }}
                            OPTIONAL {{ ?object a ?object_type }}
                        }} GROUP BY ?subject_type ?object_type 
                        ORDER BY DESC(?connection_count) 
                        LIMIT 15
                    """,
                    "variables": ["subject_type", "object_type", "connection_count"]
                }
        
        return {
            "phase": "template_generation",
            "templates": templates,
            "template_count": len(templates)
        }
    
    def _split_uri(self, uri: str) -> tuple[str, str]:
        """Split URI into namespace and local name"""
        if "#" in uri:
            namespace, local_name = uri.rsplit("#", 1)
            return namespace + "#", local_name
        elif "/" in uri:
            namespace, local_name = uri.rsplit("/", 1)
            return namespace + "/", local_name
        else:
            return uri, ""
    
    def _summarize_usage_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from usage patterns"""
        
        total_properties = len(patterns)
        object_properties = sum(1 for p in patterns.values() if p.get("is_object_property", False))
        datatype_properties = sum(1 for p in patterns.values() if p.get("is_datatype_property", False))
        
        # Find most common object types
        all_object_types = {}
        for pattern in patterns.values():
            for obj_type in pattern.get("object_types", []):
                type_uri = obj_type["type"]
                if type_uri != "literal":
                    all_object_types[type_uri] = all_object_types.get(type_uri, 0) + obj_type["count"]
        
        top_object_types = sorted(all_object_types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_properties": total_properties,
            "object_properties": object_properties,
            "datatype_properties": datatype_properties,
            "mixed_properties": total_properties - object_properties - datatype_properties,
            "top_object_types": [{"type": t[0], "usage_count": t[1]} for t in top_object_types]
        }

    # Entity-Known Discovery Helper Methods
    async def _resolve_entity_uri(self, endpoint: str, entity_id: str) -> str:
        """
        Convert external entity ID to full URI for DESCRIBE queries
        
        Args:
            endpoint: SPARQL endpoint URL
            entity_id: External ID (like P01308) or full URI
            
        Returns:
            Full URI for the entity
        """
        # If already a full URI, return as-is
        if entity_id.startswith('http://') or entity_id.startswith('https://'):
            return entity_id
        
        # Try to resolve using known patterns for different endpoints
        if 'uniprot' in endpoint.lower():
            # UniProt pattern: http://purl.uniprot.org/uniprot/P01308
            return f"http://purl.uniprot.org/uniprot/{entity_id}"
        elif 'wikidata' in endpoint.lower():
            # Wikidata pattern: http://www.wikidata.org/entity/Q123
            if entity_id.startswith('Q') or entity_id.startswith('P'):
                return f"http://www.wikidata.org/entity/{entity_id}"
        elif 'wikipathways' in endpoint.lower():
            # WikiPathways pattern: need to discover
            pass
        
        # Fallback: try simple exploration to find URI pattern
        try:
            # Try a simple SELECT to find example URIs
            explore_query = f"""
            SELECT DISTINCT ?uri WHERE {{
                ?uri ?p ?o .
                FILTER(CONTAINS(str(?uri), "{entity_id}"))
            }} LIMIT 5
            """
            results = await self._execute_sparql(endpoint, explore_query)
            bindings = results.get('results', {}).get('bindings', [])
            if bindings:
                return bindings[0]['uri']['value']
        except:
            pass
        
        # Last resort: return as-is and hope for the best
        return entity_id
    
    def _extract_entity_affordances(self, describe_results: Dict[str, Any], entity_uri: str) -> Dict[str, Any]:
        """
        Extract affordances (capabilities) from DESCRIBE query results
        
        Args:
            describe_results: Results from DESCRIBE query
            entity_uri: URI of the described entity
            
        Returns:
            Dict with extracted affordances
        """
        affordances = {
            'properties': [],
            'types': [],
            'relationships': [],
            'namespaces': set(),
            'patterns': []
        }
        
        bindings = describe_results.get('results', {}).get('bindings', [])
        
        for binding in bindings:
            subject = binding.get('subject', {}).get('value', '')
            predicate = binding.get('predicate', {}).get('value', '')
            object_value = binding.get('object', {})
            
            # Only process triples where our entity is the subject
            if subject == entity_uri:
                # Extract property information
                if predicate:
                    property_info = {
                        'uri': predicate,
                        'object_type': object_value.get('type', 'unknown'),
                        'object_value': object_value.get('value', '')
                    }
                    affordances['properties'].append(property_info)
                    
                    # Extract namespace
                    if '#' in predicate:
                        namespace = predicate.split('#')[0] + '#'
                    elif '/' in predicate:
                        namespace = '/'.join(predicate.split('/')[:-1]) + '/'
                    else:
                        namespace = predicate
                    affordances['namespaces'].add(namespace)
                    
                    # Check for type declarations
                    if predicate in ['http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
                                   'https://www.w3.org/1999/02/22-rdf-syntax-ns#type']:
                        affordances['types'].append(object_value.get('value', ''))
                    
                    # Check for relationships to other entities
                    if object_value.get('type') == 'uri':
                        affordances['relationships'].append({
                            'property': predicate,
                            'target': object_value.get('value', '')
                        })
        
        # Generate usage patterns
        affordances['patterns'] = self._generate_affordance_patterns(affordances)
        affordances['namespaces'] = list(affordances['namespaces'])
        
        return affordances
    
    def _generate_affordance_patterns(self, affordances: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate SPARQL query patterns from discovered affordances"""
        patterns = []
        
        # Basic property pattern
        if affordances['properties']:
            prop_examples = affordances['properties'][:5]  # Top 5 properties
            pattern = {
                'name': 'entity_properties',
                'description': 'Query properties of this entity type',
                'variables': ['entity', 'property', 'value'],
                'pattern': '?entity ?property ?value .',
                'example_properties': [p['uri'] for p in prop_examples]
            }
            patterns.append(pattern)
        
        # Type-based pattern
        if affordances['types']:
            pattern = {
                'name': 'entities_of_type',
                'description': 'Find other entities of the same type',
                'variables': ['entity', 'type'],
                'pattern': '?entity rdf:type ?type .',
                'example_types': affordances['types'][:3]
            }
            patterns.append(pattern)
        
        # Relationship pattern
        if affordances['relationships']:
            rel_examples = affordances['relationships'][:3]
            pattern = {
                'name': 'entity_relationships',
                'description': 'Follow relationships from this entity',
                'variables': ['source', 'property', 'target'],
                'pattern': '?source ?property ?target .',
                'example_relationships': [r['property'] for r in rel_examples]
            }
            patterns.append(pattern)
        
        return patterns
    
    def _build_schema_from_affordances(self, endpoint: str, entity_uri: str, affordances: Dict[str, Any]) -> 'EndpointSchema':
        """Build EndpointSchema from entity affordances"""
        # Extract vocabularies from namespaces
        vocabularies = []
        for namespace in affordances['namespaces']:
            vocab = {
                'namespace': namespace,
                'prefix': self._extract_prefix_from_namespace(namespace),
                'discovered_from': 'entity_affordances'
            }
            vocabularies.append(vocab)
        
        # Extract classes from types
        classes = []
        for type_uri in affordances['types']:
            class_info = {
                'uri': type_uri,
                'label': type_uri.split('/')[-1].split('#')[-1],
                'discovered_from': 'entity_type'
            }
            classes.append(class_info)
        
        # Extract properties from affordances
        properties = []
        for prop in affordances['properties']:
            prop_info = {
                'uri': prop['uri'],
                'label': prop['uri'].split('/')[-1].split('#')[-1],
                'range': prop['object_type'],
                'discovered_from': 'entity_affordances'
            }
            properties.append(prop_info)
        
        # Create schema
        schema = EndpointSchema(
            endpoint=endpoint,
            vocabularies=vocabularies,
            classes=classes,
            properties=properties,
            query_patterns=affordances['patterns'],
            discovery_metadata={
                'method': 'entity_known_pathway',
                'entity_uri': entity_uri,
                'discovery_time': time.time()
            }
        )
        
        return schema
    
    # Property Affordance Discovery Helper Methods
    async def _discover_entity_types(self, endpoint: str) -> List[Dict[str, Any]]:
        """Discover what types of entities exist in the endpoint"""
        try:
            # Query for entity types with counts
            type_query = """
            SELECT DISTINCT ?type (COUNT(?entity) as ?count) WHERE {
                ?entity rdf:type ?type .
            } GROUP BY ?type 
            ORDER BY DESC(?count) 
            LIMIT 20
            """
            results = await self._execute_sparql(endpoint, type_query)
            return results.get('results', {}).get('bindings', [])
        except:
            # Fallback: simple type discovery
            simple_query = """
            SELECT DISTINCT ?type WHERE {
                ?entity rdf:type ?type .
            } LIMIT 20
            """
            results = await self._execute_sparql(endpoint, simple_query)
            bindings = results.get('results', {}).get('bindings', [])
            # Convert to expected format
            return [{'type': b, 'count': {'value': '0'}} for b in bindings]
    
    async def _discover_type_affordances(self, endpoint: str, type_uri: str) -> Dict[str, Any]:
        """Discover what affordances are available for a specific type"""
        try:
            # Find properties used by entities of this type
            affordance_query = f"""
            SELECT DISTINCT ?property (COUNT(*) as ?usage) WHERE {{
                ?entity rdf:type <{type_uri}> .
                ?entity ?property ?value .
            }} GROUP BY ?property 
            ORDER BY DESC(?usage) 
            LIMIT 50
            """
            results = await self._execute_sparql(endpoint, affordance_query)
            properties = results.get('results', {}).get('bindings', [])
            
            return {
                'type': type_uri,
                'properties': properties,
                'sample_count': len(properties)
            }
        except:
            return {'type': type_uri, 'properties': [], 'sample_count': 0}
    
    def _build_schema_from_type_affordances(self, endpoint: str, entity_types: List[Dict[str, Any]], type_affordances: Dict[str, Dict[str, Any]]) -> 'EndpointSchema':
        """Build comprehensive schema from type-based affordance discovery"""
        vocabularies = []
        classes = []
        properties = []
        query_patterns = []
        
        # Process entity types as classes
        for entity_type in entity_types:
            type_uri = entity_type.get('type', {}).get('value', '')
            if type_uri:
                class_info = {
                    'uri': type_uri,
                    'label': type_uri.split('/')[-1].split('#')[-1],
                    'instance_count': entity_type.get('count', {}).get('value', '0'),
                    'discovered_from': 'type_discovery'
                }
                classes.append(class_info)
        
        # Process affordances for each type
        namespaces = set()
        for type_uri, affordances in type_affordances.items():
            for prop in affordances.get('properties', []):
                prop_uri = prop.get('property', {}).get('value', '')
                if prop_uri:
                    prop_info = {
                        'uri': prop_uri,
                        'label': prop_uri.split('/')[-1].split('#')[-1],
                        'usage_count': prop.get('usage', {}).get('value', '0'),
                        'domain_type': type_uri,
                        'discovered_from': 'type_affordances'
                    }
                    properties.append(prop_info)
                    
                    # Extract namespace
                    if '#' in prop_uri:
                        namespace = prop_uri.split('#')[0] + '#'
                    elif '/' in prop_uri:
                        namespace = '/'.join(prop_uri.split('/')[:-1]) + '/'
                    else:
                        namespace = prop_uri
                    namespaces.add(namespace)
        
        # Generate vocabularies from namespaces
        for namespace in namespaces:
            vocab = {
                'namespace': namespace,
                'prefix': self._extract_prefix_from_namespace(namespace),
                'discovered_from': 'type_affordances'
            }
            vocabularies.append(vocab)
        
        # Generate query patterns
        if classes:
            pattern = {
                'name': 'type_exploration',
                'description': 'Explore entities by type',
                'variables': ['entity', 'type'],
                'pattern': '?entity rdf:type ?type .',
                'example_types': [c['uri'] for c in classes[:5]]
            }
            query_patterns.append(pattern)
        
        # Create schema
        from .schema_discovery import EndpointSchema  # Import here to avoid circular imports
        schema = EndpointSchema(
            endpoint=endpoint,
            vocabularies=vocabularies,
            classes=classes,
            properties=properties,
            query_patterns=query_patterns,
            discovery_metadata={
                'method': 'property_affordance_pathway',
                'types_discovered': len(entity_types),
                'total_properties': len(properties),
                'discovery_time': time.time()
            }
        )
        
        return schema
    
    # Progressive Property Affordance Discovery Methods
    async def _discover_ontology_properties(self, endpoint: str) -> List[Dict[str, Any]]:
        """
        Phase 1: Discover properties through ontology introspection
        
        Look for explicit property declarations (OWL/RDFS) in the endpoint's ontology.
        """
        ontology_queries = [
            # OWL style - most comprehensive
            """
            SELECT DISTINCT ?property ?label ?comment ?domain ?range WHERE {
                { ?property rdf:type owl:ObjectProperty }
                UNION 
                { ?property rdf:type owl:DatatypeProperty }
                OPTIONAL { ?property rdfs:label ?label }
                OPTIONAL { ?property rdfs:comment ?comment }
                OPTIONAL { ?property rdfs:domain ?domain }
                OPTIONAL { ?property rdfs:range ?range }
            } LIMIT 50
            """,
            
            # RDFS style - simpler fallback
            """
            SELECT DISTINCT ?property ?label ?comment WHERE {
                ?property rdf:type rdfs:Property .
                OPTIONAL { ?property rdfs:label ?label }
                OPTIONAL { ?property rdfs:comment ?comment }
            } LIMIT 50
            """,
            
            # Schema.org style - web-focused
            """
            SELECT DISTINCT ?property ?label WHERE {
                ?property rdf:type rdf:Property .
                OPTIONAL { ?property rdfs:label ?label }
            } LIMIT 50
            """
        ]
        
        for query in ontology_queries:
            try:
                results = await self._execute_sparql(endpoint, query)
                bindings = results.get('results', {}).get('bindings', [])
                
                if bindings:
                    # Convert to structured format
                    properties = []
                    for binding in bindings:
                        prop_info = {
                            'uri': binding.get('property', {}).get('value', ''),
                            'label': binding.get('label', {}).get('value', ''),
                            'comment': binding.get('comment', {}).get('value', ''),
                            'domain': binding.get('domain', {}).get('value', ''),
                            'range': binding.get('range', {}).get('value', ''),
                            'discovery_method': 'ontology_introspection'
                        }
                        if prop_info['uri']:
                            properties.append(prop_info)
                    
                    if properties:
                        log.info(f"Found {len(properties)} ontology properties in {endpoint}")
                        return properties
                        
            except Exception as e:
                log.debug(f"Ontology query failed for {endpoint}: {e}")
                continue
        
        return []
    
    async def _discover_usage_properties(self, endpoint: str) -> List[Dict[str, Any]]:
        """
        Phase 2: Discover properties through usage analysis
        
        Find properties by analyzing what predicates are actually used in the data.
        """
        usage_queries = [
            # Simple property enumeration
            """
            SELECT DISTINCT ?property (COUNT(*) as ?usage) WHERE {
                ?subject ?property ?object .
                FILTER(!isBlank(?subject))
            } GROUP BY ?property 
            ORDER BY DESC(?usage) 
            LIMIT 30
            """,
            
            # Fallback without aggregation
            """
            SELECT DISTINCT ?property WHERE {
                ?subject ?property ?object .
            } LIMIT 30
            """
        ]
        
        for query in usage_queries:
            try:
                results = await self._execute_sparql(endpoint, query)
                bindings = results.get('results', {}).get('bindings', [])
                
                if bindings:
                    properties = []
                    for binding in bindings:
                        prop_uri = binding.get('property', {}).get('value', '')
                        usage_count = binding.get('usage', {}).get('value', '0')
                        
                        if prop_uri:
                            # Extract label from URI
                            if '#' in prop_uri:
                                label = prop_uri.split('#')[-1]
                            elif '/' in prop_uri:
                                label = prop_uri.split('/')[-1]
                            else:
                                label = prop_uri
                            
                            prop_info = {
                                'uri': prop_uri,
                                'label': label,
                                'usage_count': usage_count,
                                'discovery_method': 'usage_analysis'
                            }
                            properties.append(prop_info)
                    
                    if properties:
                        log.info(f"Found {len(properties)} usage properties in {endpoint}")
                        return properties
                        
            except Exception as e:
                log.debug(f"Usage query failed for {endpoint}: {e}")
                continue
        
        return []
    
    async def _build_schema_from_ontology_properties(self, endpoint: str, ontology_properties: List[Dict[str, Any]]) -> EndpointSchema:
        """Build schema from ontology-declared properties with rich metadata"""
        
        # Extract vocabularies from namespaces
        vocabularies = []
        namespaces = set()
        for prop in ontology_properties:
            prop_uri = prop['uri']
            if '#' in prop_uri:
                namespace = prop_uri.split('#')[0] + '#'
            elif '/' in prop_uri:
                namespace = '/'.join(prop_uri.split('/')[:-1]) + '/'
            else:
                continue
            namespaces.add(namespace)
        
        for namespace in namespaces:
            vocab = {
                'namespace': namespace,
                'prefix': self._extract_prefix_from_namespace(namespace),
                'discovered_from': 'ontology_introspection'
            }
            vocabularies.append(vocab)
        
        # Extract classes from domains/ranges
        classes = []
        class_uris = set()
        for prop in ontology_properties:
            if prop.get('domain'):
                class_uris.add(prop['domain'])
            if prop.get('range') and not prop['range'].startswith('http://www.w3.org/2001/XMLSchema'):
                class_uris.add(prop['range'])
        
        for class_uri in class_uris:
            class_info = {
                'uri': class_uri,
                'label': class_uri.split('/')[-1].split('#')[-1],
                'discovered_from': 'ontology_introspection'
            }
            classes.append(class_info)
        
        # Properties are already in good format
        properties = ontology_properties
        
        # Generate query patterns based on property semantics
        query_patterns = []
        if properties:
            # Basic property pattern
            pattern = {
                'name': 'ontology_properties',
                'description': 'Query using ontology-declared properties',
                'variables': ['subject', 'property', 'object'],
                'pattern': '?subject ?property ?object .',
                'example_properties': [p['uri'] for p in properties[:5]]
            }
            query_patterns.append(pattern)
            
            # Domain-specific patterns
            domain_properties = [p for p in properties if p.get('domain')]
            if domain_properties:
                pattern = {
                    'name': 'typed_properties',
                    'description': 'Query properties with known domains',
                    'variables': ['entity', 'property', 'value'],
                    'pattern': '?entity rdf:type ?type . ?entity ?property ?value .',
                    'example_domains': list(set(p['domain'] for p in domain_properties[:3]))
                }
                query_patterns.append(pattern)
        
        return EndpointSchema(
            endpoint=endpoint,
            vocabularies=vocabularies,
            classes=classes,
            properties=properties,
            query_patterns=query_patterns,
            discovery_metadata={
                'method': 'property_affordance_pathway',
                'approach': 'ontology_introspection',
                'properties_discovered': len(properties),
                'discovery_time': time.time()
            }
        )
    
    async def _build_schema_from_usage_properties(self, endpoint: str, usage_properties: List[Dict[str, Any]]) -> EndpointSchema:
        """Build schema from usage-discovered properties"""
        
        # Extract vocabularies from namespaces
        vocabularies = []
        namespaces = set()
        for prop in usage_properties:
            prop_uri = prop['uri']
            if '#' in prop_uri:
                namespace = prop_uri.split('#')[0] + '#'
            elif '/' in prop_uri:
                namespace = '/'.join(prop_uri.split('/')[:-1]) + '/'
            else:
                continue
            namespaces.add(namespace)
        
        for namespace in namespaces:
            vocab = {
                'namespace': namespace,
                'prefix': self._extract_prefix_from_namespace(namespace),
                'discovered_from': 'usage_analysis'
            }
            vocabularies.append(vocab)
        
        # No explicit classes from usage analysis
        classes = []
        
        # Properties from usage analysis
        properties = usage_properties
        
        # Generate simple query patterns
        query_patterns = []
        if properties:
            pattern = {
                'name': 'usage_properties',
                'description': 'Query using frequently used properties',
                'variables': ['subject', 'property', 'object'],
                'pattern': '?subject ?property ?object .',
                'example_properties': [p['uri'] for p in properties[:5]]
            }
            query_patterns.append(pattern)
        
        return EndpointSchema(
            endpoint=endpoint,
            vocabularies=vocabularies,
            classes=classes,
            properties=properties,
            query_patterns=query_patterns,
            discovery_metadata={
                'method': 'property_affordance_pathway',
                'approach': 'usage_based',
                'properties_discovered': len(properties),
                'discovery_time': time.time()
            }
        )
    
    async def _enhance_with_ontology_dereferencing(self, schema: EndpointSchema) -> EndpointSchema:
        """
        Enhancement step: Ontology dereferencing using OntoFetch tool
        
        Extracts namespaces from discovered vocabularies, attempts to dereference 
        ontology URLs, and enriches schema with additional properties from fetched ontologies.
        
        This is a non-blocking enhancement that gracefully fails if ontology 
        dereferencing is unavailable or fails.
        """
        try:
            # Import OntoFetch functionality
            from ..cli.cl_ontfetch import AgenticOntologyFetcher
            ontology_fetcher = AgenticOntologyFetcher()
            
            # Extract ontology URIs from discovered vocabularies
            ontology_uris_to_fetch = self._extract_ontology_uris_from_schema(schema)
            
            # Track enhancement metadata
            enhancement_metadata = {
                'ontology_uris_attempted': len(ontology_uris_to_fetch),
                'ontology_uris_successfully_dereferenced': 0,
                'additional_properties_discovered': 0,
                'enhancement_enabled': True,
                'attempted_uris': ontology_uris_to_fetch[:5]  # For debugging
            }
            
            log.debug(f"Ontology dereferencing attempting {len(ontology_uris_to_fetch)} URIs: {ontology_uris_to_fetch}")
            
            # Attempt to dereference each ontology URI (with reasonable limits)
            max_ontologies_to_fetch = 5  # Reasonable limit to prevent long delays
            additional_properties = []
            
            for ontology_uri in ontology_uris_to_fetch[:max_ontologies_to_fetch]:
                try:
                    # Check if this URI/prefix is already in cache (user's request)
                    cache_key = f"ontology_dereferencing_{hash(ontology_uri)}"
                    cached_ontology = self.cache.get(cache_key)
                    
                    if cached_ontology:
                        log.debug(f"Skipping cached ontology: {ontology_uri}")
                        continue
                    
                    log.debug(f"Attempting ontology dereferencing for: {ontology_uri}")
                    
                    # Use OntoFetch to discover the ontology
                    ontology_result = await ontology_fetcher.discover_ontology(
                        target=ontology_uri,
                        ontology_type="sparql" if "sparql" in ontology_uri else "discover",
                        domain=self._infer_domain_from_uri(ontology_uri),
                        force_refresh=False
                    )
                    
                    if ontology_result.get("success") and ontology_result.get("properties"):
                        enhancement_metadata['ontology_uris_successfully_dereferenced'] += 1
                        
                        # Extract additional properties from dereferenced ontology (list format)
                        ontology_properties = ontology_result.get("properties", [])
                        
                        for prop_info in ontology_properties:
                            # Create property entry compatible with schema format
                            additional_prop = {
                                'uri': prop_info.get('uri', ''),
                                'label': prop_info.get('label', ''),
                                'comment': prop_info.get('comment', ''),
                                'domain': prop_info.get('domain', ''),
                                'range': prop_info.get('range', ''),
                                'property_type': prop_info.get('property_type', ''),
                                'discovery_method': 'ontology_dereferencing',
                                'dereferenced_from': ontology_uri
                            }
                            if additional_prop['uri']:  # Only add if we have a valid URI
                                additional_properties.append(additional_prop)
                        
                        # Cache the successful result
                        self.cache.set(cache_key, ontology_result)
                        
                        log.info(f"Successfully dereferenced ontology {ontology_uri}: found {len(ontology_properties)} additional properties")
                    
                except Exception as e:
                    log.debug(f"Failed to dereference ontology {ontology_uri}: {e}")
                    continue
            
            # Merge additional properties into schema
            if additional_properties:
                # Create enhanced schema with additional properties
                enhanced_properties = list(schema.properties) + additional_properties
                enhancement_metadata['additional_properties_discovered'] = len(additional_properties)
                
                enhanced_schema = EndpointSchema(
                    endpoint=schema.endpoint,
                    vocabularies=schema.vocabularies,
                    classes=schema.classes,
                    properties=enhanced_properties,
                    query_patterns=schema.query_patterns,
                    performance_hints=schema.performance_hints,
                    agent_guidance=schema.agent_guidance,
                    discovery_metadata={
                        **schema.discovery_metadata,
                        'ontology_enhancement': enhancement_metadata
                    }
                )
                
                log.info(f"Schema enhanced with {len(additional_properties)} properties from ontology dereferencing")
                return enhanced_schema
            else:
                # No enhancement possible, but record that we tried
                schema.discovery_metadata['ontology_enhancement'] = enhancement_metadata
                log.debug("No additional properties discovered through ontology dereferencing")
                return schema
                
        except ImportError:
            log.debug("OntoFetch not available for ontology dereferencing enhancement")
            schema.discovery_metadata['ontology_enhancement'] = {
                'enhancement_enabled': False,
                'reason': 'OntoFetch not available'
            }
            return schema
        except Exception as e:
            log.debug(f"Ontology dereferencing enhancement failed: {e}")
            schema.discovery_metadata['ontology_enhancement'] = {
                'enhancement_enabled': False,
                'reason': str(e)
            }
            return schema
    
    def _extract_ontology_uris_from_schema(self, schema: EndpointSchema) -> List[str]:
        """Extract potential ontology URIs from discovered vocabularies for dereferencing"""
        
        ontology_uris = []
        
        for vocab in schema.vocabularies:
            namespace = vocab.get('namespace', '')
            
            # Skip standard W3C vocabularies that don't need dereferencing
            skip_namespaces = [
                'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'http://www.w3.org/2000/01/rdf-schema#',
                'http://www.w3.org/2002/07/owl#',
                'http://www.w3.org/2001/XMLSchema#',
                'http://www.w3.org/2004/02/skos/core#'
            ]
            
            if namespace and namespace not in skip_namespaces:
                # Convert namespace to potential ontology URI
                # Remove trailing # or / to get base ontology URI
                if namespace.endswith('#'):
                    base_uri = namespace[:-1]
                elif namespace.endswith('/'):
                    base_uri = namespace[:-1]
                else:
                    base_uri = namespace
                
                # Look for common ontology patterns
                if any(pattern in base_uri for pattern in [
                    'purl.org', 'w3id.org', 'bioschemas.org', 'schema.org',
                    'purl.uniprot.org', 'purl.obolibrary.org', 'vocabularies.wikipathways.org',
                    'purl.org/dc', 'xmlns.com', 'dbpedia.org/ontology'
                ]):
                    ontology_uris.append(base_uri)
        
        return ontology_uris
    
    def _infer_domain_from_uri(self, ontology_uri: str) -> Optional[str]:
        """Infer biological domain from ontology URI for better OntoFetch performance"""
        
        domain_patterns = {
            'proteins': ['uniprot', 'pdb', 'pfam', 'interpro'],
            'chemicals': ['chebi', 'chembl', 'pubchem'],
            'pathways': ['wikipathways', 'reactome', 'kegg'],
            'biology': ['go', 'obo', 'bioschemas'],
            'general': ['schema.org', 'dc', 'dcterms', 'foaf']
        }
        
        uri_lower = ontology_uri.lower()
        for domain, patterns in domain_patterns.items():
            if any(pattern in uri_lower for pattern in patterns):
                return domain
        
        return None


# Global discovery engine instance
discovery_engine = OntologyDiscovery()


# Test function for development
async def test_ontology_discovery():
    """Test ontology discovery with various endpoints"""
    
    discovery = OntologyDiscovery(progress_format="human")
    
    test_endpoints = [
        ("wikidata", "auto"),
        ("wikipathways", "introspection"),
        ("https://query.wikidata.org/sparql", "documentation")
    ]
    
    for endpoint, method in test_endpoints:
        print(f"\n🔍 Testing {endpoint} with method '{method}'")
        print("=" * 50)
        
        try:
            schema = await discovery.discover_schema(endpoint, method)
            print(f"✅ Discovery successful!")
            print(f"📊 Found {len(schema.vocabularies)} vocabularies, {len(schema.classes)} classes, {len(schema.properties)} properties")
            print(f"⏱️ Discovery time: {schema.discovery_metadata.get('discovery_time_ms', 0)}ms")
            
        except Exception as e:
            print(f"❌ Discovery failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_ontology_discovery())