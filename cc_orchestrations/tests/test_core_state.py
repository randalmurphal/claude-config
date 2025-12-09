"""Unit tests for cc_orchestrations.core.state.

Tests state persistence, checkpointing, and phase tracking.
"""

import json
import tempfile
from pathlib import Path

from cc_orchestrations.core.state import (
    ComponentStatus,
    PhaseStatus,
    State,
    StateManager,
    VoteResult,
)


class TestPhaseStatus:
    """Tests for PhaseStatus enum."""

    def test_status_values_exist(self):
        """Verify expected statuses exist."""
        # These are the actual values in the enum
        assert PhaseStatus.NOT_STARTED
        assert PhaseStatus.IN_PROGRESS
        assert PhaseStatus.COMPLETE
        assert PhaseStatus.BLOCKED
        assert PhaseStatus.SKIPPED

    def test_status_is_string_enum(self):
        """PhaseStatus should be string enum."""
        assert isinstance(PhaseStatus.COMPLETE.value, str)


class TestComponentStatus:
    """Tests for ComponentStatus enum."""

    def test_component_status_exists(self):
        """Verify component status values exist."""
        assert ComponentStatus.NOT_STARTED
        assert ComponentStatus.SKELETON
        assert ComponentStatus.IMPLEMENTING
        assert ComponentStatus.COMPLETE
        assert ComponentStatus.BLOCKED


class TestState:
    """Tests for State dataclass."""

    def test_state_creation(self):
        """Test state can be created with defaults."""
        state = State()
        assert state.mode == 'standard'
        assert state.dry_run is False
        assert state.phase_status == PhaseStatus.NOT_STARTED

    def test_state_with_dry_run(self):
        """Test state with dry_run flag."""
        state = State(mode='quick', dry_run=True)
        assert state.mode == 'quick'
        assert state.dry_run is True

    def test_state_serialization(self):
        """Test state round-trip serialization."""
        original = State(
            mode='full',
            dry_run=True,
            current_phase='validation',
            phase_status=PhaseStatus.IN_PROGRESS,
        )

        data = original.to_dict()
        restored = State.from_dict(data)

        assert restored.mode == original.mode
        assert restored.dry_run == original.dry_run
        assert restored.current_phase == original.current_phase
        assert restored.phase_status == original.phase_status


class TestVoteResult:
    """Tests for VoteResult."""

    def test_vote_result_creation(self):
        """Test vote result creation."""
        result = VoteResult(
            gate_name='test-gate',
            votes=[
                {'voter': 1, 'choice': 'approve', 'reasoning': 'looks good'},
                {'voter': 2, 'choice': 'approve', 'reasoning': 'agreed'},
            ],
            winner='approve',
            consensus=True,
        )
        assert result.winner == 'approve'
        assert result.consensus is True
        assert len(result.votes) == 2

    def test_vote_result_serialization(self):
        """Test vote result round-trip."""
        original = VoteResult(
            gate_name='impact',
            votes=[{'voter': 1, 'choice': 'proceed'}],
            winner='proceed',
            consensus=True,
        )

        data = original.to_dict()
        restored = VoteResult.from_dict(data)

        assert restored.gate_name == original.gate_name
        assert restored.winner == original.winner


class TestStateManager:
    """Tests for StateManager."""

    def test_save_and_load(self):
        """Test basic save/load cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / '.spec'
            manager = StateManager(state_dir)

            # Save state
            state = State(mode='standard', dry_run=True)
            state.current_phase = 'parse_spec'
            state.phase_status = PhaseStatus.COMPLETE
            manager.save(state)

            # Load and verify
            loaded = manager.load()
            assert loaded.mode == 'standard'
            assert loaded.dry_run is True
            assert loaded.current_phase == 'parse_spec'
            assert loaded.phase_status == PhaseStatus.COMPLETE

    def test_state_file_location(self):
        """Test state file is created in correct location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / '.spec'
            manager = StateManager(state_dir)

            state = State()
            manager.save(state)

            # Verify file exists
            state_file = state_dir / 'STATE.json'
            assert state_file.exists()

            # Verify it's valid JSON
            with open(state_file) as f:
                data = json.load(f)
            assert 'mode' in data

    def test_state_updates(self):
        """Test state can be modified and saved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / '.spec'
            manager = StateManager(state_dir)

            # Initial state
            state = State()
            manager.save(state)

            # Update state
            loaded = manager.load()
            loaded.current_phase = 'validation'
            loaded.phase_status = PhaseStatus.IN_PROGRESS
            manager.save(loaded)

            # Verify update persisted
            reloaded = manager.load()
            assert reloaded.current_phase == 'validation'
            assert reloaded.phase_status == PhaseStatus.IN_PROGRESS
