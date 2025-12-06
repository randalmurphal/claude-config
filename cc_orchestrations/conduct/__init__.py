"""
Conduct Orchestrator - External enforcement for Claude Code workflows.

Philosophy: Claude can't skip validation loops because the script won't let it
proceed until the JSON says "pass".

Backwards compatibility layer - imports from new locations.
"""

__version__ = '0.1.0'

# Re-export from new locations for backwards compatibility
from cc_orchestrations.conduct.workflows.conduct import (
    CONDUCT_CONFIG,
    CONDUCT_HANDLERS,
    create_conduct_workflow,
)

__all__ = [
    'CONDUCT_CONFIG',
    'CONDUCT_HANDLERS',
    'create_conduct_workflow',
]
