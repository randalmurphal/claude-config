# [Project Name] - Agent-Executable Specification

**Generated:** [Date]
**For Agent Orchestrator Execution in /conduct**

---

## Mission

[One paragraph: What is this building and why?]

**Success Definition:** [Concrete end state - e.g., "System runs end-to-end: user logs in → ingests events → sees dashboard"]

---

## Orchestration Plan

### Execution Graph

```
Phase 1: [module] → Phase 2-3: [module_a || module_b || module_c] → Phase 4: [module_d]
```

**Legend:**
- `→` Sequential (must complete before next)
- `||` Parallel (can run simultaneously)

**Critical Path:** Phase 1 → Phase 2 → Phase 4 (longest sequential chain)

**Total Estimated Phases:** [N]
**Parallelizable Phases:** [N]
**Sequential Phases:** [N]

---

## Phase 1: [Phase Name]

**Modules:** [module_name]
**Depends on:** (none) OR (Phase N must complete first)
**Parallelizable:** No OR Yes (with Phase X, Phase Y)
**Working mode:** Direct (no worktree) OR Worktree (parallel with others)

### Tasks

- [ ] [Specific task 1 - e.g., "Create proto/events.proto with Event message"]
- [ ] [Specific task 2 - e.g., "Implement generate.sh that runs protoc"]
- [ ] [Specific task 3]

### Success Criteria (ALL must pass)

- [ ] Files exist: [exact file paths]
- [ ] Command `[exact command]` exits 0
- [ ] Command `[validation check]` produces expected output
- [ ] No TODO/FIXME comments in [module path]
- [ ] No import errors: `[import check command]`

### Validation Commands

Run these commands to validate this phase:

```bash
cd [working_directory]

# Test 1: [what this tests]
[exact command]

# Test 2: [what this tests]
[exact command]

# Test 3: [what this tests]
[exact command]
```

**All commands must exit 0. Any non-zero exit = phase failed.**

### References

**Specifications:**
- [Component contract: location in this file or external doc]
- [API contract: section to reference]
- [Data schema: where to find it]

**External dependencies:**
- [Library: version requirement]
- [Service: endpoint it will call]

### Gotchas

**Gotcha 1:** [What will break]
- **Symptom:** [Error message or behavior]
- **Cause:** [Why it breaks]
- **Prevention:** [How to avoid]
- **Recovery:** [Exact commands to fix]

**Gotcha 2:** [Next issue]
- **Symptom:** ...
- **Cause:** ...
- **Prevention:** ...
- **Recovery:** ...

### On Failure

**Retry Strategy:**
1. Get error output from validation commands
2. Launch fix-executor agent with error context
3. Re-run validation commands
4. If still fails: retry once more (max 2 retries)
5. If still fails: rollback to checkpoint [previous_phase], escalate to user

**Common Failures:**

| Error | Cause | Fix |
|-------|-------|-----|
| [Error pattern] | [Root cause] | [Command to fix] |
| [Error pattern] | [Root cause] | [Command to fix] |

---

## Phase 2-N: [Parallel Group Name]

**Execution Strategy:** Create worktrees for all modules, launch agents in parallel (ONE message, multiple Task calls), merge after all complete

### Merge Strategy (After All Modules Complete)

1. **Validate each module independently:**
   ```bash
   cd [module1_worktree] && [validation commands]
   cd [module2_worktree] && [validation commands]
   ```

2. **Use synthesis-architect to merge:**
   - Compare branches
   - Resolve conflicts intelligently (understand code)
   - Ensure integration points match

3. **Post-merge validation:**
   ```bash
   # Check imports resolve across modules
   [command to check cross-module imports]

   # Run integration smoke test
   [command to test modules communicate]
   ```

4. **Cleanup worktrees:**
   ```bash
   # Done by orchestrator via MCP
   cleanup_worktrees(task_id, base_dir)
   ```

5. **Create checkpoint:**
   ```bash
   # Done by orchestrator via MCP
   create_checkpoint(task_id, "phase2-N_complete", working_dir)
   ```

**Merge Validation Must Pass:**
- [ ] No merge conflicts remain
- [ ] All imports resolve
- [ ] Integration points match (e.g., gRPC contracts, API schemas)
- [ ] Smoke test passes: [exact command]

---

### Module: [module_a]

**Depends on:** Phase [N]
**Parallelizable:** Yes (with [module_b, module_c])
**Working mode:** Worktree

#### Tasks

- [ ] [Specific implementation task]
- [ ] [Another task]
- [ ] [Test implementation]

#### Success Criteria

- [ ] Command `cd [module_a] && [test command]` exits 0
- [ ] Files exist: [list exact files]
- [ ] No TODO/FIXME comments
- [ ] Linting passes: `[lint command]` exits 0

#### Validation Commands

```bash
cd [module_a]

# Unit tests
[test command with -v flag]

# Build check (if compiled language)
[build command]

# Import check
[command to validate imports]

# Lint check
[lint command]
```

#### References

**Contracts this module implements:**
- [Contract name: location of spec]

**Contracts this module depends on:**
- [Contract name: where it's defined - may be in another module or Phase N output]

**Configuration:**
- [Config file: location]
- [Environment variables needed]

#### Gotchas

[Same format as Phase 1 gotchas]

#### On Failure

[Same format as Phase 1 failure handling]

---

### Module: [module_b]

[Same structure as module_a]

---

### Module: [module_c]

[Same structure as module_a]

---

## Phase [N]: [Final Phase Name]

[Same structure as Phase 1]

---

## Quality Gates

### After Each Phase

Run these commands before proceeding:

```bash
# Validation commands from phase
[commands from phase's Validation Commands section]

# Create checkpoint
# (orchestrator does this via MCP after validation passes)
```

### Before Merging Worktrees

```bash
# Each module's tests pass independently
cd [worktree1] && [test commands]
cd [worktree2] && [test commands]

# No uncommitted changes
git status  # Should be clean in each worktree
```

### Before Final Completion

**All must be true:**
- [ ] All phases executed in order
- [ ] All checkpoints created
- [ ] Integration tests pass: `[integration test command]`
- [ ] System runs end-to-end: `[e2e test command]`
- [ ] No TODO/FIXME in codebase: `grep -r "TODO\|FIXME" [src_dirs]` returns empty
- [ ] All documentation complete: `[list required docs]`
- [ ] Linting passes across entire codebase: `[lint command]`

**Final Validation Command:**
```bash
# Run complete system validation
[command that proves entire system works]

# Example for microservices:
docker-compose up -d
sleep 10
curl localhost:8000/health | grep "ok"
curl localhost:50051/health | grep "ok"
curl localhost:3000 | grep "<!DOCTYPE html>"
docker-compose down
```

---

## Failure Recovery

### Rollback Strategy

**If phase fails after 2 retries:**
```bash
# Orchestrator executes:
rollback_to_checkpoint(task_id, last_checkpoint_id, working_dir)

# System state returns to last successful phase
# Agent can investigate or escalate to user
```

**If merge fails:**
```bash
# Don't commit merge
# Rollback to pre-merge state
# Investigate conflict with code-reviewer agent
# Retry merge with conflict resolution strategy
```

**If integration tests fail:**
```bash
# System components don't integrate correctly
# Likely issue: contracts mismatch between modules
# Strategy:
# 1. Check Phase outputs - did each produce expected contracts?
# 2. Check imports - do they reference correct paths?
# 3. Check configuration - are ports/endpoints correct?
# 4. Use code-reviewer agent to find integration bugs
```

### Escalation Criteria

**Escalate to user when:**
- Phase fails validation after 2 fix attempts
- Merge conflicts can't be resolved programmatically
- Integration tests fail after checking all contracts
- Total failures exceed 3 phases

**Escalation message format:**
```
Phase [N] failed after 2 retry attempts.

Last error:
[error output from validation commands]

Current state:
- Rolled back to checkpoint: [checkpoint_id]
- Last successful phase: [phase_name]

Investigation performed:
- [what fix-executor tried]
- [validation commands run]

User action needed:
[specific guidance on what to check]
```

---

## Component Contracts

### [Component A] Contract

**Purpose:** [What this component does]

**Inputs:**
- [Input format/type]
- [Example input]

**Outputs:**
- [Output format/type]
- [Example output]

**Interface:**
```
[Code signature, API endpoint, or proto definition]
```

**Dependencies:**
- Depends on: [Component X output]
- Depended on by: [Component Y, Component Z]

---

### [Component B] Contract

[Same structure]

---

## Configuration

### Environment Variables

| Variable | Purpose | Required | Default | Example |
|----------|---------|----------|---------|---------|
| [VAR_NAME] | [What it configures] | Yes/No | [default] | `value` |

### Configuration Files

**[config.yaml]:**
```yaml
[Example configuration]
```

**Location:** [path]
**Loaded by:** [which modules]

---

## Development Commands

**Run locally:**
```bash
[commands to start system locally]
```

**Run tests:**
```bash
[commands to run all tests]
```

**Build:**
```bash
[commands to build if applicable]
```

**Deploy:**
```bash
[commands to deploy - if applicable]
```

---

## Appendix: Spike Test Results

**Spike tests performed during /spec:**

1. **[Component tested]** (spike location: `.spec/SPIKE_RESULTS/[name].md`)
   - **Finding:** [Key discovery]
   - **Validation:** [Command that proves it works]

2. **[Another component]**
   - **Finding:** [Key discovery]
   - **Validation:** [Command]

[List all spike tests that informed this spec]

---

## Appendix: Architecture Decisions

**Why [decision]?**
- **Context:** [Situation]
- **Decision:** [What was decided]
- **Rationale:** [Why - based on spike tests]
- **Alternatives considered:** [What else was explored]
- **Consequences:** [Trade-offs accepted]

[Document major architectural decisions that agent should know about]

---

## Version History

| Date | Change | Reason |
|------|--------|--------|
| [YYYY-MM-DD] | Initial spec | First spec completion |
| [YYYY-MM-DD] | [Change] | [Why it changed] |

---

**End of Agent-Executable Specification**

**Validation:** This spec has been tested for agent executability:
- [x] All validation commands tested and work
- [x] All gotchas documented with recovery
- [x] Execution graph is unambiguous
- [x] Every module has exact success criteria
- [x] No assumptions or guesses required
- [x] Agent can execute with zero questions
