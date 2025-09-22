#!/opt/envs/py3.13/bin/python
"""
Auto-Orchestration Detection Hook
Suggests /conduct for complex tasks based on patterns and complexity analysis.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

def load_orchestration_patterns() -> Dict:
    """Load successful orchestration patterns from learner."""
    patterns_file = Path.home() / ".claude" / "orchestration_patterns.json"
    if patterns_file.exists():
        with open(patterns_file) as f:
            return json.load(f)
    return {"successful_workflows": [], "task_types": {}}

def load_agent_performance() -> Dict:
    """Load agent performance data."""
    perf_file = Path.home() / ".claude" / "agent_performance.json"
    if perf_file.exists():
        with open(perf_file) as f:
            return json.load(f)
    return {}

def analyze_task_complexity(description: str) -> Tuple[int, List[str]]:
    """Analyze task description for complexity indicators."""
    complexity_score = 0
    indicators = []

    # File scope indicators
    if re.search(r'\bmultiple\s+files?\b|\bacross\s+files?\b|\ball\s+files?\b', description, re.I):
        complexity_score += 3
        indicators.append("multiple files")

    if re.search(r'\b(\d+)\s+files?\b', description):
        match = re.search(r'\b(\d+)\s+files?\b', description)
        file_count = int(match.group(1))
        if file_count >= 10:
            complexity_score += 5
            indicators.append(f"{file_count} files")
        elif file_count >= 5:
            complexity_score += 3
            indicators.append(f"{file_count} files")

    # Task type indicators
    complex_tasks = [
        (r'\brefactor\b|\brestructure\b|\breorganize\b', "refactoring", 4),
        (r'\bmigrat(e|ion)\b|\bupgrade\b|\bport\b', "migration", 5),
        (r'\bfeature\b|\bimplement\b|\badd\s+support\b', "new feature", 3),
        (r'\barchitect(ure)?\b|\bdesign\b|\bsystem\b', "architecture", 5),
        (r'\boptimiz(e|ation)\b|\bperformance\b', "optimization", 4),
        (r'\btest\s+suite\b|\btest\s+coverage\b|\bcomprehensive\s+test', "test suite", 3),
        (r'\bAPI\b|\bendpoint\b|\bREST\b|\bGraphQL\b', "API work", 3),
        (r'\bdatabase\b|\bschema\b|\bmigration\b', "database work", 4),
        (r'\bsecurity\b|\bauth(entication|orization)\b|\bencrypt', "security", 4),
        (r'\bparallel\b|\bconcurrent\b|\basync\b', "parallelization", 4),
        (r'\bmodulariz(e|ation)\b|\bdecouple\b', "modularization", 4),
        (r'\bbreaking\s+change\b|\bbackward\s+compat', "breaking changes", 5)
    ]

    for pattern, task_type, score in complex_tasks:
        if re.search(pattern, description, re.I):
            complexity_score += score
            indicators.append(task_type)

    # Scope indicators
    if re.search(r'\bentire\b|\bwhole\b|\ball\b|\bcomplete\b|\bfull\b', description, re.I):
        complexity_score += 2
        indicators.append("large scope")

    if re.search(r'\bmulti-?step\b|\bphase\b|\bstage\b', description, re.I):
        complexity_score += 3
        indicators.append("multi-step")

    # Coordination indicators
    if re.search(r'\bcoordinat\b|\borchestrat\b|\bmanage\b', description, re.I):
        complexity_score += 3
        indicators.append("coordination needed")

    if re.search(r'\bdependen(cy|cies)\b|\binter-?related\b', description, re.I):
        complexity_score += 2
        indicators.append("dependencies")

    # Testing indicators
    if re.search(r'\bwith\s+tests?\b|\bincluding\s+tests?\b|\btest.*?coverage\b', description, re.I):
        complexity_score += 2
        indicators.append("testing required")

    return complexity_score, indicators

def find_matching_patterns(description: str, patterns: Dict) -> List[Dict]:
    """Find similar successful orchestration patterns."""
    matches = []
    desc_lower = description.lower()

    # Extract key terms
    key_terms = set(re.findall(r'\b\w+\b', desc_lower))

    for workflow in patterns.get('successful_workflows', []):
        if 'task_description' in workflow:
            workflow_terms = set(re.findall(r'\b\w+\b', workflow['task_description'].lower()))
            overlap = len(key_terms & workflow_terms)
            if overlap > 3:  # Significant overlap
                matches.append({
                    'description': workflow['task_description'][:100],
                    'agents': workflow.get('sequence', []),
                    'duration': workflow.get('duration', 0),
                    'overlap_score': overlap
                })

    # Sort by relevance
    matches.sort(key=lambda x: x['overlap_score'], reverse=True)
    return matches[:3]

def calculate_confidence(complexity_score: int, pattern_matches: List, agent_performance: Dict) -> float:
    """Calculate confidence that orchestration will help."""
    confidence = 0.0

    # Base confidence from complexity
    if complexity_score >= 15:
        confidence = 0.9
    elif complexity_score >= 10:
        confidence = 0.75
    elif complexity_score >= 7:
        confidence = 0.6
    elif complexity_score >= 5:
        confidence = 0.4
    else:
        confidence = 0.2

    # Boost from pattern matches
    if pattern_matches:
        confidence = min(1.0, confidence + 0.1 * len(pattern_matches))

    # Boost from good agent performance
    total_agents = sum(1 for agent, stats in agent_performance.items()
                      if stats.get('total_uses', 0) > 0)
    successful_agents = sum(1 for agent, stats in agent_performance.items()
                           if stats.get('success_rate', 0) > 0.7)

    if total_agents > 0:
        agent_success_ratio = successful_agents / total_agents
        confidence = min(1.0, confidence + 0.1 * agent_success_ratio)

    return confidence

def generate_suggestion(confidence: float, complexity_score: int, indicators: List[str],
                       pattern_matches: List[Dict]) -> str:
    """Generate orchestration suggestion message."""
    if confidence < 0.5:
        return ""  # Don't suggest for low confidence

    suggestion = f"""
🎯 ORCHESTRATION RECOMMENDED

Complexity Score: {complexity_score} ({', '.join(indicators[:3])})
Confidence: {confidence:.0%} that orchestration will improve outcomes

Why orchestration would help:
"""

    # Add specific reasons
    reasons = []
    if 'multiple files' in indicators or 'large scope' in indicators:
        reasons.append("• Parallel work on multiple components")
    if 'refactoring' in indicators:
        reasons.append("• Systematic refactoring with validation")
    if 'new feature' in indicators:
        reasons.append("• Coordinated skeleton → implementation → testing")
    if 'testing required' in indicators:
        reasons.append("• Test oracle generation and coverage enforcement")
    if 'dependencies' in indicators:
        reasons.append("• Dependency analysis and proper sequencing")
    if pattern_matches:
        reasons.append(f"• {len(pattern_matches)} similar successful orchestrations found")

    suggestion += "\n".join(reasons[:4])

    if pattern_matches:
        suggestion += f"\n\nSimilar successful task: {pattern_matches[0]['description']}"
        if pattern_matches[0]['duration'] > 0:
            minutes = pattern_matches[0]['duration'] / 60
            suggestion += f"\n(Completed in {minutes:.1f} minutes)"

    suggestion += "\n\nUse: /conduct \"<your task description>\""

    return suggestion

def main():
    """Main hook handler."""
    input_data = json.loads(sys.stdin.read())

    # Only run on user messages that look like task descriptions
    if input_data.get('hook_event_name') != 'PreUserMessage':
        print(json.dumps({"action": "continue"}))
        return

    message = input_data.get('message', '')

    # Skip if already using /conduct or other commands
    if message.startswith('/'):
        print(json.dumps({"action": "continue"}))
        return

    # Skip very short messages
    if len(message) < 20:
        print(json.dumps({"action": "continue"}))
        return

    # Analyze task complexity
    complexity_score, indicators = analyze_task_complexity(message)

    # Quick exit for simple tasks
    if complexity_score < 5:
        print(json.dumps({"action": "continue"}))
        return

    # Load historical data
    patterns = load_orchestration_patterns()
    agent_performance = load_agent_performance()

    # Find matching patterns
    pattern_matches = find_matching_patterns(message, patterns)

    # Calculate confidence
    confidence = calculate_confidence(complexity_score, pattern_matches, agent_performance)

    # Generate suggestion if confidence is high enough
    suggestion = generate_suggestion(confidence, complexity_score, indicators, pattern_matches)

    if suggestion:
        # Store analysis for orchestration to use
        analysis = {
            'task_description': message,
            'complexity_score': complexity_score,
            'indicators': indicators,
            'confidence': confidence,
            'pattern_matches': pattern_matches
        }

        analysis_file = Path.home() / ".claude" / "last_task_analysis.json"
        analysis_file.parent.mkdir(exist_ok=True)
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)

        # Show suggestion to user
        print(suggestion, file=sys.stderr)

    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()