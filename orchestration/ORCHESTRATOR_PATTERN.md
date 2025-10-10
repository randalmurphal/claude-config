# Orchestrator Pattern for /conduct

## Philosophy

**Orchestrator = Intelligent Staff Engineer**
- Reads SPEC.md to understand full picture
- Makes decisions about execution order
- Launches sub-agents for grunt work
- Validates results between phases
- Trust but verify all sub-agent work

**MCP = Dumb State Machine**
- Stores task state (Redis)
- Creates/cleans up worktrees (git safety)
- Creates checkpoints (git commits)
- NO intelligence, NO decisions

**SPEC.md = Source of Truth**
- Implementation phases with order
- Dependencies and gotchas
- Success criteria
- All human/Claude intelligence from /prelude

## Orchestrator Workflow

### 1. Initialize Task

```python
# Start task and get task_id
task = mcp.start_task(
    description="Build X from SPEC.md",
    working_directory="/path/to/project"
)
task_id = task['task_id']

# Read SPEC.md to understand the mission
spec_md = read_file(f"{working_directory}/.spec/SPEC.md")
phases = extract_phases(spec_md)  # Parse "## Implementation Phases"
```

### 2. Execute Each Phase Sequentially

```python
for phase in phases:
    print(f"Starting {phase.name}...")

    # Create worktrees for modules in this phase
    worktrees = []
    for module in phase.modules:
        wt_path = mcp.create_worktree(
            task_id=task_id,
            name=module,
            base_dir=working_directory
        )
        worktrees.append((module, wt_path))

    # Launch sub-agents in parallel (one message, multiple Task calls)
    # Each agent gets minimal context:
    agents = []
    for module, wt_path in worktrees:
        agent = Task(
            subagent_type="implementation-executor",
            description=f"Implement {module} for {phase.name}",
            prompt=f"""
You are implementing the {module} module for {phase.name}.

Working directory: {wt_path}
SPEC.md spec: {working_directory}/.spec/SPEC.md

Instructions:
1. Read SPEC.md section for {phase.name}
2. Implement all files for {module} as specified
3. Run tests: {phase.test_command}
4. Fix any errors
5. Report: what you built, what tests passed, any issues

SUCCESS CRITERIA:
{phase.success_criteria}

GOTCHAS:
{phase.gotchas}
"""
        )
        agents.append(agent)

    # Wait for all agents to complete
    results = await_agents(agents)

    # Validate phase completion
    validation_passed = validate_phase(
        phase=phase,
        working_directory=working_directory,
        results=results
    )

    if not validation_passed:
        # Retry or escalate
        handle_failure(phase, results)

    # Create checkpoint
    checkpoint = mcp.create_checkpoint(
        task_id=task_id,
        phase=phase.name,
        working_directory=working_directory
    )

    # Mark phase complete
    mcp.mark_phase_complete(
        task_id=task_id,
        phase=phase.name,
        checkpoint_id=checkpoint['id']
    )
```

### 3. Merge and Finalize

```python
# After all phases complete, merge worktrees
# Use synthesis-architect agent for intelligent merge
merge_agent = Task(
    subagent_type="synthesis-architect",
    prompt=f"""
Merge all worktrees for task {task_id} into main branch.

Worktrees to merge:
{list_worktrees(task_id)}

Strategy:
1. Compare each worktree branch with main
2. Identify conflicts
3. Resolve intelligently (understand code, don't just git merge)
4. Merge to main branch
5. Verify tests pass after merge

Report: what was merged, any conflicts resolved, test status
"""
)

# Cleanup
mcp.cleanup_worktrees(task_id)
mcp.complete_task(task_id, commit_changes=True)
```

## Phase Validation (Smell Checks)

**What orchestrator validates after each phase:**

### Code Exists
- Files specified in SPEC.md are present
- No placeholder/mock code

### Tests Pass
- Run phase test command (from SPEC.md)
- pytest for Python, go test for Go, npm test for JS
- All tests green

### Imports Resolve
- No import errors
- Dependencies installed
- Generated code present (e.g., proto stubs)

### Quality Gates
- Linting passes (ruff, golangci-lint, eslint)
- No TODO/FIXME comments (unless spec says phased work)

### Phase-Specific Checks
From SPEC.md "Success Criteria" for each phase

## Parsing SPEC.md Phases

```markdown
## Implementation Phases

### Phase 1: Proto Definitions & Setup
- Define gRPC proto files
- Generate Python and Go code
- Setup project structure

Modules: proto
Test Command: ./proto/generate.sh && echo "Proto files generated"
Success Criteria:
- proto/*.proto files exist
- Python and Go stubs generated in backend/ and grpc-service/

### Phase 2: Go gRPC Service (Base Layer)
- Implement gRPC server
- SQLite database layer
- Unit tests

Modules: grpc-service
Test Command: cd grpc-service && go test ./...
Success Criteria:
- gRPC server starts on port 50051
- Database migrations run
- All unit tests pass
```

**Orchestrator extracts:**
- Phase name: "Phase 1: Proto Definitions & Setup"
- Modules: ["proto"]
- Tasks: bullet list
- Test command: how to validate
- Success criteria: what to check

## Sub-Agent Usage

**When to use sub-agents (conserve orchestrator context):**
- Implementing modules (implementation-executor)
- Running tests and fixing errors (fix-executor)
- Code analysis (code-reviewer)
- Merging worktrees (synthesis-architect)
- Security audits (security-auditor)

**What orchestrator does directly:**
- Read SPEC.md
- Parse phases
- Make execution decisions
- Launch agents
- Validate high-level success

## MCP Tools (Simplified)

```python
# State management
start_task(description, working_dir) -> {task_id, status}
get_task_state(task_id) -> {phases_complete: [], current_phase: "..."}
mark_phase_complete(task_id, phase_name, checkpoint_id)
complete_task(task_id, commit_changes=True)

# Git safety
create_worktree(task_id, name, base_dir) -> worktree_path
cleanup_worktrees(task_id)
list_worktrees(task_id) -> [worktree_paths]

# Checkpoints
create_checkpoint(task_id, phase, working_dir) -> {id, sha, message}
list_checkpoints(task_id) -> [checkpoints]
rollback_to_checkpoint(task_id, checkpoint_id)
```

## Example: DataFlow Project

**SPEC.md says:**
```
Phase 1: Proto Definitions & Setup
Phase 2: Go gRPC Service (Base Layer)
Phase 3: Python Backend (Orchestration Layer)
Phase 4: React Frontend (Presentation Layer)
Phase 5: Integration & Documentation
```

**Orchestrator flow:**
1. Read phases from SPEC.md
2. Phase 1: Launch agent for proto module, validate protos + generated code
3. Phase 2: Launch agent for grpc-service, validate gRPC server + tests
4. Phase 3: Launch agent for backend, validate FastAPI + gRPC client
5. Phase 4: Launch agent for frontend, validate React + API integration
6. Phase 5: Launch agent for tests, validate end-to-end scenarios
7. Merge all worktrees, commit, done

**No Neo4j. No execution strategy calculation. Just follow the spec.**

## Trust But Verify

**Trust:**
- Sub-agents return accurate status
- If agent says "tests pass", believe it
- If agent says "implemented X", it did

**Verify:**
- Run tests yourself after phase completes
- Check files exist
- Validate imports resolve
- Ensure no TODO/FIXME left behind

**If verification fails:**
- Don't silently accept
- Re-launch agent with fix-executor
- Or handle yourself if trivial

## Error Handling

**If phase fails:**
1. Get agent's error report
2. Check if it's retryable (flaky test, timeout)
3. If retryable: launch fix-executor agent with error context
4. If not retryable: escalate to user with clear explanation

**Never:**
- Silently skip errors
- Mark phase complete when tests fail
- Move to next phase with broken dependencies

## Context Management

**Orchestrator keeps minimal context:**
- Current phase name
- List of completed phases
- Latest validation results
- task_id

**Delegates to sub-agents:**
- Reading large files
- Running long test suites
- Analyzing code complexity
- Fixing implementation errors

**Uses SPEC.md as reference:**
- Re-read sections as needed
- Don't memorize entire spec
- Trust the spec is correct

## Success Metrics

**Orchestrator succeeded when:**
- All SPEC.md phases completed in order
- All tests pass
- No import errors
- Quality gates green
- System works end-to-end

**Orchestrator failed when:**
- Skipped phases
- Ignored test failures
- Left broken code
- Didn't validate dependencies
