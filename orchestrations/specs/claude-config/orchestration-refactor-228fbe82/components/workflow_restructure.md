# Component: Workflow Restructure

## Purpose
Move `conduct/workflow/` up to `orchestrations/workflow/`. The workflow primitives (engine, gates, loops) are generic and should be at the orchestrations level.

## Files to Move

| From | To |
|------|-----|
| `conduct/workflow/engine.py` | `workflow/engine.py` |
| `conduct/workflow/gates.py` | `workflow/gates.py` |
| `conduct/workflow/loops.py` | `workflow/loops.py` |
| `conduct/workflow/__init__.py` | `workflow/__init__.py` |

## New File: `orchestrations/workflow/__init__.py`

```python
"""Workflow execution primitives.

Generic workflow infrastructure used by all workflow types:
- WorkflowEngine: Executes phases from config
- ValidationLoop: Multi-reviewer validation with fix cycles
- FixLoop: Automated fix attempts
- VotingGate: Multi-agent consensus decisions
"""

from .engine import (
    WorkflowEngine,
    ExecutionContext,
    PhaseResult,
    ComponentLoop,
    PhaseHandler,
)
from .gates import (
    VotingGate,
    VotingOutcome,
    tally_votes,
    run_voting_gate,
)
from .loops import (
    ValidationLoop,
    FixLoop,
    LoopResult,
    issues_are_same,
)

__all__ = [
    # Engine
    "WorkflowEngine", "ExecutionContext", "PhaseResult",
    "ComponentLoop", "PhaseHandler",
    # Gates
    "VotingGate", "VotingOutcome", "tally_votes", "run_voting_gate",
    # Loops
    "ValidationLoop", "FixLoop", "LoopResult", "issues_are_same",
]
```

## Import Updates in Moved Files

### engine.py
```python
# Old
from ..agents.runner import AgentRunner, AgentResult
from ..core.config import Config, PhaseConfig
from ..core.state import ...

# New
from ..core import (
    AgentRunner, AgentResult,
    Config, PhaseConfig,
    State, StateManager, ComponentState, ComponentStatus, PhaseStatus, Issue,
)
from .gates import VotingGate, VotingOutcome
from .loops import ValidationLoop, FixLoop, LoopResult
```

### gates.py
```python
# Old
from ..agents.runner import AgentRunner
from ..core.config import VotingGateConfig
from ..core.state import VoteResult
from ..core.schemas import get_schema

# New
from ..core import (
    AgentRunner,
    VotingGateConfig,
    VoteResult,
    get_schema,
)
```

### loops.py
```python
# Old
from ..agents.runner import AgentRunner, AgentResult
from ..core.state import Issue
from .gates import run_voting_gate, VotingOutcome

# New
from ..core import AgentRunner, AgentResult, Issue
from .gates import run_voting_gate, VotingOutcome
```

## Verification

After restructure:
```bash
python -c "from orchestrations.workflow import WorkflowEngine, ValidationLoop, VotingGate"
```
