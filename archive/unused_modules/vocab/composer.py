"""Given one or more registry prefixes, return a single, **safe** JSON-LD `@context` that callers can embed directly into a document."""

from __future__ import annotations

from typing import Any, Dict, List

from ..core.debug import get_logger
from .registry import registry
from .collision import resolver, Strategy

log = get_logger("composer")

__all__ = ['log', 'composer', 'Composer']

class Composer:
    "Merge one or more vocabularies into a conflict-free `@context` dict."

    # --------------------------- public API ----------------------------
    def compose(self, prefixes: List[str], support_nest=False, propagate=True) -> Dict[str, Any]:
        """
        Parameters
        ----------
        prefixes : list of registry prefixes, **ordered by priority**.
                   The first prefix is treated as the primary vocabulary.
        support_nest : bool, if True, add @nest support to the context
        propagate : bool, if False, add @propagate: false to prevent context inheritance
        
        Returns
        -------
        dict – JSON-LD object ready to drop into a document:
               `{"@context": ...}`
        """
        if not prefixes:
            raise ValueError("`prefixes` must contain at least one prefix.")

        # start with primary vocabulary
        ctx_primary = registry[prefixes[0]].context_payload()["@context"]
        merged: Dict[str, Any] = ctx_primary

        for p in prefixes[1:]:
            next_ctx = registry[p].context_payload()["@context"]
            plan     = resolver.choose(prefixes[0], p)

            log.debug(f"merge {p} under strategy {plan.strategy}")

            if plan.strategy is Strategy.property_scoped:
                prop = plan.details.get("property", "data")
                merged[prop] = next_ctx

            elif plan.strategy is Strategy.nested_contexts:
                # outer context goes first in the array
                outer, inner = plan.details["outer"], plan.details["inner"]
                ctx_outer = registry[outer].context_payload()["@context"]
                ctx_inner = registry[inner].context_payload()["@context"]
                merged = {"@context": [ctx_outer, ctx_inner]}

            elif plan.strategy is Strategy.graph_partition:
                # simplistic: just keep contexts in an array; the real graph
                # separation happens later in GraphManager.
                merged = {"@context": [merged, next_ctx]}

            elif plan.strategy is Strategy.context_versioning:
                # honour requested version; for now we just append
                merged = {"@context": [merged, next_ctx]}

            else:   # Strategy.separate_graphs (default)
                merged = {"@context": [merged, next_ctx]}

        # final shape must be `{"@context": ...}`
        if "@context" not in merged:
            merged = {"@context": merged}
            
        # Add JSON-LD 1.1 features if requested
        ctx = merged["@context"]
        
        # Add propagation control
        if not propagate:
            if isinstance(ctx, dict):
                ctx["@propagate"] = False
            elif isinstance(ctx, list) and len(ctx) > 0 and isinstance(ctx[0], dict):
                ctx[0]["@propagate"] = False
                
        # Add @nest support
        if support_nest and isinstance(ctx, dict):
            # This adds '@nest' to the context vocabulary
            ctx["@nest"] = "@nest"

        return merged


# module-level singleton for convenience
composer = Composer()