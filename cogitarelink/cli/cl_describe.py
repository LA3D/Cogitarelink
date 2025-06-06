"""
cl_describe: Enhanced entity descriptions with vocabulary intelligence

Synthesis of wikidata-mcp enhanced entity tools with cogitarelink vocabulary management.
Provides rich entity descriptions combining Wikidata cross-reference resolution,
vocabulary-aware contextualization, and cross-domain enrichment suggestions.
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

log = get_logger("cl_describe")


@click.command()
@click.argument('entity_identifier', required=True)
@click.option('--context-vocabs', multiple=True,
              help='Vocabulary contexts: schema, bioschemas, foaf, geonames, etc.')
@click.option('--include-cross-refs', is_flag=True, default=True,
              help='Include cross-references to external databases')
@click.option('--include-spatial', is_flag=True, default=True,
              help='Include spatial intelligence for geographic entities')
@click.option('--resolve-urls', is_flag=True, default=False,
              help='Resolve cross-reference URLs for richer data')
@click.option('--materialize', is_flag=True, default=True,
              help='Auto-materialize entity as semantic memory')
@click.option('--properties', multiple=True,
              help='Specific properties to focus on: P31, schema:name, etc.')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
def describe(
    entity_identifier: str,
    context_vocabs: List[str],
    include_cross_refs: bool,
    include_spatial: bool,
    resolve_urls: bool,
    materialize: bool,
    properties: List[str],
    level: str,
    output_format: str
):
    """
    Enhanced entity descriptions with vocabulary-aware contextualization.
    
    Examples:
        cl_describe Q42 --context-vocabs schema,foaf
        cl_describe Q7240673 --include-cross-refs --resolve-urls
        cl_describe Q90 --include-spatial --context-vocabs geonames
        cl_describe "Douglas Adams" --materialize --properties P31,P106
    """
    asyncio.run(_describe_async(
        entity_identifier, list(context_vocabs), include_cross_refs, include_spatial,
        resolve_urls, materialize, list(properties), level, output_format
    ))


async def _describe_async(
    entity_identifier: str,
    context_vocabs: List[str],
    include_cross_refs: bool,
    include_spatial: bool,
    resolve_urls: bool,
    materialize: bool,
    properties: List[str],
    level: str,
    output_format: str
):
    """Async entity description with vocabulary intelligence."""
    
    start_time = time.time()
    
    try:
        log.info(f"Describing entity: {entity_identifier}")
        
        # Initialize clients
        wikidata_client = WikidataClient(timeout=30)
        sparql_client = MultiSparqlClient(timeout=30)
        
        # 1. Enhanced Entity Resolution (wikidata-mcp pattern)
        entity_data = await _resolve_enhanced_entity(
            entity_identifier, wikidata_client, properties
        )
        
        if not entity_data:
            _output_error(
                f"Entity not found: {entity_identifier}",
                "Check entity identifier format or try search first",
                output_format
            )
            return
        
        # 2. Cross-Reference Enrichment
        cross_references = {}
        if include_cross_refs:
            cross_references = await _enrich_with_cross_references(
                entity_data, sparql_client, resolve_urls
            )
        
        # 3. Spatial Intelligence Enhancement
        spatial_context = {}
        if include_spatial and _is_geographic_entity(entity_data):
            spatial_context = await _apply_spatial_intelligence(
                entity_data, sparql_client
            )
        
        # 4. Vocabulary Contextualization (cogitarelink pattern)
        vocab_enrichment = await _apply_vocabulary_contextualization(
            entity_data, context_vocabs, cross_references
        )
        
        # 5. Domain Intelligence Generation
        domain_intelligence = await _generate_entity_intelligence(
            entity_data, cross_references, spatial_context, vocab_enrichment
        )
        
        # 6. Semantic Memory Materialization
        materialized_entity = None
        if materialize:
            materialized_entity = await _materialize_enriched_entity(
                entity_data, cross_references, spatial_context, vocab_enrichment
            )
        
        # Build comprehensive response
        response = await _build_describe_response(
            entity_identifier, entity_data, cross_references, spatial_context,
            vocab_enrichment, domain_intelligence, materialized_entity, start_time, level
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
        log.error(f"Entity description failed: {e}")
        _output_error(f"Entity description failed: {str(e)}", "Check entity identifier and network connectivity", output_format)
        sys.exit(1)


async def _resolve_enhanced_entity(
    entity_identifier: str,
    wikidata_client: WikidataClient,
    properties: List[str]
) -> Optional[Dict[str, Any]]:
    """Resolve entity with enhanced data using wikidata-mcp patterns."""
    
    try:
        # Handle different entity identifier formats
        entity_id = await _normalize_entity_identifier(entity_identifier, wikidata_client)
        if not entity_id:
            return None
        
        # Get comprehensive entity data
        props = ['labels', 'descriptions', 'sitelinks', 'claims']
        entity_data = await wikidata_client.get_entities([entity_id], props=props)
        
        if entity_id not in entity_data.get('entities', {}):
            return None
        
        raw_entity = entity_data['entities'][entity_id]
        
        # Enhanced entity processing
        enhanced_entity = {
            "id": entity_id,
            "uri": f"http://www.wikidata.org/entity/{entity_id}",
            "labels": raw_entity.get('labels', {}),
            "descriptions": raw_entity.get('descriptions', {}),
            "sitelinks": raw_entity.get('sitelinks', {}),
            "claims": raw_entity.get('claims', {}),
            "wikidata_url": f"https://www.wikidata.org/wiki/{entity_id}"
        }
        
        # Extract key information
        enhanced_entity["name"] = _extract_best_label(raw_entity)
        enhanced_entity["description"] = _extract_best_description(raw_entity)
        enhanced_entity["wikipedia_url"] = _extract_wikipedia_url(raw_entity)
        enhanced_entity["entity_types"] = _extract_entity_types(raw_entity)
        
        # Filter to specific properties if requested
        if properties:
            filtered_claims = {}
            for prop in properties:
                if prop in enhanced_entity["claims"]:
                    filtered_claims[prop] = enhanced_entity["claims"][prop]
            enhanced_entity["claims"] = filtered_claims
        
        return enhanced_entity
        
    except Exception as e:
        log.error(f"Enhanced entity resolution failed: {e}")
        return None


async def _enrich_with_cross_references(
    entity_data: Dict[str, Any],
    sparql_client: MultiSparqlClient,
    resolve_urls: bool
) -> Dict[str, Any]:
    """Enrich entity with cross-references to external databases."""
    
    cross_references = {
        "databases": {},
        "resolved_data": {},
        "total_references": 0
    }
    
    # Database property mappings (from cl_follow implementation)
    database_properties = {
        'P352': 'uniprot',      # UniProt protein ID
        'P683': 'chebi',        # ChEBI ID
        'P231': 'cas',          # CAS Registry Number
        'P592': 'chembl',       # ChEMBL ID
        'P715': 'drugbank',     # DrugBank ID
        'P486': 'mesh',         # MeSH descriptor ID
        'P685': 'ncbi_gene',    # NCBI Gene ID
        'P594': 'ensembl_gene', # Ensembl gene ID
        'P625': 'coordinates',  # Geographic coordinates
        'P17': 'country',       # Country
        'P131': 'located_in',   # Located in administrative division
    }
    
    claims = entity_data.get('claims', {})
    
    for prop_id, db_name in database_properties.items():
        if prop_id in claims:
            values = []
            for claim in claims[prop_id]:
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                    value = claim['mainsnak']['datavalue']['value']
                    if isinstance(value, str):
                        values.append(value)
                    elif isinstance(value, dict):
                        if 'text' in value:
                            values.append(value['text'])
                        elif 'id' in value:  # Entity reference
                            values.append(value['id'])
                        elif 'latitude' in value:  # Coordinates
                            values.append(f"{value['latitude']},{value['longitude']}")
            
            if values:
                cross_references["databases"][db_name] = values
                cross_references["total_references"] += len(values)
    
    # Resolve URLs and fetch additional data if requested
    if resolve_urls and cross_references["databases"]:
        resolved_data = await _resolve_cross_reference_data(
            cross_references["databases"], sparql_client
        )
        cross_references["resolved_data"] = resolved_data
    
    return cross_references


async def _apply_spatial_intelligence(
    entity_data: Dict[str, Any],
    sparql_client: MultiSparqlClient
) -> Dict[str, Any]:
    """Apply spatial intelligence for geographic entities."""
    
    spatial_context = {
        "is_geographic": False,
        "coordinates": None,
        "administrative_divisions": [],
        "spatial_relationships": [],
        "osm_references": []
    }
    
    claims = entity_data.get('claims', {})
    
    # Check for coordinates
    if 'P625' in claims:
        coord_claims = claims['P625']
        if coord_claims and 'mainsnak' in coord_claims[0] and 'datavalue' in coord_claims[0]['mainsnak']:
            coord_value = coord_claims[0]['mainsnak']['datavalue']['value']
            spatial_context["is_geographic"] = True
            spatial_context["coordinates"] = {
                "latitude": coord_value.get('latitude'),
                "longitude": coord_value.get('longitude'),
                "precision": coord_value.get('precision')
            }
    
    # Check for administrative divisions
    admin_properties = ['P17', 'P131', 'P706']  # country, located in, located on terrain feature
    for prop in admin_properties:
        if prop in claims:
            for claim in claims[prop]:
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                    value = claim['mainsnak']['datavalue']['value']
                    if isinstance(value, dict) and 'id' in value:
                        spatial_context["administrative_divisions"].append({
                            "property": prop,
                            "entity_id": value['id']
                        })
    
    # Generate spatial relationships if coordinates available
    if spatial_context["coordinates"]:
        spatial_context["spatial_relationships"] = _generate_spatial_relationships(
            spatial_context["coordinates"]
        )
    
    return spatial_context


async def _apply_vocabulary_contextualization(
    entity_data: Dict[str, Any],
    context_vocabs: List[str],
    cross_references: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply vocabulary contextualization using cogitarelink patterns."""
    
    vocab_enrichment = {
        "requested_vocabularies": context_vocabs,
        "auto_detected_vocabularies": [],
        "composed_context": {},
        "vocabulary_mappings": {},
        "conflicts_resolved": []
    }
    
    try:
        # Auto-detect relevant vocabularies if none specified
        if not context_vocabs:
            context_vocabs = _auto_detect_vocabularies_from_entity(entity_data, cross_references)
            vocab_enrichment["auto_detected_vocabularies"] = context_vocabs
            vocab_enrichment["requested_vocabularies"] = context_vocabs
        
        # Map entity properties to vocabulary terms
        for vocab in context_vocabs:
            mappings = _map_entity_to_vocabulary(entity_data, vocab)
            if mappings:
                vocab_enrichment["vocabulary_mappings"][vocab] = mappings
        
        # Compose context with collision handling
        if len(context_vocabs) > 1:
            composed_context = composer.compose(context_vocabs)
            vocab_enrichment["composed_context"] = composed_context
            
            # Handle any conflicts (simplified for now)
            conflicts = []  # Placeholder - would use composer.detect_conflicts
            if conflicts:
                # Placeholder for collision resolution
                vocab_enrichment["conflicts_resolved"] = conflicts
                vocab_enrichment["collision_resolution"] = {}
        else:
            # Single vocabulary - simple context
            if context_vocabs:
                try:
                    vocab_entry = registry.resolve(context_vocabs[0])
                    vocab_enrichment["composed_context"] = {
                        "@context": vocab_entry.context_payload()
                    }
                except KeyError:
                    vocab_enrichment["composed_context"] = {}
        
    except Exception as e:
        log.warning(f"Vocabulary contextualization failed: {e}")
        vocab_enrichment["error"] = str(e)
    
    return vocab_enrichment


async def _generate_entity_intelligence(
    entity_data: Dict[str, Any],
    cross_references: Dict[str, Any],
    spatial_context: Dict[str, Any],
    vocab_enrichment: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate intelligent reasoning guidance for entity description."""
    
    # Determine domain type based on entity characteristics
    domain_type = DomainType.KNOWLEDGE_GRAPH
    entity_types = entity_data.get("entity_types", [])
    
    # Biological domain detection
    if any(t in ["Q8054", "Q7187", "Q11173"] for t in entity_types):  # protein, gene, chemical
        domain_type = DomainType.LIFE_SCIENCES
    elif cross_references.get("databases", {}).keys() & {"uniprot", "chebi", "ncbi_gene"}:
        domain_type = DomainType.LIFE_SCIENCES
    
    # Geographic domain detection
    elif spatial_context.get("is_geographic") or any(t in ["Q515", "Q6256"] for t in entity_types):  # city, country
        domain_type = DomainType.GEOSPATIAL
    
    # Semantic web domain detection
    elif "foaf" in vocab_enrichment.get("requested_vocabularies", []):
        domain_type = DomainType.SEMANTIC_WEB
    
    # Generate guidance context
    guidance_context = GuidanceContext(
        entity_type=f"Entity:{entity_data.get('name', 'Unknown')}",
        domain_type=domain_type,
        properties=list(entity_data.get("claims", {}).keys()),
        confidence_score=0.9,
        previous_actions=["entity_description"],
        available_tools=["cl_sparql", "cl_property", "cl_follow", "cl_materialize"]
    )
    
    return guidance_generator.generate_guidance(guidance_context)


async def _materialize_enriched_entity(
    entity_data: Dict[str, Any],
    cross_references: Dict[str, Any],
    spatial_context: Dict[str, Any],
    vocab_enrichment: Dict[str, Any]
) -> Optional[Entity]:
    """Materialize enriched entity in semantic memory."""
    
    try:
        # Determine appropriate vocabularies
        vocabs = vocab_enrichment.get("requested_vocabularies", ["schema"])
        
        # Build entity content
        content = {
            "@type": _determine_entity_type(entity_data),
            "identifier": entity_data.get("id"),
            "name": entity_data.get("name"),
            "description": entity_data.get("description"),
            "sameAs": [entity_data.get("uri")]
        }
        
        # Add cross-references
        if cross_references.get("databases"):
            content["additionalProperty"] = []
            for db_name, refs in cross_references["databases"].items():
                for ref in refs:
                    content["additionalProperty"].append({
                        "@type": "PropertyValue",
                        "name": f"{db_name}_id",
                        "value": ref
                    })
        
        # Add spatial information
        if spatial_context.get("coordinates"):
            coords = spatial_context["coordinates"]
            content["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": coords["latitude"],
                "longitude": coords["longitude"]
            }
        
        # Create entity with composed context
        context = vocab_enrichment.get("composed_context", {}).get("@context", {})
        if context:
            content["@context"] = context
        
        # Create materialized entity
        entity = Entity(
            id=f"urn:cogitarelink:described:{entity_data.get('id')}",
            vocab=vocabs,
            content=content,
            meta={
                "source": "cl_describe",
                "enrichment_timestamp": "auto-generated",
                "cross_references_count": cross_references.get("total_references", 0),
                "spatial_enhanced": spatial_context.get("is_geographic", False)
            }
        )
        
        log.info(f"Materialized enriched entity with signature {entity.sha256[:8]}...")
        return entity
        
    except Exception as e:
        log.error(f"Entity materialization failed: {e}")
        return None


async def _build_describe_response(
    entity_identifier: str,
    entity_data: Dict[str, Any],
    cross_references: Dict[str, Any],
    spatial_context: Dict[str, Any],
    vocab_enrichment: Dict[str, Any],
    domain_intelligence: Dict[str, Any],
    materialized_entity: Optional[Entity],
    start_time: float,
    level: str
) -> Dict[str, Any]:
    """Build comprehensive entity description response."""
    
    execution_time = int((time.time() - start_time) * 1000)
    
    return {
        "success": True,
        "data": {
            "entity": {
                "identifier": entity_identifier,
                "resolved_id": entity_data.get("id"),
                "name": entity_data.get("name"),
                "description": entity_data.get("description"),
                "uri": entity_data.get("uri"),
                "wikidata_url": entity_data.get("wikidata_url"),
                "wikipedia_url": entity_data.get("wikipedia_url"),
                "entity_types": entity_data.get("entity_types", []),
                "claims_count": len(entity_data.get("claims", {}))
            },
            "enrichment": {
                "cross_references": cross_references,
                "spatial_context": spatial_context,
                "vocabulary_context": vocab_enrichment
            },
            "materialization": {
                "materialized": materialized_entity is not None,
                "entity_signature": materialized_entity.sha256[:12] if materialized_entity else None,
                "vocabularies_used": vocab_enrichment.get("requested_vocabularies", [])
            }
        },
        "metadata": {
            "execution_time_ms": execution_time,
            "enrichment_types": [
                "cross_references" if cross_references.get("total_references", 0) > 0 else None,
                "spatial_intelligence" if spatial_context.get("is_geographic") else None,
                "vocabulary_contextualization" if vocab_enrichment.get("composed_context") else None
            ],
            "databases_referenced": len(cross_references.get("databases", {})),
            "confidence_score": 0.9
        },
        "suggestions": {
            "next_tools": [
                f"cl_follow {entity_data.get('id')} --databases {','.join(list(cross_references.get('databases', {}).keys())[:3])}",
                f"cl_sparql 'SELECT ?related WHERE {{ wd:{entity_data.get('id')} ?p ?related }} LIMIT 10'",
                "cl_materialize --from-entity-description"
            ],
            "cross_database_opportunities": [
                f"Follow {db}: {refs[0]}" for db, refs in cross_references.get("databases", {}).items()
            ][:3],
            "spatial_opportunities": [
                "Explore geographic relationships",
                "Query nearby entities",
                "Analyze administrative hierarchies"
            ] if spatial_context.get("is_geographic") else [],
            "vocabulary_recommendations": [
                f"Use {vocab} vocabulary for domain-specific queries"
                for vocab in vocab_enrichment.get("requested_vocabularies", [])
            ]
        },
        "claude_guidance": {
            "entity_summary": f"Described {entity_data.get('name')} with {cross_references.get('total_references', 0)} cross-references across {len(cross_references.get('databases', {}))} databases",
            "enrichment_intelligence": [
                f"Enhanced with {len(cross_references.get('databases', {}))} external database references",
                "Spatial intelligence applied" if spatial_context.get("is_geographic") else "Non-geographic entity",
                f"Contextualized with {len(vocab_enrichment.get('requested_vocabularies', []))} vocabularies"
            ],
            "domain_intelligence": domain_intelligence.get("reasoning_patterns", [])[:3],
            "workflow_recommendations": [
                "Use cross-references for federated database queries",
                "Apply spatial reasoning for geographic relationships" if spatial_context.get("is_geographic") else "Focus on semantic relationships",
                "Leverage vocabulary contexts for multi-domain integration",
                "Materialize entity for semantic memory workflows"
            ]
        }
    }


# Utility functions
async def _normalize_entity_identifier(identifier: str, wikidata_client: WikidataClient) -> Optional[str]:
    """Normalize entity identifier to Wikidata Q-ID."""
    
    # Already a Q-ID
    if identifier.startswith('Q') and identifier[1:].isdigit():
        return identifier
    
    # Try search if it's a label
    try:
        search_results = await wikidata_client.search_entities(identifier, limit=1)
        if search_results.get('search'):
            return search_results['search'][0]['id']
    except:
        pass
    
    return None


def _extract_best_label(entity_data: Dict) -> str:
    """Extract best label from entity data."""
    labels = entity_data.get('labels', {})
    
    # Prefer English
    if 'en' in labels:
        return labels['en']['value']
    
    # Fallback to any available label
    for label_data in labels.values():
        return label_data['value']
    
    return "Unknown"


def _extract_best_description(entity_data: Dict) -> str:
    """Extract best description from entity data."""
    descriptions = entity_data.get('descriptions', {})
    
    # Prefer English
    if 'en' in descriptions:
        return descriptions['en']['value']
    
    # Fallback to any available description
    for desc_data in descriptions.values():
        return desc_data['value']
    
    return ""


def _extract_wikipedia_url(entity_data: Dict) -> Optional[str]:
    """Extract Wikipedia URL from sitelinks."""
    sitelinks = entity_data.get('sitelinks', {})
    
    if 'enwiki' in sitelinks:
        title = sitelinks['enwiki']['title']
        return f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    
    return None


def _extract_entity_types(entity_data: Dict) -> List[str]:
    """Extract entity types from P31 (instance of) claims."""
    claims = entity_data.get('claims', {})
    types = []
    
    if 'P31' in claims:
        for claim in claims['P31']:
            if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                value = claim['mainsnak']['datavalue']['value']
                if isinstance(value, dict) and 'id' in value:
                    types.append(value['id'])
    
    return types


def _is_geographic_entity(entity_data: Dict) -> bool:
    """Check if entity is geographic based on properties and types."""
    claims = entity_data.get('claims', {})
    
    # Has coordinates
    if 'P625' in claims:
        return True
    
    # Has geographic administrative properties
    geo_props = ['P17', 'P131', 'P706']  # country, located in, located on terrain feature
    if any(prop in claims for prop in geo_props):
        return True
    
    # Has geographic entity types
    entity_types = entity_data.get("entity_types", [])
    geo_types = ["Q515", "Q6256", "Q35657", "Q839954"]  # city, country, state, archaeological site
    if any(t in geo_types for t in entity_types):
        return True
    
    return False


async def _resolve_cross_reference_data(
    databases: Dict[str, List[str]],
    sparql_client: MultiSparqlClient
) -> Dict[str, Any]:
    """Resolve cross-reference data from external databases."""
    
    resolved_data = {}
    
    # Try to resolve UniProt data if available
    if 'uniprot' in databases:
        uniprot_ids = databases['uniprot'][:3]  # Limit to avoid timeout
        
        for uniprot_id in uniprot_ids:
            try:
                query = f"""
                SELECT ?protein ?name ?organism WHERE {{
                    ?protein up:mnemonic "{uniprot_id}" .
                    OPTIONAL {{ ?protein up:recommendedName/up:fullName ?name }}
                    OPTIONAL {{ ?protein up:organism ?organism }}
                }}
                LIMIT 1
                """
                
                result = await sparql_client.sparql_query(query, endpoint="uniprot")
                bindings = result.get('results', {}).get('bindings', [])
                
                if bindings:
                    binding = bindings[0]
                    resolved_data[f'uniprot_{uniprot_id}'] = {
                        'protein_uri': binding.get('protein', {}).get('value', ''),
                        'name': binding.get('name', {}).get('value', ''),
                        'organism': binding.get('organism', {}).get('value', '')
                    }
            except Exception as e:
                log.warning(f"Failed to resolve UniProt data for {uniprot_id}: {e}")
    
    return resolved_data


def _generate_spatial_relationships(coordinates: Dict) -> List[str]:
    """Generate spatial relationship descriptions."""
    lat = coordinates.get("latitude", 0)
    lon = coordinates.get("longitude", 0)
    
    relationships = []
    
    # Hemisphere information
    if lat > 0:
        relationships.append("Northern Hemisphere")
    else:
        relationships.append("Southern Hemisphere")
    
    if lon > 0:
        relationships.append("Eastern Hemisphere")
    else:
        relationships.append("Western Hemisphere")
    
    # Rough continental assignment
    if -180 <= lon <= -30:
        relationships.append("Americas region")
    elif -30 <= lon <= 60:
        relationships.append("Europe/Africa region")
    elif 60 <= lon <= 180:
        relationships.append("Asia/Pacific region")
    
    return relationships


def _auto_detect_vocabularies_from_entity(
    entity_data: Dict[str, Any],
    cross_references: Dict[str, Any]
) -> List[str]:
    """Auto-detect relevant vocabularies based on entity characteristics."""
    
    vocabs = ["schema"]  # Default
    
    # Biological vocabularies
    bio_databases = {"uniprot", "chebi", "ncbi_gene", "ensembl_gene"}
    if cross_references.get("databases", {}).keys() & bio_databases:
        vocabs.append("bioschemas")
    
    # Geographic vocabularies
    if cross_references.get("databases", {}).get("coordinates") or "P625" in entity_data.get("claims", {}):
        vocabs.append("geonames")
    
    # Person-related vocabularies
    entity_types = entity_data.get("entity_types", [])
    if "Q5" in entity_types:  # human
        vocabs.append("foaf")
    
    return list(set(vocabs))


def _map_entity_to_vocabulary(entity_data: Dict[str, Any], vocab: str) -> Dict[str, Any]:
    """Map entity properties to vocabulary terms."""
    
    mappings = {}
    
    if vocab == "schema":
        mappings = {
            "name": entity_data.get("name"),
            "description": entity_data.get("description"),
            "url": entity_data.get("wikidata_url"),
            "sameAs": entity_data.get("uri")
        }
    elif vocab == "foaf":
        if "Q5" in entity_data.get("entity_types", []):  # human
            mappings = {
                "name": entity_data.get("name"),
                "homepage": entity_data.get("wikipedia_url")
            }
    elif vocab == "bioschemas":
        mappings = {
            "name": entity_data.get("name"),
            "description": entity_data.get("description"),
            "identifier": entity_data.get("id")
        }
    
    return {k: v for k, v in mappings.items() if v}


def _determine_entity_type(entity_data: Dict[str, Any]) -> str:
    """Determine appropriate @type for entity based on characteristics."""
    
    entity_types = entity_data.get("entity_types", [])
    
    # Person
    if "Q5" in entity_types:
        return "Person"
    
    # Biological entities
    if "Q8054" in entity_types:  # protein
        return "Protein"
    elif "Q7187" in entity_types:  # gene
        return "Gene"
    elif "Q11173" in entity_types:  # chemical compound
        return "ChemicalSubstance"
    
    # Geographic entities
    if "Q515" in entity_types:  # city
        return "City"
    elif "Q6256" in entity_types:  # country
        return "Country"
    elif "Q35657" in entity_types:  # state
        return "State"
    
    # Organization
    if any(t in ["Q43229", "Q4830453"] for t in entity_types):  # organization, business
        return "Organization"
    
    return "Thing"  # Default


def _output_error(message: str, suggestion: str, output_format: str):
    """Output error in requested format."""
    error_response = {
        "success": False,
        "error": {
            "code": "ENTITY_DESCRIPTION_ERROR",
            "message": message,
            "suggestion": suggestion,
            "examples": [
                "cl_describe Q42 --context-vocabs schema,foaf",
                "cl_describe Q7240673 --include-cross-refs",
                "cl_describe \"Douglas Adams\" --materialize"
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
    """Print human-readable entity description summary."""
    
    if response.get("success", False):
        data = response.get("data", {})
        entity = data.get("entity", {})
        enrichment = data.get("enrichment", {})
        
        print(f"🔍 Entity Description: {entity.get('name', 'Unknown')}")
        print(f"   ID: {entity.get('resolved_id', 'Unknown')}")
        print(f"   Description: {entity.get('description', 'No description')}")
        print(f"   Claims: {entity.get('claims_count', 0)}")
        
        # Cross-references
        cross_refs = enrichment.get("cross_references", {})
        if cross_refs.get("total_references", 0) > 0:
            print(f"\n🔗 Cross-References ({cross_refs['total_references']} total):")
            for db, refs in cross_refs.get("databases", {}).items():
                print(f"   {db.title()}: {', '.join(refs[:3])}")
                if len(refs) > 3:
                    print(f"      ... and {len(refs) - 3} more")
        
        # Spatial context
        spatial = enrichment.get("spatial_context", {})
        if spatial.get("is_geographic"):
            print(f"\n🌍 Geographic Information:")
            coords = spatial.get("coordinates")
            if coords:
                print(f"   Coordinates: {coords['latitude']}, {coords['longitude']}")
            
            admin_divs = spatial.get("administrative_divisions", [])
            if admin_divs:
                print(f"   Administrative divisions: {len(admin_divs)}")
        
        # Vocabulary context
        vocab_context = enrichment.get("vocabulary_context", {})
        vocabs = vocab_context.get("requested_vocabularies", [])
        if vocabs:
            print(f"\n📚 Vocabulary Contexts: {', '.join(vocabs)}")
        
        # Suggestions
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
    describe()