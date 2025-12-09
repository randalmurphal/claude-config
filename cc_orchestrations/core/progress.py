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
    _last_line_len: int = 0  # Track for proper clearing

    # Spinner characters (braille dots)
    SPINNER = [
        '\u280b',
        '\u2819',
        '\u2839',
        '\u2838',
        '\u283c',
        '\u2834',
        '\u2826',
        '\u2827',
        '\u2807',
        '\u280f',
    ]

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
        # Clear the line using tracked length
        clear_len = max(self._last_line_len, 80)
        sys.stdout.write('\r' + ' ' * clear_len + '\r')
        sys.stdout.flush()

    def _display_loop(self) -> None:
        """Display loop that updates the progress line once per second."""
        spinner_idx = 0
        last_update = 0

        while not self._stop_spinner:
            # Only update once per second
            now = time.time()
            if now - last_update < 1.0:
                time.sleep(0.1)
                continue
            last_update = now

            with self._lock:
                # Build status: running with time, done with checkmark
                agent_parts = []
                for agent in self.agents.values():
                    if agent.status == AgentStatus.RUNNING:
                        elapsed = f'{agent.elapsed:.0f}s'
                        agent_parts.append(f'{agent.name} ({elapsed})')
                    elif agent.status == AgentStatus.COMPLETE:
                        agent_parts.append(f'{agent.name} \u2713')
                    elif agent.status == AgentStatus.FAILED:
                        agent_parts.append(f'{agent.name} \u2717')
                    # Skip PENDING agents

                done_statuses = (AgentStatus.COMPLETE, AgentStatus.FAILED)
                done_count = sum(
                    1 for a in self.agents.values() if a.status in done_statuses
                )

            if agent_parts:
                spinner = self.SPINNER[spinner_idx % len(self.SPINNER)]
                spinner_idx += 1

                status = f'{spinner} {", ".join(agent_parts)} [{done_count}/{len(self.agents)}]'

                # Clear previous line completely, then write new status
                clear_str = '\r' + ' ' * self._last_line_len + '\r'
                sys.stdout.write(clear_str + status)
                sys.stdout.flush()
                self._last_line_len = len(status)

    def print_summary(self) -> None:
        """Print final summary of all agents."""
        print()  # New line after spinner
        with self._lock:
            for agent in self.agents.values():
                status_icon = {
                    AgentStatus.COMPLETE: '\u2713',
                    AgentStatus.FAILED: '\u2717',
                    AgentStatus.PENDING: '\u25cb',
                    AgentStatus.RUNNING: '\u25d0',
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


class SingleAgentProgress:
    """Simple progress display for a single agent."""

    SPINNER = [
        '\u280b',
        '\u2819',
        '\u2839',
        '\u2838',
        '\u283c',
        '\u2834',
        '\u2826',
        '\u2827',
        '\u2807',
        '\u280f',
    ]

    def __init__(self, agent_name: str, model: str = ''):
        self.agent_name = agent_name
        self.model = model
        self._stop = False
        self._thread: threading.Thread | None = None
        self._start_time = 0.0
        self._last_line_len = 0

    def start(self) -> None:
        """Start the progress display."""
        self._stop = False
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._display_loop, daemon=True)
        self._thread.start()

    def stop(self, success: bool = True, summary: str = '') -> None:
        """Stop the progress display."""
        self._stop = True
        if self._thread:
            self._thread.join(timeout=1.0)

        # Clear line and show final status
        elapsed = time.time() - self._start_time
        icon = '\u2713' if success else '\u2717'
        model_str = f' ({self.model})' if self.model else ''
        final = f'{icon} {self.agent_name}{model_str}: {elapsed:.1f}s'
        if summary:
            final += f' - {summary}'

        clear_str = '\r' + ' ' * self._last_line_len + '\r'
        sys.stdout.write(clear_str + final + '\n')
        sys.stdout.flush()

    def _display_loop(self) -> None:
        """Display spinning progress, updating once per second."""
        spinner_idx = 0
        last_update = 0

        while not self._stop:
            now = time.time()
            if now - last_update < 1.0:
                time.sleep(0.1)
                continue
            last_update = now

            spinner = self.SPINNER[spinner_idx % len(self.SPINNER)]
            spinner_idx += 1

            elapsed = now - self._start_time
            model_str = f' ({self.model})' if self.model else ''
            status = f'{spinner} {self.agent_name}{model_str} ({elapsed:.0f}s)'

            clear_str = '\r' + ' ' * self._last_line_len + '\r'
            sys.stdout.write(clear_str + status)
            sys.stdout.flush()
            self._last_line_len = len(status)
