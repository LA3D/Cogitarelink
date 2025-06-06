"""CLI tools with structured intelligence.

Provides 8 core CLI tools with rich structured responses and agent intelligence:
- cl_discover: Scientific resource discovery with auto-materialization
- cl_sparql: SPARQL queries with guardrails
- cl_materialize: Knowledge materialization
- cl_explain: Reasoning chain explanation
- cl_validate: SHACL validation with suggestions
- cl_query_memory: Semantic memory queries
- cl_resolve: Universal identifier resolution
- cl_orchestrate: Multi-step workflow coordination
"""

from .cl_discover import discover
from .cl_sparql import sparql_query
from .cl_materialize import materialize
from .cl_wikidata import wikidata

__all__ = ['discover', 'sparql_query', 'materialize', 'wikidata']