"""cl_select: Validated SELECT query execution following Claude Code patterns.

Simple tool for SELECT SPARQL queries with WHERE clause validation.
"""

from __future__ import annotations

import json
import sys
import re
from typing import Optional

import click
import httpx

from ..backend.sparql import discover_sparql_endpoints, build_prefixed_query
from ..backend.cache import cache_manager
from ..utils.logging import get_logger

log = get_logger("cl_select")


def validate_select_query(query: str) -> dict:
    """Validate SELECT query syntax for LLM guardrails."""
    query = query.strip()
    
    if not query.upper().startswith("SELECT"):
        return {
            "valid": False,
            "error": "Query must start with SELECT",
            "suggestion": "SELECT ?s ?p ?o WHERE { ?s ?p ?o }"
        }
    
    if "WHERE" not in query.upper():
        return {
            "valid": False,
            "error": "SELECT queries require WHERE clause",
            "suggestion": f"{query} WHERE {{ ?s ?p ?o }}"
        }
    
    # Check for basic syntax elements
    if not re.search(r'\?\w+', query):
        return {
            "valid": False,
            "error": "SELECT queries require variables (e.g., ?s, ?p, ?o)",
            "suggestion": "SELECT ?s ?p ?o WHERE { ?s ?p ?o }"
        }
    
    if not re.search(r'WHERE\s*\{.*\}', query, re.IGNORECASE | re.DOTALL):
        return {
            "valid": False,
            "error": "WHERE clause must contain graph pattern in braces { }",
            "suggestion": f"{query.split('WHERE')[0]}WHERE {{ ?s ?p ?o }}"
        }
    
    return {"valid": True}


@click.command()
@click.argument('query')
@click.option('--endpoint', help='SPARQL endpoint name or URL (auto-detected if not specified)')
@click.option('--limit', type=int, default=20, help='Maximum number of results (default: 20)')
@click.option('--offset', type=int, default=0, help='Starting offset for pagination (default: 0)')
@click.option('--timeout', default=30, help='Query timeout in seconds (default: 30)')
def select(query: str, endpoint: Optional[str], limit: int, offset: int, timeout: int):
    """Execute SELECT SPARQL queries with validation and pagination.
    
    Validates query syntax and provides ReadTool-style pagination for exploring results.
    Primary tool for semantic data exploration in Claude Code.
    
    Examples:
        cl_select "SELECT ?p ?o WHERE { wd:Q905695 ?p ?o }"               # Entity properties
        cl_select "SELECT ?p ?o WHERE { wd:Q905695 ?p ?o }" --limit 10    # First 10 properties
        cl_select "SELECT ?p ?o WHERE { wd:Q905695 ?p ?o }" --offset 10   # Next 10 properties
        cl_select "SELECT ?protein WHERE { ?protein a up:Protein }" --endpoint uniprot --limit 5
    """
    
    if not query.strip():
        click.echo('{"error": "Query cannot be empty"}', err=True)
        sys.exit(1)
    
    # Validate SELECT query syntax
    validation = validate_select_query(query)
    if not validation["valid"]:
        error_output = {
            "error": validation["error"],
            "suggestion": validation["suggestion"],
            "query": query,
            "query_type": "SELECT",
            "success": False
        }
        click.echo(json.dumps(error_output), err=True)
        sys.exit(1)
    
    try:
        # Determine endpoint
        if endpoint:
            if endpoint.startswith("http"):
                endpoint_url = endpoint
            else:
                endpoints = discover_sparql_endpoints()
                endpoint_url = endpoints.get(endpoint)
                if not endpoint_url:
                    available = list(endpoints.keys())
                    error_output = {
                        "error": f"Unknown endpoint: {endpoint}",
                        "available_endpoints": available,
                        "success": False
                    }
                    click.echo(json.dumps(error_output), err=True)
                    sys.exit(1)
        else:
            endpoints = discover_sparql_endpoints()
            endpoint_url = endpoints.get("wikidata")
            endpoint = "wikidata"
        
        # Prepare query - don't add SELECT if already present
        if query.strip().upper().startswith("SELECT"):
            sparql_query = query.strip()
        else:
            sparql_query = f"SELECT {query.strip()}"
        
        # Remove any existing LIMIT/OFFSET to avoid conflicts
        sparql_query = re.sub(r'\s+(LIMIT|OFFSET)\s+\d+', '', sparql_query, flags=re.IGNORECASE)
        
        # Add pagination - OFFSET must come before LIMIT in SPARQL
        if offset > 0:
            sparql_query += f" OFFSET {offset}"
        sparql_query += f" LIMIT {limit}"
        
        # Add prefixes automatically
        prefixed_query = build_prefixed_query(sparql_query, endpoint_url)
        
        log.debug(f"Executing SELECT query on {endpoint_url}:\\n{prefixed_query}")
        
        # WORKFLOW GUARDRAIL: Check for vocabulary discovery (Claude Code pattern)
        vocabulary_reminder = check_vocabulary_discovery(endpoint)
        
        # Execute query with redirect support for semantic web URIs
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                endpoint_url,
                params={
                    "query": prefixed_query,
                    "format": "json"
                }
            )
            response.raise_for_status()
            
            # Capture redirect information for semantic web debugging
            redirect_info = None
            if len(response.history) > 0:
                redirect_info = {
                    "original_url": str(response.history[0].url),
                    "final_url": str(response.url),
                    "redirect_count": len(response.history),
                    "redirect_chain": [str(r.url) for r in response.history] + [str(response.url)]
                }
            
            data = response.json()
        
        # Extract results
        if "results" in data and "bindings" in data["results"]:
            results = data["results"]["bindings"]
        else:
            results = []
        
        # Add exploration metadata like ReadTool
        has_more = len(results) == limit  # If we got exactly 'limit' results, likely more exist
        next_offset = offset + limit
        
        output = {
            "query": sparql_query,
            "endpoint": endpoint_url,
            "query_type": "SELECT",
            "results": results,
            "count": len(results),
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
            "success": True
        }
        
        # Add redirect information if any occurred
        if redirect_info:
            output["redirect_info"] = redirect_info
        
        # Add exploration hints like ReadTool
        if has_more:
            # Create next page command by updating offset in original query
            base_query = query.strip()
            output["next_page_command"] = f"cl_select \"{base_query}\" --limit {limit} --offset {next_offset}"
            if endpoint:
                output["next_page_command"] += f" --endpoint {endpoint}"
        
        if results:
            # Analyze result patterns to provide helpful hints
            hints = []
            
            # Count variables in results
            if results:
                variables = set(results[0].keys()) if results else set()
                hints.append(f"Variables returned: {', '.join(sorted(variables))}")
            
            # Check for common patterns
            uri_count = sum(1 for result in results for val in result.values() if val.get("type") == "uri")
            literal_count = sum(1 for result in results for val in result.values() if val.get("type") == "literal")
            
            if uri_count > 0:
                hints.append(f"Found {uri_count} URI references")
            if literal_count > 0:
                hints.append(f"Found {literal_count} literal values")
            
            if has_more:
                hints.append(f"More results available (showing {offset+1}-{offset+len(results)})")
            else:
                hints.append(f"Showing results {offset+1}-{offset+len(results)}")
            
            output["exploration_hints"] = hints
        
        # Add vocabulary reminder if needed (Claude Code workflow enforcement)
        if vocabulary_reminder:
            output["system_reminder"] = vocabulary_reminder
        
        click.echo(json.dumps(output))
    
    except Exception as e:
        error_output = {
            "error": str(e),
            "query": query,
            "endpoint": endpoint or "auto-detected",
            "query_type": "SELECT",
            "success": False
        }
        
        # Add vocabulary reminder even on errors (workflow issue separate from query issue)
        if 'vocabulary_reminder' in locals() and vocabulary_reminder:
            error_output["system_reminder"] = vocabulary_reminder
        
        click.echo(json.dumps(error_output), err=True)
        sys.exit(1)


def check_vocabulary_discovery(endpoint: str) -> Optional[str]:
    """Check if SPARQL service description has been discovered (Claude Code pattern)."""
    if not endpoint or endpoint == "wikidata":
        # Wikidata is well-known, skip check
        return None
    
    # Get the actual endpoint URL for service description discovery
    from ..backend.sparql import discover_sparql_endpoints
    endpoints = discover_sparql_endpoints()
    endpoint_url = endpoints.get(endpoint)
    
    if not endpoint_url:
        return None  # This will be caught by earlier endpoint validation
    
    # Look for cached SPARQL service description for this endpoint
    cache_key = f"rdf:{endpoint}_service"
    enhanced_entry = cache_manager.get_enhanced(cache_key)
    
    if not enhanced_entry:
        return (
            f"⚠️ DISCOVERY-FIRST REMINDER: No SPARQL service description discovered for '{endpoint}'. "
            f"Use 'rdf_get {endpoint_url} --cache-as {endpoint}_service' to discover service capabilities first. "
            f"This fetches the SPARQL 1.1 service description via HTTP GET."
        )
    
    if enhanced_entry.semantic_metadata is None:
        return (
            f"⚠️ METADATA-FIRST REMINDER: Service description discovered but not analyzed for '{endpoint}'. "
            f"Use 'rdf_cache {endpoint}_service --update-metadata {{...}}' to store semantic analysis of the service capabilities."
        )
    
    return None


if __name__ == "__main__":
    select()