"""cl_discover: Endpoint capability discovery following Claude Code patterns.

Minimal tool for discovering endpoint capabilities - fast, simple, composable.
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import click

from ..discovery.base import discovery_engine
from ..core.debug import get_logger

log = get_logger("cl_discover")


@click.command()
@click.argument('endpoint')
@click.option('--capabilities', is_flag=True, help='Show search and query capabilities')
@click.option('--schema', is_flag=True, help='Show schema information (prefixes, classes)')
@click.option('--patterns', is_flag=True, help='Show query patterns')
@click.option('--guidance', is_flag=True, help='Show usage guidance')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'text']),
              help='Output format (default: json)')
def discover(endpoint: str, capabilities: bool, schema: bool, patterns: bool, 
             guidance: bool, output_format: str):
    """Discover endpoint capabilities and schema information.
    
    Examples:
        cl_discover wikidata
        cl_discover wikipathways --capabilities
        cl_discover uniprot --schema --format text
        cl_discover unknown-endpoint --guidance
    """
    
    if not endpoint.strip():
        click.echo('{"error": "Endpoint cannot be empty"}', err=True)
        sys.exit(1)
    
    try:
        # Discover endpoint
        result = discovery_engine.discover(endpoint)
        
        # Build output based on flags (default to all if none specified)
        if not any([capabilities, schema, patterns, guidance]):
            # Show everything by default
            capabilities = schema = patterns = guidance = True
        
        output = {
            "endpoint": result.endpoint,
            "url": result.url
        }
        
        if capabilities:
            # Determine available capabilities
            search_methods = []
            if endpoint == "wikidata":
                search_methods.append({
                    "method": "api",
                    "type": "wbsearchentities",
                    "description": "Fast entity search via Wikidata API",
                    "recommended": True
                })
            
            if result.patterns:
                search_methods.append({
                    "method": "sparql",
                    "type": "text_search", 
                    "description": "SPARQL text search with CONTAINS filters",
                    "recommended": False
                })
            
            query_methods = ["sparql"]
            if endpoint == "wikidata":
                query_methods.extend(["api", "wbgetentities"])
            
            output["capabilities"] = {
                "search_methods": search_methods,
                "query_methods": query_methods,
                "supports_describe": True,
                "supports_introspection": endpoint in discovery_engine.KNOWN_ENDPOINTS
            }
        
        if schema:
            output["schema"] = {
                "prefixes": result.prefixes,
                "known_classes": _extract_known_classes(endpoint),
                "known_properties": _extract_known_properties(endpoint)
            }
        
        if patterns:
            output["patterns"] = result.patterns
        
        if guidance:
            output["guidance"] = result.guidance
        
        # Output results
        if output_format == "json":
            click.echo(json.dumps(output, indent=2))
        else:
            # Simple text format
            click.echo(f"Endpoint: {result.endpoint}")
            click.echo(f"URL: {result.url}")
            
            if capabilities and "capabilities" in output:
                caps = output["capabilities"]
                click.echo(f"\nSearch Methods:")
                for method in caps["search_methods"]:
                    rec = " (recommended)" if method.get("recommended") else ""
                    click.echo(f"  - {method['method']}: {method['description']}{rec}")
                
                click.echo(f"\nQuery Methods: {', '.join(caps['query_methods'])}")
                click.echo(f"Supports DESCRIBE: {caps['supports_describe']}")
                click.echo(f"Known endpoint: {caps['supports_introspection']}")
            
            if schema and "schema" in output:
                click.echo(f"\nPrefixes: {len(output['schema']['prefixes'])}")
                for prefix, uri in output["schema"]["prefixes"].items():
                    click.echo(f"  {prefix}: <{uri}>")
            
            if patterns and "patterns" in output:
                click.echo(f"\nQuery Patterns: {len(output['patterns'])}")
                for pattern_name in output["patterns"]:
                    click.echo(f"  - {pattern_name}")
            
            if guidance and "guidance" in output:
                click.echo(f"\nGuidance:")
                for tip in output["guidance"]:
                    click.echo(f"  - {tip}")
    
    except Exception as e:
        error_output = {
            "error": str(e),
            "endpoint": endpoint
        }
        if output_format == "json":
            click.echo(json.dumps(error_output), err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _extract_known_classes(endpoint: str) -> list:
    """Extract known classes for endpoint."""
    known_classes = {
        "wikidata": ["wdt:Q5", "wdt:Q7187", "wdt:Q8054"],  # human, gene, protein
        "wikipathways": ["wp:Pathway", "wp:DataNode"],
        "uniprot": ["up:Protein", "up:Gene"]
    }
    return known_classes.get(endpoint, [])


def _extract_known_properties(endpoint: str) -> list:
    """Extract known properties for endpoint."""
    known_props = {
        "wikidata": ["wdt:P31", "wdt:P279", "wdt:P352", "wdt:P703"],  # instance of, subclass, UniProt ID, organism
        "wikipathways": ["dc:title", "wp:organism", "wp:pathwayOntology"],
        "uniprot": ["up:recommendedName", "up:organism", "up:sequence"]
    }
    return known_props.get(endpoint, [])


if __name__ == "__main__":
    discover()