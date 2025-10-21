---
name: solo
description: Streamlined task execution with proper delegation and validation - no prerequisites required
---

# /solo - Streamlined Implementation

## 🎯 FOCUSED EXECUTION

**When to use /solo:**
- Straightforward tasks with clear scope
- Single component or a few related files
- Standard patterns apply
- Quick iteration needed

**When NOT to use /solo:**
- Complex multi-component features → Use /conduct
- Architectural uncertainty → Use /spec then /conduct
- Need variant exploration → Use /conduct

**Prerequisites:** None (generates minimal spec internally)

---

## Your Mission

1. Generate minimal spec for context
2. Implement via task-by-task execution with validation
3. Full validation after all tasks complete
4. Merge .spec learnings into permanent documentation
5. [Optional] Testing if user requested
6. Cleanup .spec/
7. Deliver working, validated, documented code

**You are intelligent.** Assess if task is actually straightforward. If not, tell user to use /conduct.

**You are autonomous.** Execute without asking permission at each step.

---

## Workflow

### Step 0: Load Agent Prompting Skill

**CRITICAL: Load before spawning any sub-agents.**

```
Skill: agent-prompting
```

**This skill contains:**
- Critical inline standards for each agent type
- What to include in prompts (logging, try/except, mocking, etc.)
- Prompt templates with examples

**You will use this throughout the workflow to write effective agent prompts.**

---

### Step 0.5: Determine Working Directory

**Infer from task description which directory/component is being worked on:**
- Search for relevant files/directories mentioned in task
- Check project structure (e.g., monorepo with services/api/, services/auth/)
- If task mentions specific component/service → that's the working dir

**If unclear after search, ask:**
"Which directory should I work in? (provide path relative to repo root, or '.' for current)"

**Once determined:**
- `$WORK_DIR` = that directory
- Create `.spec/` at `$WORK_DIR/.spec/`
- All paths relative to `$WORK_DIR`

---

### Step 1: Generate Minimal Spec

**Create `.spec/BUILD_[taskname].md`:**

Use template: `~/.claude/templates/spec-minimal.md`

```markdown
# [Task Name]

## Goal
[Clear, concise outcome - what to build]

## Problem
[1-2 sentences - what gap are we filling]

## Approach
[Basic implementation strategy]

## Implementation Tasks
- Task 1: [description]
- Task 2: [description]
- Task 3: [description]

## Files
### New Files
- path/to/file.py: [purpose]
- path/to/test_file.py: [tests what]

### Modified Files
- path/to/existing.py: [what changes]

## Tests (only if user requested)
- Unit tests for all new functions/classes
- Integration test for [workflow]
- Coverage target: 95%

## Quality
- Linting: Pass ruff check + pyright
- Security: [any specific concerns or "Standard practices"]
- Performance: [any specific requirements or "No specific requirements"]

## Context & Constraints
[Any important context the main agent and sub-agents need to stay on track]
- [Constraint or context 1]
- [Constraint or context 2]
```

**Naming:** Extract 2-3 words from task (e.g., "rate-limit", "user-export")

**Initialize PROGRESS.md:** Track implementation progress

**Commit changes** (follow project's commit style from recent commits)

---

### Step 2: Task-by-Task Implementation

**Read implementation tasks from BUILD_[taskname].md:**
```markdown
## Implementation Tasks
- Implement data models
- Implement validation logic
- Implement API endpoint
- Add error handling
```

**Determine if tasks can run in parallel:**
- If tasks are independent (no dependencies) → spawn implementation-executors in PARALLEL
- If tasks have dependencies → run sequentially

**For EACH task:**

```
1. Implement task:
   Task(implementation-executor, """
   Implement: {task description}

   Spec: $WORK_DIR/.spec/BUILD_[taskname].md
   Workflow: solo
   Task: {task name}

   CRITICAL STANDARDS (from agent-prompting skill):
   - Logging: import logging; LOG = logging.getLogger(__name__)
   - try/except ONLY for connection errors (network, DB, cache)
   - Type hints required, 80 char limit
   - No # noqa without documented reason
   - DO NOT run tests

   Load python-style skill.

   Read spec: $WORK_DIR/.spec/BUILD_[taskname].md
   Focus on: {task name}
   """)

2. Validate task (2 code-reviewers in PARALLEL - single message with 2 Task calls):

   Task(code-reviewer, """
   Review: {task description}

   Spec: $WORK_DIR/.spec/BUILD_[taskname].md
   Workflow: solo

   Focus: Code quality, logic correctness, standards compliance

   Load python-style skill.

   Return JSON: {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   """)

   Task(code-reviewer, """
   Review: {task description}

   Spec: $WORK_DIR/.spec/BUILD_[taskname].md
   Workflow: solo

   Focus: Edge cases, error handling, coupling

   Return JSON: {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   """)

3. Fix issues (if found):
   IF critical or important issues:
     LOOP (max 2 attempts):
       Task(fix-executor, """
       Fix task validation issues.

       Spec: $WORK_DIR/.spec/BUILD_[taskname].md
       Task: {task description}

       Issues: [paste combined JSON from 2 reviewers]

       CRITICAL RULES (from agent-prompting skill):
       - Fix PROPERLY - no workarounds
       - Follow code standards: logging.getLogger, try/except only for connections
       - Max 2 attempts, then ESCALATE

       Load python-style skill.

       Read spec: $WORK_DIR/.spec/BUILD_[taskname].md
       """)

       Re-run 2 code-reviewers in parallel (verify fixes)

       IF clean: Break
       IF attempt >= 2: ESCALATE

4. Update PROGRESS.md with task completion

5. Commit changes for this task

NEXT task...
```

**After ALL tasks complete:**

Update BUILD spec with any discoveries:
```markdown
## Implementation Notes (added after completion)
- {gotchas encountered}
- {deviations from original approach}
- {learnings}
```

**Commit changes**

---

### Step 3: Full Validation

**Goal:** Comprehensive validation of entire implementation after all tasks complete.

**Run linting + 6 reviewers in PARALLEL (single message with 7 operations):**

```bash
# Operation 1: Linting (run alongside reviewers)
ruff check $WORK_DIR && pyright $WORK_DIR
```

```
# Operations 2-7: Spawn 6 reviewers (same message as linting)

Common for all reviewers:
- Spec: $WORK_DIR/.spec/BUILD_[taskname].md
- Workflow: solo
- Return JSON: {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}

Task(security-auditor, """
Audit implementation for security vulnerabilities.

Load vulnerability-triage skill.

Review for: injection risks, auth bypasses, data exposure, crypto issues.
""")

Task(performance-optimizer, """
Review implementation for performance issues.

Load mongodb-aggregation-optimization skill if MongoDB code detected.

Review for: N+1 queries, missing indexes, inefficient algorithms, memory leaks.
""")

Task(code-reviewer, """
Review implementation: complexity, errors, clarity.

Load python-style skill.

Focus: cyclomatic complexity, error handling, code clarity, maintainability.
""")

Task(code-reviewer, """
Review implementation: responsibility, coupling, type safety.

Focus: SRP violations, tight coupling, type hint coverage, interface clarity.
""")

Task(code-beautifier, """
Review implementation: DRY violations, magic numbers, dead code.

Focus: code duplication, hardcoded values, unused imports/variables, formatting.
""")

Task(code-reviewer, """
Review implementation: documentation, comments, naming.

Focus: docstring coverage, comment quality, variable naming, function naming.
""")
```

**Combine all findings:**
- Merge linting errors + 6 reviewer responses
- Consolidate critical + important + minor
- Deduplicate issues

**Fix ALL issues (max 3 attempts):**
```
LOOP until validation clean:
  1. Spawn fix-executor:
     Task(fix-executor, """
     Fix all validation issues.

     Spec: $WORK_DIR/.spec/BUILD_[taskname].md
     Workflow: solo

     Critical: [list]
     Important: [list]
     Minor: [list]

     CRITICAL RULES (from agent-prompting skill):
     - Fix PROPERLY - no workarounds
     - NO # noqa / # type: ignore as "fixes"
     - If architectural issue: ESCALATE immediately
     - Max 3 attempts

     Load python-style skill.
     Load code-refactoring skill if complexity issues.

     Read spec: $WORK_DIR/.spec/BUILD_[taskname].md
     """)

  2. Re-run linting + 6 reviewers in PARALLEL (single message - verify fixes)

  3. IF clean: Break
     IF new issues AND attempt < 3: Continue loop
     IF attempt >= 3: ESCALATE

  4. Update PROGRESS.md with validation status
```

**Validation complete criteria:**
- ✅ Zero linting errors
- ✅ All critical issues fixed
- ✅ All important issues fixed
- ✅ All minor issues fixed (or documented why skipped)

**Commit changes**

---

### Step 4: Documentation (Merge .spec to Permanent Docs)

**Goal:** Validate all documentation and merge .spec learnings into permanent docs.

**Invoke documentation-reviewer:**

```
validation_result = Task(documentation-reviewer, """
Validate all documentation against implemented code.

Working directory: $WORK_DIR
Spec: $WORK_DIR/.spec/BUILD_[taskname].md
Workflow: solo

Implementation complete and validated. Ensure docs accurate.

Load ai-documentation skill.

Find all .md files in $WORK_DIR, validate each systematically:
- CLAUDE.md
- README.md
- docs/ directory
- .spec/BUILD_[taskname].md

Check:
- File:line references accurate
- Function signatures match code
- Code examples work
- CLAUDE.md line counts within targets
- No duplication from parent CLAUDE.md

Return JSON with issues categorized by severity.
""")
```

**Fix documentation issues (if found):**
```
IF validation_result contains CRITICAL or IMPORTANT issues:

  # Group issues by file if multiple files need fixes
  issues_by_file = group_issues_by_file(validation_result)

  # Spawn general-builder per file (PARALLEL if multiple files)
  FOR each file with issues:
    Task(general-builder, """
    Fix documentation issues in {file}.

    Working directory: $WORK_DIR
    Spec: $WORK_DIR/.spec/BUILD_[taskname].md

    Issues to fix (JSON from reviewer):
    [paste issues for this file]

    Fix priorities:
    1. All CRITICAL issues (incorrect refs, signatures, contradictions)
    2. All IMPORTANT issues (missing docs, outdated terms, line count violations)
    3. MINOR issues if time permits

    Load ai-documentation skill.

    IMPORTANT: Merge learnings from .spec/BUILD_[taskname].md into permanent docs.
    """)

  # Re-validate after fixes
  Task(documentation-reviewer, """
  Re-validate all documentation after fixes.

  Working directory: $WORK_DIR
  Spec: $WORK_DIR/.spec/BUILD_[taskname].md

  Load ai-documentation skill.

  Return JSON with remaining issues (if any).
  """)
```

**Documentation validation complete criteria:**
- ✅ All .md files reviewed
- ✅ No CRITICAL or IMPORTANT issues remaining
- ✅ .spec/BUILD_[taskname].md learnings merged into permanent docs
- ✅ File:line references accurate
- ✅ Function signatures match code
- ✅ Code examples work
- ✅ CLAUDE.md line counts within targets

**Commit changes**

---

### Step 5: [OPTIONAL] Testing

**Only run if user explicitly requested tests.**

**Check if testing requested:**
```
IF user said "create tests" OR "write tests" OR BUILD spec has "Tests" section:
  Proceed with testing
ELSE:
  Skip to Step 6
```

**Spawn test-implementer:**
```
Task(test-implementer, """
Implement comprehensive tests for working implementation.

Spec: $WORK_DIR/.spec/BUILD_[taskname].md
Workflow: solo

Production code: [files from step 2]

CRITICAL STANDARDS (from agent-prompting skill):
- 1:1 file mapping: tests/unit/test_<module>.py for src/<module>.py
- 95% coverage minimum
- AAA pattern (Arrange-Act-Assert)
- Mock EVERYTHING external to the function being tested:
  - Database calls, API calls, file I/O, cache operations
  - OTHER INTERNAL FUNCTIONS called by the function under test
  - Test function in ISOLATION, not with its dependencies
- Integration tests: 2-4 files per module (ADD to existing, don't create new)
- DO NOT run tests

Load testing-standards skill.

Implementation is validated and working - tests document behavior.

Read spec: $WORK_DIR/.spec/BUILD_[taskname].md
""")
```

**Test & fix loop:**
```
LOOP until tests pass with coverage:
  1. Run tests with coverage:
     pytest tests/ --cov=$WORK_DIR --cov-report=term-missing -v

  2. IF passing + coverage >= 95%:
       Break

  3. IF failed:
       Task(fix-executor, """
       Fix test failures.

       Spec: $WORK_DIR/.spec/BUILD_[taskname].md
       Workflow: solo

       Test output:
       [paste pytest output]

       CRITICAL RULES (from agent-prompting skill):
       - Fix PROPERLY - no workarounds
       - Maintain business logic
       - Follow code standards: logging.getLogger, try/except only for connections

       Load python-style skill.

       Read spec: $WORK_DIR/.spec/BUILD_[taskname].md
       """)

       Re-run tests

  4. IF attempt > 3: ESCALATE with failure details
```

**Commit changes**

---

### Step 6: Cleanup .spec/

**Goal:** Clean up temporary .spec/ artifacts.

**Archive task-related files:**
```bash
# Create archive directory
mkdir -p $WORK_DIR/.spec/archive/

# Archive operational files
mv $WORK_DIR/.spec/PROGRESS.md $WORK_DIR/.spec/archive/
mv $WORK_DIR/.spec/BUILD_*.md $WORK_DIR/.spec/archive/

# Keep DOC_VALIDATION_REPORT.json for reference if exists
```

**Update .gitignore to exclude archived files:**
```bash
echo ".spec/archive/" >> $WORK_DIR/.gitignore
```

**Commit changes**

---

### Step 7: Complete

**Final summary:**
```
✅ Task complete!

Files: X created, Y modified
Tasks: Z completed
Testing: {W tests passing, V% coverage} OR {Skipped - not requested}
Quality: All validation passed

Ready for use.
```

**Final commit**

---

## Sub-Agents

**Implementation:** implementation-executor, test-implementer
**Validation:** security-auditor, performance-optimizer, code-reviewer, code-beautifier, documentation-reviewer
**Fixing:** fix-executor
**Analysis:** general-builder

All inherit parent tools (Read, Write, Edit, Bash, Grep, Glob).

All agents spawned during /solo receive:
```
Spec: $WORK_DIR/.spec/BUILD_[taskname].md
Workflow: solo
```

---

## Tracking

**BUILD spec:** `.spec/BUILD_[taskname].md` - minimal context
**PROGRESS.md:** Simple task tracking
**TodoWrite:** Step completion
**Git commits:** After each major step

**Templates:** `~/.claude/templates/spec-minimal.md`, `~/.claude/templates/operational.md`

---

## When to Escalate to /conduct

**If you discover during execution:**
- More components needed than anticipated
- Complex dependencies emerge
- Architecture needs planning
- Multiple valid approaches exist

**Tell user:**
```
This task is more complex than initially assessed.

Reasons:
- [what you discovered]

Recommend:
1. Stop current work
2. Run /spec to properly plan architecture
3. Run /conduct for full orchestration

OR

Continue with /solo if: [condition]
```

Let user decide.

---

## Escalation (When Blocked)

**When:**
- 3 failed attempts
- External deps missing
- Architectural issue discovered
- Security concern unfixable

**Format:**
```
🚨 BLOCKED: [Step] - [Issue]

Issue: [description]
Attempts: [what tried]
Need: [specific question]
Options: [A, B, C]
Recommendation: [your suggestion]
```

---

## Key Rules

**DO:**
- Generate BUILD spec for context
- Execute task-by-task (2 reviewers per task)
- Full validation after all tasks (6 reviewers)
- Update PROGRESS.md throughout
- Parallelize: reviewers, independent tasks
- Documentation phase BEFORE testing
- Testing ONLY if user requested
- Archive .spec/ files after completion
- Commit after major steps
- Escalate to /conduct if complexity discovered

**DON'T:**
- Use for complex multi-component tasks
- Skip per-task validation (2 reviewers required)
- Skip full validation after tasks
- Run tests unless user requested
- Accept prose responses from agents
- Complete with failing validation
- Continue after 3 failed attempts
- Delete .spec/ files before merging learnings to permanent docs

---

## Comparison: /solo vs /conduct

**Use /solo when:**
- ✅ Single component or few related files
- ✅ Clear, straightforward implementation
- ✅ Standard patterns apply
- ✅ Fast iteration desired

**Use /conduct when:**
- ✅ Multiple interconnected components
- ✅ Dependencies need management
- ✅ Architecture needs planning
- ✅ Variant exploration beneficial
- ✅ High stakes (security, payments, auth)

**Key difference:**
- /solo: Streamlined workflow (7 steps: spec → task-by-task impl → full validation → docs → optional tests → cleanup → done)
- /conduct: Full orchestration (dependency analysis, per-component phases, worktrees, skeletal progression)
- **BOTH:** Same validation rigor (2 reviewers per task, 6 reviewers full validation, comprehensive testing, documentation)

**When in doubt:** Start with /solo, escalate to /conduct if needed.

---

**You are focused. Delegate task-by-task, validate incrementally, parallelize where possible, deliver.**
