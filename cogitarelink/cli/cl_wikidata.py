"""cl_wikidata: Wikidata search and entity retrieval with agent intelligence.

Provides Wikidata search, entity retrieval, and SPARQL capabilities
integrated with CogitareLink's semantic memory and agent intelligence.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

import click

from ..adapters.wikidata_client import WikidataClient
from ..adapters.multi_sparql_client import MultiSparqlClient
from ..core.entity import Entity
from ..core.debug import get_logger
from ..intelligence.guidance_generator import guidance_generator, GuidanceContext, DomainType
from ..intelligence.response_manager import response_manager, ResponseLevel

log = get_logger("cl_wikidata")


@click.group()
def wikidata():
    """Wikidata search and entity operations with semantic intelligence."""
    pass


@wikidata.command()
@click.argument('query', required=True)
@click.option('--language', default='en', help='Language code for labels')
@click.option('--limit', default=10, help='Maximum results to return')
@click.option('--entity-type', help='Filter by entity type (item, property)')
@click.option('--vocab', multiple=True, default=['wikidata', 'schema.org'],
              help='Vocabularies for entity context')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
def search(
    query: str,
    language: str,
    limit: int,
    entity_type: Optional[str],
    vocab: List[str],
    output_format: str,
    level: str
):
    """
    Search Wikidata entities with semantic intelligence.
    
    Examples:
        cl_wikidata search "Douglas Adams"
        cl_wikidata search "protein" --entity-type item --limit 5
        cl_wikidata search "SARS-CoV-2" --vocab bioschemas
        cl_wikidata search "insulin" --format human
    """
    asyncio.run(_search_async(
        query, language, limit, entity_type, list(vocab), output_format, level
    ))


@wikidata.command()
@click.argument('entity_id', required=True)
@click.option('--language', default='en', help='Language code for labels')
@click.option('--include-claims/--no-claims', default=True, help='Include entity claims')
@click.option('--properties', multiple=True, help='Specific properties to include')
@click.option('--vocab', multiple=True, default=['wikidata', 'schema.org'],
              help='Vocabularies for entity context')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
def entity(
    entity_id: str,
    language: str,
    include_claims: bool,
    properties: List[str],
    vocab: List[str],
    output_format: str,
    level: str
):
    """
    Get detailed Wikidata entity information.
    
    Examples:
        cl_wikidata entity Q42
        cl_wikidata entity P31 --no-claims
        cl_wikidata entity Q8054 --properties P31,P279 --format human
    """
    asyncio.run(_entity_async(
        entity_id, language, include_claims, list(properties), list(vocab), output_format, level
    ))


@wikidata.command()
def endpoints():
    """List available SPARQL endpoints with descriptions."""
    asyncio.run(_endpoints_async())


@wikidata.command()
@click.argument('sparql_query', required=True)
@click.option('--endpoint', default='wikidata', 
              help='SPARQL endpoint: wikidata, wikipathways, uniprot, idsm, rhea, or URL')
@click.option('--limit', default=100, help='Maximum results to return')
@click.option('--timeout', default=30, help='Query timeout in seconds')
@click.option('--validate/--no-validate', default=True, 
              help='Validate query against endpoint vocabulary')
@click.option('--add-prefixes/--no-add-prefixes', default=True,
              help='Automatically add endpoint-specific prefixes')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human', 'table']), 
              default='json', help='Output format')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
@click.option('--vocab', multiple=True, default=['wikidata'],
              help='Vocabularies for result entities')
def sparql(
    sparql_query: str,
    endpoint: str,
    limit: int,
    timeout: int,
    validate: bool,
    add_prefixes: bool,
    output_format: str,
    level: str,
    vocab: List[str]
):
    """
    Execute SPARQL queries against multiple biological databases.
    
    Examples:
        cl_wikidata sparql "SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q8054 } LIMIT 5"
        cl_wikidata sparql "SELECT ?pathway ?title WHERE { ?pathway a wp:Pathway }" --endpoint wikipathways
        cl_wikidata sparql "SELECT ?protein ?name WHERE { ?protein a up:Protein }" --endpoint uniprot
        cl_wikidata sparql "SELECT ?compound ?name WHERE { ?compound rdfs:label ?name }" --endpoint idsm
    """
    asyncio.run(_sparql_async(
        sparql_query, endpoint, limit, timeout, validate, add_prefixes, output_format, level, list(vocab)
    ))


async def _search_async(
    query: str,
    language: str,
    limit: int,
    entity_type: Optional[str],
    vocab: List[str],
    output_format: str,
    level: str
):
    """Async Wikidata search with semantic intelligence."""
    
    start_time = time.time()
    
    try:
        log.info(f"Searching Wikidata for: '{query}'")
        
        # Input validation
        if not query.strip():
            _output_error("Search query cannot be empty", output_format)
            return
            
        if limit < 1 or limit > 50:
            _output_error(f"Limit must be between 1 and 50, got: {limit}", output_format)
            return
        
        # Initialize Wikidata client
        client = WikidataClient(timeout=30)
        
        # Execute search
        raw_results = await client.search_entities(
            query, language, limit, entity_type
        )
        
        # Convert to CogitareLink entities
        entities = await client.convert_search_to_entities(raw_results, vocab)
        
        # Generate semantic intelligence
        guidance_context = GuidanceContext(
            entity_type="WikidataSearchResults",
            domain_type=DomainType.KNOWLEDGE_GRAPH,
            properties=["identifier", "name", "description"] + ([f"entity_type:{entity_type}"] if entity_type else []),
            confidence_score=0.9,
            previous_actions=["search"],
            available_tools=["cl_wikidata entity", "cl_sparql", "cl_materialize"]
        )
        
        guidance = guidance_generator.generate_guidance(guidance_context)
        
        # Build comprehensive response
        response = await _build_search_response(
            query, entities, raw_results, guidance, start_time, level
        )
        
        # Apply response management
        response_level = ResponseLevel(level)
        if response_level != ResponseLevel.FULL:
            final_response, _ = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
            
        _output_response(final_response, output_format)
        
    except Exception as e:
        log.error(f"Wikidata search failed: {e}")
        _output_error(f"Search failed: {str(e)}", output_format)
        sys.exit(1)


async def _entity_async(
    entity_id: str,
    language: str,
    include_claims: bool,
    properties: List[str],
    vocab: List[str],
    output_format: str,
    level: str
):
    """Async Wikidata entity retrieval with semantic intelligence."""
    
    start_time = time.time()
    
    try:
        log.info(f"Retrieving Wikidata entity: {entity_id}")
        
        # Validate entity ID
        if not ((entity_id.startswith('Q') or entity_id.startswith('P')) and entity_id[1:].isdigit()):
            _output_error(
                f"Entity ID must be in format Q123456 or P123456, got: {entity_id}",
                output_format
            )
            return
        
        # Initialize Wikidata client
        client = WikidataClient(timeout=30)
        
        # Get entity data
        props = None
        if not include_claims:
            props = ['labels', 'descriptions', 'sitelinks']
        elif properties:
            props = ['labels', 'descriptions', 'sitelinks', 'claims']
        
        raw_result = await client.get_entities([entity_id], language, props)
        
        if entity_id not in raw_result.get('entities', {}):
            _output_error(f"Entity {entity_id} not found", output_format)
            return
        
        # Convert to CogitareLink entity
        entity_data = raw_result['entities'][entity_id]
        entity = await client.convert_entity_data_to_entity(entity_data, entity_id, vocab)
        
        if not entity:
            _output_error(f"Failed to process entity {entity_id}", output_format)
            return
        
        # Generate semantic intelligence based on entity type
        entity_label = entity.content.get('name', 'Unknown')
        claims = entity.content.get('claims', {})
        
        # Determine domain type based on claims
        domain_type = DomainType.KNOWLEDGE_GRAPH
        if 'P31' in claims:  # instance of
            instance_types = [claim['value'] for claim in claims['P31']]
            if any('Q8054' in t for t in instance_types):  # protein
                domain_type = DomainType.LIFE_SCIENCES
            elif any('Q11173' in t for t in instance_types):  # chemical compound
                domain_type = DomainType.CHEMISTRY
        
        guidance_context = GuidanceContext(
            entity_type=f"WikidataEntity:{entity_id}",
            domain_type=domain_type,
            properties=list(claims.keys()) if claims else [],
            confidence_score=0.95,
            previous_actions=["entity_retrieval"],
            available_tools=["cl_wikidata sparql", "cl_materialize", "cl_discover"]
        )
        
        guidance = guidance_generator.generate_guidance(guidance_context)
        
        # Build comprehensive response
        response = await _build_entity_response(
            entity, raw_result, guidance, start_time, level
        )
        
        # Apply response management
        response_level = ResponseLevel(level)
        if response_level != ResponseLevel.FULL:
            final_response, _ = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
            
        _output_response(final_response, output_format)
        
    except Exception as e:
        log.error(f"Wikidata entity retrieval failed: {e}")
        _output_error(f"Entity retrieval failed: {str(e)}", output_format)
        sys.exit(1)


async def _sparql_async(
    sparql_query: str,
    endpoint: str,
    limit: int,
    timeout: int,
    validate: bool,
    add_prefixes: bool,
    output_format: str,
    level: str,
    vocab: List[str]
):
    """Async SPARQL execution with multi-endpoint support and intelligence."""
    
    start_time = time.time()
    
    try:
        log.info(f"Executing SPARQL query against {endpoint}")
        
        # Input validation
        if not sparql_query.strip():
            _output_error("SPARQL query cannot be empty", output_format)
            return
        
        # Initialize multi-endpoint SPARQL client
        client = MultiSparqlClient(timeout=timeout)
        
        # Validate query against endpoint if requested
        if validate:
            validation = client.validate_query_for_endpoint(sparql_query, endpoint)
            if not validation.get('valid', True):
                error_response = {
                    "success": False,
                    "error": {
                        "code": "QUERY_VALIDATION_FAILED",
                        "message": validation.get('error', 'Query validation failed'),
                        "endpoint": endpoint,
                        "wrong_prefixes": validation.get('wrong_prefixes', []),
                        "expected_prefixes": validation.get('expected_prefixes', []),
                        "suggestions": validation.get('suggestions', [])
                    }
                }
                _output_response(error_response, output_format)
                return
        
        # Execute SPARQL query with multi-endpoint support
        raw_results = await client.sparql_query(
            sparql_query, 
            endpoint=endpoint,
            add_prefixes=add_prefixes,
            limit=limit if 'LIMIT' not in sparql_query.upper() else None
        )
        
        # Process results
        processed_results = _process_sparql_results(raw_results)
        
        # Generate semantic intelligence based on endpoint
        endpoint_domain_map = {
            "wikidata": DomainType.KNOWLEDGE_GRAPH,
            "wikipathways": DomainType.LIFE_SCIENCES,
            "uniprot": DomainType.LIFE_SCIENCES,
            "idsm": DomainType.CHEMISTRY,
            "rhea": DomainType.CHEMISTRY
        }
        
        domain_type = endpoint_domain_map.get(endpoint, DomainType.KNOWLEDGE_GRAPH)
        
        guidance_context = GuidanceContext(
            entity_type=f"{endpoint.title()}SPARQLResults",
            domain_type=domain_type,
            properties=processed_results.get('variables', []),
            confidence_score=0.85,
            previous_actions=[f"sparql_query_{endpoint}"],
            available_tools=["cl_wikidata entity", "cl_materialize", "cl_sparql"]
        )
        
        guidance = guidance_generator.generate_guidance(guidance_context)
        
        # Build comprehensive response
        response = await _build_sparql_response(
            sparql_query, processed_results, guidance, start_time, level, endpoint, raw_results
        )
        
        # Apply response management
        response_level = ResponseLevel(level)
        if response_level != ResponseLevel.FULL:
            final_response, _ = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
            
        _output_response(final_response, output_format)
        
    except Exception as e:
        log.error(f"Wikidata SPARQL query failed: {e}")
        _output_error(f"SPARQL query failed: {str(e)}", output_format)
        sys.exit(1)


async def _endpoints_async():
    """List available SPARQL endpoints."""
    
    try:
        client = MultiSparqlClient()
        endpoints = client.list_endpoints()
        
        response = {
            "success": True,
            "data": {
                "endpoints": endpoints,
                "total_count": len(endpoints)
            },
            "metadata": {
                "operation": "list_endpoints",
                "capabilities": [
                    "Multi-database SPARQL queries",
                    "Biological database federation", 
                    "Vocabulary-aware query validation",
                    "Automatic prefix injection"
                ]
            },
            "suggestions": {
                "usage_examples": [
                    "cl_wikidata sparql \"SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q8054 } LIMIT 5\"",
                    "cl_wikidata sparql \"SELECT ?pathway ?title WHERE { ?pathway a wp:Pathway } LIMIT 5\" --endpoint wikipathways",
                    "cl_wikidata sparql \"SELECT ?protein ?name WHERE { ?protein a up:Protein } LIMIT 5\" --endpoint uniprot",
                    "cl_wikidata sparql \"SELECT ?compound ?name WHERE { ?compound rdfs:label ?name } LIMIT 5\" --endpoint idsm"
                ],
                "endpoint_selection": [
                    "Use 'wikidata' for general knowledge graph queries",
                    "Use 'wikipathways' for biological pathway analysis",
                    "Use 'uniprot' for detailed protein information",
                    "Use 'idsm' for chemical compound data",
                    "Use 'rhea' for biochemical reaction data"
                ]
            },
            "claude_guidance": {
                "multi_endpoint_strategy": "Query multiple endpoints for comprehensive biological research",
                "cross_database_linking": "Use Wikidata cross-references to connect to specialized databases",
                "workflow_recommendations": [
                    "Start with Wikidata search to identify entities",
                    "Follow cross-references to specialized databases",
                    "Use endpoint-specific vocabularies for detailed queries",
                    "Materialize results for semantic integration"
                ]
            }
        }
        
        click.echo(json.dumps(response, indent=2))
        
    except Exception as e:
        log.error(f"Failed to list endpoints: {e}")
        error_response = {
            "success": False,
            "error": {
                "code": "ENDPOINT_LISTING_FAILED",
                "message": f"Failed to list endpoints: {str(e)}"
            }
        }
        click.echo(json.dumps(error_response, indent=2))
        sys.exit(1)


async def _build_search_response(
    query: str,
    entities: List[Entity],
    raw_results: Dict[str, Any],
    guidance: Dict[str, Any],
    start_time: float,
    level: str
) -> Dict[str, Any]:
    """Build comprehensive search response with agent intelligence."""
    
    execution_time = int((time.time() - start_time) * 1000)
    
    # Process entities for response
    entity_summaries = []
    for entity in entities[:10]:  # Limit for response size
        summary = {
            "id": entity.content.get("identifier"),
            "name": entity.content.get("name"),
            "description": entity.content.get("description"),
            "wikidataUrl": entity.content.get("@id"),
            "signature": entity.sha256[:12]
        }
        entity_summaries.append(summary)
    
    return {
        "success": True,
        "data": {
            "query": query,
            "entities": entity_summaries,
            "total_found": len(entities)
        },
        "metadata": {
            "execution_time_ms": execution_time,
            "results_count": len(entities),
            "api_endpoint": "wikidata_search",
            "confidence_score": 0.9
        },
        "suggestions": {
            "next_tools": [
                f"cl_wikidata entity {entity_summaries[0]['id']}" if entity_summaries else "",
                "cl_sparql with discovered entities",
                "cl_materialize --from-entities"
            ],
            "reasoning_patterns": guidance.get("reasoning_patterns", []),
            "workflow_guidance": guidance.get("workflow_guidance", {})
        },
        "claude_guidance": {
            "search_summary": f"Found {len(entities)} Wikidata entities for '{query}'",
            "next_actions": [
                "Explore detailed entity information",
                "Use entities in SPARQL queries",
                "Materialize entity relationships"
            ],
            "reasoning_scaffolds": [
                "Wikidata entities provide stable identifiers for knowledge graphs",
                "Entity descriptions help understand semantic relationships",
                "Cross-references enable federated database queries"
            ]
        }
    }


async def _build_entity_response(
    entity: Entity,
    raw_result: Dict[str, Any],
    guidance: Dict[str, Any],
    start_time: float,
    level: str
) -> Dict[str, Any]:
    """Build comprehensive entity response with agent intelligence."""
    
    execution_time = int((time.time() - start_time) * 1000)
    
    # Extract key properties for summary
    content = entity.content
    claims = content.get('claims', {})
    
    # Identify important cross-references
    cross_references = {}
    important_props = {
        'P352': 'UniProt',
        'P683': 'ChEBI', 
        'P231': 'CAS',
        'P592': 'ChEMBL',
        'P715': 'Drugbank'
    }
    
    for prop, db_name in important_props.items():
        if prop in claims:
            values = []
            for claim in claims[prop]:
                if isinstance(claim, dict) and 'value' in claim:
                    values.append(claim['value'])
                elif isinstance(claim, str):
                    values.append(claim)
            cross_references[db_name] = values
    
    return {
        "success": True,
        "data": {
            "entity": {
                "id": content.get("identifier"),
                "name": content.get("name"),
                "description": content.get("description"),
                "wikidataUrl": content.get("@id"),
                "wikipediaUrl": content.get("wikipediaUrl"),
                "signature": entity.sha256[:12]
            },
            "claims_count": len(claims),
            "cross_references": cross_references
        },
        "metadata": {
            "execution_time_ms": execution_time,
            "entity_id": content.get("identifier"),
            "confidence_score": 0.95
        },
        "suggestions": {
            "next_tools": [
                "cl_sparql with entity relationships",
                "cl_materialize --from-entities", 
                "cl_discover with cross-references"
            ],
            "reasoning_patterns": guidance.get("reasoning_patterns", []),
            "workflow_guidance": guidance.get("workflow_guidance", {})
        },
        "claude_guidance": {
            "entity_summary": f"Retrieved {content.get('name')} with {len(claims)} properties",
            "cross_reference_summary": f"Found {len(cross_references)} database cross-references",
            "next_actions": [
                "Follow cross-references to external databases",
                "Query for related entities using SPARQL",
                "Materialize entity relationships for analysis"
            ],
            "reasoning_scaffolds": [
                "Cross-references enable federated database exploration",
                "Entity properties define semantic relationships",
                "Claims provide structured knowledge for reasoning"
            ]
        }
    }


async def _build_sparql_response(
    query: str,
    results: Dict[str, Any],
    guidance: Dict[str, Any],
    start_time: float,
    level: str,
    endpoint: str = "wikidata",
    raw_results: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Build comprehensive SPARQL response with multi-endpoint intelligence."""
    
    execution_time = int((time.time() - start_time) * 1000)
    
    # Extract endpoint info if available
    endpoint_info = raw_results.get('endpoint_info', {}) if raw_results else {}
    
    return {
        "success": True,
        "data": {
            "query": query,
            "sparql_results": results.get("bindings", []),
            "result_count": results.get("total", 0),
            "columns": results.get("variables", []),
            "endpoint": endpoint
        },
        "metadata": {
            "execution_time_ms": execution_time,
            "query_complexity": _calculate_query_complexity(query),
            "endpoint": endpoint,
            "endpoint_info": endpoint_info,
            "confidence_score": 0.85
        },
        "suggestions": {
            "next_tools": [
                "cl_materialize --from-sparql-results",
                f"cl_wikidata sparql --endpoint {endpoint}" if endpoint != "wikidata" else "cl_wikidata entity <entity_id>",
                f"cl_wikidata sparql --endpoint other_endpoint for cross-database queries"
            ],
            "reasoning_patterns": guidance.get("reasoning_patterns", []),
            "workflow_guidance": guidance.get("workflow_guidance", {})
        },
        "claude_guidance": {
            "sparql_summary": f"Retrieved {results.get('total', 0)} results from {endpoint} with complexity {_calculate_query_complexity(query):.1f}",
            "endpoint_intelligence": f"Query executed on {endpoint} using {len(results.get('variables', []))} variables",
            "next_actions": [
                f"Materialize {endpoint} results as Entities for semantic processing",
                f"Cross-reference {endpoint} results with other biological databases",
                "Explore result relationships via follow-up queries"
            ],
            "reasoning_scaffolds": [
                f"SPARQL results from {endpoint} can be materialized as semantic entities",
                "Use cross-references to link between biological databases",
                f"Consider querying complementary endpoints for {endpoint} data"
            ]
        }
    }


def _process_sparql_results(raw_results: Dict[str, Any]) -> Dict[str, Any]:
    """Process raw SPARQL results into structured format."""
    
    if 'results' not in raw_results or 'bindings' not in raw_results['results']:
        return {"variables": [], "bindings": [], "total": 0}
    
    bindings = raw_results['results']['bindings']
    variables = raw_results.get('head', {}).get('vars', [])
    
    return {
        "variables": variables,
        "bindings": bindings,
        "total": len(bindings)
    }


def _calculate_query_complexity(query: str) -> float:
    """Calculate SPARQL query complexity score."""
    
    complexity_score = 0.0
    query_upper = query.upper()
    
    # Basic complexity factors
    if 'OPTIONAL' in query_upper:
        complexity_score += query_upper.count('OPTIONAL') * 0.5
    if 'FILTER' in query_upper:
        complexity_score += query_upper.count('FILTER') * 0.3
    if 'UNION' in query_upper:
        complexity_score += query_upper.count('UNION') * 0.7
    if 'LIMIT' not in query_upper:
        complexity_score += 1.0
    
    return complexity_score


def _output_error(message: str, output_format: str):
    """Output error in requested format."""
    error_response = {
        "success": False,
        "error": {
            "code": "WIKIDATA_ERROR",
            "message": message,
            "suggestions": [
                "Check input parameters",
                "Verify internet connection",
                "Try simpler query"
            ]
        }
    }
    _output_response(error_response, output_format)


def _output_response(response: Dict[str, Any], output_format: str):
    """Output response in requested format."""
    
    if output_format == 'json':
        click.echo(json.dumps(response, indent=2))
    elif output_format == 'human':
        _print_human_readable(response)


def _print_human_readable(response: Dict[str, Any]):
    """Print human-readable response."""
    
    if response.get("success", False):
        data = response.get("data", {})
        
        if "entities" in data:
            # Search results
            print(f"✅ Wikidata Search Results")
            print(f"   Query: {data.get('query')}")
            print(f"   Found: {data.get('total_found')} entities")
            
            for entity in data["entities"][:5]:
                print(f"   {entity['id']}: {entity['name']}")
                print(f"      {entity['description']}")
                
        elif "entity" in data:
            # Entity details
            entity = data["entity"]
            print(f"✅ Wikidata Entity")
            print(f"   ID: {entity['id']}")
            print(f"   Name: {entity['name']}")
            print(f"   Description: {entity['description']}")
            print(f"   Claims: {data.get('claims_count', 0)}")
            
            cross_refs = data.get("cross_references", {})
            if cross_refs:
                print(f"   Cross-references:")
                for db, ids in cross_refs.items():
                    print(f"      {db}: {', '.join(ids[:3])}")
                    
        elif "sparql_results" in data:
            # SPARQL results
            print(f"✅ SPARQL Query Results")
            print(f"   Results: {data.get('result_count')}")
            print(f"   Columns: {', '.join(data.get('columns', []))}")
            
            for result in data["sparql_results"][:5]:
                row_data = []
                for var in data.get("columns", []):
                    if var in result:
                        row_data.append(result[var]['value'])
                print(f"   {' | '.join(row_data)}")
                
        # Show suggestions
        suggestions = response.get("suggestions", {})
        next_tools = suggestions.get("next_tools", [])
        if next_tools:
            print(f"\n💡 Suggested next steps:")
            for tool in next_tools[:3]:
                if tool.strip():
                    print(f"   → {tool}")
                    
    else:
        error = response.get("error", {})
        print(f"❌ Error: {error.get('message', 'Unknown error')}")


if __name__ == "__main__":
    wikidata()