"""
CogitareLink: Living Scientific Assistant

A semantic web-powered scientific research assistant that combines rigorous knowledge 
management with intelligent discovery and continuous learning from agent interactions.

## Core Philosophy
- Hybrid CLI + Agentic: CLI-first composable tools with rich structured responses for agent intelligence
- Semantic Memory: All discovered knowledge stored as immutable entities with full provenance tracking
- Discovery-First Guardrails: Never query without schema understanding (like Read-before-Edit in Claude Code)
- In-Context Teaching: Continuously learn and improve from actual agent usage patterns
- Software 2.0: Generalized tools + intelligent prompting rather than hardcoded logic
- Verifiable Science: Every conclusion traceable to sources with cryptographic verification
- Framework Agnostic: Works with Claude Code, DSPy, LangGraph, or any agent framework
"""

__version__ = "0.1.0"

# Core modules
from . import core, vocab, reason

# Intelligence and memory
from . import intelligence, memory

# Verification and teaching
from . import verify, teaching

# CLI and adapters
from . import cli, adapters

__all__ = [
    "core", "vocab", "reason", "intelligence", "memory", 
    "verify", "teaching", "cli", "adapters"
]