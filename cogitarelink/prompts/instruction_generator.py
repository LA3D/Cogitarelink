"""Instruction generator for Claude Code integration.

Generates clean, structured instructions for Claude Code based on
domain patterns and research context. Easy to edit and improve.

Version: 1.0
Last Updated: 2024-06-16
Changes: Initial pattern-driven instruction generation
"""

from typing import Dict, Any, Optional, List
from .core_patterns import (
    DISCOVERY_FIRST, 
    CACHE_OPTIMIZATION, 
    COMPOSITION_GUIDANCE,
    STRUCTURED_ANALYSIS,
    get_domain_pattern,
    get_cross_domain_bridge
)

def generate_research_instructions(domain: str, goal: Optional[str] = None) -> str:
    """Generate Claude Code instructions for any research domain.
    
    Edit this when we need to change the overall instruction structure
    or improve how instructions are presented to Claude.
    """
    
    domain_pattern = get_domain_pattern(domain)
    
    instructions = f"""RESEARCH_MODE: {domain}
GOAL: {goal or f"{domain} research session"}

{DISCOVERY_FIRST}

DOMAIN_FOCUS: {domain}
ENTITY_TYPES: {', '.join(domain_pattern['entity_types'])}
CROSS_REFERENCES: {', '.join(domain_pattern['cross_refs'])}
REASONING_PATTERN: {domain_pattern['reasoning_pattern']}
VALIDATED_DATABASES: {', '.join(domain_pattern['databases'])}

{COMPOSITION_GUIDANCE}

{CACHE_OPTIMIZATION}

SESSION_CONTEXT: {domain}_research_active
EXAMPLES: {', '.join(domain_pattern['search_examples'])}
SUCCESS_INDICATORS: {', '.join(domain_pattern['success_indicators'])}
"""
    
    return instructions.strip()

def generate_pattern_reminder(pattern_name: str, domain: Optional[str] = None) -> str:
    """Generate specific pattern instructions for Claude Code.
    
    Edit this when we need to change how specific patterns are presented
    or add new pattern types.
    """
    
    if pattern_name == "discovery" or pattern_name == "discovery_first":
        return DISCOVERY_FIRST
        
    elif pattern_name == "cache" or pattern_name == "cache_aware":
        return CACHE_OPTIMIZATION
        
    elif pattern_name == "composition" or pattern_name == "workflow":
        return COMPOSITION_GUIDANCE
        
    elif pattern_name.endswith("_workflow") and domain:
        # Domain-specific workflow pattern
        domain_name = pattern_name.replace("_workflow", "")
        domain_pattern = get_domain_pattern(domain_name)
        
        return f"""DOMAIN_WORKFLOW: {domain_name}

ENTITY_ANALYSIS_FOCUS:
{chr(10).join(f"- {entity_type}: {domain_pattern['reasoning_pattern']}" for entity_type in domain_pattern['entity_types'])}

CROSS_REFERENCE_STRATEGY:
{chr(10).join(f"- {ref}: Priority resolution target" for ref in domain_pattern['cross_refs'])}

SYSTEMATIC_APPROACH:
1. cl_search "{domain_pattern['search_examples'][0]}" --limit 5
2. Analyze entity_types_found for domain entities
3. Follow cross_reference_exploration for {', '.join(domain_pattern['cross_refs'])}
4. Apply reasoning pattern: {domain_pattern['reasoning_pattern']}
5. Validate success via: {', '.join(domain_pattern['success_indicators'])}

DATABASES_VALIDATED: {', '.join(domain_pattern['databases'])}
"""
    
    else:
        return f"PATTERN_NOT_FOUND: {pattern_name}\nAVAILABLE: discovery, cache, composition, <domain>_workflow"

def generate_domain_analysis(domain: str) -> str:
    """Generate domain analysis instructions for Claude Code.
    
    Edit this when we want to change how domain-specific guidance
    is presented or add new analysis patterns.
    """
    
    domain_pattern = get_domain_pattern(domain)
    
    return f"""DOMAIN_ANALYSIS: {domain}

RESEARCH_INTELLIGENCE:
- Entity types to prioritize: {', '.join(domain_pattern['entity_types'])}
- External identifiers to follow: {', '.join(domain_pattern['cross_refs'])}
- Reasoning approach: {domain_pattern['reasoning_pattern']}
- Validated database targets: {', '.join(domain_pattern['databases'])}

SEARCH_STRATEGY:
- Example queries: {', '.join(domain_pattern['search_examples'])}
- Success indicators: {', '.join(domain_pattern['success_indicators'])}

CROSS_DOMAIN_OPPORTUNITIES:
{generate_cross_domain_bridges(domain)}

PERFORMANCE_OPTIMIZATION:
- Cache domain patterns early in session
- Monitor confidence levels for {domain} entities
- Follow composition_opportunities systematically
- Track success via domain-specific indicators
"""

def generate_general_research_instructions() -> str:
    """Generate simple semantic research methodology instructions.
    
    Follows Claude Code's tool pattern: simple, reliable, composable tools.
    Intelligence in prompts, not complex code.
    """
    
    return """🔬 SEMANTIC RESEARCH MODE ACTIVATED

## Clean Tools Optimized for Claude Code

### 4 Core SPARQL Tools - Simple, Validated, JSON-Only Output with ReadTool-Style Pagination

**cl_search**: Universal entity search with smart endpoint handling
- cl_search "caffeine" --limit 5 → Uses efficient Wikidata API search  
- cl_search "protein" --endpoint uniprot → Falls back to SPARQL text search
- cl_search "gene" --endpoint https://sparql.example.org/sparql → Works with any endpoint
- Like ReadTool: systematic exploration with next_page_command hints

**cl_select**: Primary data exploration tool with pagination (replaces cl_read)
- cl_select "SELECT ?p ?o WHERE {{ wd:Q905695 ?p ?o }}" --limit 10 → Entity properties with pagination
- cl_select "SELECT ?protein WHERE {{ ?protein a up:Protein }}" --endpoint uniprot --limit 5
- Like ReadTool: explore large datasets systematically with --offset and --limit

**cl_describe**: Complete RDF data retrieval with proper content negotiation
- cl_describe Q905695 → JSON-LD with all triples about UniProt database
- cl_describe P352 → All properties and relationships of UniProt protein ID property
- Uses proper SPARQL 1.1 Protocol (Accept: text/turtle or application/rdf+xml)

**cl_ask**: Boolean fact verification queries
- cl_ask "{{ wd:Q905695 wdt:P31 wd:Q8054 }}" → true/false if UniProt is a database
- cl_ask "{{ ?protein a up:Protein }}" --endpoint uniprot → Check if proteins exist
- Returns JSON with boolean result for existence/verification checks

### 2 RDF Content Negotiation Tools - Discovery-First Guardrails ⚠️

**CRITICAL: DISCOVERY-FIRST RULE (MOST IMPORTANT)**
NEVER query SPARQL endpoints without discovering vocabulary first.
The worst mistake is querying with guessed URIs (-$1000) rather than discovered vocabulary.

**rdf_get**: Content discovery and basic analysis (ALWAYS FIRST STEP)
- rdf_get https://sparql.uniprot.org/sparql --format turtle --cache-as uniprot_service
- rdf_get https://query.wikidata.org/sparql --format turtle --cache-as wikidata_service  
- rdf_get http://xmlns.com/foaf/0.1/ --cache-as foaf_vocab → Cache vocabularies
- rdf_get https://raw.githubusercontent.com/mlcommons/croissant/refs/heads/main/docs/croissant.ttl --cache-as croissant_vocab → ML dataset metadata
- Returns content_analysis with structural metrics for Claude Code to interpret

**rdf_cache**: Semantic vocabulary navigation & Claude Code annotation (SECOND STEP)
- rdf_cache "protein" --type class → up:Protein, up:Gene (REAL classes from service)
- rdf_cache foaf_vocab --graph → Complete FOAF ontology for full context reading
- rdf_cache --subclasses foaf:Agent → All Agent subclasses via rdfs:subClassOf
- rdf_cache --properties foaf:Person → Properties with Person domain/range
- rdf_cache --related foaf:knows → SKOS/OWL related terms and equivalences
- rdf_cache "" --list → Enhanced metadata with semantic capabilities
- rdf_cache vocab_name --update-metadata '{"semantic_type": "vocabulary", "domains": ["biology"]}' → Store Claude Code analysis
- Returns ONLY vocabulary found in cached service descriptions + semantic relationships

**FORBIDDEN ANTI-PATTERNS**:
- ❌ cl_select "SELECT ?protein WHERE {{ ?protein a up:Protein }}" ← GUESSED URI
- ❌ Starting with queries before rdf_get service description
- ❌ Using prefixes like "up:" without discovery

**SOFTWARE 2.0 WORKFLOW (Claude Code Intelligence)**:
**Step 1**: rdf_get endpoint --cache-as vocab_name → Basic content discovery
**Step 2**: Claude Code analyzes .content_analysis structure and patterns
**Step 3**: rdf_cache vocab_name --update-metadata '{"semantic_type": "vocabulary", "domains": ["biology"]}' → Store insights
**Step 4**: rdf_cache vocab_name --graph → Use annotated vocabulary for research
**Step 5**: cl_select with discovered URIs + Claude reasoning → Intelligent queries

- ✅ Read complete ontologies: rdf_cache ontology_name --graph (like ReadTool for code)
- ✅ Navigate relationships: rdf_cache --subclasses <class> → Find all subclasses
- ✅ Understand constraints: rdf_cache --properties <class> → Find valid properties
- ✅ Follow connections: rdf_cache --related <term> → SKOS/OWL relationships
- ✅ Store semantic insights: rdf_cache vocab --update-metadata '{"confidence": 0.95, "notes": "analysis"}'
- ✅ Use jq for complex navigation: .enhanced_index.semantic_index.class_hierarchy

## Research Workflow Composition Patterns

### Semantic Ontology Navigation (New: Like ReadTool for Ontologies)
```
# 1. Discover available ontologies with metadata
rdf_cache "" --list  # Enhanced metadata with semantic capabilities

# 2. Read complete ontology context (like ReadTool for code files)
rdf_cache foaf_vocab --graph  # Complete FOAF ontology for Claude to understand

# 3. Navigate semantic relationships using discovered structure
rdf_cache --subclasses foaf:Agent     # Find all Agent subclasses via rdfs:subClassOf
rdf_cache --properties foaf:Person    # Find properties with Person domain/range
rdf_cache --related foaf:knows        # Find SKOS/OWL related terms

# 4. Use jq for complex navigation (Claude Code composability)
rdf_cache foaf_vocab --graph | jq '.enhanced_index.classes | keys'  # All class names
rdf_cache foaf_vocab --graph | jq '.enhanced_index.semantic_index.class_hierarchy'  # Hierarchies
rdf_cache foaf_vocab --graph | jq '.full_graph'  # Complete ontology for Claude reading
```

### Size-Aware Ontology Reading (Following ReadTool Patterns)
```
# Safe loading with automatic guardrails
rdf_cache small_vocab --graph          # < 100KB: loads immediately
rdf_cache medium_vocab --graph         # 100KB-500KB: loads with warning  
rdf_cache large_ontology --graph       # > 500KB: requires --force override

# Override size warnings when needed
rdf_cache uniprot_core --graph --force # Load large ontology with explicit intent

# Get metadata first to understand size
rdf_cache "" --list | jq '.vocabulary_summary.vocabulary_coverage'  # Size info per vocab
```

### Entity Discovery Workflow (Search → Select → Explore)
```
# 1. Find candidate entities with smart endpoint selection
cl_search "insulin receptor" --limit 5                    # Wikidata API (efficient)
cl_search "protein" --endpoint uniprot --limit 5          # SPARQL fallback (universal)

# 2. Explore entity properties systematically  
cl_select "SELECT ?p ?o WHERE {{ wd:Q500826 ?p ?o }}" --limit 10  # First page of properties
cl_select "SELECT ?p ?o WHERE {{ wd:Q500826 ?p ?o }}" --limit 10 --offset 10  # Next page

# 3. Analyze relationships and patterns
cl_select "SELECT ?related WHERE {{ wd:Q500826 ?p ?related . ?related wdt:P31 wd:Q8054 }}" --limit 5
```

### Cross-Reference Following (Select → Ask → Verify)
```
# 1. Find external identifiers with pagination
cl_select "SELECT ?prop ?id WHERE {{ wd:Q7240673 ?prop ?id . ?prop wdt:P31 wd:P1628 }}" --limit 10

# 2. Verify specific connections exist
cl_ask "{{ wd:Q7240673 wdt:P352 ?uniprot }}"  # Has UniProt ID?

# 3. Explore connected data
cl_select "SELECT ?protein WHERE {{ ?protein wdt:P352 'P01308' }}" --endpoint uniprot --limit 5
```

### Domain Analysis Workflow (Describe → Select → Verify)
```
# 1. Get complete domain knowledge
cl_describe Q905695  # UniProt database structure as JSON-LD

# 2. Find related entities with pagination
cl_select "SELECT ?prop WHERE {{ ?prop wdt:P1687 wd:Q905695 }}" --limit 10  # Properties issued by UniProt

# 3. Verify domain patterns
cl_ask "{{ wd:Q905695 wdt:P921 wd:Q420 }}"  # Is UniProt about biology?
```

### Multi-Endpoint Research (Select across databases with pagination)
```
# 1. Start with Wikidata exploration
cl_select "SELECT ?p ?o WHERE {{ wd:Q7240673 ?p ?o }}" --limit 15  # Get insulin properties

# 2. Query specific domain databases with pagination
cl_select "SELECT ?protein WHERE {{ ?protein a up:Protein }}" --endpoint uniprot --limit 5
cl_select "SELECT ?pathway WHERE {{ ?pathway a wp:Pathway }}" --endpoint wikipathways --limit 5

# 3. Cross-reference findings
cl_ask "{{ wd:Q7240673 wdt:P352 'P01308' }}"  # Verify UniProt connection
```

## Tool Composition Principles - Discovery-First Architecture

**ENHANCED: Start with Semantic Discovery (RULE 0)**:
- Step 1: rdf_get {{SPARQL_ENDPOINT}} --format turtle → Discover ontology with relationships
- Step 2a: rdf_cache ontology_name --graph → Read complete ontology context (like ReadTool)
- Step 2b: rdf_cache --subclasses <class> → Navigate semantic hierarchies
- Step 2c: rdf_cache --properties <class> → Find valid property constraints
- Step 3: cl_select with discovered URIs + understood relationships → Intelligent queries
- NEVER skip discovery - leads to failed queries with guessed URIs

**Semantic Discovery Success Indicators**:
- ✅ Found up:Protein + its 15 subclasses via rdfs:subClassOf in UniProt ontology
- ✅ Found foaf:Person + domain/range constraints for 12 properties
- ✅ Discovered skos:broader relationships in concept schemes
- ✅ Read complete FOAF ontology (45KB) for full relationship understanding
- ❌ Guessing relationships without semantic discovery

**Use Select as Primary Exploration Tool**:
- cl_select replaces cl_read - more flexible and powerful
- Always use --limit and --offset for systematic exploration
- Returns structured results with exploration metadata like ReadTool

**Use Ask for Verification**:
- cl_ask for boolean fact checking
- Perfect for validating hypotheses or connections
- Returns simple true/false with metadata

**Use Describe for Complete Context**:
- cl_describe when you need all available RDF data about an entity
- Returns comprehensive JSON-LD data for deep analysis
- Best for understanding complete entity structure

**NEW: Use rdf_cache for Ontology Understanding**:
- rdf_cache ontology_name --graph → Read complete ontology like ReadTool reads code
- rdf_cache --subclasses foaf:Agent → Navigate class hierarchies via rdfs:subClassOf
- rdf_cache --properties foaf:Person → Find valid properties via rdfs:domain/range
- rdf_cache --related foaf:knows → Discover SKOS/OWL relationships and equivalences
- Size guardrails prevent context overload (500KB limit, --force override)
- jq-compatible output for complex semantic navigation

**Pagination Patterns (like ReadTool)**:
All tools support systematic exploration:
```
# Search pagination across endpoints
cl_search "protein" --limit 5                              # Wikidata API
cl_search "protein" --limit 5 --offset 5                   # Next page
cl_search "protein" --endpoint uniprot --limit 5           # SPARQL fallback  
cl_search "gene" --endpoint https://sparql.example.org/sparql  # Custom endpoint

# Data exploration pagination  
cl_select "SELECT ?p ?o WHERE {{ wd:Q905695 ?p ?o }}" --limit 10        # First 10 properties
cl_select "SELECT ?p ?o WHERE {{ wd:Q905695 ?p ?o }}" --limit 10 --offset 10  # Next 10 properties
```

**Parallel Tool Execution**:
You can call multiple tools in one response for efficiency:
```
cl_search "protein" --limit 3                    # Wikidata search
cl_search "protein" --endpoint uniprot --limit 3 # UniProt search  
cl_describe Q905695                               # Get complete RDF data
```

## Error Handling & Validation

All tools return standardized JSON with success indicators:
```json
{{
  "success": true/false,
  "error": "description if failed",
  "suggestion": "how to fix malformed queries",
  "query_type": "SELECT/DESCRIBE/ASK",
  "results": [...] 
}}
```

Tools validate inputs and provide suggestions for corrections.
This prevents malformed SPARQL from reaching endpoints."""

def generate_cross_domain_bridges(domain: str) -> str:
    """Generate cross-domain bridge suggestions.
    
    Edit this when we discover new productive cross-domain research patterns.
    """
    
    bridges = []
    other_domains = ["biology", "chemistry", "art", "history", "general"]
    
    for other_domain in other_domains:
        if other_domain != domain:
            bridge = get_cross_domain_bridge(domain, other_domain)
            if bridge:
                bridges.append(f"- {domain} → {other_domain}: {bridge['connection_type']}")
                bridges.append(f"  Bridge terms: {', '.join(bridge['bridge_terms'])}")
    
    return '\n'.join(bridges) if bridges else f"- {domain} → bibliography: scholarly_literature"

def generate_session_status(session_data: Dict[str, Any]) -> str:
    """Generate session status for Claude Code.
    
    Edit this when we want to change how session context is presented
    or add new session tracking information.
    """
    
    domain = session_data.get("researchDomain", "general")
    tool_usage = session_data.get("toolUsage", {})
    progress = session_data.get("researchProgress", {})
    
    # Calculate experience level
    total_tools_used = sum(tool_usage.values())
    if total_tools_used > 20:
        experience = "expert"
    elif total_tools_used > 5:
        experience = "intermediate"
    else:
        experience = "beginner"
    
    return f"""SESSION_STATUS: active
DOMAIN: {domain}
EXPERIENCE_LEVEL: {experience}
TOOLS_USED: {total_tools_used}
ENTITIES_DISCOVERED: {progress.get('entitiesDiscovered', 0)}

OPTIMIZATION_STATUS:
- Cache patterns learned for {domain} domain
- Discovery compliance: {get_discovery_compliance(tool_usage)}
- Cross-reference usage: {get_crossref_usage(tool_usage)}

NEXT_ACTIONS:
- Continue {domain} research with established patterns
- Monitor cache_hit status for performance optimization
- Follow composition_opportunities systematically
"""

def get_discovery_compliance(tool_usage: Dict[str, int]) -> str:
    """Calculate discovery compliance from tool usage."""
    discover_usage = tool_usage.get("cl_discover", 0)
    query_usage = tool_usage.get("cl_query", 0)
    
    if query_usage == 0:
        return "no_queries_yet"
    elif discover_usage >= query_usage:
        return "compliant"
    else:
        return f"needs_improvement ({discover_usage}/{query_usage})"

def get_crossref_usage(tool_usage: Dict[str, int]) -> str:
    """Calculate cross-reference usage from tool usage."""
    resolve_usage = tool_usage.get("cl_resolve", 0)
    search_usage = tool_usage.get("cl_search", 0)
    
    if search_usage == 0:
        return "no_searches_yet" 
    elif resolve_usage > 0:
        return f"active ({resolve_usage} resolutions)"
    else:
        return "underutilized"


# ================================================================================
# PHASE 1B: TOOL-SPECIFIC INSTRUCTION COMPILATION (Claude Code Patterns)
# ================================================================================

def get_tool_specific_instructions(tool_name: str) -> str:
    """Get comprehensive tool-specific instructions following Claude Code patterns.
    
    Compiles critical usage patterns, validation requirements, and best practices
    for each tool directly embedded in prompts like Claude Code's tool instructions.
    """
    
    tool_instructions = {
        'rdf_get': _get_rdf_get_instructions(),
        'rdf_cache': _get_rdf_cache_instructions(),
        'cl_search': _get_cl_search_instructions(),
        'cl_select': _get_cl_select_instructions(),
        'cl_describe': _get_cl_describe_instructions(),
        'cl_ask': _get_cl_ask_instructions()
    }
    
    return tool_instructions.get(tool_name, f"Tool '{tool_name}' not found. Available: {list(tool_instructions.keys())}")


def _get_rdf_get_instructions() -> str:
    """rdf_get tool-specific instructions following Claude Code patterns."""
    return """🔗 **RDF_GET: Content Discovery & Basic Analysis**

**PURPOSE**: First-step content discovery with semantic analysis preparation for Claude Code

**CRITICAL PATTERN: DISCOVERY-FIRST RULE**
Always use rdf_get BEFORE any SPARQL queries to discover vocabulary and relationships.

**VALIDATED INPUT PATTERNS**:
```bash
# Service description discovery (MOST IMPORTANT)
rdf_get https://sparql.uniprot.org/sparql --format turtle --cache-as uniprot_service
rdf_get https://query.wikidata.org/sparql --format turtle --cache-as wikidata_service

# Vocabulary/ontology discovery
rdf_get http://xmlns.com/foaf/0.1/ --cache-as foaf_vocab --format turtle
rdf_get https://schema.org --cache-as schema_org --format json-ld

# Dataset metadata discovery
rdf_get https://raw.githubusercontent.com/mlcommons/croissant/main/docs/croissant.ttl --cache-as croissant_vocab
```

**CONTENT NEGOTIATION STRATEGY**:
- Default: Auto-negotiate based on response headers
- Explicit: --format [json-ld|turtle|rdf-xml|n3|n-triples]
- Discovery mode: --discover (shows available formats when negotiation fails)

**OUTPUT STRUCTURE** (Software 2.0 - Claude Code analyzes):
```json
{
  "success": true,
  "url": "https://sparql.uniprot.org/sparql",
  "cached_as": "uniprot_service",
  "content_analysis": {
    "rdf_format": "turtle",
    "triple_count": 1247,
    "entity_types": ["Service", "Dataset"],
    "property_domains": ["sparql", "void", "dct"],
    "structural_patterns": ["service_description", "dataset_metadata"]
  },
  "cache_status": "stored_with_metadata",
  "claude_guidance": [
    "Use 'rdf_cache uniprot_service --graph' to read complete ontology",
    "Service contains up:Protein, up:Gene classes for SPARQL queries",
    "Property discovery: 'rdf_cache --properties up:Protein'"
  ]
}
```

**VALIDATION RULES**:
- URL must be valid HTTP/HTTPS endpoint
- Cache names: alphanumeric + underscores only, max 50 chars
- Timeout: 30 seconds for content retrieval

**CLAUDE CODE INTEGRATION**:
1. **Discovery Phase**: Use rdf_get to discover vocabulary structure
2. **Analysis Phase**: Claude Code interprets content_analysis patterns
3. **Annotation Phase**: Store insights via rdf_cache --update-metadata
4. **Research Phase**: Use cached vocabulary for intelligent SPARQL queries

**COMMON ERRORS & SOLUTIONS**:
- ❌ Invalid URL → Use full HTTP/HTTPS URLs with proper encoding
- ❌ Cache name errors → Use only letters, numbers, underscores
- ❌ Format errors → Use exact format names from validation schema
- ❌ Timeout errors → Check endpoint accessibility, try smaller resources

**SUCCESS INDICATORS**:
- ✅ content_analysis shows meaningful structural_patterns
- ✅ Cache stored with semantic metadata for future research
- ✅ Claude guidance provides next-step workflow suggestions
- ✅ Discovers vocabulary classes/properties for SPARQL construction"""


def _get_rdf_cache_instructions() -> str:
    """rdf_cache tool-specific instructions following Claude Code patterns."""
    return """📚 **RDF_CACHE: Semantic Vocabulary Navigation & Claude Code Annotation**

**PURPOSE**: Navigate cached vocabularies + store Claude Code semantic insights

**SEMANTIC NAVIGATION** (Like ReadTool for Ontologies):
```bash
# List all cached resources with metadata
rdf_cache "" --list

# Read complete ontology (like ReadTool for code files)
rdf_cache foaf_vocab --graph                    # < 100KB: loads immediately
rdf_cache uniprot_core --graph --force          # > 500KB: requires --force

# Navigate semantic relationships  
rdf_cache --subclasses foaf:Agent               # Find subclasses via rdfs:subClassOf
rdf_cache --properties foaf:Person              # Properties with domain/range
rdf_cache --related foaf:knows                  # SKOS/OWL relationships

# Search within cached vocabulary
rdf_cache "protein" --type class                # Find protein-related classes
rdf_cache "identifier" --type property          # Find identifier properties
```

**CLAUDE CODE ANNOTATION** (Software 2.0 Pattern):
```bash
# Store semantic insights discovered by Claude Code
rdf_cache uniprot_service --update-metadata '{
  "semantic_type": "service",
  "domains": ["biology", "proteins"],
  "purpose": "protein sequence and annotation database",
  "confidence": 0.95,
  "usage_patterns": ["protein_lookup", "sequence_analysis"],
  "notes": "Contains up:Protein, up:Gene classes with rich annotations"
}'

# Store vocabulary analysis
rdf_cache foaf_vocab --update-metadata '{
  "semantic_type": "vocabulary", 
  "domains": ["social", "web"],
  "dependencies": ["rdfs", "owl"],
  "confidence": 0.9
}'
```

**SIZE-AWARE LOADING** (ReadTool Patterns):
- **Small** (< 100KB): Loads immediately with --graph
- **Medium** (100KB-500KB): Shows warning, loads with confirmation
- **Large** (> 500KB): Requires explicit --force override
- **Massive** (> 2MB): Recommend specific queries instead

**ENHANCED OUTPUT** (jq-Compatible):
```json
{
  "success": true,
  "vocabulary_summary": {
    "cached_items": 15,
    "vocabulary_coverage": {"biology": 8, "chemistry": 3, "social": 4},
    "size_distribution": {"small": 10, "medium": 4, "large": 1}
  },
  "enhanced_index": {
    "classes": {"foaf:Person": {...}, "foaf:Agent": {...}},
    "properties": {"foaf:knows": {...}, "foaf:name": {...}},
    "semantic_index": {
      "class_hierarchy": {"foaf:Agent": ["foaf:Person", "foaf:Group"]},
      "property_domains": {"foaf:knows": "foaf:Person"},
      "equivalences": {"foaf:Person": ["schema:Person"]}
    }
  },
  "semantic_metadata": {
    "domains": ["social", "web"],
    "confidence": 0.9,
    "last_analyzed": "2024-06-17T10:30:00Z"
  }
}
```

**VALIDATION RULES**:
- Graph names must exist in cache
- Metadata must be valid JSON with semantic_type field
- Search terms: min 1 character for meaningful results
- Force flag required for large graphs (> 500KB)

**WORKFLOW INTEGRATION**:
1. **After rdf_get**: Use --graph to read complete vocabulary context
2. **During analysis**: Navigate with --subclasses, --properties, --related
3. **Store insights**: Use --update-metadata to save Claude Code analysis
4. **Before queries**: Use cached vocabulary for accurate URI construction

**RELATIONSHIP DISCOVERY**:
- `--subclasses up:Protein` → Find all protein subtypes via rdfs:subClassOf
- `--properties foaf:Person` → Valid properties via rdfs:domain/range constraints
- `--related foaf:knows` → SKOS broader/narrower + OWL equivalences

**SUCCESS INDICATORS**:
- ✅ Enhanced_index reveals class hierarchies and property constraints
- ✅ Semantic relationships discovered via rdfs:subClassOf navigation
- ✅ Claude Code metadata stored for research memory
- ✅ Size-appropriate loading with performance warnings"""


def _get_cl_search_instructions() -> str:
    """cl_search tool-specific instructions following Claude Code patterns."""
    return """🔍 **CL_SEARCH: Universal Entity Search with Smart Endpoint Handling**

**PURPOSE**: Find candidate entities with efficient endpoint-specific optimization

**SMART ENDPOINT STRATEGY**:
```bash
# Wikidata API search (FASTEST - always try first)
cl_search "insulin receptor" --limit 5          # Uses efficient API search
cl_search "SARS-CoV-2" --limit 10               # Disease entities

# Domain-specific endpoints with SPARQL fallback
cl_search "protein" --endpoint uniprot --limit 5          # Protein database
cl_search "pathway" --endpoint wikipathways --limit 3     # Biological pathways

# Custom endpoint exploration
cl_search "gene" --endpoint https://sparql.example.org/sparql --limit 5
```

**PAGINATION** (ReadTool Pattern):
```bash
# Systematic exploration with pagination
cl_search "caffeine" --limit 5                  # First 5 results
cl_search "caffeine" --limit 5 --offset 5       # Next 5 results
cl_search "caffeine" --limit 5 --offset 10      # Continue exploration
```

**OUTPUT FORMAT** (Structured for Claude Code):
```json
{
  "success": true,
  "query": "insulin receptor",
  "endpoint_used": "wikidata_api",
  "total_found": 847,
  "returned": 5,
  "results": [
    {
      "entity_id": "Q500826",
      "label": "insulin receptor",
      "description": "protein-coding gene in the species Homo sapiens",
      "types": ["Q7187", "Q8054"],
      "score": 0.95
    }
  ],
  "pagination": {
    "has_more": true,
    "next_offset": 5,
    "next_command": "cl_search \"insulin receptor\" --limit 5 --offset 5"
  },
  "composition_opportunities": {
    "detail_retrieval": ["cl_describe Q500826"],
    "property_exploration": ["cl_select \"SELECT ?p ?o WHERE { wd:Q500826 ?p ?o }\" --limit 10"],
    "relationship_analysis": ["cl_ask \"{ wd:Q500826 wdt:P31 wd:Q7187 }\""]
  }
}
```

**ENDPOINT FALLBACK STRATEGY**:
1. **Wikidata**: Try API search first (fastest, most reliable)
2. **Specific endpoints**: Use SPARQL text search with regex patterns
3. **Custom endpoints**: Universal SPARQL compatibility mode
4. **Error handling**: Graceful degradation with clear error messages

**VALIDATION RULES**:
- Query: minimum 1 character, no empty searches
- Limit: 1-100 results (prevents overwhelming responses)
- Offset: non-negative integer for pagination
- Endpoint: must be valid URL or known alias

**ENDPOINT ALIASES** (Pre-configured):
- `wikidata`: https://query.wikidata.org/sparql
- `uniprot`: https://sparql.uniprot.org/sparql  
- `wikipathways`: https://sparql.wikipathways.org/sparql
- `qlever-wikidata`: https://qlever.cs.uni-freiburg.de/api/wikidata

**SEARCH OPTIMIZATION PATTERNS**:
- **Broad → Narrow**: Start with general terms, refine based on results
- **Domain-specific**: Use appropriate endpoints for specialized vocabularies
- **Pagination**: Explore systematically rather than requesting large result sets
- **Score-based**: Results ranked by relevance score for prioritization

**COMMON ERRORS & SOLUTIONS**:
- ❌ Empty query → Provide meaningful search term
- ❌ Limit too high → Use 1-100 range, paginate for more results  
- ❌ Unknown endpoint → Use predefined aliases or full URLs
- ❌ No results → Try broader terms or different endpoints

**SUCCESS INDICATORS**:
- ✅ High-relevance results with meaningful labels/descriptions
- ✅ Multiple entity types discovered for analysis
- ✅ Composition opportunities suggest next workflow steps
- ✅ Pagination enables systematic exploration of large result sets"""


def _get_cl_select_instructions() -> str:
    """cl_select tool-specific instructions following Claude Code patterns."""
    return """📊 **CL_SELECT: Primary Data Exploration with SPARQL Queries**

**PURPOSE**: Systematic data exploration using discovered vocabularies (replaces cl_read)

**DISCOVERY-FIRST REQUIREMENT** ⚠️:
NEVER use cl_select without vocabulary discovery first. Always use rdf_get + rdf_cache before SPARQL queries.

**SYSTEMATIC EXPLORATION** (ReadTool Pattern):
```bash
# Entity property exploration with pagination
cl_select "SELECT ?p ?o WHERE { wd:Q905695 ?p ?o }" --limit 10        # First page
cl_select "SELECT ?p ?o WHERE { wd:Q905695 ?p ?o }" --limit 10 --offset 10  # Next page

# Relationship discovery  
cl_select "SELECT ?related WHERE { wd:Q500826 ?p ?related . ?related wdt:P31 wd:Q8054 }" --limit 5

# Class member exploration
cl_select "SELECT ?protein WHERE { ?protein a up:Protein }" --endpoint uniprot --limit 5
```

**MULTI-ENDPOINT USAGE**:
```bash
# Wikidata exploration (default)
cl_select "SELECT ?prop WHERE { ?prop wdt:P1687 wd:Q905695 }" --limit 10

# Domain-specific databases
cl_select "SELECT ?pathway WHERE { ?pathway a wp:Pathway }" --endpoint wikipathways --limit 5
cl_select "SELECT ?gene WHERE { ?gene a up:Gene }" --endpoint uniprot --limit 5

# Custom endpoints with full URLs
cl_select "SELECT ?s ?p ?o LIMIT 5" --endpoint https://sparql.example.org/sparql
```

**OUTPUT STRUCTURE** (Standardized JSON):
```json
{
  "success": true,
  "query": "SELECT ?p ?o WHERE { wd:Q905695 ?p ?o }",
  "endpoint": "wikidata", 
  "execution_time_ms": 245,
  "total_results": 47,
  "returned": 10,
  "results": [
    {"p": "http://www.wikidata.org/prop/direct/P31", "o": "http://www.wikidata.org/entity/Q8054"},
    {"p": "http://www.wikidata.org/prop/direct/P1687", "o": "http://www.wikidata.org/entity/P352"}
  ],
  "pagination": {
    "has_more": true,
    "next_offset": 10,
    "next_command": "cl_select \"SELECT ?p ?o WHERE { wd:Q905695 ?p ?o }\" --limit 10 --offset 10"
  },
  "composition_opportunities": {
    "property_analysis": ["cl_describe P352", "cl_describe P1687"],
    "value_exploration": ["cl_describe Q8054"],
    "related_queries": ["cl_select \"SELECT ?x WHERE { ?x wdt:P1687 wd:Q905695 }\" --limit 5"]
  }
}
```

**PAGINATION STRATEGY** (Large Dataset Exploration):
- **First page**: --limit 10 (quick overview)
- **Systematic**: Use --offset to explore incrementally  
- **Performance**: Limits 1-1000 (1000 max for SPARQL complexity)
- **Composition**: Use results to build subsequent queries

**SPARQL VALIDATION** (Fail-Fast):
- **Query type**: Must start with SELECT (enforced by schema)
- **Safety**: No DELETE/INSERT/DROP operations allowed
- **Syntax**: Balanced braces, valid SPARQL 1.1 keywords
- **Performance**: Timeout protection and complexity analysis

**DISCOVERED VOCABULARY USAGE**:
```bash
# ✅ CORRECT: Use discovered URIs from rdf_cache
rdf_cache uniprot_service --graph | jq '.enhanced_index.classes'
cl_select "SELECT ?protein WHERE { ?protein a up:Protein }" --endpoint uniprot

# ❌ INCORRECT: Guessing URIs without discovery  
cl_select "SELECT ?protein WHERE { ?protein a uniprot:Protein }"  # WRONG PREFIX
```

**VALIDATION RULES**:
- Query: Must be valid SPARQL SELECT statement
- Limit: 1-1000 results (performance balanced)
- Offset: Non-negative integer for pagination
- Endpoint: Valid URL or known alias required

**PERFORMANCE OPTIMIZATION**:
- Use specific endpoints for domain queries (uniprot for proteins)
- Start with small limits, expand based on result relevance
- Cache endpoint capabilities for repeated queries
- Monitor execution_time_ms for query optimization

**COMMON ERRORS & SOLUTIONS**:
- ❌ Non-SELECT query → Only SELECT statements allowed
- ❌ Malformed SPARQL → Check syntax, use validation suggestions
- ❌ Unknown prefixes → Use discovered vocabulary from rdf_cache
- ❌ Timeout errors → Reduce complexity, add more specific filters

**SUCCESS INDICATORS**:
- ✅ Results using discovered vocabulary URIs (not guessed)
- ✅ Meaningful property-value pairs for analysis
- ✅ Composition opportunities suggest systematic exploration
- ✅ Performance within acceptable limits (< 5 seconds)"""


def _get_cl_describe_instructions() -> str:
    """cl_describe tool-specific instructions following Claude Code patterns."""
    return """📋 **CL_DESCRIBE: Complete RDF Entity Retrieval**

**PURPOSE**: Get comprehensive RDF data about specific entities using SPARQL 1.1 DESCRIBE

**COMPLETE ENTITY ANALYSIS**:
```bash
# Database/service descriptions
cl_describe Q905695                              # UniProt database entity
cl_describe P352                                 # UniProt protein ID property

# Biological entities  
cl_describe Q7240673                             # Insulin (complete data)
cl_describe Q500826                              # Insulin receptor

# Cross-domain entities
cl_describe Q5                                   # Human (comprehensive)
cl_describe Q2329                                # Chemistry concept
```

**MULTI-ENDPOINT USAGE**:
```bash
# Default Wikidata (rich metadata)
cl_describe Q905695                              # Comprehensive Wikidata data

# Domain-specific endpoints  
cl_describe P01308 --endpoint uniprot           # UniProt protein record
cl_describe WP4846 --endpoint wikipathways      # WikiPathways pathway
```

**OUTPUT STRUCTURE** (Complete JSON-LD):
```json
{
  "success": true,
  "entity": "Q905695",
  "endpoint": "wikidata",
  "rdf_format": "json-ld",
  "triple_count": 156,
  "data": {
    "@context": {...},
    "@id": "http://www.wikidata.org/entity/Q905695",
    "@type": ["http://www.wikidata.org/entity/Q8054"],
    "http://www.wikidata.org/prop/direct/P31": [
      {"@id": "http://www.wikidata.org/entity/Q8054"}
    ],
    "http://www.wikidata.org/prop/direct/P1687": [
      {"@id": "http://www.wikidata.org/entity/P352"}
    ]
  },
  "analysis_summary": {
    "entity_types": ["Q8054"],
    "property_count": 47,
    "external_references": {"P352": "UniProt", "P594": "Ensembl"},
    "relationship_depth": 3
  },
  "composition_opportunities": {
    "property_details": ["cl_describe P352", "cl_describe P1687"],
    "type_exploration": ["cl_describe Q8054"],
    "related_entities": ["cl_select \"SELECT ?x WHERE { ?x wdt:P1687 wd:Q905695 }\""]
  }
}
```

**RDF FORMAT HANDLING**:
- **Default**: JSON-LD for structured Claude Code consumption
- **Content negotiation**: Proper Accept headers for SPARQL 1.1 compliance
- **Fallback**: Turtle format if JSON-LD not available
- **Processing**: Full RDF parsing with relationship extraction

**VALIDATION RULES**:
- Entity: Non-empty identifier (URI, QID, or local identifier)
- Endpoint: Must support SPARQL 1.1 DESCRIBE operation
- Timeout: 30 seconds for complex entity retrieval
- Format: Always returns JSON for Claude Code compatibility

**USE CASES** (When to use cl_describe):
1. **Complete context**: Need all available information about an entity
2. **Relationship mapping**: Understanding all connections and properties  
3. **Metadata extraction**: Getting comprehensive descriptions for analysis
4. **Cross-reference discovery**: Finding all external identifiers and links

**PERFORMANCE CONSIDERATIONS**:
- **Entity complexity**: Some entities (like Q5 "Human") have thousands of statements
- **Endpoint efficiency**: Domain-specific endpoints often faster for their entities
- **Caching**: Results automatically cached for subsequent analysis
- **Timeout handling**: Graceful degradation for complex entities

**INTEGRATION WITH OTHER TOOLS**:
```bash
# Discovery workflow: search → describe → explore
cl_search "insulin" --limit 3                   # Find candidates
cl_describe Q7240673                             # Get complete insulin data  
cl_select "SELECT ?related WHERE { wd:Q7240673 ?p ?related }" --limit 10  # Explore relationships
```

**COMMON ENTITY PATTERNS**:
- **Wikidata QIDs**: Q7240673, Q905695, Q500826
- **Properties**: P31 (instance of), P352 (UniProt ID), P1687 (property issued by)
- **Domain entities**: UniProt IDs, pathway identifiers, chemical compounds
- **Cross-references**: External database identifiers and mappings

**VALIDATION & ERROR HANDLING**:
- **Entity existence**: Validates entity exists before DESCRIBE query
- **Format compliance**: Ensures valid JSON-LD output structure
- **Relationship parsing**: Extracts meaningful connections for analysis
- **Error recovery**: Graceful handling of missing or restricted entities

**SUCCESS INDICATORS**:
- ✅ Complete JSON-LD data with @context and structured properties
- ✅ Analysis summary reveals entity types and relationship patterns
- ✅ External references discovered for cross-database research
- ✅ Composition opportunities suggest logical next analysis steps"""


def _get_cl_ask_instructions() -> str:
    """cl_ask tool-specific instructions following Claude Code patterns."""
    return """❓ **CL_ASK: Boolean Fact Verification with SPARQL ASK**

**PURPOSE**: Verify specific facts and hypotheses with true/false boolean queries

**FACT VERIFICATION PATTERNS**:
```bash
# Entity type verification
cl_ask "{ wd:Q905695 wdt:P31 wd:Q8054 }"        # Is UniProt a database?
cl_ask "{ wd:Q7240673 wdt:P31 wd:Q8054 }"       # Is insulin a database? (false)

# Relationship existence  
cl_ask "{ wd:Q7240673 wdt:P352 ?uniprot }"      # Does insulin have UniProt ID?
cl_ask "{ wd:Q500826 wdt:P688 ?gene }"          # Does insulin receptor encode gene?

# Property connectivity
cl_ask "{ ?x wdt:P1687 wd:Q905695 }"            # Are there properties issued by UniProt?
```

**CROSS-ENDPOINT VERIFICATION**:
```bash
# Wikidata fact checking (default)
cl_ask "{ wd:Q905695 wdt:P921 wd:Q420 }"        # Is UniProt about biology?

# Domain-specific existence checks
cl_ask "{ ?protein a up:Protein }" --endpoint uniprot           # Do proteins exist in UniProt?
cl_ask "{ ?pathway a wp:Pathway }" --endpoint wikipathways      # Do pathways exist in WikiPathways?
```

**OUTPUT STRUCTURE** (Simple Boolean + Metadata):
```json
{
  "success": true,
  "query": "{ wd:Q905695 wdt:P31 wd:Q8054 }",
  "endpoint": "wikidata",
  "result": true,
  "execution_time_ms": 89,
  "interpretation": {
    "fact_verified": "UniProt (Q905695) is confirmed to be a database (Q8054)",
    "confidence": "definitive",
    "evidence_type": "direct_assertion"
  },
  "composition_opportunities": {
    "explore_type": ["cl_describe Q8054"],
    "find_similar": ["cl_select \"SELECT ?db WHERE { ?db wdt:P31 wd:Q8054 }\" --limit 10"],
    "verify_related": ["cl_ask \"{ wd:Q905695 wdt:P921 wd:Q420 }\""]
  }
}
```

**QUERY CONSTRUCTION PATTERNS**:
```bash
# ✅ CORRECT: Use discovered vocabulary
rdf_cache uniprot_service --graph               # Discover up:Protein class
cl_ask "{ ?protein a up:Protein }" --endpoint uniprot

# ✅ Type checking with Wikidata
cl_ask "{ wd:Q7240673 wdt:P31 wd:Q8054 }"      # Instance relationship

# ✅ Property existence  
cl_ask "{ wd:Q500826 ?p ?o }"                   # Has any properties?

# ❌ INCORRECT: Guessing vocabulary
cl_ask "{ ?protein a uniprot:Protein }"         # Wrong prefix
```

**VALIDATION RULES**:
- Query: Must be valid SPARQL ASK statement (enforced by schema)
- Safety: No modification operations (DELETE/INSERT/DROP) allowed
- Syntax: Balanced braces { }, valid triple patterns
- Performance: Fast execution optimized for boolean results

**HYPOTHESIS TESTING WORKFLOW**:
1. **Generate hypothesis**: Based on previous search/describe results
2. **Construct ASK query**: Using discovered vocabulary from rdf_cache
3. **Verify fact**: Get definitive true/false answer
4. **Follow up**: Use composition_opportunities for deeper analysis

**USE CASES** (When to use cl_ask):
- **Type verification**: "Is X an instance of Y?"
- **Relationship existence**: "Does A have property P pointing to B?"
- **Data presence**: "Are there any entities of type X in this endpoint?"
- **Cross-reference validation**: "Does entity A have external ID in database B?"

**PERFORMANCE OPTIMIZATION**:
- **Boolean queries**: Extremely fast compared to SELECT/DESCRIBE
- **Early termination**: SPARQL engines stop at first result match
- **Cache-friendly**: Results suitable for caching true/false facts
- **Parallel execution**: Can run multiple ASK queries concurrently

**INTEGRATION PATTERNS**:
```bash
# Search → Ask → Describe workflow
cl_search "insulin receptor" --limit 3          # Find candidates
cl_ask "{ wd:Q500826 wdt:P31 wd:Q7187 }"       # Verify it's a gene
cl_describe Q500826                              # Get complete data if verified

# Batch verification
cl_ask "{ wd:Q905695 wdt:P31 wd:Q8054 }"       # Database check
cl_ask "{ wd:Q905695 wdt:P921 wd:Q420 }"       # Biology check  
cl_ask "{ wd:Q905695 wdt:P1687 ?prop }"        # Issues properties check
```

**COMMON ERROR PATTERNS**:
- ❌ Non-ASK query → Must start with ASK keyword
- ❌ Complex aggregations → Use cl_select for counting/grouping
- ❌ Multiple questions → Split into separate ASK queries
- ❌ Guessed vocabulary → Use discovered URIs from rdf_cache

**SUCCESS INDICATORS**:
- ✅ Clear true/false result with confident interpretation
- ✅ Fast execution time (< 500ms typically)
- ✅ Uses discovered vocabulary from previous rdf_cache exploration  
- ✅ Composition opportunities suggest logical follow-up analysis"""


def compile_all_tool_instructions() -> Dict[str, str]:
    """Compile all tool-specific instructions for embedding in prompts.
    
    Following Claude Code pattern of comprehensive tool guidance compilation.
    """
    tools = ['rdf_get', 'rdf_cache', 'cl_search', 'cl_select', 'cl_describe', 'cl_ask']
    
    return {
        tool_name: get_tool_specific_instructions(tool_name) 
        for tool_name in tools
    }


def get_workflow_specific_instructions(workflow_type: str) -> str:
    """Get workflow-specific instruction patterns following Claude Code composition.
    
    Compiles multi-tool workflows with validation and error handling guidance.
    """
    
    workflows = {
        'discovery_first': _get_discovery_workflow_instructions(),
        'entity_analysis': _get_entity_analysis_workflow(),
        'cross_reference': _get_cross_reference_workflow(),
        'domain_research': _get_domain_research_workflow(),
        'ontology_navigation': _get_ontology_navigation_workflow()
    }
    
    return workflows.get(workflow_type, f"Workflow '{workflow_type}' not found. Available: {list(workflows.keys())}")


def _get_discovery_workflow_instructions() -> str:
    """Discovery-first workflow instructions."""
    return """🔍 **DISCOVERY-FIRST WORKFLOW** (CRITICAL FOUNDATION)

**PHASE 1: Service Discovery** (NEVER SKIP)
```bash
# 1. Discover service capabilities and vocabulary
rdf_get https://sparql.uniprot.org/sparql --format turtle --cache-as uniprot_service
rdf_get https://query.wikidata.org/sparql --format turtle --cache-as wikidata_service

# 2. Analyze content structure (Claude Code interpretation)
# content_analysis provides structural_patterns for vocabulary understanding
```

**PHASE 2: Vocabulary Analysis** (Software 2.0)
```bash
# 3. Read complete vocabulary context
rdf_cache uniprot_service --graph               # Complete ontology for understanding

# 4. Navigate semantic relationships
rdf_cache --subclasses up:Protein               # Find all protein subtypes
rdf_cache --properties up:Protein               # Valid properties for proteins
rdf_cache --related up:Protein                  # SKOS/OWL relationships

# 5. Store Claude Code analysis
rdf_cache uniprot_service --update-metadata '{
  "semantic_type": "service",
  "domains": ["biology"],
  "confidence": 0.95
}'
```

**PHASE 3: Intelligent Querying** (Using Discovered Vocabulary)
```bash
# 6. Use discovered classes and properties
cl_select "SELECT ?protein WHERE { ?protein a up:Protein }" --endpoint uniprot --limit 5
cl_ask "{ ?protein a up:Protein }" --endpoint uniprot

# 7. NEVER use guessed URIs
# ❌ cl_select "SELECT ?protein WHERE { ?protein a uniprot:Protein }"
```

**SUCCESS CRITERIA**:
- ✅ Service vocabulary discovered and cached before queries
- ✅ Semantic relationships mapped via rdfs:subClassOf navigation  
- ✅ Claude Code insights stored for research memory
- ✅ All queries use discovered URIs, not guessed prefixes

**FAILURE PATTERNS TO AVOID**:
- ❌ Direct SPARQL queries without vocabulary discovery
- ❌ Guessing namespace prefixes (up:, uniprot:, etc.)
- ❌ Skipping semantic relationship analysis
- ❌ Not storing Claude Code analysis for session memory"""


def _get_entity_analysis_workflow() -> str:
    """Entity analysis workflow instructions."""
    return """📊 **ENTITY ANALYSIS WORKFLOW** (Systematic Exploration)

**PATTERN: Search → Describe → Select → Verify**

**STEP 1: Entity Discovery**
```bash
# Find candidate entities
cl_search "insulin receptor" --limit 5          # Multiple candidates
cl_search "COVID spike protein" --limit 3       # Domain-specific search
```

**STEP 2: Complete Entity Analysis**  
```bash
# Get comprehensive data for top candidates
cl_describe Q500826                              # Insulin receptor (complete)
cl_describe Q7240673                             # Insulin (reference)
```

**STEP 3: Property Exploration** (ReadTool Pattern)
```bash
# Systematic property analysis with pagination
cl_select "SELECT ?p ?o WHERE { wd:Q500826 ?p ?o }" --limit 10
cl_select "SELECT ?p ?o WHERE { wd:Q500826 ?p ?o }" --limit 10 --offset 10

# Relationship discovery
cl_select "SELECT ?related WHERE { wd:Q500826 ?p ?related }" --limit 10
```

**STEP 4: Cross-Reference Analysis**
```bash
# Find external identifiers
cl_select "SELECT ?prop ?id WHERE { wd:Q500826 ?prop ?id . ?prop wdt:P31 wd:P1628 }" --limit 10

# Verify specific connections
cl_ask "{ wd:Q500826 wdt:P352 ?uniprot }"       # Has UniProt ID?
cl_ask "{ wd:Q500826 wdt:P594 ?ensembl }"       # Has Ensembl ID?
```

**STEP 5: Domain Context**
```bash
# Find related entities of same type
cl_select "SELECT ?similar WHERE { ?similar wdt:P31 ?type . wd:Q500826 wdt:P31 ?type }" --limit 5

# Explore functional relationships  
cl_select "SELECT ?pathway WHERE { ?pathway wdt:P527 wd:Q500826 }" --limit 5
```

**COMPOSITION PATTERNS**:
- Use describe results to guide subsequent select queries
- Follow composition_opportunities from tool outputs
- Verify hypotheses with targeted ask queries
- Build entity knowledge systematically with pagination

**SUCCESS INDICATORS**:
- ✅ Complete entity properties mapped with pagination
- ✅ External database references discovered and verified
- ✅ Functional relationships and pathways identified
- ✅ Domain context established through type analysis"""


def _get_cross_reference_workflow() -> str:
    """Cross-reference workflow instructions."""  
    return """🔗 **CROSS-REFERENCE WORKFLOW** (Database Integration)

**PATTERN: Discover → Map → Follow → Verify**

**STEP 1: External Identifier Discovery**
```bash
# Find all external database properties for entity
cl_select "SELECT ?prop ?id WHERE { 
  wd:Q7240673 ?prop ?id . 
  ?prop wdt:P31 wd:P1628 
}" --limit 10

# Verify identifier exists
cl_ask "{ wd:Q7240673 wdt:P352 ?uniprot }"      # UniProt ID check
```

**STEP 2: Cross-Database Resolution**
```bash
# Get actual identifier values
cl_select "SELECT ?uniprot WHERE { wd:Q7240673 wdt:P352 ?uniprot }" --limit 1

# Use identifiers in domain databases
cl_search "P01308" --endpoint uniprot --limit 3
cl_describe P01308 --endpoint uniprot
```

**STEP 3: Bidirectional Verification**
```bash
# Verify connection from other database
cl_ask "{ <http://purl.uniprot.org/uniprot/P01308> ?p ?o }" --endpoint uniprot

# Check for reciprocal references
cl_select "SELECT ?wikidata WHERE { 
  <http://purl.uniprot.org/uniprot/P01308> rdfs:seeAlso ?wikidata 
}" --endpoint uniprot
```

**STEP 4: Relationship Validation**
```bash
# Confirm entity types align across databases
cl_ask "{ wd:Q7240673 wdt:P31 wd:Q8054 }"       # Wikidata type
cl_ask "{ ?protein a up:Protein }" --endpoint uniprot  # UniProt type

# Verify semantic consistency
cl_describe Q8054                                # Database type analysis
```

**CROSS-DATABASE MAPPING PATTERNS**:
- **Wikidata → UniProt**: P352 (UniProt protein ID)
- **Wikidata → Ensembl**: P594 (Ensembl gene ID)
- **Wikidata → PubChem**: P662 (PubChem CID)
- **Wikidata → ChEMBL**: P592 (ChEMBL compound ID)

**VALIDATION REQUIREMENTS**:
- ✅ Bidirectional verification of cross-references
- ✅ Type consistency across databases
- ✅ Semantic alignment of entity descriptions
- ✅ Temporal consistency of identifier validity

**SUCCESS INDICATORS**:
- ✅ External identifiers discovered via P1628 pattern
- ✅ Cross-database entity resolution confirmed
- ✅ Bidirectional references validated
- ✅ Semantic consistency verified across endpoints"""


def _get_domain_research_workflow() -> str:
    """Domain research workflow instructions."""
    return """🧬 **DOMAIN RESEARCH WORKFLOW** (Biology Example)

**PATTERN: Context → Entities → Relationships → Integration**

**STEP 1: Domain Context Discovery**
```bash
# Establish domain boundaries and vocabulary
rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot_service
rdf_cache uniprot_service --graph               # Read complete biology ontology

# Understand domain classes and properties
rdf_cache --subclasses up:Protein               # Protein taxonomy
rdf_cache --properties up:Protein               # Valid protein properties
```

**STEP 2: Entity Type Exploration**
```bash
# Find domain-specific entity types
cl_select "SELECT DISTINCT ?type WHERE { ?entity a ?type }" --endpoint uniprot --limit 10

# Analyze type distributions
cl_select "SELECT ?type (COUNT(?entity) as ?count) WHERE { 
  ?entity a ?type 
} GROUP BY ?type ORDER BY DESC(?count)" --endpoint uniprot --limit 10
```

**STEP 3: Relationship Pattern Discovery**
```bash
# Map property usage patterns
cl_select "SELECT ?property (COUNT(?usage) as ?frequency) WHERE {
  ?entity ?property ?value
} GROUP BY ?property ORDER BY DESC(?frequency)" --endpoint uniprot --limit 15

# Discover domain-specific relationships
cl_select "SELECT ?protein ?pathway WHERE {
  ?protein up:annotation ?pathway .
  ?pathway a up:Pathway_Annotation
}" --endpoint uniprot --limit 10
```

**STEP 4: Cross-Domain Integration**
```bash
# Find cross-domain connections via Wikidata
cl_select "SELECT ?protein ?wikidata WHERE {
  ?protein wdt:P352 ?uniprot .
  wd:?wikidata wdt:P352 ?uniprot
}" --limit 10

# Explore multi-domain pathways
cl_select "SELECT ?pathway ?chemical WHERE {
  ?pathway wp:hasParticipant ?chemical .
  ?chemical wdt:P231 ?cas
}" --endpoint wikipathways --limit 10
```

**DOMAIN-SPECIFIC PATTERNS**:

**Biology Domain**:
- Entity types: up:Protein, up:Gene, up:Enzyme
- Key properties: up:annotation, up:sequence, up:organism
- Cross-references: P352 (UniProt), P594 (Ensembl), P705 (Ensembl transcript)

**Chemistry Domain**:
- Entity types: Chemical compounds, reactions, pathways
- Key properties: P231 (CAS number), P662 (PubChem), P592 (ChEMBL)
- Cross-references: Chemical databases and biological targets

**SUCCESS INDICATORS**:
- ✅ Domain vocabulary comprehensively mapped
- ✅ Entity type distributions understood  
- ✅ Property usage patterns identified
- ✅ Cross-domain connections established
- ✅ Research workflows optimized for domain patterns"""


def _get_ontology_navigation_workflow() -> str:
    """Ontology navigation workflow instructions."""
    return """📚 **ONTOLOGY NAVIGATION WORKFLOW** (Semantic Understanding)

**PATTERN: Load → Navigate → Understand → Apply**

**STEP 1: Complete Ontology Loading** (ReadTool Pattern)
```bash
# List available ontologies with metadata
rdf_cache "" --list

# Load complete ontology context (size-aware)
rdf_cache foaf_vocab --graph                    # < 100KB: immediate load
rdf_cache uniprot_core --graph --force          # > 500KB: explicit override

# Check ontology structure
rdf_cache foaf_vocab --graph | jq '.enhanced_index.classes | keys'
```

**STEP 2: Class Hierarchy Navigation**
```bash
# Explore class hierarchies via rdfs:subClassOf
rdf_cache --subclasses foaf:Agent               # Find all Agent subtypes
rdf_cache --subclasses up:Protein               # Protein classification

# Understand inheritance patterns
rdf_cache foaf_vocab --graph | jq '.enhanced_index.semantic_index.class_hierarchy'
```

**STEP 3: Property Constraint Discovery**
```bash
# Find valid properties for classes via rdfs:domain/range
rdf_cache --properties foaf:Person              # Person-specific properties
rdf_cache --properties up:Protein               # Protein annotation properties

# Analyze property constraints
rdf_cache foaf_vocab --graph | jq '.enhanced_index.semantic_index.property_domains'
```

**STEP 4: Relationship Mapping**
```bash
# Discover semantic relationships via SKOS/OWL
rdf_cache --related foaf:knows                  # Social relationship patterns
rdf_cache --related up:enzyme                   # Enzyme classification patterns

# Find equivalent terms across vocabularies
rdf_cache foaf_vocab --graph | jq '.enhanced_index.semantic_index.equivalences'
```

**STEP 5: Applied Ontology Usage**
```bash
# Use discovered classes in queries
cl_select "SELECT ?person WHERE { ?person a foaf:Person }" --limit 5
cl_ask "{ ?agent a foaf:Agent }"

# Apply property constraints
cl_select "SELECT ?person ?name WHERE { 
  ?person a foaf:Person . 
  ?person foaf:name ?name 
}" --limit 5
```

**SIZE MANAGEMENT** (Following ReadTool Patterns):
- **Small ontologies** (< 100KB): Load immediately with --graph
- **Medium ontologies** (100KB-500KB): Warning + confirmation  
- **Large ontologies** (> 500KB): Require --force override
- **Complex navigation**: Use jq for selective data extraction

**SEMANTIC ANALYSIS PATTERNS**:
```bash
# Class hierarchy depth analysis
rdf_cache ontology --graph | jq '.enhanced_index.semantic_index.class_hierarchy | to_entries | map({class: .key, depth: (.value | length)})'

# Property usage frequency  
rdf_cache ontology --graph | jq '.enhanced_index.properties | to_entries | map({property: .key, usage_count: .value.usage_count})'

# Cross-vocabulary alignments
rdf_cache ontology --graph | jq '.enhanced_index.semantic_index.equivalences'
```

**SUCCESS INDICATORS**:
- ✅ Complete ontology structure loaded and understood
- ✅ Class hierarchies navigated via rdfs:subClassOf
- ✅ Property constraints discovered via rdfs:domain/range
- ✅ Semantic relationships mapped via SKOS/OWL patterns
- ✅ Applied understanding in intelligent SPARQL construction"""