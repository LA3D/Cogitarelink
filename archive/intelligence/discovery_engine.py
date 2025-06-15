"""Self-configuring discovery engine based on wikidata-mcp patterns."""

from __future__ import annotations

import hashlib
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..core.debug import get_logger
from ..core.cache import InMemoryCache

log = get_logger("discovery")

class DiscoveryStrategy(str, Enum):
    """Discovery strategies ordered by preference."""
    SPARQL_ENDPOINT = "sparql_endpoint"
    WEB_URL = "web_url"
    REGISTRY_LOOKUP = "registry_lookup"
    IDENTIFIER_ONLY = "identifier_only"

@dataclass
class DiscoveryMetadata:
    """Rich metadata discovered about a resource."""
    resource_id: str
    resource_type: str
    domain_context: List[str]
    resolution_urls: List[str]
    validation_patterns: List[str]
    discovery_strategy: DiscoveryStrategy
    confidence_score: float
    reasoning_hints: List[str]
    
    def as_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "domain_context": self.domain_context,
            "resolution_urls": self.resolution_urls,
            "validation_patterns": self.validation_patterns,
            "discovery_strategy": self.discovery_strategy.value,
            "confidence_score": self.confidence_score,
            "reasoning_hints": self.reasoning_hints
        }

@dataclass
class DiscoveryResult:
    """Complete discovery result with agent guidance."""
    success: bool
    metadata: Optional[DiscoveryMetadata]
    suggestions: Dict[str, Any]
    context_id: Optional[str]
    error: Optional[Dict[str, Any]] = None
    
    def to_agent_response(self) -> Dict[str, Any]:
        """Generate agent-friendly structured response."""
        base = {
            "success": self.success,
            "data": self.metadata.as_dict() if self.metadata else {},
            "suggestions": self.suggestions
        }
        
        if self.context_id:
            base["context_id"] = self.context_id
        
        if self.error:
            base["error"] = self.error
            
        return base

class DiscoveryEngine:
    """Self-configuring discovery engine with agent intelligence patterns."""
    
    def __init__(self, cache_size: int = 512, cache_ttl: float = 3600):
        self.cache = InMemoryCache(maxsize=cache_size, ttl=cache_ttl)
        self.context_cache = InMemoryCache(maxsize=128, ttl=1800)
        
    def _create_context_id(self, context_data: Dict[str, Any]) -> str:
        """Create opaque context handle for stateless protocols."""
        context_str = str(sorted(context_data.items()))
        return f"ctx_{hashlib.sha256(context_str.encode()).hexdigest()[:16]}"
    
    async def _cache_context(self, context_data: Dict[str, Any]) -> str:
        """Cache context and return opaque handle."""
        context_id = self._create_context_id(context_data)
        self.context_cache.set(context_id, context_data)
        log.debug(f"Cached context {context_id}")
        return context_id
    
    async def _get_context(self, context_id: Optional[str]) -> Dict[str, Any]:
        """Retrieve context from opaque handle."""
        if not context_id:
            return {}
        
        context = self.context_cache.get(context_id)
        if context is None:
            log.warning(f"Context {context_id} not found, using empty context")
            return {}
        
        return context
    
    async def discover_resource(
        self, 
        resource_identifier: str,
        domain_hints: Optional[List[str]] = None,
        context_id: Optional[str] = None
    ) -> DiscoveryResult:
        """
        Discover metadata about a resource using multiple strategies.
        
        Based on wikidata-mcp's multi-strategy resolution with graceful degradation.
        """
        # Get existing context
        context = await self._get_context(context_id)
        
        # Create cache key
        cache_key = f"discover:{resource_identifier}:{hash(tuple(domain_hints or []))}"
        
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            log.debug(f"Cache hit for resource discovery: {resource_identifier}")
            return DiscoveryResult(
                success=True,
                metadata=cached,
                suggestions=self._generate_discovery_suggestions(cached, context),
                context_id=await self._cache_context({**context, "last_discovery": cached.as_dict()})
            )
        
        # Try discovery strategies in order of preference
        strategies = [
            (DiscoveryStrategy.SPARQL_ENDPOINT, self._discover_via_sparql),
            (DiscoveryStrategy.WEB_URL, self._discover_via_web),
            (DiscoveryStrategy.REGISTRY_LOOKUP, self._discover_via_registry),
            (DiscoveryStrategy.IDENTIFIER_ONLY, self._discover_minimal)
        ]
        
        for strategy, method in strategies:
            try:
                log.debug(f"Trying discovery strategy: {strategy}")
                metadata = await method(resource_identifier, domain_hints or [])
                
                if metadata:
                    # Cache successful discovery
                    self.cache.set(cache_key, metadata)
                    
                    # Generate agent guidance
                    suggestions = self._generate_discovery_suggestions(metadata, context)
                    
                    # Update context
                    new_context = {
                        **context,
                        "last_discovery": metadata.as_dict(),
                        "discovery_strategy": strategy.value,
                        "domain_context": metadata.domain_context
                    }
                    
                    return DiscoveryResult(
                        success=True,
                        metadata=metadata,
                        suggestions=suggestions,
                        context_id=await self._cache_context(new_context)
                    )
                    
            except Exception as e:
                log.warning(f"Discovery strategy {strategy.value} failed: {e}")
                continue
        
        # All strategies failed - return educational error
        error = self._create_educational_error(resource_identifier, domain_hints)
        return DiscoveryResult(
            success=False,
            metadata=None,
            suggestions={"recovery_actions": error["recovery_plan"]},
            context_id=context_id,
            error=error
        )
    
    async def _discover_via_sparql(self, resource_id: str, domain_hints: List[str]) -> Optional[DiscoveryMetadata]:
        """Discover via SPARQL endpoint (richest data)."""
        # Placeholder for SPARQL-based discovery
        # Would query endpoints to discover property metadata
        log.debug(f"SPARQL discovery for {resource_id} with domains {domain_hints}")
        
        # For now, return None to try next strategy
        return None
    
    async def _discover_via_web(self, resource_id: str, domain_hints: List[str]) -> Optional[DiscoveryMetadata]:
        """Discover via web URL resolution (universal fallback)."""
        # Placeholder for web-based discovery
        # Would try to resolve URLs and extract metadata
        log.debug(f"Web discovery for {resource_id}")
        
        return None
    
    async def _discover_via_registry(self, resource_id: str, domain_hints: List[str]) -> Optional[DiscoveryMetadata]:
        """Discover via local vocabulary registry."""
        from ..vocab.registry import registry
        
        try:
            # Try to resolve via vocabulary registry
            entry = registry.resolve(resource_id)
            
            return DiscoveryMetadata(
                resource_id=resource_id,
                resource_type="vocabulary",
                domain_context=list(entry.tags) + domain_hints,
                resolution_urls=[str(entry.uris.get("primary", ""))],
                validation_patterns=[],
                discovery_strategy=DiscoveryStrategy.REGISTRY_LOOKUP,
                confidence_score=0.8,
                reasoning_hints=[
                    f"Vocabulary '{entry.prefix}' found in local registry",
                    f"Features: {', '.join(list(entry.features))}",
                    f"Version: {entry.versions.current}"
                ]
            )
        except KeyError:
            return None
    
    async def _discover_minimal(self, resource_id: str, domain_hints: List[str]) -> DiscoveryMetadata:
        """Minimal discovery (always succeeds)."""
        # Detect resource type from identifier patterns
        resource_type = self._detect_resource_type(resource_id, domain_hints)
        
        return DiscoveryMetadata(
            resource_id=resource_id,
            resource_type=resource_type,
            domain_context=domain_hints + [resource_type],
            resolution_urls=[],
            validation_patterns=[],
            discovery_strategy=DiscoveryStrategy.IDENTIFIER_ONLY,
            confidence_score=0.3,
            reasoning_hints=[
                f"Detected as {resource_type} based on identifier pattern",
                "Limited metadata available - consider SPARQL discovery for richer data"
            ]
        )
    
    def _detect_resource_type(self, resource_id: str, domain_hints: List[str]) -> str:
        """Detect resource type from identifier patterns."""
        # Simple pattern matching for common identifier types
        if any(bio in domain_hints for bio in ["biology", "bioschemas", "life_sciences"]):
            if resource_id.startswith(("P", "Q")):
                return "wikidata_entity"
            elif resource_id.upper().startswith("UNIPROT"):
                return "protein"
            elif len(resource_id) == 6 and resource_id.startswith(("CHEBI:", "MESH:")):
                return "compound"
        
        if "http" in resource_id:
            return "uri"
        
        return "identifier"
    
    def _generate_discovery_suggestions(
        self, 
        metadata: DiscoveryMetadata, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate agent guidance suggestions based on wikidata-mcp patterns."""
        
        suggestions = {
            "next_tools": [],
            "research_workflows": [],
            "reasoning_context": {
                "domain_suggestions": [],
                "workflow_guidance": [],
                "cross_domain_opportunities": []
            }
        }
        
        # Add domain-specific suggestions
        if "biology" in metadata.domain_context or "bioschemas" in metadata.domain_context:
            suggestions["next_tools"].extend([
                "cl_sparql --query 'SELECT ?property ?value WHERE { <{}> ?property ?value }'".format(metadata.resource_id),
                "cl_validate --entity {}".format(metadata.resource_id)
            ])
            
            suggestions["research_workflows"].extend([
                "Protein characterization: sequence → structure → function → interactions",
                "Drug discovery: target identification → binding site analysis → compound screening"
            ])
            
            suggestions["reasoning_context"]["domain_suggestions"].extend([
                "Consider biological pathways and interactions",
                "Look for cross-references to other biological databases",
                "Examine temporal aspects of biological processes"
            ])
        
        # Add confidence-based suggestions
        if metadata.confidence_score < 0.5:
            suggestions["next_tools"].append("cl_discover --enhance {}".format(metadata.resource_id))
            suggestions["reasoning_context"]["workflow_guidance"].append(
                "Low confidence discovery - consider enhanced discovery for richer metadata"
            )
        
        # Add context-aware suggestions
        if "last_discovery" in context:
            suggestions["reasoning_context"]["cross_domain_opportunities"].append(
                "Build on previous discovery: {}".format(context["last_discovery"]["resource_type"])
            )
        
        return suggestions
    
    def _create_educational_error(
        self, 
        resource_id: str, 
        domain_hints: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Create educational error with recovery plan."""
        return {
            "code": "DISCOVERY_FAILED",
            "message": f"Could not discover metadata for resource '{resource_id}'",
            "suggestions": [
                "Verify the resource identifier is correct",
                "Add domain hints to improve discovery accuracy",
                "Try manual resolution with cl_sparql or cl_validate"
            ],
            "recovery_plan": {
                "next_tool": "cl_discover",
                "parameters": {
                    "resource_identifier": resource_id,
                    "domain_hints": domain_hints or ["general"],
                    "enhance": True
                },
                "reasoning": "Enhanced discovery may find metadata via alternative strategies"
            },
            "example_patterns": [
                "UniProt: P01308 (insulin)",
                "Wikidata: Q127367 (insulin)",
                "CHEBI: CHEBI:5931 (insulin)"
            ]
        }

# Global discovery engine instance
discovery_engine = DiscoveryEngine()