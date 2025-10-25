# CogitareLink Technical Architecture

## Executive Overview

CogitareLink is a semantic web tool suite (~6,600 lines of Python) designed specifically for AI agents like Claude Code. It provides seven simple, composable CLI tools for discovering, caching, and querying RDF/semantic data. The architecture prioritizes:

- **Discovery-First Workflows**: Always discover vocabulary before querying (prevents hallucinated URIs)
- **Cache-Driven Intelligence**: Store structured semantic data Claude can reason over
- **Composable Tools**: Work seamlessly with Claude Code's built-in capabilities
- **Agent-Optimized Output**: JSON responses for systematic analysis, not human-readable text

## Package Structure

```
cogitarelink/                       # Main package
├── backend/                        # Core semantic web operations
│   ├── cache.py                   # Disk-based RDF caching (313 lines)
│   ├── content.py                 # Content structure analysis (183 lines)
│   ├── sparql.py                  # SPARQL endpoint management (318 lines)
│   └── __init__.py                # Public API exports
├── cli/                           # Seven main tools (~2,900 lines total)
│   ├── rdf_get.py                # Fetch & cache RDF content (799 lines)
│   ├── rdf_cache.py              # Search/navigate cached vocabularies (1,248 lines)
│   ├── cl_search.py              # Entity search across endpoints (236 lines)
│   ├── cl_select.py              # SELECT SPARQL query execution (273 lines)
│   ├── cl_describe.py            # DESCRIBE entity queries (171 lines)
│   ├── cl_ask.py                 # Boolean ASK fact verification (156 lines)
│   ├── cl_construct.py           # SHACL template reasoning (818 lines)
│   ├── cogitarelink.py           # Main entry point (23 lines)
│   └── __init__.py
├── prompts/                       # Instruction generation for Claude Code
│   ├── instruction_generator.py  # Generates domain-specific instructions (1,627 lines)
│   └── core_patterns.py          # Core research patterns (351 lines)
├── utils/                         # Shared utilities
│   ├── logging.py                # Structured logging system
│   └── __init__.py
├── patterns/                      # Pattern learning system
│   ├── use_cases/                # Session capture templates
│   └── README.md                 # Learning approach documentation
├── data/
│   └── system/
│       ├── obqc.ttl              # Ontology rules
│       └── rules.ttl             # SHACL templates
└── __init__.py

tests/                            # Test suite (~15 test files)
pyproject.toml                    # Project metadata & dependencies
CLAUDE.md                         # Guidance for Claude Code sessions
```

## Core Dependencies

From `pyproject.toml`:
- **Click** (8.2.1+) - CLI framework
- **httpx** (0.28.1+) - HTTP client with redirects
- **RDFlib** (7.1.4+) - RDF parsing/serialization
- **pyld** (2.0.4+) - JSON-LD processing
- **SPARQLWrapper** (2.0.0+) - SPARQL query execution
- **pyshacl** (0.30.1+) - SHACL validation/reasoning
- **diskcache** (5.6.3+) - Disk-based caching
- **pydantic** (2.11.5+) - Data validation
- **claude-code-sdk** (0.0.10+) - Claude Code integration

## Architecture Patterns

### 1. Backend: Semantic Web Operations

#### `backend/sparql.py` (318 lines)

**Core Class: SPARQLEngine**
- Static endpoint configuration for known endpoints (Wikidata, UniProt, WikiPathways, DBpedia)
- Each endpoint defines:
  - URL
  - Namespace prefixes
  - Query patterns
  - Usage guidance

**Key Functions:**
```
- resolve_endpoint(endpoint_name: str) → (url: str, prefixes: Dict)
  Resolves endpoint name to URL and prefixes with fallback chain:
  1. KNOWN_ENDPOINTS (hardcoded, highest priority)
  2. Cached endpoints (from service descriptions)
  3. Dynamic discovery (via Wikidata query)
  4. Error if not found anywhere

- get_all_endpoints() → Dict[str, str]
  Aggregates endpoints from all sources (known + discovered + cached)

- build_prefixed_query(query: str, endpoint: str) → str
  Prepends appropriate PREFIX declarations to SPARQL queries

- discover_sparql_endpoints_dynamic() → Dict[str, str]
  Queries Wikidata for databases with SPARQL endpoints (P5305 property)
  Results cached for 24 hours to avoid repeated network calls

- get_entity_uri(entity: str, endpoint_url: str) → str
  Converts entity identifiers to full URIs based on endpoint type
  Handles prefixed entities (up:Protein), ID patterns (Q, P, WP), and full URIs

- find_endpoint_for_entity(entity: str) → Optional[str]
  Auto-detects endpoint based on entity ID format
  (Q/P → Wikidata, WP → WikiPathways, 6-char alphanumeric → UniProt)

Data Structures:
- DiscoveryResult: endpoint, url, prefixes, patterns, guidance
```

**Known Endpoints (Built-In):**
1. **wikidata** (https://query.wikidata.org/sparql)
   - Prefixes: wd, wdt, p, ps, pq, rdfs, wikibase, bd
   - Guidance: Use wdt: for direct properties, SERVICE wikibase:label for labels

2. **uniprot** (https://sparql.uniprot.org/sparql)
   - Prefixes: up, uniprotkb, rdfs, taxon
   - Guidance: up:Protein for proteins, up:recommendedName for names

3. **wikipathways** (https://sparql.wikipathways.org/sparql)
   - Prefixes: wp, gpml, dcterms, rdfs
   - Guidance: wp:Pathway for pathways, dcterms:title for names

4. **dbpedia** (https://dbpedia.org/sparql)
   - Prefixes: dbo, dbr, dct, rdfs, owl, foaf
   - Guidance: dbo: for ontology, dbr: for resources, filter by LANG

#### `backend/cache.py` (313 lines)

**Cache Architecture:**
Uses diskcache library for disk-based caching with TTL support. Cache stored at `~/.cogitarelink/cache/`.

**Data Classes:**
```python
@dataclass
class SemanticMetadata:
    semantic_type: str                  # "vocabulary", "context", "service", "schema"
    domains: List[str]                  # ["biology", "chemistry", "general"]
    format_type: str                    # "turtle", "json-ld", "rdf-xml"
    purpose: str                        # "schema_definition", "term_mapping", "endpoint_capability"
    dependencies: List[str]             # Other vocabularies this builds on
    provides: Dict[str, int]            # {"classes": 45, "properties": 120}
    confidence_scores: Dict[str, float] # Classification confidence metrics
    vocabulary_size: int                # Number of terms/triples
    learned_at: float                   # UNIX timestamp of semantic analysis
    usage_patterns: List[str]           # Common usage patterns discovered

@dataclass
class EnhancedCacheEntry:
    data: Dict[str, Any]                # Full RDF data (raw, expanded, enhanced)
    semantic_metadata: Optional[SemanticMetadata]
    cached_at: float                    # UNIX timestamp
    ttl_seconds: int = 86400            # Default 24 hours
    
    @property
    def is_expired(bool)
    
@dataclass
class CachedSchema:
    endpoint: str
    prefixes: Dict[str, str]
    classes: Dict[str, Any]
    properties: Dict[str, Any]
    patterns: Dict[str, str]
    cached_at: float
    ttl_seconds: int = 3600             # Default 1 hour
```

**CacheManager Class Methods:**
```
- get(key: str) → Optional[Any]
  Retrieves cached data with TTL checking
  
- get_enhanced(key: str) → Optional[EnhancedCacheEntry]
  Retrieves cache entry with semantic metadata
  Handles legacy format migration
  
- set(key: str, data: Any, ttl: int = 3600)
  Stores data with TTL expiration
  
- set_enhanced(key: str, data: Dict, metadata: Optional[SemanticMetadata], ttl: int)
  Stores with semantic metadata for context-aware analysis
  
- update_semantic_metadata(key: str, metadata: SemanticMetadata) → bool
  Updates semantic understanding for cached item
  
- list_by_semantic_type(type: str) → List[str]
  Find vocabularies by classification (vocabulary, context, service)
  
- list_by_domain(domain: str) → List[str]
  Find vocabularies by domain (biology, chemistry, etc.)
  
- set_schema(endpoint: str, prefixes, classes, properties, patterns)
  Cache endpoint schema information
```

**Cache Key Naming Convention:**
- RDF content: `rdf:{name}` (e.g., `rdf:foaf_vocab`, `rdf:uniprot_service`)
- Schema info: `schema:{endpoint}` (e.g., `schema:wikidata`)

#### `backend/content.py` (183 lines)

**ContentAnalyzer Class**
Provides basic structural analysis without hardcoded classification (Claude does interpretation).

**Key Methods:**
```
- analyze_content_structure(data: Dict, url: str = "") → Dict
  Returns basic metrics for Claude reasoning:
  - format detection (json-ld, turtle, etc.)
  - vocabulary size
  - content counts (classes, properties, namespaces)
  - structural patterns (has_context, has_type_declarations)
  - references and dependencies
  
- _determine_format(data: Dict) → str
  Detects RDF format from data structure
  
- _extract_content_metrics(data: Dict) → Dict[str, int]
  Counts classes, properties, namespaces, triples
  
- _detect_structural_patterns(data: Dict) → Dict
  Identifies JSON-LD features, SHACL patterns, query templates
  
- _extract_references(data: Dict) → Dict[str, List[str]]
  Extracts dependencies on other vocabularies (schema.org, PROV, FOAF, etc.)
```

### 2. CLI Tools: The Seven Semantic Web Tools

Entry point: `pyproject.toml` [project.scripts] defines CLI commands

#### Tool 1: `rdf_get` (799 lines)

**Purpose**: Fetch RDF from any URL with content negotiation and caching

**Command**:
```bash
rdf_get URL [--format FORMAT] [--cache-as NAME] [--discover]
```

**Key Features:**
1. **Content Negotiation**: Tries formats in priority order
   - Default: application/ld+json → text/turtle → application/rdf+xml → text/n3 → application/n-triples
   - Custom: `--format turtle` changes priority

2. **RDF Format Parsing**: 
   - JSON-LD: Parsed directly, expanded with pyld.expand()
   - Turtle/RDF-XML/N3/N-Triples: Parsed with RDFLib, converted to JSON-LD for consistency
   - Creates enhanced JSON-LD 1.1 structure with @container patterns

3. **Enhanced JSON-LD 1.1 Structure**:
   ```json
   {
     "format": "json-ld",
     "raw": {...},                          // Original document
     "expanded": [...],                     // Expanded form for semantic analysis
     "enhanced": {                          // Claude-reasoning-optimized structure
       "@context": { "@version": 1.1, ... },
       "classes": {"ClassName": {"@id": "...", "@type": [...], "domain": "..." }},
       "properties": {"propName": {"@id": "...", "@type": [...], "domain": "..." }},
       "namespaces": {"prefix": "http://..."},
       "domains": {"biology": {"@graph": [...]}},
       "semantic_index": {
         "class_hierarchy": {...},          // rdfs:subClassOf relationships
         "property_constraints": {...},     // rdfs:domain/range
         "concept_schemes": {...},          // SKOS broader/narrower
         "cross_references": {...},         // rdfs:seeAlso
         "equivalences": {...}              // owl:equivalentClass/sameAs
       },
       "graph_metadata": {
         "size_bytes": 1024,
         "triples_count": 50,
         "safe_to_load": true
       }
     }
   }
   ```

4. **Cache Checking**:
   - Prevents duplicate caching of same content
   - Checks both exact cache names and URL variations
   - Returns cached data without re-fetching

5. **Output**: JSON with jq compatibility
   - `success`: boolean
   - `data`: full enhanced RDF structure
   - `cache_key`: if cached
   - `cached`: boolean if caching occurred
   - `execution_time_ms`: performance metric
   - `claude_guidance`: instructions for next steps

**Helper Functions**:
```
- get_accept_headers(format_pref: Optional[str]) → list[str]
  Returns Accept headers in priority order

- parse_rdf_response(response, content_type) → Optional[Dict]
  Parses HTTP response into enhanced JSON-LD structure
  Handles both JSON-LD and serialized RDF formats

- create_enhanced_vocabulary_index(raw_data, expanded_data) → Dict
  Creates JSON-LD 1.1 @container structure for fast vocabulary navigation
  Extracts classes, properties, semantic relationships
  Generates domain-specific query templates

- extract_ontology_metadata(expanded_data) → Dict
  Extracts Dublin Core + OWL versioning metadata

- extract_semantic_relationships(enhanced, expanded_data)
  Populates semantic_index with RDFS/OWL/SKOS relationships
  - Class hierarchies (rdfs:subClassOf)
  - Property constraints (rdfs:domain/range)
  - SKOS concept schemes (skos:broader/narrower)
  - OWL equivalences (owl:equivalentClass, owl:sameAs)
  - Cross-references (rdfs:seeAlso)
```

#### Tool 2: `rdf_cache` (1,248 lines)

**Purpose**: Search and navigate cached RDF vocabularies for discovery-driven workflows

**Commands**:
```bash
rdf_cache QUERY [--type TYPE] [--list] [--graph] [--force]
rdf_cache [--subclasses URI] [--properties URI] [--related URI]
rdf_cache [--clear] [--clear-item NAME]
rdf_cache CACHE_NAME --update-metadata JSON
```

**Query Modes**:

1. **Full Ontology Mode** (`--graph`):
   - Loads complete cached vocabulary
   - Size guardrails (500KB default limit, override with `--force`)
   - Returns structured navigation aid + full ontology

2. **Search Mode**:
   - Navigates in-memory @container @index structures
   - Fast vocabulary term lookup
   - Filter by type (class, property, namespace, template)

3. **Semantic Navigation** (`--subclasses`, `--properties`, `--related`):
   - Traverses RDFS subclass hierarchies
   - Finds properties with given domain/range
   - Explores SKOS/OWL relationships

4. **Cache Management**:
   - `--list`: Show all cached vocabularies with metadata
   - `--clear`: Clear all RDF cache
   - `--clear-item`: Remove specific vocabulary
   - `--update-metadata`: Store Claude's semantic analysis

**Key Algorithms**:

```
load_all_enhanced_indices() → Dict[str, Dict]
  Loads all rdf:* entries into memory
  Extracts JSON-LD 1.1 @container @index structures
  Ready for fast in-memory navigation

navigate_vocabulary_indices(indices, query, result_type) → List[Dict]
  Walks through @container @index classes/properties
  Case-insensitive substring matching
  Returns context information for each match

search_enhanced_structure(enhanced: Dict, query: str, result_type) → List[Dict]
  Navigates @container @index patterns for fast vocabulary lookup
  Searches: classes, properties, namespaces, domains, templates

navigate_semantic_relationships(subclasses, properties, related)
  Traverse loaded semantic_index structures
  - rdfs:subClassOf for class hierarchies
  - rdfs:domain/range for property relationships
  - SKOS/OWL relationships for concept schemes

extract_relevant_subgraphs(indices, matches, query) → List[Dict]
  Extracts JSON path from semantic_index based on discovered vocabulary
```

**Output Structure**:
```json
{
  "query": "protein",
  "results": [
    {
      "type": "class",
      "value": "Protein → http://purl.uniprot.org/core/Protein",
      "context": {
        "id": "http://purl.uniprot.org/core/Protein",
        "name": "Protein",
        "domain": "biology",
        "types": ["rdfs:Class"]
      }
    }
  ],
  "cache_keys": ["rdf:uniprot_vocab"],
  "claude_guidance": {
    "discovered_vocabulary": {"classes_found": [...], "total_classes": 5},
    "query_templates": ["SELECT ?item ?label WHERE { ?item a <...> ; rdfs:label ?label }"],
    "next_actions": ["Ready: cl_select \"...\""]}
}
```

#### Tool 3: `cl_search` (236 lines)

**Purpose**: Find entities across semantic endpoints

**Command**:
```bash
cl_search QUERY [--endpoint ENDPOINT] [--limit LIMIT] [--offset OFFSET]
```

**Endpoints**:
- `wikidata` (default): Uses efficient Wikidata API (wbsearchentities)
- `uniprot`, `wikipathways`: Fall back to SPARQL text search
- Custom URL: Any SPARQL endpoint

**Key Functions**:

```
search_wikidata_api(query, limit, offset) → Dict
  Uses Wikidata API (/w/api.php?action=wbsearchentities)
  Better performance than SPARQL for entity search
  Returns paginated results with has_more flag

search_sparql_endpoint(query, limit, offset, endpoint_url) → Dict
  Generic SPARQL text search:
  SELECT ?entity ?label WHERE {
    ?entity rdfs:label ?label .
    FILTER(LANG(?label) = "en")
    FILTER(CONTAINS(LCASE(?label), LCASE("query")))
  }
  OFFSET {offset} LIMIT {limit}
```

**Output**:
```json
{
  "query": "insulin",
  "results": [
    {
      "id": "Q28399",
      "label": "insulin",
      "description": "protein",
      "url": "http://www.wikidata.org/entity/Q28399"
    }
  ],
  "count": 1,
  "has_more": false,
  "next_page_command": "cl_search \"insulin\" --limit 10 --offset 10"
}
```

#### Tool 4: `cl_select` (273 lines)

**Purpose**: Execute SELECT SPARQL queries with validation and pagination

**Command**:
```bash
cl_select "SELECT ... WHERE { ... }" [--endpoint ENDPOINT] [--limit N] [--offset N] [--timeout SECONDS]
```

**Workflow Guardrails**:
1. Validates SELECT query syntax:
   - Must start with SELECT
   - Must have WHERE clause
   - Must contain variables (?s, ?p, ?o)
   - Must have graph pattern in braces

2. Automatic prefix addition via `build_prefixed_query()`

3. Pagination support (ReadTool-style exploration)
   - OFFSET/LIMIT injected automatically
   - Next page hints provided

4. Vocabulary discovery check:
   - Reminds Claude to use rdf_get/rdf_cache before querying
   - Prevents guessing unknown URIs

**Output**:
```json
{
  "query": "SELECT ?p ?o WHERE { wd:Q28399 ?p ?o }",
  "endpoint": "wikidata",
  "results": [...],
  "count": 20,
  "offset": 0,
  "limit": 20,
  "has_more": true,
  "next_page_command": "cl_select \"...\" --offset 20",
  "execution_time_ms": 150.0
}
```

#### Tool 5: `cl_describe` (171 lines)

**Purpose**: Get complete RDF data about an entity

**Command**:
```bash
cl_describe ENTITY [--endpoint ENDPOINT] [--timeout SECONDS]
```

**Entity Validation**:
- Wikidata IDs: Q905695, P352
- UniProt IDs: 6-char alphanumeric
- WikiPathways IDs: WP*
- Prefixed: wd:Q905695, up:P01308
- Full URIs: http://...

**Endpoint Auto-Detection**:
- Q/P → Wikidata
- WP* → WikiPathways
- 6-char alphanumeric → UniProt

**RDF Format Handling**:
- Auto-detects Accept header per endpoint
- Parses to JSON-LD for Claude
- Returns complete entity graph

**Output**:
```json
{
  "entity": "Q28399",
  "entity_uri": "http://www.wikidata.org/entity/Q28399",
  "endpoint": "wikidata",
  "data": { "@context": {...}, "@graph": [...] },
  "execution_time_ms": 250.0
}
```

#### Tool 6: `cl_ask` (156 lines)

**Purpose**: Boolean fact verification queries

**Command**:
```bash
cl_ask "ASK { ... }" [--endpoint ENDPOINT] [--timeout SECONDS]
cl_ask "{ ?s ?p ?o }" # ASK added automatically
```

**Validation**:
- Must start with ASK (or prefix is added)
- Must have graph pattern in braces
- Pattern cannot be empty

**Output**:
```json
{
  "query": "ASK { wd:Q28399 wdt:P31 wd:Q11344 }",
  "result": true,
  "endpoint": "wikidata",
  "execution_time_ms": 100.0
}
```

#### Tool 7: `cl_construct` (818 lines)

**Purpose**: Apply SHACL reasoning templates for knowledge synthesis

**Command**:
```bash
cl_construct TEMPLATE [--focus ENTITY] [--endpoint ENDPOINT] [--cache-as NAME] [--limit N]
cl_construct --list-templates
cl_construct --describe TEMPLATE
```

**SHACL Templates** (hardcoded in SHACL_TEMPLATES dict):

1. **SC_Transitive** - Subclass Transitivity
   ```sparql
   CONSTRUCT { ?c1 rdfs:subClassOf ?c3 }
   WHERE { 
     ?c1 rdfs:subClassOf ?c2 .
     ?c2 rdfs:subClassOf ?c3 .
     FILTER NOT EXISTS { ?c1 rdfs:subClassOf ?c3 }
   }
   ```

2. **SP_Transitive** - Subproperty Transitivity

3. **DomainEnt** - Domain Entailment
   - Infer types from property domains: P rdfs:domain D, S P O → S a D

4. **RangeEnt** - Range Entailment
   - Infer types from property ranges: P rdfs:range R, S P O → O a R

5. **SchemaDomainEnt** - Schema.org Domain Hints (soft inference, 0.6 confidence)

6. **InverseEnt** - Inverse Property Entailment
   - Apply inverse properties: P owl:inverseOf Q, S P O → O Q S

**Output**:
- CONSTRUCT query results (typically JSON-LD)
- Optional caching with `--cache-as`
- Materialized knowledge facts

### 3. Prompt System: Claude Code-Inspired Instruction Injection

**Key Insight**: CogitareLink follows Claude Code's architecture where **intelligence lives in prompts, not complex code**. The tools are simple; the sophistication comes from injected instructions.

#### Architecture: Prompt Injection via stdout

**The Pattern** (inspired by Claude Code's tool reminders):

```
User runs command → CLI prints instructions to stdout → Claude Code captures as context
```

**Entry Point**: `cogitarelink/cli/cogitarelink.py` (23 lines)

```python
from ..prompts.instruction_generator import generate_general_research_instructions

def main():
    """Print semantic research instructions directly to Claude Code context."""
    instructions = generate_general_research_instructions()
    print(instructions)  # ← Claude Code captures this as contextual instructions
```

When a user (or Claude) runs the `cogitarelink` command, it doesn't perform operations - it **injects methodology instructions** into Claude's working context.

#### Two-Layer Prompt Architecture

**Layer 1: Core Patterns** (`prompts/core_patterns.py` - 351 lines)

Module-level string constants that are **designed to be edited** when better patterns are discovered:

```python
# Editable instruction strings (not code)
DISCOVERY_FIRST = """
RESEARCH_MODE_ACTIVE: universal_domain_discovery
CRITICAL_RULE: cl_discover REQUIRED before any SPARQL queries (-$1000 penalty for violations)

Basic workflow:
- cl_discover <endpoint> → Cache schema and capabilities
- cl_search "<query>" --limit 5 → ANALYZE universal_discovery section first
...
"""

CACHE_OPTIMIZATION = """
CACHE_STRATEGY_ACTIVE: claude_code_methodology
PRINCIPLE: READ→VERIFY→Cache for 200x performance gains
...
"""

COMPOSITION_GUIDANCE = """
SYSTEMATIC_RESEARCH_ACTIVE: composition_opportunities
PRINCIPLE: Follow structured suggestions rather than ad-hoc exploration
...
"""

STRUCTURED_ANALYSIS = """
METADATA_ANALYSIS_ENFORCEMENT:
When using cl_search, wrap your analysis in <cogitarelink_analysis> tags:
...
"""

DOMAIN_PATTERNS = {
    "biology": {
        "entity_types": ["Q8054", "Q898273"],  # protein, gene
        "cross_refs": ["P352", "P594"],        # UniProt, Ensembl
        "reasoning_pattern": "Structure → Function → Interactions → Pathways",
        "databases": ["uniprot", "pdb"],
        ...
    },
    "chemistry": {...},
    "medical": {...},
    # 8 total domains with cross-domain bridges
}

CROSS_DOMAIN_BRIDGES = {
    ("biology", "chemistry"): {
        "connection_type": "protein_drug_interactions",
        "workflow": "protein → drug targets → compounds → bioactivity"
    },
    ...
}
```

**Why This Works**: These aren't rules enforced by code - they're **reminders for Claude's reasoning**. When Claude sees "CRITICAL_RULE: cl_discover REQUIRED", it's a strong signal in the prompt, not a technical constraint.

**Layer 2: Instruction Generator** (`prompts/instruction_generator.py` - 1,627 lines)

Functions that **compose** core patterns into contextual instructions:

```python
def generate_general_research_instructions() -> str:
    """Compose core patterns into general semantic research methodology.

    Returns markdown-formatted instructions that Claude Code reads as context.
    """
    return """🔬 SEMANTIC RESEARCH MODE ACTIVATED

## Tool Composition: Natural Extensions to Claude Code

**CRITICAL INSIGHT**: Semantic web tools are natural extensions to Claude Code's
built-in capabilities, not separate systems.

### Integrated Discovery Workflows
```bash
# 1. Domain research with built-in tools
Task: "Research DBpedia ontology structure"
WebSearch: "UniProt RDF vocabulary usage"
WebFetch: "https://dbpedia.org/ontology docs"

# 2. RDF-specific operations
rdf_get https://dbpedia.org/sparql --cache-as dbpedia_service
rdf_cache dbpedia_ontology --graph

# 3. Apply semantic reasoning with combined intelligence
cl_construct SP_Transitive --focus dbo:Person
```

**Tool Composition Patterns**:
- ✅ WebSearch → rdf_get → rdf_cache → cl_select (research then query)
- ✅ Task → cl_search → WebFetch → cl_describe (investigate then validate)
...
"""

def generate_research_instructions(domain: str, goal: Optional[str]) -> str:
    """Generate domain-specific instructions by composing patterns."""
    domain_pattern = get_domain_pattern(domain)

    return f"""RESEARCH_MODE: {domain}
GOAL: {goal or f"{domain} research session"}

{DISCOVERY_FIRST}

DOMAIN_FOCUS: {domain}
ENTITY_TYPES: {', '.join(domain_pattern['entity_types'])}
CROSS_REFERENCES: {', '.join(domain_pattern['cross_refs'])}
REASONING_PATTERN: {domain_pattern['reasoning_pattern']}

{COMPOSITION_GUIDANCE}
{CACHE_OPTIMIZATION}
...
"""

def generate_pattern_reminder(pattern_name: str, domain: Optional[str]) -> str:
    """Return specific pattern slice for focused injection."""
    if pattern_name == "discovery_first":
        return DISCOVERY_FIRST
    elif pattern_name == "cache_aware":
        return CACHE_OPTIMIZATION
    ...
```

#### How Instructions Flow Into Claude Code

**Mechanism 1: Direct Command Execution**

```bash
$ cogitarelink
# Prints to stdout → Claude Code captures as context:
🔬 SEMANTIC RESEARCH MODE ACTIVATED
## Tool Composition: Natural Extensions to Claude Code
...
```

**Mechanism 2: Tool Output Injection** (future pattern)

Each CLI tool could inject mini-reminders in their JSON output:

```json
{
  "results": [...],
  "claude_guidance": {
    "pattern_reminder": "Remember: discovery-first workflow (REF: DISCOVERY_FIRST)",
    "next_actions": ["Use rdf_cache to read vocabulary before querying"]
  }
}
```

**Mechanism 3: CLAUDE.md Project Instructions**

The repo's `CLAUDE.md` file contains high-level patterns that Claude Code loads automatically:

```markdown
## Critical Reminders

### 🚨 DISCOVERY-FIRST RULE (like Read-before-Edit)
```bash
# ✅ ALWAYS discover vocabulary first
rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot
rdf_cache uniprot --graph
```
```

#### Why This Architecture Works (Claude Code Pattern)

**1. Intelligence Distribution**:
- **Simple tools**: 7 CLI commands with basic validation
- **Complex reasoning**: Lives in injected prompts Claude interprets
- Like Claude Code's `Read` tool: simple file reader + sophisticated usage patterns

**2. Editable Instructions**:
- Change behavior by editing `DISCOVERY_FIRST` string, not refactoring code
- Add domain by updating `DOMAIN_PATTERNS` dict
- No complex rule engines or validators

**3. Composable Context**:
- `generate_general_research_instructions()`: Full methodology
- `generate_pattern_reminder("cache_aware")`: Specific reminder slice
- `generate_research_instructions("biology")`: Domain-focused instructions

**4. Natural Language Reasoning**:
- "-$1000 penalty for violations" → Strong signal for Claude's value system
- "Like ReadTool: systematic exploration" → Leverage existing mental models
- "✅ / ❌" → Visual pattern matching

**5. Self-Improving System**:
- Comments like "Edit this when users skip discovery steps"
- Pattern learning captured in `patterns/use_cases/` (markdown narratives)
- Claude distills session narratives → updates `DISCOVERY_FIRST` string

#### Core Functions Reference

```python
# Instruction Generation
generate_general_research_instructions() → str
  Full semantic research methodology for Claude Code

generate_research_instructions(domain: str, goal: Optional[str]) → str
  Domain-specific methodology (biology, chemistry, medical, etc.)

generate_pattern_reminder(pattern_name: str, domain: Optional[str]) → str
  Focused pattern injection ("discovery_first", "cache_aware", etc.)

# Pattern Retrieval
get_domain_pattern(domain: str) → Dict
  Returns: entity_types, cross_refs, reasoning_pattern, databases,
           search_examples, success_indicators

get_cross_domain_bridge(from_domain: str, to_domain: str) → Dict
  Returns: connection_type, bridge_terms, workflow
  Example: ("biology", "chemistry") → protein_drug_interactions

# Domain Patterns (8 domains)
DOMAIN_PATTERNS["biology"] = {...}
DOMAIN_PATTERNS["chemistry"] = {...}
DOMAIN_PATTERNS["medical"] = {...}
DOMAIN_PATTERNS["geographic"] = {...}
DOMAIN_PATTERNS["cultural"] = {...}
DOMAIN_PATTERNS["history"] = {...}
DOMAIN_PATTERNS["bibliographic"] = {...}
DOMAIN_PATTERNS["technical"] = {...}
```

### 4. Entry Point: How Users Trigger Injection

**CLI Entry** (`pyproject.toml`):

```toml
[project.scripts]
cogitarelink = "cogitarelink.cli.cogitarelink:main"
```

**Usage**:

```bash
# User or Claude runs this
$ cogitarelink

# Output injected into Claude's context:
🔬 SEMANTIC RESEARCH MODE ACTIVATED
...
```

**Alternative Pattern** (not yet implemented):

```python
# Could inject per-tool reminders
def search(...):
    result = do_search(...)
    result["claude_reminder"] = generate_pattern_reminder("discovery_first")
    return result
```

## Data Flow Patterns

### Discovery Workflow: The Core Pattern

```
User Query
    ↓
Claude Code analyzes query domain
    ↓
1. DISCOVERY: rdf_get ENDPOINT --cache-as vocab_name
   → Fetches RDF, creates enhanced JSON-LD structure
   → Stores in ~/.cogitarelink/cache/
    ↓
2. CACHING & UNDERSTANDING: rdf_cache vocab_name --graph
   → Claude reads complete ontology from cache
   → Analyzes class/property hierarchies
   → Optional: rdf_cache --update-metadata (store analysis)
    ↓
3. VOCABULARY-DRIVEN SEARCH: cl_search "entity_name" --endpoint endpoint
   → Uses discovered vocabulary to understand search domain
   → Returns entities with URIs ready for querying
    ↓
4. DATA EXPLORATION: cl_select "SELECT ?p ?o WHERE { DISCOVERED_URI ?p ?o }"
   → Uses only URIs from vocabulary discovery
   → NEVER guesses unknown URIs
    ↓
5. KNOWLEDGE SYNTHESIS: cl_construct TEMPLATE --focus URI --endpoint endpoint
   → Applies SHACL reasoning templates
   → Materializes new facts from ontology
    ↓
Synthesized Results to User
```

### Cache Architecture in Practice

**Physical Location**: `~/.cogitarelink/cache/` (automatically created on first use)

**Storage Technology**: `diskcache` library (SQLite-backed, cross-platform, ACID compliant)

**Cache Initialization** (from `backend/cache.py:73-79`):
```python
class CacheManager:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".cogitarelink" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = dc.Cache(str(self.cache_dir))
```

**What Gets Cached**:

1. **RDF Content** (key: `rdf:{name}`):
   - Enhanced JSON-LD structures with semantic indices
   - Complete vocabularies/ontologies (FOAF, UniProt Core, etc.)
   - Service descriptions from SPARQL endpoints
   - TTL: 24 hours (86400 seconds)

2. **Schema Information** (key: `schema:{endpoint}`):
   - Endpoint prefixes and namespaces
   - Available classes and properties
   - Query patterns and templates
   - TTL: 1 hour (3600 seconds)

3. **Dynamic Endpoint Discovery** (key: `sparql_endpoints`):
   - Wikidata-discovered SPARQL endpoints
   - TTL: 24 hours

**Cache Entry Structure**:

```python
EnhancedCacheEntry {
    data: Dict[str, Any]                    # Full RDF data
    semantic_metadata: SemanticMetadata {
        semantic_type: "vocabulary"          # vocabulary|context|service|schema
        domains: ["biology", "chemistry"]    # Domain classification
        format_type: "json-ld"              # Original format
        purpose: "schema_definition"         # What this provides
        dependencies: ["rdfs", "owl"]       # What it builds on
        provides: {                         # What it contains
            "classes": 45,
            "properties": 120,
            "contexts": 1
        }
        confidence_scores: {"domain": 0.95} # Classification confidence
        vocabulary_size: 165                # Total terms
        learned_at: 1697824321.5           # UNIX timestamp
        usage_patterns: [...]               # Discovered patterns
    }
    cached_at: 1697824321.5                # UNIX timestamp
    ttl_seconds: 86400                     # Expiration time
}
```

**Example Cache Contents**:

```
~/.cogitarelink/cache/ (diskcache database)
├── rdf:foaf_vocab                       # FOAF ontology (social networking)
│   └── {data: {...}, semantic_metadata: {...}, cached_at: ..., ttl: 86400}
├── rdf:uniprot_service                  # UniProt service description
│   └── {data: {...}, semantic_metadata: {...}, cached_at: ..., ttl: 86400}
├── rdf:dbpedia_ontology                 # DBpedia ontology classes
│   └── {data: {...}, semantic_metadata: {...}, cached_at: ..., ttl: 86400}
├── schema:wikidata                      # Wikidata schema info
│   └── {endpoint: "wikidata", prefixes: {...}, classes: {...}, ttl: 3600}
├── schema:uniprot                       # UniProt schema info
│   └── {endpoint: "uniprot", prefixes: {...}, classes: {...}, ttl: 3600}
└── sparql_endpoints                     # Dynamically discovered endpoints
    └── {discovered_endpoints: {...}, cached_at: ..., ttl: 86400}
```

**Cache Operations**:

```python
# Store with semantic metadata
cache_manager.set_enhanced(
    key="rdf:foaf_vocab",
    data={"raw": ..., "expanded": ..., "enhanced": ...},
    metadata=SemanticMetadata(
        semantic_type="vocabulary",
        domains=["social"],
        format_type="json-ld",
        purpose="schema_definition",
        dependencies=["rdfs"],
        provides={"classes": 12, "properties": 45},
        confidence_scores={"domain": 0.95},
        vocabulary_size=57,
        learned_at=time.time(),
        usage_patterns=["friend_networks", "social_graphs"]
    ),
    ttl=86400
)

# Retrieve with metadata
entry = cache_manager.get_enhanced("rdf:foaf_vocab")
if entry and not entry.is_expired:
    vocabulary = entry.data["enhanced"]
    domains = entry.semantic_metadata.domains

# Search by classification
biology_vocabs = cache_manager.list_by_domain("biology")
# Returns: ["rdf:uniprot_service", "rdf:gene_ontology", ...]

# Update Claude's analysis
cache_manager.update_semantic_metadata(
    "rdf:foaf_vocab",
    SemanticMetadata(usage_patterns=["discovered new pattern: ..."])
)
```

**Why Local Cache is Critical**:

1. **Performance**: 200x speedup (1000ms → 5ms for repeated operations)
2. **Offline Capability**: Work without network once cached
3. **Reduced Load**: Avoid hammering public SPARQL endpoints
4. **Semantic Intelligence**: Store Claude's vocabulary analysis
5. **Session Continuity**: Maintain context across research sessions
6. **TTL Management**: Auto-refresh stale data (24h for RDF, 1h for schemas)

**Cache Management Commands** (via `rdf_cache` tool):

```bash
# List all cached vocabularies with metadata
rdf_cache --list
# Output: Shows cache keys, semantic types, domains, sizes, ages

# Inspect specific cached vocabulary
rdf_cache foaf_vocab --graph
# Output: Complete ontology structure with navigation guide

# Update semantic metadata (Claude's analysis)
rdf_cache foaf_vocab --update-metadata '{
  "usage_patterns": ["social_networks", "friend_of_friend"],
  "confidence_scores": {"domain": 0.95}
}'

# Clear specific vocabulary
rdf_cache --clear-item foaf_vocab

# Clear entire cache (nuclear option)
rdf_cache --clear
```

**Cache Workflow Integration**:

```bash
# Step 1: Fetch and cache
rdf_get http://xmlns.com/foaf/0.1/ --cache-as foaf_vocab

# Step 2: Read from cache (fast, offline)
rdf_cache foaf_vocab --graph

# Step 3: Search cached vocabulary (in-memory, <10ms)
rdf_cache "Person" --type class

# Step 4: Update with learned patterns
rdf_cache foaf_vocab --update-metadata '{"usage_patterns": [...]}'

# Step 5: Use in queries (cache provides context)
cl_select "SELECT ?person WHERE { ?person a foaf:Person }"
```

## JSON-LD 1.1 Container Patterns

rdf_get creates JSON-LD 1.1 structures optimized for fast vocabulary navigation:

```json
{
  "enhanced": {
    "@context": {
      "@version": 1.1,
      "classes": {"@container": "@index"},        // O(1) class lookup
      "properties": {"@container": "@index"},     // O(1) property lookup
      "namespaces": {"@container": "@index"},     // O(1) namespace lookup
      "domains": {"@container": ["@graph", "@index"]},  // Domain-grouped queries
      "semantic_index": {"@container": "@index"}  // Relationships
    },
    "classes": {
      "Protein": {"@id": "http://...", "@type": [...], "domain": "biology"},
      "Gene": {...}
    },
    "semantic_index": {
      "class_hierarchy": {
        "http://parent_class": {"subclasses": ["http://child1", "http://child2"]}
      },
      "property_constraints": {
        "http://prop": {"domain": "http://domain_class", "range": "http://range_class"}
      }
    }
  }
}
```

This enables:
- **Fast Lookup**: `enhanced["classes"]["Protein"]` is O(1)
- **Semantic Navigation**: Walk class hierarchies, find constrained properties
- **Domain-Filtered Queries**: Get biology-specific classes in one step

## Error Handling & Guardrails

All tools implement:

1. **Input Validation**:
   - SPARQL query syntax validation (SELECT/ASK/DESCRIBE)
   - Entity ID format validation
   - URL validation

2. **Execution Guardrails**:
   - Timeout protection (default 30 seconds)
   - Size warnings for large ontologies (>500KB)
   - Vocabulary discovery reminders

3. **Claude Code Workflow Guidance**:
   - `claude_guidance` field in JSON responses
   - Suggests next actions based on results
   - Reminds about discovery-first workflows
   - Explains pagination options

## Testing Infrastructure

Test files in `tests/` directory:
- `test_cli_tools.py` - CLI tool unit tests
- `test_cache_manager.py` - Cache functionality
- `test_integration.py` - End-to-end workflows
- `test_dynamic_discovery_live.py` - Live endpoint testing
- `conftest.py` - Shared fixtures and test data

## Performance Characteristics

| Operation | First Run | Cached | Typical Time |
|-----------|-----------|--------|--------------|
| rdf_get (small vocab) | Discovery | Cache | 500-1000ms / 5-50ms |
| rdf_cache search | Full scan | In-memory | 100-500ms / <10ms |
| cl_search | HTTP request | N/A | 200-500ms |
| cl_select | SPARQL query | N/A | 100-300ms |
| cl_construct | SPARQL CONSTRUCT | Cache | 300-1000ms |

Cache strategy: ~200x performance improvement for repeated operations on same vocabulary.

## Entry Points & Integration

### Command-Line Interface
- **rdf_get** → `cogitarelink.cli.rdf_get:fetch`
- **rdf_cache** → `cogitarelink.cli.rdf_cache:search`
- **cl_search** → `cogitarelink.cli.cl_search:search`
- **cl_select** → `cogitarelink.cli.cl_select:select`
- **cl_describe** → `cogitarelink.cli.cl_describe:describe`
- **cl_ask** → `cogitarelink.cli.cl_ask:ask`
- **cl_construct** → `cogitarelink.cli.cl_construct:construct`
- **cogitarelink** → `cogitarelink.cli.cogitarelink:main` (entry point)

### Python API
```python
from cogitarelink.backend import (
    cache_manager,
    sparql_engine,
    resolve_endpoint,
    get_all_endpoints,
    ContentAnalyzer
)

# Access cache directly
data = cache_manager.get("rdf:foaf_vocab")

# Resolve endpoints
url, prefixes = resolve_endpoint("uniprot")

# Analyze content
analyzer = ContentAnalyzer()
analysis = analyzer.analyze_content_structure(rdf_data)
```

## Future Extension Points

1. **New SHACL Templates**: Add to SHACL_TEMPLATES dict in cl_construct.py
2. **New Endpoints**: Add to KNOWN_ENDPOINTS in sparql.py
3. **Domain Patterns**: Extend prompts/core_patterns.py
4. **Custom Query Types**: Add validators + executors following cl_select/cl_ask pattern
5. **Storage Backends**: Replace diskcache with alternative via CacheManager interface

## Design Philosophy

The architecture embodies Claude Code's core patterns:

1. **Read Before Edit**: Discover → Cache → Query (never guess URIs)
2. **Structured Output**: JSON for systematic analysis, not human-readable text
3. **Composability**: Mix with WebSearch, Task, WebFetch seamlessly
4. **Agent-First Design**: Optimize for AI reasoning, not human convenience
5. **Simplicity**: Each tool does ONE thing well
6. **Expressiveness**: Combine simple tools for powerful results
7. **Intelligence in Prompts**: Sophisticated behavior from injected instructions, not complex code

## Prompt Injection Architecture Summary

**The Core Innovation**: CogitareLink extends Claude Code by following its **tools + prompts** pattern:

```
Simple Tools (7 CLI commands)
    +
Injected Instructions (prompts/core_patterns.py)
    +
Claude's Reasoning
    =
Sophisticated Semantic Web Capabilities
```

**How It Works**:

1. **Editable Instruction Strings**: `DISCOVERY_FIRST`, `CACHE_OPTIMIZATION`, etc. are plain strings in `core_patterns.py`
2. **Instruction Composition**: `instruction_generator.py` composes these strings into domain-specific guidance
3. **stdout Injection**: `cogitarelink` command prints instructions → Claude Code captures as context
4. **Natural Language Signals**: "-$1000 penalty", "✅ / ❌", "Like ReadTool" guide Claude's reasoning
5. **Self-Improving**: Edit pattern strings when usage reveals better approaches

**Three Injection Mechanisms**:

| Mechanism | How It Works | When Used |
|-----------|--------------|-----------|
| **Direct Command** | `cogitarelink` prints to stdout | Session start, manual trigger |
| **Tool Output** | `claude_guidance` field in JSON | Every tool invocation (current) |
| **CLAUDE.md** | Project instructions file | Auto-loaded by Claude Code |

**Why This Beats Traditional Approaches**:

- ❌ **Rule Engines**: Complex validation logic hard to modify
- ❌ **Hardcoded Behavior**: Requires code changes for new patterns
- ✅ **Prompt Injection**: Edit strings, see immediate behavior changes
- ✅ **Composable Instructions**: Mix domain patterns, optimization hints, workflow guidance
- ✅ **Leverages Claude's Intelligence**: AI interprets natural language instructions naturally

**Example Evolution**:

```python
# Discovery pattern v1 (too weak)
DISCOVERY_FIRST = "Try to discover vocabulary before querying"

# Discovery pattern v2 (stronger signal)
DISCOVERY_FIRST = "CRITICAL: Always use rdf_get before cl_select"

# Discovery pattern v3 (current - uses value system)
DISCOVERY_FIRST = """
CRITICAL_RULE: cl_discover REQUIRED before SPARQL (-$1000 penalty)
"""
```

No code changes required - just edit the string, and Claude's behavior adapts.

