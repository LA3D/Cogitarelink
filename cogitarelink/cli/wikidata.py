#!/usr/bin/env python3
"""
CogitareLink Wikidata CLI - Claude Code Agent Interface

Simple, clean commands designed specifically for Claude Code agents.
No complex flags - just pure JSON responses with agent guidance.

Usage:
    cl_wikidata guide
    cl_wikidata search "Douglas Adams"
    cl_wikidata entity Q42
    cl_wikidata sparql "SELECT ?item WHERE { ?item wdt:P31 wd:Q5 } LIMIT 5"
    cl_wikidata discover wikidata
"""

import asyncio
import argparse
import json
import sys
import time
from typing import Optional, List, Set
from pathlib import Path

from ..adapters.wikidata_client import WikidataClient
from ..adapters.unified_sparql_client import get_sparql_client
from ..core.debug import get_logger

log = get_logger("cl_wikidata")

# Global state for tracking discovered endpoints (Claude Code style)
DISCOVERED_ENDPOINTS: Set[str] = set()
ENDPOINT_VOCABULARIES = {
    "wikidata": ["wd:", "wdt:", "p:", "ps:", "pq:", "rdfs:", "wikibase:", "bd:"],
    "wikipathways": ["wp:", "dc:", "dcterms:", "foaf:", "rdfs:"],
    "uniprot": ["up:", "taxon:", "rdfs:", "skos:"],
    "idsm": ["rdfs:", "owl:", "skos:"],
    "rhea": ["rh:", "rdfs:", "owl:"]
}

# Cache file for persistent state (like Claude Code's file state tracking)
DISCOVERY_CACHE_FILE = Path.home() / ".cogitarelink_discovered_endpoints.json"

def load_discovered_endpoints():
    """Load discovered endpoints from cache file"""
    global DISCOVERED_ENDPOINTS
    try:
        if DISCOVERY_CACHE_FILE.exists():
            with open(DISCOVERY_CACHE_FILE, 'r') as f:
                endpoints = json.load(f)
                DISCOVERED_ENDPOINTS = set(endpoints)
    except Exception:
        DISCOVERED_ENDPOINTS = set()

def save_discovered_endpoints():
    """Save discovered endpoints to cache file"""
    try:
        with open(DISCOVERY_CACHE_FILE, 'w') as f:
            json.dump(list(DISCOVERED_ENDPOINTS), f)
    except Exception:
        pass

def validate_sparql_prerequisites(query: str, endpoint: str) -> Optional[dict]:
    """Claude Code style guardrails for SPARQL workflow"""
    
    load_discovered_endpoints()
    
    # Guardrail 1: Discovery prerequisite (like ReadTool before EditTool)
    if endpoint != "wikidata" and endpoint not in DISCOVERED_ENDPOINTS:
        return {
            "success": False,
            "error": {
                "code": "DISCOVERY_REQUIRED",
                "message": f"Endpoint '{endpoint}' must be discovered before querying",
                "required_action": f"cl_wikidata discover {endpoint}",
                "reasoning": "Schema discovery provides vocabulary context needed for effective queries",
                "suggestions": [
                    f"Run: cl_wikidata discover {endpoint}",
                    "Discovery provides CoT patterns and vocabulary guidance",
                    "This prevents common prefix and syntax errors"
                ]
            }
        }
    
    return None

async def guide_command(domain: str = "general", level: str = "beginner"):
    """Agent workflow guidance - exactly like wikidata-mcp reference"""
    
    workflows = {
        "general": {
            "beginner": {
                "workflow_name": "Agent Cold Start Workflow", 
                "description": "Essential tool discovery and basic entity research",
                "tools_sequence": [
                    {"tool": "--help", "purpose": "Discover available tools", "example": "cl_wikidata --help"},
                    {"tool": "discover", "purpose": "Get endpoint schema and CoT patterns", "example": "cl_wikidata discover wikidata"},
                    {"tool": "search", "purpose": "Find entities of interest", "example": "cl_wikidata search 'Douglas Adams'"},
                    {"tool": "entity", "purpose": "Get comprehensive entity data", "example": "cl_wikidata entity Q42"},
                    {"tool": "property", "purpose": "Understand property meanings", "example": "cl_wikidata property P31 P856"}
                ],
                "reasoning_patterns": [
                    "🎯 DISCOVERY-FIRST APPROACH: Always start with 'discover' to get CoT guidance for new endpoints",
                    "🔍 PROGRESSIVE EXPLORATION: Search → Entity → Property → Advanced workflows", 
                    "🧠 TOOL COMPOSITION: Chain tools based on suggestions in response metadata"
                ]
            }
        }
    }
    
    domain_workflows = workflows.get(domain, workflows["general"])
    workflow = domain_workflows.get(level, domain_workflows["beginner"])
    
    response = {
        "success": True,
        "data": {
            "workflow": workflow,
            "available_tools": ["search", "entity", "sparql", "discover", "property"],
            "tool_categories": {
                "basic_discovery": ["search", "entity", "property"],
                "schema_intelligence": ["discover"],
                "advanced_queries": ["sparql"]
            },
            "cot_features": {
                "reasoning_scaffolds": "All tools provide reasoning context in 'suggestions' fields",
                "progressive_complexity": "Discovery provides curricula from basic to advanced",
                "workflow_orchestration": "Multi-tool composition guidance"
            }
        },
        "metadata": {
            "domain": domain,
            "level": level,
            "agent_guidance_version": "2.0",
            "cot_enabled": True
        },
        "suggestions": {
            "immediate_next_steps": [
                "Try: cl_wikidata --help",
                "Use 'cl_wikidata discover wikidata' to get comprehensive schema guidance",
                "All tool responses include 'suggestions' with next recommended actions"
            ],
            "workflow_progression": [
                f"Follow the 5-step workflow for {workflow['workflow_name']}",
                "Each tool response includes reasoning scaffolds for next steps",
                "Use discovery command for new endpoints to get domain-specific CoT patterns"
            ],
            "advanced_features": [
                "Use '--help' on any command for parameter details",
                "Chain tools based on ID/URL outputs from previous commands", 
                "Explore general domain patterns with 'discover' command"
            ]
        }
    }
    
    print(json.dumps(response, indent=2))

async def search_command(query: str, limit: int = 10, entity_type: Optional[str] = None, language: str = "en"):
    """Search for entities - Agent-friendly output exactly like reference"""
    start_time = time.time()
    
    try:
        client = WikidataClient()
        raw_results = await client.search_entities(query, language, limit, entity_type)
        
        # Convert to clean agent format - exactly like reference
        results = []
        for item in raw_results.get('search', []):
            results.append({
                'id': item.get('id'),
                'label': item.get('label', 'No label'),
                'description': item.get('description', 'No description'),
                'url': item.get('concepturi', ''),
                'match_score': item.get('match', {}).get('text', '')
            })
        
        execution_time = int((time.time() - start_time) * 1000)
        
        response = {
            "success": True,
            "data": {
                "query": query,
                "results": results,
                "total_found": len(results)
            },
            "metadata": {
                "execution_time_ms": execution_time,
                "cached": False,
                "data_freshness": "current",
                "api_version": "1.0",
                "language": language,
                "entity_type": entity_type
            },
            "suggestions": {
                "next_tools": [
                    f"Get detailed info: cl_wikidata entity('{results[0]['id']}')" if results else ""
                ],
                "related_queries": [
                    "Try with specific type: entity_type='person' or 'place'"
                ],
                "optimization_hints": []
            }
        }
        
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": {
                "code": "SEARCH_ERROR",
                "message": f"Search failed: {str(e)}",
                "suggestions": ["Check internet connection", "Try a simpler query", "Retry in a moment"]
            }
        }
        print(json.dumps(error_response, indent=2))

async def entity_command(entity_id: str, language: str = "en", include_claims: bool = True, properties: Optional[List[str]] = None):
    """Get entity details - Agent-friendly output exactly like reference"""
    start_time = time.time()
    
    try:
        client = WikidataClient()
        
        # Get entity data
        props = None
        if not include_claims:
            props = ['labels', 'descriptions', 'sitelinks']
        elif properties:
            props = ['labels', 'descriptions', 'sitelinks', 'claims']
        
        raw_result = await client.get_entities([entity_id], language, props)
        
        if entity_id not in raw_result.get('entities', {}):
            error_response = {
                "success": False,
                "error": {
                    "code": "ENTITY_NOT_FOUND",
                    "message": f"Entity {entity_id} not found",
                    "suggestions": ["Check the entity ID is correct", "Use cl_wikidata search to find entities"]
                }
            }
            print(json.dumps(error_response, indent=2))
            return
        
        # Convert to CogitareLink entity to process claims properly
        entity_data = raw_result['entities'][entity_id]
        entity = await client.convert_entity_data_to_entity(entity_data, entity_id)
        
        if not entity:
            error_response = {
                "success": False,
                "error": {
                    "code": "ENTITY_PROCESSING_FAILED", 
                    "message": f"Failed to process entity {entity_id}",
                    "suggestions": ["Try again", "Check entity ID format"]
                }
            }
            print(json.dumps(error_response, indent=2))
            return
        
        # Build response exactly like reference format
        response_data = {
            'id': entity_id,
            'label': entity.content.get('name', 'No label'),
            'description': entity.content.get('description', 'No description'),
            'sitelinks': {},
            'claims': {}
        }
        
        # Add Wikipedia links if available
        if entity.content.get('wikipediaUrl'):
            response_data['wikipedia_url'] = entity.content['wikipediaUrl']
        
        # Process claims in reference format
        if include_claims and 'claims' in entity.content:
            claims = entity.content['claims']
            for prop_id, claim_list in claims.items():
                values = []
                for claim in claim_list:
                    if isinstance(claim, dict) and 'value' in claim:
                        values.append({
                            'value': str(claim['value']),
                            'rank': claim.get('rank', 'normal')
                        })
                
                if values:
                    response_data['claims'][prop_id] = values
        
        execution_time = int((time.time() - start_time) * 1000)
        
        response = {
            "success": True,
            "data": response_data,
            "metadata": {
                "execution_time_ms": execution_time,
                "cached": False,
                "data_freshness": "current",
                "api_version": "1.0",
                "entity_id": entity_id,
                "language": language,
                "claims_included": include_claims,
                "properties_filtered": properties is not None
            },
            "suggestions": {
                "next_tools": [
                    f"Explore relationships: cl_wikidata sparql with {entity_id}",
                    "Query with SPARQL for specific properties"
                ],
                "related_queries": [
                    "Find similar entities of same type",
                    f"Explore works or activities related to {response_data['label']}"
                ],
                "optimization_hints": []
            }
        }
        
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": {
                "code": "ENTITY_ERROR",
                "message": f"Failed to get entity data: {str(e)}",
                "suggestions": ["Check internet connection", "Verify entity ID exists", "Try again in a moment"]
            }
        }
        print(json.dumps(error_response, indent=2))

async def sparql_command(query: str, endpoint: str = "wikidata", format_type: str = "table", limit: int = 100, timeout: int = 30):
    """Execute SPARQL query - Agent-friendly output with guardrails exactly like reference"""
    
    # GUARDRAIL VALIDATION (Claude Code style)
    validation_error = validate_sparql_prerequisites(query, endpoint)
    if validation_error:
        print(json.dumps(validation_error, indent=2))
        return
    
    start_time = time.time()
    
    try:
        if endpoint == "wikidata":
            # Use our basic Wikidata client
            client = WikidataClient()
            raw_result = await client.sparql_query(query)
        else:
            # Use unified endpoint client
            client = get_sparql_client()
            query_result = await client.query(endpoint, query, add_prefixes=True, timeout=timeout)
            raw_result = query_result.data
        
        # Process results like reference
        bindings = raw_result.get('results', {}).get('bindings', [])
        variables = raw_result.get('head', {}).get('vars', [])
        
        execution_time = int((time.time() - start_time) * 1000)
        
        response = {
            "success": True,
            "data": {
                "query": query,
                "results": {
                    "variables": variables,
                    "bindings": bindings,
                    "total": len(bindings)
                },
                "endpoint": endpoint
            },
            "metadata": {
                "execution_time_ms": execution_time,
                "cached": False,
                "data_freshness": "current", 
                "api_version": "1.0",
                "endpoint": endpoint,
                "query_complexity": _calculate_query_complexity(query)
            },
            "suggestions": {
                "next_tools": [
                    "Use entity IDs from results with cl_wikidata entity",
                    "Refine query with additional constraints"
                ],
                "related_queries": [
                    "Add FILTER clauses for more specific results",
                    "Use different endpoints for specialized data"
                ],
                "optimization_hints": []
            }
        }
        
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": {
                "code": "SPARQL_ERROR",
                "message": f"SPARQL query failed: {str(e)}",
                "endpoint": endpoint,
                "suggestions": [
                    f"Run 'cl_wikidata discover {endpoint}' to check endpoint availability",
                    "Verify SPARQL syntax against endpoint documentation",
                    "Check network connectivity to endpoint"
                ]
            }
        }
        print(json.dumps(error_response, indent=2))

def _calculate_query_complexity(query: str) -> float:
    """Calculate SPARQL query complexity score"""
    complexity_score = 0.0
    query_upper = query.upper()
    
    if 'OPTIONAL' in query_upper:
        complexity_score += query_upper.count('OPTIONAL') * 0.5
    if 'FILTER' in query_upper:
        complexity_score += query_upper.count('FILTER') * 0.3
    if 'UNION' in query_upper:
        complexity_score += query_upper.count('UNION') * 0.7
    if 'LIMIT' not in query_upper:
        complexity_score += 1.0
    
    return complexity_score

async def discover_command(endpoint: str, method: str = "auto"):
    """Discover endpoint schema - Agent-friendly output with state tracking"""
    try:
        # Simple built-in schema for wikidata 
        if endpoint == "wikidata":
            schema_info = {
                "endpoint_info": {
                    "url": "https://query.wikidata.org/sparql",
                    "discovery_method": "known_patterns",
                    "discovery_time_ms": 0
                },
                "vocabularies": {
                    "wd": "http://www.wikidata.org/entity/",
                    "wdt": "http://www.wikidata.org/prop/direct/",
                    "p": "http://www.wikidata.org/prop/",
                    "ps": "http://www.wikidata.org/prop/statement/",
                    "pq": "http://www.wikidata.org/prop/qualifier/",
                    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
                },
                "classes": {
                    "Q5": {"description": "human", "usage_count": 1000000},
                    "Q8054": {"description": "protein", "usage_count": 50000},
                    "Q11173": {"description": "chemical compound", "usage_count": 100000}
                },
                "properties": {
                    "P31": {"description": "instance of", "usage_count": 50000000},
                    "P352": {"description": "UniProt protein ID", "usage_count": 45000},
                    "P683": {"description": "ChEBI ID", "usage_count": 25000}
                },
                "query_patterns": {
                    "entity_search": "SELECT ?item ?itemLabel WHERE { ?item rdfs:label ?label . FILTER(CONTAINS(?label, '{search_term}')) SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' } }",
                    "instance_query": "SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:{class_id} . SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' } }"
                },
                "guidance": {
                    "performance_hints": [
                        "⚠️ ENDPOINT SIZE: ~10+ billion triples - always use specific constraints!",
                        "Always use SERVICE wikibase:label for human-readable labels",
                        "Use LIMIT to prevent timeouts (recommended: 10-1000)",
                        "Filter early with wdt: properties for better performance",
                        "NEVER use SELECT ?s ?p ?o without type/property constraints"
                    ],
                    "agent_guidance": [
                        "Start entity discovery with rdfs:label or wdt:P31 (instance of)",
                        "Use P352 (UniProt), P683 (ChEBI), P662 (PubChem) for biological cross-references",
                        "Always include SERVICE wikibase:label for readable results"
                    ]
                }
            }
            
            # Mark as discovered
            DISCOVERED_ENDPOINTS.add(endpoint)
            save_discovered_endpoints()
            
            print(json.dumps(schema_info, indent=2))
        else:
            # For non-wikidata endpoints, use multi-endpoint client if available
            try:
                client = get_sparql_client()
                # This would use the discovery engine if it exists
                error_response = {
                    "success": False,
                    "error": {
                        "code": "DISCOVERY_NOT_IMPLEMENTED",
                        "message": f"Discovery for {endpoint} not yet implemented",
                        "suggestions": [
                            "Use 'wikidata' endpoint which has built-in schema",
                            "Manual endpoint discovery coming soon"
                        ]
                    }
                }
                print(json.dumps(error_response, indent=2))
            except Exception as e:
                error_response = {
                    "success": False,
                    "error": {
                        "code": "DISCOVERY_FAILED",
                        "message": f"Schema discovery failed: {str(e)}",
                        "endpoint": endpoint,
                        "suggestions": [
                            "Check endpoint accessibility and network connectivity",
                            "Use 'wikidata' for basic functionality"
                        ]
                    }
                }
                print(json.dumps(error_response, indent=2))
                
    except Exception as e:
        error_response = {
            "success": False,
            "error": {
                "code": "DISCOVERY_FAILED",
                "message": f"Schema discovery failed: {str(e)}",
                "endpoint": endpoint,
                "suggestions": [
                    "Check endpoint accessibility", 
                    "Use 'wikidata' for basic functionality"
                ]
            }
        }
        print(json.dumps(error_response, indent=2))

async def property_command(property_ids: List[str], language: str = "en", include_constraints: bool = False):
    """Property lookup - Agent-friendly output exactly like reference"""
    try:
        client = WikidataClient()
        results = []
        
        for prop_id in property_ids:
            try:
                raw_result = await client.get_entities([prop_id], language)
                
                if prop_id in raw_result.get('entities', {}):
                    entity_data = raw_result['entities'][prop_id]
                    
                    prop_info = {
                        'id': prop_id,
                        'label': entity_data.get('labels', {}).get(language, {}).get('value', 'No label'),
                        'description': entity_data.get('descriptions', {}).get(language, {}).get('value', 'No description'),
                        'datatype': None,
                        'constraints': {},
                        'usage_count': None
                    }
                    
                    results.append(prop_info)
                else:
                    results.append({
                        'id': prop_id,
                        'error': 'Property not found'
                    })
                    
            except Exception as e:
                results.append({
                    'id': prop_id,
                    'error': f'Error retrieving property: {str(e)}'
                })
        
        # Format exactly like reference
        output = {
            'success': True,
            'data': {
                'properties': results,
                'total_found': len([r for r in results if 'error' not in r])
            },
            'metadata': {
                'language': language,
                'include_constraints': include_constraints
            },
            'suggestions': {
                'next_tools': [
                    'Use property IDs with cl_wikidata sparql for complex queries',
                    'Use cl_wikidata entity to see how properties are used on specific entities'
                ],
                'usage_patterns': []
            }
        }
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": {
                "code": "PROPERTY_ERROR",
                "message": f"Property lookup failed: {str(e)}",
                "suggestions": ["Check property ID format", "Verify internet connection"]
            }
        }
        print(json.dumps(error_response, indent=2))

def create_parser():
    """Create argument parser - simplified like reference"""
    parser = argparse.ArgumentParser(
        description="CogitareLink Wikidata CLI - Claude Code Agent Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🧬 CLAUDE CODE BIOLOGICAL RESEARCH INTERFACE

IMPORTANT: Always start with 'discover' for new endpoints to get CoT patterns
IMPORTANT: All responses are JSON with reasoning scaffolds for next steps

## CRITICAL WORKFLOW: Discovery → Query → Follow → Analysis

# STEP 1: DISCOVER CAPABILITIES (REQUIRED FIRST STEP)
cl_wikidata discover wikidata                      # Core knowledge graph

# STEP 2: BASIC QUERIES  
cl_wikidata search "insulin"                       # Find entities
cl_wikidata entity Q50265665                       # Get entity details
cl_wikidata sparql "SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q8054 } LIMIT 5"

# STEP 3: UNDERSTAND PROPERTIES
cl_wikidata property P31 P352 P683                 # Look up property meanings

OUTPUT: JSON with success, data, metadata, suggestions (NOT human-readable text)
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Guide command for cold start
    guide_parser = subparsers.add_parser("guide", help="Agent workflow guidance and tool discovery")
    guide_parser.add_argument("--domain", choices=["general"], default="general", help="Domain-specific guidance")
    guide_parser.add_argument("--level", choices=["beginner"], default="beginner", help="Complexity level")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for entities")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum results (default: 10)")
    search_parser.add_argument("--type", dest="entity_type", help="Entity type filter")
    search_parser.add_argument("--language", default="en", help="Language code (default: en)")
    
    # Entity command
    entity_parser = subparsers.add_parser("entity", help="Get entity details")
    entity_parser.add_argument("entity_id", help="Wikidata entity ID (e.g., Q42)")
    entity_parser.add_argument("--language", default="en", help="Language code (default: en)")
    entity_parser.add_argument("--no-claims", action="store_false", dest="include_claims", help="Exclude claims/properties")
    entity_parser.add_argument("--properties", nargs="+", help="Specific properties to include (e.g., P31 P106)")
    
    # SPARQL command
    sparql_parser = subparsers.add_parser("sparql", help="Execute SPARQL query")
    sparql_parser.add_argument("query", help="SPARQL query")
    sparql_parser.add_argument("--endpoint", default="wikidata", help="Target endpoint (default: wikidata)")
    sparql_parser.add_argument("--format", dest="format_type", choices=["table", "json"], default="table", help="Output format (default: table)")
    sparql_parser.add_argument("--limit", type=int, default=100, help="Result limit (default: 100)")
    sparql_parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds (default: 30)")
    
    # Property command
    property_parser = subparsers.add_parser("property", help="Look up property definitions")
    property_parser.add_argument("property_ids", nargs="+", help="Property IDs (e.g., P31 P106 P569)")
    property_parser.add_argument("--language", default="en", help="Language code (default: en)")
    property_parser.add_argument("--constraints", action="store_true", help="Include constraint information")
    
    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover endpoint schema")
    discover_parser.add_argument("endpoint", help="Endpoint URL or alias")
    discover_parser.add_argument("--method", default="auto", help="Discovery method (default: auto)")
    
    return parser

async def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "guide":
            await guide_command(args.domain, args.level)
        elif args.command == "search":
            await search_command(args.query, args.limit, args.entity_type, args.language)
        elif args.command == "entity":
            await entity_command(args.entity_id, args.language, args.include_claims, args.properties)
        elif args.command == "sparql":
            await sparql_command(args.query, args.endpoint, args.format_type, args.limit, args.timeout)
        elif args.command == "property":
            await property_command(args.property_ids, args.language, args.constraints)
        elif args.command == "discover":
            await discover_command(args.endpoint, args.method)
        else:
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

def cli():
    """Entry point for console script"""
    asyncio.run(main())

if __name__ == "__main__":
    cli()