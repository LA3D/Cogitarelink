# CogitareLink Tools Guide

CogitareLink provides semantic research tools optimized for Claude Code usage patterns. Tools return clean JSON data that Claude can navigate directly with jq.

## Core Principles

1. **Discovery-First Workflow**: Always discover entities/schema before querying
2. **Anti-Hallucination**: Use only discovered QIDs/PIDs, never fabricate identifiers
3. **Clean Data Output**: Tools return pure data, Claude provides the intelligence
4. **Fast Execution**: All tools respond in < 2s for typical queries
5. **Exploration Analysis**: Use structured thinking tags to encourage curiosity and follow research threads

## Exploration Analysis Pattern

Following Claude Code's structured thinking approach, after using CogitareLink tools, wrap your analysis in `<research_analysis>` tags to encourage exploration:

```markdown
<research_analysis>
- What new research threads emerged from the tool results?
- Which cross-references or relationships warrant deeper investigation?
- What questions arise that could guide next steps?
- How do the discovered entities connect to broader research domains?
- What patterns in the data suggest interesting follow-up queries?
- Which external databases contain relevant supplementary information?
</research_analysis>
```

This pattern encourages systematic exploration of research opportunities rather than stopping at surface-level results.

## Tool Usage Hierarchy

**Discovery → Exploration → Navigation → Multi-Endpoint Query:**

1. **`cl_entity`** - Convert natural language to semantic identifiers (ALWAYS start here)
2. **`cl_describe`** - Explore entity properties and cross-references  
3. **`cl_follow`** - Navigate to external databases via cross-references
4. **`cl_sparql`** - Multi-endpoint queries with automatic guardrails (5 biological databases)
5. **`cl_resolve`** - Follow specific cross-reference identifiers

### Multi-Endpoint Discovery Pattern
```bash
# Step 1: Find entity in Wikidata
cl_entity "insulin" | jq '.candidates[0].id'
# → "Q7240673"

# Step 2: Explore cross-references
cl_describe Q7240673 | jq '.cross_references.uniprot[0]'  
# → "P01308"

# Step 3: Query pathways containing this protein
cl_sparql "SELECT ?pathway ?title WHERE { ?gene a wp:GeneProduct . ?gene rdfs:label 'insulin' . ?gene dcterms:isPartOf ?pathway . ?pathway dc:title ?title }" --endpoint wikipathways

# Step 4: Get protein details from UniProt  
cl_sparql "SELECT ?protein ?organism WHERE { ?protein up:mnemonic 'INS_HUMAN' . ?protein up:organism ?organism }" --endpoint uniprot
```

## Discovery Pattern Examples

### Pattern 1: Biological Research Discovery
```bash
# Start with natural language
cl_entity "insulin" --domain-hint biology | jq '.candidates[0].id'
# → "Q7240673"

# Explore the entity to find semantic structure  
cl_describe Q7240673 | jq '.cross_references.uniprot[0]'
# → "P01308"

# Follow cross-references to external databases
cl_follow Q7240673 | jq '.data.statistics.total_identifiers'
# → 226

# Query with discovered context (auto-adds LIMIT 100)
cl_sparql "SELECT ?protein ?uniprot WHERE { ?protein wdt:P352 ?uniprot }"
# → Returns clean JSON with query metadata and results
```

<research_analysis>
- The protein cross-reference P01308 suggests connections to protein structure databases
- 226 total identifiers indicate this entity has extensive cross-database coverage  
- The SPARQL pattern reveals a broader protein-identifier relationship that could apply to other proteins
- What other proteins share similar cross-reference patterns?
- Which specialized protein databases might contain functional information beyond basic identifiers?
- How do insulin variants relate to other hormone proteins in the semantic network?
</research_analysis>

**Pattern Recognition**: Any biological entity follows this structure: Wikidata entity → cross-reference properties → external database identifiers → specialized databases.

**Claude Code Integration**: Use jq to navigate results directly. Tools return pure data without suggestions or guidance.

### Pattern 2: Corporate Research Discovery
```bash
# Discover corporate entity
cl_entity "Lockheed Martin" --domain-hint corporate | jq '.candidates[0]'
# → {"id": "Q7240", "label": "Lockheed Martin", "confidence": 0.85}

# Explore corporate structure
cl_describe Q7240 | jq '.entity.claims_count'
# → 89

# Follow corporate relationships
cl_follow Q7240 | jq '.data.cross_references | keys'
# → Links to regulatory databases, financial identifiers

# Query with discovered context
cl_sparql "SELECT ?company ?ticker WHERE { ?company wdt:P414 ?ticker }"
# → Clean JSON results with auto-LIMIT 100
```

<research_analysis>
- 89 claims suggest rich corporate data with multiple relationship types
- Corporate cross-references likely include SEC filings, stock exchanges, and regulatory databases
- The ticker symbol pattern (P414) opens research into financial market relationships
- What subsidiaries and corporate partnerships exist for this entity?
- How do defense contractors connect through shared board members or contracts?
- Which government agencies and international partners appear in the relationship network?
</research_analysis>

**Pattern Recognition**: Corporate entities have structural relationships (subsidiaries, parents) and regulatory identifiers (SEC, stock exchanges) that follow the same discovery pattern.

### Pattern 3: Property Discovery and Analysis
```bash
# Discover what a property means
cl_entity "UniProt ID" --type property | jq '.candidates[0].id'
# → "P352"

# Analyze property usage and constraints
cl_property P352 | jq '.data.examples.example_count'
# → 10

# See property in action (auto-adds LIMIT 100)
cl_sparql "SELECT ?entity ?uniprot WHERE { ?entity wdt:P352 ?uniprot }"
# → Clean JSON with variables and bindings
```

<research_analysis>
- P352 connects Wikidata entities to UniProt protein database entries
- 10 examples reveal usage patterns across different protein types
- The SPARQL results show the breadth of protein entities with UniProt mappings
- What other biological identifier properties (P683 ChEBI, P486 MeSH) create similar networks?
- How do protein identifier mappings relate to functional classifications?
- Which entities have multiple biological database cross-references that could enable federated queries?
</research_analysis>

**Pattern Recognition**: Properties have metadata (datatypes, constraints) and usage patterns that can be discovered and analyzed.

## Key Learnings from Discovery Patterns

**Generalization Principle**: Every domain follows the same discovery pattern:
1. Natural language → semantic identifiers (`cl_entity`)
2. Semantic identifiers → property structure (`cl_describe`) 
3. Property structure → external databases (`cl_follow`)
4. External databases → specialized queries (`cl_sparql`, `cl_resolve`)

**Unknown Domain Strategy**: When encountering new domains (geology, astronomy, linguistics), apply the same pattern. The semantic web structure is consistent - only the specific properties and databases change.

## Tool Reference (Claude Code Optimized)

### cl_entity - String→Entity Resolution
**ALWAYS start here** - prevents QID/PID hallucination

```bash
cl_entity "search term" --domain-hint biology|corporate|geography
cl_entity "UniProt ID" --type property  # Auto-detects property searches for "ID" terms
```
**Returns**: `{"query": "...", "candidates": [...], "search_strategy": {...}}`
**Features**: Enhanced confidence scoring with domain-aware patterns, auto-property detection
**Performance**: ~200ms, anti-hallucination verified

### cl_describe - Entity Exploration
```bash
cl_describe Q7240673 --include-cross-refs
```
**Returns**: `{"entity": {...}, "cross_references": {...}}`
**Features**: Enhanced cross-reference mappings for 15+ databases (UniProt, ChEBI, CAS, DrugBank, etc.), geographic coordinate extraction
**Performance**: ~300ms, includes external database IDs

### cl_follow - Cross-Reference Navigation  
```bash
cl_follow Q7240673 --resolve-urls
```
**Returns**: `{"data": {"entity": {...}, "cross_references": {...}, "statistics": {...}}}`
**Performance**: ~300ms, comprehensive database links

### cl_property - Property Analysis
```bash
cl_property P352 --include-examples
```
**Returns**: `{"data": {"property": {...}, "examples": {...}}}`
**Performance**: ~4s, simplified query approach

### cl_sparql - Multi-Endpoint Structured Queries
**ONLY after discovery** - automatic safety guardrails across biological databases
```bash
# Wikidata (default)
cl_sparql "SELECT ?s ?o WHERE { ?s wdt:P352 ?o }"

# WikiPathways - biological pathways  
cl_sparql "SELECT ?pathway ?title WHERE { ?pathway a wp:Pathway . ?pathway dc:title ?title }" --endpoint wikipathways

# UniProt - protein sequences and functions
cl_sparql "SELECT ?protein ?name WHERE { ?protein a up:Protein . ?protein up:mnemonic ?name }" --endpoint uniprot

# IDSM - chemical compounds from PubChem/ChEBI
cl_sparql "SELECT ?compound ?name WHERE { ?compound rdfs:label ?name }" --endpoint idsm
```
**Available Endpoints**: `wikidata`, `wikipathways`, `uniprot`, `idsm`, `rhea`
**Returns**: `{"query": {...}, "results": {"bindings": [...], "count": N, "variables": [...]}}`
**Features**: Enhanced SPARQL validation patterns, auto-LIMIT addition, dangerous operation detection, unknown prefix warnings
**Performance**: ~400ms, auto-adds LIMIT 100, blocks dangerous queries

### cl_resolve - External Database Navigation
```bash
cl_resolve P352 P01308  
```
**Returns**: External database links and metadata
**Performance**: ~500ms, cross-database navigation

## Claude Code Integration

### Data Navigation with jq
All tools return clean JSON that Claude can navigate directly:

```bash
# Extract specific values
cl_entity "insulin" | jq '.candidates[0].id'
cl_describe Q7240673 | jq '.cross_references.uniprot[0]'
cl_follow Q7240673 | jq '.data.statistics.total_identifiers'
cl_sparql "SELECT ?s WHERE { ?s wdt:P31 wd:Q8054 }" | jq '.results.count'

# Multi-endpoint navigation
cl_sparql "SELECT ?pathway WHERE { ?pathway a wp:Pathway }" --endpoint wikipathways | jq '.results.bindings[0].pathway.value'
cl_sparql "SELECT ?protein WHERE { ?protein a up:Protein }" --endpoint uniprot | jq '.results.bindings | length'

# Navigate complex structures
cl_follow Q7240673 | jq '.data.cross_references | keys[]'
cl_sparql "..." | jq '.results.bindings[0].s.value'
```

### Endpoint Discovery
```bash
# List available SPARQL endpoints
cl_sparql "SELECT ?s WHERE { ?s ?p ?o }" --endpoint help

# Available: wikidata, wikipathways, uniprot, idsm, rhea
# Each endpoint has specialized vocabularies and data types
```

### Tool Response Patterns
Following Claude Code principles: **"Tools return data, system prompts provide intelligence"**

**✅ Simplified Pattern:**
```json
{
  "query": "insulin",
  "candidates": [{"id": "Q7240673", "confidence": 0.8}]
}
```

**❌ Over-engineered Pattern:**
```json
{
  "success": true,
  "data": {...},
  "suggestions": [...],
  "claude_guidance": {...}
}
```

### Performance Characteristics
- ✅ **cl_entity**: 194 lines, ~200ms, enhanced confidence scoring and auto-property detection
- ✅ **cl_describe**: 198 lines, ~300ms, comprehensive cross-reference mappings for 15+ databases
- ✅ **cl_follow**: 300 lines, ~300ms, complete database links
- ✅ **cl_property**: 288 lines, ~4s, simplified analysis  
- ✅ **cl_sparql**: 218 lines, ~400ms, enhanced validation patterns and safety guardrails

**Architecture**: Simplified to Claude Code patterns (v2024.12) - extracted best features from complex versions, removed duplicate tools, unified SPARQL client with ontology discovery integration.

### Safety Guardrails
- **Auto-LIMIT**: Appends `LIMIT 100` to SELECT queries if missing
- **Query blocking**: Prevents `COUNT(*)` without reasonable limits, blocks dangerous operations (DELETE, INSERT, DROP)
- **Prefix validation**: Detects unknown prefixes and provides discovery guidance
- **Complexity analysis**: Monitors query complexity and suggests optimizations
- **Timeouts**: 10s max execution time
- **Anti-hallucination**: Only real QIDs/PIDs from search results, enhanced confidence scoring

## Final Note: Pattern Discovery Over Property Memorization

This guide emphasizes **pattern discovery** rather than memorizing specific properties. The semantic web structure is consistent across domains - learn the discovery pattern once, apply it everywhere.

**Key insight from Claude Code architecture**: Tools should be fast, reliable, and data-focused. Intelligence belongs in system prompts, not tool responses. Claude composes workflows and generalizes patterns naturally when given clean data to work with.

## Ontological Context Analysis

When exploring entities, always examine the **foundational ontological relationships** for deeper understanding:

### Critical Properties for Context
- **P31 (instance of)** / `rdf:type`: What IS this entity? (essential classifications)
- **P279 (subclass of)** / `rdfs:subClassOf`: What broader category does this belong to? (hierarchical context)

```bash
# Essential ontological queries for any entity
cl_sparql "SELECT ?class WHERE { wd:Q109997567 wdt:P31 ?class }" 
cl_sparql "SELECT ?superclass WHERE { wd:Q109997567 wdt:P279 ?superclass }"

# Example: Cube Orange Standard Set ontological analysis
# P31 reveals: embedded system + autopilot + technical standard + electronic device model
# P279 reveals: (none - leaf-level specification)
# Insight: "Standard Set" = certified technical standard, not marketing tier
```

**Why These Matter:**
- **P31** provides the **essential nature** of an entity (biological protein vs. electronic device vs. abstract concept)
- **P279** shows **hierarchical positioning** and inheritance relationships
- Together they reveal **semantic context** that pure labels cannot convey
- Critical for understanding **domain boundaries** and **concept precision**

## Structured Thinking for Research Exploration

After using CogitareLink tools, always apply the `<research_analysis>` pattern to:

1. **Examine Ontological Foundation**: What do P31/P279 reveal about the entity's true nature?
2. **Identify Research Threads**: What new questions emerged from the results?
3. **Spot Connection Opportunities**: Which cross-references or relationships warrant deeper investigation?
4. **Generate Follow-up Queries**: What SPARQL patterns or entity explorations would be valuable?
5. **Recognize Domain Patterns**: How do the discovered structures generalize to other entities?
6. **Plan Next Steps**: Which tools and parameters would advance the research most effectively?

This systematic approach transforms tool results from isolated data points into interconnected research workflows that leverage the full semantic web.