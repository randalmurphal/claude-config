"""Unit tests for cc_orchestrations.core.trajectory.

Tests trajectory logging functionality including AgentTrajectory,
TrajectoryLogger, and SessionSummary.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from cc_orchestrations.core.trajectory import (
    AgentTrajectory,
    SessionSummary,
    TrajectoryLogger,
)


@pytest.fixture
def temp_work_dir(tmp_path: Path) -> Path:
    """Create a temporary work directory."""
    work = tmp_path / 'work'
    work.mkdir()
    return work


@pytest.fixture
def sample_trajectory() -> AgentTrajectory:
    """Create a sample trajectory for testing."""
    return AgentTrajectory(
        agent_name='test_agent',
        prompt_hash='abc123def456',
        model='sonnet',
        input_context_keys=['component', 'issues'],
        prompt_preview='Fix the bug in foo.py',
        duration_ms=1500,
        retry_attempts=0,
        success=True,
        output_preview='{"status": "fixed"}',
        structured_keys=['status', 'changes'],
        error='',
        status='success',
    )


class TestAgentTrajectory:
    """Tests for AgentTrajectory dataclass."""

    def test_basic_creation(self):
        """Test basic trajectory creation."""
        trajectory = AgentTrajectory(
            agent_name='validator',
            prompt_hash='abc123',
        )

        assert trajectory.agent_name == 'validator'
        assert trajectory.prompt_hash == 'abc123'
        assert trajectory.success is False  # Default
        assert trajectory.error == ''

    def test_with_all_fields(self, sample_trajectory):
        """Test trajectory with all fields populated."""
        assert sample_trajectory.agent_name == 'test_agent'
        assert sample_trajectory.model == 'sonnet'
        assert sample_trajectory.duration_ms == 1500
        assert sample_trajectory.success is True
        assert 'component' in sample_trajectory.input_context_keys

    def test_timestamp_auto_set(self):
        """Timestamp should be auto-set on creation."""
        trajectory = AgentTrajectory(
            agent_name='test',
            prompt_hash='abc',
        )

        assert trajectory.timestamp is not None
        # Should be valid ISO format
        datetime.fromisoformat(trajectory.timestamp)

    def test_default_values(self):
        """Test default values are correct."""
        trajectory = AgentTrajectory(
            agent_name='test',
            prompt_hash='abc',
        )

        assert trajectory.model == ''
        assert trajectory.input_context_keys == []
        assert trajectory.prompt_preview == ''
        assert trajectory.duration_ms == 0
        assert trajectory.retry_attempts == 0
        assert trajectory.success is False
        assert trajectory.structured_keys == []


class TestTrajectoryLoggerInit:
    """Tests for TrajectoryLogger initialization."""

    def test_basic_init(self, temp_work_dir):
        """Test basic logger initialization."""
        logger = TrajectoryLogger(temp_work_dir)

        assert logger.work_dir == temp_work_dir
        assert (
            logger.trajectories_dir
            == temp_work_dir / '.workspace' / 'trajectories'
        )
        assert logger.session_id is not None

    def test_creates_directory(self, temp_work_dir):
        """Logger should create trajectories directory."""
        logger = TrajectoryLogger(temp_work_dir)

        assert logger.trajectories_dir.exists()
        assert logger.trajectories_dir.is_dir()

    def test_custom_session_id(self, temp_work_dir):
        """Test initialization with custom session ID."""
        logger = TrajectoryLogger(
            temp_work_dir, session_id='custom_session_123'
        )

        assert logger.session_id == 'custom_session_123'

    def test_auto_session_id_format(self, temp_work_dir):
        """Auto session ID should be timestamp format."""
        logger = TrajectoryLogger(temp_work_dir)

        # Should be in YYYYMMDD_HHMMSS format
        assert len(logger.session_id) == 15  # e.g., "20251209_123456"
        assert '_' in logger.session_id


class TestTrajectoryLoggerHashPrompt:
    """Tests for TrajectoryLogger.hash_prompt static method."""

    def test_deterministic_hash(self):
        """Same prompt should produce same hash."""
        prompt = 'Test prompt'
        hash1 = TrajectoryLogger.hash_prompt(prompt)
        hash2 = TrajectoryLogger.hash_prompt(prompt)

        assert hash1 == hash2

    def test_different_prompts_different_hash(self):
        """Different prompts should produce different hashes."""
        hash1 = TrajectoryLogger.hash_prompt('Prompt A')
        hash2 = TrajectoryLogger.hash_prompt('Prompt B')

        assert hash1 != hash2

    def test_hash_format(self):
        """Hash should be SHA256 hex string."""
        hash_value = TrajectoryLogger.hash_prompt('test')

        assert len(hash_value) == 64  # SHA256 = 64 hex chars
        assert all(c in '0123456789abcdef' for c in hash_value)


class TestTrajectoryLoggerLog:
    """Tests for TrajectoryLogger.log method."""

    def test_log_creates_file(self, temp_work_dir, sample_trajectory):
        """Logging should create a JSON file."""
        logger = TrajectoryLogger(temp_work_dir, session_id='test_session')
        path = logger.log(sample_trajectory)

        assert path.exists()
        assert path.suffix == '.json'
        assert 'test_session' in path.name

    def test_log_file_content(self, temp_work_dir, sample_trajectory):
        """Logged file should contain trajectory data."""
        logger = TrajectoryLogger(temp_work_dir)
        path = logger.log(sample_trajectory)

        with open(path) as f:
            data = json.load(f)

        assert data['agent_name'] == 'test_agent'
        assert data['model'] == 'sonnet'
        assert data['success'] is True
        assert data['duration_ms'] == 1500

    def test_log_multiple_trajectories(self, temp_work_dir):
        """Multiple trajectories should create multiple files."""
        logger = TrajectoryLogger(temp_work_dir, session_id='multi_test')

        for i in range(3):
            trajectory = AgentTrajectory(
                agent_name=f'agent_{i}',
                prompt_hash=f'hash_{i}',
            )
            logger.log(trajectory)

        files = list(logger.trajectories_dir.glob('multi_test_*.json'))
        assert len(files) == 3

    def test_log_filename_format(self, temp_work_dir, sample_trajectory):
        """Filename should follow expected format."""
        logger = TrajectoryLogger(temp_work_dir, session_id='sess123')
        path = logger.log(sample_trajectory)

        # Format: {session}_{idx:03d}_{agent}_{hash[:8]}.json
        assert path.name.startswith('sess123_001_')
        assert 'test_agent' in path.name
        assert sample_trajectory.prompt_hash[:8] in path.name

    def test_log_increments_index(self, temp_work_dir):
        """File index should increment for each log."""
        logger = TrajectoryLogger(temp_work_dir, session_id='idx_test')

        path1 = logger.log(AgentTrajectory(agent_name='a', prompt_hash='h1'))
        path2 = logger.log(AgentTrajectory(agent_name='b', prompt_hash='h2'))
        path3 = logger.log(AgentTrajectory(agent_name='c', prompt_hash='h3'))

        assert '_001_' in path1.name
        assert '_002_' in path2.name
        assert '_003_' in path3.name


class TestTrajectoryLoggerCreateTrajectory:
    """Tests for TrajectoryLogger.create_trajectory helper."""

    def test_creates_trajectory(self):
        """Helper should create trajectory with computed fields."""
        trajectory = TrajectoryLogger.create_trajectory(
            agent_name='validator',
            prompt='Check the code for issues',
            model='opus',
            context={'component': 'foo.py', 'issues': []},
        )

        assert trajectory.agent_name == 'validator'
        assert trajectory.model == 'opus'
        assert 'component' in trajectory.input_context_keys
        assert 'issues' in trajectory.input_context_keys
        assert trajectory.prompt_preview == 'Check the code for issues'
        assert len(trajectory.prompt_hash) == 64

    def test_truncates_long_prompt(self):
        """Long prompts should be truncated in preview."""
        long_prompt = 'x' * 1000
        trajectory = TrajectoryLogger.create_trajectory(
            agent_name='test',
            prompt=long_prompt,
        )

        assert len(trajectory.prompt_preview) == 500
        assert trajectory.prompt_preview == 'x' * 500

    def test_handles_none_context(self):
        """None context should be handled gracefully."""
        trajectory = TrajectoryLogger.create_trajectory(
            agent_name='test',
            prompt='test',
            context=None,
        )

        assert trajectory.input_context_keys == []


class TestTrajectoryLoggerGetTraces:
    """Tests for trace retrieval methods."""

    def test_get_session_traces_in_memory(self, temp_work_dir):
        """get_session_traces should return in-memory trajectories."""
        logger = TrajectoryLogger(temp_work_dir)

        t1 = AgentTrajectory(agent_name='a', prompt_hash='h1', success=True)
        t2 = AgentTrajectory(agent_name='b', prompt_hash='h2', success=False)

        logger.log(t1)
        logger.log(t2)

        traces = logger.get_session_traces()

        assert len(traces) == 2
        assert traces[0].agent_name == 'a'
        assert traces[1].agent_name == 'b'

    def test_load_session_traces_from_disk(self, temp_work_dir):
        """load_session_traces should load from disk."""
        session_id = 'disk_test'
        logger = TrajectoryLogger(temp_work_dir, session_id=session_id)

        logger.log(AgentTrajectory(agent_name='disk_agent', prompt_hash='h1'))

        # Create new logger with same session to test disk loading
        logger2 = TrajectoryLogger(temp_work_dir, session_id=session_id)
        traces = logger2.load_session_traces()

        assert len(traces) == 1
        assert traces[0].agent_name == 'disk_agent'

    def test_get_failed_traces(self, temp_work_dir):
        """get_failed_traces should return only failures."""
        logger = TrajectoryLogger(temp_work_dir)

        logger.log(
            AgentTrajectory(agent_name='pass', prompt_hash='h1', success=True)
        )
        logger.log(
            AgentTrajectory(agent_name='fail1', prompt_hash='h2', success=False)
        )
        logger.log(
            AgentTrajectory(agent_name='fail2', prompt_hash='h3', success=False)
        )

        failed = logger.get_failed_traces()

        assert len(failed) == 2
        assert all(not t.success for t in failed)

    def test_get_trace_by_agent(self, temp_work_dir):
        """get_trace_by_agent should filter by agent name."""
        logger = TrajectoryLogger(temp_work_dir)

        logger.log(AgentTrajectory(agent_name='validator', prompt_hash='h1'))
        logger.log(AgentTrajectory(agent_name='validator', prompt_hash='h2'))
        logger.log(AgentTrajectory(agent_name='fix_executor', prompt_hash='h3'))

        validator_traces = logger.get_trace_by_agent('validator')

        assert len(validator_traces) == 2
        assert all(t.agent_name == 'validator' for t in validator_traces)


class TestSessionSummary:
    """Tests for SessionSummary and summary generation."""

    def test_summary_dataclass(self):
        """Test SessionSummary dataclass."""
        summary = SessionSummary(
            session_id='test',
            start_time='2025-01-01T00:00:00',
            end_time='2025-01-01T00:01:00',
            total_agents=5,
            successful=4,
            failed=1,
            total_duration_ms=10000,
            agents_run=['a', 'b', 'c', 'd', 'e'],
        )

        assert summary.session_id == 'test'
        assert summary.total_agents == 5
        assert summary.successful == 4
        assert summary.failed == 1

    def test_get_session_summary(self, temp_work_dir):
        """get_session_summary should aggregate statistics."""
        logger = TrajectoryLogger(temp_work_dir, session_id='summary_test')

        logger.log(
            AgentTrajectory(
                agent_name='a', prompt_hash='h1', success=True, duration_ms=100
            )
        )
        logger.log(
            AgentTrajectory(
                agent_name='b', prompt_hash='h2', success=True, duration_ms=200
            )
        )
        logger.log(
            AgentTrajectory(
                agent_name='c', prompt_hash='h3', success=False, duration_ms=50
            )
        )

        summary = logger.get_session_summary()

        assert summary.session_id == 'summary_test'
        assert summary.total_agents == 3
        assert summary.successful == 2
        assert summary.failed == 1
        assert summary.total_duration_ms == 350
        assert summary.agents_run == ['a', 'b', 'c']

    def test_write_session_summary(self, temp_work_dir):
        """write_session_summary should create summary file."""
        logger = TrajectoryLogger(temp_work_dir, session_id='write_test')

        logger.log(
            AgentTrajectory(agent_name='test', prompt_hash='h1', success=True)
        )

        path = logger.write_session_summary()

        assert path.exists()
        assert 'SUMMARY' in path.name

        with open(path) as f:
            data = json.load(f)

        assert data['session_id'] == 'write_test'
        assert data['total_agents'] == 1


class TestTrajectoryLoggerEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_session(self, temp_work_dir):
        """Empty session should have valid summary."""
        logger = TrajectoryLogger(temp_work_dir)

        summary = logger.get_session_summary()

        assert summary.total_agents == 0
        assert summary.successful == 0
        assert summary.failed == 0

    def test_unicode_in_prompt(self, temp_work_dir):
        """Unicode in prompts should be handled."""
        logger = TrajectoryLogger(temp_work_dir)

        trajectory = AgentTrajectory(
            agent_name='test',
            prompt_hash='h1',
            prompt_preview='Test with emoji 🚀 and unicode: café',
        )

        path = logger.log(trajectory)

        with open(path) as f:
            data = json.load(f)

        assert '🚀' in data['prompt_preview']
        assert 'café' in data['prompt_preview']

    def test_special_chars_in_agent_name(self, temp_work_dir):
        """Special characters in agent name should be handled."""
        logger = TrajectoryLogger(temp_work_dir, session_id='special_test')

        trajectory = AgentTrajectory(
            agent_name='agent-with-dashes_and_underscores',
            prompt_hash='h1',
        )

        path = logger.log(trajectory)
        assert path.exists()
