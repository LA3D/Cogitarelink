"""
Shared chain-of-thought scaffolds for Software 2.0 tools.

These patterns & prompts are injected into each tool's suggestions payload
to activate the LLM's own reasoning rather than hard-coding domain logic.
"""

# 1. Reasoning trigger questions (activate domain expertise)
REASONING_TRIGGERS = [
    "What relationships might this entity have with others of its type?",
    "What hierarchical classifications could help narrow or broaden this search?",
    "What external databases might contain related information?",
    "What temporal or spatial constraints might be relevant here?",
]

# 2. Meta-pattern discovery scaffolds (universal exploration workflows)
DISCOVERY_PATTERNS = [
    "🔍 ENTITY → TYPE → CATEGORY → RELATED_ENTITIES",
    "🔗 CURRENT → PROPERTIES → EXTERNAL_IDS → CROSS_REFERENCES",
    "📊 INDIVIDUAL → CLASS → SUPERCLASS → DOMAIN_KNOWLEDGE",
    "⏱️ SNAPSHOT → HISTORICAL → TRENDS → PREDICTIONS",
]

# 4. Analytical prompts (scaffold the LLM's own thinking process)
ANALYSIS_PROMPTS = [
    "Given this entity's properties, what domain expertise should be applied?",
    "What are the natural follow-up questions for this type of discovery?",
    "What cross-database connections would be most valuable here?",
    "What patterns do you see that suggest the next exploration direction?",
]

# 6. Exploration framework (generic extension questions)
EXPLORATION_FRAMEWORK = {
    "natural_extensions": [
        "What contains this? (hierarchical_up)",
        "What does this contain? (hierarchical_down)",
        "What is similar to this? (lateral_relationships)",
        "What external systems know about this? (cross_references)",
        "What has changed about this over time? (temporal_analysis)",
    ],
    # per-call customization: knowledge_gaps, connection_opportunities
    "knowledge_gaps": [],
    "connection_opportunities": [],
}

# 7. Adaptive error-recovery patterns (reasoning scaffolds for common failures)
ERROR_RECOVERY_PATTERNS = {
    "when_entity_not_found": {
        "reasoning_path": "identifier_format → search_strategy → related_entities",
        "example_adaptations": ["Q123 → search_by_label", "URI → extract_identifier"],
    },
    "when_query_too_broad": {
        "reasoning_path": "add_constraints → limit_scope → focus_properties",
        "constraint_strategies": ["entity_type", "temporal", "geographic", "domain_specific"],
    },
}