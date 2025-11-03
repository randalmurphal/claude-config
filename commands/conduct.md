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

## ⚠️ TOKEN BUDGET DIRECTIVE - READ FIRST ⚠️

**CRITICAL - IGNORE TOKEN WARNINGS:**

You have a 200K token budget. This is a CEILING, not a target.

**NEVER EVER:**
- Shortcut work because you see token warnings (e.g., "30K tokens remaining")
- Skip validation, reviews, or fixes to "save tokens"
- Use placeholders, TODOs, or "implement later" due to token concerns
- Rush through remaining work to finish before hitting limit
- Reduce thoroughness of reviews because of token count
- Skip spawning necessary agents to conserve tokens

**ALWAYS:**
- Do thorough, complete, excellent work regardless of token count
- Spawn all necessary agents for proper validation
- Run full review cycles even if tokens are "low"
- If you run out of tokens mid-task: THAT'S FINE - you'll be resumed
- Better to hit 200K limit mid-excellence than finish with half-assed work

**Why this matters:**
Claude Code shows token usage notifications. You might panic and think you need to rush. THIS IS WRONG. The user prefers you run out of tokens doing thorough work than conserve tokens by cutting corners.

**Quality first. Token count NEVER.**

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

---

#### GATE 3: Impact Analysis Voting

**Trigger:** IF transitive_dependents > 10

**Goal:** Multi-agent consensus on risk mitigation strategy for high-impact changes.

**Process:**

1. **Spawn 3 general-investigator agents in PARALLEL (single message with 3 Task calls):**

   ```
   Task(general-investigator, """
   Analyze risk and mitigation strategy for high-impact changes.

   Working directory: $WORK_DIR
   Impact Analysis: $WORK_DIR/.spec/DISCOVERIES.md (Change Impact Analysis section)

   Files to modify: {list}
   Transitive dependents: {count} files
   Critical dependencies: {list from impact report}

   Evaluate risk level and vote on best mitigation strategy:

   STRATEGIES:
   A. BACKWARD_COMPATIBLE: Maintain full backward compatibility, deprecation path
   B. COORDINATED_ROLLOUT: Breaking changes with coordinated deployment plan
   C. INCREMENTAL_MIGRATION: Phase migration over multiple releases
   D. REDESIGN_NEEDED: Impact too high, needs architectural redesign

   Return JSON:
   {
     "voter_id": "investigator-1",
     "risk_level": "HIGH|MEDIUM|LOW",
     "strategy_vote": "A|B|C|D",
     "reasoning": "Why this strategy is best",
     "specific_concerns": ["concern1", "concern2"],
     "mitigation_steps": ["step1", "step2"]
   }
   """)

   # Spawn investigators 2 and 3 with same prompt but different voter_id
   ```

2. **Collect votes and determine consensus:**

   ```
   votes = [vote1, vote2, vote3]

   # Count strategy votes
   strategy_counts = count_votes(votes, 'strategy_vote')

   IF any strategy has >= 2 votes (2/3 consensus):
     winning_strategy = strategy_with_most_votes

     Update DISCOVERIES.md:
     ```markdown
     ## Impact Analysis Voting Results

     Transitive dependents: {count} (threshold exceeded)

     Votes:
     - Strategy A (BACKWARD_COMPATIBLE): {count} votes
     - Strategy B (COORDINATED_ROLLOUT): {count} votes
     - Strategy C (INCREMENTAL_MIGRATION): {count} votes
     - Strategy D (REDESIGN_NEEDED): {count} votes

     **CONSENSUS: {winning_strategy}** (2/3 threshold met)

     Rationale:
     {combined reasoning from winning voters}

     Mitigation Steps:
     {consolidated mitigation steps from all voters}

     Risk Level: {most common risk_level from votes}
     ```

     Proceed with winning_strategy approach

   ELSE (no 2/3 consensus):
     ESCALATE to user:
     ```
     🚨 DECISION NEEDED: Impact Analysis Voting - No Consensus

     Transitive Dependents: {count} files (high-impact change)

     Votes:
     - Investigator 1: Strategy {X} - {reasoning}
     - Investigator 2: Strategy {Y} - {reasoning}
     - Investigator 3: Strategy {Z} - {reasoning}

     No strategy achieved 2/3 consensus.

     Please choose:
     A. BACKWARD_COMPATIBLE: {brief description from votes}
     B. COORDINATED_ROLLOUT: {brief description from votes}
     C. INCREMENTAL_MIGRATION: {brief description from votes}
     D. REDESIGN_NEEDED: {brief description from votes}

     Your choice: [wait for user input]
     ```

     Document user decision in DISCOVERIES.md
   ```

3. **Update SPEC.md with strategy:**
   - Add winning strategy to "Implementation Approach" section
   - Add mitigation steps to "Known Gotchas" section

**Skip this gate if:**
- New project (no existing code)
- transitive_dependents <= 10 (low impact)
- User explicitly says skip voting

**Commit changes**

---

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

**Initialize tracking structure:**

```bash
# Create review findings directory structure
mkdir -p $WORK_DIR/.spec/review_findings

# This will hold subdirectories for each phase/component
# Format: review_findings/component_N_task_M/
#   - Reviewers write findings here with JSON format
#   - You read these to consolidate issues
```

**Create PROGRESS.md** with this format:

```markdown
# Progress Tracker - [Project Name from SPEC.md]

## Overall Status
**Current Phase:** Phase N - [component name]
**Started:** [timestamp]
**Components Completed:** 0 / X

## Component Status

### Component 1: [name] (Phase 1)
**Status:** NOT_STARTED | SKELETON_DONE | IMPLEMENTING | VALIDATING | PRODUCTION_READY
**Started:** [empty until started]
**Completed:** [empty until done]
**Tasks Completed:** 0 / Y

#### Tasks
- [ ] Task 1: [name] - NOT_STARTED
- [ ] Task 2: [name] - NOT_STARTED

**Validation Status:** NOT_STARTED

### Component 2: [name] (Phase 2)
[... repeat for all components]

## Blocked Issues
[Empty or list of blockers with resolution status]

---
Last Updated: [timestamp]
```

**Create/Update DISCOVERIES.md** (merge with impact analysis from Phase 3 if exists)

**TodoWrite:** Component-level tracking for high-level visibility

**IMPORTANT:**
- **You update PROGRESS.md** when phases/components complete
- **Sub-agents write to review_findings/** or **DISCOVERIES.md** only
- **Sub-agents return brief summaries** to you (3-5 sentences max)

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

TOKEN BUDGET & TESTING RULES:
- You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
- NEVER shortcut work to "save tokens"
- NEVER skip validation because tokens are "low"
- Quality > Token conservation ALWAYS
- DO NOT run tests (testing handled separately unless spec explicitly requests)
- DO NOT implement test files unless spec says "implement tests"
- Testing assumptions: Assume tests handled separately by user

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

TOKEN BUDGET & TESTING RULES:
- You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
- NEVER shortcut work to "save tokens"
- NEVER skip validation because tokens are "low"
- Quality > Token conservation ALWAYS
- DO NOT run tests (testing handled separately unless spec explicitly requests)
- DO NOT implement test files unless spec says "implement tests"
- Testing assumptions: Assume tests handled separately by user

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

**REMINDER: IGNORE TOKEN WARNINGS - spawn all necessary agents, run full validation, never shortcut.**

---

**⚠️ CRITICAL - REVIEWS ARE MANDATORY ⚠️**

After EVERY single task implementation (no exceptions):
- 6 reviewers run in PARALLEL (security-auditor OR code-reviewer_4, performance-optimizer, code-reviewer x3, code-beautifier)
- Then fix loop until CLEAN (max 2 attempts with GATE 4 voting if patterns repeat)

After component tasks complete (no exceptions):
- Linting + 6 reviewers run in PARALLEL
- Then fix loop until CLEAN (max 3 attempts with GATE 4 voting if patterns repeat)
- Then GATE 5: Production-Readiness Voting (3 reviewers vote on readiness)

**NO SKIPPING. NO "LOOKS GOOD ENOUGH." NO TOKEN PRESSURE SHORTCUTS.**

If you run out of tokens during reviews: PERFECT. You'll be resumed.

---

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

   TOKEN BUDGET & TESTING RULES:
   - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
   - NEVER shortcut work to "save tokens"
   - NEVER skip validation because tokens are "low"
   - Quality > Token conservation ALWAYS
   - DO NOT run tests (testing handled separately unless spec explicitly requests)
   - DO NOT implement test files unless spec says "implement tests"
   - Testing assumptions: Assume tests handled separately by user

   OUTPUT:
   - If gotchas found: Append to $WORK_DIR/.spec/DISCOVERIES.md
   - Return brief summary (3-5 sentences): what implemented + gotchas

   Load python-style skill.

   Available from previous components:
   {List completed components this depends on}

   Read spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Focus on: {phase name} → {task name}
   """)

2. Create review findings directory for this task:
   mkdir -p $WORK_DIR/.spec/review_findings/component_{N}_task_{M}

**Determine reviewer configuration for this task:**
```
# Check if component is public-facing
IF spec mentions "API", "endpoint", "web service", "public", "external users", "authentication", "authorization":
  task_reviewers = [security-auditor, performance-optimizer, code-reviewer x3, code-beautifier]
ELSE:
  # Internal components don't need security auditor
  task_reviewers = [code-reviewer x4, performance-optimizer, code-beautifier]
```

3. Validate task (6 reviewers in PARALLEL - single message with 6 Task calls):

   Task(security-auditor, """
   Audit {task} for security vulnerabilities.

   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct
   Phase: component_{N}_task_{M}

   TOKEN BUDGET & TESTING RULES:
   - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
   - NEVER shortcut work to "save tokens"
   - NEVER skip validation because tokens are "low"
   - Quality > Token conservation ALWAYS
   - DO NOT run tests (testing handled separately unless spec explicitly requests)
   - DO NOT implement test files unless spec says "implement tests"
   - Testing assumptions: Assume tests handled separately by user

   OUTPUT:
   1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_task_{M}/{task_name}_security-auditor.md
      Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

   Load vulnerability-triage skill.

   Review for: injection risks, auth bypasses, data exposure, crypto issues.
   """)

   Task(performance-optimizer, """
   Review {task} for performance issues.

   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct
   Phase: component_{N}_task_{M}

   TOKEN BUDGET & TESTING RULES:
   - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
   - NEVER shortcut work to "save tokens"
   - NEVER skip validation because tokens are "low"
   - Quality > Token conservation ALWAYS
   - DO NOT run tests (testing handled separately unless spec explicitly requests)
   - DO NOT implement test files unless spec says "implement tests"
   - Testing assumptions: Assume tests handled separately by user

   OUTPUT:
   1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_task_{M}/{task_name}_performance-optimizer.md
      Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

   Load mongodb-aggregation-optimization skill if MongoDB detected.

   Review for: N+1 queries, missing indexes, inefficient algorithms.
   """)

   Task(code-reviewer, """
   Review {task}: Code quality, logic correctness, standards compliance.

   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct
   Phase: component_{N}_task_{M}

   TOKEN BUDGET & TESTING RULES:
   - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
   - NEVER shortcut work to "save tokens"
   - NEVER skip validation because tokens are "low"
   - Quality > Token conservation ALWAYS
   - DO NOT run tests (testing handled separately unless spec explicitly requests)
   - DO NOT implement test files unless spec says "implement tests"
   - Testing assumptions: Assume tests handled separately by user

   OUTPUT:
   1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_task_{M}/{task_name}_code-reviewer_1.md
      Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

   Load python-style skill.

   Focus: cyclomatic complexity, error handling, code clarity, maintainability.
   """)

   Task(code-reviewer, """
   Review {task}: Edge cases, error handling, coupling.

   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct
   Phase: component_{N}_task_{M}

   TOKEN BUDGET & TESTING RULES:
   - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
   - NEVER shortcut work to "save tokens"
   - NEVER skip validation because tokens are "low"
   - Quality > Token conservation ALWAYS
   - DO NOT run tests (testing handled separately unless spec explicitly requests)
   - DO NOT implement test files unless spec says "implement tests"
   - Testing assumptions: Assume tests handled separately by user

   OUTPUT:
   1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_task_{M}/{task_name}_code-reviewer_2.md
      Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

   Focus: SRP violations, tight coupling, type hint coverage, error scenarios.
   """)

   Task(code-beautifier, """
   Review {task}: DRY violations, magic numbers, dead code.

   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct
   Phase: component_{N}_task_{M}

   TOKEN BUDGET & TESTING RULES:
   - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
   - NEVER shortcut work to "save tokens"
   - NEVER skip validation because tokens are "low"
   - Quality > Token conservation ALWAYS
   - DO NOT run tests (testing handled separately unless spec explicitly requests)
   - DO NOT implement test files unless spec says "implement tests"
   - Testing assumptions: Assume tests handled separately by user

   OUTPUT:
   1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_task_{M}/{task_name}_code-beautifier.md
      Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

   Focus: code duplication, hardcoded values, unused imports/variables.
   """)

   Task(code-reviewer, """
   Review {task}: Documentation, comments, naming.

   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct
   Phase: component_{N}_task_{M}

   TOKEN BUDGET & TESTING RULES:
   - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
   - NEVER shortcut work to "save tokens"
   - NEVER skip validation because tokens are "low"
   - Quality > Token conservation ALWAYS
   - DO NOT run tests (testing handled separately unless spec explicitly requests)
   - DO NOT implement test files unless spec says "implement tests"
   - Testing assumptions: Assume tests handled separately by user

   OUTPUT:
   1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_task_{M}/{task_name}_code-reviewer_3.md
      Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
   2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

   Focus: docstring coverage, comment quality, variable naming, function naming.
   """)

4. Consolidate review findings:
   - Read all .md files in review_findings/component_{N}_task_{M}/
   - Merge critical, important, minor issues from all 6 reviewers
   - Deduplicate across reviewers

5. Fix issues (if found) - WITH INTELLIGENT FAILURE PATTERN DETECTION AND VOTING:
   IF critical or important issues:
     # Track failure patterns across attempts
     failure_history = []

     LOOP (max 2 attempts):
       a. Task(fix-executor, """
          Fix task validation issues.

          Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
          Task: {task description}

          Issues from: $WORK_DIR/.spec/review_findings/component_{N}_task_{M}/*.md

          CRITICAL RULES (from agent-prompting skill):
          - Fix PROPERLY - no workarounds
          - Follow code standards: logging.getLogger, try/except only for connections
          - Max 2 attempts, then ESCALATE

          TOKEN BUDGET & TESTING RULES:
          - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
          - NEVER shortcut work to "save tokens"
          - NEVER skip validation because tokens are "low"
          - Quality > Token conservation ALWAYS
          - DO NOT run tests (testing handled separately unless spec explicitly requests)
          - DO NOT implement test files unless spec says "implement tests"
          - Testing assumptions: Assume tests handled separately by user

          OUTPUT:
          - Return brief summary (3-5 sentences): issues fixed, files modified
          - 2 reviewers will validate after you complete

          Load python-style skill.

          Agent will read spec and review findings automatically.
          """)

       b. MANDATORY: Re-run 2 code-reviewers in PARALLEL (FULL REVIEW, not just fix verification)

          Focus instructions:
          - Reviewer 1: Complete review as if first time - verify fixes PLUS check for new issues introduced
          - Reviewer 2: Complete review as if first time - catch anything missed before or new problems from fixes

          **This is NOT "check the fixes worked" - this is a FULL SECOND REVIEW with fresh eyes on the entire task.**

          - Same pattern as step 3 above
          - Write new findings to review_findings/component_{N}_task_{M}/{task_name}_code-reviewer_{N}_attempt_{attempt}.md
          - Return summaries

       c. Consolidate findings from new reviews

       d. failure_history.append(current_issues)

       e. IF clean: Break
          IF attempt >= 2:
            # CHECK FOR REPEATED ISSUE PATTERN
            IF same_issue_repeated(failure_history):
              # GATE 4: Fix Strategy Voting
              Trigger_Fix_Strategy_Voting()
            ELSE:
              # Different issues = making progress
              ESCALATE: "Multiple different issues after 2 attempts. Need human review."

6. Update PROGRESS.md:
   - Mark task complete
   - Update task status to COMPLETE
   - Update component's "Tasks Completed" count
   - Update timestamp

7. Commit changes for this task (pre-commit validation runs)

NEXT task...
```

---

#### GATE 4: Fix Strategy Voting (Task-by-Task Loop)

**Trigger:** IF same_issue_repeated(failure_history) after 2 fix attempts

**Goal:** Multi-agent consensus on best approach when same issue persists.

**Process:**

1. **Spawn 3 general-investigator agents in PARALLEL:**

   ```
   Task(general-investigator, """
   Analyze repeated fix failure and vote on best strategy.

   Component: {component_name}
   Task: {task_description}
   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md

   Failure History (2 attempts):
   Attempt 1: {failure_history[0]}
   Attempt 2: {failure_history[1]}

   Issue Classification:
   {classify_issue(failure_history)}

   The same issue has appeared in both fix attempts. Evaluate best strategy:

   STRATEGIES:
   - FIX_IN_PLACE: Issue is fixable with proper implementation, try different approach
   - REFACTOR: Architectural/design issue, needs refactoring (extract function, DI, etc.)
   - ESCALATE: Requires spec change or human decision (scope change, external dependency)

   Return JSON:
   {
     "voter_id": "investigator-1",
     "strategy_vote": "FIX_IN_PLACE|REFACTOR|ESCALATE",
     "reasoning": "Why this strategy is best for this specific issue",
     "issue_type": "circular_dependency|tight_coupling|complexity|type_error|other",
     "root_cause": "What's actually causing the repeated failure",
     "recommended_action": "Specific steps to resolve (if FIX_IN_PLACE or REFACTOR)",
     "spec_change_needed": "boolean - true if ESCALATE"
   }
   """)

   # Spawn investigators 2 and 3 with same prompt but different voter_id
   ```

2. **Collect votes and determine consensus:**

   ```
   votes = [vote1, vote2, vote3]

   # Count strategy votes
   strategy_counts = count_votes(votes, 'strategy_vote')

   IF any strategy has >= 2 votes (2/3 consensus):
     winning_strategy = strategy_with_most_votes

     Document in DISCOVERIES.md:
     ```markdown
     ## Fix Strategy Voting: {task_name}

     Issue: {issue_classification}
     Repeated after 2 fix attempts

     Votes:
     - FIX_IN_PLACE: {count} votes
     - REFACTOR: {count} votes
     - ESCALATE: {count} votes

     **CONSENSUS: {winning_strategy}** (2/3 threshold met)

     Root Cause: {consolidated root_cause from winning voters}
     Recommended Action: {consolidated recommended_action}
     ```

     IF winning_strategy == "FIX_IN_PLACE":
       Task(fix-executor, """
       Fix with alternative approach (attempt 3).

       Strategy from voting: {consolidated recommended_action}
       Root cause: {root_cause from votes}

       TOKEN BUDGET & TESTING RULES:
       - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
       - NEVER shortcut work to "save tokens"
       - NEVER skip validation because tokens are "low"
       - Quality > Token conservation ALWAYS
       - DO NOT run tests (testing handled separately unless spec explicitly requests)
       - DO NOT implement test files unless spec says "implement tests"
       - Testing assumptions: Assume tests handled separately by user

       [include all fix-executor standards]
       """)

       Re-run 2 reviewers
       IF still failing: ESCALATE with voting results

     ELIF winning_strategy == "REFACTOR":
       Task(fix-executor, """
       Refactor to resolve architectural issue.

       Refactoring approach: {consolidated recommended_action}
       Root cause: {root_cause from votes}

       TOKEN BUDGET & TESTING RULES:
       - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
       - NEVER shortcut work to "save tokens"
       - NEVER skip validation because tokens are "low"
       - Quality > Token conservation ALWAYS
       - DO NOT run tests (testing handled separately unless spec explicitly requests)
       - DO NOT implement test files unless spec says "implement tests"
       - Testing assumptions: Assume tests handled separately by user

       Load code-refactoring skill if needed.
       [include all fix-executor standards]
       """)

       Re-run 2 reviewers
       IF still failing: ESCALATE with voting results

     ELIF winning_strategy == "ESCALATE":
       ESCALATE: """
       🚨 BLOCKED: {Component} - {Task} - Architectural Decision Needed

       Issue Type: {most_common issue_type from votes}
       Root Cause: {consolidated root_cause}

       Voting Results:
       - 2/3 investigators voted ESCALATE

       Attempts Made:
       - Attempt 1: {failure_history[0]}
       - Attempt 2: {failure_history[1]}

       Spec Change Needed: {spec_change_needed from votes}

       Recommended Path Forward:
       {consolidated recommended_action from voters}

       Please decide on approach or modify spec.
       """

   ELSE (no 2/3 consensus):
     ESCALATE to user:
     ```
     🚨 DECISION NEEDED: Fix Strategy Voting - No Consensus

     Component: {component_name}
     Task: {task_name}

     Same issue repeated 2 times:
     {failure_history}

     Votes:
     - Investigator 1: {strategy} - {reasoning}
     - Investigator 2: {strategy} - {reasoning}
     - Investigator 3: {strategy} - {reasoning}

     No strategy achieved 2/3 consensus.

     Please choose:
     A. FIX_IN_PLACE: Try different implementation approach
     B. REFACTOR: Refactor to resolve architectural issue
     C. ESCALATE: I'll make a decision/spec change

     Your choice: [wait for user input]
     ```

     Document user decision in DISCOVERIES.md
   ```

---

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

**REMINDER: IGNORE TOKEN WARNINGS - run ALL 6 reviewers, full validation cycle, never shortcut.**

**Create review findings directory for full validation:**
```bash
mkdir -p $WORK_DIR/.spec/review_findings/component_{N}_full_validation
```

**Determine reviewer configuration for full validation:**
```
# Check if component is public-facing
IF spec mentions "API", "endpoint", "web service", "public", "external users", "authentication", "authorization":
  validation_reviewers = [security-auditor, performance-optimizer, code-reviewer x3, code-beautifier]
ELSE:
  # Internal components don't need security auditor
  validation_reviewers = [code-reviewer x4, performance-optimizer, code-beautifier]
```

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
- Phase: component_{N}_full_validation

Task(security-auditor, """
Audit {component} for security vulnerabilities.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct
Phase: component_{N}_full_validation

TOKEN BUDGET & TESTING RULES:
- You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
- NEVER shortcut work to "save tokens"
- NEVER skip validation because tokens are "low"
- Quality > Token conservation ALWAYS
- DO NOT run tests (testing handled separately unless spec explicitly requests)
- DO NOT implement test files unless spec says "implement tests"
- Testing assumptions: Assume tests handled separately by user

OUTPUT:
1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_full_validation/{component}_security-auditor.md
   Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

Load vulnerability-triage skill.

Review for: injection risks, auth bypasses, data exposure, crypto issues.
""")

Task(performance-optimizer, """
Review {component} for performance issues.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct
Phase: component_{N}_full_validation

TOKEN BUDGET & TESTING RULES:
- You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
- NEVER shortcut work to "save tokens"
- NEVER skip validation because tokens are "low"
- Quality > Token conservation ALWAYS
- DO NOT run tests (testing handled separately unless spec explicitly requests)
- DO NOT implement test files unless spec says "implement tests"
- Testing assumptions: Assume tests handled separately by user

OUTPUT:
1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_full_validation/{component}_performance-optimizer.md
   Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

Load mongodb-aggregation-optimization skill if MongoDB detected.

Review for: N+1 queries, missing indexes, inefficient algorithms, memory leaks.
""")

Task(code-reviewer, """
Review {component}: complexity, errors, clarity.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct
Phase: component_{N}_full_validation

TOKEN BUDGET & TESTING RULES:
- You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
- NEVER shortcut work to "save tokens"
- NEVER skip validation because tokens are "low"
- Quality > Token conservation ALWAYS
- DO NOT run tests (testing handled separately unless spec explicitly requests)
- DO NOT implement test files unless spec says "implement tests"
- Testing assumptions: Assume tests handled separately by user

OUTPUT:
1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_full_validation/{component}_code-reviewer_1.md
   Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

Load python-style skill.

Focus: cyclomatic complexity, error handling, code clarity, maintainability.
""")

Task(code-reviewer, """
Review {component}: responsibility, coupling, type safety.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct
Phase: component_{N}_full_validation

TOKEN BUDGET & TESTING RULES:
- You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
- NEVER shortcut work to "save tokens"
- NEVER skip validation because tokens are "low"
- Quality > Token conservation ALWAYS
- DO NOT run tests (testing handled separately unless spec explicitly requests)
- DO NOT implement test files unless spec says "implement tests"
- Testing assumptions: Assume tests handled separately by user

OUTPUT:
1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_full_validation/{component}_code-reviewer_2.md
   Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

Focus: SRP violations, tight coupling, type hint coverage, interface clarity.
""")

Task(code-beautifier, """
Review {component}: DRY violations, magic numbers, dead code.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct
Phase: component_{N}_full_validation

TOKEN BUDGET & TESTING RULES:
- You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
- NEVER shortcut work to "save tokens"
- NEVER skip validation because tokens are "low"
- Quality > Token conservation ALWAYS
- DO NOT run tests (testing handled separately unless spec explicitly requests)
- DO NOT implement test files unless spec says "implement tests"
- Testing assumptions: Assume tests handled separately by user

OUTPUT:
1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_full_validation/{component}_code-beautifier.md
   Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

Focus: code duplication, hardcoded values, unused imports/variables, formatting.
""")

Task(code-reviewer, """
Review {component}: documentation, comments, naming.

Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
Workflow: conduct
Phase: component_{N}_full_validation

TOKEN BUDGET & TESTING RULES:
- You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
- NEVER shortcut work to "save tokens"
- NEVER skip validation because tokens are "low"
- Quality > Token conservation ALWAYS
- DO NOT run tests (testing handled separately unless spec explicitly requests)
- DO NOT implement test files unless spec says "implement tests"
- Testing assumptions: Assume tests handled separately by user

OUTPUT:
1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_full_validation/{component}_code-reviewer_3.md
   Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

Focus: docstring coverage, comment quality, variable naming, function naming.
""")
```

**Consolidate findings:**
- Read all .md files in review_findings/component_{N}_full_validation/
- Merge linting errors + 6 reviewer findings
- Consolidate critical + important + minor
- Deduplicate issues

**Fix ALL issues (max 3 attempts with pattern detection and voting):**
```
failure_history = []

LOOP until validation clean:
  1. Spawn fix-executor:
     Task(fix-executor, """
     Fix all validation issues for {component}.

     Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
     Workflow: conduct

     Issues from: $WORK_DIR/.spec/review_findings/component_{N}_full_validation/*.md

     CRITICAL RULES (from agent-prompting skill):
     - Fix PROPERLY - no workarounds
     - NO # noqa / # type: ignore as "fixes"
     - If architectural issue: ESCALATE immediately
     - Max 3 attempts

     TOKEN BUDGET & TESTING RULES:
     - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
     - NEVER shortcut work to "save tokens"
     - NEVER skip validation because tokens are "low"
     - Quality > Token conservation ALWAYS
     - DO NOT run tests (testing handled separately unless spec explicitly requests)
     - DO NOT implement test files unless spec says "implement tests"
     - Testing assumptions: Assume tests handled separately by user

     OUTPUT:
     - Return brief summary (3-5 sentences): issues fixed, files modified
     - 2 reviewers will validate after you complete

     Load python-style skill.
     Load code-refactoring skill if complexity issues.

     Agent will read spec and review findings automatically.
     """)

  2. MANDATORY: Re-run 2 code-reviewers in PARALLEL (FULL REVIEW - NOT full 6, but NOT just fix verification either!)

     Create review findings directory for this attempt:
     mkdir -p $WORK_DIR/.spec/review_findings/component_{N}_full_validation_attempt_{attempt}

     Focus for both reviewers:
     - Do COMPLETE review as if first time
     - Verify all previous issues were fixed correctly
     - Look for new issues introduced by fixes
     - Catch anything that was missed in previous validation round

     **This is NOT just "check fixes worked" - this is a FULL REVIEW CYCLE with fresh eyes on the component.**

     Task(code-reviewer, """
     Review fixes for {component}.

     Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
     Workflow: conduct
     Phase: component_{N}_full_validation_attempt_{attempt}

     Focus: COMPLETE review as if first time - verify previous fixes AND check for new issues introduced

     OUTPUT:
     1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_full_validation_attempt_{attempt}/{component}_code-reviewer_1.md
        Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
     2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND

     Load python-style skill.
     """)

     Task(code-reviewer, """
     Review fixes for {component}.

     Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
     Workflow: conduct
     Phase: component_{N}_full_validation_attempt_{attempt}

     Focus: COMPLETE review as if first time - catch anything missed in previous round AND new problems from fixes

     OUTPUT:
     1. Write findings to: $WORK_DIR/.spec/review_findings/component_{N}_full_validation_attempt_{attempt}/{component}_code-reviewer_2.md
        Format (JSON): {"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
     2. Return summary (2-3 sentences): Critical: X, Important: Y, Overall: CLEAN/ISSUES_FOUND
     """)

  3. Consolidate findings from 2 reviewers

  4. failure_history.append(current_issues)

  5. IF clean: Break
     IF new issues AND attempt < 3: Continue loop
     IF attempt >= 3:
       # CHECK FOR REPEATED ISSUE PATTERN
       IF same_issues_repeated(failure_history):
         # GATE 4: Fix Strategy Voting (Full Validation Loop)
         Trigger_Fix_Strategy_Voting()
       ELSE:
         ESCALATE: "Different issues across 3 attempts, need review"

6. Update PROGRESS.md:
   - Update component validation status to COMPLETE (if clean)
   - Update component status to VALIDATING → READY_FOR_GATE5
   - Update timestamp
```

---

#### GATE 4: Fix Strategy Voting (Full Validation Loop)

**Trigger:** IF same_issues_repeated(failure_history) after 3 fix attempts

**Process:** Same as GATE 4 in Task-by-Task loop, but applied to full component validation issues.

**Adjustments:**
- Context: "Full component validation" instead of specific task
- Issues: Consolidated issues from linting + 6 reviewers
- Scope: May involve multiple functions/classes across component

---

**Validation complete criteria:**
- ✅ Zero linting errors
- ✅ All critical issues fixed
- ✅ All important issues fixed
- ✅ All minor issues fixed (or documented why skipped)

**Commit changes** (pre-commit validation runs)

---

#### GATE 5: Component Production-Readiness Voting

**Trigger:** After Step 3 (Full Component Validation) passes - ALL fixes applied

**Goal:** Multi-agent consensus on whether component is truly production-ready.

**Process:**

1. **Spawn 3 code-reviewer agents in PARALLEL:**

   ```
   Task(code-reviewer, """
   Vote on production readiness for {component}.

   Component: {component_name}
   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct

   Component has passed:
   - Task-by-task implementation with 2 reviewers per task
   - Full component validation (linting + 6 reviewers)
   - All critical/important/minor fixes applied

   Evaluate if component is TRULY production-ready:

   VOTE OPTIONS:
   - PRODUCTION_READY: Code is solid, well-tested logic, maintainable, follows standards
   - NEEDS_WORK: Passes validation but has concerns (code smells, maintainability issues)
   - RISKY: Technical debt, unclear logic, or fragile implementation despite passing checks

   Return JSON:
   {
     "voter_id": "reviewer-1",
     "vote": "PRODUCTION_READY|NEEDS_WORK|RISKY",
     "reasoning": "Why this vote",
     "concerns": ["concern1", "concern2"] (if NEEDS_WORK or RISKY),
     "blocking_issues": ["issue1"] (if RISKY - must fix before production),
     "nice_to_haves": ["improvement1"] (if NEEDS_WORK - recommended but not blocking)
   }

   Load python-style skill.

   Read component: {component_file}
   Read spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   """)

   # Spawn reviewers 2 and 3 with same prompt but different voter_id
   ```

2. **Collect votes and determine consensus:**

   ```
   votes = [vote1, vote2, vote3]

   # Count votes
   vote_counts = count_votes(votes, 'vote')

   IF any vote has >= 2 (2/3 consensus):
     winning_vote = vote_with_most_votes

     Document in DISCOVERIES.md:
     ```markdown
     ## Production Readiness Voting: {component_name}

     Votes:
     - PRODUCTION_READY: {count} votes
     - NEEDS_WORK: {count} votes
     - RISKY: {count} votes

     **CONSENSUS: {winning_vote}** (2/3 threshold met)

     Reasoning: {consolidated reasoning from winning voters}
     ```

     IF winning_vote == "PRODUCTION_READY":
       # Great! Component approved
       Update PROGRESS.md: Component PRODUCTION_READY
       Proceed to Step 4 (Enhance Future Phase Specs)

     ELIF winning_vote == "NEEDS_WORK":
       # Non-blocking concerns
       Document nice-to-haves in DISCOVERIES.md:
       ```markdown
       ### Nice-to-Have Improvements
       {consolidated nice_to_haves from voters}
       ```

       Update PROGRESS.md: Component PRODUCTION_READY (with recommendations)
       Proceed to Step 4 (Enhance Future Phase Specs)

     ELIF winning_vote == "RISKY":
       # Blocking issues
       blocking = consolidate_blocking_issues(votes)

       Task(fix-executor, """
       Fix blocking production-readiness issues.

       Component: {component_name}
       Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md

       Blocking Issues (2/3 reviewers flagged as RISKY):
       {blocking_issues}

       These must be fixed before production deployment.

       TOKEN BUDGET & TESTING RULES:
       - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
       - NEVER shortcut work to "save tokens"
       - NEVER skip validation because tokens are "low"
       - Quality > Token conservation ALWAYS
       - DO NOT run tests (testing handled separately unless spec explicitly requests)
       - DO NOT implement test files unless spec says "implement tests"
       - Testing assumptions: Assume tests handled separately by user

       Load python-style skill.
       Load code-refactoring skill if needed.

       [include all fix-executor standards]
       """)

       # Re-run GATE 5 voting after fixes
       Re_trigger_Production_Readiness_Voting()

   ELSE (no 2/3 consensus):
     ESCALATE to user:
     ```
     🚨 DECISION NEEDED: Production Readiness Voting - No Consensus

     Component: {component_name}

     All validation passed, but reviewers disagree on production readiness:

     Votes:
     - Reviewer 1: {vote} - {reasoning}
       Concerns: {concerns}
     - Reviewer 2: {vote} - {reasoning}
       Concerns: {concerns}
     - Reviewer 3: {vote} - {reasoning}
       Concerns: {concerns}

     No vote achieved 2/3 consensus.

     Please decide:
     A. PRODUCTION_READY: Deploy as-is
     B. NEEDS_WORK: Note concerns, deploy anyway
     C. RISKY: Fix blocking issues first

     Your choice: [wait for user input]
     ```

     Document user decision in DISCOVERIES.md
   ```

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
- ✅ Production-readiness voting approved (GATE 5)
- ✅ Discoveries documented
- ✅ Future phase specs enhanced

**Summary:**
```
✅ Component {N}: {component_name} complete!

Files: X created, Y modified
Tasks: Z completed
Quality: All validation passed
Production Readiness: {PRODUCTION_READY|PRODUCTION_READY with recommendations}
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

---

#### GATE 7: Documentation Quality Voting

**Trigger:** After documentation-reviewer fixes applied (if any)

**Goal:** Multi-agent consensus on documentation production-readiness.

**Process:**

1. **Spawn 3 general-builder agents in PARALLEL:**

   ```
   Task(general-builder, """
   Vote on documentation quality and production-readiness.

   Working directory: $WORK_DIR
   Spec: $WORK_DIR/.spec/SPEC.md
   Workflow: conduct

   Documentation has been:
   - Validated by documentation-reviewer
   - Fixed for all CRITICAL/IMPORTANT issues
   - Enhanced with .spec/DISCOVERIES.md learnings

   Evaluate if documentation is TRULY production-ready:

   VOTE OPTIONS:
   - PRODUCTION_READY: Accurate, complete, clear, maintainable
   - GAPS_EXIST: Validated but missing important context/examples/explanations
   - INACCURATE: Contains errors, outdated info, or contradictions despite fixes

   Return JSON:
   {
     "voter_id": "builder-1",
     "vote": "PRODUCTION_READY|GAPS_EXIST|INACCURATE",
     "reasoning": "Why this vote",
     "specific_gaps": ["gap1", "gap2"] (if GAPS_EXIST),
     "inaccuracies": ["error1", "error2"] (if INACCURATE),
     "examples_checked": ["example1", "example2"] (which examples you verified)
   }

   Load ai-documentation skill.

   Read all .md files in $WORK_DIR
   Read validation report: $WORK_DIR/.spec/DOC_VALIDATION_REPORT.json (if exists)
   """)

   # Spawn builders 2 and 3 with same prompt but different voter_id
   ```

2. **Collect votes and determine consensus:**

   ```
   votes = [vote1, vote2, vote3]

   # Count votes
   vote_counts = count_votes(votes, 'vote')

   IF any vote has >= 2 (2/3 consensus):
     winning_vote = vote_with_most_votes

     Document in DISCOVERIES.md:
     ```markdown
     ## Documentation Quality Voting

     Votes:
     - PRODUCTION_READY: {count} votes
     - GAPS_EXIST: {count} votes
     - INACCURATE: {count} votes

     **CONSENSUS: {winning_vote}** (2/3 threshold met)

     Reasoning: {consolidated reasoning from winning voters}
     ```

     IF winning_vote == "PRODUCTION_READY":
       # Great! Docs approved
       Update PROGRESS.md: Documentation PRODUCTION_READY
       Proceed to Phase N+2 (Testing)

     ELIF winning_vote == "GAPS_EXIST":
       # Need to fill gaps
       gaps = consolidate_gaps(votes)

       Task(general-builder, """
       Fill documentation gaps.

       Working directory: $WORK_DIR
       Spec: $WORK_DIR/.spec/SPEC.md

       Gaps identified by 2/3 builders:
       {specific_gaps}

       Add missing context, examples, explanations.

       Load ai-documentation skill.

       [include all general-builder standards]
       """)

       # Re-run GATE 7 voting after gaps filled
       Re_trigger_Documentation_Quality_Voting()

     ELIF winning_vote == "INACCURATE":
       # Errors remain despite fixes
       inaccuracies = consolidate_inaccuracies(votes)

       Task(general-builder, """
       Fix documentation inaccuracies.

       Working directory: $WORK_DIR
       Spec: $WORK_DIR/.spec/SPEC.md

       Inaccuracies identified by 2/3 builders:
       {inaccuracies}

       These were missed by previous validation/fixes.

       Load ai-documentation skill.

       [include all general-builder standards]
       """)

       # Re-run GATE 7 voting after inaccuracies fixed
       Re_trigger_Documentation_Quality_Voting()

   ELSE (no 2/3 consensus):
     ESCALATE to user:
     ```
     🚨 DECISION NEEDED: Documentation Quality Voting - No Consensus

     Documentation validated and fixed, but builders disagree on quality:

     Votes:
     - Builder 1: {vote} - {reasoning}
       Issues: {specific_gaps or inaccuracies}
     - Builder 2: {vote} - {reasoning}
       Issues: {specific_gaps or inaccuracies}
     - Builder 3: {vote} - {reasoning}
       Issues: {specific_gaps or inaccuracies}

     No vote achieved 2/3 consensus.

     Please decide:
     A. PRODUCTION_READY: Docs are good enough
     B. GAPS_EXIST: Fill identified gaps
     C. INACCURATE: Fix identified errors

     Your choice: [wait for user input]
     ```

     Document user decision in DISCOVERIES.md
   ```

---

**Documentation validation complete criteria:**
- ✅ All .md files reviewed
- ✅ No CRITICAL or IMPORTANT issues remaining
- ✅ Documentation quality voting passed (GATE 7)
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

  TOKEN BUDGET & TESTING RULES:
  - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
  - NEVER shortcut work to "save tokens"
  - NEVER skip validation because tokens are "low"
  - Quality > Token conservation ALWAYS
  - DO NOT run tests (testing handled separately unless spec explicitly requests)
  - DO NOT implement test files unless spec says "implement tests"
  - Testing assumptions: Assume tests handled separately by user

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
       # Proceed to GATE 6
       Trigger_Test_Coverage_Adequacy_Voting()
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

       TOKEN BUDGET & TESTING RULES:
       - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
       - NEVER shortcut work to "save tokens"
       - NEVER skip validation because tokens are "low"
       - Quality > Token conservation ALWAYS
       - DO NOT run tests (testing handled separately unless spec explicitly requests)
       - DO NOT implement test files unless spec says "implement tests"
       - Testing assumptions: Assume tests handled separately by user

       Load python-style skill.

       Read spec: $WORK_DIR/.spec/SPEC.md
       """)

       Re-run tests

  4. IF attempt > 3: ESCALATE with failure details
```

---

#### GATE 6: Test Coverage Adequacy Voting

**Trigger:** After tests pass + coverage >= 95%

**Goal:** Multi-agent consensus on whether test coverage is truly adequate (not just meeting percentage threshold).

**Process:**

1. **Spawn 3 code-reviewer agents in PARALLEL:**

   ```
   Task(code-reviewer, """
   Vote on test coverage adequacy for {component}.

   Component: {component_name}
   Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md
   Workflow: conduct

   Tests PASS with {coverage_percentage}% coverage (>= 95% threshold).

   Evaluate if tests are TRULY adequate:

   VOTE OPTIONS:
   - ADEQUATE: Coverage meaningful, tests verify behavior, edge cases covered
   - NEEDS_MORE_TESTS: Percentage met but missing critical scenarios/edge cases
   - WEAK_TESTS: Tests exist but don't verify behavior properly (trivial assertions, poor mocking)

   Return JSON:
   {
     "voter_id": "reviewer-1",
     "vote": "ADEQUATE|NEEDS_MORE_TESTS|WEAK_TESTS",
     "reasoning": "Why this vote",
     "missing_scenarios": ["scenario1", "scenario2"] (if NEEDS_MORE_TESTS),
     "weak_tests": ["test1", "test2"] (if WEAK_TESTS - which tests are weak and why),
     "edge_cases_checked": ["case1", "case2"] (which edge cases you verified are tested)
   }

   Load testing-standards skill.

   Read production code: {component_file}
   Read tests: tests/unit/test_{component}.py
   Read coverage report: {coverage_output}
   """)

   # Spawn reviewers 2 and 3 with same prompt but different voter_id
   ```

2. **Collect votes and determine consensus:**

   ```
   votes = [vote1, vote2, vote3]

   # Count votes
   vote_counts = count_votes(votes, 'vote')

   IF any vote has >= 2 (2/3 consensus):
     winning_vote = vote_with_most_votes

     Document in DISCOVERIES.md:
     ```markdown
     ## Test Coverage Adequacy Voting: {component_name}

     Coverage: {coverage_percentage}% (>= 95%)

     Votes:
     - ADEQUATE: {count} votes
     - NEEDS_MORE_TESTS: {count} votes
     - WEAK_TESTS: {count} votes

     **CONSENSUS: {winning_vote}** (2/3 threshold met)

     Reasoning: {consolidated reasoning from winning voters}
     ```

     IF winning_vote == "ADEQUATE":
       # Great! Tests approved
       Update PROGRESS.md: Component tests ADEQUATE
       Proceed to next component or integration testing

     ELIF winning_vote == "NEEDS_MORE_TESTS":
       # Missing scenarios
       missing = consolidate_missing_scenarios(votes)

       Task(test-implementer, """
       Add missing test scenarios.

       Component: {component_name}
       Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md

       Missing scenarios (identified by 2/3 reviewers):
       {missing_scenarios}

       Add tests for these scenarios, maintain 95%+ coverage.

       TOKEN BUDGET & TESTING RULES:
       - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
       - NEVER shortcut work to "save tokens"
       - NEVER skip validation because tokens are "low"
       - Quality > Token conservation ALWAYS
       - DO NOT run tests (testing handled separately unless spec explicitly requests)
       - DO NOT implement test files unless spec says "implement tests"
       - Testing assumptions: Assume tests handled separately by user

       Load testing-standards skill.

       [include all test-implementer standards]
       """)

       Run tests again
       # Re-run GATE 6 voting after new tests added
       Re_trigger_Test_Coverage_Adequacy_Voting()

     ELIF winning_vote == "WEAK_TESTS":
       # Tests don't verify behavior properly
       weak = consolidate_weak_tests(votes)

       Task(test-implementer, """
       Strengthen weak tests.

       Component: {component_name}
       Spec: $WORK_DIR/.spec/SPEC_{N}_{component}.md

       Weak tests (identified by 2/3 reviewers):
       {weak_tests}

       Improve assertions, mocking, behavior verification.

       TOKEN BUDGET & TESTING RULES:
       - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
       - NEVER shortcut work to "save tokens"
       - NEVER skip validation because tokens are "low"
       - Quality > Token conservation ALWAYS
       - DO NOT run tests (testing handled separately unless spec explicitly requests)
       - DO NOT implement test files unless spec says "implement tests"
       - Testing assumptions: Assume tests handled separately by user

       Load testing-standards skill.

       [include all test-implementer standards]
       """)

       Run tests again
       # Re-run GATE 6 voting after tests strengthened
       Re_trigger_Test_Coverage_Adequacy_Voting()

   ELSE (no 2/3 consensus):
     ESCALATE to user:
     ```
     🚨 DECISION NEEDED: Test Coverage Adequacy Voting - No Consensus

     Component: {component_name}
     Coverage: {coverage_percentage}% (passes 95% threshold)

     Reviewers disagree on test adequacy:

     Votes:
     - Reviewer 1: {vote} - {reasoning}
       Issues: {missing_scenarios or weak_tests}
     - Reviewer 2: {vote} - {reasoning}
       Issues: {missing_scenarios or weak_tests}
     - Reviewer 3: {vote} - {reasoning}
       Issues: {missing_scenarios or weak_tests}

     No vote achieved 2/3 consensus.

     Please decide:
     A. ADEQUATE: Tests are good enough
     B. NEEDS_MORE_TESTS: Add missing scenarios
     C. WEAK_TESTS: Strengthen test quality

     Your choice: [wait for user input]
     ```

     Document user decision in DISCOVERIES.md
   ```

---

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

TOKEN BUDGET & TESTING RULES:
- You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
- NEVER shortcut work to "save tokens"
- NEVER skip validation because tokens are "low"
- Quality > Token conservation ALWAYS
- DO NOT run tests (testing handled separately unless spec explicitly requests)
- DO NOT implement test files unless spec says "implement tests"
- Testing assumptions: Assume tests handled separately by user

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

       TOKEN BUDGET & TESTING RULES:
       - You have 200K tokens - running out is EXPECTED and FINE (you'll be resumed)
       - NEVER shortcut work to "save tokens"
       - NEVER skip validation because tokens are "low"
       - Quality > Token conservation ALWAYS
       - DO NOT run tests (testing handled separately unless spec explicitly requests)
       - DO NOT implement test files unless spec says "implement tests"
       - Testing assumptions: Assume tests handled separately by user

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
- Voting gate reaches no consensus and requires user decision

**Format:**
```
🚨 BLOCKED: [Component/Phase] - [Issue]

Issue: [description]
Attempts: [what tried]
Pattern Detected: [if applicable - repeated failure analysis]
Voting Results: [if applicable - gate voting breakdown]
Need: [specific question]
Options: [A, B, C with implications]
Recommendation: [your suggestion]
```

---

## Key Rules

**DO:**
- Require .spec/SPEC.md
- Run change impact analysis (Phase 3)
- Run GATE 3 (Impact Analysis Voting) if transitive_dependents > 10
- Verify dependencies match reality (Phase 4)
- Batch independent tasks for parallel execution
- Detect intelligent failure patterns in fix loops
- Run GATE 4 (Fix Strategy Voting) when same issue repeats
- Generate SPEC_N_component.md files if not exist
- Execute per-component: Skeleton (sequential) → Task-by-Task Impl (2 reviewers per task) → Full Validation (6 reviewers)
- Run GATE 5 (Component Production-Readiness Voting) after full validation passes
- Update PROGRESS.md + DISCOVERIES.md throughout
- Parallelize: reviewers, independent tasks, independent component tests, voting gates
- Enhance future phase specs with discoveries
- Documentation phase BEFORE testing
- Run GATE 7 (Documentation Quality Voting) after doc fixes
- Testing ONLY if user requested
- Run GATE 6 (Test Coverage Adequacy Voting) after tests pass with 95%+ coverage
- Archive .spec/ files after completion
- Commit after major steps (with pre-commit validation)

**DON'T:**
- Proceed without SPEC.md
- Skip dependency verification (Phase 4)
- Skip per-task validation (2 reviewers required)
- Skip voting gates when triggered
- Move to next component with failing validation
- Run tests unless user requested
- Let sub-agents spawn sub-agents
- Skip documentation validation before cleanup
- Delete .spec/ files before merging learnings to permanent docs
- Retry blindly without analyzing failure patterns

---

**You are the conductor. Analyze impact with voting when high-risk, verify dependencies, batch parallel work, detect patterns, execute incrementally with validation at each step, use voting gates for critical decisions, deliver working system.**
