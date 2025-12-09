"""Integration tests using dry-run mode with haiku.

These tests make actual API calls but use:
- dry_run=True (agents return mock/test data)
- haiku model (fast and cheap)

Run with: pytest tests/cc_orchestrations/test_integration_dry_run.py -v
Skip with: pytest -m "not integration"
"""

import os
import tempfile
from pathlib import Path

import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def work_dir():
    """Create temporary work directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config():
    """Create test config with dry-run enabled."""
    from cc_orchestrations.core.config import Config

    claude_path = os.path.expanduser('~/.claude/local/claude')
    return Config(
        name='integration-test',
        dry_run=True,
        claude_path=claude_path,
        default_model='haiku',
    )


@pytest.fixture
def runner(config, work_dir):
    """Create AgentRunner for tests."""
    from cc_orchestrations.core.runner import AgentRunner

    return AgentRunner(
        config=config,
        work_dir=work_dir,
        dry_run=True,
    )


class TestRunnerDryRun:
    """Integration tests for AgentRunner in dry-run mode."""

    def test_simple_agent_call(self, runner):
        """Test basic agent call returns mock data."""
        result = runner.run(
            agent_name='test-agent',
            prompt='Return JSON: {"status": "ok", "message": "test passed"}',
            dry_run=True,
            show_progress=False,
        )

        assert result.success, f'Agent failed: {result.error}'
        assert result.duration > 0
        # Dry-run should return some data
        assert result.data is not None or result.raw_output

    def test_agent_with_json_output(self, runner):
        """Test agent returns parseable JSON in dry-run."""
        result = runner.run(
            agent_name='json-test',
            prompt="""Return exactly this JSON:
{
    "status": "pass",
    "findings": [],
    "summary": "No issues found"
}""",
            dry_run=True,
            show_progress=False,
        )

        assert result.success, f'Agent failed: {result.error}'
        # In dry-run, agent should attempt to follow instructions
        if result.data:
            assert 'status' in result.data or 'findings' in result.data

    def test_agent_timeout_respected(self, runner):
        """Test that timeout configuration is respected."""
        # This shouldn't take long in dry-run mode
        result = runner.run(
            agent_name='timeout-test',
            prompt='Quick test',
            dry_run=True,
            show_progress=False,
            timeout=30,  # Short timeout
        )

        # Should complete within timeout
        assert result.duration < 30

    def test_multiple_sequential_calls(self, runner):
        """Test multiple agent calls work sequentially."""
        results = []
        for i in range(3):
            result = runner.run(
                agent_name=f'seq-test-{i}',
                prompt=f'Test call {i}',
                dry_run=True,
                show_progress=False,
            )
            results.append(result)

        # All should succeed
        for i, result in enumerate(results):
            assert result.success, f'Call {i} failed: {result.error}'


class TestStatePersistence:
    """Integration tests for state persistence across operations."""

    def test_state_survives_restart(self, work_dir):
        """Test state persists to disk and can be reloaded."""
        from cc_orchestrations.core.state import (
            PhaseStatus,
            State,
            StateManager,
        )

        state_dir = work_dir / '.spec'

        # First manager - save state
        manager1 = StateManager(state_dir)
        state = State(mode='full', dry_run=True)
        state.current_phase = 'investigation'
        state.phase_status = PhaseStatus.IN_PROGRESS
        manager1.save(state)

        # Second manager - load state (simulates restart)
        manager2 = StateManager(state_dir)
        loaded = manager2.load()

        assert loaded.mode == 'full'
        assert loaded.dry_run is True
        assert loaded.current_phase == 'investigation'
        assert loaded.phase_status == PhaseStatus.IN_PROGRESS

    def test_checkpoint_restore_cycle(self, work_dir):
        """Test full checkpoint/restore cycle."""
        from cc_orchestrations.core.state import State, StateManager

        state_dir = work_dir / '.spec'
        manager = StateManager(state_dir)

        # Phase 1
        state = State()
        state.current_phase = 'phase1'
        state.discoveries.append('Found issue A')
        manager.save(state)
        manager.checkpoint_phase('phase1', 'complete')

        # Phase 2
        state.current_phase = 'phase2'
        state.discoveries.append('Found issue B')
        manager.save(state)
        manager.checkpoint_phase('phase2', 'complete')

        # Phase 3 (current)
        state.current_phase = 'phase3'
        manager.save(state)

        # Restore to phase 1
        restored = manager.load_checkpoint('phase_phase1_complete')
        assert restored.current_phase == 'phase1'
        assert 'Found issue A' in restored.discoveries
        assert 'Found issue B' not in restored.discoveries


class TestWorkflowConfig:
    """Integration tests for workflow configuration."""

    def test_conduct_config_loads(self):
        """Test conduct workflow config can be created."""
        from cc_orchestrations.conduct.config import CONDUCT_CONFIG

        assert CONDUCT_CONFIG is not None
        assert len(CONDUCT_CONFIG.phases) > 0
        assert 'parse_spec' in [p.name for p in CONDUCT_CONFIG.phases]

    def test_pr_review_config_loads(self):
        """Test PR review config can be created."""
        from cc_orchestrations.pr_review.config import create_default_config

        config = create_default_config()
        assert config is not None
        assert len(config.agents) > 0


class TestWorkflowEngineSetup:
    """Integration tests for workflow engine initialization."""

    def test_conduct_workflow_creation(self, work_dir):
        """Test conduct workflow engine can be created."""
        from cc_orchestrations.conduct import create_conduct_workflow

        # Create spec file
        spec_dir = work_dir / '.spec'
        spec_dir.mkdir(parents=True, exist_ok=True)
        spec_path = spec_dir / 'SPEC.md'
        spec_path.write_text("""# Test Spec

## Summary
Test feature

## Components

### src/test.py
- Purpose: Test file
- Depends on: None
- Complexity: low
""")

        # Create workflow
        engine = create_conduct_workflow(
            work_dir=work_dir,
            spec_path=spec_path,
        )

        assert engine is not None
        assert engine.config is not None
        assert len(engine.handlers) > 0

    def test_conduct_workflow_with_dry_run(self, work_dir):
        """Test conduct workflow respects dry-run flag."""
        from cc_orchestrations.conduct import create_conduct_workflow
        from cc_orchestrations.conduct.config import CONDUCT_CONFIG

        # Create spec
        spec_dir = work_dir / '.spec'
        spec_dir.mkdir(parents=True, exist_ok=True)
        spec_path = spec_dir / 'SPEC.md'
        spec_path.write_text('# Minimal spec\n\n## Summary\nTest')

        # Enable dry-run
        config = CONDUCT_CONFIG
        config.dry_run = True

        engine = create_conduct_workflow(
            work_dir=work_dir,
            spec_path=spec_path,
            config_override=config,
        )

        assert engine.config.dry_run is True


# Skip marker for expensive tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        'markers',
        'integration: marks tests as integration tests (may make API calls)',
    )
    config.addinivalue_line(
        'markers',
        'slow: marks tests as slow running',
    )
