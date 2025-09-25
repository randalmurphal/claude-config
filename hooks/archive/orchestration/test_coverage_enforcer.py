#!/usr/bin/env python3
"""
Test Coverage Enforcement Hook
Verifies test coverage meets oracle targets after test execution.
Now with universal learning integration.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Tuple, Optional

# Import universal learner
sys.path.insert(0, str(Path(__file__).parent))
from universal_learner import get_learner

def parse_pytest_coverage(output: str) -> Tuple[float, float]:
    """Parse pytest coverage output for line and function coverage."""
    # Look for coverage summary lines like:
    # TOTAL    1234   567    54%
    # or Coverage: 85.3% (lines), 92.1% (functions)

    line_coverage = 0.0
    func_coverage = 0.0

    # Try pytest-cov format first
    total_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
    if total_match:
        line_coverage = float(total_match.group(1))
        func_coverage = line_coverage  # Often same if not specified

    # Try alternate format
    cov_match = re.search(r'Coverage:\s+(\d+\.?\d*)%.*?(\d+\.?\d*)%\s*\(functions\)', output)
    if cov_match:
        line_coverage = float(cov_match.group(1))
        func_coverage = float(cov_match.group(2))

    # Try statement coverage format
    stmt_match = re.search(r'(\d+\.?\d*)%\s+statements', output)
    if stmt_match:
        line_coverage = float(stmt_match.group(1))

    return line_coverage, func_coverage

def parse_go_coverage(output: str) -> float:
    """Parse go test coverage output."""
    # Look for: coverage: 78.9% of statements
    match = re.search(r'coverage:\s+(\d+\.?\d*)%', output)
    if match:
        return float(match.group(1))
    return 0.0

def parse_jest_coverage(output: str) -> Tuple[float, float]:
    """Parse jest coverage output."""
    line_coverage = 0.0
    func_coverage = 0.0

    # Look for All files row in jest table
    # All files | 85.71 | 100 | 80 | 85.71
    all_files_match = re.search(r'All files\s+\|\s+(\d+\.?\d*)\s+\|\s+\d+\.?\d*\s+\|\s+(\d+\.?\d*)', output)
    if all_files_match:
        line_coverage = float(all_files_match.group(1))
        func_coverage = float(all_files_match.group(2))

    return line_coverage, func_coverage

def get_oracle_targets() -> Dict[str, float]:
    """Get test oracle targets from orchestration context."""
    # Check if we have stored oracle targets from the current task
    oracle_file = Path.home() / ".claude" / "current_test_oracle.json"

    if oracle_file.exists():
        with open(oracle_file) as f:
            oracle = json.load(f)
            return {
                'line_coverage': oracle.get('coverage_target', 95.0),
                'function_coverage': oracle.get('function_coverage_target', 100.0),
                'complexity': oracle.get('complexity', 'medium')
            }

    # Default targets based on project standards
    return {
        'line_coverage': 95.0,
        'function_coverage': 100.0,
        'complexity': 'unknown'
    }

def identify_coverage_gaps(output: str) -> list:
    """Identify specific files/functions with low coverage."""
    gaps = []

    # Look for files with low coverage in pytest output
    # file.py    100    20    80%
    file_pattern = r'(\S+\.py)\s+\d+\s+\d+\s+(\d+)%'
    for match in re.finditer(file_pattern, output):
        filename = match.group(1)
        coverage = float(match.group(2))
        if coverage < 90:  # Flag files below 90%
            gaps.append(f"{filename}: {coverage}% coverage")

    # Look for missing coverage lines
    # Missing: lines 45-67, 89, 102-145
    missing_pattern = r'(\S+):\s+Missing:?\s+lines?\s+([\d\-,\s]+)'
    for match in re.finditer(missing_pattern, output):
        filename = match.group(1)
        lines = match.group(2)
        gaps.append(f"{filename}: Missing lines {lines}")

    # Look for uncovered functions
    func_pattern = r'(\w+)\s+function\s+not\s+covered'
    for match in re.finditer(func_pattern, output):
        gaps.append(f"Function {match.group(1)} not covered")

    return gaps

def main():
    """Main hook handler."""
    input_data = json.loads(sys.stdin.read())

    # Only run after test execution commands
    if input_data.get('hook_event_name') != 'PostBashExecute':
        print(json.dumps({"action": "continue"}))
        return

    command = input_data.get('command', '')
    output = input_data.get('output', '')
    exit_code = input_data.get('exit_code', 0)

    # Check if this was a test command
    test_commands = ['pytest', 'go test', 'jest', 'npm test', 'npm run test', 'yarn test']
    is_test_command = any(cmd in command for cmd in test_commands)

    if not is_test_command:
        print(json.dumps({"action": "continue"}))
        return

    # Don't enforce on failed tests (they need to pass first)
    if exit_code != 0:
        print(json.dumps({"action": "continue"}))
        return

    # Parse coverage based on test framework
    line_coverage = 0.0
    func_coverage = 0.0

    if 'pytest' in command or 'python -m pytest' in command:
        line_coverage, func_coverage = parse_pytest_coverage(output)
    elif 'go test' in command:
        line_coverage = parse_go_coverage(output)
        func_coverage = line_coverage  # Go doesn't separate function coverage
    elif 'jest' in command or 'npm test' in command or 'yarn test' in command:
        line_coverage, func_coverage = parse_jest_coverage(output)

    # Get oracle targets
    targets = get_oracle_targets()

    # Check if coverage meets targets
    line_target = targets['line_coverage']
    func_target = targets['function_coverage']

    # Learn coverage patterns regardless of pass/fail
    learner = get_learner()

    # Extract file being tested from command if possible
    test_file = "unknown"
    if '--cov=' in command:
        match = re.search(r'--cov=(\S+)', command)
        if match:
            test_file = match.group(1)
    elif 'tests/' in command:
        match = re.search(r'tests/(\S+)', command)
        if match:
            test_file = f"tests/{match.group(1)}"

    # Learn the coverage pattern
    learner.learn_coverage_pattern(
        file=test_file,
        coverage=line_coverage,
        target=line_target,
        test_command=command
    )

    if line_coverage < line_target or func_coverage < func_target:
        # Identify specific gaps
        gaps = identify_coverage_gaps(output)

        # Store coverage data for orchestration to use
        coverage_data = {
            'line_coverage': line_coverage,
            'function_coverage': func_coverage,
            'line_target': line_target,
            'function_target': func_target,
            'gaps': gaps,
            'command': command
        }

        coverage_file = Path.home() / ".claude" / "last_coverage_result.json"
        coverage_file.parent.mkdir(exist_ok=True)
        with open(coverage_file, 'w') as f:
            json.dump(coverage_data, f, indent=2)

        # Learn about the test failure with specific gaps
        if gaps:
            learner.learn_test_failure(
                file=test_file,
                test=command,
                error=f"Coverage below target: {line_coverage:.1f}% < {line_target:.1f}%",
                coverage=line_coverage
            )

        # Block with specific feedback
        error_msg = f"""
❌ TEST COVERAGE BELOW TARGET

Current Coverage:
  Lines: {line_coverage:.1f}% (target: {line_target:.1f}%)
  Functions: {func_coverage:.1f}% (target: {func_target:.1f}%)

Coverage Gaps:
{chr(10).join(f'  - {gap}' for gap in gaps[:5]) if gaps else '  Run with --cov-report=term-missing for details'}

{'More gaps hidden. Total: ' + str(len(gaps)) if len(gaps) > 5 else ''}

Run the test-implementer agent to add missing coverage, or adjust targets if inappropriate.
"""

        print(json.dumps({
            "action": "block",
            "message": error_msg
        }))
        return

    # Coverage meets targets - celebrate!
    if line_coverage >= line_target and func_coverage >= func_target:
        success_msg = f"✅ Coverage targets met! Lines: {line_coverage:.1f}%, Functions: {func_coverage:.1f}%"
        print(json.dumps({
            "action": "continue",
            "message": success_msg
        }), file=sys.stderr)

    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()