"""Backend data handling for CogitareLink.

Cache management, content analysis, SPARQL operations, and property discovery.
"""

from .cache import cache_manager, SemanticMetadata
from .content import ContentAnalyzer, content_analyzer  
from .sparql import sparql_engine, discover_sparql_endpoints, build_prefixed_query
# from .properties import PropertyDiscovery  # TODO: update after moving

__all__ = [
    "cache_manager",
    "SemanticMetadata", 
    "ContentAnalyzer",
    "content_analyzer",
    "sparql_engine",
    "discover_sparql_endpoints",
    "build_prefixed_query"
]