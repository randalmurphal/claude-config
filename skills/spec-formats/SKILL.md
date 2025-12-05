---
name: spec-formats
description: Templates for brainstorm artifacts and manifest.json. Load when using /spec.
---

# Spec Formats

## Spec Storage

Specs live in the project's `.claude/specs/` directory:

```
<git_root>/
└── .claude/
    └── specs/
        └── <name>-<hash>/
            ├── manifest.json          # Execution config (machine-readable)
            ├── SPEC.md                # Human-readable spec
            ├── CONTEXT.md             # Accumulated context
            ├── STATE.json             # Execution state
            ├── brainstorm/            # From /spec phase
            │   ├── MISSION.md
            │   ├── INVESTIGATION.md
            │   ├── DECISIONS.md
            │   ├── CONCERNS.md
            │   └── SPIKE_RESULTS/
            └── components/            # Per-component context
                ├── component_a.md
                └── component_b.md
```

CLI commands:
- `python -m cc_orchestrations list` - List specs in current project
- `python -m cc_orchestrations new --name feature` - Create new spec
- `python -m cc_orchestrations status --spec <name>` - Show status

---

## Brainstorm Artifacts

### MISSION.md (50-100 lines)

```markdown
# Mission

## Goal
[Single sentence: what we're building and why]

## Success Criteria
- [ ] Measurable outcome 1
- [ ] Measurable outcome 2
- [ ] Performance/quality target

## Non-Goals
- Thing we're explicitly NOT doing
- Out of scope item

## Constraints
- Hard requirement 1
- Hard requirement 2
```

### INVESTIGATION.md

```markdown
# Investigation Findings

## Project Structure
[What we found - tech stack, directory layout]

## Existing Patterns
- Auth: [how auth works]
- APIs: [API patterns used]
- Testing: [test approach]

## Dependencies
- External: [packages, services]
- Internal: [modules this touches]

## Blast Radius
[What files/components this change affects]
- Direct: [files we modify]
- Indirect: [files that import from modified files]
- Transitive: [N files deep]
```

### DECISIONS.md

```markdown
# Architectural Decisions

## Decision 1: [Topic]

**Choice:** [What we're doing]

**Rationale:** [Why this approach]

**Alternatives Considered:**
- Option A: [pros/cons]
- Option B: [pros/cons]

**Consequences:**
- [Trade-off accepted]
- [Future implication]

---

## Decision 2: [Topic]
[Same format]
```

### CONCERNS.md

```markdown
# Concerns & Gotchas

## Conflicts
- [Conflict with existing code]
- [Breaking change risk]

## Hidden Complexity
- [Challenge that's not obvious]
- [Edge case to handle]

## Assumptions
- [Assumption 1] - VALIDATED / NEEDS_SPIKE / ASK_USER
- [Assumption 2] - Status

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk 1] | High | [How we handle it] |
| [Risk 2] | Medium | [How we handle it] |
```

---

## manifest.json Schema

Machine-readable execution config created by formalization:

```json
{
  "name": "feature-name",
  "project": "project-name",
  "work_dir": "/path/to/project",
  "spec_dir": ".claude/specs/feature-abc123",
  "created": "2025-12-05",

  "complexity": 7,
  "risk_level": "medium",

  "execution": {
    "mode": "standard",
    "parallel_components": false,
    "reviewers": 4,
    "require_tests": true,
    "voting_gates": ["impact", "production_ready"]
  },

  "components": [
    {
      "id": "parser",
      "file": "path/to/parser.py",
      "depends_on": [],
      "complexity": "medium",
      "purpose": "Parse input data",
      "context_file": "components/parser.md"
    },
    {
      "id": "validator",
      "file": "path/to/validator.py",
      "depends_on": ["parser"],
      "complexity": "high",
      "purpose": "Validate against schema",
      "context_file": "components/validator.md"
    }
  ],

  "quality": {
    "coverage_target": 95,
    "lint_required": true,
    "security_scan": false
  },

  "gotchas": [
    "MongoDB aggregation has 16MB limit",
    "Existing callers in endpoints.py"
  ],

  "validation_command": "python -m pytest tests/"
}
```

### Required Fields
- `name`, `project`, `work_dir`
- `components` (at least one)
- Each component needs: `id`, `file`, `depends_on`

### Validation Rules
- All `depends_on` entries must reference existing component IDs
- No circular dependencies
- Risk level should match complexity/reviewer count

---

## SPEC.md (Human-Readable)

Reference document for humans, generated alongside manifest:

```markdown
# [Feature Name]

## Problem Statement
[What problem we're solving]

## Mission
[Single sentence goal]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Approach
[High-level strategy from DECISIONS.md]

## Components

| ID | File | Purpose | Complexity |
|----|------|---------|------------|
| parser | parser.py | Parse input | Medium |
| validator | validator.py | Validate schema | High |

## Dependencies
```
parser (no deps)
  └── validator
```

## Known Gotchas
- [From CONCERNS.md]

## Quality Requirements
- Coverage: 95%
- Reviewers: 4
- Security scan: No
```

---

## Component Context Template

Per-component context in `components/<id>.md`:

```markdown
# Component: <id>

## Status
NOT_STARTED | SKELETON | IMPLEMENTING | VALIDATING | COMPLETE

## Purpose
[From manifest]

## What's Been Done
- [timestamp] Created skeleton
- [timestamp] Implemented core logic

## Discoveries
- [timestamp] Found edge case with null values
- [timestamp] Existing callers use old signature

## For Next Agent
[Instructions for whoever works on this next]
```

---

## CONTEXT.md (Global)

Accumulated context across all components:

```markdown
# Execution Context

## Current State
Status: IN_PROGRESS
Components: 3/10 complete
Last updated: 2025-12-05

## Critical Discoveries
- [timestamp] MongoDB 16MB limit affects bulk operations
- [timestamp] Need to update test fixtures

## Blockers
- [Blocker if any]

## For Next Agent
[Global instructions]
```

---

## Naming Conventions

| Artifact | Location | Format |
|----------|----------|--------|
| Spec directory | `.claude/specs/<name>-<hash>/` | Unique hash suffix |
| Manifest | `manifest.json` | Machine-readable |
| Human spec | `SPEC.md` | Reference doc |
| Brainstorm | `brainstorm/*.md` | Discovery artifacts |
| Component context | `components/<id>.md` | Per-component |
| Global context | `CONTEXT.md` | Accumulated state |
| Execution state | `STATE.json` | Phase/component status |

---

## Dependency Graph Rules

1. **IDs must be unique** - Each component has a distinct ID
2. **Dependencies reference IDs** - Not file paths
3. **No cycles** - Detected by validator, fails immediately
4. **Order matters** - Topological sort determines execution order
5. **Declare all deps** - Missing dependency = wrong order
