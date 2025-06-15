"""Decide how two vocabularies can coexist inside a JSON-LD document."""

from __future__ import annotations

import json
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Optional

from pydantic import BaseModel

from ..core.debug import get_logger
from .registry import registry, preferred_collision

log = get_logger("collision")

__all__ = ['log', 'resolver', 'Strategy', 'Plan', 'Resolver']

# Basic collision data - will enhance with data files later
_BUNDLED: Dict[str, Dict[str, Any]] = {
    "('schema', 'bioschemas')": {
        "strategy": "nested_contexts",
        "outer": "schema",
        "inner": "bioschemas",
        "reason": "bioschemas extends schema.org"
    },
    "('bioschemas', 'schema')": {
        "strategy": "nested_contexts", 
        "outer": "schema",
        "inner": "bioschemas",
        "reason": "bioschemas extends schema.org"
    }
}

class Strategy(str, Enum):
    property_scoped   = "property_scoped"
    graph_partition   = "graph_partition"
    nested_contexts   = "nested_contexts"
    context_versioning= "context_versioning"
    separate_graphs   = "separate_graphs"


class Plan(BaseModel):
    strategy: Strategy
    details:  Dict[str, Any] = {}

    model_config = dict(frozen=True)

def _protected_terms(ctx: Dict[str, Any]) -> set[str]:
    "Return the set of keys whose definition contains `\"@protected\": true`."
    if "@context" in ctx:
        ctx = ctx["@context"]
    return {
        term
        for term, defi in ctx.items()
        if isinstance(defi, dict) and defi.get("@protected") is True
    }

@lru_cache(maxsize=128)
def _prot_overlap(a: str, b: str) -> tuple[bool, bool, bool]:
    """
    Cached check returning:
        (a_has_protected, b_has_protected, overlap_exists)
    """
    # Check if terms exist in registry
    a_exists = a in registry._v
    b_exists = b in registry._v
    
    # If either doesn't exist, they can't have protected terms
    if not a_exists or not b_exists:
        return False, False, False
        
    ea, eb = registry[a], registry[b]
    sa = _protected_terms(ea.context_payload())
    sb = _protected_terms(eb.context_payload())
    return bool(sa), bool(sb), bool(sa & sb)


class Resolver:
    "Figure out _how_ two vocabularies should be merged."

    # -------------------------------- private helpers --------------------
    def _registry_hint(self, a: str, b: str) -> Optional[Dict[str, Any]]:
        "Look for a strategy hinted in either vocab's `strategy_defaults`."
        return preferred_collision(a, b) or preferred_collision(b, a)

    def _bundled(self, a: str, b: str) -> Optional[Dict[str, Any]]:
        "Lookup (a,b) or (b,a) in the legacy table."
        key1 = f"('{a}', '{b}')"
        key2 = f"('{b}', '{a}')"
        return _BUNDLED.get(key1) or _BUNDLED.get(key2)
    
    # -------------------------------- public API ------------------------
    def choose(self, a: str, b: str) -> Plan:
        """
        Return a **Plan** describing how vocabularies *a* and *b* should
        coexist in the same JSON-LD document.
        """
        # identical vocabularies never collide
        if a == b:
            return Plan(strategy=Strategy.separate_graphs)

        # 1 – explicit registry hint
        row = self._registry_hint(a, b)
        if row:
            log.debug(f"registry hint ({a},{b}) → {row}")
            return Plan(strategy=Strategy(row["strategy"]),
                        details={k: v for k, v in row.items() if k != "strategy"})

        # 2 – bundled rule
        row = self._bundled(a, b)
        if row:
            log.debug(f"bundled rule ({a},{b}) → {row}")
            return Plan(strategy=Strategy(row["strategy"]),
                        details={k: v for k, v in row.items() if k != "strategy"})

        # 3 – dynamic safety heuristic
        a_has, b_has, overlap = _prot_overlap(a, b)
        if a_has or b_has:                           # at least one uses @protected
            if a_has and b_has and overlap:
                log.debug(f"protected-overlap ({a},{b}) → separate_graphs")
                return Plan(strategy=Strategy.separate_graphs,
                            details={"reason": "overlapping @protected terms"})
            outer, inner = (a, b) if a_has else (b, a)
            log.debug(f"protected one-way ({a},{b}) → nested_contexts")
            return Plan(strategy=Strategy.nested_contexts,
                        details={"outer": outer, "inner": inner})

        # 4 – safe default
        log.debug(f"default ({a},{b}) → separate_graphs")
        return Plan(strategy=Strategy.separate_graphs)

resolver = Resolver()