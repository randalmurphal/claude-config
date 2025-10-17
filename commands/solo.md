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
2. Implement via sub-agents
3. Validate & fix loop (get it working first)
4. Comprehensive testing (lock in behavior)
5. Documentation validation (ensure accuracy)
6. Deliver working, tested, validated, documented code

**You are intelligent.** Assess if task is actually straightforward. If not, tell user to use /conduct.

**You are autonomous.** Execute without asking permission at each step.

**Token budget:** Use what you need (typically 10-20k for solo tasks).

---

## Workflow

### Step 0: Determine Working Directory

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
- Goal, Problem, Approach
- Files to create/modify
- Tests required
- Quality constraints
- Context for sub-agents

**Template:** `~/.claude/templates/spec-minimal.md`

**Naming:** Extract 2-3 words (e.g., "rate-limit", "user-export")

**Initialize PROGRESS.md** (simpler than /conduct)

**Commit changes** (follow project's commit style from recent commits)

---

### Step 2: Implementation

**Spawn implementation-executor:**
```
Task(implementation-executor, """
Implement [task description]

Spec: $WORK_DIR/.spec/BUILD_[taskname].md
Workflow: solo

[Additional context if needed]

Agent will read spec automatically - no need to paste spec content.
""")
```

**Wait for completion, check status COMPLETE**

**Review result:**
- Files created make sense?
- Gotchas found? → Note in PROGRESS.md
- Blockers? → ESCALATE or adjust approach

**Commit changes**

---

### Step 3: Validation & Fix Loop

**Goal:** Get implementation working before writing tests.

**Run validation:**
```bash
# Syntax/import checks
python -m py_compile $WORK_DIR/**/*.py
# or: tsc --noEmit (for TypeScript)

# Linting
ruff check $WORK_DIR
```

**Spawn 6 reviewers in parallel (NO SKIMPING):**

All get spec context:
```
Spec: $WORK_DIR/.spec/BUILD_[taskname].md
Workflow: solo
```

1. security-auditor
2. performance-optimizer
3. code-reviewer (pass 1: complexity, errors, clarity)
4. code-reviewer (pass 2: responsibility, coupling, type safety)
5. code-beautifier (DRY, magic numbers, dead code)
6. code-reviewer (pass 3: documentation, comments, naming)

**Combine findings:**
- Parse all responses (JSON for reviewers, markdown for beautifier)
- Merge critical + important + minor lists
- Deduplicate issues

**Fix ALL issues (no skipping):**
```
LOOP until validation clean:
  1. Spawn fix-executor with ALL issues (critical + important + minor)
     ```
     Task(fix-executor, """
     Fix all validation issues.

     Spec: $WORK_DIR/.spec/BUILD_[taskname].md
     Workflow: solo

     Critical issues:
     [list]

     Important issues:
     [list]

     Minor issues:
     [list]

     RULES:
     - Fix the actual problem, don't add # noqa or ignore comments
     - If linter error has proper solution (extract method, simplify), do that
     - Only if NO proper fix exists AND business logic must stay: document why
     - Maintain business logic while making code cleaner

     Agent will read spec automatically.
     """)
     ```

  2. Re-run linting: ruff check $WORK_DIR

  3. Re-run ALL 6 reviewers (verify fixes didn't break anything)

  4. IF new issues found: Continue loop
     IF validation clean: Break
     IF loop > 3 attempts: ESCALATE with details

  5. NO ignored errors allowed unless absolutely necessary (document reason)
```

**Validation complete criteria:**
- ✅ Zero linter errors (or all documented with justification)
- ✅ All reviewer critical issues fixed
- ✅ All reviewer important issues fixed
- ✅ All reviewer minor issues fixed
- ✅ No # noqa / # type: ignore / @ts-ignore comments (unless documented exception)
- ✅ Code compiles/imports successfully

**Commit changes**

---

### Step 4: Testing

**Now that implementation works, lock in behavior with tests.**

**Spawn test-implementer:**
```
Task(test-implementer, """
Implement comprehensive tests for working implementation.

Spec: $WORK_DIR/.spec/BUILD_[taskname].md
Workflow: solo

Production code: [files from step 2]
Follow: ~/.claude/docs/TESTING_STANDARDS.md

Key rules:
- 1:1 file mapping: one test file per production file
- Coverage: 95%+ for all public functions
- Test happy path + error cases + edge cases
- Choose organization: single function (simple), parametrized (many cases), or separate methods (critical)

Implementation is validated and working - tests document behavior.

Agent will read spec automatically.
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
       Spawn fix-executor with test failures:
       ```
       Task(fix-executor, """
       Fix test failures.

       Spec: $WORK_DIR/.spec/BUILD_[taskname].md
       Workflow: solo

       Test output:
       [paste pytest output]

       Fix implementation bugs found by tests.
       Maintain business logic.
       Follow testing standards: ~/.claude/docs/TESTING_STANDARDS.md

       Agent will read spec automatically.
       """)
       ```
       Re-run tests

  4. IF attempt > 3: ESCALATE with failure details
```

**Commit changes**

---

### Step 5: Documentation Validation

**Goal:** Ensure ALL documentation is accurate and up-to-date.

**Find all documentation in working directory:**
```bash
# Find markdown files (README, docs, etc.)
find $WORK_DIR -name "*.md" -type f

# Common docs to check:
- README.md
- $WORK_DIR/.spec/BUILD_*.md
- CLAUDE.md (if in working dir)
- Any project-specific docs
```

**Invoke documentation-validator agent:**

```
validation_result = Task(documentation-validator, """
Validate ALL documentation for 100% accuracy against implementation.

Working directory: $WORK_DIR
Spec: $WORK_DIR/.spec/BUILD_[taskname].md
Workflow: solo

Validation scope:
- CLAUDE.md (at current level)
- README.md
- docs/ directory (all .md files if exists)
- .spec/BUILD_[taskname].md

Steps:
1. Invoke ai-documentation skill to load standards
2. Find all .md files in $WORK_DIR
3. Validate systematically:
   - File:line references accurate
   - Function signatures match code
   - Architecture claims verified
   - Constants/values correct
   - CLAUDE.md structure follows best practices
4. Return structured JSON with issues categorized

See ~/.claude/docs/DOCUMENTATION_VALIDATOR_AGENT.md for full methodology.

Agent will read spec automatically.
""")
```

**Fix documentation issues (if found):**
```
IF validation_result contains CRITICAL or IMPORTANT issues:
  Task(general-builder, """
  Fix documentation issues found by validator.

  Working directory: $WORK_DIR
  Spec: $WORK_DIR/.spec/BUILD_[taskname].md

  Issues to fix (JSON from validator):
  [paste validation_result JSON]

  Fix priorities:
  1. All CRITICAL issues
  2. All IMPORTANT issues
  3. MINOR issues if time permits

  Invoke ai-documentation skill for standards.
  """)

  # Re-validate after fixes
  Task(documentation-validator, "Re-validate after fixes...")
```

**Documentation validation complete criteria:**
- ✅ All .md files reviewed
- ✅ No outdated information
- ✅ Code examples match implementation
- ✅ BUILD spec includes discoveries from implementation
- ✅ No contradictions between docs and code

**Commit changes**

---

### Step 6: CLAUDE.md Optimization

**Goal:** Ensure CLAUDE.md files follow hierarchical best practices and don't exceed line count targets.

**Find all CLAUDE.md files in working directory:**
```bash
find $WORK_DIR -name "CLAUDE.md" -type f
```

**Validate CLAUDE.md with documentation-validator:**

```
# NOTE: documentation-validator in Step 5 already validated CLAUDE.md
# This step focuses on optimization if issues remain

Task(documentation-validator, """
Validate CLAUDE.md optimization (focus on line count and structure).

Working directory: $WORK_DIR
Spec: $WORK_DIR/.spec/BUILD_[taskname].md
CLAUDE.md file: [path to CLAUDE.md]

Invoke ai-documentation skill to load best practices.

Check:
1. Line count within target for hierarchy level
2. No duplication from parent CLAUDE.md
3. Business logic in table format (not prose)
4. File structure condensed
5. Deep-dive content extracted to QUICKREF.md if >400 lines

Return structured JSON with optimization recommendations.

See ~/.claude/docs/DOCUMENTATION_VALIDATOR_AGENT.md for methodology.
""")
```

**Fix CLAUDE.md issues:**
```
IF CLAUDE.md issues found:
  For each file with issues:
    Task(general-builder, """
    Optimize CLAUDE.md following AI documentation best practices.

    File: [path to CLAUDE.md]
    Working directory: $WORK_DIR
    Spec: $WORK_DIR/.spec/BUILD_[taskname].md

    Invoke ai-documentation skill to load best practices.

    Issues to fix:
    [paste JSON from validator]

    Optimization strategy:
    1. Remove duplicate content (reference parent CLAUDE.md files)
    2. Convert prose to tables/bullets (content optimization)
    3. Extract deep-dive content to QUICKREF.md if >400 lines
    4. Condense file structure trees
    5. Ensure line count within target for hierarchy level

    Maintain all critical information - reorganize for AI readability.
    """)

  # Re-validate
  Task(documentation-validator, "Re-validate optimized CLAUDE.md files...")
```

**CLAUDE.md optimization complete criteria:**
- ✅ All CLAUDE.md files within target line counts
- ✅ No duplication across hierarchy levels
- ✅ Business logic in table format (where applicable)
- ✅ Deep-dive content extracted to QUICKREF.md (if needed)
- ✅ Hierarchical references working (child → parent)

**Commit changes**

---

### Step 7: Complete

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

**Commit changes**

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
- Commit after major steps (follow project's commit style)
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
- /solo: Streamlined workflow (6 steps: spec → impl → validate → test → docs → done)
- /conduct: Full orchestration (dependency analysis, worktrees, skeletal phase)
- **BOTH:** Same validation rigor (comprehensive reviewers, testing, documentation)

**When in doubt:** Start with /solo, escalate to /conduct if needed.

---

**You are focused. Delegate, validate, deliver.**
