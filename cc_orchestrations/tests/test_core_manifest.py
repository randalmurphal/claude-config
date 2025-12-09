"""Unit tests for cc_orchestrations.core.manifest.

Tests Manifest, ComponentDef, ExecutionConfig, and QualityConfig dataclasses.
"""

import json
from pathlib import Path

import pytest

from cc_orchestrations.core.manifest import (
    ComponentDef,
    ExecutionConfig,
    Manifest,
    QualityConfig,
)


class TestComponentDef:
    """Tests for ComponentDef dataclass."""

    def test_basic_creation(self):
        """Test basic component creation."""
        comp = ComponentDef(
            id='my_component',
            file='src/my_component.py',
        )

        assert comp.id == 'my_component'
        assert comp.file == 'src/my_component.py'
        assert comp.depends_on == []
        assert comp.complexity == 'medium'

    def test_full_creation(self):
        """Test component with all fields."""
        comp = ComponentDef(
            id='my_component',
            file='src/my_component.py',
            depends_on=['base', 'utils'],
            complexity='high',
            purpose='Main logic handler',
            context_file='context/my_component.md',
            notes='Watch out for edge cases',
        )

        assert comp.depends_on == ['base', 'utils']
        assert comp.complexity == 'high'
        assert comp.purpose == 'Main logic handler'

    def test_to_dict(self):
        """Test serialization to dict."""
        comp = ComponentDef(
            id='test',
            file='test.py',
            depends_on=['a', 'b'],
            complexity='low',
        )

        d = comp.to_dict()

        assert d['id'] == 'test'
        assert d['file'] == 'test.py'
        assert d['depends_on'] == ['a', 'b']
        assert d['complexity'] == 'low'

    def test_from_dict(self):
        """Test deserialization from dict."""
        d = {
            'id': 'test',
            'file': 'test.py',
            'depends_on': ['a'],
            'complexity': 'high',
            'purpose': 'Test purpose',
        }

        comp = ComponentDef.from_dict(d)

        assert comp.id == 'test'
        assert comp.file == 'test.py'
        assert comp.depends_on == ['a']
        assert comp.complexity == 'high'
        assert comp.purpose == 'Test purpose'

    def test_from_dict_defaults(self):
        """Test from_dict with minimal data."""
        d = {'id': 'test', 'file': 'test.py'}

        comp = ComponentDef.from_dict(d)

        assert comp.depends_on == []
        assert comp.complexity == 'medium'
        assert comp.purpose == ''


class TestExecutionConfig:
    """Tests for ExecutionConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = ExecutionConfig()

        assert config.mode == 'standard'
        assert config.parallel_components is False
        assert config.reviewers == 2
        assert config.require_tests is True
        assert config.voting_gates == []

    def test_custom_values(self):
        """Test custom configuration."""
        config = ExecutionConfig(
            mode='full',
            parallel_components=True,
            reviewers=3,
            voting_gates=['production_ready'],
        )

        assert config.mode == 'full'
        assert config.parallel_components is True
        assert config.reviewers == 3
        assert 'production_ready' in config.voting_gates

    def test_to_dict(self):
        """Test serialization."""
        config = ExecutionConfig(mode='quick', reviewers=1)
        d = config.to_dict()

        assert d['mode'] == 'quick'
        assert d['reviewers'] == 1

    def test_from_dict(self):
        """Test deserialization."""
        d = {
            'mode': 'full',
            'parallel_components': True,
            'reviewers': 4,
        }

        config = ExecutionConfig.from_dict(d)

        assert config.mode == 'full'
        assert config.parallel_components is True
        assert config.reviewers == 4


class TestQualityConfig:
    """Tests for QualityConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = QualityConfig()

        assert config.coverage_target == 80
        assert config.lint_required is True
        assert config.security_scan is False

    def test_custom_values(self):
        """Test custom configuration."""
        config = QualityConfig(
            coverage_target=95,
            lint_required=False,
            security_scan=True,
        )

        assert config.coverage_target == 95
        assert config.security_scan is True

    def test_to_dict(self):
        """Test serialization."""
        config = QualityConfig(coverage_target=90)
        d = config.to_dict()

        assert d['coverage_target'] == 90

    def test_from_dict(self):
        """Test deserialization."""
        d = {
            'coverage_target': 85,
            'lint_required': False,
        }

        config = QualityConfig.from_dict(d)

        assert config.coverage_target == 85
        assert config.lint_required is False


class TestManifest:
    """Tests for Manifest dataclass."""

    def test_basic_creation(self):
        """Test basic manifest creation."""
        manifest = Manifest(
            name='test-feature',
            project='test-project',
            work_dir='/tmp/work',
            spec_dir='/tmp/spec',
        )

        assert manifest.name == 'test-feature'
        assert manifest.project == 'test-project'
        assert manifest.work_dir == '/tmp/work'
        assert manifest.spec_dir == '/tmp/spec'

    def test_defaults(self):
        """Test default values."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir='/tmp',
        )

        assert manifest.complexity == 5
        assert manifest.risk_level == 'medium'
        assert manifest.components == []
        assert manifest.gotchas == []
        assert manifest.validation_command == ''

    def test_with_components(self):
        """Test manifest with components."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir='/tmp',
            components=[
                ComponentDef(id='a', file='a.py'),
                ComponentDef(id='b', file='b.py', depends_on=['a']),
            ],
        )

        assert len(manifest.components) == 2
        assert manifest.components[0].id == 'a'
        assert manifest.components[1].depends_on == ['a']

    def test_to_dict(self):
        """Test serialization to dict."""
        manifest = Manifest(
            name='test',
            project='myproject',
            work_dir='/tmp/work',
            spec_dir='/tmp/spec',
            complexity=7,
            components=[ComponentDef(id='a', file='a.py')],
        )

        d = manifest.to_dict()

        assert d['name'] == 'test'
        assert d['project'] == 'myproject'
        assert d['complexity'] == 7
        assert len(d['components']) == 1
        assert d['components'][0]['id'] == 'a'

    def test_from_dict(self):
        """Test deserialization from dict."""
        d = {
            'name': 'test',
            'project': 'myproject',
            'work_dir': '/tmp/work',
            'spec_dir': '/tmp/spec',
            'complexity': 8,
            'risk_level': 'high',
            'components': [
                {'id': 'a', 'file': 'a.py'},
                {'id': 'b', 'file': 'b.py', 'depends_on': ['a']},
            ],
            'execution': {'mode': 'full', 'reviewers': 3},
            'quality': {'coverage_target': 90},
        }

        manifest = Manifest.from_dict(d)

        assert manifest.name == 'test'
        assert manifest.complexity == 8
        assert manifest.risk_level == 'high'
        assert len(manifest.components) == 2
        assert manifest.execution.mode == 'full'
        assert manifest.execution.reviewers == 3
        assert manifest.quality.coverage_target == 90


class TestManifestFileOperations:
    """Tests for manifest save/load operations."""

    def test_save_and_load(self, tmp_path: Path):
        """Test saving and loading manifest."""
        spec_dir = tmp_path / 'spec'

        manifest = Manifest(
            name='save-test',
            project='test-project',
            work_dir=str(tmp_path / 'work'),
            spec_dir=str(spec_dir),
            components=[
                ComponentDef(id='a', file='a.py', purpose='Test'),
            ],
        )

        # Save
        manifest.save(spec_dir)
        assert (spec_dir / 'manifest.json').exists()

        # Load
        loaded = Manifest.load(spec_dir)

        assert loaded.name == 'save-test'
        assert loaded.project == 'test-project'
        assert len(loaded.components) == 1
        assert loaded.components[0].id == 'a'

    def test_load_nonexistent(self, tmp_path: Path):
        """Test loading from nonexistent path."""
        with pytest.raises(FileNotFoundError, match='Manifest not found'):
            Manifest.load(tmp_path / 'nonexistent')

    def test_load_invalid_json(self, tmp_path: Path):
        """Test loading invalid JSON."""
        spec_dir = tmp_path / 'spec'
        spec_dir.mkdir()
        (spec_dir / 'manifest.json').write_text('not valid json{')

        with pytest.raises(ValueError, match='Invalid JSON'):
            Manifest.load(spec_dir)

    def test_load_missing_required_field(self, tmp_path: Path):
        """Test loading manifest with missing required field."""
        spec_dir = tmp_path / 'spec'
        spec_dir.mkdir()
        (spec_dir / 'manifest.json').write_text(
            json.dumps(
                {
                    'name': 'test',
                    # Missing project, work_dir, spec_dir
                }
            )
        )

        with pytest.raises(ValueError, match='Missing required field'):
            Manifest.load(spec_dir)

    def test_save_creates_directory(self, tmp_path: Path):
        """Test that save creates directory if needed."""
        spec_dir = tmp_path / 'nested' / 'spec' / 'dir'

        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir=str(spec_dir),
        )

        manifest.save(spec_dir)

        assert spec_dir.exists()
        assert (spec_dir / 'manifest.json').exists()


class TestManifestGetComponent:
    """Tests for get_component method."""

    @pytest.fixture
    def manifest_with_components(self) -> Manifest:
        """Create manifest with components for testing."""
        return Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir='/tmp',
            components=[
                ComponentDef(id='alpha', file='alpha.py'),
                ComponentDef(id='beta', file='beta.py'),
                ComponentDef(id='gamma', file='gamma.py'),
            ],
        )

    def test_get_existing_component(self, manifest_with_components: Manifest):
        """Test getting an existing component."""
        comp = manifest_with_components.get_component('beta')

        assert comp.id == 'beta'
        assert comp.file == 'beta.py'

    def test_get_nonexistent_component(
        self, manifest_with_components: Manifest
    ):
        """Test getting a nonexistent component."""
        with pytest.raises(
            ValueError, match="Component 'nonexistent' not found"
        ):
            manifest_with_components.get_component('nonexistent')

    def test_error_shows_available(self, manifest_with_components: Manifest):
        """Test that error message shows available components."""
        with pytest.raises(ValueError) as exc_info:
            manifest_with_components.get_component('missing')

        assert 'alpha' in str(exc_info.value)
        assert 'beta' in str(exc_info.value)
        assert 'gamma' in str(exc_info.value)


class TestManifestDependencyOrder:
    """Tests for get_dependency_order method."""

    def test_no_dependencies(self):
        """Test with components that have no dependencies."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir='/tmp',
            components=[
                ComponentDef(id='a', file='a.py'),
                ComponentDef(id='b', file='b.py'),
                ComponentDef(id='c', file='c.py'),
            ],
        )

        order = manifest.get_dependency_order()

        # All should be present
        assert set(order) == {'a', 'b', 'c'}

    def test_linear_dependencies(self):
        """Test with linear dependency chain."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir='/tmp',
            components=[
                ComponentDef(id='a', file='a.py'),
                ComponentDef(id='b', file='b.py', depends_on=['a']),
                ComponentDef(id='c', file='c.py', depends_on=['b']),
            ],
        )

        order = manifest.get_dependency_order()

        # a must come before b, b must come before c
        assert order.index('a') < order.index('b')
        assert order.index('b') < order.index('c')

    def test_diamond_dependencies(self):
        """Test with diamond-shaped dependencies."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir='/tmp',
            components=[
                ComponentDef(id='a', file='a.py'),
                ComponentDef(id='b', file='b.py', depends_on=['a']),
                ComponentDef(id='c', file='c.py', depends_on=['a']),
                ComponentDef(id='d', file='d.py', depends_on=['b', 'c']),
            ],
        )

        order = manifest.get_dependency_order()

        # a must come before b and c
        assert order.index('a') < order.index('b')
        assert order.index('a') < order.index('c')
        # b and c must come before d
        assert order.index('b') < order.index('d')
        assert order.index('c') < order.index('d')

    def test_cycle_detection(self):
        """Test that cycles are detected."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir='/tmp',
            components=[
                ComponentDef(id='a', file='a.py', depends_on=['c']),
                ComponentDef(id='b', file='b.py', depends_on=['a']),
                ComponentDef(id='c', file='c.py', depends_on=['b']),
            ],
        )

        with pytest.raises(ValueError, match='Dependency cycle detected'):
            manifest.get_dependency_order()

    def test_unknown_dependency(self):
        """Test that unknown dependencies are caught."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir='/tmp',
            components=[
                ComponentDef(id='a', file='a.py', depends_on=['nonexistent']),
            ],
        )

        with pytest.raises(ValueError, match='depends on unknown component'):
            manifest.get_dependency_order()

    def test_deterministic_order(self):
        """Test that order is deterministic (sorted)."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp',
            spec_dir='/tmp',
            components=[
                ComponentDef(id='z', file='z.py'),
                ComponentDef(id='a', file='a.py'),
                ComponentDef(id='m', file='m.py'),
            ],
        )

        order = manifest.get_dependency_order()

        # Should be alphabetically sorted when no dependencies
        assert order == ['a', 'm', 'z']


class TestManifestResolveWorkDir:
    """Tests for resolve_work_dir method."""

    def test_absolute_path(self):
        """Test with absolute path."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='/tmp/absolute/path',
            spec_dir='/tmp',
        )

        result = manifest.resolve_work_dir()

        assert result == Path('/tmp/absolute/path')

    def test_tilde_expansion(self):
        """Test with tilde path."""
        manifest = Manifest(
            name='test',
            project='test',
            work_dir='~/my-project',
            spec_dir='/tmp',
        )

        result = manifest.resolve_work_dir()

        # Should expand tilde
        assert str(result).startswith(str(Path.home()))
        assert 'my-project' in str(result)
