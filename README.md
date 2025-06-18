# CogitareLink

Six simple RDF tools that give Claude Code semantic web capabilities. Like Claude Code's file tools (Read, Edit) but for linked data.

**Core Pattern**: `discover → cache → query` (like Read-before-Edit)

## Installation

Install CogitareLink directly from GitHub in your Claude Code environment:

```bash
pip install git+https://github.com/LA3D/Cogitarelink.git
```

Or clone and install in development mode:

```bash
git clone https://github.com/LA3D/Cogitarelink.git
cd Cogitarelink
pip install -e .
```

## Getting Started with Claude Code

CogitareLink is designed specifically for Claude Code sessions. Initialize it with:

```bash
cogitarelink
```

This loads semantic research instructions directly into Claude Code's context, enabling intelligent discovery workflows.

The cache system will be automatically created at `~/.cogitarelink/cache/` on first use.

## What You Get

### 🔍 Discovery & Caching Tools
- **`rdf_get`** - Fetch RDF content from any URL with content negotiation
- **`rdf_cache`** - Navigate cached vocabularies and add semantic metadata

### 🗂️ SPARQL Query Tools  
- **`cl_search`** - Universal entity search (Wikidata API, then SPARQL fallback)
- **`cl_select`** - Data exploration with ReadTool-style pagination
- **`cl_describe`** - Complete RDF data about any entity
- **`cl_ask`** - Boolean fact verification queries
- **`cl_construct`** - SHACL template reasoning for knowledge synthesis

## Tool Composition with Claude Code

CogitareLink tools compose naturally with Claude Code's built-in capabilities:

```bash
# 1. Domain research with built-in tools
Task: "Research DBpedia ontology structure"
WebSearch: "UniProt RDF vocabulary usage"  
WebFetch: "https://dbpedia.org/ontology docs"

# 2. RDF-specific operations with semantic web tools
rdf_get https://dbpedia.org/sparql --cache-as dbpedia_service
rdf_get http://dbpedia.org/ontology/ --cache-as dbpedia_ontology
rdf_cache dbpedia_ontology --update-metadata "Uses standard RDFS confirmed via web research"

# 3. Apply semantic reasoning with discovered knowledge
cl_construct SC_Transitive --focus dbo:Person --endpoint dbpedia
```

## Discovery-First Workflow

**🚨 Critical Rule**: Always discover vocabulary before querying (like Read-before-Edit):

```bash
# ✅ ALWAYS discover vocabulary first
rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot
rdf_cache uniprot --graph  # Understand available classes/properties
cl_select "SELECT ?p WHERE {?p a up:Protein}" --endpoint uniprot

# ❌ NEVER guess URIs
cl_select "SELECT ?p WHERE {?p a uniprot:Protein}"  # WRONG - guessed prefix
```

## Quick Examples

### Biology Research
```bash
rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot
cl_search "insulin" --endpoint uniprot
cl_describe P01308 --endpoint uniprot
```

### Cross-Reference Following  
```bash
cl_search "caffeine" --limit 5                    # Find in Wikidata
cl_select "SELECT ?id WHERE {wd:Q60235 wdt:P662 ?id}"  # Get PubChem ID
```

### Vocabulary Navigation
```bash
rdf_cache foaf_vocab --graph                      # Read full ontology
rdf_cache --subclasses foaf:Agent                 # Find subclasses
rdf_cache --properties foaf:Person                # Valid properties
```

## Known Endpoints

CogitareLink includes built-in support for major semantic web endpoints:

- **`wikidata`** - General knowledge graph (225M+ entities)
- **`uniprot`** - Protein database (225B+ triples)
- **`wikipathways`** - Biological pathways
- **`dbpedia`** - Structured Wikipedia data

Use endpoint aliases for simple queries:
```bash
cl_select "SELECT ?o WHERE { dbo:Person rdfs:subClassOf ?o }" --endpoint dbpedia
cl_describe dbo:Person --endpoint dbpedia
cl_ask "{ dbo:Person rdfs:subClassOf ?o }" --endpoint dbpedia
```

## Requirements

- **Python 3.11+**
- **Claude Code** (designed specifically for Claude Code integration)

## Architecture: Extending Claude Code's Design Patterns

CogitareLink is architected as a **natural extension** to Claude Code's existing patterns, not a separate system. It follows Claude Code's core philosophy: simple, reliable, composable tools where intelligence lives in prompts, not complex code.

### Claude Code Architecture Extension

CogitareLink extends Claude Code's documented architecture patterns from `llmstxt/cc-arch/*`:

**1. Instruction-Driven Enhancement** (cc-arch-promts.txt)
- **Claude Code Pattern**: Tools provide capabilities, instructions focus intelligence in system prompts
- **CogitareLink Extension**: `cogitarelink` command loads semantic research methodology via instruction generator
- **Implementation**: Following Claude Code's prompt engineering with progressive disclosure and confidence building
- **Result**: Claude Code gets semantic web capabilities through enhanced prompting, not complex tool logic

**2. Tool Execution Pipeline** (cc-arch-tools.txt)
- **Claude Code Pattern**: Async generators with streaming progress, input validation (Zod), permission checks
- **CogitareLink Extension**: Same execution pipeline with RDF-specific input validation and discovery guardrails  
- **Implementation**: JSON output, error normalization, batch tool execution capabilities
- **Result**: Semantic tools feel native to Claude Code's execution environment

**3. Tool Composition Philosophy** (cc-arch-flow.txt)
- **Claude Code Pattern**: ReadTool → EditTool → Bash (file-based workflows)
- **CogitareLink Extension**: rdf_get → rdf_cache → cl_select (semantic-based workflows)
- **Implementation**: Natural composition between built-in tools (WebSearch, Task) and semantic tools
- **Result**: Unified workflow orchestration across file and semantic operations

**4. Progressive Tool Instructions** (cc-arch-promts.txt)
- **Claude Code Pattern**: "Opening with confidence", "Trust building", "Error normalization"
- **CogitareLink Extension**: Same instructional patterns for semantic web operations
- **Implementation**: "You can access any RDF endpoint", "SPARQL errors are normal", discovery-first guidance
- **Result**: Confidence-building instructions that prevent hesitation and over-validation

**5. Safety-First Design** (cc-arch-editing.txt)
- **Claude Code Pattern**: Read-before-Edit prevents unauthorized file modifications  
- **CogitareLink Extension**: discover-before-query prevents guessed URIs and vocabulary errors
- **Implementation**: Discovery workflow enforcement similar to Claude Code's editing guardrails
- **Result**: Same safety principles applied to semantic web operations

### Intelligence Distribution (cc-arch-inf.txt)

Following Claude Code's intelligence distribution model:

**Base Context** (Claude Code's System Prompt):
- Complete semantic web knowledge (RDF, SPARQL, JSON-LD 1.1)
- Ontology reasoning and vocabulary understanding  
- Cross-domain research methodologies and discovery patterns
- SHACL template reasoning and knowledge synthesis

**Tool Instructions** (CogitareLink's Progressive Disclosure):
- Endpoint-specific behaviors and quirks
- Discovery workflow enforcement ("ALWAYS discover vocabulary first")
- Cache system navigation patterns (`rdf_cache --graph`, metadata annotation)
- Error normalization ("SPARQL timeouts are normal", "Empty results expected")

**Runtime Execution** (Async Generator Pipeline):
- Clean JSON output for systematic analysis and jq composability
- ReadTool-style pagination with `--limit`, `--offset`, `next_page_command`
- Structured error handling with suggestions and recovery workflows
- Batch tool execution for parallel discovery operations

### Architectural Benefits

**1. Zero Learning Curve**: Users familiar with Claude Code patterns immediately understand semantic web workflows
**2. Tool Ecosystem Consistency**: All tools follow same JSON output, error handling, and composability patterns  
**3. Intelligence Centralization**: Semantic web expertise lives in Claude Code's base context, not scattered across tool implementations
**4. Natural Extensions**: WebSearch → rdf_get → cl_select feels like using built-in tools together
**5. Maintainable Simplicity**: Complex semantic reasoning happens in prompts, tools remain simple and reliable
**6. Progressive Enhancement**: Semantic capabilities layered on Claude Code without disrupting existing workflows

### Design Philosophy Alignment

CogitareLink directly implements Claude Code's documented architectural principles:

- **Instruction-Driven Enhancement**: Intelligence in prompts, capabilities in tools
- **Progressive Disclosure**: Tool instructions build confidence and prevent over-validation  
- **Safety-First Design**: Discovery workflows prevent errors like Read-before-Edit prevents unauthorized changes
- **JSON-First Composability**: All outputs designed for systematic analysis and tool chaining
- **Natural Tool Composition**: Semantic tools compose with built-in tools (WebSearch, Task, WebFetch)

This architecture enables sophisticated semantic web research while maintaining Claude Code's core design principles of simplicity, reliability, and composability, as documented in `llmstxt/cc-arch/*`.

## Learning & Prompting System: From Use Cases to Instructions

CogitareLink implements a **Software 2.0 learning system** that transforms real research sessions into optimized instruction prompts, following Claude Code's memory and auto-compact patterns.

### Use Case → Instruction Pipeline

**1. Session Capture** (Rich Narratives)
```markdown
# cogitarelink/patterns/use_cases/session_2024_06_18_dbpedia_discovery_workflow.md

**Domain**: semantic_reasoning, discovery_workflow  
**Goal**: Test complete discovery-first workflow with DBpedia

## Session Narrative
Started testing cl_construct tool with DBpedia after discovering cache system issues with UniProt vocabulary discovery. Used external research tools to determine DBpedia compatibility before testing SHACL templates.

**External Discovery Phase**:
Used Task tool to research "DBpedia ontology structure" and confirmed DBpedia uses standard RDFS vocabulary:
- ✅ Uses `rdfs:subClassOf` for class hierarchies  
- ✅ Uses `rdfs:subPropertyOf` for property hierarchies
```

**2. Pattern Distillation** (Claude Code Intelligence)
```python
# cogitarelink/prompts/instruction_generator.py

def generate_research_instructions(domain: str, goal: Optional[str] = None) -> str:
    """Generate Claude Code instructions from use case patterns."""
    
    domain_pattern = get_domain_pattern(domain)
    
    instructions = f"""RESEARCH_MODE: {domain}
GOAL: {goal or f"{domain} research session"}

{DISCOVERY_FIRST}

DOMAIN_FOCUS: {domain}
ENTITY_TYPES: {', '.join(domain_pattern['entity_types'])}
CROSS_REFERENCES: {', '.join(domain_pattern['cross_refs'])}
REASONING_PATTERN: {domain_pattern['reasoning_pattern']}
```

**3. Memory Consolidation** (CLAUDE.md Pattern)
```markdown
### Discovery-First Workflow
- Always use discovery-first workflow when working with unfamiliar endpoints (prevents 403 errors)
- Cache service descriptions early to avoid repeated discovery overhead

### Biology Research Patterns  
- Use Wikidata as discovery hub, then follow cross-references to domain databases
- P352 (UniProt protein ID) is highly reliable bridge property for protein research

### Anti-Patterns to Avoid
- NEVER assume all endpoints support Wikidata-style API search → UniProt needs FILTER patterns
- Don't try direct domain database search → cross-reference following is more reliable
```

### Instruction Prompting Architecture

**Base Context Loading** (`cogitarelink` command):
```python
def main():
    """CogitareLink: Print semantic research instructions to Claude Code context."""
    instructions = generate_general_research_instructions()
    print(instructions)
```

**Progressive Tool Reminders** (Following Claude Code's cc-arch-promts.txt):
```
⚡ cl_search reminders:
- Research first with WebSearch/Task (REF: tool-composition)
- Wikidata → API first (REF: discovery-first)
- Others → SPARQL fallback (REF: endpoint-behaviors)
- Cache findings with rdf_cache (REF: workflow-integration)
```

**Core Pattern Distribution** (cogitarelink/prompts/core_patterns.py):
```python
DISCOVERY_FIRST = """
RESEARCH_MODE_ACTIVE: universal_domain_discovery
CRITICAL_RULE: discover REQUIRED before any SPARQL queries

Basic workflow:
- rdf_get <endpoint> → Cache schema and capabilities
- cl_search "<query>" --limit 5 → ANALYZE discovery section first
- Follow composition_opportunities systematically
"""
```

### Learning System Benefits

**1. Session Intelligence**: Real research sessions become training data for better instructions
**2. Pattern Recognition**: Common workflows (discovery → cache → query) encoded as reminders  
**3. Anti-Pattern Prevention**: Failed approaches documented to prevent repetition
**4. Domain Specialization**: Biology, chemistry, geography patterns captured and reused
**5. Memory Compaction**: Like Claude Code's auto-compact, rich narratives become focused reminders

### Software 2.0 Philosophy

**Intelligence Distribution**:
- **Session Narratives**: Rich context about what worked/failed in real research
- **Pattern Distillation**: Claude Code analyzes narratives and extracts reusable patterns  
- **Instruction Generation**: Patterns become focused prompts that guide future sessions
- **Memory Evolution**: Instructions improve based on accumulated research experience

This creates a **self-improving research assistant** where each session makes the system better at semantic web research, following Claude Code's principle that intelligence lives in prompts, not code.

## Cache System: JSON-LD 1.1 Structured Knowledge

CogitareLink maintains a sophisticated cache system at `~/.cogitarelink/cache/` that stores RDF data in JSON-LD 1.1 format with semantic metadata for Claude Code navigation.

### Cache Structure

**Enhanced Cache Entries** with dual-layer architecture:
```json
{
  "data": {
    "@context": { "up": "http://purl.uniprot.org/core/" },
    "@graph": [ /* JSON-LD 1.1 normalized RDF data */ ]
  },
  "semantic_metadata": {
    "semantic_type": "vocabulary|service_description|ontology",
    "domains": ["biology", "chemistry"], 
    "format_type": "turtle|json-ld|rdf-xml",
    "purpose": "schema_definition|term_mapping|endpoint_capability",
    "vocabulary_size": 1543,
    "provides": {"classes": 45, "properties": 120},
    "usage_patterns": ["SPARQL_construct_reasoning", "cross_reference_lookup"]
  },
  "cached_at": 1703875200.0,
  "ttl_seconds": 86400
}
```

### How Claude Navigates Cached Knowledge

**1. Vocabulary Discovery via rdf_cache**:
```bash
rdf_cache "protein" --type class  # Searches JSON-LD @graph for rdfs:Class entities
# Returns: up:Protein, up:Gene with full URIs from cached context
```

**2. Semantic Metadata Analysis**:
```bash  
rdf_cache foaf_vocab --graph  # Loads complete JSON-LD graph for analysis
# Claude analyzes @context mappings, class hierarchies, property domains/ranges
```

**3. Cross-Reference Navigation**:
```bash
rdf_cache --subclasses foaf:Agent  # Traverses rdfs:subClassOf in cached graph
rdf_cache --properties foaf:Person # Finds rdfs:domain/range relationships  
```

**4. Claude's Intelligence Integration**:
- **Context Awareness**: Uses JSON-LD @context for prefix expansion (`dbo:Person` → `http://dbpedia.org/ontology/Person`)
- **Graph Reasoning**: Analyzes rdfs:subClassOf, owl:equivalentClass relationships in normalized JSON-LD @graph
- **Semantic Typing**: Leverages metadata to understand vocabulary purpose and scope (biology vs general knowledge)
- **Discovery Workflows**: Follows cached breadcrumbs to build comprehensive SPARQL queries with real URIs
- **Metadata Annotation**: Claude adds semantic_metadata through `rdf_cache --update-metadata` for workflow optimization

### Cache Benefits for Discovery

- **JSON-LD 1.1 Standard**: All RDF formats normalized to consistent JSON-LD representation
- **Semantic Metadata**: Claude understands vocabulary scope, purpose, and relationships  
- **Efficient Navigation**: Fast disk-based lookup (diskcache) with structured semantic search
- **Discovery-First Enforcement**: Prevents guessed URIs by requiring cached vocabulary first
- **Cross-Tool Consistency**: All SPARQL tools use same cached vocabulary and prefixes

## Development

```bash
# Setup
git clone https://github.com/LA3D/Cogitarelink.git
cd Cogitarelink
uv sync
uv pip install -e .

# Test
uv run pytest tests/ -v
```

## License

MIT - See LICENSE file for details.

---

**Remember**: These are reminders, not tutorials. The tools work like Claude Code's file tools - simple, reliable, composable. Intelligence comes from Claude Code's reasoning, not complex tool logic.