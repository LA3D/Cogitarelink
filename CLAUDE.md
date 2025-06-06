# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the unified CogitareLink repository.

## Project Overview

**CogitareLink: Living Scientific Assistant**

A semantic web-powered scientific research assistant that combines rigorous knowledge management with intelligent discovery and continuous learning from agent interactions. CogitareLink ("to think connectedly") synthesizes:

- **Semantic Rigor**: Immutable JSON-LD entities, SHACL reasoning, cryptographic verification
- **Agent Intelligence**: Discovery-first guardrails, structured responses, Chain-of-Thought scaffolds
- **Software 2.0**: Generalized tools + intelligent prompting rather than hardcoded logic

### Core Philosophy

- **Hybrid CLI + Agentic**: CLI-first composable tools with rich structured responses for agent intelligence
- **Semantic Memory**: All discovered knowledge stored as immutable entities with full provenance tracking
- **Discovery-First Guardrails**: Never query without schema understanding (like Read-before-Edit in Claude Code)
- **In-Context Teaching**: Continuously learn and improve from actual agent usage patterns
- **Verifiable Science**: Every conclusion traceable to sources with cryptographic verification
- **Framework Agnostic**: Works with Claude Code, DSPy, LangGraph, or any agent framework

## Architecture Overview

```
cogitarelink/
├── core/                           # Semantic memory micro-kernel (~1500 LOC)
│   ├── entity.py                  # Immutable JSON-LD entities with SHA-256 signatures
│   ├── graph.py                   # Multi-backend RDF storage with named graphs
│   ├── context.py                 # Full JSON-LD 1.1 processor
│   ├── cache.py                   # Multi-layer caching (memory LRU + disk + TTL)
│   └── processor.py               # Entity processing pipeline with normalization
│
├── vocab/                          # Advanced vocabulary management
│   ├── registry.py                # Dynamic vocab registry with versioning
│   ├── composer.py                # Context composition with JSON-LD 1.1 features
│   └── collision.py               # Multi-strategy conflict resolution
│
├── reason/                         # SHACL-unified reasoning engine
│   ├── shacl_engine.py           # Universal SHACL SPARQL rules
│   ├── prov.py                    # W3C PROV-O provenance wrapper
│   └── obqc.py                    # Ontology-based query checking
│
├── intelligence/                   # Agent intelligence layer
│   ├── discovery_engine.py       # Multi-method endpoint discovery
│   ├── complexity_analyzer.py    # Query complexity analysis
│   ├── guidance_generator.py     # Domain-specific CoT patterns
│   └── universal_resolver.py     # Self-configuring identifier resolution
│
├── memory/                         # Semantic memory with introspection
│   ├── semantic_cache.py          # Queryable semantic memory
│   └── state_manager.py          # Discovery state tracking
│
├── cli/                            # CLI tools with structured intelligence
│   ├── discover.py                # cl_discover - Scientific resource discovery
│   ├── sparql.py                  # cl_sparql - Guardrail-protected queries
│   ├── materialize.py             # cl_materialize - Knowledge materialization
│   └── explain.py                 # cl_explain - Reasoning chain explanation
│
└── adapters/                       # Framework-agnostic integration
    ├── claude_code.py             # Claude Code tool registration
    └── universal_cli.py           # Direct CLI access
```

## Development Approach - Fast.ai Style Implementation

### Philosophy: Jeremy Howard's Incremental, Tested Development

Following Jeremy Howard's fast.ai approach for building AI-friendly tools with immediate feedback loops:

#### 1. **Step-by-Step Foundation Building**
- Start with the simplest possible working component
- Build each layer on proven foundations
- Test immediately at every step
- Refactor when patterns emerge

#### 2. **Test-as-You-Go Development**
```python
# Every function includes immediate testing
def normalize_entity(entity: Entity) -> str:
    """URDNA2015 normalization with immediate validation"""
    result = _proc.normalize(entity.as_json)
    # Immediate test
    assert len(result) > 0, "Normalization failed"
    return result
```

#### 3. **Incremental Tool Development Order**
1. **Core Infrastructure** - Entity, Graph, Context (foundation)
2. **Simple Tools** - Basic discovery and validation
3. **Agent Intelligence** - Structured responses and CoT patterns
4. **Complex Workflows** - Multi-step research orchestration

#### 4. **Agent-Friendly Design from Start**
- Structured JSON responses with metadata and suggestions
- Helpful error messages with recovery strategies
- Rich context for follow-up actions
- Comprehensive input validation

### Development Structure

```
tests/
├── test_core.py           # Foundation tests - run first
├── test_vocab.py          # Vocabulary management tests
├── test_intelligence.py   # Agent intelligence tests
└── test_workflows.py      # End-to-end workflow tests
```

### Key Development Principles

1. **Foundation First**: Solid core components make everything else easier
2. **Test Immediately**: Catch issues early, build confidence at each step
3. **Incremental Complexity**: Simple → useful → powerful
4. **Agent Patterns**: Claude Code analysis guides design decisions
5. **Real Workflow Testing**: End-to-end tests confirm integration

## Agent-Friendly Tool Design Patterns

Based on analysis of Claude Code's tool architecture, CogitareLink implements patterns that make tools effective for AI agents:

### 1. **Structured Response Architecture**

All CLI tools return rich JSON responses with agent guidance:

```json
{
    "success": true,
    "data": {...},
    "metadata": {
        "execution_time_ms": 1250,
        "materialized_triples": 156,
        "complexity_score": 3.2
    },
    "suggestions": {
        "next_tools": ["cl_sparql --endpoint discovered"],
        "reasoning_patterns": ["🧬 PROTEIN → PATHWAY → DISEASE"],
        "workflow_steps": ["1. Extract cross-references", "2. Follow to databases"]
    },
    "claude_guidance": {
        "domain_context": ["Biological research patterns discovered"],
        "optimization_hints": ["Query complexity acceptable"],
        "potential_issues": ["Check temporal coverage"]
    }
}
```

### 2. **Discovery-First Guardrails**

Like Claude Code's "Read-before-Edit" pattern, CogitareLink enforces "Discover-before-Query":

```python
# SPARQL queries require prior schema discovery
if not state_manager.is_discovered(endpoint):
    return {
        "success": False,
        "error": {
            "code": "DISCOVERY_REQUIRED",
            "required_action": f"cl_discover --endpoint {endpoint}",
            "reasoning": "Schema discovery prevents vocabulary errors"
        }
    }
```

### 3. **Chain-of-Thought (CoT) Reasoning Scaffolds**

Tools provide reasoning context rather than hardcoded solutions:

```python
# Instead of hardcoded drug_discovery() tool:
guidance = {
    "reasoning_patterns": [
        "Disease → Associated Pathways → Pathway Proteins → Drug Targets",
        "Protein Structure → Binding Sites → Compound Libraries → Candidates"
    ],
    "biological_workflow": [
        "1. Identify disease pathways using SPARQL",
        "2. Extract pathway proteins via cross-references", 
        "3. Analyze protein structures in UniProt",
        "4. Search compound databases for binding candidates"
    ]
}
```

### 4. **Software 2.0: Generalized Tools + Intelligent Prompting**

Following Claude Code's success pattern:
- **Few, powerful tools** that compose infinitely (like ripgrep)
- **Rich prompting context** that enables agent reasoning
- **Domain expertise** encoded as reasoning scaffolds, not hardcoded logic

## Build/Test Commands

### Environment Setup
```bash
# Create environment with uv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install development dependencies
uv pip install -e ".[dev]"
```

### Development Workflow
```bash
# Run all tests with immediate feedback
pytest -v

# Run specific test module
pytest tests/test_core.py -v

# Run single test function
pytest tests/test_entity.py::test_immutable_entity -v

# Format code (Black, 88 columns)
black cogitarelink/ tests/

# Type checking
mypy cogitarelink/

# CLI tool testing
cl_discover "SARS-CoV-2 spike protein" --domains biology
cl_sparql "SELECT ?protein WHERE { ?protein wdt:P31 wd:Q8054 }"
```

### Testing Strategy
```python
# Use fastcore test patterns for immediate feedback
from fastcore.test import test_eq, test_fail

def test_entity_immutability():
    """Test that entities are truly immutable"""
    entity = Entity(vocab=["bioschemas"], content={"name": "insulin"})
    
    # Test immutability
    test_eq(entity.content["name"], "insulin")
    
    # Test SHA-256 signature consistency  
    sig1 = entity.sha256
    sig2 = entity.sha256
    test_eq(sig1, sig2)
    
    # Test that modification creates new entity
    with test_fail():
        entity.content["name"] = "modified"  # Should fail
```

## Code Style Guidelines

### Core Principles
- **Format**: Black (88 columns) with immediate formatting on save
- **Types**: Use type hints everywhere with `from __future__ import annotations`
- **Testing**: Include at least one test per public function using fastcore patterns
- **Error Handling**: Graceful degradation with structured error responses
- **Documentation**: Rich docstrings with agent-friendly examples

### Naming Conventions
```python
# Files and modules
cli/discover.py          # cl_discover command
intelligence/guidance.py # Agent guidance generation

# Functions and variables
def discover_endpoints():     # Clear, action-oriented
    endpoint_capabilities = {} # Descriptive variable names
    
# Classes
class EntityProcessor:       # Noun-based, clear purpose
class DiscoveryEngine:      # Service-oriented naming
```

### Agent-Friendly Patterns
```python
# Rich error responses for agent guidance
def validate_sparql_query(query: str) -> ValidationResult:
    """Validate SPARQL with agent-friendly suggestions"""
    if "LIMIT" not in query.upper():
        return ValidationResult(
            valid=False,
            error="Missing LIMIT clause in SPARQL query",
            suggestion="Add 'LIMIT 100' to prevent timeout",
            example="SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 100"
        )
```

### Import Organization
```python
# Standard library imports
from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib, json

# Third-party imports  
from pydantic import BaseModel, Field
import click

# Local imports
from .entity import Entity
from ..vocab.composer import composer
```

## Network and Performance Guidelines

### Request Timeouts
```python
# Always set reasonable timeouts for network requests
async def fetch_ontology(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        return response.json()
```

### Caching Strategy
```python
# Multi-layer caching with semantic awareness
cache_key = f"schema:{hash(endpoint_url)}"
if cached := semantic_cache.get(cache_key):
    return cached

# Cache with biological context preservation
semantic_cache.set(cache_key, schema, ttl=3600)
```

### Response Size Management
```python
# Context-aware truncation for large biological datasets
def truncate_biological_result(result: dict, max_size=100_000) -> dict:
    """Preserve essential biological information during truncation"""
    if estimate_tokens(result) <= max_size:
        return result
    
    # Priority preservation:
    # 1. Entity IDs and cross-references
    # 2. Essential biological properties (P31, P352, P703)
    # 3. Key relationships and reasoning context
    return truncated_with_biological_awareness(result)
```

## Knowledge Artifact Layers

CogitareLink follows a structured approach to knowledge representation:

### 1. **Context Layers** (*.context.jsonld)
```json
{
  "@context": {
    "protein": "https://bioschemas.org/Protein",
    "hasSequence": "https://bioschemas.org/hasSequence"
  }
}
```

### 2. **Ontology Definitions** (ontology.ttl)
```turtle
@prefix bio: <https://bioschemas.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

bio:Protein a rdfs:Class ;
    rdfs:label "Protein" ;
    rdfs:comment "A biological macromolecule" .
```

### 3. **SHACL Shapes/Rules** (shapes.ttl)
```turtle
bio:ProteinShape a sh:NodeShape ;
    sh:targetClass bio:Protein ;
    sh:property [
        sh:path bio:hasSequence ;
        sh:minCount 1 ;
        sh:datatype xsd:string
    ] .
```

### 4. **Data Instances** (*.jsonld)
```json
{
  "@context": "protein.context.jsonld",
  "@type": "protein",
  "identifier": "P04637",
  "hasSequence": "MEEPQSDPSVEPPLS..."
}
```

## CLI Tools with Structured Intelligence

### Tool Response Pattern
All CLI tools follow a consistent pattern for agent intelligence:

```python
@click.command()
@click.argument('query')
@click.option('--domains', multiple=True)
def discover(query: str, domains: List[str]):
    """Scientific resource discovery with auto-materialization"""
    
    # Core discovery logic
    result = discovery_engine.discover_resources(query, domains)
    
    # Generate agent guidance
    guidance = guidance_generator.generate_discovery_guidance(result)
    
    # Structured response for agents
    response = {
        "success": True,
        "data": result["resources"],
        "metadata": {
            "execution_time_ms": result["timing"],
            "discovery_methods_used": result["methods"]
        },
        "suggestions": {
            "next_tools": guidance["next_tools"],
            "reasoning_patterns": guidance["reasoning_patterns"]
        },
        "claude_guidance": {
            "discovered_capabilities": guidance["endpoint_capabilities"],
            "domain_intelligence": guidance["domain_patterns"]
        }
    }
    
    click.echo(json.dumps(response, indent=2))
```

### Core CLI Tools

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `cl_discover` | Scientific resource discovery | Multi-method fallbacks, auto-materialization |
| `cl_sparql` | SPARQL queries with guardrails | Complexity analysis, discovery-first validation |
| `cl_materialize` | Knowledge materialization | SHACL rules, convergence detection |
| `cl_explain` | Reasoning chain explanation | PROV-O traces, temporal context |
| `cl_validate` | SHACL validation | Consistency checking, improvement suggestions |
| `cl_query_memory` | Semantic memory queries | OBQC validation, introspection |
| `cl_resolve` | Universal identifier resolution | Self-configuring, cross-reference navigation |
| `cl_orchestrate` | Multi-step workflow coordination | Research templates, checkpoint/resume |

## Framework Integration

### Claude Code Integration
```python
# Automatic tool registration for Claude Code
from cogitarelink.adapters.claude_code import enable_claude_tools

# Enable all CogitareLink tools for Claude Code
enable_claude_tools(teaching_mode=True)

# Tools automatically available:
# - discover_science()
# - sparql_query()  
# - query_memory()
# - explain_reasoning()
```

### Direct CLI Usage
```bash
# Scientific discovery with materialization
cl_discover "SARS-CoV-2 spike protein" --domains biology virology

# SPARQL with discovery guardrails
cl_sparql "SELECT ?protein WHERE { ?protein wdt:P31 wd:Q8054 }" --endpoint wikidata

# Query semantic memory
cl_query_memory "What spike proteins have been discovered?"

# Explain reasoning chain
cl_explain "SARS-CoV-2 spike protein binds ACE2 receptor" --include-provenance
```

## Teaching System Integration

### Continuous Learning from Agent Interactions
```python
# All CLI tools automatically log interactions for learning
@with_teaching
@click.command()
def discover(query, domains):
    """Discovery with automatic teaching integration"""
    
    # Tool execution with automatic logging
    result = execute_discovery(query, domains)
    
    # Teaching system learns from:
    # - Successful discovery patterns
    # - Query composition strategies  
    # - Agent workflow preferences
    # - Error recovery patterns
    
    return result
```

### Learning Metrics
- **Query Success Rate**: Improved SPARQL composition through learning
- **Research Workflow Completion**: Higher success rates for multi-step research
- **Error Recovery**: Better agent recovery from failed operations
- **Reasoning Quality**: More sophisticated biological research strategies

## Security and Safety

### Path and Input Validation
```python
# Secure path handling for CLI tools
def validate_file_path(path: str) -> bool:
    """Validate file paths for security"""
    resolved = Path(path).resolve()
    return resolved.is_relative_to(ALLOWED_BASE_PATH)

# Input sanitization for SPARQL queries
def sanitize_sparql_query(query: str) -> str:
    """Remove potentially dangerous SPARQL constructs"""
    # Remove UPDATE, DELETE, INSERT operations
    # Validate query structure
    return sanitized_query
```

### Cryptographic Verification
```python
# Ed25519 signing for entity verification
def sign_entity(entity: Entity, private_key: bytes) -> SignedEntity:
    """Sign entity with URDNA2015 canonicalization"""
    canonical = entity.normalized  # URDNA2015 format
    signature = ed25519.sign(canonical.encode(), private_key)
    return SignedEntity(entity=entity, signature=signature)
```

## Project Memories and Context

### Key Implementation Decisions
- **uv for package management**: Fast, reliable dependency management
- **Pydantic models**: Type safety and validation for all data structures
- **SHACL as dual-purpose**: Both executable logic and LLM prompting templates
- **Discovery-first pattern**: Prevents common agent errors through guardrails
- **Immutable entities**: Ensures data integrity and reproducible research

### Integration Points
- **llmstxt/**: Reference documentation for LLM context
- **config/**: Live configuration system for prompts and heuristics
- **teaching/**: Continuous learning from agent interactions
- **adapters/**: Framework-agnostic integration layer

### Performance Considerations
- **Schema caching**: Avoid repeated ontology discovery
- **Result streaming**: Handle large biological datasets efficiently
- **Context compaction**: Manage long research sessions within token limits
- **Weak references**: Memory-efficient caching for large vocabularies

## Success Metrics

### Agent Experience
- **Query Success Rate**: Agents compose effective SPARQL queries
- **Research Workflow Completion**: Multi-step biological research succeeds
- **Error Recovery**: Agents recover gracefully from failures
- **Response Time**: Sub-10s response for most operations

### Scientific Rigor
- **Provenance Tracking**: Complete citation chains for all conclusions
- **Cryptographic Verification**: Tamper-evident research data
- **Reproducible Results**: Consistent entity signatures across sessions
- **Knowledge Quality**: High-confidence biological insights

### System Performance
- **Memory Efficiency**: Handles large-scale biological datasets
- **Context Management**: Maintains research continuity within token limits
- **Caching Effectiveness**: Minimizes redundant network requests
- **Teaching System Learning**: Improves agent guidance over time

This unified CogitareLink architecture successfully combines semantic web rigor with agent intelligence, creating a living scientific assistant that continuously improves through real-world usage while maintaining the highest standards of scientific verification and reproducibility.