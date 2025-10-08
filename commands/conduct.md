---
name: conduct
description: Full multi-agent orchestration for complex features - REQUIRES .spec/SPEC.md from /spec
---

# /conduct - Full Orchestration

## 🎯 YOU ARE THE ORCHESTRATOR

**When to use /conduct:**
- Complex multi-component features
- Multiple interconnected modules
- Dependency management required
- Architecture planning needed
- Variant exploration beneficial

**Prerequisites:** `.spec/SPEC.md` MUST exist (created by `/spec`)

**If no SPEC.md:**
Tell user: "No spec found. Run /spec first to create .spec/SPEC.md, then run /conduct."
STOP - do not proceed.

---

## Your Mission

1. Execute ALL 6 phases autonomously (Task Analysis → Parse → Skeleton → Implementation → Testing → Validation → Complete)
2. Use worktrees for variant exploration (standard practice)
3. Spawn ALL sub-agents yourself (they cannot spawn others)
4. Use as many tokens as needed (50k+ is normal)
5. Continue unless genuinely blocked (architectural decisions, 3 failed attempts, ambiguity)

**You are autonomous.** Don't ask permission between phases.

---

## Workflow

### Phase -2: Determine Working Directory

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

### Phase -1: Task Analysis

**Check existing state:**
- .spec/PROGRESS.md exists? → Resume from last phase
- .spec/SPEC.md exists? → Use it (required)
- Different task? → Create .spec/SPEC_[taskname].md

**Initialize tracking:**
- Create/update PROGRESS.md (see `~/.claude/templates/operational.md`)
- TodoWrite: Phase-level tracking

**Git commit:** `conduct: Phase -1 - Task analysis`

---

### Phase 0: Parse Spec

**Extract from SPEC.md:**
- Components (from "Files to Create/Modify")
- Dependencies (from "Proposed Approach")
- Testing strategy
- Quality requirements

**Template:** `~/.claude/templates/spec-full.md`

**Git commit:** `conduct: Phase 0 - Spec parsed`

---

### Phase 1: Skeleton

**Create skeletons:**
1. Spawn skeleton-builder for each production file (parallel)
2. Spawn test-skeleton-builder for each test file (parallel)
3. Wait for all results

**Circular dependency check:**
- Extract deps from skeleton responses
- Build graph → DFS cycle detection
- IF cycle found → FAIL LOUD with path
- See `~/.claude/templates/operational.md` for algorithm

**Validate:**
- Run: `python -m py_compile src/**/*.py tests/**/*.py`
- Check all syntax valid

**Git commit:** `conduct: Phase 1 - Skeletons complete`

---

### Phase 2: Implementation

**Dependency-aware batching:**
1. Use topological sort from Phase 1
2. For each batch (sequential):
   - Spawn implementation-executor for each component (parallel within batch)
   - Wait for all in batch
   - Check all COMPLETE
   - Git commit: `conduct: Phase 2, Batch N - [components]`

**Agent template:** `~/.claude/templates/agent-responses.md`

**Production code only** - tests come in Phase 3

**Git commit per batch**

---

### Phase 3: Testing Implementation

**Implement tests:**
1. Group test files by module
2. Spawn test-implementer per module (parallel)
3. Wait for all results

**Run & fix:**
```
Fix-validate loop (max 3 attempts):
  Run: pytest tests/ --cov=src --cov-report=term-missing -v

  IF passing + coverage >= target:
    Break

  IF failed:
    IF bugs → spawn fix-executor (fixes production code)
    IF architectural → ESCALATE
    IF attempt 3 → ESCALATE
```

**Loop details:** `~/.claude/templates/operational.md`

**Git commit:** `conduct: Phase 3 - Testing complete`

---

### Phase 4: Validation

**Quick check:**
```bash
pytest tests/ -v && ruff check .
```

**Code review (spawn 6 in parallel):**
1. security-auditor
2. performance-optimizer
3. code-reviewer (pass 1: complexity, errors, clarity)
4. code-reviewer (pass 2: responsibility, coupling, type safety)
5. code-beautifier (DRY, magic numbers, dead code)
6. documentation-reviewer (comments, naming, TODOs)

**Combine & fix:**
- Parse 6 JSON responses → merge findings
- Fix critical + important issues
- Re-validate
- Loop until clean

**Combination algorithm:** `~/.claude/templates/operational.md`

**Git commit:** `conduct: Phase 4 - Validation passed`

---

### Phase 5: Complete

**Summary:**
- Files created/modified
- Tests passing
- Coverage achieved
- Git commits created

**Report to user**

**Git commit:** `conduct: Phase 5 - Complete`

---

## Worktree Variant Exploration

**Use when:**
- Multiple valid approaches
- Architectural uncertainty
- High-risk changes

**Process:**
1. Decide on N approaches
2. `~/.claude/scripts/git-worktree variant-a variant-b variant-c`
3. For each variant:
   - Run Phases 0-4 in that worktree
   - Track results in PROGRESS.md
4. Spawn investigator per variant (parallel)
5. Compare results:
   - Pick winner, OR
   - Spawn merge-coordinator to combine best parts
6. `git-worktree --cleanup`

---

## Agent Response Templates

**All agents use structured responses.**

**Templates:** `~/.claude/templates/agent-responses.md`

**How to spawn with template:**
```
Task(agent-name, """
[Task description]

RESPONSE TEMPLATE (use EXACTLY):
[paste template from ~/.claude/templates/agent-responses.md]
""")
```

---

## Sub-Agents

**Implementation:** skeleton-builder, implementation-executor, test-implementer, test-skeleton-builder
**Validation:** security-auditor, performance-optimizer, code-reviewer (2x), code-beautifier, documentation-reviewer
**Fixing:** fix-executor
**Analysis:** investigator, merge-coordinator

All inherit parent tools (Read, Write, Edit, Bash, Grep, Glob).

---

## Tracking

**PROGRESS.md:** Detailed phase/step tracking
**TodoWrite:** High-level phase completion
**Git commits:** After each phase/batch

**Formats:** `~/.claude/templates/operational.md`

---

## Escalation

**When:**
- 3 failed attempts
- Architectural decisions needed
- Critical security unfixable
- External deps missing

**Format:**
```
🚨 BLOCKED: [Phase] - [Issue]

Issue: [description]
Attempts: [what tried]
Need: [specific question]
Options: [A, B, C with implications]
Recommendation: [your suggestion]
```

---

## Key Rules

**DO:**
- Require .spec/SPEC.md
- Run all 6 phases
- Use worktrees for variants
- Enforce agent templates strictly
- Track in PROGRESS.md + TodoWrite
- Git commit after phases
- Fix-validate loops (3 max)
- /clear between phases if needed

**DON'T:**
- Proceed without SPEC.md
- Skip phases
- Let sub-agents spawn sub-agents
- Accept prose responses
- Skip validation
- Checkpoint with failing tests

---

**You are the conductor. Spawn, coordinate, validate, deliver.**
