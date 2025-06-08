#!/usr/bin/env python3
"""
cl_discover: Simple resource discovery tool

Basic discovery functionality without the over-engineered discovery engine.
"""

from __future__ import annotations

import json
import sys
from typing import Optional, List, Dict, Any

import click

from ..core.debug import get_logger

log = get_logger("cl_discover")


@click.command()
@click.argument('resource_identifier', required=True)
@click.option('--domains', multiple=True, help='Domain hints (biology, corporate, geography)')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
def discover(resource_identifier: str, domains: List[str], output_format: str):
    """
    Simple resource discovery with basic metadata detection.
    
    Examples:
        cl_discover "insulin" --domains biology
        cl_discover "Q28209" --domains biology
        cl_discover "P352"
    """
    
    try:
        # Simple discovery logic
        resource_type = _detect_resource_type(resource_identifier, domains)
        domain_context = list(domains) if domains else [_infer_domain(resource_identifier)]
        
        # Build response
        response = {
            'success': True,
            'data': {
                'resource_identifier': resource_identifier,
                'resource_type': resource_type,
                'domain_context': domain_context,
                'discovery_method': 'pattern_matching',
                'confidence_score': 0.7 if domains else 0.5
            },
            'suggestions': _generate_suggestions(resource_identifier, resource_type, domain_context)
        }
        
        # Output response
        if output_format == 'human':
            _print_human_readable(response)
        else:
            click.echo(json.dumps(response, indent=2))
            
    except Exception as e:
        error_response = {
            'success': False,
            'error': str(e),
            'suggestions': [
                'Check resource identifier format',
                'Add domain hints with --domains',
                f'Try: cl_entity "{resource_identifier}" for entity resolution'
            ]
        }
        
        if output_format == 'human':
            click.echo(f"Error: {e}")
        else:
            click.echo(json.dumps(error_response, indent=2))
        sys.exit(1)


def _detect_resource_type(resource_id: str, domain_hints: List[str]) -> str:
    """Detect resource type from identifier patterns."""
    
    # Wikidata patterns
    if resource_id.startswith('Q') and resource_id[1:].isdigit():
        return 'wikidata_entity'
    elif resource_id.startswith('P') and resource_id[1:].isdigit():
        return 'wikidata_property'
    
    # URL patterns
    if resource_id.startswith(('http://', 'https://')):
        return 'uri'
    
    # Domain-specific patterns
    if any(bio in domain_hints for bio in ['biology', 'bioschemas']):
        if 'uniprot' in resource_id.lower():
            return 'protein_identifier'
        elif 'chebi' in resource_id.lower():
            return 'chemical_identifier'
        elif 'pdb' in resource_id.lower():
            return 'structure_identifier'
    
    # Default
    return 'identifier'


def _infer_domain(resource_id: str) -> str:
    """Infer domain from resource identifier."""
    
    resource_lower = resource_id.lower()
    
    # Biology indicators
    if any(bio in resource_lower for bio in ['protein', 'gene', 'uniprot', 'pdb', 'chebi']):
        return 'biology'
    
    # Corporate indicators  
    if any(corp in resource_lower for corp in ['company', 'corp', 'inc', 'ltd']):
        return 'corporate'
    
    # Geography indicators
    if any(geo in resource_lower for geo in ['city', 'country', 'place', 'location']):
        return 'geography'
    
    return 'general'


def _generate_suggestions(resource_id: str, resource_type: str, domain_context: List[str]) -> List[str]:
    """Generate next-step suggestions."""
    
    suggestions = []
    
    # Entity/Property specific suggestions
    if resource_type == 'wikidata_entity':
        suggestions.extend([
            f'cl_describe {resource_id}',
            f'cl_follow {resource_id}'
        ])
    elif resource_type == 'wikidata_property':
        suggestions.append(f'cl_property {resource_id}')
    else:
        suggestions.append(f'cl_entity "{resource_id}"')
    
    # Domain-specific suggestions
    if 'biology' in domain_context:
        suggestions.extend([
            'cl_sparql for biological queries',
            'cl_resolve for cross-references'
        ])
    elif 'corporate' in domain_context:
        suggestions.extend([
            'cl_sparql for corporate relationships',
            'cl_follow for SEC/financial data'
        ])
    
    return suggestions


def _print_human_readable(response: Dict[str, Any]):
    """Print human-readable output."""
    
    if not response['success']:
        click.echo(f"❌ Error: {response['error']}")
        return
    
    data = response['data']
    
    click.echo(f"🔍 Discovery: '{data['resource_identifier']}'")
    click.echo(f"📋 Type: {data['resource_type']}")
    click.echo(f"🏷️ Domain: {', '.join(data['domain_context'])}")
    click.echo(f"🎯 Confidence: {data['confidence_score']:.1f}")
    
    if response['suggestions']:
        click.echo("\n💡 Next steps:")
        for suggestion in response['suggestions']:
            click.echo(f"   • {suggestion}")


if __name__ == "__main__":
    discover()