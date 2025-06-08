#!/usr/bin/env python3
"""
cl_sparql: Simple SPARQL query tool with basic guardrails

Execute SPARQL queries with automatic LIMIT and timeout guardrails.
Simplified version without complex discovery systems.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from typing import Optional, List, Dict, Any

import click

from ..adapters.unified_sparql_client import get_sparql_client
from ..core.debug import get_logger

log = get_logger("cl_sparql")

# SPARQL validation patterns (extracted from complex version)
SPARQL_PATTERNS = {
    'prefixes': re.compile(r'PREFIX\s+(\w+):\s*<([^>]+)>', re.IGNORECASE),
    'select': re.compile(r'SELECT\s+(.*?)\s+WHERE', re.IGNORECASE | re.DOTALL),
    'limit': re.compile(r'LIMIT\s+(\d+)', re.IGNORECASE),
    'entities': re.compile(r'<([^>]+)>|(\w+:\w+)'),
    'dangerous': re.compile(r'COUNT\s*\(\s*\*\s*\)|DELETE|INSERT|DROP|CLEAR', re.IGNORECASE)
}


@click.command()
@click.argument('query', required=True)
@click.option('--endpoint', default='wikidata',
              help='SPARQL endpoint: wikidata, uniprot, etc.')
@click.option('--timeout', default=10, type=int,
              help='Query timeout in seconds (default: 10)')
@click.option('--max-limit', default=100, type=int,
              help='Maximum LIMIT to auto-add (default: 100)')
def sparql_query(query: str, endpoint: str, timeout: int, max_limit: int):
    """
    Execute SPARQL queries with basic safety guardrails.
    
    Automatically adds LIMIT if missing and blocks dangerous operations.
    
    Examples:
        cl_sparql "SELECT ?s ?p ?o WHERE { ?s ?p ?o }" --endpoint wikidata
        cl_sparql "SELECT ?protein WHERE { ?protein wdt:P31 wd:Q8054 } LIMIT 5"
        cl_sparql "ASK { wd:Q7240673 wdt:P352 ?uniprot }" --format human
    """
    asyncio.run(_sparql_async(query, endpoint, timeout, max_limit))


async def _sparql_async(query: str, endpoint: str, timeout: int, max_limit: int):
    """Async SPARQL execution with guardrails."""
    
    # Handle help request
    if endpoint == "help" or query.lower().strip() in ["help", "endpoints", "list"]:
        client = get_sparql_client()
        endpoints_list = client.list_known_endpoints()
        
        help_response = {
            "available_endpoints": endpoints_list,
            "usage_examples": {
                "wikidata": "cl_sparql \"SELECT ?protein WHERE { ?protein wdt:P31 wd:Q8054 } LIMIT 5\"",
                "wikipathways": "cl_sparql \"SELECT ?pathway ?title WHERE { ?pathway a wp:Pathway . ?pathway dc:title ?title } LIMIT 5\" --endpoint wikipathways",
                "uniprot": "cl_sparql \"SELECT ?protein ?name WHERE { ?protein a up:Protein . ?protein up:mnemonic ?name } LIMIT 5\" --endpoint uniprot",
                "idsm": "cl_sparql \"SELECT ?compound ?name WHERE { ?compound rdfs:label ?name } LIMIT 5\" --endpoint idsm"
            },
            "endpoint_vocabularies": {
                "wikidata": ["wd:", "wdt:", "wikibase:", "bd:"],
                "wikipathways": ["wp:", "dc:", "dcterms:", "foaf:"],
                "uniprot": ["up:", "taxon:", "skos:"],
                "idsm": ["rdfs:", "owl:", "skos:", "dcterms:"]
            }
        }
        click.echo(json.dumps(help_response, indent=2))
        return
    
    start_time = time.time()
    
    try:
        # Apply query guardrails
        safe_query, guardrail_warnings = _apply_query_guardrails(query, max_limit)
        
        # Block dangerous queries
        if not _is_query_safe(safe_query):
            error_result = {
                "query": query,
                "error": "Query blocked by safety guardrails",
                "suggestions": [
                    "COUNT(*) queries must include LIMIT < 1000",
                    "Large aggregations are not allowed", 
                    "Use more specific constraints"
                ]
            }
            click.echo(json.dumps(error_result, indent=2))
            return
        
        # Execute query
        log.info(f"Executing SPARQL query on {endpoint}")
        sparql_client = get_sparql_client()
        query_result = await sparql_client.query(endpoint, safe_query, timeout=timeout)
        result = query_result.data
        
        # Process results
        execution_time = int((time.time() - start_time) * 1000)
        bindings = result.get('results', {}).get('bindings', [])
        
        # Clean response - just the data Claude needs
        response = {
            'query': {
                'original': query,
                'executed': safe_query,
                'endpoint': endpoint,
                'guardrails_applied': guardrail_warnings
            },
            'results': {
                'bindings': bindings,
                'count': len(bindings),
                'variables': result.get('head', {}).get('vars', [])
            }
        }
        
        click.echo(json.dumps(response, indent=2))
            
    except Exception as e:
        log.error(f"SPARQL query failed: {e}")
        error_result = {
            "query": query,
            "error": f"SPARQL query failed: {str(e)}",
            "suggestions": [
                "Check query syntax",
                "Verify endpoint is available", 
                "Try simpler query first"
            ]
        }
        click.echo(json.dumps(error_result, indent=2))
        sys.exit(1)


def _apply_query_guardrails(query: str, max_limit: int) -> tuple[str, List[str]]:
    """Apply enhanced safety guardrails to SPARQL query."""
    
    warnings = []
    safe_query = query.strip()
    
    # 1. Check for dangerous operations first
    if SPARQL_PATTERNS['dangerous'].search(safe_query):
        warnings.append("Query contains potentially dangerous operations")
    
    # 2. Auto-add LIMIT if missing (for SELECT queries)
    if re.search(r'^\s*SELECT', safe_query, re.IGNORECASE):
        if not SPARQL_PATTERNS['limit'].search(safe_query):
            safe_query += f" LIMIT {max_limit}"
            warnings.append(f"Auto-added LIMIT {max_limit} for performance")
    
    # 3. Validate and limit COUNT queries  
    if re.search(r'COUNT\s*\(\s*\*?\s*\)', safe_query, re.IGNORECASE):
        if not SPARQL_PATTERNS['limit'].search(safe_query):
            safe_query += f" LIMIT {min(max_limit, 1000)}"
            warnings.append("Auto-added LIMIT to COUNT query")
    
    # 4. Cap excessive LIMITs
    limit_match = SPARQL_PATTERNS['limit'].search(safe_query)
    if limit_match:
        limit_value = int(limit_match.group(1))
        if limit_value > 10000:
            safe_query = re.sub(r'LIMIT\s+\d+', 'LIMIT 1000', safe_query, flags=re.IGNORECASE)
            warnings.append(f"Reduced LIMIT from {limit_value} to 1000")
    
    # 5. Check for missing prefixes (basic discovery hint)
    entities = SPARQL_PATTERNS['entities'].findall(safe_query)
    prefixed_entities = [entity for full, prefixed in entities if prefixed for entity in [prefixed]]
    if prefixed_entities:
        unknown_prefixes = set(entity.split(':')[0] for entity in prefixed_entities 
                             if ':' in entity and not entity.startswith('http'))
        if unknown_prefixes:
            warnings.append(f"Unknown prefixes detected: {', '.join(unknown_prefixes)}")
    
    return safe_query, warnings


def _is_query_safe(query: str) -> bool:
    """Check if query is safe to execute using enhanced patterns."""
    
    # 1. Block dangerous operations
    if SPARQL_PATTERNS['dangerous'].search(query):
        return False
    
    # 2. Block COUNT(*) without reasonable LIMIT
    if re.search(r'COUNT\s*\(\s*\*?\s*\)', query, re.IGNORECASE):
        limit_match = SPARQL_PATTERNS['limit'].search(query)
        if not limit_match or int(limit_match.group(1)) > 1000:
            return False
    
    # 3. Block expensive patterns
    expensive_patterns = [
        r'COUNT\s*\(\s*DISTINCT.*\)\s*WHERE\s*\{.*\}(?!\s*LIMIT)',  # COUNT DISTINCT without LIMIT
        r'OPTIONAL\s*\{.*OPTIONAL\s*\{.*OPTIONAL',                 # Deeply nested OPTIONAL
        r'SELECT\s+\*.*WHERE\s*\{\s*\?\w+\s+\?\w+\s+\?\w+\s*\}(?!\s*LIMIT)',  # SELECT * ?s ?p ?o without LIMIT
    ]
    
    for pattern in expensive_patterns:
        if re.search(pattern, query, re.IGNORECASE | re.DOTALL):
            return False
    
    return True


# Removed complex output functions - using clean Claude Code pattern


if __name__ == "__main__":
    sparql_query()