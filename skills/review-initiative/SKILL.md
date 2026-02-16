---
name: review-initiative
description: Use after /breakdown-work or manual initiative creation, before running tasks. Use when initiative has 5+ tasks, multiple dependencies, or references a design document.
---

# Initiative Review

## Overview

Validate and fix initiative tasks before execution using specialized auditor subagents.

**Core principle:** Each task executes in complete isolation. If an agent can't succeed with only the task description, initiative context, and design doc — the task will fail.

**Announce at start:** "Running initiative review with 3 parallel auditors..."

## The Process

### Step 1: Gather Context

```bash
orc initiative show INIT-XXX
```

Extract:
- Initiative ID
- Design doc path (from vision/description)
- Task count and dependency structure

### Step 2: Invoke Auditor Subagents

Launch these three auditors **in parallel** using Task tool:

| Auditor | Purpose | Returns |
|---------|---------|---------|
| `coverage-auditor` | Design doc → task mapping | Gaps, orphans, scope creep |
| `dependency-auditor` | Blocked_by correctness | Missing deps, over-constraints, cross-initiative issues |
| `description-auditor` | Task description quality | Improvements needed per task |

Each auditor is defined in `.claude/agents/` and knows its output format.

**Prompt template for each:**
```
Audit INIT-{ID} for {coverage/dependencies/description quality}.
Design doc: {path}
Return structured findings with specific fix recommendations.
```

### Step 3: Consolidate Findings

After auditors complete, synthesize into action plan:

```markdown
## Critical Issues (Block Execution)
| Issue | Impact | Fix |
|-------|--------|-----|

## Should Fix (Quality)
| Issue | Tasks | Improvement |
|-------|-------|-------------|

## Action Items
1. [ ] Create missing tasks
2. [ ] Add/remove dependencies
3. [ ] Update task descriptions
```

### Step 4: Execute Fixes

**With user approval**, execute the fixes. The mechanics depend on what's broken:

#### Creating Missing Tasks
```bash
orc new "Title" -w medium -c feature -i INIT-XXX -d "Description..."
```

Look at existing tasks in the initiative for description patterns. Match the style.

#### Fixing Dependencies
```bash
# Add missing dependency
orc edit TASK-X --add-blocker TASK-Y

# Remove unnecessary dependency
orc edit TASK-X --remove-blocker TASK-Y

# Cross-initiative dependency
orc edit TASK-X --add-blocker TASK-Y  # Y from other initiative
```

#### Updating Descriptions
```bash
orc edit TASK-X -d "Updated description..."
```

When updating descriptions, preserve what's good and add what's missing:
- Keep existing design doc references
- Add file paths if missing
- Add acceptance criteria if missing
- Add scope boundaries if missing

### Step 5: Re-Run Auditors

After fixes, re-run the auditors to verify. Continue until:
- Coverage: No gaps, no orphans
- Dependencies: No missing, no over-constraints
- Descriptions: All tasks rated "Good"

## Flexibility Notes

Projects differ. The auditors return **what's wrong** and **recommendations**, but:

- **File paths**: Auditors suggest paths based on project structure they observe
- **Description style**: Match existing task descriptions in the initiative
- **Dependency logic**: Use the "would tests fail?" test, not intuition
- **Fix commands**: Use `orc edit --help` and `orc new --help` for current flags

The skill teaches the process. The auditors analyze the specific project. You execute fixes appropriate to the context.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `orc initiative show INIT-X` | View all tasks and deps |
| `orc show TASK-X` | View task details |
| `orc edit TASK-X --add-blocker TASK-Y` | Add dependency |
| `orc edit TASK-X --remove-blocker TASK-Y` | Remove dependency |
| `orc edit TASK-X -d "..."` | Update description |
| `orc new "Title" -i INIT-X ...` | Create task in initiative |
| `orc initiative link INIT-X TASK-Y` | Link existing task |

## Red Flags (Stop and Fix)

- Cross-initiative dependency mentioned but not set
- 10+ tasks with zero dependencies (suspicious)
- Task says "see design doc" without path
- Large task touching 2 files (wrong weight)
- Circular dependencies
- Task says "deprecate" or "either X or Y" (hedging - pick one)
- Design says "replace X" but task doesn't say DELETE X
- Major decision left to executing agent ("choose between...")
