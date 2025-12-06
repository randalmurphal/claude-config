"""Agent invocation and management."""

from .registry import AgentRegistry, register_agent
from .runner import AgentResult, AgentRunner

__all__ = [
    'AgentRegistry',
    'AgentResult',
    'AgentRunner',
    'register_agent',
]
