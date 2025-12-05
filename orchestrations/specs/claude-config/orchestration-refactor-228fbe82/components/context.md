# Component: context.py

## Purpose
Manages context files that persist information between agent calls. Agents read context before executing and write updates after completing work.

## Location
`~/.claude/orchestrations/core/context.py`

## Dependencies
- `paths.py` (for path resolution)

## Interface

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ContextUpdate:
    """Update to apply to context files."""
    summary: str = ""  # What was accomplished
    discoveries: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    for_next_agent: str = ""  # Specific instructions for next agent

class ContextManager:
    """Manages context files for a spec."""

    def __init__(self, spec_dir: Path):
        self.spec_dir = spec_dir
        self.context_file = spec_dir / "CONTEXT.md"
        self.decisions_file = spec_dir / "DECISIONS.md"
        self.components_dir = spec_dir / "components"

    def get_global_context(self) -> str:
        """Read global CONTEXT.md content."""

    def get_component_context(self, component_id: str) -> str:
        """Read component-specific context."""

    def get_context_for_prompt(self, component_id: str | None = None) -> str:
        """Build full context section for agent prompt.

        Includes:
        - Global context (CONTEXT.md)
        - Relevant decisions (DECISIONS.md)
        - Component-specific context if component_id provided
        """

    def update_from_result(
        self,
        update: ContextUpdate,
        component_id: str | None = None,
    ) -> None:
        """Update context files from agent result.

        - Appends discoveries to CONTEXT.md
        - Appends decisions to DECISIONS.md
        - Updates component context if component_id provided
        """

    def update_component_status(
        self,
        component_id: str,
        status: str,
        summary: str = "",
    ) -> None:
        """Update component context with new status."""

    def initialize(self, manifest: "Manifest") -> None:
        """Initialize context files for a new spec execution."""
```

## Context File Formats

### CONTEXT.md
```markdown
# Execution Context

## Current State
Status: IN_PROGRESS
Components: 3/10 complete
Last updated: 2025-12-05T10:00:00Z

## Critical Discoveries
- [timestamp] Discovery 1
- [timestamp] Discovery 2

## Blockers
- None

## For Next Agent
[Instructions from previous agent]
```

### components/<id>.md
```markdown
# Component: <id>

## Status
IMPLEMENTING

## Purpose
[From manifest]

## What's Been Done
- [timestamp] Action 1

## Discoveries
- [timestamp] Finding 1

## For Next Agent
[Specific instructions]
```

## Implementation Notes

- Use append-only for discoveries and decisions (don't overwrite)
- Timestamp all entries
- Keep files under 100 lines (summarize if needed)
- Component contexts are created on first access
