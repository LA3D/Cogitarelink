# CLAUDE.md

This file provides guidance to Claude Code when working with CogitareLink - a semantic web research assistant that extends Claude Code's capabilities.

## Project Overview

**CogitareLink: Semantic Web Tools + Distributed Intelligence for Claude Code**

CogitareLink ("to think connectedly") provides Claude Code with expert semantic web capabilities through:

- **Simple, Composable Tools**: 6 RDF tools following Claude Code patterns (ReadTool, EditTool, BashTool)
- **Software 2.0 Architecture**: Intelligence in prompts, not hardcoded logic
- **Distributed Expert Knowledge**: Package semantic web expertise for non-expert users
- **Research Memory**: Cache system extends Claude Code sessions with persistent research intelligence

## Core Philosophy

- **Tools + Prompts**: Simple tools provide data, Claude Code provides reasoning
- **Expert Knowledge Distribution**: Semantic web expertise packaged for normal users  
- **Discovery-First Guardrails**: Never query without understanding vocabulary (like Read-before-Edit)
- **Cache as Memory**: Persistent research intelligence across sessions
- **Framework Agnostic**: Works with any Claude Code workflow

## Current Working Tools

### 6 Core RDF Tools (Production Ready ✅)

**Content Discovery & Caching:**
```bash
rdf_get http://xmlns.com/foaf/0.1/ --cache-as foaf_vocab    # Fetch RDF with content negotiation
rdf_cache foaf_vocab --graph                               # Navigate cached vocabularies  
rdf_cache foaf_vocab --update-metadata '{"type": "vocab"}' # Claude Code annotation storage
```

**SPARQL Query Tools:**
```bash
cl_search "insulin" --limit 5                              # Universal entity search
cl_select "SELECT ?p ?o WHERE {wd:Q7240673 ?p ?o}"        # Primary data exploration 
cl_describe Q7240673                                       # Complete RDF data retrieval
cl_ask "{wd:Q7240673 wdt:P31 wd:Q8054}"                   # Boolean fact verification
```

### Software 2.0 Intelligence Workflow

**Discovery → Analysis → Annotation → Research:**

```bash
# Step 1: Content Discovery
rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot_service

# Step 2: Claude Code Analysis (automatic via content_analysis structure)
# Claude examines structural patterns, vocabularies, relationships

# Step 3: Store Claude Intelligence 
rdf_cache uniprot_service --update-metadata '{
  "semantic_type": "service_description", 
  "domains": ["biology", "proteins"],
  "confidence": 0.95,
  "notes": "UniProt SPARQL with 225B+ triples, full VoID statistics"
}'

# Step 4: Research with Annotated Knowledge
rdf_cache uniprot_service --graph   # Use enriched vocabulary
cl_search "spike protein" --endpoint uniprot
```

## Intelligence Distribution Architecture

### Three Layers of Knowledge

**Layer 1: Package Intelligence** (Ships with CogitareLink)
- Endpoint patterns: "UniProt = W3C compliant, QLever = query-only"
- Domain vocabularies: "Biology = up:, wp:, foaf: patterns" 
- Discovery workflows: "Try service description → fallback to SPARQL discovery"
- Common failures: "404 on GET → not W3C compliant → use introspective queries"

**Layer 2: Session Memory** (Learned locally)
- `.cogitarelink/cache/` - Discovered vocabularies and annotations
- Research patterns learned from Claude Code + user interactions
- Domain specializations accumulated over time

**Layer 3: Claude Code Integration** (Runtime)
- Package intelligence + session memory loaded into Claude context
- Expert knowledge available automatically for non-expert users
- "Just works" semantic research without SPARQL expertise required

### User Experience Transformation

**Before:** "I need spike protein interactions" → "You need to learn SPARQL, find endpoints, discover vocabularies..."

**After:** "I need spike protein interactions" → [Claude automatically knows UniProt, uses up: prefixes, constructs queries, returns results]

## Current System Status

### Working Features ✅
- **6 RDF Tools**: Full SPARQL workflow with content negotiation
- **Software 2.0 Architecture**: No hardcoded classification, Claude Code provides intelligence
- **W3C Standards Support**: Proper service descriptions (UniProt, WikiPathways)
- **Non-Compliant Endpoint Handling**: Query-only endpoints (QLever) via introspective discovery
- **Cache System**: Research memory with semantic annotation
- **JSON-LD 1.1 Features**: Advanced indexing, semantic relationships, size-aware loading

### Known Endpoint Patterns ✅
- **UniProt**: W3C compliant, 225B+ triples, rich VoID statistics, up: prefix
- **WikiPathways**: W3C compliant, minimal service description, wp:/gpml: vocabularies
- **QLever (Wikidata, OSM)**: Query-only, no service descriptions, requires SPARQL discovery
- **Wikidata (official)**: W3C compliant, comprehensive service descriptions

### Research Workflows ✅
- **Biology**: UniProt (proteins) → WikiPathways (pathways) → cross-reference following
- **Chemistry**: PubChem → ChEBI → bioactivity databases
- **Geographic**: OSM Planet → 258B triples of OpenStreetMap data in RDF

## Cache as Research Memory

### Cache Structure
```
.cogitarelink/cache/
├── rdf:foaf_vocab          # Vocabularies with Claude annotations
├── rdf:uniprot_service     # Service descriptions with statistics  
├── rdf:wp_vocabulary       # Domain-specific prefix mappings
└── sparql_endpoints        # 191 known SPARQL endpoints
```

### Claude Code Annotation Storage
```bash
# Store semantic insights for reuse
rdf_cache vocabulary_name --update-metadata '{
  "semantic_type": "vocabulary|ontology|context|service",
  "domains": ["biology", "chemistry", "social"],
  "purpose": "description_of_use_case", 
  "confidence": 0.95,
  "notes": "Claude analysis and insights"
}'
```

## Development Workflow

### Environment Setup
```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Testing (30/30 tests passing ✅)
```bash
uv run pytest tests/ -v                    # All tests
uv run pytest tests/test_cli_tools.py -v   # Tool functionality
```

### Tool Usage Examples
```bash
# Test W3C compliant endpoints
uv run rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot

# Test non-compliant endpoints  
uv run cl_search "caffeine" --endpoint https://qlever.cs.uni-freiburg.de/api/wikidata

# Navigate semantic relationships
uv run rdf_cache foaf_vocab --subclasses foaf:Agent
uv run rdf_cache uniprot_vocab --properties up:Protein
```

## Key Insights Learned

### SPARQL Endpoint Reality
- **W3C Compliant**: UniProt, WikiPathways, official Wikidata
- **Non-Compliant**: QLever endpoints (no service descriptions, query-only)
- **Manual Discovery Works**: curl + jq + Claude reasoning is effective
- **Service Descriptions Vary**: From minimal (WikiPathways) to massive (UniProt 8MB+)

### Successful Architecture Decisions
- **Software 2.0 Transformation**: Removed hardcoded classification, Claude provides intelligence
- **Cache Integration**: Research memory persists across sessions
- **Discovery-First**: Always try service description, fallback to introspective queries
- **Expert Knowledge Distribution**: Package semantic web expertise for non-experts

### Next Evolution
- **Research Memory**: Accumulate learned patterns like CLAUDE.md does for Claude Code
- **Intelligence Distribution**: Ship domain expertise with the package
- **Session Continuity**: Link CogitareLink research sessions with Claude Code sessions
- **Prompt Memory**: Learned patterns become part of instruction prompting

This system transforms semantic web research from "expert tool" to "just works" for domain scientists who need the data but shouldn't need to learn SPARQL.