# CogitareLink

**Semantic web tools for AI agents.** Seven simple RDF tools that give Claude Code semantic reasoning capabilities over linked data.

## Motivation: Tools for AI Agents, Not Humans

CogitareLink is designed specifically for **AI agents like Claude Code**, not human users. While humans interact with Claude, **Claude is the actual user** of these tools. This distinction matters because:

- **Agents need structured data**: Claude reasons over JSON-LD, follows relationships, and builds knowledge graphs
- **Agents work with discovery workflows**: Claude naturally follows `discover → cache → query` patterns  
- **Agents compose tools**: Claude seamlessly combines semantic tools with built-in capabilities (WebSearch, Task, WebFetch)
- **Agents handle complexity**: Claude can navigate ontologies, translate vocabularies, and apply reasoning templates

This is not a human semantic web toolkit - it's an **agent intelligence amplifier** for semantic reasoning.

## First Principles

**1. Discovery Before Querying**  
Like "Read before Edit" for files, always discover vocabulary before SPARQL queries. No guessing URIs.

**2. Cache for Intelligence**  
Store RDF vocabularies as structured JSON-LD that Claude can reason over, not just raw data.

**3. Natural Tool Composition**  
Semantic tools work alongside Claude's built-in tools (WebSearch → rdf_get → cl_select).

**4. Agent-Optimized Output**  
All tools return structured JSON for systematic analysis, not human-readable text.

## Quick Start

```bash
# Install (one-time setup)
pip install git+https://github.com/LA3D/Cogitarelink.git

# Initialize semantic capabilities in Claude Code session
cogitarelink
```

Then simply ask Claude questions that require semantic web research:

**Human**: *"Can you research insulin and its protein interactions? I'm interested in understanding the molecular pathways."*

**Claude Code automatically**:
- Determines relevant databases (UniProt, Wikidata, WikiPathways)
- Discovers vocabulary structures with `rdf_get` and `rdf_cache`
- Searches for insulin-related entities with `cl_search`
- Follows cross-references between databases with `cl_describe`
- Applies reasoning templates with `cl_construct` to find pathway relationships
- Synthesizes findings into comprehensive insights

**Human**: *"What are the genetic variants associated with diabetes medications?"*

**Claude Code autonomously**:
- Researches pharmacogenomics databases
- Discovers drug-gene interaction vocabularies  
- Queries for medication entities and genetic markers
- Maps relationships across chemical and biological databases
- Provides structured analysis of variant-drug associations

## The Seven Tools

### Discovery & Caching
- **`rdf_get`** - Fetch and cache RDF content from any URL
- **`rdf_cache`** - Navigate cached vocabularies and semantic relationships

### SPARQL Operations  
- **`cl_search`** - Find entities (Wikidata API or SPARQL text search)
- **`cl_select`** - Explore data with pagination (like ReadTool for RDF)
- **`cl_describe`** - Get complete RDF data about entities
- **`cl_ask`** - Boolean fact verification queries
- **`cl_construct`** - Apply SHACL reasoning templates for knowledge synthesis

## How Claude Uses These Tools

**Research Discovery Pattern**:
```bash
# 1. Use Claude's built-in tools for domain research
Task: "Research UniProt RDF vocabulary patterns"
WebSearch: "UniProt SPARQL endpoint capabilities"

# 2. Use semantic tools for RDF operations  
rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot_service
rdf_cache uniprot_service --graph  # Claude analyzes vocabulary structure

# 3. Apply semantic reasoning with discovered knowledge
cl_select "SELECT ?protein WHERE { ?protein a up:Protein }" --endpoint uniprot --limit 5
cl_construct SC_Transitive --focus up:Protein --endpoint uniprot
```

**Why This Works**:
- Claude's base knowledge includes complete semantic web expertise (RDF, SPARQL, JSON-LD)
- Tools provide capabilities, intelligence lives in Claude's reasoning
- Structured JSON output enables systematic analysis and tool chaining
- Discovery workflows prevent common semantic web errors (guessed URIs, wrong namespaces)

## Agent Intelligence Benefits

**For Claude Code**:
- **Semantic reasoning**: Navigate knowledge graphs, follow relationships, apply ontological reasoning
- **Cross-domain research**: Bridge biology, chemistry, geography through linked data
- **Knowledge synthesis**: Use SHACL templates to construct new knowledge from existing data
- **Structured exploration**: Systematic discovery with pagination and error handling

**For Humans**:
- **Natural interaction**: Ask Claude to research topics using semantic web data
- **No SPARQL knowledge needed**: Claude handles query construction and vocabulary discovery
- **Rich insights**: Claude can synthesize information across multiple linked datasets
- **Reliable results**: Discovery-first workflow prevents common semantic web errors

## Known Endpoints

Built-in support for major semantic web databases:

- **`wikidata`** - General knowledge graph (500M+ entities)
- **`uniprot`** - Protein sequences and functions (225B+ triples)  
- **`wikipathways`** - Biological pathways and reactions
- **`dbpedia`** - Structured Wikipedia data

Claude can also work with any SPARQL endpoint URL.

## Example: Biology Research

```bash
# Find insulin-related proteins
cl_search "insulin receptor" --limit 3

# Get complete data about insulin  
cl_describe Q7240673  # Wikidata entity

# Find cross-references to protein databases
cl_select "SELECT ?prop ?id WHERE { 
  wd:Q7240673 ?prop ?id . 
  ?prop wdt:P31 wd:P1628 
}" --limit 5

# Follow cross-reference to UniProt
cl_describe P01308 --endpoint uniprot

# Apply reasoning to discover protein relationships
cl_construct DomainEnt --focus "up:recommendedName" --endpoint uniprot
```

Claude handles the vocabulary discovery, query construction, and knowledge synthesis automatically.

## Architecture Philosophy  

CogitareLink extends Claude Code's core design patterns:

- **Instruction-driven enhancement**: Intelligence in prompts, not complex code
- **Progressive disclosure**: Tools build confidence, prevent over-validation  
- **Safety-first design**: Discovery workflows prevent errors
- **Natural composition**: Semantic tools work with built-in tools
- **JSON-first output**: Structured data for systematic agent reasoning

## Cache System

Maintains semantic vocabularies as structured JSON-LD at `~/.cogitarelink/cache/`:

- **JSON-LD normalization**: All RDF formats converted to consistent JSON-LD
- **Semantic metadata**: Claude's annotations about vocabulary purpose and scope
- **Relationship mapping**: Cached class hierarchies and property constraints  
- **Discovery enforcement**: Prevents guessed URIs by requiring cached vocabulary

## Requirements

- **Python 3.11+**
- **Claude Code** (designed specifically for AI agent integration)

## Development

```bash
git clone https://github.com/LA3D/Cogitarelink.git
cd Cogitarelink
uv sync && uv pip install -e .
uv run pytest tests/ -v
```

## License

MIT - See LICENSE file for details.

---

**Remember**: These tools are for Claude Code, not humans. The intelligence lives in Claude's semantic reasoning, tools provide clean capabilities.