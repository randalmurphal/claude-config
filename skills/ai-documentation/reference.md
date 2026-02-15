# AI Documentation Reference

Companion to SKILL.md — templates and before/after examples.

---

## CLAUDE.md Template

A project root CLAUDE.md should cover what the agent cannot infer. Target under 300 lines — shorter is better.

```markdown
# Project Name

Brief purpose (1-2 lines).

## Commands

| Action | Command |
|--------|---------|
| Build | `npm run build` |
| Test (all) | `npm test` |
| Test (single) | `npm test -- path/to/test` |
| Lint | `npm run lint` |
| Type check | `npm run typecheck` |

## Architecture

Key directories:
- `src/api/` — API routes and middleware
- `src/services/` — Business logic
- `src/stores/` — State management
- `src/components/` — UI components

For detailed architecture decisions, see docs/ARCHITECTURE.md

## Code Style (Deviations from Defaults)

- [Only list rules that differ from standard conventions]
- [If using a formatter/linter, just list the command]

## Gotchas

- [Non-obvious behavior 1]
- [Non-obvious behavior 2]

## Boundaries

**Always**: Run tests before committing
**Ask first**: Schema changes, shared utility changes
**Never**: Commit secrets, modify production configs
```

## Path-Scoped Rule Template

For `.claude/rules/` files that activate only for matching paths:

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/middleware/**/*.ts"
---
# API Standards

- All endpoints validate input with zod schemas
- Error responses use `ApiError` class from `src/api/errors.ts`
- Auth middleware pattern: see `authMiddleware()` in `src/middleware/auth.ts`
- Rate limiting: see `rateLimiter()` in `src/middleware/rate-limit.ts`
```

---

## Content Optimization Examples

### Table-ify Prose (70-85% reduction)

**Before** (200 lines of prose):
```markdown
External IP detection is handled by the asset processor. The algorithm
uses the Python ipaddress module to match against CIDR notation and IP
ranges. The configuration can specify IPs as single addresses like
"10.0.0.1", CIDR blocks like "10.0.0.0/24", or ranges like
"10.0.0.1-10.0.0.255". When an IP matches the external IP configuration,
it gets stored in the data.externalIpAddresses field instead of the
data.ipAddresses field...
[180 more lines]
```

**After** (30 lines):
```markdown
## IP Classification

| Type | Condition | Field | WHY |
|------|-----------|-------|-----|
| Internal | Not in external config | `data.ipAddresses` | Default |
| External | Matches external config | `data.externalIpAddresses` | Separate security posture |

**Matching formats** (`check_if_ip_is_external()` in `asset_processor.py`):
- Single IP: `10.0.0.1`
- CIDR: `10.0.0.0/24`
- Range: `10.0.0.1-10.0.0.255`

**Config**: `config['external_ip_ranges']` — list of IP patterns
```

### Bullet Points Over Paragraphs (60-75% reduction)

**Before**:
```markdown
The import framework provides a standardized approach to data ingestion
that ensures consistency across all import tools. By following the
three-phase processing pattern of fetch, normalize, and store, all
imports maintain a consistent architecture that makes the codebase easier
to understand and maintain.
```

**After**:
```markdown
**Framework**: Standardized fetch/normalize/store pipeline across all imports.
Shared base classes, consistent testing patterns, centralized utilities.
```

### Condense File Trees (50-67% reduction)

**Before** (60 lines — every file listed):
```
project/
├── main.py                      # Main orchestrator with dual-view download
├── constants.py                  # Business logic constants
├── processors/                   # Business object processors
│   ├── base_processor.py        # Shared MongoDB/SQLite operations
│   ├── scan_file_processor.py   # Two-pass scan processing
│   ├── parallel_handler.py      # Generic parallel processing
│   ├── scan_db_handler.py       # SQLite scan database wrapper
│   ├── asset_processor.py       # Asset business objects
│   ├── vuln_processor.py        # Vulnerability processing
│   ├── compliance_processor.py  # Compliance processing
│   └── audit_processor.py       # Audit trail processing
[... 30 more lines ...]
```

**After** (20 lines — key files, counts for rest):
```
project/
├── main.py              # Orchestrator
├── constants.py          # Business logic constants
├── processors/           # Business object processors
│   ├── base_processor.py # Shared operations
│   └── [7 more processors]
├── cache/               # SQLite caching layer
├── api/                 # Async API operations
└── docs/                # Reference documentation
```

### Extract-Consolidate-Reference

**Before** (duplicate rules across 4 files):
```
BUSINESS_RULES.md (828 lines) — full rules
DV_ARCHITECTURE.md (1,575 lines) — DV rules embedded
KV_ARCHITECTURE.md (942 lines) — KV rules embedded
APP_ARCHITECTURE.md (540 lines) — app rules embedded
Total: 3,885 lines, rules defined 4 times
```

**After** (single source of truth):
```
BUSINESS_RULES.md (800 lines) — authoritative source
DV_ARCHITECTURE.md (400 lines) — "For DV rules see BUSINESS_RULES.md"
KV_ARCHITECTURE.md (300 lines) — "For KV rules see BUSINESS_RULES.md"
APP_ARCHITECTURE.md (250 lines) — "For app rules see BUSINESS_RULES.md"
Total: 1,750 lines, rules defined once
Savings: ~2,100 lines, zero duplication
```

---

## Anti-Pattern Examples

### Tutorials vs Reference

**Bad** (tutorial):
```markdown
# How to Add a New Processor

In this guide, we'll walk through adding a new business object
processor step by step. First, let's understand what a processor does...
[500 lines of tutorial]
```

**Good** (reference checklist):
```markdown
# Adding a New Processor

**Base class**: `BaseProcessor` in `processors/base_processor.py`
**Reference implementation**: `DetectedVulnProcessor` in `processors/dv_processor.py`

**Steps**:
1. Create `processors/<name>_processor.py` extending BaseProcessor
2. Implement: `should_process_record()`, `build_insert_doc()`, `build_update_fields()`
3. Register in `main.py` → `_initialize_processors()`
4. Add tests in `tests/test_<name>_processor.py`
```

### Explaining Code vs Documenting Intent

**Bad** (restating what code does):
```markdown
The function first checks if the record is None. If it is None, it
returns False. Otherwise, it extracts the severity field from the record
using the get method with a default value of '0'. Then it checks if the
severity is in the list ['0', 'Pass', 'Info']...
```

**Good** (documenting why):
```markdown
**Skip compliance insert**: severity in ['0', 'Pass', 'Info']
- See `determine_if_should_skip_dv_insert()` in `dv_processor.py`
- WHY: Pass/Info = compliant, no vulnerability record needed
```

### Mixing Abstraction Levels

**Bad** (implementation details in overview):
```markdown
# System Overview
The system processes vulnerability data through three phases. In phase 1,
the AsyncTenableSCClient uses sessionless API key authentication to
download scan data in parallel chunks of 5000 records with 10 concurrent
workers using asyncio.gather() with a semaphore...
```

**Good** (overview stays high-level):
```markdown
# System Overview

## Three-Phase Pipeline
1. **Download** — async parallel chunking to SQLite (100x faster than sequential)
2. **Process** — parallel workers with caching (2-5x throughput)
3. **Sync** — batch MongoDB writes with consolidation (60% fewer ops)

For implementation details: see docs/DOWNLOAD.md, docs/PROCESS.md, docs/SYNC.md
```

### Hierarchy Duplication

**Bad** (testing standards in 3 files):
```markdown
# Global CLAUDE.md
## Testing: 95% line coverage, 100% function coverage, 1:1 file mapping

# Project CLAUDE.md
## Testing: 95% line coverage, 100% function coverage, 1:1 file mapping  ← DUPLICATE

# Tool CLAUDE.md
## Testing: 95% line coverage, 100% function coverage, 1:1 file mapping  ← DUPLICATE
```

**Good** (define once, reference):
```markdown
# Global CLAUDE.md
## Testing: 95% line, 100% function coverage. 1:1 file mapping.

# Project CLAUDE.md
## Testing Structure
- Unit: `tests/unit/` | Integration: `tests/integration/`
- Run: `pytest tests/ --cov=src -v`
- Coverage standards: see global CLAUDE.md

# Tool CLAUDE.md
## Testing
- Tests: `tests/test_tool.py`
- Conventions: see project CLAUDE.md
```

---

## On-Demand Reference Doc Template

For detailed docs in `docs/` that agents read when needed (not auto-loaded). These can be longer — they're pulled in just-in-time.

```markdown
# [Component] Architecture

**Purpose**: [One sentence]
**Key files**: [2-3 most important files]

## Design Principles
- [Principle]: [Why it matters for this component]

## How It Works

### [Phase/Step 1]
**Input**: [What comes in]
**Output**: [What goes out]
**Key function**: `function_name()` in `path/to/file.py`

[Brief explanation of non-obvious logic]

### [Phase/Step 2]
[Same structure]

## Key Patterns
### [Pattern Name]
**When**: [Conditions to use this pattern]
**Example**: See `ExampleClass` in `path/to/example.py`
**Anti-pattern**: [What not to do and why]

## Integration Points
- Depends on: [services/components]
- Used by: [consumers]

## Gotchas
1. [Non-obvious behavior] — [why it exists]
2. [Edge case] — [how to handle]
```
