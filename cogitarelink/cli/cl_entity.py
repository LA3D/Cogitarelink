#!/usr/bin/env python3
"""
cl_entity: String→Entity Resolution

Converts natural language strings to Wikidata QIDs/PIDs with confidence scoring.
Simplified for Claude Code patterns - clean data output only.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Optional, List, Dict, Any

import click

from ..adapters.wikidata_client import WikidataClient
from ..core.debug import get_logger

log = get_logger("cl_entity")


@click.command()
@click.argument('search_string', required=True)
@click.option('--type', 'search_type', type=click.Choice(['auto', 'entity', 'property']), 
              default='auto', help='Search type: auto-detect, entities only, or properties only')
@click.option('--limit', default=5, help='Maximum candidates to return (1-20)')
@click.option('--domain-hint', help='Domain hint: biology, corporate, geography, etc.')
def entity(search_string: str, search_type: str, limit: int, domain_hint: Optional[str]):
    """
    Convert natural language to semantic identifiers (QIDs/PIDs).
    
    Examples:
        cl_entity "insulin" --domain-hint biology
        cl_entity "Lockheed Martin" --domain-hint corporate  
        cl_entity "UniProt ID" --type property
    """
    asyncio.run(_entity_async(search_string, search_type, limit, domain_hint))


async def _entity_async(search_string: str, search_type: str, limit: int, domain_hint: Optional[str]):
    """Async entity resolution with clean output."""
    
    try:
        # Initialize Wikidata client
        client = WikidataClient()
        
        # Validate limit
        if not 1 <= limit <= 20:
            limit = 5
        
        log.info(f"Resolving entity: '{search_string}' (type: {search_type}, domain: {domain_hint})")
        
        # Search entities and properties based on type
        candidates = []
        search_strategy = {"searched_entities": False, "searched_properties": False, "domain_hint": domain_hint}
        
        if search_type in ['auto', 'entity']:
            entity_results = await _search_entities(client, search_string, domain_hint, limit)
            candidates.extend(entity_results)
            search_strategy["searched_entities"] = True
        
        if search_type in ['auto', 'property'] or 'id' in search_string.lower():
            property_results = await _search_properties(client, search_string, limit)
            candidates.extend(property_results)
            search_strategy["searched_properties"] = True
        
        # Sort by confidence and limit results
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        candidates = candidates[:limit]
        
        # Clean output - just the data Claude needs
        result = {
            "query": search_string,
            "candidates": candidates,
            "search_strategy": search_strategy
        }
        
        click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        log.error(f"Entity resolution failed: {e}")
        # Simple error output
        error_result = {
            "query": search_string,
            "candidates": [],
            "error": str(e)
        }
        click.echo(json.dumps(error_result, indent=2))
        sys.exit(1)


async def _search_entities(client: WikidataClient, search_string: str, domain_hint: Optional[str], limit: int) -> List[Dict[str, Any]]:
    """Search for entities with domain-aware scoring."""
    
    candidates = []
    
    try:
        # Basic entity search (using working API)
        results = await client.search_entities(
            query=search_string, 
            language='en', 
            limit=limit,
            entity_type='item'
        )
        
        for result in results.get('search', [])[:limit]:
            candidate = {
                "id": result.get('id', ''),
                "type": "entity", 
                "label": result.get('label', ''),
                "description": result.get('description', ''),
                "confidence": _calculate_confidence(search_string, result, domain_hint)
            }
            candidates.append(candidate)
            
    except Exception as e:
        log.warning(f"Entity search failed: {e}")
    
    return candidates


async def _search_properties(client: WikidataClient, search_string: str, limit: int) -> List[Dict[str, Any]]:
    """Search for properties."""
    
    candidates = []
    
    try:
        # Property search (using working API)
        results = await client.search_entities(
            query=search_string,
            language='en',
            limit=limit,
            entity_type='property'
        )
        
        for result in results.get('search', [])[:limit]:
            candidate = {
                "id": result.get('id', ''),
                "type": "property",
                "label": result.get('label', ''),
                "description": result.get('description', ''),
                "confidence": _calculate_confidence(search_string, result, None)
            }
            candidates.append(candidate)
            
    except Exception as e:
        log.warning(f"Property search failed: {e}")
    
    return candidates


def _calculate_confidence(search_string: str, result: Dict[str, Any], domain_hint: Optional[str]) -> float:
    """Calculate confidence score with enhanced domain-aware patterns (extracted from complex version)."""
    
    confidence = 0.0
    search_lower = search_string.lower()
    label = result.get('label', '').lower()
    description = result.get('description', '').lower()
    
    # Exact label match gets high score
    if search_lower == label:
        confidence += 0.8
    elif search_lower in label or label in search_lower:
        confidence += 0.5
    
    # Partial matches using word intersection
    search_words = set(search_lower.split())
    label_words = set(label.split())
    if search_words & label_words:
        confidence += 0.3 * len(search_words & label_words) / len(search_words)
    
    # Description relevance
    if search_lower in description:
        confidence += 0.2
    elif any(word in description for word in search_lower.split()):
        confidence += 0.1
    
    # Enhanced domain hint bonus (anti-hallucination patterns)
    if domain_hint and description:
        domain_keywords = {
            'biology': ['protein', 'gene', 'organism', 'biological', 'molecular', 'species', 'enzyme', 'cellular'],
            'corporate': ['company', 'corporation', 'organization', 'business', 'enterprise', 'firm', 'industry'],
            'geography': ['location', 'place', 'country', 'city', 'geographic', 'region', 'territory', 'administrative']
        }
        
        if domain_hint in domain_keywords:
            for keyword in domain_keywords[domain_hint]:
                if keyword in description:
                    confidence += 0.2
                    break
    
    return min(confidence, 1.0)


if __name__ == "__main__":
    entity()