"""Unit tests for cc_orchestrations.core.agents.

Tests the AgentLoader and agent definition parsing.
"""

from pathlib import Path

import pytest

from cc_orchestrations.core.agents import (
    AgentDefinition,
    AgentLoader,
    get_agent_loader,
    load_agent_prompt,
)


@pytest.fixture
def temp_agents_dir(tmp_path: Path) -> Path:
    """Create a temporary agents directory."""
    agents_dir = tmp_path / '.claude' / 'agents'
    agents_dir.mkdir(parents=True)
    return agents_dir


@pytest.fixture
def sample_agent_file(temp_agents_dir: Path) -> Path:
    """Create a sample agent definition file."""
    agent_file = temp_agents_dir / 'test-agent.md'
    agent_file.write_text("""---
name: test-agent
description: A test agent for unit testing
tools: Read, Grep, Glob
model: sonnet
---

# Test Agent

This is a test agent prompt.

## Instructions

Do the thing.
""")
    return agent_file


@pytest.fixture
def minimal_agent_file(temp_agents_dir: Path) -> Path:
    """Create a minimal agent definition file."""
    agent_file = temp_agents_dir / 'minimal-agent.md'
    agent_file.write_text("""---
name: minimal
---

Minimal prompt.
""")
    return agent_file


class TestAgentDefinition:
    """Tests for AgentDefinition dataclass."""

    def test_basic_creation(self):
        """Test basic AgentDefinition creation."""
        agent = AgentDefinition(
            name='test-agent',
            description='Test description',
            tools=['Read', 'Grep'],
            model='opus',
            prompt='Do the thing.',
        )

        assert agent.name == 'test-agent'
        assert agent.description == 'Test description'
        assert agent.model == 'opus'
        assert agent.prompt == 'Do the thing.'

    def test_default_values(self):
        """Test default values."""
        agent = AgentDefinition(name='minimal')

        assert agent.description == ''
        assert agent.tools == []
        assert agent.model == 'opus'
        assert agent.prompt == ''
        assert agent.source_file is None

    def test_allowed_tools_from_list(self):
        """Test allowed_tools property with list input."""
        agent = AgentDefinition(
            name='test',
            tools=['Read', 'Grep', 'Glob'],
        )

        assert agent.allowed_tools == ['Read', 'Grep', 'Glob']

    def test_allowed_tools_from_string(self):
        """Test allowed_tools property with string input."""
        agent = AgentDefinition(
            name='test',
            tools='Read, Grep, Glob',  # type: ignore
        )

        assert agent.allowed_tools == ['Read', 'Grep', 'Glob']

    def test_allowed_tools_empty(self):
        """Test allowed_tools with empty tools."""
        agent = AgentDefinition(name='test')
        assert agent.allowed_tools == []


class TestAgentLoader:
    """Tests for AgentLoader."""

    def test_loader_creation(self, tmp_path: Path):
        """Test basic loader creation."""
        loader = AgentLoader(project_dir=tmp_path)

        assert loader.project_agents_dir == tmp_path / '.claude' / 'agents'

    def test_loader_without_project_dir(self):
        """Test loader without project directory."""
        loader = AgentLoader()

        assert loader.project_agents_dir is None
        assert loader.global_agents_dir == Path.home() / '.claude' / 'agents'

    def test_parse_agent_file(
        self,
        tmp_path: Path,
        sample_agent_file: Path,
    ):
        """Test parsing an agent file."""
        loader = AgentLoader(project_dir=tmp_path)
        agent = loader._parse_agent_file(sample_agent_file)

        assert agent is not None
        assert agent.name == 'test-agent'
        assert agent.description == 'A test agent for unit testing'
        assert agent.model == 'sonnet'
        assert 'Read' in agent.allowed_tools
        assert 'Grep' in agent.allowed_tools
        assert 'Test Agent' in agent.prompt
        assert agent.source_file == sample_agent_file

    def test_parse_minimal_agent(
        self,
        tmp_path: Path,
        minimal_agent_file: Path,
    ):
        """Test parsing a minimal agent file."""
        loader = AgentLoader(project_dir=tmp_path)
        agent = loader._parse_agent_file(minimal_agent_file)

        assert agent is not None
        assert agent.name == 'minimal'
        assert agent.model == 'opus'  # Default
        assert agent.prompt == 'Minimal prompt.'

    def test_parse_file_without_frontmatter(self, tmp_path: Path):
        """Test parsing file without frontmatter."""
        bad_file = tmp_path / 'no-frontmatter.md'
        bad_file.write_text('Just some content without frontmatter.')

        loader = AgentLoader(project_dir=tmp_path)
        agent = loader._parse_agent_file(bad_file)

        assert agent is None

    def test_parse_file_with_invalid_yaml(self, tmp_path: Path):
        """Test parsing file with invalid YAML."""
        bad_file = tmp_path / 'bad-yaml.md'
        bad_file.write_text("""---
name: [invalid yaml
---

Content
""")
        loader = AgentLoader(project_dir=tmp_path)
        agent = loader._parse_agent_file(bad_file)

        assert agent is None

    def test_get_agent(
        self,
        tmp_path: Path,
        sample_agent_file: Path,
    ):
        """Test getting an agent by name."""
        loader = AgentLoader(project_dir=tmp_path)
        agent = loader.get('test-agent')

        assert agent is not None
        assert agent.name == 'test-agent'

    def test_get_nonexistent_agent(self, tmp_path: Path):
        """Test getting a nonexistent agent."""
        loader = AgentLoader(project_dir=tmp_path)
        agent = loader.get('nonexistent')

        assert agent is None

    def test_get_prompt(
        self,
        tmp_path: Path,
        sample_agent_file: Path,
    ):
        """Test getting just the prompt."""
        loader = AgentLoader(project_dir=tmp_path)
        prompt = loader.get_prompt('test-agent')

        assert 'Test Agent' in prompt
        assert 'Do the thing' in prompt

    def test_get_prompt_nonexistent(self, tmp_path: Path):
        """Test getting prompt for nonexistent agent."""
        loader = AgentLoader(project_dir=tmp_path)
        prompt = loader.get_prompt('nonexistent')

        assert prompt == ''

    def test_list_agents(
        self,
        tmp_path: Path,
        sample_agent_file: Path,
        minimal_agent_file: Path,
    ):
        """Test listing all agents."""
        loader = AgentLoader(project_dir=tmp_path)
        agents = loader.list_agents()

        assert 'test-agent' in agents
        assert 'minimal' in agents

    def test_get_all(
        self,
        tmp_path: Path,
        sample_agent_file: Path,
    ):
        """Test getting all agents."""
        loader = AgentLoader(project_dir=tmp_path)
        agents = loader.get_all()

        assert 'test-agent' in agents
        assert isinstance(agents['test-agent'], AgentDefinition)

    def test_caching(
        self,
        tmp_path: Path,
        sample_agent_file: Path,
    ):
        """Test that agents are cached after first load."""
        loader = AgentLoader(project_dir=tmp_path)

        # First load
        loader._load_all()
        assert loader._loaded is True

        cache_size = len(loader._cache)

        # Second call should use cache
        loader._load_all()
        assert len(loader._cache) == cache_size


class TestAgentLoaderOverrides:
    """Tests for project agents overriding global agents."""

    def test_project_overrides_global(self, tmp_path: Path):
        """Test that project agents override global agents."""
        # Create global agent
        global_dir = tmp_path / 'global' / 'agents'
        global_dir.mkdir(parents=True)
        (global_dir / 'shared-agent.md').write_text("""---
name: shared-agent
description: Global version
model: opus
---

Global prompt.
""")

        # Create project agent with same name
        project_dir = tmp_path / 'project'
        agents_dir = project_dir / '.claude' / 'agents'
        agents_dir.mkdir(parents=True)
        (agents_dir / 'shared-agent.md').write_text("""---
name: shared-agent
description: Project version
model: sonnet
---

Project prompt.
""")

        loader = AgentLoader(project_dir=project_dir, global_dir=global_dir)
        agent = loader.get('shared-agent')

        assert agent is not None
        assert agent.description == 'Project version'
        assert agent.model == 'sonnet'


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_agent_loader(self, tmp_path: Path):
        """Test get_agent_loader function."""
        loader = get_agent_loader(project_dir=tmp_path, force_new=True)

        assert isinstance(loader, AgentLoader)

    def test_get_agent_loader_singleton(self):
        """Test that get_agent_loader returns same instance."""
        loader1 = get_agent_loader()
        loader2 = get_agent_loader()

        assert loader1 is loader2

    def test_get_agent_loader_force_new(self):
        """Test force_new creates new loader."""
        loader1 = get_agent_loader()
        loader2 = get_agent_loader(force_new=True)

        assert loader1 is not loader2

    def test_load_agent_prompt(
        self,
        tmp_path: Path,
        sample_agent_file: Path,
    ):
        """Test load_agent_prompt function."""
        # Need to force new loader for test isolation
        prompt = load_agent_prompt('test-agent', project_dir=tmp_path)

        # Note: This uses the singleton, so may not find the temp agent
        # unless we force a new loader first
        get_agent_loader(project_dir=tmp_path, force_new=True)
        prompt = load_agent_prompt('test-agent', project_dir=tmp_path)

        assert 'Test Agent' in prompt


class TestAgentFileFormats:
    """Tests for various agent file formats."""

    def test_tools_as_list_in_yaml(self, tmp_path: Path):
        """Test tools specified as YAML list."""
        agents_dir = tmp_path / '.claude' / 'agents'
        agents_dir.mkdir(parents=True)
        (agents_dir / 'list-tools.md').write_text("""---
name: list-tools
tools:
  - Read
  - Grep
  - Glob
---

Prompt.
""")

        loader = AgentLoader(project_dir=tmp_path)
        agent = loader.get('list-tools')

        assert agent is not None
        assert agent.allowed_tools == ['Read', 'Grep', 'Glob']

    def test_name_from_filename(self, tmp_path: Path):
        """Test name derived from filename when not in frontmatter."""
        agents_dir = tmp_path / '.claude' / 'agents'
        agents_dir.mkdir(parents=True)
        (agents_dir / 'filename-based.md').write_text("""---
description: No name specified
---

Prompt.
""")

        loader = AgentLoader(project_dir=tmp_path)
        agent = loader.get('filename-based')

        assert agent is not None
        assert agent.name == 'filename-based'

    def test_multiline_prompt(self, tmp_path: Path):
        """Test agent with multiline prompt."""
        agents_dir = tmp_path / '.claude' / 'agents'
        agents_dir.mkdir(parents=True)
        (agents_dir / 'multiline.md').write_text("""---
name: multiline
---

# Heading

Paragraph one.

Paragraph two.

## Section

More content.
""")

        loader = AgentLoader(project_dir=tmp_path)
        agent = loader.get('multiline')

        assert agent is not None
        assert '# Heading' in agent.prompt
        assert 'Paragraph one' in agent.prompt
        assert '## Section' in agent.prompt
