#!/usr/bin/env python3
"""Code quality validator - runs linters and formatters for the project's languages"""

import json
import sys
import subprocess
from pathlib import Path

# Import base validator functions
sys.path.insert(0, str(Path(__file__).parent))
from base_validator import is_large_task_mode, update_validation_log

# Language-specific linting/formatting commands
LINTERS = {
    'javascript': {
        'files': ['*.js', '*.jsx', '*.ts', '*.tsx'],
        'linters': [
            {'cmd': 'npm run lint', 'name': 'ESLint'},
            {'cmd': 'npm run typecheck', 'name': 'TypeScript'},
            {'cmd': 'npm run format:check', 'name': 'Prettier'}
        ],
        'formatters': [
            {'cmd': 'npm run format', 'name': 'Prettier'}
        ],
        'config_files': ['package.json', '.eslintrc', 'tsconfig.json']
    },
    'python': {
        'files': ['*.py'],
        'linters': [
            {'cmd': 'ruff check .', 'name': 'Ruff'},
            {'cmd': 'mypy .', 'name': 'MyPy'},
            {'cmd': 'black --check .', 'name': 'Black'}
        ],
        'formatters': [
            {'cmd': 'black .', 'name': 'Black'},
            {'cmd': 'ruff check --fix .', 'name': 'Ruff'}
        ],
        'config_files': ['pyproject.toml', 'setup.py', 'requirements.txt']
    },
    'go': {
        'files': ['*.go'],
        'linters': [
            {'cmd': 'go fmt ./...', 'name': 'Go Fmt'},
            {'cmd': 'go vet ./...', 'name': 'Go Vet'},
            {'cmd': 'golangci-lint run', 'name': 'GolangCI-Lint'}
        ],
        'formatters': [
            {'cmd': 'go fmt ./...', 'name': 'Go Fmt'}
        ],
        'config_files': ['go.mod', 'go.sum']
    },
    'rust': {
        'files': ['*.rs'],
        'linters': [
            {'cmd': 'cargo fmt -- --check', 'name': 'Rustfmt'},
            {'cmd': 'cargo clippy -- -D warnings', 'name': 'Clippy'}
        ],
        'formatters': [
            {'cmd': 'cargo fmt', 'name': 'Rustfmt'}
        ],
        'config_files': ['Cargo.toml', 'Cargo.lock']
    }
}

def detect_project_languages():
    """Detect which languages are used in the project"""
    detected = []
    
    for lang, config in LINTERS.items():
        # Check for config files
        for config_file in config['config_files']:
            if Path(config_file).exists():
                detected.append(lang)
                break
        
        # Check for source files if not detected by config
        if lang not in detected:
            for pattern in config['files']:
                if list(Path('.').rglob(pattern)):
                    detected.append(lang)
                    break
    
    return detected

def run_linters(languages, fix=False):
    """Run linters for detected languages"""
    results = {
        'passed': True,
        'issues': [],
        'fixed': []
    }
    
    for lang in languages:
        lang_config = LINTERS.get(lang, {})
        
        if fix:
            # Run formatters to fix issues
            for formatter in lang_config.get('formatters', []):
                try:
                    result = subprocess.run(
                        formatter['cmd'],
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        results['fixed'].append(f"{formatter['name']} ({lang})")
                except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                    # Formatter not available, skip
                    continue
        else:
            # Run linters to check for issues
            for linter in lang_config.get('linters', []):
                try:
                    result = subprocess.run(
                        linter['cmd'],
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode != 0:
                        results['passed'] = False
                        results['issues'].append({
                            'linter': linter['name'],
                            'language': lang,
                            'output': result.stdout[:500] if result.stdout else result.stderr[:500]
                        })
                except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                    # Linter not available, skip
                    continue
    
    return results

def main():
    """Main validation function"""
    # Exit silently if not in Large Task Mode
    if not is_large_task_mode():
        sys.exit(0)
    
    # Try to read hook input if available
    try:
        input_data = json.load(sys.stdin)
        event_name = input_data.get('hook_event_name', '')
        tool_name = input_data.get('tool_name', '')
    except:
        # Running standalone
        event_name = 'manual'
        tool_name = ''
    
    # Detect project languages
    languages = detect_project_languages()
    
    if not languages:
        # No recognized languages, exit
        sys.exit(0)
    
    # For PostToolUse on Write/Edit, automatically fix
    if event_name == 'PostToolUse' and tool_name in ['Write', 'Edit', 'MultiEdit']:
        results = run_linters(languages, fix=True)
        if results['fixed']:
            # Log that we fixed issues
            update_validation_log({
                'type': 'code_quality',
                'action': 'auto_fixed',
                'fixed': results['fixed']
            })
    else:
        # For validation, just check
        results = run_linters(languages, fix=False)
        
        if not results['passed']:
            # Report issues
            issue_summary = []
            for issue in results['issues']:
                issue_summary.append(f"- {issue['linter']} ({issue['language']})")
            
            output = {
                "decision": "block",
                "reason": f"Code quality issues detected:\n" + "\n".join(issue_summary) + "\n\nRun linters/formatters to fix."
            }
            
            # Update validation log
            update_validation_log({
                'type': 'code_quality',
                'status': 'failed',
                'issues': results['issues']
            })
            
            json.dump(output, sys.stdout)
            sys.exit(0)
    
    sys.exit(0)

if __name__ == "__main__":
    main()