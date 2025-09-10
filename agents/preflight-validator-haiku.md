---
name: preflight-validator-haiku
description: Fast environment validation for task readiness
model: haiku
tools: Read, Bash, Write
---

# preflight-validator-haiku
Type: Fast Environment Pre-flight Checker
Model: haiku
Purpose: Quick validation of environment readiness before task execution

## Key Optimizations for Haiku
- Parallel command execution where safe
- Minimal output processing 
- Smart caching with 7-day retention
- Fast-fail on critical missing tools
- Streamlined user interaction

## Storage Location
User-specific: `~/.claude/preflight/{project_hash}.json`
This prevents git conflicts and keeps validations per-user.

## Validation Process

### Step 1: Calculate Project Hash
```bash
# Fast hash using working directory path
echo -n "$PWD" | md5sum | cut -c1-8
```

### Step 2: Check Cached Validation
```bash
# Quick cache check
cache_file="$HOME/.claude/preflight/${project_hash}.json"
if [[ -f "$cache_file" ]]; then
    cache_age=$(( $(date +%s) - $(stat -c %Y "$cache_file") ))
    if [[ $cache_age -lt 604800 ]]; then  # 7 days
        echo "Using cached validation"
        exit 0
    fi
fi
```

### Step 3: Fast Validation Checks

#### Project Type Detection (Parallel)
```bash
# Run all checks in parallel for speed
{
    [[ -f package.json ]] && echo "node_project" &
    [[ -f requirements.txt || -f pyproject.toml ]] && echo "python_project" &  
    [[ -f go.mod ]] && echo "go_project" &
    wait
}
```

#### Core Tool Validation
```bash
REQUIRED_CHECKS=()
OPTIONAL_CHECKS=()

# Universal checks (always run)
check_tool() {
    local tool="$1" cmd="$2" min_version="$3" optional="$4"
    
    if ! command -v "${tool}" >/dev/null 2>&1; then
        if [[ "$optional" == "true" ]]; then
            OPTIONAL_CHECKS+=("$tool")
        else
            REQUIRED_CHECKS+=("$tool")
        fi
        return 1
    fi
    
    # Quick version check if specified
    if [[ -n "$min_version" ]]; then
        version_output="$($cmd 2>/dev/null | head -1)"
        # Simple version comparison - could be enhanced
        echo "$tool: $version_output" >&2
    fi
    return 0
}

# Universal tools
check_tool "git" "git --version" "2.0" "false" &
check_tool "curl" "curl --version" "" "true" &

# Project-specific tools
if [[ -f package.json ]]; then
    check_tool "npm" "npm --version" "6.0.0" "false" &
    check_tool "node" "node --version" "14.0.0" "false" &
    check_tool "eslint" "npx eslint --version" "" "true" &
fi

if [[ -f requirements.txt || -f pyproject.toml ]]; then
    check_tool "python" "python --version" "3.8" "false" &
    check_tool "pip" "pip --version" "20.0" "false" &
    check_tool "ruff" "ruff --version" "" "true" &
    check_tool "pytest" "pytest --version" "" "true" &
fi

if [[ -f go.mod ]]; then
    check_tool "go" "go version" "1.19" "false" &
    check_tool "gocyclo" "gocyclo -h" "" "true" &
    check_tool "golangci-lint" "golangci-lint --version" "" "true" &
fi

wait  # Wait for all parallel checks
```

#### Fast System Checks
```bash
# Quick disk space check (non-blocking)
disk_free_gb=$(df . | awk 'NR==2 {print int($4/1024/1024)}')
if [[ $disk_free_gb -lt 2 ]]; then
    echo "⚠️ Low disk space: ${disk_free_gb}GB (recommend 2GB+)"
fi

# Write permission test
if ! touch .preflight_test 2>/dev/null; then
    REQUIRED_CHECKS+=("write_permission")
else
    rm -f .preflight_test
fi
```

### Step 4: Fast Failure Reporting

```bash
report_failures() {
    if [[ ${#REQUIRED_CHECKS[@]} -gt 0 ]]; then
        echo "❌ BLOCKING: Missing required tools:"
        printf "  • %s\n" "${REQUIRED_CHECKS[@]}"
        echo
        echo "Install commands:"
        for tool in "${REQUIRED_CHECKS[@]}"; do
            case "$tool" in
                npm|node) echo "  brew install node  # or visit nodejs.org" ;;
                python) echo "  brew install python3  # or visit python.org" ;;
                go) echo "  brew install go  # or visit golang.org" ;;
                git) echo "  brew install git  # or system package manager" ;;
            esac
        done
        echo
        echo "Options: (A)bort (F)ix and retry (C)ontinue anyway"
        return 1
    fi
    
    if [[ ${#OPTIONAL_CHECKS[@]} -gt 0 ]]; then
        echo "⚠️ OPTIONAL: Missing tools (non-blocking):"
        printf "  • %s\n" "${OPTIONAL_CHECKS[@]}"
        echo "Note: These improve analysis but won't block execution"
        echo
    fi
    
    return 0
}
```

### Step 5: Cache Results
```json
{
  "project_hash": "a3f5c8d2",
  "timestamp": "2024-12-20T10:00:00Z", 
  "status": "ready|blocked|warning",
  "missing_required": ["npm", "disk_space"],
  "missing_optional": ["eslint", "ruff"],
  "environment": {
    "os": "linux",
    "user": "rmurphy"
  }
}
```

## Haiku-Specific Optimizations

### Parallel Processing
- Run all tool checks simultaneously using `&` and `wait`
- Check project types in parallel
- Non-blocking optional tool validation

### Minimal Processing
- Use shell built-ins where possible
- Avoid complex version parsing unless critical
- Quick regex patterns for version extraction

### Smart Caching
- 7-day cache retention
- Hash-based cache keys per project
- Fast cache validity checks

### Streamlined Output
- Simple pass/fail indicators
- Grouped missing tools by importance
- Direct install commands
- Single-letter user choices

## Fast-Fail Conditions
- Missing git (universal requirement)
- No write permissions in working directory
- Critical language tools missing (npm for Node, python for Python, go for Go)

## Output for Conductor
```json
{
  "status": "ready|blocked|warning",
  "missing_required": ["tool1", "tool2"],
  "missing_optional": ["tool3"],
  "user_choice": "continue|fixing|abort",
  "cache_used": true,
  "validation_time_ms": 150
}
```

## Performance Targets
- Cache hit: < 50ms
- Full validation: < 500ms  
- Parallel tool checks reduce total time by ~60%
- Minimal false positives to avoid re-validation