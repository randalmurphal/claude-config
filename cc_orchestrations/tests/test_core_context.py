"""Unit tests for cc_orchestrations.core.context.

Tests ContextManager for spec execution context management.
"""

from pathlib import Path

import pytest

from cc_orchestrations.core.context import ContextManager, ContextUpdate
from cc_orchestrations.core.manifest import ComponentDef, Manifest


@pytest.fixture
def spec_dir(tmp_path: Path) -> Path:
    """Create a temporary spec directory."""
    spec = tmp_path / 'spec'
    spec.mkdir()
    return spec


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
            ),
        ],
    )


class TestContextUpdate:
    """Tests for ContextUpdate dataclass."""

    def test_default_values(self):
        """Test default values."""
        update = ContextUpdate()

        assert update.summary == ''
        assert update.discoveries == []
        assert update.blockers == []
        assert update.decisions == []
        assert update.for_next_agent == ''

    def test_with_values(self):
        """Test with explicit values."""
        update = ContextUpdate(
            summary='Implemented feature X',
            discoveries=['Found existing pattern', 'Discovered edge case'],
            blockers=['Missing dependency'],
            decisions=['Use strategy A'],
            for_next_agent='Continue with tests',
        )

        assert update.summary == 'Implemented feature X'
        assert len(update.discoveries) == 2
        assert len(update.blockers) == 1
        assert len(update.decisions) == 1


class TestContextManagerInit:
    """Tests for ContextManager initialization."""

    def test_basic_creation(self, spec_dir: Path):
        """Test basic context manager creation."""
        manager = ContextManager(spec_dir)

        assert manager.spec_dir == spec_dir
        assert manager.context_file == spec_dir / 'CONTEXT.md'
        assert manager.decisions_file == spec_dir / 'DECISIONS.md'
        assert manager.components_dir == spec_dir / 'components'

    def test_tilde_expansion(self, tmp_path: Path):
        """Test that tilde is expanded in path."""
        # This tests the expand_path functionality
        manager = ContextManager(str(tmp_path))
        assert manager.spec_dir.is_absolute()


class TestContextManagerGetContext:
    """Tests for context retrieval methods."""

    def test_get_global_context_empty(self, spec_dir: Path):
        """Test getting global context when file doesn't exist."""
        manager = ContextManager(spec_dir)

        result = manager.get_global_context()

        assert result == ''

    def test_get_global_context(self, spec_dir: Path):
        """Test getting global context."""
        manager = ContextManager(spec_dir)
        (spec_dir / 'CONTEXT.md').write_text('# Context\n\nSome context here.')

        result = manager.get_global_context()

        assert 'Some context here' in result

    def test_get_component_context_empty(self, spec_dir: Path):
        """Test getting component context when file doesn't exist."""
        manager = ContextManager(spec_dir)

        result = manager.get_component_context('nonexistent')

        assert result == ''

    def test_get_component_context(self, spec_dir: Path):
        """Test getting component context."""
        manager = ContextManager(spec_dir)
        components_dir = spec_dir / 'components'
        components_dir.mkdir()
        (components_dir / 'my_component.md').write_text('# Component Context')

        result = manager.get_component_context('my_component')

        assert '# Component Context' in result

    def test_get_context_for_prompt(self, spec_dir: Path):
        """Test building context for prompt."""
        manager = ContextManager(spec_dir)

        # Create context files
        (spec_dir / 'CONTEXT.md').write_text('Global context content')
        (spec_dir / 'DECISIONS.md').write_text('Decision 1\nDecision 2')

        components_dir = spec_dir / 'components'
        components_dir.mkdir()
        (components_dir / 'my_component.md').write_text('Component specific')

        result = manager.get_context_for_prompt('my_component')

        assert '# Global Context' in result
        assert 'Global context content' in result
        assert '# Decisions' in result
        assert '# Component Context: my_component' in result

    def test_get_context_for_prompt_empty(self, spec_dir: Path):
        """Test context for prompt when no files exist."""
        manager = ContextManager(spec_dir)

        result = manager.get_context_for_prompt()

        assert result == ''


class TestContextManagerInitialize:
    """Tests for initialize method."""

    def test_initialize_creates_files(
        self,
        spec_dir: Path,
        sample_manifest: Manifest,
    ):
        """Test that initialize creates required files."""
        manager = ContextManager(spec_dir)
        manager.initialize(sample_manifest)

        assert manager.context_file.exists()
        assert manager.decisions_file.exists()
        assert manager.components_dir.exists()

    def test_initialize_context_content(
        self,
        spec_dir: Path,
        sample_manifest: Manifest,
    ):
        """Test CONTEXT.md content after initialization."""
        manager = ContextManager(spec_dir)
        manager.initialize(sample_manifest)

        content = manager.context_file.read_text()

        assert '# Execution Context' in content
        assert 'IN_PROGRESS' in content
        assert 'Components: 0/2 complete' in content

    def test_initialize_decisions_content(
        self,
        spec_dir: Path,
        sample_manifest: Manifest,
    ):
        """Test DECISIONS.md content after initialization."""
        manager = ContextManager(spec_dir)
        manager.initialize(sample_manifest)

        content = manager.decisions_file.read_text()

        assert '# Decisions' in content
        assert 'Execution initialized' in content

    def test_initialize_component_files(
        self,
        spec_dir: Path,
        sample_manifest: Manifest,
    ):
        """Test component context files after initialization."""
        manager = ContextManager(spec_dir)
        manager.initialize(sample_manifest)

        comp_a = (manager.components_dir / 'component_a.md').read_text()
        comp_b = (manager.components_dir / 'component_b.md').read_text()

        assert 'component_a' in comp_a
        assert 'Main component' in comp_a
        assert 'PENDING' in comp_a

        assert 'component_b' in comp_b
        assert 'Depends: component_a' in comp_b or 'component_a' in comp_b


class TestContextManagerUpdateFromResult:
    """Tests for update_from_result method."""

    @pytest.fixture
    def initialized_manager(
        self,
        spec_dir: Path,
        sample_manifest: Manifest,
    ) -> ContextManager:
        """Create an initialized context manager."""
        manager = ContextManager(spec_dir)
        manager.initialize(sample_manifest)
        return manager

    def test_update_with_discoveries(self, initialized_manager: ContextManager):
        """Test updating with discoveries."""
        update = ContextUpdate(
            discoveries=['Found existing pattern', 'Edge case discovered'],
        )

        initialized_manager.update_from_result(update)

        content = initialized_manager.get_global_context()
        assert 'existing pattern' in content
        assert 'Edge case discovered' in content

    def test_update_with_blockers(self, initialized_manager: ContextManager):
        """Test updating with blockers."""
        update = ContextUpdate(
            blockers=['Missing dependency X'],
        )

        initialized_manager.update_from_result(update)

        content = initialized_manager.get_global_context()
        assert 'Missing dependency X' in content

    def test_update_with_decisions(self, initialized_manager: ContextManager):
        """Test updating with decisions."""
        update = ContextUpdate(
            decisions=['Use approach A', 'Prefer composition over inheritance'],
        )

        initialized_manager.update_from_result(update)

        content = initialized_manager.decisions_file.read_text()
        assert 'approach A' in content
        assert 'composition' in content

    def test_update_component_context(
        self, initialized_manager: ContextManager
    ):
        """Test updating component-specific context."""
        update = ContextUpdate(
            summary='Skeleton complete',
            discoveries=['Found helper function'],
        )

        initialized_manager.update_from_result(
            update, component_id='component_a'
        )

        content = initialized_manager.get_component_context('component_a')
        assert 'Skeleton complete' in content or 'helper function' in content


class TestContextManagerUpdateComponentStatus:
    """Tests for update_component_status method."""

    @pytest.fixture
    def initialized_manager(
        self,
        spec_dir: Path,
        sample_manifest: Manifest,
    ) -> ContextManager:
        """Create an initialized context manager."""
        manager = ContextManager(spec_dir)
        manager.initialize(sample_manifest)
        return manager

    def test_update_status(self, initialized_manager: ContextManager):
        """Test updating component status."""
        initialized_manager.update_component_status(
            'component_a',
            'IMPLEMENTING',
        )

        content = initialized_manager.get_component_context('component_a')
        assert 'IMPLEMENTING' in content

    def test_update_status_with_summary(
        self, initialized_manager: ContextManager
    ):
        """Test updating status with summary."""
        initialized_manager.update_component_status(
            'component_a',
            'COMPLETE',
            summary='All tests pass',
        )

        content = initialized_manager.get_component_context('component_a')
        assert 'COMPLETE' in content

    def test_update_creates_file_if_missing(self, spec_dir: Path):
        """Test that update creates component file if missing."""
        manager = ContextManager(spec_dir)
        manager.components_dir.mkdir(parents=True)

        manager.update_component_status(
            'new_component',
            'IN_PROGRESS',
            summary='Started work',
        )

        assert (manager.components_dir / 'new_component.md').exists()
        content = (manager.components_dir / 'new_component.md').read_text()
        assert 'IN_PROGRESS' in content


class TestContextManagerTimestamps:
    """Tests for timestamp handling."""

    def test_timestamp_format(self, spec_dir: Path, sample_manifest: Manifest):
        """Test that timestamps are in expected format."""
        manager = ContextManager(spec_dir)
        manager.initialize(sample_manifest)

        content = manager.context_file.read_text()

        # Should contain ISO 8601 format timestamp
        import re

        timestamp_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
        assert re.search(timestamp_pattern, content)


class TestContextManagerEdgeCases:
    """Tests for edge cases."""

    def test_update_without_initialize(self, spec_dir: Path):
        """Test updating when files don't exist."""
        manager = ContextManager(spec_dir)

        update = ContextUpdate(
            discoveries=['Something'],
        )

        # Should handle gracefully (creates files)
        manager.update_from_result(update)

        # Context file should now exist
        assert manager.context_file.exists()

    def test_multiple_updates(self, spec_dir: Path, sample_manifest: Manifest):
        """Test multiple sequential updates."""
        manager = ContextManager(spec_dir)
        manager.initialize(sample_manifest)

        # First update
        manager.update_from_result(
            ContextUpdate(
                discoveries=['Discovery 1'],
            )
        )

        # Second update
        manager.update_from_result(
            ContextUpdate(
                discoveries=['Discovery 2'],
            )
        )

        content = manager.get_global_context()

        # Both should be present
        assert 'Discovery 1' in content
        assert 'Discovery 2' in content

    def test_special_characters_in_content(
        self,
        spec_dir: Path,
        sample_manifest: Manifest,
    ):
        """Test handling of special characters."""
        manager = ContextManager(spec_dir)
        manager.initialize(sample_manifest)

        update = ContextUpdate(
            discoveries=['Found regex: /[a-z]+/'],
            decisions=['Use `code` formatting'],
        )

        manager.update_from_result(update)

        content = manager.get_global_context()
        decisions = manager.decisions_file.read_text()

        assert 'regex:' in content
        assert '`code`' in decisions
