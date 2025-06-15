#!/usr/bin/env python3
"""
Discovery Orchestrator - Claude Code Style Async Generator Pattern

Orchestrates multiple discovery tools (wikidata, sparql, resolve) following
Claude Code's AgentTool synthesis pattern for intelligent tool composition.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from ..core.debug import get_logger
from ..core.entity import Entity

log = get_logger("discovery_orchestrator")

@dataclass
class DiscoveryProgress:
    """Progress event from discovery operation"""
    type: str  # 'progress', 'result', 'complete', 'error'
    tool_name: str
    timestamp: datetime
    data: Dict[str, Any]
    elapsed_ms: int

@dataclass  
class DiscoveryResult:
    """Final discovery result with synthesis"""
    query: str
    entities: List[Entity]
    sources: List[str]
    metadata: Dict[str, Any]
    synthesis: str
    total_time_ms: int

class DiscoveryOrchestrator:
    """
    Orchestrates multiple discovery tools following Claude Code patterns:
    - Async generators for streaming progress
    - Tool synthesis for coherent results  
    - Memory integration for semantic caching
    """
    
    def __init__(self):
        self.start_time = 0
        self.completed_tools: Set[str] = set()
        self.tool_results: Dict[str, Any] = {}
        self.discovered_entities: List[Entity] = []
        
    async def discover(
        self, 
        query: str, 
        domains: List[str] = None,
        container_mode: bool = False
    ) -> AsyncGenerator[DiscoveryProgress, None]:
        """
        Main discovery orchestration using async generator pattern.
        
        Follows Claude Code's tool execution pipeline:
        1. Plan tool sequence based on query
        2. Execute tools with progress streaming  
        3. Synthesize results intelligently
        4. Format for container/memory integration
        """
        self.start_time = time.time() * 1000
        
        try:
            log.info(f"Starting discovery orchestration for: {query}")
            
            # Phase 1: Query Analysis & Tool Planning
            yield DiscoveryProgress(
                type='progress',
                tool_name='orchestrator',
                timestamp=datetime.now(),
                data={'status': 'Analyzing query and planning tool sequence...'},
                elapsed_ms=self._elapsed_ms()
            )
            
            tool_plan = self._plan_tool_sequence(query, domains)
            
            # Phase 2: Parallel Tool Execution with Progress Streaming
            async for progress in self._execute_tool_sequence(tool_plan, query):
                yield progress
                
            # Phase 3: Result Synthesis (following AgentTool pattern)
            yield DiscoveryProgress(
                type='progress', 
                tool_name='orchestrator',
                timestamp=datetime.now(),
                data={'status': 'Synthesizing results from multiple tools...'},
                elapsed_ms=self._elapsed_ms()
            )
            
            synthesis_result = await self._synthesize_results(query)
            
            # Phase 4: Final Result with Container Integration
            final_result = self._create_final_result(query, synthesis_result, container_mode)
            
            yield DiscoveryProgress(
                type='complete',
                tool_name='orchestrator', 
                timestamp=datetime.now(),
                data=final_result,
                elapsed_ms=self._elapsed_ms()
            )
            
        except Exception as e:
            log.error(f"Discovery orchestration failed: {e}")
            yield DiscoveryProgress(
                type='error',
                tool_name='orchestrator',
                timestamp=datetime.now(), 
                data={'error': str(e), 'suggestions': self._generate_error_suggestions(e)},
                elapsed_ms=self._elapsed_ms()
            )
    
    def _plan_tool_sequence(self, query: str, domains: List[str] = None) -> List[Dict[str, Any]]:
        """
        Plan tool execution sequence based on query analysis.
        
        Following Claude Code's dynamic context assembly pattern for intelligent 
        tool selection and ordering.
        """
        tools = []
        
        # Always start with Wikidata for entity resolution
        tools.append({
            'name': 'wikidata',
            'priority': 1,
            'params': {'query': query, 'limit': 10},
            'purpose': 'Entity identification and basic properties'
        })
        
        # Identifier resolution if query looks like an external ID
        if self._looks_like_external_id(query):
            tools.append({
                'name': 'resolve',
                'priority': 2, 
                'params': {'identifier': query},
                'purpose': 'External identifier resolution'
            })
        
        # Domain-specific SPARQL if domains specified
        if domains:
            for domain in domains:
                endpoint = self._map_domain_to_endpoint(domain)
                if endpoint:
                    tools.append({
                        'name': 'sparql',
                        'priority': 3,
                        'params': {
                            'endpoint': endpoint,
                            'query': self._generate_domain_query(query, domain)
                        },
                        'purpose': f'Domain-specific search in {domain}'
                    })
        
        return sorted(tools, key=lambda x: x['priority'])
    
    async def _execute_tool_sequence(
        self, 
        tool_plan: List[Dict[str, Any]], 
        query: str
    ) -> AsyncGenerator[DiscoveryProgress, None]:
        """
        Execute tools with Claude Code's parallel/sequential execution strategy.
        
        Read-only tools (wikidata, resolve) run in parallel.
        Complex tools (sparql) run sequentially.
        """
        
        # Categorize tools for execution strategy
        parallel_tools = [t for t in tool_plan if t['name'] in ['wikidata', 'resolve']]
        sequential_tools = [t for t in tool_plan if t['name'] not in ['wikidata', 'resolve']]
        
        # Execute parallel tools first
        if parallel_tools:
            async for progress in self._execute_parallel_tools(parallel_tools):
                yield progress
        
        # Execute sequential tools
        for tool in sequential_tools:
            async for progress in self._execute_single_tool(tool):
                yield progress
    
    async def _execute_parallel_tools(
        self, 
        tools: List[Dict[str, Any]]
    ) -> AsyncGenerator[DiscoveryProgress, None]:
        """Execute multiple tools in parallel with progress aggregation"""
        
        # Create concurrent tasks
        tasks = []
        for tool in tools:
            task = asyncio.create_task(self._run_tool_async(tool))
            tasks.append((tool['name'], task))
        
        # Wait for completion with progress updates
        while tasks:
            # Check for completed tasks
            completed = []
            for tool_name, task in tasks:
                if task.done():
                    completed.append((tool_name, task))
            
            # Process completed tasks
            for tool_name, task in completed:
                try:
                    result = await task
                    self.tool_results[tool_name] = result
                    self.completed_tools.add(tool_name)
                    
                    yield DiscoveryProgress(
                        type='result',
                        tool_name=tool_name,
                        timestamp=datetime.now(),
                        data=result,
                        elapsed_ms=self._elapsed_ms()
                    )
                except Exception as e:
                    log.error(f"Tool {tool_name} failed: {e}")
                    yield DiscoveryProgress(
                        type='error', 
                        tool_name=tool_name,
                        timestamp=datetime.now(),
                        data={'error': str(e)},
                        elapsed_ms=self._elapsed_ms()
                    )
                
                tasks.remove((tool_name, task))
            
            if tasks:
                # Brief wait before checking again
                await asyncio.sleep(0.1)
    
    async def _execute_single_tool(
        self, 
        tool: Dict[str, Any]
    ) -> AsyncGenerator[DiscoveryProgress, None]:
        """Execute single tool with progress streaming"""
        
        tool_name = tool['name']
        
        yield DiscoveryProgress(
            type='progress',
            tool_name=tool_name,
            timestamp=datetime.now(),
            data={'status': f"Starting {tool['purpose']}..."},
            elapsed_ms=self._elapsed_ms()
        )
        
        try:
            result = await self._run_tool_async(tool)
            self.tool_results[tool_name] = result
            self.completed_tools.add(tool_name)
            
            yield DiscoveryProgress(
                type='result',
                tool_name=tool_name,
                timestamp=datetime.now(),
                data=result,
                elapsed_ms=self._elapsed_ms()
            )
            
        except Exception as e:
            log.error(f"Tool {tool_name} failed: {e}")
            yield DiscoveryProgress(
                type='error',
                tool_name=tool_name, 
                timestamp=datetime.now(),
                data={'error': str(e)},
                elapsed_ms=self._elapsed_ms()
            )
    
    async def _run_tool_async(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run individual tool asynchronously.
        
        This is where we'll call the actual CLI tools (wikidata, sparql, resolve)
        and parse their JSON responses.
        """
        tool_name = tool['name']
        params = tool['params']
        
        # Import and run the actual tools
        if tool_name == 'wikidata':
            return await self._run_wikidata_tool(params)
        elif tool_name == 'resolve':
            return await self._run_resolve_tool(params)  
        elif tool_name == 'sparql':
            return await self._run_sparql_tool(params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _run_wikidata_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run cl_wikidata search command"""
        from ..cli.cl_wikidata import _search_async
        
        try:
            # Capture stdout to get the JSON response
            import io
            import sys
            from contextlib import redirect_stdout
            
            # Temporarily redirect stdout to capture the response
            stdout_capture = io.StringIO()
            
            # Use a custom click context to suppress actual output during search
            with redirect_stdout(stdout_capture):
                # Call the async search function directly with container mode
                await _search_async(
                    query=params['query'],
                    language='en',
                    limit=params.get('limit', 10),
                    entity_type=None,
                    vocab=['wikidata'],
                    level='detailed',
                    container=True  # Request container format
                )
            
            # Parse the captured JSON output
            captured_output = stdout_capture.getvalue().strip()
            if captured_output:
                import json
                try:
                    result = json.loads(captured_output)
                    return {
                        'tool': 'wikidata',
                        'query': params['query'],
                        'results': result.get('data', []),
                        'container_data': result,  # Include full container response
                        'metadata': {
                            'source': 'wikidata',
                            'query_time_ms': result.get('meta', {}).get('execution_time_ms', 0),
                            'count': result.get('count', 0)
                        }
                    }
                except json.JSONDecodeError as e:
                    log.warning(f"Failed to parse wikidata output: {e}")
                    
        except Exception as e:
            log.warning(f"Failed to run wikidata tool: {e}")
        
        # Fallback to basic search result
        return {
            'tool': 'wikidata',
            'query': params['query'],
            'results': [],
            'metadata': {
                'source': 'wikidata',
                'query_time_ms': 100,
                'error': 'Failed to execute wikidata search'
            }
        }
    
    async def _run_resolve_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run cl_resolve command"""
        # For now, return mock data until we implement the container integration
        return {
            'tool': 'resolve',
            'identifier': params['identifier'],
            'resolved_uris': [],
            'metadata': {
                'source': 'resolve',
                'resolution_time_ms': 50
            }
        }
    
    async def _run_sparql_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run cl_sparql command"""
        # For now, return mock data until we implement the container integration
        return {
            'tool': 'sparql',
            'endpoint': params['endpoint'],
            'query': params['query'],
            'results': [],
            'metadata': {
                'source': 'sparql',
                'query_time_ms': 200
            }
        }
    
    async def _synthesize_results(self, query: str) -> Dict[str, Any]:
        """
        Synthesize results from multiple tools following Claude Code's AgentTool pattern.
        
        Combines findings intelligently rather than simple concatenation.
        """
        
        # Extract entities from all tool results
        all_entities = []
        all_sources = []
        
        for tool_name, result in self.tool_results.items():
            all_sources.append(tool_name)
            
            # Extract entities based on tool type
            if tool_name == 'wikidata' and 'results' in result:
                for item in result['results']:
                    entity = self._convert_wikidata_to_entity(item)
                    if entity:
                        all_entities.append(entity)
            
            elif tool_name == 'resolve' and 'resolved_uris' in result:
                for uri in result['resolved_uris']:
                    entity = self._convert_uri_to_entity(uri)
                    if entity:
                        all_entities.append(entity)
        
        # Generate synthesis summary
        synthesis = self._generate_synthesis_summary(query, all_entities, all_sources)
        
        return {
            'entities': all_entities,
            'sources': all_sources,
            'synthesis': synthesis,
            'confidence': self._calculate_confidence(all_entities),
            'coverage': self._calculate_coverage(query, all_entities)
        }
    
    def _convert_wikidata_to_entity(self, item: Dict[str, Any]) -> Optional[Entity]:
        """Convert Wikidata search result to Entity"""
        try:
            content = {
                'name': item.get('label', ''),
                'description': item.get('description', ''),
                'wikidata_id': item.get('id', ''),
                'source': 'wikidata',
                '@type': 'Entity'
            }
            return Entity(vocab=['wikidata'], content=content)
        except Exception as e:
            log.warning(f"Failed to convert Wikidata item to entity: {e}")
            return None
    
    def _convert_uri_to_entity(self, uri: str) -> Optional[Entity]:
        """Convert resolved URI to Entity"""
        try:
            content = {
                'uri': uri,
                'source': 'resolve',
                '@type': 'Entity'
            }
            return Entity(vocab=['resolve'], content=content)
        except Exception as e:
            log.warning(f"Failed to convert URI to entity: {e}")
            return None
    
    def _generate_synthesis_summary(
        self, 
        query: str, 
        entities: List[Entity], 
        sources: List[str]
    ) -> str:
        """Generate intelligent synthesis of discovery results"""
        
        if not entities:
            return f"No entities found for query '{query}' across {len(sources)} sources."
        
        entity_count = len(entities)
        source_list = ', '.join(sources)
        
        # Find most relevant entity (first one for now)
        primary_entity = entities[0] if entities else None
        
        if primary_entity:
            name = primary_entity.content.get('name', 'Unknown')
            desc = primary_entity.content.get('description', '')
            
            synthesis = f"Discovery found {entity_count} entities for '{query}' across {source_list}. "
            synthesis += f"Primary match: {name}"
            if desc:
                synthesis += f" - {desc}"
        else:
            synthesis = f"Discovery completed for '{query}' using {source_list}."
        
        return synthesis
    
    def _calculate_confidence(self, entities: List[Entity]) -> float:
        """Calculate confidence score based on entity quality"""
        if not entities:
            return 0.0
        
        # Simple confidence based on number of entities and completeness
        base_confidence = min(len(entities) * 0.2, 1.0)
        
        # Boost for entities with descriptions
        desc_bonus = sum(1 for e in entities if e.content.get('description')) * 0.1
        
        return min(base_confidence + desc_bonus, 1.0)
    
    def _calculate_coverage(self, query: str, entities: List[Entity]) -> float:
        """Calculate how well entities cover the query"""
        if not entities:
            return 0.0
        
        # Simple coverage based on name matches
        query_lower = query.lower()
        matches = 0
        
        for entity in entities:
            name = entity.content.get('name', '').lower()
            if query_lower in name or name in query_lower:
                matches += 1
        
        return min(matches / len(entities), 1.0) if entities else 0.0
    
    def _create_final_result(
        self, 
        query: str, 
        synthesis: Dict[str, Any], 
        container_mode: bool
    ) -> Dict[str, Any]:
        """Create final result in appropriate format"""
        
        result = {
            'query': query,
            'entities': [entity.to_dict() for entity in synthesis['entities']],
            'sources': synthesis['sources'],
            'metadata': {
                'total_time_ms': self._elapsed_ms(),
                'tools_used': list(self.completed_tools),
                'confidence': synthesis['confidence'], 
                'coverage': synthesis['coverage']
            },
            'synthesis': synthesis['synthesis']
        }
        
        if container_mode:
            # Wrap in JSON-LD container for semantic memory integration
            result = self._wrap_in_container(result)
        
        return result
    
    def _wrap_in_container(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Wrap result in JSON-LD container for semantic memory"""
        return {
            '@context': {
                '@version': 1.1,
                '@vocab': 'https://cogitarelink.org/vocab/',
                'entities': {'@container': ['@set', '@id']},
                'sources': {'@container': '@set'}
            },
            '@type': 'DiscoveryResult',
            'timestamp': datetime.now().isoformat(),
            'data': result
        }
    
    # Helper methods
    
    def _elapsed_ms(self) -> int:
        """Calculate elapsed time in milliseconds"""
        return int((time.time() * 1000) - self.start_time)
    
    def _looks_like_external_id(self, query: str) -> bool:
        """Check if query looks like an external identifier"""
        # Simple heuristics for common ID patterns
        patterns = ['WP', 'P0', 'Q', 'CHEBI:', 'GO:', 'UniProt:']
        return any(query.startswith(p) for p in patterns)
    
    def _map_domain_to_endpoint(self, domain: str) -> Optional[str]:
        """Map domain to SPARQL endpoint"""
        domain_map = {
            'biology': 'uniprot',
            'pathways': 'wikipathways', 
            'chemicals': 'idsm',
            'proteins': 'uniprot'
        }
        return domain_map.get(domain.lower())
    
    def _generate_domain_query(self, query: str, domain: str) -> str:
        """Generate domain-specific SPARQL query"""
        # Simple query generation - can be enhanced later
        return f'SELECT ?item ?itemLabel WHERE {{ ?item rdfs:label ?label . FILTER(CONTAINS(?label, "{query}")) }} LIMIT 10'
    
    def _generate_error_suggestions(self, error: Exception) -> List[str]:
        """Generate helpful error recovery suggestions"""
        suggestions = [
            "Check network connectivity",
            "Verify query format and syntax",
            "Try a simpler or more specific query"
        ]
        
        if "timeout" in str(error).lower():
            suggestions.append("Query may be too complex - try narrowing the scope")
        
        return suggestions