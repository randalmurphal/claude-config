"""Progress indicator with spinning animation for agent execution."""

import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(Enum):
    """Status of an agent task."""

    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETE = 'complete'
    FAILED = 'failed'


@dataclass
class AgentProgress:
    """Track progress of a single agent."""

    name: str
    status: AgentStatus = AgentStatus.PENDING
    start_time: float | None = None
    end_time: float | None = None
    result_summary: str = ''

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time


@dataclass
class ProgressTracker:
    """Track and display progress of parallel agent execution."""

    agents: dict[str, AgentProgress] = field(default_factory=dict)
    _spinner_thread: threading.Thread | None = None
    _stop_spinner: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # Spinner characters
    SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def add_agent(self, name: str) -> None:
        """Add an agent to track."""
        with self._lock:
            self.agents[name] = AgentProgress(name=name)

    def start_agent(self, name: str) -> None:
        """Mark an agent as started."""
        with self._lock:
            if name in self.agents:
                self.agents[name].status = AgentStatus.RUNNING
                self.agents[name].start_time = time.time()

    def complete_agent(
        self, name: str, success: bool, summary: str = ''
    ) -> None:
        """Mark an agent as complete."""
        with self._lock:
            if name in self.agents:
                self.agents[name].status = (
                    AgentStatus.COMPLETE if success else AgentStatus.FAILED
                )
                self.agents[name].end_time = time.time()
                self.agents[name].result_summary = summary

    def start_display(self) -> None:
        """Start the spinner display thread."""
        self._stop_spinner = False
        self._spinner_thread = threading.Thread(
            target=self._display_loop, daemon=True
        )
        self._spinner_thread.start()

    def stop_display(self) -> None:
        """Stop the spinner display thread."""
        self._stop_spinner = True
        if self._spinner_thread:
            self._spinner_thread.join(timeout=1.0)
        # Clear the line
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()

    def _display_loop(self) -> None:
        """Display loop that updates the progress line."""
        spinner_idx = 0
        while not self._stop_spinner:
            with self._lock:
                running = [
                    a
                    for a in self.agents.values()
                    if a.status == AgentStatus.RUNNING
                ]
                complete = [
                    a
                    for a in self.agents.values()
                    if a.status in (AgentStatus.COMPLETE, AgentStatus.FAILED)
                ]

            if running:
                # Build status line
                spinner = self.SPINNER[spinner_idx % len(self.SPINNER)]
                spinner_idx += 1

                # Show running agents with elapsed time
                running_names = []
                for agent in running[:3]:  # Show max 3
                    elapsed = f'{agent.elapsed:.0f}s'
                    running_names.append(f'{agent.name} ({elapsed})')

                if len(running) > 3:
                    running_names.append(f'+{len(running) - 3} more')

                status = f'{spinner} Running: {", ".join(running_names)} [{len(complete)}/{len(self.agents)} done]'

                # Truncate if too long
                max_width = 100
                if len(status) > max_width:
                    status = status[: max_width - 3] + '...'

                sys.stdout.write(f'\r{status}')
                sys.stdout.flush()

            time.sleep(0.1)

    def print_summary(self) -> None:
        """Print final summary of all agents."""
        print()  # New line after spinner
        with self._lock:
            for agent in self.agents.values():
                status_icon = {
                    AgentStatus.COMPLETE: '✓',
                    AgentStatus.FAILED: '✗',
                    AgentStatus.PENDING: '○',
                    AgentStatus.RUNNING: '◐',
                }.get(agent.status, '?')

                elapsed = f'{agent.elapsed:.1f}s' if agent.elapsed > 0 else '-'
                summary = (
                    f' - {agent.result_summary}' if agent.result_summary else ''
                )

                print(f'  {status_icon} {agent.name}: {elapsed}{summary}')


def create_progress_tracker(agent_names: list[str]) -> ProgressTracker:
    """Create a progress tracker for the given agents.

    Args:
        agent_names: List of agent names to track

    Returns:
        Configured ProgressTracker
    """
    tracker = ProgressTracker()
    for name in agent_names:
        tracker.add_agent(name)
    return tracker
