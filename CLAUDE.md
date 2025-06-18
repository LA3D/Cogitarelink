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

## Session Annotation & Knowledge Capture

After discovering something useful, annotate it for future sessions:

```bash
rdf_cache uniprot --update-metadata '{
  "semantic_type": "service",
  "domains": ["biology"],
  "notes": "Use up:Protein for protein queries"
}'
```

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

### Knowledge Distillation Workflow

1. **Usage Annotation** - Claude records what worked/failed:
```bash
rdf_cache tool_usage --update-metadata '{
  "tool": "cl_search",
  "what_worked": "Wikidata API 10x faster than SPARQL",
  "what_failed": "UniProt needs FILTER regex",
  "edge_case": "Empty results need explicit handling"
}'
```

2. **Pattern Extraction** - Distill critical patterns from usage
3. **Reminder Generation** - Create focused attention pointers

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