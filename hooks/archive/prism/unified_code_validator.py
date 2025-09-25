#!/usr/bin/env python3
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
- Universal learning integration for validation patterns
"""

import json
import sys
import re
import ast
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import subprocess

# Import semantic analyzer, PRISM client, universal learner, no_fallback enforcer, and preference manager
sys.path.append(str(Path(__file__).parent))
from semantic_code_analyzer import get_semantic_analyzer
from prism_client import get_prism_client
from universal_learner import get_learner
from no_fallback_enforcer import NoFallbackEnforcer
from preference_manager import get_preference_manager

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
        self.semantic_analyzer = get_semantic_analyzer()  # REQUIRED for code analysis
        self.client = get_prism_client()
        self.no_fallback = NoFallbackEnforcer()
        self.learner = get_learner()
        self.preference_manager = get_preference_manager()
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

    def detect_logical_drift(self, code: str, file_path: str) -> Dict[str, Any]:
        """
        Detect logical drift using CodeT5+ semantic analysis.
        Returns detailed analysis of potential issues.
        """
        issues = []

        try:
            # Get expected behavior from context
            expected_behavior = self._extract_expected_behavior(code, file_path)

            if expected_behavior:
                # Use CodeT5+ semantic analysis
                logic_analysis = self.semantic_analyzer.analyze_code_logic(
                    code,
                    expected_behavior,
                    cache_key=f"{file_path}:logic"
                )

                if logic_analysis.get('has_issues'):
                    for issue in logic_analysis.get('logical_issues', []):
                        issues.append({
                            'type': 'logical_drift',
                            'severity': 'HIGH' if 'invert' in issue.lower() or 'missing auth' in issue.lower() else 'MEDIUM',
                            'message': issue,
                            'suggestion': "Review the implementation to ensure it matches requirements",
                            'what_code_does': logic_analysis.get('what_code_does', ''),
                            'what_was_expected': logic_analysis.get('what_was_expected', '')
                        })

            # Also detect patterns and anti-patterns using CodeT5+
            pattern_analysis = self.semantic_analyzer.detect_code_patterns(
                code,
                cache_key=f"{file_path}:patterns"
            )

            # Add anti-patterns as issues
            anti_patterns = pattern_analysis['anti_patterns'] if 'anti_patterns' in pattern_analysis else []
            suggestions = pattern_analysis['suggestions'] if 'suggestions' in pattern_analysis else []

            for anti_pattern in anti_patterns:
                severity = 'CRITICAL' if any(x in anti_pattern for x in ['SQL injection', 'Command injection', 'Hardcoded']) else 'HIGH'
                # Use first suggestion if available
                suggestion = suggestions[0] if suggestions else f"Fix this anti-pattern: {anti_pattern}"

                issues.append({
                    'type': 'anti_pattern',
                    'severity': severity,
                    'message': anti_pattern,
                    'suggestion': suggestion
                })

            return {
                'has_drift': len(issues) > 0,
                'issues': issues,
                'summary': f"Found {len(issues)} code quality issues"
            }

        except Exception as e:
            logger.error(f"Logical drift detection failed: {e}")
            # NO FALLBACK - if semantic analysis fails, we fail loudly
            raise RuntimeError(f"Cannot analyze code logic - semantic analyzer required: {e}")

    def detect_hallucination(self, code: str, file_path: str) -> Tuple[bool, float, str]:
        """
        Detect potential hallucination using PRISM semantic analysis.
        Returns: (is_hallucination, confidence, reason)
        """
        if not self.client:
            return False, 0.0, "PRISM unavailable"

        try:
            # First check for logical drift
            drift_analysis = self.detect_logical_drift(code, file_path)
            if drift_analysis.get('has_drift'):
                high_severity_issues = [i for i in drift_analysis.get('issues', []) if i.get('severity') == 'HIGH']
                if high_severity_issues:
                    return True, 0.85, f"Logical drift detected: {high_severity_issues[0].get('message', '')}"

            # Get context about what this code should do
            context_query = f"file:{file_path} purpose implementation requirements"
            context_results = self.client.search_memory(
                context_query,
                limit=3,
                tiers=['LONGTERM']
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
        """Scan for security vulnerabilities using CodeT5+ semantic analysis."""
        issues = []

        try:
            # Use semantic analyzer to detect patterns and anti-patterns
            pattern_analysis = self.semantic_analyzer.detect_code_patterns(
                code,
                cache_key=f"security:{hashlib.md5(code.encode()).hexdigest()[:8]}"
            )

            # Convert anti-patterns to security issues
            anti_patterns = pattern_analysis['anti_patterns'] if 'anti_patterns' in pattern_analysis else []
            for anti_pattern in anti_patterns:
                # Determine severity based on pattern content
                severity = 'CRITICAL' if any(x in anti_pattern for x in ['SQL injection', 'Command injection', 'eval', 'exec']) else \
                          'HIGH' if any(x in anti_pattern for x in ['Hardcoded', 'password', 'XSS', 'Path traversal']) else \
                          'MEDIUM'

                # Suggestions is a list, not a dict mapping to anti-patterns
                # Use the first suggestion if available, or provide specific guidance
                suggestions = pattern_analysis['suggestions'] if 'suggestions' in pattern_analysis else []
                suggestion = suggestions[0] if suggestions else f"Fix this security issue: {anti_pattern}"

                issues.append({
                    'type': 'security_vulnerability',
                    'severity': severity,
                    'message': anti_pattern,
                    'suggestion': suggestion
                })

            # Also check for security-specific patterns that CodeT5+ found
            if pattern_analysis.get('security_issues'):
                for security_issue in pattern_analysis['security_issues']:
                    issues.append({
                        'type': 'security_vulnerability',
                        'severity': security_issue.get('severity', 'HIGH'),
                        'message': security_issue.get('message', 'Security issue detected'),
                        'suggestion': security_issue.get('suggestion', 'Review and fix this issue')
                    })

        except Exception as e:
            logger.error(f"Security scan with semantic analyzer failed: {e}")
            # NO FALLBACK - semantic analysis required for security
            raise RuntimeError(f"Cannot scan for security issues - semantic analyzer required: {e}")

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
                            # Ensure item is a dict before calling .get()
                            if isinstance(item, dict):
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

    def _extract_functions(self, code: str) -> List[Dict]:
        """Extract function definitions with their docstrings."""
        functions = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_info = {
                        'name': node.name,
                        'code': ast.unparse(node) if hasattr(ast, 'unparse') else ast.get_source_segment(code, node),
                        'docstring': ast.get_docstring(node) or '',
                        'args': [arg.arg for arg in node.args.args]
                    }
                    functions.append(func_info)
        except:
            # Fallback to regex for non-Python or parse errors
            func_pattern = r'(?:def|function|func)\s+(\w+)\s*\([^)]*\)'
            for match in re.finditer(func_pattern, code):
                functions.append({
                    'name': match.group(1),
                    'code': code,  # Use full code as fallback
                    'docstring': '',
                    'args': []
                })
        return functions

    def _name_to_intent(self, func_name: str) -> str:
        """Convert function name to likely intent."""
        # Convert camelCase or snake_case to readable intent
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|\d+', func_name)
        words = [w.lower() for w in words]

        # Common patterns
        if words[0] in ['get', 'fetch', 'retrieve', 'load']:
            return ' '.join(words[1:]) + ' and return it'
        elif words[0] in ['set', 'save', 'store', 'update']:
            return 'update ' + ' '.join(words[1:])
        elif words[0] in ['is', 'has', 'can', 'should']:
            return 'check if ' + ' '.join(words[1:])
        elif words[0] in ['validate', 'verify', 'check']:
            return 'ensure ' + ' '.join(words[1:]) + ' is valid'
        elif words[0] in ['calculate', 'compute']:
            return 'calculate ' + ' '.join(words[1:])
        else:
            return ' '.join(words)

    def _extract_expected_behavior(self, code: str, file_path: str) -> Optional[str]:
        """Extract expected behavior from various sources."""
        expected_parts = []

        # Try to get from PRISM memory
        if self.client:
            try:
                results = self.client.search_memory(
                    f"file:{file_path} expected behavior intent requirements",
                    limit=2,
                    tiers=["WORKING"]
                )
                for result in results:
                    if 'content' in result:
                        expected_parts.append(result['content'])
            except Exception as e:
                logger.debug(f"Could not retrieve expected behavior from PRISM: {e}")

        # Extract from function names and docstrings
        functions = self._extract_functions(code)
        for func in functions[:3]:  # First 3 functions
            func_name = func.get('name', '')
            docstring = func.get('docstring', '')

            if func_name:
                expected_parts.append(f"Function {func_name} should {self._name_to_intent(func_name)}")
            if docstring and len(docstring) > 20:
                expected_parts.append(f"Documentation: {docstring}")

        # Extract from comments about purpose
        import re
        purpose_patterns = [
            r'# Purpose: (.*)',
            r'# Expected: (.*)',
            r'# Should: (.*)'
        ]
        for pattern in purpose_patterns:
            matches = re.findall(pattern, code)
            expected_parts.extend(matches[:2])

        if expected_parts:
            return " ".join(expected_parts)[:1000]  # Limit length

        return None

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
                code_snippet,
                limit=5,
                tiers=['ANCHORS']  # Validated patterns stored as anchors
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

        # Logical drift results
        if issues.get('logical_drift', {}).get('has_drift'):
            feedback.append("## 🧠 Logical Drift Detected")
            for issue in issues['logical_drift'].get('issues', [])[:5]:  # Show first 5
                severity = issue.get('severity', 'MEDIUM')
                feedback.append(f"### {severity}: {issue.get('message', 'Logic issue')}")
                if issue.get('suggestion'):
                    feedback.append(f"**Fix:** {issue['suggestion']}")
                if issue.get('what_code_does'):
                    feedback.append(f"**Code does:** {issue['what_code_does']}")
                if issue.get('what_was_expected'):
                    feedback.append(f"**Expected:** {issue['what_was_expected']}")
            feedback.append("")

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
                    feedback.append(f"- {issue['message']}")
                    if issue.get('suggestion'):
                        feedback.append(f"  **Fix:** {issue['suggestion']}")

            if high:
                feedback.append(f"### ⚠️ HIGH ({len(high)} issues)")
                for issue in high[:3]:
                    feedback.append(f"- {issue['message']}")
                    if issue.get('suggestion'):
                        feedback.append(f"  **Fix:** {issue['suggestion']}")

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
        """Main validation function - runs ALL analyses and returns ALL issues."""
        all_issues = {}

        # Run ALL analyses - don't stop at first issue

        # 1. Logical drift and pattern detection using CodeT5+
        try:
            logical_analysis = self.detect_logical_drift(code, file_path)
            if logical_analysis.get('has_drift'):
                all_issues['logical_drift'] = logical_analysis
        except Exception as e:
            logger.error(f"Logical analysis failed: {e}")
            all_issues['logical_drift'] = {'error': str(e)}

        # 2. User preferences (HIGHEST PRIORITY)
        try:
            preference_violations = self.preference_manager.check_violations(code, file_path)
            if preference_violations:
                all_issues['preference_violations'] = preference_violations
                # Mark severity based on tier
                for violation in preference_violations:
                    if violation.get('tier') == 'ANCHORS':
                        violation['severity'] = 'CRITICAL'
                    elif violation.get('tier') == 'LONGTERM':
                        violation['severity'] = 'HIGH'
                    else:
                        violation['severity'] = 'MEDIUM'

                    # Learn from repeated violations
                    if violation.get('correction_count', 0) >= 2:
                        self.learner.learn_pattern({
                            "type": "preference_violation",
                            "content": f"Repeated violation: {violation.get('rule', 'unknown')}",
                            "file": file_path,
                            "frustration_level": min(1.0, violation.get('correction_count', 0) * 0.3),
                            "confidence": 0.95
                        })
        except Exception as e:
            logger.error(f"Preference check failed: {e}")

        # 3. Fallback patterns (NO FALLBACKS ALLOWED)
        try:
            fallback_violations = self.no_fallback.check_for_fallback_patterns(code)
            if fallback_violations:
                all_issues['fallback_violations'] = fallback_violations
                for violation in fallback_violations:
                    self.learner.learn_pattern({
                        "type": "bad_pattern",
                        "subtype": "fallback_detected",
                        "content": f"Fallback pattern: {violation.get('description', '')}",
                        "file": file_path,
                        "confidence": 0.95
                    })
        except Exception as e:
            logger.error(f"Fallback check failed: {e}")

        # 4. Security scanning using CodeT5+
        try:
            security_issues = self.scan_security_issues(code)
            if security_issues:
                all_issues['security'] = security_issues
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            all_issues['security'] = [{'error': str(e)}]

        # 5. Hallucination detection
        try:
            is_hallucination, confidence, reason = self.detect_hallucination(code, file_path)
            if is_hallucination:
                all_issues['hallucination'] = {
                    'detected': True,
                    'confidence': confidence,
                    'reason': reason
                }
        except Exception as e:
            logger.error(f"Hallucination detection failed: {e}")

        # 6. Complexity analysis
        try:
            complexity_metrics = self.calculate_complexity(code)
            if (complexity_metrics['cyclomatic_complexity'] > COMPLEXITY_THRESHOLD or
                complexity_metrics['cognitive_complexity'] > COGNITIVE_COMPLEXITY_THRESHOLD or
                complexity_metrics['maintainability_index'] < 50):
                all_issues['complexity'] = complexity_metrics
        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")

        # 7. Check against known patterns
        try:
            good_patterns, bad_patterns = self.retrieve_similar_patterns(code)
            if bad_patterns:
                all_issues['bad_patterns'] = bad_patterns
            if good_patterns:
                all_issues['good_patterns'] = good_patterns
        except Exception as e:
            logger.error(f"Pattern retrieval failed: {e}")

        # Store validation result for learning
        try:
            has_critical = self._has_critical_issues(all_issues)
            self.store_validation_result(code, file_path, not has_critical, all_issues)
        except Exception as e:
            logger.debug(f"Failed to store validation result: {e}")

        return all_issues

    def _has_critical_issues(self, issues: Dict) -> bool:
        """Check if any critical issues found."""
        # Check logical drift
        if 'logical_drift' in issues and issues['logical_drift'].get('has_drift'):
            for issue in issues['logical_drift'].get('issues', []):
                if issue.get('severity') in ['CRITICAL', 'HIGH']:
                    return True

        # Check security
        if 'security' in issues:
            for issue in issues['security']:
                if issue.get('severity') == 'CRITICAL':
                    return True

        # Check preferences (ANCHORS tier)
        if 'preference_violations' in issues:
            for violation in issues['preference_violations']:
                if violation.get('severity') == 'CRITICAL' or violation.get('tier') == 'ANCHORS':
                    return True

        # Check fallbacks
        if 'fallback_violations' in issues and issues['fallback_violations']:
            return True

        # Check hallucination
        if 'hallucination' in issues and issues['hallucination'].get('detected'):
            return True

        return False

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

    # Learn from validation errors using universal learner
    learner = get_learner()

    # Collect ALL validation errors (don't stop at first category)
    all_errors = []
    error_types = []
    has_critical = False
    has_high = False

    # 1. Logical drift issues (using CodeT5+)
    if issues.get('logical_drift', {}).get('has_drift'):
        error_types.append("logical_drift")
        all_errors.append("## 🧠 Logical Drift Detected:")
        for issue in issues['logical_drift'].get('issues', []):
            severity_marker = "❌" if issue.get('severity') == 'CRITICAL' else "⚠️" if issue.get('severity') == 'HIGH' else "ℹ️"
            all_errors.append(f"{severity_marker} {issue.get('message', 'Logic issue')}")
            if issue.get('suggestion'):
                all_errors.append(f"  FIX: {issue['suggestion']}")

            if issue.get('severity') == 'CRITICAL':
                has_critical = True
            elif issue.get('severity') == 'HIGH':
                has_high = True

    # 2. User preference violations
    if issues.get('preference_violations'):
        error_types.append("preference_violation")
        all_errors.append("## 📝 User Preference Violations:")
        for violation in issues['preference_violations']:
            # Check severity without fallback
            if 'severity' not in violation:
                violation['severity'] = 'MEDIUM'  # Must be explicit

            severity_marker = "❌" if violation['severity'] == 'CRITICAL' else "⚠️"
            all_errors.append(f"{severity_marker} {violation['message']}")

            if 'correction_count' in violation and violation['correction_count'] >= 2:
                all_errors.append(f"  🔴 BLOCKED: You've corrected this {violation['correction_count']} times!")

            if violation['severity'] == 'CRITICAL':
                has_critical = True  # This will block execution
            elif violation['severity'] == 'HIGH':
                has_high = True

    # 3. Fallback violations
    if issues.get('fallback_violations'):
        error_types.append("fallback_violation")
        has_critical = True
        all_errors.append("\n## ❌ Forbidden Patterns:")
        for violation in issues['fallback_violations']:
            all_errors.append(f"- {violation['description']}")
            suggestion = validator.no_fallback.suggest_proper_solution(violation)
            all_errors.append(f"  FIX: {suggestion}")

    # 4. Hallucination detection
    if issues.get('hallucination', {}).get('detected'):
        error_types.append("hallucination")
        has_high = True
        all_errors.append(f"\n## 🤔 Hallucination Detected:")
        all_errors.append(f"- {issues['hallucination']['reason']}")

    # 5. Security issues
    if issues.get('security'):
        error_types.append("security")
        all_errors.append("\n## 🔒 Security Issues:")
        for sec_issue in issues['security']:
            all_errors.append(f"- {sec_issue['type']}: {sec_issue.get('message', '')}")
            if sec_issue.get('severity') == 'CRITICAL':
                has_critical = True

    # 6. Complexity issues
    if issues.get('complexity'):
        error_types.append("complexity")
        all_errors.append("\n## 📊 Complexity Issues:")
        all_errors.append(f"- Cyclomatic: {issues['complexity']['cyclomatic_complexity']} (threshold: {COMPLEXITY_THRESHOLD})")
        all_errors.append(f"- Cognitive: {issues['complexity']['cognitive_complexity']} (threshold: {COGNITIVE_COMPLEXITY_THRESHOLD})")
        all_errors.append(f"- Maintainability: {issues['complexity']['maintainability_index']:.1f} (should be > 50)")

    # Learn if there are errors
    if all_errors:
        learner.learn_pattern({
            "type": "validation_error",
            "file": file_path,
            "errors": all_errors,
            "error_types": error_types,  # Now plural, tracks all types
            "context": f"Multiple validation errors in {file_path}"
        })

    # Format feedback
    feedback = validator.format_validation_feedback(issues)

    # Determine intervention level based on ALL issues found
    intervention = None

    if all_errors:
        # Determine severity based on worst violation
        if has_critical:
            severity = "CRITICAL"
            action = "block_execution"
            header = "❌ BLOCKED: Critical issues detected"
        elif has_high:
            severity = "HIGH"
            action = "block_execution"
            header = "❌ BLOCKED: High-priority issues detected"
        else:
            severity = "MEDIUM"
            action = "warning"
            header = "⚠️ WARNING: Issues detected"

        # Build comprehensive message with ALL violations
        message_parts = [
            header,
            "",
            "Please fix ALL of the following issues:",
            ""
        ]
        message_parts.extend(all_errors)

        # Add summary of what needs fixing
        message_parts.extend([
            "",
            "## 📋 Summary:",
            f"Found {len(error_types)} categories of issues: {', '.join(error_types)}",
            "",
            "Fix all issues before proceeding. This prevents multiple back-and-forth corrections."
        ])

        intervention = {
            "type": action,
            "severity": severity,
            "message": "\n".join(message_parts)
        }

    # Output result
    if intervention:
        print(json.dumps({"intervention": intervention}))
    else:
        print(json.dumps({"intervention": None}))

if __name__ == "__main__":
    main()