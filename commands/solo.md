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
2. Delegate to sub-agents (NO skimping on testing/validation)
3. Fix-validate loop (3 attempts)
4. Deliver working, tested, validated code

**You are intelligent.** Assess if task is actually straightforward. If not, tell user to use /conduct.

**You are autonomous.** Execute without asking permission at each step.

**Token budget:** Use what you need (typically 10-20k for solo tasks).

---

## Workflow

### Step 1: Generate Minimal Spec

**Create `.spec/BUILD_[taskname].md`:**
- Goal, Problem, Approach
- Files to create/modify
- Tests required
- Quality constraints
- Context for sub-agents

**Template:** `~/.claude/templates/spec-minimal.md`

**Naming:** Extract 2-3 words (e.g., "rate-limit", "user-export")

**Initialize PROGRESS.md** (simpler than /conduct)

**Git commit:** `solo: Spec created`

---

### Step 2: Implementation

**Spawn implementation-executor:**
```
Task(implementation-executor, """
Implement [task description]

Context from BUILD spec:
[paste relevant sections]

RESPONSE TEMPLATE (use EXACTLY):
[paste from ~/.claude/templates/agent-responses.md]
""")
```

**Wait for completion, check status COMPLETE**

**Review result:**
- Files created make sense?
- Gotchas found? → Note in PROGRESS.md
- Blockers? → ESCALATE or adjust approach

**Git commit:** `solo: Implementation complete`

---

### Step 3: Testing

**Spawn test-implementer:**
```
Task(test-implementer, """
Implement tests for [task]

Production code: [files from step 2]
Coverage target: 90%
Follow: ~/.claude/docs/TESTING_STANDARDS.md

RESPONSE TEMPLATE (use EXACTLY):
[paste from ~/.claude/templates/agent-responses.md]
""")
```

**Run & fix:**
```
Fix-validate loop (max 3 attempts):
  Run: pytest tests/ --cov=src --cov-report=term-missing -v

  IF passing + coverage >= 90%:
    Break

  IF failed:
    IF attempt < 3:
      spawn fix-executor with failures
      wait for fixes
    IF attempt == 3:
      ESCALATE: "Cannot fix after 3 attempts"
```

**Loop details:** `~/.claude/templates/operational.md`

**Git commit:** `solo: Testing complete`

---

### Step 4: Validation

**Quick check:**
```bash
pytest tests/ -v && ruff check .
```

**Spawn 6 reviewers (parallel - NO SKIMPING):**
1. security-auditor
2. performance-optimizer
3. code-reviewer (pass 1: complexity, errors, clarity)
4. code-reviewer (pass 2: responsibility, coupling, type safety)
5. code-beautifier (DRY, magic numbers, dead code)
6. documentation-reviewer (comments, naming, TODOs)

**Agent templates:** `~/.claude/templates/agent-responses.md`

**Combine findings:**
- Parse 6 JSON responses
- Merge critical + important + minor lists
- Deduplicate

**Combination algorithm:** `~/.claude/templates/operational.md`

**Fix critical + important:**
- Spawn fix-executor with combined list
- Re-run pytest + ruff
- Re-run 6 reviewers to verify
- Loop until clean

**Minor issues:**
- Accept or fix (quick judgment)

**Git commit:** `solo: Validation passed`

---

### Step 5: Complete

**Update BUILD spec:**
- Add any gotchas discovered
- Note any TODOs for future

**Final summary:**
```
✅ Task complete!

Files: X created, Y modified
Tests: Z passing (W% coverage)
Quality: All validation passed

Ready for use.
```

**Git commit:** `solo: Complete`

---

## Agent Response Templates

**All agents use structured responses (NOT prose).**

**Templates:** `~/.claude/templates/agent-responses.md`

**How to embed:**
```
Task(agent-name, """
[Task description and context]

RESPONSE TEMPLATE (use EXACTLY):
[paste template]

Do not add prose outside template.
""")
```

---

## Sub-Agents

**Implementation:** implementation-executor, test-implementer
**Validation:** security-auditor, performance-optimizer, code-reviewer (2x), code-beautifier, documentation-reviewer
**Fixing:** fix-executor

All inherit parent tools (Read, Write, Edit, Bash, Grep, Glob).

---

## Tracking

**BUILD spec:** `.spec/BUILD_[taskname].md` - minimal context
**PROGRESS.md:** Simple step tracking
**TodoWrite:** Step completion

**Formats:** `~/.claude/templates/operational.md`

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
- Delegate to sub-agents (don't implement yourself)
- Test thoroughly (90% coverage minimum)
- Validate properly (6 reviewers - SAME as /conduct)
- Fix-validate loops (3 attempts max)
- Git commit after steps
- Escalate to /conduct if complexity discovered

**DON'T:**
- Use for complex multi-component tasks
- Skip testing
- Skip validation
- Accept prose responses from agents
- Checkpoint with failing tests
- Continue after 3 failed attempts

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
- /solo: Simpler workflow (5 steps vs 6 phases)
- /conduct: Full orchestration (dependency analysis, worktrees, skeletal phase)
- **BOTH:** Same validation rigor (6 reviewers, comprehensive testing)

**When in doubt:** Start with /solo, escalate to /conduct if needed.

---

**You are focused. Delegate, validate, deliver.**
