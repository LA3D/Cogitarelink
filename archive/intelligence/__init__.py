"""Agent intelligence layer.

Provides sophisticated intelligence for agents based on wikidata-mcp patterns:
- Discovery Engine: Self-configuring multi-strategy resource discovery
- Response Manager: Biological-aware progressive disclosure and truncation  
- Guidance Generator: Domain-specific reasoning scaffolds and workflow guidance
- Context Management: Opaque context handles for stateless protocol compatibility
"""

from .discovery_engine import discovery_engine, DiscoveryEngine, DiscoveryResult, DiscoveryMetadata
from .response_manager import response_manager, ResponseManager, ResponseLevel, TruncationMetadata
from .guidance_generator import guidance_generator, GuidanceGenerator, GuidanceContext, DomainType

__all__ = [
    'discovery_engine', 'DiscoveryEngine', 'DiscoveryResult', 'DiscoveryMetadata',
    'response_manager', 'ResponseManager', 'ResponseLevel', 'TruncationMetadata', 
    'guidance_generator', 'GuidanceGenerator', 'GuidanceContext', 'DomainType'
]