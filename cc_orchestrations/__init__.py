"""Claude Code Orchestrations - Multi-agent workflow automation.

A self-contained orchestration system for automating complex development workflows:
- Ticket implementation (Jira → Investigation → Spec → Code → PR)
- PR review with multi-agent validation
- Conduct orchestration for complex features

Designed to be extensible with project-specific modules.
"""

__version__ = '0.2.0'

from .core.config import Config, ExecutionMode
from .core.extensions import detect_project_extensions, get_installed_extensions
from .core.runner import AgentResult, AgentRunner
from .core.state import State, StateManager

__all__ = [
    'AgentResult',
    'AgentRunner',
    'Config',
    'ExecutionMode',
    'State',
    'StateManager',
    'detect_project_extensions',
    'get_installed_extensions',
]
