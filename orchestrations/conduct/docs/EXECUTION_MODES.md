# Conduct Execution Modes

Three modes optimized for different task complexity and risk levels.

---

## Mode Overview

| Mode | Use Case | Validation | Can Backtrack | Parallelization |
|------|----------|------------|---------------|-----------------|
| **QUICK** | Simple, isolated changes | End only | No | Aggressive |
| **STANDARD** | Moderate complexity, some risk | After components | Limited | Balanced |
| **FULL** | Large refactors, high risk | After every step | Yes | Conservative |

---

## Mode 1: QUICK

**Use when:**
- Small feature addition (1-3 files)
- Well-understood scope
- Isolated code (low blast radius)
- Low risk of breaking existing functionality

### Flow

```
SPEC.md
   │
   ▼
┌──────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION PHASE                       │
│                                                              │
│  Parallel execution of ALL components:                       │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                  │
│  │ Component │ │ Component │ │ Component │                  │
│  │  A + B    │ │     C     │ │   D + E   │                  │
│  │ (skeleton │ │ (skeleton │ │ (skeleton │                  │
│  │  + impl)  │ │  + impl)  │ │  + impl)  │                  │
│  └───────────┘ └───────────┘ └───────────┘                  │
│        │             │             │                         │
│        └─────────────┴─────────────┘                         │
│                      │                                       │
│              Simple lint check                               │
│              (python-code-quality)                           │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    FINAL REVIEW PHASE                         │
│                                                              │
│  Full review with all validators (parallel):                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │ general │ │  mongo  │ │ import  │ │ finding │            │
│  │validator│ │validator│ │validator│ │validator│            │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
│                      │                                       │
│                Fix loop (max 3)                              │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
                   COMPLETE
```

### Configuration

```json
{
  "mode": "quick",
  "validation": {
    "after_skeleton": false,
    "after_implementation": "lint_only",
    "final_review": true
  },
  "parallelization": "aggressive",
  "backtrack": false,
  "fix_attempts": 3
}
```

---

## Mode 2: STANDARD

**Use when:**
- Medium feature (3-10 files)
- Cross-cutting concerns
- Moderate complexity
- Some shared code touched

### Flow

```
SPEC.md
   │
   ▼
┌──────────────────────────────────────────────────────────────┐
│                    SKELETON PHASE                             │
│                                                              │
│  Parallel by dependency level:                               │
│                                                              │
│  Level 0 (no deps):   [A] [B] [C]  ─── parallel             │
│                          │                                   │
│  Level 1 (deps on 0): [D depends A] [E depends B] ─ parallel │
│                          │                                   │
│  Level 2 (deps on 1): [F depends D,E] ─── sequential         │
│                                                              │
│  Quick structure review (2 validators)                       │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                 IMPLEMENTATION PHASE                          │
│                                                              │
│  Same dependency-ordered execution                           │
│                                                              │
│  After each level:                                           │
│  • Lint check                                                │
│  • 2 validators (quick review)                               │
│  • Fix any critical/high issues                              │
│                                                              │
│  After all components:                                       │
│  • Integration test run                                      │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    FINAL REVIEW PHASE                         │
│                                                              │
│  Full review with all validators:                            │
│  • Domain validators (mongo, import, general)                │
│  • Finding validator (challenges all)                        │
│  • Fix loop with severity tracking                           │
│  • Test suite run                                            │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
                   COMPLETE
```

### Configuration

```json
{
  "mode": "standard",
  "validation": {
    "after_skeleton": "quick_review",
    "after_implementation": "level_review",
    "final_review": true
  },
  "parallelization": "by_dependency_level",
  "backtrack": "on_critical_only",
  "fix_attempts": 3
}
```

---

## Mode 3: FULL

**Use when:**
- Large refactor (10+ files)
- Structural changes
- High-risk modifications
- Widespread impact
- Complex state management

### Flow

```
SPEC.md
   │
   ▼
┌──────────────────────────────────────────────────────────────┐
│                 ARCHITECTURE REVIEW                           │
│                                                              │
│  Before any code:                                            │
│  • 3 architecture reviewers analyze spec                     │
│  • Vote on approach if multiple options                      │
│  • Identify potential issues early                           │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Can MODIFY SPEC based on findings                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    SKELETON PHASE                             │
│                                                              │
│  Sequential by component (conservative):                     │
│                                                              │
│  For each component:                                         │
│  1. Create skeleton                                          │
│  2. 2 reviewers check structure                              │
│  3. Check against spec alignment                             │
│                                                              │
│  After ALL skeletons:                                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ SKELETON REVIEW GATE                                    │ │
│  │                                                         │ │
│  │ 3 reviewers evaluate full skeleton:                     │ │
│  │ • Does structure make sense?                            │ │
│  │ • Any design issues visible now?                        │ │
│  │ • Should we rethink anything?                           │ │
│  │                                                         │ │
│  │ Votes: PROCEED / REVISE_SKELETON / REVISE_SPEC          │ │
│  │                                                         │ │
│  │ If REVISE: Go back and redo                             │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                 IMPLEMENTATION PHASE                          │
│                                                              │
│  Sequential by component:                                    │
│                                                              │
│  For each component:                                         │
│  1. Implement                                                │
│  2. Full validation (all relevant validators)                │
│  3. Fix loop until clean                                     │
│  4. Mark complete                                            │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ BACKTRACK ALLOWED                                       │ │
│  │                                                         │ │
│  │ If implementation reveals skeleton issue:               │ │
│  │ • Can go back and modify skeleton                       │ │
│  │ • Can propagate changes to dependent components         │ │
│  │ • State tracks what needs re-validation                 │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                 INTEGRATION PHASE                             │
│                                                              │
│  • Run full test suite                                       │
│  • Cross-component review                                    │
│  • Check for interaction issues                              │
│  • Verify no regressions                                     │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    FINAL REVIEW PHASE                         │
│                                                              │
│  FULL REVIEW (everything, including style):                  │
│                                                              │
│  Stage 1: Domain validators (parallel)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │ general │ │  mongo  │ │ import  │ │security │            │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
│                                                              │
│  Stage 2: Finding validator (Opus) - challenges all          │
│                                                              │
│  Stage 3: Style/completeness review                          │
│  • All style issues (not just critical)                      │
│  • Documentation completeness                                │
│  • Test coverage adequacy                                    │
│                                                              │
│  Fix ALL issues (critical through minor)                     │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                 PRODUCTION GATE                               │
│                                                              │
│  3 reviewers vote: READY / NEEDS_WORK / RISKY                │
│  2/3 consensus required                                       │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
                   COMPLETE
```

### Configuration

```json
{
  "mode": "full",
  "validation": {
    "after_skeleton": "full_review",
    "skeleton_gate": true,
    "after_implementation": "full_review",
    "final_review": true,
    "fix_all_severities": true
  },
  "parallelization": "conservative",
  "backtrack": true,
  "fix_attempts": 5,
  "production_gate": true
}
```

---

## Parallelization Strategies

### Aggressive (QUICK mode)

```
All independent components run simultaneously.
Dependencies resolved at runtime.

Example with 5 components (A→B, C→D, E independent):

Time 0: [A] [C] [E] start
Time 1: [A done] [B starts] [C done] [D starts] [E done]
Time 2: [B done] [D done]

Total: 2 time units instead of 5
```

### By Dependency Level (STANDARD mode)

```
Components grouped by dependency depth.
Each level completes before next starts.

Example:
Level 0 (no deps):    [A] [C] [E]  ─── all parallel
Level 1:              [B] [D]      ─── parallel after level 0
Level 2:              [F]          ─── after level 1

Validation runs after each level completes.
```

### Conservative (FULL mode)

```
One component at a time.
Full validation between each.

Example:
[A] → validate → [B] → validate → [C] → validate → ...

Slowest but catches issues before they compound.
Backtracking allowed at any point.
```

---

## Mode Selection Guide

| Factor | QUICK | STANDARD | FULL |
|--------|-------|----------|------|
| Files changed | 1-3 | 3-10 | 10+ |
| Shared code touched | No | Some | Yes |
| Breaking changes | No | Maybe | Likely |
| Test coverage | Good | Moderate | Any |
| Risk tolerance | High | Medium | Low |
| Time available | Low | Medium | High |
| Refactor scope | None | Limited | Extensive |

**When in doubt, go one level higher.** Over-validation costs time; under-validation costs production bugs.

---

## Scope Discipline

**ALL MODES enforce scope discipline:**

```
┌─────────────────────────────────────────────────────────────┐
│                      SCOPE RULES                            │
│                                                             │
│  DO:                                                        │
│  • Implement exactly what spec requires                     │
│  • Fix issues in files being modified                       │
│  • Add tests for new functionality                          │
│                                                             │
│  DON'T:                                                     │
│  • Refactor unrelated code                                  │
│  • Add "improvements" not in spec                           │
│  • Fix pre-existing issues in untouched files               │
│  • Change APIs beyond what's needed                         │
│                                                             │
│  FLAG BUT DON'T FIX:                                        │
│  • Pre-existing issues discovered during review             │
│  • Out-of-scope improvements that would be nice             │
│  • Technical debt in related code                           │
│                                                             │
│  → These go to DISCOVERIES.md for future tickets            │
└─────────────────────────────────────────────────────────────┘
```
