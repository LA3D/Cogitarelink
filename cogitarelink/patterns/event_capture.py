"""Tool event capture system.

Simple event logging for tool usage patterns.
Events are facts, not interpretations.
"""

from dataclasses import dataclass
from typing import Dict, Any
import time

@dataclass
class ToolEvent:
    """Simple tool event structure."""
    tool: str           # Tool name (cl_search, rdf_get, etc.)
    success: bool       # Did the tool complete successfully?
    time_ms: float      # Execution time in milliseconds  
    strategy: str       # Strategy used (api, sparql_fallback, etc.)
    context: Dict[str, Any]  # Relevant session context


def capture_tool_event(tool_name: str, success: bool, time_ms: float, 
                      strategy: str, context: Dict[str, Any]) -> None:
    """Capture a tool usage event.
    
    Following Claude Code pattern: simple, clear, fail-fast.
    """
    # TODO: Implement event storage
    # TODO: Keep it simple - just append to file or cache
    pass


def get_recent_events(tool_name: str = None, limit: int = 10) -> list[ToolEvent]:
    """Get recent tool events for pattern analysis.
    
    Used by Claude to understand what's been happening in session.
    """
    # TODO: Implement event retrieval  
    # TODO: Return simple list, let Claude do the analysis
    return []