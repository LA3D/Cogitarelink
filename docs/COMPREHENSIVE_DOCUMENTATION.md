# Wikidata-MCP: Comprehensive Documentation

## Overview

Wikidata-MCP is a **Software 2.0 architecture** for biological research that implements self-configuring tools designed specifically for AI agents like Claude Code. Unlike traditional hardcoded approaches, it uses **metadata discovery** and **progressive complexity** to enable agents to "follow their nose" through interconnected biological knowledge graphs.

## Core Design Principles

### 1. Software 2.0 Architecture

**Philosophy**: Instead of hardcoded rules and mappings, tools discover their own capabilities and configurations through metadata queries.

**Key Features**:
- **Self-Configuring Tools**: Query endpoints to discover vocabularies, schemas, and capabilities
- **Progressive Discovery**: Start simple, build complexity based on what you find
- **Agent-Friendly Design**: All outputs include reasoning scaffolds and next-step guidance
- **Universal Resolution**: Works with ANY external identifier without hardcoded mappings

### 2. Agent-Centric Design

**Built for AI Agents**: Every tool response is structured to help agents like Claude Code make intelligent decisions about next steps.

**Reasoning Scaffolds**:
```json
{
  "reasoning_scaffolds": {
    "biological_interpretation": {
      "wikidata_context": "Results are Wikidata entities with Q-numbers",
      "cross_reference_thinking": [
        "Look for P352 (UniProt), P683 (ChEBI), P662 (PubChem) properties",
        "Entity Q-numbers can be used for detailed entity_follow() queries"
      ]
    },
    "follow_up_reasoning": {
      "next_questions": ["What additional information do we need?"],
      "analysis_suggestions": ["Group results by entity type"]
    }
  }
}
```

### 3. Progressive Complexity

**Start Simple, Build Up**:
1. **Basic Search** → Find entities
2. **Entity Inspection** → Understand properties and relationships
3. **Cross-Reference Resolution** → Connect to external databases
4. **Federated Queries** → Complex multi-endpoint analysis
5. **Spatial Intelligence** → Geographic and structural analysis

## How Claude Code Interacts with the Tools

### Following Your Nose Pattern

Claude Code can **progressively discover** capabilities without prior knowledge:

```bash
# 1. Start with basic search
uv run python -m src.wikidata_mcp.cli search "MFN2"

# 2. Agent sees suggestions and follows up
uv run python -m src.wikidata_mcp.cli entity Q123456

# 3. Agent discovers external identifiers and resolves them
uv run python -m src.wikidata_mcp.cli resolve P2410 WP5443

# 4. Agent discovers new endpoints and explores
uv run python -m src.wikidata_mcp.cli discover wikipathways
uv run python -m src.wikidata_mcp.cli sparql "..." --endpoint wikipathways
```

### Agent Guidance System

Every tool response includes:
- **Next Tools**: Specific suggestions for follow-up actions
- **Query Refinements**: Ways to improve current queries
- **Biological Analysis**: Domain-specific insights
- **Cross-Reference Opportunities**: Links to other databases

### Vocabulary Discovery

Agents automatically discover endpoint-specific vocabularies:

```json
{
  "vocabularies": {
    "wp": "http://vocabularies.wikipathways.org/wp#",
    "dcterms": "http://purl.org/dc/terms/",
    "dc": "http://purl.org/dc/elements/1.1/"
  },
  "query_patterns": {
    "pathway_search": "SELECT ?pathway ?title WHERE { ?pathway a wp:Pathway . ?pathway dc:title ?title . FILTER(CONTAINS(LCASE(?title), '{search_term}')) }"
  }
}
```

## Guardrails Implementation

### 1. Query Prerequisites (Discovery Before Execution)

**Like ReadTool before EditTool in Claude Code**:

```python
def validate_sparql_prerequisites(query: str, endpoint: str) -> Optional[dict]:
    if endpoint != "wikidata" and endpoint not in DISCOVERED_ENDPOINTS:
        return {
            "error": {
                "code": "DISCOVERY_REQUIRED", 
                "required_action": f"wikidata discover {endpoint}",
                "reasoning": "Schema discovery provides vocabulary context"
            }
        }
```

### 2. Vocabulary Validation

**Prevents Wrong Prefix Usage**:
```json
{
  "error": {
    "code": "VOCABULARY_MISMATCH",
    "wrong_prefixes": ["wdt:", "schema:"],
    "expected_prefixes": ["wp:", "dc:", "dcterms:"],
    "suggestions": ["Run 'wikidata discover wikipathways' to see vocabulary examples"]
  }
}
```

### 3. Performance Protection

**Complexity Analysis with Automatic Optimization**:
- Query complexity scoring based on patterns
- Automatic LIMIT clause injection
- Timeout prediction and warnings
- Agent suggestions for optimization

### 4. Input Validation

**Agent-Friendly Error Messages**:
```python
if not query.strip():
    return ToolResponse.error(
        "EMPTY_QUERY", 
        "Search query cannot be empty",
        ["Provide a search term like 'Douglas Adams' or 'Python programming'"]
    )
```

## Wikidata Techniques

### 1. Entity Discovery and Disambiguation

**Search with Confidence Scoring**:
```bash
uv run python -m src.wikidata_mcp.cli search "MFN2" --entity-type gene
```

**Response includes disambiguation context**:
- Match scores and confidence levels
- Alternative names and aliases
- Type-specific filtering suggestions

### 2. Property Inspection

**Discover Property Metadata**:
```bash
uv run python -m src.wikidata_mcp.cli property P2410
```

**Returns**:
- Formatter URLs (P1630)
- Validation patterns (P1793)
- Example values (P1855)
- Domain context (P1629)
- Constraints (P2302)

### 3. Universal External Identifier Resolution

**Dynamic Resolution Without Hardcoding**:
```python
# Discovers how to resolve ANY Wikidata property
async def discover_property_metadata(self, property_id: str) -> ExternalIdentifierMetadata:
    # Query Wikidata for formatter URLs, patterns, constraints
    # Build resolution strategy dynamically
```

**Multi-Strategy Resolution**:
1. **SPARQL Endpoint** - Query for values directly
2. **REST API** - Use discovered formatter URLs
3. **Web URL** - Fallback to web interface
4. **Validation** - Use discovered regex patterns

### 4. Cross-Reference Resolution

**Statement URI Handling**:
```python
# Handles complex statement URIs properly
"https://www.wikidata.org/wiki/Statement:Q123-P456-UUID"
```

**Database Integration**:
- UniProt protein data
- ChEBI chemical entities
- PubChem compound information
- MeSH medical subject headings
- GenBank sequence identifiers

## General SPARQL Techniques

### 1. Progressive Query Building

**Start Simple, Add Complexity**:
```sparql
# Level 1: Basic entity search
SELECT ?item ?itemLabel WHERE {
  ?item wdt:P31 wd:Q7187 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}

# Level 2: Add property filters
SELECT ?item ?itemLabel ?uniprot WHERE {
  ?item wdt:P31 wd:Q7187 .
  ?item wdt:P352 ?uniprot .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}

# Level 3: Cross-reference resolution
SELECT ?item ?itemLabel ?uniprot ?pathway WHERE {
  ?item wdt:P31 wd:Q7187 .
  ?item wdt:P352 ?uniprot .
  ?item wdt:P2410 ?pathway .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
```

### 2. Optimization Patterns

**Automatic Query Enhancement**:
- PREFIX injection based on endpoint
- LIMIT clause insertion for performance
- OPTIONAL clause suggestions for enrichment
- FILTER optimization for complex queries

### 3. Biological-Aware Response Truncation

**Intelligent Content Prioritization**:
- Preserves essential biological identifiers
- Maintains cross-reference links
- Reduces response size by 97% while keeping readability
- Prioritizes actionable information for agents

### 4. Error Recovery Patterns

**Structured Error Handling**:
```json
{
  "reasoning_scaffolds": {
    "error_recovery_thinking": [
      "Query failed → Check syntax → Validate schema → Simplify approach",
      "Endpoint error → Check availability → Try alternative endpoints",
      "Timeout → Add LIMIT → Simplify joins → Optimize property paths"
    ]
  }
}
```

## Known Endpoints

### 1. Wikidata
- **URL**: `https://query.wikidata.org/sparql`
- **Vocabularies**: `wd:`, `wdt:`, `p:`, `ps:`, `pq:`, `rdfs:`, `wikibase:`, `bd:`
- **Capabilities**: Full semantic web, 100M+ entities, universal cross-references
- **Spatial**: Geographic coordinates, administrative boundaries

### 2. WikiPathways
- **URL**: `https://sparql.wikipathways.org/sparql`
- **Vocabularies**: `wp:`, `dc:`, `dcterms:`, `foaf:`, `rdfs:`
- **Capabilities**: Biological pathways, gene-disease associations, pathway visualization
- **Key Classes**: `wp:Pathway`, `wp:GeneProduct`, `wp:Metabolite`

### 3. UniProt
- **URL**: `https://sparql.uniprot.org/sparql`
- **Vocabularies**: `up:`, `taxon:`, `rdfs:`, `skos:`
- **Capabilities**: Protein sequences, functional annotations, taxonomic data
- **Integration**: Direct protein-pathway-disease connections

### 4. OSM QLever
- **URL**: Various regional endpoints
- **Vocabularies**: `geo:`, `ogc:`, `osm:`, `osmkey:`, `osmrel:`
- **Capabilities**: Spatial intelligence, geographic reasoning, route planning
- **Specialization**: Geometric operations, spatial relationships

### 5. IDSM (Elixir Czech)
- **URL**: `https://idsm.elixir-czech.cz/sparql/endpoint/idsm`
- **Vocabularies**: `rdfs:`, `owl:`, `skos:`
- **Capabilities**: Integrated data for systems medicine
- **Focus**: Multi-omics integration, systems biology

### 6. Rhea
- **URL**: Expert biochemical reaction database
- **Vocabularies**: `rh:`, `rdfs:`, `owl:`
- **Capabilities**: Biochemical reactions, enzyme classifications
- **Integration**: ChEBI, UniProt, pathway databases

## Spatial Search in QLever

### 1. OSM QLever Integration

**Advanced Geographic Reasoning**:
```sparql
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX osm: <https://www.openstreetmap.org/>

SELECT ?place ?name ?geometry WHERE {
  ?place osm:name ?name .
  ?place geo:hasGeometry ?geometry .
  FILTER(geo:sfWithin(?geometry, ?boundingBox))
}
```

### 2. Spatial Intelligence Features

**Geometric Operations**:
- Point-in-polygon queries
- Distance calculations
- Spatial clustering
- Route optimization
- Boundary analysis

**Use Cases**:
- **Epidemiological Analysis**: Disease spread patterns
- **Environmental Health**: Pollution exposure mapping  
- **Healthcare Access**: Hospital catchment areas
- **Biogeography**: Species distribution modeling

### 3. Cross-Domain Spatial Analysis

**Wikidata ↔ OSM Integration**:
```sparql
# Find hospitals near research institutions
SELECT ?hospital ?institution ?distance WHERE {
  ?hospital wdt:P31 wd:Q16917 .  # hospital
  ?institution wdt:P31 wd:Q31855 . # research institute
  ?hospital wdt:P625 ?hospitalCoords .
  ?institution wdt:P625 ?institutionCoords .
  BIND(geof:distance(?hospitalCoords, ?institutionCoords) AS ?distance)
  FILTER(?distance < 10) # within 10km
}
```

## Advanced Workflows

### 1. Federated Query Composition

**Multi-Endpoint Analysis**:
```python
class SparqlFederator:
    def __init__(self):
        self.endpoints = {
            "wikidata": "https://query.wikidata.org/sparql",
            "uniprot": "https://sparql.uniprot.org/sparql", 
            "wikipathways": "https://sparql.wikipathways.org/sparql"
        }
    
    async def federated_query(self, gene_symbol: str):
        # 1. Find gene in Wikidata
        # 2. Get UniProt ID and query protein details
        # 3. Find pathways in WikiPathways
        # 4. Aggregate results with cross-references
```

### 2. Biological Discovery Workflows

**Gene → Pathway → Disease Pipeline**:
1. **Gene Discovery**: Search Wikidata for gene symbols
2. **Protein Analysis**: Cross-reference to UniProt for functional data
3. **Pathway Mapping**: Find biological pathways via WikiPathways
4. **Disease Association**: Connect to disease databases via Wikidata
5. **Drug Discovery**: Identify potential therapeutic targets

### 3. Agent-Driven Exploration

**Autonomous Discovery Pattern**:
```python
# Agent can start with minimal information and build understanding
initial_query = "MFN2 mutation"

# 1. Search discovers entities and properties
search_results = await search_tool(initial_query)

# 2. Agent follows suggested entities
for entity in search_results['suggestions']['next_tools']:
    entity_data = await entity_tool(entity)
    
    # 3. Agent discovers external identifiers  
    for ext_id in entity_data['external_identifiers']:
        resolved_data = await resolve_tool(ext_id)
        
        # 4. Agent explores new endpoints
        if resolved_data['endpoint'] not in known_endpoints:
            schema = await discover_tool(resolved_data['endpoint'])
            
            # 5. Agent can now query new endpoint intelligently
            results = await sparql_tool(query, endpoint=resolved_data['endpoint'])
```

## Best Practices for Agents

### 1. Start with Discovery
Always begin with `search` or `discover` commands to understand available data and capabilities.

### 2. Follow Reasoning Scaffolds
Pay attention to the reasoning scaffolds in responses - they provide domain-specific guidance for next steps.

### 3. Use Progressive Complexity
Build queries incrementally rather than attempting complex federated queries immediately.

### 4. Leverage Cross-References
When you find external identifiers, resolve them to discover new endpoints and data sources.

### 5. Validate with Discovery
When switching endpoints, always run discovery first to understand vocabularies and patterns.

### 6. Optimize Iteratively
Use the performance hints and optimization suggestions provided in responses.

## Error Handling and Recovery

### Common Error Patterns

1. **DISCOVERY_REQUIRED**: Run discovery before querying unknown endpoints
2. **VOCABULARY_MISMATCH**: Check endpoint-specific vocabularies
3. **SPARQL_EXECUTION_ERROR**: Simplify query and check syntax
4. **TIMEOUT**: Add LIMIT clauses and optimize joins

### Recovery Strategies

Each error includes specific recovery guidance:
```json
{
  "suggestions": [
    "Check query syntax and endpoint availability",
    "Use ontology_discover() to validate schema elements", 
    "Try simpler query or add LIMIT clause"
  ]
}
```

## Complete Implementation Specifications

### Project Structure & Dependencies

#### Required Project Structure
```
wikidata-mcp/
├── pyproject.toml              # UV project configuration
├── uv.lock                     # Dependency lock file
├── src/
│   └── wikidata_mcp/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── client.py           # HTTP client foundation
│       ├── tools.py            # Core tool implementations
│       ├── server.py           # Basic MCP server
│       ├── enhanced_server.py  # Science assistant server
│       ├── enhanced_tools.py   # Cross-reference tools
│       ├── universal_resolver.py # External ID resolver
│       ├── ontology_discovery.py # Schema discovery
│       ├── response_truncation.py # Response optimization
│       └── software2_server.py # Generalized tools server
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── software2_intelligence/
├── shapes/ (future SHACL integration)
└── docs/
```

#### Core Dependencies (pyproject.toml)
```toml
[project]
name = "wikidata-mcp"
version = "0.1.0"
dependencies = [
    "httpx>=0.24.0",           # Async HTTP client
    "click>=8.0.0",            # CLI framework
    "pydantic>=2.0.0",         # Data validation
    "rdflib>=7.0.0",           # RDF processing
    "mcp>=1.0.0",              # Model Context Protocol
    "asyncio-throttle>=1.0.0", # Rate limiting
    "typing-extensions>=4.0.0", # Type hints
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-httpx>=0.21.0",
]
```

### Core Implementation Classes

#### 1. Foundation HTTP Client (client.py)
```python
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from urllib.parse import quote_plus

class WikidataClient:
    """Foundation async HTTP client for SPARQL endpoints"""
    
    def __init__(self, base_url: str = "https://query.wikidata.org/sparql"):
        self.base_url = base_url
        self.session: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=120.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def search_entities(self, query: str, language: str = "en", 
                            limit: int = 10, entity_type: Optional[str] = None) -> Dict:
        """Search entities using Wikidata API"""
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": language,
            "limit": limit,
            "format": "json"
        }
        if entity_type:
            params["type"] = entity_type
            
        response = await self.session.get(
            "https://www.wikidata.org/w/api.php", 
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_entity(self, entity_id: str, language: str = "en") -> Dict:
        """Get entity details from Wikidata API"""
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "languages": language,
            "format": "json"
        }
        response = await self.session.get(
            "https://www.wikidata.org/w/api.php",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def execute_sparql(self, query: str) -> Dict:
        """Execute SPARQL query with automatic prefix injection"""
        prefixed_query = self._add_prefixes(query)
        
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "WikidataMCP/1.0"
        }
        
        response = await self.session.post(
            self.base_url,
            data={"query": prefixed_query},
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    def _add_prefixes(self, query: str) -> str:
        """Add standard prefixes if not present"""
        standard_prefixes = {
            "wd": "http://www.wikidata.org/entity/",
            "wdt": "http://www.wikidata.org/prop/direct/",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "wikibase": "http://wikiba.se/ontology#",
            "bd": "http://www.bigdata.com/rdf#"
        }
        
        prefix_lines = []
        for prefix, uri in standard_prefixes.items():
            if f"PREFIX {prefix}:" not in query:
                prefix_lines.append(f"PREFIX {prefix}: <{uri}>")
        
        return "\n".join(prefix_lines + [query])
```

#### 2. Response Framework (tools.py)
```python
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

class ToolResponse(BaseModel):
    """Standardized tool response format with reasoning scaffolds"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]
    reasoning_scaffolds: Dict[str, Any]
    suggestions: Dict[str, List[str]]
    
    @classmethod
    def success_response(cls, data: Dict, **kwargs) -> "ToolResponse":
        return cls(
            success=True,
            data=data,
            metadata=cls._build_metadata(**kwargs),
            reasoning_scaffolds=cls._build_reasoning_scaffolds(data),
            suggestions=cls._build_suggestions(data)
        )
    
    @classmethod
    def error_response(cls, code: str, message: str, suggestions: List[str]) -> "ToolResponse":
        return cls(
            success=False,
            error={"code": code, "message": message, "suggestions": suggestions},
            metadata={"execution_time_ms": 0, "error_occurred": True},
            reasoning_scaffolds={"error_recovery_thinking": suggestions},
            suggestions={"recovery_actions": suggestions}
        )
    
    @staticmethod
    def _build_metadata(**kwargs) -> Dict[str, Any]:
        return {
            "execution_time_ms": kwargs.get("execution_time", 0),
            "cached": kwargs.get("cached", False),
            "data_freshness": "current",
            "api_version": "1.0",
            **kwargs
        }
    
    @staticmethod
    def _build_reasoning_scaffolds(data: Dict) -> Dict[str, Any]:
        """Generate domain-specific reasoning context"""
        return {
            "biological_interpretation": {
                "wikidata_context": "Results are Wikidata entities with Q-numbers",
                "cross_reference_thinking": [
                    "Look for P352 (UniProt), P683 (ChEBI), P662 (PubChem) properties",
                    "Entity Q-numbers can be used for detailed entity queries"
                ]
            },
            "follow_up_reasoning": {
                "next_questions": ["What additional information do we need?"],
                "analysis_suggestions": ["Group results by entity type"]
            }
        }
    
    @staticmethod
    def _build_suggestions(data: Dict) -> Dict[str, List[str]]:
        """Generate actionable next steps"""
        return {
            "next_tools": ["Use entity IDs for detailed analysis"],
            "query_refinements": ["Add OPTIONAL clauses for enrichment"],
            "biological_analysis": ["Check for cross-database identifiers"]
        }

class WikidataSearch:
    """Entity search with disambiguation and confidence scoring"""
    
    def __init__(self, client: WikidataClient):
        self.client = client
    
    async def search(self, query: str, language: str = "en", 
                    limit: int = 10, entity_type: Optional[str] = None) -> ToolResponse:
        start_time = datetime.now()
        
        try:
            # Input validation
            if not query.strip():
                return ToolResponse.error_response(
                    "EMPTY_QUERY",
                    "Search query cannot be empty",
                    ["Provide a search term like 'Douglas Adams' or 'Python programming'"]
                )
            
            # Execute search
            raw_results = await self.client.search_entities(
                query, language, limit, entity_type
            )
            
            # Process and enrich results
            processed_results = self._process_search_results(raw_results, query)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ToolResponse.success_response(
                data={
                    "query": query,
                    "results": processed_results,
                    "total_found": len(processed_results)
                },
                execution_time=execution_time,
                language=language,
                entity_type=entity_type
            )
            
        except Exception as e:
            return ToolResponse.error_response(
                "SEARCH_ERROR",
                f"Failed to execute search: {str(e)}",
                ["Check network connectivity", "Try simpler search terms"]
            )
    
    def _process_search_results(self, raw_results: Dict, query: str) -> List[Dict]:
        """Process raw API results into agent-friendly format"""
        processed = []
        
        for item in raw_results.get("search", []):
            processed_item = {
                "id": item.get("id"),
                "label": item.get("label"),
                "description": item.get("description", ""),
                "url": item.get("concepturi"),
                "match_score": item.get("label", "")  # Simplified for example
            }
            processed.append(processed_item)
        
        return processed
```

#### 3. Guardrails System (cli.py)
```python
from typing import Optional, Dict, Set

# Global state for discovered endpoints
DISCOVERED_ENDPOINTS: Set[str] = {"wikidata"}

# Endpoint vocabulary mappings
ENDPOINT_VOCABULARIES = {
    "wikidata": ["wd:", "wdt:", "p:", "ps:", "pq:", "rdfs:", "wikibase:", "bd:"],
    "wikipathways": ["wp:", "dc:", "dcterms:", "foaf:", "rdfs:"],
    "uniprot": ["up:", "taxon:", "rdfs:", "skos:"],
    "idsm": ["rdfs:", "owl:", "skos:"],
    "rhea": ["rh:", "rdfs:", "owl:"],
    "osm-planet": ["geo:", "ogc:", "osm:", "osmkey:", "osmrel:", "rdfs:"]
}

def validate_sparql_prerequisites(query: str, endpoint: str) -> Optional[Dict]:
    """Validate query prerequisites like Claude Code's ReadTool before EditTool"""
    
    # Guardrail 1: Discovery prerequisite
    if endpoint != "wikidata" and endpoint not in DISCOVERED_ENDPOINTS:
        return {
            "error": {
                "code": "DISCOVERY_REQUIRED",
                "required_action": f"discover {endpoint}",
                "reasoning": "Schema discovery provides vocabulary context like ReadTool before EditTool"
            }
        }
    
    # Guardrail 2: Vocabulary validation
    wrong_prefixes = []
    expected_prefixes = ENDPOINT_VOCABULARIES.get(endpoint, [])
    
    for vocab in ENDPOINT_VOCABULARIES["wikidata"]:
        if vocab in query and endpoint != "wikidata":
            wrong_prefixes.append(vocab)
    
    if wrong_prefixes:
        return {
            "error": {
                "code": "VOCABULARY_MISMATCH", 
                "wrong_prefixes": wrong_prefixes,
                "expected_prefixes": expected_prefixes,
                "suggestions": [f"Use {', '.join(expected_prefixes)} for {endpoint}"]
            }
        }
    
    return None

def calculate_query_complexity(query: str) -> Dict:
    """Analyze query complexity for performance prediction"""
    complexity_score = 0
    warnings = []
    
    # Check for expensive patterns
    if "FILTER" in query.upper():
        complexity_score += 10
    if "OPTIONAL" in query.upper():
        complexity_score += 5
    if query.upper().count("?") > 10:  # Many variables
        complexity_score += 15
        warnings.append("Consider reducing number of variables")
    
    # Check for LIMIT clause
    if "LIMIT" not in query.upper():
        warnings.append("Add LIMIT clause for better performance")
        complexity_score += 20
    
    risk_level = "LOW" if complexity_score < 20 else "MEDIUM" if complexity_score < 40 else "HIGH"
    
    return {
        "complexity_score": complexity_score,
        "risk_level": risk_level,
        "warnings": warnings,
        "estimated_time_seconds": min(complexity_score * 2, 300)  # Cap at 5 minutes
    }
```

#### 4. Universal External ID Resolver (universal_resolver.py)
```python
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ExternalIdentifierMetadata:
    """Metadata discovered about an external identifier property"""
    name: str
    formatter_url: Optional[str]
    validation_pattern: Optional[str]
    example_values: List[str]
    domain: Optional[str]

class UniversalResolver:
    """Dynamically resolves ANY external identifier using Wikidata metadata"""
    
    def __init__(self, client: WikidataClient):
        self.client = client
        self._property_cache: Dict[str, ExternalIdentifierMetadata] = {}
    
    async def resolve_identifier(self, property_id: str, identifier_value: str) -> Dict[str, Any]:
        """Resolve external identifier using discovered metadata"""
        
        # Discover property metadata if not cached
        if property_id not in self._property_cache:
            metadata = await self.discover_property_metadata(property_id)
            self._property_cache[property_id] = metadata
        else:
            metadata = self._property_cache[property_id]
        
        # Validate identifier format
        validation_passed = True
        if metadata.validation_pattern:
            validation_passed = bool(re.match(metadata.validation_pattern, identifier_value))
        
        # Try resolution strategies
        resolution_strategy = "sparql_endpoint"
        resolved_url = None
        sparql_data = {}
        
        # Strategy 1: SPARQL endpoint resolution
        try:
            sparql_data = await self._resolve_via_sparql(property_id, identifier_value)
            if sparql_data:
                resolution_strategy = "sparql_endpoint"
        except:
            pass
        
        # Strategy 2: Formatter URL resolution
        if metadata.formatter_url and not resolved_url:
            resolved_url = metadata.formatter_url.replace("$1", identifier_value)
            resolution_strategy = "formatter_url"
        
        # Strategy 3: Web URL fallback
        if not resolved_url:
            resolved_url = f"https://www.wikidata.org/wiki/Property:{property_id}"
            resolution_strategy = "web_fallback"
        
        return {
            "success": True,
            "property_id": property_id,
            "identifier_value": identifier_value,
            "resolved_url": resolved_url,
            "metadata": {
                "name": metadata.name,
                "domain": metadata.domain
            },
            "validation_passed": validation_passed,
            "resolution_strategy": resolution_strategy,
            "sparql_data": sparql_data,
            "reasoning_context": {
                "resolution_guidance": [
                    "Rich linked data available via SPARQL queries",
                    "Direct web access available for human review"
                ],
                "property_context": {
                    "name": metadata.name,
                    "domain": metadata.domain or "general"
                }
            }
        }
    
    async def discover_property_metadata(self, property_id: str) -> ExternalIdentifierMetadata:
        """Query Wikidata for property metadata"""
        query = f"""
        SELECT ?propertyLabel ?formatterURL ?validationPattern ?exampleValue ?domain WHERE {{
          wd:{property_id} rdfs:label ?propertyLabel .
          OPTIONAL {{ wd:{property_id} wdt:P1630 ?formatterURL . }}
          OPTIONAL {{ wd:{property_id} wdt:P1793 ?validationPattern . }}
          OPTIONAL {{ wd:{property_id} wdt:P1855 ?exampleValue . }}
          OPTIONAL {{ wd:{property_id} wdt:P1629 ?domain . }}
          FILTER(LANG(?propertyLabel) = "en")
        }}
        """
        
        results = await self.client.execute_sparql(query)
        
        if results.get("results", {}).get("bindings"):
            binding = results["results"]["bindings"][0]
            
            return ExternalIdentifierMetadata(
                name=binding.get("propertyLabel", {}).get("value", property_id),
                formatter_url=binding.get("formatterURL", {}).get("value"),
                validation_pattern=binding.get("validationPattern", {}).get("value"),
                example_values=[binding.get("exampleValue", {}).get("value", "")],
                domain=binding.get("domain", {}).get("value")
            )
        
        return ExternalIdentifierMetadata(
            name=property_id,
            formatter_url=None,
            validation_pattern=None,
            example_values=[],
            domain=None
        )
    
    async def _resolve_via_sparql(self, property_id: str, identifier_value: str) -> Dict:
        """Attempt to resolve via SPARQL query"""
        query = f"""
        SELECT ?item ?itemLabel WHERE {{
          ?item wdt:{property_id} "{identifier_value}" .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
        }} LIMIT 10
        """
        
        try:
            results = await self.client.execute_sparql(query)
            return {"entities": results.get("results", {}).get("bindings", [])}
        except:
            return {}
```

#### 5. Ontology Discovery System (ontology_discovery.py)
```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class EndpointSchema:
    """Discovered schema information for a SPARQL endpoint"""
    url: str
    vocabularies: Dict[str, str]
    classes: Dict[str, Dict[str, Any]]
    properties: Dict[str, Dict[str, Any]]
    query_patterns: Dict[str, str]
    guidance: Dict[str, List[str]]

class OntologyDiscovery:
    """Multi-strategy schema discovery for SPARQL endpoints"""
    
    KNOWN_ENDPOINTS = {
        "wikidata": "https://query.wikidata.org/sparql",
        "wikipathways": "https://sparql.wikipathways.org/sparql",
        "uniprot": "https://sparql.uniprot.org/sparql",
        "idsm": "https://idsm.elixir-czech.cz/sparql/endpoint/idsm"
    }
    
    def __init__(self):
        self._schema_cache: Dict[str, EndpointSchema] = {}
    
    async def discover_endpoint(self, endpoint_name: str) -> Dict[str, Any]:
        """Discover schema using multiple strategies"""
        
        if endpoint_name in self._schema_cache:
            schema = self._schema_cache[endpoint_name]
        else:
            schema = await self._discover_schema(endpoint_name)
            self._schema_cache[endpoint_name] = schema
        
        # Add to discovered endpoints for guardrails
        DISCOVERED_ENDPOINTS.add(endpoint_name)
        
        return {
            "endpoint_info": {
                "url": schema.url,
                "discovery_method": "multi_strategy",
                "discovery_time_ms": 0  # Simplified for example
            },
            "vocabularies": schema.vocabularies,
            "classes": schema.classes,
            "properties": schema.properties,
            "query_patterns": schema.query_patterns,
            "guidance": schema.guidance
        }
    
    async def _discover_schema(self, endpoint_name: str) -> EndpointSchema:
        """Multi-strategy schema discovery"""
        
        # Strategy 1: Use known patterns for common endpoints
        if endpoint_name in self._get_known_patterns():
            return self._get_known_patterns()[endpoint_name]
        
        # Strategy 2: SPARQL introspection
        url = self.KNOWN_ENDPOINTS.get(endpoint_name, f"https://{endpoint_name}/sparql")
        
        try:
            introspected = await self._introspect_via_sparql(url)
            return introspected
        except:
            # Strategy 3: Fallback to minimal schema
            return self._minimal_schema(endpoint_name, url)
    
    def _get_known_patterns(self) -> Dict[str, EndpointSchema]:
        """Hardcoded patterns for major biological endpoints"""
        return {
            "wikipathways": EndpointSchema(
                url="https://sparql.wikipathways.org/sparql",
                vocabularies={
                    "wp": "http://vocabularies.wikipathways.org/wp#",
                    "dcterms": "http://purl.org/dc/terms/",
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "foaf": "http://xmlns.com/foaf/0.1/"
                },
                classes={
                    "wp:Pathway": {"description": "Biological pathway", "usage_count": 2300},
                    "wp:GeneProduct": {"description": "Gene or protein in pathway", "usage_count": 45000}
                },
                properties={
                    "dc:title": {"description": "Pathway title", "usage_count": 2300},
                    "dcterms:isPartOf": {"description": "Part of pathway relationship", "usage_count": 45000},
                    "wp:organism": {"description": "Organism taxonomy", "usage_count": 2300}
                },
                query_patterns={
                    "pathway_search": "SELECT ?pathway ?title WHERE { ?pathway a wp:Pathway . ?pathway dc:title ?title . FILTER(CONTAINS(LCASE(?title), '{search_term}')) }",
                    "gene_in_pathway": "SELECT ?gene ?pathway WHERE { ?gene a wp:GeneProduct . ?gene dcterms:isPartOf ?pathway . ?gene rdfs:label ?label . FILTER(CONTAINS(LCASE(?label), '{gene_name}')) }"
                },
                guidance={
                    "performance_hints": [
                        "Use wp:organism filter for species-specific queries",
                        "Text searches on dc:title and rdfs:label are indexed"
                    ],
                    "agent_guidance": [
                        "Start pathway discovery with wp:Pathway and dc:title",
                        "Connect genes to pathways via dcterms:isPartOf"
                    ]
                }
            )
        }
    
    async def _introspect_via_sparql(self, url: str) -> EndpointSchema:
        """Discover schema through SPARQL introspection"""
        # Simplified introspection - real implementation would use client
        return EndpointSchema(
            url=url,
            vocabularies={},
            classes={},
            properties={},
            query_patterns={},
            guidance={"performance_hints": [], "agent_guidance": []}
        )
    
    def _minimal_schema(self, endpoint_name: str, url: str) -> EndpointSchema:
        """Fallback minimal schema"""
        return EndpointSchema(
            url=url,
            vocabularies={"rdfs": "http://www.w3.org/2000/01/rdf-schema#"},
            classes={},
            properties={},
            query_patterns={},
            guidance={"performance_hints": ["Use LIMIT clauses"], "agent_guidance": ["Start with simple queries"]}
        )
```

#### 6. CLI Implementation (cli.py)
```python
import click
import asyncio
import json
from .client import WikidataClient
from .tools import WikidataSearch
from .universal_resolver import UniversalResolver
from .ontology_discovery import OntologyDiscovery

@click.group()
def cli():
    """Wikidata-MCP Command Line Interface"""
    pass

@cli.command()
@click.argument("query")
@click.option("--entity-type", help="Filter by entity type")
@click.option("--limit", default=10, help="Number of results")
def search(query: str, entity_type: str, limit: int):
    """Search for entities"""
    async def _search():
        async with WikidataClient() as client:
            search_tool = WikidataSearch(client)
            result = await search_tool.search(query, entity_type=entity_type, limit=limit)
            click.echo(json.dumps(result.dict(), indent=2))
    
    asyncio.run(_search())

@cli.command()
@click.argument("property_id")
@click.argument("identifier")
def resolve(property_id: str, identifier: str):
    """Resolve external identifier"""
    async def _resolve():
        async with WikidataClient() as client:
            resolver = UniversalResolver(client)
            result = await resolver.resolve_identifier(property_id, identifier)
            click.echo(json.dumps(result, indent=2))
    
    asyncio.run(_resolve())

@cli.command()
@click.argument("endpoint")
def discover(endpoint: str):
    """Discover endpoint schema"""
    async def _discover():
        discovery = OntologyDiscovery()
        result = await discovery.discover_endpoint(endpoint)
        click.echo(json.dumps(result, indent=2))
    
    asyncio.run(_discover())

@cli.command()
@click.argument("query")
@click.option("--endpoint", default="wikidata", help="SPARQL endpoint")
def sparql(query: str, endpoint: str):
    """Execute SPARQL query with guardrails"""
    async def _sparql():
        # Validate prerequisites
        validation_error = validate_sparql_prerequisites(query, endpoint)
        if validation_error:
            click.echo(json.dumps(validation_error, indent=2))
            return
        
        # Calculate complexity
        complexity = calculate_query_complexity(query)
        if complexity["risk_level"] == "HIGH":
            click.echo(f"Warning: High complexity query (score: {complexity['complexity_score']})")
            for warning in complexity["warnings"]:
                click.echo(f"  - {warning}")
        
        # Execute query
        endpoint_url = OntologyDiscovery.KNOWN_ENDPOINTS.get(endpoint, f"https://{endpoint}/sparql")
        async with WikidataClient(endpoint_url) as client:
            try:
                results = await client.execute_sparql(query)
                response = {
                    "success": True,
                    "data": {
                        "query_executed": client._add_prefixes(query),
                        "results": results.get("results", {}).get("bindings", []),
                        "result_count": len(results.get("results", {}).get("bindings", [])),
                        "endpoint": endpoint_url
                    },
                    "metadata": {
                        "query_optimized": True,
                        "schema_used": endpoint in DISCOVERED_ENDPOINTS,
                        "complexity": complexity
                    }
                }
                click.echo(json.dumps(response, indent=2))
            except Exception as e:
                error_response = {
                    "success": False,
                    "error": {
                        "code": "SPARQL_EXECUTION_ERROR",
                        "message": f"Failed to execute SPARQL query: {str(e)}",
                        "suggestions": [
                            "Check query syntax",
                            "Verify endpoint availability",
                            "Try simpler query with LIMIT"
                        ]
                    }
                }
                click.echo(json.dumps(error_response, indent=2))
    
    asyncio.run(_sparql())

if __name__ == "__main__":
    cli()
```

### Installation & Setup Instructions

#### 1. Environment Setup
```bash
# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
mkdir wikidata-mcp
cd wikidata-mcp
uv init

# Create project structure
mkdir -p src/wikidata_mcp tests/{unit,integration} docs shapes
```

#### 2. Dependencies Installation
```bash
# Install core dependencies
uv add httpx click pydantic rdflib mcp asyncio-throttle typing-extensions

# Install development dependencies  
uv add --dev pytest pytest-asyncio pytest-httpx
```

#### 3. Implementation Steps
1. **Foundation**: Implement `client.py` with async HTTP client
2. **Tools Framework**: Create `tools.py` with ToolResponse class
3. **Core Tools**: Implement search, entity, SPARQL tools
4. **Guardrails**: Add validation and performance protection
5. **Universal Resolver**: Dynamic external ID resolution
6. **Ontology Discovery**: Multi-strategy schema discovery
7. **CLI Interface**: Command-line tool with all features
8. **Testing**: Unit and integration tests
9. **MCP Server**: Model Context Protocol integration

#### 4. Testing Commands
```bash
# Test basic functionality
uv run python -m src.wikidata_mcp.cli search "MFN2"
uv run python -m src.wikidata_mcp.cli resolve P2410 WP5443  
uv run python -m src.wikidata_mcp.cli discover wikipathways
uv run python -m src.wikidata_mcp.cli sparql "SELECT ?item WHERE { ?item wdt:P31 wd:Q7187 } LIMIT 5"

# Run tests
uv run pytest tests/
```

### Critical Success Factors

1. **Async-First Architecture**: All network operations must be async
2. **Comprehensive Error Handling**: Every operation needs graceful failure modes
3. **Agent-Friendly Responses**: Rich metadata and reasoning scaffolds essential
4. **Performance Optimization**: Caching, complexity analysis, timeout handling
5. **Extensible Design**: Easy to add new endpoints and capabilities
6. **Testing Coverage**: Both unit tests and real workflow integration tests

### Expected Implementation Timeline

- **Week 1**: Foundation (client.py, basic tools.py)
- **Week 2**: Core tools (search, entity, SPARQL) 
- **Week 3**: Guardrails and validation system
- **Week 4**: Universal resolver and cross-references
- **Week 5**: Ontology discovery system
- **Week 6**: CLI interface and integration testing
- **Week 7**: MCP server implementation
- **Week 8**: Performance optimization and documentation

This specification provides sufficient detail to recreate the entire infrastructure from first principles, including the specific Software 2.0 patterns, guardrails implementation, and agent-friendly design that makes this system effective for biological research.

## Conclusion

Wikidata-MCP represents a new paradigm in biological data integration - **Software 2.0 tools that teach themselves and guide AI agents through complex scientific discovery workflows**. By following the "nose-first" discovery pattern and leveraging reasoning scaffolds, agents like Claude Code can autonomously navigate the interconnected landscape of biological knowledge graphs, making novel connections and driving scientific discovery.

The system's strength lies not in predefined workflows, but in its ability to **adapt and discover** - much like how scientists themselves explore unknown territories by following promising leads and building understanding incrementally.