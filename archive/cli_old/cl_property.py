"""
cl_property: Universal property analysis with vocabulary intelligence

Synthesis of wikidata-mcp universal resolution with cogitarelink vocabulary management.
Provides intelligent property analysis combining Wikidata metadata discovery,
vocabulary registry resolution, and cross-domain reasoning suggestions.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Optional, List, Dict, Any, Union

import click

from ..adapters.wikidata_client import WikidataClient
from ..adapters.multi_sparql_client import MultiSparqlClient
from ..core.entity import Entity
from ..core.debug import get_logger
from ..vocab.registry import registry
from ..vocab.composer import composer
from ..intelligence.guidance_generator import guidance_generator, GuidanceContext, DomainType
from ..intelligence.response_manager import response_manager, ResponseLevel

log = get_logger("cl_property")


@click.command()
@click.argument('property_identifier', required=True)
@click.option('--context-vocabs', multiple=True, 
              help='Vocabulary contexts to include: schema, bioschemas, foaf, etc.')
@click.option('--include-usage', is_flag=True, default=True,
              help='Include property usage statistics and patterns')
@click.option('--include-mappings', is_flag=True, default=True,
              help='Include cross-vocabulary property mappings')
@click.option('--resolve-conflicts', is_flag=True, default=True,
              help='Apply collision resolution for vocabulary conflicts')
@click.option('--endpoint', default='wikidata',
              help='Primary SPARQL endpoint for property analysis')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
def property(
    property_identifier: str,
    context_vocabs: List[str],
    include_usage: bool,
    include_mappings: bool,
    resolve_conflicts: bool,
    endpoint: str,
    level: str,
    output_format: str
):
    """
    Universal property analysis combining Wikidata intelligence with vocabulary management.
    
    Examples:
        cl_property P31 --context-vocabs schema,bioschemas
        cl_property "rdf:type" --include-usage --include-mappings
        cl_property "schema:name" --resolve-conflicts --endpoint wikidata
        cl_property P352 --context-vocabs bioschemas --level full
    """
    asyncio.run(_property_async(
        property_identifier, list(context_vocabs), include_usage, include_mappings,
        resolve_conflicts, endpoint, level, output_format
    ))


async def _property_async(
    property_identifier: str,
    context_vocabs: List[str],
    include_usage: bool,
    include_mappings: bool,
    resolve_conflicts: bool,
    endpoint: str,
    level: str,
    output_format: str
):
    """Async property analysis with vocabulary intelligence."""
    
    start_time = time.time()
    
    try:
        log.info(f"Analyzing property: {property_identifier}")
        
        # Validate property identifier format
        if not _is_valid_property_identifier(property_identifier):
            _output_error(
                f"Invalid property identifier format: {property_identifier}",
                "Expected formats: P123, schema:name, rdf:type, or full URI",
                output_format
            )
            return
        
        # Initialize clients
        wikidata_client = WikidataClient(timeout=30)
        sparql_client = MultiSparqlClient(timeout=30)
        
        # 1. Universal Property Discovery (wikidata-mcp pattern)
        property_metadata = await _discover_property_metadata(
            property_identifier, wikidata_client, sparql_client, endpoint
        )
        
        # 2. Vocabulary Registry Resolution (cogitarelink pattern)
        vocab_context = await _resolve_vocabulary_context(
            property_identifier, context_vocabs, resolve_conflicts
        )
        
        # 3. Property Usage Analysis
        usage_analysis = {}
        if include_usage:
            usage_analysis = await _analyze_property_usage(
                property_identifier, sparql_client, endpoint
            )
        
        # 4. Cross-Vocabulary Mappings
        cross_mappings = {}
        if include_mappings:
            cross_mappings = await _analyze_cross_vocabulary_mappings(
                property_identifier, vocab_context
            )
        
        # 5. Generate Cross-Domain Intelligence
        domain_intelligence = await _generate_property_intelligence(
            property_identifier, property_metadata, vocab_context, usage_analysis
        )
        
        # Build comprehensive response
        response = await _build_property_response(
            property_identifier, property_metadata, vocab_context, usage_analysis,
            cross_mappings, domain_intelligence, start_time, level
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
        log.error(f"Property analysis failed: {e}")
        _output_error(f"Property analysis failed: {str(e)}", "Check property identifier and network connectivity", output_format)
        sys.exit(1)


async def _discover_property_metadata(
    property_identifier: str,
    wikidata_client: WikidataClient,
    sparql_client: MultiSparqlClient,
    endpoint: str
) -> Dict[str, Any]:
    """Discover property metadata using universal resolver pattern."""
    
    metadata = {
        "identifier": property_identifier,
        "type": "unknown",
        "domain": [],
        "range": [],
        "description": "",
        "labels": {},
        "wikidata_equivalent": None
    }
    
    # Handle Wikidata property IDs (P123 format)
    if property_identifier.startswith('P') and property_identifier[1:].isdigit():
        try:
            # Get property data from Wikidata
            prop_data = await wikidata_client.get_entities([property_identifier])
            if property_identifier in prop_data.get('entities', {}):
                entity_data = prop_data['entities'][property_identifier]
                
                metadata.update({
                    "type": "wikidata_property",
                    "description": entity_data.get('descriptions', {}).get('en', {}).get('value', ''),
                    "labels": {
                        lang: label.get('value', '') 
                        for lang, label in entity_data.get('labels', {}).items()
                    },
                    "wikidata_url": f"https://www.wikidata.org/wiki/Property:{property_identifier}",
                    "wikidata_equivalent": property_identifier
                })
                
                # Extract domain and range from claims if available
                claims = entity_data.get('claims', {})
                if 'P1629' in claims:  # subject item of this property
                    metadata["domain"] = [
                        claim['mainsnak']['datavalue']['value']['id']
                        for claim in claims['P1629'] 
                        if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']
                    ]
        
        except Exception as e:
            log.warning(f"Failed to get Wikidata metadata for {property_identifier}: {e}")
    
    # Handle prefixed properties (schema:name, rdf:type, etc.)
    elif ':' in property_identifier:
        prefix, local_name = property_identifier.split(':', 1)
        metadata.update({
            "type": "prefixed_property",
            "prefix": prefix,
            "local_name": local_name,
            "namespace_uri": _resolve_namespace_uri(prefix)
        })
        
        # Try to find Wikidata equivalent
        equivalent = await _find_wikidata_equivalent(property_identifier, sparql_client)
        if equivalent:
            metadata["wikidata_equivalent"] = equivalent
    
    # Handle full URIs
    elif property_identifier.startswith('http'):
        metadata.update({
            "type": "full_uri",
            "uri": property_identifier,
            "namespace": _extract_namespace(property_identifier),
            "local_name": _extract_local_name(property_identifier)
        })
    
    return metadata


async def _resolve_vocabulary_context(
    property_identifier: str,
    context_vocabs: List[str],
    resolve_conflicts: bool
) -> Dict[str, Any]:
    """Resolve vocabulary context using cogitarelink registry and composer."""
    
    vocab_context = {
        "requested_vocabularies": context_vocabs,
        "resolved_context": {},
        "conflicts_detected": [],
        "collision_resolution": {}
    }
    
    if not context_vocabs:
        # Auto-detect relevant vocabularies based on property
        context_vocabs = _auto_detect_vocabularies(property_identifier)
        vocab_context["auto_detected"] = True
        vocab_context["requested_vocabularies"] = context_vocabs
    
    try:
        # Check vocabulary registry for property mappings
        registry_mappings = {}
        for vocab in context_vocabs:
            try:
                vocab_entry = registry.resolve(vocab)
                registry_mappings[vocab] = {
                    "prefix": vocab_entry.prefix,
                    "features": list(vocab_entry.features),
                    "tags": list(vocab_entry.tags)
                }
            except KeyError:
                log.warning(f"Vocabulary {vocab} not found in registry")
        
        vocab_context["registry_mappings"] = registry_mappings
        
        # Compose context with collision detection
        if len(context_vocabs) > 1:
            composed_context = composer.compose(context_vocabs)
            vocab_context["resolved_context"] = composed_context
            
            # Check for conflicts (simplified for now)
            conflicts = []  # Placeholder - would use composer.detect_conflicts
            if conflicts and resolve_conflicts:
                # Placeholder for collision resolution
                vocab_context["collision_resolution"] = {}
                vocab_context["conflicts_detected"] = conflicts
        else:
            # Single vocabulary - simple resolution
            if context_vocabs:
                try:
                    vocab_entry = registry.resolve(context_vocabs[0])
                    vocab_context["resolved_context"] = {
                        "@context": vocab_entry.context_payload()
                    }
                except KeyError:
                    vocab_context["resolved_context"] = {}
        
    except Exception as e:
        log.warning(f"Vocabulary context resolution failed: {e}")
        vocab_context["error"] = str(e)
    
    return vocab_context


async def _analyze_property_usage(
    property_identifier: str,
    sparql_client: MultiSparqlClient,
    endpoint: str
) -> Dict[str, Any]:
    """Analyze property usage patterns across endpoints."""
    
    usage_analysis = {
        "total_usage_count": 0,
        "sample_subjects": [],
        "sample_objects": [],
        "usage_patterns": [],
        "endpoints_analyzed": [endpoint]
    }
    
    try:
        # Convert property identifier to appropriate format for endpoint
        sparql_property = _convert_property_for_sparql(property_identifier, endpoint)
        
        # Query for usage count and samples
        usage_query = f"""
        SELECT ?subject ?object (COUNT(*) as ?count) WHERE {{
            ?subject {sparql_property} ?object .
        }}
        GROUP BY ?subject ?object
        ORDER BY DESC(?count)
        LIMIT 20
        """
        
        result = await sparql_client.sparql_query(usage_query, endpoint=endpoint)
        bindings = result.get('results', {}).get('bindings', [])
        
        if bindings:
            usage_analysis["total_usage_count"] = len(bindings)
            usage_analysis["sample_subjects"] = [
                binding.get('subject', {}).get('value', '') for binding in bindings[:10]
            ]
            usage_analysis["sample_objects"] = [
                binding.get('object', {}).get('value', '') for binding in bindings[:10]
            ]
            
            # Analyze usage patterns
            usage_analysis["usage_patterns"] = _analyze_usage_patterns(bindings)
        
    except Exception as e:
        log.warning(f"Property usage analysis failed: {e}")
        usage_analysis["error"] = str(e)
    
    return usage_analysis


async def _analyze_cross_vocabulary_mappings(
    property_identifier: str,
    vocab_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze cross-vocabulary property mappings."""
    
    mappings = {
        "equivalent_properties": [],
        "similar_properties": [],
        "vocabulary_alignments": {},
        "confidence_scores": {}
    }
    
    try:
        requested_vocabs = vocab_context.get("requested_vocabularies", [])
        
        for vocab in requested_vocabs:
            # Check for equivalent properties in each vocabulary
            equivalents = _find_equivalent_properties(property_identifier, vocab)
            if equivalents:
                mappings["equivalent_properties"].extend(equivalents)
                mappings["confidence_scores"][vocab] = 0.9  # High confidence for direct mappings
            
            # Check for similar properties
            similar = _find_similar_properties(property_identifier, vocab)
            if similar:
                mappings["similar_properties"].extend(similar)
                mappings["confidence_scores"][f"{vocab}_similar"] = 0.6  # Medium confidence
        
        # Cross-vocabulary alignment analysis
        if len(requested_vocabs) > 1:
            alignments = _analyze_vocabulary_alignments(requested_vocabs, property_identifier)
            mappings["vocabulary_alignments"] = alignments
        
    except Exception as e:
        log.warning(f"Cross-vocabulary mapping analysis failed: {e}")
        mappings["error"] = str(e)
    
    return mappings


async def _generate_property_intelligence(
    property_identifier: str,
    property_metadata: Dict[str, Any],
    vocab_context: Dict[str, Any],
    usage_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate intelligent reasoning guidance for property analysis."""
    
    # Determine domain type based on property and vocabularies
    domain_type = DomainType.KNOWLEDGE_GRAPH
    vocabs = vocab_context.get("requested_vocabularies", [])
    
    if any(v in ["bioschemas", "uniprot", "ncbi"] for v in vocabs):
        domain_type = DomainType.LIFE_SCIENCES
    elif any(v in ["schema", "foaf", "dcterms"] for v in vocabs):
        domain_type = DomainType.SEMANTIC_WEB
    elif "geonames" in vocabs or property_identifier in ["P625", "P17", "P131"]:
        domain_type = DomainType.GEOSPATIAL
    
    # Generate guidance context
    guidance_context = GuidanceContext(
        entity_type=f"Property:{property_metadata.get('type', 'unknown')}",
        domain_type=domain_type,
        properties=[property_identifier],
        confidence_score=0.85,
        previous_actions=["property_analysis"],
        available_tools=["cl_sparql", "cl_describe", "cl_validate"]
    )
    
    return guidance_generator.generate_guidance(guidance_context)


async def _build_property_response(
    property_identifier: str,
    property_metadata: Dict[str, Any],
    vocab_context: Dict[str, Any],
    usage_analysis: Dict[str, Any],
    cross_mappings: Dict[str, Any],
    domain_intelligence: Dict[str, Any],
    start_time: float,
    level: str
) -> Dict[str, Any]:
    """Build comprehensive property analysis response."""
    
    execution_time = int((time.time() - start_time) * 1000)
    
    return {
        "success": True,
        "data": {
            "property": {
                "identifier": property_identifier,
                "metadata": property_metadata,
                "vocabulary_context": vocab_context,
                "usage_analysis": usage_analysis,
                "cross_vocabulary_mappings": cross_mappings
            }
        },
        "metadata": {
            "execution_time_ms": execution_time,
            "property_type": property_metadata.get("type", "unknown"),
            "vocabularies_analyzed": len(vocab_context.get("requested_vocabularies", [])),
            "conflicts_resolved": len(vocab_context.get("conflicts_detected", [])),
            "confidence_score": 0.85
        },
        "suggestions": {
            "next_tools": [
                f"cl_sparql 'SELECT ?s ?o WHERE {{ ?s {property_identifier} ?o }} LIMIT 10'",
                f"cl_describe <entity_id> --include-properties {property_identifier}",
                "cl_validate --property-analysis"
            ],
            "usage_patterns": [
                f"Property used {usage_analysis.get('total_usage_count', 0)} times",
                "Common in biological entity descriptions" if domain_intelligence.get("reasoning_patterns") else "General knowledge property"
            ],
            "vocabulary_recommendations": _generate_vocabulary_recommendations(vocab_context, cross_mappings)
        },
        "claude_guidance": {
            "property_summary": f"Analyzed {property_identifier} across {len(vocab_context.get('requested_vocabularies', []))} vocabularies",
            "domain_intelligence": domain_intelligence.get("reasoning_patterns", [])[:3],
            "cross_vocabulary_insights": [
                f"Found {len(cross_mappings.get('equivalent_properties', []))} equivalent properties",
                f"Detected {len(vocab_context.get('conflicts_detected', []))} vocabulary conflicts",
                "Safe for multi-vocabulary contexts" if vocab_context.get("collision_resolution") else "Use single vocabulary for safety"
            ],
            "usage_recommendations": [
                f"Property shows {_assess_usage_frequency(usage_analysis)} usage frequency",
                "Suitable for automated reasoning" if usage_analysis.get("total_usage_count", 0) > 100 else "Manual validation recommended",
                f"Best used with {', '.join(vocab_context.get('requested_vocabularies', [])[:2])} vocabularies"
            ]
        }
    }


# Utility functions
def _is_valid_property_identifier(identifier: str) -> bool:
    """Validate property identifier format."""
    return (
        identifier.startswith('P') and identifier[1:].isdigit() or  # Wikidata P123
        ':' in identifier or  # Prefixed property
        identifier.startswith('http')  # Full URI
    )


def _resolve_namespace_uri(prefix: str) -> str:
    """Resolve namespace URI for common prefixes."""
    common_namespaces = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "schema": "https://schema.org/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": "http://purl.org/dc/terms/"
    }
    return common_namespaces.get(prefix, f"http://example.org/{prefix}#")


def _extract_namespace(uri: str) -> str:
    """Extract namespace from full URI."""
    if '#' in uri:
        return uri.split('#')[0] + '#'
    else:
        return '/'.join(uri.split('/')[:-1]) + '/'


def _extract_local_name(uri: str) -> str:
    """Extract local name from full URI."""
    if '#' in uri:
        return uri.split('#')[-1]
    else:
        return uri.split('/')[-1]


def _auto_detect_vocabularies(property_identifier: str) -> List[str]:
    """Auto-detect relevant vocabularies based on property identifier."""
    if property_identifier.startswith('P'):
        return ["wikidata"]
    elif property_identifier.startswith('schema:'):
        return ["schema"]
    elif property_identifier.startswith('rdf:') or property_identifier.startswith('rdfs:'):
        return ["rdf", "rdfs"]
    elif property_identifier.startswith('foaf:'):
        return ["foaf"]
    else:
        return ["schema"]  # Default fallback


def _convert_property_for_sparql(property_identifier: str, endpoint: str) -> str:
    """Convert property identifier to appropriate SPARQL format for endpoint."""
    if endpoint == "wikidata":
        if property_identifier.startswith('P'):
            return f"wdt:{property_identifier}"
        elif ':' in property_identifier:
            return property_identifier
        else:
            return f"<{property_identifier}>"
    else:
        return property_identifier


async def _find_wikidata_equivalent(property_identifier: str, sparql_client: MultiSparqlClient) -> Optional[str]:
    """Find Wikidata equivalent for external property."""
    # This would involve complex mapping queries - placeholder for now
    return None


def _analyze_usage_patterns(bindings: List[Dict]) -> List[str]:
    """Analyze usage patterns from SPARQL bindings."""
    patterns = []
    
    if len(bindings) > 10:
        patterns.append("High usage frequency")
    elif len(bindings) > 3:
        patterns.append("Moderate usage frequency")
    else:
        patterns.append("Low usage frequency")
    
    # Analyze subject/object types
    subjects = [b.get('subject', {}).get('value', '') for b in bindings]
    if any('Q' in s for s in subjects):
        patterns.append("Used with Wikidata entities")
    
    return patterns


def _find_equivalent_properties(property_identifier: str, vocab: str) -> List[str]:
    """Find equivalent properties in specified vocabulary."""
    # Placeholder - would use vocabulary registry mappings
    return []


def _find_similar_properties(property_identifier: str, vocab: str) -> List[str]:
    """Find similar properties in specified vocabulary."""
    # Placeholder - would use semantic similarity analysis
    return []


def _analyze_vocabulary_alignments(vocabs: List[str], property_identifier: str) -> Dict[str, Any]:
    """Analyze alignments between vocabularies for this property."""
    # Placeholder for cross-vocabulary alignment analysis
    return {}


def _generate_vocabulary_recommendations(vocab_context: Dict, cross_mappings: Dict) -> List[str]:
    """Generate vocabulary usage recommendations."""
    recommendations = []
    
    if vocab_context.get("conflicts_detected"):
        recommendations.append("Consider using collision resolution for vocabulary conflicts")
    
    if cross_mappings.get("equivalent_properties"):
        recommendations.append("Multiple equivalent properties available - choose based on domain")
    
    recommendations.append("Use composed context for multi-vocabulary queries")
    return recommendations


def _assess_usage_frequency(usage_analysis: Dict) -> str:
    """Assess usage frequency from analysis."""
    count = usage_analysis.get("total_usage_count", 0)
    if count > 1000:
        return "very high"
    elif count > 100:
        return "high"
    elif count > 10:
        return "moderate"
    else:
        return "low"


def _output_error(message: str, suggestion: str, output_format: str):
    """Output error in requested format."""
    error_response = {
        "success": False,
        "error": {
            "code": "PROPERTY_ANALYSIS_ERROR",
            "message": message,
            "suggestion": suggestion,
            "examples": [
                "cl_property P31 --context-vocabs schema",
                "cl_property schema:name --include-mappings",
                "cl_property rdf:type --resolve-conflicts"
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
    """Print human-readable property analysis summary."""
    
    if response.get("success", False):
        data = response.get("data", {})
        prop_data = data.get("property", {})
        metadata = prop_data.get("metadata", {})
        
        print(f"🔍 Property Analysis: {prop_data.get('identifier', 'Unknown')}")
        print(f"   Type: {metadata.get('type', 'unknown')}")
        print(f"   Description: {metadata.get('description', 'No description available')}")
        
        vocab_context = prop_data.get("vocabulary_context", {})
        if vocab_context.get("requested_vocabularies"):
            print(f"   Vocabularies: {', '.join(vocab_context['requested_vocabularies'])}")
        
        usage = prop_data.get("usage_analysis", {})
        if usage.get("total_usage_count"):
            print(f"   Usage Count: {usage['total_usage_count']}")
        
        mappings = prop_data.get("cross_vocabulary_mappings", {})
        equiv_count = len(mappings.get("equivalent_properties", []))
        if equiv_count > 0:
            print(f"   Equivalent Properties: {equiv_count}")
        
        suggestions = response.get("suggestions", {})
        next_tools = suggestions.get("next_tools", [])
        if next_tools:
            print(f"\n💡 Next Steps:")
            for tool in next_tools[:3]:
                print(f"   → {tool}")
                
    else:
        error = response.get("error", {})
        print(f"❌ Error: {error.get('message', 'Unknown error')}")
        if error.get("suggestion"):
            print(f"💡 Suggestion: {error['suggestion']}")


if __name__ == "__main__":
    property()