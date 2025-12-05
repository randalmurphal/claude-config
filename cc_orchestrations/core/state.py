"""State machine and persistence for workflow execution.

State is persisted to JSON files, allowing recovery from any point.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


LOG = logging.getLogger(__name__)


class ComponentStatus(str, Enum):
    """Status of a component in the workflow."""

    NOT_STARTED = 'not_started'
    SKELETON = 'skeleton'
    IMPLEMENTING = 'implementing'
    VALIDATING = 'validating'
    FIXING = 'fixing'
    COMPLETE = 'complete'
    BLOCKED = 'blocked'


class PhaseStatus(str, Enum):
    """Status of a workflow phase."""

    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETE = 'complete'
    BLOCKED = 'blocked'
    SKIPPED = 'skipped'


@dataclass
class Issue:
    """A validation issue found during review."""

    severity: str  # critical, major, minor
    issue: str
    file: str = ''
    line: int = 0
    fix: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'severity': self.severity,
            'issue': self.issue,
            'file': self.file,
            'line': self.line,
            'fix': self.fix,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Issue':
        return cls(
            severity=data.get('severity', 'minor'),
            issue=data.get('issue', ''),
            file=data.get('file', ''),
            line=data.get('line', 0),
            fix=data.get('fix', ''),
        )


@dataclass
class ComponentState:
    """State of a single component."""

    file: str
    status: ComponentStatus = ComponentStatus.NOT_STARTED
    depends_on: list[str] = field(default_factory=list)
    purpose: str = ''
    complexity: str = 'medium'
    current_task: str = ''
    tasks_completed: int = 0
    tasks_total: int = 0
    fix_attempts: int = 0
    issues: list[Issue] = field(default_factory=list)
    previous_issues: list[Issue] = field(default_factory=list)
    started_at: str = ''
    completed_at: str = ''
    error: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'file': self.file,
            'status': self.status.value,
            'depends_on': self.depends_on,
            'purpose': self.purpose,
            'complexity': self.complexity,
            'current_task': self.current_task,
            'tasks_completed': self.tasks_completed,
            'tasks_total': self.tasks_total,
            'fix_attempts': self.fix_attempts,
            'issues': [i.to_dict() for i in self.issues],
            'previous_issues': [i.to_dict() for i in self.previous_issues],
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error': self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ComponentState':
        return cls(
            file=data['file'],
            status=ComponentStatus(data.get('status', 'not_started')),
            depends_on=data.get('depends_on', []),
            purpose=data.get('purpose', ''),
            complexity=data.get('complexity', 'medium'),
            current_task=data.get('current_task', ''),
            tasks_completed=data.get('tasks_completed', 0),
            tasks_total=data.get('tasks_total', 0),
            fix_attempts=data.get('fix_attempts', 0),
            issues=[Issue.from_dict(i) for i in data.get('issues', [])],
            previous_issues=[
                Issue.from_dict(i) for i in data.get('previous_issues', [])
            ],
            started_at=data.get('started_at', ''),
            completed_at=data.get('completed_at', ''),
            error=data.get('error', ''),
        )


@dataclass
class VoteResult:
    """Result of a voting gate."""

    gate_name: str
    votes: list[dict[str, Any]]
    winner: str = ''
    consensus: bool = False
    user_decision: str = ''
    timestamp: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'gate_name': self.gate_name,
            'votes': self.votes,
            'winner': self.winner,
            'consensus': self.consensus,
            'user_decision': self.user_decision,
            'timestamp': self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'VoteResult':
        return cls(
            gate_name=data['gate_name'],
            votes=data.get('votes', []),
            winner=data.get('winner', ''),
            consensus=data.get('consensus', False),
            user_decision=data.get('user_decision', ''),
            timestamp=data.get('timestamp', ''),
        )


@dataclass
class State:
    """Complete workflow state."""

    # Identity
    workflow_name: str = 'conduct'
    spec_path: str = ''
    work_dir: str = ''

    # Execution mode
    mode: str = 'standard'  # quick, standard, full
    dry_run: bool = False

    # Current position
    current_phase: str = 'init'
    phase_status: PhaseStatus = PhaseStatus.NOT_STARTED
    current_component: str = ''

    # Components
    components: dict[str, ComponentState] = field(default_factory=dict)
    component_order: list[str] = field(default_factory=list)

    # History
    voting_results: list[VoteResult] = field(default_factory=list)
    discoveries: list[str] = field(default_factory=list)
    commits: list[str] = field(default_factory=list)

    # Metadata
    started_at: str = ''
    updated_at: str = ''
    completed_at: str = ''
    error: str = ''
    is_new_project: bool = False
    risk_level: str = 'medium'

    def to_dict(self) -> dict[str, Any]:
        return {
            'workflow_name': self.workflow_name,
            'spec_path': self.spec_path,
            'work_dir': self.work_dir,
            'mode': self.mode,
            'dry_run': self.dry_run,
            'current_phase': self.current_phase,
            'phase_status': self.phase_status.value,
            'current_component': self.current_component,
            'components': {k: v.to_dict() for k, v in self.components.items()},
            'component_order': self.component_order,
            'voting_results': [v.to_dict() for v in self.voting_results],
            'discoveries': self.discoveries,
            'commits': self.commits,
            'started_at': self.started_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'error': self.error,
            'is_new_project': self.is_new_project,
            'risk_level': self.risk_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'State':
        return cls(
            workflow_name=data.get('workflow_name', 'conduct'),
            spec_path=data.get('spec_path', ''),
            work_dir=data.get('work_dir', ''),
            mode=data.get('mode', 'standard'),
            dry_run=data.get('dry_run', False),
            current_phase=data.get('current_phase', 'init'),
            phase_status=PhaseStatus(data.get('phase_status', 'not_started')),
            current_component=data.get('current_component', ''),
            components={
                k: ComponentState.from_dict(v)
                for k, v in data.get('components', {}).items()
            },
            component_order=data.get('component_order', []),
            voting_results=[
                VoteResult.from_dict(v) for v in data.get('voting_results', [])
            ],
            discoveries=data.get('discoveries', []),
            commits=data.get('commits', []),
            started_at=data.get('started_at', ''),
            updated_at=data.get('updated_at', ''),
            completed_at=data.get('completed_at', ''),
            error=data.get('error', ''),
            is_new_project=data.get('is_new_project', False),
            risk_level=data.get('risk_level', 'medium'),
        )

    def get_completed_components(self) -> list[str]:
        """Get list of completed component files."""
        return [
            f
            for f, c in self.components.items()
            if c.status == ComponentStatus.COMPLETE
        ]

    def get_pending_components(self) -> list[str]:
        """Get components not yet started, in dependency order."""
        return [
            f
            for f in self.component_order
            if self.components.get(f, ComponentState(file=f)).status
            == ComponentStatus.NOT_STARTED
        ]

    def all_components_complete(self) -> bool:
        """Check if all components are complete."""
        return all(
            c.status == ComponentStatus.COMPLETE
            for c in self.components.values()
        )


class StateManager:
    """Manages state persistence and updates."""

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_file = state_dir / 'STATE.json'
        self.history_dir = state_dir / 'history'
        self._state: State | None = None

    def ensure_dirs(self) -> None:
        """Create state directories if needed."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> State:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self._state = State.from_dict(data)
                LOG.info(f'Loaded state from {self.state_file}')
            except (json.JSONDecodeError, KeyError) as e:
                LOG.error(f'Failed to load state: {e}')
                self._state = State()
        else:
            self._state = State()
            self._state.started_at = datetime.now().isoformat()
        return self._state

    def save(self, state: State | None = None) -> None:
        """Save state to file."""
        if state:
            self._state = state
        if not self._state:
            raise ValueError('No state to save')

        self.ensure_dirs()
        self._state.updated_at = datetime.now().isoformat()

        # Write current state
        self.state_file.write_text(json.dumps(self._state.to_dict(), indent=2))

        # Write timestamped history
        history_file = (
            self.history_dir
            / f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        history_file.write_text(json.dumps(self._state.to_dict(), indent=2))

        LOG.debug(f'Saved state to {self.state_file}')

    @property
    def state(self) -> State:
        """Get current state, loading if needed."""
        if not self._state:
            self.load()
        return self._state  # type: ignore

    def update_phase(self, phase: str, status: PhaseStatus) -> None:
        """Update current phase."""
        self.state.current_phase = phase
        self.state.phase_status = status
        self.save()

    def update_component(
        self,
        file: str,
        status: ComponentStatus | None = None,
        **kwargs: Any,
    ) -> None:
        """Update component state."""
        if file not in self.state.components:
            self.state.components[file] = ComponentState(file=file)

        comp = self.state.components[file]
        if status:
            comp.status = status
            if status == ComponentStatus.COMPLETE:
                comp.completed_at = datetime.now().isoformat()
            elif (
                comp.status == ComponentStatus.NOT_STARTED
                and status != ComponentStatus.NOT_STARTED
            ):
                comp.started_at = datetime.now().isoformat()

        for key, value in kwargs.items():
            if hasattr(comp, key):
                setattr(comp, key, value)

        self.save()

    def add_discovery(self, discovery: str) -> None:
        """Add a discovery to the log."""
        self.state.discoveries.append(discovery)
        self.save()

    def add_vote_result(self, result: VoteResult) -> None:
        """Add a voting result."""
        result.timestamp = datetime.now().isoformat()
        self.state.voting_results.append(result)
        self.save()

    def set_error(self, error: str) -> None:
        """Set error state."""
        self.state.error = error
        self.save()

    def clear_error(self) -> None:
        """Clear error state."""
        self.state.error = ''
        self.save()

    def mark_complete(self) -> None:
        """Mark workflow as complete."""
        self.state.completed_at = datetime.now().isoformat()
        self.state.phase_status = PhaseStatus.COMPLETE
        self.save()
