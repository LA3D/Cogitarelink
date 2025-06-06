"""cl_sparql: SPARQL queries with discovery-first guardrails.

Implements discovery-first guardrails (never query without schema understanding) 
with vocabulary-aware validation and agent intelligence patterns.
"""

from __future__ import annotations

import asyncio
import json
import sys
import re
import urllib.parse
from typing import Optional, List, Dict, Any

import click

# Add optional SPARQLWrapper for real SPARQL execution
try:
    from SPARQLWrapper import SPARQLWrapper, JSON, XML, CSV, TSV
    _HAS_SPARQLWRAPPER = True
except ImportError:
    _HAS_SPARQLWRAPPER = False

# Import Wikidata client for direct Wikidata access
try:
    from ..adapters.wikidata_client import WikidataClient
    _HAS_WIKIDATA_CLIENT = True
except ImportError:
    _HAS_WIKIDATA_CLIENT = False

from ..intelligence.discovery_engine import discovery_engine
from ..intelligence.response_manager import response_manager, ResponseLevel
from ..intelligence.guidance_generator import guidance_generator, GuidanceContext, DomainType
from ..core.entity import Entity
from ..core.debug import get_logger
from ..vocab.registry import registry

log = get_logger("cl_sparql")

# SPARQL query patterns for validation
SPARQL_PATTERNS = {
    'prefixes': re.compile(r'PREFIX\s+(\w+):\s*<([^>]+)>', re.IGNORECASE),
    'select': re.compile(r'SELECT\s+(.*?)\s+WHERE', re.IGNORECASE | re.DOTALL),
    'where': re.compile(r'WHERE\s*{(.+?)}', re.IGNORECASE | re.DOTALL),
    'limit': re.compile(r'LIMIT\s+(\d+)', re.IGNORECASE),
    'entities': re.compile(r'<([^>]+)>|(\w+:\w+)'),
}

@click.command()
@click.argument('query', required=True)
@click.option('--endpoint', help='SPARQL endpoint URL (if not auto-discovered)')
@click.option('--context-id', help='Context ID from previous discovery')
@click.option('--discover-first/--no-discover-first', default=True, 
              help='Discover schema before querying (default: True)')
@click.option('--validate-query/--no-validate-query', default=True,
              help='Validate query structure and vocabulary (default: True)')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
@click.option('--max-results', default=100, help='Maximum results to return')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human', 'csv']), 
              default='json', help='Output format')
@click.option('--domains', multiple=True, help='Domain hints for discovery')
def sparql_query(
    query: str,
    endpoint: Optional[str],
    context_id: Optional[str],
    discover_first: bool,
    validate_query: bool,
    level: str,
    max_results: int,
    output_format: str,
    domains: List[str]
):
    """
    Execute SPARQL queries with discovery-first guardrails and vocabulary validation.
    
    Examples:
        cl_sparql "SELECT ?protein WHERE { ?protein a <http://schema.org/Protein> }"
        cl_sparql "SELECT * WHERE { ?s ?p ?o } LIMIT 10" --endpoint wikidata
        cl_sparql "PREFIX wp: <http://wikipathways.org/> SELECT ?pathway WHERE { ?pathway wp:organism ?org }" --discover-first
        cl_sparql "SELECT ?protein ?name WHERE { ?protein a bioschemas:Protein ; name ?name }" --context-id ctx_abc123
    """
    asyncio.run(_sparql_async(
        query, endpoint, context_id, discover_first, validate_query,
        level, max_results, output_format, list(domains)
    ))

async def _sparql_async(
    query: str,
    endpoint: Optional[str], 
    context_id: Optional[str],
    discover_first: bool,
    validate_query: bool,
    level: str,
    max_results: int,
    output_format: str,
    domains: List[str]
):
    """Async SPARQL execution with full intelligence integration."""
    
    try:
        log.info(f"Processing SPARQL query with discovery-first guardrails")
        
        # Convert level to ResponseLevel enum
        response_level = ResponseLevel(level)
        
        # Step 1: Query validation and analysis
        validation_result = await _validate_sparql_query(query, domains)
        if not validation_result["valid"]:
            response = _build_validation_error_response(validation_result, query)
            _output_response(response, output_format)
            return
        
        # Step 2: Discovery-first guardrails
        if discover_first:
            discovery_context = await _ensure_schema_discovery(
                validation_result, context_id, domains
            )
            if discovery_context["requires_discovery"]:
                response = _build_discovery_required_response(
                    discovery_context, query, validation_result
                )
                _output_response(response, output_format)
                return
        
        # Step 3: Execute SPARQL query (placeholder for now)
        query_result = await _execute_sparql_query(
            query, endpoint, validation_result, max_results
        )
        
        # Step 4: Build comprehensive agent response
        response = await _build_sparql_response(
            query_result, validation_result, response_level, context_id
        )
        
        # Step 5: Apply response management
        if response_level != ResponseLevel.FULL:
            final_response, _ = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
        
        _output_response(final_response, output_format)
        
    except Exception as e:
        log.error(f"SPARQL execution failed: {e}")
        error_response = {
            "success": False,
            "error": {
                "code": "SPARQL_EXECUTION_ERROR",
                "message": str(e),
                "recovery_plan": {
                    "next_tool": "cl_discover",
                    "parameters": {"query_entities": _extract_entities_from_query(query)},
                    "reasoning": "Discover schemas for entities in query before retrying"
                }
            }
        }
        _output_response(error_response, output_format)
        sys.exit(1)

async def _validate_sparql_query(query: str, domains: List[str]) -> Dict[str, Any]:
    """Validate SPARQL query structure and vocabulary usage."""
    
    validation = {
        "valid": True,
        "issues": [],
        "suggestions": [],
        "extracted_prefixes": {},
        "extracted_entities": [],
        "detected_domains": domains or [],
        "complexity_score": 0.0
    }
    
    # Extract prefixes
    prefixes = SPARQL_PATTERNS['prefixes'].findall(query)
    for prefix, uri in prefixes:
        validation["extracted_prefixes"][prefix] = uri
    
    # Check for missing LIMIT (performance guardrail)
    if not SPARQL_PATTERNS['limit'].search(query):
        validation["issues"].append({
            "type": "performance",
            "message": "Query lacks LIMIT clause - may cause timeout",
            "suggestion": "Add 'LIMIT 100' to prevent performance issues",
            "severity": "warning"
        })
        validation["suggestions"].append("Add LIMIT clause for better performance")
    
    # Extract entities and URIs
    entities = SPARQL_PATTERNS['entities'].findall(query)
    for full_uri, prefixed in entities:
        if full_uri:
            validation["extracted_entities"].append(full_uri)
        elif prefixed:
            validation["extracted_entities"].append(prefixed)
    
    # Validate known prefixes against registry
    for prefix in validation["extracted_prefixes"]:
        try:
            registry_entry = registry.resolve(prefix)
            validation["suggestions"].append(f"Prefix '{prefix}' found in vocabulary registry")
        except KeyError:
            validation["issues"].append({
                "type": "vocabulary",
                "message": f"Unknown prefix '{prefix}' - may need discovery",
                "suggestion": f"Run 'cl_discover {prefix}' to register vocabulary",
                "severity": "warning"
            })
    
    # Calculate complexity score
    complexity_factors = [
        len(validation["extracted_entities"]) * 0.1,  # Entity count
        len(validation["extracted_prefixes"]) * 0.2,  # Vocabulary complexity
        query.count("OPTIONAL") * 0.3,               # Optional patterns
        query.count("UNION") * 0.4,                  # Union complexity
        query.count("FILTER") * 0.2,                 # Filter complexity
    ]
    validation["complexity_score"] = min(sum(complexity_factors), 10.0)
    
    # Detect domains from query content
    if any(bio in query.lower() for bio in ["protein", "gene", "uniprot", "bioschemas"]):
        validation["detected_domains"].append("biology")
    if any(geo in query.lower() for geo in ["coordinate", "location", "place"]):
        validation["detected_domains"].append("geospatial")
    
    return validation

async def _ensure_schema_discovery(
    validation_result: Dict[str, Any],
    context_id: Optional[str],
    domains: List[str]
) -> Dict[str, Any]:
    """Ensure schema discovery for entities in query (discovery-first guardrails)."""
    
    discovery_context = {
        "requires_discovery": False,
        "undiscovered_entities": [],
        "discovery_suggestions": [],
        "context_available": context_id is not None
    }
    
    # Check if entities need discovery
    for entity in validation_result["extracted_entities"]:
        if entity.startswith("http"):
            # Full URI - check if we have schema information
            try:
                # Try to resolve via registry
                registry.resolve(entity)
            except KeyError:
                discovery_context["undiscovered_entities"].append(entity)
                discovery_context["requires_discovery"] = True
        
        elif ":" in entity:
            # Prefixed entity - check if prefix is known
            prefix = entity.split(":")[0]
            if prefix not in validation_result["extracted_prefixes"]:
                discovery_context["undiscovered_entities"].append(entity)
                discovery_context["requires_discovery"] = True
    
    # Generate discovery suggestions
    if discovery_context["requires_discovery"]:
        for entity in discovery_context["undiscovered_entities"]:
            discovery_context["discovery_suggestions"].append(
                f"cl_discover '{entity}' --domains {' '.join(domains or ['general'])}"
            )
    
    return discovery_context

async def _execute_sparql_query(
    query: str,
    endpoint: Optional[str],
    validation_result: Dict[str, Any],
    max_results: int
) -> Dict[str, Any]:
    """Execute SPARQL query against real endpoints (Wikidata, etc.)."""
    
    if not _HAS_SPARQLWRAPPER:
        log.warning("SPARQLWrapper not available - falling back to mock results")
        return _mock_sparql_results(query, max_results, validation_result)
    
    # Determine endpoint
    sparql_endpoint = _determine_sparql_endpoint(endpoint, validation_result)
    
    # Add common prefixes if needed
    enhanced_query = _enhance_query_with_prefixes(query, sparql_endpoint)
    
    # Calculate execution timeout based on complexity
    timeout = _calculate_timeout(validation_result["complexity_score"])
    
    try:
        import time
        start_time = time.time()
        
        # Set up SPARQLWrapper with endpoint and timeout
        sparql = SPARQLWrapper(sparql_endpoint)
        sparql.setTimeout(int(timeout))
        sparql.setQuery(enhanced_query)
        sparql.setReturnFormat(JSON)
        
        log.info(f"Executing SPARQL query against {sparql_endpoint}")
        log.debug(f"Query: {enhanced_query[:200]}...")
        
        # Execute the query
        results = sparql.query()
        result_data = results.convert()
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Process and format results
        processed_results = _process_sparql_response(result_data, max_results)
        
        return {
            "success": True,
            "results": processed_results["rows"],
            "result_count": processed_results["total"],
            "columns": processed_results["columns"],
            "execution_time_ms": execution_time,
            "endpoint_used": sparql_endpoint,
            "query_complexity": validation_result["complexity_score"],
            "raw_response": result_data  # For debugging/advanced use
        }
        
    except Exception as e:
        error_msg = str(e)
        log.error(f"SPARQL query execution failed: {error_msg}")
        
        # Categorize error types
        if "timeout" in error_msg.lower():
            error_type = "timeout"
            suggestions = [
                "Add more specific FILTER constraints",
                "Reduce LIMIT value",
                "Break complex query into smaller parts",
                "Add more specific entity constraints"
            ]
        elif "400" in error_msg or "bad request" in error_msg.lower():
            error_type = "http_error"
            suggestions = [
                "Check SPARQL syntax",
                "Verify entity and property IDs",
                "Ensure proper PREFIX declarations",
                "Check endpoint availability"
            ]
        else:
            error_type = "execution_error"
            suggestions = [
                "Check network connectivity",
                "Verify query syntax",
                "Try simpler query first",
                "Check endpoint URL"
            ]
            
        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": f"SPARQL execution failed: {error_msg}",
                "suggestions": suggestions
            },
            "endpoint_used": sparql_endpoint,
            "query_complexity": validation_result["complexity_score"]
        }

def _mock_sparql_results(query: str, max_results: int, validation_result: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback mock results when SPARQLWrapper not available."""
    mock_results = [
        {"protein": "http://example.org/protein1", "name": "insulin"},
        {"protein": "http://example.org/protein2", "name": "glucagon"}
    ]
    
    limited_results = mock_results[:max_results]
    
    return {
        "success": True,
        "results": limited_results,
        "result_count": len(limited_results),
        "execution_time_ms": 150,
        "endpoint_used": "mock://sparql.endpoint",
        "query_complexity": validation_result["complexity_score"]
    }

def _determine_sparql_endpoint(endpoint: Optional[str], validation_result: Dict[str, Any]) -> str:
    """Determine which SPARQL endpoint to use based on query analysis."""
    
    # If endpoint explicitly provided, use it
    if endpoint:
        endpoint_urls = {
            "wikidata": "https://query.wikidata.org/sparql",
            "uniprot": "https://sparql.uniprot.org/sparql", 
            "idsm": "https://idsm.elixir-czech.cz/sparql/endpoint/idsm"
        }
        return endpoint_urls.get(endpoint, endpoint)
    
    # Auto-detect endpoint from query content
    query_domains = validation_result.get("detected_domains", [])
    extracted_prefixes = validation_result.get("extracted_prefixes", {})
    
    # Check for Wikidata patterns
    wikidata_indicators = ["wd:", "wdt:", "wikibase:", "bd:", "p:", "ps:", "pq:", "pr:"]
    if any(prefix in str(extracted_prefixes) for prefix in wikidata_indicators):
        return "https://query.wikidata.org/sparql"
    
    # Check for biology domain
    if "biology" in query_domains:
        # Default to Wikidata for biological queries (has extensive bio data)
        return "https://query.wikidata.org/sparql"
    
    # Default to Wikidata (most comprehensive)
    return "https://query.wikidata.org/sparql"

def _enhance_query_with_prefixes(query: str, endpoint: str) -> str:
    """Add common prefixes to query if not already present."""
    
    # Common Wikidata prefixes
    if "wikidata.org" in endpoint:
        common_prefixes = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
"""
        
        # Check if prefixes are already declared
        existing_prefixes = set()
        for match in SPARQL_PATTERNS['prefixes'].finditer(query):
            existing_prefixes.add(match.group(1))
        
        # Add missing prefixes
        needed_prefixes = []
        for line in common_prefixes.strip().split('\n'):
            if line.strip():
                prefix_name = line.split()[1].rstrip(':')
                if prefix_name not in existing_prefixes and f"{prefix_name}:" in query:
                    needed_prefixes.append(line)
        
        if needed_prefixes:
            prefix_block = '\n'.join(needed_prefixes) + '\n\n'
            return prefix_block + query
    
    return query

def _calculate_timeout(complexity_score: float) -> float:
    """Calculate appropriate timeout based on query complexity."""
    # Base timeout: 10 seconds for simple queries
    base_timeout = 10.0
    
    # Scale with complexity (max 60 seconds)
    complexity_factor = min(complexity_score / 10.0, 5.0)  # 0-5x multiplier
    
    return min(base_timeout + (complexity_factor * 10), 60.0)

def _process_sparql_response(raw_response: Dict[str, Any], max_results: int) -> Dict[str, Any]:
    """Process raw SPARQL JSON response into agent-friendly format."""
    
    if 'results' not in raw_response or 'bindings' not in raw_response['results']:
        return {"columns": [], "rows": [], "total": 0}
    
    bindings = raw_response['results']['bindings']
    variables = raw_response.get('head', {}).get('vars', [])
    
    # Convert bindings to simplified table format
    rows = []
    for binding in bindings[:max_results]:  # Apply limit
        row = {}
        for var in variables:
            if var in binding:
                value_obj = binding[var]
                # Extract just the value, keeping datatype info available
                if value_obj['type'] == 'uri':
                    row[var] = value_obj['value']
                elif value_obj['type'] == 'literal':
                    row[var] = value_obj['value']
                    # Preserve datatype if present
                    if 'datatype' in value_obj:
                        row[f"{var}_datatype"] = value_obj['datatype']
                else:
                    row[var] = value_obj['value']
            else:
                row[var] = None
        rows.append(row)
    
    return {
        "columns": variables,
        "rows": rows,
        "total": len(rows),
        "total_available": len(bindings)  # Before limit applied
    }

async def _build_sparql_response(
    query_result: Dict[str, Any],
    validation_result: Dict[str, Any], 
    response_level: ResponseLevel,
    context_id: Optional[str]
) -> Dict[str, Any]:
    """Build comprehensive agent-friendly SPARQL response."""
    
    # Create guidance context for SPARQL results
    guidance_context = GuidanceContext(
        entity_type="SparqlResult",
        domain_type=DomainType.SEMANTIC_WEB,
        properties=list(query_result.get("results", [{}])[0].keys()) if query_result.get("results") else [],
        confidence_score=0.9,  # High confidence for successful queries
        previous_actions=["sparql_query"],
        available_tools=["cl_materialize", "cl_validate", "cl_explain"]
    )
    
    # Generate guidance
    guidance = guidance_generator.generate_guidance(guidance_context)
    
    # Handle failed queries
    if not query_result.get("success", False):
        error = query_result.get("error", {})
        return {
            "success": False,
            "error": error,
            "metadata": {
                "endpoint": query_result.get("endpoint_used", "unknown"),
                "query_complexity": validation_result["complexity_score"],
                "validation_issues": len(validation_result["issues"])
            },
            "claude_guidance": {
                "error_analysis": f"SPARQL execution failed: {error.get('type', 'unknown')}",
                "recovery_strategy": _get_error_recovery_strategy(error),
                "next_actions": error.get("suggestions", []),
                "performance_guidance": {
                    "complexity_assessment": "high" if validation_result["complexity_score"] > 7 else "medium",
                    "timeout_prevention": [
                        "Add LIMIT clause if missing",
                        "Use more specific entity constraints",
                        "Break complex queries into parts"
                    ]
                }
            }
        }
    
    # Build successful response
    result_count = query_result.get("result_count", 0)
    response = {
        "success": True,
        "data": {
            "sparql_results": query_result.get("results", []),
            "result_count": result_count,
            "columns": query_result.get("columns", []),
            "query_metadata": {
                "complexity_score": validation_result["complexity_score"],
                "entities_discovered": validation_result["extracted_entities"],
                "vocabularies_used": list(validation_result["extracted_prefixes"].keys()),
                "execution_time_ms": query_result.get("execution_time_ms", 0),
                "total_available": query_result.get("total_available", result_count)
            }
        },
        "metadata": {
            "endpoint": query_result["endpoint_used"],
            "query_complexity": validation_result["complexity_score"],
            "result_count": result_count,
            "validation_issues": len(validation_result["issues"]),
            "vocabularies_count": len(validation_result["extracted_prefixes"]),
            "performance": {
                "execution_time_ms": query_result.get("execution_time_ms", 0),
                "results_limited": result_count < query_result.get("total_available", result_count)
            }
        },
        "suggestions": {
            "next_tools": [
                "cl_materialize --from-sparql-results",
                "cl_validate --sparql-results", 
                "cl_explain --sparql-reasoning"
            ],
            "reasoning_patterns": guidance["reasoning_patterns"],
            "workflow_guidance": guidance["workflow_guidance"],
            "query_optimization": validation_result["suggestions"]
        },
        "claude_guidance": {
            "sparql_summary": f"Retrieved {result_count} results with complexity {validation_result['complexity_score']:.1f}",
            "query_intelligence": f"Query uses {len(validation_result['extracted_prefixes'])} vocabularies via {query_result['endpoint_used']}",
            "next_actions": [
                "Materialize results as Entities for semantic processing",
                "Validate results against known schemas",
                "Explore result relationships via follow-up queries"
            ],
            "reasoning_scaffolds": [
                "SPARQL results can be materialized as semantic entities",
                "Use entity signatures for result verification",
                "Consider expanding queries for richer context"
            ],
            "performance_guidance": {
                "complexity_assessment": "low" if validation_result["complexity_score"] < 3 else 
                                       "medium" if validation_result["complexity_score"] < 7 else "high",
                "optimization_hints": validation_result["suggestions"],
                "execution_performance": "fast" if query_result.get("execution_time_ms", 0) < 1000 else
                                       "moderate" if query_result.get("execution_time_ms", 0) < 5000 else "slow"
            }
        }
    }
    
    # Add context chaining if available
    if context_id:
        response["context_id"] = context_id
        response["suggestions"]["chaining_context"] = {
            "previous_context": context_id,
            "recommended_workflows": [
                f"cl_discover → cl_sparql → cl_materialize",
                f"cl_sparql → cl_validate → cl_explain"
            ]
        }
    
    return response

def _build_validation_error_response(
    validation_result: Dict[str, Any],
    query: str
) -> Dict[str, Any]:
    """Build educational validation error response."""
    
    return {
        "success": False,
        "error": {
            "code": "QUERY_VALIDATION_FAILED",
            "message": "SPARQL query validation failed",
            "validation_issues": validation_result["issues"],
            "suggestions": validation_result["suggestions"]
        },
        "claude_guidance": {
            "validation_summary": f"Found {len(validation_result['issues'])} issues in SPARQL query",
            "common_fixes": [
                "Add LIMIT clause for performance",
                "Ensure all prefixes are declared",
                "Validate entity URIs and identifiers"
            ],
            "next_actions": [
                "Fix validation issues and retry",
                "Use cl_discover for unknown vocabularies",
                "Consider query simplification"
            ],
            "query_analysis": {
                "entities_found": validation_result["extracted_entities"],
                "prefixes_used": list(validation_result["extracted_prefixes"].keys()),
                "complexity_score": validation_result["complexity_score"]
            }
        }
    }

def _build_discovery_required_response(
    discovery_context: Dict[str, Any],
    query: str,
    validation_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Build discovery-first guardrail response."""
    
    return {
        "success": False,
        "error": {
            "code": "DISCOVERY_REQUIRED",
            "message": "Discovery-first guardrail: Schema discovery required before querying",
            "undiscovered_entities": discovery_context["undiscovered_entities"],
            "required_actions": discovery_context["discovery_suggestions"]
        },
        "claude_guidance": {
            "guardrail_explanation": "CogitareLink enforces discovery-first to prevent vocabulary errors",
            "discovery_workflow": [
                "1. Discover schemas for unknown entities/vocabularies",
                "2. Validate vocabulary compatibility", 
                "3. Retry SPARQL query with discovered context",
                "4. Materialize results for semantic processing"
            ],
            "next_actions": discovery_context["discovery_suggestions"],
            "reasoning": [
                "Discovery-first prevents common SPARQL errors",
                "Schema understanding improves query accuracy",
                "Validated vocabularies enable better result processing"
            ]
        }
    }

def _get_error_recovery_strategy(error: Dict[str, Any]) -> Dict[str, Any]:
    """Generate recovery strategy based on error type."""
    
    error_type = error.get("type", "unknown")
    
    if error_type == "timeout":
        return {
            "strategy": "query_optimization",
            "next_tool": "cl_sparql",
            "parameters": {
                "add_limit": True,
                "reduce_complexity": True,
                "add_filters": True
            },
            "reasoning": "Query timed out - needs optimization for better performance"
        }
    
    elif error_type == "http_error":
        status_code = error.get("status_code", 0)
        if status_code == 400:
            return {
                "strategy": "syntax_validation",
                "next_tool": "cl_discover",
                "parameters": {
                    "validate_syntax": True,
                    "check_prefixes": True
                },
                "reasoning": "Bad request - likely SPARQL syntax or vocabulary error"
            }
        elif status_code in [500, 502, 503]:
            return {
                "strategy": "endpoint_fallback",
                "next_tool": "cl_sparql",
                "parameters": {
                    "try_alternative_endpoint": True,
                    "reduce_query_complexity": True
                },
                "reasoning": "Server error - try simpler query or alternative endpoint"
            }
        else:
            return {
                "strategy": "endpoint_discovery",
                "next_tool": "cl_discover",
                "parameters": {
                    "check_endpoint_status": True,
                    "find_alternatives": True
                },
                "reasoning": f"HTTP {status_code} error - validate endpoint availability"
            }
    
    elif error_type == "execution_error":
        return {
            "strategy": "discovery_first",
            "next_tool": "cl_discover",
            "parameters": {
                "discover_schemas": True,
                "validate_entities": True
            },
            "reasoning": "Execution failed - need schema discovery before retrying"
        }
    
    else:
        return {
            "strategy": "general_recovery",
            "next_tool": "cl_discover",
            "parameters": {
                "broad_discovery": True,
                "syntax_check": True
            },
            "reasoning": "Unknown error - start with discovery and validation"
        }

def _extract_entities_from_query(query: str) -> List[str]:
    """Extract entity references from SPARQL query for error recovery."""
    entities = []
    matches = SPARQL_PATTERNS['entities'].findall(query)
    for full_uri, prefixed in matches:
        if full_uri:
            entities.append(full_uri)
        elif prefixed:
            entities.append(prefixed)
    return entities[:5]  # Limit for recovery suggestions

def _output_response(response: Dict[str, Any], output_format: str):
    """Output response in requested format."""
    
    if output_format == 'json':
        click.echo(json.dumps(response, indent=2))
    elif output_format == 'human':
        _print_human_readable(response)
    elif output_format == 'csv':
        _print_csv_format(response)

def _print_human_readable(response: Dict[str, Any]):
    """Print human-readable SPARQL results."""
    
    if response.get("success", False):
        data = response.get("data", {})
        print(f"✅ SPARQL Query Results")
        
        # Handle potentially truncated fields gracefully
        result_count = data.get('result_count', 'unknown')
        print(f"   Results: {result_count}")
        
        query_meta = data.get('query_metadata', {})
        if 'complexity_score' in query_meta:
            print(f"   Complexity: {query_meta['complexity_score']:.1f}")
        if 'execution_time_ms' in query_meta:
            print(f"   Execution time: {query_meta['execution_time_ms']}ms")
        
        sparql_results = data.get("sparql_results", [])
        if sparql_results:
            print(f"\n📊 Sample Results:")
            for i, result in enumerate(sparql_results[:3], 1):
                print(f"   {i}. {result}")
        
        suggestions = response.get("suggestions", {})
        next_tools = suggestions.get("next_tools", [])
        if next_tools:
            print(f"\n💡 Suggested next steps:")
            for i, tool in enumerate(next_tools[:3], 1):
                print(f"   {i}. {tool}")
                
        # Show vocabulary information if available
        vocab_count = response.get("metadata", {}).get("vocabularies_count", 0)
        if vocab_count > 0:
            print(f"\n📚 Vocabularies used: {vocab_count}")
            
    else:
        error = response.get("error", {})
        message = error.get("message", "Unknown error")
        print(f"❌ SPARQL Query Failed: {message}")
        
        if "required_actions" in error:
            print(f"🔍 Required Discovery:")
            for action in error["required_actions"][:3]:
                print(f"   • {action}")

def _print_csv_format(response: Dict[str, Any]):
    """Print SPARQL results in CSV format."""
    
    if response["success"] and response["data"]["sparql_results"]:
        results = response["data"]["sparql_results"]
        if results:
            # Print CSV header
            headers = list(results[0].keys())
            print(",".join(headers))
            
            # Print CSV rows
            for result in results:
                row = [str(result.get(h, "")) for h in headers]
                print(",".join(row))
    else:
        print("# No results available")

if __name__ == "__main__":
    sparql_query()