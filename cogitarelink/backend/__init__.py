"""Backend data handling for CogitareLink.

Cache management, content analysis, SPARQL operations, and property discovery.
"""

from .cache import cache_manager, SemanticMetadata
from .content import ContentAnalyzer, content_analyzer  
from .sparql import sparql_engine, discover_sparql_endpoints, build_prefixed_query, resolve_endpoint, get_all_endpoints
# Properties discovery functionality replaced by Software 2.0 workflow
# See: cogitarelink/patterns/use_cases/wikidata_property_entity_discovery.md

__all__ = [
    "cache_manager",
    "SemanticMetadata", 
    "ContentAnalyzer",
    "content_analyzer",
    "sparql_engine",
    "discover_sparql_endpoints",
    "build_prefixed_query",
    "resolve_endpoint",
    "get_all_endpoints"
]