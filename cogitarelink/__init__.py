"""
CogitareLink: Living Scientific Assistant

A semantic web-powered scientific research assistant following Claude Code patterns 
with discovery-first guardrails and multi-agent coordination capabilities.

## Core Philosophy
- Simple Tools: Each tool does ONE thing well (like Claude Code)
- Fast Execution: Sub-second response times  
- Discovery First: Cache schemas, discover before query
- Prompt Intelligence: Move complexity to prompts, not code
- Multi-Agent Ready: Tools compose for agent workflows
"""

__version__ = "0.1.0"

# Core modules only - minimal clean architecture
from . import backend, utils, cli, patterns, prompts

__all__ = ["backend", "utils", "cli", "patterns", "prompts"]