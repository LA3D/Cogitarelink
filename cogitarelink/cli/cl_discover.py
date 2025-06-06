"""cl_discover: Scientific resource discovery with auto-materialization.

Foundation CLI tool demonstrating integration of:
- Discovery engine with multi-strategy resolution
- Agent intelligence patterns with structured responses
- Discovery-first guardrails for semantic queries
- Context chaining for workflow composition
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Optional, List, Dict, Any

import click

from ..intelligence.discovery_engine import discovery_engine, DiscoveryResult
from ..intelligence.response_manager import response_manager, ResponseLevel
from ..intelligence.guidance_generator import guidance_generator, GuidanceContext, DomainType
from ..intelligence.schema_discovery import schema_discovery_engine
from ..core.entity import Entity
from ..core.debug import get_logger

log = get_logger("cl_discover")

@click.command()
@click.argument('resource_identifier', required=True)
@click.option('--domains', multiple=True, help='Domain hints (biology, semantic_web, geospatial)')
@click.option('--endpoint', help='Discover SPARQL endpoint schema instead of resource')
@click.option('--method', default='auto', type=click.Choice(['auto', 'introspection', 'void', 'documentation']),
              help='Schema discovery method for endpoints')
@click.option('--context-id', help='Context ID for tool chaining')
@click.option('--enhance', is_flag=True, help='Use enhanced discovery for richer metadata')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
@click.option('--materialize', is_flag=True, help='Auto-materialize discovered resource as Entity')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
def discover(
    resource_identifier: str,
    domains: List[str],
    endpoint: Optional[str],
    method: str,
    context_id: Optional[str],
    enhance: bool,
    level: str,
    materialize: bool,
    output_format: str
):
    """
    Discover metadata about a scientific resource or SPARQL endpoint schema.
    
    Resource Discovery Examples:
        cl_discover "P01308" --domains biology
        cl_discover "insulin" --domains biology --enhance --materialize
        cl_discover "http://schema.org/Protein" --level full
        cl_discover "UniProt:P01308" --context-id ctx_abc123 --materialize
        
    Endpoint Schema Discovery Examples:
        cl_discover wikidata --endpoint wikidata --method documentation
        cl_discover wikipathways --endpoint wikipathways --method introspection
        cl_discover uniprot --endpoint uniprot --method auto
    """
    asyncio.run(_discover_async(
        resource_identifier, domains, endpoint, method, context_id, enhance, 
        level, materialize, output_format
    ))

async def _discover_async(
    resource_identifier: str,
    domains: List[str],
    endpoint: Optional[str],
    method: str,
    context_id: Optional[str],
    enhance: bool,
    level: str,
    materialize: bool,
    output_format: str
):
    """Async implementation of discovery with endpoint schema and resource intelligence."""
    
    try:
        # Check if this is endpoint schema discovery
        if endpoint:
            log.info(f"Discovering schema for endpoint: {endpoint} using method: {method}")
            await _endpoint_schema_discovery(
                endpoint, method, level, output_format
            )
            return
        
        log.info(f"Discovering resource: {resource_identifier}")
        
        # Convert level string to ResponseLevel enum
        response_level = ResponseLevel(level)
        
        # Execute discovery with intelligence patterns
        discovery_result = await discovery_engine.discover_resource(
            resource_identifier=resource_identifier,
            domain_hints=list(domains) if domains else None,
            context_id=context_id
        )
        
        # Build comprehensive response
        if discovery_result.success and discovery_result.metadata:
            
            # Auto-materialize if requested
            materialized_entity = None
            if materialize:
                materialized_entity = await _materialize_discovery(discovery_result)
            
            # Build agent-friendly response
            response = _build_agent_response(
                discovery_result, 
                materialized_entity, 
                response_level,
                enhance
            )
            
        else:
            # Handle discovery failure with educational error
            response = _build_error_response(discovery_result, resource_identifier, domains)
        
        # Apply response management (truncation/optimization)
        if response_level != ResponseLevel.FULL:
            final_response, truncation_metadata = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
        
        # Output results
        if output_format == 'json':
            click.echo(json.dumps(final_response, indent=2))
        else:
            _print_human_readable(final_response, discovery_result)
            
    except Exception as e:
        log.error(f"Discovery failed: {e}")
        error_response = {
            "success": False,
            "error": {
                "code": "DISCOVERY_EXCEPTION",
                "message": str(e),
                "recovery_plan": {
                    "next_tool": "cl_discover",
                    "parameters": {
                        "resource_identifier": resource_identifier,
                        "enhance": True,
                        "domains": list(domains) if domains else ["general"]
                    },
                    "reasoning": "Retry with enhanced discovery and domain hints"
                }
            }
        }
        click.echo(json.dumps(error_response, indent=2))
        sys.exit(1)

async def _materialize_discovery(discovery_result: DiscoveryResult) -> Optional[Entity]:
    """Materialize discovery as an Entity with intelligence patterns."""
    
    if not discovery_result.metadata:
        return None
    
    try:
        # Detect appropriate vocabularies from discovery
        vocabs = []
        if discovery_result.metadata.domain_context:
            for domain in discovery_result.metadata.domain_context:
                if domain in ["biology", "biological"]:
                    vocabs.append("bioschemas")
                elif domain in ["semantic_web", "schema"]:
                    vocabs.append("schema")
        
        if not vocabs:
            vocabs = ["schema"]  # Default vocabulary
        
        # Build entity content from discovery metadata
        content = {
            "@type": discovery_result.metadata.resource_type.title(),
            "name": discovery_result.metadata.resource_id,
            "identifier": discovery_result.metadata.resource_id
        }
        
        # Add resolution URLs if available
        if discovery_result.metadata.resolution_urls:
            content["sameAs"] = discovery_result.metadata.resolution_urls
        
        # Create materialized entity
        entity = Entity(
            id=f"urn:cogitarelink:discovered:{discovery_result.metadata.resource_id}",
            vocab=vocabs,
            content=content,
            meta={
                "discovery_strategy": discovery_result.metadata.discovery_strategy.value,
                "confidence_score": discovery_result.metadata.confidence_score,
                "discovery_timestamp": "auto-generated"
            }
        )
        
        log.info(f"Materialized entity with vocab {vocabs} and signature {entity.sha256[:8]}...")
        return entity
        
    except Exception as e:
        log.error(f"Materialization failed: {e}")
        return None

def _build_agent_response(
    discovery_result: DiscoveryResult,
    materialized_entity: Optional[Entity],
    response_level: ResponseLevel,
    enhance: bool
) -> dict:
    """Build comprehensive agent-friendly response."""
    
    metadata = discovery_result.metadata
    
    # Base response structure
    response = {
        "success": True,
        "data": {
            "discovery": metadata.as_dict(),
            "resource_identifier": metadata.resource_id,
            "domain_type": metadata.domain_context[0] if metadata.domain_context else "general",
            "confidence_score": metadata.confidence_score
        },
        "metadata": {
            "discovery_strategy": metadata.discovery_strategy.value,
            "domain_context": metadata.domain_context,
            "resolution_urls_count": len(metadata.resolution_urls),
            "validation_patterns_count": len(metadata.validation_patterns),
            "reasoning_hints_count": len(metadata.reasoning_hints)
        },
        "suggestions": discovery_result.suggestions
    }
    
    # Add materialized entity if available
    if materialized_entity:
        # Get enhanced entity response with intelligence patterns
        entity_response = materialized_entity.to_agent_response(response_level)
        response["data"]["materialized_entity"] = entity_response["data"]
        response["data"]["entity_signature"] = materialized_entity.sha256
        
        # Merge entity suggestions with discovery suggestions
        if "suggestions" in entity_response:
            response["suggestions"].update(entity_response["suggestions"])
    
    # Add context chaining
    if discovery_result.context_id:
        response["context_id"] = discovery_result.context_id
        response["suggestions"]["chaining_context"] = {
            "use_context_id": discovery_result.context_id,
            "recommended_next_tools": [
                f"cl_sparql --context-id {discovery_result.context_id}",
                f"cl_materialize --context-id {discovery_result.context_id}",
                f"cl_validate --context-id {discovery_result.context_id}"
            ]
        }
    
    # Add discovery-specific guidance
    response["claude_guidance"] = {
        "discovery_summary": f"Discovered {metadata.resource_type} '{metadata.resource_id}' with {metadata.confidence_score:.1f} confidence",
        "domain_intelligence": f"Resource appears to be in {metadata.domain_context[0] if metadata.domain_context else 'general'} domain",
        "next_actions": [
            "Use materialized entity for semantic queries" if materialized_entity else "Consider materialization for entity-based workflows",
            f"Explore {metadata.resource_type} relationships via SPARQL",
            "Validate discovery with authoritative sources"
        ],
        "reasoning_scaffolds": metadata.reasoning_hints[:3],
        "workflow_guidance": [
            "1. Verify discovery metadata accuracy",
            "2. Materialize as Entity for semantic processing", 
            "3. Query for related resources",
            "4. Validate findings with external sources"
        ]
    }
    
    return response

def _build_error_response(
    discovery_result: DiscoveryResult,
    resource_identifier: str,
    domains: List[str]
) -> dict:
    """Build educational error response with recovery guidance."""
    
    return {
        "success": False,
        "error": discovery_result.error,
        "suggestions": discovery_result.suggestions,
        "claude_guidance": {
            "error_analysis": f"Discovery failed for '{resource_identifier}'",
            "recovery_strategy": "Try enhanced discovery with domain hints",
            "next_actions": [
                "Add domain hints with --domains flag",
                "Use --enhance flag for richer discovery methods",
                "Verify resource identifier format",
                "Check network connectivity for remote resources"
            ],
            "example_patterns": [
                "Biological: 'P01308', 'UniProt:P01308', 'insulin'",
                "Semantic: 'http://schema.org/Protein', 'schema:Protein'",
                "Geographic: 'Paris', 'Q90' (Wikidata)"
            ]
        }
    }

def _print_human_readable(response: dict, discovery_result: DiscoveryResult):
    """Print human-readable summary for terminal users."""
    
    if response["success"]:
        data = response["data"]
        print(f"🔍 Discovery Result for '{data['resource_identifier']}'")
        print(f"   Domain: {data['domain_type']}")
        print(f"   Confidence: {data['confidence_score']:.1f}")
        print(f"   Strategy: {response['metadata']['discovery_strategy']}")
        
        if "materialized_entity" in data:
            print(f"   ✅ Materialized as Entity (signature: {data['entity_signature'][:8]}...)")
        
        suggestions = response.get("suggestions", {})
        if "next_tools" in suggestions:
            print(f"\n💡 Suggested next steps:")
            for i, tool in enumerate(suggestions["next_tools"][:3], 1):
                print(f"   {i}. {tool}")
                
    else:
        error = response["error"]
        print(f"❌ Discovery failed: {error['message']}")
        if "recovery_plan" in error:
            print(f"💡 Try: {error['recovery_plan']['reasoning']}")


async def _endpoint_schema_discovery(
    endpoint: str,
    method: str,
    level: str,
    output_format: str
):
    """Discover SPARQL endpoint schema with agent intelligence."""
    
    start_time = time.time()
    
    try:
        log.info(f"Starting schema discovery for {endpoint}")
        
        # Execute schema discovery
        schema = await schema_discovery_engine.discover_schema(
            endpoint=endpoint,
            method=method,
            include_examples=True
        )
        
        # Generate agent guidance
        guidance = schema_discovery_engine.generate_agent_guidance(schema)
        
        # Build comprehensive response
        execution_time = int((time.time() - start_time) * 1000)
        
        response = {
            "success": True,
            "data": {
                "endpoint": schema.endpoint,
                "schema_info": {
                    "classes": schema.classes,
                    "properties": schema.properties,
                    "prefixes": schema.prefixes,
                    "statistics": schema.statistics
                },
                "discovery_method": schema.discovery_method,
                "confidence_score": schema.confidence_score,
                "examples": schema.examples
            },
            "metadata": {
                "execution_time_ms": execution_time,
                "classes_discovered": len(schema.classes),
                "properties_discovered": len(schema.properties),
                "prefixes_available": len(schema.prefixes),
                "examples_generated": len(schema.examples)
            },
            "guidance": guidance,
            "suggestions": {
                "immediate_next_steps": [
                    f"Try example queries against {schema.endpoint}",
                    f"Use discovered prefixes in custom queries",
                    "Cross-reference with other biological databases",
                    "Materialize interesting query results"
                ],
                "sparql_patterns": [
                    f"cl_wikidata sparql \"<query>\" --endpoint {schema.endpoint}",
                    f"cl_materialize --from-sparql-results",
                    "cl_wikidata endpoints (list all available endpoints)"
                ]
            },
            "claude_guidance": {
                "schema_summary": f"Discovered {len(schema.classes)} classes and {len(schema.properties)} properties from {schema.endpoint}",
                "endpoint_intelligence": guidance.get("biological_intelligence", []),
                "query_strategy": [
                    f"Use {schema.discovery_method} discovery results for informed querying",
                    f"Confidence level: {schema.confidence_score:.1f} - {'High' if schema.confidence_score > 0.7 else 'Medium' if schema.confidence_score > 0.4 else 'Low'} reliability",
                    f"Best for: {guidance.get('biological_intelligence', ['General SPARQL queries'])[0] if guidance.get('biological_intelligence') else 'General SPARQL queries'}"
                ],
                "workflow_recommendations": guidance.get("next_steps", [])
            }
        }
        
        # Apply response management for level
        response_level = ResponseLevel(level)
        if response_level != ResponseLevel.FULL:
            final_response, _ = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
        
        # Output response
        if output_format == 'json':
            click.echo(json.dumps(final_response, indent=2))
        else:
            _print_schema_human_readable(final_response, schema)
            
    except Exception as e:
        log.error(f"Schema discovery failed for {endpoint}: {e}")
        error_response = {
            "success": False,
            "error": {
                "code": "SCHEMA_DISCOVERY_FAILED",
                "message": f"Schema discovery failed for {endpoint}: {str(e)}",
                "endpoint": endpoint,
                "method": method,
                "suggestions": [
                    "Try a different discovery method (auto, introspection, void, documentation)",
                    "Check endpoint accessibility and network connectivity",
                    "Verify endpoint URL if using custom endpoint",
                    "Use 'cl_wikidata endpoints' to see available endpoints"
                ]
            }
        }
        
        if output_format == 'json':
            click.echo(json.dumps(error_response, indent=2))
        else:
            print(f"❌ Schema discovery failed for {endpoint}: {str(e)}")
            print("💡 Try: cl_wikidata endpoints to see available endpoints")


def _print_schema_human_readable(response: Dict[Any, Any], schema):
    """Print human-readable schema discovery summary."""
    
    if response["success"]:
        data = response["data"]
        print(f"🔍 Schema Discovery for '{data['endpoint']}'")
        print(f"   Method: {data['discovery_method']}")
        print(f"   Confidence: {data['confidence_score']:.2f}")
        print(f"   Classes: {len(data['schema_info']['classes'])}")
        print(f"   Properties: {len(data['schema_info']['properties'])}")
        print(f"   Prefixes: {len(data['schema_info']['prefixes'])}")
        
        if data.get('examples'):
            print(f"\n📝 Example Queries:")
            for i, example in enumerate(data['examples'][:3], 1):
                print(f"   {i}. {example}")
        
        guidance = response.get("guidance", {})
        if guidance.get("biological_intelligence"):
            print(f"\n🧬 Biological Intelligence:")
            for insight in guidance["biological_intelligence"][:3]:
                print(f"   • {insight}")
        
        suggestions = response.get("suggestions", {})
        if suggestions.get("immediate_next_steps"):
            print(f"\n💡 Next Steps:")
            for step in suggestions["immediate_next_steps"][:3]:
                print(f"   → {step}")


if __name__ == "__main__":
    discover()