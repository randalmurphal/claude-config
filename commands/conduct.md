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
- Component validation at each step

**Prerequisites:** `.spec/SPEC.md` MUST exist (created by `/spec`)

**If no SPEC.md:**
Tell user: "No spec found. Run /spec first to create .spec/SPEC.md, then run /conduct."
STOP - do not proceed.

---

## Your Mission

1. Parse SPEC.md and build dependency graph
2. Generate per-component phase specs
3. Execute each component phase: Skeleton → Implement → Validate/Fix Loop → Unit Test → Checkpoint
4. Enhance future phase specs with discoveries from completed phases
5. Integration testing after all components complete
6. Documentation validation
7. Deliver working, tested, validated, documented system

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

### Phase -1: Parse SPEC.md & Build Dependency Graph

**Read SPEC.md:**
- Extract components from "Files to Create/Modify" section
- Extract dependencies from "Depends on:" field for each file
- Extract implementation phases (if specified)
- Extract quality requirements

**Build dependency graph:**
```
For each file in "Files to Create/Modify":
  file_path = extract path
  depends_on = extract "Depends on:" field
  complexity = extract "Complexity:" field
  purpose = extract "Purpose:" field

  graph[file_path] = {
    'dependencies': depends_on,
    'complexity': complexity,
    'purpose': purpose
  }
```

**Topologically sort components:**
- Perform topological sort on dependency graph
- Detect circular dependencies (DFS cycle detection)
- If cycle found → FAIL LOUD with cycle path
- Result: component_order (list of components in dependency order)

**Initialize tracking:**
- Create PROGRESS.md (see `~/.claude/templates/operational.md`)
- TodoWrite: Component-level tracking

**Commit changes**

---

### Phase 0: Validate Component Phase Specs Exist

**Check for component phase specs:**
```bash
# Look for SPEC_N_*.md files in .spec/
ls $WORK_DIR/.spec/SPEC_*.md | grep -v "^SPEC.md$"
```

**If component phase specs exist (created by /spec):**
- ✅ Use them as-is
- Verify they match component_order from dependency graph
- Skip to Phase 1

**If component phase specs DON'T exist (fallback):**
- Generate them now from SPEC.md

**Generate fallback specs for each component in component_order:**

Create `.spec/SPEC_{phase_num}_{component_name}.md`:

```markdown
# Phase {N}: {Component Name}

## Components in This Phase
- {file_path}
  - Purpose: {from SPEC.md}
  - Complexity: {from SPEC.md}

## Dependencies
{List what this component depends on from previous phases}

## What's Available from Previous Phases
{Initially empty, will be populated as phases complete}

## Success Criteria
{Extract from SPEC.md for this component}

## Known Gotchas
{Extract from SPEC.md "Known Gotchas" section}
{Will be enhanced as phases complete}

## Implementation Requirements
{Extract from SPEC.md "Proposed Approach" and "Requirements"}

## Testing Requirements
{Extract from SPEC.md "Testing Strategy"}
```

**Result:**
```
.spec/
├── SPEC.md                        # High-level architecture (unchanged)
├── SPEC_1_foundation.md          # Phase 1 component details
├── SPEC_2_database.md            # Phase 2 component details
├── SPEC_3_api.md                 # Phase 3 component details
├── ...
├── DISCOVERIES.md                # Learnings captured here
└── PROGRESS.md                   # Phase tracking
```

**Note:** Ideally /spec creates these during discovery. This is fallback if missing.

**Commit changes**

---

### Phase 1-N: Component Phases (for each component in dependency order)

**For each component:**

#### Step 1: Skeleton

**Create skeleton:**
- Spawn skeleton-builder for production file:
```
Task(skeleton-builder, """
Create skeleton for {component}.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct

Read spec for requirements and dependencies.
""")
```

- Spawn test-skeleton-builder for test file (parallel):
```
Task(test-skeleton-builder, """
Create test skeleton for {component}.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct

Read spec for requirements and dependencies.
""")
```

**Validate syntax:**
```bash
python -m py_compile {component_file}
# or: tsc --noEmit (TypeScript)
```

**Commit changes**

---

#### Step 2: Implementation

**Spawn implementation-executor:**
```
Task(implementation-executor, """
Implement {component}.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct

Read spec for complete requirements.

Available from previous phases:
{List completed components this depends on}

Agent will read spec automatically.
""")
```

**Wait for completion, check status COMPLETE**

**Review result:**
- Files created make sense?
- Gotchas found? → Note in DISCOVERIES.md
- Spec corrections? → Document in DISCOVERIES.md
- Blockers? → ESCALATE or adjust approach

**Commit changes**

---

#### Step 3: Validate & Fix Loop

**Goal:** Get component working before writing tests.

**Run validation:**
```bash
# Syntax/import checks
python -m py_compile $WORK_DIR/{component}/*.py
# or: tsc --noEmit (for TypeScript)

# Linting
ruff check $WORK_DIR/{component}
```

**Spawn 6 reviewers in parallel (NO SKIMPING):**

All get spec context:
```
Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct
```

Single message with 6 Task calls:
1. security-auditor
2. performance-optimizer
3. code-reviewer (pass 1: complexity, errors, clarity)
4. code-reviewer (pass 2: responsibility, coupling, type safety)
5. code-beautifier (DRY, magic numbers, dead code)
6. code-reviewer (pass 3: documentation, comments, naming)

**Combine findings:**
- Parse all responses
- Merge critical + important + minor lists
- Deduplicate issues

**Fix ALL issues (no skipping):**
```
LOOP until validation clean:
  1. Spawn fix-executor with ALL issues (critical + important + minor)
     ```
     Task(fix-executor, """
     Fix all validation issues for {component}.

     Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
     Workflow: conduct

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

  2. Re-run linting: ruff check $WORK_DIR/{component}

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

#### Step 4: Unit Testing

**Now that component works, lock in behavior with tests.**

**Spawn test-implementer:**
```
Task(test-implementer, """
Implement comprehensive unit tests for working component.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct

Production code: {component_file}
Coverage target: 95%+
Follow: ~/.claude/docs/TESTING_STANDARDS.md

Component is validated and working - tests document behavior.

Agent will read spec automatically.
""")
```

**Test & fix loop:**
```
LOOP until tests pass with coverage:
  1. Run tests with coverage:
     pytest tests/{component}/ --cov=$WORK_DIR/{component} --cov-report=term-missing -v

  2. IF passing + coverage >= 95%:
       Break

  3. IF failed:
       Spawn fix-executor with test failures:
       ```
       Task(fix-executor, """
       Fix test failures for {component}.

       Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
       Workflow: conduct

       Test output:
       [paste pytest output]

       Fix implementation bugs found by tests.
       Maintain business logic.

       Agent will read spec automatically.
       """)
       ```
       Re-run tests

  4. IF attempt > 3: ESCALATE with failure details
```

**Commit changes**

---

#### Step 5: Document Discoveries & Enhance Future Phase Specs

**Update DISCOVERIES.md:**
```markdown
## Component: {component_name} (Phase {N})

### Discoveries
- {what was learned during implementation}
- {gotchas encountered}
- {spec corrections made}

### API Surface
- {public functions/classes available}
- {usage examples}
- {known limitations}
```

**Enhance future phase specs:**
```
For each remaining phase spec (SPEC_{M}_{component}.md where M > N):
  IF that component depends on current component:
    Update "What's Available from Previous Phases" section:
    - Add current component's API surface
    - Add gotchas from DISCOVERIES.md that affect future component
    - Add usage examples if relevant
```

**Example enhancement:**
```markdown
# Phase 3: API Routes (SPEC_3_api.md)

## What's Available from Previous Phases
- Phase 1: auth module
  - auth.verify_token(token: str) -> User
  - auth.create_token(user_id: str) -> str
  - Gotcha: verify_token expects 'Bearer' prefix in token string
  - Example: user = auth.verify_token(f"Bearer {token}")

- Phase 2: database module
  - db.query(sql: str, params: dict) -> List[Row]
  - db.save(table: str, data: dict) -> int
  - Gotcha: Connection pool must be initialized before first query
```

**Commit changes**

---

#### Step 6: Checkpoint Component

**Component fully complete:**
- ✅ Validated (all issues fixed)
- ✅ Unit tested (95%+ coverage)
- ✅ Discoveries documented
- ✅ Future phase specs enhanced

**Summary:**
```
✅ Component {N}: {component_name} complete!

Files: X created, Y modified
Tests: Z passing (W% coverage)
Quality: All validation passed
Discoveries: [brief summary]

Ready for dependent components.
```

**Commit changes**

---

### Phase N+1: Integration Testing

**All components working individually, now test interactions.**

**Spawn test-implementer:**
```
Task(test-implementer, """
Implement integration tests for multi-component interactions.

Spec: $WORK_DIR/.spec/SPEC.md
Workflow: conduct

All components are implemented and unit tested:
{list all completed components}

Test cross-component workflows:
{extract from SPEC.md "Testing Strategy" - integration scenarios}

Coverage target: End-to-end scenarios from SPEC.md

Agent will read spec automatically.
""")
```

**Test & fix loop:**
```
LOOP until integration tests pass:
  1. Run integration tests:
     pytest tests/integration/ -v

  2. IF passing:
       Break

  3. IF failed:
       Spawn fix-executor with integration failures:
       ```
       Task(fix-executor, """
       Fix integration test failures.

       Spec: $WORK_DIR/.spec/SPEC.md
       Workflow: conduct

       Test output:
       [paste pytest output]

       Fix bugs in component interactions.
       Components are individually tested, issue is integration.

       Agent will read spec automatically.
       """)
       ```
       Re-run tests

  4. IF attempt > 3: ESCALATE with failure details
```

**Commit changes**

---

### Phase N+2: Documentation Validation

**Goal:** Ensure ALL documentation is accurate and up-to-date.

**Find all documentation in working directory:**
```bash
# Find markdown files (README, docs, etc.)
find $WORK_DIR -name "*.md" -type f

# Common docs to check:
- README.md
- $WORK_DIR/.spec/SPEC.md
- $WORK_DIR/.spec/SPEC_*.md (phase specs)
- CLAUDE.md (if in working dir)
- Any project-specific docs
```

**Invoke documentation-validator agent:**

```
validation_result = Task(documentation-validator, """
Validate ALL documentation for 100% accuracy against implementation.

Working directory: $WORK_DIR
Spec: $WORK_DIR/.spec/SPEC.md
Workflow: conduct

Validation scope:
- CLAUDE.md (at current level)
- README.md
- docs/ directory (all .md files if exists)
- .spec/ files (SPEC.md, SPEC_*.md phase specs)

Steps:
1. Invoke ai-documentation skill to load standards
2. Find all .md files in $WORK_DIR
3. Validate systematically (6-step methodology):
   - File:line references accurate
   - Function signatures match code
   - Architecture claims verified
   - Constants/values correct
   - CLAUDE.md structure follows best practices
   - No duplication from parent CLAUDE.md
4. Return structured JSON response with issues categorized

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
  Spec: $WORK_DIR/.spec/SPEC.md

  Issues to fix (JSON from validator):
  [paste validation_result JSON]

  Fix priorities:
  1. All CRITICAL issues (incorrect refs, signatures, contradictions)
  2. All IMPORTANT issues (missing docs, outdated terms)
  3. MINOR issues if time permits

  Invoke ai-documentation skill for standards.
  """)

  # Re-validate after fixes
  Task(documentation-validator, "Re-validate all documentation after fixes...")
```

**Documentation validation complete criteria:**
- ✅ All .md files reviewed
- ✅ No outdated information
- ✅ Code examples match implementation
- ✅ Phase specs include discoveries from implementation
- ✅ No contradictions between docs and code

**Commit changes**

---

### Phase N+3: CLAUDE.md Optimization

**Goal:** Ensure CLAUDE.md files follow hierarchical best practices and don't exceed line count targets.

**Find all CLAUDE.md files in working directory:**
```bash
find $WORK_DIR -name "CLAUDE.md" -type f
```

**For EACH CLAUDE.md found, validate with documentation-validator:**

```
# NOTE: documentation-validator in Phase N+2 already validates CLAUDE.md structure
# This phase focuses on optimization if issues remain

Task(documentation-validator, """
Validate CLAUDE.md optimization (focus on line count and structure).

Working directory: $WORK_DIR
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

### Phase N+4: Complete

**Update SPEC.md:**
- Add any major gotchas discovered to "Known Gotchas" section
- Note any TODOs for future work

**Final summary:**
```
✅ Implementation complete!

Components: X implemented and tested
Integration tests: Y passing
Documentation: Z files validated and updated
Quality: All validation passed

System ready for use.
```

**Commit changes**

---

## Worktree Variant Exploration

**Use when:**
- Multiple valid approaches for same component
- Architectural uncertainty
- High-risk changes

**Process:**
1. Decide on N approaches for component
2. Create worktrees: `git worktree add ../variant-a` etc.
3. For each variant:
   - Run component phase (Skeleton → Impl → Validate → Test) in that worktree
   - Track results in PROGRESS.md
4. Spawn investigator per variant (parallel)
5. Compare results:
   - Pick winner, OR
   - Spawn merge-coordinator to combine best parts
6. Cleanup worktrees: `git worktree remove ../variant-a`

---

## Sub-Agents

**Implementation:** skeleton-builder, implementation-executor, test-implementer, test-skeleton-builder
**Validation:** security-auditor, performance-optimizer, code-reviewer, code-beautifier
**Fixing:** fix-executor
**Analysis:** investigator, general-builder

All inherit parent tools (Read, Write, Edit, Bash, Grep, Glob).

All agents spawned during /conduct receive:
```
Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct
```

Agents auto-read spec for full context.

---

## Tracking

**SPEC.md:** High-level architecture (created by /spec, unchanged during /conduct)
**SPEC_N_component.md:** Per-component phase specs (generated by /conduct, enhanced as phases complete)
**DISCOVERIES.md:** Learnings captured as phases complete
**PROGRESS.md:** Detailed component/step tracking
**TodoWrite:** High-level component completion
**Git commits:** After each major step

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
🚨 BLOCKED: [Component/Phase] - [Issue]

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
- Generate SPEC_N_component.md files
- Execute per-component phases (Skeleton → Impl → Validate → Test → Checkpoint)
- Validate each component before moving to next
- Enhance future phase specs with discoveries
- Integration testing after all components
- Documentation validation at end
- Fix-validate loops (3 max per component)
- Track in PROGRESS.md + TodoWrite
- Commit after major steps

**DON'T:**
- Proceed without SPEC.md
- Skip per-component validation
- Move to next component with failing tests
- Let sub-agents spawn sub-agents
- Accept prose responses
- Skip integration testing
- Skip documentation validation

---

**You are the conductor. Parse dependencies, execute components bottom-up, validate incrementally, deliver working system.**
