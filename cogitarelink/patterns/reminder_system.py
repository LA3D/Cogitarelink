"""Tool reminder system.

Focus Claude's attention on relevant patterns.
Like Claude Code's tool instructions - pointers to knowledge, not tutorials.
"""

from typing import Dict, List, Any


def get_tool_reminders(tool_name: str, context: Dict[str, Any]) -> List[str]:
    """Get focused reminders for tool usage.
    
    Following Claude Code pattern: reminders focus attention on relevant 
    parts of base knowledge, they don't teach new concepts.
    """
    # TODO: Implement reminder selection
    # TODO: Critical reminders (always shown)
    # TODO: Contextual reminders (based on session state)  
    # TODO: Learned reminders (from distilled patterns)
    
    # Example structure:
    # return [
    #     "⚡ REMINDER: Discovery-first rule (REF: base-patterns)",
    #     "⚡ CONTEXT: Previous SPARQL query failed (REF: error-patterns)", 
    #     "⚡ LEARNED: Wikidata API 10x faster for search (REF: session-patterns)"
    # ]
    
    return []


def add_learned_reminder(tool_name: str, reminder: str, priority: str = "normal") -> None:
    """Add a new reminder based on learned patterns.
    
    Called when Claude discovers something worth remembering.
    """
    # TODO: Implement reminder storage
    # TODO: Keep it simple - text files or cache entries
    pass


def get_critical_reminders(tool_name: str) -> List[str]:
    """Get critical reminders that should always be shown.
    
    These are the non-negotiable patterns (like discovery-first rule).
    """
    # TODO: Implement critical reminder lookup
    # TODO: These should be stable, well-tested patterns
    return []