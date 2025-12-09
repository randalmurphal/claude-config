---
name: spec-formats
description: Templates for brainstorm artifacts and manifest.json. Load when using /spec.
---

# Spec Formats

## Spec Storage

Specs live in the **project's** `.claude/specs/` directory (not ~/.claude):

```
<project>/                    # e.g., m32rimm/
└── .claude/
    └── specs/
        └── <name>-<hash>/
            ├── manifest.json          # Execution config (machine-readable)
            ├── SPEC.md                # Human-readable spec
            ├── brainstorm/            # From /spec phase
            │   ├── MISSION.md
            │   ├── INVESTIGATION.md
            │   ├── DECISIONS.md
            │   └── CONCERNS.md
            └── components/            # Per-component context
```

**Workflow:**
1. `/spec` - Create spec (brainstorm → formalize → manifest.json)
2. `cd ~/.claude && python3 -m cc_orchestrations run --spec <name>` - Execute spec

**Utility:**
- `ls .claude/specs/` - List specs

---

## manifest.json Schema (Full)

Machine-readable execution config created by formalization:

```json
{
  "name": "feature-name",
  "project": "project-name",
  "work_dir": "/path/to/project",
  "spec_dir": ".claude/specs/feature-abc123",
  "created": "2025-12-08",

  "complexity": 7,
  "risk_level": "medium",
  "risk_score": 9,

  "execution": {
    "mode": "standard",
    "reviewers": 4,
    "require_tests": true,
    "voting_gates": ["fix_strategy", "production_ready"]
  },

  "components": [
    {
      "id": "parser",
      "file": "path/to/parser.py",
      "depends_on": [],
      "complexity": "medium",
      "purpose": "Parse input data",
      "parallel_group": 1
    },
    {
      "id": "validator",
      "file": "path/to/validator.py",
      "depends_on": ["parser"],
      "complexity": "high",
      "purpose": "Validate against schema",
      "parallel_group": 2
    }
  ],

  "parallelization": {
    "skeleton_parallel": true,
    "implementation_parallel": true,
    "validation_parallel": false,
    "parallel_groups": [
      {
        "group": 1,
        "components": ["parser", "config"],
        "reason": "No dependencies between them"
      },
      {
        "group": 2,
        "components": ["validator"],
        "reason": "Depends on group 1"
      }
    ]
  },

  "agents": {
    "skeleton": "skeleton-builder",
    "implementation": "implementation-executor",
    "test_skeleton": "test-skeleton-builder",
    "test_implementation": "test-implementer",
    "validators": ["code-reviewer"],
    "project_validators": []
  },

  "project_config": {
    "extends": "m32rimm",
    "validators": ["mongo_validator", "import_validator", "general_validator"],
    "finding_validator": true,
    "validator_triggers": {
      "mongo_validator": "file uses: db., pymongo, DBOpsHelper, retry_run, businessObjects",
      "import_validator": "file in: imports/, or uses: data_importer"
    }
  },

  "quality": {
    "coverage_target": 95,
    "lint_required": true,
    "lint_command": "python-code-quality --fix",
    "security_scan": false
  },

  "gotchas": [
    "MongoDB aggregation has 16MB limit",
    "Must call flush() before mark_for_aggregation()"
  ],

  "validation_command": "python -m pytest tests/"
}
```

---

## Parallelization Rules

### How to Determine Parallel Groups

1. **Group 0**: Components with NO dependencies (can all run in parallel)
2. **Group N**: Components that depend ONLY on completed groups < N
3. **Same group = parallel, different group = sequential**

```
Example:
  A (no deps)     → Group 0
  B (no deps)     → Group 0   ← A and B run in PARALLEL
  C (depends A)   → Group 1
  D (depends B)   → Group 1   ← C and D run in PARALLEL (after A,B complete)
  E (depends C,D) → Group 2   ← E runs after C,D complete
```

### Parallel Safety Rules

1. **Never parallelize components that write to the same file**
2. **Tests can parallelize if they don't share fixtures**
3. **skeleton + test-skeleton can ALWAYS parallelize (different files)**
4. **implementation + test-implementation can parallelize if isolated**

### Parallelization Config Options

```json
{
  "parallelization": {
    "skeleton_parallel": true,       // skeleton-builder + test-skeleton-builder
    "implementation_parallel": true, // implementation-executor + test-implementer
    "validation_parallel": false,    // Multiple validators (be careful with edits)
    "max_concurrent": 4              // Max parallel agents
  }
}
```

---

## Project-Specific Agent Configuration

### For m32rimm Projects

When working in m32rimm, include in manifest:

```json
{
  "project_config": {
    "extends": "m32rimm",
    "validators": [
      "mongo_validator",
      "import_validator",
      "general_validator"
    ],
    "finding_validator": true,
    "validator_triggers": {
      "mongo_validator": "file uses: db., pymongo, DBOpsHelper, retry_run, businessObjects",
      "import_validator": "file in: imports/, or uses: data_importer, insert_data_importer",
      "bo_structure_validator": "file creates: BO, or uses: upsert_bo, BOUpsert"
    },
    "agents_dir": ".claude/agents/"
  }
}
```

### Available m32rimm Validators

| Validator | Purpose | Trigger |
|-----------|---------|---------|
| `mongo_validator` | flush(), subID, retry_run | Any MongoDB operation |
| `import_validator` | data_importer patterns | Files in imports/ |
| `general_validator` | Logging, try/except, types | All code |
| `finding_validator` | False positive filter | All findings |
| `bo_structure_validator` | BO field validation | BO creation |
| `schema_alignment_validator` | MongoDB schema | Collection operations |

### Agent Override in Components

```json
{
  "components": [
    {
      "id": "complex_import",
      "file": "imports/scanner/handler.py",
      "agents": {
        "implementation": "implementation-executor",
        "validators": ["mongo_validator", "import_validator", "general_validator"]
      }
    }
  ]
}
```

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

## Non-Goals
- Thing we're explicitly NOT doing

## Constraints
- Hard requirement
```

### INVESTIGATION.md

```markdown
# Investigation Findings

## Project Structure
[Tech stack, directory layout]

## Existing Patterns
- Auth: [how auth works]
- APIs: [API patterns]
- Testing: [test approach]

## Dependencies
- External: [packages]
- Internal: [modules this touches]

## Blast Radius
- Direct: [files we modify]
- Indirect: [files that import modified files]
- Transitive: [N files deep]
```

### DECISIONS.md

```markdown
# Architectural Decisions

## Decision 1: [Topic]

**Choice:** [What we're doing]
**Rationale:** [Why]
**Alternatives:** [What else we considered]
**Consequences:** [Trade-offs]

## Parallelization Decision

**Parallel Groups:**
- Group 0: [components] - no dependencies
- Group 1: [components] - depends on group 0

**Rationale:** [Why this grouping]

## Agent Selection

**Project validators needed:**
- [validator]: [because X uses Y]

**Model overrides:**
- [component]: opus (complex judgment needed)
```

### CONCERNS.md

```markdown
# Concerns & Gotchas

## Conflicts
- [Conflict with existing code]

## Hidden Complexity
- [Challenge that's not obvious]

## m32rimm-Specific Concerns
- [ ] DBOpsHelper flush() before aggregation
- [ ] subID filter on businessObjects queries
- [ ] retry_run on all mongo operations

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk] | High | [Mitigation] |
```

---

## Formalization Checklist

Before converting brainstorm to manifest, verify:

### Parallelization
- [ ] Components grouped by dependency level
- [ ] No conflicts in parallel groups
- [ ] skeleton/test parallel where possible
- [ ] implementation/test parallel where safe

### Agent Config
- [ ] Project-specific validators identified
- [ ] Validator triggers defined
- [ ] Model overrides for complex components

### Risk Assessment
- [ ] Risk score calculated (5-15)
- [ ] Reviewer count matches risk level
- [ ] Voting gates appropriate for risk

### Quality
- [ ] Coverage target set
- [ ] Lint command specified
- [ ] Test command specified

---

## SPEC.md Generation

After formalization, generate human-readable SPEC.md:

```markdown
# [Feature Name]

## Mission
[From MISSION.md]

## Components

| ID | File | Group | Validators |
|----|------|-------|------------|
| parser | parser.py | 0 | general |
| validator | validator.py | 1 | general, mongo |

## Execution Plan

```
Group 0 (parallel): parser, config
       ↓
Group 1 (parallel): validator, transformer
       ↓
Group 2: aggregator (depends on all)
```

## Validators Active
- mongo_validator (files use MongoDB)
- import_validator (files in imports/)
- general_validator (all files)
- finding_validator (filter false positives)

## Risk Assessment
- Score: 9/15 (Medium)
- Reviewers: 4
- Voting gates: fix_strategy, production_ready

## Gotchas
[From CONCERNS.md]
```

---

## Dependency Rules

1. **IDs must be unique**
2. **Dependencies reference IDs, not file paths**
3. **No cycles** - Validator fails immediately
4. **Parallel group derived from deps** - Don't manually assign wrong group
5. **Components in same group MUST NOT conflict**
