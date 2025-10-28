---
name: python-packaging
description: Python package management with poetry, pip, and uv including dependency resolution, lock files, version pinning, security audits (pip-audit, safety), virtual environments, and dependency graphs. Use when managing dependencies, resolving version conflicts, setting up new projects, or investigating security vulnerabilities in packages.
allowed-tools:
  - Read
  - Bash
  - Grep
---

# Python Packaging & Dependency Management

**Purpose:** Manage Python dependencies, resolve conflicts, secure packages, and set up reproducible environments.

**When to use:** Installing/updating packages, resolving version conflicts, security scanning, virtual environment setup, migrating between tools.

**For comprehensive examples and detailed workflows:** See reference.md

---

## Core Principles

1. **Always use virtual environments** - Never install to system Python
2. **Commit lock files** - Reproducibility requires exact versions
3. **Scan for security** - Use pip-audit or safety regularly
4. **Update proactively** - Old dependencies = security risks
5. **Choose the right tool** - Match tool to use case

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

---

## Essential Commands Quick Reference

### uv (Fastest)

```bash
# Install: curl -LsSf https://astral.sh/uv/install.sh | sh
uv init my-project              # Create project
uv add requests                 # Add dependency
uv add pytest --dev             # Add dev dependency
uv sync                         # Install from lock
uv run python script.py         # Run in venv
uv lock --upgrade               # Update all
uv tree                         # Show dependency tree
```

### Poetry (Full-featured)

```bash
# Install: curl -sSL https://install.python-poetry.org | python3 -
poetry new my-project           # Create project
poetry init                     # Init in existing dir
poetry add requests             # Add dependency
poetry add pytest --group dev   # Add dev dependency
poetry install                  # Install from lock
poetry run python script.py     # Run in venv
poetry update                   # Update all
poetry show --tree              # Show dependency tree
poetry build                    # Build wheel
poetry publish                  # Publish to PyPI
```

### pip (Legacy/Simple)

```bash
python3 -m venv .venv           # Create venv
source .venv/bin/activate       # Activate (Linux/Mac)
pip install requests            # Install package
pip install -r requirements.txt # Install from file
pip freeze > requirements.txt   # Generate requirements
pip install pipdeptree          # Install tree viewer
pipdeptree                      # Show dependency tree
```

---

## Virtual Environments

### Why Virtual Environments?

**Without venvs:** Global conflicts, version mismatches, breaks system Python.
**With venvs:** Isolated dependencies per project, reproducible builds.

### Creating Virtual Environments

**Manual (pip):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Automatic (uv/poetry):**
```bash
uv sync          # Creates .venv automatically
poetry install   # Creates venv automatically
```

### Best Practices

**✅ DO:**
- Add `.venv/` to `.gitignore`
- Use project-local venvs (`.venv` in project root)
- Activate before installing packages

**❌ DON'T:**
- Install packages globally
- Commit virtual environments to git
- Share venvs between projects

---

## Lock Files & Reproducibility

### What Are Lock Files?

**Purpose:** Pin exact versions of ALL dependencies (including transitive).

**Problem without locks:**
```
# requirements.txt: requests>=2.31.0
# Today: requests==2.31.0, urllib3==2.0.7
# Next month: requests==2.32.0, urllib3==2.1.0
# Result: "Works on my machine" 🔥
```

**Solution:** Lock files pin EXACT versions.

### Using Lock Files

| Tool | Lock File | Create/Update | Install |
|------|-----------|---------------|---------|
| **uv** | `uv.lock` | `uv lock` | `uv sync` |
| **Poetry** | `poetry.lock` | `poetry lock` | `poetry install` |
| **pip-tools** | `requirements.txt` | `pip-compile` | `pip-sync` |

**Update locked versions:**
```bash
uv lock --upgrade              # Update all (uv)
poetry update                  # Update all (poetry)
pip-compile --upgrade          # Update all (pip-tools)
```

✅ **Always commit lock files to git.**

---

## Version Pinning Strategies

### Version Specifier Syntax

| Specifier | Meaning | Example | Use Case |
|-----------|---------|---------|----------|
| `==` | Exact version | `requests==2.31.0` | Critical stability |
| `>=` | Minimum version | `requests>=2.31.0` | Want features from 2.31+ |
| `~=` | Compatible release | `requests~=2.31.0` | Allow 2.31.x patches |
| `^` | Poetry caret | `requests^2.31.0` | Allow 2.x but not 3.0 |
| `*` | Any version | `requests` | ⚠️ Dangerous, avoid |

### Recommended Strategy

**Applications:** Use loose constraints + lock file
```toml
# pyproject.toml
requests = "^2.31.0"  # Allow 2.x

# Lock file pins exact version
# poetry.lock or uv.lock
requests==2.31.0
```

**Libraries:** Use permissive constraints
```toml
requests = ">=2.28.0"  # Support wide range
```

---

## Security Scanning

### Tools Comparison

| Tool | Speed | Database | Cost |
|------|-------|----------|------|
| **pip-audit** | ⚡ Fast | PyPI | Free |
| **safety** | 🏃 Medium | Safety DB | Free tier |
| **snyk** | 🐌 Slow | Snyk DB | Paid |

**Recommendation:** pip-audit (free, fast, official).

### pip-audit Usage

```bash
pip install pip-audit
pip-audit                      # Scan current env
pip-audit -r requirements.txt  # Scan file
pip-audit --fix                # Show fixes
pip-audit --format json        # CI output
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
pip install --upgrade urllib3
poetry add urllib3@latest
uv add urllib3 --upgrade
```

### CI Integration

```yaml
# .github/workflows/security.yml
- name: Security audit
  run: |
    pip install pip-audit
    pip-audit
```

---

## Dependency Conflicts

### Understanding Conflicts

**Example:**
```
package-a requires requests>=2.28.0
package-b requires requests<2.28.0
Result: ⚠️ CONFLICT
```

### Resolution Steps

1. **Identify conflict**
   ```bash
   pip check
   pipdeptree --warn conflict
   ```

2. **Find compatible versions**
   ```bash
   pip index versions package-name
   pipdeptree -p requests
   ```

3. **Apply fix**
   ```bash
   poetry add package-b@latest      # Update to latest
   poetry add "requests==2.28.0"    # Pin compatible version
   poetry add package-a[minimal]    # Use minimal extras
   ```

4. **Verify**
   ```bash
   poetry install --dry-run
   pip check
   ```

---

## Dependency Graphs

### Viewing Dependency Trees

```bash
# uv
uv tree                         # Full tree
uv tree --package requests      # Specific package
uv tree --invert                # Reverse (what depends on X)

# Poetry
poetry show --tree              # Full tree
poetry show requests --tree     # Specific package

# pip (requires pipdeptree)
pip install pipdeptree
pipdeptree                      # Full tree
pipdeptree -p requests          # Specific package
pipdeptree -r -p requests       # Reverse tree
```

**Example output:**
```
requests==2.31.0
├── certifi>=2017.4.17
├── charset-normalizer>=2,<4
├── idna>=2.5,<4
└── urllib3>=1.21.1,<3
```

**Use cases:**
- Find why package is installed
- Identify bloated dependencies
- Debug import errors
- Optimize Docker image size

---

## Migration Strategies

### pip → Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
poetry init  # Imports from requirements.txt automatically
poetry install && poetry run pytest
```

### pip → uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv init
uv add $(cat requirements.txt | grep -v "^#" | cut -d= -f1)
uv sync && uv run pytest
```

### Poetry → uv

```bash
# uv understands poetry's pyproject.toml
uv sync  # Just works!
```

---

## Common Workflows

### Starting New Project

```bash
# uv (fastest)
uv init my-project && cd my-project
uv add requests pytest --dev

# Poetry (full-featured)
poetry new my-project && cd my-project
poetry add requests
poetry add pytest --group dev
```

### Adding Dependencies

```bash
# Production
uv add requests | poetry add requests | pip install requests

# Development
uv add pytest --dev | poetry add pytest --group dev
```

### Updating Dependencies

```bash
# Update all
uv lock --upgrade && uv sync
poetry update
pip-compile --upgrade && pip-sync

# Update specific
uv lock --upgrade-package requests
poetry update requests
pip install --upgrade requests
```

### Docker Integration

**uv (fastest builds):**
```dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev
COPY . .
CMD ["uv", "run", "python", "app.py"]
```

**Poetry:**
```dockerfile
FROM python:3.11-slim
RUN pip install poetry
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-dev
COPY . .
CMD ["python", "app.py"]
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Package not found | Check typo: `pip index versions pkg` |
| Version conflict | Find cause: `pipdeptree -p pkg` |
| SSL certificate error | Add to trusted hosts (only on safe network) |
| Permission denied | Use virtual environment, not system Python |
| Lock file out of sync | Regenerate: `poetry lock --no-update` or `uv lock` |

### Resolution Commands

```bash
# Show what's installed
pip list | poetry show | uv tree

# Check for conflicts
pip check
pipdeptree --warn conflict

# Verify package versions
pip show package-name
poetry show package-name
```

---

## Decision Trees

### Which tool to use?

```
Building a library for PyPI?
└─ Yes → Poetry (has build/publish tools)
└─ No
   ├─ Need maximum speed? → uv
   ├─ Legacy codebase? → pip
   └─ Want auto-venv? → uv or Poetry
```

### How to pin versions?

```
Is this an application?
└─ Yes → Lock file + loose constraints (^2.31.0)
   ├─ Security-critical? → Exact pin (==2.31.0)
   └─ Regular package? → Compatible (^2.31.0)
└─ No (library) → Loose constraints (>=2.28.0)
```

### Update frequency?

```
Security vulnerability?
└─ Yes → Update immediately
└─ No
   ├─ Major version? → Test in branch first
   ├─ Minor/patch? → Weekly/monthly
   └─ Full update? → Quarterly review
```

---

## Remember

**The Golden Rules:**
1. **Always use virtual environments** - Never install to system Python
2. **Commit lock files** - Enables reproducible builds
3. **Scan for security** - Run pip-audit regularly
4. **Update proactively** - Old dependencies = security risks
5. **Choose the right tool** - Match tool to project needs

**Common mistakes:**
- Installing without active venv
- Not committing lock files
- Using `pip freeze` instead of lock files
- Ignoring security warnings
- Pinning exact versions without reason

**For detailed examples, workflows, and private repos:** See reference.md
