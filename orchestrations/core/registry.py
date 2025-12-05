"""Agent registry - defines available agent types.

Each agent type has default configuration that can be overridden.
"""

from dataclasses import dataclass, field
from typing import Any

from .config import AgentConfig


@dataclass
class AgentType:
    """Definition of an agent type with defaults."""

    name: str
    description: str
    model: str = 'sonnet'
    schema: str = ''
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    prompt_template: str = ''
    timeout: int = 300

    def to_config(self, **overrides: Any) -> AgentConfig:
        """Convert to AgentConfig with optional overrides."""
        return AgentConfig(
            name=overrides.get('name', self.name),
            model=overrides.get('model', self.model),
            schema=overrides.get('schema', self.schema),
            allowed_tools=overrides.get('allowed_tools', self.allowed_tools),
            disallowed_tools=overrides.get(
                'disallowed_tools', self.disallowed_tools
            ),
            prompt_template=overrides.get(
                'prompt_template', self.prompt_template
            ),
            timeout=overrides.get('timeout', self.timeout),
            description=overrides.get('description', self.description),
        )


class AgentRegistry:
    """Registry of available agent types."""

    def __init__(self):
        self._agents: dict[str, AgentType] = {}

    def register(self, agent: AgentType) -> None:
        """Register an agent type."""
        self._agents[agent.name] = agent

    def get(self, name: str) -> AgentType:
        """Get an agent type by name."""
        if name not in self._agents:
            raise ValueError(f'Unknown agent type: {name}')
        return self._agents[name]

    def list(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def to_configs(self) -> dict[str, AgentConfig]:
        """Convert all agents to configs."""
        return {name: agent.to_config() for name, agent in self._agents.items()}


# Global registry
REGISTRY = AgentRegistry()


def register_agent(agent: AgentType) -> AgentType:
    """Decorator/function to register an agent."""
    REGISTRY.register(agent)
    return agent


# =============================================================================
# DEFAULT AGENT TYPES
# =============================================================================

register_agent(
    AgentType(
        name='spec_parser',
        description='Parse SPEC.md and extract components with dependencies',
        model='sonnet',
        schema='spec_parser',
        allowed_tools=['Read', 'Glob'],
        timeout=120,
    )
)

register_agent(
    AgentType(
        name='impact_analyzer',
        description='Analyze blast radius of changes',
        model='opus',
        schema='impact_analysis',
        allowed_tools=['Read', 'Grep', 'Glob', 'Bash'],
        timeout=180,
    )
)

register_agent(
    AgentType(
        name='skeleton_builder',
        description='Create file structure with signatures only',
        model='sonnet',
        schema='skeleton_builder',
        allowed_tools=['Read', 'Write', 'Glob', 'Grep'],
        disallowed_tools=['Bash'],
        prompt_template='skeleton',
        timeout=300,
    )
)

register_agent(
    AgentType(
        name='test_skeleton_builder',
        description='Create test file structure',
        model='sonnet',
        schema='skeleton_builder',
        allowed_tools=['Read', 'Write', 'Glob'],
        disallowed_tools=['Bash'],
        prompt_template='test_skeleton',
        timeout=300,
    )
)

register_agent(
    AgentType(
        name='implementation_executor',
        description='Fill skeleton stubs with production code',
        model='sonnet',
        schema='implementation',
        allowed_tools=['Read', 'Write', 'Edit', 'Glob', 'Grep'],
        disallowed_tools=['Bash'],
        prompt_template='implement',
        timeout=600,
    )
)

# Read-only bash commands for reviewers (no file modification)
REVIEWER_BASH_ALLOWED = [
    'Bash(git:*)',
    'Bash(grep:*)',
    'Bash(find:*)',
    'Bash(ls:*)',
    'Bash(cat:*)',
    'Bash(head:*)',
    'Bash(tail:*)',
    'Bash(wc:*)',
    'Bash(diff:*)',
    'Bash(python3 -m py_compile:*)',
    'Bash(python3 -m pytest:*)',
]

register_agent(
    AgentType(
        name='validator',
        description='Review code for issues',
        model='sonnet',
        schema='validator',
        allowed_tools=['Read', 'Glob', 'Grep', *REVIEWER_BASH_ALLOWED],
        disallowed_tools=['Write', 'Edit', 'MultiEdit'],
        prompt_template='validate',
        timeout=300,
    )
)

register_agent(
    AgentType(
        name='security_auditor',
        description='Audit code for security vulnerabilities',
        model='sonnet',
        schema='validator',
        allowed_tools=['Read', 'Glob', 'Grep', *REVIEWER_BASH_ALLOWED],
        disallowed_tools=['Write', 'Edit', 'MultiEdit'],
        prompt_template='security_audit',
        timeout=300,
    )
)

register_agent(
    AgentType(
        name='performance_reviewer',
        description='Review code for performance issues',
        model='sonnet',
        schema='validator',
        allowed_tools=['Read', 'Glob', 'Grep', *REVIEWER_BASH_ALLOWED],
        disallowed_tools=['Write', 'Edit', 'MultiEdit'],
        prompt_template='performance_review',
        timeout=300,
    )
)

register_agent(
    AgentType(
        name='fix_executor',
        description='Fix reported issues',
        model='sonnet',
        schema='fix_executor',
        allowed_tools=['Read', 'Write', 'Edit', 'Glob', 'Grep', 'Bash'],
        prompt_template='fix',
        timeout=600,
    )
)

register_agent(
    AgentType(
        name='investigator',
        description='Investigate issues and vote on strategies',
        model='opus',
        schema='',  # Schema varies by voting gate
        allowed_tools=['Read', 'Glob', 'Grep', 'Bash'],
        timeout=300,
    )
)

register_agent(
    AgentType(
        name='test_runner',
        description='Run tests and report results',
        model='sonnet',
        schema='test_runner',
        allowed_tools=['Bash', 'Read'],
        timeout=600,
    )
)
