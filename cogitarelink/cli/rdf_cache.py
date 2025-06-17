"""rdf_cache: Search and manage cached RDF data following Claude Code patterns.

Clean, composable tool for searching cached semantic knowledge with jq compatibility.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Optional, List, Dict, Any

import click

from ..discovery.cache_manager import cache_manager
from ..core.debug import get_logger

log = get_logger("rdf_cache")


@click.command()
@click.argument('query', required=False, default="")
@click.option('--type', 'result_type', help='Filter by type: class, property, namespace, context')
@click.option('--list', 'list_cache', is_flag=True, help='List cached service descriptions and vocabularies')
@click.option('--graph', 'get_graph', is_flag=True, help='Get complete named graph (use with graph name as query)')
@click.option('--force', is_flag=True, help='Force load large graphs (override size warnings)')
@click.option('--subclasses', help='Find subclasses of given class URI via rdfs:subClassOf')
@click.option('--properties', help='Find properties related to given class URI via rdfs:domain/range')
@click.option('--related', help='Find related terms via skos:broader/narrower, owl:sameAs')
@click.option('--clear', 'clear_cache', is_flag=True, help='Clear all cached RDF data')
@click.option('--clear-item', help='Clear specific cached item by name (e.g., foaf_vocab)')
@click.option('--update-metadata', help='Update semantic metadata for cached item (JSON string)')
def search(query: str, result_type: Optional[str], list_cache: bool, get_graph: bool, force: bool, subclasses: Optional[str], properties: Optional[str], related: Optional[str], clear_cache: bool, clear_item: Optional[str], update_metadata: Optional[str]):
    """Search discovered vocabulary for SPARQL-ready URIs with semantic navigation.
    
    DISCOVERY WORKFLOW STEP 2 of 3:
    1. rdf_get {endpoint} --format turtle  ← Discovery (done)
    2. rdf_cache {term} --type class       ← Search vocabulary (current)
    3. cl_select with discovered URIs      ← Query with real vocabulary
    
    Examples:
        rdf_cache "protein" --type class      # → up:Protein, up:Gene (real URIs)
        rdf_cache "" --list                   # → Show all cached vocabularies with metadata
        rdf_cache foaf_vocab --graph          # → Read complete FOAF ontology
        rdf_cache large_ontology --graph --force  # → Override size warnings
        rdf_cache --subclasses foaf:Agent     # → Find all Agent subclasses via rdfs:subClassOf
        rdf_cache --properties foaf:Person    # → Find properties with Person in domain/range
        rdf_cache --related foaf:knows        # → Find related terms via semantic relationships
        rdf_cache --clear                     # → Clear all cached RDF data
        rdf_cache --clear-item foaf_vocab     # → Clear specific cached vocabulary
        
    Returns ready-to-use SPARQL query templates with discovered URIs.
    NEVER returns guessed vocabulary - only cached service descriptions.
    """
    
    # Handle cache clearing modes
    if clear_cache:
        try:
            start_time = time.time()
            result = clear_all_cache()
            execution_time = time.time() - start_time
            result['execution_time_ms'] = round(execution_time * 1000, 2)
            click.echo(json.dumps(result, indent=2))
            return
        except Exception as e:
            error_result = {
                'error': f'Cache clearing failed: {str(e)}'
            }
            click.echo(json.dumps(error_result, indent=2), err=True)
            sys.exit(1)
    
    if clear_item:
        try:
            start_time = time.time()
            result = clear_cache_item(clear_item)
            execution_time = time.time() - start_time
            result['execution_time_ms'] = round(execution_time * 1000, 2)
            click.echo(json.dumps(result, indent=2))
            return
        except Exception as e:
            error_result = {
                'error': f'Cache item clearing failed: {str(e)}',
                'item': clear_item
            }
            click.echo(json.dumps(error_result, indent=2), err=True)
            sys.exit(1)
    
    # Handle metadata update mode
    if update_metadata:
        try:
            start_time = time.time()
            result = update_cache_metadata(query, update_metadata)
            execution_time = time.time() - start_time
            result['execution_time_ms'] = round(execution_time * 1000, 2)
            click.echo(json.dumps(result, indent=2))
            return
        except Exception as e:
            error_result = {
                'error': f'Metadata update failed: {str(e)}',
                'item': query,
                'metadata': update_metadata
            }
            click.echo(json.dumps(error_result, indent=2), err=True)
            sys.exit(1)
    
    # Handle graph mode (full ontology reading)
    if get_graph:
        if not query.strip():
            click.echo('{"error": "Graph name required when using --graph"}', err=True)
            sys.exit(1)
        try:
            start_time = time.time()
            result = get_full_graph(query, force)
            execution_time = time.time() - start_time
            result['execution_time_ms'] = round(execution_time * 1000, 2)
            click.echo(json.dumps(result, indent=2))
            return
        except Exception as e:
            error_result = {
                'error': f'Graph retrieval failed: {str(e)}',
                'graph_name': query
            }
            click.echo(json.dumps(error_result, indent=2), err=True)
            sys.exit(1)
    
    # Handle semantic navigation modes
    if subclasses or properties or related:
        try:
            start_time = time.time()
            result = navigate_semantic_relationships(subclasses, properties, related)
            execution_time = time.time() - start_time
            result['execution_time_ms'] = round(execution_time * 1000, 2)
            click.echo(json.dumps(result, indent=2))
            return
        except Exception as e:
            error_result = {
                'error': f'Semantic navigation failed: {str(e)}',
                'requested': {'subclasses': subclasses, 'properties': properties, 'related': related}
            }
            click.echo(json.dumps(error_result, indent=2), err=True)
            sys.exit(1)
    
    # Handle list mode
    if list_cache:
        try:
            start_time = time.time()
            result = list_cached_rdf(result_type)
            execution_time = time.time() - start_time
            result['execution_time_ms'] = round(execution_time * 1000, 2)
            click.echo(json.dumps(result, indent=2))
            return
        except Exception as e:
            error_result = {
                'error': f'Cache listing failed: {str(e)}'
            }
            click.echo(json.dumps(error_result, indent=2), err=True)
            sys.exit(1)
    
    if not query.strip():
        click.echo('{"error": "Query cannot be empty - use --list to see cached vocabularies"}', err=True)
        sys.exit(1)
    
    try:
        start_time = time.time()
        
        result = search_cached_rdf(query, result_type)
        
        execution_time = time.time() - start_time
        result['execution_time_ms'] = round(execution_time * 1000, 2)
        
        # Output JSON for jq composability
        click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            'error': f'Cache search failed: {str(e)}',
            'query': query
        }
        click.echo(json.dumps(error_result, indent=2), err=True)
        sys.exit(1)


def list_cache(result_type: Optional[str]):
    """List cached RDF items.
    
    Returns JSON for jq composability.
    
    Examples:
        rdf_cache list                          # List all cached items
        rdf_cache list --type vocabularies      # List vocabulary caches only
    """
    
    try:
        start_time = time.time()
        
        result = list_cached_rdf(result_type)
        
        execution_time = time.time() - start_time
        result['execution_time_ms'] = round(execution_time * 1000, 2)
        
        # Output JSON for jq composability
        click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            'error': f'Cache listing failed: {str(e)}'
        }
        click.echo(json.dumps(error_result, indent=2), err=True)
        sys.exit(1)


def get_cache(cache_key: str):
    """Get specific cached item by key.
    
    Returns JSON for jq composability.
    
    Examples:
        rdf_cache get foaf_vocab                    # Get FOAF vocabulary data
        rdf_cache get uniprot_service               # Get UniProt service info
    """
    
    if not cache_key.strip():
        click.echo('{"error": "Cache key cannot be empty"}', err=True)
        sys.exit(1)
    
    try:
        start_time = time.time()
        
        # Add rdf: prefix if not present
        full_key = cache_key if cache_key.startswith('rdf:') else f'rdf:{cache_key}'
        
        cached_data = cache_manager.get(full_key)
        
        if cached_data:
            result = {
                'success': True,
                'cache_key': full_key,
                'data': cached_data
            }
        else:
            result = {
                'success': False,
                'cache_key': full_key,
                'error': 'Cache key not found',
                'available_keys': get_available_cache_keys()
            }
        
        execution_time = time.time() - start_time
        result['execution_time_ms'] = round(execution_time * 1000, 2)
        
        # Output JSON for jq composability
        click.echo(json.dumps(result, indent=2))
        
        if not cached_data:
            sys.exit(1)
        
    except Exception as e:
        error_result = {
            'error': f'Cache retrieval failed: {str(e)}',
            'cache_key': cache_key
        }
        click.echo(json.dumps(error_result, indent=2), err=True)
        sys.exit(1)


def search_cached_rdf(query: str, result_type: Optional[str]) -> Dict[str, Any]:
    """Search cached RDF data using in-memory index navigation."""
    
    log.debug(f"Searching cache for: {query}")
    
    result = {
        'query': query,
        'type_filter': result_type,
        'results': [],
        'cache_keys': [],
        'claude_guidance': {
            'workflow_status': f'Discovery → Cache Search → Query (Step 2 of 3)',
            'next_actions': [],
            'discovered_vocabulary': {},
            'query_templates': [],
            'index_navigation': {
                'loaded_indices': [],
                'subgraphs_found': [],
                'total_vocabulary_size': 0
            }
        }
    }
    
    try:
        # Load all enhanced indices into memory for fast navigation
        enhanced_indices = load_all_enhanced_indices()
        result['claude_guidance']['index_navigation']['loaded_indices'] = list(enhanced_indices.keys())
        result['claude_guidance']['index_navigation']['total_vocabulary_size'] = sum(
            len(idx.get('classes', {})) + len(idx.get('properties', {})) 
            for idx in enhanced_indices.values()
        )
        
        log.debug(f"Loaded {len(enhanced_indices)} enhanced indices into memory")
        
        # Navigate through @container @index structures in memory
        matches = navigate_vocabulary_indices(enhanced_indices, query, result_type)
        result['results'].extend(matches)
        
        result['total_matches'] = len(result['results'])
        
        # Extract subgraphs from discovered vocabulary
        if result['results']:
            subgraphs = extract_relevant_subgraphs(enhanced_indices, result['results'], query)
            result['claude_guidance']['index_navigation']['subgraphs_found'] = subgraphs
        
        # Add Claude Code guidance based on results
        if result['results']:
            # Generate query templates from discovered vocabulary
            unique_classes = set()
            for match in result['results']:
                if match.get('match_type') == 'class' and 'context' in match:
                    class_id = match['context'].get('id', '')
                    if class_id:
                        unique_classes.add(class_id)
            
            if unique_classes:
                result['claude_guidance']['discovered_vocabulary'] = {
                    'classes_found': list(unique_classes)[:5],  # Top 5
                    'total_classes': len(unique_classes)
                }
                
                # Generate ready-to-use SPARQL templates
                result['claude_guidance']['query_templates'] = [
                    f'SELECT ?item ?label WHERE {{ ?item a <{cls}> ; rdfs:label ?label }} LIMIT 5'
                    for cls in list(unique_classes)[:3]  # Top 3 templates
                ]
                
                result['claude_guidance']['next_actions'] = [
                    f'Ready: cl_select "{template}" --endpoint discovered_endpoint'
                    for template in result['claude_guidance']['query_templates'][:2]
                ]
        else:
            result['claude_guidance']['next_actions'] = [
                f'Try: rdf_cache "{query}" --type property → Find properties instead',
                f'Try: rdf_cache "{query}" → Search all types',
                f'Check: rdf_get {query}_endpoint --format turtle → Discover more vocabulary'
            ]
        
    except Exception as e:
        log.error(f"Cache search failed: {e}")
        result['error'] = str(e)
    
    return result


def search_in_rdf_data(data: Dict[str, Any], query: str, result_type: Optional[str]) -> List[Dict[str, Any]]:
    """Search within cached RDF data for discovered vocabulary matches.
    
    Only returns vocabulary actually found in service descriptions.
    Prioritizes classes and properties for SPARQL querying.
    """
    
    matches = []
    query_lower = query.lower()
    
    # NEW: Use enhanced JSON-LD 1.1 structure if available
    if 'enhanced' in data and data['enhanced']:
        matches.extend(search_enhanced_structure(data['enhanced'], query, result_type))
        if matches:  # If enhanced search found results, use those
            return matches
    
    # FALLBACK: Search in traditional JSON-LD data
    if data.get('format') == 'json-ld' and 'raw' in data:
        raw_data = data['raw']
        
        # Search in @context
        if '@context' in raw_data:
            context = raw_data['@context']
            if isinstance(context, dict):
                for key, value in context.items():
                    if query_lower in key.lower() or (isinstance(value, str) and query_lower in value.lower()):
                        if not result_type or result_type == 'context':
                            matches.append({
                                'type': 'context_term',
                                'value': f'{key} → {value}',
                                'context': {'term': key, 'iri': value}
                            })
        
        # Search in defines (classes and properties)
        if 'defines' in raw_data:
            for item in raw_data['defines']:
                if '@id' in item:
                    item_id = item['@id']
                    label = item.get('label', '')
                    comment = item.get('comment', '')
                    types = item.get('@type', [])
                    
                    # Check if query matches
                    if (query_lower in item_id.lower() or 
                        query_lower in label.lower() or 
                        query_lower in comment.lower()):
                        
                        # Determine match type
                        match_type = determine_item_type(types)
                        
                        if not result_type or result_type == match_type:
                            matches.append({
                                'type': match_type,
                                'value': f'{item_id} ({label})',
                                'context': {
                                    'id': item_id,
                                    'label': label,
                                    'comment': comment,
                                    'types': types
                                }
                            })
    
    # Search in RDF format data  
    elif data.get('format') == 'rdf' and 'namespaces' in data:
        namespaces = data['namespaces']
        for prefix, namespace in namespaces.items():
            if query_lower in prefix.lower() or query_lower in namespace.lower():
                if not result_type or result_type == 'namespace':
                    matches.append({
                        'type': 'namespace',
                        'value': f'{prefix}: <{namespace}>',
                        'context': {'prefix': prefix, 'namespace': namespace}
                    })
    
    return matches


def search_enhanced_structure(enhanced: Dict[str, Any], query: str, result_type: Optional[str]) -> List[Dict[str, Any]]:
    """Search enhanced JSON-LD 1.1 structure with @container @index for fast lookup."""
    
    matches = []
    query_lower = query.lower()
    
    # Search @container @index classes
    if not result_type or result_type == 'class':
        classes = enhanced.get('classes', {})
        for class_name, class_info in classes.items():
            if query_lower in class_name.lower():
                matches.append({
                    'type': 'class',
                    'value': f'{class_name} → {class_info.get("@id", "")}',
                    'context': {
                        'id': class_info.get('@id', ''),
                        'name': class_name,
                        'domain': class_info.get('domain', 'general'),
                        'types': class_info.get('@type', [])
                    }
                })
    
    # Search @container @index properties
    if not result_type or result_type == 'property':
        properties = enhanced.get('properties', {})
        for prop_name, prop_info in properties.items():
            if query_lower in prop_name.lower():
                matches.append({
                    'type': 'property',
                    'value': f'{prop_name} → {prop_info.get("@id", "")}',
                    'context': {
                        'id': prop_info.get('@id', ''),
                        'name': prop_name,
                        'domain': prop_info.get('domain', 'general'),
                        'types': prop_info.get('@type', [])
                    }
                })
    
    # Search @container @index namespaces
    if not result_type or result_type == 'namespace':
        namespaces = enhanced.get('namespaces', {})
        for prefix, namespace_uri in namespaces.items():
            if query_lower in prefix.lower() or query_lower in namespace_uri.lower():
                matches.append({
                    'type': 'namespace',
                    'value': f'{prefix}: <{namespace_uri}>',
                    'context': {
                        'prefix': prefix,
                        'namespace': namespace_uri,
                        'domain': 'namespace'
                    }
                })
    
    # Search @container @graph query templates
    if not result_type or result_type == 'template':
        domains = enhanced.get('domains', {})
        for domain_name, domain_info in domains.items():
            if query_lower in domain_name.lower():
                templates = domain_info.get('@graph', [])
                for template in templates:
                    if query_lower in template.get('name', '').lower():
                        matches.append({
                            'type': 'query_template',
                            'value': f'{template.get("name", "")} → {template.get("description", "")}',
                            'context': {
                                'name': template.get('name', ''),
                                'sparql': template.get('sparql', ''),
                                'description': template.get('description', ''),
                                'domain': domain_name
                            }
                        })
    
    return matches


def determine_item_type(types: List[str]) -> str:
    """Determine the type of an RDF item from its rdf:type values."""
    
    if 'owl:Class' in types or 'rdfs:Class' in types:
        return 'class'
    elif any(prop_type in types for prop_type in ['rdf:Property', 'owl:ObjectProperty', 'owl:DatatypeProperty']):
        return 'property'
    elif 'owl:Ontology' in types:
        return 'ontology'
    else:
        return 'resource'


def list_cached_rdf(result_type: Optional[str]) -> Dict[str, Any]:
    """List cached RDF items with vocabulary discovery metadata."""
    
    result = {
        'type_filter': result_type,
        'cached_items': [],
        'vocabulary_summary': {
            'namespaces': {},
            'domains': {},
            'total_classes': 0,
            'total_properties': 0,
            'vocabulary_coverage': {}
        }
    }
    
    try:
        all_keys = list(cache_manager.cache)
        rdf_keys = [k for k in all_keys if k.startswith('rdf:')]
        
        for key in rdf_keys:
            cache_data = cache_manager.get(key)
            if cache_data:
                item_info = {
                    'cache_key': key,
                    'name': key.replace('rdf:', ''),
                    'format': cache_data.get('format', 'unknown'),
                    'summary': cache_data.get('summary', {}),
                    'cached_at': cache_data.get('cached_at', 'unknown')
                }
                
                # Add format-specific summary info and collect vocabulary metadata
                if cache_data.get('format') == 'json-ld':
                    raw_data = cache_data.get('raw', {})
                    enhanced = cache_data.get('enhanced', {})
                    defines = raw_data.get('defines', [])
                    
                    item_info['size_info'] = {
                        'defined_terms': len(defines),
                        'context_terms': len(raw_data.get('@context', {})) if isinstance(raw_data.get('@context'), dict) else 0
                    }
                    
                    # Collect vocabulary metadata from enhanced structure
                    if enhanced:
                        # Add namespace info
                        namespaces = enhanced.get('namespaces', {})
                        for prefix, uri in namespaces.items():
                            if prefix not in result['vocabulary_summary']['namespaces']:
                                result['vocabulary_summary']['namespaces'][prefix] = {
                                    'uri': uri,
                                    'sources': []
                                }
                            result['vocabulary_summary']['namespaces'][prefix]['sources'].append(key)
                        
                        # Add domain info
                        domains = enhanced.get('domains', {})
                        for domain_name, domain_info in domains.items():
                            if domain_name not in result['vocabulary_summary']['domains']:
                                result['vocabulary_summary']['domains'][domain_name] = {
                                    'templates': 0,
                                    'sources': []
                                }
                            result['vocabulary_summary']['domains'][domain_name]['templates'] += len(domain_info.get('@graph', []))
                            result['vocabulary_summary']['domains'][domain_name]['sources'].append(key)
                        
                        # Count classes and properties
                        classes_count = len(enhanced.get('classes', {}))
                        properties_count = len(enhanced.get('properties', {}))
                        result['vocabulary_summary']['total_classes'] += classes_count
                        result['vocabulary_summary']['total_properties'] += properties_count
                        
                        # Track vocabulary coverage
                        vocab_name = item_info['name']
                        result['vocabulary_summary']['vocabulary_coverage'][vocab_name] = {
                            'classes': classes_count,
                            'properties': properties_count,
                            'domains': list(domains.keys()),
                            'namespaces': list(namespaces.keys())
                        }
                
                elif cache_data.get('format') == 'rdf':
                    namespaces = cache_data.get('namespaces', {})
                    item_info['size_info'] = {
                        'triples': cache_data.get('triples', 0),
                        'namespaces': len(namespaces)
                    }
                    
                    # Add namespace info for RDF format
                    for prefix, uri in namespaces.items():
                        if prefix not in result['vocabulary_summary']['namespaces']:
                            result['vocabulary_summary']['namespaces'][prefix] = {
                                'uri': uri,
                                'sources': []
                            }
                        result['vocabulary_summary']['namespaces'][prefix]['sources'].append(key)
                
                result['cached_items'].append(item_info)
        
        result['total_items'] = len(result['cached_items'])
        
        # Add Claude guidance for vocabulary discovery
        result['claude_guidance'] = {
            'vocabulary_discovery': f"Found {len(result['vocabulary_summary']['namespaces'])} namespaces across {len(result['cached_items'])} vocabularies",
            'available_domains': list(result['vocabulary_summary']['domains'].keys()),
            'namespace_prefixes': list(result['vocabulary_summary']['namespaces'].keys()),
            'discovery_commands': [
                f'rdf_cache "protein" --type class → Find biology classes',
                f'rdf_cache "person" --type class → Find social/foaf classes', 
                f'rdf_cache "" --list → See this vocabulary summary'
            ],
            'vocabulary_stats': {
                'richest_vocabulary': max(result['vocabulary_summary']['vocabulary_coverage'].items(), 
                                        key=lambda x: x[1]['classes'] + x[1]['properties'])[0] if result['vocabulary_summary']['vocabulary_coverage'] else 'none',
                'total_terms': result['vocabulary_summary']['total_classes'] + result['vocabulary_summary']['total_properties']
            }
        }
        
    except Exception as e:
        log.error(f"Cache listing failed: {e}")
        result['error'] = str(e)
    
    return result


def load_all_enhanced_indices() -> Dict[str, Dict[str, Any]]:
    """Load all enhanced JSON-LD 1.1 indices into memory for fast navigation."""
    
    enhanced_indices = {}
    
    try:
        all_keys = list(cache_manager.cache)
        rdf_keys = [k for k in all_keys if k.startswith('rdf:')]
        
        for key in rdf_keys:
            cache_data = cache_manager.get(key)
            if cache_data and isinstance(cache_data, dict) and 'enhanced' in cache_data:
                enhanced = cache_data['enhanced']
                if enhanced and isinstance(enhanced, dict):
                    # Load entire index structure into memory
                    enhanced_indices[key] = {
                        'classes': enhanced.get('classes', {}),
                        'properties': enhanced.get('properties', {}),
                        'namespaces': enhanced.get('namespaces', {}),
                        'domains': enhanced.get('domains', {}),
                        'source_url': cache_data.get('url', key),
                        'format': cache_data.get('format', 'unknown')
                    }
                    log.debug(f"Loaded index {key}: {len(enhanced.get('classes', {}))} classes, {len(enhanced.get('properties', {}))} properties")
        
    except Exception as e:
        log.error(f"Failed to load enhanced indices: {e}")
    
    return enhanced_indices


def navigate_vocabulary_indices(indices: Dict[str, Dict[str, Any]], query: str, result_type: Optional[str]) -> List[Dict[str, Any]]:
    """Navigate through @container @index structures in memory for fast vocabulary lookup."""
    
    matches = []
    query_lower = query.lower()
    
    for cache_key, index in indices.items():
        # Navigate @container @index classes
        if not result_type or result_type == 'class':
            classes = index.get('classes', {})
            for class_name, class_info in classes.items():
                if query_lower in class_name.lower():
                    matches.append({
                        'cache_key': cache_key,
                        'source': index.get('format', 'unknown'),
                        'match_type': 'class',
                        'match_value': f'{class_name} → {class_info.get("@id", "")}',
                        'context': {
                            'id': class_info.get('@id', ''),
                            'name': class_name,
                            'label': class_info.get('label', class_name),
                            'comment': class_info.get('comment', ''),
                            'domain': class_info.get('domain', 'general'),
                            'types': class_info.get('@type', []),
                            'subgraph_key': f'classes.{class_name}'
                        }
                    })
        
        # Navigate @container @index properties
        if not result_type or result_type == 'property':
            properties = index.get('properties', {})
            for prop_name, prop_info in properties.items():
                if query_lower in prop_name.lower():
                    matches.append({
                        'cache_key': cache_key,
                        'source': index.get('format', 'unknown'), 
                        'match_type': 'property',
                        'match_value': f'{prop_name} → {prop_info.get("@id", "")}',
                        'context': {
                            'id': prop_info.get('@id', ''),
                            'name': prop_name,
                            'label': prop_info.get('label', prop_name),
                            'comment': prop_info.get('comment', ''),
                            'domain': prop_info.get('domain', 'general'),
                            'types': prop_info.get('@type', []),
                            'subgraph_key': f'properties.{prop_name}'
                        }
                    })
        
        # Navigate @container @index namespaces
        if not result_type or result_type == 'namespace':
            namespaces = index.get('namespaces', {})
            for prefix, namespace_uri in namespaces.items():
                if query_lower in prefix.lower() or query_lower in namespace_uri.lower():
                    matches.append({
                        'cache_key': cache_key,
                        'source': index.get('format', 'unknown'),
                        'match_type': 'namespace',
                        'match_value': f'{prefix}: <{namespace_uri}>',
                        'context': {
                            'prefix': prefix,
                            'namespace': namespace_uri,
                            'domain': 'namespace',
                            'subgraph_key': f'namespaces.{prefix}'
                        }
                    })
        
        # Navigate @container @graph domain templates
        if not result_type or result_type == 'template':
            domains = index.get('domains', {})
            for domain_name, domain_info in domains.items():
                templates = domain_info.get('@graph', [])
                for i, template in enumerate(templates):
                    template_name = template.get('name', f'template_{i}')
                    template_desc = template.get('description', '')
                    
                    # Search in domain name, template name, or description
                    if (query_lower in domain_name.lower() or 
                        query_lower in template_name.lower() or 
                        query_lower in template_desc.lower()):
                        
                        matches.append({
                            'cache_key': cache_key,
                            'source': index.get('format', 'unknown'),
                            'match_type': 'query_template',
                            'match_value': f'{template_name} → {template_desc}',
                            'context': {
                                'name': template_name,
                                'sparql': template.get('sparql', ''),
                                'description': template_desc,
                                'domain': domain_name,
                                'subgraph_key': f'domains.{domain_name}.@graph.{i}'
                            }
                        })
    
    return matches


def extract_relevant_subgraphs(indices: Dict[str, Dict[str, Any]], matches: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Extract relevant subgraphs from the index based on discovered vocabulary."""
    
    subgraphs = []
    
    for match in matches:
        cache_key = match.get('cache_key', '')
        subgraph_key = match.get('context', {}).get('subgraph_key', '')
        
        if cache_key in indices and subgraph_key:
            index = indices[cache_key]
            
            # Navigate to specific subgraph using JSON path
            try:
                path_parts = subgraph_key.split('.')
                subgraph_data = index
                
                for part in path_parts:
                    if '[' in part and ']' in part:
                        # Handle array access like "@graph[0]"
                        array_key, array_index = part.split('[')
                        array_index = int(array_index.rstrip(']'))
                        subgraph_data = subgraph_data[array_key][array_index]
                    elif part.isdigit():
                        # Handle numeric array indices
                        subgraph_data = subgraph_data[int(part)]
                    else:
                        subgraph_data = subgraph_data[part]
                
                subgraphs.append({
                    'cache_key': cache_key,
                    'subgraph_key': subgraph_key,
                    'data': subgraph_data,
                    'size': len(str(subgraph_data)) if subgraph_data else 0
                })
                
            except (KeyError, IndexError, ValueError) as e:
                log.debug(f"Could not extract subgraph {subgraph_key}: {e}")
    
    return subgraphs


def get_available_cache_keys() -> List[str]:
    """Get list of available RDF cache keys."""
    
    try:
        all_keys = list(cache_manager.cache)
        return [k for k in all_keys if k.startswith('rdf:')]
    except:
        return []


def get_full_graph(graph_name: str, force: bool) -> Dict[str, Any]:
    """Get complete named graph with size guardrails following Claude Code patterns."""
    
    # Add rdf: prefix if not present
    cache_key = graph_name if graph_name.startswith('rdf:') else f'rdf:{graph_name}'
    
    cached_data = cache_manager.get(cache_key)
    if not cached_data:
        return {
            'success': False,
            'error': f'Graph "{graph_name}" not found in cache',
            'available_graphs': [k.replace('rdf:', '') for k in get_available_cache_keys()],
            'suggestion': f'Try: rdf_cache "" --list → See all cached vocabularies'
        }
    
    # Check size and apply guardrails (Claude Code safety pattern)
    graph_metadata = cached_data.get('enhanced', {}).get('graph_metadata', {})
    size_bytes = graph_metadata.get('size_bytes', 0)
    safe_to_load = graph_metadata.get('safe_to_load', True)
    
    if not safe_to_load and not force:
        return {
            'success': False,
            'error': f'Graph too large ({size_bytes:,} bytes > 500KB limit)',
            'graph_metadata': graph_metadata,
            'ontology_metadata': cached_data.get('enhanced', {}).get('ontology_metadata', {}),
            'suggestion': f'Try: rdf_cache {graph_name} --graph --force (override warning)',
            'safe_alternatives': [
                f'rdf_cache "{graph_name.replace("_vocab", "").replace("_ontology", "")}" --type class --limit 20',
                f'rdf_cache --subclasses <specific_class> → Navigate specific parts'
            ]
        }
    
    # Return full graph context (like ReadTool for large files)
    result = {
        'success': True,
        'graph_name': graph_name,
        'cache_key': cache_key,
        'graph_metadata': graph_metadata,
        'ontology_metadata': cached_data.get('enhanced', {}).get('ontology_metadata', {}),
        'full_graph': cached_data.get('raw', {}),  # Complete ontology for Claude to read
        'enhanced_index': cached_data.get('enhanced', {}),  # Structured navigation aid
        'claude_guidance': {
            'ontology_type': 'Complete ontology loaded - Claude can navigate full context',
            'size_info': f'{size_bytes:,} bytes, {graph_metadata.get("triples_count", 0):,} triples',
            'navigation_hints': [
                'Use jq to navigate: .enhanced_index.semantic_index.class_hierarchy',
                'Find classes: .enhanced_index.classes | keys',
                'Find properties: .enhanced_index.properties | keys',
                'See relationships: .enhanced_index.semantic_index'
            ],
            'semantic_capabilities': {
                'class_hierarchies': len(cached_data.get('enhanced', {}).get('semantic_index', {}).get('class_hierarchy', {})),
                'property_constraints': len(cached_data.get('enhanced', {}).get('semantic_index', {}).get('property_constraints', {})),
                'concept_schemes': len(cached_data.get('enhanced', {}).get('semantic_index', {}).get('concept_schemes', {})),
                'cross_references': len(cached_data.get('enhanced', {}).get('semantic_index', {}).get('cross_references', {}))
            }
        }
    }
    
    if not safe_to_load:
        result['claude_guidance']['size_warning'] = f'Large ontology ({size_bytes:,} bytes) - loaded with --force override'
    
    return result


def navigate_semantic_relationships(subclasses: Optional[str], properties: Optional[str], related: Optional[str]) -> Dict[str, Any]:
    """Navigate semantic relationships across all cached ontologies."""
    
    result = {
        'success': True,
        'navigation_type': None,
        'target_uri': None,
        'results': [],
        'claude_guidance': {
            'semantic_navigation': 'Finding relationships via RDFS/OWL/SKOS properties',
            'sources_searched': [],
            'relationship_types': []
        }
    }
    
    # Load all enhanced indices for semantic navigation
    enhanced_indices = load_all_enhanced_indices()
    result['claude_guidance']['sources_searched'] = list(enhanced_indices.keys())
    
    target_uri = subclasses or properties or related
    result['target_uri'] = target_uri
    
    # Navigate subclass relationships (rdfs:subClassOf)
    if subclasses:
        result['navigation_type'] = 'subclass_hierarchy'
        result['claude_guidance']['relationship_types'] = ['rdfs:subClassOf']
        
        for cache_key, index in enhanced_indices.items():
            class_hierarchy = index.get('semantic_index', {}).get('class_hierarchy', {})
            if subclasses in class_hierarchy:
                subclass_list = class_hierarchy[subclasses].get('subclasses', [])
                for subclass in subclass_list:
                    result['results'].append({
                        'relationship': 'rdfs:subClassOf',
                        'subject': subclass,
                        'object': subclasses,
                        'source_graph': cache_key,
                        'description': f'{subclass} is a subclass of {subclasses}'
                    })
    
    # Navigate property domain/range relationships
    elif properties:
        result['navigation_type'] = 'property_relationships'
        result['claude_guidance']['relationship_types'] = ['rdfs:domain', 'rdfs:range']
        
        for cache_key, index in enhanced_indices.items():
            property_constraints = index.get('semantic_index', {}).get('property_constraints', {})
            
            # Find properties with this class in domain or range
            for prop_uri, constraints in property_constraints.items():
                if constraints.get('domain') == properties:
                    result['results'].append({
                        'relationship': 'rdfs:domain',
                        'property': prop_uri,
                        'class': properties,
                        'source_graph': cache_key,
                        'description': f'{prop_uri} has domain {properties}'
                    })
                
                if constraints.get('range') == properties:
                    result['results'].append({
                        'relationship': 'rdfs:range',
                        'property': prop_uri,
                        'class': properties,
                        'source_graph': cache_key,
                        'description': f'{prop_uri} has range {properties}'
                    })
    
    # Navigate related terms (SKOS, OWL equivalences, cross-references)
    elif related:
        result['navigation_type'] = 'related_terms'
        result['claude_guidance']['relationship_types'] = ['skos:broader', 'skos:narrower', 'owl:sameAs', 'owl:equivalentClass', 'rdfs:seeAlso']
        
        for cache_key, index in enhanced_indices.items():
            semantic_index = index.get('semantic_index', {})
            
            # Check SKOS concept schemes
            concept_schemes = semantic_index.get('concept_schemes', {})
            if related in concept_schemes:
                scheme_info = concept_schemes[related]
                for broader in scheme_info.get('broader', []):
                    result['results'].append({
                        'relationship': 'skos:broader',
                        'subject': related,
                        'object': broader,
                        'source_graph': cache_key,
                        'description': f'{related} has broader concept {broader}'
                    })
                
                for narrower in scheme_info.get('narrower', []):
                    result['results'].append({
                        'relationship': 'skos:narrower',
                        'subject': related,
                        'object': narrower,
                        'source_graph': cache_key,
                        'description': f'{related} has narrower concept {narrower}'
                    })
            
            # Check OWL equivalences
            equivalences = semantic_index.get('equivalences', {})
            if related in equivalences:
                for equiv in equivalences[related]:
                    result['results'].append({
                        'relationship': 'owl:equivalentClass/sameAs',
                        'subject': related,
                        'object': equiv,
                        'source_graph': cache_key,
                        'description': f'{related} is equivalent to {equiv}'
                    })
            
            # Check cross-references
            cross_references = semantic_index.get('cross_references', {})
            if related in cross_references:
                for ref in cross_references[related]:
                    result['results'].append({
                        'relationship': 'rdfs:seeAlso',
                        'subject': related,
                        'object': ref,
                        'source_graph': cache_key,
                        'description': f'{related} see also {ref}'
                    })
    
    result['total_relationships'] = len(result['results'])
    
    if not result['results']:
        result['claude_guidance']['no_results_suggestions'] = [
            f'Try: rdf_cache "{target_uri.split(":")[-1]}" → Search for term by name',
            f'Try: rdf_cache "" --list → See all available vocabularies',
            f'Check: URI namespace is loaded in cache'
        ]
    
    return result


def clear_all_cache() -> Dict[str, Any]:
    """Clear all cached RDF data following Claude Code patterns."""
    
    try:
        # Get count of items before clearing
        all_keys = list(cache_manager.cache)
        rdf_keys = [k for k in all_keys if k.startswith('rdf:')]
        items_count = len(rdf_keys)
        
        # Clear only RDF cache items (preserve other cache types)
        for key in rdf_keys:
            cache_manager.cache.delete(key)
        
        result = {
            'success': True,
            'action': 'clear_all_rdf_cache',
            'items_cleared': items_count,
            'cache_keys_cleared': rdf_keys,
            'message': f'Cleared {items_count} RDF cache items',
            'claude_guidance': {
                'cache_status': 'All RDF vocabularies cleared from cache',
                'next_actions': [
                    'Use rdf_get <endpoint> --cache-as <name> → Rebuild cache',
                    'Use rdf_cache "" --list → Verify cache is empty'
                ],
                'discovery_workflow': [
                    '1. rdf_get <endpoint> → Discover and cache vocabularies',
                    '2. rdf_cache <term> → Search cached vocabularies',
                    '3. cl_select → Query with discovered URIs'
                ]
            }
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'action': 'clear_all_rdf_cache',
            'error': str(e),
            'suggestion': 'Check cache permissions and disk space'
        }


def clear_cache_item(item_name: str) -> Dict[str, Any]:
    """Clear specific cached RDF item following Claude Code patterns."""
    
    # Add rdf: prefix if not present
    cache_key = item_name if item_name.startswith('rdf:') else f'rdf:{item_name}'
    
    try:
        # Check if item exists
        cached_data = cache_manager.get(cache_key)
        if not cached_data:
            return {
                'success': False,
                'action': 'clear_cache_item',
                'item': item_name,
                'cache_key': cache_key,
                'error': f'Cache item "{item_name}" not found',
                'available_items': [k.replace('rdf:', '') for k in get_available_cache_keys()],
                'suggestion': f'Use rdf_cache "" --list → See available items'
            }
        
        # Get metadata before deletion
        item_info = {
            'name': item_name,
            'cache_key': cache_key,
            'format': cached_data.get('format', 'unknown')
        }
        
        if cached_data.get('format') == 'json-ld':
            enhanced = cached_data.get('enhanced', {})
            item_info['metadata'] = {
                'classes': len(enhanced.get('classes', {})),
                'properties': len(enhanced.get('properties', {})),
                'size_bytes': enhanced.get('graph_metadata', {}).get('size_bytes', 0)
            }
        
        # Delete the item
        cache_manager.cache.delete(cache_key)
        
        result = {
            'success': True,
            'action': 'clear_cache_item',
            'item_cleared': item_info,
            'message': f'Cleared cache item "{item_name}"',
            'claude_guidance': {
                'cache_status': f'RDF cache item "{item_name}" removed',
                'next_actions': [
                    f'Use rdf_get <endpoint> --cache-as {item_name} → Rebuild this item',
                    'Use rdf_cache "" --list → See remaining cached items'
                ],
                'workflow_impact': f'Need to rediscover vocabulary for "{item_name}" before querying'
            }
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'action': 'clear_cache_item',
            'item': item_name,
            'cache_key': cache_key,
            'error': str(e),
            'suggestion': 'Check cache permissions and item name'
        }


def update_cache_metadata(cache_name: str, metadata_json: str) -> Dict[str, Any]:
    """Update semantic metadata for cached item - Claude Code driven annotation."""
    
    # Add rdf: prefix if not present
    cache_key = cache_name if cache_name.startswith('rdf:') else f'rdf:{cache_name}'
    
    try:
        # Parse the JSON metadata from Claude Code
        metadata = json.loads(metadata_json)
        
        # Get existing cached data
        cached_data = cache_manager.get(cache_key)
        if not cached_data:
            return {
                'success': False,
                'action': 'update_metadata',
                'item': cache_name,
                'cache_key': cache_key,
                'error': f'Cache item "{cache_name}" not found',
                'available_items': [k.replace('rdf:', '') for k in get_available_cache_keys()],
                'suggestion': f'Use rdf_cache "" --list → See available items'
            }
        
        # Create/update metadata structure
        if 'claude_analysis' not in cached_data:
            cached_data['claude_analysis'] = {}
        
        # Store Claude Code's analysis
        cached_data['claude_analysis'].update({
            'semantic_type': metadata.get('semantic_type', 'unknown'),
            'domains': metadata.get('domains', ['general']),
            'purpose': metadata.get('purpose', 'unknown'),
            'dependencies': metadata.get('dependencies', []),
            'usage_patterns': metadata.get('usage_patterns', []),
            'confidence': metadata.get('confidence', 0.0),
            'analysis_notes': metadata.get('notes', ''),
            'analyzed_at': time.time(),
            'analyzed_by': 'claude_code'
        })
        
        # Save back to cache
        cache_manager.set(cache_key, cached_data, ttl=86400)
        
        result = {
            'success': True,
            'action': 'update_metadata',
            'item': cache_name,
            'cache_key': cache_key,
            'metadata_updated': cached_data['claude_analysis'],
            'message': f'Updated semantic metadata for "{cache_name}"',
            'claude_guidance': {
                'annotation_stored': 'Claude Code analysis saved to cache',
                'next_actions': [
                    f'rdf_cache "{cache_name}" --graph → View annotated content',
                    f'rdf_cache "" --list → See metadata in cache listing'
                ],
                'workflow_enhancement': 'Future rdf_cache queries will include your semantic analysis'
            }
        }
        
        return result
        
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'action': 'update_metadata',
            'item': cache_name,
            'error': f'Invalid JSON metadata: {str(e)}',
            'suggestion': 'Provide valid JSON string with semantic metadata',
            'example': '{"semantic_type": "context", "domains": ["biology"], "purpose": "term_mapping", "confidence": 0.9}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'action': 'update_metadata',
            'item': cache_name,
            'cache_key': cache_key,
            'error': str(e),
            'suggestion': 'Check cache permissions and metadata format'
        }


if __name__ == '__main__':
    search()