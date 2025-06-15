"""
Universal Core Tools - Following Claude Code patterns

Two essential tools following Claude Code composition patterns:
1. UniversalSparqlQuery - Like WebFetch: one tool, infinite compositions via context
2. EndpointDiscovery - Like WebSearch: structured capabilities, Claude interprets

Refactored from 4 over-engineered tools to 2 universal tools + AI reasoning.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from .client import UnifiedSparqlClient
# Removed static scaffolds - using dynamic pattern analysis instead

def generate_thinking_prompts_from_data(data: Any, context: Dict[str, Any]) -> Dict[str, str]:
    """Generate dynamic thinking prompts based on actual data patterns."""
    prompts = {}
    
    # Analyze data complexity and generate relevant thinking questions
    if isinstance(data, list) and len(data) > 0:
        if len(data) > 10:
            prompts["complexity_thinking"] = f"Found {len(data)} results - what does this volume suggest about query specificity and next steps?"
        elif len(data) == 1:
            prompts["precision_thinking"] = "Single result found - what does this precision suggest about query effectiveness and follow-up exploration?"
        
        # Analyze property patterns in first result
        if isinstance(data[0], dict) and "properties" in data[0]:
            prop_count = data[0].get("total_properties", 0)
            if prop_count > 50:
                prompts["density_thinking"] = f"{prop_count} properties detected - what does this density reveal about entity significance and research potential?"
            
            # Check for external references
            external_ids = data[0].get("properties", {}).get("external_ids", [])
            if len(external_ids) > 5:
                prompts["connectivity_thinking"] = f"{len(external_ids)} external database connections found - what cross-domain research opportunities does this connectivity suggest?"
    
    # Analyze execution patterns
    if context.get("execution_time_ms", 0) > 5000:
        prompts["performance_thinking"] = f"Query took {context['execution_time_ms']}ms - what does this timing suggest about data complexity and optimization opportunities?"
    
    return prompts

def detect_domain_signals_from_properties(properties: Dict[str, List]) -> Dict[str, str]:
    """Detect domain patterns from actual property data and generate domain-specific thinking prompts."""
    signals = {}
    
    # Analyze actual property names for domain signals
    all_props = []
    for category in properties.values():
        all_props.extend([p.get("property_id", "") for p in category])
    
    prop_text = " ".join(all_props).lower()
    
    if any(term in prop_text for term in ["sequence", "organism", "protein", "gene"]):
        signals["biological_domain"] = "Biological entity patterns detected - what molecular research methodologies should be applied here?"
    
    if any(term in prop_text for term in ["coordinates", "location", "country", "region"]):
        signals["geographic_domain"] = "Geographic entity patterns detected - what spatial analysis approaches are relevant?"
    
    if any(term in prop_text for term in ["industry", "company", "stock", "revenue"]):
        signals["business_domain"] = "Business entity patterns detected - what market analysis frameworks apply?"
    
    if any(term in prop_text for term in ["pathway", "ontology", "classification"]):
        signals["systems_domain"] = "Systems/pathway patterns detected - what network analysis approaches are appropriate?"
    
    return signals

class ToolResponse:
    """Standard response format following Claude Code patterns."""
    
    @staticmethod
    def success(data: Any, metadata: Optional[Dict] = None, suggestions: Optional[Dict] = None) -> str:
        """Create successful tool response."""
        if metadata is None:
            metadata = {}
        if suggestions is None:
            suggestions = {}
            
        return json.dumps({
            "success": True,
            "data": data,
            "metadata": {
                "execution_time_ms": metadata.get("execution_time_ms", 0),
                "cached": metadata.get("cached", False),
                "api_version": "2.0",
                **metadata
            },
            "suggestions": {
                "next_tools": suggestions.get("next_tools", []),
                "reasoning_patterns": suggestions.get("reasoning_patterns", []),
                **suggestions
            }
        }, indent=2)
    
    @staticmethod
    def error(code: str, message: str, suggestions: Optional[List[str]] = None) -> str:
        """Create error response with recovery suggestions."""
        return json.dumps({
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "suggestions": suggestions or []
            }
        }, indent=2)


class UniversalSparqlQuery:
    """
    Universal SPARQL tool following Claude Code WebFetch pattern.
    
    Like WebFetch: One general tool with infinite compositions via research_context.
    Context guides Claude's interpretation and reasoning about results.
    
    Research contexts trigger domain-specific AI reasoning:
    - "protein_function" → interprets UniProt data scientifically
    - "pathway_analysis" → connects genes to disease mechanisms  
    - "structure_search" → reasons about PDB availability
    - "cross_reference" → suggests follow-up database queries
    """
    
    def __init__(self, client: UnifiedSparqlClient):
        self.client = client
    
    async def query(
        self,
        query: str,
        endpoint: str = "wikidata", 
        research_context: str = "general",
        timeout: int = 30
    ) -> str:
        """
        Universal SPARQL query with AI-guided interpretation.
        
        Args:
            query: SPARQL query string
            endpoint: Target SPARQL endpoint
            research_context: Guides Claude's interpretation of results
            timeout: Query timeout in seconds
            
        Returns:
            Structured response with data + AI-guided context
        """
        start_time = time.time()
        
        # Basic validation
        if not query.strip():
            return ToolResponse.error(
                "EMPTY_QUERY",
                "SPARQL query cannot be empty",
                ["Provide a valid SPARQL query"]
            )
        
        # Auto-inject prefixes based on endpoint
        enhanced_query = self._enhance_query_with_prefixes(query, endpoint)
        
        try:
            # Execute query
            if endpoint == "wikidata" and "SELECT" in query.upper() and not enhanced_query.startswith("SELECT"):
                # Special handling for Wikidata entity search
                results = await self._execute_wikidata_search(query)
            else:
                results = await self.client.sparql_query(enhanced_query, endpoint, timeout)
            
            # Generate AI-guided context based on research_context
            ai_context = self._generate_research_context(results, research_context, endpoint)
            
            # Detect next steps based on results and context
            next_steps = self._suggest_next_research_steps(results, research_context, endpoint)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return ToolResponse.success(
                data=results,
                metadata={
                    "execution_time_ms": execution_time,
                    "endpoint": endpoint,
                    "research_context": research_context,
                    "query_type": self._detect_query_type(enhanced_query),
                    "result_count": self._count_results(results)
                },
                suggestions={
                    "ai_context": ai_context,
                    "next_research_steps": next_steps,
                    "reasoning_patterns": self._generate_reasoning_patterns(research_context)
                }
            )
            
        except Exception as e:
            return ToolResponse.error(
                "SPARQL_ERROR",
                f"Query failed: {str(e)}",
                [
                    "Check query syntax",
                    f"Verify {endpoint} endpoint is accessible",
                    "Try simpler query first",
                    f"Use endpoint_discover('{endpoint}') to check capabilities"
                ]
            )
    
    def _enhance_query_with_prefixes(self, query: str, endpoint: str) -> str:
        """Auto-inject common prefixes for endpoint if not present."""
        common_prefixes = {
            "wikidata": [
                "PREFIX wd: <http://www.wikidata.org/entity/>",
                "PREFIX wdt: <http://www.wikidata.org/prop/direct/>", 
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
                "PREFIX wikibase: <http://wikiba.se/ontology#>"
            ],
            "uniprot": [
                "PREFIX up: <http://purl.uniprot.org/core/>",
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
                "PREFIX taxon: <http://purl.uniprot.org/taxonomy/>"
            ],
            "wikipathways": [
                "PREFIX wp: <http://vocabularies.wikipathways.org/wp#>",
                "PREFIX dc: <http://purl.org/dc/elements/1.1/>",
                "PREFIX dcterms: <http://purl.org/dc/terms/>",
                "PREFIX foaf: <http://xmlns.com/foaf/0.1/>"
            ]
        }
        
        if endpoint in common_prefixes:
            existing_prefixes = set()
            for line in query.split('\n'):
                if line.strip().startswith('PREFIX'):
                    prefix_name = line.split(':')[0].replace('PREFIX', '').strip()
                    existing_prefixes.add(prefix_name)
            
            needed_prefixes = []
            for prefix_line in common_prefixes[endpoint]:
                prefix_name = prefix_line.split(':')[0].replace('PREFIX', '').strip()
                if prefix_name not in existing_prefixes:
                    needed_prefixes.append(prefix_line)
            
            if needed_prefixes:
                return '\n'.join(needed_prefixes) + '\n\n' + query
        
        return query
    
    async def _execute_wikidata_search(self, search_term: str) -> Dict[str, Any]:
        """Handle Wikidata entity search as special case."""
        return await self.client.search_entities(search_term.strip())
    
    def _generate_research_context(self, results: Dict[str, Any], context: str, endpoint: str) -> Dict[str, Any]:
        """Generate AI-guided research context based on results and research_context."""
        ai_context = {
            "domain_analysis": [],
            "data_interpretation": [],
            "research_opportunities": []
        }
        
        # Context-specific analysis
        if context == "protein_function":
            ai_context["domain_analysis"] = [
                "Analyzing protein data for functional insights",
                "Look for UniProt functional annotations, GO terms, pathways",
                "Consider structural constraints for membrane proteins"
            ]
        elif context == "pathway_analysis": 
            ai_context["domain_analysis"] = [
                "Analyzing pathway components and disease connections",
                "Look for gene-disease associations, protein interactions",
                "Consider systems-level effects and therapeutic targets"
            ]
        elif context == "structure_search":
            ai_context["domain_analysis"] = [
                "Searching for structural data and 3D information", 
                "Membrane proteins often lack PDB structures",
                "Look for domain information, models, and structural predictions"
            ]
        elif context == "cross_reference":
            ai_context["domain_analysis"] = [
                "Following database cross-references for data integration",
                "Map between identifier systems and databases",
                "Look for comprehensive entity profiles across resources"
            ]
        
        # Result-specific interpretation
        if isinstance(results, dict) and "results" in results:
            result_count = len(results.get("results", {}).get("bindings", []))
            if result_count == 0:
                ai_context["data_interpretation"] = ["No results found - consider broader search terms or different endpoint"]
            elif result_count == 1:
                ai_context["data_interpretation"] = ["Single precise result - good specificity, analyze in detail"]
            elif result_count > 50:
                ai_context["data_interpretation"] = ["Many results found - consider filtering or ranking by relevance"]
        
        return ai_context
    
    def _suggest_next_research_steps(self, results: Dict[str, Any], context: str, endpoint: str) -> List[str]:
        """Suggest logical next research steps based on results and context."""
        steps = []
        
        # If we found cross-references, suggest following them
        if self._has_cross_references(results):
            steps.append("Follow cross-references to other databases for comprehensive analysis")
        
        # Context-specific next steps
        if context == "protein_function" and endpoint == "wikidata":
            steps.append("Query UniProt for detailed functional information")
        elif context == "pathway_analysis" and endpoint == "wikipathways":
            steps.append("Query Wikidata for gene-disease associations")
        elif context == "structure_search":
            steps.append("Check PDB database or consider homology models")
            
        # Endpoint-specific opportunities
        if endpoint == "wikidata":
            steps.append("Explore related entities and properties")
        elif endpoint == "uniprot":
            steps.append("Check for pathway and interaction data")
        elif endpoint == "wikipathways":
            steps.append("Analyze pathway components and disease connections")
            
        return steps
    
    def _generate_reasoning_patterns(self, context: str) -> List[str]:
        """Generate reasoning patterns for Claude to consider."""
        patterns = {
            "protein_function": [
                "Protein → Function → Pathways → Disease",
                "Structure → Function relationships",
                "Cross-species conservation analysis"
            ],
            "pathway_analysis": [
                "Disease → Pathways → Targets → Drugs",
                "Gene → Protein → Pathway → Phenotype", 
                "Systems-level pathway crosstalk"
            ],
            "structure_search": [
                "Sequence → Structure → Function",
                "Domain architecture analysis",
                "Structural constraints on mutations"
            ],
            "cross_reference": [
                "Database integration workflows",
                "Identifier mapping strategies",
                "Multi-database evidence synthesis"
            ]
        }
        return patterns.get(context, ["Entity → Properties → Relationships → Insights"])
    
    def _detect_query_type(self, query: str) -> str:
        """Detect type of SPARQL query for metadata."""
        query_upper = query.upper()
        if "SELECT" in query_upper:
            return "select"
        elif "DESCRIBE" in query_upper:
            return "describe"
        elif "ASK" in query_upper:
            return "ask"
        elif "CONSTRUCT" in query_upper:
            return "construct"
        return "unknown"
    
    def _count_results(self, results: Dict[str, Any]) -> int:
        """Count results in SPARQL response."""
        if isinstance(results, dict):
            if "results" in results and "bindings" in results["results"]:
                return len(results["results"]["bindings"])
            elif isinstance(results, list):
                return len(results)
        return 0
    
    def _has_cross_references(self, results: Dict[str, Any]) -> bool:
        """Check if results contain cross-references to other databases."""
        # Simple heuristic - look for common database identifier patterns
        result_str = str(results).lower()
        return any(db in result_str for db in ["uniprot", "pdb", "pubmed", "chebi", "genbank"])


class EndpointDiscovery:
    """
    Universal endpoint discovery following Claude Code WebSearch pattern.
    
    Like WebSearch: Returns structured endpoint capabilities, Claude interprets.
    Discovery focus guides what Claude should reason about for research planning.
    
    Discovery focuses trigger different analysis:
    - "vocabulary" → find prefixes and classes for query building
    - "capabilities" → understand what research is possible  
    - "examples" → get query patterns for composition
    """
    
    def __init__(self, client: UnifiedSparqlClient):
        self.client = client
    
    async def discover(
        self,
        endpoint: str = "wikidata",
        discovery_focus: str = "comprehensive",
        cache_duration: int = 3600
    ) -> str:
        """
        Universal endpoint schema discovery with AI reasoning context.
        
        Args:
            endpoint: Target SPARQL endpoint to discover
            discovery_focus: Guides Claude's interpretation of capabilities
            cache_duration: How long to cache discovery results
            
        Returns:
            Structured capabilities with AI guidance for research planning
        """
        start_time = time.time()
        
        if endpoint not in self.client.ENDPOINTS:
            return ToolResponse.error(
                "UNKNOWN_ENDPOINT", 
                f"Unknown endpoint: {endpoint}",
                [f"Available endpoints: {', '.join(self.client.ENDPOINTS.keys())}"]
            )
        
        try:
            # Discover endpoint capabilities
            if endpoint == "wikidata":
                capabilities = await self._discover_wikidata_capabilities()
            else:
                capabilities = await self._discover_sparql_capabilities(endpoint)
            
            # Generate AI context based on discovery focus
            ai_guidance = self._generate_discovery_guidance(capabilities, discovery_focus, endpoint)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return ToolResponse.success(
                data=capabilities,
                metadata={
                    "execution_time_ms": execution_time,
                    "endpoint": endpoint,
                    "discovery_focus": discovery_focus,
                    "cached": False  # TODO: Implement caching
                },
                suggestions={
                    "ai_guidance": ai_guidance,
                    "query_examples": self._generate_example_queries(endpoint, discovery_focus),
                    "research_workflows": self._suggest_research_workflows(endpoint, capabilities)
                }
            )
            
        except Exception as e:
            return ToolResponse.error(
                "DISCOVERY_ERROR",
                f"Discovery failed: {str(e)}",
                [
                    "Check network connectivity",
                    f"Verify {endpoint} endpoint is accessible",
                    "Try with different discovery_focus"
                ]
            )
    
    async def _discover_wikidata_capabilities(self) -> Dict[str, Any]:
        """Discover Wikidata-specific capabilities."""
        return {
            "endpoint_type": "wikidata",
            "search_api": True,
            "common_prefixes": {
                "wd": "http://www.wikidata.org/entity/",
                "wdt": "http://www.wikidata.org/prop/direct/",
                "p": "http://www.wikidata.org/prop/",
                "ps": "http://www.wikidata.org/prop/statement/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "wikibase": "http://wikiba.se/ontology#"
            },
            "key_classes": [
                {"uri": "wd:Q5", "label": "human", "usage": "persons and individuals"},
                {"uri": "wd:Q8054", "label": "protein", "usage": "biological proteins"},
                {"uri": "wd:Q7187", "label": "gene", "usage": "genetic elements"},
                {"uri": "wd:Q12136", "label": "disease", "usage": "medical conditions"},
                {"uri": "wd:Q11173", "label": "chemical compound", "usage": "molecules and substances"}
            ],
            "key_properties": [
                {"uri": "wdt:P31", "label": "instance of", "usage": "classification"},
                {"uri": "wdt:P279", "label": "subclass of", "usage": "hierarchy"},
                {"uri": "wdt:P352", "label": "UniProt ID", "usage": "protein cross-reference"},
                {"uri": "wdt:P703", "label": "found in taxon", "usage": "species specification"},
                {"uri": "wdt:P688", "label": "encodes", "usage": "gene-protein relationships"}
            ],
            "research_domains": ["biology", "medicine", "chemistry", "geography", "general_knowledge"],
            "special_features": ["wikibase:label service", "federated queries", "entity search API"]
        }
    
    async def _discover_sparql_capabilities(self, endpoint: str) -> Dict[str, Any]:
        """Discover capabilities for general SPARQL endpoints."""
        capabilities = {
            "endpoint_type": endpoint,
            "search_api": False,
            "common_prefixes": {},
            "key_classes": [],
            "key_properties": [],
            "research_domains": [],
            "special_features": []
        }
        
        # Endpoint-specific configuration
        if endpoint == "uniprot":
            capabilities.update({
                "common_prefixes": {
                    "up": "http://purl.uniprot.org/core/",
                    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                    "taxon": "http://purl.uniprot.org/taxonomy/"
                },
                "research_domains": ["protein_function", "sequence_analysis", "structural_biology"],
                "special_features": ["protein sequences", "functional annotations", "GO terms"]
            })
        elif endpoint == "wikipathways":
            capabilities.update({
                "common_prefixes": {
                    "wp": "http://vocabularies.wikipathways.org/wp#",
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "dcterms": "http://purl.org/dc/terms/",
                    "foaf": "http://xmlns.com/foaf/0.1/"
                },
                "research_domains": ["pathway_analysis", "systems_biology", "disease_mechanisms"],
                "special_features": ["biological pathways", "gene networks", "species-specific data"]
            })
        
        return capabilities
    
    def _generate_discovery_guidance(self, capabilities: Dict[str, Any], focus: str, endpoint: str) -> Dict[str, Any]:
        """Generate AI guidance based on discovered capabilities and focus."""
        guidance = {
            "endpoint_strengths": [],
            "query_strategies": [],
            "research_opportunities": []
        }
        
        # Focus-specific guidance
        if focus == "vocabulary":
            guidance["query_strategies"] = [
                "Use discovered prefixes to build syntactically correct queries",
                "Leverage key classes and properties for effective filtering",
                "Follow naming conventions for better query success"
            ]
        elif focus == "capabilities":
            guidance["endpoint_strengths"] = [
                f"{endpoint} specializes in: {', '.join(capabilities.get('research_domains', []))}",
                f"Special features available: {', '.join(capabilities.get('special_features', []))}",
                f"Search API available: {capabilities.get('search_api', False)}"
            ]
        elif focus == "examples":
            guidance["query_strategies"] = [
                "Start with simple SELECT queries using key properties",
                "Use OPTIONAL clauses for properties that may not exist",
                "Apply LIMIT clauses to prevent large result sets"
            ]
        
        # Endpoint-specific opportunities
        if endpoint == "wikidata":
            guidance["research_opportunities"] = [
                "Cross-reference discovery using P352, P683, P637 properties",
                "Multi-domain entity exploration with federated queries",
                "Hierarchical classification analysis using P31/P279"
            ]
        elif endpoint == "uniprot":
            guidance["research_opportunities"] = [
                "Protein functional analysis with GO term integration",
                "Sequence-based research and homology studies",
                "Structural data discovery and domain analysis"
            ]
        elif endpoint == "wikipathways":
            guidance["research_opportunities"] = [
                "Pathway component analysis for disease research",
                "Gene regulatory network exploration",
                "Cross-species pathway comparison"
            ]
        
        return guidance
    
    def _generate_example_queries(self, endpoint: str, focus: str) -> List[str]:
        """Generate example queries based on endpoint and focus."""
        examples = []
        
        if endpoint == "wikidata":
            if focus in ["vocabulary", "comprehensive"]:
                examples.extend([
                    "SELECT ?protein ?proteinLabel WHERE { ?protein wdt:P31 wd:Q8054 } LIMIT 10",
                    "SELECT ?gene ?geneLabel ?organism WHERE { ?gene wdt:P31 wd:Q7187 ; wdt:P703 ?organism } LIMIT 5"
                ])
            if focus in ["capabilities", "comprehensive"]:
                examples.extend([
                    "SELECT ?item ?itemLabel ?uniprot WHERE { ?item wdt:P352 ?uniprot } LIMIT 10",
                    "ASK { wd:Q6715626 wdt:P31 wd:Q8054 }"
                ])
        elif endpoint == "uniprot":
            examples.extend([
                "SELECT ?protein ?organism WHERE { ?protein a up:Protein ; up:organism ?organism } LIMIT 5",
                "SELECT ?protein ?function WHERE { ?protein a up:Protein ; up:function ?function } LIMIT 5"
            ])
        elif endpoint == "wikipathways":
            examples.extend([
                "SELECT ?pathway ?title WHERE { ?pathway a wp:Pathway ; dc:title ?title } LIMIT 5",
                "SELECT ?gene ?pathway WHERE { ?gene dcterms:isPartOf ?pathway } LIMIT 10"
            ])
        
        return examples
    
    def _suggest_research_workflows(self, endpoint: str, capabilities: Dict[str, Any]) -> List[str]:
        """Suggest research workflows based on endpoint capabilities."""
        workflows = []
        
        research_domains = capabilities.get("research_domains", [])
        
        if "biology" in research_domains or "protein_function" in research_domains:
            workflows.append("Protein research: Discovery → Function → Pathways → Disease")
        if "pathway_analysis" in research_domains:
            workflows.append("Disease research: Disease → Pathways → Genes → Targets")
        if "chemistry" in research_domains:
            workflows.append("Drug discovery: Compound → Targets → Pathways → Effects")
        if "general_knowledge" in research_domains:
            workflows.append("Entity exploration: Search → Details → Relationships → Context")
        
        return workflows