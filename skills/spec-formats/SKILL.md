---
name: spec-formats
description: Templates and structures for SPEC.md, BUILD specs, component specs, and .spec/ directory organization. Load when using /spec or /conduct.
---

# Spec Formats

## Directory Structure

```
$WORK_DIR/.spec/
├── SPEC.md                    # High-level architecture (from /spec)
├── SPEC_1_component.md        # Component phase specs (for /conduct)
├── SPEC_2_component.md
├── BUILD_taskname.md          # Minimal spec (for /solo)
├── DISCOVERIES.md             # Learnings during execution
├── PROGRESS.md                # Execution tracking
└── archive/                   # Completed artifacts
```

---

## SPEC.md Template (Full Orchestration)

Created by `/spec`, consumed by `/conduct`.

```markdown
# [Feature Name]

## Problem Statement
[1-2 paragraphs: What problem are we solving? Why now?]

## User Impact
[Who benefits? How? What changes for them?]

## Mission
[Single sentence: What we're building]

## Success Criteria
- [ ] Measurable outcome 1
- [ ] Measurable outcome 2
- [ ] Performance target (if applicable)

## Requirements (IMMUTABLE)
### Must Have
- Requirement 1
- Requirement 2

### Must Not
- Anti-requirement 1

## Proposed Approach (EVOLVABLE)
[High-level strategy - can be refined during implementation]

### Architecture Decision
**Decision:** [Chosen approach]
**Context:** [Why decision was needed]
**Alternatives:** [What else was considered]
**Consequences:** [Trade-offs accepted]

## Files to Create/Modify

### New Files
- `path/to/file.py`
  - Purpose: [What it does]
  - Depends on: [Other files] ← CRITICAL for dependency graph
  - Complexity: Low|Medium|High

### Modified Files
- `path/to/existing.py`
  - Changes: [What's changing]
  - Risk: Low|Medium|High

## Implementation Phases
### Phase 1: [Name]
- Task 1
- Task 2

### Phase 2: [Name]
- Task 3
- Task 4

## Known Gotchas
- [Gotcha 1 from investigation/spikes]
- [Gotcha 2]

## Quality Requirements
- Coverage: 95%+ for new code
- Review: [Risk-based from orchestration-standards]
- Security: [If applicable]

## Testing Strategy (Optional)
### Unit Tests
- [What to test]

### Integration Tests
- [Scenarios]
```

---

## BUILD Spec Template (Streamlined)

Created internally by `/solo` for simpler tasks.

```markdown
# [Task Name]

## Goal
[Clear outcome - what to build]

## Problem
[1-2 sentences - what gap we're filling]

## Approach
[Basic strategy]

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Files
### New
- `path/file.py`: [purpose]

### Modified
- `path/existing.py`: [changes]

## Quality
- Linting: Pass python-code-quality
- Tests: [If requested]

## Context
[Important constraints or notes]
```

---

## Component Spec Template

Created by `/spec` or `/conduct` for each component in dependency order.

```markdown
# Phase [N]: [Component Name]

## Component
- `path/to/file.py`
  - Purpose: [from SPEC.md]
  - Complexity: [from SPEC.md]

## Dependencies
[What this component needs from previous phases]

## Available from Previous Phases
[Populated as phases complete - APIs, types, utilities]

## Success Criteria
- [ ] Compiles without errors
- [ ] Tests pass (95%+ coverage)
- [ ] Validation clean

## Known Gotchas
[From SPEC.md + discoveries during earlier phases]

## Implementation Notes
[Specific approach for this component]
```

---

## DISCOVERIES.md Template

Running log of learnings during execution.

```markdown
# Discoveries

## [Date]: [Topic]
**Status:** INVESTIGATING | RESOLVED | OBSOLETE

### Findings
- Key point 1
- Key point 2

### Gotchas
- Issue discovered
- Workaround/solution

### Impact
[How this affects other components/future work]

---
[Repeat for each discovery]
```

**Maintenance:**
- Keep under 50 lines
- Archive OBSOLETE entries
- Promote RESOLVED to permanent docs

---

## PROGRESS.md Template

Execution tracking for orchestrator.

```markdown
# Progress: [Project/Task Name]

## Status
**Phase:** [Current phase]
**Started:** [timestamp]
**Components:** X / Y complete

## Component Status

### [Component 1]
- Status: NOT_STARTED | SKELETON | IMPLEMENTING | VALIDATING | COMPLETE
- Tasks: X / Y
- Issues: [Any blockers]

### [Component 2]
...

## Blockers
[Current blockers with resolution status]

## Recent Activity
- [timestamp]: [what happened]

---
Last Updated: [timestamp]
```

---

## Naming Conventions

| Artifact | Pattern | Example |
|----------|---------|---------|
| Full spec | `SPEC.md` | `SPEC.md` |
| Component spec | `SPEC_N_name.md` | `SPEC_1_auth.md` |
| Build spec | `BUILD_taskname.md` | `BUILD_rate-limit.md` |
| Discoveries | `DISCOVERIES.md` | `DISCOVERIES.md` |
| Progress | `PROGRESS.md` | `PROGRESS.md` |

---

## Dependency Graph Rules

The `Depends on:` field in SPEC.md is **critical**:

1. Must list all files this component imports from
2. Used to build execution order (topological sort)
3. Circular dependencies = fail immediately
4. Missing dependency = incorrect execution order

**Validation:** Before /conduct starts, verify declared dependencies match actual imports.
