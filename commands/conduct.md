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
2. Analyze change impact (existing codebases)
3. Generate per-component phase specs
4. Execute each component: Skeleton → Task-by-Task Implementation → Full Validation
5. Enhance future phase specs with discoveries
6. Merge .spec learnings into permanent documentation
7. [Optional] Testing if user requested
8. Cleanup .spec/ directory
9. Deliver working, validated, documented system

**You are autonomous.** Don't ask permission between phases.

---

## Workflow

### Phase 1: Load Agent Prompting Skill

**CRITICAL: Load before spawning any sub-agents.**

```
Skill: agent-prompting
```

**This skill contains:**
- Critical inline standards for each agent type
- What to include in prompts (logging, try/except, mocking, etc.)
- Prompt templates with examples

**You will use this throughout all phases to write effective agent prompts.**

---

### Phase 2: Determine Working Directory

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

### Phase 3: Change Impact Analysis

**For existing codebases (not new projects):**

**Goal:** Understand blast radius of changes before starting work.

1. **Identify files to be modified** (from task description or SPEC.md if exists)

2. **For each file to modify:**
   ```bash
   # Find direct dependents (files that import this file)
   grep -r "from.*$(basename $file .py)" $WORK_DIR --include="*.py" -l
   grep -r "import.*$(basename $file .py)" $WORK_DIR --include="*.py" -l
   ```

3. **Recursively find transitive dependents** (dependents of dependents up to 2-3 levels)

4. **Generate impact report** and add to DISCOVERIES.md:
   ```markdown
   ## Change Impact Analysis

   Files to modify: X files
   Direct dependents: Y files (components: auth, api, frontend)
   Transitive dependents: Z files

   Critical dependencies:
   - auth/service.py imported by 8 files → breaking changes affect entire auth flow
   - api/endpoints.py imported by 23 files → API contract changes very risky

   Recommendations:
   - Maintain backward compatibility for auth/service.py
   - Consider deprecation path for api/endpoints.py changes
   - Plan coordinated rollout for components: [list]

   Test surface:
   - Must test: [critical dependent components]
   - Should test: [moderate dependent components]
   - Nice to test: [transitive dependents]
   ```

5. **Add to SPEC.md "Known Gotchas" section** if high-risk changes identified

**Skip this phase if:**
- New project (no existing code)
- Only creating new files (no modifications to existing files)
- User explicitly says skip impact analysis

**Commit changes**

---

### Phase 4: Parse SPEC.md & Build Dependency Graph

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

**Verify dependencies match reality (AUTOMATED VALIDATION):**
```bash
# For each component in dependency graph
for component in component_order:
  declared_deps = graph[component]['dependencies']

  # Use Grep to find actual imports in component file
  actual_imports=$(grep -E "^(from|import)" $component | \
                  sed 's/from \([^ ]*\).*/\1/' | \
                  sed 's/import \([^ ]*\).*/\1/' | \
                  sort -u)

  # Cross-reference with declared dependencies
  missing_deps = []
  for actual_dep in actual_imports:
    if actual_dep in project_modules AND actual_dep not in declared_deps:
      missing_deps.append(actual_dep)

  # FAIL LOUD if mismatch
  if len(missing_deps) > 0:
    ESCALATE: "Component {component} declares {declared_deps} but actually imports {missing_deps}. Fix SPEC.md dependencies before proceeding."
```

**Initialize tracking:**
- Create PROGRESS.md (see `~/.claude/templates/operational.md`)
- Create DISCOVERIES.md (merge with impact analysis from Phase 3)
- TodoWrite: Component-level tracking

**Commit changes** (with pre-commit validation):
```bash
# Git pre-commit hook will run automatically:
# - Auto-format (ruff/prettier/gofmt)
# - Linting (ruff check/eslint/golangci-lint)
# - Type checking (pyright/tsc)
~/.claude/hooks/pre-commit-validation.sh

# If hooks fail:
#   - Review output
#   - Fix issues
#   - Re-stage files: git add .
#   - Commit again
```

---

### Phase 5: Validate Component Phase Specs Exist

**Check for component phase specs:**
```bash
# Look for SPEC_N_*.md files in .spec/
ls $WORK_DIR/.spec/SPEC_*.md | grep -v "^SPEC.md$"
```

**If component phase specs exist (created by /spec):**
- ✅ Use them as-is
- Verify they match component_order from dependency graph
- Skip to Phase 6

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

## Implementation Phases
{Extract from SPEC.md "Implementation Phases" section}

Tasks per phase:
- {task 1}
- {task 2}

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

### Phase 6-N: Component Phases (for each component in dependency order)

**For each component:**

#### Step 1: Skeleton (Sequential: prod → test)

**Create production skeleton FIRST:**
```
Task(skeleton-builder, """
Create skeleton for {component}.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct

CRITICAL STANDARDS (from agent-prompting skill):
- Type hints required, 80 char limit
- Logging: import logging; LOG = logging.getLogger(__name__)

Read spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
""")
```

**Wait for completion, validate syntax:**
```bash
python -m py_compile {component_file}
# or: tsc --noEmit (TypeScript)
```

**THEN create test skeleton (needs prod skeleton to reference):**
```
Task(test-skeleton-builder, """
Create test skeleton for {component}.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct

Production skeleton: {component_file}

CRITICAL STANDARDS (from agent-prompting skill):
- 1:1 file mapping: tests/unit/test_<module>.py
- AAA pattern structure

Read spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
""")
```

**Update PROGRESS.md with skeleton completion**

**Commit changes** (pre-commit validation runs automatically)

---

#### Step 2: Task-by-Task Implementation

**Read implementation phases and tasks from SPEC_{N}_{component}.md:**
```markdown
## Implementation Phases
### Phase 1: Foundation (2h estimate)
Tasks:
- Implement data models
- Implement validation logic

### Phase 2: API (1h estimate)
Tasks:
- Implement endpoint handlers
- Add error handling
```

**For EACH task in EACH phase:**

**Determine if tasks can run in parallel (BATCHING ALGORITHM):**

```
# Analyze task dependencies within phase
task_deps = extract_task_dependencies(phase_tasks)

# Group into waves (topological sort within phase)
waves = topological_sort(phase_tasks, task_deps)

For each wave in waves:
  independent_tasks = tasks_in_wave

  # Parallel execution criteria:
  IF len(independent_tasks) >= 3 AND estimated_duration_per_task > 30s:
    # Batch parallel execution
    Execute ALL tasks in wave simultaneously:
    - Spawn N implementation-executors in PARALLEL (single message)
    - Wait for all to complete
    - Run 2 reviewers per task in PARALLEL
  ELSE:
    # Sequential execution (coordination overhead not worth it)
    For each task:
      Execute task sequentially
```

**Example batching:**
```
Wave 1 (parallel - 3 independent tasks):
  - "Implement data models" (40s)
  - "Implement validation logic" (35s)
  - "Implement utility functions" (30s)
  → Spawn 3 implementation-executors in PARALLEL

Wave 2 (sequential - depends on Wave 1):
  - "Implement API endpoint (depends on models)" (50s)
  → Execute after Wave 1 completes

Wave 3 (parallel - 2 independent tasks):
  - "Add error handling" (25s)
  - "Add logging" (20s)
  → Duration too short, execute sequentially (overhead > benefit)
```

**For EACH task:**

```
1. Implement task:
   Task(implementation-executor, """
   Implement: {task description}

   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct
   Phase: {phase name}
   Task: {task name}

   CRITICAL STANDARDS (from agent-prompting skill):
   - Logging: import logging; LOG = logging.getLogger(__name__)
   - try/except ONLY for connection errors (network, DB, cache)
   - Type hints required, 80 char limit
   - No # noqa without documented reason
   - DO NOT run tests

   Load python-style skill.

   Available from previous components:
   {List completed components this depends on}

   Read spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Focus on: {phase name} → {task name}
   """)

2. Validate task (2 code-reviewers in PARALLEL - single message with 2 Task calls):

   Task(code-reviewer, """
   Review: {task description}

   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct

   Focus: Code quality, logic correctness, standards compliance

   Load python-style skill.

   Return JSON: {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   """)

   Task(code-reviewer, """
   Review: {task description}

   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct

   Focus: Edge cases, error handling, coupling

   Return JSON: {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   """)

3. Fix issues (if found) - WITH INTELLIGENT FAILURE PATTERN DETECTION:
   IF critical or important issues:
     # Track failure patterns across attempts
     failure_history = []

     LOOP (max 2 attempts):
       Task(fix-executor, """
       Fix task validation issues.

       Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
       Task: {task description}

       Issues: [paste combined JSON from 2 reviewers]

       CRITICAL RULES (from agent-prompting skill):
       - Fix PROPERLY - no workarounds
       - Follow code standards: logging.getLogger, try/except only for connections
       - Max 2 attempts, then ESCALATE

       Load python-style skill.

       Read spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
       """)

       Re-run 2 code-reviewers in parallel (verify fixes)

       failure_history.append(current_issues)

       IF clean: Break
       IF attempt >= 2:
         # INTELLIGENT PATTERN ANALYSIS
         IF same_issue_repeated(failure_history):
           # Same issue after 2 attempts = architectural problem
           issue_type = classify_issue(failure_history)

           ESCALATE: """
           🚨 BLOCKED: {Component} - Repeated Issue Pattern

           Issue Type: {issue_type} (detected across {len(failure_history)} attempts)

           Pattern: {describe_pattern(failure_history)}

           Examples:
           - Attempt 1: {failure_history[0]}
           - Attempt 2: {failure_history[1]}

           Root Cause Analysis:
           {suggest_root_cause(issue_type, failure_history)}

           Recommended Fixes:
           {suggest_architectural_fix(issue_type)}

           This requires architectural decision or different approach.
           """
         ELSE:
           # Different issues = making progress
           ESCALATE: "Multiple different issues after 2 attempts. Need human review."

4. Update tracking:
   - PROGRESS.md: Mark task complete
   - DISCOVERIES.md: Note any gotchas/learnings from this task

5. Commit changes for this task (pre-commit validation runs)

NEXT task...
```

**Common failure patterns to detect:**
- **Circular dependency**: Same circular import error → suggest dependency inversion or interface extraction
- **Tight coupling**: Same coupling violation → suggest facade pattern or dependency injection
- **Complexity**: Same complexity warning → suggest function extraction or class decomposition
- **Type errors**: Same type mismatch → suggest protocol/abstract base class

**After ALL tasks in component complete:**

Update DISCOVERIES.md with component summary:
```markdown
## Component: {component_name} (Phase {N})

### Implementation Notes
- {consolidated learnings from all tasks}
- {gotchas encountered}
- {deviations from spec}

### API Surface
- {public functions/classes}
- {usage examples}
- {known limitations}
```

**Commit changes**

---

#### Step 3: Full Component Validation

**Goal:** Comprehensive validation of entire component after all tasks complete.

**Run linting + 6 reviewers in PARALLEL (single message with 7 operations):**

```bash
# Operation 1: Linting (run alongside reviewers)
ruff check $WORK_DIR/{component} && pyright $WORK_DIR/{component}
```

```
# Operations 2-7: Spawn 6 reviewers (same message as linting)

Common for all reviewers:
- Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
- Workflow: conduct
- Return JSON: {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}

Task(security-auditor, """
Audit {component} for security vulnerabilities.

Load vulnerability-triage skill.

Review entire component for: injection risks, auth bypasses, data exposure, crypto issues.
""")

Task(performance-optimizer, """
Review {component} for performance issues.

Load mongodb-aggregation-optimization skill if MongoDB code detected.

Review for: N+1 queries, missing indexes, inefficient algorithms, memory leaks.
""")

Task(code-reviewer, """
Review {component}: complexity, errors, clarity.

Load python-style skill.

Focus: cyclomatic complexity, error handling, code clarity, maintainability.
""")

Task(code-reviewer, """
Review {component}: responsibility, coupling, type safety.

Focus: SRP violations, tight coupling, type hint coverage, interface clarity.
""")

Task(code-beautifier, """
Review {component}: DRY violations, magic numbers, dead code.

Focus: code duplication, hardcoded values, unused imports/variables, formatting.
""")

Task(code-reviewer, """
Review {component}: documentation, comments, naming.

Focus: docstring coverage, comment quality, variable naming, function naming.
""")
```

**Combine all findings:**
- Merge linting errors + 6 reviewer responses
- Consolidate critical + important + minor
- Deduplicate issues

**Fix ALL issues (max 3 attempts with pattern detection):**
```
failure_history = []

LOOP until validation clean:
  1. Spawn fix-executor:
     Task(fix-executor, """
     Fix all validation issues for {component}.

     Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
     Workflow: conduct

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

     Read spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
     """)

  2. Re-run linting + 6 reviewers in PARALLEL (single message - verify fixes)

  failure_history.append(current_issues)

  3. IF clean: Break
     IF new issues AND attempt < 3: Continue loop
     IF attempt >= 3:
       # INTELLIGENT PATTERN ANALYSIS
       IF same_issues_repeated(failure_history):
         pattern = analyze_failure_pattern(failure_history)
         ESCALATE with pattern analysis and architectural recommendations
       ELSE:
         ESCALATE: "Different issues across 3 attempts, need review"

  4. Update PROGRESS.md with validation status
```

**Validation complete criteria:**
- ✅ Zero linting errors
- ✅ All critical issues fixed
- ✅ All important issues fixed
- ✅ All minor issues fixed (or documented why skipped)

**Commit changes** (pre-commit validation runs)

---

#### Step 4: Enhance Future Phase Specs

**Update future component specs with discoveries from this component:**

```
For each remaining phase spec (SPEC_{M}_{component}.md where M > N):
  IF that component depends on current component:
    Update "What's Available from Previous Phases" section:

    - Add current component's API surface
    - Add gotchas from DISCOVERIES.md that affect future component
    - Add usage examples if relevant

    Example:
    ```markdown
    ## What's Available from Previous Phases

    ### Phase {N}: {current_component}
    - function_name(params) -> return_type
      - Location: file.py:123
      - Purpose: What it does
      - Gotcha: Known edge case
      - Example: usage_example()
    ```
```

**Commit changes**

---

#### Step 5: Component Checkpoint

**Component fully complete:**
- ✅ Skeleton created (prod + test)
- ✅ All tasks implemented and validated
- ✅ Full component validation passed
- ✅ Discoveries documented
- ✅ Future phase specs enhanced

**Summary:**
```
✅ Component {N}: {component_name} complete!

Files: X created, Y modified
Tasks: Z completed
Quality: All validation passed
Discoveries: [brief summary]

Ready for dependent components.
```

**Update TodoWrite: Mark component complete**

**Commit changes**

**NEXT component in dependency order...**

---

### Phase N+1: Documentation (Merge .spec to Permanent Docs)

**Goal:** Merge all learnings from .spec/ into permanent documentation before cleanup.

**Invoke documentation-reviewer to validate ALL current documentation:**

```
validation_result = Task(documentation-reviewer, """
Validate ALL documentation systematically against implementation.

Working directory: $WORK_DIR
Spec: $WORK_DIR/.spec/SPEC.md
Workflow: conduct

All components implemented and tested. Validate docs match reality.

Load ai-documentation skill.

Find all .md files in $WORK_DIR, validate each systematically:
- CLAUDE.md
- README.md
- docs/ directory
- .spec/ files

Check:
- File:line references accurate
- Function signatures match code
- Code examples work
- CLAUDE.md line counts within targets
- No duplication from parent CLAUDE.md
- Business logic claims verified

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
    Spec: $WORK_DIR/.spec/SPEC.md

    Issues to fix (JSON from reviewer):
    [paste issues for this file]

    Fix priorities:
    1. All CRITICAL issues (incorrect refs, signatures, contradictions)
    2. All IMPORTANT issues (missing docs, outdated terms, line count violations)
    3. MINOR issues if time permits

    Load ai-documentation skill.

    IMPORTANT: Merge learnings from .spec/DISCOVERIES.md into permanent docs.
    """)

  # Re-validate after fixes
  Task(documentation-reviewer, """
  Re-validate all documentation after fixes.

  Working directory: $WORK_DIR
  Spec: $WORK_DIR/.spec/SPEC.md

  Load ai-documentation skill.

  Return JSON with remaining issues (if any).
  """)
```

**Documentation validation complete criteria:**
- ✅ All .md files reviewed
- ✅ No CRITICAL or IMPORTANT issues remaining
- ✅ .spec/DISCOVERIES.md learnings merged into permanent docs
- ✅ File:line references accurate
- ✅ Function signatures match code
- ✅ Code examples work
- ✅ CLAUDE.md line counts within targets

**Commit changes** (pre-commit validation runs)

---

### Phase N+2: [OPTIONAL] Testing

**Only run if user explicitly requested tests OR SPEC.md specifies testing requirements.**

**Check if testing requested:**
```
IF user said "create tests" OR "write tests" OR SPEC.md has "Testing Strategy" section:
  Proceed with testing
ELSE:
  Skip to Phase N+3
```

#### Unit Testing (per component)

**If multiple components with independent tests → spawn test-implementers in PARALLEL:**

```
FOR each component in component_order:
  Task(test-implementer, """
  Implement comprehensive unit tests for {component}.

  Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
  Workflow: conduct

  Production code: {component_file}

  CRITICAL STANDARDS (from agent-prompting skill):
  - 1:1 file mapping: tests/unit/test_<module>.py
  - 95% coverage minimum
  - AAA pattern (Arrange-Act-Assert)
  - Mock EVERYTHING external to the function being tested:
    - Database calls, API calls, file I/O, cache operations
    - OTHER INTERNAL FUNCTIONS called by the function under test
    - Test function in ISOLATION, not with its dependencies
  - DO NOT run tests

  Load testing-standards skill.

  Component is validated and working - tests document behavior.

  Read spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
  """)
```

**Test & fix loop (per component):**
```
LOOP until tests pass with coverage:
  1. Run tests with coverage:
     pytest tests/unit/ --cov=$WORK_DIR --cov-report=term-missing -v

  2. IF passing + coverage >= 95%:
       Break

  3. IF failed:
       Task(fix-executor, """
       Fix test failures.

       Spec: $WORK_DIR/.spec/SPEC.md
       Workflow: conduct

       Test output:
       [paste pytest output]

       CRITICAL RULES (from agent-prompting skill):
       - Fix PROPERLY - no workarounds
       - Maintain business logic
       - Follow code standards: logging.getLogger, try/except only for connections

       Load python-style skill.

       Read spec: $WORK_DIR/.spec/SPEC.md
       """)

       Re-run tests

  4. IF attempt > 3: ESCALATE with failure details
```

**Commit changes** (pre-commit validation runs)

---

#### Integration Testing (only if SPEC.md specifies)

**Check if integration tests specified in SPEC.md:**
```
IF SPEC.md "Testing Strategy" section includes integration test scenarios:
  Proceed with integration testing
ELSE:
  Skip integration testing
```

**Spawn test-implementer for integration tests:**
```
Task(test-implementer, """
Implement integration tests for multi-component interactions.

Spec: $WORK_DIR/.spec/SPEC.md
Workflow: conduct

All components are implemented and unit tested:
{list all completed components}

Test cross-component workflows:
{extract from SPEC.md "Testing Strategy" - integration scenarios}

CRITICAL STANDARDS (from agent-prompting skill):
- Integration tests: 2-4 files per module (ADD to existing, don't create new)
- Use REAL dependencies (test database, cache) - NOT mocks
- Test components working together
- DO NOT run tests

Load testing-standards skill.

Coverage target: End-to-end scenarios from SPEC.md

Read spec: $WORK_DIR/.spec/SPEC.md
""")
```

**Test & fix loop:**
```
LOOP until integration tests pass:
  1. Run integration tests:
     pytest tests/integration/ -v

  2. IF passing: Break

  3. IF failed:
       Task(fix-executor, """
       Fix integration test failures.

       Spec: $WORK_DIR/.spec/SPEC.md
       Workflow: conduct

       Test output:
       [paste pytest output]

       CRITICAL RULES (from agent-prompting skill):
       - Fix PROPERLY - no workarounds
       - Components are individually tested, issue is integration
       - Follow code standards: logging.getLogger, try/except only for connections

       Load python-style skill.

       Read spec: $WORK_DIR/.spec/SPEC.md
       """)

       Re-run tests

  4. IF attempt > 3: ESCALATE with failure details
```

**Commit changes** (pre-commit validation runs)

---

### Phase N+3: Cleanup .spec/

**Goal:** Clean up temporary .spec/ artifacts, archive task-related files, keep only permanent docs.

**Archive task-related files:**
```bash
# Create archive directory
mkdir -p $WORK_DIR/.spec/archive/

# Archive operational files
mv $WORK_DIR/.spec/PROGRESS.md $WORK_DIR/.spec/archive/
mv $WORK_DIR/.spec/DISCOVERIES.md $WORK_DIR/.spec/archive/

# Archive component phase specs (keep SPEC.md for reference)
mv $WORK_DIR/.spec/SPEC_*.md $WORK_DIR/.spec/archive/ 2>/dev/null || true

# Keep SPEC.md as permanent reference
# Keep DOC_VALIDATION_REPORT.json for reference
```

**Update .gitignore to exclude archived files:**
```bash
echo ".spec/archive/" >> $WORK_DIR/.gitignore
```

**Commit changes** (pre-commit validation runs)

---

### Phase N+4: Complete

**Update SPEC.md (in archive now):**
- Add any major gotchas discovered to "Known Gotchas" section
- Note any TODOs for future work

**Final summary:**
```
✅ Implementation complete!

Components: X implemented and validated
Testing: {Y unit tests passing, Z integration tests passing} OR {Skipped - not requested}
Documentation: All validated and updated
Quality: All validation passed

System ready for use.
```

**Final commit** (pre-commit validation runs)

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
   - Run component phase (Skeleton → Task Implementation → Validate) in that worktree
   - Track results in PROGRESS.md
4. Spawn investigator per variant (parallel)
5. Compare results:
   - Pick winner, OR
   - Spawn merge-coordinator to combine best parts
6. Cleanup worktrees: `git worktree remove ../variant-a`

---

## Sub-Agents

**Implementation:** skeleton-builder, implementation-executor, test-implementer, test-skeleton-builder
**Validation:** security-auditor, performance-optimizer, code-reviewer, code-beautifier, documentation-reviewer
**Fixing:** fix-executor
**Analysis:** general-investigator, general-builder

All inherit parent tools (Read, Write, Edit, Bash, Grep, Glob).

All agents spawned during /conduct receive:
```
Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct
```

---

## Tracking

**SPEC.md:** High-level architecture (created by /spec, archived after /conduct)
**SPEC_N_component.md:** Per-component phase specs (generated by /conduct, archived after)
**DISCOVERIES.md:** Learnings captured during implementation (archived after)
**PROGRESS.md:** Detailed task tracking (archived after)
**TodoWrite:** High-level component completion tracking
**Git commits:** After each major step (with pre-commit validation)

**Templates:** `~/.claude/templates/operational.md`

---

## Escalation

**When:**
- 3 failed fix attempts (with repeated failure pattern)
- Architectural decisions needed
- Critical security unfixable
- External deps missing

**Format:**
```
🚨 BLOCKED: [Component/Phase] - [Issue]

Issue: [description]
Attempts: [what tried]
Pattern Detected: [if applicable - repeated failure analysis]
Need: [specific question]
Options: [A, B, C with implications]
Recommendation: [your suggestion]
```

---

## Key Rules

**DO:**
- Require .spec/SPEC.md
- Run change impact analysis (Phase 3)
- Verify dependencies match reality (Phase 4)
- Batch independent tasks for parallel execution
- Detect intelligent failure patterns in fix loops
- Generate SPEC_N_component.md files if not exist
- Execute per-component: Skeleton (sequential) → Task-by-Task Impl (2 reviewers per task) → Full Validation (6 reviewers)
- Update PROGRESS.md + DISCOVERIES.md throughout
- Parallelize: reviewers, independent tasks, independent component tests
- Enhance future phase specs with discoveries
- Documentation phase BEFORE testing
- Testing ONLY if user requested
- Archive .spec/ files after completion
- Commit after major steps (with pre-commit validation)

**DON'T:**
- Proceed without SPEC.md
- Skip dependency verification (Phase 4)
- Skip per-task validation (2 reviewers required)
- Move to next component with failing validation
- Run tests unless user requested
- Let sub-agents spawn sub-agents
- Skip documentation validation before cleanup
- Delete .spec/ files before merging learnings to permanent docs
- Retry blindly without analyzing failure patterns

---

**You are the conductor. Analyze impact, verify dependencies, batch parallel work, detect patterns, execute incrementally with validation at each step, deliver working system.**
