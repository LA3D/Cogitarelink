# CLAUDE.md

Guidance for using CogitareLink's semantic web tools in Claude Code sessions.

## What is CogitareLink?

Six simple RDF tools that give Claude Code semantic web capabilities. Like Claude Code's file tools (Read, Edit) but for linked data.

**Core Pattern**: `discover → cache → query` (like Read-before-Edit)

```bash
# Discovery & Caching
rdf_get URL --cache-as NAME              # Fetch RDF content, discover vocabulary
rdf_cache NAME --graph                   # Read cached vocabulary (like ReadTool)
rdf_cache NAME --update-metadata '{...}' # Store Claude's semantic analysis

# SPARQL Tools  
cl_search "term" --endpoint NAME         # Find entities (API or SPARQL)
cl_select "SELECT..." --endpoint NAME    # Explore data with pagination
cl_describe ENTITY                       # Get complete RDF data
cl_ask "{SPARQL ASK}"                   # Verify facts (true/false)
```

## Critical Reminders

### 🚨 DISCOVERY-FIRST RULE (like Read-before-Edit)
```bash
# ✅ ALWAYS discover vocabulary first
rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot
rdf_cache uniprot --graph  # Understand available classes/properties
cl_select "SELECT ?p WHERE {?p a up:Protein}" --endpoint uniprot

# ❌ NEVER guess URIs
cl_select "SELECT ?p WHERE {?p a uniprot:Protein}"  # WRONG - guessed prefix
```

### Known Endpoints

**W3C Compliant** (have service descriptions):
- `uniprot` - 225B+ protein triples, `up:` prefix
- `wikipathways` - Biological pathways, `wp:` prefix  
- `wikidata` - General knowledge graph

**Query-Only** (no service descriptions):
- `qlever-wikidata` - Fast but non-standard
- `qlever-osm` - 258B OpenStreetMap triples

## Quick Patterns

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

## Learning System (Claude Code Memory Pattern)

CogitareLink includes a memory system that follows Claude Code's approach to learning from usage patterns.

### Session Capture
After research sessions, capture what worked/failed in natural narrative:

```markdown
# cogitarelink/patterns/use_cases/session_2024_06_17_14.md

**Domain**: biology  
**Goal**: Find drug targets related to COVID-19 spike protein

## Session Narrative
I tried direct UniProt search first but it failed with timeouts. The breakthrough 
came when I used Wikidata as a hub - cl_search "SARS-CoV-2" found the entity, 
then cl_describe gave me P352 cross-reference to UniProt P0DTC2...
```

### Memory Distillation
Claude analyzes session narratives and extracts CLAUDE.md-style memories:

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

### Why This Works
Like Claude Code's auto-compact system, we distill rich research narratives into focused reminders that prevent repeated mistakes and speed up future work.

## Prompting Architecture (Claude Code Pattern)

### How CogitareLink Distributes Intelligence

Following Claude Code's architecture, we use **reminders, not tutorials**:

**Base Context** (loaded once per session):
- Full semantic web patterns and SPARQL knowledge
- Endpoint behaviors and quirks
- Discovery workflows and error patterns

**Tool Reminders** (injected at tool use):
```
⚡ cl_search reminders:
- Wikidata → API first (REF: discovery-first)
- Others → SPARQL fallback (REF: endpoint-behaviors)
- Empty = error (REF: validation-rules)
```

### Why This Works

Like Claude Code's tools, instructions don't teach - they **focus attention**:
- `ReadTool`: "reads up to 2000 lines" → points to file handling rules
- `cl_search`: "use API for Wikidata" → points to endpoint patterns

The intelligence lives in Claude's base context. Tools just remind where to look.

## Common Mistakes to Avoid

1. **Guessing URIs** - Always discover first with rdf_get
2. **Skipping cache** - Use rdf_cache to understand vocabulary  
3. **Large limits** - Keep under 100 for performance
4. **Wrong endpoints** - Check endpoint type before queries

## Development

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Test
uv run pytest tests/test_cli_tools.py -v
```

---

**Remember**: These are reminders, not tutorials. The tools work like Claude Code's file tools - simple, reliable, composable. Intelligence comes from Claude Code's reasoning, not complex tool logic.