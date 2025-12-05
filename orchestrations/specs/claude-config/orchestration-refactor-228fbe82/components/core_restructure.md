# Component: Core Restructure

## Purpose
Move generic code from `conduct/core` and `conduct/agents` up to `orchestrations/core`. This makes the core reusable across workflow types.

## Files to Move

| From | To |
|------|-----|
| `conduct/core/config.py` | `core/config.py` |
| `conduct/core/state.py` | `core/state.py` |
| `conduct/core/schemas.py` | `core/schemas.py` |
| `conduct/agents/runner.py` | `core/runner.py` |
| `conduct/agents/registry.py` | `core/registry.py` |

## New File: `orchestrations/core/__init__.py`

```python
"""Core orchestration infrastructure.

This module provides the generic foundation for all workflow types:
- Configuration management
- State persistence
- Agent invocation
- Schema definitions
- Path and context utilities
"""

from .config import (
    Config,
    AgentConfig,
    PhaseConfig,
    ValidationConfig,
    RiskConfig,
    VotingGateConfig,
    ExecutionMode,
    ModeConfig,
)
from .state import (
    State,
    StateManager,
    ComponentState,
    ComponentStatus,
    PhaseStatus,
    Issue,
    VoteResult,
)
from .schemas import get_schema, register_schema, AgentSchema
from .runner import AgentRunner, AgentResult
from .registry import REGISTRY
from .paths import expand_path, get_claude_home, get_specs_dir
from .manifest import Manifest, ComponentDef
from .context import ContextManager, ContextUpdate

__all__ = [
    # Config
    "Config", "AgentConfig", "PhaseConfig", "ValidationConfig",
    "RiskConfig", "VotingGateConfig", "ExecutionMode", "ModeConfig",
    # State
    "State", "StateManager", "ComponentState", "ComponentStatus",
    "PhaseStatus", "Issue", "VoteResult",
    # Schemas
    "get_schema", "register_schema", "AgentSchema",
    # Runner
    "AgentRunner", "AgentResult",
    # Registry
    "REGISTRY",
    # Paths
    "expand_path", "get_claude_home", "get_specs_dir",
    # Manifest
    "Manifest", "ComponentDef",
    # Context
    "ContextManager", "ContextUpdate",
]
```

## Import Updates Needed

After moving, update imports in:
- `conduct/workflow/*.py` - change `from ..core.` to `from orchestrations.core.`
- `conduct/workflows/conduct.py` - update all imports
- `conduct/cli.py` - update imports
- `conduct/__main__.py` - update imports

## Backwards Compatibility

Keep `conduct/core/__init__.py` as re-exports for any external code:

```python
"""Backwards compatibility - use orchestrations.core instead."""
from orchestrations.core import *
```

## Verification

After restructure, run:
```bash
python -c "from orchestrations.core import Config, State, AgentRunner"
python -m orchestrations.conduct.tests.test_dry_run
```
