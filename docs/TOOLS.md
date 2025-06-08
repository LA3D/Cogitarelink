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

### Pattern 4: Chemical Compound Discovery
```bash
# Chemical compound with rich structural identifiers
cl_entity "caffeine" --domain-hint biology | jq '.candidates[0].id'
# → "Q60235"

# Explore chemical structure and database mappings
cl_describe Q60235 | jq '.cross_references.pubchem_cid[0]'
# → "2519"

cl_describe Q60235 | jq '.cross_references.smiles[0]' 
# → "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"

# Rich chemical database coverage
cl_follow Q60235 | jq '.data.statistics.total_identifiers'
# → Multiple chemical databases (ChEBI, CAS, ChEMBL, DrugBank, PubChem, KEGG)
```

<research_analysis>
- SMILES and molecular formulas enable computational chemistry workflows
- Multiple chemical database IDs allow cross-database validation and data integration
- PDB structures (when available) connect to 3D molecular modeling databases
- Chemical identifiers enable pathway analysis and drug discovery research
- Cross-references support both small molecule and macromolecule research workflows
</research_analysis>

### Pattern 5: Geographic Entity Discovery
```bash
# Geographic entity with coordinate information
cl_entity "Paris" --domain-hint geography | jq '.candidates[0].id'
# → "Q90"

# Extract geographic coordinates and administrative identifiers
cl_describe Q90 | jq '.cross_references.coordinates'
# → {"latitude": 48.857, "longitude": 2.352, "precision": 0.0003}

# Geographic entities may have limited cross-references but rich coordinate data
cl_describe Q90 | jq '.cross_references | keys'
# → ["coordinates", "mesh", "umls"]
```

<research_analysis>
- Coordinate data enables spatial analysis and GIS workflows
- Geographic entities often have fewer external database mappings than biological entities
- Medical subject headings (MeSH) may appear for major cities due to epidemiological research
- The coordinates format provides precision information for spatial accuracy assessment
- Geographic discovery patterns focus more on hierarchical relationships than database cross-references
</research_analysis>

### Pattern 6: Entity Type Coverage Analysis
```bash
# Corporate entities typically have minimal cross-references
cl_entity "Lockheed Martin" --domain-hint corporate | jq '.candidates[0].id'
# → "Q7240"

cl_describe Q7240 | jq '.cross_references'
# → {} (empty - corporate entities lack biological/chemical database mappings)

# Biological entities have rich cross-reference coverage
cl_entity "hemoglobin" --domain-hint biology | jq '.candidates[0].id'  
# → "Q43041"

cl_describe Q43041 | jq '.cross_references | keys'
# → ["cas", "chebi", "drugbank", "kegg", "mesh", "molecular_formula", "umls"]
```

<research_analysis>
- Cross-reference availability depends heavily on entity domain and type
- Biological/chemical entities have the richest database coverage (15+ databases)
- Geographic entities provide coordinate data and some administrative identifiers
- Corporate/organizational entities may lack relevant cross-references in our current mapping
- The tool design prioritizes scientific research workflows over business intelligence
- Empty cross-references are handled gracefully, returning `{}` rather than errors
</research_analysis>

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
**Returns**: `{"entity": {...}, "cross_references": {"uniprot": ["P01308"], "pdb": [...]}}`
**Features**: Clean cross-reference format for 17 databases:
- **Proteins**: uniprot, pdb, refseq, ensembl_gene, entrez_gene, hgnc
- **Chemicals**: chebi, cas, chembl, drugbank, pubchem_cid, pubchem_sid, kegg, smiles, isomeric_smiles, molecular_formula
- **Medical**: mesh, umls, disease_ontology, ec_number  
- **Geographic**: coordinates (latitude, longitude, precision)
**Performance**: ~300ms, optimized for Claude Code jq navigation and Entity-Known discovery pathways

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

### cl_ontfetch - HTTP Ontology Dereferencing
**NEW**: Comprehensive HTTP-based ontology dereferencing with RDFLib integration
```bash
# Direct URI dereferencing with content negotiation
cl_ontfetch discover "http://xmlns.com/foaf/0.1/" --domain biology

# Schema.org using specialized strategy  
cl_ontfetch discover "https://schema.org/version/latest/schemaorg-current-https.jsonld"

# Known endpoint discovery
cl_ontfetch sparql "https://sparql.uniprot.org/sparql" --domain proteins

# List cached ontologies
cl_ontfetch cache --list
```
**Returns**: `{"success": true, "ontology_type": "http_dereferenced", "properties": [...], "classes": [...], "vocabularies": [...], "metadata": {...}}`
**Features**: 
- **True HTTP Dereferencing**: Content negotiation, Accept headers, multiple URI fallback patterns
- **RDFLib Integration**: Robust parsing of Turtle, RDF/XML, JSON-LD, N-Triples, N3
- **Semantic Extraction**: OWL/RDFS properties, classes, domains, ranges with full metadata  
- **Claude Guidance**: Domain-specific usage recommendations and SPARQL query patterns
- **Vocabulary Integration**: Automatic registration with CogitareLink's vocabulary system
- **Comprehensive Error Handling**: Graceful failures with specific improvement suggestions

**Supported Ontology Patterns**:
- ✅ **Standard RDF**: FOAF (620 triples, 123 properties), Dublin Core (107 triples, 15 properties)
- ✅ **OWL Ontologies**: SKOS Core (252 triples, 56 properties), BIBO (1,224 triples, 120 properties)
- ✅ **JSON-LD**: Schema.org specialized URLs (1,508 properties, 919 classes)
- ✅ **Content Negotiation**: Automatic format detection and quality scoring

**Performance**: ~2-10s depending on ontology size, with intelligent caching and vocabulary registration

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

## Cross-Database Discovery Patterns

The most powerful CogitareLink capability is **cross-database research workflows** that follow semantic links from Wikidata to specialized SPARQL endpoints. These patterns work for any domain - biological, chemical, geographical, or cultural.

### The Universal Discovery Workflow

**Wikidata → External Identifiers → Specialized SPARQL Endpoints**

```bash
# 1. Start with natural language in Wikidata
cl_entity "insulin" --domain-hint biology
# → Q7240673 (preproinsulin)

# 2. Discover cross-references and SPARQL endpoints  
cl_describe Q7240673
# → P352: P01308 (UniProt ID)
# → endpoint_type: "sparql_endpoint" 
# → sparql_endpoint: "https://sparql.uniprot.org/sparql"

# 3. Use external ID to discover URI patterns in target endpoint
cl_sparql "SELECT * WHERE { ?s ?p ?o } LIMIT 10" --endpoint uniprot
# → Found pattern: http://purl.uniprot.org/uniprot/P01308

# 4. Enumerate available properties for the specific entity
cl_sparql "SELECT DISTINCT ?property WHERE { <http://purl.uniprot.org/uniprot/P01308> ?property ?value } LIMIT 50" --endpoint uniprot
# → up:mnemonic, up:sequence, rdfs:label, up:organism, etc.

# 5. Construct informed queries using discovered schema
cl_sparql "SELECT ?name ?mnemonic ?organism WHERE { <http://purl.uniprot.org/uniprot/P01308> rdfs:label ?name ; up:mnemonic ?mnemonic ; up:organism ?organism }" --endpoint uniprot
# → "Insulin", "INS_HUMAN", "http://purl.uniprot.org/taxonomy/9606"
```

### Discovery State Machine Integration

The clean cross-reference format from `cl_describe` integrates seamlessly with CogitareLink's **Entity-Known Discovery pathway**:

```bash
# Step 1: Discover external identifiers
UNIPROT_ID=$(cl_describe Q7240673 | jq -r '.cross_references.uniprot[0]')
# → "P01308"

# Step 2: Entity-Known discovery automatically converts to full URI
# P01308 → http://purl.uniprot.org/uniprot/P01308

# Step 3: DESCRIBE query extracts entity affordances
cl_sparql "DESCRIBE <http://purl.uniprot.org/uniprot/P01308>" --endpoint uniprot
# → Properties, types, relationships available for this protein

# Step 4: Build informed queries from discovered affordances
cl_sparql "SELECT ?protein ?function WHERE { ?protein up:classifiedWith ?function . ?protein up:mnemonic 'INS_HUMAN' }" --endpoint uniprot
```

**Semantic Hierarchy Workflow**:
1. **External Identifier Anchor** (clean IDs from `cl_describe`: uniprot, chebi, pdb, etc.)
2. **URI Pattern Resolution** (automatic conversion: P01308 → http://purl.uniprot.org/uniprot/P01308)  
3. **DESCRIBE-based Affordance Discovery** (understand what this entity can do)
4. **Schema Building** (construct patterns from actual entity capabilities)
5. **Informed Query Construction** (queries based on discovered semantics, not assumptions)

### Cross-Database Research Strategies

#### Strategy 1: Biological Research Chain
```bash
# Protein → Structure → Pathways → Diseases
cl_entity "spike protein" → cl_describe → 
cl_sparql --endpoint uniprot → cl_sparql --endpoint wikipathways
```

#### Strategy 2: Chemical Research Chain  
```bash
# Compound → Properties → Reactions → Targets
cl_entity "caffeine" → cl_describe →
cl_sparql --endpoint idsm → chemical pathway analysis
```

#### Strategy 3: Geographic Research Chain
```bash
# Location → Administrative divisions → Population → Economic data
cl_entity "Paris" → cl_describe →
cl_sparql --endpoint osm-qlever → spatial analysis
```

### Error-Guided Discovery Principles

When queries fail, use **incremental refinement**:

1. **Start Simple**: `SELECT * WHERE { ?s ?p ?o } LIMIT 10`
2. **Add Specificity**: Use known external identifiers
3. **Discover Schema**: Enumerate properties before complex queries
4. **Build Incrementally**: Add clauses one at a time
5. **Follow Error Guidance**: Use error messages to guide next steps

### Endpoint Classification Insights

**Well-Designed Endpoints** (UniProt, Wikidata):
- Comprehensive VoID/Service Description documents
- Rich vocabulary documentation
- Consistent URI patterns

**General SPARQL Endpoints** (Most others):
- Limited or no formal documentation
- Require discovery-based schema exploration
- Need incremental query building

**The Key Insight**: Use **semantic-first discovery** with branching pathways based on entity availability. This reveals actual capabilities rather than assumed schemas.

## Semantic Discovery Methodology

CogitareLink follows a **semantic hierarchy** for discovery, prioritizing authoritative semantics over statistical analysis:

### Discovery Branching Structure

```
1. Service Description/VoID Discovery (Authoritative Semantics)
   ↓
2. Entity Availability Check
   ├─ Entity Known/Discoverable → Entity-Known Discovery Pathway
   └─ No Entity Available → Property Affordance Discovery Pathway
   ↓
3. Statistical Fallback (Last Resort)
```

### Pathway A: Entity-Known Discovery (Semantic)
**When**: External identifier available or discoverable
**Process**: External ID → DESCRIBE entity → Extract affordances → Build patterns
**Focus**: "What can this specific entity type do in this endpoint?"

```bash
# Example: Insulin protein discovery
cl_entity "insulin" | jq '.candidates[0].id'
# → Q7240673

cl_describe Q7240673 | jq '.cross_references.uniprot[0]'
# → P01308

# DESCRIBE the actual entity to understand its affordances
cl_sparql "DESCRIBE <http://purl.uniprot.org/uniprot/P01308>" --endpoint uniprot
# → Shows: sequences, citations, functions, interactions, pathways

# Build queries based on discovered affordances
cl_sparql "SELECT ?protein ?function WHERE { ?protein up:classifiedWith ?function . ?protein up:mnemonic 'INS_HUMAN' }" --endpoint uniprot
```

### Pathway B: Property Affordance Discovery (Exploratory) 
**When**: No known entities to anchor discovery
**Process**: Property enumeration → Affordance analysis → Entity type discovery
**Focus**: "What kinds of things can I do here? What entity types exist?"

```bash
# Discover what kinds of entities and affordances exist
cl_sparql "SELECT DISTINCT ?type (COUNT(?entity) as ?count) WHERE { ?entity rdf:type ?type } GROUP BY ?type ORDER BY DESC(?count) LIMIT 20" --endpoint unknown_endpoint

# Discover primary affordances/relationships
cl_sparql "SELECT DISTINCT ?property (COUNT(*) as ?usage) WHERE { ?s ?property ?o } GROUP BY ?property ORDER BY DESC(?usage) LIMIT 50" --endpoint unknown_endpoint
```

### Semantic Hierarchy Principles

1. **Authoritative First**: Service descriptions and VoID reveal intended semantics
2. **Affordance-Based**: DESCRIBE entities to understand "what can this do?" not just "what exists?"
3. **Type-Aware**: Discover entity types and their capabilities, not just property frequencies  
4. **Context-Driven**: Build from semantic understanding, not statistical analysis
5. **Fallback Strategy**: Use property enumeration only when semantic methods fail

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