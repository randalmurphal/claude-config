"""Core orchestration infrastructure.

This module provides the generic foundation for all workflow types:
- Configuration management
- State persistence
- Agent invocation
- Schema definitions
- Path and context utilities
"""

from .config import (
    AgentConfig,
    Config,
    ExecutionMode,
    ModeConfig,
    PhaseConfig,
    RiskConfig,
    ValidationConfig,
    VotingGateConfig,
)
from .context import ContextManager, ContextUpdate
from .manifest import ComponentDef, ExecutionConfig, Manifest, QualityConfig
from .paths import (
    expand_path,
    get_claude_home,
    get_git_root,
    get_project_name,
    get_spec_path,
    get_specs_dir,
    relative_to_git_root,
    relative_to_home,
)
from .registry import REGISTRY
from .runner import AgentResult, AgentRunner
from .schemas import AgentSchema, get_schema, register_schema
from .state import (
    ComponentState,
    ComponentStatus,
    Issue,
    PhaseStatus,
    State,
    StateManager,
    VoteResult,
)


__all__ = [
    # Registry
    'REGISTRY',
    'AgentConfig',
    'AgentResult',
    # Runner
    'AgentRunner',
    'AgentSchema',
    'ComponentDef',
    'ComponentState',
    'ComponentStatus',
    # Config
    'Config',
    # Context
    'ContextManager',
    'ContextUpdate',
    'ExecutionConfig',
    'ExecutionMode',
    'Issue',
    # Manifest
    'Manifest',
    'ModeConfig',
    'PhaseConfig',
    'PhaseStatus',
    'QualityConfig',
    'RiskConfig',
    # State
    'State',
    'StateManager',
    'ValidationConfig',
    'VoteResult',
    'VotingGateConfig',
    # Paths
    'expand_path',
    'get_claude_home',
    'get_git_root',
    'get_project_name',
    'get_spec_path',
    'get_specs_dir',
    'relative_to_git_root',
    'relative_to_home',
    # Schemas
    'get_schema',
    'register_schema',
]
