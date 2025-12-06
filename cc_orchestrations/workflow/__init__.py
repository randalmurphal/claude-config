"""Workflow execution primitives.

Generic workflow infrastructure used by all workflow types.
"""

from .engine import (
    ComponentLoop,
    ExecutionContext,
    PhaseHandler,
    PhaseResult,
    WorkflowEngine,
)
from .gates import (
    VotingGate,
    VotingOutcome,
    run_voting_gate,
    tally_votes,
)
from .loops import (
    FixLoop,
    LoopResult,
    ValidationLoop,
    issues_are_same,
)

__all__ = [
    'ComponentLoop',
    'ExecutionContext',
    'FixLoop',
    'LoopResult',
    'PhaseHandler',
    'PhaseResult',
    # Loops
    'ValidationLoop',
    # Gates
    'VotingGate',
    'VotingOutcome',
    # Engine
    'WorkflowEngine',
    'issues_are_same',
    'run_voting_gate',
    'tally_votes',
]
