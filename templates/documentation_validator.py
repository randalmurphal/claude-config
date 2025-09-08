#!/usr/bin/env python3
"""Documentation validator - ensures code is properly documented"""

import json
import sys
import re
from pathlib import Path

# Import base validator functions
sys.path.insert(0, str(Path(__file__).parent))
from base_validator import is_large_task_mode, update_validation_log

def check_function_documentation(file_path, content):
    """Check if functions have proper documentation"""
    issues = []
    lines = content.split('\n')
    
    if file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
        # JavaScript/TypeScript function patterns
        patterns = [
            r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)',  # Named functions
            r'^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(',  # Arrow functions
            r'^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?function',  # Function expressions
            r'^\s*(?:public|private|protected)?\s*(?:async\s+)?(\w+)\s*\(',  # Class methods
        ]
        
        for i, line in enumerate(lines):
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    func_name = match.group(1)
                    
                    # Skip constructor and common lifecycle methods
                    if func_name in ['constructor', 'render', 'componentDidMount', 'componentWillUnmount']:
                        continue
                    
                    # Check if there's JSDoc above
                    has_doc = False
                    if i > 0:
                        # Look for JSDoc pattern above function
                        for j in range(max(0, i-10), i):
                            if '/**' in lines[j]:
                                has_doc = True
                                break
                    
                    if not has_doc and not func_name.startswith('_'):  # Skip private functions
                        issues.append({
                            'file': str(file_path),
                            'line': i + 1,
                            'function': func_name,
                            'type': 'missing_jsdoc'
                        })
    
    elif file_path.suffix == '.py':
        # Python function patterns
        patterns = [
            r'^def\s+(\w+)\s*\(',
            r'^async\s+def\s+(\w+)\s*\(',
            r'^\s*def\s+(\w+)\s*\(',  # Class methods
        ]
        
        for i, line in enumerate(lines):
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    func_name = match.group(1)
                    
                    # Skip magic methods except __init__
                    if func_name.startswith('__') and func_name != '__init__':
                        continue
                    
                    # Check if there's a docstring below
                    has_doc = False
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.startswith('"""') or next_line.startswith("'''"):
                            has_doc = True
                    
                    if not has_doc and not func_name.startswith('_'):  # Skip private functions
                        issues.append({
                            'file': str(file_path),
                            'line': i + 1,
                            'function': func_name,
                            'type': 'missing_docstring'
                        })
    
    return issues

def check_readme_exists(project_path):
    """Check if README.md exists and has content"""
    readme_files = ['README.md', 'readme.md', 'Readme.md']
    
    for readme_name in readme_files:
        readme_path = project_path / readme_name
        if readme_path.exists():
            content = readme_path.read_text()
            # Check if README has substantial content
            if len(content) > 100:  # At least 100 characters
                return True
    
    return False

def check_api_documentation(project_path):
    """Check if API documentation exists"""
    doc_patterns = [
        '**/docs/api/**/*',
        '**/api-docs/**/*',
        '**/swagger.json',
        '**/swagger.yaml',
        '**/openapi.json',
        '**/openapi.yaml'
    ]
    
    for pattern in doc_patterns:
        if list(project_path.glob(pattern)):
            return True
    
    return False

def check_architecture_docs(project_path):
    """Check if architecture documentation exists"""
    arch_file = project_path / '.claude' / 'ARCHITECTURE.md'
    if arch_file.exists():
        content = arch_file.read_text()
        return len(content) > 200  # Has substantial content
    
    return False

def calculate_documentation_coverage(project_path):
    """Calculate overall documentation coverage"""
    total_functions = 0
    documented_functions = 0
    
    for pattern in ['*.js', '*.jsx', '*.ts', '*.tsx', '*.py']:
        for file_path in project_path.rglob(pattern):
            # Skip excluded directories
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git', 'dist', 'build']):
                continue
            
            content = file_path.read_text()
            issues = check_function_documentation(file_path, content)
            
            # Count functions
            if file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                functions = re.findall(r'(?:function\s+\w+|const\s+\w+\s*=\s*(?:async\s+)?(?:function|\())', content)
                total_functions += len(functions)
                documented_functions += len(functions) - len(issues)
            elif file_path.suffix == '.py':
                functions = re.findall(r'def\s+\w+\s*\(', content)
                total_functions += len(functions)
                documented_functions += len(functions) - len(issues)
    
    if total_functions == 0:
        return 100
    
    return int((documented_functions / total_functions) * 100)

def validate_documentation():
    """Main validation function"""
    # Exit silently if not in Large Task Mode
    if not is_large_task_mode():
        sys.exit(0)
    
    issues = []
    project_path = Path.cwd()
    
    # Check README
    if not check_readme_exists(project_path):
        issues.append({
            'type': 'missing_readme',
            'message': 'README.md is missing or has insufficient content',
            'severity': 'high'
        })
    
    # Check architecture docs
    if not check_architecture_docs(project_path):
        issues.append({
            'type': 'missing_architecture',
            'message': 'Architecture documentation is missing',
            'severity': 'medium'
        })
    
    # Check API documentation (if APIs exist)
    api_files = list(project_path.glob('**/api/**/*')) + list(project_path.glob('**/routes/**/*'))
    if api_files and not check_api_documentation(project_path):
        issues.append({
            'type': 'missing_api_docs',
            'message': 'API documentation is missing',
            'severity': 'medium'
        })
    
    # Check function documentation coverage
    coverage = calculate_documentation_coverage(project_path)
    if coverage < 70:  # Require 70% documentation coverage
        issues.append({
            'type': 'low_coverage',
            'message': f'Documentation coverage is {coverage}% (minimum 70%)',
            'severity': 'medium'
        })
    
    # Check for undocumented public functions
    undocumented = []
    for pattern in ['*.js', '*.jsx', '*.ts', '*.tsx', '*.py']:
        for file_path in project_path.rglob(pattern):
            if any(skip in str(file_path) for skip in ['node_modules', 'venv', '.git']):
                continue
            
            content = file_path.read_text()
            file_issues = check_function_documentation(file_path, content)
            undocumented.extend(file_issues[:3])  # Limit to first 3 per file
    
    if undocumented:
        issues.append({
            'type': 'undocumented_functions',
            'functions': undocumented[:10],  # Show first 10
            'severity': 'low'
        })
    
    # Report results
    if issues:
        report = []
        
        for issue in issues:
            if issue['type'] == 'missing_readme':
                report.append("❌ README.md missing or insufficient")
            elif issue['type'] == 'missing_architecture':
                report.append("❌ Architecture documentation missing")
            elif issue['type'] == 'missing_api_docs':
                report.append("❌ API documentation missing")
            elif issue['type'] == 'low_coverage':
                report.append(f"⚠️ {issue['message']}")
            elif issue['type'] == 'undocumented_functions':
                report.append(f"⚠️ {len(issue['functions'])} undocumented public functions")
                for func in issue['functions'][:5]:
                    report.append(f"  - {func['file']}:{func['line']} ({func['function']})")
        
        # Update validation log
        update_validation_log({
            'type': 'documentation',
            'status': 'failed',
            'coverage': coverage,
            'issues': issues
        })
        
        # Only block for high severity issues
        high_severity = [i for i in issues if i.get('severity') == 'high']
        if high_severity:
            output = {
                "decision": "block",
                "reason": "Documentation issues detected:\n" + "\n".join(report)
            }
            json.dump(output, sys.stdout)
            sys.exit(0)
    
    sys.exit(0)

if __name__ == "__main__":
    validate_documentation()