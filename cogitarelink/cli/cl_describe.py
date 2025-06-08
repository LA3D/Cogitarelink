#!/usr/bin/env python3
"""
cl_describe: Entity description tool

Get entity descriptions with cross-references.
Simplified for Claude Code patterns - clean data output only.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Optional, List, Dict, Any

import click

from ..adapters.wikidata_client import WikidataClient
from ..adapters.unified_sparql_client import get_sparql_client
from ..core.debug import get_logger

log = get_logger("cl_describe")


@click.command()
@click.argument('entity_identifier', required=True)
@click.option('--include-cross-refs', is_flag=True, default=True,
              help='Include cross-references to external databases')
def describe(entity_identifier: str, include_cross_refs: bool):
    """
    Get detailed entity description with cross-references.
    
    Examples:
        cl_describe Q7240673
        cl_describe P352 --include-cross-refs
    """
    asyncio.run(_describe_async(entity_identifier, include_cross_refs))


async def _describe_async(entity_identifier: str, include_cross_refs: bool):
    """Async entity description with clean output."""
    
    try:
        # Validate entity ID format
        if not _is_valid_entity_id(entity_identifier):
            error_result = {
                "entity_id": entity_identifier,
                "error": f"Invalid entity ID format: {entity_identifier}. Expected Q123456 or P123456"
            }
            click.echo(json.dumps(error_result, indent=2))
            sys.exit(1)
        
        # Initialize client
        client = WikidataClient(timeout=30)
        
        log.info(f"Describing entity: {entity_identifier}")
        
        # Get entity data
        entity_data = await client.get_entities([entity_identifier])
        
        if entity_identifier not in entity_data.get('entities', {}):
            error_result = {
                "entity_id": entity_identifier,
                "error": f"Entity {entity_identifier} not found in Wikidata"
            }
            click.echo(json.dumps(error_result, indent=2))
            sys.exit(1)
        
        entity_info = entity_data['entities'][entity_identifier]
        
        # Build entity description
        description = _build_entity_description(entity_info, entity_identifier)
        
        # Add cross-references if requested
        if include_cross_refs:
            cross_refs = await _extract_cross_references(entity_info)
            description['cross_references'] = cross_refs
        
        # Clean output - just the data Claude needs
        click.echo(json.dumps(description, indent=2))
        
    except Exception as e:
        log.error(f"Entity description failed: {e}")
        error_result = {
            "entity_id": entity_identifier,
            "error": str(e)
        }
        click.echo(json.dumps(error_result, indent=2))
        sys.exit(1)


def _build_entity_description(entity_info: Dict[str, Any], entity_id: str) -> Dict[str, Any]:
    """Build clean entity description."""
    
    # Extract basic information
    labels = entity_info.get('labels', {})
    descriptions = entity_info.get('descriptions', {})
    aliases = entity_info.get('aliases', {})
    claims = entity_info.get('claims', {})
    
    # Get English label and description
    name = labels.get('en', {}).get('value', '')
    description = descriptions.get('en', {}).get('value', '')
    
    # Extract entity types (P31 - instance of)
    entity_types = []
    if 'P31' in claims:
        for claim in claims['P31'][:3]:  # Limit to first 3
            if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                type_id = claim['mainsnak']['datavalue']['value']['id']
                entity_types.append(type_id)
    
    # Count total claims
    claims_count = sum(len(prop_claims) for prop_claims in claims.values())
    
    return {
        "entity": {
            "identifier": entity_id,
            "name": name,
            "description": description,
            "wikidata_url": f"https://www.wikidata.org/wiki/{entity_id}",
            "entity_types": entity_types,
            "claims_count": claims_count
        }
    }


async def _extract_cross_references(entity_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract cross-references to external databases with dynamic property discovery."""
    
    claims = entity_info.get('claims', {})
    cross_refs = {}
    coordinates = None
    
    # Get all external identifier properties present in this entity
    external_id_properties = [prop_id for prop_id in claims.keys() if prop_id.startswith('P')]
    
    if external_id_properties:
        # Get dynamic property metadata from Wikidata
        property_metadata = await _get_property_metadata(external_id_properties)
        
        # Process external identifier cross-references
        for prop_id in external_id_properties:
            if prop_id in claims and prop_id in property_metadata:
                values = []
                for claim in claims[prop_id][:5]:  # Limit to first 5 per database
                    if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                        value = claim['mainsnak']['datavalue']['value']
                        if isinstance(value, str):
                            values.append(value)
                        elif isinstance(value, dict):
                            if 'text' in value:
                                values.append(value['text'])
                            elif 'id' in value:  # Entity reference
                                values.append(value['id'])
                
                if values:
                    # Use official property label as database name
                    db_name = property_metadata[prop_id]['label']
                    database_info = property_metadata[prop_id].get('database_info', {'type': 'unknown'})
                    
                    cross_refs[db_name] = {
                        'identifiers': values,
                        'property_id': prop_id,
                        'description': property_metadata[prop_id].get('description', ''),
                        'formatter_url': property_metadata[prop_id].get('formatter_url'),
                        'endpoint_type': database_info.get('type', 'unknown'),
                        'sparql_endpoint': database_info.get('sparql_endpoint') if database_info.get('type') == 'sparql_endpoint' else None,
                        'database_name': database_info.get('database_name') if database_info.get('type') == 'sparql_endpoint' else None
                    }
    
    # Special handling for coordinates (P625) - not an external identifier
    if 'P625' in claims:
        coord_claims = claims['P625']
        if coord_claims and 'mainsnak' in coord_claims[0] and 'datavalue' in coord_claims[0]['mainsnak']:
            coord_value = coord_claims[0]['mainsnak']['datavalue']['value']
            coordinates = {
                "latitude": coord_value.get('latitude'),
                "longitude": coord_value.get('longitude'),
                "precision": coord_value.get('precision')
            }
    
    # Build result structure
    result = {"databases": cross_refs}
    if coordinates:
        result["coordinates"] = coordinates
    
    return result


async def _get_sparql_databases() -> Dict[str, str]:
    """Get databases with SPARQL endpoints from Wikidata."""
    try:
        query = """
        SELECT ?database ?databaseLabel ?sparqlEndpoint WHERE {
            ?database wdt:P5305 ?sparqlEndpoint .
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
        }
        """
        
        sparql_client = get_sparql_client()
        query_result = await sparql_client.query('wikidata', query, timeout=5)
        
        # Create mapping of database names to SPARQL endpoints
        sparql_databases = {}
        for binding in query_result.data.get('results', {}).get('bindings', []):
            db_name = binding.get('databaseLabel', {}).get('value', '').lower()
            sparql_endpoint = binding.get('sparqlEndpoint', {}).get('value', '')
            if db_name and sparql_endpoint:
                sparql_databases[db_name] = sparql_endpoint
        
        return sparql_databases
        
    except Exception as e:
        log.warning(f"Failed to get SPARQL databases: {e}")
        return {}


async def _get_property_metadata(property_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Get metadata for properties from Wikidata dynamically, including SPARQL endpoint discovery."""
    
    if not property_ids:
        return {}
    
    try:
        # Filter to only valid property IDs and limit to avoid timeout
        valid_props = [pid for pid in property_ids if pid.startswith('P') and pid[1:].isdigit()][:20]
        
        if not valid_props:
            return {}
        
        # Get list of databases with SPARQL endpoints
        sparql_databases = await _get_sparql_databases()
        
        # Basic SPARQL query to get property metadata
        values_clause = ' '.join(f'wd:{prop_id}' for prop_id in valid_props)
        query = f"""
        SELECT ?property ?propertyLabel ?propertyDescription ?formatterURL WHERE {{
            VALUES ?property {{ {values_clause} }}
            ?property wikibase:propertyType wikibase:ExternalId .
            OPTIONAL {{ ?property wdt:P1630 ?formatterURL }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
        }}
        """
        
        # Execute query using unified SPARQL client
        sparql_client = get_sparql_client()
        query_result = await sparql_client.query('wikidata', query, timeout=5)
        
        # Process results and match against SPARQL databases
        metadata = {}
        for binding in query_result.data.get('results', {}).get('bindings', []):
            prop_uri = binding.get('property', {}).get('value', '')
            prop_id = prop_uri.split('/')[-1] if '/' in prop_uri else ''
            
            if prop_id:
                prop_label = binding.get('propertyLabel', {}).get('value', prop_id)
                prop_description = binding.get('propertyDescription', {}).get('value', '')
                
                metadata[prop_id] = {
                    'label': prop_label,
                    'description': prop_description,
                    'formatter_url': binding.get('formatterURL', {}).get('value'),
                    'database_info': {'type': 'api_endpoint'}  # Default
                }
                
                # Pattern match property label/description against known SPARQL databases
                prop_text = f"{prop_label} {prop_description}".lower()
                for db_name, sparql_endpoint in sparql_databases.items():
                    # More precise matching - require significant overlap
                    db_words = set(db_name.split())
                    prop_words = set(prop_text.split())
                    
                    # Match if database name appears as whole words or significant overlap
                    if (db_name in prop_text and len(db_name) > 3) or \
                       (len(db_words & prop_words) >= len(db_words) * 0.7 and len(db_words) > 1):
                        metadata[prop_id]['database_info'] = {
                            'database_name': db_name.title(),
                            'sparql_endpoint': sparql_endpoint,
                            'type': 'sparql_endpoint'
                        }
                        break
        
        return metadata
        
    except Exception as e:
        log.warning(f"Failed to get property metadata: {e}")
        # Fallback to property IDs as labels
        return {prop_id: {'label': prop_id, 'description': '', 'formatter_url': None, 'database_info': {'type': 'unknown'}} 
                for prop_id in property_ids if prop_id.startswith('P')}


def _is_valid_entity_id(entity_id: str) -> bool:
    """Check if entity ID is valid format."""
    return ((entity_id.startswith('Q') or entity_id.startswith('P')) and 
            entity_id[1:].isdigit())


if __name__ == "__main__":
    describe()