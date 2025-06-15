# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the unified CogitareLink repository.

## Project Overview

**CogitareLink: Living Scientific Assistant**

A semantic web-powered scientific research assistant that combines rigorous knowledge management with intelligent discovery and continuous learning from agent interactions. CogitareLink ("to think connectedly") synthesizes:

- **Semantic Rigor**: Immutable JSON-LD entities, SHACL reasoning, cryptographic verification
- **Agent Intelligence**: Discovery-first guardrails, structured responses, Chain-of-Thought scaffolds
- **Software 2.0**: Generalized tools + intelligent prompting rather than hardcoded logic

### Core Philosophy

- **Hybrid CLI + Agentic**: CLI-first composable tools with rich structured responses for agent intelligence
- **Semantic Memory**: All discovered knowledge stored as immutable entities with full provenance tracking
- **Discovery-First Guardrails**: Never query without schema understanding (like Read-before-Edit in Claude Code)
- **In-Context Teaching**: Continuously learn and improve from actual agent usage patterns
- **Verifiable Science**: Every conclusion traceable to sources with cryptographic verification
- **Framework Agnostic**: Works with Claude Code, DSPy, LangGraph, or any agent framework

## Research Agent Integration with Claude Code

### Architecture Overview
CogitareLink enhances Claude Code through **instruction-driven enhancement** rather than architectural modification. The core insight: transform Claude Code into a research assistant by providing enhanced instructions and maintaining parallel session state.

### Parallel Session Design
- **Claude Code Session**: `.claude/session.json` (untouched - cost tracking, model usage)
- **Research Session**: `.cogitarelink/session.json` (research context, domain knowledge, instruction state)
- **Session Linking**: Research sessions reference Claude Code sessions for correlation
- **Independent Persistence**: Both systems persist separately using debounced patterns

### Entry Point: `cogitarelink` Command
```bash
cogitarelink init biology                    # Initialize research mode
cogitarelink status                         # Show research session state  
cogitarelink remind discovery               # Print discovery-first instructions
cogitarelink remind protein-workflow        # Print protein research patterns
cogitarelink resume cl_research_20240615    # Resume previous research session
```

**Key Behavior**: Prints research instructions directly to Claude Code's context, enabling enhanced research capabilities without architectural changes.

## CLI Tool Refactoring Plan (Jeremy Howard Style)

### Overview
Refactoring completed ✅ - 5 CLI tools built following Claude Code patterns with discovery-first guardrails and session-aware caching.

Built clean foundation using proper libraries (diskcache, SPARQLWrapper, rdflib, pyld) instead of custom implementations.

### Phase 2: CLI Tools - COMPLETED ✅
Created 5 production-ready CLI tools:
- **cl_search**: Entity search (Wikidata API + SPARQL endpoints)
- **cl_fetch**: Entity data retrieval with structured output
- **cl_discover**: Endpoint capability discovery with caching
- **cl_query**: SPARQL execution with discovery-first guardrails
- **cl_resolve**: Cross-reference resolution across databases

All tools follow Claude Code patterns: simple parameters, fast execution, structured responses.

### Phase 3: Research Agent Entry Point - IN PROGRESS 🚧

#### Research Session Architecture
```json
// .cogitarelink/session.json structure
{
  "sessionId": "cl_research_20240615_123456",
  "claudeSessionId": "abc123-def456-ghi789", 
  "researchDomain": "biology",
  "researchGoal": "COVID spike protein analysis",
  "discoveredEndpoints": [...],
  "activeInstructions": ["discovery_first_biology", "protein_workflow"],
  "researchProgress": {...}
}
```

#### Instruction Index System
```
cogitarelink/instructions/
├── discovery_first.md      # Discovery-before-query patterns  
├── biology_workflow.md     # Protein research workflows
├── chemistry_workflow.md   # Chemical compound analysis
└── multi_agent.md         # Agent coordination patterns
```

#### Entry Point Commands
- `cogitarelink init <domain>` - Initialize research session
- `cogitarelink status` - Show current research context
- `cogitarelink remind <pattern>` - Print specific instructions
- `cogitarelink resume <session_id>` - Resume previous session

### Phase 4: Enhanced Tool Intelligence - IN PROGRESS 🚧

**Software 2.0 Architecture Strategy**: Build domain-agnostic tools with rich metadata that future sub-agents can interpret intelligently.

#### Core Design Principle
**Tools should be data-rich and suggestion-smart, but domain-dumb.** Domain reasoning will eventually be handled by specialized sub-agents, not hardcoded logic.

### Cache-Aware Dynamic Discovery Architecture ✨

**Revolutionary Insight**: CogitareLink tools should follow Claude Code's caching patterns - cache-aware but capability-backed, self-improving through usage.

#### The Claude Code Pattern Applied to Discovery
```python
def classify_domain_from_service(service_id: str) -> str:
    # 1. Check cache first (fast path)
    cache_key = f"service_domain:{service_id}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    # 2. Fallback to live discovery capability
    domain = self._discover_domain_via_sparql(service_id)
    
    # 3. Cache the result for future use
    cache_manager.set(cache_key, domain, ttl=86400)
    
    return domain
```

#### Multi-Layer Cache Strategy
- **Layer 1**: Property → Service mapping (`P352 → Q905695`, 24h TTL)
- **Layer 2**: Service → Domain mapping (`Q905695 → "biology"`, 24h TTL)  
- **Layer 3**: Domain → Workflow patterns (`"biology" → ["P31→P352→P638"]`, 1 week TTL)
- **Layer 4**: Identifier → Resolution results (`"P04637" → [results]`, 1h TTL)

#### Self-Improving Tool Design
Each tool usage teaches the system more about semantic web structure:
- **Discovery**: SPARQL queries discover service domains automatically
- **Caching**: Discoveries cached for fast subsequent access
- **Fallback**: Always falls back to live discovery when cache misses
- **Learning**: System improves performance through actual usage patterns

#### Implementation Requirements

### Dynamic Discovery Implementation Plan

#### 1. Core Discovery Functions (cl_resolve)
```python
# IMPLEMENT: Cache-aware domain discovery
def discover_service_for_property(prop_id: str) -> str:
    """P352 → Q905695 via cached/live SPARQL"""

def classify_domain_from_service(service_id: str) -> str:
    """Q905695 → "biology" via cached/live SPARQL query to P921 (main subject)"""

def discover_database_pattern(prop_id: str) -> Dict[str, Any]:
    """P352 → {name, domain, format, url} via cached/live discovery"""

def resolve_identifier_dynamic(identifier: str) -> List[Dict]:
    """P04637 → auto-detect → discover patterns → resolve"""
```

#### 2. Cache Manager Integration
```python
# USE EXISTING: cogitarelink.discovery.cache_manager
cache_manager.get(cache_key)
cache_manager.set(cache_key, result, ttl=86400)

# CACHE KEYS STRATEGY:
# "service_discovery:P352" → "Q905695"
# "service_domain:Q905695" → "biology"  
# "database_pattern:P352" → {complete pattern dict}
# "identifier_resolution:P04637" → [resolution results]
```

#### 3. Enhanced Prompting Integration
Update `cogitarelink.py` instruction templates to include:
- **Cache-aware workflow patterns**: "First time: discovery + cache, subsequent: fast cache lookup"
- **Domain intelligence prompts**: Generated from discovered service → domain mappings
- **Cross-reference workflow suggestions**: Based on cached external identifier patterns
- **Self-improving guidance**: "System learns from your usage patterns"

#### 4. Tool Response Enhancement
```python
# IMPLEMENT: Claude Code structured responses
{
    "success": true,
    "data": {...},
    "metadata": {
        "cache_hit": true,
        "discovery_method": "cached_pattern",
        "execution_time_ms": 15
    },
    "suggestions": {
        "next_tools": ["cl_sparql --endpoint discovered"],
        "workflow_patterns": ["biology: P352→P638→P705"],
        "cache_status": "pattern_learned"
    },
    "claude_guidance": {
        "domain_intelligence": ["UniProt focuses on protein sequences"],
        "learned_patterns": ["System cached biology workflow for Q905695"],
        "discovery_insights": ["Found 3 external identifier patterns"]
    }
}
```

#### 5. Session-Aware Learning
```python
# ENHANCE: Research session tracks discoveries
session_data["learned_patterns"] = [
    {"service": "Q905695", "domain": "biology", "learned_at": timestamp},
    {"property": "P352", "pattern": {...}, "learned_at": timestamp}
]

# IMPLEMENT: Session-specific cache warming
def warm_session_cache(domain: str):
    """Pre-populate cache with domain-specific patterns"""
```

#### 6. Live Testing & Validation
```python
# TESTS TO IMPLEMENT:
class TestCacheAwareDiscovery:
    def test_p352_to_uniprot_cached(self):
        """First call: discovery + cache, second call: cache hit"""
        
    def test_dynamic_domain_classification(self):
        """Q905695 → "biology" via live SPARQL → cached"""
        
    def test_self_improving_workflows(self):
        """Usage patterns improve subsequent recommendations"""
```

### Enhanced Prompting Integration Requirements

#### Update Instruction Templates (cogitarelink.py)

**1. Discovery-First Template Enhancement:**
```markdown
🔍 **CACHE-AWARE DISCOVERY PATTERN**

**First Usage (Discovery + Learning):**
- Use `cl_resolve <identifier>` → System discovers and caches patterns
- Execution time: ~500ms (includes SPARQL discovery)
- Cache warm-up: Service domains, format patterns, workflow suggestions

**Subsequent Usage (Fast Cache Access):**  
- Use `cl_resolve <identifier>` → System uses cached patterns
- Execution time: ~50ms (cache hit)
- Intelligent suggestions based on learned domain patterns

**System Learning Indicators:**
- ✅ "Pattern cached for Q905695 → biology domain"
- ✅ "Discovered workflow: P352→P638→P705"
- ✅ "Next resolution will be 10x faster"
```

**2. Dynamic Domain Intelligence:**
```markdown
📊 **DYNAMIC DOMAIN INTELLIGENCE**

**Biology Domain (Automatically Discovered):**
- UniProt (Q905695): Main subject → Biology (Q420)
- Workflow patterns: P352→P638→P705 (protein→structure→genomics)
- Cache status: ✅ Learned from previous usage

**Chemistry Domain (Automatically Discovered):**
- PubChem (Q278487): Main subject → Chemistry (Q2329)  
- Workflow patterns: P231→P662→P592 (identity→structure→bioactivity)
- Cache status: ✅ Learned from previous usage

**System continuously learns new domains as you discover them.**
```

**3. Self-Improving Workflow Guidance:**
```markdown
🚀 **SELF-IMPROVING RESEARCH WORKFLOWS**

The system learns from your usage patterns:

**Session Learning:**
- Tracks discovered domains and patterns per session
- Builds personalized workflow recommendations
- Warms cache for your research domain

**Cross-Session Learning:**
- Remembers successful discovery patterns
- Improves suggestion quality over time
- Reduces discovery overhead through intelligent caching

**Usage Examples:**
```bash
# First time: System learns about biology
cl_resolve P04637  # Discovers: P352→Q905695→biology, caches pattern

# Second time: Fast cached access + intelligent suggestions  
cl_resolve Q9UHC7  # Uses cached biology patterns, suggests P638 (PDB)
```

#### Session Enhancement Requirements

**1. Cache Warmup Integration:**
```python
# IMPLEMENT: Domain-specific cache warming
def init_biology_session():
    """Pre-populate cache with biology patterns for fast research"""
    warm_patterns = ["P352", "P638", "P705", "P594", "P637"]
    for prop_id in warm_patterns:
        discover_database_pattern(prop_id)  # Cache for fast access
```

**2. Learning Metrics Tracking:**
```json
// ADD TO: session.json
"cache_learning": {
    "patterns_discovered": 15,
    "domains_learned": ["biology", "chemistry"],
    "avg_resolution_time_ms": 45,  // Improved from 500ms via caching
    "cache_hit_rate": 0.85
}
```

#### Target Architecture
│ • cl_search     │────│ • Context        │────│ • Biology Agent     │
│ • cl_fetch      │    │ • Progress       │    │ • Chemistry Agent   │
│ • cl_discover   │    │ • Tool Usage     │    │ • Literature Agent  │
│ • cl_query      │    │ • Metadata       │    │ • Analysis Agent    │
│ • cl_resolve    │    │                  │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

#### Enhanced Tool Response Pattern
```json
{
  "data": {...},
  "metadata": {
    "entity_types": ["Q8054", "Q11173"],
    "external_references": {"P352": 5, "P594": 2},
    "relationship_graph": {...},
    "execution_context": {
      "cache_hit": true,
      "execution_time_ms": 250,
      "complexity_score": 3.2
    }
  },
  "composition_opportunities": {
    "detail_retrieval": ["cl_fetch Q123", "cl_fetch Q456"],
    "cross_reference_following": ["cl_resolve P04637"],
    "search_expansion": ["cl_search 'broader_term'"],
    "endpoint_exploration": ["cl_discover uniprot"]
  },
  "session_context": {
    "research_domain": "biology",
    "entities_discovered": 15,
    "successful_patterns": ["search→fetch→resolve"]
  }
}
```

#### Software 2.0 vs Software 1.0 Guidelines

**❌ Avoid (Software 1.0 - Hardcoded Logic):**
```python
# BAD: Domain-specific hardcoded logic
if domain == "biology":
    if "protein" in results:
        suggestions = ["Follow protein pathways", "Check UniProt"]
elif domain == "chemistry":  
    if "compound" in results:
        suggestions = ["Check PubChem", "Find targets"]
```

**✅ Prefer (Software 2.0 - General + Rich Metadata):**
```python
# GOOD: General patterns + contextual metadata
suggestions = {
    "entity_expansion": [f"cl_fetch {entity['id']}" for entity in top_results],
    "cross_references": self._extract_external_ids(results),
    "relationship_exploration": self._extract_relationships(results),
    "endpoint_bridging": self._suggest_related_endpoints(entity_types)
}
```

**Key Principle**: Tools provide comprehensive, structured metadata. Domain intelligence comes from:
1. **Enhanced instruction templates** that teach agents how to interpret metadata
2. **Research session context** that focuses the interpretation  
3. **Future sub-agents** that specialize in domain reasoning

#### Implementation Phases
**Phase 4a**: Enhance tool responses with rich metadata and composition patterns
**Phase 4b**: Add session-aware context and research progress tracking  
**Phase 4c**: Create instruction templates that prepare for sub-agent architecture

### Future Phases (Multi-Agent Integration)
**Phase 5**: Extract domain reasoning into specialized sub-agents using claude-code SDK
**Phase 6**: Sub-agent coordination and workflow orchestration
**Phase 7**: Advanced research workflows with cross-domain intelligence

## Session Management Design

### .cogitarelink/session.json Structure
```json
{
  "sessionId": "cl_research_20240615_123456",
  "claudeSessionId": "abc123-def456-ghi789",
  "originalCwd": "/Users/username/project",
  "cwd": "/Users/username/project",
  "researchDomain": "biology",
  "researchGoal": "COVID spike protein analysis",
  "lastInteractionTime": 1703123456789,
  "sessionCounter": 1,
  "toolUsage": {
    "cl_discover": 3,
    "cl_search": 8,
    "cl_fetch": 5,
    "cl_query": 12,
    "cl_resolve": 2
  },
  "discoveredEndpoints": [
    {
      "name": "wikidata",
      "url": "https://query.wikidata.org/sparql", 
      "discoveredAt": 1703123456789,
      "capabilities": {...}
    }
  ],
  "activeInstructions": [
    "discovery_first_biology",
    "protein_research_workflow"
  ],
  "researchProgress": {
    "entitiesDiscovered": 23,
    "relationshipsFound": 8,
    "workflowsCompleted": 2
  }
}
```

## Updated pyproject.toml CLI Scripts
```toml
[project.scripts]
# Existing 5 CLI tools (COMPLETED ✅)
cl_search = "cogitarelink.cli.cl_search:search"
cl_fetch = "cogitarelink.cli.cl_fetch:fetch"  
cl_discover = "cogitarelink.cli.cl_discover:discover"
cl_query = "cogitarelink.cli.cl_query:query"
cl_resolve = "cogitarelink.cli.cl_resolve:resolve"

# Research agent entry point (IN PROGRESS 🚧)
cogitarelink = "cogitarelink.cli.cogitarelink:main"
```

**Step 3.2: Create Agent Prompts Module**
- Create `cogitarelink/prompts/` directory
- `lead_agent.txt` - Orchestrator prompt
- `biology_agent.txt` - Biology subagent prompt
- `chemistry_agent.txt` - Chemistry subagent prompt
- Move intelligence to prompts, not code

**Step 3.3: Test Multi-Agent Flow**
- Create `tests/test_multi_agent.py`
- Mock Claude Code SDK calls
- Test task decomposition
- Test result synthesis

### Phase 4: Prompt-Based Intelligence (Week 4)
**Step 4.1: Extract Guardrails to Prompts**
- Move discovery requirements to agent prompts
- Move vocabulary validation to prompts
- Keep only minimal safety checks in code

**Step 4.2: Create Prompt Templates**
```
prompts/
   discovery_first.txt     # "Always discover before query"
   progressive_search.txt  # "Start broad, narrow down"
   cross_reference.txt     # "Follow external IDs"
   synthesis.txt          # "Combine findings with citations"
```

**Step 4.3: Simplify Response Format**
- Remove complex metadata structures
- Return simple JSON or text
- Let agents add reasoning via prompts

### Phase 5: Integration and Testing (Week 5)
**Step 5.1: Update pyproject.toml**
```toml
[project.scripts]
cl_search = "cogitarelink.cli.cl_search:search"
cl_fetch = "cogitarelink.cli.cl_fetch:fetch"
cl_discover = "cogitarelink.cli.cl_discover:discover"
cl_query = "cogitarelink.cli.cl_query:query"
cl_resolve = "cogitarelink.cli.cl_resolve:resolve"
cl_research = "cogitarelink.cli.cl_research:research"
```

**Step 5.2: Create Example Workflows**
- `examples/simple_search.py` - Basic entity search
- `examples/cross_reference.py` - Follow external IDs
- `examples/multi_agent_research.py` - Full research workflow

**Step 5.3: Performance Testing**
- Ensure tools execute in <100ms (except network calls)
- Test cache effectiveness
- Profile multi-agent coordination

### Key Principles Applied:
1. **Simple Tools**: Each tool does ONE thing well
2. **Fast Execution**: Sub-second response times
3. **Discovery First**: Cache schemas, discover before query
4. **Prompt Intelligence**: Move complexity to prompts
5. **Claude Code Patterns**: Simple params, clear output
6. **Multi-Agent Ready**: Tools compose for agent workflows

### Migration Strategy:
- Keep old tools during transition
- New tools in `cogitarelink/cli/` directory
- Gradual migration of functionality
- Test each phase before proceeding

## Build/Test Commands

### Environment Setup
```bash
# Create environment with uv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install development dependencies
uv pip install -e ".[dev]"
```

### Current Test Coverage (✅ Implemented)
```bash
# Foundation tests (9/9 passing) ✅
uv run pytest tests/test_cache_manager.py -v     # Diskcache integration
uv run pytest tests/test_discovery_base.py -v   # SPARQLWrapper integration

# CLI Tool tests (11/11 passing) ✅
uv run pytest tests/test_cli_tools.py -v        # All 5 CLI tools tested

# Integration tests (10/10 passing) ✅  
uv run pytest tests/test_integration.py -v      # Tool composition workflows

# Core test suite (30/30 passing) ✅
uv run pytest tests/ -k "not error_handling and not output_formats" -v

# All implemented tests
uv run pytest tests/ -v
```

### Advanced Test Coverage (📋 Optional)
```bash
# Error Handling Tests (MEDIUM - agent robustness)
tests/test_error_handling.py:
  - test_network_timeout_handling()
  - test_invalid_sparql_queries()
  - test_missing_entities()
  - test_malformed_endpoints()

# Output Format Tests (MEDIUM - agent parsing)  
tests/test_output_formats.py:
  - test_json_output_structure()
  - test_text_output_formatting()
  - test_csv_output_formatting()
  - test_error_output_consistency()

# Performance Tests (LOW - optimization)
tests/test_performance.py:
  - test_tool_execution_speed()
  - test_memory_usage_limits()
  - test_concurrent_requests()
```

### Development Workflow
```bash
# Run all tests with immediate feedback
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_cli_tools.py -v

# Run single test function
uv run pytest tests/test_cli_tools.py::test_cl_search_wikidata_api -v

# Format code (Black, 88 columns)
uv run black cogitarelink/ tests/

# Type checking
uv run mypy cogitarelink/
```

### CLI Tool Testing (Manual Verification)
```bash
# Test all 5 CLI tools working together
uv run cl_discover wikidata --capabilities --format text
uv run cl_search "insulin" --limit 3 --format text  
uv run cl_fetch Q7240673 --properties labels,descriptions
uv run cl_query "SELECT ?item WHERE { ?item wdt:P31 wd:Q8054 }" --limit 2 --format text
uv run cl_resolve P04637 --to-db wikidata --format text

# Test different endpoints
uv run cl_search "COVID" --endpoint wikipathways --format json
uv run cl_fetch WP4846_r120585 --endpoint wikipathways --format text
uv run cl_discover uniprot --schema --format text
```

### Testing Strategy (Jeremy Howard Style)
```python
# Use fastcore test patterns for immediate feedback
from fastcore.test import test_eq, test_fail

def test_cl_search_basic():
    """Test basic search functionality"""
    result = run_cli_command("cl_search", ["insulin", "--limit", "1"])
    test_eq(result.returncode, 0)
    data = json.loads(result.stdout)
    test_eq(data["count"], 1)
    test_eq(len(data["results"]), 1)

def test_cl_search_error_handling():
    """Test search with invalid input"""
    with test_fail():
        run_cli_command("cl_search", [""])  # Should fail
```

### Performance Requirements
```bash
# Tools should execute in <100ms (except network calls)
# Test cache effectiveness with repeated queries
# Profile SPARQL query construction time
time uv run cl_search "insulin" --format json
time uv run cl_discover wikidata --capabilities
```

This follows Jeremy Howard's approach: start simple, test immediately, build incrementally, refactor when patterns emerge.