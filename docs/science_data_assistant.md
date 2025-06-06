# Science Data Assistant Implementation Guide

**Enhanced Wikidata MCP Tools for Biological Research**

This document outlines the implementation plan for transforming the Wikidata MCP tools into a comprehensive science data assistant capable of federated queries across multiple biological databases.

## 🧬 Overview

The science data assistant enhances the existing Wikidata MCP tools with:
- **Automatic cross-reference resolution** to specialized biological databases
- **Federated SPARQL queries** across multiple endpoints
- **Domain-specific workflows** for biological research
- **Agent-friendly suggestions** for multi-step research tasks

## 📊 Current Capabilities

### Working Base Tools
```bash
# Entity search and details
python wikidata_cli.py search "SARS-CoV-2"
python wikidata_cli.py entity Q82069695

# SPARQL queries for scientific data
python wikidata_cli.py sparql "SELECT ?compound ?formula WHERE { 
  ?compound wdt:P31 wd:Q11173 . 
  ?compound wdt:P274 ?formula 
} LIMIT 5"

# Property lookup for cross-references
python wikidata_cli.py property P352  # UniProt ID
python wikidata_cli.py property P683  # ChEBI ID
```

### Rich Scientific Content Available
- **Proteins**: Q8054 with UniProt cross-references (P352)
- **Genes**: Q7187 with chromosome locations (P1057)
- **Chemical compounds**: Q11173 with molecular formulas (P274)
- **Viruses**: Q82069695 with genome sequences (P4333)
- **Diseases**: Comprehensive COVID-19/SARS-CoV-2 data

## 🔗 Enhanced Cross-Reference Resolution

### Phase 1: Core Database Integration

#### 1.1 Enhanced Entity Tool
```python
@app.tool()
async def wikidata_entity_enriched(
    entity_id: str, 
    resolve_xrefs: bool = True,
    include_databases: List[str] = ["uniprot", "chebi", "genbank"]
) -> str:
    """
    Enhanced entity details with automatic cross-reference resolution
    
    SCIENCE-SPECIFIC FEATURES:
    • Auto-resolves UniProt protein data (sequences, functions, diseases)
    • Enriches ChEBI chemical properties and classifications
    • Fetches GenBank genome sequences and annotations
    • Provides agent-friendly suggestions for follow-up queries
    
    Args:
        entity_id: Wikidata entity ID (Q...)
        resolve_xrefs: Whether to fetch data from external databases
        include_databases: Which databases to query for enrichment
    
    Returns:
        Enhanced JSON with external_data section and smart suggestions
    """
    
    # Get base Wikidata entity
    base_data = await wikidata_entity(entity_id)
    
    if resolve_xrefs:
        # Resolve cross-references using multiple APIs
        external_data = await resolve_cross_references(
            base_data['claims'], 
            include_databases
        )
        base_data['external_data'] = external_data
        
        # Add agent-friendly suggestions
        base_data['suggestions'] = generate_research_suggestions(
            base_data, external_data
        )
        
    return base_data
```

#### 1.2 Cross-Reference Resolver
```python
async def resolve_cross_references(claims: dict, databases: List[str]) -> dict:
    """Resolve Wikidata cross-references to external biological databases"""
    
    resolved = {}
    
    # UniProt protein data
    if 'uniprot' in databases and 'P352' in claims:
        uniprot_id = claims['P352'][0]['value']
        resolved['uniprot'] = await fetch_uniprot_data(uniprot_id)
    
    # ChEBI chemical data  
    if 'chebi' in databases and 'P683' in claims:
        chebi_id = claims['P683'][0]['value']
        resolved['chebi'] = await fetch_chebi_data(chebi_id)
        
    # GenBank genome data
    if 'genbank' in databases and 'P4333' in claims:
        genbank_id = claims['P4333'][0]['value'] 
        resolved['genbank'] = await fetch_genbank_data(genbank_id)
        
    # bioDBnet crosswalk service
    if len(resolved) > 0:
        resolved['crosswalks'] = await fetch_biodbnet_crosswalks(claims)
        
    return resolved

async def fetch_uniprot_data(uniprot_id: str) -> dict:
    """Fetch protein data from UniProt REST API"""
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    
    # Implementation with proper error handling and rate limiting
    # Returns: protein_name, organism, sequence_length, function, diseases
    
async def fetch_chebi_data(chebi_id: str) -> dict:
    """Fetch chemical data from ChEBI API"""
    # Implementation for chemical properties, IUPAC names, etc.
    
async def fetch_genbank_data(genbank_id: str) -> dict:
    """Fetch genome data from GenBank/NCBI E-utilities"""
    # Implementation for sequence data, organism, annotations
```

#### 1.3 Database Navigation Tool
```python
@app.tool()
async def follow_database_link(
    wikidata_id: str, 
    target_db: str,
    query_type: str = "basic"
) -> str:
    """
    Follow cross-references to external biological databases
    
    SUPPORTED DATABASES:
    • uniprot: Protein sequences, structures, functions, diseases
    • chebi: Chemical properties, classifications, reactions
    • genbank: Genome sequences, annotations, assemblies
    • mesh: Medical subject headings and relationships
    • pdb: 3D protein structures and complexes
    • reactome: Biological pathways and reactions
    
    QUERY TYPES:
    • basic: Essential information for the entity
    • detailed: Comprehensive data including annotations
    • network: Related entities and connections
    • pathways: Biological pathway associations
    
    Args:
        wikidata_id: Source Wikidata entity (Q...)
        target_db: Target database (uniprot|chebi|genbank|mesh|pdb|reactome)
        query_type: Depth of information to retrieve
    
    Returns:
        Rich JSON with database-specific information and follow-up suggestions
    """
```

## 🌐 Federated SPARQL Integration

### Phase 2: Multi-Endpoint Queries

#### 2.1 Federated Query Tool
```python
@app.tool()
async def federated_biological_query(
    query_type: str,
    entity_name: str,
    include_endpoints: List[str] = ["wikidata", "uniprot"],
    organism_filter: Optional[str] = None
) -> str:
    """
    Execute federated SPARQL queries across biological databases
    
    QUERY TYPES:
    • protein_analysis: Complete protein characterization across databases
    • disease_network: Disease-protein-drug connections and pathways
    • chemical_interactions: Compound-protein binding and reactions
    • pathway_exploration: Metabolic and signaling pathways
    • evolution_analysis: Taxonomic relationships and sequence evolution
    • structure_function: 3D structures and functional domains
    
    ENDPOINTS:
    • wikidata: Entity relationships and cross-references
    • uniprot: Protein sequences, functions, diseases (225+ billion triples)
    • rhea: Biochemical reactions and pathways
    • chebi: Chemical properties and classifications
    • rdf.ncbi.nlm.nih.gov: NCBI databases (PubMed, taxonomy, etc.)
    
    Args:
        query_type: Type of biological analysis to perform
        entity_name: Target entity (protein, compound, disease, etc.)
        include_endpoints: Which SPARQL endpoints to include
        organism_filter: Optional taxonomic filter (e.g., "Homo sapiens")
    
    Returns:
        Unified results combining data from multiple specialized databases
    """
    
    # Build federated query based on type
    if query_type == "protein_analysis":
        return await execute_protein_analysis(entity_name, include_endpoints)
    elif query_type == "disease_network":
        return await execute_disease_network(entity_name, include_endpoints)
    # ... other query types
```

#### 2.2 Example Federated Queries

##### Protein Analysis Workflow
```sparql
# Step 1: Find protein in Wikidata with cross-references
SELECT ?protein ?proteinLabel ?uniprot_id ?pdb_id WHERE {
  SERVICE <https://query.wikidata.org/sparql> {
    ?protein wdt:P31 wd:Q8054 .
    ?protein rdfs:label "{entity_name}"@en .
    ?protein wdt:P352 ?uniprot_id .
    OPTIONAL { ?protein wdt:P637 ?pdb_id }
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
  }
}

# Step 2: Get detailed protein data from UniProt
PREFIX up: <http://purl.uniprot.org/core/>
SELECT ?protein ?sequence ?function ?disease ?pathway WHERE {
  SERVICE <https://sparql.uniprot.org/sparql> {
    ?protein a up:Protein .
    ?protein up:sequence ?seq .
    ?seq rdf:value ?sequence .
    ?protein up:annotation ?func_ann .
    ?func_ann a up:Function_Annotation .
    ?func_ann rdfs:comment ?function .
    OPTIONAL {
      ?protein up:annotation ?disease_ann .
      ?disease_ann a up:Disease_Annotation .
      ?disease_ann rdfs:comment ?disease
    }
    FILTER(?protein = <http://purl.uniprot.org/uniprot/{uniprot_id}>)
  }
}
```

##### Disease-Protein Network
```sparql
# Federated query combining Wikidata diseases with UniProt proteins
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX up: <http://purl.uniprot.org/core/>

SELECT ?disease ?diseaseLabel ?protein ?proteinLabel ?function WHERE {
  # Find disease in Wikidata
  SERVICE <https://query.wikidata.org/sparql> {
    ?disease wdt:P31 wd:Q12136 .
    ?disease rdfs:label ?diseaseLabel .
    FILTER(CONTAINS(LCASE(?diseaseLabel), "{disease_name}"))
  }
  
  # Find associated proteins in UniProt
  SERVICE <https://sparql.uniprot.org/sparql> {
    ?protein up:annotation ?ann .
    ?ann a up:Disease_Annotation .
    ?ann rdfs:comment ?comment .
    ?protein rdfs:label ?proteinLabel .
    ?protein up:annotation ?func_ann .
    ?func_ann a up:Function_Annotation .
    ?func_ann rdfs:comment ?function .
    FILTER(CONTAINS(LCASE(?comment), "{disease_name}"))
  }
}
```

### Phase 3: Advanced Science Workflows

#### 3.1 Biological Network Explorer
```python
@app.tool()
async def explore_biological_networks(
    entity_id: str,
    network_type: str,
    depth: int = 2,
    include_pathways: bool = True
) -> str:
    """
    Explore biological networks and pathways using multiple databases
    
    NETWORK TYPES:
    • protein_interactions: STRING database and IntAct integration
    • metabolic_pathways: Reactome, KEGG, and WikiPathways
    • gene_regulation: Transcription factors and regulatory networks
    • disease_associations: Disease-gene-drug networks
    • phylogenetic: Evolutionary relationships and sequence conservation
    • structural: Protein domains, folds, and 3D interactions
    
    Args:
        entity_id: Starting Wikidata entity
        network_type: Type of biological network to explore
        depth: How many relationship hops to include (1-3)
        include_pathways: Whether to include pathway context
    
    Returns:
        Network data with nodes, edges, and pathway annotations
    """
```

#### 3.2 Database Crosswalk Service
```python
@app.tool()
async def database_crosswalk(
    source_id: str,
    source_db: str,
    target_db: str,
    conversion_path: Optional[str] = None
) -> str:
    """
    Convert identifiers between biological databases using bioDBnet
    
    SUPPORTED DATABASES:
    • uniprot ↔ genbank ↔ pdb (protein sequences to structures)
    • chebi ↔ pubchem ↔ drugbank (chemical compound mappings)
    • ensembl ↔ ncbi_gene ↔ hgnc (gene identifier conversion)
    • mesh ↔ umls ↔ snomed (medical terminology mapping)
    
    CONVERSION PATHS:
    • protein_to_structure: UniProt → PDB via cross-references
    • compound_to_targets: ChEBI → UniProt via binding annotations
    • gene_to_pathways: Ensembl → Reactome via pathway participation
    • disease_to_drugs: MESH → DrugBank via therapeutic relationships
    
    Args:
        source_id: Source database identifier
        source_db: Source database name
        target_db: Target database name  
        conversion_path: Optional predefined conversion pathway
    
    Returns:
        Conversion results with confidence scores and metadata
    """
```

## 🎯 Agent-Friendly Enhancements

### Smart Suggestion System
```python
def generate_research_suggestions(base_data: dict, external_data: dict) -> dict:
    """Generate intelligent follow-up suggestions based on entity data"""
    
    suggestions = {
        "next_tools": [],
        "research_workflows": [],
        "database_links": [],
        "scientific_questions": []
    }
    
    # Analyze entity type and data to provide specific guidance
    entity_type = analyze_entity_type(base_data)
    
    if entity_type == "protein":
        if "uniprot" in external_data:
            suggestions["research_workflows"].extend([
                "Explore protein-protein interactions using STRING database",
                "Find 3D structures in PDB for structural analysis",
                "Investigate metabolic pathways via Reactome"
            ])
            
        if "diseases" in external_data.get("uniprot", {}):
            suggestions["scientific_questions"].extend([
                "What other proteins are involved in these diseases?",
                "Are there approved drugs targeting this protein?",
                "What genetic variants affect protein function?"
            ])
    
    elif entity_type == "chemical_compound":
        suggestions["research_workflows"].extend([
            "Find protein targets using ChEBI-UniProt crosslinks",
            "Explore metabolic reactions via Rhea database",
            "Investigate drug safety profiles"
        ])
        
    return suggestions
```

### Domain-Specific Templates
```python
@app.tool()
async def apply_science_template(
    entity_id: str,
    template: str
) -> str:
    """
    Apply domain-specific templates for biological entities
    
    AVAILABLE TEMPLATES:
    • virus: Genome size, taxonomy, host organisms, diseases caused
    • protein: Sequence, structure, function, interactions, diseases
    • compound: Molecular formula, structure, biological activity, targets
    • gene: Chromosome location, protein products, regulation, variants
    • disease: Causative agents, affected pathways, therapeutic targets
    • pathway: Participating molecules, regulation, disease associations
    
    Args:
        entity_id: Wikidata entity ID
        template: Template type to apply
        
    Returns:
        Structured data formatted according to template with relevant cross-references
    """
```

## 🚀 Implementation Strategy

### Development Phases

#### **Phase 1: Foundation Enhancement** (4-6 weeks)
1. **Enhanced entity tool** with basic cross-reference resolution
2. **UniProt REST API integration** for protein data
3. **ChEBI API integration** for chemical compounds
4. **GenBank/NCBI integration** for genomic data
5. **Agent-friendly response formatting** with suggestions

#### **Phase 2: Federated Queries** (6-8 weeks)
1. **SPARQL endpoint client** with multiple endpoint support
2. **Federated query builder** for common biological questions
3. **bioDBnet integration** for database crosswalks
4. **UniProt SPARQL integration** for advanced protein queries
5. **Error handling and fallback strategies**

#### **Phase 3: Advanced Workflows** (8-10 weeks)
1. **Biological network exploration** tools
2. **Pathway analysis integration** (Reactome, WikiPathways)
3. **Literature mining connections** (PubMed integration)
4. **Predictive analysis features** (AI-driven hypothesis generation)
5. **Real-time data integration** capabilities

### Testing Strategy

#### **Unit Testing**
- Individual API integrations (UniProt, ChEBI, GenBank)
- SPARQL query generation and execution
- Cross-reference resolution accuracy
- Error handling and timeout management

#### **Integration Testing**
- End-to-end federated query workflows
- Multi-database consistency checks
- Performance under load
- Cache effectiveness and invalidation

#### **Scientific Validation**
- Accuracy of cross-reference mappings
- Completeness of biological data
- Relevance of agent suggestions
- User workflow completeness

### Performance Considerations

#### **Caching Strategy**
- **Entity cache**: Wikidata entities (15 min TTL)
- **Cross-reference cache**: External database mappings (1 hour TTL)
- **SPARQL cache**: Query results (30 min TTL)
- **API response cache**: External API calls (2 hour TTL)

#### **Rate Limiting**
- Respect API limits for all external services
- Implement exponential backoff for failed requests
- Queue management for concurrent requests
- User-friendly error messages for rate limit hits

#### **Fallback Strategies**
- Graceful degradation when external services are unavailable
- Cached data serving during outages
- Alternative API endpoints where available
- Clear indication of data freshness and availability

## 📈 Success Metrics

### Technical Metrics
- **Response time**: <2 seconds for basic queries, <10 seconds for federated
- **Success rate**: >95% for cross-reference resolution
- **Cache hit rate**: >80% for repeated queries
- **API availability**: >99% uptime for core functionality

### User Experience Metrics
- **Query completeness**: Can agents complete complex research workflows?
- **Suggestion relevance**: How often do agents follow suggested next steps?
- **Data accuracy**: Validation against known biological facts
- **Workflow efficiency**: Time to complete research tasks

### Scientific Impact Metrics
- **Coverage**: Percentage of biological entities with enriched data
- **Cross-reference accuracy**: Validation against authoritative sources
- **Novel discoveries**: Unexpected connections found through federated queries
- **Research acceleration**: Time saved in data gathering and analysis

## 🔮 Future Enhancements

### Advanced Integrations
- **AlphaFold**: Protein structure predictions
- **ChEMBL**: Drug discovery and medicinal chemistry
- **STRING**: Protein-protein interaction networks
- **KEGG**: Metabolic pathway analysis
- **ClinVar**: Clinical genetic variant data

### AI-Powered Features
- **Hypothesis generation**: AI-driven research question suggestions
- **Literature summarization**: Automatic paper analysis and synthesis
- **Predictive modeling**: Machine learning for drug discovery
- **Personalized research**: Tailored suggestions based on user patterns

### Real-Time Data
- **Live experimental data**: Integration with laboratory databases
- **Clinical trial data**: Real-time therapeutic development tracking
- **Publication feeds**: Latest research paper integration
- **Patent monitoring**: Intellectual property tracking for discoveries

This implementation plan transforms the Wikidata MCP tools into a comprehensive science data assistant capable of sophisticated biological research workflows with seamless cross-database integration and intelligent agent guidance.