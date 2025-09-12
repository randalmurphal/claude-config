# Symphony Orchestration System Guide

## Overview

The Symphony orchestration system manages complex development tasks through intelligent delegation and progressive refinement. It uses a **merge-purge-continue pattern** to handle architectural discoveries without interrupting work.

## Directory Structure

```
{project}/
├── .symphony/                    # Orchestration infrastructure
│   ├── tools/
│   │   └── orchestration.py      # Main orchestration tool
│   ├── chambers/                 # Worker chambers (git worktrees)
│   │   ├── auth-impl/
│   │   │   └── .chamber/         # Chamber-specific context
│   │   └── db-impl/
│   │       └── .chamber/
│   ├── MISSION_CONTEXT.json      # Evolving task understanding
│   ├── DEVIATIONS.json           # Architectural mismatches found
│   ├── BUSINESS_LOGIC.json       # Extracted business rules
│   └── MERGE_PLAN.json           # Merge/purge decisions
└── .claude/                      # User's Claude settings (separate)
```

## Key Concepts

### 1. Living Mission Context
The mission evolves as we learn, rather than staying static:
- `original_request`: Preserved for reference
- `current_understanding`: Updated as requirements clarify
- `discovered_requirements`: New requirements found during work

### 2. Deviation Handling Protocol

When agents discover architectural mismatches, they handle by severity:

**🟢 Level 1 - Minor Deviation**
- Example: Sync in skeleton, but async is better
- Action: Implement the better way
- Mark: `# DEVIATION_MINOR: [explanation]`
- Continue normally

**🟡 Level 2 - Major Deviation**
- Example: REST expected but GraphQL needed
- Action: Create minimal stub + document
- Mark: `# ARCHITECTURAL_MISMATCH: [details]`
- Skip related components

**🔴 Level 3 - Fundamental Break**
- Example: Entire approach won't work
- Action: Interface stubs only + extensive docs
- Mark: `# FUNDAMENTAL_BREAK: [explanation]`
- Switch to exploration mode

### 3. Merge-Purge-Continue Pattern

Instead of stopping work on discoveries, we:
1. **Complete** - Let all agents finish
2. **Review** - Orchestrator evaluates deviations
3. **Decide** - Make architectural decisions
4. **Merge** - Keep code aligning with decisions
5. **Purge** - Remove incompatible code
6. **Continue** - Resume from clean state

## Phase 4: Implementation (Detailed)

### Cycle 1: Initial Implementation (2 hours)

**Setup:**
```bash
python .symphony/tools/orchestration.py setup-chambers \
  --workers '[{"id": "auth-impl", "module": "auth", "scope": "src/auth/**"}]'
```

**Agent Instructions:**
```
=== YOUR TASK ===
Implement [module] following skeleton

=== DEVIATION PROTOCOL ===
If skeleton doesn't match reality:
- Minor: Implement better way, mark deviation
- Major: Create stub, document, continue elsewhere
- Fundamental: Interfaces only, document extensively

=== ALWAYS INCLUDE IN DEVIATIONS ===
- What was expected
- What was discovered
- What you did instead
- Why this approach
- Integration impact
```

### Cycle 2: Merge & Purge (1 hour)

**Orchestrator Reviews:**
```bash
python .symphony/tools/orchestration.py get-deviations
```

**Make Decisions:**
- Convert all to async?
- Use GraphQL or REST?
- Keep which patterns?

**Execute Merge:**
Launch merge-purge-coordinator agent:
```
Review all code and:
1. PRESERVE code matching decisions
2. ADAPT good patterns needing adjustment
3. PURGE code based on wrong assumptions
4. DOCUMENT what was removed and why
```

### Cycle 3: Refinement (1 hour)

**Redistribute Clean Code:**
```bash
python .symphony/tools/orchestration.py setup-chambers \
  --workers '[...]' --clean-state
```

Agents work from merged, clean state with:
- Architectural consistency
- Clear patterns to follow
- No confusion about approach

## Context Flow

### What Each Phase Outputs for Next

**Phase 1 → 2**: Key interfaces, module responsibilities, business rules
**Phase 2 → 3**: Entry points, key behaviors, mock points
**Phase 3 → 4**: Test coverage plan, known tricky areas
**Phase 4 → 5**: Actual behaviors, edge cases found
**Phase 5 → 6**: Validated behaviors, coverage achieved

### Context Importance Levels

Every agent receives context marked as:
- **MUST READ (CRITICAL)**: Essential for the task
- **SHOULD KNOW (CONTEXT)**: Helpful awareness
- **REFERENCE IF NEEDED**: Available but optional

## Key Commands

### Recording Deviations
```bash
python .symphony/tools/orchestration.py record-deviation \
  --agent "auth-impl" \
  --module "auth" \
  --severity major \
  --expected "REST API" \
  --discovered "GraphQL needed" \
  --action "Created GraphQL stub" \
  --reasoning "Complex nested queries required" \
  --impact "All API modules affected"
```

### Getting Deviations
```bash
python .symphony/tools/orchestration.py get-deviations
```

### Task Cleanup
```bash
python .symphony/tools/orchestration.py cleanup-task [--no-archive]
```
Preserves: GOTCHAS.md, CLAUDE.md, MODULE_CACHE.json, FAILURE_ANALYSIS.json
Archives: BUSINESS_LOGIC.json, INTEGRATION_PLAN.json
Purges: Task-specific files

## Principles

1. **No Interruptions**: Let agents complete their work
2. **Progressive Refinement**: Each cycle improves the codebase
3. **Preserve Good Code**: Don't throw away working patterns
4. **Clear Decisions**: Orchestrator makes architectural calls
5. **Continuous Integration**: Merge frequently, resolve conflicts early

## Benefits Over Stop/Restart

- **Efficiency**: No redundant work
- **Learning**: Each cycle incorporates discoveries
- **Morale**: Agents complete tasks (satisfaction)
- **Quality**: Good code preserved, bad code purged
- **Speed**: Parallel work continues uninterrupted

## Troubleshooting

### When to Use Each Severity

**Minor**: Implementation detail differences
**Major**: Architectural pattern changes
**Fundamental**: Entire approach invalid

### Common Issues

**Too many deviations**: Skeleton may be incomplete
**Merge conflicts**: Boundaries not clear enough
**Repeated discoveries**: Not sharing context properly

## Summary

The Symphony system orchestrates development through:
1. Clear mission that evolves
2. Deviation tracking without interruption
3. Merge-purge-continue cycles
4. Progressive refinement
5. Preserved learning

This enables efficient parallel development with architectural flexibility.