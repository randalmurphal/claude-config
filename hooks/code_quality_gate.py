#!/usr/bin/env python3
"""
Unified Code Quality Gate Hook for Claude Code
Combines critical pattern checking with language-specific complexity analysis
"""

import re
import json
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class CodeQualityGate:
    def __init__(self):
        self.working_directory = Path.cwd()
        self.cache_dir = Path.home() / '.claude' / 'quality-tools' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"{hash(str(self.working_directory))}.json"
        self.complexity_cache = self.load_cache()
        
        # Load user preferences if they exist
        self.project_hash = hash(str(self.working_directory))
        self.prefs_file = Path.home() / '.claude' / 'preferences' / 'projects' / f'{self.project_hash}.json'
        self.preferences = self.load_preferences()
        
    def load_preferences(self) -> dict:
        """Load project-specific preferences including venv paths"""
        if self.prefs_file.exists():
            try:
                with open(self.prefs_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def load_cache(self) -> dict:
        """Load cached complexity scores"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    # Clean old entries (> 7 days)
                    current_time = time.time()
                    cleaned = {}
                    for key, value in data.items():
                        if current_time - value.get('timestamp', 0) < 604800:  # 7 days
                            cleaned[key] = value
                    return cleaned
            except:
                pass
        return {}
    
    def save_cache(self):
        """Save complexity scores to cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.complexity_cache, f, indent=2)
    
    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.java': 'java',
            '.rb': 'ruby',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp'
        }
        return language_map.get(ext, 'unknown')
    
    def check_missing_why_comments(self, code: str) -> List[str]:
        """Check for code that needs WHY comments but doesn't have them"""
        issues = []
        
        # Check for magic numbers without explanation
        magic_number_pattern = r'(?<!["\'])\b(?:if|while|for|=)\s*.*?(\d{2,}|\d+\.\d+)(?!["\'])'
        for match in re.finditer(magic_number_pattern, code):
            line_num = code[:match.start()].count('\n') + 1
            # Check if there's a comment nearby explaining WHY
            lines = code.split('\n')
            if line_num > 0 and line_num <= len(lines):
                line = lines[line_num - 1]
                prev_line = lines[line_num - 2] if line_num > 1 else ""
                if not ('WHY' in line or 'WHY' in prev_line or 'because' in line.lower() or 'because' in prev_line.lower()):
                    issues.append(f"Magic number {match.group(1)} on line {line_num} needs WHY comment")
        
        # Check for workarounds without explanation
        workaround_patterns = [
            (r'#\s*[Ww]orkaround', "Workaround needs WHY comment and issue reference"),
            (r'#\s*[Hh]ack', "Hack needs WHY comment and when to remove"),
            (r'#\s*[Ff]ixme', "FIXME needs ticket number and WHY"),
            (r'#\s*TODO(?!\s*\([\w-]+\))', "TODO needs ticket number in format TODO(TICKET-123)"),
        ]
        
        for pattern, message in workaround_patterns:
            if re.search(pattern, code):
                issues.append(message)
        
        return issues
    
    def check_critical_patterns(self, code: str, language: str) -> List[Tuple[str, str]]:
        """Check for critical anti-patterns that should always be blocked"""
        violations = []
        
        # Universal anti-patterns
        universal_patterns = [
            # Nested ternaries (JS/TS/Python)
            (r'\?[^:?]*\?[^:?]*:', "Nested ternary operator - use if-else for clarity"),
            (r'\sif\s.*\selse\s.*\sif\s.*\selse\s', "Nested conditional expression - use if-elif-else"),
            
            # Double negation for type conversion
            (r'!!\w+', "Double negation '!!' is unclear - use Boolean() or explicit conversion"),
            
            # Bitwise tricks for non-bitwise operations
            (r'~~\w+', "Using ~~ for floor is clever but unclear - use Math.floor() explicitly"),
            
            # Linter suppression
            (r'#\s*noqa(?:\s|:|$)', "Don't suppress linter with noqa - fix the issue"),
            (r'#\s*pylint:\s*disable', "Don't disable pylint - fix the issue"),
            (r'#\s*type:\s*ignore', "Don't ignore type errors - fix them properly"),
            (r'//\s*eslint-disable', "Don't disable eslint - fix the issue"),
            (r'//\s*@ts-ignore', "Don't use @ts-ignore - fix the type issue"),
            (r'//\s*@ts-nocheck', "Don't use @ts-nocheck - fix the types"),
            
            # Poor error handling
            (r'except\s*:\s*pass', "Empty except block - handle or log the error"),
            (r'except\s+Exception\s*:', "Don't catch base Exception - catch specific exceptions"),
            (r'catch\s*\(\s*\)', "Empty catch block - handle the error properly"),
        ]
        
        # Language-specific patterns
        python_patterns = [
            (r'print\s*\(', "Use logging instead of print() in production code"),
            (r'exec\s*\(', "exec() is dangerous - find a safer approach"),
            (r'eval\s*\(', "eval() is dangerous - use ast.literal_eval or json.loads"),
        ] if language == 'python' else []
        
        js_patterns = [
            (r'console\.\w+\s*\(', "Remove console statements from production code"),
            (r'eval\s*\(', "eval() is dangerous - find a safer approach"),
            (r'document\.write\s*\(', "document.write is bad practice - use DOM methods"),
        ] if language in ['javascript', 'typescript'] else []
        
        # Check all patterns
        all_patterns = universal_patterns + python_patterns + js_patterns
        
        for pattern, message in all_patterns:
            if re.search(pattern, code, re.MULTILINE):
                violations.append((pattern, message))
        
        return violations
    
    def check_error_messages(self, code: str) -> List[str]:
        """Check for unhelpful error messages"""
        issues = []
        
        # Extract error messages
        error_patterns = [
            r'raise\s+\w*(?:Exception|Error)\s*\(\s*["\']([^"\']+)["\']',  # Python
            r'throw\s+(?:new\s+)?\w*Error\s*\(\s*["\']([^"\']+)["\']',     # JS/TS
            r'return\s+.*["\']([Ee]rror:?[^"\']+)["\']',                   # Return errors
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, code)
            for msg in matches:
                msg_lower = msg.lower()
                
                # Check for useless messages
                useless = ['something went wrong', 'an error occurred', 'failed', 
                          'invalid', 'bad request', 'error', 'failed to process']
                
                if any(u in msg_lower for u in useless) and len(msg) < 50:
                    issues.append(f"Unhelpful error message: '{msg}' - include what went wrong and how to fix it")
                
                # Check if message mentions entity but doesn't include value
                if re.search(r'\b(file|user|id|key|value|port|host)\b', msg_lower):
                    if not re.search(r'["\'].*?["\']|\d+|:\s*\w+', msg):
                        issues.append(f"Error mentions entity but not its value: '{msg}'")
        
        return issues
    
    def analyze_complexity_python(self, code: str, file_path: str) -> Dict:
        """Analyze Python code complexity using radon if available"""
        result = {'complexity': 0, 'issues': [], 'tool_available': False}
        
        try:
            # Check for virtual environment
            python_cmd = 'python'
            if 'python' in self.preferences:
                venv_path = self.preferences['python'].get('venv_path')
                if venv_path:
                    python_cmd = os.path.join(venv_path, 'bin', 'python')
            
            # Try to use radon
            radon_result = subprocess.run(
                [python_cmd, '-m', 'radon', 'cc', '-s', '-j', '-'],
                input=code,
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if radon_result.returncode == 0:
                result['tool_available'] = True
                data = json.loads(radon_result.stdout)
                
                # Extract complexity scores
                max_complexity = 0
                complex_functions = []
                
                for item in data.get('-', []):
                    complexity = item.get('complexity', 0)
                    if complexity > max_complexity:
                        max_complexity = complexity
                    if complexity > 10:
                        complex_functions.append({
                            'name': item.get('name', 'unknown'),
                            'complexity': complexity,
                            'line': item.get('lineno', 0)
                        })
                
                result['complexity'] = max_complexity
                
                # Add issues based on complexity
                for func in complex_functions:
                    if func['complexity'] > 15:
                        result['issues'].append(
                            f"Function '{func['name']}' has complexity {func['complexity']} (line {func['line']}) - refactor to reduce complexity below 10"
                        )
                    elif func['complexity'] > 10:
                        result['issues'].append(
                            f"Function '{func['name']}' has complexity {func['complexity']} (line {func['line']}) - consider simplifying"
                        )
                        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to pattern-based analysis
            result['complexity'] = self.estimate_complexity_fallback(code)
            if result['complexity'] > 10:
                result['issues'].append(f"Estimated complexity {result['complexity']} - consider refactoring")
        
        return result
    
    def analyze_complexity_javascript(self, code: str, file_path: str) -> Dict:
        """Analyze JavaScript/TypeScript complexity using eslint if available"""
        result = {'complexity': 0, 'issues': [], 'tool_available': False}
        
        try:
            # Check if eslint is available locally
            eslint_cmd = 'npx' if os.path.exists('node_modules/.bin/eslint') else 'eslint'
            
            # Create temp file for analysis
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            
            try:
                eslint_result = subprocess.run(
                    [eslint_cmd, '--format=json', '--rule=complexity:["error",10]', tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                
                if eslint_result.stdout:
                    result['tool_available'] = True
                    data = json.loads(eslint_result.stdout)
                    
                    for file_result in data:
                        for message in file_result.get('messages', []):
                            if 'complexity' in message.get('ruleId', ''):
                                result['complexity'] = 11  # Over threshold
                                result['issues'].append(message.get('message', 'High complexity detected'))
            finally:
                os.unlink(tmp_path)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # Fallback to pattern-based analysis
            result['complexity'] = self.estimate_complexity_fallback(code)
            if result['complexity'] > 10:
                result['issues'].append(f"Estimated complexity {result['complexity']} - consider refactoring")
        
        return result
    
    def analyze_complexity_go(self, code: str, file_path: str) -> Dict:
        """Analyze Go code complexity using gocyclo if available"""
        result = {'complexity': 0, 'issues': [], 'tool_available': False}
        
        try:
            # Try gocyclo
            gocyclo_result = subprocess.run(
                ['gocyclo', '-avg', '-'],
                input=code,
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if gocyclo_result.returncode == 0:
                result['tool_available'] = True
                output_lines = gocyclo_result.stdout.strip().split('\n')
                
                for line in output_lines:
                    # Parse gocyclo output format: "complexity package.Function file.go:line:col"
                    parts = line.split()
                    if parts and parts[0].isdigit():
                        complexity = int(parts[0])
                        if complexity > result['complexity']:
                            result['complexity'] = complexity
                        if complexity > 10:
                            func_name = parts[1] if len(parts) > 1 else 'function'
                            result['issues'].append(
                                f"Function {func_name} has complexity {complexity} - refactor to reduce below 10"
                            )
                            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # Fallback
            result['complexity'] = self.estimate_complexity_fallback(code)
            if result['complexity'] > 10:
                result['issues'].append(f"Estimated complexity {result['complexity']} - consider refactoring")
        
        return result
    
    def estimate_complexity_fallback(self, code: str) -> int:
        """Estimate cyclomatic complexity using patterns when tools unavailable"""
        complexity = 1  # Base complexity
        
        # Count decision points
        patterns = [
            r'\bif\b', r'\belif\b', r'\belse\s+if\b', r'\bfor\b', r'\bwhile\b',
            r'\bcase\b', r'\bcatch\b', r'\bexcept\b', r'\band\b', r'\bor\b',
            r'&&', r'\|\|', r'\?.*:'
        ]
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code, re.IGNORECASE))
        
        # Penalize deep nesting
        lines = code.split('\n')
        max_indent = 0
        for line in lines:
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
        
        if max_indent > 16:  # 4 levels of indentation (4 spaces each)
            complexity += (max_indent // 4) - 4
        
        return complexity
    
    def check_code_quality(self, tool: str, params: dict) -> Tuple[bool, Optional[str]]:
        """Main quality check function"""
        
        if tool not in ["Write", "Edit", "MultiEdit"]:
            return True, None
        
        # Extract code and file path
        file_path = params.get("file_path", "")
        
        # Skip test files and configs for some checks
        is_test = 'test' in file_path.lower() or 'spec' in file_path.lower()
        is_config = file_path.endswith(('.json', '.yml', '.yaml', '.toml', '.ini'))
        
        if is_config:
            return True, None  # Skip quality checks for config files
        
        # Extract code content
        code = None
        if tool == "Write":
            code = params.get("content", "")
        elif tool == "Edit":
            code = params.get("new_string", "")
        elif tool == "MultiEdit":
            edits = params.get("edits", [])
            code = "\n".join(edit.get("new_string", "") for edit in edits)
        
        if not code:
            return True, None
        
        # Detect language
        language = self.detect_language(file_path)
        if language == 'unknown':
            return True, None  # Can't analyze unknown languages
        
        all_issues = []
        
        # Stage 1: Critical pattern checks (FAST)
        pattern_violations = self.check_critical_patterns(code, language)
        if pattern_violations:
            # Block on critical patterns
            first_violation = pattern_violations[0]
            return False, f"❌ Code Quality Violation: {first_violation[1]}"
        
        # Stage 2: Error message quality (FAST)
        if not is_test:  # Skip error message checks in tests
            error_issues = self.check_error_messages(code)
            if error_issues:
                # Block on poor error messages
                return False, f"❌ Error Message Issue: {error_issues[0]}"
        
        # Stage 3: Check for missing WHY comments (FAST)
        if not is_test:
            why_issues = self.check_missing_why_comments(code)
            if why_issues:
                # Warn about missing WHY comments (don't block, just inform)
                all_issues.extend(why_issues)
        
        # Stage 3: Complexity analysis (SMART)
        if not is_test and len(code) > 100:  # Skip trivial code and tests
            complexity_result = None
            
            if language == 'python':
                complexity_result = self.analyze_complexity_python(code, file_path)
            elif language in ['javascript', 'typescript']:
                complexity_result = self.analyze_complexity_javascript(code, file_path)
            elif language == 'go':
                complexity_result = self.analyze_complexity_go(code, file_path)
            else:
                # Fallback for other languages
                complexity = self.estimate_complexity_fallback(code)
                complexity_result = {
                    'complexity': complexity,
                    'issues': [f"High complexity ({complexity}) - refactor to reduce"] if complexity > 15 else [],
                    'tool_available': False
                }
            
            if complexity_result:
                # Cache the result
                cache_key = f"{file_path}:{hash(code)}"
                self.complexity_cache[cache_key] = {
                    'complexity': complexity_result['complexity'],
                    'timestamp': time.time()
                }
                self.save_cache()
                
                # Handle complexity issues
                if complexity_result['complexity'] > 15:
                    # Block on very high complexity
                    issue_msg = complexity_result['issues'][0] if complexity_result['issues'] else f"Complexity {complexity_result['complexity']} exceeds limit (15)"
                    tool_status = " (using language tool)" if complexity_result['tool_available'] else " (estimated)"
                    return False, f"❌ Complexity Issue{tool_status}: {issue_msg}"
                elif complexity_result['complexity'] > 10:
                    # Warn on moderate complexity
                    all_issues.extend(complexity_result['issues'])
        
        # If we have non-blocking issues, report them as warnings
        if all_issues:
            return True, f"⚠️ Quality Warning: {all_issues[0]}"
        
        return True, None

def main():
    """Main entry point for the hook"""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        
        tool = input_data.get("tool", "")
        params = input_data.get("params", {})
        
        # Check code quality
        gate = CodeQualityGate()
        allowed, message = gate.check_code_quality(tool, params)
        
        # Return result
        result = {
            "allowed": allowed,
            "message": message
        }
        
        print(json.dumps(result))
        return 0 if allowed else 1
        
    except Exception as e:
        # On error, allow the operation but log the issue
        result = {
            "allowed": True,
            "message": f"Quality gate error: {str(e)}"
        }
        print(json.dumps(result))
        return 0

if __name__ == "__main__":
    sys.exit(main())