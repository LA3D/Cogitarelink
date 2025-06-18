# CLAUDE.md

Guidance for using CogitareLink's semantic web tools in Claude Code sessions.

## What is CogitareLink?

Seven simple RDF tools that extend Claude Code's built-in capabilities with semantic web functionality. **Natural extensions**, not separate systems.

**Core Pattern**: `discover → cache → query` (like Read-before-Edit)

## Tool Composition: Semantic Web + Claude Code Integration

CogitareLink tools compose fluidly with Claude Code's built-in tools for discovery workflows:

**Integrated Discovery Pattern**:
```bash
# 1. Domain research with built-in tools
Task: "Research DBpedia ontology structure" 
WebSearch: "DBpedia RDFS vocabulary usage"
WebFetch: "https://dbpedia.org/ontology docs"

# 2. RDF-specific operations with semantic web tools  
rdf_get https://dbpedia.org/sparql --cache-as dbpedia_service
rdf_get http://dbpedia.org/ontology/ --cache-as dbpedia_ontology
rdf_cache dbpedia_ontology --update-metadata "Uses standard RDFS confirmed via web research"

# 3. Apply semantic reasoning with discovered knowledge
cl_construct SP_Transitive --focus dbo:Person --endpoint dbpedia
```

**Key Insight**: Use the full Claude Code toolchain seamlessly. WebSearch discovers what exists, rdf_get fetches it, rdf_cache analyzes it, SPARQL tools query it.

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
cl_construct TEMPLATE --focus ENTITY    # Apply SHACL reasoning templates
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

### SHACL Template Reasoning
```bash
cl_construct --list-templates                     # Show available templates
cl_construct SC_Transitive --focus up:Protein --endpoint uniprot
cl_construct DomainEnt --focus foaf:knows --cache-as social_domains
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

## Tool Composition Patterns

### Discovery Workflows Mix All Available Tools

**Domain Understanding** (built-in tools):
- Task → "Find DBpedia ontology documentation" 
- WebSearch → "DBpedia vocabulary patterns"
- WebFetch → "https://dbpedia.org/docs" → understand domain

**Resource Acquisition** (semantic web tools):
- rdf_get → fetch actual RDF content discovered above
- rdf_cache → analyze and store semantic metadata

**Knowledge Application** (combined intelligence):
- cl_construct → apply templates using web research + cached analysis
- cl_select → query with vocabulary patterns from web + RDF discovery

### Integration Examples

**Biology Research**:
```bash
WebSearch: "UniProt RDF vocabulary"          # Domain research
rdf_get uniprot_sparql --cache-as uniprot   # Fetch actual RDF  
cl_search "insulin" --endpoint uniprot      # Apply combined knowledge
```

**Cross-Domain Investigation**:
```bash
Task: "Find Wikidata → UniProt mappings"    # Research strategy
cl_search "caffeine" --limit 5              # Find entities
WebFetch: "https://pubchem.ncbi.nlm.nih.gov" # Validate external links
cl_describe Q60235 --follow-links           # Apply full toolchain
```

## Prompting Architecture (Claude Code Pattern)

### How CogitareLink Distributes Intelligence

Following Claude Code's architecture, we use **reminders, not tutorials**:

**Base Context** (loaded once per session):
- Full semantic web patterns and SPARQL knowledge
- Web research and discovery workflows  
- Tool composition and integration patterns
- Endpoint behaviors and quirks

**Tool Reminders** (injected at tool use):
```
⚡ cl_search reminders:
- Research first with WebSearch/Task (REF: tool-composition)
- Wikidata → API first (REF: discovery-first)
- Others → SPARQL fallback (REF: endpoint-behaviors)
- Cache findings with rdf_cache (REF: workflow-integration)
```

### Why This Works

Like Claude Code's tools, instructions don't teach - they **focus attention**:
- `WebSearch` + `rdf_get`: "research then fetch" → points to discovery patterns
- `Task` + `cl_construct`: "analyze then apply" → points to workflow integration  
- `ReadTool` + `rdf_cache`: "read then understand" → points to analysis patterns

The intelligence lives in Claude's reasoning about tool composition, not individual tool complexity.

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

**Remember**: These are reminders, not tutorials. CogitareLink tools extend Claude Code's capabilities naturally - simple, reliable, composable with the full toolchain. Intelligence comes from Claude Code's reasoning about tool composition, not complex individual tool logic.

**Key Philosophy**: Never treat semantic web tools in isolation. Always consider how WebSearch, Task, WebFetch, Read, and RDF tools compose together for discovery workflows.