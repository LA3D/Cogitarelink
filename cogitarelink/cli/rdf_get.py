"""rdf_get: RDF content negotiation tool following Claude Code patterns.

Clean, composable tool for fetching and caching RDF data with jq compatibility.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Optional, Dict, Any

import click
import httpx
from rdflib import Graph
from pyld import jsonld

from ..backend.cache import cache_manager
from ..backend.content import content_analyzer
from ..utils.logging import get_logger

log = get_logger("rdf_get")


@click.command()
@click.argument('url')
@click.option('--format', 'format_pref', help='Preferred format: json-ld, turtle, rdf-xml, n3, n-triples')
@click.option('--cache-as', help='Cache name for reuse (e.g., foaf_vocab, uniprot_core)')
@click.option('--discover', is_flag=True, help='Show available formats when content negotiation fails')
def fetch(url: str, format_pref: Optional[str], cache_as: Optional[str], discover: bool):
    """Fetch RDF data with content negotiation and caching.
    
    Returns JSON for jq composability. Supports multiple RDF formats.
    
    Examples:
        rdf_get http://xmlns.com/foaf/0.1/                    # Auto-negotiate format
        rdf_get http://xmlns.com/foaf/0.1/ --format json-ld   # Prefer JSON-LD  
        rdf_get http://xmlns.com/foaf/0.1/ --cache-as foaf    # Cache for reuse
        rdf_get https://unknown.org/data --discover           # Show format options
    """
    
    if not url.strip():
        click.echo('{"error": "URL cannot be empty"}', err=True)
        sys.exit(1)
    
    try:
        start_time = time.time()
        
        result = fetch_rdf_content(url, format_pref, cache_as, discover)
        
        execution_time = time.time() - start_time
        result['execution_time_ms'] = round(execution_time * 1000, 2)
        
        # Output JSON for jq composability
        click.echo(json.dumps(result, indent=2))
        
        if not result['success']:
            sys.exit(1)
            
    except Exception as e:
        error_result = {
            'success': False,
            'error': f'Tool execution failed: {str(e)}',
            'url': url
        }
        click.echo(json.dumps(error_result, indent=2), err=True)
        sys.exit(1)


def check_existing_cache(url: str, cache_as: Optional[str]) -> Dict[str, Any]:
    """Check if URL or cache name already exists to prevent duplicates."""
    
    # Check if user-provided cache name already exists
    if cache_as:
        cache_key = f'rdf:{cache_as}'
        existing_data = cache_manager.get(cache_key)
        if existing_data:
            return {
                'success': True,
                'already_cached': True,
                'cache_key': cache_as,
                'url': url,
                'cache_status': 'already_exists',
                'data': existing_data,
                'claude_guidance': {
                    'cache_optimization': [
                        f'✅ Content already cached as "{cache_as}"',
                        f'Use: rdf_cache "{cache_as}" --graph to read complete ontology',
                        f'Use: rdf_cache "search_term" --type class to find vocabulary',
                        'No need to re-fetch - cache is available for immediate use'
                    ],
                    'workflow_guidance': [
                        'Step 1: ✅ rdf_get completed (cached)',
                        'Step 2: rdf_cache for vocabulary search', 
                        'Step 3: cl_select with discovered URIs'
                    ],
                    'next_actions': [
                        f'rdf_cache "{cache_as}" --graph',
                        f'rdf_cache "term" --type class',
                        f'rdf_cache "" --list'
                    ]
                },
                'suggestions': [
                    f'Cache already exists: use rdf_cache "{cache_as}" --graph',
                    f'Search vocabulary: rdf_cache "term" --type class',
                    'List all caches: rdf_cache "" --list'
                ],
                'execution_time_ms': 0.0  # Cache hit - no network time
            }
    
    # Check if URL has been cached under different names
    # This is a basic check - could be enhanced to scan cache metadata
    url_normalized = url.lower().rstrip('/')
    potential_duplicates = []
    
    # Common URL variations to check
    url_variations = [
        url,
        url.rstrip('/'),
        url + '/',
        url_normalized,
        url_normalized + '/',
        url_normalized.rstrip('/')
    ]
    
    # Check for common cache patterns based on URL
    if 'prov' in url_normalized:
        potential_duplicates.extend(['prov_o', 'prov_ontology', 'prov_vocab'])
    if 'foaf' in url_normalized:
        potential_duplicates.extend(['foaf', 'foaf_vocab', 'foaf_ontology'])
    if 'uniprot' in url_normalized:
        potential_duplicates.extend(['uniprot', 'uniprot_service', 'uniprot_vocab'])
    
    for cache_name in potential_duplicates:
        cache_key = f'rdf:{cache_name}'
        existing_data = cache_manager.get(cache_key)
        if existing_data:
            return {
                'success': True,
                'already_cached': True,
                'cache_key': cache_name,
                'url': url,
                'cache_status': 'found_similar',
                'data': existing_data,
                'claude_guidance': {
                    'cache_optimization': [
                        f'✅ Similar content may already be cached as "{cache_name}"',
                        f'Check: rdf_cache "{cache_name}" --graph to verify content',
                        f'If same content: use rdf_cache "{cache_name}" instead of re-fetching',
                        'If different: specify unique --cache-as name'
                    ],
                    'workflow_guidance': [
                        'Step 1: Verify existing cache content',
                        'Step 2: Use existing cache or fetch with new name',
                        'Step 3: Proceed with vocabulary search'
                    ],
                    'next_actions': [
                        f'rdf_cache "{cache_name}" --graph',
                        f'rdf_cache "" --list',
                        'Compare content before deciding to re-fetch'
                    ]
                },
                'suggestions': [
                    f'Similar cache found: rdf_cache "{cache_name}" --graph',
                    f'Verify content matches your needs',
                    f'If different, use: rdf_get {url} --cache-as unique_name'
                ],
                'execution_time_ms': 0.0  # Cache hit - no network time
            }
    
    # No duplicates found - proceed with fetching
    return {'already_cached': False}


def fetch_rdf_content(url: str, format_pref: Optional[str], cache_as: Optional[str], discover: bool) -> Dict[str, Any]:
    """Fetch RDF content with content negotiation."""
    
    log.debug(f"Fetching RDF from {url}")
    
    # Check for existing cache before fetching
    cache_check = check_existing_cache(url, cache_as)
    if cache_check['already_cached']:
        return cache_check
    
    # Content negotiation priority
    accept_headers = get_accept_headers(format_pref)
    
    result = {
        'success': False,
        'url': url,
        'format_attempted': [],
        'content_type': None,
        'data': None,
        'cache_key': cache_as,
        'suggestions': [],
        'claude_guidance': {
            'discovery_workflow': [
                'Step 1: rdf_get discovers vocabulary (current step)',
                'Step 2: rdf_cache search discovered terms',
                'Step 3: cl_select with discovered URIs only'
            ],
            'anti_patterns': [
                'Never query with guessed URIs like up:Protein',
                'Never skip service description discovery',
                'Never assume vocabulary without verification'
            ]
        }
    }
    
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for accept in accept_headers:
            log.debug(f"Trying Accept: {accept}")
            result['format_attempted'].append(accept)
            
            try:
                response = client.get(url, headers={'Accept': accept})
                content_type = response.headers.get('content-type', '').lower()
                result['content_type'] = content_type
                
                log.debug(f"Status: {response.status_code}, Content-Type: {content_type}")
                
                if response.status_code == 200:
                    parsed_data = parse_rdf_response(response, content_type)
                    
                    if parsed_data:
                        result['success'] = True
                        result['data'] = parsed_data
                        
                        # Cache if requested with content analysis
                        if cache_as:
                            # Perform basic content analysis (no hardcoded classification)
                            content_analysis = content_analyzer.analyze_content_structure(parsed_data, url)
                            cache_result(cache_as, parsed_data, url)
                            result['cached'] = True
                            result['content_analysis'] = {
                                'format': content_analysis['format'],
                                'size_metrics': content_analysis['size_metrics'],
                                'structural_indicators': content_analysis['structural_indicators'],
                                'references': content_analysis['references'],
                                'claude_guidance': {
                                    'analysis_available': 'Use rdf_cache to examine content and add semantic metadata',
                                    'next_steps': [
                                        f'rdf_cache "{cache_as}" --graph to read complete content',
                                        'Analyze content patterns and classify semantic type/domain',
                                        f'Use rdf_cache --update-metadata "{cache_as}" to store your analysis'
                                    ]
                                }
                            }
                        
                        break  # Success, stop trying other formats
                
            except Exception as e:
                log.warning(f"Request failed for {accept}: {e}")
                result['suggestions'].append(f'Request failed for {accept}: {str(e)}')
    
    if not result['success']:
        if discover:
            result['suggestions'].extend(generate_discovery_suggestions(url))
        else:
            result['suggestions'].extend([
                f'Try: rdf_get {url} --discover',
                f'Try: WebFetch {url} --prompt "Extract RDF/JSON-LD data"'
            ])
    
    return result


def get_accept_headers(format_pref: Optional[str]) -> list[str]:
    """Get Accept headers in priority order based on preference."""
    
    
    if format_pref == 'turtle':
        return ['text/turtle', 'application/rdf+xml', 'application/ld+json', 'text/n3', 'application/n-triples']
    elif format_pref == 'json-ld':
        return ['application/ld+json', 'text/turtle', 'application/rdf+xml', 'text/n3']
    elif format_pref == 'rdf-xml':
        return ['application/rdf+xml', 'text/turtle', 'application/ld+json', 'text/n3']
    elif format_pref == 'n3':
        return ['text/n3', 'text/turtle', 'application/ld+json', 'application/rdf+xml']
    elif format_pref == 'n-triples':
        return ['application/n-triples', 'text/plain', 'text/turtle', 'application/ld+json']
    else:
        # Default priority: JSON-LD first for Claude Code compatibility, then common formats
        return ['application/ld+json', 'text/turtle', 'application/rdf+xml', 'text/n3', 'application/n-triples']


def parse_rdf_response(response: httpx.Response, content_type: str) -> Optional[Dict[str, Any]]:
    """Parse RDF response into enhanced JSON-LD 1.1 structure with intelligent indexing."""
    
    try:
        if 'json' in content_type:
            data = response.json()
            
            # Check if it's JSON-LD
            if isinstance(data, dict) and ('@context' in data or '@graph' in data or '@id' in data):
                # Expand JSON-LD for structured access
                expanded = jsonld.expand(data)
                
                # Create enhanced structure with JSON-LD 1.1 @container patterns
                enhanced_structure = create_enhanced_vocabulary_index(data, expanded)
                
                return {
                    'format': 'json-ld',
                    'raw': data,
                    'expanded': expanded,
                    'enhanced': enhanced_structure,
                    'contexts': data.get('@context', {}),
                    'graphs': data.get('@graph', []),
                    'vocabularies': extract_vocabularies(data),
                    'summary': {
                        'type': 'json-ld',
                        'expanded_items': len(expanded),
                        'context_terms': get_context_term_count(data.get('@context', {})),
                        'indexed_classes': len(enhanced_structure.get('classes', {})),
                        'indexed_properties': len(enhanced_structure.get('properties', {})),
                        'query_templates': len(enhanced_structure.get('query_templates', []))
                    }
                }
            else:
                return {'format': 'json', 'data': data}
                
        elif any(fmt in content_type.lower() for fmt in ['turtle', 'rdf+xml', 'xml', 'n3', 'n-triples', 'nt', 'trig', 'n-quads', 'plain']):
            g = Graph()
            
            # Parse various RDF formats with comprehensive format detection
            content_lower = content_type.lower()
            
            if 'turtle' in content_lower:
                g.parse(data=response.text, format='turtle')
                serialization = 'turtle'
            elif 'rdf+xml' in content_lower or ('xml' in content_lower and 'rdf' in content_lower):
                g.parse(data=response.text, format='xml')
                serialization = 'rdf-xml'
            elif 'n3' in content_lower:
                g.parse(data=response.text, format='n3')
                serialization = 'n3'
            elif 'n-triples' in content_lower or 'ntriples' in content_lower:
                g.parse(data=response.text, format='nt')
                serialization = 'n-triples'
            elif 'trig' in content_lower:
                g.parse(data=response.text, format='trig')
                serialization = 'trig'
            elif 'n-quads' in content_lower or 'nquads' in content_lower:
                g.parse(data=response.text, format='nquads')
                serialization = 'n-quads'
            elif 'plain' in content_lower:
                # text/plain often used for N-Triples
                try:
                    g.parse(data=response.text, format='nt')
                    serialization = 'n-triples'
                except:
                    # If N-Triples fails, try turtle
                    g.parse(data=response.text, format='turtle')
                    serialization = 'turtle'
            else:
                # Try turtle as fallback since it's most common and forgiving
                g.parse(data=response.text, format='turtle')
                serialization = 'turtle'
            
            # Extract useful information
            namespaces = dict(g.namespaces())
            triples_count = len(g)
            
            # Convert to JSON-LD for consistent output format
            jsonld_data = g.serialize(format='json-ld')
            jsonld_parsed = json.loads(jsonld_data)
            
            # Handle the case where RDFLib returns a list instead of a dict
            if isinstance(jsonld_parsed, list):
                # Wrap list in a @graph structure for consistency
                jsonld_parsed = {
                    '@context': {},
                    '@graph': jsonld_parsed
                }
            
            # CRITICAL FIX: Apply enhanced indexing to all RDF formats
            # Expand JSON-LD for structured access
            expanded = jsonld.expand(jsonld_parsed)
            
            # Create enhanced structure with JSON-LD 1.1 @container patterns
            enhanced_structure = create_enhanced_vocabulary_index(jsonld_parsed, expanded)
            
            return {
                'format': 'json-ld',  # Changed from 'rdf' to 'json-ld' for consistency
                'serialization': serialization,
                'raw': jsonld_parsed,  # Consistent with JSON-LD path
                'expanded': expanded,  # Added expanded form
                'enhanced': enhanced_structure,  # Added enhanced indexing
                'contexts': jsonld_parsed.get('@context', {}),  # Added contexts
                'graphs': jsonld_parsed.get('@graph', []),  # Added graphs
                'vocabularies': extract_vocabularies(jsonld_parsed),  # Added vocabularies
                'triples': triples_count,
                'namespaces': namespaces,
                'summary': {
                    'type': 'json-ld',  # Changed to json-ld for consistency
                    'serialization_source': serialization,  # Track original format
                    'expanded_items': len(expanded),
                    'context_terms': get_context_term_count(jsonld_parsed.get('@context', {})),
                    'indexed_classes': len(enhanced_structure.get('classes', {})),
                    'indexed_properties': len(enhanced_structure.get('properties', {})),
                    'query_templates': len(enhanced_structure.get('query_templates', [])),
                    'triples': triples_count,
                    'namespaces': len(namespaces)
                }
            }
            
    except Exception as e:
        log.warning(f"Failed to parse RDF: {e}")
        return None


def get_context_term_count(context) -> int:
    """Count terms in @context, handling both dict and list formats."""
    if isinstance(context, dict):
        return len(context)
    elif isinstance(context, list):
        count = 0
        for ctx_item in context:
            if isinstance(ctx_item, dict):
                count += len(ctx_item)
        return count
    else:
        return 0


def extract_vocabularies(data: Dict[str, Any]) -> Dict[str, str]:
    """Extract vocabulary/namespace information from JSON-LD context."""
    
    vocabularies = {}
    context = data.get('@context', {})
    
    # Handle both dict and list contexts (RDFLib may return either)
    if isinstance(context, dict):
        for key, value in context.items():
            if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                vocabularies[key] = value
    elif isinstance(context, list):
        # Process list of context objects
        for ctx_item in context:
            if isinstance(ctx_item, dict):
                for key, value in ctx_item.items():
                    if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                        vocabularies[key] = value
    
    return vocabularies


def create_enhanced_vocabulary_index(raw_data: Dict[str, Any], expanded_data: list) -> Dict[str, Any]:
    """Create enhanced JSON-LD 1.1 structure with semantic indexing for ontology navigation."""
    
    # Enhanced structure using JSON-LD 1.1 @container patterns with semantic relationships
    enhanced = {
        '@context': {
            '@version': 1.1,
            'classes': {'@container': '@index'},
            'properties': {'@container': '@index'},
            'namespaces': {'@container': '@index'},
            'domains': {'@container': ['@graph', '@index']},
            'semantic_index': {'@container': '@index'},
            'ontology_metadata': {'@container': '@index'}
        },
        'classes': {},
        'properties': {},
        'namespaces': extract_vocabularies(raw_data),
        'domains': {},
        'semantic_index': {
            'class_hierarchy': {},  # rdfs:subClassOf relationships
            'property_constraints': {},  # rdfs:domain/range constraints
            'concept_schemes': {},  # skos:ConceptScheme navigation
            'cross_references': {},  # owl:sameAs, rdfs:seeAlso
            'equivalences': {}  # owl:equivalentClass, owl:equivalentProperty
        },
        'ontology_metadata': extract_ontology_metadata(expanded_data),
        'graph_metadata': {
            'size_bytes': len(str(raw_data).encode('utf-8')),
            'triples_count': len(expanded_data),
            'safe_to_load': len(str(raw_data).encode('utf-8')) < 500000,  # 500KB limit
            'load_warning': 'Large ontology - consider subsetting' if len(str(raw_data).encode('utf-8')) > 100000 else None
        }
    }
    
    # Extract classes and properties from raw data (handles FOAF-style defines)
    if 'defines' in raw_data:
        for item in raw_data['defines']:
            if isinstance(item, dict):
                item_types = item.get('@type', [])
                if isinstance(item_types, str):
                    item_types = [item_types]
                
                item_id = item.get('@id', '')
                item_label = item.get('label', extract_short_name(item_id))
                
                # Identify classes
                if any('Class' in t for t in item_types):
                    class_name = extract_short_name(item_id)
                    if class_name:
                        enhanced['classes'][class_name] = {
                            '@id': item_id,
                            '@type': item_types,
                            'label': item_label,
                            'comment': item.get('comment', ''),
                            'domain': classify_domain(item_id)
                        }
                
                # Identify properties
                elif any('Property' in t for t in item_types):
                    prop_name = extract_short_name(item_id)
                    if prop_name:
                        enhanced['properties'][prop_name] = {
                            '@id': item_id,
                            '@type': item_types,
                            'label': item_label,
                            'comment': item.get('comment', ''),
                            'domain': classify_domain(item_id)
                        }
    
    # Also extract from expanded data (handles other vocabulary styles)
    for item in expanded_data:
        if isinstance(item, dict):
            item_types = item.get('@type', [])
            if isinstance(item_types, str):
                item_types = [item_types]
            
            item_id = item.get('@id', '')
            
            # Identify classes
            if any('Class' in t for t in item_types) or 'void#class' in str(item):
                class_name = extract_short_name(item_id)
                if class_name and class_name not in enhanced['classes']:
                    enhanced['classes'][class_name] = {
                        '@id': item_id,
                        '@type': item_types,
                        'domain': classify_domain(item_id)
                    }
            
            # Identify properties
            elif any('Property' in t for t in item_types) or 'void#property' in str(item):
                prop_name = extract_short_name(item_id)
                if prop_name and prop_name not in enhanced['properties']:
                    enhanced['properties'][prop_name] = {
                        '@id': item_id,
                        '@type': item_types,
                        'domain': classify_domain(item_id)
                    }
    
    # Extract semantic relationships from expanded data
    extract_semantic_relationships(enhanced, expanded_data)
    
    # Generate domain-specific query templates
    domains = set()
    for cls in enhanced['classes'].values():
        domains.add(cls.get('domain', 'general'))
    
    for domain in domains:
        domain_classes = [cls for cls in enhanced['classes'].values() if cls.get('domain') == domain]
        if domain_classes:
            enhanced['domains'][domain] = {
                '@graph': generate_query_templates(domain, domain_classes[:5])  # Top 5 classes
            }
    
    return enhanced


def extract_short_name(uri: str) -> str:
    """Extract short name from URI for indexing."""
    if not uri:
        return ''
    
    # Handle URIs like http://purl.uniprot.org/core/Protein
    if '/' in uri:
        return uri.split('/')[-1]
    elif '#' in uri:
        return uri.split('#')[-1]
    return uri


def classify_domain(uri: str) -> str:
    """Classify vocabulary term into domain based on URI patterns."""
    uri_lower = uri.lower()
    
    if any(term in uri_lower for term in ['protein', 'gene', 'organism', 'uniprot', 'bio']):
        return 'biology'
    elif any(term in uri_lower for term in ['person', 'agent', 'foaf', 'social']):
        return 'social'
    elif any(term in uri_lower for term in ['compound', 'chemical', 'molecule']):
        return 'chemistry'
    else:
        return 'general'


def extract_semantic_relationships(enhanced: Dict[str, Any], expanded_data: list) -> None:
    """Extract semantic relationships (RDFS/OWL/SKOS) from expanded JSON-LD data."""
    
    for item in expanded_data:
        if not isinstance(item, dict) or '@id' not in item:
            continue
            
        item_id = item['@id']
        item_types = item.get('@type', [])
        if isinstance(item_types, str):
            item_types = [item_types]
        
        # Extract rdfs:subClassOf relationships
        subclass_of = item.get('http://www.w3.org/2000/01/rdf-schema#subClassOf', [])
        if subclass_of:
            if not isinstance(subclass_of, list):
                subclass_of = [subclass_of]
            for parent in subclass_of:
                parent_id = parent.get('@id') if isinstance(parent, dict) else parent
                if parent_id:
                    if parent_id not in enhanced['semantic_index']['class_hierarchy']:
                        enhanced['semantic_index']['class_hierarchy'][parent_id] = {'subclasses': []}
                    enhanced['semantic_index']['class_hierarchy'][parent_id]['subclasses'].append(item_id)
        
        # Extract rdfs:domain and rdfs:range for properties
        domain = item.get('http://www.w3.org/2000/01/rdf-schema#domain', [])
        range_prop = item.get('http://www.w3.org/2000/01/rdf-schema#range', [])
        
        if domain or range_prop:
            constraint_info = {}
            if domain:
                domain_val = domain[0] if isinstance(domain, list) else domain
                domain_id = domain_val.get('@id') if isinstance(domain_val, dict) else domain_val
                if domain_id:
                    constraint_info['domain'] = domain_id
            
            if range_prop:
                range_val = range_prop[0] if isinstance(range_prop, list) else range_prop
                range_id = range_val.get('@id') if isinstance(range_val, dict) else range_val
                if range_id:
                    constraint_info['range'] = range_id
            
            if constraint_info:
                enhanced['semantic_index']['property_constraints'][item_id] = constraint_info
        
        # Extract SKOS relationships
        broader = item.get('http://www.w3.org/2004/02/skos/core#broader', [])
        narrower = item.get('http://www.w3.org/2004/02/skos/core#narrower', [])
        
        if broader or narrower:
            if item_id not in enhanced['semantic_index']['concept_schemes']:
                enhanced['semantic_index']['concept_schemes'][item_id] = {}
            
            if broader:
                broader_list = broader if isinstance(broader, list) else [broader]
                enhanced['semantic_index']['concept_schemes'][item_id]['broader'] = [
                    b.get('@id') if isinstance(b, dict) else b for b in broader_list
                ]
            
            if narrower:
                narrower_list = narrower if isinstance(narrower, list) else [narrower]
                enhanced['semantic_index']['concept_schemes'][item_id]['narrower'] = [
                    n.get('@id') if isinstance(n, dict) else n for n in narrower_list
                ]
        
        # Extract OWL equivalences
        equivalent_class = item.get('http://www.w3.org/2002/07/owl#equivalentClass', [])
        equivalent_property = item.get('http://www.w3.org/2002/07/owl#equivalentProperty', [])
        same_as = item.get('http://www.w3.org/2002/07/owl#sameAs', [])
        
        equivalences = []
        for equiv_list in [equivalent_class, equivalent_property, same_as]:
            if equiv_list:
                equiv_list = equiv_list if isinstance(equiv_list, list) else [equiv_list]
                for equiv in equiv_list:
                    equiv_id = equiv.get('@id') if isinstance(equiv, dict) else equiv
                    if equiv_id:
                        equivalences.append(equiv_id)
        
        if equivalences:
            enhanced['semantic_index']['equivalences'][item_id] = equivalences
        
        # Extract cross-references (rdfs:seeAlso)
        see_also = item.get('http://www.w3.org/2000/01/rdf-schema#seeAlso', [])
        if see_also:
            see_also_list = see_also if isinstance(see_also, list) else [see_also]
            cross_refs = []
            for ref in see_also_list:
                ref_id = ref.get('@id') if isinstance(ref, dict) else ref
                if ref_id:
                    cross_refs.append(ref_id)
            
            if cross_refs:
                enhanced['semantic_index']['cross_references'][item_id] = cross_refs


def extract_ontology_metadata(expanded_data: list) -> Dict[str, Any]:
    """Extract ontology metadata (Dublin Core, OWL versioning, etc.)."""
    
    metadata = {}
    
    # Look for ontology declaration in expanded data
    for item in expanded_data:
        if not isinstance(item, dict):
            continue
            
        item_types = item.get('@type', [])
        if isinstance(item_types, str):
            item_types = [item_types]
        
        # Check if this is an ontology declaration
        if 'http://www.w3.org/2002/07/owl#Ontology' in item_types:
            # Extract Dublin Core metadata
            metadata['title'] = extract_literal_value(item.get('http://purl.org/dc/terms/title', []))
            metadata['description'] = extract_literal_value(item.get('http://purl.org/dc/terms/description', []))
            metadata['creator'] = extract_literal_value(item.get('http://purl.org/dc/terms/creator', []))
            metadata['contributor'] = extract_literal_value(item.get('http://purl.org/dc/terms/contributor', []))
            metadata['modified'] = extract_literal_value(item.get('http://purl.org/dc/terms/modified', []))
            metadata['created'] = extract_literal_value(item.get('http://purl.org/dc/terms/created', []))
            
            # Extract OWL versioning info
            metadata['version_info'] = extract_literal_value(item.get('http://www.w3.org/2002/07/owl#versionInfo', []))
            metadata['prior_version'] = extract_uri_value(item.get('http://www.w3.org/2002/07/owl#priorVersion', []))
            metadata['incompatible_with'] = extract_uri_value(item.get('http://www.w3.org/2002/07/owl#incompatibleWith', []))
            
            # Extract RDFS metadata
            metadata['comment'] = extract_literal_value(item.get('http://www.w3.org/2000/01/rdf-schema#comment', []))
            metadata['label'] = extract_literal_value(item.get('http://www.w3.org/2000/01/rdf-schema#label', []))
            
            break
    
    return {k: v for k, v in metadata.items() if v is not None}


def extract_literal_value(value_list):
    """Extract literal value from JSON-LD value object."""
    if not value_list:
        return None
    
    if isinstance(value_list, list):
        value_list = value_list[0]
    
    if isinstance(value_list, dict):
        return value_list.get('@value', value_list.get('@id'))
    
    return value_list


def extract_uri_value(value_list):
    """Extract URI value from JSON-LD value object."""
    if not value_list:
        return None
    
    if isinstance(value_list, list):
        value_list = value_list[0]
    
    if isinstance(value_list, dict):
        return value_list.get('@id')
    
    return value_list


def generate_query_templates(domain: str, domain_classes: list) -> list:
    """Generate ready-to-use SPARQL query templates for domain."""
    templates = []
    
    for cls in domain_classes[:3]:  # Limit to 3 templates per domain
        class_uri = cls.get('@id', '')
        class_name = extract_short_name(class_uri)
        
        if class_uri and class_name:
            templates.append({
                '@type': 'QueryTemplate',
                'name': f'find_{class_name.lower()}',
                'sparql': f'SELECT ?item ?label WHERE {{ ?item a <{class_uri}> ; rdfs:label ?label }} LIMIT 10',
                'description': f'Find {class_name} instances with labels',
                'domain': domain
            })
    
    return templates


def cache_result(cache_as: str, data: Dict[str, Any], url: str = "") -> None:
    """Cache the parsed RDF data without automatic classification."""
    
    try:
        # Cache with basic metadata structure (no automatic classification)
        cache_key = f'rdf:{cache_as}'
        cache_manager.set(cache_key, data, ttl=86400)
        
        log.info(f"Cached RDF data as: {cache_as}")
        log.debug(f"Use rdf_cache to analyze and classify this content")
        
    except Exception as e:
        log.error(f"Failed to cache data: {e}")


def generate_discovery_suggestions(url: str) -> list[str]:
    """Generate suggestions when content negotiation fails."""
    
    return [
        f'Try different Accept headers manually',
        f'Check if {url} serves HTML with embedded RDF',
        f'Use WebFetch to examine available formats',
        f'Verify the URL is a valid RDF resource'
    ]


if __name__ == '__main__':
    fetch()