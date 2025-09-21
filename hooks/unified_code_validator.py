#!/opt/envs/py3.13/bin/python
"""
Unified Code Validator Hook
===========================
Consolidates code validation features from:
- prism_write_validator.py
- code_quality_gate.py
- codet5_analyzer.py

Key Features:
- Hallucination detection using PRISM semantic analysis
- Security scanning (SQL injection, XSS, hardcoded secrets)
- Code quality checks (complexity, maintainability)
- Pattern validation against known good/bad patterns
- Stores validated patterns for reuse
- Provides actionable feedback with fix suggestions
"""

import json
import sys
import re
import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import subprocess

# Import PRISM client
sys.path.append(str(Path(__file__).parent))
from prism_client import get_prism_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
VALIDATED_PATTERNS_FILE = Path.home() / ".claude" / "validated_patterns.json"
COMPLEXITY_THRESHOLD = 10  # Cyclomatic complexity threshold
COGNITIVE_COMPLEXITY_THRESHOLD = 15
HALLUCINATION_CONFIDENCE_THRESHOLD = 0.7
SEMANTIC_DRIFT_THRESHOLD = 0.3

class UnifiedCodeValidator:
    """Unified code validator with security, quality, and hallucination detection."""

    def __init__(self):
        self.client = get_prism_client()
        self.validated_patterns = self.load_validated_patterns()
        self.context_cache = {}

    def load_validated_patterns(self) -> Dict[str, List[Dict]]:
        """Load previously validated code patterns."""
        try:
            if VALIDATED_PATTERNS_FILE.exists():
                with open(VALIDATED_PATTERNS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load validated patterns: {e}")
        return {"good": [], "bad": []}

    def save_validated_patterns(self):
        """Save validated patterns for future reference."""
        try:
            VALIDATED_PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(VALIDATED_PATTERNS_FILE, 'w') as f:
                json.dump(self.validated_patterns, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save validated patterns: {e}")

    def detect_hallucination(self, code: str, file_path: str) -> Tuple[bool, float, str]:
        """
        Detect potential hallucination using PRISM semantic analysis.
        Returns: (is_hallucination, confidence, reason)
        """
        if not self.client:
            return False, 0.0, "PRISM unavailable"

        try:
            # Get context about what this code should do
            context_query = f"file:{file_path} purpose implementation requirements"
            context_results = self.client.search_memory(
                query=context_query,
                tier='LONGTERM',
                limit=3
            )

            if not context_results:
                # No context to compare against
                return False, 0.5, "No context available for validation"

            # Build expected behavior from context
            expected_behavior = []
            for result in context_results:
                try:
                    content = json.loads(result.get('content', '{}'))
                    if 'requirements' in content or 'specification' in content:
                        expected_behavior.append(content)
                except:
                    continue

            # Use PRISM to check semantic drift
            if hasattr(self.client, 'detect_hallucination'):
                hallucination_result = self.client.detect_hallucination(
                    text=code,
                    confidence_threshold=HALLUCINATION_CONFIDENCE_THRESHOLD
                )

                if hallucination_result and hallucination_result.get('risk_level', 0) > 0.7:
                    return True, hallucination_result.get('confidence', 0.8), hallucination_result.get('reason', 'High hallucination risk detected')

            # Check for common hallucination patterns
            hallucination_indicators = [
                (r'# TODO:.*implement', 0.9, "Unimplemented TODO found"),
                (r'raise NotImplementedError', 0.95, "NotImplementedError - code not implemented"),
                (r'pass\s*#.*later', 0.85, "Placeholder pass statement"),
                (r'return None\s*#.*TODO', 0.9, "Placeholder return"),
                (r'print\(["\']Not implemented', 0.95, "Not implemented message"),
                (r'^\s*\.\.\.\s*$', 0.95, "Ellipsis placeholder found"),
            ]

            for pattern, confidence, reason in hallucination_indicators:
                if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                    return True, confidence, reason

            # Check if code matches known bad patterns
            for bad_pattern in self.validated_patterns.get('bad', []):
                if bad_pattern.get('pattern') in code:
                    return True, 0.8, f"Matches known bad pattern: {bad_pattern.get('reason', 'Unknown')}"

            return False, 0.2, "Code appears valid"

        except Exception as e:
            logger.debug(f"Hallucination detection failed: {e}")
            return False, 0.0, f"Detection error: {str(e)}"

    def scan_security_issues(self, code: str, language: str = 'python') -> List[Dict]:
        """Scan for security vulnerabilities."""
        issues = []

        # Common security patterns to check
        security_patterns = [
            # SQL Injection
            (r'f["\'].*SELECT.*WHERE.*{.*}', 'sql_injection', 'CRITICAL',
             'SQL injection vulnerability - use parameterized queries'),
            (r'["\'].*SELECT.*WHERE.*["\'].*\+', 'sql_injection', 'CRITICAL',
             'SQL injection vulnerability - use parameterized queries'),

            # Command Injection
            (r'os\.system\s*\([^)]*\+[^)]*\)', 'command_injection', 'CRITICAL',
             'Command injection risk - use subprocess with list arguments'),
            (r'subprocess\.\w+\s*\([^,)]*(shell\s*=\s*True)', 'command_injection', 'HIGH',
             'Shell=True is dangerous with user input - use list arguments'),

            # XSS
            (r'innerHTML\s*=\s*[^\'\"]*\+', 'xss', 'HIGH',
             'XSS vulnerability - sanitize user input before innerHTML'),
            (r'document\.write\s*\([^)]*\+', 'xss', 'HIGH',
             'XSS vulnerability - avoid document.write with user input'),

            # Hardcoded Secrets
            (r'(password|api_key|secret|token)\s*=\s*["\'][^"\']+["\']', 'hardcoded_secret', 'HIGH',
             'Hardcoded credential detected - use environment variables'),
            (r'["\']([A-Z0-9]{32,})["\']', 'potential_secret', 'MEDIUM',
             'Potential hardcoded secret - verify this is not sensitive'),

            # Weak Crypto
            (r'md5|sha1', 'weak_crypto', 'MEDIUM',
             'Weak cryptographic algorithm - use SHA256 or better'),
            (r'random\.\w+\s*\(.*\)\s*#.*password|token', 'weak_random', 'HIGH',
             'Insecure randomness for secrets - use secrets module'),

            # Path Traversal
            (r'open\s*\([^)]*\+[^)]*\)', 'path_traversal', 'HIGH',
             'Path traversal risk - validate and sanitize file paths'),

            # Eval/Exec
            (r'\beval\s*\(', 'code_execution', 'CRITICAL',
             'eval() is dangerous - find alternative approach'),
            (r'\bexec\s*\(', 'code_execution', 'CRITICAL',
             'exec() is dangerous - find alternative approach'),
        ]

        for pattern, issue_type, severity, message in security_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                issues.append({
                    'type': issue_type,
                    'severity': severity,
                    'message': message,
                    'line': code[:match.start()].count('\n') + 1,
                    'code_snippet': match.group(0)[:100]
                })

        return issues

    def calculate_complexity(self, code: str, language: str = 'python') -> Dict:
        """Calculate code complexity metrics."""
        metrics = {
            'cyclomatic_complexity': 0,
            'cognitive_complexity': 0,
            'lines_of_code': len(code.splitlines()),
            'maintainability_index': 100
        }

        if language == 'python':
            try:
                # Try using radon if available
                result = subprocess.run(
                    ['radon', 'cc', '-s', '-j', '-'],
                    input=code,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    radon_data = json.loads(result.stdout)
                    if radon_data:
                        # Extract complexity from radon output
                        for item in radon_data.get('-', []):
                            metrics['cyclomatic_complexity'] = max(
                                metrics['cyclomatic_complexity'],
                                item.get('complexity', 0)
                            )
            except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
                # Fallback to simple heuristic
                metrics['cyclomatic_complexity'] = self._estimate_complexity(code)

        # Estimate cognitive complexity (simplified)
        cognitive_indicators = [
            (r'\bif\b', 1), (r'\belif\b', 1), (r'\belse\b', 0.5),
            (r'\bfor\b', 1), (r'\bwhile\b', 1.5),
            (r'\btry\b', 1), (r'\bexcept\b', 1),
            (r'\band\b', 0.5), (r'\bor\b', 0.5),
            (r'\bnot\b', 0.5), (r'lambda', 1.5),
            (r'[^=]=[^=]', 0.1),  # Conditions
        ]

        for pattern, weight in cognitive_indicators:
            matches = len(re.findall(pattern, code))
            metrics['cognitive_complexity'] += matches * weight

        # Calculate maintainability index (simplified)
        # MI = 171 - 5.2*ln(V) - 0.23*CC - 16.2*ln(LOC)
        import math
        loc = max(1, metrics['lines_of_code'])
        cc = max(1, metrics['cyclomatic_complexity'])
        volume = loc * math.log(max(1, len(set(re.findall(r'\w+', code)))))  # Simplified Halstead volume

        metrics['maintainability_index'] = max(0, min(100,
            171 - 5.2 * math.log(volume) - 0.23 * cc - 16.2 * math.log(loc)
        ))

        return metrics

    def _estimate_complexity(self, code: str) -> int:
        """Simple complexity estimation when tools unavailable."""
        complexity = 1  # Base complexity

        # Count decision points
        decision_patterns = [
            r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
            r'\bexcept\b', r'\bcase\b', r'\bwhen\b'
        ]

        for pattern in decision_patterns:
            complexity += len(re.findall(pattern, code))

        return complexity

    def retrieve_similar_patterns(self, code: str) -> Tuple[List[Dict], List[Dict]]:
        """Retrieve similar validated patterns from memory."""
        good_matches = []
        bad_matches = []

        if not self.client:
            return good_matches, bad_matches

        try:
            # Search for similar code patterns
            code_snippet = code[:200]  # Use first 200 chars for search
            results = self.client.search_memory(
                query=code_snippet,
                tier='ANCHORS',  # Validated patterns stored as anchors
                limit=5
            )

            for result in results:
                try:
                    content = json.loads(result.get('content', '{}'))
                    if content.get('type') == 'validated_pattern':
                        pattern_data = {
                            'pattern': content.get('pattern', ''),
                            'reason': content.get('reason', ''),
                            'score': result.get('score', 0)
                        }

                        if content.get('quality') == 'good':
                            good_matches.append(pattern_data)
                        else:
                            bad_matches.append(pattern_data)
                except:
                    continue

        except Exception as e:
            logger.debug(f"Failed to retrieve patterns: {e}")

        return good_matches, bad_matches

    def store_validation_result(self, code: str, file_path: str, is_valid: bool, issues: List[Dict]):
        """Store validation results for learning."""
        if not self.client:
            return

        try:
            validation_data = {
                'type': 'validated_pattern',
                'file_path': file_path,
                'code_snippet': code[:500],  # Store first 500 chars
                'quality': 'good' if is_valid else 'bad',
                'issues': issues,
                'timestamp': time.time()
            }

            # Store as ANCHOR if it's a significant pattern
            if len(issues) > 0 or is_valid:
                self.client.store_memory(
                    content=json.dumps(validation_data),
                    tier='ANCHORS' if len(issues) > 2 else 'LONGTERM',
                    metadata={
                        'importance': 'high' if len(issues) > 2 else 'medium',
                        'tags': ['validation', 'pattern', 'code_quality']
                    }
                )
        except Exception as e:
            logger.debug(f"Failed to store validation result: {e}")

    def format_validation_feedback(self, issues: Dict) -> str:
        """Format validation issues into actionable feedback."""
        if not any(issues.values()):
            return ""

        feedback = ["# 🔍 Code Validation Report\n"]

        # Hallucination detection results
        if issues.get('hallucination'):
            h = issues['hallucination']
            if h['detected']:
                feedback.append(f"## 🤖 Hallucination Detected (Confidence: {h['confidence']:.0%})")
                feedback.append(f"**Reason:** {h['reason']}")
                feedback.append("**Fix:** Implement actual logic instead of placeholders\n")

        # Security issues
        if issues.get('security'):
            feedback.append("## 🔒 Security Issues Found")
            critical = [i for i in issues['security'] if i['severity'] == 'CRITICAL']
            high = [i for i in issues['security'] if i['severity'] == 'HIGH']
            medium = [i for i in issues['security'] if i['severity'] == 'MEDIUM']

            if critical:
                feedback.append(f"### 🚨 CRITICAL ({len(critical)} issues)")
                for issue in critical[:3]:
                    feedback.append(f"- **Line {issue['line']}:** {issue['message']}")
                    feedback.append(f"  Code: `{issue['code_snippet']}`")

            if high:
                feedback.append(f"### ⚠️ HIGH ({len(high)} issues)")
                for issue in high[:3]:
                    feedback.append(f"- **Line {issue['line']}:** {issue['message']}")

        # Complexity issues
        if issues.get('complexity'):
            metrics = issues['complexity']
            if metrics['cyclomatic_complexity'] > COMPLEXITY_THRESHOLD:
                feedback.append("## 📊 Complexity Warning")
                feedback.append(f"- **Cyclomatic Complexity:** {metrics['cyclomatic_complexity']} (threshold: {COMPLEXITY_THRESHOLD})")
                feedback.append("- **Suggestion:** Break down into smaller functions")

            if metrics['cognitive_complexity'] > COGNITIVE_COMPLEXITY_THRESHOLD:
                feedback.append(f"- **Cognitive Complexity:** {metrics['cognitive_complexity']:.1f} (threshold: {COGNITIVE_COMPLEXITY_THRESHOLD})")
                feedback.append("- **Suggestion:** Simplify nested conditions and logic")

            if metrics['maintainability_index'] < 50:
                feedback.append(f"- **Maintainability Index:** {metrics['maintainability_index']:.0f}/100")
                feedback.append("- **Suggestion:** Refactor for better readability")

        # Similar patterns found
        if issues.get('similar_patterns'):
            good, bad = issues['similar_patterns']
            if bad:
                feedback.append("## ⚠️ Similar Anti-Patterns Detected")
                for pattern in bad[:2]:
                    feedback.append(f"- {pattern['reason']} (relevance: {pattern['score']:.0%})")

            if good:
                feedback.append("## ✅ Matches Good Patterns")
                for pattern in good[:2]:
                    feedback.append(f"- {pattern['reason']} (relevance: {pattern['score']:.0%})")

        return "\n".join(feedback) if len(feedback) > 1 else ""

    def validate_code(self, code: str, file_path: str, operation: str) -> Dict:
        """Main validation function."""
        issues = {}

        # 1. Detect hallucination
        is_hallucination, confidence, reason = self.detect_hallucination(code, file_path)
        issues['hallucination'] = {
            'detected': is_hallucination,
            'confidence': confidence,
            'reason': reason
        }

        # 2. Security scanning
        security_issues = self.scan_security_issues(code)
        if security_issues:
            issues['security'] = security_issues

        # 3. Complexity analysis
        complexity_metrics = self.calculate_complexity(code)
        if (complexity_metrics['cyclomatic_complexity'] > COMPLEXITY_THRESHOLD or
            complexity_metrics['cognitive_complexity'] > COGNITIVE_COMPLEXITY_THRESHOLD or
            complexity_metrics['maintainability_index'] < 50):
            issues['complexity'] = complexity_metrics

        # 4. Check against known patterns
        good_patterns, bad_patterns = self.retrieve_similar_patterns(code)
        if good_patterns or bad_patterns:
            issues['similar_patterns'] = (good_patterns, bad_patterns)

        # Store validation result for learning
        is_valid = not (is_hallucination or any(i['severity'] == 'CRITICAL' for i in security_issues))
        self.store_validation_result(code, file_path, is_valid, issues)

        return issues

def main():
    """Main hook execution."""
    import time

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON input")
        sys.exit(1)

    # Process Write, Edit, MultiEdit tools
    tool_name = input_data.get("tool_name", "")
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        sys.exit(0)

    event_type = input_data.get("hook_event_name", "")

    # Only process pre-execution for validation
    if event_type != "PreToolUse":
        sys.exit(0)

    # Initialize validator
    validator = UnifiedCodeValidator()

    # Get code content based on tool type
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name == "Write":
        code = tool_input.get("content", "")
    elif tool_name == "Edit":
        code = tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        # For multi-edit, validate all new strings
        edits = tool_input.get("edits", [])
        code = "\n".join(edit.get("new_string", "") for edit in edits)
    else:
        code = ""

    if not code or not file_path:
        sys.exit(0)

    # Validate the code
    issues = validator.validate_code(code, file_path, tool_name)

    # Format feedback
    feedback = validator.format_validation_feedback(issues)

    # Determine intervention level
    intervention = None

    if issues.get('hallucination', {}).get('detected'):
        # Block hallucinated code
        intervention = {
            "type": "block_execution",
            "severity": "HIGH",
            "message": feedback or "Hallucination detected - implement actual logic"
        }
    elif any(i['severity'] == 'CRITICAL' for i in issues.get('security', [])):
        # Block critical security issues
        intervention = {
            "type": "block_execution",
            "severity": "CRITICAL",
            "message": feedback or "Critical security vulnerability detected"
        }
    elif feedback:
        # Warn about other issues
        intervention = {
            "type": "warning",
            "severity": "MEDIUM",
            "message": feedback
        }

    # Output result
    if intervention:
        print(json.dumps({"intervention": intervention}))
    else:
        print(json.dumps({"intervention": None}))

if __name__ == "__main__":
    main()