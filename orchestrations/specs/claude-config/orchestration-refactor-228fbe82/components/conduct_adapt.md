# Component: Conduct Workflow Adaptation

## Purpose
Adapt the conduct workflow to use the new core structure. Update imports and ensure all existing functionality works.

## Location
`~/.claude/orchestrations/workflows/conduct/`

## Structure After Adaptation

```
orchestrations/workflows/conduct/
├── __init__.py
├── config.py          # Conduct-specific CONDUCT_CONFIG
├── phases.py          # Phase handlers (moved from conduct.py)
├── schemas.py         # Conduct-specific schemas
├── prompts/           # Prompt templates
└── tests/
    └── test_dry_run.py
```

## Import Updates

### workflows/conduct/__init__.py

```python
"""Conduct workflow - full orchestration for complex features."""

from .config import CONDUCT_CONFIG, create_conduct_workflow
from .phases import CONDUCT_HANDLERS

__all__ = ["CONDUCT_CONFIG", "CONDUCT_HANDLERS", "create_conduct_workflow"]
```

### workflows/conduct/config.py

```python
"""Conduct workflow configuration."""

from pathlib import Path
from orchestrations.core import (
    Config,
    PhaseConfig,
    VotingGateConfig,
    ValidationConfig,
    RiskConfig,
)
from orchestrations.workflow import WorkflowEngine
from .phases import CONDUCT_HANDLERS

CONDUCT_CONFIG = Config(
    name="conduct",
    # ... existing config ...
)

def create_conduct_workflow(
    work_dir: Path,
    spec_path: Path | None = None,
    config_override: Config | None = None,
) -> WorkflowEngine:
    # ... existing implementation with updated imports ...
```

### workflows/conduct/phases.py

```python
"""Conduct phase handlers."""

from orchestrations.core import (
    Config, State, StateManager,
    ComponentState, ComponentStatus, PhaseStatus,
    AgentRunner,
)
from orchestrations.workflow import (
    ExecutionContext,
    PhaseResult,
    ComponentLoop,
    run_voting_gate,
    ValidationLoop,
)

def phase_parse_spec(ctx: ExecutionContext, phase: PhaseConfig) -> PhaseResult:
    # ... existing implementation ...

# ... other phase handlers ...

CONDUCT_HANDLERS = {
    "parse_spec": phase_parse_spec,
    # ... etc ...
}
```

### workflows/conduct/schemas.py

```python
"""Conduct-specific schemas."""

from orchestrations.core import register_schema, AgentSchema

# Move conduct-specific schemas here from core/schemas.py:
# - spec_parser
# - impact_analysis
# - skeleton_builder
# - implementation
# - validator
# - fix_executor
# - test_runner
# - vote schemas
```

## Backwards Compatibility

Keep old import paths working:

```python
# conduct/__init__.py
"""Backwards compatibility - use orchestrations.workflows.conduct"""
from orchestrations.workflows.conduct import *
```

## Verification

```bash
# Must pass after adaptation
python -m orchestrations.workflows.conduct.tests.test_dry_run

# Old import path should still work
python -c "from orchestrations.conduct import create_conduct_workflow"
```

## What Stays Conduct-Specific

- Phase handlers (parse_spec, impact_analysis, component_loop, etc.)
- CONDUCT_CONFIG with specific phases/gates
- Conduct-specific schemas
- Prompt templates

## What's Now in Core

- WorkflowEngine
- ValidationLoop, FixLoop
- VotingGate
- AgentRunner
- State, StateManager
- Config base classes
