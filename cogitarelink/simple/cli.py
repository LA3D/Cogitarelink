#!/usr/bin/env python3
"""
Simplified Cogitarelink CLI - Following wikidata-mcp success patterns

Single CLI entry point with 4 core commands:
- discover: Universal knowledge discovery
- sparql: SPARQL query execution  
- entity: Entity details
- ontfetch: Schema discovery
"""

import asyncio
import click
import sys
from typing import List, Optional

from .client import UnifiedSparqlClient
from .tools import (
    UniversalDiscovery,
    SimpleSparql, 
    SimpleEntity,
    SimpleOntologyFetch
)


@click.group()
@click.version_option(version="0.2.0")
def cli():
    """
    Cogitarelink - Universal Knowledge Discovery Assistant
    
    Simplified tools for Claude Code integration across all knowledge domains.
    """
    pass


@cli.command()
@click.argument('query')
@click.option('--endpoint', default='wikidata', help='SPARQL endpoint (default: wikidata)')
@click.option('--limit', default=10, type=int, help='Maximum results (default: 10)')
def discover(query: str, endpoint: str, limit: int):
    """
    Universal knowledge discovery.
    
    Examples:
        cogitarelink discover "Tesla"
        cogitarelink discover "Paris"
        cogitarelink discover "insulin" --endpoint uniprot
    """
    asyncio.run(_discover_async(query, endpoint, limit))


@cli.command()
@click.argument('query')
@click.option('--endpoint', default='wikidata', help='SPARQL endpoint (default: wikidata)')
@click.option('--timeout', default=30, type=int, help='Query timeout in seconds')
def sparql(query: str, endpoint: str, timeout: int):
    """
    Execute SPARQL queries with safety guardrails.
    
    Examples:
        cogitarelink sparql "SELECT ?item ?label WHERE { ?item rdfs:label ?label } LIMIT 5"
        cogitarelink sparql "DESCRIBE wd:Q5" --endpoint wikidata
    """
    asyncio.run(_sparql_async(query, endpoint, timeout))


@cli.command()
@click.argument('entity_id')
@click.option('--endpoint', default='wikidata', help='SPARQL endpoint (default: wikidata)')
@click.option('--properties', multiple=True, help='Specific properties to retrieve')
def entity(entity_id: str, endpoint: str, properties: List[str]):
    """
    Get detailed entity information.
    
    Examples:
        cogitarelink entity Q5 --endpoint wikidata
        cogitarelink entity P31 --properties rdfs:label rdfs:comment
    """
    asyncio.run(_entity_async(entity_id, endpoint, list(properties) if properties else None))


@cli.command()
@click.argument('endpoint')
def ontfetch(endpoint: str):
    """
    Discover schema and vocabulary information for endpoints.
    
    Examples:
        cogitarelink ontfetch wikidata
        cogitarelink ontfetch uniprot
        cogitarelink ontfetch wikipathways
    """
    asyncio.run(_ontfetch_async(endpoint))


# Async implementations
async def _discover_async(query: str, endpoint: str, limit: int):
    """Async discovery implementation."""
    client = UnifiedSparqlClient(endpoint)
    discovery = UniversalDiscovery(client)
    
    try:
        result = await discovery.discover(query, endpoint, limit)
        print(result)
    finally:
        await client.close()


async def _sparql_async(query: str, endpoint: str, timeout: int):
    """Async SPARQL implementation."""
    client = UnifiedSparqlClient(endpoint)
    sparql_tool = SimpleSparql(client)
    
    try:
        result = await sparql_tool.query(query, endpoint, timeout)
        print(result)
    finally:
        await client.close()


async def _entity_async(entity_id: str, endpoint: str, properties: Optional[List[str]]):
    """Async entity implementation."""
    client = UnifiedSparqlClient(endpoint)
    entity_tool = SimpleEntity(client)
    
    try:
        result = await entity_tool.get_entity(entity_id, endpoint, properties)
        print(result)
    finally:
        await client.close()


async def _ontfetch_async(endpoint: str):
    """Async ontology fetch implementation.""" 
    client = UnifiedSparqlClient()
    ontfetch_tool = SimpleOntologyFetch(client)
    
    try:
        result = await ontfetch_tool.fetch_schema(endpoint)
        print(result)
    finally:
        await client.close()


if __name__ == '__main__':
    cli()