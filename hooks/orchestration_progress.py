#!/opt/envs/py3.13/bin/python
"""
Orchestration Progress Hook
Displays real-time orchestration progress and status updates.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Optional
import redis
from datetime import datetime

class ProgressTracker:
    """Track and display orchestration progress."""

    def __init__(self):
        self.redis_client = None
        self.current_task_id = None
        self.start_time = None
        self.phases = [
            "goal_alignment",
            "architecture",
            "skeleton_building",
            "implementation",
            "testing",
            "validation",
            "completion"
        ]

    def connect_redis(self) -> bool:
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url('redis://localhost:6379', decode_responses=True)
            self.redis_client.ping()
            return True
        except:
            return False

    def get_task_data(self, task_id: str) -> Dict:
        """Get task data from Redis."""
        if not self.redis_client:
            return {}

        task_key = f"task:{task_id}"
        data = self.redis_client.hgetall(task_key)
        return data

    def get_agent_status(self, task_id: str) -> Dict:
        """Get current agent statuses."""
        if not self.redis_client:
            return {}

        # Get all agents for this task
        pattern = f"agent:{task_id}:*"
        agents = {}

        for key in self.redis_client.scan_iter(match=pattern):
            agent_data = self.redis_client.hgetall(key)
            if agent_data:
                agent_id = key.split(':')[-1]
                agents[agent_id] = agent_data

        return agents

    def calculate_progress(self, task_data: Dict, agents: Dict) -> float:
        """Calculate overall progress percentage."""
        if not task_data:
            return 0.0

        # Get current phase
        current_phase = task_data.get('current_phase', 'goal_alignment')
        phase_index = self.phases.index(current_phase) if current_phase in self.phases else 0

        # Base progress from phase
        phase_progress = (phase_index / len(self.phases)) * 100

        # Add progress within current phase
        active_agents = sum(1 for a in agents.values() if a.get('state') == 'running')
        completed_agents = sum(1 for a in agents.values() if a.get('state') == 'completed')
        total_agents = len(agents)

        if total_agents > 0:
            within_phase = (completed_agents / total_agents) * (100 / len(self.phases))
            phase_progress += within_phase

        return min(100.0, phase_progress)

    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def generate_progress_bar(self, progress: float, width: int = 30) -> str:
        """Generate ASCII progress bar."""
        filled = int(width * progress / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {progress:.1f}%"

    def display_progress(self, event_data: Dict):
        """Display orchestration progress."""
        task_id = event_data.get('task_id')
        if not task_id:
            return

        task_data = self.get_task_data(task_id)
        agents = self.get_agent_status(task_id)

        # Calculate metrics
        progress = self.calculate_progress(task_data, agents)
        current_phase = task_data.get('current_phase', 'initializing')

        # Get timing
        start_time = task_data.get('created_at')
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            elapsed = (datetime.now() - start_dt).total_seconds()
        else:
            elapsed = 0

        # Get active agents
        active_agents = [
            a.get('agent_type', 'unknown')
            for a in agents.values()
            if a.get('state') == 'running'
        ]

        # Build display
        output = []
        output.append("\n" + "=" * 50)
        output.append("🎯 ORCHESTRATION PROGRESS")
        output.append("=" * 50)

        output.append(f"\nTask: {task_data.get('description', 'Unknown')[:60]}")
        output.append(f"ID: {task_id[:8]}...")

        output.append(f"\n{self.generate_progress_bar(progress)}")

        output.append(f"\nPhase: {current_phase.replace('_', ' ').title()}")
        if active_agents:
            output.append(f"Active: {', '.join(active_agents[:3])}")

        output.append(f"\nElapsed: {self.format_duration(elapsed)}")

        # Estimate remaining
        if progress > 10:
            estimated_total = elapsed / (progress / 100)
            remaining = estimated_total - elapsed
            output.append(f"Estimated remaining: {self.format_duration(remaining)}")

        # Show completed phases
        completed_phases = []
        if current_phase in self.phases:
            current_index = self.phases.index(current_phase)
            for i, phase in enumerate(self.phases):
                if i < current_index:
                    completed_phases.append(f"✓ {phase.replace('_', ' ').title()}")

        if completed_phases:
            output.append("\nCompleted:")
            for phase in completed_phases[-3:]:  # Show last 3
                output.append(f"  {phase}")

        # Show any gotchas discovered
        gotchas = task_data.get('gotchas', [])
        if gotchas:
            output.append("\n⚠️ Discovered Issues:")
            for gotcha in gotchas[-2:]:  # Show last 2
                output.append(f"  - {gotcha[:60]}")

        output.append("\n" + "=" * 50)

        print("\n".join(output), file=sys.stderr)

def main():
    """Main hook handler."""
    input_data = json.loads(sys.stdin.read())

    # Handle orchestration events
    event_name = input_data.get('hook_event_name')

    # Look for orchestration-related events
    if event_name in ['OrchestrationEvent', 'AgentEvent', 'TaskEvent']:
        event_data = input_data.get('event_data', {})

        # Create progress tracker
        tracker = ProgressTracker()
        if tracker.connect_redis():
            tracker.display_progress(event_data)

    # Also handle MCP tool calls to track orchestration
    elif event_name == 'PostToolUse':
        tool_name = input_data.get('tool_name', '')
        if 'orchestration' in tool_name.lower():
            # Extract task_id from tool result if available
            result = input_data.get('result', {})
            if isinstance(result, dict):
                task_id = result.get('task_id')
                if task_id:
                    tracker = ProgressTracker()
                    if tracker.connect_redis():
                        tracker.display_progress({'task_id': task_id})

    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()