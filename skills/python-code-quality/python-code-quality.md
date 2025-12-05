# Python Code Quality & Security Analysis

**IMPORTANT: This skill is for PYTHON CODE ONLY. Do not use for JavaScript, TypeScript, Go, or other languages.**

## Overview

This skill provides comprehensive Python code quality and security analysis by running multiple tools in a unified workflow:

1. **Ruff** - Fast linting, formatting, and basic security checks
2. **Pyright** - Static type checking
3. **Bandit** - Python-specific security vulnerability scanner
4. **Semgrep** - Advanced security analysis with taint tracking

## When to Use

**MANDATORY usage:**
- Before claiming any Python code is ready for review
- During PR reviews of Python code
- When making changes to security-sensitive Python code
- Before committing Python code changes

**Optional but recommended:**
- When debugging Python code issues
- When refactoring existing Python code
- When investigating Python security concerns

## Tool Location

The unified script is located in each project's `.claude/scripts/` directory:
- m32rimm: `.claude/scripts/python-code-quality`

## Usage Patterns

### Basic Usage

```bash
# Check Python code without modifying
.claude/scripts/python-code-quality fisio/imports/tenable_sc_refactor/

# Auto-format Python code then check
.claude/scripts/python-code-quality --format fisio/imports/

# Auto-fix Python issues where possible
.claude/scripts/python-code-quality --fix fisio/common/

# Security scan only (skip style/types)
.claude/scripts/python-code-quality --security fisio/
```

### Common Scenarios

**Scenario 1: Before Committing Python Code**
```bash
# Format, fix, and check everything
.claude/scripts/python-code-quality --fix fisio/imports/nvd_api/
```

**Scenario 2: PR Review of Python Code**
```bash
# Run full analysis on changed Python files
.claude/scripts/python-code-quality fisio/imports/tenable_sc_refactor/
```

**Scenario 3: Security Audit of Python Module**
```bash
# Deep security scan only
.claude/scripts/python-code-quality --security fisio/imports/
```

**Scenario 4: Quick Python Style Check**
```bash
# Just format and lint (skip slow security scans)
ruff format fisio/ --config ~/repos/m32rimm/ruff.toml
ruff check fisio/ --config ~/repos/m32rimm/ruff.toml
```

## What Each Tool Catches (Python-Specific)

### Ruff (Python Linting)
- **Style issues**: Line length, imports, naming conventions
- **Code smells**: Unused variables, unreachable code
- **Basic security**: Hardcoded secrets (limited), dangerous functions
- **Python best practices**: PEP 8 compliance

**Severity: 🔵 MEDIUM** (mostly style/quality)

### Pyright (Python Type Checking)
- **Type errors**: Mismatched types, missing type hints
- **None handling**: Potential None dereference
- **API misuse**: Wrong function signatures
- **Import errors**: Missing modules, circular imports

**Severity: 🟡 HIGH** (prevents runtime bugs)

### Bandit (Python Security)
- **Hardcoded credentials**: Passwords, API keys, tokens
- **Dangerous functions**: `eval()`, `exec()`, `pickle.loads()`
- **Insecure crypto**: Weak algorithms, bad random
- **Injection (basic)**: `shell=True` with user input, SQL string concat
- **File operations**: Insecure temp files, path traversal

**Severity: 🔴 CRITICAL** (security vulnerabilities)

**Example Python findings:**
```python
# Bandit will catch:
password = "hardcoded123"  # B105: Hardcoded password
exec(user_input)           # B102: Use of exec()
subprocess.call(cmd, shell=True)  # B602: shell=True
```

### Semgrep (Advanced Python Security)
- **SQL injection**: Unparameterized Python DB queries
- **Command injection**: User input in subprocess calls
- **Path traversal**: Unvalidated file paths in Python
- **Insecure deserialization**: pickle, yaml.load()
- **Taint analysis**: Tracks Python data flow from sources to sinks
- **OWASP Top 10**: Python-specific patterns

**Severity: 🔴 CRITICAL** (advanced security)

**Example Python findings:**
```python
# Semgrep will catch:
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # SQL injection
os.system(f"ping {hostname}")  # Command injection
open(f"/data/{user_file}")  # Path traversal
```

## Output Interpretation

### Severity Levels

- **🔴 CRITICAL** - Security vulnerabilities in Python code (Bandit, Semgrep)
  - Fix immediately before committing
  - Block PR merges
  - Examples: SQL injection, hardcoded credentials, command injection

- **🟡 HIGH** - Type errors, logic bugs in Python (Pyright)
  - Fix before PR approval
  - Can cause runtime failures
  - Examples: Type mismatches, None errors, import issues

- **🔵 MEDIUM** - Python code quality issues (Ruff)
  - Fix when convenient
  - Improve maintainability
  - Examples: Style violations, code smells, complexity

- **🟢 LOW** - Minor Python style issues (Ruff formatting)
  - Optional improvements
  - Examples: Line length, whitespace

### Exit Codes

- **0** - All Python checks passed OR only non-critical issues
- **1** - Critical security issues found in Python code

## Integration with Claude Code

### During Code Reviews (Python)

When reviewing Python code, ALWAYS run python-code-quality before giving approval:

```bash
# Review Python PR changes
.claude/scripts/python-code-quality fisio/imports/tenable_sc_refactor/
```

If critical issues found:
1. Report specific findings with file:line references
2. Provide fix recommendations
3. DO NOT approve until fixed

### Before Claiming Done (Python)

Before saying "Python code is ready" or "implementation complete":

```bash
# Validate Python code quality
.claude/scripts/python-code-quality --fix fisio/imports/nvd_api/
```

If issues remain:
1. Fix what auto-fix couldn't handle
2. Re-run until clean
3. Document any intentional exceptions

### Manual Tool Usage (Python-Specific)

If you need to run individual Python tools:

```bash
# Ruff format Python only
ruff format fisio/ --config ~/repos/m32rimm/ruff.toml

# Ruff check Python with auto-fix
ruff check --fix fisio/ --config ~/repos/m32rimm/ruff.toml

# Pyright on Python files
pyright fisio/imports/

# Bandit on Python with medium+ severity
bandit -r fisio/ -ll -ii --exclude '*/tests/*'

# Semgrep on Python with auto rules
semgrep --config=auto fisio/ --exclude tests
```

## Tool Configurations (Python)

### Ruff (Python)
- Config: `/home/rmurphy/repos/m32rimm/ruff.toml`
- Line length: 80 characters
- Python version: 3.12
- Includes: pycodestyle, pyflakes, isort, etc.

### Pyright (Python)
- Config: `/home/rmurphy/repos/m32rimm/pyrightconfig.json`
- Type checking: strict mode
- Python version: 3.12

### Bandit (Python Security)
- Default config (no custom config needed)
- Filters: Medium+ severity, medium+ confidence
- Excludes: test files, venvs

### Semgrep (Python Security)
- Ruleset: `--config=auto` (Python security rules)
- Registry: 2000+ community rules (Python-specific)
- Excludes: test files, venvs

## Common Python Issues & Fixes

### Issue: Hardcoded Credentials (Python)

**Finding:**
```
[bandit] B105: Possible hardcoded password: 'mysecret123'
```

**Fix:**
```python
# BAD (Python)
API_KEY = "sk_live_abc123xyz"

# GOOD (Python)
import os
API_KEY = os.environ.get("API_KEY")
```

### Issue: SQL Injection (Python)

**Finding:**
```
[semgrep] SQL injection via string formatting
```

**Fix:**
```python
# BAD (Python)
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD (Python)
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### Issue: Command Injection (Python)

**Finding:**
```
[bandit] B602: shell=True with possible user input
```

**Fix:**
```python
# BAD (Python)
subprocess.call(f"ping {hostname}", shell=True)

# GOOD (Python)
subprocess.run(["ping", hostname], check=True)
```

### Issue: Type Errors (Python)

**Finding:**
```
[pyright] Argument type mismatch: expected "str" but got "int | None"
```

**Fix:**
```python
# BAD (Python)
def process(data):
    return data.upper()

# GOOD (Python)
def process(data: str) -> str:
    return data.upper()
```

## Limitations (Python)

### What Tools Don't Catch

1. **Logic bugs** - Tools can't understand business logic in Python
2. **Performance issues** - No profiling or benchmarking
3. **Runtime errors** - Only static analysis of Python code
4. **Complex vulnerabilities** - Some require manual review of Python code
5. **False negatives** - Not 100% coverage of all Python vulnerabilities

### False Positives (Python)

Sometimes Python tools flag valid code:

```python
# Bandit may flag this as insecure, but it's safe
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z]).{8,}$"  # noqa: S105
```

Use `# noqa: <code>` to suppress false positives in Python, but document why.

## Performance Notes (Python)

- **Ruff**: Fast (< 1 second for Python modules)
- **Pyright**: Medium (1-5 seconds for Python)
- **Bandit**: Medium (2-10 seconds for Python)
- **Semgrep**: Slow first run (downloads Python rules), then medium (5-30 seconds)

## Troubleshooting (Python)

### "Command not found: bandit/semgrep"

Ensure tools are installed in Python venv:
```bash
source /opt/envs/imports/bin/activate
pip install bandit semgrep
```

### "Config file not found"

Python tool configs are in M32RIMM repo:
- Ruff: `~/repos/m32rimm/ruff.toml`
- Pyright: `~/repos/m32rimm/pyrightconfig.json`

### "Too many issues"

Start with Python security only:
```bash
.claude/scripts/python-code-quality --security fisio/imports/
```

Fix critical Python issues first, then re-run full scan.

## Best Practices (Python)

1. **Run before every Python commit** - Catch issues early
2. **Auto-fix first** - `--fix` handles most Python style issues
3. **Review security findings carefully** - Don't ignore Python vulnerabilities
4. **Use in PR reviews** - Validate all Python changes
5. **Document exceptions** - If suppressing Python warnings, explain why

## Questions to Ask

- "Is this Python code?" (If no, don't use this skill)
- "What type of issues am I looking for?" (security vs style vs types)
- "Should I auto-fix Python issues?" (--fix flag)
- "Are there test files I should exclude?" (Usually yes for Python)

---

**Remember: This skill is for PYTHON CODE ONLY. For other languages, different tools and configurations are needed.**
