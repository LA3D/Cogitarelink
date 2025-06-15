"""cl_query: Simple SPARQL execution following Claude Code patterns.

Minimal tool for SPARQL queries - fast, simple, composable.
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import click

from ..discovery.base import discovery_engine
from ..core.debug import get_logger

log = get_logger("cl_query")


@click.command()
@click.argument('query')
@click.option('--endpoint', default='wikidata', help='SPARQL endpoint (default: wikidata)')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'text', 'csv']),
              help='Output format (default: json)')
@click.option('--limit', type=int, help='Add LIMIT clause to query (optional)')
@click.option('--timeout', default=30, help='Query timeout in seconds (default: 30)')
def query(query: str, endpoint: str, output_format: str, limit: Optional[int], timeout: int):
    """Execute SPARQL queries on endpoints.
    
    Examples:
        cl_query "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 5"
        cl_query "SELECT ?protein WHERE { ?protein a up:Protein }" --endpoint uniprot --limit 10
        cl_query "SELECT ?pathway WHERE { ?pathway a wp:Pathway }" --endpoint wikipathways --format csv
        cl_query "DESCRIBE wd:Q7240673" --endpoint wikidata
    """
    
    if not query.strip():
        click.echo('{"error": "Query cannot be empty"}', err=True)
        sys.exit(1)
    
    try:
        # Prepare query
        sparql_query = query.strip()
        
        # Add LIMIT if specified and not already present
        if limit and "LIMIT" not in sparql_query.upper():
            sparql_query += f" LIMIT {limit}"
        
        log.debug(f"Executing SPARQL query on {endpoint}:\n{sparql_query}")
        
        # Execute query
        result = discovery_engine.query_endpoint(endpoint, sparql_query)
        
        if not result["success"]:
            error_output = {
                "error": result.get("error", "Unknown error"),
                "query": query,
                "endpoint": endpoint
            }
            if output_format == "json":
                click.echo(json.dumps(error_output), err=True)
            else:
                click.echo(f"Error: {result.get('error', 'Unknown error')}", err=True)
            sys.exit(1)
        
        # Format output based on requested format
        if output_format == "json":
            output = {
                "query": query,
                "endpoint": endpoint,
                "results": result["results"],
                "head": result.get("head", {}),
                "count": len(result["results"])
            }
            click.echo(json.dumps(output, indent=2))
        
        elif output_format == "csv":
            # CSV format
            if result["results"]:
                # Get variables from first result
                variables = list(result["results"][0].keys()) if result["results"] else []
                
                # Header
                click.echo(",".join(variables))
                
                # Data rows
                for binding in result["results"]:
                    row = []
                    for var in variables:
                        value = binding.get(var, {}).get("value", "")
                        # Escape CSV values
                        if "," in value or '"' in value or "\n" in value:
                            value = '"' + value.replace('"', '""') + '"'
                        row.append(value)
                    click.echo(",".join(row))
            else:
                click.echo("# No results")
        
        else:
            # Text format
            if not result["results"]:
                click.echo("No results found.")
                return
            
            click.echo(f"Query results ({len(result['results'])} rows):")
            click.echo()
            
            # Get all unique variables across results
            all_vars = set()
            for binding in result["results"]:
                all_vars.update(binding.keys())
            all_vars = sorted(all_vars)
            
            # Calculate column widths
            col_widths = {}
            for var in all_vars:
                col_widths[var] = max(
                    len(var),
                    max((len(str(binding.get(var, {}).get("value", ""))) 
                        for binding in result["results"]), default=0)
                )
            
            # Header
            header = " | ".join(var.ljust(col_widths[var]) for var in all_vars)
            click.echo(header)
            click.echo("-" * len(header))
            
            # Data rows
            for binding in result["results"]:
                row = []
                for var in all_vars:
                    value = str(binding.get(var, {}).get("value", ""))
                    row.append(value.ljust(col_widths[var]))
                click.echo(" | ".join(row))
    
    except Exception as e:
        error_output = {
            "error": str(e),
            "query": query,
            "endpoint": endpoint
        }
        if output_format == "json":
            click.echo(json.dumps(error_output), err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    query()