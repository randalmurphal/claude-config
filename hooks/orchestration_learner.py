#!/opt/envs/py3.13/bin/python
"""
Orchestration Learner Hook
==========================
New hook specifically for learning from /conduct orchestration.

Key Features:
- Tracks agent performance by type and task
- Stores chamber operations and merge conflicts
- Learns optimal agent sequencing patterns
- Builds performance profiles for each agent type
- Stores discovered gotchas and optimization hints
- Helps improve future orchestrations
- PRISM integration via universal learner
"""

import json
import sys
import time
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime

# Import PRISM client and universal learner
sys.path.append(str(Path(__file__).parent))
from prism_client import get_prism_client
from universal_learner import get_learner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
AGENT_PERFORMANCE_FILE = Path.home() / ".claude" / "agent_performance.json"
ORCHESTRATION_PATTERNS_FILE = Path.home() / ".claude" / "orchestration_patterns.json"
GLOBAL_PATTERNS_FILE = Path.home() / ".claude" / "global_orchestration_patterns.json"
CONFIDENCE_CALIBRATION_FILE = Path.home() / ".claude" / "confidence_calibration.json"
MAX_HISTORY_SIZE = 500
PERFORMANCE_THRESHOLD = 0.7
CONFIDENCE_THRESHOLD = 0.8

class OrchestrationLearner:
    """Learn from orchestration patterns and agent performance."""

    def __init__(self):
        self.client = get_prism_client()
        self.agent_performance = self.load_agent_performance()
        # Ensure agent_sequences exists even in old data
        if "agent_sequences" not in self.agent_performance:
            self.agent_performance["agent_sequences"] = []
        self.orchestration_patterns = self.load_orchestration_patterns()
        self.global_patterns = self.load_global_patterns()
        self.confidence_calibration = self.load_confidence_calibration()
        self.current_task_id = None
        self.current_agents = {}
        self.current_project = self.get_current_project()

    def load_agent_performance(self) -> Dict:
        """Load agent performance history."""
        try:
            if AGENT_PERFORMANCE_FILE.exists():
                with open(AGENT_PERFORMANCE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load agent performance: {e}")

        return {
            "by_agent_type": defaultdict(lambda: {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "average_duration": 0,
                "common_errors": [],
                "task_types": defaultdict(int)
            }),
            "agent_sequences": [],  # Track agent workflow sequences
            "by_task_type": defaultdict(lambda: {
                "best_agents": [],
                "worst_agents": [],
                "average_duration": 0,
                "success_rate": 0
            }),
            "gotchas": []
        }

    def save_agent_performance(self):
        """Save agent performance data."""
        try:
            AGENT_PERFORMANCE_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Convert defaultdicts to regular dicts for JSON
            data_to_save = {
                "by_agent_type": dict(self.agent_performance["by_agent_type"]),
                "by_task_type": dict(self.agent_performance["by_task_type"]),
                "agent_sequences": self.agent_performance["agent_sequences"][-100:],
                "gotchas": self.agent_performance["gotchas"][-50:]
            }

            with open(AGENT_PERFORMANCE_FILE, 'w') as f:
                json.dump(data_to_save, f, indent=2, default=str)
        except Exception as e:
            logger.debug(f"Failed to save agent performance: {e}")

    def load_orchestration_patterns(self) -> Dict:
        """Load learned orchestration patterns."""
        try:
            if ORCHESTRATION_PATTERNS_FILE.exists():
                with open(ORCHESTRATION_PATTERNS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load orchestration patterns: {e}")

        return {
            "successful_workflows": [],
            "chamber_patterns": {
                "merge_conflicts": [],
                "parallel_success": [],
                "isolation_benefits": []
            },
            "optimization_hints": {},
            "task_complexity_indicators": {}
        }

    def save_orchestration_patterns(self):
        """Save orchestration patterns."""
        try:
            ORCHESTRATION_PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(ORCHESTRATION_PATTERNS_FILE, 'w') as f:
                json.dump(self.orchestration_patterns, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save orchestration patterns: {e}")

    def load_global_patterns(self) -> Dict:
        """Load global cross-project patterns."""
        try:
            if GLOBAL_PATTERNS_FILE.exists():
                with open(GLOBAL_PATTERNS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load global patterns: {e}")

        return {
            "patterns_by_type": {},
            "universal_gotchas": [],
            "cross_project_successes": []
        }

    def save_global_patterns(self):
        """Save global patterns."""
        try:
            GLOBAL_PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(GLOBAL_PATTERNS_FILE, 'w') as f:
                json.dump(self.global_patterns, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save global patterns: {e}")

    def load_confidence_calibration(self) -> Dict:
        """Load confidence calibration data."""
        try:
            if CONFIDENCE_CALIBRATION_FILE.exists():
                with open(CONFIDENCE_CALIBRATION_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load confidence calibration: {e}")

        return {
            "predictions": [],
            "calibration_factors": {},
            "accuracy_by_type": {}
        }

    def save_confidence_calibration(self):
        """Save confidence calibration."""
        try:
            CONFIDENCE_CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIDENCE_CALIBRATION_FILE, 'w') as f:
                json.dump(self.confidence_calibration, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save confidence calibration: {e}")

    def get_current_project(self) -> str:
        """Get current project identifier."""
        try:
            # Try to get git remote origin
            import subprocess
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Extract repo name from URL
                if '/' in url:
                    return url.split('/')[-1].replace('.git', '')
        except:
            pass

        # Fall back to current directory name
        return Path.cwd().name

    def extract_task_type(self, task_description: str) -> str:
        """Extract task type from description."""
        desc_lower = task_description.lower()

        task_patterns = [
            (r'\b(refactor|consolidate|clean|optimize)\b', 'refactoring'),
            (r'\b(bug|fix|error|issue|problem)\b', 'bug_fix'),
            (r'\b(feature|add|implement|create|build)\b', 'feature'),
            (r'\b(test|testing|coverage|validate)\b', 'testing'),
            (r'\b(document|docs|readme|comment)\b', 'documentation'),
            (r'\b(security|vulnerability|auth|encrypt)\b', 'security'),
            (r'\b(performance|speed|optimize|cache)\b', 'performance'),
            (r'\b(migrate|upgrade|update|version)\b', 'migration'),
        ]

        for pattern, task_type in task_patterns:
            if re.search(pattern, desc_lower):
                return task_type

        return 'general'

    def track_agent_start(self, agent_data: Dict):
        """Track when an agent starts."""
        agent_type = agent_data.get('subagent_type', 'unknown')
        task_id = agent_data.get('task_id')
        prompt = agent_data.get('prompt', '')

        # Extract task type from prompt
        task_type = self.extract_task_type(prompt)

        # Store agent info
        agent_id = f"{agent_type}_{int(time.time())}"
        self.current_agents[agent_id] = {
            'agent_type': agent_type,
            'task_id': task_id,
            'task_type': task_type,
            'start_time': time.time(),
            'prompt': prompt[:200]
        }

        # Track agent usage
        if agent_type not in self.agent_performance["by_agent_type"]:
            self.agent_performance["by_agent_type"][agent_type] = {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "average_duration": 0,
                "common_errors": [],
                "task_types": defaultdict(int)
            }

        self.agent_performance["by_agent_type"][agent_type]["total_runs"] += 1
        self.agent_performance["by_agent_type"][agent_type]["task_types"][task_type] += 1

        return agent_id

    def track_agent_completion(self, agent_id: str, result: Dict):
        """Track agent completion and learn from it."""
        if agent_id not in self.current_agents:
            return

        agent_info = self.current_agents[agent_id]
        agent_type = agent_info['agent_type']
        task_type = agent_info['task_type']
        duration = time.time() - agent_info['start_time']

        # Determine success
        success = not bool(result.get('error')) and result.get('status') != 'failed'

        # Update agent performance metrics
        perf = self.agent_performance["by_agent_type"][agent_type]

        if success:
            perf["successful_runs"] += 1
        else:
            perf["failed_runs"] += 1
            error_msg = str(result.get('error', 'Unknown error'))[:100]
            if error_msg not in perf["common_errors"]:
                perf["common_errors"].append(error_msg)
                perf["common_errors"] = perf["common_errors"][-5:]  # Keep last 5

        # Update average duration
        total_runs = perf["successful_runs"] + perf["failed_runs"]
        perf["average_duration"] = (
            (perf["average_duration"] * (total_runs - 1) + duration) / total_runs
        )

        # Update task type performance
        if task_type not in self.agent_performance["by_task_type"]:
            self.agent_performance["by_task_type"][task_type] = {
                "best_agents": [],
                "worst_agents": [],
                "average_duration": 0,
                "success_rate": 0
            }

        task_perf = self.agent_performance["by_task_type"][task_type]

        # Track best/worst agents for this task type
        agent_score = {
            'agent_type': agent_type,
            'success_rate': perf["successful_runs"] / max(1, total_runs),
            'average_duration': perf["average_duration"]
        }

        if success:
            if agent_score not in task_perf["best_agents"]:
                task_perf["best_agents"].append(agent_score)
                task_perf["best_agents"].sort(key=lambda x: x['success_rate'], reverse=True)
                task_perf["best_agents"] = task_perf["best_agents"][:5]
        else:
            if agent_score not in task_perf["worst_agents"]:
                task_perf["worst_agents"].append(agent_score)
                task_perf["worst_agents"] = task_perf["worst_agents"][:5]

        # Store in PRISM for long-term learning
        if self.client:
            try:
                performance_data = {
                    'type': 'agent_performance',
                    'agent_type': agent_type,
                    'task_type': task_type,
                    'success': success,
                    'duration': duration,
                    'error': result.get('error') if not success else None,
                    'timestamp': time.time()
                }

                self.client.store_memory(
                    content=json.dumps(performance_data),
                    tier='LONGTERM',
                    metadata={
                        'importance': 'high' if not success else 'medium',
                        'tags': ['orchestration', 'agent_performance', agent_type]
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to store agent performance: {e}")

        # Clean up
        del self.current_agents[agent_id]
        self.save_agent_performance()

    def learn_chamber_patterns(self, chamber_data: Dict):
        """Learn from chamber operations (parallel work)."""
        chamber_name = chamber_data.get('chamber_name')
        operation = chamber_data.get('operation')
        success = chamber_data.get('success', True)

        if operation == 'merge':
            if success:
                self.orchestration_patterns["chamber_patterns"]["parallel_success"].append({
                    'chamber': chamber_name,
                    'timestamp': time.time()
                })
            else:
                conflict_data = {
                    'chamber': chamber_name,
                    'conflicts': chamber_data.get('conflicts', []),
                    'resolution': chamber_data.get('resolution'),
                    'timestamp': time.time()
                }
                self.orchestration_patterns["chamber_patterns"]["merge_conflicts"].append(conflict_data)

                # Learn from conflict resolution
                if conflict_data['resolution']:
                    self.add_gotcha(f"Chamber {chamber_name} had merge conflicts: {conflict_data['resolution']}")

        elif operation == 'isolation_benefit':
            # Track when isolation helped
            self.orchestration_patterns["chamber_patterns"]["isolation_benefits"].append({
                'chamber': chamber_name,
                'benefit': chamber_data.get('benefit'),
                'timestamp': time.time()
            })

        self.save_orchestration_patterns()

    def add_gotcha(self, gotcha: str):
        """Add a discovered gotcha or important learning."""
        if gotcha not in self.agent_performance["gotchas"]:
            self.agent_performance["gotchas"].append({
                'gotcha': gotcha,
                'discovered_at': time.time()
            })

            # Also store in PRISM as ANCHOR
            if self.client:
                try:
                    self.client.store_memory(
                        content=json.dumps({
                            'type': 'orchestration_gotcha',
                            'gotcha': gotcha,
                            'timestamp': time.time()
                        }),
                        tier='ANCHORS',  # Important learnings are immutable
                        metadata={
                            'importance': 'critical',
                            'tags': ['orchestration', 'gotcha', 'learning']
                        }
                    )
                except Exception as e:
                    logger.debug(f"Failed to store gotcha: {e}")

        self.save_agent_performance()

    def suggest_agent_for_task(self, task_description: str) -> Optional[Dict]:
        """Suggest the best agent for a given task based on history."""
        task_type = self.extract_task_type(task_description)

        if task_type in self.agent_performance["by_task_type"]:
            task_perf = self.agent_performance["by_task_type"][task_type]
            if task_perf["best_agents"]:
                best = task_perf["best_agents"][0]
                return {
                    'suggested_agent': best['agent_type'],
                    'success_rate': best['success_rate'],
                    'average_duration': best['average_duration'],
                    'task_type': task_type
                }

        return None

    def get_agent_warnings(self, agent_type: str) -> List[str]:
        """Get warnings about an agent based on performance history."""
        warnings = []

        if agent_type in self.agent_performance["by_agent_type"]:
            perf = self.agent_performance["by_agent_type"][agent_type]

            total_runs = perf["successful_runs"] + perf["failed_runs"]
            if total_runs > 5:
                success_rate = perf["successful_runs"] / total_runs

                if success_rate < 0.5:
                    warnings.append(f"⚠️ {agent_type} has low success rate: {success_rate:.0%}")

                if perf["average_duration"] > 300:  # More than 5 minutes
                    warnings.append(f"⏰ {agent_type} typically takes {perf['average_duration']:.0f} seconds")

                if perf["common_errors"]:
                    warnings.append(f"🐛 Common errors: {perf['common_errors'][0]}")

        return warnings

    def learn_workflow_sequence(self, agents_used: List[str], success: bool, duration: float, task_description: str = ""):
        """Learn successful agent workflow sequences."""
        task_type = self.extract_task_type(task_description) if task_description else "unknown"

        sequence_data = {
            'agents': agents_used,
            'success': success,
            'duration': duration,
            'timestamp': time.time(),
            'project': self.current_project,
            'task_type': task_type,
            'task_description': task_description[:200]
        }

        self.agent_performance["agent_sequences"].append(sequence_data)

        # Update global patterns
        self.update_global_patterns(task_type, agents_used, success, duration)

        # If successful and fast, store as recommended workflow
        if success and duration < 600:  # Less than 10 minutes
            if len(agents_used) > 2:
                self.orchestration_patterns["successful_workflows"].append({
                    'sequence': agents_used,
                    'duration': duration,
                    'timestamp': time.time()
                })

                # Store in PRISM via universal learner
                learner = get_learner()
                learner.learn_pattern({
                    'type': 'orchestration_workflow',
                    'agents': agents_used,
                    'duration': duration,
                    'success': success,
                    'task_type': task_type,
                    'task_description': task_description[:200],
                    'confidence': 0.8 if success else 0.4
                })

                # Also store directly in PRISM for orchestration-specific queries
                if self.client:
                    try:
                        self.client.store_memory(
                            content=json.dumps({
                                'type': 'successful_workflow',
                                'agents': agents_used,
                                'duration': duration,
                                'timestamp': time.time()
                            }),
                            tier='LONGTERM',
                            metadata={
                                'importance': 'high',
                                'tags': ['orchestration', 'workflow', 'success']
                            }
                        )
                    except Exception as e:
                        logger.debug(f"Failed to store workflow: {e}")

        self.save_agent_performance()
        self.save_orchestration_patterns()
        self.save_global_patterns()

    def update_global_patterns(self, task_type: str, agents: List[str], success: bool, duration: float):
        """Update global cross-project patterns."""
        if task_type not in self.global_patterns["patterns_by_type"]:
            self.global_patterns["patterns_by_type"][task_type] = {
                "successful_sequences": [],
                "failed_sequences": [],
                "average_duration": 0,
                "success_rate": 0,
                "projects": set()
            }

        pattern = self.global_patterns["patterns_by_type"][task_type]

        # Track project diversity
        if isinstance(pattern["projects"], list):
            pattern["projects"] = set(pattern["projects"])
        pattern["projects"].add(self.current_project)

        # Store sequence
        sequence_key = "successful_sequences" if success else "failed_sequences"
        pattern[sequence_key].append({
            "agents": agents,
            "duration": duration,
            "project": self.current_project,
            "timestamp": time.time()
        })

        # Keep only recent sequences
        pattern[sequence_key] = pattern[sequence_key][-20:]

        # Calculate success rate
        success_count = len(pattern["successful_sequences"])
        fail_count = len(pattern["failed_sequences"])
        total = success_count + fail_count
        if total > 0:
            pattern["success_rate"] = success_count / total

        # Calculate average duration of successes
        if pattern["successful_sequences"]:
            durations = [s["duration"] for s in pattern["successful_sequences"]]
            pattern["average_duration"] = sum(durations) / len(durations)

        # Convert set to list for JSON serialization
        pattern["projects"] = list(pattern["projects"])

    def calibrate_confidence(self, predicted_confidence: float, actual_difficulty: str,
                            task_type: str, success: bool, duration: float):
        """Calibrate confidence predictions based on actual outcomes."""
        # Map actual difficulty from outcome metrics
        if not success:
            actual_confidence = 0.2  # Failed tasks were harder than expected
        elif duration < 60:
            actual_confidence = 0.9  # Very quick = easy
        elif duration < 300:
            actual_confidence = 0.7  # Moderate time = medium
        elif duration < 600:
            actual_confidence = 0.5  # Long time = hard
        else:
            actual_confidence = 0.3  # Very long = very hard

        # Store prediction vs actual
        self.confidence_calibration["predictions"].append({
            "predicted": predicted_confidence,
            "actual": actual_confidence,
            "task_type": task_type,
            "success": success,
            "duration": duration,
            "timestamp": time.time()
        })

        # Keep only recent predictions
        self.confidence_calibration["predictions"] = self.confidence_calibration["predictions"][-100:]

        # Calculate calibration factor for this task type
        if task_type not in self.confidence_calibration["calibration_factors"]:
            self.confidence_calibration["calibration_factors"][task_type] = 1.0

        # Get recent predictions for this type
        type_predictions = [
            p for p in self.confidence_calibration["predictions"]
            if p["task_type"] == task_type
        ][-20:]

        if len(type_predictions) >= 5:
            # Calculate mean error
            errors = [p["actual"] - p["predicted"] for p in type_predictions]
            mean_error = sum(errors) / len(errors)

            # Update calibration factor (slowly)
            old_factor = self.confidence_calibration["calibration_factors"][task_type]
            new_factor = old_factor + (mean_error * 0.1)  # Slow adjustment
            self.confidence_calibration["calibration_factors"][task_type] = max(0.5, min(1.5, new_factor))

        # Update accuracy metrics
        if task_type not in self.confidence_calibration["accuracy_by_type"]:
            self.confidence_calibration["accuracy_by_type"][task_type] = {
                "predictions": 0,
                "within_0_1": 0,
                "within_0_2": 0,
                "mean_error": 0
            }

        accuracy = self.confidence_calibration["accuracy_by_type"][task_type]
        accuracy["predictions"] += 1

        error = abs(actual_confidence - predicted_confidence)
        if error <= 0.1:
            accuracy["within_0_1"] += 1
        if error <= 0.2:
            accuracy["within_0_2"] += 1

        # Update mean error
        old_mean = accuracy["mean_error"]
        accuracy["mean_error"] = (old_mean * (accuracy["predictions"] - 1) + error) / accuracy["predictions"]

        self.save_confidence_calibration()

    def get_calibrated_confidence(self, raw_confidence: float, task_type: str) -> float:
        """Apply calibration to raw confidence score."""
        factor = self.confidence_calibration["calibration_factors"].get(task_type, 1.0)
        calibrated = raw_confidence * factor
        return max(0.0, min(1.0, calibrated))

    def promote_pattern_to_prism(self, pattern: Dict, confidence: float):
        """Promote successful pattern to PRISM higher memory tier."""
        # Only promote high-confidence patterns
        if confidence < 0.8:
            return

        # Use universal learner for promotion
        learner = get_learner()

        # Generate pattern ID for promotion
        pattern_id = learner.generate_pattern_id(pattern)

        # Determine tier based on confidence and usage
        if confidence > 0.95 and pattern.get('usage_count', 0) > 10:
            tier = 'ANCHORS'
        elif confidence > 0.85:
            tier = 'LONGTERM'
        else:
            tier = 'EPISODIC'

        # Promote via universal learner
        learner.promote_pattern(pattern_id, tier)

        # Also store directly in PRISM for orchestration-specific queries
        if self.client:
            try:
                self.client.store_memory(
                    content=json.dumps({
                        'type': 'promoted_pattern',
                        'pattern': pattern,
                        'confidence': confidence,
                        'promoted_at': time.time(),
                        'source': 'orchestration_learner'
                    }),
                    tier=tier,
                    metadata={
                        'importance': 'critical' if confidence > 0.95 else 'high',
                        'tags': ['pattern', 'orchestration', 'promoted'],
                        'confidence': confidence
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to promote pattern: {e}")

def main():
    """Main hook execution."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON input")
        sys.exit(1)

    event_type = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")

    # Initialize learner
    learner = OrchestrationLearner()

    result = {"intervention": None}

    # Track Task tool usage (agent launches)
    if tool_name == "Task":
        if event_type == "PreToolUse":
            # Agent is starting
            tool_input = input_data.get("tool_input", {})
            agent_id = learner.track_agent_start(tool_input)

            # Get warnings about this agent
            agent_type = tool_input.get('subagent_type', 'unknown')
            warnings = learner.get_agent_warnings(agent_type)

            # Suggest alternative if poor performance
            suggestion = learner.suggest_agent_for_task(tool_input.get('prompt', ''))

            if warnings or suggestion:
                message_parts = ["## 🎯 Orchestration Intelligence\n"]

                if warnings:
                    message_parts.append("### Agent Warnings")
                    message_parts.extend(warnings)

                if suggestion and suggestion['suggested_agent'] != agent_type:
                    message_parts.append(f"\n### 💡 Suggestion")
                    message_parts.append(f"Consider using **{suggestion['suggested_agent']}** for {suggestion['task_type']} tasks")
                    message_parts.append(f"Success rate: {suggestion['success_rate']:.0%}")

                result = {
                    "intervention": {
                        "type": "suggestion",
                        "severity": "INFO",
                        "message": "\n".join(message_parts)
                    }
                }

            # Store agent_id for tracking
            input_data['_agent_id'] = agent_id

        elif event_type == "PostToolUse":
            # Agent completed
            agent_id = input_data.get('_agent_id')
            if agent_id:
                tool_response = input_data.get("tool_response", {})
                learner.track_agent_completion(agent_id, tool_response)

    # Track chamber operations (from orchestration MCP)
    elif event_type == "OrchestrationEvent":
        event_data = input_data.get("event_data", {})
        if event_data.get('type') == 'chamber_operation':
            learner.learn_chamber_patterns(event_data)
        elif event_data.get('type') == 'workflow_complete':
            learner.learn_workflow_sequence(
                event_data.get('agents', []),
                event_data.get('success', False),
                event_data.get('duration', 0)
            )
        elif event_data.get('type') == 'gotcha':
            learner.add_gotcha(event_data.get('message', ''))

    # Output result
    print(json.dumps(result))

if __name__ == "__main__":
    main()