#!/usr/bin/env python3
"""
cl_discover_patterns: External identifier pattern discovery for SPARQL endpoints

Implements the discovery state machine:
1. External Identifier Anchor - Use known external ID
2. URI Pattern Discovery - Find how the endpoint constructs URIs  
3. Property Enumeration - Discover available properties
4. Schema Validation - Test basic patterns work
5. Query Construction - Build informed queries

This tool enables systematic discovery for any SPARQL endpoint, especially
useful for endpoints without comprehensive documentation.
"""

from __future__ import annotations

import asyncio
import json
import sys
import click

from ..intelligence.ontology_discovery import discovery_engine
from ..core.debug import get_logger

log = get_logger("cl_discover_patterns")


@click.command()
@click.argument('external_id', required=True)
@click.option('--endpoint', default='uniprot',
              help='SPARQL endpoint: uniprot, wikipathways, idsm, etc.')
@click.option('--id-type', 
              help='Identifier type hint: uniprot, chebi, pubchem, mesh, go')
@click.option('--progress', default='silent', type=click.Choice(['silent', 'human', 'json']),
              help='Progress tracking format')
def discover_patterns(external_id: str, endpoint: str, id_type: str, progress: str):
    """
    Discover URI patterns and schema for external identifiers in SPARQL endpoints.
    
    This tool implements the experimental discovery workflow for systematic
    schema exploration of any SPARQL endpoint using known external identifiers.
    
    Examples:
        cl_discover_patterns P01308 --endpoint uniprot --id-type uniprot
        cl_discover_patterns "CHEBI:15551" --endpoint idsm --id-type chebi  
        cl_discover_patterns "GO:0008152" --endpoint some_endpoint --id-type go
        cl_discover_patterns "12345" --endpoint pubchem --id-type pubchem
    """
    asyncio.run(_discover_patterns_async(external_id, endpoint, id_type, progress))


async def _discover_patterns_async(external_id: str, endpoint: str, id_type: str, progress: str):
    """Async pattern discovery execution."""
    
    try:
        log.info(f"Starting pattern discovery for {external_id} on {endpoint}")
        
        # Execute external identifier pattern discovery
        discovery_results = await discovery_engine.discover_external_identifier_patterns(
            endpoint=endpoint,
            external_id=external_id,
            id_property=id_type,
            progress_format=progress
        )
        
        # Clean response following Claude Code patterns
        response = {
            "external_id": external_id,
            "endpoint": discovery_results["endpoint"],
            "discovery_results": {
                "uri_patterns": discovery_results.get("uri_patterns", []),
                "validated_patterns": discovery_results.get("validated_patterns", []),
                "properties": discovery_results.get("properties", []),
                "query_templates": discovery_results.get("query_templates", {}),
                "discovery_steps": len(discovery_results.get("discovery_metadata", {}).get("discovery_steps", []))
            }
        }
        
        # Add error information if discovery failed
        if "error" in discovery_results:
            response["error"] = discovery_results["error"]
            response["discovery_results"]["status"] = "failed"
        else:
            response["discovery_results"]["status"] = "success"
            
        # Add summary statistics
        stats = response["discovery_results"]
        if stats["validated_patterns"]:
            best_pattern = stats["validated_patterns"][0]
            response["discovery_results"]["best_pattern"] = {
                "pattern": best_pattern.get("pattern", ""),
                "example_uri": best_pattern.get("example_uri", ""),
                "confidence": best_pattern.get("confidence", 0),
                "property_count": best_pattern.get("property_count", 0)
            }
        
        click.echo(json.dumps(response, indent=2))
        
    except Exception as e:
        log.error(f"Pattern discovery failed: {e}")
        error_response = {
            "external_id": external_id,
            "endpoint": endpoint,
            "error": f"Pattern discovery failed: {str(e)}",
            "suggestions": [
                "Check if external identifier exists in the endpoint",
                "Verify endpoint is accessible and responding",
                "Try a different identifier type hint",
                "Use simpler discovery methods first"
            ]
        }
        click.echo(json.dumps(error_response, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    discover_patterns()