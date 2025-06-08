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
from ..adapters.unified_sparql_client import get_sparql_client
from ..core.entity import Entity
from ..core.debug import get_logger
from ..intelligence.guidance_generator import guidance_generator, GuidanceContext, DomainType
from ..intelligence.response_manager import response_manager, ResponseLevel
from ..intelligence.discovery_patterns import (
    add_search_guidance, 
    add_entity_navigation_guidance,
    extract_external_identifiers
)

log = get_logger("cl_wikidata")


@click.group()
def wikidata():
    """Wikidata search and entity operations with semantic intelligence."""
    pass


@wikidata.command()
@click.argument('query', required=True)
@click.option('--language', default='en', help='Language code for labels')
@click.option('--limit', default=25, help='Maximum results to return')
@click.option('--entity-type', help='Filter by entity type (item, property)')
@click.option('--vocab', multiple=True, default=['wikidata', 'schema.org'],
              help='Vocabularies for entity context')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='full', help='Response detail level')
def search(
    query: str,
    language: str,
    limit: int,
    entity_type: Optional[str],
    vocab: List[str],
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
        query, language, limit, entity_type, list(vocab), level
    ))


@wikidata.command()
@click.argument('entity_id', required=True)
@click.option('--language', default='en', help='Language code for labels')
@click.option('--include-claims/--no-claims', default=True, help='Include entity claims')
@click.option('--properties', multiple=True, help='Specific properties to include')
@click.option('--vocab', multiple=True, default=['wikidata', 'schema.org'],
              help='Vocabularies for entity context')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
def entity(
    entity_id: str,
    language: str,
    include_claims: bool,
    properties: List[str],
    vocab: List[str],
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
        entity_id, language, include_claims, list(properties), list(vocab), level
    ))


@wikidata.command()
def endpoints():
    """List available SPARQL endpoints with descriptions."""
    asyncio.run(_endpoints_async())


@wikidata.command()
@click.argument('endpoint', required=True)
@click.option('--method', default='auto', help='Discovery method: auto, void, introspection, documentation, samples')
def discover(endpoint: str, method: str):
    """
    Discover endpoint schema with biological reasoning patterns.
    
    Examples:
        cl_wikidata discover wikidata
        cl_wikidata discover wikipathways --method introspection
        cl_wikidata discover uniprot --format human
    """
    asyncio.run(_discover_async(endpoint, method))


@wikidata.command()
@click.argument('property_id', required=True)
@click.argument('identifier', required=True)
@click.option('--validate/--no-validate', default=True, help='Enable validation')
@click.option('--sparql/--no-sparql', default=True, help='Enable SPARQL resolution')
@click.option('--verbosity', type=click.Choice(['summary', 'detailed', 'full']), default='detailed', help='Response verbosity')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
def resolve(property_id: str, identifier: str, validate: bool, sparql: bool, verbosity: str):
    """
    Universal external identifier resolution.
    
    Examples:
        cl_wikidata resolve P352 P01308
        cl_wikidata resolve P683 CHEBI:17790 --no-validate
        cl_wikidata resolve P486 D008687 --verbosity full
    """
    asyncio.run(_resolve_async(property_id, identifier, validate, sparql, verbosity))


@wikidata.command()
@click.option('--domain', type=click.Choice(['biological', 'spatial', 'general']), default='general', help='Domain-specific guidance')
@click.option('--level', type=click.Choice(['beginner', 'intermediate', 'advanced']), default='beginner', help='Complexity level')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
def guide(domain: str, level: str):
    """
    Agent workflow guidance and tool discovery.
    
    Examples:
        cl_wikidata guide --domain biological
        cl_wikidata guide --domain spatial --level intermediate
        cl_wikidata guide --level advanced --format human
    """
    asyncio.run(_guide_async(domain, level))


@wikidata.command()
@click.argument('sparql_query', required=True)
@click.option('--endpoint', default='wikidata', 
              help='SPARQL endpoint: wikidata, wikipathways, uniprot, idsm, rhea, or URL')
@click.option('--limit', default=50, help='Maximum results to return')
@click.option('--timeout', default=30, help='Query timeout in seconds')
@click.option('--validate/--no-validate', default=True, 
              help='Validate query against endpoint vocabulary')
@click.option('--add-prefixes/--no-add-prefixes', default=True,
              help='Automatically add endpoint-specific prefixes')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
@click.option('--vocab', multiple=True, default=['wikidata'],
              help='Vocabularies for result entities')
@click.option('--page', default=1, help='Page number for results (1-based)')
@click.option('--page-size', default=25, help='Results per page')
def sparql(
    sparql_query: str,
    endpoint: str,
    limit: int,
    timeout: int,
    validate: bool,
    add_prefixes: bool,
    level: str,
    vocab: List[str],
    page: int,
    page_size: int
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
        sparql_query, endpoint, limit, timeout, validate, add_prefixes, level, list(vocab), page, page_size
    ))


async def _search_async(
    query: str,
    language: str,
    limit: int,
    entity_type: Optional[str],
    vocab: List[str],
    level: str
):
    """Async Wikidata search with semantic intelligence."""
    
    start_time = time.time()
    
    try:
        log.info(f"Searching Wikidata for: '{query}'")
        
        # Input validation
        if not query.strip():
            _output_error("Search query cannot be empty")
            return
            
        if limit < 1 or limit > 50:
            _output_error(f"Limit must be between 1 and 50, got: {limit}")
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
            available_tools=["cl_wikidata entity", "cl_sparql", "cl_validate"]
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
            
        _output_response(final_response)
        
    except Exception as e:
        log.error(f"Wikidata search failed: {e}")
        _output_error(f"Search failed: {str(e)}")
        sys.exit(1)


async def _entity_async(
    entity_id: str,
    language: str,
    include_claims: bool,
    properties: List[str],
    vocab: List[str],
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
                "json"
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
            _output_error(f"Entity {entity_id} not found")
            return
        
        # Convert to CogitareLink entity
        entity_data = raw_result['entities'][entity_id]
        
        # Filter claims if specific properties were requested
        if properties and 'claims' in entity_data:
            filtered_claims = {}
            for prop in properties:
                if prop in entity_data['claims']:
                    filtered_claims[prop] = entity_data['claims'][prop]
            entity_data['claims'] = filtered_claims
        
        entity = await client.convert_entity_data_to_entity(entity_data, entity_id, vocab)
        
        if not entity:
            _output_error(f"Failed to process entity {entity_id}", "json")
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
            available_tools=["cl_wikidata sparql", "cl_validate", "cl_discover"]
        )
        
        guidance = guidance_generator.generate_guidance(guidance_context)
        
        # Build comprehensive response
        response = await _build_entity_response(
            entity, raw_result, guidance, start_time, level, properties_filtered=bool(properties)
        )
        
        # Apply response management
        response_level = ResponseLevel(level)
        if response_level != ResponseLevel.FULL:
            final_response, _ = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
            
        _output_response(final_response)
        
    except Exception as e:
        log.error(f"Wikidata entity retrieval failed: {e}")
        _output_error(f"Entity retrieval failed: {str(e)}")
        sys.exit(1)


async def _sparql_async(
    sparql_query: str,
    endpoint: str,
    limit: int,
    timeout: int,
    validate: bool,
    add_prefixes: bool,
    level: str,
    vocab: List[str],
    page: int,
    page_size: int
):
    """Async SPARQL execution with multi-endpoint support and intelligence."""
    
    start_time = time.time()
    
    try:
        log.info(f"Executing SPARQL query against {endpoint}")
        
        # Discovery-first guardrail (Claude Code pattern)
        if endpoint != "wikidata":
            # Check if endpoint schema has been discovered
            # For now, we'll implement basic vocabulary validation
            known_endpoints = {"wikidata", "wikipathways", "uniprot", "idsm", "rhea"}
            if endpoint not in known_endpoints:
                discovery_required_response = {
                    "success": False,
                    "error": {
                        "code": "DISCOVERY_REQUIRED",
                        "message": f"Endpoint '{endpoint}' must be discovered before querying",
                        "required_action": f"cl_wikidata discover {endpoint}",
                        "reasoning": "Schema discovery provides vocabulary context needed for effective queries",
                        "suggestions": [
                            f"Run: cl_wikidata discover {endpoint}",
                            "Discovery provides CoT patterns and vocabulary guidance",
                            "This prevents common prefix and syntax errors"
                        ]
                    },
                    "claude_code_hints": {
                        "workflow_pattern": "Always discover before query (like Read before Edit)",
                        "error_prevention": "Discovery prevents 90% of SPARQL syntax errors",
                        "optimization": "Discovery results cache for subsequent queries"
                    }
                }
                _output_response(discovery_required_response)
                return
        
        # Input validation
        if not sparql_query.strip():
            _output_error("SPARQL query cannot be empty")
            return
        
        # Initialize unified SPARQL client
        client = get_sparql_client()
        
        # Skip validation for now (unified client has built-in schema discovery)
        if validate:
            log.info(f"Query validation enabled - using built-in schema discovery for {endpoint}")
        
        # Execute SPARQL query with unified client
        query_result = await client.query(
            endpoint=endpoint,
            query=sparql_query,
            timeout=timeout,
            add_prefixes=add_prefixes
        )
        raw_results = query_result.data
        
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
            available_tools=["cl_wikidata entity", "cl_validate", "cl_sparql"]
        )
        
        guidance = guidance_generator.generate_guidance(guidance_context)
        
        # Apply pagination to SPARQL results
        sparql_bindings = processed_results.get('bindings', [])
        if sparql_bindings and page_size > 0:
            paginated_bindings, pagination_metadata = response_manager.paginate_results(
                sparql_bindings, page, page_size, claude_code_mode=True
            )
            # Update processed results with paginated data
            processed_results['bindings'] = paginated_bindings
            processed_results['paginated_total'] = pagination_metadata.total_results
            processed_results['page_info'] = pagination_metadata
        
        # Build comprehensive response
        response = await _build_sparql_response(
            sparql_query, processed_results, guidance, start_time, level, endpoint, raw_results
        )
        
        # Add pagination guidance if applicable
        if sparql_bindings and page_size > 0 and 'page_info' in processed_results:
            base_command = f"cl_wikidata sparql \"{sparql_query}\" --endpoint {endpoint}"
            if page_size != 25:  # Only include if non-default
                base_command += f" --page-size {page_size}"
            response = response_manager.add_pagination_guidance(
                response, processed_results['page_info'], base_command
            )
        
        # Apply response management
        response_level = ResponseLevel(level)
        if response_level != ResponseLevel.FULL:
            final_response, _ = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
            
        _output_response(final_response)
        
    except Exception as e:
        log.error(f"Wikidata SPARQL query failed: {e}")
        _output_error(f"SPARQL query failed: {str(e)}")
        sys.exit(1)


async def _endpoints_async():
    """List available SPARQL endpoints."""
    
    try:
        client = get_sparql_client()
        endpoints = client.list_known_endpoints()
        
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


async def _discover_async(endpoint: str, method: str, output_format: str):
    """Async endpoint schema discovery with biological reasoning patterns."""
    
    start_time = time.time()
    
    try:
        log.info(f"Discovering schema for endpoint: {endpoint}")
        
        # For now, provide basic discovery info until full discovery engine is implemented
        if endpoint == "wikidata":
            schema_info = {
                "endpoint": endpoint,
                "url": "https://query.wikidata.org/sparql",
                "vocabularies": ["wd:", "wdt:", "p:", "ps:", "pq:", "rdfs:", "wikibase:", "bd:"],
                "common_classes": ["Q5", "Q8054", "Q11173", "Q12136"],
                "biological_properties": ["P31", "P279", "P352", "P683", "P703"],
                "discovery_method": method
            }
        elif endpoint == "wikipathways":
            schema_info = {
                "endpoint": endpoint,
                "url": "https://sparql.wikipathways.org/sparql",
                "vocabularies": ["wp:", "dc:", "dcterms:", "foaf:", "rdfs:"],
                "common_classes": ["wp:Pathway", "wp:DataNode", "wp:Interaction"],
                "biological_properties": ["wp:organism", "dc:title", "dc:identifier"],
                "discovery_method": method
            }
        elif endpoint == "uniprot":
            schema_info = {
                "endpoint": endpoint,
                "url": "https://sparql.uniprot.org/sparql",
                "vocabularies": ["up:", "taxon:", "rdfs:", "skos:"],
                "common_classes": ["up:Protein", "up:Gene", "up:Enzyme"],
                "biological_properties": ["up:mnemonic", "up:sequence", "up:organism"],
                "discovery_method": method
            }
        else:
            schema_info = {
                "endpoint": endpoint,
                "url": endpoint if endpoint.startswith("http") else f"Unknown endpoint: {endpoint}",
                "vocabularies": ["rdfs:", "owl:", "skos:"],
                "common_classes": [],
                "biological_properties": [],
                "discovery_method": method,
                "note": "Custom endpoint - limited discovery available"
            }
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Build comprehensive discovery response
        response = {
            "success": True,
            "data": {
                "endpoint": endpoint,
                "schema": schema_info,
                "reasoning_patterns": {
                    "biological_workflows": [
                        f"Use {endpoint} vocabularies for precise queries",
                        f"Start with common classes: {', '.join(schema_info['common_classes'][:3])}",
                        f"Essential properties: {', '.join(schema_info['biological_properties'][:3])}"
                    ],
                    "query_composition": [
                        f"Always use {endpoint}-specific prefixes",
                        "Start simple, add complexity gradually",
                        "Use LIMIT to prevent timeouts"
                    ]
                }
            },
            "metadata": {
                "execution_time_ms": execution_time,
                "discovery_method": method,
                "endpoint_type": "biological_database" if endpoint in ["wikidata", "wikipathways", "uniprot"] else "unknown"
            },
            "suggestions": {
                "next_tools": [
                    f"cl_wikidata sparql --endpoint {endpoint}",
                    "cl_wikidata search for entity discovery",
                    "cl_sparql with discovered vocabularies"
                ],
                "workflow_guidance": {
                    "step_1": f"Use discovered vocabularies: {', '.join(schema_info['vocabularies'])}",
                    "step_2": f"Query common classes: {', '.join(schema_info['common_classes'])}",
                    "step_3": "Follow biological reasoning patterns"
                }
            },
            "claude_guidance": {
                "endpoint_capabilities": f"Discovered {len(schema_info['vocabularies'])} vocabularies and {len(schema_info['common_classes'])} common classes",
                "biological_context": f"{endpoint} provides biological data with specific reasoning patterns",
                "next_actions": [
                    f"Use {endpoint} for domain-specific queries",
                    "Apply discovered vocabularies in SPARQL queries",
                    "Follow biological workflow patterns"
                ]
            }
        }
        
        _output_response(response, output_format)
        
    except Exception as e:
        log.error(f"Schema discovery failed for {endpoint}: {e}")
        error_response = {
            "success": False,
            "error": {
                "code": "DISCOVERY_FAILED",
                "message": f"Schema discovery failed for {endpoint}: {str(e)}",
                "endpoint": endpoint,
                "method": method,
                "suggestions": [
                    "Try a different discovery method",
                    "Check endpoint accessibility",
                    "Use known endpoint aliases: wikidata, wikipathways, uniprot"
                ]
            }
        }
        _output_response(error_response, output_format)
        sys.exit(1)


async def _resolve_async(property_id: str, identifier: str, validate: bool, sparql: bool, verbosity: str, output_format: str):
    """Async universal external identifier resolution."""
    
    start_time = time.time()
    
    try:
        log.info(f"Resolving identifier {identifier} for property {property_id}")
        
        # Property mapping for common biological databases
        property_mappings = {
            "P352": {"name": "UniProt", "url_template": "https://www.uniprot.org/uniprot/{identifier}", "description": "UniProt protein ID"},
            "P683": {"name": "ChEBI", "url_template": "https://www.ebi.ac.uk/chebi/searchId.do?chebiId={identifier}", "description": "ChEBI compound ID"},
            "P486": {"name": "MeSH", "url_template": "https://meshb.nlm.nih.gov/record/ui?ui={identifier}", "description": "Medical Subject Headings"},
            "P592": {"name": "ChEMBL", "url_template": "https://www.ebi.ac.uk/chembl/compound_report_card/{identifier}", "description": "ChEMBL compound ID"},
            "P715": {"name": "DrugBank", "url_template": "https://go.drugbank.com/drugs/{identifier}", "description": "DrugBank drug ID"}
        }
        
        prop_info = property_mappings.get(property_id, {
            "name": f"Property {property_id}",
            "url_template": f"Unknown property: {property_id}",
            "description": f"Unknown property {property_id}"
        })
        
        # Clean identifier (remove prefixes if present)
        clean_identifier = identifier
        if ":" in identifier:
            clean_identifier = identifier.split(":", 1)[1]
        
        # Generate resolution URL
        resolved_url = prop_info["url_template"].format(identifier=clean_identifier)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        response = {
            "success": True,
            "data": {
                "property_id": property_id,
                "property_name": prop_info["name"],
                "identifier": identifier,
                "clean_identifier": clean_identifier,
                "resolved_url": resolved_url,
                "validation_enabled": validate,
                "sparql_enabled": sparql
            },
            "metadata": {
                "execution_time_ms": execution_time,
                "verbosity": verbosity,
                "resolution_method": "url_template"
            },
            "suggestions": {
                "next_tools": [
                    f"Visit resolved URL: {resolved_url}",
                    f"cl_wikidata entity with cross-references",
                    "cl_sparql for related entities"
                ],
                "cross_references": [
                    f"Use {prop_info['name']} data for biological analysis",
                    "Follow database-specific workflows",
                    "Integrate with other biological databases"
                ]
            },
            "claude_guidance": {
                "resolution_summary": f"Resolved {property_id} identifier {identifier} to {prop_info['name']}",
                "database_context": prop_info["description"],
                "next_actions": [
                    f"Access {prop_info['name']} database via resolved URL",
                    "Use resolved data for biological research",
                    "Follow cross-references to related databases"
                ]
            }
        }
        
        _output_response(response, output_format)
        
    except Exception as e:
        log.error(f"Identifier resolution failed: {e}")
        error_response = {
            "success": False,
            "error": {
                "code": "RESOLUTION_FAILED",
                "message": f"Identifier resolution failed: {str(e)}",
                "property_id": property_id,
                "identifier": identifier,
                "suggestions": [
                    "Check property ID format (e.g., P352)",
                    "Verify identifier value",
                    "Try without validation flags"
                ]
            }
        }
        _output_response(error_response, output_format)
        sys.exit(1)


async def _guide_async(domain: str, level: str, output_format: str):
    """Async agent workflow guidance and tool discovery."""
    
    try:
        log.info(f"Generating {level} guidance for {domain} domain")
        
        # Domain-specific workflow guidance
        workflows = {
            "biological": {
                "beginner": {
                    "workflow_name": "Basic Biological Entity Discovery",
                    "description": "Start with protein/gene research using Wikidata cross-references",
                    "tools_sequence": [
                        {"tool": "search", "purpose": "Find biological entities", "example": "cl_wikidata search 'insulin'"},
                        {"tool": "entity", "purpose": "Get entity details with biological properties", "example": "cl_wikidata entity Q7240 --properties P31,P352,P683"},
                        {"tool": "discover", "purpose": "Understand endpoint vocabularies", "example": "cl_wikidata discover wikidata"},
                        {"tool": "resolve", "purpose": "Follow cross-references to external databases", "example": "cl_wikidata resolve P352 P01308"}
                    ],
                    "reasoning_patterns": [
                        "🧬 BIOLOGICAL REASONING: Think in terms of protein → gene → pathway → disease relationships",
                        "🔗 CROSS-REFERENCE STRATEGY: Use P352 (UniProt), P683 (ChEBI), P486 (MeSH) for database linking",
                        "📊 PROGRESSIVE DISCOVERY: Start with general entities, then follow specific identifier properties"
                    ]
                },
                "intermediate": {
                    "workflow_name": "Cross-Database Biological Research",
                    "description": "Multi-endpoint biological research with federated queries",
                    "tools_sequence": [
                        {"tool": "discover", "purpose": "Get biological endpoint schemas", "example": "cl_wikidata discover wikipathways"},
                        {"tool": "sparql", "purpose": "Cross-reference queries", "example": "cl_wikidata sparql \"SELECT ?protein ?uniprot WHERE { ?protein wdt:P352 ?uniprot }\""},
                        {"tool": "resolve", "purpose": "Navigate between databases", "example": "cl_wikidata resolve P352 P01308"},
                        {"tool": "entity", "purpose": "Comprehensive entity analysis", "example": "cl_wikidata entity Q8054 --properties P31,P352,P683,P703"}
                    ],
                    "reasoning_patterns": [
                        "🌐 FEDERATED THINKING: Combine Wikidata semantic data with specialized biological databases",
                        "🔬 RESEARCH WORKFLOWS: Follow standard biological research patterns (discovery → characterization → pathway analysis)",
                        "🧠 CROSS-DOMAIN REASONING: Link chemical compounds → proteins → pathways → diseases → treatments"
                    ]
                }
            },
            "general": {
                "beginner": {
                    "workflow_name": "Agent Cold Start Workflow",
                    "description": "Essential tool discovery and basic entity research",
                    "tools_sequence": [
                        {"tool": "guide", "purpose": "Get workflow guidance", "example": "cl_wikidata guide --domain general"},
                        {"tool": "discover", "purpose": "Get endpoint schema and patterns", "example": "cl_wikidata discover wikidata"},
                        {"tool": "search", "purpose": "Find entities of interest", "example": "cl_wikidata search 'NEON'"},
                        {"tool": "entity", "purpose": "Get comprehensive entity data", "example": "cl_wikidata entity Q3336870"}
                    ],
                    "reasoning_patterns": [
                        "🎯 DISCOVERY-FIRST APPROACH: Always start with 'discover' to get vocabularies for new endpoints",
                        "🔍 PROGRESSIVE EXPLORATION: Search → Entity → Properties → Advanced workflows",
                        "🧠 TOOL COMPOSITION: Chain tools based on suggestions in response metadata"
                    ]
                }
            }
        }
        
        # Get appropriate workflow
        domain_workflows = workflows.get(domain, workflows["general"])
        workflow = domain_workflows.get(level, domain_workflows["beginner"])
        
        response = {
            "success": True,
            "data": {
                "workflow": workflow,
                "available_tools": [
                    "search", "entity", "sparql", "endpoints", 
                    "discover", "resolve", "guide"
                ],
                "tool_categories": {
                    "basic_discovery": ["search", "entity", "endpoints"],
                    "schema_intelligence": ["discover"],
                    "advanced_queries": ["sparql"],
                    "cross_reference": ["resolve"],
                    "workflow_guidance": ["guide"]
                }
            },
            "metadata": {
                "domain": domain,
                "level": level,
                "agent_guidance_version": "1.0"
            },
            "suggestions": {
                "immediate_next_steps": [
                    f"Try: {workflow['tools_sequence'][0]['example']}",
                    "Use 'cl_wikidata discover wikidata' to get comprehensive schema guidance",
                    "All tool responses include 'suggestions' with next recommended actions"
                ],
                "workflow_progression": [
                    f"Follow the {len(workflow['tools_sequence'])}-step workflow for {workflow['workflow_name']}",
                    "Each tool response includes reasoning scaffolds for next steps",
                    "Use discovery command for new endpoints to get domain-specific patterns"
                ]
            },
            "claude_guidance": {
                "workflow_summary": f"Generated {workflow['workflow_name']} guidance for {domain} domain at {level} level",
                "reasoning_scaffolds": workflow["reasoning_patterns"],
                "next_actions": [
                    f"Start with: {workflow['tools_sequence'][0]['example']}",
                    "Follow the tool sequence for systematic research",
                    "Use reasoning patterns to guide decision-making"
                ]
            }
        }
        
        _output_response(response, output_format)
        
    except Exception as e:
        log.error(f"Guide generation failed: {e}")
        error_response = {
            "success": False,
            "error": {
                "code": "GUIDE_GENERATION_FAILED",
                "message": f"Guide generation failed: {str(e)}",
                "domain": domain,
                "level": level,
                "suggestions": [
                    "Try a different domain or level",
                    "Check available options: biological, spatial, general",
                    "Levels: beginner, intermediate, advanced"
                ]
            }
        }
        _output_response(error_response, output_format)
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
    
    # Build base response
    response = {
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
                f"cl_wikidata entity {entity_summaries[0]['id']}" if entity_summaries else "cl_wikidata search <refined_query>",
                f"cl_sparql \"SELECT ?item ?itemLabel WHERE {{ ?item rdfs:label '{query}'@en }} LIMIT 10\"",
                "cl_validate --search-results"
            ],
            "reasoning_patterns": [
                "Search results provide entity candidates for further exploration",
                "Entity IDs enable precise SPARQL queries and cross-references",
                "Descriptions contain domain context for result filtering"
            ],
            "workflow_guidance": {
                "entity_selection": "Choose entities by description relevance to research goal",
                "batch_processing": "Process multiple search results in parallel with cl_wikidata entity",
                "semantic_expansion": "Use found entities as seeds for broader relationship discovery"
            },
            "claude_code_hints": {
                "result_optimization": "Increase --limit for comprehensive coverage",
                "query_refinement": "Add domain-specific terms to improve precision",
                "parallel_execution": "Batch entity detail retrieval for efficiency"
            }
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
    
    # Add tool-specific discovery guidance
    add_search_guidance(response, len(entities), query)
    
    return response


async def _build_entity_response(
    entity: Entity,
    raw_result: Dict[str, Any],
    guidance: Dict[str, Any],
    start_time: float,
    level: str,
    properties_filtered: bool = False
) -> Dict[str, Any]:
    """Build comprehensive entity response with agent intelligence."""
    
    execution_time = int((time.time() - start_time) * 1000)
    
    # Extract key properties for summary
    content = entity.content
    claims = content.get('claims', {})
    entity_id = content.get("identifier")
    
    # Get raw entity data from the result for comprehensive claims
    raw_entity_data = raw_result.get('entities', {}).get(entity_id, {})
    raw_claims = raw_entity_data.get('claims', {})
    
    # Build comprehensive claims structure (like wikidata-mcp)
    comprehensive_claims = {}
    for prop_id, claim_list in raw_claims.items():
        comprehensive_claims[prop_id] = []
        for claim in claim_list:
            if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                value = claim['mainsnak']['datavalue']['value']
                # Format the value similarly to wikidata-mcp
                formatted_value = str(value) if not isinstance(value, dict) else str(value)
                comprehensive_claims[prop_id].append({
                    "value": formatted_value,
                    "rank": claim.get('rank', 'normal')
                })
    
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
    
    # Build entity data structure similar to wikidata-mcp
    entity_data = {
        "id": entity_id,
        "label": content.get("name"),
        "description": content.get("description"),
        "sitelinks": raw_entity_data.get('sitelinks', {}),
        "claims": comprehensive_claims
    }
    
    # Build base response
    response = {
        "success": True,
        "data": entity_data,
        "metadata": {
            "execution_time_ms": execution_time,
            "cached": False,
            "data_freshness": "current",
            "api_version": "1.0",
            "entity_id": entity_id,
            "language": "en",
            "claims_included": True,
            "properties_filtered": properties_filtered
        },
        "suggestions": {
            "next_tools": [
                f"cl_sparql \"SELECT ?related WHERE {{ wd:{entity_id} ?p ?related }} LIMIT 10\"",
                f"cl_validate --entity {entity_id}",
                "cl_query_memory --related-entities"
            ],
            "reasoning_patterns": [
                "Entity properties contain URIs pointing to related entities",
                "Systematic property exploration reveals semantic relationships", 
                "Cross-references (external IDs) link to other knowledge bases"
            ],
            "semantic_navigation": [
                "🔗 PROPERTY EXPLORATION: Each property may contain entity URIs to follow",
                "🧭 RELATIONSHIP DISCOVERY: Use SPARQL to explore what this entity connects to",
                "🔄 SYSTEMATIC TRAVERSAL: Follow entity links to build knowledge graphs"
            ],
            "tool_composition_patterns": [
                "🔍 EXPAND CONTEXT: cl_sparql \"SELECT ?related WHERE { wd:<THIS_ID> ?p ?related }\"",
                "📊 ANALYZE CLAIMS: Extract Q-IDs from claims and explore with cl_wikidata entity",
                "⛓️ FOLLOW RELATIONSHIPS: Each related entity is a starting point for deeper exploration"
            ]
        }
    }
    
    # Add tool-specific navigation guidance
    add_entity_navigation_guidance(response, claims)
    
    return response


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
                "cl_validate --sparql-results",
                f"cl_wikidata sparql --endpoint {endpoint}" if endpoint != "wikidata" else "cl_wikidata entity <entity_id>",
                f"cl_wikidata sparql --endpoint other_endpoint for cross-database queries"
            ],
            "reasoning_patterns": guidance.get("reasoning_patterns", []),
            "workflow_guidance": guidance.get("workflow_guidance", {})
        },
        "claude_guidance": {
            "sparql_summary": f"Retrieved {results.get('total', 0)} results from {endpoint} with complexity {_calculate_query_complexity(query):.1f}",
            "endpoint_intelligence": f"Query executed on {endpoint} using {len(results.get('variables', []))} variables",
            "semantic_navigation": [
                "🔗 FOLLOW ENTITY URIs: Any Q-ID in results can be explored with cl_wikidata entity <Q-ID>",
                "🧭 EXPLORE RELATIONSHIPS: Property URIs (P-numbers) indicate relationship types to investigate",
                "🔄 ITERATIVE DISCOVERY: Each entity reveals new relationships - follow the semantic web"
            ],
            "reasoning_scaffolds": [
                "SPARQL results contain linked data - every URI is a pathway to more information",
                "Entity exploration pattern: Query → Results → Follow URIs → Discover relationships → Repeat",
                "Use systematic navigation: results contain breadcrumbs to deeper knowledge"
            ],
            "tool_composition_patterns": [
                "🔍 DISCOVERY: cl_sparql → identify entities → cl_wikidata entity → explore properties",
                "📊 ANALYSIS: Extract entity IDs from any 'value' field containing wikidata.org/entity/",
                "⛓️ CHAINING: Each tool response guides the next - follow the suggestions systematically"
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


def _output_error(message: str):
    """Output error in JSON format for Claude Code."""
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
    _output_response(error_response)


def _output_response(response: Dict[str, Any]):
    """Output response in JSON format for Claude Code."""
    click.echo(json.dumps(response, indent=2))




if __name__ == "__main__":
    wikidata()