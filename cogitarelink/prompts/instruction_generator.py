"""Instruction generator for Claude Code integration.

Generates clean, structured instructions for Claude Code based on
domain patterns and research context. Easy to edit and improve.

Version: 1.0
Last Updated: 2024-06-16
Changes: Initial pattern-driven instruction generation
"""

from typing import Dict, Any, Optional
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
    
    return f"""🔬 SEMANTIC RESEARCH MODE ACTIVATED

## Clean Tools Optimized for Claude Code

### 4 Core Tools - Simple, Validated, JSON-Only Output with ReadTool-Style Pagination

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

## Research Workflow Composition Patterns

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

## Tool Composition Principles for Claude Code

**Start with Search (discovery)**:
- Use cl_search for universal entity discovery across any endpoint
- Wikidata uses efficient API search, other endpoints use SPARQL fallback
- Explore systematically with --offset for pagination
- Returns clean JSON with next_page_command hints

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