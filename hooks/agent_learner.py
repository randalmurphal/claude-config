#!/usr/bin/env python3
"""
Agent Learner Hook - Captures Agent Discoveries
================================================
Triggered on SubagentStop to capture what agents learned during execution.
Stores agent findings, patterns, and decisions in PRISM for future use.
"""

import json
import sys
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Import PRISM client and universal learner
sys.path.insert(0, str(Path(__file__).parent))
from prism_client import get_prism_client
from universal_learner import get_learner

class AgentLearner:
    """Captures and stores agent learnings in PRISM."""

    def __init__(self):
        self.client = get_prism_client()
        self.learner = get_learner()
        self.session_id = f"agent_{int(time.time())}"

    def extract_agent_findings(self, agent_type: str, agent_output: str) -> Dict:
        """Extract semantic findings from agent output."""
        findings = {
            "type": "agent_discovery",
            "agent_type": agent_type,
            "patterns": [],
            "decisions": [],
            "errors_fixed": [],
            "files_modified": [],
            "recommendations": [],
            "confidence": 0.7
        }

        # Convert output to lowercase for pattern matching
        output_lower = agent_output.lower()

        # Extract patterns based on agent type
        if "skeleton" in agent_type.lower():
            findings["type"] = "architecture_pattern"
            findings["confidence"] = 0.85
            findings["patterns"] = self.extract_skeleton_patterns(agent_output)

        elif "test" in agent_type.lower():
            findings["type"] = "test_pattern"
            findings["patterns"] = self.extract_test_patterns(agent_output)
            findings["confidence"] = 0.9 if "passed" in output_lower else 0.6

        elif "implement" in agent_type.lower():
            findings["type"] = "implementation_pattern"
            findings["patterns"] = self.extract_implementation_patterns(agent_output)

        elif "validator" in agent_type.lower() or "review" in agent_type.lower():
            findings["type"] = "validation_finding"
            findings["patterns"] = self.extract_validation_issues(agent_output)
            findings["confidence"] = 0.9

        elif "fix" in agent_type.lower() or "debug" in agent_type.lower():
            findings["type"] = "bug_fix"
            findings["errors_fixed"] = self.extract_fixes(agent_output)
            findings["confidence"] = 0.95

        # Extract common patterns across all agent types
        findings["files_modified"] = self.extract_file_paths(agent_output)
        findings["decisions"] = self.extract_decisions(agent_output)
        findings["recommendations"] = self.extract_recommendations(agent_output)

        return findings

    def extract_skeleton_patterns(self, output: str) -> List[str]:
        """Extract architecture and skeleton patterns."""
        patterns = []

        # Look for interface definitions
        if re.search(r'interface|abstract|protocol|trait', output, re.I):
            patterns.append("defined_interfaces")

        # Look for layer separation
        if re.search(r'layer|separation|boundary|module', output, re.I):
            patterns.append("layer_separation")

        # Look for dependency injection
        if re.search(r'inject|dependency|provider|factory', output, re.I):
            patterns.append("dependency_injection")

        # Look for circular dependency issues
        if re.search(r'circular|cyclic|dependency.*cycle', output, re.I):
            patterns.append("circular_dependency_detected")

        return patterns

    def extract_test_patterns(self, output: str) -> List[str]:
        """Extract test-related patterns."""
        patterns = []

        # Test types
        if re.search(r'unit.?test', output, re.I):
            patterns.append("unit_tests")
        if re.search(r'integration.?test', output, re.I):
            patterns.append("integration_tests")
        if re.search(r'e2e|end.?to.?end', output, re.I):
            patterns.append("e2e_tests")

        # Test patterns
        if re.search(r'mock|stub|fake', output, re.I):
            patterns.append("mocking_used")
        if re.search(r'fixture|setup|teardown', output, re.I):
            patterns.append("fixtures_implemented")
        if re.search(r'parameterized|data.?driven', output, re.I):
            patterns.append("parameterized_tests")

        # Test results
        if re.search(r'\d+.*pass', output, re.I):
            patterns.append("tests_passing")
        if re.search(r'\d+.*fail', output, re.I):
            patterns.append("tests_failing")

        return patterns

    def extract_implementation_patterns(self, output: str) -> List[str]:
        """Extract implementation patterns."""
        patterns = []

        # Design patterns
        if re.search(r'singleton|factory|observer|strategy', output, re.I):
            patterns.append("design_pattern_used")

        # Async patterns
        if re.search(r'async|await|promise|concurrent', output, re.I):
            patterns.append("async_implementation")

        # Error handling
        if re.search(r'try|catch|except|error.?handl', output, re.I):
            patterns.append("error_handling_added")

        # Performance
        if re.search(r'cache|memo|optimize|performance', output, re.I):
            patterns.append("performance_optimization")

        return patterns

    def extract_validation_issues(self, output: str) -> List[str]:
        """Extract validation findings."""
        issues = []

        # Common code issues
        if re.search(r'complex|cyclomatic|cognitive', output, re.I):
            issues.append("high_complexity")
        if re.search(r'duplicate|DRY|repeat', output, re.I):
            issues.append("code_duplication")
        if re.search(r'unused|dead.?code|unreachable', output, re.I):
            issues.append("dead_code")
        if re.search(r'security|vulnerability|injection', output, re.I):
            issues.append("security_issue")
        if re.search(r'performance|slow|inefficient', output, re.I):
            issues.append("performance_issue")

        return issues

    def extract_fixes(self, output: str) -> List[str]:
        """Extract bug fixes made."""
        fixes = []

        # Common fix patterns
        if re.search(r'fix.*import|import.*error', output, re.I):
            fixes.append("import_error_fixed")
        if re.search(r'fix.*type|type.*error', output, re.I):
            fixes.append("type_error_fixed")
        if re.search(r'fix.*null|null.*pointer|undefined', output, re.I):
            fixes.append("null_reference_fixed")
        if re.search(r'fix.*race|race.*condition', output, re.I):
            fixes.append("race_condition_fixed")
        if re.search(r'fix.*memory|memory.*leak', output, re.I):
            fixes.append("memory_leak_fixed")

        return fixes

    def extract_file_paths(self, output: str) -> List[str]:
        """Extract file paths mentioned in output."""
        # Common file path patterns
        patterns = [
            r'[\w/\-_.]+\.(?:py|js|ts|go|rs|java|cpp|c|h)',  # Source files
            r'[\w/\-_.]+\.(?:json|yaml|yml|toml|xml)',  # Config files
            r'[\w/\-_.]+\.(?:md|txt|rst)',  # Doc files
        ]

        files = []
        for pattern in patterns:
            matches = re.findall(pattern, output)
            files.extend(matches)

        # Clean and deduplicate
        cleaned_files = []
        for f in set(files):
            # Skip if it looks like a sentence fragment
            if ' ' not in f and len(f) > 3:
                cleaned_files.append(f)

        return cleaned_files[:10]  # Limit to 10 files

    def extract_decisions(self, output: str) -> List[str]:
        """Extract architectural/design decisions."""
        decisions = []

        # Decision keywords
        decision_patterns = [
            r'decided to ([\w\s]+)',
            r'chose ([\w\s]+) because',
            r'using ([\w\s]+) instead of',
            r'implemented ([\w\s]+) pattern',
            r'selected ([\w\s]+) approach',
        ]

        for pattern in decision_patterns:
            matches = re.findall(pattern, output, re.I)
            for match in matches[:3]:  # Limit matches per pattern
                if len(match) < 100:  # Reasonable length
                    decisions.append(match.strip())

        return decisions[:5]  # Limit total decisions

    def extract_recommendations(self, output: str) -> List[str]:
        """Extract recommendations for future work."""
        recommendations = []

        # Recommendation patterns
        rec_patterns = [
            r'should ([\w\s]+)',
            r'recommend ([\w\s]+)',
            r'suggest ([\w\s]+)',
            r'consider ([\w\s]+)',
            r'TODO:? ([\w\s]+)',
        ]

        for pattern in rec_patterns:
            matches = re.findall(pattern, output, re.I)
            for match in matches[:2]:  # Limit matches
                if 10 < len(match) < 100:  # Reasonable length
                    recommendations.append(match.strip())

        return recommendations[:5]  # Limit recommendations

    def store_agent_learning(self, findings: Dict, task_description: str):
        """Store agent learnings in PRISM."""
        if not self.client:
            return

        try:
            # Build semantic content
            content = {
                "type": findings["type"],
                "content": f"{findings['agent_type']} agent discovered: {', '.join(findings['patterns'][:3])}",
                "agent_type": findings["agent_type"],
                "task": task_description[:200],
                "patterns": findings["patterns"],
                "decisions": findings["decisions"],
                "errors_fixed": findings["errors_fixed"],
                "files_modified": findings["files_modified"],
                "recommendations": findings["recommendations"],
                "session_id": self.session_id,
                "timestamp": time.time(),
                "confidence": findings["confidence"]
            }

            # Determine tier based on finding importance
            tier = "WORKING"
            if findings["type"] in ["bug_fix", "security_issue", "architecture_pattern"]:
                tier = "LONGTERM"
            elif findings["confidence"] >= 0.85:
                tier = "LONGTERM"

            # Store in PRISM
            self.client.store_memory(
                content=json.dumps(content),
                tier=tier,
                metadata={
                    "importance": "high" if tier == "LONGTERM" else "medium",
                    "tags": [findings["agent_type"], findings["type"]] + findings["patterns"][:3],
                    "agent": findings["agent_type"]
                }
            )

            # Store specific patterns in learner
            for pattern in findings["patterns"]:
                pattern_data = {
                    "type": f"agent_{pattern}",
                    "content": f"{findings['agent_type']} agent: {pattern}",
                    "agent": findings["agent_type"],
                    "confidence": findings["confidence"]
                }
                self.learner.learn_pattern(pattern_data)

            # Store decisions as critical knowledge
            for decision in findings["decisions"]:
                decision_data = {
                    "type": "design_decision",
                    "content": f"Decision by {findings['agent_type']}: {decision}",
                    "reason": task_description[:100],
                    "confidence": 0.9
                }
                self.learner.learn_pattern(decision_data)

        except Exception as e:
            print(f"Failed to store agent learning: {e}", file=sys.stderr)

    def analyze_agent_performance(self, agent_type: str, duration: float, success: bool) -> Dict:
        """Analyze agent performance metrics."""
        performance = {
            "agent_type": agent_type,
            "duration": duration,
            "success": success,
            "efficiency": "normal"
        }

        # Categorize performance
        if duration < 30:
            performance["efficiency"] = "fast"
        elif duration > 120:
            performance["efficiency"] = "slow"

        # Store performance metric
        if self.client:
            try:
                self.client.store_memory(
                    content=json.dumps({
                        "type": "agent_performance",
                        "agent": agent_type,
                        "duration": duration,
                        "success": success,
                        "efficiency": performance["efficiency"],
                        "timestamp": time.time()
                    }),
                    tier="EPISODIC",
                    metadata={
                        "importance": "low",
                        "tags": ["metrics", "performance", agent_type]
                    }
                )
            except:
                pass

        return performance

def main():
    """Main hook handler for SubagentStop event."""
    try:
        input_data = json.loads(sys.stdin.read())
        event_name = input_data.get("hook_event_name", "")

        # Only process SubagentStop events
        if event_name == "SubagentStop":
            learner = AgentLearner()

            # Extract agent information
            agent_data = input_data.get("agent_data", {})
            agent_type = agent_data.get("agent_type", "unknown")
            agent_output = agent_data.get("output", "")
            task_description = agent_data.get("task", "")
            duration = agent_data.get("duration", 0)

            # Determine success (simple heuristic)
            success = not bool(re.search(r'error|fail|exception|unable', agent_output.lower()))

            # Extract findings from agent output
            findings = learner.extract_agent_findings(agent_type, agent_output)

            # Store the learnings
            learner.store_agent_learning(findings, task_description)

            # Analyze performance
            performance = learner.analyze_agent_performance(agent_type, duration, success)

            # Report summary
            if findings["patterns"] or findings["decisions"]:
                print(f"═══════════════════════════════════════════════", file=sys.stderr)
                print(f"🤖 Agent Learning Captured: {agent_type}", file=sys.stderr)
                print(f"═══════════════════════════════════════════════", file=sys.stderr)

                if findings["patterns"]:
                    print(f"Patterns: {', '.join(findings['patterns'][:5])}", file=sys.stderr)

                if findings["decisions"]:
                    print(f"Decisions: {', '.join(findings['decisions'][:3])}", file=sys.stderr)

                if findings["errors_fixed"]:
                    print(f"Fixes: {', '.join(findings['errors_fixed'][:3])}", file=sys.stderr)

                print(f"Performance: {performance['efficiency']} ({duration:.1f}s)", file=sys.stderr)
                print(f"═══════════════════════════════════════════════", file=sys.stderr)

    except Exception as e:
        print(f"Error in agent_learner: {e}", file=sys.stderr)

    # Always allow operation to continue
    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()