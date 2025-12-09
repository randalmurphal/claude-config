"""Unit tests for cc_orchestrations.core.workspace.

Tests the PULL-based context management system.
"""

from pathlib import Path

import pytest

from cc_orchestrations.core.manifest import ComponentDef, Manifest
from cc_orchestrations.core.workspace import (
    AGENT_WORKSPACE_DEFAULTS,
    INDEX_TEMPLATE,
    SECTION_MAPPINGS,
    Workspace,
    WorkspaceConfig,
    create_workspace,
)


@pytest.fixture
def temp_worktree(tmp_path: Path) -> Path:
    """Create a temporary worktree directory."""
    worktree = tmp_path / 'worktree'
    worktree.mkdir()
    return worktree


@pytest.fixture
def sample_manifest() -> Manifest:
    """Create a sample manifest for testing."""
    return Manifest(
        name='test-feature',
        project='test-project',
        work_dir='/tmp/test',
        spec_dir='/tmp/test/.spec',
        components=[
            ComponentDef(
                id='component_a',
                file='src/component_a.py',
                depends_on=[],
                purpose='Main component',
                notes='Start here',
            ),
            ComponentDef(
                id='component_b',
                file='src/component_b.py',
                depends_on=['component_a'],
                purpose='Secondary component',
                notes='Depends on A',
            ),
        ],
    )


@pytest.fixture
def sample_spec_content() -> str:
    """Sample SPEC.md content for testing."""
    return """# Feature Implementation

## Overview
This is a test feature implementation.

## Requirements
- REQ-1: Must do X
- REQ-2: Must do Y

## Architecture
Use the existing patterns in the codebase.

### Technical Approach
Implement using standard patterns.

## Components
- component_a.py: Main logic
- component_b.py: Helper functions

## Testing
- Unit tests required
- Integration tests for API

## Gotchas
- Watch out for edge case X
- Handle null values carefully
"""


class TestWorkspaceConfig:
    """Tests for WorkspaceConfig dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = WorkspaceConfig()
        assert config.inject_index is True
        assert config.inject_overview is True
        assert config.inject_component is True
        assert config.additional_sections == []

    def test_custom_config(self):
        """Test custom configuration."""
        config = WorkspaceConfig(
            inject_overview=False,
            additional_sections=['architecture', 'testing'],
        )
        assert config.inject_overview is False
        assert 'architecture' in config.additional_sections


class TestAgentWorkspaceDefaults:
    """Tests for AGENT_WORKSPACE_DEFAULTS."""

    def test_skeleton_builder_has_architecture(self):
        """Skeleton builder should include architecture section."""
        config = AGENT_WORKSPACE_DEFAULTS['skeleton_builder']
        assert 'architecture' in config.additional_sections

    def test_validator_has_testing_and_gotchas(self):
        """Validator should include testing and gotchas."""
        config = AGENT_WORKSPACE_DEFAULTS['validator']
        assert 'testing' in config.additional_sections
        assert 'gotchas' in config.additional_sections

    def test_fix_executor_minimal_context(self):
        """Fix executor should have minimal context."""
        config = AGENT_WORKSPACE_DEFAULTS['fix_executor']
        assert config.inject_overview is False

    def test_spec_parser_minimal(self):
        """Spec parser needs minimal injection."""
        config = AGENT_WORKSPACE_DEFAULTS['spec_parser']
        assert config.inject_overview is False
        assert config.inject_component is False


class TestWorkspaceInit:
    """Tests for Workspace initialization."""

    def test_workspace_creation(self, temp_worktree: Path):
        """Test basic workspace creation."""
        workspace = Workspace(temp_worktree)
        assert workspace.worktree_path == temp_worktree
        assert workspace.root == temp_worktree / '.workspace'
        assert workspace.spec_dir == temp_worktree / '.workspace' / 'spec'
        assert (
            workspace.components_dir
            == temp_worktree / '.workspace' / 'components'
        )

    def test_not_initialized_before_init(self, temp_worktree: Path):
        """Workspace should not be initialized before calling initialize()."""
        workspace = Workspace(temp_worktree)
        assert workspace.is_initialized is False

    def test_is_initialized_after_init(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """Workspace should be initialized after calling initialize()."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)
        assert workspace.is_initialized is True
        assert (temp_worktree / '.workspace' / 'INDEX.md').exists()


class TestWorkspaceInitialize:
    """Tests for Workspace.initialize()."""

    def test_creates_directory_structure(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """initialize() should create the workspace directory structure."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)

        assert workspace.root.exists()
        assert workspace.spec_dir.exists()
        assert workspace.components_dir.exists()

    def test_creates_index_file(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """initialize() should create INDEX.md."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)

        index_file = workspace.root / 'INDEX.md'
        assert index_file.exists()
        content = index_file.read_text()
        assert 'Workspace Navigation' in content

    def test_creates_spec_sections(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """initialize() should parse spec into section files."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)

        # Check that spec section files exist
        assert (workspace.spec_dir / 'OVERVIEW.md').exists()
        assert (workspace.spec_dir / 'requirements.md').exists()
        assert (workspace.spec_dir / 'architecture.md').exists()
        assert (workspace.spec_dir / 'components.md').exists()
        assert (workspace.spec_dir / 'testing.md').exists()
        assert (workspace.spec_dir / 'gotchas.md').exists()

    def test_creates_component_files(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """initialize() should create component context files."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)

        # Check component files
        assert (workspace.components_dir / 'component_a.md').exists()
        assert (workspace.components_dir / 'component_b.md').exists()

        # Check content
        comp_a = (workspace.components_dir / 'component_a.md').read_text()
        assert 'component_a' in comp_a
        assert 'PENDING' in comp_a
        assert 'Main component' in comp_a

    def test_creates_shared_files(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """initialize() should create shared knowledge files."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)

        assert (workspace.root / 'DISCOVERIES.md').exists()
        assert (workspace.root / 'DECISIONS.md').exists()
        assert (workspace.root / 'BLOCKERS.md').exists()

    def test_project_context_included_in_overview(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """initialize() should include project context in OVERVIEW.md."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(
            sample_manifest,
            sample_spec_content,
            project_context='This is a Python project using FastAPI.',
        )

        overview = (workspace.spec_dir / 'OVERVIEW.md').read_text()
        assert 'Project Context' in overview
        assert 'FastAPI' in overview


class TestWorkspaceSpecParsing:
    """Tests for spec parsing into sections."""

    def test_requirements_section_extracted(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """Requirements section should be extracted."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)

        requirements = (workspace.spec_dir / 'requirements.md').read_text()
        assert 'REQ-1' in requirements
        assert 'REQ-2' in requirements

    def test_architecture_section_extracted(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """Architecture section should be extracted."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)

        architecture = (workspace.spec_dir / 'architecture.md').read_text()
        assert 'existing patterns' in architecture

    def test_unmatched_sections_go_to_overview(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
    ):
        """Sections that don't match known patterns go to overview."""
        spec_content = """# My Feature

## Random Section
This is random content.

## Another Unknown
More random stuff.
"""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, spec_content)

        overview = (workspace.spec_dir / 'OVERVIEW.md').read_text()
        assert 'Random Section' in overview or 'random content' in overview

    def test_spec_with_no_headers(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
    ):
        """Spec without headers should go to overview."""
        spec_content = 'Just some text without any headers.'

        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, spec_content)

        overview = (workspace.spec_dir / 'OVERVIEW.md').read_text()
        assert 'without any headers' in overview


class TestWorkspaceContextRetrieval:
    """Tests for context retrieval methods."""

    @pytest.fixture
    def initialized_workspace(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ) -> Workspace:
        """Create an initialized workspace."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)
        return workspace

    def test_get_context_for_skeleton_builder(
        self,
        initialized_workspace: Workspace,
    ):
        """skeleton_builder should get index + overview + architecture."""
        context = initialized_workspace.get_context_for_agent(
            'skeleton_builder',
            'component_a',
        )

        assert 'Workspace Navigation' in context
        assert 'architecture' in context.lower()

    def test_get_context_for_validator(
        self,
        initialized_workspace: Workspace,
    ):
        """validator should get index + overview + testing + gotchas."""
        context = initialized_workspace.get_context_for_agent(
            'validator',
            'component_a',
        )

        assert 'Workspace Navigation' in context
        # Testing section should be included
        assert 'testing' in context.lower() or 'Unit tests' in context

    def test_get_context_for_fix_executor(
        self,
        initialized_workspace: Workspace,
    ):
        """fix_executor should get minimal context (just index)."""
        context = initialized_workspace.get_context_for_agent('fix_executor')

        assert 'Workspace Navigation' in context
        # fix_executor has inject_overview=False, so should not include OVERVIEW content
        # It should only include the INDEX.md
        # Verify by checking no section separators between content blocks
        # (the '---\n\n' pattern is used to separate injected sections)
        assert '\n\n---\n\n' not in context

    def test_get_context_with_component(
        self,
        initialized_workspace: Workspace,
    ):
        """Context should include component context when component_id provided."""
        context = initialized_workspace.get_context_for_agent(
            'implementation_executor',
            'component_a',
        )

        assert 'component_a' in context

    def test_get_context_with_config_override(
        self,
        initialized_workspace: Workspace,
    ):
        """Config override should be respected."""
        custom_config = WorkspaceConfig(
            inject_index=True,
            inject_overview=False,
            inject_component=False,
            additional_sections=['gotchas'],
        )

        context = initialized_workspace.get_context_for_agent(
            'any_agent',
            config_override=custom_config,
        )

        assert 'Workspace Navigation' in context
        # gotchas should be included
        assert 'gotchas' in context.lower() or 'edge case' in context.lower()

    def test_get_navigation_header(
        self,
        initialized_workspace: Workspace,
    ):
        """get_navigation_header() should return just INDEX.md content."""
        header = initialized_workspace.get_navigation_header()
        assert 'Workspace Navigation' in header
        assert 'Read files with the Read tool' in header

    def test_get_component_context(
        self,
        initialized_workspace: Workspace,
    ):
        """get_component_context() should return component file content."""
        context = initialized_workspace.get_component_context('component_a')
        assert 'component_a' in context
        assert 'Main component' in context

    def test_get_spec_section(
        self,
        initialized_workspace: Workspace,
    ):
        """get_spec_section() should return section content."""
        requirements = initialized_workspace.get_spec_section('requirements')
        assert 'REQ-1' in requirements

        # Also works with .md extension
        architecture = initialized_workspace.get_spec_section('architecture.md')
        assert 'architecture' in architecture.lower() or len(architecture) > 0

    def test_list_components(
        self,
        initialized_workspace: Workspace,
    ):
        """list_components() should return component IDs."""
        components = initialized_workspace.list_components()
        assert 'component_a' in components
        assert 'component_b' in components


class TestWorkspaceUpdates:
    """Tests for context update methods."""

    @pytest.fixture
    def initialized_workspace(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ) -> Workspace:
        """Create an initialized workspace."""
        workspace = Workspace(temp_worktree)
        workspace.initialize(sample_manifest, sample_spec_content)
        return workspace

    def test_append_discovery(
        self,
        initialized_workspace: Workspace,
    ):
        """append_discovery() should add to DISCOVERIES.md."""
        initialized_workspace.append_discovery(
            'Found existing pattern in utils.py',
            'skeleton_builder',
        )

        discoveries = initialized_workspace.get_all_discoveries()
        assert 'existing pattern' in discoveries
        assert 'skeleton_builder' in discoveries

    def test_append_decision(
        self,
        initialized_workspace: Workspace,
    ):
        """append_decision() should add to DECISIONS.md."""
        initialized_workspace.append_decision(
            'Use dataclass instead of dict',
            'Better type safety and IDE support',
            'investigator',
        )

        decisions = initialized_workspace.get_all_decisions()
        assert 'dataclass' in decisions
        assert 'type safety' in decisions

    def test_update_blocker(
        self,
        initialized_workspace: Workspace,
    ):
        """update_blocker() should update BLOCKERS.md."""
        initialized_workspace.update_blocker('Missing config file')

        blockers = (initialized_workspace.root / 'BLOCKERS.md').read_text()
        assert 'Missing config file' in blockers
        assert 'BLOCKING' in blockers

    def test_update_blocker_resolved(
        self,
        initialized_workspace: Workspace,
    ):
        """update_blocker() with resolved=True should mark as resolved."""
        initialized_workspace.update_blocker('Fixed the issue', resolved=True)

        blockers = (initialized_workspace.root / 'BLOCKERS.md').read_text()
        assert 'RESOLVED' in blockers

    def test_update_component_status(
        self,
        initialized_workspace: Workspace,
    ):
        """update_component_status() should update component file."""
        initialized_workspace.update_component_status(
            'component_a',
            'IMPLEMENTING',
            for_next_agent='Continue with validation',
            context='Skeleton complete',
        )

        context = initialized_workspace.get_component_context('component_a')
        assert 'IMPLEMENTING' in context

    def test_update_nonexistent_component(
        self,
        initialized_workspace: Workspace,
    ):
        """update_component_status() should handle missing component gracefully."""
        # Should not raise
        initialized_workspace.update_component_status(
            'nonexistent_component',
            'COMPLETE',
        )


class TestCreateWorkspace:
    """Tests for create_workspace() convenience function."""

    def test_create_workspace(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """create_workspace() should create and initialize workspace."""
        workspace = create_workspace(
            temp_worktree,
            sample_manifest,
            sample_spec_content,
        )

        assert workspace.is_initialized
        assert (temp_worktree / '.workspace' / 'INDEX.md').exists()

    def test_create_workspace_with_project_context(
        self,
        temp_worktree: Path,
        sample_manifest: Manifest,
        sample_spec_content: str,
    ):
        """create_workspace() should include project context."""
        workspace = create_workspace(
            temp_worktree,
            sample_manifest,
            sample_spec_content,
            project_context='Python FastAPI project',
        )

        overview = (workspace.spec_dir / 'OVERVIEW.md').read_text()
        assert 'FastAPI' in overview


class TestSectionMappings:
    """Tests for SECTION_MAPPINGS configuration."""

    def test_requirements_keywords(self):
        """Requirements section should have correct keywords."""
        for keywords, filename in SECTION_MAPPINGS:
            if filename == 'requirements.md':
                assert 'requirements' in keywords
                break
        else:
            pytest.fail('requirements.md mapping not found')

    def test_architecture_keywords(self):
        """Architecture section should have correct keywords."""
        for keywords, filename in SECTION_MAPPINGS:
            if filename == 'architecture.md':
                assert 'architecture' in keywords
                assert 'technical' in keywords
                break
        else:
            pytest.fail('architecture.md mapping not found')

    def test_gotchas_keywords(self):
        """Gotchas section should have correct keywords."""
        for keywords, filename in SECTION_MAPPINGS:
            if filename == 'gotchas.md':
                assert 'gotchas' in keywords
                assert 'edge cases' in keywords
                break
        else:
            pytest.fail('gotchas.md mapping not found')


class TestIndexTemplate:
    """Tests for INDEX_TEMPLATE."""

    def test_template_has_navigation_header(self):
        """Template should have navigation header."""
        assert 'Workspace Navigation' in INDEX_TEMPLATE

    def test_template_has_spec_sections_table(self):
        """Template should list spec sections."""
        assert 'OVERVIEW.md' in INDEX_TEMPLATE
        assert 'requirements.md' in INDEX_TEMPLATE
        assert 'architecture.md' in INDEX_TEMPLATE

    def test_template_has_instructions(self):
        """Template should include instructions for agents."""
        assert 'Read files' in INDEX_TEMPLATE or 'Read tool' in INDEX_TEMPLATE
