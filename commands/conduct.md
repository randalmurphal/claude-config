---
name: conduct
description: Orchestrate complex development tasks using orchestration MCP - BUILD what the user requests with REAL validation
---

# /conduct - Orchestrated Development with MCP

**WHAT THIS IS:** Multi-agent orchestration with MCP utilities for state/git/validation.

**WHAT THIS ISN'T:** MCP doesn't orchestrate. You do. MCP just provides tools.

## Core Principle

**MCP = Dumb Utilities**
- Run pytest → return JSON
- Create checkpoint → git commit
- Analyze dependencies → return graph
- Store decision → call PRISM HTTP

**Claude (You) = Smart Orchestrator**
- Spawn agents with context
- Interpret validation results
- Combine multi-agent findings
- Make strategic decisions

## When to Use /conduct (vs Simple Agents)

**/conduct is for COMPLEX multi-file tasks** requiring orchestration:
- 5+ files to implement
- Multiple phases (skeleton → implementation → validation)
- Need dependency analysis, checkpoints, rollback
- Architecture decisions to document

**For SIMPLE tasks, use agents directly (no orchestration overhead):**
- **investigator** - Understand >3 files, find information
- **spike-tester** - Validate assumptions before committing
- **quick-builder** - Simple 1-3 file features

**Example decisions:**
- "Add JWT verification" (3 files, straightforward) → `quick-builder`
- "Implement auth system" (10+ files, multiple modules) → `/conduct`
- "How does auth work?" (investigation) → `investigator`
- "Can we use library X?" (validation) → `spike-tester`

If you're unsure: **use simple agents first**. If complexity grows, escalate to /conduct.

## The Validation-Driven Workflow

**VALIDATION IS EVERYTHING.** This is where quality happens. Be thorough.

### Phase Pattern

```
1. IMPLEMENT
   - Spawn implementation agents (skeleton + implementation)
   - Build working code

2. VALIDATE (MOST CRITICAL)
   a. MCP validate_phase → Get facts (tests, lint, imports, complexity)
   b. If failed → Fix → Retry (up to 3 attempts)
   c. If passed → Spawn validation agents IN PARALLEL
   d. Combine findings → Prioritize issues
   e. Fix critical issues → Re-validate
   f. Repeat until clean OR blocked

3. CHECKPOINT
   - create_checkpoint after validation passes

4. COMPLETE
   - complete_task to promote memories to PRISM
```

## Comprehensive Validation Pattern

**DO NOT checkpoint until ALL validation passes.**

### Step 1: MCP Validation (Facts)

```python
result = validate_phase(
    task_id=task_id,
    working_directory="./",
    validation_type="full",
    check_complexity=True,  # Optional: check code complexity
    max_complexity=10
)

if not result["passed"]:
    # FIX-VALIDATE LOOP (up to 3 attempts)
    for attempt in range(1, 4):
        analyze_issues(result["issues"])
        fix_issues()  # Directly or spawn fix-executor agent

        result = validate_phase(task_id, "./", "full", check_complexity=True)
        if result["passed"]:
            break

        if attempt == 3:
            # Escalate to user after 3 failed attempts
            report_to_user("Blocked: Cannot fix validation issues", result["issues"])
            return
```

### Step 2: Multi-Agent Code Review (Judgment)

**Spawn 4 specialized agents IN PARALLEL (send ONE message with all Task calls):**

```python
# Spawn all 4 agents in single message
Task(security-auditor, "Review for security vulnerabilities and attack vectors")
Task(performance-optimizer, "Review for performance bottlenecks and scalability")
Task(code-reviewer, "Review for maintainability, clarity, and edge cases")
Task(code-beautifier, "Review code style, DRY violations, and naming")
```

**Why 4 agents?**
- Security: Catches vulnerabilities (SQL injection, XSS, auth flaws)
- Performance: Catches inefficiencies (N+1 queries, memory leaks)
- Maintainability: Catches complexity (nested logic, unclear code)
- Style: Catches DRY violations (duplication, bad names)

### Step 3: Synthesize Findings

```python
# Combine all 4 reports
security_issues = agent1_report
performance_issues = agent2_report
maintainability_issues = agent3_report
style_issues = agent4_report

# Prioritize (security > performance > maintainability > style)
critical_issues = filter_critical(all_issues)
important_issues = filter_important(all_issues)
nice_to_have = filter_nice_to_have(all_issues)
```

### Step 4: Fix-Validate Loop

```python
# Fix critical and important issues
if critical_issues or important_issues:
    fix_issues(critical_issues + important_issues)

    # Re-run MCP validation
    result = validate_phase(task_id, "./", "full", check_complexity=True)

    if not result["passed"]:
        # Fix validation failures, retry up to 3 times
        # (same fix-validate loop as Step 1)
        ...

    # Re-run agent reviews on fixed code
    # Spawn same 4 agents to verify fixes didn't break anything
    ...
```

### Step 5: Checkpoint When Clean

```python
# Only checkpoint when:
# 1. MCP validate_phase passes
# 2. No critical issues from code review agents
# 3. Important issues addressed

checkpoint_id = create_checkpoint(task_id, "implementation", "./")
```

## Available MCP Tools

### Tier 0: State (Use Always)
- **start_task**(description, working_dir) → task_id
- **get_task_state**(task_id) → current phase, completed phases
- **save_phase_result**(task_id, phase_name, result_data) → compresses progress
- **complete_task**(task_id, commit_changes) → cleanup + PRISM memory promotion

### Tier 1: Validation & Safety (Use Before Checkpoints)
- **validate_phase**(task_id, working_dir, validation_type, check_complexity, max_complexity) → runs pytest/ruff/imports/complexity, returns pass/fail
  - Complexity checking optional: Python (radon), Go (gocyclo), JS/TS (coming soon)
- **create_checkpoint**(task_id, phase, working_dir) → git commit
- **rollback_to_checkpoint**(task_id, checkpoint_id, working_dir) → git reset --hard
- **list_checkpoints**(task_id, working_dir) → all checkpoints with metadata

### Tier 2: Intelligence (Use for 5+ File Tasks)
- **analyze_dependencies**(task_id, components) → dependency graph, circular dep detection, build order
- **store_decision**(task_id, decision, reasoning, alternatives) → ADR to PRISM ANCHORS
- **query_similar_tasks**(task_id, query) → past work with gotchas

### Tier 3: Parallel Work (Use for 10+ Files)
- **create_worktree**(task_id, module_name, base_dir) → git worktree for isolation
- **cleanup_worktrees**(task_id, base_dir) → remove all worktrees
- **list_worktrees**(task_id, base_dir) → active worktrees

### Tier 5: Optimization (Use When Needed)
- **detect_duplicates**(task_id, working_dir) → semantic duplication detection

## Workflow Examples

### Small Task (1-3 Files)

```
1. start_task("Add logging", "./")
2. Do work directly or spawn implementation agents
3. validate_phase → fix until passes (up to 3 attempts)
4. Spawn 4 validation agents in parallel
5. Fix critical issues from agents
6. Re-validate
7. create_checkpoint
8. complete_task
```

### Medium Task (5-10 Files)

```
1. start_task("Implement auth", "./")
2. query_similar_tasks(task_id, "authentication patterns")
3. analyze_dependencies(task_id, {auth: [], jwt: [auth]})
4. store_decision(task_id, "Use JWT", "stateless auth", [...])
5. Spawn implementation agents
6. validate_phase → fix until passes (up to 3 attempts)
7. Spawn 4 validation agents in parallel
8. Combine findings, prioritize
9. Fix critical + important issues
10. Re-validate MCP + agents
11. create_checkpoint
12. complete_task
```

### Large Task (10+ Files, Parallel)

```
1. start_task("Refactor API layer", "./")
2. analyze_dependencies(task_id, {auth: [], cart: [auth], payment: [cart, auth]})
3. create_worktree for each module
4. Work on modules in parallel (dependency-aware)
5. validate_phase in each worktree → fix until passes
6. Spawn 4 validation agents per worktree
7. Fix issues in each worktree
8. Merge worktrees to main
9. validate_phase on merged code
10. detect_duplicates (check for redundancy across modules)
11. Spawn 4 validation agents on merged code
12. Fix final issues
13. Re-validate
14. create_checkpoint
15. cleanup_worktrees
16. complete_task
```

## Fix-Validate Loop Pattern

**CRITICAL: Don't give up easily. Retry validation up to 3 times.**

```python
MAX_ATTEMPTS = 3

for attempt in range(1, MAX_ATTEMPTS + 1):
    result = validate_phase(task_id, "./", "full", check_complexity=True)

    if result["passed"]:
        break  # Success!

    # Analyze what failed
    issues = result["issues"]
    test_failures = [i for i in issues if "Test failed" in i]
    lint_errors = [i for i in issues if "Lint:" in i]
    import_errors = [i for i in issues if "Import error" in i]
    complexity_warnings = [i for i in issues if "High complexity" in i]

    # Try to fix automatically
    if attempt < MAX_ATTEMPTS:
        # Spawn fix-executor or fix directly
        fix_validation_issues(issues)
        continue
    else:
        # After 3 attempts, escalate to user
        report_to_user(
            f"Cannot fix validation issues after {MAX_ATTEMPTS} attempts",
            issues
        )
        return  # Block further progression
```

## Escalation Pattern

**When to ask user for help:**
1. After 3 failed validation attempts
2. When code reviewers find critical security issues you can't fix
3. When architectural decisions are ambiguous
4. When tests require external dependencies you can't set up

**How to escalate:**
```
User, I'm blocked. Here's what I tried:

1. Implementation completed
2. Validation failed: [specific issues]
3. Attempted fixes:
   - Attempt 1: [what I did] → [still failed because...]
   - Attempt 2: [what I did] → [still failed because...]
   - Attempt 3: [what I did] → [still failed because...]

I need your help with: [specific question or decision]
```

## Multi-Agent Review Details

**Why 4 specialized agents?**
- **One agent has blind spots** - might miss performance issues while focusing on security
- **Different optimization goals** find different issues
- **Combine findings** for comprehensive review

**Perspectives:**
1. **security-auditor**: SQL injection, XSS, auth bypass, timing attacks, data leaks (Opus model, OWASP Top 10)
2. **performance-optimizer**: N+1 queries, memory leaks, inefficient algorithms, database indices (Opus model, profiling)
3. **code-reviewer**: Cyclomatic complexity, unclear naming, missing error handling, edge cases (maintainability focus)
4. **code-beautifier**: DRY violations, magic numbers, inconsistent formatting, unclear comments (style focus)

**How to spawn (IMPORTANT):**
```
Send ONE message with 4 Task calls:

Task(security-auditor, "Review for security: SQL injection, XSS, auth bypass, timing attacks")
Task(performance-optimizer, "Review for performance: N+1 queries, memory leaks, inefficiencies")
Task(code-reviewer, "Review for maintainability: complexity, naming, error handling, edge cases")
Task(code-beautifier, "Review style: DRY violations, magic numbers, formatting, comments")
```

**DON'T** spawn sequentially - parallel is faster.

**After agents return:**
- Read all 4 reports thoroughly
- Find common themes (if multiple agents flag something → critical)
- Prioritize: security > performance > maintainability > style
- Fix critical issues immediately
- Re-validate with MCP + re-run agents
- Checkpoint when clean

## Error Recovery

**Validation fails:**
```
validate_phase → {passed: false, issues: ["test_auth.py::test_login FAILED"]}
→ Analyze failure (why did test fail?)
→ Fix the issue (spawn fix-executor or fix directly)
→ validate_phase again → {passed: true}
→ Continue to agent review
```

**Agent review finds critical issue:**
```
Security agent: "Timing attack vulnerability in token comparison"
→ Fix the vulnerability immediately
→ validate_phase (ensure tests still pass)
→ Re-run security agent to verify fix
→ Continue to checkpoint
```

**Need to rollback:**
```
list_checkpoints(task_id) → see all checkpoints
rollback_to_checkpoint(task_id, checkpoint_id)
→ Git reset --hard to that point
→ Retry from checkpoint
```

## Decision Framework

**Use MCP tools when:**
- Need facts (test results, dependency graph, git operations)
- Need state management (task tracking, checkpointing)
- Need PRISM integration (ADRs, duplication detection)

**Use agents when:**
- Need judgment (is this code good?)
- Need multiple perspectives (spawn 4 reviewers)
- Need implementation (skeleton, code writing)
- Need fixing (fix-executor for validation failures)

**Example of mixing:**
```
validate_phase(task_id, "./")  # MCP: Get facts
→ Returns: tests passed, coverage 92%, no lint errors

Task(security-auditor, "Review for security")       # Agent: Get judgment
Task(performance-optimizer, "Review for performance")
Task(code-reviewer, "Review for maintainability")
Task(code-beautifier, "Review style")
→ Returns: 4 different perspectives on code quality

Combine MCP facts + agent judgment = complete picture
```

## Quick Start

```
You: "/conduct implement user authentication with JWT"

1. start_task("Implement JWT auth", "./")
2. query_similar_tasks(task_id, "JWT authentication")
3. analyze_dependencies(task_id, {auth: [], jwt: [auth]})
4. store_decision(task_id, "Use JWT for stateless auth", "...", alternatives)
5. Spawn implementation agents (skeleton-builder + implementation-executor)
6. validate_phase → fix until passes (up to 3 attempts)
7. Spawn 4 validation agents in parallel:
   - security-auditor (security)
   - performance-optimizer (performance)
   - code-reviewer (maintainability)
   - code-beautifier (style)
8. Combine findings, prioritize issues
9. Fix critical + important issues
10. Re-validate: validate_phase + re-run agents
11. create_checkpoint(task_id, "implementation", "./")
12. complete_task(task_id, true)
```

---

**Bottom Line:**

Validation is the most important phase. Be thorough:
1. MCP validate_phase for facts
2. 4 specialized agents for judgment
3. Fix-validate loop (retry up to 3x)
4. Only checkpoint when clean
5. Escalate to user if blocked after 3 attempts

Don't rush through validation. Quality happens here.
