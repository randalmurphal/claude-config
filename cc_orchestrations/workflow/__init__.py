"""Workflow execution engine and loop constructs.

This module provides the core workflow execution infrastructure:
- WorkflowEngine: Drives workflows through phases
- ExecutionContext: Runtime context for phase handlers
- PhaseResult: Result of a phase execution
- ValidationLoop: Validation with multiple reviewers
- FixLoop: Fix attempts until resolved
- VotingGate: Multi-agent consensus for decisions
- ComponentLoop: Per-component execution pipeline
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
    tally_votes_weighted,
)
from .loops import (
    FixLoop,
    LoopResult,
    ValidationLoop,
    issues_are_same,
)

__all__ = [
    # Engine
    'ComponentLoop',
    'ExecutionContext',
    'PhaseHandler',
    'PhaseResult',
    'WorkflowEngine',
    # Gates
    'VotingGate',
    'VotingOutcome',
    'run_voting_gate',
    'tally_votes',
    'tally_votes_weighted',
    # Loops
    'FixLoop',
    'LoopResult',
    'ValidationLoop',
    'issues_are_same',
]
