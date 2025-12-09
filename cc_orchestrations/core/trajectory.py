"""Trajectory logging for agent execution traces.

Persists structured traces to .workspace/trajectories/ for post-hoc debugging.
When an orchestration fails, trajectory logs help answer "what went wrong?"
by showing the exact sequence of agent calls, their inputs, and outputs.
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

LOG = logging.getLogger(__name__)


@dataclass
class AgentTrajectory:
    """Single agent execution trace."""

    agent_name: str
    prompt_hash: str  # SHA256 of prompt for deduplication
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Inputs
    model: str = ''
    input_context_keys: list[str] = field(default_factory=list)
    prompt_preview: str = ''  # First 500 chars

    # Execution
    duration_ms: int = 0
    retry_attempts: int = 0

    # Outputs
    success: bool = False
    output_preview: str = ''  # First 500 chars of raw output
    structured_keys: list[str] = field(default_factory=list)  # Keys in response
    error: str = ''

    # Status
    status: str = ''  # From result.status


@dataclass
class SessionSummary:
    """Summary of a trajectory logging session."""

    session_id: str
    start_time: str
    end_time: str = ''
    total_agents: int = 0
    successful: int = 0
    failed: int = 0
    total_duration_ms: int = 0
    agents_run: list[str] = field(default_factory=list)


class TrajectoryLogger:
    """Logs agent trajectories to workspace for debugging.

    Usage:
        logger = TrajectoryLogger(work_dir)
        # ... after each agent run ...
        logger.log(trajectory)
        # ... at end of session ...
        summary = logger.get_session_summary()
    """

    def __init__(self, work_dir: Path, session_id: str | None = None):
        """Initialize trajectory logger.

        Args:
            work_dir: Working directory (trajectories stored in .workspace/trajectories/)
            session_id: Optional session ID. If not provided, uses timestamp.
        """
        self.work_dir = work_dir
        self.trajectories_dir = work_dir / '.workspace' / 'trajectories'
        self._session_id = session_id or datetime.now().strftime(
            '%Y%m%d_%H%M%S'
        )
        self._start_time = datetime.now().isoformat()
        self._trajectories: list[AgentTrajectory] = []

        # Create directory if it doesn't exist
        self.trajectories_dir.mkdir(parents=True, exist_ok=True)

    @property
    def session_id(self) -> str:
        """Get the session ID for this logger."""
        return self._session_id

    def log(self, trajectory: AgentTrajectory) -> Path:
        """Write trajectory to file and track in memory.

        Args:
            trajectory: The trajectory to log

        Returns:
            Path to the written file
        """
        self._trajectories.append(trajectory)

        # Generate unique filename
        idx = len(self._trajectories)
        filename = f'{self._session_id}_{idx:03d}_{trajectory.agent_name}_{trajectory.prompt_hash[:8]}.json'
        path = self.trajectories_dir / filename

        try:
            with open(path, 'w') as f:
                json.dump(asdict(trajectory), f, indent=2)
            LOG.debug(f'Logged trajectory: {filename}')
        except OSError as e:
            LOG.warning(f'Failed to write trajectory {filename}: {e}')

        return path

    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """Create deterministic hash of prompt for deduplication.

        Args:
            prompt: The prompt text

        Returns:
            SHA256 hash of the prompt
        """
        return hashlib.sha256(prompt.encode()).hexdigest()

    @staticmethod
    def create_trajectory(
        agent_name: str,
        prompt: str,
        model: str = '',
        context: dict[str, Any] | None = None,
    ) -> AgentTrajectory:
        """Create a trajectory with pre-computed fields.

        Helper to create a trajectory before execution, then update
        it with results after.

        Args:
            agent_name: Name of the agent
            prompt: The full prompt
            model: Model used
            context: Context dictionary

        Returns:
            AgentTrajectory ready to be updated with results
        """
        return AgentTrajectory(
            agent_name=agent_name,
            prompt_hash=TrajectoryLogger.hash_prompt(prompt),
            model=model,
            input_context_keys=list((context or {}).keys()),
            prompt_preview=prompt[:500] if prompt else '',
        )

    def get_session_traces(self) -> list[AgentTrajectory]:
        """Get all traces from current session (in-memory).

        Returns:
            List of trajectories in order of execution
        """
        return list(self._trajectories)

    def load_session_traces(self) -> list[AgentTrajectory]:
        """Load all traces from current session from disk.

        Returns:
            List of trajectories sorted by timestamp
        """
        traces = []
        for path in self.trajectories_dir.glob(f'{self._session_id}_*.json'):
            try:
                with open(path) as f:
                    data = json.load(f)
                    traces.append(AgentTrajectory(**data))
            except (OSError, json.JSONDecodeError, TypeError) as e:
                LOG.warning(f'Failed to load trajectory {path}: {e}')

        return sorted(traces, key=lambda t: t.timestamp)

    def get_session_summary(self) -> SessionSummary:
        """Get summary of current session.

        Returns:
            SessionSummary with aggregate statistics
        """
        traces = self._trajectories

        return SessionSummary(
            session_id=self._session_id,
            start_time=self._start_time,
            end_time=datetime.now().isoformat(),
            total_agents=len(traces),
            successful=sum(1 for t in traces if t.success),
            failed=sum(1 for t in traces if not t.success),
            total_duration_ms=sum(t.duration_ms for t in traces),
            agents_run=[t.agent_name for t in traces],
        )

    def write_session_summary(self) -> Path:
        """Write session summary to file.

        Returns:
            Path to the summary file
        """
        summary = self.get_session_summary()
        path = self.trajectories_dir / f'{self._session_id}_SUMMARY.json'

        try:
            with open(path, 'w') as f:
                json.dump(asdict(summary), f, indent=2)
            LOG.info(f'Wrote session summary: {path}')
        except OSError as e:
            LOG.warning(f'Failed to write session summary: {e}')

        return path

    def get_failed_traces(self) -> list[AgentTrajectory]:
        """Get all failed traces from current session.

        Useful for quick debugging - "what failed?"

        Returns:
            List of failed trajectories
        """
        return [t for t in self._trajectories if not t.success]

    def get_trace_by_agent(self, agent_name: str) -> list[AgentTrajectory]:
        """Get all traces for a specific agent.

        Args:
            agent_name: Agent name to filter by

        Returns:
            List of trajectories for that agent
        """
        return [t for t in self._trajectories if t.agent_name == agent_name]
