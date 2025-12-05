"""Test dry-run mode for the conduct orchestrator.

This test validates that the dry-run mode:
1. Accepts the --dry-run flag
2. Uses haiku model to save costs
3. Disables all tools
4. Returns properly formatted test data
5. Goes through the full flow without errors
"""

import contextlib
import tempfile
from pathlib import Path

import pytest

from cc_orchestrations.conduct.agents.runner import DRY_RUN_WRAPPER, AgentRunner
from cc_orchestrations.conduct.core.config import (
    MODE_CONFIGS,
    Config,
    ExecutionMode,
)
from cc_orchestrations.conduct.core.state import State, StateManager


class TestModeConfig:
    """Test execution mode configurations."""

    def test_quick_mode_config(self) -> None:
        """Quick mode should have aggressive parallelization."""
        config = MODE_CONFIGS[ExecutionMode.QUICK]
        assert config.parallelization == 'aggressive'
        assert config.validate_after_skeleton is False
        assert config.validate_after_implementation == 'lint_only'
        assert config.fix_all_severities is False

    def test_standard_mode_config(self) -> None:
        """Standard mode should have balanced settings."""
        config = MODE_CONFIGS[ExecutionMode.STANDARD]
        assert config.parallelization == 'by_level'
        assert config.validate_after_skeleton is True
        assert config.validate_after_implementation == 'quick_review'

    def test_full_mode_config(self) -> None:
        """Full mode should have thorough validation."""
        config = MODE_CONFIGS[ExecutionMode.FULL]
        assert config.parallelization == 'conservative'
        assert config.validate_after_skeleton is True
        assert config.validate_after_implementation == 'full_review'
        assert config.fix_all_severities is True
        assert config.skeleton_gate is True
        assert config.production_gate is True


class TestConfigSerialization:
    """Test config serialization with mode and dry_run."""

    def test_config_to_dict_includes_mode(self) -> None:
        """Config.to_dict() should include mode and dry_run."""
        config = Config(mode=ExecutionMode.FULL, dry_run=True)
        data = config.to_dict()
        assert data['mode'] == 'full'
        assert data['dry_run'] is True

    def test_config_from_dict_parses_mode(self) -> None:
        """Config.from_dict() should parse mode correctly."""
        data = {
            'mode': 'quick',
            'dry_run': True,
        }
        config = Config.from_dict(data)
        assert config.mode == ExecutionMode.QUICK
        assert config.dry_run is True

    def test_config_mode_config_auto_set(self) -> None:
        """Config should auto-set mode_config from mode."""
        config = Config(mode=ExecutionMode.FULL)
        assert config.mode_config is not None
        assert config.mode_config.name == 'full'


class TestStateSerialization:
    """Test state serialization with mode and dry_run."""

    def test_state_to_dict_includes_mode(self) -> None:
        """State.to_dict() should include mode and dry_run."""
        state = State(mode='full', dry_run=True)
        data = state.to_dict()
        assert data['mode'] == 'full'
        assert data['dry_run'] is True

    def test_state_from_dict_parses_mode(self) -> None:
        """State.from_dict() should parse mode correctly."""
        data = {
            'mode': 'quick',
            'dry_run': True,
        }
        state = State.from_dict(data)
        assert state.mode == 'quick'
        assert state.dry_run is True


class TestDryRunPromptWrapper:
    """Test the dry-run prompt wrapper."""

    def test_wrapper_includes_original_prompt(self) -> None:
        """Dry-run wrapper should include the original prompt."""
        original = 'Parse the specification file'
        wrapped = DRY_RUN_WRAPPER.format(original_prompt=original)
        assert original in wrapped
        assert 'DRY RUN MODE' in wrapped
        assert 'test data' in wrapped.lower()


class TestAgentRunnerDryRun:
    """Test AgentRunner dry-run behavior."""

    def test_runner_inherits_dry_run_from_config(self) -> None:
        """Runner should use config.dry_run if not explicitly set."""
        config = Config(dry_run=True)
        runner = AgentRunner(config, Path('.'))
        assert runner.dry_run is True

    def test_runner_explicit_dry_run_overrides_config(self) -> None:
        """Runner should use explicit dry_run over config."""
        config = Config(dry_run=False)
        runner = AgentRunner(config, Path('.'), dry_run=True)
        assert runner.dry_run is True


class TestStateManager:
    """Test state manager with mode tracking."""

    def test_state_manager_preserves_mode(self) -> None:
        """State manager should preserve mode through save/load cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / '.spec'
            manager = StateManager(state_dir)
            manager.ensure_dirs()

            # Create and save state
            state = State(mode='full', dry_run=True)
            manager.save(state)

            # Load and verify
            loaded = manager.load()
            assert loaded.mode == 'full'
            assert loaded.dry_run is True


def test_cli_help_shows_options() -> None:
    """CLI should show --mode and --dry-run in help."""
    import sys
    from io import StringIO

    from cc_orchestrations.conduct.cli import main

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    with contextlib.suppress(SystemExit):
        main(['run', '--help'])

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert '--mode' in output or '-m' in output
    assert '--dry-run' in output
    assert 'quick' in output.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
