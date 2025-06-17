"""LLM-friendly error message formatting following Claude Code patterns.

Provides clear, actionable error messages optimized for Claude Code consumption
with specific suggestions for correction.
"""

from typing import Dict, Any, List, Optional
import re


def format_validation_error(error: Exception, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format validation errors for LLM consumption following Claude Code patterns.
    
    Returns structured error response with suggestions for fixing the input.
    """
    return {
        'success': False,
        'error': str(error),
        'tool': tool_name,
        'error_type': 'input_validation',
        'suggestions': generate_error_suggestions(error, tool_name, input_data),
        'corrected_examples': generate_corrected_examples(error, tool_name),
        'documentation': get_tool_documentation_link(tool_name)
    }


def generate_error_suggestions(error: Exception, tool_name: str, input_data: Dict[str, Any]) -> List[str]:
    """Generate specific suggestions for fixing validation errors."""
    suggestions = []
    error_msg = str(error).lower()
    
    # URL validation errors
    if 'url' in error_msg or 'invalid url' in error_msg:
        suggestions.extend([
            'Ensure URL starts with http:// or https://',
            'Check for typos in the URL',
            'Try a known working endpoint like https://sparql.uniprot.org/sparql'
        ])
    
    # Cache name validation errors  
    if 'cache' in error_msg and 'name' in error_msg:
        suggestions.extend([
            'Use only alphanumeric characters and underscores in cache names',
            'Keep cache names under 50 characters',
            'Example: --cache-as uniprot_proteins'
        ])
    
    # JSON validation errors
    if 'json' in error_msg:
        suggestions.extend([
            'Ensure JSON string is properly quoted',
            'Check for missing commas or brackets',
            'Example: \'{"semantic_type": "vocabulary", "domains": ["biology"]}\''
        ])
    
    # SPARQL query errors
    if 'select' in error_msg or 'sparql' in error_msg:
        suggestions.extend([
            'SPARQL queries must start with SELECT, ASK, DESCRIBE, or CONSTRUCT',
            'Check for balanced braces { }',
            'Only read-only queries are allowed (no DELETE, INSERT, DROP)'
        ])
    
    # Limit/range errors
    if 'limit' in error_msg or 'range' in error_msg:
        suggestions.extend([
            'Use --limit between 1 and 100 for searches',
            'Use --limit between 1 and 1000 for SPARQL queries',
            'Example: --limit 10'
        ])
    
    # Empty query errors
    if 'empty' in error_msg or 'min_length' in error_msg:
        suggestions.extend([
            'Query cannot be empty',
            'Provide a search term or entity identifier',
            'Example: "insulin" or "spike protein"'
        ])
    
    # Endpoint errors
    if 'endpoint' in error_msg:
        suggestions.extend([
            'Use a known endpoint alias: wikidata, uniprot, wikipathways',
            'Or provide a full SPARQL endpoint URL',
            'Example: --endpoint uniprot'
        ])
    
    # Tool-specific suggestions
    tool_suggestions = get_tool_specific_suggestions(tool_name, error_msg, input_data)
    suggestions.extend(tool_suggestions)
    
    return suggestions[:5]  # Limit to 5 most relevant suggestions


def get_tool_specific_suggestions(tool_name: str, error_msg: str, input_data: Dict[str, Any]) -> List[str]:
    """Get tool-specific error suggestions."""
    suggestions = []
    
    if tool_name == 'rdf_get':
        if 'format' in error_msg:
            suggestions.append('Valid formats: json-ld, turtle, rdf-xml, n3, n-triples')
        if input_data.get('url', '').endswith('.ttl'):
            suggestions.append('For .ttl files, try --format turtle')
            
    elif tool_name == 'rdf_cache':
        if 'graph' in error_msg:
            suggestions.append('Use --graph with a cached vocabulary name')
            suggestions.append('Example: rdf_cache foaf_vocab --graph')
        if 'metadata' in error_msg:
            suggestions.append('Metadata must be valid JSON with semantic_type field')
            
    elif tool_name in ['cl_search', 'cl_select']:
        if 'query' in error_msg:
            suggestions.append('Provide a non-empty search query or SPARQL statement')
        if 'endpoint' in error_msg:
            suggestions.append('Try a specific endpoint: --endpoint uniprot')
            
    return suggestions


def generate_corrected_examples(error: Exception, tool_name: str) -> List[str]:
    """Generate corrected usage examples for common errors."""
    error_msg = str(error).lower()
    examples = []
    
    if tool_name == 'rdf_get':
        if 'url' in error_msg:
            examples.extend([
                'rdf_get https://sparql.uniprot.org/sparql --cache-as uniprot',
                'rdf_get http://xmlns.com/foaf/0.1/ --format turtle'
            ])
        if 'cache' in error_msg:
            examples.extend([
                'rdf_get https://example.org/vocab --cache-as my_vocab',
                'rdf_get https://schema.org --cache-as schema_org'
            ])
            
    elif tool_name == 'rdf_cache':
        if 'json' in error_msg:
            examples.extend([
                'rdf_cache vocab --update-metadata \'{"semantic_type": "vocabulary"}\'',
                'rdf_cache foaf --update-metadata \'{"domains": ["social"], "confidence": 0.9}\''
            ])
        if 'graph' in error_msg:
            examples.extend([
                'rdf_cache foaf_vocab --graph',
                'rdf_cache uniprot_service --graph --force'
            ])
            
    elif tool_name == 'cl_select':
        if 'sparql' in error_msg:
            examples.extend([
                'cl_select "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"',
                'cl_select "SELECT ?protein WHERE { ?protein a up:Protein }" --endpoint uniprot'
            ])
            
    elif tool_name == 'cl_ask':
        if 'ask' in error_msg:
            examples.extend([
                'cl_ask "ASK { wd:Q7240673 wdt:P31 wd:Q8054 }"',
                'cl_ask "ASK { ?s a up:Protein }" --endpoint uniprot'
            ])
    
    return examples[:3]  # Limit to 3 most relevant examples


def get_tool_documentation_link(tool_name: str) -> str:
    """Get documentation link for the tool."""
    base_docs = "https://github.com/your-org/cogitarelink/blob/main/docs"
    
    tool_docs = {
        'rdf_get': f"{base_docs}/rdf_get.md",
        'rdf_cache': f"{base_docs}/rdf_cache.md", 
        'cl_search': f"{base_docs}/cl_search.md",
        'cl_select': f"{base_docs}/cl_select.md",
        'cl_describe': f"{base_docs}/cl_describe.md",
        'cl_ask': f"{base_docs}/cl_ask.md"
    }
    
    return tool_docs.get(tool_name, f"{base_docs}/tools.md")


def format_performance_warning(duration_ms: float, tool_name: str) -> Optional[str]:
    """Format performance warnings for slow operations."""
    if duration_ms > 5.0:
        return f"Input validation took {duration_ms:.1f}ms (slower than expected for {tool_name})"
    return None


def format_success_message(tool_name: str, validation_time_ms: float) -> Dict[str, Any]:
    """Format successful validation message."""
    return {
        'success': True,
        'tool': tool_name,
        'validation_time_ms': round(validation_time_ms, 2),
        'status': 'input_validated'
    }


# Common error patterns and their solutions
ERROR_PATTERN_SOLUTIONS = {
    'missing_url': {
        'pattern': r'field required.*url',
        'message': 'URL parameter is required',
        'solution': 'Provide a valid HTTP/HTTPS URL',
        'example': 'rdf_get https://sparql.uniprot.org/sparql'
    },
    'invalid_json': {
        'pattern': r'invalid.*json|json.*decode',
        'message': 'Invalid JSON format',
        'solution': 'Use proper JSON syntax with quoted strings',
        'example': '\'{"semantic_type": "vocabulary", "confidence": 0.9}\''
    },
    'empty_query': {
        'pattern': r'ensure this value has at least.*characters',
        'message': 'Query cannot be empty',
        'solution': 'Provide a search term or SPARQL query',
        'example': '"insulin" or "SELECT ?s WHERE { ?s a up:Protein }"'
    },
    'invalid_limit': {
        'pattern': r'ensure this value is (greater|less) than',
        'message': 'Limit value out of range',
        'solution': 'Use appropriate limit values for the tool',
        'example': '--limit 10 (1-100 for search, 1-1000 for SPARQL)'
    }
}


def match_error_pattern(error_msg: str) -> Optional[Dict[str, str]]:
    """Match error message to known patterns and return solution."""
    for pattern_name, pattern_info in ERROR_PATTERN_SOLUTIONS.items():
        if re.search(pattern_info['pattern'], error_msg, re.IGNORECASE):
            return pattern_info
    return None