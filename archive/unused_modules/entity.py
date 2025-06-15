"""Enhanced Entity: Immutable JSON-LD entities with agent intelligence."""

from __future__ import annotations

import hashlib
import uuid
from copy import deepcopy
from datetime import datetime
from functools import cached_property
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from .cache import InMemoryCache
from .debug import get_logger
from ..vocab.composer import composer
from ..intelligence.guidance_generator import guidance_generator, GuidanceContext, DomainType
from ..intelligence.response_manager import response_manager, ResponseLevel

# Try to import pyld for proper JSON-LD processing
try:
    from pyld import jsonld
    _HAS_PYLD = True
except ImportError:
    _HAS_PYLD = False

# Global cache instances for different types of caching
_normalization_cache = InMemoryCache(maxsize=256, ttl=3600)  # 1 hour TTL
_context_cache = InMemoryCache(maxsize=128, ttl=1800)        # 30 min TTL

log = get_logger("entity")


class ContextProcessor:
    """Context processor with sophisticated caching."""
    
    def normalize(self, doc: Dict[str, Any]) -> str:
        """
        Canonicalize using URDNA2015 and return N-Quads string.
        Results are cached for performance.
        """
        # Create hashable cache key from document
        import json
        doc_str = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        cache_key = f"norm:{hash(doc_str)}"
        
        # Check cache first
        cached = _normalization_cache.get(cache_key)
        if cached is not None:
            log.debug("Cache hit for normalization")
            return cached
        
        if not _HAS_PYLD:
            # Fallback to simple JSON canonicalization if pyld not available
            log.warning("pyld not available, falling back to JSON canonicalization")
            result = doc_str
        else:
            try:
                result = jsonld.normalize(
                    doc,
                    options=dict(algorithm="URDNA2015", format="application/n-quads")
                )
                log.debug(f"URDNA2015 normalization successful, {len(result)} chars")
            except Exception as e:
                log.error(f"URDNA2015 normalization failed: {e}")
                # Fallback to JSON canonicalization
                result = doc_str
        
        # Cache the result
        _normalization_cache.set(cache_key, result)
        return result
    
    def process_context(self, vocab_list: List[str]) -> Dict[str, Any]:
        """
        Process vocabulary list into JSON-LD context using vocabulary registry.
        Results are cached for performance.
        """
        # Create hashable cache key from vocab list
        cache_key = tuple(sorted(vocab_list))  # Sort for consistent caching
        
        # Check cache first
        cached = _context_cache.get(f"context:{hash(cache_key)}")
        if cached is not None:
            log.debug(f"Cache hit for vocab context: {vocab_list}")
            return cached
        
        try:
            # Use sophisticated vocabulary composer with collision detection
            result = composer.compose(vocab_list, support_nest=False)
            log.debug(f"Composed context for vocab {vocab_list}: {len(result.get('@context', {}))} terms")
            
            # Cache the result
            _context_cache.set(f"context:{hash(cache_key)}", result)
            return result
        except Exception as e:
            log.warning(f"Context composition failed for {vocab_list}: {e}, falling back to basic context")
            # Fallback to basic context if composition fails
            basic_context = {"name": "http://schema.org/name"}
            for vocab in vocab_list:
                if vocab == "bioschemas":
                    basic_context.update({
                        "Protein": "https://bioschemas.org/Protein",
                        "Gene": "https://bioschemas.org/Gene",
                        "hasSequence": "https://bioschemas.org/hasSequence"
                    })
                elif vocab in ["schema", "schema.org"]:
                    basic_context.update({
                        "Person": "http://schema.org/Person",
                        "Organization": "http://schema.org/Organization"
                    })
            fallback_result = {"@context": basic_context}
            
            # Cache the fallback too
            _context_cache.set(f"context:{hash(cache_key)}", fallback_result)
            return fallback_result


# Global context processor instance
_processor = ContextProcessor()


class Entity(BaseModel):
    """
    Enhanced Entity combining cogitarelink-experimental's semantic rigor 
    with wikidata-mcp's agent intelligence patterns.
    
    Features:
    - Immutable JSON-LD entities with proper canonicalization
    - URDNA2015 normalization for cryptographic signatures
    - Agent-friendly structured responses
    - Chain-of-Thought reasoning scaffolds
    """
    
    id: Optional[str] = Field(default=None, alias="@id")
    vocab: List[str] = Field(min_length=1)
    content: Dict[str, Any] = Field(default_factory=dict)
    meta: Optional[Dict[str, Any]] = None
    created: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = dict(frozen=True, populate_by_name=True)
    
    @model_validator(mode="after")
    def _attach_context_and_id(self) -> "Entity":
        """Generate ID and ensure content immutability."""
        # Generate blank-node ID if missing
        if self.id is None:
            object.__setattr__(self, "id", f"urn:uuid:{uuid.uuid4()}")
        
        # Make deep copy of content to ensure immutability
        immutable_content = deepcopy(self.content)
        object.__setattr__(self, "content", immutable_content)
        
        return self
    
    @property
    def as_json(self) -> Dict[str, Any]:
        """Full JSON-LD dict with sophisticated multi-vocabulary @context."""
        # Use real vocabulary composition with collision detection
        context_data = _processor.process_context(self.vocab)
        
        base = {}
        # Handle both nested and flat context structures
        if "@context" in context_data:
            base["@context"] = context_data["@context"]
        else:
            base["@context"] = context_data
            
        if self.id:
            base["@id"] = self.id
        base.update(self.content)
        return base
    
    @cached_property
    def normalized(self) -> str:
        """URDNA2015 N-Quads representation for signing."""
        return _processor.normalize(self.as_json)
    
    @cached_property
    def sha256(self) -> str:
        """Cryptographic signature over normalized representation."""
        return hashlib.sha256(self.normalized.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-LD dict (alias for as_json for backward compatibility)."""
        return self.as_json
    
    def to_agent_response(self, level: ResponseLevel = ResponseLevel.DETAILED) -> Dict[str, Any]:
        """Generate structured response for AI agents with wikidata-mcp intelligence patterns."""
        # Detect domain type from vocabularies and content
        domain_type = self._detect_domain_type()
        
        # Create guidance context
        guidance_context = GuidanceContext(
            entity_type=self.content.get("@type", "Unknown"),
            domain_type=domain_type,
            properties=list(self.content.keys()),
            confidence_score=0.8,  # High confidence for validated entities
            previous_actions=[],
            available_tools=["cl_discover", "cl_sparql", "cl_validate", "cl_resolve"]
        )
        
        # Generate sophisticated guidance
        guidance = guidance_generator.generate_guidance(guidance_context)
        
        # Build comprehensive response
        full_response = {
            "success": True,
            "data": {
                "entity": self.to_dict(),
                "signature": self.sha256,
                "vocab": self.vocab,
                "domain_context": guidance["domain_context"]
            },
            "metadata": {
                "vocab_count": len(self.vocab),
                "property_count": len(self.content),
                "entity_type": self.content.get("@type", "Unknown"),
                "has_signature": True,
                "domain_type": domain_type.value,
                "confidence_score": guidance_context.confidence_score
            },
            "suggestions": {
                "next_tools": guidance["next_tools"],
                "reasoning_patterns": guidance["reasoning_patterns"],
                "workflow_guidance": guidance["workflow_guidance"],
                "cross_domain_opportunities": guidance["cross_domain_opportunities"]
            },
            "claude_guidance": {
                "entity_summary": f"Entity of type '{self.content.get('@type', 'Unknown')}' with {len(self.content)} properties",
                "key_properties": list(self.content.keys())[:5],
                "reasoning_hints": guidance["reasoning_patterns"][:3],
                "next_actions": guidance["next_tools"][:3],
                "domain_intelligence": guidance["domain_context"],
                "confidence_guidance": guidance["confidence_guidance"]
            }
        }
        
        # Apply response truncation based on level
        if level != ResponseLevel.FULL:
            truncated_response, truncation_metadata = response_manager.truncate_response(
                full_response, level, preserve_structure=True
            )
            return truncated_response
        
        # Enhance for agent chaining
        return response_manager.enhance_for_agent_chain(full_response)
    
    def _detect_domain_type(self) -> DomainType:
        """Detect domain type from vocabularies and content."""
        # Check vocabularies for domain hints
        bio_vocabs = {"bioschemas", "biology", "life_sciences"}
        if any(vocab in bio_vocabs for vocab in self.vocab):
            return DomainType.BIOLOGICAL
        
        # Check entity type for biological indicators
        entity_type = self.content.get("@type", "").lower()
        bio_types = {"protein", "gene", "compound", "disease", "virus", "organism"}
        if any(bio_type in entity_type for bio_type in bio_types):
            return DomainType.BIOLOGICAL
        
        # Check for geospatial indicators
        geo_properties = {"coordinate", "location", "place", "latitude", "longitude"}
        if any(prop in self.content for prop in geo_properties):
            return DomainType.GEOSPATIAL
        
        # Check for semantic web indicators
        semantic_properties = {"@context", "@type", "@id", "rdf", "owl", "rdfs"}
        if any(prop in str(self.content) for prop in semantic_properties):
            return DomainType.SEMANTIC_WEB
        
        return DomainType.GENERAL
    
    def generate_reasoning_context(self) -> Dict[str, Any]:
        """Generate Chain-of-Thought scaffolds for agents using intelligence patterns."""
        # Use the sophisticated guidance generator instead of simple patterns
        domain_type = self._detect_domain_type()
        
        guidance_context = GuidanceContext(
            entity_type=self.content.get("@type", "Unknown"),
            domain_type=domain_type,
            properties=list(self.content.keys()),
            confidence_score=0.8,  # High confidence for validated entities
            previous_actions=[],
            available_tools=["cl_discover", "cl_sparql", "cl_validate", "cl_resolve"]
        )
        
        # Generate comprehensive guidance
        guidance = guidance_generator.generate_guidance(guidance_context)
        
        # Return enhanced reasoning context
        return {
            "reasoning_patterns": guidance["reasoning_patterns"],
            "workflow_suggestions": guidance["workflow_guidance"]["suggested_sequence"],
            "biological_reasoning": guidance["reasoning_patterns"] if domain_type == DomainType.BIOLOGICAL else [],
            "semantic_context": {
                "vocabularies_used": self.vocab,
                "properties_available": list(self.content.keys()),
                "entity_signature": self.sha256[:8] + "...",  # Short signature for display
                "reasoning_confidence": guidance["confidence_guidance"]["reliability_assessment"],
                "domain_type": domain_type.value,
                "entity_analysis": guidance["entity_analysis"]
            },
            "cross_domain_opportunities": guidance["cross_domain_opportunities"],
            "confidence_guidance": guidance["confidence_guidance"]
        }