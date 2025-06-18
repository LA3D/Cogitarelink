# CogitareLink Pattern Learning Architecture

This directory implements a simple learning system following Claude Code design patterns.

## Philosophy: Tools as Sensors, Claude as Brain

**Core Principle**: Tools observe and report facts. Claude Code interprets patterns and provides intelligence.

## Architecture Overview

### 1. Event Capture (Simple Facts)
Tools emit structured events about what happened:
```json
{
  "tool": "cl_search", 
  "success": true,
  "strategy": "wikidata_api",
  "time_ms": 145,
  "context": {"had_cache": true}
}
```

### 2. Pattern Storage (Human-Readable)
```
cogitarelink/patterns/
├── README.md           # This file
├── events/             # Raw tool events  
├── session/            # Within-session patterns
├── distilled/          # Claude's interpretations
└── reminders/          # Active reminder templates
```

### 3. Reminder Injection (Claude Code Style)
Like Claude Code's tools, reminders focus attention:
```
⚡ cl_search reminders:
- Wikidata → API first (faster)
- Others → SPARQL fallback  
- Empty query = error
```

### 4. Learning Loop

**Session Level**:
1. Tools capture events during use
2. Claude analyzes patterns within session
3. Reminders adjusted for current context

**Cross-Session Level**:
1. Claude distills successful patterns
2. Updates reminder templates
3. Improves default behavior

## Design Constraints

### Keep It Simple
- **No ML models** - Just pattern observation
- **No complex logic** - Tools stay simple
- **Human readable** - All patterns stored as text
- **Immediate application** - No training/deployment cycle

### Follow Claude Code Patterns
- **Tools provide data** - Intelligence in prompts
- **Fail-fast** - Clear errors, not silent failures
- **Composable** - Each tool does one thing well
- **Observable** - Users can see what's happening

### Privacy & Control
- **Local only** - No cloud pattern sharing
- **User controlled** - Can clear/export patterns
- **Transparent** - Users see what was learned

## Implementation Notes

### Event Schema (Keep Simple)
```python
@dataclass
class ToolEvent:
    tool: str           # Tool name
    success: bool       # Did it work?
    time_ms: float      # How long?
    strategy: str       # What approach used?
    context: dict       # Relevant session state
```

### Reminder System (Focus Attention)
```python
def get_reminders(tool_name: str, context: dict) -> list[str]:
    """Return attention-focusing reminders for tool use."""
    # Static critical reminders (always shown)
    # + contextual reminders (based on session state)
    # + learned reminders (from distilled patterns)
```

### Integration Points
1. **Tool initialization** - Load relevant reminders
2. **Pre-execution** - Show contextual reminders  
3. **Post-execution** - Capture event data
4. **Error cases** - Record failure patterns

## Success Metrics

- **Fewer repeated mistakes** - Same errors don't happen twice
- **Faster discovery** - Tools suggest better approaches
- **Context awareness** - Reminders adapt to session state
- **Progressive learning** - System gets smarter through use

## NOT Goals

- Complex AI/ML systems
- Prediction/forecasting  
- Automated decision making
- User behavior tracking
- Performance optimization algorithms

The goal is simple: help Claude Code learn the patterns that make semantic web research effective, then remind users of those patterns at the right moments.