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

### Phase 1: Load Agent Prompting Skill

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

### Phase 3: Generate Minimal Spec

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

**Commit changes** (pre-commit validation runs automatically):
```bash
# Git pre-commit hook runs automatically on commit:
# - Auto-format (ruff/prettier/gofmt)
# - Linting (ruff check/eslint/golangci-lint)
# - Type checking (pyright/tsc)

# If hooks fail:
#   - Review output
#   - Fix issues
#   - Re-stage files: git add .
#   - Commit again
```

---

### Phase 4: Task-by-Task Implementation

**Read implementation tasks from BUILD_[taskname].md:**
```markdown
## Implementation Tasks
- Implement data models
- Implement validation logic
- Implement API endpoint
- Add error handling
```

**Determine if tasks can run in parallel:**
```
# Simple batching for /solo (fewer tasks, simpler dependencies)
independent_tasks = [tasks with no mutual dependencies]

IF len(independent_tasks) >= 3 AND complexity suggests >30s each:
  # Batch parallel execution
  Spawn ALL implementation-executors in PARALLEL (single message)
  Wait for all to complete
  Run 2 reviewers per task in PARALLEL
ELSE:
  # Sequential execution (overhead not worth it for solo)
  Execute tasks sequentially
```

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

3. Fix issues (if found) - WITH INTELLIGENT FAILURE PATTERN DETECTION + VOTING GATE:
   IF critical or important issues:
     # Track failure patterns across attempts
     failure_history = []

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

       failure_history.append(current_issues)

       IF clean: Break
       IF attempt >= 2:
         # GATE 4: FIX STRATEGY VOTING
         IF same_issue_repeated(failure_history):
           # Same issue after 2 attempts = need voting consensus on fix strategy

           # Spawn 3 general-investigator agents in PARALLEL (single message)
           vote_results = []

           FOR i in range(3):
             result = Task(general-investigator, """
             Analyze repeated fix failure and vote on fix strategy.

             Task: {task description}
             Spec: $WORK_DIR/.spec/BUILD_[taskname].md
             Workflow: solo

             Failure History:
             - Attempt 1: {failure_history[0]}
             - Attempt 2: {failure_history[1]}

             Code Context: [relevant file excerpts]

             VOTE ON ONE:
             - FIX_IN_PLACE: Issue can be fixed with current approach
             - REFACTOR: Architectural change needed (suggest specific refactor)
             - ESCALATE: Requires human decision

             Return JSON:
             {
               "vote": "FIX_IN_PLACE" | "REFACTOR" | "ESCALATE",
               "reasoning": "why this approach",
               "specific_recommendation": "concrete next step"
             }
             """)
             vote_results.append(result)

           # Tally votes (2/3 consensus required)
           votes = tally_votes(vote_results)
           winning_vote = votes.most_common_with_threshold(threshold=2)

           IF winning_vote == "FIX_IN_PLACE":
             # Consensus: one more attempt with combined recommendations
             recommendations = merge_recommendations(vote_results, "FIX_IN_PLACE")

             Task(fix-executor, """
             Fix issues based on voting consensus.

             Spec: $WORK_DIR/.spec/BUILD_[taskname].md
             Task: {task description}

             Strategy: FIX_IN_PLACE (voted 2/3 or 3/3)

             Combined Recommendations:
             {recommendations}

             This is a final attempt based on consensus.
             """)

             Re-run 2 code-reviewers to verify

             IF still failing:
               ESCALATE with voting results + failure history

           ELSE IF winning_vote == "REFACTOR":
             # Consensus: architectural change needed
             refactor_plan = merge_refactor_plans(vote_results, "REFACTOR")

             ESCALATE: """
             🚨 BLOCKED: {Task} - Voting Consensus: REFACTOR Required

             Vote Results: {votes}

             Refactor Plan (consensus):
             {refactor_plan}

             Failure History:
             - Attempt 1: {failure_history[0]}
             - Attempt 2: {failure_history[1]}

             Recommendation: Apply refactor or escalate to /conduct for proper planning.
             """

           ELSE IF winning_vote == "ESCALATE":
             # Consensus: human decision needed
             ESCALATE: """
             🚨 BLOCKED: {Task} - Voting Consensus: Human Decision Required

             Vote Results: {votes}

             Failure History:
             - Attempt 1: {failure_history[0]}
             - Attempt 2: {failure_history[1]}

             Voting Analysis:
             {summarize_reasoning(vote_results, "ESCALATE")}

             Consider /conduct if task more complex than anticipated.
             """

           ELSE:
             # No consensus (e.g., 1-1-1 split)
             ESCALATE: """
             🚨 BLOCKED: {Task} - No Voting Consensus

             Vote Results: {votes}

             No clear consensus on fix strategy. Need human decision.

             Failure History:
             - Attempt 1: {failure_history[0]}
             - Attempt 2: {failure_history[1]}
             """

         ELSE:
           # Different issues = making progress
           ESCALATE: "Multiple different issues after 2 attempts. Need human review."

4. Update PROGRESS.md with task completion

5. Commit changes for this task (pre-commit validation runs automatically)

NEXT task...
```

**Common failure patterns to detect:**
- **Circular dependency**: Same circular import error → suggest dependency inversion
- **Tight coupling**: Same coupling violation → suggest interface extraction
- **Complexity**: Same complexity warning → suggest function decomposition
- **Type errors**: Same type mismatch → suggest protocol/abstract base class

**After ALL tasks complete:**

Update BUILD spec with any discoveries:
```markdown
## Implementation Notes (added after completion)
- {gotchas encountered}
- {deviations from original approach}
- {learnings}
```

**Commit changes** (pre-commit validation runs)

---

### Phase 5: Full Validation

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

**Fix ALL issues (max 3 attempts with pattern detection + voting):**
```
failure_history = []

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

  failure_history.append(current_issues)

  3. IF clean: Break
     IF new issues AND attempt < 3: Continue loop
     IF attempt >= 3:
       # GATE 4: FIX STRATEGY VOTING (same as Phase 4)
       IF same_issues_repeated(failure_history):
         # Spawn 3 general-investigator agents in PARALLEL
         vote_results = []

         FOR i in range(3):
           result = Task(general-investigator, """
           Analyze repeated validation fix failure and vote on fix strategy.

           Spec: $WORK_DIR/.spec/BUILD_[taskname].md
           Workflow: solo

           Failure History:
           {failure_history}

           Code Context: [relevant excerpts from all files]

           VOTE ON ONE:
           - FIX_IN_PLACE: Issue can be fixed with current approach
           - REFACTOR: Architectural change needed
           - ESCALATE: Requires human decision

           Return JSON with vote, reasoning, specific_recommendation.
           """)
           vote_results.append(result)

         # Tally votes (2/3 consensus)
         votes = tally_votes(vote_results)
         winning_vote = votes.most_common_with_threshold(threshold=2)

         # Handle winning_vote same as Phase 4 (FIX_IN_PLACE, REFACTOR, ESCALATE, or no consensus)

       ELSE:
         ESCALATE: "Different issues across 3 attempts, need review"

  4. Update PROGRESS.md with validation status
```

**After validation clean + all fixes applied:**

```
# GATE 5: PRODUCTION-READINESS VOTING
# All issues fixed, time for production-readiness assessment

# Spawn 3 code-reviewer agents in PARALLEL (single message)
readiness_results = []

FOR i in range(3):
  result = Task(code-reviewer, """
  Vote on production-readiness after full validation.

  Spec: $WORK_DIR/.spec/BUILD_[taskname].md
  Workflow: solo

  Context:
  - All validation issues fixed
  - 6 reviewers approved (security, performance, code quality, etc.)
  - Linting/type checking passed

  Files to assess: [all implementation files]

  VOTE ON ONE:
  - PRODUCTION_READY: Code is production-ready
  - NEEDS_WORK: Minor issues remain (list specific items)
  - RISKY: Concerns about production deployment (list risks)

  Load python-style skill.

  Return JSON:
  {
    "vote": "PRODUCTION_READY" | "NEEDS_WORK" | "RISKY",
    "reasoning": "why this assessment",
    "concerns": ["list any specific concerns"],
    "recommendations": ["list any recommendations"]
  }
  """)
  readiness_results.append(result)

# Tally votes (2/3 consensus)
readiness_votes = tally_votes(readiness_results)
readiness_consensus = readiness_votes.most_common_with_threshold(threshold=2)

IF readiness_consensus == "PRODUCTION_READY":
  # Consensus: ready to proceed
  Log: """
  ✅ PRODUCTION-READINESS VOTE: APPROVED

  Vote Results: {readiness_votes}

  Proceeding to Phase 6 (Documentation).
  """

ELSE IF readiness_consensus == "NEEDS_WORK":
  # Consensus: minor issues need addressing
  combined_concerns = merge_concerns(readiness_results, "NEEDS_WORK")

  Task(fix-executor, """
  Address production-readiness concerns from voting.

  Spec: $WORK_DIR/.spec/BUILD_[taskname].md
  Workflow: solo

  Vote Results: {readiness_votes}

  Concerns to address:
  {combined_concerns}

  These are final polish items before production.
  """)

  # Re-run 3 code-reviewers to verify (PARALLEL)
  # Re-vote if needed (max 1 re-vote)

ELSE IF readiness_consensus == "RISKY":
  # Consensus: production concerns exist
  risks = merge_risks(readiness_results, "RISKY")

  ESCALATE: """
  🚨 PRODUCTION-READINESS VOTE: RISKY

  Vote Results: {readiness_votes}

  Identified Risks:
  {risks}

  Recommendations:
  {merge_recommendations(readiness_results, "RISKY")}

  User decision required: Accept risks, address concerns, or redesign?
  """

ELSE:
  # No consensus
  ESCALATE: """
  🚨 PRODUCTION-READINESS VOTE: No Consensus

  Vote Results: {readiness_votes}

  Reviewers disagree on production-readiness. Need human decision.

  Summary of concerns:
  {summarize_all_concerns(readiness_results)}
  """
```

**Validation complete criteria:**
- ✅ Zero linting errors
- ✅ All critical issues fixed
- ✅ All important issues fixed
- ✅ All minor issues fixed (or documented why skipped)
- ✅ Production-readiness voting passed (2/3 consensus)

**Commit changes** (pre-commit validation runs)

---

### Phase 6: Documentation (Merge .spec to Permanent Docs)

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

**After documentation validated and fixed:**

```
# GATE 7: DOCUMENTATION QUALITY VOTING
# All doc issues fixed, assess overall documentation quality

# Spawn 3 general-builder agents in PARALLEL (single message)
doc_quality_results = []

FOR i in range(3):
  result = Task(general-builder, """
  Vote on documentation quality after validation and fixes.

  Working directory: $WORK_DIR
  Spec: $WORK_DIR/.spec/BUILD_[taskname].md
  Workflow: solo

  Context:
  - Documentation-reviewer validation passed
  - All critical/important issues fixed
  - Learnings from .spec merged to permanent docs

  Documentation to assess:
  - CLAUDE.md
  - README.md
  - docs/ directory
  - Docstrings in code

  VOTE ON ONE:
  - PRODUCTION_READY: Documentation is complete and accurate
  - GAPS_EXIST: Missing important documentation (list gaps)
  - INACCURATE: Documentation contradicts code (list inaccuracies)

  Load ai-documentation skill.

  Return JSON:
  {
    "vote": "PRODUCTION_READY" | "GAPS_EXIST" | "INACCURATE",
    "reasoning": "why this assessment",
    "specific_issues": ["list specific gaps or inaccuracies"],
    "recommendations": ["list recommended additions/fixes"]
  }
  """)
  doc_quality_results.append(result)

# Tally votes (2/3 consensus)
doc_votes = tally_votes(doc_quality_results)
doc_consensus = doc_votes.most_common_with_threshold(threshold=2)

IF doc_consensus == "PRODUCTION_READY":
  # Consensus: docs are production-ready
  Log: """
  ✅ DOCUMENTATION QUALITY VOTE: APPROVED

  Vote Results: {doc_votes}

  Proceeding to Phase 7 (Testing) or Phase 8 (Cleanup).
  """

ELSE IF doc_consensus == "GAPS_EXIST":
  # Consensus: documentation gaps need filling
  gaps = merge_gaps(doc_quality_results, "GAPS_EXIST")

  Task(general-builder, """
  Fill documentation gaps identified by voting.

  Working directory: $WORK_DIR
  Spec: $WORK_DIR/.spec/BUILD_[taskname].md
  Workflow: solo

  Vote Results: {doc_votes}

  Gaps to fill:
  {gaps}

  Load ai-documentation skill.

  Add missing documentation based on consensus.
  """)

  # Re-validate with documentation-reviewer
  # Re-vote if needed (max 1 re-vote)

ELSE IF doc_consensus == "INACCURATE":
  # Consensus: documentation contradicts code
  inaccuracies = merge_inaccuracies(doc_quality_results, "INACCURATE")

  Task(general-builder, """
  Fix documentation inaccuracies identified by voting.

  Working directory: $WORK_DIR
  Spec: $WORK_DIR/.spec/BUILD_[taskname].md
  Workflow: solo

  Vote Results: {doc_votes}

  Inaccuracies to fix:
  {inaccuracies}

  Load ai-documentation skill.

  Correct documentation to match actual code behavior.
  """)

  # Re-validate with documentation-reviewer
  # Re-vote if needed (max 1 re-vote)

ELSE:
  # No consensus
  ESCALATE: """
  🚨 DOCUMENTATION QUALITY VOTE: No Consensus

  Vote Results: {doc_votes}

  Reviewers disagree on documentation quality. Need human decision.

  Summary of concerns:
  {summarize_all_issues(doc_quality_results)}
  """
```

**Documentation validation complete criteria:**
- ✅ All .md files reviewed
- ✅ No CRITICAL or IMPORTANT issues remaining
- ✅ .spec/BUILD_[taskname].md learnings merged into permanent docs
- ✅ File:line references accurate
- ✅ Function signatures match code
- ✅ Code examples work
- ✅ CLAUDE.md line counts within targets
- ✅ Documentation quality voting passed (2/3 consensus)

**Commit changes** (pre-commit validation runs)

---

### Phase 7: [OPTIONAL] Testing

**Only run if user explicitly requested tests.**

**Check if testing requested:**
```
IF user said "create tests" OR "write tests" OR BUILD spec has "Tests" section:
  Proceed with testing
ELSE:
  Skip to Phase 8
```

**Spawn test-implementer:**
```
Task(test-implementer, """
Implement comprehensive tests for working implementation.

Spec: $WORK_DIR/.spec/BUILD_[taskname].md
Workflow: solo

Production code: [files from phase 4]

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

**After tests pass + coverage >= 95%:**

```
# GATE 6: TEST COVERAGE ADEQUACY VOTING
# Tests pass and coverage met, assess test quality

# Spawn 3 code-reviewer agents in PARALLEL (single message)
test_adequacy_results = []

FOR i in range(3):
  result = Task(code-reviewer, """
  Vote on test coverage adequacy after tests pass.

  Spec: $WORK_DIR/.spec/BUILD_[taskname].md
  Workflow: solo

  Context:
  - All tests passing
  - Coverage >= 95%

  Test files to assess: [all test files]
  Production files: [all implementation files]

  VOTE ON ONE:
  - ADEQUATE: Test coverage is sufficient
  - NEEDS_MORE_TESTS: Important scenarios missing (list gaps)
  - WEAK_TESTS: Tests exist but lack rigor (list weaknesses)

  Load testing-standards skill.

  Return JSON:
  {
    "vote": "ADEQUATE" | "NEEDS_MORE_TESTS" | "WEAK_TESTS",
    "reasoning": "why this assessment",
    "gaps": ["missing test scenarios"],
    "weak_areas": ["tests that need strengthening"],
    "recommendations": ["specific improvements needed"]
  }
  """)
  test_adequacy_results.append(result)

# Tally votes (2/3 consensus)
test_votes = tally_votes(test_adequacy_results)
test_consensus = test_votes.most_common_with_threshold(threshold=2)

IF test_consensus == "ADEQUATE":
  # Consensus: test coverage is adequate
  Log: """
  ✅ TEST COVERAGE ADEQUACY VOTE: APPROVED

  Vote Results: {test_votes}

  Proceeding to Phase 8 (Cleanup).
  """

ELSE IF test_consensus == "NEEDS_MORE_TESTS":
  # Consensus: important scenarios missing
  missing_scenarios = merge_gaps(test_adequacy_results, "NEEDS_MORE_TESTS")

  Task(test-implementer, """
  Add missing test scenarios identified by voting.

  Spec: $WORK_DIR/.spec/BUILD_[taskname].md
  Workflow: solo

  Vote Results: {test_votes}

  Missing scenarios:
  {missing_scenarios}

  Load testing-standards skill.

  Add tests for identified gaps.
  """)

  # Re-run tests to verify new tests pass
  # Re-vote if needed (max 1 re-vote)

ELSE IF test_consensus == "WEAK_TESTS":
  # Consensus: tests lack rigor
  weaknesses = merge_weaknesses(test_adequacy_results, "WEAK_TESTS")

  Task(test-implementer, """
  Strengthen weak tests identified by voting.

  Spec: $WORK_DIR/.spec/BUILD_[taskname].md
  Workflow: solo

  Vote Results: {test_votes}

  Weaknesses:
  {weaknesses}

  Load testing-standards skill.

  Improve test rigor based on consensus.
  """)

  # Re-run tests to verify strengthened tests pass
  # Re-vote if needed (max 1 re-vote)

ELSE:
  # No consensus
  ESCALATE: """
  🚨 TEST COVERAGE ADEQUACY VOTE: No Consensus

  Vote Results: {test_votes}

  Reviewers disagree on test adequacy. Need human decision.

  Summary of concerns:
  {summarize_all_test_concerns(test_adequacy_results)}
  """
```

**Commit changes** (pre-commit validation runs)

---

### Phase 8: Cleanup .spec/

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

**Commit changes** (pre-commit validation runs)

---

### Phase 9: Complete

**Final summary:**
```
✅ Task complete!

Files: X created, Y modified
Tasks: Z completed
Testing: {W tests passing, V% coverage} OR {Skipped - not requested}
Quality: All validation passed
Voting Gates: 4 gates passed (Fix Strategy, Production-Readiness, Documentation Quality, Test Coverage)

Ready for use.
```

**Final commit** (pre-commit validation runs)

---

## Sub-Agents

**Implementation:** implementation-executor, test-implementer
**Validation:** security-auditor, performance-optimizer, code-reviewer, code-beautifier, documentation-reviewer
**Fixing:** fix-executor
**Analysis:** general-builder, general-investigator

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
**Git commits:** After each major step (with pre-commit validation)

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
- 3 failed attempts (with repeated failure pattern)
- Voting gate produces ESCALATE consensus
- Voting gate produces no consensus
- External deps missing
- Architectural issue discovered
- Security concern unfixable

**Format:**
```
🚨 BLOCKED: [Phase] - [Issue]

Issue: [description]
Attempts: [what tried]
Voting Results: [if gate involved]
Pattern Detected: [if applicable - repeated failure analysis]
Need: [specific question]
Options: [A, B, C]
Recommendation: [your suggestion]
```

---

## Key Rules

**DO:**
- Generate BUILD spec for context
- Execute task-by-task (2 reviewers per task)
- Batch independent tasks when beneficial (3+ tasks, >30s each)
- Detect intelligent failure patterns in fix loops
- Use voting gates when fix patterns repeat (Gate 4)
- Full validation after all tasks (6 reviewers)
- Use production-readiness voting after validation (Gate 5)
- Use documentation quality voting after doc fixes (Gate 7)
- Use test coverage adequacy voting after tests pass (Gate 6)
- Update PROGRESS.md throughout
- Parallelize: reviewers, independent tasks, voting agents
- Documentation phase BEFORE testing
- Testing ONLY if user requested
- Archive .spec/ files after completion
- Commit after major steps (with pre-commit validation)
- Escalate to /conduct if complexity discovered

**DON'T:**
- Use for complex multi-component tasks
- Skip per-task validation (2 reviewers required)
- Skip full validation after tasks
- Skip voting gates when applicable (repeated failures, production-readiness, doc quality, test adequacy)
- Run tests unless user requested
- Accept prose responses from agents
- Complete with failing validation
- Continue after 3 failed attempts without pattern analysis
- Delete .spec/ files before merging learnings to permanent docs
- Retry blindly without analyzing failure patterns
- Proceed with voting gate ESCALATE or no-consensus without user input

---

## Voting Gates Summary

**Gate 4: Fix Strategy Voting**
- **When:** Repeated failures in Phase 4 (task fixes) or Phase 5 (validation fixes)
- **Who:** 3 general-investigator agents (PARALLEL)
- **Votes:** FIX_IN_PLACE, REFACTOR, ESCALATE
- **Threshold:** 2/3 consensus
- **Action:** One more attempt (FIX_IN_PLACE), architectural escalation (REFACTOR), or human decision (ESCALATE)

**Gate 5: Production-Readiness Voting**
- **When:** After Phase 5 validation clean + all fixes applied
- **Who:** 3 code-reviewer agents (PARALLEL)
- **Votes:** PRODUCTION_READY, NEEDS_WORK, RISKY
- **Threshold:** 2/3 consensus
- **Action:** Proceed (PRODUCTION_READY), polish (NEEDS_WORK), or escalate risks (RISKY)

**Gate 6: Test Coverage Adequacy Voting**
- **When:** After Phase 7 tests pass + coverage >= 95%
- **Who:** 3 code-reviewer agents (PARALLEL)
- **Votes:** ADEQUATE, NEEDS_MORE_TESTS, WEAK_TESTS
- **Threshold:** 2/3 consensus
- **Action:** Proceed (ADEQUATE), add scenarios (NEEDS_MORE_TESTS), or strengthen tests (WEAK_TESTS)

**Gate 7: Documentation Quality Voting**
- **When:** After Phase 6 doc validation + fixes applied
- **Who:** 3 general-builder agents (PARALLEL)
- **Votes:** PRODUCTION_READY, GAPS_EXIST, INACCURATE
- **Threshold:** 2/3 consensus
- **Action:** Proceed (PRODUCTION_READY), fill gaps (GAPS_EXIST), or fix inaccuracies (INACCURATE)

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
- /solo: Streamlined workflow (9 phases: load skill → determine dir → spec → task-by-task impl → full validation → docs → optional tests → cleanup → done)
- /conduct: Full orchestration (dependency analysis, impact analysis, per-component phases, skeletal progression)
- **BOTH:** Same validation rigor (2 reviewers per task, 6 reviewers full validation, 4 voting gates, comprehensive testing, documentation)

**When in doubt:** Start with /solo, escalate to /conduct if needed.

---

**You are focused. Delegate task-by-task, detect patterns, use voting gates for consensus, validate incrementally, parallelize where beneficial, deliver.**
