#!/usr/bin/env python3
"""
cl_lens: Semantic jq filter library for CogitareLink tools

Provides pre-built jq filters for common scientific data patterns,
enabling easy navigation and extraction from CogitareLink tool outputs.
"""

from __future__ import annotations

import json
from typing import Dict, List

import click


# Semantic Lens Library - jq filters for common patterns
LENSES = {
    # Entity extraction patterns
    "entity_ids": ".data[].id",
    "entity_names": ".data[].name",
    "entity_types": ".data[].type",
    "entity_summary": ".data[] | {id, name, type, confidence}",
    
    # Discovery patterns
    "discovery_status": ".status",
    "discovery_count": ".count", 
    "discovery_next": ".next[0]",
    "discovery_query": ".meta.query",
    
    # SPARQL result patterns
    "sparql_bindings": ".results.bindings[]",
    "sparql_values": ".results.bindings[] | to_entries | .[].value.value",
    "sparql_uris": ".results.bindings[] | to_entries | .[].value | select(.type==\"uri\") | .value",
    
    # Cross-reference patterns  
    "uniprot_ids": ".data[] | .identifiers.uniprot // empty",
    "wikidata_ids": ".data[] | select(.type==\"wikidata_entity\") | .id",
    "external_ids": ".data[] | .identifiers // {}",
    
    # Metadata patterns
    "execution_time": ".meta.execution_time_ms // 0",
    "error_message": ".error.message // null",
    "next_commands": ".next[]",
    
    # Scientific domain patterns
    "protein_summary": ".data[] | select(.domains[]? == \"biology\") | {id, name, type, confidence}",
    "chemical_summary": ".data[] | select(.type | contains(\"chemical\")) | {id, name, type}",
    "pathway_entities": ".data[] | select(.type | contains(\"pathway\"))",
    
    # Composition helpers
    "pipe_ready": ".data[0].id",  # Extract first ID for piping to next tool
    "all_ids": ".data[] | .id",   # Extract all IDs for batch operations
    "has_results": ".count > 0",  # Check if query returned results
    "is_success": ".status == \"success\"",  # Check operation success
    
    # JSON-LD Container Navigation
    "memory_entities": ".memory.entities",                    # Access @container: "@id" entities
    "memory_by_type": ".memory.by_type",                     # Access @container: "@type" grouping
    "memory_by_domain": ".memory.by_domain",                 # Access @container: "@index" domains
    "memory_by_thread": ".memory.by_thread",                 # Access @container: "@index" threads
    "context_entities": ".memory.entities | keys[]",         # List all entity IDs in memory
    "context_types": ".memory.by_type | keys[]",            # List all entity types in memory
    "context_domains": ".memory.by_domain | keys[]",        # List all domains in memory
    
    # Container-specific patterns
    "entity_by_id": ".memory.entities[\\(.id)]",              # Direct entity access by ID (needs interpolation)
    "entities_of_type": ".memory.by_type[\\(.type)][]",       # Entities of specific type (needs interpolation)
    "entities_in_domain": ".memory.by_domain[\\(.domain)][]", # Entities in specific domain (needs interpolation)
    "thread_contexts": ".memory.by_thread[\\(.thread)][]",   # Contexts in specific thread (needs interpolation)
    
    # Semantic Memory Patterns
    "semantic_summary": ".memory | {entities: (.entities | length), types: (.by_type | length), domains: (.by_domain | length)}",
    "memory_stats": "{entity_count: (.memory.entities | length), type_count: (.memory.by_type | length), domain_count: (.memory.by_domain | length)}",
    "cross_references": ".memory.entities[] | select(.identifiers) | {id, identifiers}",
    "high_confidence": ".memory.entities[] | select(.confidence > 0.8)",
    "biological_entities": ".memory.by_domain.biology[]? // empty",
    
    # Context Management Patterns
    "context_list": ".data[] | {name, id, thread, entity_count, size_kb, created}",
    "thread_list": ".data[] | select(.thread) | .thread",
    "recent_contexts": ".data | sort_by(.created) | reverse | .[0:5]",
    "large_contexts": ".data[] | select(.size_kb > 10)",
    
    # Research Workflow Patterns
    "research_entities": ".memory.entities[] | select(.domains[]? == \"biology\" or .domains[]? == \"chemistry\")",
    "pathway_links": ".memory.entities[] | select(.type | contains(\"pathway\")) | {id, name, connections: .relationships[]?}",
    "protein_network": ".memory.by_type.protein_identifier[]? // .memory.by_type.wikidata_entity[] | select(.domains[]? == \"biology\")",
    "compound_library": ".memory.by_type.chemical_identifier[]? // .memory.entities[] | select(.type | contains(\"chemical\"))",
}


@click.command()
@click.argument('lens_name', required=False)
@click.option('--list', 'list_lenses', is_flag=True, help='List all available lenses')
@click.option('--describe', is_flag=True, help='Show description of the lens')
@click.option('--raw', is_flag=True, help='Output raw jq filter without explanation')
def lens(lens_name: str, list_lenses: bool, describe: bool, raw: bool):
    """
    Get jq filters for common CogitareLink data patterns.
    
    Examples:
        cl_lens entity_ids                    # Get jq filter for extracting entity IDs
        cl_lens --list                        # List all available lenses
        cl_lens protein_summary --describe    # Show what protein_summary does
        
    Usage in pipelines:
        cl_discover insulin | jq "$(cl_lens entity_ids --raw)"
        cl_sparql "..." | jq "$(cl_lens sparql_uris --raw)"
    """
    
    if list_lenses:
        _list_all_lenses()
        return
        
    if not lens_name:
        _show_help()
        return
        
    if lens_name not in LENSES:
        _handle_unknown_lens(lens_name)
        return
        
    filter_str = LENSES[lens_name]
    
    if describe:
        _describe_lens(lens_name, filter_str)
    elif raw:
        click.echo(filter_str)
    else:
        _show_lens_usage(lens_name, filter_str)


def _list_all_lenses():
    """List all available lenses by category"""
    categories = {
        "Entity Patterns": ["entity_ids", "entity_names", "entity_types", "entity_summary"],
        "Discovery Patterns": ["discovery_status", "discovery_count", "discovery_next", "discovery_query"],
        "SPARQL Patterns": ["sparql_bindings", "sparql_values", "sparql_uris"],
        "Cross-Reference Patterns": ["uniprot_ids", "wikidata_ids", "external_ids"],
        "Scientific Domain": ["protein_summary", "chemical_summary", "pathway_entities"],
        "Composition Helpers": ["pipe_ready", "all_ids", "has_results", "is_success"],
        "Container Navigation": ["memory_entities", "memory_by_type", "memory_by_domain", "context_entities", "context_types", "context_domains"],
        "Semantic Memory": ["semantic_summary", "memory_stats", "cross_references", "high_confidence", "biological_entities"],
        "Context Management": ["context_list", "thread_list", "recent_contexts", "large_contexts"],
        "Research Workflows": ["research_entities", "pathway_links", "protein_network", "compound_library"]
    }
    
    response = {
        "status": "success",
        "data": [],
        "count": 0,
        "meta": {
            "total_lenses": len(LENSES),
            "categories": len(categories)
        }
    }
    
    for category, lens_list in categories.items():
        for lens_name in lens_list:
            response["data"].append({
                "name": lens_name,
                "category": category,
                "filter": LENSES[lens_name]
            })
            
    response["count"] = len(response["data"])
    click.echo(json.dumps(response, indent=2))


def _describe_lens(lens_name: str, filter_str: str):
    """Show detailed description of a lens"""
    descriptions = {
        "entity_ids": "Extract all entity identifiers from discovery results",
        "entity_names": "Extract all entity names/labels",
        "entity_types": "Extract all entity types (protein, chemical, etc.)",
        "entity_summary": "Get compact summary with id, name, type, confidence",
        
        "discovery_status": "Get operation status (success/error)",
        "discovery_count": "Get number of results found",
        "discovery_next": "Get first suggested next command",
        "discovery_query": "Get original query that was executed",
        
        "sparql_bindings": "Extract all SPARQL result bindings",
        "sparql_values": "Extract just the values from SPARQL results",
        "sparql_uris": "Extract only URI values from SPARQL results",
        
        "uniprot_ids": "Extract UniProt protein identifiers",
        "wikidata_ids": "Extract Wikidata entity IDs (Q-numbers)",
        "external_ids": "Get all external identifier mappings",
        
        "protein_summary": "Summary for biological/protein entities only",
        "chemical_summary": "Summary for chemical compounds only", 
        "pathway_entities": "Filter for pathway-related entities",
        
        "pipe_ready": "Extract first entity ID for piping to next tool",
        "all_ids": "Extract all entity IDs for batch operations",
        "has_results": "Check if query returned any results",
        "is_success": "Check if operation completed successfully",
        
        # Container Navigation
        "memory_entities": "Access all entities in semantic memory (@container: @id)",
        "memory_by_type": "Access entities grouped by type (@container: @type)",
        "memory_by_domain": "Access entities grouped by domain (@container: @index)",
        "memory_by_thread": "Access entities by research thread (@container: @index)", 
        "context_entities": "List all entity IDs stored in semantic memory",
        "context_types": "List all entity types in semantic memory",
        "context_domains": "List all domains represented in semantic memory",
        
        # Semantic Memory
        "semantic_summary": "Get summary statistics of semantic memory structure",
        "memory_stats": "Get entity, type, and domain counts from memory",
        "cross_references": "Extract entities with cross-reference identifiers",
        "high_confidence": "Filter entities with confidence > 0.8",
        "biological_entities": "Extract all biology domain entities from memory",
        
        # Context Management
        "context_list": "Format context list with essential metadata",
        "thread_list": "Extract all research thread identifiers",
        "recent_contexts": "Get 5 most recently created contexts",
        "large_contexts": "Filter contexts larger than 10KB",
        
        # Research Workflows
        "research_entities": "Extract biology and chemistry domain entities",
        "pathway_links": "Extract pathway entities with relationship connections",
        "protein_network": "Extract protein identifiers and related entities",
        "compound_library": "Extract chemical compound identifiers and entities"
    }
    
    description = descriptions.get(lens_name, "No description available")
    
    response = {
        "status": "success",
        "data": [{
            "lens": lens_name,
            "filter": filter_str,
            "description": description,
            "usage_examples": _get_usage_examples(lens_name)
        }],
        "count": 1,
        "meta": {
            "lens_name": lens_name
        }
    }
    
    click.echo(json.dumps(response, indent=2))


def _get_usage_examples(lens_name: str) -> List[str]:
    """Get usage examples for a lens"""
    examples = {
        "entity_ids": [
            'cl_discover insulin | jq "$(cl_lens entity_ids --raw)"',
            'cl_sparql "..." | jq "$(cl_lens entity_ids --raw)"'
        ],
        "pipe_ready": [
            'ID=$(cl_discover insulin | jq -r "$(cl_lens pipe_ready --raw)")',
            'cl_discover insulin | jq -r "$(cl_lens pipe_ready --raw)" | cl_resolve P352'
        ],
        "protein_summary": [
            'cl_discover "BRCA1" --domains biology | jq "$(cl_lens protein_summary --raw)"'
        ],
        "sparql_uris": [
            'cl_sparql "SELECT ?protein WHERE {?protein wdt:P31 wd:Q8054}" | jq "$(cl_lens sparql_uris --raw)"'
        ]
    }
    
    return examples.get(lens_name, [f'cl_discover example | jq "$(cl_lens {lens_name} --raw)"'])


def _show_lens_usage(lens_name: str, filter_str: str):
    """Show lens with usage examples"""
    response = {
        "status": "success", 
        "data": [{
            "lens": lens_name,
            "filter": filter_str,
            "usage": f'jq "{filter_str}"',
            "pipeline_usage": f'cl_discover example | jq "$(cl_lens {lens_name} --raw)"'
        }],
        "count": 1,
        "meta": {
            "lens_name": lens_name
        }
    }
    
    click.echo(json.dumps(response, indent=2))


def _show_help():
    """Show help when no lens name provided"""
    response = {
        "status": "info",
        "data": [{
            "message": "cl_lens: Semantic jq filter library",
            "usage": "cl_lens LENS_NAME [--raw|--describe]",
            "examples": [
                "cl_lens --list",
                "cl_lens entity_ids",
                "cl_lens pipe_ready --raw"
            ]
        }],
        "count": 1,
        "meta": {
            "total_lenses": len(LENSES)
        },
        "next": [
            "cl_lens --list",
            "cl_lens entity_ids",
            "cl_lens discovery_status"
        ]
    }
    
    click.echo(json.dumps(response, indent=2))


def _handle_unknown_lens(lens_name: str):
    """Handle unknown lens names with suggestions"""
    # Find similar lens names
    similar = []
    for available in LENSES.keys():
        if lens_name.lower() in available.lower() or available.lower() in lens_name.lower():
            similar.append(available)
    
    response = {
        "status": "error",
        "data": [],
        "count": 0,
        "error": {
            "message": f"Unknown lens: {lens_name}",
            "code": "LENS_NOT_FOUND"
        },
        "meta": {
            "requested_lens": lens_name,
            "available_count": len(LENSES)
        },
        "next": [
            "cl_lens --list",
            *[f"cl_lens {s}" for s in similar[:3]]
        ]
    }
    
    click.echo(json.dumps(response, indent=2))


if __name__ == "__main__":
    lens()