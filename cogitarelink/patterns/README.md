# CogitareLink Pattern Learning System

Simple approach: capture session narratives in markdown, manually distill into CLAUDE.md improvements when requested.

## Philosophy: Start Simple, Test Immediately

Following Jeremy Howard's approach - build the simplest thing that works, then iterate.

## What We Actually Need Right Now

### Session Capture Template
- Human fills out session narrative in `use_cases/template.md`
- Natural story format: what worked, what failed, key insights
- No complex structured data or automation

### Manual Distillation When Requested  
- Human says "Claude, read my session files and suggest CLAUDE.md improvements"
- Claude reads markdown files and suggests specific CLAUDE.md additions
- Human manually adds good suggestions to CLAUDE.md

**That's it.** No complex infrastructure until we prove this simple approach works.

## Example Workflow

1. **After research session**: Copy `template.md`, fill out narrative about what happened
2. **When ready to improve**: "Claude, analyze my biology sessions and suggest CLAUDE.md updates"
3. **Claude responds**: "Based on your sessions, I suggest adding: '- Always start biology research with Wikidata search for cross-references'"
4. **Human decides**: Manually add good suggestions to CLAUDE.md

## Directory Structure

```
cogitarelink/patterns/
├── README.md              # This file - simple approach documentation
├── use_cases/             # Session capture templates and examples
│   ├── template.md        # Template for capturing session narratives
│   └── example_*.md       # Example completed session narratives
```

## What We're NOT Building (Yet)

- Automated pattern extraction systems
- Complex data storage and retrieval 
- Real-time instruction enhancement
- Statistical analysis of usage patterns
- Integration hooks into tool execution

## The Vision

Like Claude Code's auto-compact system, we want to distill rich semantic web research narratives into focused reminders that prevent repeated mistakes and speed up future work.

But we start with the simplest possible implementation: manual capture, manual distillation, manual integration.

## Future Phases (Only If Simple Approach Proves Valuable)

**Phase 2**: Simple prompt templates for Claude to analyze session narratives more systematically

**Phase 3**: Basic integration to suggest CLAUDE.md updates automatically

**Phase 4**: Multi-session pattern accumulation

But we don't build any of this until Phase 1 (manual process) proves the value.