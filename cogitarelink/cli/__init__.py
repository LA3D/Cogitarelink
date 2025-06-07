"""CLI tools with structured intelligence.

Provides core CLI tools with rich structured responses and agent intelligence:
- cl_discover: Scientific resource discovery with auto-materialization
- cl_sparql: SPARQL queries with guardrails
- cl_validate: SHACL validation with suggestions
- cl_query_memory: Semantic memory queries
- cl_resolve: Universal identifier resolution
- cl_wikidata: Wikidata search and entity operations
- cl_ontfetch: Ontology fetching and analysis
"""

from .cl_discover import discover
from .cl_sparql import sparql_query
# from .cl_materialize import materialize  # Not implemented
from .cl_wikidata import wikidata
from .cl_resolve import resolve
from .cl_ontfetch import ontfetch

__all__ = ['discover', 'sparql_query', 'wikidata', 'resolve', 'ontfetch']