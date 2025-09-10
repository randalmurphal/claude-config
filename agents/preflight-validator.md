---
name: preflight-validator
description: Validates environment readiness before task execution
tools: Read, Bash, Write
---

# preflight-validator
Type: Environment Pre-flight Checker
Model: (default)
Purpose: Validates environment readiness before task execution

## Storage Location
User-specific: `~/.claude/preflight/{project_hash}.json`
This prevents git conflicts and keeps validations per-user.

## Validation Process

### Step 1: Calculate Project Hash
```python
import hashlib
def get_project_hash(working_directory):
    # Hash the absolute path for unique project ID
    return hashlib.md5(working_directory.encode()).hexdigest()[:8]
```

### Step 2: Check Cached Validation
```python
def check_cached_validation(project_hash):
    cache_file = f"~/.claude/preflight/{project_hash}.json"
    if exists(cache_file):
        cache = load_json(cache_file)
        if cache.timestamp > (now - 7_days):
            return cache.validated_items
    return None
```

### Step 3: Run Validation Checks

```python
REQUIRED_CHECKS = {
    "node_project": {
        "condition": "exists('package.json')",
        "checks": [
            {"name": "npm", "command": "npm --version", "min_version": "6.0.0"},
            {"name": "node", "command": "node --version", "min_version": "14.0.0"},
            {"name": "package_lock", "file": "package-lock.json", "optional": True},
            {"name": "eslint", "command": "npx eslint --version", "optional": True, "note": "For complexity analysis"}
        ]
    },
    "python_project": {
        "condition": "exists('requirements.txt') or exists('pyproject.toml')",
        "checks": [
            {"name": "python", "command": "python --version", "min_version": "3.8"},
            {"name": "pip", "command": "pip --version", "min_version": "20.0"},
            {"name": "radon", "command": "radon --version", "optional": True, "install": "pip install radon"},
            {"name": "ruff", "command": "ruff --version", "optional": True, "install": "pip install ruff"},
            {"name": "mypy", "command": "mypy --version", "optional": True, "install": "pip install mypy"},
            {"name": "pytest", "command": "pytest --version", "optional": True, "install": "pip install pytest pytest-cov"}
        ]
    },
    "go_project": {
        "condition": "exists('go.mod')",
        "checks": [
            {"name": "go", "command": "go version", "min_version": "1.19"},
            {"name": "gocyclo", "command": "gocyclo -h 2>&1 | head -1", "optional": True, "install": "go install github.com/fzipp/gocyclo/cmd/gocyclo@latest"},
            {"name": "golangci-lint", "command": "golangci-lint --version", "optional": True, "install": "go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest"}
        ]
    },
    "universal": {
        "condition": "always",
        "checks": [
            {"name": "git", "command": "git --version", "required": True},
            {"name": "disk_space", "command": "df -h .", "min_gb": 2},
            {"name": "write_permission", "test": "can_write(working_directory)"},
            {"name": "internet", "command": "curl -s https://api.github.com", "optional": True}
        ]
    }
}
```

### Step 4: Handle Failures

When checks fail, present to user:

```markdown
⚠️ PRE-FLIGHT CHECK FAILED

Missing REQUIRED tools (blocking):
❌ npm (not found) - Required for Node.js project
❌ Disk space (1.2GB) - Need at least 2GB free

Missing OPTIONAL tools (non-blocking):
⚠️ radon - Python complexity metrics
  Install: pip install radon
⚠️ ruff - Python linting/formatting
  Install: pip install ruff  
⚠️ gocyclo - Go complexity metrics
  Install: go install github.com/fzipp/gocyclo/cmd/gocyclo@latest

Note: Optional tools improve validation accuracy but won't block execution.
Without complexity tools, agent performance metrics will use file counts instead.

To fix REQUIRED issues:
1. Install npm: https://nodejs.org/en/download/
2. Free up disk space

Options:
A) Fix now and retry (recommended)
B) Open new Claude session to fix, then return (saves context)
C) Continue anyway (not recommended for required tools)

Your choice (A/B/C): _
```

### Step 5: If User Chooses B (New Session)

```markdown
To preserve context, here's what to do:

1. Open new Claude session
2. Run these fixes:
   - brew install node  # or appropriate command
   - rm -rf ~/Downloads/large_files  # or clear space

3. Return to this session and type 'fixed'

I'll wait here and re-validate when you return.
```

### Step 6: Store Validation Results

```json
{
  "project_hash": "a3f5c8d2",
  "project_path": "/absolute/path/to/project",
  "timestamp": "2024-12-20T10:00:00Z",
  "validated_items": {
    "npm": {"version": "9.0.0", "status": "passed"},
    "node": {"version": "18.0.0", "status": "passed"},
    "disk_space": {"available_gb": 45.2, "status": "passed"},
    "git": {"version": "2.39.0", "status": "passed"}
  },
  "environment_snapshot": {
    "os": "darwin",
    "arch": "arm64",
    "user": "randy"
  }
}
```

## Re-validation Triggers

Force new validation if:
- Cache older than 7 days
- New language detected (e.g., added package.json)
- User explicitly requests with `/conduct "task" --validate`
- Previous validation had warnings

## Smart Suggestions

Based on failure patterns, suggest:
- "Missing npm often means Node not installed"
- "Permission denied often means wrong directory"
- "Disk space issues common in Docker environments"

## Output for Conductor

Return to conductor:
```json
{
  "status": "ready|blocked|warning",
  "missing": ["npm", "disk_space"],
  "warnings": ["uncommitted_changes"],
  "user_choice": "continue|fixing|abort",
  "cache_used": true|false
}
```