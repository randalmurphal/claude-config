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
            (r'#\s*[Tt]odo', "TODO needs ticket number or clear action")
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in workaround_patterns:
                if re.search(pattern, line):
                    if 'WHY' not in line and 'because' not in line.lower():
                        issues.append(f"Line {i}: {message}")
        
        return issues
    
    def check_critical_patterns(self, code: str, language: str) -> List[str]:
        """Check for critical anti-patterns that should be blocked"""
        issues = []
        
        # Universal anti-patterns
        patterns = [
            # Nested ternaries (unreadable)
            (r'\?.*\?.*:', "Nested ternary operators are unreadable - use if/else statements"),
            
            # Double negation (confusing)
            (r'!\s*!\s*(?!Boolean|bool\()', "Double negation is confusing - use positive logic"),
            
            # Bitwise operations for non-bitwise purposes
            (r'(?<![&|])[&|](?![&|])\s*(?![0-9a-fA-Fx])', "Use logical operators (&&, ||) not bitwise (&, |) for boolean logic"),
        ]
        
        # Language-specific patterns
        if language == 'python':
            patterns.extend([
                # Linter suppression
                (r'#\s*noqa(?:\s|:|$)', "Do not suppress linter warnings - fix the issue instead"),
                (r'#\s*pylint:\s*disable', "Do not disable pylint - fix the issue instead"),
                (r'#\s*type:\s*ignore', "Do not ignore type errors - fix the type issue"),
                
                # Poor error handling
                (r'except\s*:', "Never use bare except - catch specific exceptions"),
                (r'except\s+Exception\s*:', "Avoid catching base Exception - be more specific"),
                (r'except.*?:\s*\n\s*pass', "Empty except blocks hide errors - handle or log properly"),
            ])
        
        elif language in ['javascript', 'typescript']:
            patterns.extend([
                # ESLint suppression
                (r'//\s*eslint-disable', "Do not disable ESLint - fix the issue instead"),
                (r'/\*\s*eslint-disable', "Do not disable ESLint - fix the issue instead"),
                (r'@ts-ignore', "Do not use @ts-ignore - fix the type issue"),
                
                # Console logs in production
                (r'console\.(log|debug|info)', "Remove console statements - use proper logging"),
            ])
        
        # Check all patterns
        for pattern, message in patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(f"Line {line_num}: {message}")
        
        return issues
    
    def check_helpful_errors(self, code: str, language: str) -> List[str]:
        """Check that error messages are helpful (include what went wrong AND how to fix)"""
        issues = []
        
        # Pattern for error messages that are not helpful
        if language == 'python':
            # Find raise statements with generic messages
            error_patterns = [
                (r'raise\s+\w+Exception\(["\']Error["\']', "Error message 'Error' is not helpful"),
                (r'raise\s+\w+Exception\(["\']Failed["\']', "Error message 'Failed' is not helpful"),
                (r'raise\s+\w+Exception\(["\']Invalid["\']', "Error message 'Invalid' is not helpful - explain what is invalid and expected format"),
            ]
        elif language in ['javascript', 'typescript']:
            error_patterns = [
                (r'throw\s+new\s+Error\(["\']Error["\']', "Error message 'Error' is not helpful"),
                (r'throw\s+new\s+Error\(["\']Failed["\']', "Error message 'Failed' is not helpful"),
                (r'throw\s+["\']Error["\']', "Error message 'Error' is not helpful"),
            ]
        else:
            error_patterns = []
        
        for pattern, message in error_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(f"Line {line_num}: {message} - include what went wrong and how to fix it")
        
        return issues
    
    def analyze_complexity_python(self, code: str, file_path: str) -> Dict:
        """Analyze Python code using radon, cognitive complexity, and vulture"""
        result = {'complexity': 0, 'issues': [], 'tool_available': False}
        
        # Use venv python if available
        python_cmd = 'python'
        if 'python' in self.preferences:
            venv_path = self.preferences['python'].get('venv_path')
            if venv_path:
                python_cmd = os.path.join(venv_path, 'bin', 'python')
        
        # 1. Radon Cyclomatic Complexity Analysis
        try:
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
                
                max_complexity = 0
                complex_functions = []
                
                for item in data.get('-', []):
                    complexity = item.get('complexity', 0)
                    rank = item.get('rank', 'A')
                    if complexity > max_complexity:
                        max_complexity = complexity
                    
                    # Track functions by grade
                    if rank in ['F', 'E', 'D']:  # Complexity > 20
                        complex_functions.append({
                            'name': item.get('name', 'unknown'),
                            'complexity': complexity,
                            'rank': rank,
                            'line': item.get('lineno', 0),
                            'severity': 'high' if rank == 'F' else 'medium'
                        })
                    elif rank == 'C':  # Complexity 11-20
                        complex_functions.append({
                            'name': item.get('name', 'unknown'),
                            'complexity': complexity,
                            'rank': rank,
                            'line': item.get('lineno', 0),
                            'severity': 'low'
                        })
                
                result['complexity'] = max_complexity
                
                # Add cyclomatic complexity issues
                for func in complex_functions:
                    if func['severity'] == 'high':
                        result['issues'].append(
                            f"🔴 CRITICAL: Function '{func['name']}' (line {func['line']}) has cyclomatic complexity {func['complexity']} (grade {func['rank']}) - MUST refactor to reduce below 20"
                        )
                    elif func['severity'] == 'medium':
                        result['issues'].append(
                            f"🟠 HIGH: Function '{func['name']}' (line {func['line']}) has cyclomatic complexity {func['complexity']} (grade {func['rank']}) - should refactor to reduce below 15"
                        )
                    else:
                        result['issues'].append(
                            f"🟡 MEDIUM: Function '{func['name']}' (line {func['line']}) has cyclomatic complexity {func['complexity']} (grade {func['rank']}) - consider simplifying"
                        )
                        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to pattern-based analysis
            result['complexity'] = self.estimate_complexity_fallback(code)
            if result['complexity'] > 10:
                result['issues'].append(f"⚠️ Estimated complexity {result['complexity']} - consider refactoring")
        
        # 2. Cognitive Complexity Analysis
        try:
            # Create temporary file for cognitive complexity analysis
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            
            try:
                # Run cognitive complexity check
                cog_result = subprocess.run(
                    [python_cmd, '-c', f"""
import ast
from cognitive_complexity.api import get_cognitive_complexity_for_node

with open('{tmp_path}') as f:
    tree = ast.parse(f.read())

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        cc = get_cognitive_complexity_for_node(node)
        if cc > 7:  # Threshold for cognitive complexity
            print(f'{{node.name}}:{{node.lineno}}:{{cc}}')
"""],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if cog_result.returncode == 0 and cog_result.stdout:
                    for line in cog_result.stdout.strip().split('\n'):
                        if ':' in line:
                            parts = line.split(':')
                            if len(parts) >= 3:
                                func_name = parts[0]
                                lineno = parts[1]
                                cog_complexity = int(parts[2])
                                
                                if cog_complexity > 30:
                                    result['issues'].append(
                                        f"🔴 CRITICAL: Function '{func_name}' (line {lineno}) has cognitive complexity {cog_complexity} - extremely hard to understand, MUST simplify"
                                    )
                                elif cog_complexity > 15:
                                    result['issues'].append(
                                        f"🟠 HIGH: Function '{func_name}' (line {lineno}) has cognitive complexity {cog_complexity} - difficult to understand, should simplify"
                                    )
                                elif cog_complexity > 7:
                                    result['issues'].append(
                                        f"🟡 MEDIUM: Function '{func_name}' (line {lineno}) has cognitive complexity {cog_complexity} - getting complex, consider simplifying"
                                    )
            finally:
                os.unlink(tmp_path)
                
        except Exception:
            pass  # Cognitive complexity is optional enhancement
        
        # 3. Vulture Dead Code Analysis
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            
            try:
                vulture_result = subprocess.run(
                    [python_cmd, '-m', 'vulture', tmp_path, '--min-confidence', '80'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if vulture_result.returncode == 0 and vulture_result.stdout:
                    dead_code_count = 0
                    for line in vulture_result.stdout.strip().split('\n'):
                        if line and not line.startswith('#'):
                            dead_code_count += 1
                            # Parse vulture output format: "filename:line: unused ..."
                            if ':' in line:
                                parts = line.split(':', 2)
                                if len(parts) >= 3:
                                    line_num = parts[1]
                                    issue = parts[2].strip()
                                    # Only report high confidence dead code
                                    if '(100% confidence)' in issue or '(90% confidence)' in issue:
                                        result['issues'].append(f"💀 DEAD CODE: Line {line_num}: {issue}")
                                    elif '(80% confidence)' in issue:
                                        result['issues'].append(f"⚠️ POSSIBLY DEAD: Line {line_num}: {issue}")
            finally:
                os.unlink(tmp_path)
                
        except Exception:
            pass  # Vulture is optional enhancement
        
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
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        
        # Add complexity for deep nesting
        if max_indent > 20:
            complexity += (max_indent - 20) // 4
        
        return complexity
    
    def analyze_file(self, file_path: str, content: str) -> Dict:
        """Analyze a single file for quality issues"""
        language = self.detect_language(file_path)
        
        all_issues = []
        max_complexity = 0
        tool_available = False
        
        # Skip analysis for non-code files
        if language == 'unknown':
            return {
                'file': file_path,
                'language': language,
                'issues': [],
                'complexity': 0,
                'tool_available': False
            }
        
        # 1. Check critical anti-patterns
        pattern_issues = self.check_critical_patterns(content, language)
        all_issues.extend(pattern_issues)
        
        # 2. Check for missing WHY comments
        why_issues = self.check_missing_why_comments(content)
        # Only report the most egregious missing WHY comments
        all_issues.extend(why_issues[:3])
        
        # 3. Check error message quality
        error_issues = self.check_helpful_errors(content, language)
        all_issues.extend(error_issues)
        
        # 4. Language-specific complexity analysis
        if language == 'python':
            complexity_result = self.analyze_complexity_python(content, file_path)
        elif language in ['javascript', 'typescript']:
            complexity_result = self.analyze_complexity_javascript(content, file_path)
        elif language == 'go':
            complexity_result = self.analyze_complexity_go(content, file_path)
        else:
            complexity_result = {
                'complexity': self.estimate_complexity_fallback(content),
                'issues': [],
                'tool_available': False
            }
        
        max_complexity = complexity_result['complexity']
        all_issues.extend(complexity_result['issues'])
        tool_available = complexity_result['tool_available']
        
        # Cache the results
        cache_key = f"{file_path}:{hash(content)}"
        self.complexity_cache[cache_key] = {
            'complexity': max_complexity,
            'timestamp': time.time(),
            'tool_available': tool_available
        }
        self.save_cache()
        
        return {
            'file': file_path,
            'language': language,
            'issues': all_issues,
            'complexity': max_complexity,
            'tool_available': tool_available
        }
    
    def should_block(self, issues: List[str]) -> bool:
        """Determine if we should block based on issues found"""
        # Block on critical issues
        critical_keywords = [
            'CRITICAL:', 'MUST', 'never use bare except',
            'Do not suppress', 'Do not disable', 'Do not ignore',
            'Remove console statements', 'is not helpful'
        ]
        
        for issue in issues:
            for keyword in critical_keywords:
                if keyword in issue:
                    return True
        
        # Block if too many issues
        return len(issues) > 10

def main():
    """Main entry point for the hook"""
    # Read input from stdin
    input_data = json.loads(sys.stdin.read())
    
    # Extract file operations
    operations = input_data.get('operations', [])
    
    # Initialize quality gate
    gate = CodeQualityGate()
    
    # Analyze each file operation
    all_issues = []
    files_analyzed = []
    
    for op in operations:
        if op.get('type') in ['write', 'edit', 'create']:
            file_path = op.get('path', '')
            content = op.get('content', '')
            
            if content and file_path:
                result = gate.analyze_file(file_path, content)
                
                if result['issues']:
                    files_analyzed.append(file_path)
                    all_issues.extend([f"{file_path}: {issue}" for issue in result['issues']])
    
    # Determine if we should block
    should_block = gate.should_block(all_issues)
    
    # Output result
    result = {
        'action': 'block' if should_block else 'warn',
        'message': None,
        'issues': all_issues
    }
    
    if should_block:
        result['message'] = f"Code quality issues found in {len(files_analyzed)} file(s). Please fix critical issues before proceeding."
    elif all_issues:
        result['message'] = f"Code quality warnings in {len(files_analyzed)} file(s). Consider addressing these issues."
    
    # Return result
    print(json.dumps(result))
    return 0 if not should_block else 1

if __name__ == '__main__':
    sys.exit(main())