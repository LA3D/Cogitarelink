# Wikidata Property & Entity Discovery: Software 2.0 Workflow

**Use Case**: Semantic discovery of property meanings and entity type relationships using Claude Code intelligence instead of hardcoded classification logic.

**Context**: Replaces the orphaned `properties.py` module which attempted automated discovery with brittle hardcoded patterns. Uses CogitareLink's discovery-first workflow with Wikidata's unique RDF/knowledge representation hybrid.

## Overview

Wikidata is unique among semantic web endpoints - it uses RDF technology but has its own internal knowledge representation with special properties, service patterns, and cross-referencing mechanisms. This workflow shows how to discover what properties and entity types mean using Claude Code reasoning.

## Core Patterns

### 1. Property Discovery Pattern

**Goal**: Understand what Wikidata properties (P31, P279, P352, etc.) actually mean

**Workflow**:
```bash
# Step 1: Discover property meanings using VALUES pattern
cl_select "SELECT ?prop ?propLabel ?propDescription WHERE {
  VALUES ?prop { wd:P31 wd:P279 wd:P352 }
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
}"

# Step 2: Analyze and categorize (Claude Code reasoning)
# - P31 = "instance of" → fundamental classification property
# - P279 = "subclass of" → class hierarchy property  
# - P352 = "UniProt protein ID" → external reference property

# Step 3: Store semantic analysis
rdf_cache wikidata_properties --update-metadata '{
  "semantic_type": "property_definitions",
  "domains": ["classification", "biology"],
  "purpose": "wikidata_property_semantics",
  "provides": {"properties": 3},
  "learned_patterns": {
    "classification_properties": ["P31", "P279"],
    "external_id_properties": ["P352"],
    "cross_reference_capabilities": ["uniprot"]
  }
}'
```

**Key Wikidata-Specific Patterns**:
- **Always use `SERVICE wikibase:label`** for human-readable output
- **VALUES clause** for batch property queries (more efficient than individual queries)
- **External ID detection**: Properties with database names in descriptions (UniProt, PubChem, etc.)

### 2. Entity Type Discovery Pattern

**Goal**: Understand entity type hierarchies and domain categories

**Workflow**:
```bash
# Step 1: Discover entity types and their relationships
cl_select "SELECT ?type ?typeLabel ?typeDescription ?superclass WHERE {
  VALUES ?type { wd:Q8054 wd:Q7187 }
  OPTIONAL { ?type wdt:P279 ?superclass }
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
}"

# Results show:
# - Q8054 = "protein" with multiple superclasses (biomolecule, etc.)
# - Q7187 = "gene" with superclasses in molecular biology domain

# Step 2: Explore superclass meanings
cl_select "SELECT ?superclass ?superclassLabel WHERE {
  VALUES ?superclass { wd:Q422649 wd:Q424689 wd:Q15712714 }
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
}"

# Step 3: Claude Code domain inference and storage
rdf_cache biology_entity_types --update-metadata '{
  "semantic_type": "entity_taxonomy",
  "domains": ["biology", "molecular_biology"],
  "purpose": "wikidata_biology_classification",
  "provides": {"entity_types": 2, "relationships": 6},
  "learned_patterns": {
    "biology_entities": ["Q8054", "Q7187"],
    "hierarchy_depth": "multiple_inheritance",
    "domain_indicators": ["biomolecule", "heredity"]
  }
}'
```

### 3. External Reference Discovery Pattern

**Goal**: Find properties that enable cross-database bridging

**Workflow**:
```bash
# Step 1: Search for database identifier properties
cl_search "uniprot" --limit 10

# Step 2: Discover external ID properties by keyword patterns
cl_select "SELECT ?prop ?propLabel ?propDescription WHERE {
  ?prop wdt:P31 wd:Q19847637 .  # Wikidata property for identifiers
  FILTER(CONTAINS(LCASE(?propDescription), 'uniprot') || 
         CONTAINS(LCASE(?propDescription), 'pubchem') ||
         CONTAINS(LCASE(?propDescription), 'ensembl'))
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
} LIMIT 20"

# Step 3: Test cross-referencing capability
cl_select "SELECT ?entity ?uniprotId WHERE {
  ?entity wdt:P352 ?uniprotId .
} LIMIT 5"
```

**External Reference Indicators** (from original properties.py logic):
- Keywords: "id", "identifier", "registry", "database", "accession"
- Database names: "uniprot", "ensembl", "pdb", "pubchem", "chembl", "mesh", "cas"

## Advanced Wikidata Patterns

### Dynamic Cross-Database Discovery Pattern

**The Complete Workflow**: Wikidata entity → External ID discovery → Endpoint discovery → Domain database query

#### Step 1: Discover External Reference Properties
```bash
# Find external identifier properties by semantic analysis
cl_select "SELECT ?prop ?propLabel ?propDescription WHERE {
  VALUES ?prop { wd:P352 wd:P594 wd:P486 wd:P662 wd:P235 }
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
}"

# Results reveal external database connections:
# P352 = "UniProt protein ID" → UniProt database
# P594 = "Ensembl gene ID" → Ensembl database  
# P486 = "MeSH descriptor ID" → MeSH/PubMed
# P662 = "PubChem CID" → PubChem database
# P235 = "InChI" → Chemical structure databases
```

#### Step 2: Extract External IDs from Wikidata
```bash
# Get external IDs for specific entities (e.g., insulin)
cl_search "insulin" --limit 5  # Find insulin entity (Q7240)

cl_select "SELECT ?prop ?propLabel ?value WHERE {
  wd:Q7240 ?prop ?value .
  ?prop wdt:P31 wd:Q19847637 .  # Properties that are external identifiers
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
} LIMIT 10"

# Example results:
# P352: "P01308" (UniProt)
# P662: "6051" (PubChem) 
# P486: "D007328" (MeSH)
```

#### Step 3: Dynamic Endpoint Discovery
```bash
# Discover available SPARQL endpoints that might have this data
rdf_cache "" --list  # Check cached endpoints

# Query for databases that have SPARQL endpoints
cl_select "SELECT ?database ?databaseLabel ?endpoint WHERE {
  ?database wdt:P5305 ?endpoint .
  FILTER(CONTAINS(LCASE(?databaseLabel), 'uniprot') || 
         CONTAINS(LCASE(?databaseLabel), 'pubchem'))
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
}"

# Discover endpoint capabilities
rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot_service
rdf_cache uniprot_service --graph  # Examine service description
```

#### Step 4: Cross-Database Query Execution
```bash
# Use discovered external ID (P01308) to query UniProt directly
cl_select "SELECT ?protein ?name ?function WHERE {
  ?protein a up:Protein ;
           up:mnemonic 'INS_HUMAN' ;
           up:recommendedName/up:fullName ?name ;
           up:annotation/up:comment ?function .
  FILTER(CONTAINS(?function, 'glucose'))
}" --endpoint uniprot

# Alternative: Use URI construction pattern
cl_describe "http://purl.uniprot.org/uniprot/P01308" --endpoint uniprot

# Query PubChem using discovered CID
# (Note: PubChem doesn't have SPARQL, but shows the discovery pattern)
```

#### Step 5: Verification and Annotation
```bash
# Verify cross-reference worked by checking data consistency
cl_select "SELECT ?uniprotId ?description WHERE {
  wd:Q7240 wdt:P352 ?uniprotId ;
           schema:description ?description .
  FILTER(LANG(?description) = 'en')
}"

# Store discovered cross-reference capabilities
rdf_cache cross_db_discovery --update-metadata '{
  "semantic_type": "cross_database_mapping",
  "domains": ["biology", "chemistry", "cross_referencing"],
  "purpose": "dynamic_endpoint_bridging",
  "provides": {
    "external_id_properties": 5,
    "working_endpoints": 2,
    "verified_mappings": 3
  },
  "cross_reference_mappings": {
    "wikidata_to_uniprot": {"property": "P352", "pattern": "direct_id"},
    "wikidata_to_pubchem": {"property": "P662", "pattern": "numeric_cid"},
    "wikidata_to_mesh": {"property": "P486", "pattern": "descriptor_id"}
  },
  "endpoint_discovery": {
    "uniprot": "https://sparql.uniprot.org/sparql",
    "mesh_via_nlm": "discovered_but_no_sparql",
    "pubchem": "no_sparql_endpoint"
  }
}'
```

### Advanced Dynamic Patterns

#### Pattern A: Database-to-Database Bridging
```bash
# Discover entities in one database, find external IDs, query another
# Example: WikiPathways → Wikidata → UniProt

# 1. Find pathway in WikiPathways
cl_select "SELECT ?pathway ?title ?protein WHERE {
  ?pathway a wp:Pathway ;
           dc:title ?title ;
           wp:hasChemical ?protein .
  FILTER(CONTAINS(LCASE(?title), 'insulin'))
}" --endpoint wikipathways

# 2. Find Wikidata entity for the protein
cl_search "insulin receptor" --limit 3

# 3. Get UniProt ID from Wikidata
cl_select "SELECT ?entity ?uniprotId WHERE {
  ?entity rdfs:label ?label ;
          wdt:P352 ?uniprotId .
  FILTER(CONTAINS(LCASE(?label), 'insulin receptor'))
}"

# 4. Query UniProt with discovered ID
cl_describe "http://purl.uniprot.org/uniprot/P06213" --endpoint uniprot
```

#### Pattern B: Endpoint Capability Discovery
```bash
# Dynamically discover what databases are available
cl_select "SELECT DISTINCT ?database ?databaseLabel ?endpoint WHERE {
  ?database wdt:P5305 ?endpoint .
  ?database wdt:P31/wdt:P279* wd:Q8513 .  # biological databases
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
} LIMIT 20"

# Test endpoint accessibility and capabilities
for endpoint in $(cl_select "..." | jq -r '.results[].endpoint.value'); do
  echo "Testing: $endpoint"
  rdf_get "$endpoint" --cache-as "$(basename $endpoint)_service" 2>/dev/null || echo "Failed: $endpoint"
done
```

#### Pattern C: Cross-Reference Validation
```bash
# Verify that external IDs actually work across databases
# Get entity with multiple external IDs
cl_select "SELECT ?entity ?uniprotId ?pubchemId ?meshId WHERE {
  ?entity wdt:P352 ?uniprotId ;
          wdt:P662 ?pubchemId ;
          wdt:P486 ?meshId .
} LIMIT 5"

# Test each external reference
cl_select "SELECT ?protein ?name WHERE {
  ?protein a up:Protein ;
           up:accession 'P01308' ;
           up:recommendedName/up:fullName ?name .
}" --endpoint uniprot
```

### Domain Category Inference
```bash
# Discover domain patterns by analyzing superclass hierarchies
cl_select "SELECT ?class ?classLabel ?domain WHERE {
  VALUES ?class { wd:Q8054 wd:Q7187 wd:Q11173 }  # protein, gene, chemical compound
  ?class wdt:P279+ ?domain .
  ?domain wdt:P31 wd:Q4393107 .  # fundamental concepts
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
}"
```

## Software 2.0 Semantic Annotation

### Storing Discovery Results
```bash
# After discovery session, store learned patterns
rdf_cache wikidata_discovery_session --update-metadata '{
  "semantic_type": "discovery_session",
  "domains": ["wikidata", "biology", "cross_referencing"],
  "format_type": "sparql_results",
  "purpose": "property_entity_discovery",
  "dependencies": ["wikidata_endpoint"],
  "provides": {
    "properties_discovered": 15,
    "entity_types_discovered": 8,
    "cross_references_found": 5
  },
  "confidence_scores": {
    "property_classification": 0.95,
    "domain_inference": 0.85,
    "external_id_detection": 0.90
  },
  "vocabulary_size": 23,
  "learned_at": '$(date +%s)',
  "usage_patterns": [
    "VALUES_batch_queries",
    "SERVICE_wikibase_label",
    "P279_hierarchy_traversal",
    "external_id_bridging"
  ]
}'
```

## Anti-Patterns from properties.py

**What NOT to do** (hardcoded approaches that were replaced):

❌ **Hardcoded heuristics**: 
```python
# OLD: Brittle keyword matching
external_indicators = ["id", "identifier", "registry"]
return any(indicator in text_to_check for indicator in external_indicators)
```

✅ **Claude Code analysis**:
```bash
# NEW: Semantic understanding through discovery
cl_select "SELECT ?prop ?propDescription WHERE { wd:P352 ?prop ?propDescription }"
# Claude analyzes: "identifier for a protein per the UniProt database" → external reference
```

❌ **Automatic domain classification**:
```python  
# OLD: Pattern matching for domains
if any(term in uri_lower for term in ['protein', 'gene']):
    return 'biology'
```

✅ **Discovery-driven classification**:
```bash
# NEW: Explore actual relationships
cl_select "SELECT ?type ?superclass WHERE { wd:Q8054 wdt:P279 ?superclass }"
# Claude reasons about biomolecule → molecular biology domain
```

## Complete Working Example: Insulin Discovery Chain

**Goal**: Start with "insulin" concept, discover external identifiers, find endpoints, query domain databases

### End-to-End Workflow
```bash
# 1. Find insulin entity in Wikidata
cl_search "insulin" --limit 3
# Result: Q7240 (insulin), Q1570135 (insulin receptor), etc.

# 2. Discover external identifier properties for insulin
cl_select "SELECT ?prop ?propLabel ?value WHERE {
  wd:Q7240 ?prop ?value .
  ?prop wdt:P31 wd:Q19847637 .  # external identifier properties
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
} LIMIT 10"
# Result: P352 (UniProt ID): P01308, P662 (PubChem CID): 6051, etc.

# 3. Dynamically discover which databases have SPARQL endpoints
cl_select "SELECT ?database ?databaseLabel ?endpoint WHERE {
  ?database wdt:P5305 ?endpoint .
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
} LIMIT 20"
# Result: UniProt → https://sparql.uniprot.org/sparql (found!)

# 4. Discover UniProt service capabilities
rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot_service
rdf_cache uniprot_service --graph
# Result: up: vocabulary, protein classes, annotation patterns

# 5. Query UniProt using discovered external ID
cl_describe "http://purl.uniprot.org/uniprot/P01308" --endpoint uniprot
# Result: Complete protein data from UniProt database

# 6. Verify cross-reference consistency
cl_select "SELECT ?name ?organism WHERE {
  ?protein a up:Protein ;
           up:accession 'P01308' ;
           up:recommendedName/up:fullName ?name ;
           up:organism/up:scientificName ?organism .
}" --endpoint uniprot
# Result: "Insulin" + "Homo sapiens" (validates the connection)

# 7. Store the complete discovery chain
rdf_cache insulin_discovery_chain --update-metadata '{
  "semantic_type": "cross_database_discovery_chain", 
  "domains": ["biology", "endocrinology"],
  "purpose": "dynamic_cross_reference_validation",
  "discovery_chain": {
    "start_entity": "Q7240",
    "external_ids": {"uniprot": "P01308", "pubchem": "6051"},
    "endpoints_discovered": ["https://sparql.uniprot.org/sparql"],
    "validation_successful": true
  },
  "provides": {"validated_mappings": 1, "working_endpoints": 1}
}'
```

### Key Success Patterns
- ✅ **Wikidata Hub Strategy**: Use Wikidata as central hub for external ID discovery
- ✅ **Dynamic Endpoint Discovery**: Query P5305 to find available SPARQL endpoints  
- ✅ **Service Description Pattern**: Always cache endpoint capabilities first
- ✅ **Validation Loop**: Test external IDs actually work in target databases
- ✅ **Semantic Annotation**: Store successful discovery chains for reuse

## Session Template

For future property/entity discovery sessions, follow this template:

1. **Discovery Phase**: Use `cl_select` with VALUES and SERVICE patterns
2. **Analysis Phase**: Claude Code reasoning about semantic meanings
3. **Classification Phase**: Identify patterns (classification, external ref, domain)
4. **Cross-Reference Phase**: Use P5305 to discover endpoints, test external IDs
5. **Annotation Phase**: Store insights with `rdf_cache --update-metadata`
6. **Validation Phase**: Verify cross-database queries work end-to-end

## Why This Works Better

- **No Hardcoded Logic**: Claude Code provides semantic reasoning
- **Wikidata-Aware**: Uses proper SERVICE patterns and Wikidata conventions  
- **Extensible**: Easy to discover new properties and relationships
- **Cacheable**: Results stored in enhanced cache with semantic metadata
- **Cross-Database**: Enables proper semantic web bridging

This replaces 400+ lines of brittle hardcoded logic with flexible, intelligent discovery workflows.