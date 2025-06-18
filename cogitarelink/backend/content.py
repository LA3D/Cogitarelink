"""Content analysis helpers for Claude Code semantic classification.

Provides basic content metrics and structure analysis for Claude Code to reason about.
No hardcoded classification - Claude Code does the intelligent analysis.
"""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

from .cache import SemanticMetadata
from ..utils.logging import get_logger

log = get_logger("content_analyzer")


class ContentAnalyzer:
    """Basic content analysis helpers for Claude Code reasoning."""
    
    def analyze_content_structure(self, data: Dict[str, Any], url: str = "") -> Dict[str, Any]:
        """Provide basic content analysis for Claude Code to reason about."""
        
        log.debug(f"Analyzing content structure from {url}")
        
        # Basic structural metrics (no interpretation)
        format_type = self._determine_format(data)
        vocabulary_size = self._calculate_vocabulary_size(data)
        
        # Raw content counts (facts, not classifications)
        content_metrics = self._extract_content_metrics(data)
        
        # Structural patterns (observations, not conclusions)
        structural_patterns = self._detect_structural_patterns(data)
        
        # Dependencies and references (factual extraction)
        references = self._extract_references(data)
        
        return {
            'url': url,
            'format': format_type,
            'size_metrics': {
                'vocabulary_size': vocabulary_size,
                'triples_count': content_metrics.get('triples', 0),
                'classes_count': content_metrics.get('classes', 0),
                'properties_count': content_metrics.get('properties', 0),
                'namespaces_count': content_metrics.get('namespaces', 0)
            },
            'structural_indicators': structural_patterns,
            'references': references,
            'raw_content_sample': self._extract_content_sample(data),
            'analysis_timestamp': time.time()
        }
    
    def _determine_format(self, data: Dict[str, Any]) -> str:
        """Determine RDF format from data structure."""
        if data.get('format') == 'json-ld':
            return 'json-ld'
        elif data.get('serialization'):
            return data['serialization']
        elif '@context' in data.get('raw', {}):
            return 'json-ld'
        else:
            return 'unknown'
    
    def _calculate_vocabulary_size(self, data: Dict[str, Any]) -> int:
        """Calculate vocabulary size from various metrics."""
        size_indicators = [
            data.get('triples', 0),
            len(data.get('expanded', [])),
            len(data.get('enhanced', {}).get('classes', {})),
            len(data.get('enhanced', {}).get('properties', {}))
        ]
        return max(size_indicators)
    
    def _extract_content_metrics(self, data: Dict[str, Any]) -> Dict[str, int]:
        """Extract basic content counts without interpretation."""
        enhanced = data.get('enhanced', {})
        
        return {
            'classes': len(enhanced.get('classes', {})),
            'properties': len(enhanced.get('properties', {})),
            'namespaces': len(enhanced.get('namespaces', {})),
            'triples': data.get('triples', 0),
            'contexts': 1 if '@context' in data.get('raw', {}) else 0,
            'expanded_items': len(data.get('expanded', []))
        }
    
    def _detect_structural_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect structural patterns without classification."""
        raw_data = data.get('raw', {})
        enhanced = data.get('enhanced', {})
        
        patterns = {
            'has_context': '@context' in raw_data,
            'has_type_declarations': '@type' in raw_data,
            'has_class_definitions': len(enhanced.get('classes', {})) > 0,
            'has_property_definitions': len(enhanced.get('properties', {})) > 0,
            'has_semantic_relationships': bool(enhanced.get('semantic_index', {})),
            'has_query_templates': len(enhanced.get('query_templates', [])) > 0,
            'context_mapping_ratio': 0.0,
            'namespace_diversity': len(enhanced.get('namespaces', {}))
        }
        
        # Calculate context mapping ratio
        if patterns['has_context']:
            context = raw_data.get('@context', {})
            if isinstance(context, dict):
                total_mappings = len(context)
                simple_mappings = sum(1 for v in context.values() 
                                    if isinstance(v, str) and v.startswith('http'))
                patterns['context_mapping_ratio'] = simple_mappings / total_mappings if total_mappings > 0 else 0.0
        
        return patterns
    
    def _extract_references(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract references to other vocabularies and standards."""
        raw_data = data.get('raw', {})
        references = {
            'based_on': [],
            'namespaces': [],
            'dependencies': []
        }
        
        # Extract isBasedOn relationships
        if 'isBasedOn' in raw_data:
            based_on = raw_data['isBasedOn']
            if isinstance(based_on, list):
                for item in based_on:
                    if isinstance(item, dict) and '@id' in item:
                        references['based_on'].append(item['@id'])
        
        # Extract namespace references
        enhanced = data.get('enhanced', {})
        namespaces = enhanced.get('namespaces', {})
        for prefix, uri in namespaces.items():
            references['namespaces'].append(f"{prefix}: {uri}")
        
        # Extract context dependencies
        context = raw_data.get('@context', {})
        if isinstance(context, dict):
            for term, uri in context.items():
                if isinstance(uri, str) and uri.startswith('http'):
                    # Common vocabulary detection
                    if 'schema.org' in uri:
                        references['dependencies'].append('schema.org')
                    elif 'w3.org' in uri and 'prov' in uri:
                        references['dependencies'].append('prov-o')
                    elif 'xmlns.com/foaf' in uri:
                        references['dependencies'].append('foaf')
        
        # Remove duplicates
        for key in references:
            references[key] = list(set(references[key]))
        
        return references
    
    def _extract_content_sample(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sample content for Claude Code to examine."""
        enhanced = data.get('enhanced', {})
        sample = {}
        
        # Sample classes
        classes = enhanced.get('classes', {})
        if classes:
            sample['sample_classes'] = dict(list(classes.items())[:3])
        
        # Sample properties  
        properties = enhanced.get('properties', {})
        if properties:
            sample['sample_properties'] = dict(list(properties.items())[:3])
        
        # Sample context mappings
        raw_data = data.get('raw', {})
        context = raw_data.get('@context', {})
        if isinstance(context, dict):
            sample['sample_context_mappings'] = dict(list(context.items())[:5])
        
        return sample


# Global content analyzer instance
content_analyzer = ContentAnalyzer()