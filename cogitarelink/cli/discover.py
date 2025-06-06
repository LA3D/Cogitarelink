"""Simple discovery CLI tool for interactive testing with Claude Code."""

from __future__ import annotations

import json
from typing import Dict, Any

import click

from cogitarelink.core.entity import Entity


def main() -> None:
    """Entry point for cl_discover command."""
    discover()


@click.command()
@click.argument('query')
@click.option('--vocab', multiple=True, default=['bioschemas'], help='Vocabulary prefixes')
@click.option('--entity-type', default='Unknown', help='Entity type')
@click.option('--format', 'output_format', default='agent', 
              type=click.Choice(['agent', 'entity', 'reasoning']),
              help='Output format')
def discover(query: str, vocab: tuple[str, ...], entity_type: str, output_format: str) -> None:
    """Simple entity discovery for testing Enhanced Entity with Claude Code.
    
    This is a minimal implementation for testing the Enhanced Entity class
    with Claude Code during the fast.ai iterative development process.
    """
    
    # Create a mock entity based on the query (for testing purposes)
    content = {
        "name": query,
        "@type": entity_type,
        "discovered_via": "cl_discover",
        "query_terms": query.split()
    }
    
    # Create Enhanced Entity
    entity = Entity(vocab=list(vocab), content=content)
    
    # Generate different output formats
    if output_format == 'agent':
        response = entity.to_agent_response()
        
    elif output_format == 'reasoning':
        response = {
            "success": True,
            "data": {"entity": entity.to_dict()},
            "reasoning_context": entity.generate_reasoning_context()
        }
        
    else:  # entity format
        response = {
            "success": True,
            "data": {
                "entity": entity.to_dict(),
                "signature": entity.sha256,
                "vocab": entity.vocab
            }
        }
    
    # Output structured JSON for Claude Code
    click.echo(json.dumps(response, indent=2))


if __name__ == "__main__":
    discover()