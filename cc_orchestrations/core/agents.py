"""Agent definition loader - reads .claude/agents/*.md files.

These agent definitions are shared between:
- Claude Code's Task tool (subagent_type)
- cc_orchestrations AgentRunner

This ensures prompts live in one place and both systems use them.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

LOG = logging.getLogger(__name__)


@dataclass
class AgentDefinition:
    """Parsed agent definition from .claude/agents/*.md file.

    Attributes:
        name: Agent name (from frontmatter)
        description: Brief description (from frontmatter)
        tools: List of allowed tools (from frontmatter)
        model: Model to use (from frontmatter, default: opus)
        prompt: The full prompt body (markdown after frontmatter)
        source_file: Path to the source .md file
    """

    name: str
    description: str = ''
    tools: list[str] = field(default_factory=list)
    model: str = 'opus'
    prompt: str = ''
    source_file: Path | None = None

    @property
    def allowed_tools(self) -> list[str]:
        """Convert tools string to list."""
        if isinstance(self.tools, str):
            return [t.strip() for t in self.tools.split(',') if t.strip()]
        return self.tools or []


class AgentLoader:
    """Loads agent definitions from .claude/agents/ directories.

    Searches multiple locations:
    1. Project-specific: <project>/.claude/agents/
    2. Global: ~/.claude/agents/

    Project-specific agents override global ones.
    """

    def __init__(
        self,
        project_dir: Path | None = None,
        global_dir: Path | None = None,
    ):
        """Initialize agent loader.

        Args:
            project_dir: Project root (containing .claude/agents/)
            global_dir: Global agents dir (typically ~/.claude/agents/)
        """
        self.project_agents_dir = (
            project_dir / '.claude' / 'agents' if project_dir else None
        )
        self.global_agents_dir = (
            global_dir or Path.home() / '.claude' / 'agents'
        )
        self._cache: dict[str, AgentDefinition] = {}
        self._loaded = False

    def _parse_agent_file(self, file_path: Path) -> AgentDefinition | None:
        """Parse a single agent definition file.

        Expected format:
        ```
        ---
        name: agent-name
        description: Brief description
        tools: Read, Grep, Glob
        model: opus
        ---

        # Agent Name

        Prompt content here...
        ```

        Args:
            file_path: Path to .md file

        Returns:
            AgentDefinition or None if parse fails
        """
        try:
            content = file_path.read_text()
        except OSError as e:
            LOG.warning(f'Failed to read agent file {file_path}: {e}')
            return None

        # Extract frontmatter
        frontmatter_match = re.match(
            r'^---\s*\n(.*?)\n---\s*\n(.*)$',
            content,
            re.DOTALL,
        )

        if not frontmatter_match:
            LOG.warning(f'No frontmatter found in {file_path}')
            return None

        frontmatter_str = frontmatter_match.group(1)
        prompt_body = frontmatter_match.group(2).strip()

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_str) or {}
        except yaml.YAMLError as e:
            LOG.warning(f'Invalid YAML in {file_path}: {e}')
            return None

        name = frontmatter.get('name', file_path.stem)

        # Parse tools - can be string or list
        tools_raw = frontmatter.get('tools', [])
        if isinstance(tools_raw, str):
            tools = [t.strip() for t in tools_raw.split(',') if t.strip()]
        else:
            tools = tools_raw or []

        return AgentDefinition(
            name=name,
            description=frontmatter.get('description', ''),
            tools=tools,
            model=frontmatter.get('model', 'opus'),
            prompt=prompt_body,
            source_file=file_path,
        )

    def _load_all(self) -> None:
        """Load all agent definitions from search paths.

        Global agents are loaded first, then project-specific override.
        """
        if self._loaded:
            return

        # Load global agents first
        if self.global_agents_dir and self.global_agents_dir.exists():
            for file_path in self.global_agents_dir.glob('*.md'):
                agent = self._parse_agent_file(file_path)
                if agent:
                    self._cache[agent.name] = agent
                    LOG.debug(f'Loaded global agent: {agent.name}')

        # Load project agents (override global)
        if self.project_agents_dir and self.project_agents_dir.exists():
            for file_path in self.project_agents_dir.glob('*.md'):
                agent = self._parse_agent_file(file_path)
                if agent:
                    if agent.name in self._cache:
                        LOG.debug(
                            f'Project agent {agent.name} overrides global'
                        )
                    self._cache[agent.name] = agent
                    LOG.debug(f'Loaded project agent: {agent.name}')

        self._loaded = True
        LOG.info(f'Loaded {len(self._cache)} agent definitions')

    def get(self, name: str) -> AgentDefinition | None:
        """Get an agent definition by name.

        Args:
            name: Agent name (e.g., 'finding-validator')

        Returns:
            AgentDefinition or None if not found
        """
        self._load_all()
        return self._cache.get(name)

    def get_prompt(self, name: str) -> str:
        """Get just the prompt for an agent.

        Args:
            name: Agent name

        Returns:
            Prompt string or empty if not found
        """
        agent = self.get(name)
        return agent.prompt if agent else ''

    def list_agents(self) -> list[str]:
        """List all available agent names.

        Returns:
            List of agent names
        """
        self._load_all()
        return list(self._cache.keys())

    def get_all(self) -> dict[str, AgentDefinition]:
        """Get all loaded agent definitions.

        Returns:
            Dict of name -> AgentDefinition
        """
        self._load_all()
        return self._cache.copy()


# Singleton instance for convenience
_default_loader: AgentLoader | None = None


def get_agent_loader(
    project_dir: Path | None = None,
    force_new: bool = False,
) -> AgentLoader:
    """Get or create the default agent loader.

    Args:
        project_dir: Project root directory
        force_new: Force creation of new loader

    Returns:
        AgentLoader instance
    """
    global _default_loader

    if _default_loader is None or force_new:
        _default_loader = AgentLoader(project_dir=project_dir)

    return _default_loader


def load_agent_prompt(name: str, project_dir: Path | None = None) -> str:
    """Convenience function to load an agent's prompt.

    Args:
        name: Agent name
        project_dir: Project root directory

    Returns:
        Prompt string or empty if not found
    """
    loader = get_agent_loader(project_dir)
    return loader.get_prompt(name)
