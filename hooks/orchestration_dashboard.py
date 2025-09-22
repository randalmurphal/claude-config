#!/usr/bin/env python3
"""
Unified Orchestration Dashboard
Aggregates and displays all orchestration intelligence in one view.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
import redis

def load_json_file(filepath: Path) -> Dict:
    """Load JSON file if it exists."""
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def get_redis_stats() -> Dict:
    """Get orchestration stats from Redis."""
    stats = {
        "active_tasks": 0,
        "completed_today": 0,
        "active_chambers": 0
    }

    try:
        client = redis.from_url('redis://localhost:6379', decode_responses=True)

        # Count active tasks
        for key in client.scan_iter(match="task:*"):
            task = client.hgetall(key)
            if task.get('state') in ['in_progress', 'pending']:
                stats["active_tasks"] += 1

            # Check if completed today
            if task.get('completed_at'):
                completed = datetime.fromisoformat(task['completed_at'])
                if completed.date() == datetime.now().date():
                    stats["completed_today"] += 1

        # Count active chambers
        for key in client.scan_iter(match="chamber:*"):
            stats["active_chambers"] += 1

        client.close()
    except:
        pass

    return stats

def generate_dashboard():
    """Generate unified dashboard output."""
    # Load all data sources
    agent_perf = load_json_file(Path.home() / ".claude" / "agent_performance.json")
    orchestration_patterns = load_json_file(Path.home() / ".claude" / "orchestration_patterns.json")
    global_patterns = load_json_file(Path.home() / ".claude" / "global_orchestration_patterns.json")
    confidence_cal = load_json_file(Path.home() / ".claude" / "confidence_calibration.json")

    redis_stats = get_redis_stats()

    # Build dashboard
    output = []
    output.append("\n" + "=" * 60)
    output.append("🎯 ORCHESTRATION INTELLIGENCE DASHBOARD")
    output.append("=" * 60)

    # Current Activity
    output.append("\n📊 CURRENT ACTIVITY")
    output.append(f"  Active Tasks: {redis_stats['active_tasks']}")
    output.append(f"  Completed Today: {redis_stats['completed_today']}")
    output.append(f"  Active Chambers: {redis_stats['active_chambers']}")

    # Agent Performance
    output.append("\n🤖 AGENT PERFORMANCE")
    if agent_perf.get("by_agent_type"):
        top_agents = []
        for agent, data in agent_perf["by_agent_type"].items():
            total = data.get("successful_runs", 0) + data.get("failed_runs", 0)
            if total > 0:
                success_rate = data["successful_runs"] / total
                top_agents.append({
                    "name": agent,
                    "rate": success_rate,
                    "total": total,
                    "avg_time": data.get("average_duration", 0)
                })

        # Sort by success rate
        top_agents.sort(key=lambda x: x["rate"], reverse=True)

        for agent in top_agents[:5]:
            output.append(f"  {agent['name']}: {agent['rate']:.0%} success ({agent['total']} runs, avg {format_duration(agent['avg_time'])})")

    # Pattern Insights
    output.append("\n🔍 PATTERN INSIGHTS")
    if global_patterns.get("patterns_by_type"):
        for task_type, data in list(global_patterns["patterns_by_type"].items())[:5]:
            success_rate = data.get("success_rate", 0)
            avg_duration = data.get("average_duration", 0)
            project_count = len(data.get("projects", []))

            output.append(f"  {task_type}: {success_rate:.0%} success, {format_duration(avg_duration)} avg")
            if project_count > 1:
                output.append(f"    Used across {project_count} projects")

    # Confidence Calibration
    output.append("\n📈 CONFIDENCE CALIBRATION")
    if confidence_cal.get("accuracy_by_type"):
        for task_type, accuracy in list(confidence_cal["accuracy_by_type"].items())[:3]:
            predictions = accuracy.get("predictions", 0)
            if predictions > 0:
                within_01 = accuracy.get("within_0_1", 0)
                accuracy_pct = (within_01 / predictions) * 100
                mean_error = accuracy.get("mean_error", 0)
                output.append(f"  {task_type}: {accuracy_pct:.0f}% accurate (±0.1), mean error: {mean_error:.2f}")

    # Recent Gotchas
    output.append("\n⚠️ RECENT GOTCHAS")
    gotchas = orchestration_patterns.get("optimization_hints", {})
    recent_gotchas = []

    # Extract gotchas from patterns
    for workflow in orchestration_patterns.get("successful_workflows", [])[-10:]:
        if "gotcha" in workflow:
            recent_gotchas.append(workflow["gotcha"])

    # Also check chamber patterns for issues
    chamber_conflicts = orchestration_patterns.get("chamber_patterns", {}).get("merge_conflicts", [])
    for conflict in chamber_conflicts[-3:]:
        if conflict.get("files"):
            recent_gotchas.append(f"Merge conflict in {conflict['files'][0]}")

    for gotcha in recent_gotchas[-3:]:
        output.append(f"  - {gotcha[:70]}")

    # Success Patterns
    output.append("\n✨ SUCCESSFUL PATTERNS")
    successful = orchestration_patterns.get("successful_workflows", [])
    if successful:
        # Group by agent sequence
        sequence_counts = {}
        for workflow in successful[-20:]:
            seq = " → ".join(workflow.get("sequence", [])[:3])
            if seq not in sequence_counts:
                sequence_counts[seq] = {"count": 0, "durations": []}
            sequence_counts[seq]["count"] += 1
            sequence_counts[seq]["durations"].append(workflow.get("duration", 0))

        # Show top sequences
        for seq, data in sorted(sequence_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:3]:
            avg_duration = sum(data["durations"]) / len(data["durations"]) if data["durations"] else 0
            output.append(f"  {seq}")
            output.append(f"    Used {data['count']} times, avg {format_duration(avg_duration)}")

    # Recommendations
    output.append("\n💡 RECOMMENDATIONS")

    # Check for low-performing agents
    low_performers = []
    if agent_perf.get("by_agent_type"):
        for agent, data in agent_perf["by_agent_type"].items():
            total = data.get("successful_runs", 0) + data.get("failed_runs", 0)
            if total > 5:
                success_rate = data["successful_runs"] / total
                if success_rate < 0.5:
                    low_performers.append(agent)

    if low_performers:
        output.append(f"  ⚠️ Consider avoiding: {', '.join(low_performers[:3])}")

    # Check for uncalibrated task types
    uncalibrated = []
    if confidence_cal.get("calibration_factors"):
        for task_type, factor in confidence_cal["calibration_factors"].items():
            if abs(factor - 1.0) > 0.3:
                uncalibrated.append(task_type)

    if uncalibrated:
        output.append(f"  📊 Confidence needs calibration for: {', '.join(uncalibrated)}")

    # Check for stale chambers
    if redis_stats["active_chambers"] > 5:
        output.append(f"  🧹 {redis_stats['active_chambers']} chambers may need cleanup")

    output.append("\n" + "=" * 60)

    return "\n".join(output)

def main():
    """Main hook handler."""
    input_data = json.loads(sys.stdin.read())

    # Run dashboard on specific commands or events
    event = input_data.get('hook_event_name')
    message = input_data.get('message', '')

    show_dashboard = False

    # Show on explicit request (musical themed!)
    if message.lower() in ['/symphony', '/orchestration', '/maestro', '/score', 'show orchestration dashboard']:
        show_dashboard = True

    # Show after orchestration completion
    if event == 'OrchestrationEvent':
        event_data = input_data.get('event_data', {})
        if event_data.get('type') == 'workflow_complete':
            show_dashboard = True

    # Show on session start if there's interesting data
    if event == 'SessionStart':
        # Check if we have enough data to show
        agent_perf = load_json_file(Path.home() / ".claude" / "agent_performance.json")
        if agent_perf.get("by_agent_type"):
            total_runs = sum(
                data.get("successful_runs", 0) + data.get("failed_runs", 0)
                for data in agent_perf["by_agent_type"].values()
            )
            if total_runs > 10:
                show_dashboard = True

    if show_dashboard:
        dashboard = generate_dashboard()
        print(dashboard, file=sys.stderr)

    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()