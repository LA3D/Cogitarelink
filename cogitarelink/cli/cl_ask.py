"""cl_ask: Boolean ASK query execution following Claude Code patterns.

Simple tool for ASK SPARQL queries returning true/false results.
"""

from __future__ import annotations

import json
import sys
import re
from typing import Optional

import click
import httpx

from ..backend.sparql import build_prefixed_query, resolve_endpoint
from ..utils.logging import get_logger

log = get_logger("cl_ask")


def validate_ask_query(query: str) -> dict:
    """Validate ASK query syntax for LLM guardrails."""
    query = query.strip()
    
    if not query.upper().startswith("ASK"):
        return {
            "valid": False,
            "error": "Query must start with ASK",
            "suggestion": "ASK { wd:Q905695 wdt:P31 wd:Q8054 }"
        }
    
    # Check for graph pattern in braces
    if not re.search(r'ASK\s*\{.*\}', query, re.IGNORECASE | re.DOTALL):
        return {
            "valid": False,
            "error": "ASK requires graph pattern in braces { }",
            "suggestion": "ASK { wd:Q905695 wdt:P31 wd:Q8054 }"
        }
    
    # Check for basic triple pattern
    brace_content = re.search(r'ASK\s*\{(.*)\}', query, re.IGNORECASE | re.DOTALL)
    if brace_content and not brace_content.group(1).strip():
        return {
            "valid": False,
            "error": "ASK pattern cannot be empty",
            "suggestion": "ASK { wd:Q905695 wdt:P31 wd:Q8054 }"
        }
    
    return {"valid": True}


@click.command()
@click.argument('query')
@click.option('--endpoint', help='SPARQL endpoint name or URL (auto-detected if not specified)')
@click.option('--timeout', default=30, help='Query timeout in seconds (default: 30)')
def ask(query: str, endpoint: Optional[str], timeout: int):
    """Execute ASK SPARQL queries returning boolean results.
    
    Validates query syntax and returns true/false based on pattern matching.
    Perfect for existence checks and fact verification.
    
    Examples:
        cl_ask "{ wd:Q905695 wdt:P31 wd:Q8054 }"              # Check if UniProt is a database
        cl_ask "ASK { ?protein a up:Protein }" --endpoint uniprot  # Check if proteins exist
        cl_ask "{ wd:Q7240673 wdt:P352 ?uniprot }"           # Check if entity has UniProt ID
    """
    
    if not query.strip():
        click.echo(json.dumps({"error": "Query cannot be empty"}), err=True)
        sys.exit(1)
    
    # Add ASK prefix if not present for convenience
    if not query.strip().upper().startswith("ASK"):
        query = f"ASK {query.strip()}"
    
    # Validate ASK query syntax
    validation = validate_ask_query(query)
    if not validation["valid"]:
        error_output = {
            "error": validation["error"],
            "suggestion": validation["suggestion"],
            "query": query,
            "query_type": "ASK"
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
                    "query": query,
                    "query_type": "ASK",
                    "success": False
                }
                click.echo(json.dumps(error_output), err=True)
                sys.exit(1)
        else:
            endpoint_url, _ = resolve_endpoint("wikidata")
            endpoint = "wikidata"
        
        # Add prefixes automatically
        prefixed_query = build_prefixed_query(query.strip(), endpoint or "wikidata")
        
        log.debug(f"Executing ASK query on {endpoint_url}:\\n{prefixed_query}")
        
        # Execute query
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                endpoint_url,
                params={
                    "query": prefixed_query,
                    "format": "json"
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Extract boolean result
        if "boolean" in data:
            result = data["boolean"]
        else:
            # Fallback: check if any results exist
            if "results" in data and "bindings" in data["results"]:
                result = len(data["results"]["bindings"]) > 0
            else:
                result = False
        
        # Return structured result for Claude Code
        output = {
            "query": query,
            "endpoint": endpoint_url,
            "query_type": "ASK",
            "result": result,
            "success": True
        }
        click.echo(json.dumps(output))
    
    except Exception as e:
        error_output = {
            "error": str(e),
            "query": query,
            "endpoint": endpoint or "auto-detected",
            "query_type": "ASK",
            "success": False
        }
        click.echo(json.dumps(error_output), err=True)
        sys.exit(1)


if __name__ == "__main__":
    ask()