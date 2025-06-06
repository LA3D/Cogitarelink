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
from typing import Optional, List

import click

from ..intelligence.discovery_engine import discovery_engine, DiscoveryResult
from ..intelligence.response_manager import response_manager, ResponseLevel
from ..intelligence.guidance_generator import guidance_generator, GuidanceContext, DomainType
from ..core.entity import Entity
from ..core.debug import get_logger

log = get_logger("cl_discover")

@click.command()
@click.argument('resource_identifier', required=True)
@click.option('--domains', multiple=True, help='Domain hints (biology, semantic_web, geospatial)')
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
    context_id: Optional[str],
    enhance: bool,
    level: str,
    materialize: bool,
    output_format: str
):
    """
    Discover metadata about a scientific resource with agent intelligence.
    
    Examples:
        cl_discover "P01308" --domains biology
        cl_discover "insulin" --domains biology --enhance --materialize
        cl_discover "http://schema.org/Protein" --level full
        cl_discover "UniProt:P01308" --context-id ctx_abc123 --materialize
    """
    asyncio.run(_discover_async(
        resource_identifier, domains, context_id, enhance, 
        level, materialize, output_format
    ))

async def _discover_async(
    resource_identifier: str,
    domains: List[str],
    context_id: Optional[str],
    enhance: bool,
    level: str,
    materialize: bool,
    output_format: str
):
    """Async implementation of discovery with full intelligence integration."""
    
    try:
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

if __name__ == "__main__":
    discover()