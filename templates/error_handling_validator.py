#!/usr/bin/env python3
"""Error handling validator - ensures proper error handling with specific error types"""

import json
import sys
import re
from pathlib import Path

# Import base validator functions
sys.path.insert(0, str(Path(__file__).parent))
from base_validator import is_large_task_mode, update_validation_log

# Patterns that indicate poor error handling
GENERIC_ERROR_PATTERNS = [
    r'catch\s*\([^)]*\)\s*{\s*}',  # Empty catch blocks
    r'catch\s*\([^)]*\)\s*{\s*console\.(log|error)',  # Only logging, no handling
    r'catch\s*\(.*?\)\s*{\s*return\s+(null|undefined|false|\{\}|\[\])',  # Swallowing errors
    r'except\s*:\s*pass',  # Python: bare except with pass
    r'except\s+Exception\s*:\s*pass',  # Python: catching Exception with pass
    r'catch\s*\([^)]*\)\s*{\s*//\s*[Tt][Oo][Dd][Oo]',  # Unfinished error handling
    r'throw\s+new\s+Error\([\'"`][\'"`]\)',  # Empty error messages
    r'throw\s+[\'"`][\'"`]',  # Throwing strings instead of errors
]

# Patterns for good error handling
SPECIFIC_ERROR_PATTERNS = [
    r'class\s+\w+Error\s+extends\s+Error',  # Custom error classes (JS)
    r'class\s+\w+Error\(.+Exception\)',  # Custom error classes (Python)
    r'throw\s+new\s+\w+Error\(',  # Throwing specific errors
    r'raise\s+\w+Error\(',  # Python specific errors
]

def check_error_handling(file_path):
    """Check a file for proper error handling"""
    issues = []
    
    if not file_path.exists():
        return issues
    
    content = file_path.read_text()
    lines = content.split('\n')
    
    # Check for generic error handling
    for pattern in GENERIC_ERROR_PATTERNS:
        matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                'file': str(file_path),
                'line': line_num,
                'type': 'generic_error',
                'message': f'Generic or insufficient error handling detected',
                'code': lines[line_num - 1].strip() if line_num <= len(lines) else ''
            })
    
    # Check for async functions without try/catch (JS/TS)
    if file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
        async_pattern = r'async\s+(?:function\s+)?(\w+)?\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*{'
        async_funcs = re.finditer(async_pattern, content)
        
        for match in async_funcs:
            func_start = match.end()
            # Find the matching closing brace
            brace_count = 1
            pos = func_start
            func_body_start = func_start
            
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            func_body = content[func_body_start:pos-1]
            
            # Check if there's a try/catch in the function
            if 'try' not in func_body or 'catch' not in func_body:
                line_num = content[:match.start()].count('\n') + 1
                func_name = match.group(1) or 'anonymous'
                issues.append({
                    'file': str(file_path),
                    'line': line_num,
                    'type': 'missing_error_boundary',
                    'message': f'Async function "{func_name}" lacks try/catch',
                    'code': lines[line_num - 1].strip() if line_num <= len(lines) else ''
                })
    
    # Check for Python async functions without try/except
    if file_path.suffix == '.py':
        async_pattern = r'async\s+def\s+(\w+)\s*\([^)]*\)\s*:'
        async_funcs = re.finditer(async_pattern, content)
        
        for match in async_funcs:
            func_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # Find the function body (based on indentation)
            func_lines = []
            base_indent = len(lines[line_num - 1]) - len(lines[line_num - 1].lstrip())
            
            for i in range(line_num, len(lines)):
                line = lines[i]
                if line.strip() and not line.startswith(' ' * (base_indent + 1)):
                    break
                func_lines.append(line)
            
            func_body = '\n'.join(func_lines)
            
            if 'try:' not in func_body or 'except' not in func_body:
                issues.append({
                    'file': str(file_path),
                    'line': line_num,
                    'type': 'missing_error_boundary',
                    'message': f'Async function "{func_name}" lacks try/except',
                    'code': lines[line_num - 1].strip()
                })
    
    return issues

def check_error_classes(project_path):
    """Check if project has proper error class definitions"""
    error_classes = []
    
    # Look for error class definitions
    common_errors = Path(project_path) / 'common' / 'errors'
    if common_errors.exists():
        for error_file in common_errors.rglob('*'):
            if error_file.is_file():
                content = error_file.read_text()
                # Find error class definitions
                js_classes = re.findall(r'class\s+(\w+Error)\s+extends\s+Error', content)
                py_classes = re.findall(r'class\s+(\w+Error)\(', content)
                error_classes.extend(js_classes)
                error_classes.extend(py_classes)
    
    return error_classes

def validate_error_handling():
    """Main validation function"""
    # Exit silently if not in Large Task Mode
    if not is_large_task_mode():
        sys.exit(0)
    
    issues = []
    project_path = Path.cwd()
    
    # Check for error class definitions
    error_classes = check_error_classes(project_path)
    if not error_classes:
        issues.append({
            'type': 'missing_error_classes',
            'message': 'No custom error classes found in /common/errors/',
            'severity': 'high'
        })
    
    # Check all source files
    for pattern in ['*.js', '*.jsx', '*.ts', '*.tsx', '*.py']:
        for file_path in project_path.rglob(pattern):
            # Skip node_modules, venv, etc.
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git', 'dist', 'build']):
                continue
            
            file_issues = check_error_handling(file_path)
            issues.extend(file_issues)
    
    # Report results
    if issues:
        # Group issues by type
        generic_errors = [i for i in issues if i.get('type') == 'generic_error']
        missing_boundaries = [i for i in issues if i.get('type') == 'missing_error_boundary']
        missing_classes = [i for i in issues if i.get('type') == 'missing_error_classes']
        
        report = []
        if missing_classes:
            report.append("❌ No custom error classes defined in /common/errors/")
        if generic_errors:
            report.append(f"❌ {len(generic_errors)} generic error handlers found")
            for issue in generic_errors[:3]:  # Show first 3
                report.append(f"  - {issue['file']}:{issue['line']}")
        if missing_boundaries:
            report.append(f"❌ {len(missing_boundaries)} async functions without error boundaries")
            for issue in missing_boundaries[:3]:  # Show first 3
                report.append(f"  - {issue['file']}:{issue['line']} ({issue['message']})")
        
        # Update validation log
        update_validation_log({
            'type': 'error_handling',
            'status': 'failed',
            'issues': issues
        })
        
        # Return failure
        output = {
            "decision": "block",
            "reason": "Error handling issues detected:\n" + "\n".join(report) + "\n\nFix: Create specific error classes and handle errors properly"
        }
        json.dump(output, sys.stdout)
        sys.exit(0)
    
    sys.exit(0)

if __name__ == "__main__":
    validate_error_handling()