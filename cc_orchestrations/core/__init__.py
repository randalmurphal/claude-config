"""Core orchestration infrastructure.

This module provides the generic foundation for all workflow types:
- Configuration management
- State persistence
- Agent invocation
- Extension discovery
- Git and worktree utilities
"""

from .config import (
    CLAUDE_ONLY_MODELS,
    CURSOR_MODELS,
    DEFAULT_COUNCIL_MODELS,
    OPUS_THINKING_MODEL,
    AgentConfig,
    CLIBackend,
    Config,
    ExecutionMode,
    ModeConfig,
    PhaseConfig,
    RiskConfig,
    ValidationConfig,
    VotingGateConfig,
    get_backend_for_model,
)
from .context import ContextManager, ContextUpdate
from .extensions import (
    detect_project_extensions,
    get_extension_context,
    get_extension_prompts,
    get_extension_validators,
    get_installed_extensions,
    load_extension,
    merge_prompts,
)
from .git import (
    get_conduct_commits,
    git_commit,
    git_has_changes,
    git_log_since,
    git_show_commit,
    git_stage_all,
)
from .manifest import ComponentDef, ExecutionConfig, Manifest, QualityConfig
from .paths import (
    expand_path,
    get_git_root,
    get_project_name,
    relative_to_git_root,
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
from .trajectory import AgentTrajectory, SessionSummary, TrajectoryLogger
from .worktree import (
    WORKTREES_BASE,
    WorktreeContext,
    WorktreeInfo,
    WorktreeManager,
    get_main_repo_from_worktree,
    is_in_worktree,
    worktree_context,
)

__all__ = [
    # Config
    'AgentConfig',
    'CLIBackend',
    'CLAUDE_ONLY_MODELS',
    'Config',
    'CURSOR_MODELS',
    'DEFAULT_COUNCIL_MODELS',
    'ExecutionMode',
    'OPUS_THINKING_MODEL',
    'ModeConfig',
    'PhaseConfig',
    'RiskConfig',
    'ValidationConfig',
    'VotingGateConfig',
    'get_backend_for_model',
    # Context
    'ContextManager',
    'ContextUpdate',
    # Extensions
    'detect_project_extensions',
    'get_extension_context',
    'get_extension_prompts',
    'get_extension_validators',
    'get_installed_extensions',
    'load_extension',
    'merge_prompts',
    # Git
    'get_conduct_commits',
    'git_commit',
    'git_has_changes',
    'git_log_since',
    'git_show_commit',
    'git_stage_all',
    # Manifest
    'ComponentDef',
    'ExecutionConfig',
    'Manifest',
    'QualityConfig',
    # Paths
    'expand_path',
    'get_git_root',
    'get_project_name',
    'relative_to_git_root',
    # Registry
    'REGISTRY',
    # Runner
    'AgentResult',
    'AgentRunner',
    # Schemas
    'AgentSchema',
    'get_schema',
    'register_schema',
    # Trajectory
    'AgentTrajectory',
    'SessionSummary',
    'TrajectoryLogger',
    # State
    'ComponentState',
    'ComponentStatus',
    'Issue',
    'PhaseStatus',
    'State',
    'StateManager',
    'VoteResult',
    # Worktrees
    'WORKTREES_BASE',
    'WorktreeContext',
    'WorktreeInfo',
    'WorktreeManager',
    'get_main_repo_from_worktree',
    'is_in_worktree',
    'worktree_context',
]
