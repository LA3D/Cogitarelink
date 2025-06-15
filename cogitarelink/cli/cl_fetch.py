"""cl_fetch: Simple entity data retrieval following Claude Code patterns.

Minimal tool for getting entity data - fast, simple, composable.
"""

from __future__ import annotations

import json
import sys
from typing import Optional, Dict, Any

import click

from ..discovery.base import discovery_engine
from ..core.debug import get_logger

log = get_logger("cl_fetch")


def fetch_wikidata(entity_id: str) -> Dict[str, Any]:
    """Fetch Wikidata entity using Wikidata API."""
    import httpx
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # Use Wikidata API for fast entity fetch
            response = client.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbgetentities",
                    "ids": entity_id,
                    "format": "json",
                    "languages": "en"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if "entities" not in data or entity_id not in data["entities"]:
                return {}
            
            entity = data["entities"][entity_id]
            
            # Extract basic info
            result = {
                "id": entity_id,
                "type": "entity",
                "labels": entity.get("labels", {}),
                "descriptions": entity.get("descriptions", {}),
                "claims": entity.get("claims", {}),
                "sitelinks": entity.get("sitelinks", {})
            }
            
            return result
            
    except Exception as e:
        log.error(f"Wikidata fetch failed: {e}")
        return {}


def fetch_sparql_entity(endpoint: str, entity_id: str) -> Dict[str, Any]:
    """Fetch entity data using SPARQL DESCRIBE query."""
    discovery_result = discovery_engine.discover(endpoint)
    
    # Build PREFIX declarations
    prefix_lines = []
    for prefix, uri in discovery_result.prefixes.items():
        prefix_lines.append(f"PREFIX {prefix}: <{uri}>")
    
    # Construct entity URI based on endpoint patterns
    if endpoint == "wikipathways":
        entity_uri = f"https://identifiers.org/wikipathways/{entity_id}"
    elif endpoint == "uniprot":
        entity_uri = f"http://purl.uniprot.org/uniprot/{entity_id}"
    else:
        # Try to construct URI from known patterns
        base_uri = discovery_result.prefixes.get("", "")
        if base_uri:
            entity_uri = f"{base_uri}{entity_id}"
        else:
            entity_uri = f"<{entity_id}>"  # Assume full URI provided
    
    # Use DESCRIBE query for comprehensive entity data
    sparql_query = f"""DESCRIBE <{entity_uri}>"""
    
    # Combine prefixes and query
    full_query = "\n".join(prefix_lines) + "\n\n" + sparql_query
    
    log.debug(f"Executing DESCRIBE query on {endpoint}:\\n{full_query}")
    
    result = discovery_engine.query_endpoint(endpoint, full_query)
    
    if not result["success"]:
        log.error(f"SPARQL fetch failed: {result.get('error', 'Unknown error')}")
        return {}
    
    # Convert SPARQL results to structured format
    entity_data = {
        "id": entity_id,
        "uri": entity_uri,
        "type": "entity",
        "properties": {}
    }
    
    # Process DESCRIBE results
    for binding in result["results"]:
        predicate = binding.get("predicate", {}).get("value", "")
        obj = binding.get("object", {})
        
        if predicate:
            prop_key = predicate.split("/")[-1]  # Extract property name
            
            if prop_key not in entity_data["properties"]:
                entity_data["properties"][prop_key] = []
            
            if obj.get("type") == "literal":
                entity_data["properties"][prop_key].append({
                    "value": obj.get("value", ""),
                    "type": "literal",
                    "datatype": obj.get("datatype"),
                    "language": obj.get("xml:lang")
                })
            else:
                entity_data["properties"][prop_key].append({
                    "value": obj.get("value", ""),
                    "type": "uri"
                })
    
    return entity_data


@click.command()
@click.argument('entity_id')
@click.option('--endpoint', default='wikidata', help='Data endpoint (default: wikidata)')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'text']),
              help='Output format (default: json)')
@click.option('--properties', help='Comma-separated list of properties to fetch (optional)')
def fetch(entity_id: str, endpoint: str, output_format: str, properties: Optional[str]):
    """Simple entity data retrieval - returns full entity data.
    
    Examples:
        cl_fetch Q7240673
        cl_fetch Q7240673 --properties labels,descriptions
        cl_fetch WP4846_r120585 --endpoint wikipathways
        cl_fetch P04637 --endpoint uniprot --format text
    """
    
    if not entity_id.strip():
        click.echo('{"error": "Entity ID cannot be empty"}', err=True)
        sys.exit(1)
    
    try:
        # Fetch based on endpoint
        if endpoint == "wikidata":
            result = fetch_wikidata(entity_id)
        else:
            result = fetch_sparql_entity(endpoint, entity_id)
        
        if not result:
            result = {"error": f"Entity {entity_id} not found", "entity_id": entity_id, "endpoint": endpoint}
        
        # Filter properties if requested
        if properties and "error" not in result:
            prop_list = [p.strip() for p in properties.split(",")]
            filtered_result = {"id": result.get("id"), "type": result.get("type")}
            
            for prop in prop_list:
                if prop in result:
                    filtered_result[prop] = result[prop]
            
            result = filtered_result
        
        # Output results
        if output_format == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            # Simple text format
            if "error" in result:
                click.echo(f"Error: {result['error']}")
            else:
                click.echo(f"Entity: {result.get('id', 'Unknown')}")
                
                # Show labels if available
                if "labels" in result and result["labels"]:
                    en_label = result["labels"].get("en", {}).get("value", "")
                    if en_label:
                        click.echo(f"Label: {en_label}")
                
                # Show description if available  
                if "descriptions" in result and result["descriptions"]:
                    en_desc = result["descriptions"].get("en", {}).get("value", "")
                    if en_desc:
                        click.echo(f"Description: {en_desc}")
                
                # Show property count
                if "claims" in result:
                    click.echo(f"Properties: {len(result['claims'])}")
                elif "properties" in result:
                    click.echo(f"Properties: {len(result['properties'])}")
    
    except Exception as e:
        error_output = {
            "error": str(e),
            "entity_id": entity_id,
            "endpoint": endpoint
        }
        if output_format == "json":
            click.echo(json.dumps(error_output), err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    fetch()