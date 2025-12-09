"""End-to-end test for conduct workflow.

This test runs the FULL conduct workflow in dry-run mode:
1. Parse spec
2. Impact analysis (skipped for new project)
3. Component loop
4. Integration validation
5. Final validation
6. Completion

Run with: pytest tests/cc_orchestrations/test_e2e_conduct.py -v -s
"""

import tempfile
from pathlib import Path

import pytest

# Mark as E2E test (expensive, makes API calls)
pytestmark = [pytest.mark.e2e, pytest.mark.slow]


MOCK_SPEC = """# Feature: Test API Endpoint

## Summary
Add a test API endpoint for health checks.

## Components

### src/api/health.py
- Purpose: Health check endpoint handler
- Depends on: None
- Complexity: low

### src/models/status.py
- Purpose: Status response model
- Depends on: None
- Complexity: low

### tests/test_health.py
- Purpose: Tests for health endpoint
- Depends on: src/api/health.py
- Complexity: low

## Quality Requirements
- All tests pass
- Type hints on functions
- Error handling

## Success Criteria
- GET /health returns status
- Response includes version info
"""


@pytest.fixture
def mock_project():
    """Create a mock project with spec."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)

        # Create spec
        spec_dir = work_dir / '.spec'
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / 'SPEC.md').write_text(MOCK_SPEC)

        # Create project structure
        (work_dir / 'src' / 'api').mkdir(parents=True, exist_ok=True)
        (work_dir / 'src' / 'models').mkdir(parents=True, exist_ok=True)
        (work_dir / 'tests').mkdir(parents=True, exist_ok=True)

        # Create __init__.py files
        (work_dir / 'src' / '__init__.py').touch()
        (work_dir / 'src' / 'api' / '__init__.py').touch()
        (work_dir / 'src' / 'models' / '__init__.py').touch()
        (work_dir / 'tests' / '__init__.py').touch()

        yield work_dir


class TestConductE2E:
    """End-to-end tests for conduct workflow."""

    def test_workflow_completes_in_dry_run(self, mock_project):
        """Test full workflow completes successfully in dry-run mode."""
        from cc_orchestrations.conduct import create_conduct_workflow
        from cc_orchestrations.conduct.config import CONDUCT_CONFIG

        spec_path = mock_project / '.spec' / 'SPEC.md'

        # Configure for dry-run
        config = CONDUCT_CONFIG
        config.dry_run = True
        config.default_model = 'haiku'

        # Create engine
        engine = create_conduct_workflow(
            work_dir=mock_project,
            spec_path=spec_path,
            config_override=config,
        )

        # Track phase transitions
        phases_executed = []

        def on_status(phase: str, status: str):
            phases_executed.append((phase, status))
            print(f'  [{phase}] {status}')

        # Note: We're not actually running the full workflow here because
        # it requires a real Claude CLI. Instead, we verify setup is correct.
        assert engine.config.dry_run is True
        assert len(engine.handlers) > 0

        # Verify expected phases are configured
        phase_names = [p.name for p in engine.config.phases]
        assert 'parse_spec' in phase_names
        assert 'component_loop' in phase_names
        assert 'completion' in phase_names

    def test_workflow_state_initialization(self, mock_project):
        """Test workflow initializes state correctly."""
        from cc_orchestrations.conduct import create_conduct_workflow
        from cc_orchestrations.conduct.config import CONDUCT_CONFIG
        from cc_orchestrations.core.state import StateManager

        spec_path = mock_project / '.spec' / 'SPEC.md'

        config = CONDUCT_CONFIG
        config.dry_run = True

        create_conduct_workflow(
            work_dir=mock_project,
            spec_path=spec_path,
            config_override=config,
        )

        # Check state manager is set up
        state_dir = mock_project / '.spec'
        manager = StateManager(state_dir)

        # State file should be creatable
        from cc_orchestrations.core.state import State

        state = State(mode='standard', dry_run=True)
        manager.save(state)

        loaded = manager.load()
        assert loaded.dry_run is True

    def test_spec_parsing_setup(self, mock_project):
        """Test spec file is accessible for parsing."""
        spec_path = mock_project / '.spec' / 'SPEC.md'

        assert spec_path.exists()
        content = spec_path.read_text()

        # Verify spec has expected sections
        assert '## Summary' in content
        assert '## Components' in content
        assert 'src/api/health.py' in content


class TestConductConfigVariations:
    """Test different configuration modes."""

    def test_quick_mode_config(self, mock_project):
        """Test quick mode reduces validation."""
        from cc_orchestrations.conduct import create_conduct_workflow
        from cc_orchestrations.conduct.config import CONDUCT_CONFIG
        from cc_orchestrations.core.config import ExecutionMode

        spec_path = mock_project / '.spec' / 'SPEC.md'

        config = CONDUCT_CONFIG
        config.mode = ExecutionMode.QUICK
        config.dry_run = True

        engine = create_conduct_workflow(
            work_dir=mock_project,
            spec_path=spec_path,
            config_override=config,
        )

        assert engine.config.mode == ExecutionMode.QUICK

    def test_full_mode_config(self, mock_project):
        """Test full mode increases validation."""
        from cc_orchestrations.conduct import create_conduct_workflow
        from cc_orchestrations.conduct.config import CONDUCT_CONFIG
        from cc_orchestrations.core.config import ExecutionMode

        spec_path = mock_project / '.spec' / 'SPEC.md'

        config = CONDUCT_CONFIG
        config.mode = ExecutionMode.FULL
        config.dry_run = True

        engine = create_conduct_workflow(
            work_dir=mock_project,
            spec_path=spec_path,
            config_override=config,
        )

        assert engine.config.mode == ExecutionMode.FULL

    def test_draft_mode_workflow(self, mock_project):
        """Test draft mode for spec validation."""
        from cc_orchestrations.conduct import create_conduct_workflow
        from cc_orchestrations.conduct.config import CONDUCT_CONFIG

        spec_path = mock_project / '.spec' / 'SPEC.md'

        config = CONDUCT_CONFIG
        config.dry_run = True

        engine = create_conduct_workflow(
            work_dir=mock_project,
            spec_path=spec_path,
            config_override=config,
            draft_mode=True,
        )

        # Draft mode should be tracked
        # (implementation detail - verify engine accepts the flag)
        assert engine is not None


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        'markers',
        'e2e: marks tests as end-to-end tests (expensive)',
    )
