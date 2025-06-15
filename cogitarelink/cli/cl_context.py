#!/usr/bin/env python3
"""
cl_context: Semantic memory management for CogitareLink

Provides context compression, research thread isolation, and semantic memory
management using JSON-LD 1.1 containers for Claude Code integration.
"""

from __future__ import annotations

import json
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import click

from ..core.debug import get_logger

log = get_logger("cl_context")


@click.command()
@click.option('--save', 'save_name', help='Save current context with name')
@click.option('--load', 'load_name', help='Load saved context by name')
@click.option('--compress', is_flag=True, help='Compress context for token efficiency')
@click.option('--expand', is_flag=True, help='Expand compressed context to full detail')
@click.option('--list', 'list_contexts', is_flag=True, help='List all saved contexts')
@click.option('--thread', help='Research thread identifier for isolation')
@click.option('--merge', multiple=True, help='Merge multiple contexts')
@click.option('--delete', 'delete_name', help='Delete saved context')
@click.argument('context_data', required=False)
def context(save_name: str, load_name: str, compress: bool, expand: bool, 
           list_contexts: bool, thread: str, merge: List[str], delete_name: str,
           context_data: str):
    """
    Semantic memory management for research contexts.
    
    Examples:
        cl_context --list                                    # List all contexts
        cl_discover insulin | cl_context --save insulin_research  # Save discovery results
        cl_context --load insulin_research                   # Load context
        cl_context --load insulin_research --compress        # Load and compress
        cl_context --thread protein_study --save current     # Thread isolation
        cl_context --merge ctx1 ctx2 --save combined        # Merge contexts
    """
    
    try:
        context_manager = ContextManager()
        
        if list_contexts:
            _list_all_contexts(context_manager)
            return
            
        if delete_name:
            _delete_context(context_manager, delete_name)
            return
            
        if load_name:
            _load_context(context_manager, load_name, compress, expand, thread)
            return
            
        if merge:
            _merge_contexts(context_manager, list(merge), save_name, thread)
            return
            
        # Handle input data (from stdin or argument)
        if context_data:
            input_data = json.loads(context_data)
        else:
            # Read from stdin
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                input_data = json.loads(stdin_data)
            else:
                _show_help()
                return
        
        # Process the context data
        if save_name:
            _save_context(context_manager, input_data, save_name, thread)
        elif compress:
            _compress_context(input_data, thread)
        elif expand:
            _expand_context(input_data, thread)
        else:
            _process_context(input_data, thread)
            
    except Exception as e:
        _error_response(str(e))


class ContextManager:
    """Manages semantic memory contexts with JSON-LD containers"""
    
    def __init__(self):
        self.context_dir = Path.home() / ".cogitarelink" / "contexts"
        self.context_dir.mkdir(parents=True, exist_ok=True)
        
    def save_context(self, data: Dict[str, Any], name: str, thread: Optional[str] = None) -> Dict[str, Any]:
        """Save context with semantic memory structure"""
        
        # Generate context metadata
        context_id = self._generate_context_id(name, thread)
        timestamp = datetime.now().isoformat()
        
        # Build semantic memory structure with containers
        context_structure = {
            '@context': {
                '@version': 1.1,
                'contexts': {'@container': ['@graph', '@index']},  # Thread isolation
                'entities': {'@container': '@id'},                 # Direct entity access
                'by_type': {'@container': '@type'},               # Type organization
                'by_thread': {'@container': '@index'},            # Thread isolation
                'temporal': {'@container': '@index'}              # Time-based access
            },
            'id': context_id,
            'name': name,
            'thread': thread,
            'created': timestamp,
            'data': data,
            'memory': self._extract_semantic_memory(data),
            'meta': {
                'size_bytes': len(json.dumps(data)),
                'entity_count': self._count_entities(data),
                'compression_ratio': 1.0
            }
        }
        
        # Save to disk
        context_file = self.context_dir / f"{context_id}.json"
        with open(context_file, 'w') as f:
            json.dump(context_structure, f, indent=2)
            
        return context_structure
    
    def load_context(self, name: str, thread: Optional[str] = None) -> Dict[str, Any]:
        """Load context by name/thread"""
        context_id = self._generate_context_id(name, thread)
        context_file = self.context_dir / f"{context_id}.json"
        
        if not context_file.exists():
            raise FileNotFoundError(f"Context not found: {name}")
            
        with open(context_file, 'r') as f:
            return json.load(f)
    
    def list_contexts(self) -> List[Dict[str, Any]]:
        """List all saved contexts"""
        contexts = []
        
        for context_file in self.context_dir.glob("*.json"):
            try:
                with open(context_file, 'r') as f:
                    context = json.load(f)
                    contexts.append({
                        'id': context.get('id'),
                        'name': context.get('name'),
                        'thread': context.get('thread'),
                        'created': context.get('created'),
                        'entity_count': context.get('meta', {}).get('entity_count', 0),
                        'size_kb': round(context.get('meta', {}).get('size_bytes', 0) / 1024, 1)
                    })
            except Exception as e:
                log.warning(f"Failed to read context {context_file}: {e}")
                
        return sorted(contexts, key=lambda x: x['created'], reverse=True)
    
    def delete_context(self, name: str, thread: Optional[str] = None) -> bool:
        """Delete saved context"""
        context_id = self._generate_context_id(name, thread)
        context_file = self.context_dir / f"{context_id}.json"
        
        if context_file.exists():
            context_file.unlink()
            return True
        return False
    
    def merge_contexts(self, context_names: List[str], thread: Optional[str] = None) -> Dict[str, Any]:
        """Merge multiple contexts into one"""
        merged_data = []
        merged_memory = {
            'entities': {},
            'by_type': {},
            'by_domain': {},
            'by_thread': {}
        }
        
        for name in context_names:
            try:
                # Try loading with thread first, then without thread
                try:
                    context = self.load_context(name, thread)
                except FileNotFoundError:
                    context = self.load_context(name, None)
                    
                if context.get('data'):
                    if isinstance(context['data'], list):
                        merged_data.extend(context['data'])
                    else:
                        merged_data.append(context['data'])
                        
                # Merge semantic memory
                if context.get('memory'):
                    self._merge_memory(merged_memory, context['memory'])
                    
            except Exception as e:
                log.warning(f"Failed to load context {name}: {e}")
        
        # Track which contexts were actually loaded
        loaded_contexts = []
        for name in context_names:
            try:
                # Try loading with thread first, then without thread
                try:
                    self.load_context(name, thread)
                    loaded_contexts.append(name)
                except FileNotFoundError:
                    self.load_context(name, None)
                    loaded_contexts.append(name)
            except Exception as e:
                pass  # Already logged above
                
        return {
            '@context': {
                '@version': 1.1,
                'data': {'@container': '@set'},
                'entities': {'@container': '@id'},
                'by_type': {'@container': '@type'},
                'by_thread': {'@container': '@index'}
            },
            'status': 'success',
            'data': merged_data,
            'count': len(merged_data),
            'memory': merged_memory,
            'meta': {
                'merged_contexts': loaded_contexts,
                'requested_contexts': context_names,
                'merge_timestamp': datetime.now().isoformat()
            }
        }
    
    def _generate_context_id(self, name: str, thread: Optional[str] = None) -> str:
        """Generate unique context identifier"""
        base = f"{name}"
        if thread:
            base = f"{thread}_{name}"
        return hashlib.md5(base.encode()).hexdigest()[:12]
    
    def _extract_semantic_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic memory structure from data"""
        memory = {
            'entities': {},
            'by_type': {},
            'by_domain': {},
            'relationships': []
        }
        
        # Extract from existing memory if present
        if isinstance(data, dict) and 'memory' in data:
            existing_memory = data['memory']
            if isinstance(existing_memory, dict):
                memory.update(existing_memory)
        
        # Extract from data array
        if isinstance(data, dict) and 'data' in data:
            data_items = data['data']
            if isinstance(data_items, list):
                for item in data_items:
                    if isinstance(item, dict) and 'id' in item:
                        entity_id = item['id']
                        memory['entities'][entity_id] = item
                        
                        # Group by type
                        entity_type = item.get('type', 'unknown')
                        if entity_type not in memory['by_type']:
                            memory['by_type'][entity_type] = []
                        memory['by_type'][entity_type].append(item)
                        
                        # Group by domain
                        domains = item.get('domains', [])
                        for domain in domains:
                            if domain not in memory['by_domain']:
                                memory['by_domain'][domain] = []
                            memory['by_domain'][domain].append(item)
        
        return memory
    
    def _count_entities(self, data: Dict[str, Any]) -> int:
        """Count entities in data"""
        if isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list):
                return len(data['data'])
            elif 'memory' in data and isinstance(data['memory'], dict):
                entities = data['memory'].get('entities', {})
                return len(entities) if isinstance(entities, dict) else 0
        return 0
    
    def _merge_memory(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Merge semantic memory structures"""
        if not isinstance(source, dict):
            return
            
        # Merge entities
        if 'entities' in source and isinstance(source['entities'], dict):
            target['entities'].update(source['entities'])
        
        # Merge by_type
        if 'by_type' in source and isinstance(source['by_type'], dict):
            for type_name, items in source['by_type'].items():
                if type_name not in target['by_type']:
                    target['by_type'][type_name] = []
                if isinstance(items, list):
                    target['by_type'][type_name].extend(items)
        
        # Merge by_domain  
        if 'by_domain' in source and isinstance(source['by_domain'], dict):
            for domain_name, items in source['by_domain'].items():
                if domain_name not in target['by_domain']:
                    target['by_domain'][domain_name] = []
                if isinstance(items, list):
                    target['by_domain'][domain_name].extend(items)


def _list_all_contexts(context_manager: ContextManager):
    """List all saved contexts"""
    contexts = context_manager.list_contexts()
    
    response = {
        '@context': {
            '@version': 1.1,
            'data': {'@container': '@set'},
            'by_thread': {'@container': '@index'}
        },
        'status': 'success',
        'data': contexts,
        'count': len(contexts),
        'meta': {
            'total_contexts': len(contexts),
            'context_directory': str(context_manager.context_dir)
        }
    }
    
    click.echo(json.dumps(response, indent=2))


def _save_context(context_manager: ContextManager, data: Dict[str, Any], name: str, thread: Optional[str]):
    """Save context to semantic memory"""
    saved_context = context_manager.save_context(data, name, thread)
    
    response = {
        '@context': {
            '@version': 1.1,
            'data': {'@container': '@set'}
        },
        'status': 'success',
        'data': [{
            'context_id': saved_context['id'],
            'name': saved_context['name'],
            'thread': saved_context.get('thread'),
            'entity_count': saved_context['meta']['entity_count'],
            'size_kb': round(saved_context['meta']['size_bytes'] / 1024, 1)
        }],
        'count': 1,
        'meta': {
            'operation': 'save_context',
            'saved_name': name,
            'thread': thread
        },
        'next': [
            f'cl_context --load {name}',
            f'cl_context --load {name} --compress'
        ]
    }
    
    click.echo(json.dumps(response, indent=2))


def _load_context(context_manager: ContextManager, name: str, compress: bool, expand: bool, thread: Optional[str]):
    """Load and optionally process context"""
    try:
        context = context_manager.load_context(name, thread)
        
        # Apply processing
        if compress:
            processed_data = _apply_compression(context['data'])
        elif expand:
            processed_data = _apply_expansion(context['data'])
        else:
            processed_data = context['data']
        
        response = {
            '@context': context.get('@context', {
                '@version': 1.1,
                'data': {'@container': '@set'},
                'entities': {'@container': '@id'},
                'by_type': {'@container': '@type'}
            }),
            'status': 'success',
            'data': processed_data if isinstance(processed_data, list) else [processed_data],
            'count': len(processed_data) if isinstance(processed_data, list) else 1,
            'memory': context.get('memory', {}),
            'meta': {
                'operation': 'load_context',
                'context_name': name,
                'thread': thread,
                'compressed': compress,
                'expanded': expand,
                'original_size_kb': round(context.get('meta', {}).get('size_bytes', 0) / 1024, 1)
            }
        }
        
        click.echo(json.dumps(response, indent=2))
        
    except FileNotFoundError:
        _error_response(f"Context not found: {name}")


def _delete_context(context_manager: ContextManager, name: str):
    """Delete a saved context"""
    success = context_manager.delete_context(name)
    
    if success:
        response = {
            'status': 'success',
            'data': [{
                'deleted_context': name,
                'operation': 'delete_context'
            }],
            'count': 1,
            'meta': {
                'operation': 'delete_context'
            }
        }
    else:
        response = {
            'status': 'error',
            'data': [],
            'count': 0,
            'error': {
                'message': f'Context not found: {name}',
                'code': 'CONTEXT_NOT_FOUND'
            }
        }
    
    click.echo(json.dumps(response, indent=2))


def _merge_contexts(context_manager: ContextManager, context_names: List[str], save_name: Optional[str], thread: Optional[str]):
    """Merge multiple contexts"""
    merged = context_manager.merge_contexts(context_names, thread)
    
    if save_name:
        context_manager.save_context(merged, save_name, thread)
        merged['meta']['saved_as'] = save_name
    
    click.echo(json.dumps(merged, indent=2))


def _compress_context(data: Dict[str, Any], thread: Optional[str]):
    """Compress context for token efficiency"""
    compressed = _apply_compression(data)
    
    response = {
        '@context': {
            '@version': 1.1,
            'data': {'@container': '@set'}
        },
        'status': 'success',
        'data': compressed if isinstance(compressed, list) else [compressed],
        'count': len(compressed) if isinstance(compressed, list) else 1,
        'meta': {
            'operation': 'compress_context',
            'compression_applied': True,
            'thread': thread
        }
    }
    
    click.echo(json.dumps(response, indent=2))


def _expand_context(data: Dict[str, Any], thread: Optional[str]):
    """Expand compressed context to full detail"""
    expanded = _apply_expansion(data)
    
    response = {
        '@context': {
            '@version': 1.1,
            'data': {'@container': '@set'}
        },
        'status': 'success',
        'data': expanded if isinstance(expanded, list) else [expanded],
        'count': len(expanded) if isinstance(expanded, list) else 1,
        'meta': {
            'operation': 'expand_context',
            'expansion_applied': True,
            'thread': thread
        }
    }
    
    click.echo(json.dumps(response, indent=2))


def _process_context(data: Dict[str, Any], thread: Optional[str]):
    """Process context data without saving"""
    # Extract semantic memory if not present
    if 'memory' not in data:
        context_manager = ContextManager()
        data['memory'] = context_manager._extract_semantic_memory(data)
    
    response = {
        '@context': {
            '@version': 1.1,
            'data': {'@container': '@set'},
            'entities': {'@container': '@id'},
            'by_type': {'@container': '@type'}
        },
        'status': 'success',
        'data': data.get('data', [data]),
        'count': len(data.get('data', [data])),
        'memory': data.get('memory', {}),
        'meta': {
            'operation': 'process_context',
            'thread': thread
        }
    }
    
    click.echo(json.dumps(response, indent=2))


def _apply_compression(data: Any) -> Any:
    """Apply compression for token efficiency"""
    if isinstance(data, dict):
        # Remove verbose fields for compression
        compressed = {}
        essential_fields = ['id', 'name', 'type', 'domains', 'confidence']
        
        for key, value in data.items():
            if key in essential_fields:
                compressed[key] = value
            elif key == 'data' and isinstance(value, list):
                compressed['data'] = [_apply_compression(item) for item in value]
            elif key == 'memory':
                # Compress memory by keeping only essential entities
                if isinstance(value, dict) and 'entities' in value:
                    compressed['memory'] = {
                        'entities': {k: _apply_compression(v) for k, v in list(value['entities'].items())[:10]}
                    }
        
        return compressed
    elif isinstance(data, list):
        return [_apply_compression(item) for item in data[:10]]  # Limit to 10 items
    else:
        return data


def _apply_expansion(data: Any) -> Any:
    """Apply expansion to restore full detail"""
    # For now, expansion just returns the data as-is
    # In a real implementation, this might fetch additional details
    return data


def _show_help():
    """Show help when no action specified"""
    response = {
        'status': 'info',
        'data': [{
            'message': 'cl_context: Semantic memory management',
            'usage': 'cl_context [--save NAME] [--load NAME] [options]',
            'examples': [
                'cl_context --list',
                'cl_discover insulin | cl_context --save insulin_research',
                'cl_context --load insulin_research --compress',
                'cl_context --merge ctx1 ctx2 --save combined'
            ]
        }],
        'count': 1,
        'next': [
            'cl_context --list',
            'cl_discover example | cl_context --save test'
        ]
    }
    
    click.echo(json.dumps(response, indent=2))


def _error_response(message: str):
    """Generate error response"""
    response = {
        'status': 'error',
        'data': [],
        'count': 0,
        'error': {
            'message': message,
            'code': 'CONTEXT_ERROR'
        },
        'next': [
            'cl_context --help',
            'cl_context --list'
        ]
    }
    
    click.echo(json.dumps(response, indent=2))
    sys.exit(1)


if __name__ == "__main__":
    context()