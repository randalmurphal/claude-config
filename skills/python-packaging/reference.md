# Python Packaging & Dependency Management - Reference

**This is the detailed reference document for python-packaging skill.**

**For core concepts and quick reference:** See SKILL.md

**This document contains:** Comprehensive examples, detailed workflows, private repository configuration, troubleshooting guides, and advanced topics.

---

## Overview

**Purpose:** Manage Python dependencies, resolve conflicts, secure packages, and set up reproducible environments.

**When to use:** Installing/updating packages, resolving version conflicts, security scanning, virtual environment setup, migrating between tools.

---

## Tool Comparison: Poetry vs Pip vs uv

| Feature | **uv** | **Poetry** | **pip** |
|---------|--------|-----------|---------|
| **Speed** | ⚡⚡⚡ Fastest (Rust) | 🏃 Fast | 🐌 Slowest |
| **Lock files** | ✅ uv.lock | ✅ poetry.lock | ❌ Needs pip-tools |
| **Dependency resolution** | ✅ Advanced | ✅ Advanced | ⚠️ Basic |
| **Virtual envs** | ✅ Auto-managed | ✅ Auto-managed | ❌ Manual |
| **Build system** | ❌ No | ✅ Full | ❌ No |
| **Project scaffolding** | ❌ No | ✅ Yes | ❌ No |
| **Maturity** | 🆕 New (2024) | ✅ Stable | ✅ Ancient |
| **Best for** | Speed, installs | Full projects | Legacy, simple |

**Quick decision:**
- **New project with build needs?** → Poetry
- **Fast installs/monorepo?** → uv
- **Legacy/simple script?** → pip
- **Maximum compatibility?** → pip

---

## Quick Command Reference

### uv Commands

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
uv init my-project
cd my-project

# Install from existing requirements.txt
uv pip install -r requirements.txt

# Add dependency
uv add requests
uv add pytest --dev

# Install all dependencies
uv sync

# Run command in project environment
uv run python script.py
uv run pytest

# Update dependencies
uv lock --upgrade

# Show dependency tree
uv tree
```

### Poetry Commands

```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Create new project
poetry new my-project
cd my-project

# Initialize in existing directory
poetry init

# Add dependency
poetry add requests
poetry add pytest --group dev

# Install all dependencies
poetry install

# Update dependencies
poetry update
poetry update requests  # Update specific package

# Run command in virtual environment
poetry run python script.py
poetry run pytest

# Show dependency tree
poetry show --tree

# Build package
poetry build

# Publish to PyPI
poetry publish
```

### pip Commands

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install package
pip install requests
pip install -e .  # Install local package in editable mode

# Install from requirements.txt
pip install -r requirements.txt

# Generate requirements.txt
pip freeze > requirements.txt

# Update package
pip install --upgrade requests

# Show dependency tree (requires pipdeptree)
pip install pipdeptree
pipdeptree
```

---

## Virtual Environment Management

### Why Virtual Environments Matter

**Problem without venvs:**
- Global package conflicts
- Different projects need different versions
- Unclear what dependencies are actually needed
- Breaks system Python

**Solution:**
- Isolated dependencies per project
- Reproducible builds
- Safe experimentation

### Creating Virtual Environments

**Using venv (stdlib):**
```bash
# Create
python3 -m venv .venv

# Activate
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Deactivate
deactivate
```

**Using uv (automatic):**
```bash
# uv creates and manages venv automatically
uv sync  # Creates .venv if missing
uv run python script.py  # Uses .venv automatically
```

**Using poetry (automatic):**
```bash
# Poetry creates venv automatically
poetry install  # Creates venv if missing
poetry run python script.py  # Uses venv automatically

# Manual venv control
poetry env use python3.11
poetry env list
poetry env remove python3.11
```

### Best Practices

**✅ DO:**
- Add `.venv/` to `.gitignore`
- Use project-local venvs (`.venv` in project root)
- Activate before installing packages
- Document Python version requirement

**❌ DON'T:**
- Install packages globally
- Commit virtual environments to git
- Share venvs between projects
- Use system Python for development

---

## Lock Files & Reproducibility

### What Are Lock Files?

**Purpose:** Pin exact versions of ALL dependencies (including transitive).

**Problem they solve:**
```
# requirements.txt
requests>=2.31.0

# What gets installed TODAY: requests==2.31.0, urllib3==2.0.7
# What gets installed NEXT MONTH: requests==2.32.0, urllib3==2.1.0
# Result: "Works on my machine" syndrome
```

**Solution:** Lock files pin EXACT versions.

### uv Lock Files

**File:** `uv.lock`

```bash
# Create/update lock file
uv lock

# Install from lock file (exact versions)
uv sync

# Update lock file (get new versions)
uv lock --upgrade
uv lock --upgrade-package requests  # Update specific package
```

**Commit to git:** ✅ YES (both `pyproject.toml` and `uv.lock`)

### Poetry Lock Files

**File:** `poetry.lock`

```bash
# Create/update lock file
poetry lock

# Install from lock file (exact versions)
poetry install

# Update lock file (get new versions)
poetry update
poetry update requests  # Update specific package
```

**Commit to git:** ✅ YES (both `pyproject.toml` and `poetry.lock`)

### pip-tools Lock Files

**Files:** `requirements.in` → `requirements.txt`

```bash
# Install pip-tools
pip install pip-tools

# requirements.in (your dependencies)
requests>=2.31.0
pytest>=7.4.0

# Generate locked requirements.txt
pip-compile requirements.in

# Install from lock file
pip-sync requirements.txt

# Update lock file
pip-compile --upgrade requirements.in
```

**Commit to git:** ✅ YES (both `.in` and `.txt` files)

### Reproducibility Checklist

- [ ] Lock file committed to git
- [ ] Python version specified (`pyproject.toml` or `.python-version`)
- [ ] Lock file updated regularly (not stale)
- [ ] CI uses lock file (not `pip install package`)
- [ ] Dependencies grouped (dev vs prod)

---

## Dependency Resolution & Conflict Handling

### Understanding Dependency Conflicts

**Example conflict:**
```
You want:
  - package-a (requires requests>=2.28.0)
  - package-b (requires requests<2.28.0)

Result: ⚠️ CONFLICT - No version of requests satisfies both
```

### Resolution Strategies by Tool

**uv (fastest, smartest):**
```bash
# uv shows clear conflict messages
uv add package-a package-b
# Error: Cannot resolve requests (>=2.28.0 conflicts with <2.28.0)

# Solution: Check if newer versions fix conflict
uv add package-a package-b --upgrade
```

**Poetry (clear error messages):**
```bash
poetry add package-a package-b
# Resolving dependencies... (1.5s)
# Because package-a depends on requests (>=2.28.0)
#  and package-b depends on requests (<2.28.0),
#  package-a is incompatible with package-b.

# Solution: Try upgrading constraints
poetry add package-b@latest
```

**pip (opaque, can install broken state):**
```bash
# pip doesn't check conflicts until runtime!
pip install package-a package-b  # Silently installs
python script.py  # ImportError or runtime failure

# Check for conflicts manually
pip check
```

### Fixing Dependency Conflicts

**Step 1: Identify conflict**
```bash
# uv/poetry show error automatically
# pip needs manual check
pip check
pipdeptree --warn conflict
```

**Step 2: Find compatible versions**
```bash
# Check available versions
pip index versions requests

# Check what depends on conflicting package
pipdeptree -p requests
poetry show requests --tree
```

**Step 3: Apply fix**
```bash
# Option 1: Update package to newer version
poetry add package-b@latest
uv add package-b --upgrade

# Option 2: Pin specific version that works
poetry add "requests==2.28.0"
uv add "requests==2.28.0"

# Option 3: Use extras to avoid dependency
poetry add package-a[minimal]  # If available
```

**Step 4: Verify resolution**
```bash
# Check no conflicts remain
poetry install --dry-run
uv sync --dry-run
pip check
```

---

## Version Pinning Strategies

### Version Specifier Syntax

| Specifier | Meaning | Example | Use Case |
|-----------|---------|---------|----------|
| `==` | Exact version | `requests==2.31.0` | Critical stability |
| `>=` | Minimum version | `requests>=2.31.0` | Want features from 2.31+ |
| `~=` | Compatible release | `requests~=2.31.0` | Allow 2.31.x patches |
| `^` | Poetry caret | `requests^2.31.0` | Allow 2.x but not 3.0 |
| `*` | Any version | `requests` | Dangerous, avoid |

### Pinning Strategies

**Strategy 1: Loose in project, locked in lock file (RECOMMENDED)**

```toml
# pyproject.toml (loose constraints)
[tool.poetry.dependencies]
requests = "^2.31.0"  # Allow 2.x
pytest = "^7.4.0"     # Allow 7.x
```

**Benefits:**
- Lock file pins exact versions
- Easy to update when needed
- Compatible with dependency resolution

**Strategy 2: Exact pins (for critical dependencies)**

```toml
# pyproject.toml (exact versions)
[tool.poetry.dependencies]
cryptography = "==41.0.7"  # Security-critical
```

**When to use:**
- Security-critical packages
- Known bugs in newer versions
- Compliance requirements

**Strategy 3: Minimal pins (for libraries)**

```toml
# pyproject.toml (library, not application)
[tool.poetry.dependencies]
requests = ">=2.28.0"  # Support wide range
```

**When to use:**
- Publishing libraries to PyPI
- Want maximum compatibility

### Updating Pinned Versions

```bash
# uv: Update all packages
uv lock --upgrade

# uv: Update specific package
uv lock --upgrade-package requests

# Poetry: Update all packages
poetry update

# Poetry: Update specific package
poetry update requests

# pip-tools: Update all
pip-compile --upgrade requirements.in
```

---

## Security Scanning

### Available Tools

| Tool | Speed | Database | Output Quality | Cost |
|------|-------|----------|----------------|------|
| **pip-audit** | ⚡ Fast | PyPI | Clear | Free |
| **safety** | 🏃 Medium | Safety DB | Detailed | Free tier |
| **snyk** | 🐌 Slow | Snyk DB | Comprehensive | Paid |

**Recommendation:** Start with pip-audit (free, fast, official).

### pip-audit

**Installation:**
```bash
pip install pip-audit
```

**Usage:**
```bash
# Scan current environment
pip-audit

# Scan requirements file
pip-audit -r requirements.txt

# Scan with fix suggestions
pip-audit --fix

# JSON output for CI
pip-audit --format json

# Ignore specific vulnerabilities
pip-audit --ignore-vuln GHSA-xxxx-xxxx-xxxx
```

**Example output:**
```
Found 2 known vulnerabilities in 1 package
Name    Version  ID              Fix Versions
------  -------  --------------  ------------
urllib3 2.0.7    GHSA-v845-jxx5  2.1.0
urllib3 2.0.7    PYSEC-2023-228  2.1.0
```

**Fix:**
```bash
# Update vulnerable package
pip install --upgrade urllib3

# Or with poetry
poetry add urllib3@latest

# Or with uv
uv add urllib3 --upgrade
```

### safety

**Installation:**
```bash
pip install safety
```

**Usage:**
```bash
# Scan current environment
safety check

# Scan requirements file
safety check -r requirements.txt

# JSON output
safety check --json

# CI-friendly (exit code on vuln)
safety check --exit-code
```

### Integrating Security Scans in CI

**GitHub Actions:**
```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install pip-audit
          pip install -r requirements.txt

      - name: Run security audit
        run: pip-audit
```

### Security Best Practices

**✅ DO:**
- Run security scans regularly (weekly or on CI)
- Update dependencies proactively
- Review security advisories for direct dependencies
- Use lock files to prevent surprise updates

**❌ DON'T:**
- Ignore security warnings without investigation
- Pin old versions indefinitely
- Trust all packages blindly
- Skip scanning transitive dependencies

---

## Private Package Repositories

### Common Use Cases
- Internal company packages
- Private forks of open-source packages
- Proprietary libraries

### Configuration by Tool

**pip (pip.conf or pip.ini):**
```ini
# ~/.pip/pip.conf (Linux/Mac)
# ~/pip/pip.ini (Windows)

[global]
index-url = https://pypi.org/simple
extra-index-url = https://private.pypi.company.com/simple
trusted-host = private.pypi.company.com
```

**uv:**
```bash
# Environment variable
export UV_INDEX_URL=https://private.pypi.company.com/simple

# Or in pyproject.toml
[[tool.uv.index]]
url = "https://private.pypi.company.com/simple"
name = "private"
```

**Poetry:**
```toml
# pyproject.toml
[[tool.poetry.source]]
name = "private"
url = "https://private.pypi.company.com/simple"
priority = "supplemental"  # or "primary" to use only this
```

### Authentication

**Environment variables (most secure):**
```bash
# Set credentials
export UV_INDEX_USERNAME=myuser
export UV_INDEX_PASSWORD=mytoken

# Or use netrc
# ~/.netrc
machine private.pypi.company.com
  login myuser
  password mytoken
```

**Poetry credential store:**
```bash
# Store credentials securely
poetry config http-basic.private myuser mytoken

# Or use token
poetry config pypi-token.private mytoken
```

### Installing from Private Repos

```bash
# pip (uses pip.conf)
pip install private-package

# uv
uv add private-package

# Poetry
poetry add private-package
```

---

## Dependency Graphs

### pipdeptree (pip)

**Installation:**
```bash
pip install pipdeptree
```

**Usage:**
```bash
# Show full tree
pipdeptree

# Show specific package
pipdeptree -p requests

# Reverse tree (what depends on X)
pipdeptree -r -p requests

# Show only conflicts
pipdeptree --warn conflict

# JSON output
pipdeptree --json-tree
```

**Example output:**
```
requests==2.31.0
├── certifi [required: >=2017.4.17, installed: 2023.11.17]
├── charset-normalizer [required: >=2,<4, installed: 3.3.2]
├── idna [required: >=2.5,<4, installed: 3.6]
└── urllib3 [required: >=1.21.1,<3, installed: 2.1.0]
```

### Poetry dependency tree

```bash
# Show full tree
poetry show --tree

# Show specific package
poetry show requests --tree

# Show only top-level
poetry show --only main
poetry show --only dev
```

### uv dependency tree

```bash
# Show full tree
uv tree

# Show specific package
uv tree --package requests

# Reverse tree
uv tree --invert
```

### Understanding Dependency Trees

**Why trees matter:**
- Identify bloated dependencies
- Find duplicate dependencies at different versions
- Debug import errors
- Optimize Docker image size

**Example investigation:**
```bash
# Why is this package installed?
pipdeptree -r -p cryptography

# Output shows:
# cryptography==41.0.7
# └── requests==2.31.0 [requires: cryptography>=1.3.4]
```

---

## Migration Strategies

### pip → Poetry

**Step 1: Install Poetry**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Step 2: Initialize project**
```bash
# Let Poetry detect existing dependencies
poetry init

# Or import from requirements.txt
poetry add $(cat requirements.txt | grep -v "^#" | cut -d= -f1)
```

**Step 3: Verify dependencies**
```bash
poetry install
poetry run pytest  # Test that everything works
```

**Step 4: Clean up**
```bash
# Remove old venv
deactivate
rm -rf venv/

# Remove old requirements files (keep for reference initially)
# mv requirements.txt requirements.txt.old
```

### pip → uv

**Step 1: Install uv**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Step 2: Initialize project**
```bash
# Create pyproject.toml
uv init

# Install from existing requirements.txt
uv add $(cat requirements.txt | grep -v "^#" | cut -d= -f1)
```

**Step 3: Verify installation**
```bash
uv sync
uv run pytest
```

### Poetry → uv

**Step 1: Install uv**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Step 2: uv reads Poetry's pyproject.toml**
```bash
# uv understands poetry format
uv sync  # Uses existing pyproject.toml
```

**Step 3: Optional - Convert to uv format**
```bash
# If you want pure uv format
uv init
# Manually copy dependencies from [tool.poetry.dependencies]
# to [project.dependencies] in pyproject.toml
```

---

## Common Workflows

### Starting New Project

**With uv (fastest):**
```bash
uv init my-project
cd my-project
uv add requests pytest --dev
uv run python -c "import requests; print(requests.__version__)"
```

**With Poetry (full-featured):**
```bash
poetry new my-project
cd my-project
poetry add requests
poetry add pytest --group dev
poetry run python -c "import requests; print(requests.__version__)"
```

### Adding Development Dependencies

```bash
# uv
uv add pytest ruff pyright --dev

# Poetry
poetry add pytest ruff pyright --group dev

# pip (requirements-dev.txt)
echo "pytest" >> requirements-dev.txt
echo "ruff" >> requirements-dev.txt
pip install -r requirements-dev.txt
```

### Updating All Dependencies

```bash
# uv (safest, updates lock file)
uv lock --upgrade
uv sync

# Poetry
poetry update

# pip-tools
pip-compile --upgrade requirements.in
pip-sync requirements.txt
```

### Docker Integration

**Using uv (fastest builds):**
```dockerfile
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (uses lock file)
RUN uv sync --no-dev

# Copy application
COPY . .

CMD ["uv", "run", "python", "app.py"]
```

**Using Poetry:**
```dockerfile
FROM python:3.11-slim

# Install poetry
RUN pip install poetry

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies without creating venv
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy application
COPY . .

CMD ["python", "app.py"]
```

---

## Troubleshooting

### "Package not found"

**Problem:** Package exists but can't be found.

**Solutions:**
```bash
# Check PyPI index
pip index versions package-name

# Try with pip directly
pip install package-name

# Check if typo or renamed
# Example: "Pillow" not "PIL"
```

### "Version conflict cannot be resolved"

**Problem:** Multiple packages need incompatible versions.

**Solutions:**
```bash
# Show dependency tree
pipdeptree -p conflicting-package

# Try updating packages
poetry update
uv lock --upgrade

# Use compatible versions
poetry add package@latest
```

### "SSL certificate verify failed"

**Problem:** Corporate proxy or firewall blocks PyPI.

**Solutions:**
```bash
# Add trusted host (ONLY if safe network)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org package-name

# Or configure in pip.conf
[global]
trusted-host = pypi.org files.pythonhosted.org
```

### "Permission denied" when installing

**Problem:** Trying to install to system Python.

**Solutions:**
```bash
# Use virtual environment (RECOMMENDED)
python3 -m venv .venv
source .venv/bin/activate
pip install package-name

# Or user install (NOT recommended)
pip install --user package-name
```

### Lock file out of sync

**Problem:** `poetry.lock` or `uv.lock` doesn't match `pyproject.toml`.

**Solutions:**
```bash
# Poetry
poetry lock --no-update  # Update lock without upgrading

# uv
uv lock  # Regenerate lock file
```

---

## Quick Decision Trees

### "Which tool should I use?"

```
Building a library? → Poetry (has build tools)
├─ No
│  ├─ Need maximum speed? → uv
│  ├─ Legacy/simple project? → pip
│  └─ Want auto-venv? → uv or Poetry
└─ Yes → Poetry
```

### "How should I pin versions?"

```
Is this an application? → Lock file + loose constraints
├─ Yes
│  ├─ Critical package? → Exact pin (==)
│  └─ Regular package? → Compatible (^2.31.0)
└─ No (library) → Loose constraints (>=2.28.0)
```

### "How often should I update dependencies?"

```
Security vulnerability? → Immediately
├─ No
│  ├─ Major version update? → Test in branch
│  ├─ Minor/patch update? → Weekly/monthly
│  └─ All dependencies? → Quarterly review
└─ Yes → Update and test ASAP
```

---

## Remember

**The Golden Rules:**
1. **Always use virtual environments** - Never install to system Python
2. **Commit lock files** - Reproducibility requires exact versions
3. **Scan for security issues** - Use pip-audit or safety regularly
4. **Update proactively** - Old dependencies = security risks
5. **Choose the right tool** - Poetry for libraries, uv for speed, pip for legacy

**Common mistakes to avoid:**
- Installing packages without active venv
- Not committing lock files to git
- Using `pip freeze` instead of proper lock files
- Ignoring security warnings
- Pinning exact versions without reason
