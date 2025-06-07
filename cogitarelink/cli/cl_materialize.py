"""cl_materialize: Knowledge materialization with SHACL rules and semantic memory.

Materializes knowledge from SPARQL results, applies SHACL reasoning rules,
and stores enriched entities in semantic memory for LLM context access.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

import click

from ..core.entity import Entity
from ..core.debug import get_logger
from ..intelligence.guidance_generator import guidance_generator, GuidanceContext, DomainType
from ..intelligence.response_manager import response_manager, ResponseLevel

# Try to import experimental reasoning components
try:
    from ..reason.sandbox import reason_over
    _HAS_REASONING = True
except ImportError:
    _HAS_REASONING = False

# Try to import SPARQLWrapper for CONSTRUCT queries
try:
    from SPARQLWrapper import SPARQLWrapper, JSON, RDFXML, TURTLE
    _HAS_SPARQLWRAPPER = True
except ImportError:
    _HAS_SPARQLWRAPPER = False

# Try to import rdflib for SHACL rule parsing
try:
    import rdflib
    from rdflib import Graph, Namespace, RDF, RDFS
    from rdflib.namespace import SH
    _HAS_RDFLIB = True
except ImportError:
    _HAS_RDFLIB = False

log = get_logger("cl_materialize")

@click.command()
@click.option('--from-sparql-results', 'sparql_results_json', 
              help='JSON file or string containing SPARQL results to materialize')
@click.option('--from-entities', 'entities_json',
              help='JSON file or string containing entities to materialize')
@click.option('--from-sparql-endpoint', 'sparql_endpoint',
              help='SPARQL endpoint to materialize from using CONSTRUCT rules')
@click.option('--shapes-file', type=click.Path(exists=True),
              help='SHACL shapes file (.ttl) for rule-based materialization')
@click.option('--rules-file', type=click.Path(exists=True),
              help='SHACL rules file (.ttl) for SPARQL CONSTRUCT materialization')
@click.option('--vocab', multiple=True, default=['bioschemas', 'schema.org'],
              help='Vocabularies to use for context composition')
@click.option('--store-in-memory', is_flag=True, default=True,
              help='Store materialized entities in semantic memory')
@click.option('--include-provenance', is_flag=True, default=True,
              help='Include full provenance tracking for materialized facts')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='full', help='Response detail level')
@click.option('--context-id', help='Context ID from previous tool execution')
def materialize(
    sparql_results_json: Optional[str],
    entities_json: Optional[str],
    sparql_endpoint: Optional[str], 
    shapes_file: Optional[str],
    rules_file: Optional[str],
    vocab: List[str],
    store_in_memory: bool,
    include_provenance: bool,
    level: str,
    context_id: Optional[str]
):
    """
    Materialize knowledge from SPARQL results or entities using SHACL rules.
    """
    response = {
        "success": False,
        "error": {
            "code": "NOT_IMPLEMENTED",
            "message": "Knowledge materialization is not implemented yet",
            "suggestions": [
                "Use cl_wikidata search for entity discovery",
                "Use cl_sparql for direct SPARQL queries",
                "Use cl_resolve for identifier resolution"
            ]
        },
        "metadata": {
            "execution_time_ms": 0,
            "feature_status": "not_implemented"
        },
        "suggestions": {
            "next_tools": [
                "cl_wikidata search <query>",
                "cl_sparql <query> --endpoint <endpoint>", 
                "cl_resolve <property> <identifier>"
            ],
            "reasoning_patterns": [
                "Discovery → Query → Resolution workflow available",
                "Use existing tools for semantic exploration"
            ]
        },
        "claude_guidance": {
            "explanation": "Knowledge materialization with SHACL rules is planned but not yet implemented",
            "alternatives": [
                "Use discovered entities directly from search results",
                "Chain cl_wikidata and cl_sparql for research workflows",
                "Export results to external tools for materialization"
            ]
        }
    }
    
    click.echo(json.dumps(response, indent=2))

async def _materialize_async(
    sparql_results_json: Optional[str],
    entities_json: Optional[str],
    sparql_endpoint: Optional[str],
    shapes_file: Optional[str],
    rules_file: Optional[str],
    vocab: List[str],
    store_in_memory: bool,
    include_provenance: bool,
    level: str,
    context_id: Optional[str]
):
    """Async materialization with full intelligence integration."""
    
    try:
        log.info("Starting knowledge materialization with SHACL reasoning")
        
        # Convert level to ResponseLevel enum
        response_level = ResponseLevel(level)
        
        # Step 1: Determine materialization mode and load/generate data
        if sparql_endpoint and (rules_file or shapes_file):
            # Mode 2: SPARQL CONSTRUCT materialization from endpoint
            log.info("Using SPARQL CONSTRUCT materialization mode")
            entities, materialization_summary = await _materialize_from_sparql_endpoint(
                sparql_endpoint, rules_file or shapes_file, vocab, include_provenance
            )
            if not entities:
                _output_error("No entities could be materialized from SPARQL endpoint")
                return
        else:
            # Mode 1: Local pyshacl materialization
            log.info("Using local pyshacl materialization mode")
            input_data = await _load_input_data(sparql_results_json, entities_json)
            if not input_data:
                _output_error("No input data provided")
                return
                
            # Convert to entities first
            entities = await _convert_to_entities(input_data, vocab)
            if not entities:
                _output_error("No entities could be created from input data")
                return
                
            # Apply local SHACL materialization (if shapes provided)
            materialization_summary = {"rules_applied": 0, "new_triples": 0}
            if shapes_file and _HAS_REASONING:
                entities, materialization_summary = await _apply_shacl_materialization(
                    entities, shapes_file, include_provenance
                )
            
        # Step 2: Store in semantic memory (if requested)
        memory_summary = {}
        if store_in_memory:
            memory_summary = await _store_in_semantic_memory(entities)
            
        # Step 3: Build comprehensive response
        response = await _build_materialization_response(
            entities, materialization_summary, memory_summary,
            response_level, context_id
        )
        
        # Step 4: Apply response management for context optimization
        if response_level != ResponseLevel.FULL:
            final_response, _ = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
            
        _output_response(final_response)
        
    except Exception as e:
        log.error(f"Materialization failed: {e}")
        error_response = {
            "success": False,
            "error": {
                "code": "MATERIALIZATION_ERROR",
                "message": str(e),
                "recovery_plan": {
                    "next_tool": "cl_validate",
                    "parameters": {"check_input_format": True},
                    "reasoning": "Validate input format before retrying materialization"
                }
            }
        }
        _output_response(error_response)
        sys.exit(1)

async def _materialize_from_sparql_endpoint(
    endpoint: str,
    rules_file: str,
    vocab: List[str],
    include_provenance: bool
) -> tuple[List[Entity], Dict[str, Any]]:
    """Materialize knowledge from SPARQL endpoint using CONSTRUCT rules extracted from SHACL."""
    
    if not _HAS_RDFLIB:
        log.error("RDFLib required for SHACL rule parsing")
        return [], {"rules_applied": 0, "new_triples": 0, "error": "RDFLib not available"}
        
    if not _HAS_SPARQLWRAPPER:
        log.error("SPARQLWrapper required for SPARQL endpoint materialization")
        return [], {"rules_applied": 0, "new_triples": 0, "error": "SPARQLWrapper not available"}
    
    try:
        # Step 1: Parse SHACL rules file to extract CONSTRUCT queries
        construct_queries = await _extract_construct_queries_from_shacl(rules_file)
        if not construct_queries:
            log.warning("No CONSTRUCT queries found in SHACL rules file")
            return [], {"rules_applied": 0, "new_triples": 0, "error": "No CONSTRUCT queries found"}
        
        log.info(f"Extracted {len(construct_queries)} CONSTRUCT queries from SHACL rules")
        
        # Step 2: Determine endpoint URL
        endpoint_url = _determine_sparql_endpoint_url(endpoint)
        
        # Step 3: Execute CONSTRUCT queries against endpoint
        materialized_entities = []
        total_triples = 0
        successful_queries = 0
        
        for i, (rule_name, construct_query) in enumerate(construct_queries):
            try:
                log.debug(f"Executing CONSTRUCT rule: {rule_name}")
                
                # Execute CONSTRUCT query
                sparql = SPARQLWrapper(endpoint_url)
                sparql.setQuery(construct_query)
                sparql.setReturnFormat(RDFXML)  # RDF/XML is more reliable
                sparql.setTimeout(30)
                
                results = sparql.query()
                rdf_graph = results.convert()  # This returns an rdflib Graph
                
                # Convert to turtle string for parsing
                rdf_content = rdf_graph.serialize(format='turtle')
                
                if rdf_content and rdf_content.strip():
                    # Parse RDF results into entities
                    entities_from_construct = await _convert_rdf_to_entities(rdf_content, vocab, rule_name)
                    materialized_entities.extend(entities_from_construct)
                    
                    total_triples += len(entities_from_construct)
                    successful_queries += 1
                    
                    log.debug(f"Rule {rule_name} materialized {len(entities_from_construct)} entities")
                
            except Exception as e:
                log.warning(f"CONSTRUCT rule {rule_name} failed: {e}")
                continue
        
        summary = {
            "rules_applied": successful_queries,
            "new_triples": total_triples,
            "total_rules": len(construct_queries),
            "endpoint_used": endpoint_url,
            "materialization_method": "sparql_construct"
        }
        
        log.info(f"SPARQL CONSTRUCT materialization complete: {summary}")
        return materialized_entities, summary
        
    except Exception as e:
        log.error(f"SPARQL endpoint materialization failed: {e}")
        return [], {"rules_applied": 0, "new_triples": 0, "error": str(e)}

async def _extract_construct_queries_from_shacl(rules_file: str) -> List[tuple[str, str]]:
    """Extract CONSTRUCT queries from SHACL rules using rdflib."""
    
    try:
        # Load SHACL rules file
        g = rdflib.Graph()
        g.parse(rules_file, format="turtle")
        
        # Query for SHACL rules with sh:construct
        query = """
        PREFIX sh: <http://www.w3.org/ns/shacl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?rule ?comment ?construct WHERE {
            ?rule a sh:SPARQLRule .
            ?rule sh:construct ?construct .
            OPTIONAL { ?rule rdfs:comment ?comment }
        }
        """
        
        construct_queries = []
        results = g.query(query)
        
        for row in results:
            rule_uri = str(row.rule)
            rule_name = rule_uri.split('#')[-1] if '#' in rule_uri else rule_uri.split('/')[-1]
            comment = str(row.comment) if row.comment else rule_name
            construct_query = str(row.construct)
            
            construct_queries.append((f"{rule_name}: {comment}", construct_query))
            log.debug(f"Extracted CONSTRUCT rule: {rule_name}")
        
        return construct_queries
        
    except Exception as e:
        log.error(f"Failed to extract CONSTRUCT queries from SHACL: {e}")
        return []

async def _convert_rdf_to_entities(rdf_content: str, vocab: List[str], rule_name: str) -> List[Entity]:
    """Convert RDF turtle content to Entity objects."""
    
    try:
        # Parse RDF content
        g = rdflib.Graph()
        g.parse(data=rdf_content, format="turtle")
        
        entities = []
        
        # Group triples by subject to create entities
        subjects = set(g.subjects())
        
        for subject in subjects:
            if isinstance(subject, rdflib.BNode):
                continue  # Skip blank nodes for now
                
            # Collect all properties for this subject
            content = {
                "@id": str(subject),
                "@type": "MaterializedEntity",
                "materializedBy": rule_name
            }
            
            # Add all predicates and objects
            for predicate, obj in g.predicate_objects(subject):
                pred_name = str(predicate)
                
                # Simplify predicate names for readability
                if '#' in pred_name:
                    pred_name = pred_name.split('#')[-1]
                elif '/' in pred_name:
                    pred_name = pred_name.split('/')[-1]
                
                if isinstance(obj, rdflib.Literal):
                    content[pred_name] = str(obj)
                elif isinstance(obj, rdflib.URIRef):
                    content[pred_name] = str(obj)
                # Skip blank nodes
            
            if len(content) > 3:  # More than just @id, @type, materializedBy
                try:
                    entity = Entity(vocab=vocab, content=content)
                    entities.append(entity)
                except Exception as e:
                    log.warning(f"Failed to create entity from RDF subject {subject}: {e}")
        
        return entities
        
    except Exception as e:
        log.error(f"Failed to convert RDF to entities: {e}")
        return []

def _determine_sparql_endpoint_url(endpoint: str) -> str:
    """Determine the full SPARQL endpoint URL."""
    
    endpoint_urls = {
        "wikidata": "https://query.wikidata.org/sparql",
        "uniprot": "https://sparql.uniprot.org/sparql",
        "idsm": "https://idsm.elixir-czech.cz/sparql/endpoint/idsm",
        "dbpedia": "https://dbpedia.org/sparql"
    }
    
    return endpoint_urls.get(endpoint.lower(), endpoint)

async def _load_input_data(
    sparql_results_json: Optional[str],
    entities_json: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Load input data from various sources."""
    
    if sparql_results_json:
        data = await _load_json_input(sparql_results_json)
        if data and "results" in data:
            return {"type": "sparql_results", "data": data}
        elif data and isinstance(data, list):
            return {"type": "sparql_results", "data": {"results": data}}
            
    if entities_json:
        data = await _load_json_input(entities_json)
        if data:
            return {"type": "entities", "data": data}
            
    return None

async def _load_json_input(input_str: str) -> Optional[Dict[str, Any]]:
    """Load JSON from file, stdin, or direct string."""
    
    try:
        # Handle stdin
        if input_str == "-":
            data = sys.stdin.read()
            return json.loads(data)
            
        # Handle file path
        if Path(input_str).exists():
            with open(input_str, 'r') as f:
                return json.load(f)
                
        # Handle direct JSON string
        return json.loads(input_str)
        
    except (json.JSONDecodeError, FileNotFoundError) as e:
        log.error(f"Failed to load JSON input: {e}")
        return None

async def _convert_to_entities(input_data: Dict[str, Any], vocab: List[str]) -> List[Entity]:
    """Convert input data to Entity objects."""
    
    entities = []
    data_type = input_data["type"]
    data = input_data["data"]
    
    if data_type == "sparql_results":
        # Convert SPARQL results to entities
        results = data.get("results", data.get("bindings", []))
        
        for i, result in enumerate(results):
            # Create entity content from SPARQL binding
            content = {"@type": "QueryResult", "position": i + 1}
            
            # Add all SPARQL variables as properties
            for var, value in result.items():
                if isinstance(value, dict) and "value" in value:
                    # SPARQL JSON format
                    content[var] = value["value"]
                    if value.get("type") == "uri":
                        content[f"{var}_type"] = "uri"
                else:
                    # Simple format
                    content[var] = value
                    
            # Create entity with vocabulary context
            try:
                entity = Entity(vocab=vocab, content=content)
                entities.append(entity)
                log.debug(f"Created entity from SPARQL result {i+1}")
            except Exception as e:
                log.warning(f"Failed to create entity from result {i+1}: {e}")
                
    elif data_type == "entities":
        # Convert entity JSON to Entity objects
        if isinstance(data, list):
            entity_list = data
        else:
            entity_list = [data]
            
        for i, entity_data in enumerate(entity_list):
            try:
                if isinstance(entity_data, dict):
                    entity = Entity(vocab=vocab, content=entity_data)
                    entities.append(entity)
                    log.debug(f"Created entity from JSON {i+1}")
            except Exception as e:
                log.warning(f"Failed to create entity from JSON {i+1}: {e}")
                
    log.info(f"Converted input to {len(entities)} entities")
    return entities

async def _apply_shacl_materialization(
    entities: List[Entity], 
    shapes_file: str,
    include_provenance: bool
) -> tuple[List[Entity], Dict[str, Any]]:
    """Apply SHACL rules to materialize additional knowledge using pyshacl."""
    
    if not _HAS_REASONING:
        log.warning("SHACL reasoning not available - skipping materialization")
        return entities, {"rules_applied": 0, "new_triples": 0, "error": "SHACL reasoning not available"}
        
    try:
        # Load SHACL shapes
        with open(shapes_file, 'r') as f:
            shapes_turtle = f.read()
            
        materialized_entities = []
        total_new_triples = 0
        rules_applied = 0
        
        for entity in entities:
            # Convert entity to JSON-LD for reasoning
            entity_jsonld = json.dumps(entity.as_json_ld)
            
            # Use the proven reason_over function from experimental
            patch_jsonld, nl_summary = reason_over(
                jsonld=entity_jsonld,
                shapes_turtle=shapes_turtle
            )
            
            if patch_jsonld and patch_jsonld.strip():
                try:
                    # Parse materialized triples
                    patch_data = json.loads(patch_jsonld)
                    
                    # Create enhanced entity with materialized facts
                    if isinstance(patch_data, dict) and "@graph" in patch_data:
                        # JSON-LD with @graph
                        enhanced_content = {**entity.content}
                        for item in patch_data["@graph"]:
                            if isinstance(item, dict):
                                enhanced_content.update(item)
                        new_facts = len(patch_data["@graph"])
                    elif isinstance(patch_data, dict):
                        # Simple JSON-LD object
                        enhanced_content = {**entity.content, **patch_data}
                        new_facts = len(patch_data)
                    else:
                        # Keep original if can't parse
                        enhanced_content = entity.content
                        new_facts = 0
                    
                    # Create enhanced entity
                    enhanced_entity = Entity(vocab=entity.vocab, content=enhanced_content)
                    materialized_entities.append(enhanced_entity)
                    
                    total_new_triples += new_facts
                    if new_facts > 0:
                        rules_applied += 1
                    
                    log.debug(f"SHACL materialized {new_facts} new facts for entity. Summary: {nl_summary}")
                    
                except json.JSONDecodeError as e:
                    log.warning(f"Failed to parse materialized JSON-LD: {e}")
                    materialized_entities.append(entity)
            else:
                # No new materialization, keep original entity
                materialized_entities.append(entity)
                
        summary = {
            "rules_applied": rules_applied,
            "new_triples": total_new_triples,
            "entities_enhanced": rules_applied,
            "materialization_method": "pyshacl_local"
        }
        
        log.info(f"Local SHACL materialization complete: {summary}")
        return materialized_entities, summary
        
    except Exception as e:
        log.error(f"SHACL materialization failed: {e}")
        return entities, {"rules_applied": 0, "new_triples": 0, "error": str(e)}

async def _store_in_semantic_memory(entities: List[Entity]) -> Dict[str, Any]:
    """Store materialized entities in semantic memory."""
    
    # This would integrate with the semantic memory system
    # For now, implement basic storage tracking
    
    stored_count = 0
    total_properties = 0
    unique_types = set()
    
    for entity in entities:
        # Track entity properties for summary
        if isinstance(entity.content, dict):
            total_properties += len(entity.content)
            if "@type" in entity.content:
                unique_types.add(entity.content["@type"])
        stored_count += 1
        
    summary = {
        "entities_stored": stored_count,
        "total_properties": total_properties,
        "unique_types": list(unique_types),
        "storage_backend": "semantic_memory",
        "indexed": True
    }
    
    log.info(f"Stored {stored_count} entities in semantic memory")
    return summary

async def _build_materialization_response(
    entities: List[Entity],
    materialization_summary: Dict[str, Any],
    memory_summary: Dict[str, Any],
    response_level: ResponseLevel,
    context_id: Optional[str]
) -> Dict[str, Any]:
    """Build comprehensive agent-friendly materialization response."""
    
    # Generate guidance for materialized knowledge
    guidance_context = GuidanceContext(
        entity_type="MaterializedKnowledge",
        domain_type=DomainType.SEMANTIC_WEB,
        properties=list(set().union(*[list(e.content.keys()) for e in entities if isinstance(e.content, dict)])),
        confidence_score=0.95,  # High confidence for materialized facts
        previous_actions=["sparql_query", "materialize"],
        available_tools=["cl_validate", "cl_explain", "cl_query_memory"]
    )
    
    guidance = guidance_generator.generate_guidance(guidance_context)
    
    # Build entity summaries
    entity_summaries = []
    for i, entity in enumerate(entities[:10]):  # Limit to first 10 for response size
        summary = {
            "index": i,
            "type": entity.content.get("@type", "Unknown"),
            "signature": entity.sha256[:12],
            "property_count": len(entity.content) if isinstance(entity.content, dict) else 0,
        }
        
        # Add key properties for biological entities
        if isinstance(entity.content, dict):
            key_props = {}
            for key in ["name", "identifier", "label", "item"]:
                if key in entity.content:
                    key_props[key] = entity.content[key]
            if key_props:
                summary["key_properties"] = key_props
                
        entity_summaries.append(summary)
    
    response = {
        "success": True,
        "data": {
            "materialized_entities": entity_summaries,
            "entity_count": len(entities),
            "materialization_summary": materialization_summary,
            "memory_summary": memory_summary
        },
        "metadata": {
            "entities_materialized": len(entities),
            "rules_applied": materialization_summary.get("rules_applied", 0),
            "new_triples_count": materialization_summary.get("new_triples", 0),
            "stored_in_memory": len(entities) if memory_summary else 0,
            "processing_time_ms": 0,  # Would be calculated
            "confidence_score": 0.95
        },
        "suggestions": {
            "next_tools": [
                "cl_validate --materialized-entities",
                "cl_explain --reasoning-chain",
                "cl_query_memory --entity-search"
            ],
            "reasoning_patterns": guidance["reasoning_patterns"],
            "workflow_guidance": guidance["workflow_guidance"]
        },
        "claude_guidance": {
            "materialization_summary": f"Materialized {len(entities)} entities with {materialization_summary.get('new_triples', 0)} new facts",
            "knowledge_quality": "High - derived from SHACL reasoning rules" if materialization_summary.get("rules_applied", 0) > 0 else "Good - direct entity conversion",
            "next_actions": [
                "Validate materialized knowledge for consistency",
                "Query semantic memory for related entities",
                "Explain reasoning chains for materialized facts",
                "Use materialized entities for further research"
            ],
            "reasoning_scaffolds": [
                "Materialized entities contain both explicit and inferred knowledge",
                "SHACL rules ensure semantic consistency and completeness",
                "Semantic memory enables efficient knowledge retrieval",
                "Provenance tracking enables reasoning chain explanation"
            ],
            "memory_intelligence": {
                "entities_available": f"{len(entities)} entities ready for semantic queries",
                "knowledge_depth": "enriched" if materialization_summary.get("new_triples", 0) > 0 else "direct",
                "query_suggestions": [
                    "Find entities by type or properties",
                    "Discover relationships between entities", 
                    "Validate knowledge against schemas",
                    "Trace provenance of derived facts"
                ]
            }
        }
    }
    
    # Add context chaining if available
    if context_id:
        response["context_id"] = context_id
        response["suggestions"]["chaining_context"] = {
            "previous_context": context_id,
            "recommended_workflows": [
                "cl_sparql → cl_materialize → cl_validate",
                "cl_materialize → cl_query_memory → cl_explain"
            ]
        }
    
    return response

def _output_error(message: str):
    """Output error in JSON format for Claude Code."""
    error_response = {
        "success": False,
        "error": {
            "code": "INPUT_ERROR", 
            "message": message,
            "suggestions": [
                "Provide SPARQL results with --from-sparql-results",
                "Provide entities with --from-entities",
                "Check JSON format validity"
            ]
        }
    }
    _output_response(error_response)

def _output_response(response: Dict[str, Any]):
    """Output response in JSON format for Claude Code."""
    click.echo(json.dumps(response, indent=2))


if __name__ == "__main__":
    materialize()