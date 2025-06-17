"""cl_search: Simple entity search following Claude Code patterns.

Clean, simple tool - no complex metadata analysis.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Optional, List, Dict, Any

import click
import httpx

from ..core.debug import get_logger

log = get_logger("cl_search")


@click.command()
@click.argument('query')
@click.option('--endpoint', default='wikidata', help='Endpoint to search: wikidata, uniprot, wikipathways, or full URL (default: wikidata)')
@click.option('--limit', default=10, type=int, help='Maximum number of results (default: 10)')
@click.option('--offset', default=0, type=int, help='Starting offset for pagination (default: 0)')
def search(query: str, endpoint: str, limit: int, offset: int):
    """Search for entities across semantic web endpoints with pagination.
    
    Uses efficient search APIs when available (Wikidata), falls back to SPARQL text search.
    
    Examples:
        cl_search "caffeine"                              # Wikidata API search
        cl_search "insulin" --limit 5                     # First 5 results  
        cl_search "protein" --endpoint uniprot --limit 5  # UniProt SPARQL search
        cl_search "pathway" --endpoint wikipathways       # WikiPathways SPARQL search
        cl_search "gene" --endpoint https://sparql.example.org/sparql  # Custom endpoint
    """
    
    if not query.strip():
        click.echo('{"error": "Query cannot be empty"}', err=True)
        sys.exit(1)
    
    try:
        start_time = time.time()
        
        # Search with pagination support
        if endpoint == "wikidata":
            # Use efficient Wikidata API
            search_result = search_wikidata_api(query, limit, offset)
        elif endpoint.startswith("http"):
            # Direct SPARQL endpoint URL
            search_result = search_sparql_endpoint(query, limit, offset, endpoint)
        else:
            # Named endpoint - resolve to URL and use SPARQL
            endpoint_urls = {
                "uniprot": "https://sparql.uniprot.org/sparql",
                "wikipathways": "https://sparql.wikipathways.org/sparql"
            }
            endpoint_url = endpoint_urls.get(endpoint)
            if endpoint_url:
                search_result = search_sparql_endpoint(query, limit, offset, endpoint_url)
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}. Use 'wikidata', 'uniprot', 'wikipathways', or provide full URL")
        
        results = search_result["results"]
        total_found = search_result.get("total_found", len(results))
        has_more = search_result.get("has_more", False)
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Output with exploration metadata like ReadTool
        next_offset = offset + limit
        
        output = {
            "query": query,
            "endpoint": endpoint,
            "results": results,
            "count": len(results),
            "offset": offset,
            "limit": limit,
            "total_found": total_found,
            "has_more": has_more,
            "execution_time_ms": round(execution_time_ms, 2),
            "success": True
        }
        
        # Add exploration hints like ReadTool
        if has_more:
            next_cmd = f"cl_search \"{query}\" --limit {limit} --offset {next_offset}"
            if endpoint != "wikidata":
                next_cmd += f" --endpoint {endpoint}"
            output["next_page_command"] = next_cmd
        
        if results:
            # Provide hints about what was found
            entity_types = set()
            property_count = 0
            for result in results:
                if result.get("type") == "property":
                    property_count += 1
                else:
                    entity_types.add("entity")
            
            hints = []
            if entity_types:
                hints.append(f"Found {len(results) - property_count} entities")
            if property_count:
                hints.append(f"Found {property_count} properties")
            if has_more:
                hints.append(f"More results available (showing {offset+1}-{offset+len(results)} of {total_found}+)")
            
            output["exploration_hints"] = hints
        
        click.echo(json.dumps(output))
    
    except Exception as e:
        error_output = {
            "error": str(e),
            "query": query,
            "endpoint": endpoint,
            "success": False
        }
        click.echo(json.dumps(error_output), err=True)
        sys.exit(1)


def search_wikidata_api(query: str, limit: int, offset: int = 0) -> Dict[str, Any]:
    """Search Wikidata using API with pagination support."""
    try:
        # Wikidata API doesn't support offset directly, but we can request more and slice
        # For now, we'll request up to limit + offset to simulate pagination
        api_limit = min(50, limit + offset)  # Wikidata API max is 50
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://www.wikidata.org/w/api.php", params={
                "action": "wbsearchentities",
                "search": query,
                "language": "en",
                "limit": api_limit,
                "format": "json"
            })
            response.raise_for_status()
            data = response.json()
            
            all_results = []
            for item in data.get("search", []):
                all_results.append({
                    "id": item.get("id", ""),
                    "label": item.get("label", ""),
                    "description": item.get("description", ""),
                    "type": item.get("match", {}).get("type", "entity"),
                    "url": item.get("concepturi", "")
                })
            
            # Apply offset and limit
            paginated_results = all_results[offset:offset + limit]
            
            # Determine if there are more results
            has_more = len(all_results) > offset + limit or len(all_results) == api_limit
            
            return {
                "results": paginated_results,
                "total_found": len(all_results),
                "has_more": has_more
            }
            
    except Exception as e:
        log.error(f"Wikidata search failed: {e}")
        return {
            "results": [],
            "total_found": 0,
            "has_more": False
        }


def search_sparql_endpoint(query: str, limit: int, offset: int, endpoint_url: str) -> Dict[str, Any]:
    """Search SPARQL endpoint using text search with pagination support."""
    try:
        # Build simple SPARQL text search query for efficiency
        sparql_query = f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?entity ?label WHERE {{
    ?entity rdfs:label ?label .
    FILTER(LANG(?label) = "en")
    FILTER(CONTAINS(LCASE(?label), LCASE("{query}")))
}}
OFFSET {offset}
LIMIT {limit}
"""
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(endpoint_url, params={
                "query": sparql_query.strip(),
                "format": "json"
            })
            response.raise_for_status()
            data = response.json()
        
        # Process SPARQL results into cl_search format
        results = []
        if "results" in data and "bindings" in data["results"]:
            for binding in data["results"]["bindings"]:
                entity_uri = binding.get("entity", {}).get("value", "")
                label = binding.get("label", {}).get("value", "")
                
                # Extract entity ID from URI (e.g., Q123 from http://...entity/Q123)
                entity_id = entity_uri.split("/")[-1] if entity_uri else ""
                
                results.append({
                    "id": entity_id,
                    "label": label,
                    "description": "",  # No description for efficiency
                    "type": "entity",
                    "url": entity_uri
                })
        
        # SPARQL pagination means if we got exactly 'limit' results, there might be more
        has_more = len(results) == limit
        
        return {
            "results": results,
            "total_found": len(results),  # We don't know total without a separate count query
            "has_more": has_more
        }
        
    except Exception as e:
        log.error(f"SPARQL endpoint search failed for {endpoint_url}: {e}")
        return {
            "results": [],
            "total_found": 0,
            "has_more": False
        }


if __name__ == "__main__":
    search()