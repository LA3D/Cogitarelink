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
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass
from urllib.parse import urlparse

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
class EndpointSchema:
    """Schema information for a SPARQL endpoint"""
    endpoint: str
    vocabularies: Dict[str, str]  # prefix -> namespace
    classes: Dict[str, Dict[str, Any]]  # class_uri -> metadata
    properties: Dict[str, Dict[str, Any]]  # property_uri -> metadata
    common_patterns: Dict[str, str]  # pattern_name -> sparql_template
    performance_hints: List[str]
    agent_guidance: List[str]
    discovery_metadata: Dict[str, Any]


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
        cache_duration: Optional[int] = None
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
                schema = await self._discover_auto(resolved_endpoint, tracker)
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
            
            # Add discovery metadata
            tracker.update_progress("Adding metadata", 0.95, "Finalizing schema")
            schema.discovery_metadata.update({
                "discovery_time_ms": int((time.time() - start_time) * 1000),
                "discovery_method": discovery_method,
                "cached_until": time.time() + (cache_duration or 3600)
            })
            
            # Cache result
            self.cache.set(cache_key, schema)
            
            # Complete progress tracking
            vocab_count = len(schema.vocabularies)
            class_count = len(schema.classes)
            prop_count = len(schema.properties)
            tracker.complete_operation(f"Found {vocab_count} vocabularies, {class_count} classes, {prop_count} properties")
            
            return schema
            
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
    
    async def _discover_auto(self, endpoint: str, tracker: Optional[ProgressTracker] = None) -> EndpointSchema:
        """Try multiple discovery methods in order of reliability with optional progress tracking"""
        
        # First try specialized endpoint discovery for known patterns
        try:
            # Check for OSM QLever endpoint - use specialized discovery with CoT patterns
            if "qlever.cs.uni-freiburg.de/api/osm" in endpoint or "osm-planet" in endpoint:
                if tracker:
                    tracker.update_progress("Using specialized OSM QLever discovery", 0.1, "Enhanced spatial intelligence patterns")
                schema = await self._discover_osm_qlever_specialized(endpoint)
                if self._is_schema_sufficient(schema):
                    schema.discovery_metadata["primary_method"] = "osm_qlever_specialized"
                    if tracker:
                        tracker.update_progress("Success with specialized OSM discovery", 0.9, "CoT patterns loaded")
                    return schema
            
            # Check for other known endpoints
            if tracker:
                tracker.update_progress("Checking known endpoint patterns", 0.15, "Looking for pre-configured schemas")
            known_schema = self._create_known_endpoint_schema(endpoint)
            if known_schema.discovery_metadata.get("method") == "known_patterns":
                if tracker:
                    tracker.update_progress("Success with known patterns", 0.9, "Schema from knowledge base")
                return known_schema
                
        except Exception as e:
            if tracker:
                tracker.update_progress("Specialized discovery failed", 0.2, f"Error: {str(e)[:50]}...")
            # Continue to standard discovery methods
        
        # Standard discovery methods - service description first per W3C SPARQL 1.1 spec
        methods = ["service_description", "void", "introspection", "documentation", "samples"]
        
        last_error = None
        for i, method in enumerate(methods):
            progress = 0.3 + (i * 0.15)  # Spread progress from 0.3 to 0.9
            if tracker:
                tracker.update_progress(f"Trying {method} discovery", progress, f"Method {i+1}/{len(methods)}")
            
            try:
                # Call the discovery method
                schema = await getattr(self, f"_discover_{method}")(endpoint)
                if self._is_schema_sufficient(schema):
                    schema.discovery_metadata["primary_method"] = method
                    if tracker:
                        tracker.update_progress(f"Success with {method}", 0.9, f"Schema discovered")
                    return schema
            except Exception as e:
                last_error = e
                if tracker:
                    tracker.update_progress(f"{method} failed", progress + 0.05, f"Error: {str(e)[:50]}...")
                continue
        
        # If all methods fail, create minimal schema
        if tracker:
            tracker.update_progress("All methods failed, creating minimal schema", 0.8, "Fallback mode")
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
    
    async def _discover_service_description(self, endpoint: str) -> EndpointSchema:
        """Discover schema through SPARQL 1.1 Service Description (W3C standard)"""
        
        try:
            # Request service description from SPARQL endpoint per W3C spec
            headers = {
                'User-Agent': 'Cogitarelink/1.0 (SPARQL Service Description Discovery)',
                'Accept': 'text/turtle, application/rdf+xml, application/n-triples'
            }
            
            req = urllib.request.Request(endpoint, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    service_desc_content = response.read().decode('utf-8')
                    return self._parse_service_description(endpoint, service_desc_content)
                else:
                    raise Exception(f"Service description request failed: HTTP {response.status}")
                    
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
                
                req = urllib.request.Request(void_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        void_content = response.read().decode('utf-8')
                        return self._parse_void_content(endpoint, void_content)
                        
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
        
        # Comprehensive documentation search strategy
        search_strategies = [
            # Direct documentation patterns
            self._try_direct_documentation_urls(base_domain),
            # Web search for ontology/vocabulary documentation  
            self._web_search_for_documentation(service_name, base_domain),
            # Known endpoint patterns
            self._create_known_endpoint_schema(endpoint)
        ]
        
        # Try each strategy until we get sufficient schema information
        for strategy in search_strategies:
            try:
                schema = await strategy
                if self._is_schema_sufficient(schema):
                    return schema
            except Exception as e:
                continue
        
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
        """Execute SPARQL query against endpoint"""
        
        encoded_query = urllib.parse.urlencode({
            'query': query,
            'format': 'application/sparql-results+json'
        })
        
        headers = {
            'User-Agent': 'Cogitarelink/1.0 (Schema Introspection)',
            'Accept': 'application/sparql-results+json'
        }
        
        req = urllib.request.Request(
            f"{endpoint}?{encoded_query}",
            headers=headers
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
            else:
                raise Exception(f"SPARQL query failed: HTTP {response.status}")
    
    def _parse_void_content(self, endpoint: str, void_content: str) -> EndpointSchema:
        """Parse VoID RDF content to extract schema information"""
        
        vocabularies = {}
        classes = {}
        properties = {}
        performance_hints = []
        agent_guidance = []
        
        # Parse VoID content using regex patterns (simplified but functional)
        import re
        
        # Extract dataset size information
        total_triples = 0
        graphs_info = []
        
        # Look for triple count patterns (including HTML format)
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
                
                req = urllib.request.Request(doc_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        doc_content = response.read().decode('utf-8')
                        
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
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    content = response.read().decode('utf-8')
                    
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