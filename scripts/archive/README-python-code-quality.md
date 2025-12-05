# Python Code Quality Setup - Complete Documentation

## Overview

This setup provides comprehensive Python code quality and security analysis using multiple best-in-class tools:

- **Ruff** - Fast Python linting and formatting
- **Pyright** - Python type checking
- **Bandit** - Python security vulnerability scanner
- **Semgrep** - Advanced Python security with taint analysis

**IMPORTANT: These tools are for PYTHON CODE ONLY. Do not use for other languages.**

## What You Asked For

You wanted a script that:
1. ✅ Auto-formats Python code with ruff
2. ✅ Runs all linters/checkers automatically
3. ✅ Outputs issues so agents don't forget to run checks
4. ✅ Provides clear, actionable results

That's exactly what `python-code-quality` does!

## Installation Summary

✅ **Installed Tools:**
- `bandit` v1.8.6 - Python security scanner
- `semgrep` v1.141.0 - Advanced Python security
- `ruff` (already installed) - Python linting/formatting
- `pyright` (already installed) - Python type checking

All installed in: `/opt/envs/imports`

## Script Location

**Main script:** `~/.claude/scripts/python-code-quality`

**Skill:** `~/.claude/skills/python-code-quality/`

## Basic Usage

**Note:** Script is at `~/.claude/scripts/python-code-quality`. Use full path or add to PATH.

```bash
# Check Python code
~/.claude/scripts/python-code-quality fisio/

# Auto-format then check Python code
~/.claude/scripts/python-code-quality --format fisio/

# Auto-fix Python issues where possible
~/.claude/scripts/python-code-quality --fix fisio/

# Security scan only (skip style/types)
~/.claude/scripts/python-code-quality --security fisio/
```

## What Each Tool Catches (Python-Specific)

### 1. Ruff (Python Linting & Formatting)
**Speed:** ⚡ Very fast (< 1 second)
**Severity:** 🔵 MEDIUM (mostly style/quality)

**Catches:**
- Python style violations (PEP 8)
- Unused Python imports/variables
- Python code smells (complexity, duplicates)
- Hardcoded secrets (basic detection in Python)
- Unsafe Python function usage

**Example:**
```python
# Ruff will catch:
import os, sys  # Bad import style
x = 1; y = 2    # Multiple statements on one line
```

### 2. Pyright (Python Type Checking)
**Speed:** 🚶 Medium (1-5 seconds)
**Severity:** 🟡 HIGH (prevents runtime bugs)

**Catches:**
- Python type mismatches
- Missing Python type hints
- None/null dereference in Python
- Wrong Python function signatures
- Python import errors

**Example:**
```python
# Pyright will catch:
def add(a: int, b: int) -> int:
    return a + b

add("hello", "world")  # Type error!
```

### 3. Bandit (Python Security)
**Speed:** 🚶 Medium (2-10 seconds)
**Severity:** 🔴 CRITICAL (security vulnerabilities)
**Configuration:** HIGH confidence only (filters false positives)

**Catches:**
- Hardcoded Python credentials/API keys
- Dangerous Python functions (eval, exec, pickle)
- Weak crypto in Python
- SQL injection (basic patterns in Python)
- Command injection (`shell=True` in Python)
- Insecure temp files in Python

**False Positive Filtering:**
- Uses `-iii` flag (HIGH confidence only)
- Filters out B608 SQL injection warnings on validated identifiers
- Reduces noise while catching real security issues
- Example: Won't flag `f'DELETE FROM {validate_identifier(table)}'`

**Example:**
```python
# Bandit will catch (HIGH confidence):
password = "hardcoded123"  # B105: Hardcoded password (if HIGH conf)
exec(user_input)           # B102: Use of exec()
subprocess.call(cmd, shell=True)  # B602: shell=True
```

### 4. Semgrep (Advanced Python Security)
**Speed:** 🐌 Slow first run (downloads rules), then medium (5-30 sec)
**Severity:** 🔴 CRITICAL (advanced security)

**Catches:**
- SQL injection (taint analysis in Python)
- Command injection (data flow tracking in Python)
- Path traversal in Python
- Insecure deserialization in Python
- XSS vulnerabilities in Python web apps
- OWASP Top 10 (Python-specific)

**Example:**
```python
# Semgrep will catch:
query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection
os.system(f"ping {hostname}")  # Command injection
open(f"/data/{user_file}")  # Path traversal
```

## Should You Run Everything Together?

**YES! Here's why:**

### ✅ Reasons to Run All Tools Together:

1. **Complementary Coverage**
   - Ruff catches Python style issues
   - Pyright catches Python type errors
   - Bandit catches Python security basics
   - Semgrep catches Python advanced security
   - Together = comprehensive Python analysis

2. **Different Strengths**
   - Ruff is fast for Python style checks
   - Semgrep is deep for Python injection attacks
   - They don't overlap much

3. **Catches More Python Issues**
   - Example: Ruff won't catch SQL injection
   - Example: Semgrep won't catch type errors
   - Example: Pyright won't catch hardcoded passwords

4. **Agent Memory**
   - Running one script = agent can't forget steps
   - All results in one output
   - Clear severity markers

### ⚠️ Potential Downsides (Minimal):

1. **Slightly Slower** - But still fast for Python:
   - Ruff: < 1 second
   - Pyright: 1-5 seconds
   - Bandit: 2-10 seconds
   - Semgrep: 5-30 seconds
   - **Total: ~10-50 seconds for typical Python module**

2. **More Output** - But organized by severity:
   - Critical issues shown first
   - Easy to filter (use `--security` for Python security only)

3. **Possible False Positives** - But rare:
   - Can suppress with `# noqa` in Python
   - Should document why

### 🎯 Recommendation: YES, Run Everything

**The benefits FAR outweigh the downsides for Python code.**

You get:
- ✅ Complete Python security coverage
- ✅ Early bug detection in Python
- ✅ Better Python code quality
- ✅ One command to rule them all
- ✅ Consistent results every time

**When to skip tools:**
- `--security` flag: Skip style/types, only Python security
- Time-sensitive: Run ruff + pyright first (faster Python checks)
- Initial scan of large Python codebase: Start with `--security`

## Common Workflows

### Workflow 1: Before Committing Python Code
```bash
# Fix everything possible in Python code
python-code-quality --fix fisio/imports/tenable_sc/

# Review remaining issues in Python
# Fix manually if needed
# Commit when clean
```

### Workflow 2: PR Review of Python Code
```bash
# Run full analysis on Python changes
python-code-quality fisio/imports/tenable_sc_refactor/

# Review all findings
# Request changes if critical issues found
```

### Workflow 3: Security Audit of Python Module
```bash
# Deep security scan of Python only
python-code-quality --security fisio/

# Review critical findings
# Fix vulnerabilities before release
```

### Workflow 4: Quick Python Style Check
```bash
# Just format and lint Python (skip security)
ruff format fisio/ --config ~/repos/m32rimm/ruff.toml
ruff check --fix fisio/ --config ~/repos/m32rimm/ruff.toml
```

## Integration with Claude Code

### For Agents (Claude Code)

When I'm reviewing or writing Python code, I should:

1. **Always run before claiming "done":**
   ```bash
   python-code-quality --fix [python_path]
   ```

2. **Report findings clearly:**
   - 🔴 CRITICAL → Block PR, must fix
   - 🟡 HIGH → Request changes
   - 🔵 MEDIUM → Suggest improvements
   - 🟢 LOW → Optional

3. **Load the skill when needed:**
   ```
   /skill python-code-quality
   ```

### For Users (You)

You can run this anytime:
```bash
# From m32rimm directory
~/.claude/scripts/python-code-quality fisio/

# Or add to PATH for easier access
export PATH="$HOME/.claude/scripts:$PATH"
python-code-quality fisio/
```

## Understanding Output

### Example Output:
```
🔴 CRITICAL - Bandit found issues
fisio/imports/nvd_api/helpers.py:42:
  B105: Possible hardcoded password: 'mysecret123'

🟡 HIGH - Pyright found issues
fisio/imports/nvd_api/helpers.py:56:
  Argument type mismatch: expected "str" but got "int | None"

🔵 MEDIUM - Ruff check found issues
fisio/imports/nvd_api/helpers.py:78:
  PLR0911 Too many return statements (11 > 6)
```

### What to Do:

**🔴 CRITICAL (Security):**
- Fix **immediately** before committing Python code
- These are real vulnerabilities in Python
- Examples: SQL injection, hardcoded credentials

**🟡 HIGH (Type Errors):**
- Fix **before PR approval** in Python
- Will likely cause runtime failures in Python
- Examples: Type mismatches, None errors

**🔵 MEDIUM (Quality):**
- Fix **when convenient** in Python
- Improves maintainability of Python code
- Examples: Complexity, unused variables

**🟢 LOW (Style):**
- Optional Python improvements
- Auto-fixable with `--fix`

## Performance Tips

### For Large Python Codebases:

1. **Scan incrementally:**
   ```bash
   # Just the Python module you're working on
   python-code-quality fisio/imports/tenable_sc/
   ```

2. **Security first:**
   ```bash
   # Skip slow type checking for Python
   python-code-quality --security fisio/
   ```

3. **Use .gitignore patterns:**
   - Script already excludes Python test files
   - Script already excludes venvs

### First Run (Semgrep):
- Downloads Python security rules (~50MB)
- Takes 1-2 minutes first time
- Subsequent runs are much faster for Python

## Troubleshooting

### "Command not found: python-code-quality"

**Fix:**
```bash
# Make sure script is executable
chmod +x ~/.claude/scripts/python-code-quality

# Or use full path
~/.claude/scripts/python-code-quality fisio/
```

### "Command not found: bandit/semgrep"

**Fix:**
```bash
# Activate venv and install
source /opt/envs/imports/bin/activate
pip install bandit semgrep
```

### "Too many Python issues found"

**Fix:**
```bash
# Start with security only for Python
python-code-quality --security fisio/

# Fix critical Python issues first
# Then run full scan
python-code-quality fisio/
```

### "Semgrep is slow on Python code"

**Fix:**
```bash
# First run downloads Python rules (slow)
# Subsequent runs are faster

# Or skip semgrep temporarily:
ruff format fisio/
ruff check --fix fisio/
pyright fisio/
bandit -r fisio/ -ll -ii
```

## Files Created

```
~/.claude/scripts/
  └── python-code-quality          # Main script (Python only)
      └── README-python-code-quality.md  # This file

~/.claude/skills/
  └── python-code-quality/         # Skill for Claude Code
      ├── skill.yml                # Skill metadata (Python)
      └── python-code-quality.md   # Detailed documentation (Python)

/opt/envs/imports/                 # Python venv
  └── (bandit, semgrep installed)
```

## Next Steps

### Recommended:

1. **Add to Git pre-commit hook** (Python only):
   ```bash
   # .git/hooks/pre-commit
   #!/bin/bash
   ~/.claude/scripts/python-code-quality --security --fix .
   ```

2. **Add to GitLab CI** (Python analysis):
   ```yaml
   # .gitlab-ci.yml
   python-security-scan:
     script:
       - pip install bandit semgrep
       - ~/.claude/scripts/python-code-quality --security fisio/
   ```

3. **Add to PATH** for easy access:
   ```bash
   # ~/.bashrc
   export PATH="$HOME/.claude/scripts:$PATH"
   ```

### Optional:

1. **Configure Python IDE integration**:
   - VSCode: Install Ruff, Pyright, Bandit extensions
   - PyCharm: Enable inspections

2. **Customize Python rules**:
   - Ruff: Edit `~/repos/m32rimm/ruff.toml`
   - Pyright: Edit `~/repos/m32rimm/pyrightconfig.json`
   - Bandit: Create `.bandit` config
   - Semgrep: Create custom Python rules

3. **Set up Python notifications**:
   - Slack/email on critical Python findings
   - GitLab MR comments with Python scan results

## Summary

✅ **Setup Complete!**

You now have:
- ✅ Comprehensive Python security scanning (Bandit + Semgrep)
- ✅ Python type checking (Pyright)
- ✅ Python linting & formatting (Ruff)
- ✅ Unified script for all Python tools
- ✅ Claude Code skill for Python analysis
- ✅ Clear, actionable Python output

**One command for complete Python code quality:**
```bash
python-code-quality --fix fisio/
```

**For agents (Claude Code):**
- Load skill: `/skill python-code-quality`
- Run before claiming Python code is done
- Report findings with severity markers

**For you:**
- Run anytime on Python code
- Add to CI/CD pipeline
- Use in PR reviews

## Questions?

Common questions answered:

**Q: Should I run this on every Python commit?**
A: Yes! Catches issues early in Python development.

**Q: Can I skip some Python tools?**
A: Yes, use `--security` for security-only Python scanning.

**Q: What about other languages (JS, Go, etc.)?**
A: These tools are PYTHON ONLY. Need different tools for other languages.

**Q: How do I suppress Python false positives?**
A: Script already filters false positives (bandit uses HIGH confidence only). For remaining false positives, use `# noqa: <code>` in Python and document why.

**Q: Why don't I see B608 SQL injection warnings on validated identifiers?**
A: Bandit is configured with `-iii` (HIGH confidence only) to avoid false positives on code that properly validates SQL identifiers before use.

**Q: Is this free?**
A: Yes! All tools are 100% free for Python.

**Q: Better than SonarQube?**
A: Yes, for free tier. Bandit+Semgrep > SonarQube Community for Python.

---

**Enjoy cleaner, safer Python code!** 🐍🔒
