"""cl_describe: Validated DESCRIBE query execution following Claude Code patterns.

Simple tool for DESCRIBE SPARQL queries with entity validation.
"""

from __future__ import annotations

import json
import sys
import re
from typing import Optional

import click
import httpx
from rdflib import Graph
from pyld import jsonld

from ..backend.sparql import build_prefixed_query, get_entity_uri, find_endpoint_for_entity, resolve_endpoint
from ..utils.logging import get_logger

log = get_logger("cl_describe")


def validate_describe_entity(entity: str) -> dict:
    """Validate entity ID for DESCRIBE query guardrails."""
    entity = entity.strip()
    
    if not entity:
        return {
            "valid": False,
            "error": "Entity ID cannot be empty",
            "suggestion": "Use entity ID like Q905695, P352, or full URI"
        }
    
    # Check for valid entity patterns
    if (entity.startswith(("Q", "P")) or  # Wikidata IDs
        entity.startswith(("UP", "A", "O")) or  # UniProt IDs  
        entity.startswith("WP") or  # WikiPathways IDs
        entity.startswith("http") or  # Full URIs
        entity.startswith(("wd:", "up:", "wp:", "dbo:", "dbr:")) or  # Prefixed entities
        ":" in entity):  # Any prefixed entity
        return {"valid": True}
    
    # Allow simple alphanumeric IDs that might be valid for some endpoints
    if re.match(r'^[A-Za-z0-9_-]+$', entity):
        return {"valid": True}
    
    return {
        "valid": False,
        "error": f"Invalid entity ID format: {entity}",
        "suggestion": "Use formats like Q905695, P352, wd:Q905695, or http://www.wikidata.org/entity/Q905695"
    }


@click.command()
@click.argument('entity')
@click.option('--endpoint', help='SPARQL endpoint name or URL (auto-detected if not specified)')
@click.option('--timeout', default=30, help='Query timeout in seconds (default: 30)')
def describe(entity: str, endpoint: Optional[str], timeout: int):
    """Execute DESCRIBE SPARQL queries with entity validation.
    
    Validates entity ID format and constructs proper DESCRIBE queries.
    Returns complete RDF data about the specified entity.
    
    Examples:
        cl_describe Q905695                    # Wikidata entity
        cl_describe P352                       # Wikidata property  
        cl_describe UP000005640 --endpoint uniprot     # UniProt entity
        cl_describe wd:Q905695                 # Prefixed entity
    """
    
    # Validate entity ID
    validation = validate_describe_entity(entity)
    if not validation["valid"]:
        error_output = {
            "error": validation["error"],
            "suggestion": validation["suggestion"],
            "entity": entity,
            "query_type": "DESCRIBE",
            "success": False
        }
        click.echo(json.dumps(error_output), err=True)
        sys.exit(1)
    
    try:
        # Determine endpoint using unified resolution
        if endpoint:
            try:
                endpoint_url, _ = resolve_endpoint(endpoint)
            except ValueError as e:
                error_output = {
                    "error": str(e),
                    "entity": entity,
                    "query_type": "DESCRIBE",
                    "success": False
                }
                click.echo(json.dumps(error_output), err=True)
                sys.exit(1)
        else:
            # Auto-detect endpoint based on entity ID
            endpoint_url = find_endpoint_for_entity(entity)
            if not endpoint_url:
                endpoint_url, _ = resolve_endpoint("wikidata")
            endpoint = "auto-detected"
        
        # Construct entity URI
        entity_uri = get_entity_uri(entity, endpoint_url)
        
        # Build DESCRIBE query
        sparql_query = f"DESCRIBE <{entity_uri}>"
        
        # Add prefixes automatically
        prefixed_query = build_prefixed_query(sparql_query, endpoint if endpoint != "auto-detected" else "wikidata")
        
        log.debug(f"Executing DESCRIBE query on {endpoint_url}:\\n{prefixed_query}")
        
        # Execute query - use appropriate Accept header based on endpoint
        if "qlever" in endpoint_url.lower():
            accept_header = "text/turtle"
            rdf_format = "turtle"
        elif "query.wikidata.org" in endpoint_url.lower():
            accept_header = "application/rdf+xml"
            rdf_format = "xml"
        else:
            # Default to turtle for most SPARQL endpoints
            accept_header = "text/turtle"
            rdf_format = "turtle"
        
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                endpoint_url,
                params={"query": prefixed_query},
                headers={"Accept": accept_header}
            )
            response.raise_for_status()
            rdf_data = response.text
        
        # Parse RDF data with rdflib using appropriate format
        graph = Graph()
        graph.parse(data=rdf_data, format=rdf_format)
        
        # Convert to JSON-LD for Claude Code
        jsonld_data = graph.serialize(format="json-ld")
        parsed_jsonld = json.loads(jsonld_data)
        
        # Return structured JSON-LD for Claude Code
        output = {
            "entity": entity,
            "entity_uri": entity_uri,
            "endpoint": endpoint_url,
            "query_type": "DESCRIBE",
            "format": "json-ld",
            "data": parsed_jsonld,
            "triple_count": len(graph),
            "success": True
        }
        click.echo(json.dumps(output))
    
    except Exception as e:
        error_output = {
            "error": str(e),
            "entity": entity,
            "endpoint": endpoint or "auto-detected",
            "query_type": "DESCRIBE",
            "success": False
        }
        click.echo(json.dumps(error_output), err=True)
        sys.exit(1)


if __name__ == "__main__":
    describe()