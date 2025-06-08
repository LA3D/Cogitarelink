#!/usr/bin/env python3
"""
cl_property: Simple property analysis tool

Analyze Wikidata properties without expensive usage queries.
Fast property metadata and examples.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Optional, List, Dict, Any

import click

from ..adapters.wikidata_client import WikidataClient
from ..adapters.unified_sparql_client import get_sparql_client
from ..core.debug import get_logger

log = get_logger("cl_property")


@click.command()
@click.argument('property_identifier', required=True)
@click.option('--include-examples', is_flag=True, default=True,
              help='Include usage examples (fast query)')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
def property(property_identifier: str, include_examples: bool, output_format: str):
    """
    Analyze Wikidata properties with metadata and examples.
    
    Examples:
        cl_property P352
        cl_property P31 --include-examples
        cl_property P625 --format human
    """
    asyncio.run(_property_async(property_identifier, include_examples, output_format))


async def _property_async(property_identifier: str, include_examples: bool, output_format: str):
    """Async property analysis."""
    
    start_time = time.time()
    
    try:
        # Validate property identifier
        if not _is_valid_property_identifier(property_identifier):
            _output_error(f"Invalid property identifier: {property_identifier}. Expected format: P123", output_format)
            return
        
        # Initialize clients
        wikidata_client = WikidataClient(timeout=10)
        
        # Get property metadata
        log.info(f"Analyzing property: {property_identifier}")
        property_metadata = await _get_property_metadata(property_identifier, wikidata_client)
        
        # Get usage examples (fast query)
        examples = {}
        if include_examples:
            examples = await _get_property_examples(property_identifier)
        
        # Build response
        execution_time = int((time.time() - start_time) * 1000)
        
        response = {
            'success': True,
            'data': {
                'property': {
                    'id': property_identifier,
                    'label': property_metadata.get('label', ''),
                    'description': property_metadata.get('description', ''),
                    'datatype': property_metadata.get('datatype', ''),
                    'wikidata_url': f"https://www.wikidata.org/wiki/Property:{property_identifier}"
                },
                'metadata': property_metadata,
                'examples': examples
            },
            'suggestions': _generate_suggestions(property_identifier, property_metadata, examples),
            'execution_time_ms': execution_time
        }
        
        # Output response
        if output_format == 'human':
            _print_human_readable(response)
        else:
            click.echo(json.dumps(response, indent=2))
            
    except Exception as e:
        log.error(f"Property analysis failed: {e}")
        _output_error(f"Property analysis failed: {str(e)}", output_format)
        sys.exit(1)


async def _get_property_metadata(property_id: str, client: WikidataClient) -> Dict[str, Any]:
    """Get basic property metadata from Wikidata."""
    
    metadata = {
        'label': '',
        'description': '', 
        'datatype': '',
        'domain': [],
        'related_properties': []
    }
    
    try:
        # Get property data
        prop_data = await client.get_entities([property_id])
        
        if property_id not in prop_data.get('entities', {}):
            return metadata
        
        entity_data = prop_data['entities'][property_id]
        
        # Extract basic info
        metadata['label'] = entity_data.get('labels', {}).get('en', {}).get('value', '')
        metadata['description'] = entity_data.get('descriptions', {}).get('en', {}).get('value', '')
        metadata['datatype'] = entity_data.get('datatype', '')
        
        # Extract domain from claims (limited extraction)
        claims = entity_data.get('claims', {})
        
        # P1629: subject item of this property (domain)
        if 'P1629' in claims:
            metadata['domain'] = [
                claim['mainsnak']['datavalue']['value']['id']
                for claim in claims['P1629'][:3]  # Limit to first 3
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']
            ]
        
        # P1647: subproperty of (related properties)  
        if 'P1647' in claims:
            metadata['related_properties'] = [
                claim['mainsnak']['datavalue']['value']['id']
                for claim in claims['P1647'][:3]  # Limit to first 3
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']
            ]
    
    except Exception as e:
        log.warning(f"Failed to get property metadata: {e}")
    
    return metadata


async def _get_property_examples(property_id: str) -> Dict[str, Any]:
    """Get usage examples with simple, fast query."""
    
    examples = {
        'sample_entities': [],
        'sample_values': [],
        'example_count': 0
    }
    
    try:
        # Simple, fast SPARQL query for examples
        query = f"""
        SELECT ?entity ?entityLabel ?value WHERE {{
            ?entity wdt:{property_id} ?value .
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
        }}
        LIMIT 10
        """
        
        sparql_client = get_sparql_client()
        query_result = await sparql_client.query('wikidata', query, timeout=3)
        bindings = query_result.data.get('results', {}).get('bindings', [])
        
        if bindings:
            examples['example_count'] = len(bindings)
            
            for binding in bindings:
                entity_info = {
                    'entity_id': binding.get('entity', {}).get('value', '').split('/')[-1],
                    'entity_label': binding.get('entityLabel', {}).get('value', ''),
                    'value': binding.get('value', {}).get('value', '')
                }
                examples['sample_entities'].append(entity_info)
                
                # Collect unique values
                value = binding.get('value', {}).get('value', '')
                if value and value not in examples['sample_values']:
                    examples['sample_values'].append(value)
    
    except Exception as e:
        log.warning(f"Failed to get property examples: {e}")
        examples['error'] = str(e)
    
    return examples


def _is_valid_property_identifier(prop_id: str) -> bool:
    """Check if property identifier is valid."""
    return prop_id.startswith('P') and prop_id[1:].isdigit()


def _generate_suggestions(property_id: str, metadata: Dict[str, Any], examples: Dict[str, Any]) -> List[str]:
    """Generate next-step suggestions."""
    
    suggestions = []
    
    # SPARQL query suggestions
    suggestions.append(f'cl_sparql "SELECT ?s ?o WHERE {{ ?s wdt:{property_id} ?o }} LIMIT 10"')
    
    # Entity exploration suggestions
    if examples.get('sample_entities'):
        first_entity = examples['sample_entities'][0]['entity_id']
        suggestions.append(f'cl_describe {first_entity}')
    
    # Domain-specific suggestions based on property type
    label = metadata.get('label', '').lower()
    description = metadata.get('description', '').lower()
    
    if any(bio in label + description for bio in ['protein', 'gene', 'uniprot', 'biological']):
        suggestions.extend([
            'cl_follow for biological cross-references',
            'cl_resolve for external database links'
        ])
    elif any(geo in label + description for geo in ['location', 'coordinate', 'place']):
        suggestions.append('cl_sparql for geographic queries')
    
    return suggestions[:5]


def _print_human_readable(response: Dict[str, Any]):
    """Print human-readable output."""
    
    if not response['success']:
        click.echo(f"❌ Error: {response['error']}")
        return
    
    data = response['data']
    prop = data['property']
    metadata = data['metadata']
    examples = data['examples']
    
    click.echo(f"🏷️  Property: {prop['label']} ({prop['id']})")
    click.echo(f"📄 Description: {prop['description']}")
    click.echo(f"🔗 Wikidata: {prop['wikidata_url']}")
    click.echo(f"📊 Datatype: {prop['datatype']}")
    click.echo()
    
    if metadata.get('domain'):
        click.echo(f"🎯 Domain: {', '.join(metadata['domain'])}")
    
    if metadata.get('related_properties'):
        click.echo(f"🔗 Related: {', '.join(metadata['related_properties'])}")
    
    if examples.get('sample_entities'):
        click.echo(f"\n📋 Usage Examples ({examples['example_count']} shown):")
        for example in examples['sample_entities'][:5]:
            click.echo(f"   • {example['entity_label']} ({example['entity_id']}) = {example['value']}")
    
    if examples.get('sample_values'):
        click.echo(f"\n🔢 Sample Values:")
        for value in examples['sample_values'][:5]:
            click.echo(f"   • {value}")
    
    if response['suggestions']:
        click.echo("\n💡 Next steps:")
        for suggestion in response['suggestions']:
            click.echo(f"   • {suggestion}")


def _output_error(message: str, output_format: str):
    """Output error in requested format."""
    
    error_response = {
        'success': False,
        'error': message,
        'suggestions': [
            'Check property ID format (P123456)',
            'Verify property exists in Wikidata',
            'Try: cl_wikidata search "property name"'
        ]
    }
    
    if output_format == 'human':
        click.echo(f"❌ Error: {message}")
    else:
        click.echo(json.dumps(error_response, indent=2))


if __name__ == "__main__":
    property()