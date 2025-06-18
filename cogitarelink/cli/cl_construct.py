"""cl_construct: SHACL template reasoning tool following Claude Code patterns.

Apply reasoning templates to discovered vocabularies for knowledge graph construction.
Follows discovery-first workflow with vocabulary-aware template application.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

import click
import httpx

from ..backend.sparql import discover_sparql_endpoints, build_prefixed_query, resolve_endpoint
from ..backend.cache import cache_manager
from ..utils.logging import get_logger

log = get_logger("cl_construct")


# SHACL Template Definitions (loaded from rules.ttl patterns)
SHACL_TEMPLATES = {
    "SC_Transitive": {
        "name": "Subclass Transitivity",
        "description": "Find transitive subclass relationships: C1 ⊑ C2, C2 ⊑ C3 ⇒ C1 ⊑ C3",
        "focus_type": "class",
        "construct": """
            CONSTRUCT {
                ?c1 rdfs:subClassOf ?c3 .
            }
            WHERE {
                ?c1 rdfs:subClassOf ?c2 .
                ?c2 rdfs:subClassOf ?c3 .
                FILTER NOT EXISTS { ?c1 rdfs:subClassOf ?c3 }
            }
        """
    },
    "SP_Transitive": {
        "name": "Subproperty Transitivity", 
        "description": "Find transitive subproperty relationships: P1 ⊑ P2, P2 ⊑ P3 ⇒ P1 ⊑ P3",
        "focus_type": "property",
        "construct": """
            CONSTRUCT {
                ?p1 rdfs:subPropertyOf ?p3 .
            }
            WHERE {
                ?p1 rdfs:subPropertyOf ?p2 .
                ?p2 rdfs:subPropertyOf ?p3 .
                FILTER NOT EXISTS { ?p1 rdfs:subPropertyOf ?p3 }
            }
        """
    },
    "DomainEnt": {
        "name": "Domain Entailment",
        "description": "Infer types from property domains: P rdfs:domain D, S P O ⇒ S a D",
        "focus_type": "property",
        "construct": """
            CONSTRUCT {
                ?s a ?D .
            }
            WHERE {
                ?s ?p ?o .
                ?p rdfs:domain ?D .
                FILTER NOT EXISTS { ?s a ?D }
            }
        """
    },
    "RangeEnt": {
        "name": "Range Entailment", 
        "description": "Infer types from property ranges: P rdfs:range R, S P O ⇒ O a R",
        "focus_type": "property",
        "construct": """
            CONSTRUCT {
                ?o a ?R .
            }
            WHERE {
                ?s ?p ?o .
                ?p rdfs:range ?R .
                FILTER NOT EXISTS { ?o a ?R }
            }
        """
    },
    "SchemaDomainEnt": {
        "name": "Schema.org Domain Hints",
        "description": "Soft type inference from schema.org: P schema:domainIncludes D ⇒ S a D (confidence 0.6)",
        "focus_type": "property", 
        "construct": """
            CONSTRUCT {
                ?s a ?D .
            }
            WHERE {
                ?s ?p ?o .
                ?p schema:domainIncludes ?D .
                FILTER NOT EXISTS { ?s a ?D }
            }
        """
    },
    "InverseEnt": {
        "name": "Inverse Property Entailment",
        "description": "Apply inverse properties: P owl:inverseOf Q, S P O ⇒ O Q S", 
        "focus_type": "property",
        "construct": """
            CONSTRUCT {
                ?o ?q ?s .
            }
            WHERE {
                ?s ?p ?o .
                ?p owl:inverseOf ?q .
                FILTER NOT EXISTS { ?o ?q ?s }
            }
        """
    }
}


@click.command()
@click.argument('template', required=False)
@click.option('--focus', help='Focus entity/class for template application (e.g., up:Protein, foaf:Person)')
@click.option('--endpoint', help='SPARQL endpoint name or URL (auto-detected if not specified)')
@click.option('--cache-as', help='Cache constructed graph with this name for reuse')
@click.option('--limit', type=int, default=100, help='Maximum results to construct (default: 100)')
@click.option('--format', default='json-ld', help='Output format: json-ld, turtle, n-triples (default: json-ld)')
@click.option('--list-templates', is_flag=True, help='Show available SHACL reasoning templates')
@click.option('--describe', help='Show detailed information about a specific template')
@click.option('--timeout', default=30, help='Query timeout in seconds (default: 30)')
def construct(template: Optional[str], focus: Optional[str], endpoint: Optional[str], 
              cache_as: Optional[str], limit: int, format: str, list_templates: bool,
              describe: Optional[str], timeout: int):
    """Apply SHACL reasoning templates to discovered vocabularies for knowledge graph construction.
    
    DISCOVERY WORKFLOW STEP 4 of 4:
    1. rdf_get {endpoint} --cache-as service    ← Service discovery  
    2. rdf_cache service --update-metadata      ← Vocabulary analysis
    3. cl_select with discovered URIs           ← Data exploration
    4. cl_construct --template reasoning        ← Knowledge synthesis (current)
    
    Examples:
        cl_construct SC_Transitive --focus up:Protein --endpoint uniprot
        cl_construct DomainEnt --focus "up:recommendedName" --endpoint uniprot --cache-as protein_domains
        cl_construct --list-templates  # Show available SHACL reasoning patterns
        cl_construct --describe SC_Transitive  # Get template details
    
    Generates CONSTRUCT queries from SHACL templates using discovered vocabulary structure.
    Templates provide reasoning patterns, Claude Code provides semantic understanding.
    """
    
    # Handle template listing mode
    if list_templates:
        try:
            start_time = time.time()
            result = list_available_templates()
            execution_time = time.time() - start_time
            result['execution_time_ms'] = round(execution_time * 1000, 2)
            click.echo(json.dumps(result, indent=2))
            return
        except Exception as e:
            error_result = {
                'error': f'Template listing failed: {str(e)}',
                'success': False
            }
            click.echo(json.dumps(error_result, indent=2), err=True)
            sys.exit(1)
    
    # Handle template description mode
    if describe:
        try:
            start_time = time.time()
            result = describe_template(describe)
            execution_time = time.time() - start_time
            result['execution_time_ms'] = round(execution_time * 1000, 2)
            click.echo(json.dumps(result, indent=2))
            return
        except Exception as e:
            error_result = {
                'error': f'Template description failed: {str(e)}',
                'template': describe,
                'success': False
            }
            click.echo(json.dumps(error_result, indent=2), err=True)
            sys.exit(1)
    
    # Validate template argument
    if not template:
        error_result = {
            'error': 'Template name required',
            'suggestion': 'Use --list-templates to see available templates',
            'success': False
        }
        click.echo(json.dumps(error_result, indent=2), err=True)
        sys.exit(1)
    
    try:
        start_time = time.time()
        
        result = construct_knowledge_graph(template, focus, endpoint, cache_as, limit, format, timeout)
        
        execution_time = time.time() - start_time
        result['execution_time_ms'] = round(execution_time * 1000, 2)
        
        # Output JSON for jq composability (Claude Code pattern)
        click.echo(json.dumps(result, indent=2))
        
        if not result['success']:
            sys.exit(1)
            
    except Exception as e:
        error_result = {
            'success': False,
            'error': f'Tool execution failed: {str(e)}',
            'template': template,
            'focus': focus,
            'endpoint': endpoint or 'auto-detected'
        }
        click.echo(json.dumps(error_result, indent=2), err=True)
        sys.exit(1)


def list_available_templates() -> Dict[str, Any]:
    """List all available SHACL reasoning templates."""
    
    templates_info = []
    for template_id, template_def in SHACL_TEMPLATES.items():
        templates_info.append({
            'id': template_id,
            'name': template_def['name'],
            'description': template_def['description'],
            'focus_type': template_def['focus_type'],
            'usage': f"cl_construct {template_id} --focus <{template_def['focus_type']}> --endpoint <endpoint>"
        })
    
    return {
        'success': True,
        'available_templates': templates_info,
        'count': len(templates_info),
        'claude_guidance': {
            'discovery_workflow': [
                'Step 1: rdf_get to discover endpoint vocabulary',
                'Step 2: rdf_cache to analyze ontology structure', 
                'Step 3: cl_construct to apply reasoning templates',
                'Step 4: Use constructed knowledge for semantic analysis'
            ],
            'template_usage': [
                'SC_Transitive: Find class hierarchies through inheritance',
                'DomainEnt: Discover what types use specific properties',
                'RangeEnt: Find value types for properties',
                'SchemaDomainEnt: Soft type inference from schema.org'
            ]
        }
    }


def describe_template(template_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific template."""
    
    if template_id not in SHACL_TEMPLATES:
        return {
            'success': False,
            'error': f'Unknown template: {template_id}',
            'available_templates': list(SHACL_TEMPLATES.keys())
        }
    
    template_def = SHACL_TEMPLATES[template_id]
    
    return {
        'success': True,
        'template_id': template_id,
        'name': template_def['name'],
        'description': template_def['description'],
        'focus_type': template_def['focus_type'],
        'construct_pattern': template_def['construct'].strip(),
        'example_usage': f"cl_construct {template_id} --focus <{template_def['focus_type']}> --endpoint uniprot",
        'claude_guidance': {
            'when_to_use': get_template_usage_guidance(template_id),
            'focus_examples': get_focus_examples(template_def['focus_type']),
            'workflow_integration': [
                f'1. Discover vocabulary: rdf_get endpoint --cache-as service',
                f'2. Apply template: cl_construct {template_id} --focus entity --endpoint service',
                f'3. Analyze results: Examine constructed triples for semantic insights'
            ]
        }
    }


def get_template_usage_guidance(template_id: str) -> List[str]:
    """Get usage guidance for specific templates."""
    
    guidance = {
        'SC_Transitive': [
            'Use when exploring class hierarchies',
            'Find all superclasses of a specific class',
            'Discover inheritance patterns in ontologies'
        ],
        'DomainEnt': [
            'Use when discovering what entities have certain properties',
            'Find types that use a specific property',
            'Understand property usage patterns'
        ],
        'RangeEnt': [
            'Use when discovering value types for properties',
            'Find what types of values a property can have',
            'Understand property constraints'
        ],
        'SchemaDomainEnt': [
            'Use with schema.org vocabularies',
            'Apply soft type inference',
            'Handle loosely-typed data'
        ]
    }
    
    return guidance.get(template_id, ['General reasoning template'])


def get_focus_examples(focus_type: str) -> List[str]:
    """Get example focus values for different focus types."""
    
    examples = {
        'class': ['up:Protein', 'foaf:Person', 'schema:Organization', 'wd:Q8054'],
        'property': ['up:recommendedName', 'foaf:knows', 'schema:name', 'wdt:P31']
    }
    
    return examples.get(focus_type, ['entity_uri'])


def construct_knowledge_graph(template: str, focus: Optional[str], endpoint: Optional[str], 
                             cache_as: Optional[str], limit: int, format: str, timeout: int) -> Dict[str, Any]:
    """Construct knowledge graph using SHACL template and discovered vocabulary."""
    
    log.debug(f"Constructing knowledge graph with template: {template}")
    
    # Phase 1: Template Validation  
    if template not in SHACL_TEMPLATES:
        return {
            'success': False,
            'error': f'Unknown template: {template}',
            'available_templates': list(SHACL_TEMPLATES.keys()),
            'suggestion': 'Use --list-templates to see available reasoning patterns'
        }
    
    template_def = SHACL_TEMPLATES[template]
    
    # Phase 2: Endpoint Resolution
    if endpoint:
        try:
            endpoint_url, discovered_prefixes = resolve_endpoint(endpoint)
        except ValueError as e:
            return {
                'success': False,
                'error': str(e),
                'template': template
            }
    else:
        endpoint_url, discovered_prefixes = resolve_endpoint("wikidata")
        endpoint = "wikidata"
    
    # Phase 3: Discovery-First Guardrails (Claude Code pattern)
    vocabulary_reminder = check_vocabulary_discovery(endpoint)
    if vocabulary_reminder:
        return {
            'success': False,
            'error': 'Discovery-first workflow required',
            'system_reminder': vocabulary_reminder,
            'template': template,
            'endpoint': endpoint
        }
    
    # Phase 4: Template Application with Discovered Vocabulary (Software 2.0)
    try:
        construct_query = apply_template_to_vocabulary(template_def, template, focus, endpoint, limit, discovered_prefixes)
        
        log.debug(f"Generated CONSTRUCT query:\\n{construct_query}")
        
        # Phase 5: Query Execution
        result = execute_construct_query(construct_query, endpoint_url, format, timeout)
        
        # Phase 6: Caching & Results
        response = {
            'success': True,
            'template': template,
            'template_name': template_def['name'],
            'focus': focus,
            'endpoint': endpoint_url,
            'constructed_triples': len(result.get('data', [])),
            'format': format,
            'data': result,
            'query_used': construct_query
        }
        
        if cache_as:
            cache_result = cache_constructed_graph(result, cache_as, template, focus, endpoint)
            response['cached'] = True
            response['cache_key'] = cache_as
            response['cache_result'] = cache_result
        
        return response
        
    except Exception as e:
        log.error(f"Knowledge graph construction failed: {e}")
        return {
            'success': False,
            'error': f'Construction failed: {str(e)}',
            'template': template,
            'focus': focus,
            'endpoint': endpoint
        }


def check_vocabulary_discovery(endpoint: str) -> Optional[str]:
    """Check if vocabulary has been discovered for reasoning (Claude Code pattern)."""
    
    if not endpoint or endpoint in ["wikidata", "qlever_wikidata_service"]:
        # Well-known endpoints with default mappings, skip check
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
            f"⚠️ TEMPLATE-REASONING REMINDER: No vocabulary discovered for '{endpoint}'. "
            f"SHACL templates need discovered ontology structure. "
            f"Use 'rdf_get {endpoint_url} --cache-as {endpoint}_service' to discover vocabulary first."
        )
    
    if enhanced_entry.semantic_metadata is None:
        return (
            f"⚠️ VOCABULARY-ANALYSIS REMINDER: Service discovered but not analyzed for '{endpoint}'. "
            f"Use 'rdf_cache {endpoint}_service --update-metadata {{...}}' to store vocabulary analysis."
        )
    
    return None


def apply_template_to_vocabulary(template_def: Dict[str, Any], template_id: str, focus: Optional[str], 
                                endpoint: str, limit: int, discovered_prefixes: Optional[Dict[str, str]] = None) -> str:
    """Apply SHACL template using discovered vocabulary (Claude Code intelligence)."""
    
    # Get discovered vocabulary from cache
    cache_key = f"rdf:{endpoint}_service"
    enhanced_entry = cache_manager.get_enhanced(cache_key)
    
    if enhanced_entry:
        vocabulary = enhanced_entry.data.get("enhanced", {})
        prefixes = vocabulary.get("namespaces", {})
        
        # Get Claude Code's semantic metadata with vocabulary mappings
        semantic_metadata = enhanced_entry.semantic_metadata
        vocabulary_mappings = {}
        template_compatibility = {}
        
        if semantic_metadata and hasattr(semantic_metadata, 'usage_patterns'):
            # Look for vocabulary mappings in usage patterns or metadata
            for pattern in semantic_metadata.usage_patterns:
                if pattern.startswith('vocabulary_mapping:'):
                    # Parse pattern like "vocabulary_mapping:subclass_relation:wdt:P279"
                    parts = pattern.split(':')
                    if len(parts) >= 4:
                        mapping_type = parts[2]
                        mapping_value = ':'.join(parts[3:])
                        vocabulary_mappings[mapping_type] = mapping_value
        
        # Also check if Claude Code stored mappings in the data structure
        if 'vocabulary_mappings' in vocabulary:
            vocabulary_mappings.update(vocabulary['vocabulary_mappings'])
        
        # Check template compatibility
        if 'template_compatibility' in vocabulary:
            template_compatibility = vocabulary.get('template_compatibility', {})
            
    else:
        # Use discovered prefixes from endpoint resolution, fallback to defaults
        prefixes = discovered_prefixes or get_default_prefixes(endpoint)
        vocabulary_mappings = get_default_vocabulary_mappings(endpoint)
        template_compatibility = {}
    
    # Check if template is compatible with this endpoint
    if template_id in template_compatibility:
        compat = template_compatibility[template_id]
        if not compat.get('supported', True):
            raise ValueError(f"Template {template_id} not supported for {endpoint}: {compat.get('reason', 'incompatible')}")
    
    # Extract base CONSTRUCT query from SHACL template
    base_query = template_def["construct"].strip()
    
    # Translate vocabulary using Claude Code's discovered mappings
    translated_query = translate_vocabulary_in_query(base_query, vocabulary_mappings, template_id)
    
    # Apply focus entity if provided (Claude Code parameterization)
    if focus:
        # Expand focus using discovered prefixes
        expanded_focus = expand_with_prefixes(focus, prefixes)
        translated_query = apply_focus_filter(translated_query, expanded_focus, template_def["focus_type"])
    
    # Add discovered prefixes
    prefix_lines = []
    for prefix, uri in prefixes.items():
        prefix_lines.append(f"PREFIX {prefix}: <{uri}>")
    
    # Add standard prefixes for reasoning (only if not already discovered)
    standard_prefixes = {
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'schema': 'https://schema.org/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    }
    
    for prefix, uri in standard_prefixes.items():
        if prefix not in prefixes:
            prefix_lines.append(f"PREFIX {prefix}: <{uri}>")
    
    prefixed_query = "\n".join(prefix_lines) + "\n\n" + translated_query
    
    # Add LIMIT for performance (Claude Code pattern)
    if "LIMIT" not in prefixed_query.upper():
        prefixed_query += f" LIMIT {limit}"
    
    return prefixed_query


def expand_with_prefixes(focus: str, prefixes: Dict[str, str]) -> str:
    """Expand focus entity using discovered prefixes."""
    
    if ':' in focus and not focus.startswith('http'):
        # This is a prefixed name, expand it
        prefix, local = focus.split(':', 1)
        if prefix in prefixes:
            return f"<{prefixes[prefix]}{local}>"
    elif focus.startswith('http'):
        # Already a full URI
        return f"<{focus}>"
    
    # Return as-is if can't expand
    return focus


def apply_focus_filter(base_query: str, expanded_focus: str, focus_type: str) -> str:
    """Apply focus entity filter to CONSTRUCT query."""
    
    # Add focus filter based on the template type
    if focus_type == "class":
        # For class-focused templates, filter on class variables
        filter_clause = f"FILTER(?c1 = {expanded_focus} || ?c2 = {expanded_focus} || ?c3 = {expanded_focus})"
    elif focus_type == "property": 
        # For property-focused templates, filter on property variables
        filter_clause = f"FILTER(?p = {expanded_focus})"
    else:
        # Generic entity filter
        filter_clause = f"FILTER(?s = {expanded_focus} || ?o = {expanded_focus})"
    
    # Insert filter before the closing brace of WHERE clause
    lines = base_query.split('\n')  # Fix: use actual newlines, not escaped
    where_end = -1
    brace_count = 0
    in_where = False
    
    for i, line in enumerate(lines):
        if 'WHERE' in line.upper():
            in_where = True
        if in_where:
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                where_end = i
                break
    
    if where_end > 0:
        # Insert filter before the closing WHERE brace
        lines.insert(where_end, f"                {filter_clause}")
    
    return '\n'.join(lines)


def translate_vocabulary_in_query(base_query: str, vocabulary_mappings: Dict[str, str], 
                                  template_id: str) -> str:
    """Translate generic RDFS/OWL vocabulary to endpoint-specific vocabulary."""
    
    if not vocabulary_mappings:
        return base_query
    
    translated_query = base_query
    
    # Apply vocabulary mappings based on template type
    
    if template_id == 'SC_Transitive':
        # Translate rdfs:subClassOf to endpoint-specific subclass relation
        if 'subclass_relation' in vocabulary_mappings:
            subclass_prop = vocabulary_mappings['subclass_relation']
            translated_query = translated_query.replace('rdfs:subClassOf', subclass_prop)
    
    elif template_id == 'DomainEnt':
        # Translate rdfs:domain to endpoint-specific domain relation
        if 'domain_relation' in vocabulary_mappings:
            domain_prop = vocabulary_mappings['domain_relation']
            translated_query = translated_query.replace('rdfs:domain', domain_prop)
        # Translate rdf:type (a) to endpoint-specific instance relation
        if 'instance_relation' in vocabulary_mappings:
            instance_prop = vocabulary_mappings['instance_relation']
            translated_query = translated_query.replace(' a ', f' {instance_prop} ')
    
    elif template_id == 'RangeEnt':
        # Translate rdfs:range to endpoint-specific range relation
        if 'range_relation' in vocabulary_mappings:
            range_prop = vocabulary_mappings['range_relation']
            translated_query = translated_query.replace('rdfs:range', range_prop)
        # Translate rdf:type (a) to endpoint-specific instance relation
        if 'instance_relation' in vocabulary_mappings:
            instance_prop = vocabulary_mappings['instance_relation']
            translated_query = translated_query.replace(' a ', f' {instance_prop} ')
    
    elif template_id == 'SP_Transitive':
        # Translate rdfs:subPropertyOf to endpoint-specific subproperty relation
        if 'subproperty_relation' in vocabulary_mappings:
            subprop_prop = vocabulary_mappings['subproperty_relation']
            translated_query = translated_query.replace('rdfs:subPropertyOf', subprop_prop)
    
    elif template_id == 'InverseEnt':
        # Translate owl:inverseOf to endpoint-specific inverse relation
        if 'inverse_relation' in vocabulary_mappings:
            inverse_prop = vocabulary_mappings['inverse_relation']
            translated_query = translated_query.replace('owl:inverseOf', inverse_prop)
    
    elif template_id == 'SchemaDomainEnt':
        # Translate schema:domainIncludes to endpoint-specific equivalent
        if 'schema_domain_relation' in vocabulary_mappings:
            schema_domain_prop = vocabulary_mappings['schema_domain_relation']
            translated_query = translated_query.replace('schema:domainIncludes', schema_domain_prop)
        # Translate rdf:type (a) to endpoint-specific instance relation
        if 'instance_relation' in vocabulary_mappings:
            instance_prop = vocabulary_mappings['instance_relation']
            translated_query = translated_query.replace(' a ', f' {instance_prop} ')
    
    return translated_query


def get_default_vocabulary_mappings(endpoint: str) -> Dict[str, str]:
    """Get default vocabulary mappings for well-known endpoints."""
    
    mappings = {
        'wikidata': {
            'subclass_relation': 'wdt:P279',
            'instance_relation': 'wdt:P31',
            'domain_relation': None,  # Wikidata doesn't use rdfs:domain
            'range_relation': None,   # Wikidata doesn't use rdfs:range
            'label_relation': 'rdfs:label',
            'inverse_relation': None  # Wikidata doesn't typically use owl:inverseOf
        },
        'qlever_wikidata_service': {
            'subclass_relation': 'wdt:P279',  # QLever uses same Wikidata vocab, just faster with rdfs:label
            'instance_relation': 'wdt:P31',
            'domain_relation': None,  # Wikidata doesn't use rdfs:domain
            'range_relation': None,   # Wikidata doesn't use rdfs:range
            'label_relation': 'rdfs:label',  # This is the difference - QLever uses rdfs:label directly
            'inverse_relation': None  # Wikidata doesn't typically use owl:inverseOf
        },
        'uniprot': {
            'subclass_relation': 'rdfs:subClassOf',
            'instance_relation': 'rdf:type',
            'domain_relation': 'rdfs:domain',
            'range_relation': 'rdfs:range',
            'label_relation': 'rdfs:label',
            'subproperty_relation': 'rdfs:subPropertyOf',
            'inverse_relation': 'owl:inverseOf'
        },
        'wikipathways': {
            'subclass_relation': 'rdfs:subClassOf',
            'instance_relation': 'rdf:type',
            'domain_relation': 'rdfs:domain',
            'range_relation': 'rdfs:range',
            'label_relation': 'rdfs:label'
        }
    }
    
    return mappings.get(endpoint, {})


def get_default_prefixes(endpoint: str) -> Dict[str, str]:
    """Get default prefixes for well-known endpoints."""
    
    # Use KNOWN_ENDPOINTS from sparql.py as source of truth
    from ..backend.sparql import SPARQLEngine
    
    if endpoint in SPARQLEngine.KNOWN_ENDPOINTS:
        return SPARQLEngine.KNOWN_ENDPOINTS[endpoint]["prefixes"]
    
    # Legacy fallbacks for endpoints not yet in KNOWN_ENDPOINTS
    legacy_defaults = {
        'qlever_wikidata_service': {
            'wd': 'http://www.wikidata.org/entity/',
            'wdt': 'http://www.wikidata.org/prop/direct/',
            'wikibase': 'http://wikiba.se/ontology#'
        }
    }
    
    return legacy_defaults.get(endpoint, {})


def execute_construct_query(query: str, endpoint_url: str, format: str, timeout: int) -> Dict[str, Any]:
    """Execute CONSTRUCT query against SPARQL endpoint."""
    
    try:
        from rdflib import Graph
        
        # Map format names to SPARQL accept headers and rdflib formats
        format_mapping = {
            'json-ld': {'accept': 'application/ld+json', 'rdflib': 'json-ld'},
            'turtle': {'accept': 'text/turtle', 'rdflib': 'turtle'},
            'n-triples': {'accept': 'application/n-triples', 'rdflib': 'nt'},
            'rdf-xml': {'accept': 'application/rdf+xml', 'rdflib': 'xml'}
        }
        
        # Default to turtle if format not recognized
        format_info = format_mapping.get(format, format_mapping['turtle'])
        
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                endpoint_url,
                params={
                    "query": query,
                    "format": format_info['accept']
                }
            )
            response.raise_for_status()
            
            # Parse RDF response with rdflib
            g = Graph()
            g.parse(data=response.text, format=format_info['rdflib'])
            
            # Convert to different output formats
            if format == "json-ld":
                # Serialize to JSON-LD
                jsonld_data = g.serialize(format='json-ld')
                import json
                parsed_data = json.loads(jsonld_data)
                
                return {
                    'format': 'json-ld',
                    'data': parsed_data if isinstance(parsed_data, list) else [parsed_data],
                    'raw_response': response.text,
                    'triples_count': len(g)
                }
            else:
                # Return as requested format
                return {
                    'format': format,
                    'data': response.text,
                    'raw_response': response.text,
                    'triples_count': len(g)
                }
            
    except Exception as e:
        log.error(f"CONSTRUCT query execution failed: {e}")
        raise


def cache_constructed_graph(result: Dict[str, Any], cache_as: str, template: str, 
                           focus: Optional[str], endpoint: str) -> Dict[str, Any]:
    """Cache constructed knowledge graph with semantic metadata."""
    
    try:
        cache_key = f'rdf:{cache_as}'
        
        # Store with enhanced cache metadata
        from ..backend.cache import SemanticMetadata
        
        metadata = SemanticMetadata(
            semantic_type="constructed_knowledge_graph",
            domains=["reasoning", "inference"],
            format_type=result.get('format', 'json-ld'),
            purpose="shacl_template_reasoning",
            dependencies=[f"{endpoint}_service"] if endpoint != "wikidata" else [],
            provides={
                "constructed_triples": len(result.get('data', [])),
                "reasoning_template": 1
            },
            confidence_scores={"template_reasoning": 0.9},
            vocabulary_size=len(result.get('data', [])),
            learned_at=time.time(),
            usage_patterns=[f"SHACL_{template}_reasoning"]
        )
        
        cache_manager.set_enhanced(cache_key, result, semantic_metadata=metadata)
        
        log.info(f"Cached constructed knowledge graph as: {cache_as}")
        
        return {
            'success': True,
            'cache_key': cache_as,
            'metadata': metadata.__dict__,
            'claude_guidance': {
                'analysis_available': f'Use rdf_cache {cache_as} --graph to examine constructed knowledge',
                'next_steps': [
                    f'Analyze constructed triples for semantic insights',
                    f'Apply additional reasoning templates if needed',
                    f'Use constructed knowledge for semantic research'
                ]
            }
        }
        
    except Exception as e:
        log.error(f"Failed to cache constructed graph: {e}")
        return {
            'success': False,
            'error': f'Caching failed: {str(e)}'
        }


if __name__ == '__main__':
    construct()