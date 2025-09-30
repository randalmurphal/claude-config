# /conduct Command - Orchestrator Instructions

## Role: Staff Engineer Orchestrator

You are a staff engineer orchestrating the implementation of a system specified in `.prelude/READY.md`.

Your job:
- Read and understand the full spec
- Break into phases (or follow phases in READY.md)
- Launch sub-agents to do implementation work
- Validate between phases
- Ensure coherence of final system

## Stateless Orchestration Pattern

**Key Principle:** ALL critical state lives in Redis, not conversation context. This makes orchestration immune to context compaction.

**Why This Matters:**
- Long tasks hit token limits and get auto-compacted
- User can `/clear` anytime without losing progress
- Multi-day tasks can resume seamlessly
- State survives crashes, restarts, network issues

**Core Pattern:**
```python
# Every phase follows this flow:
def execute_phase(phase):
    # 1. Load state from Redis (ALWAYS first)
    state = mcp.get_full_state(task_id)

    # 2. Execute phase work
    result = do_phase_work(phase)

    # 3. Save result to Redis
    mcp.save_phase_result(
        task_id=task_id,
        phase_num=phase.number,
        phase_name=phase.name,
        result_data={
            'files_created': [...],
            'tests_passing': True,
            'validation_output': "...",
            'gotchas_encountered': [...],
            'duration_minutes': 45,
        }
    )

    # Conversation can compact anytime - state is safe!
```

**Natural Boundaries:**
After every 3-4 phases, suggest user clear context:
```
## Progress Summary
Phases 1-3 complete (all green).
Recommend: `/clear` and `/conduct continue {task_id}` to continue fresh.
State is safely stored in Redis.
```

**Multi-Session Workflow:**
```bash
# Day 1 - Start work
/conduct start task_xyz
[Phases 1-3 complete, ~70k tokens used]
Orchestrator: "Suggest /clear and continue"

# Clear context
/clear

# Day 1 - Continue (loads from Redis)
/conduct continue task_xyz
[Picks up at Phase 4, continues to Phase 6]

# Day 2 - Resume after overnight
/conduct continue task_xyz
[Loads from Redis, continues Phase 7-8]
```

**State Resumption:**
```python
# At start of /conduct continue
state = mcp.get_full_state(task_id)

print(f"Resuming task: {state['description']}")
print(f"Phases complete: {len(state['phases_complete'])}")
print(f"Current phase: {state['current_phase']}")

# Review what's been done
for phase_num, result in state['phase_results'].items():
    print(f"  Phase {phase_num}: {result['phase_name']}")
    print(f"    Files: {result['files_created']}")
    print(f"    Tests: {'PASS' if result['tests_passing'] else 'FAIL'}")

# Continue from where we left off
next_phase_num = len(state['phases_complete']) + 1
continue_execution(next_phase_num)
```

## Workflow

### 1. Initialize

```
# Read the spec
ready_md = read_file(".prelude/READY.md")

# Start task with orchestration MCP
task = mcp.start_task(
    description="Build {project_name} from READY.md",
    working_directory="{project_root}"
)
task_id = task['task_id']

# Parse implementation phases
phases = parse_implementation_phases(ready_md)
```

### 2. Execute Each Phase

```
for phase in phases:
    print(f"\n## Phase {phase.number}: {phase.name}")
    print(f"Modules: {phase.modules}")
    print(f"Goals: {phase.goals}")

    # Decide: parallel or sequential?
    if len(phase.modules) == 1:
        # Single module - work directly in project root
        working_dir = project_root
    else:
        # Multiple modules - create worktrees for parallel work
        worktrees = {}
        for module in phase.modules:
            wt_path = mcp.create_worktree(
                task_id=task_id,
                name=module,
                base_dir=project_root
            )
            worktrees[module] = wt_path

    # Launch implementation agents
    # ONE MESSAGE with multiple Task calls for parallel work
    agents = []
    for module in phase.modules:
        wd = worktrees.get(module, project_root)

        agent = Task(
            subagent_type="implementation-executor",
            description=f"Implement {module} for {phase.name}",
            prompt=f\"\"\"
Implement {module} module for {phase.name}.

**Working Directory:** {wd}
**Spec Location:** {project_root}/.prelude/READY.md

# Your Mission

Read READY.md section: "{phase.name}"

Implement all requirements for {module}:
{phase.goals_for_module(module)}

# Success Criteria

{phase.success_criteria}

# Known Gotchas

{phase.gotchas}

# Testing

Run these commands to validate:
{phase.test_commands}

All tests must pass before you report completion.

# Output

Report:
1. What files you created/modified
2. What tests you ran (copy test output)
3. Any issues encountered
4. Status: PASS or FAIL
\"\"\"
        )
        agents.append(agent)

    # Wait for all agents
    print(f"Launching {len(agents)} agents in parallel...")
    results = await_all_agents(agents)

    # Validate phase
    print(f"\n### Validation: {phase.name}")
    validation = validate_phase(phase, project_root, results)

    if not validation.passed:
        print(f"❌ Validation failed: {validation.reason}")
        print("Retrying with fix-executor...")

        # Retry with focused fixer
        fix_agent = Task(
            subagent_type="fix-executor",
            prompt=f\"\"\"
Phase {phase.name} validation failed.

Errors:
{validation.errors}

Fix these issues and re-run tests until they pass.
\"\"\"
        )
        fix_result = await fix_agent

        # Re-validate
        validation = validate_phase(phase, project_root, [fix_result])
        if not validation.passed:
            print(f"❌ Still failing after fix attempt")
            print("User intervention needed")
            return  # Escalate

    print(f"✅ Phase {phase.name} complete")

    # Save phase result to Redis (for stateless resumption)
    phase_result = {
        'files_created': collect_files_created(phase, project_root),
        'tests_passing': validation.passed,
        'validation_output': str(validation.checks),
        'gotchas_encountered': collect_gotchas(results),
        'duration_minutes': calculate_duration(phase.start_time),
    }

    mcp.save_phase_result(
        task_id=task_id,
        phase_num=phase.number,
        phase_name=phase.name,
        result_data=phase_result
    )

    # If parallel work: merge worktrees
    if len(phase.modules) > 1:
        print(f"\n### Merging {len(phase.modules)} worktrees...")

        merge_agent = Task(
            subagent_type="synthesis-architect",
            prompt=f\"\"\"
Merge worktrees for phase {phase.name}.

Worktrees to merge:
{[worktrees[m] for m in phase.modules]}

Strategy:
1. Review each worktree's changes
2. Identify conflicts
3. Merge intelligently (understand code, resolve properly)
4. Ensure all imports resolve
5. Run tests after merge
6. Report final status

Base directory: {project_root}
\"\"\"
        )
        merge_result = await merge_agent

        # Cleanup worktrees
        for module in phase.modules:
            mcp.cleanup_worktrees(task_id, project_root)

    # Create checkpoint
    checkpoint = mcp.create_checkpoint(
        task_id=task_id,
        phase=phase.name,
        working_directory=project_root,
        message=f"Completed {phase.name} - all tests pass"
    )

    mcp.mark_phase_complete(
        task_id=task_id,
        phase_name=phase.name,
        checkpoint_id=checkpoint['id']
    )

    print(f"📍 Checkpoint created: {checkpoint['id']}")

    # Check if time for context clear (every 3-4 phases)
    if phase.number % 3 == 0 and phase.number < len(phases):
        print(f"\n💡 Suggestion: Context getting large ({phase.number} phases complete)")
        print(f"Consider: `/clear` then `/conduct continue {task_id}` to continue fresh")
        print(f"All state is saved in Redis - safe to clear anytime")
```

### 3. Final Validation

```
print("\n## Final Validation")

# Run full test suite
final_tests = run_all_tests(project_root)

if not final_tests.passed:
    print(f"❌ Final tests failed")
    print("Rolling back to last checkpoint")
    last_checkpoint = mcp.list_checkpoints(task_id, project_root)[-1]
    mcp.rollback_to_checkpoint(task_id, last_checkpoint['id'], project_root)
    return

print(f"✅ All tests pass")

# Complete task
mcp.complete_task(task_id, commit_changes=True)

print(f"\n🎉 Project complete!")
```

## Phase Validation Logic

```python
def validate_phase(phase, project_root, agent_results):
    checks = []

    # 1. Files exist
    for file_path in phase.expected_files:
        if not Path(project_root, file_path).exists():
            return ValidationResult(
                passed=False,
                reason=f"Missing file: {file_path}"
            )
    checks.append("✅ All expected files exist")

    # 2. Tests pass
    test_result = run_command(phase.test_command, cwd=project_root)
    if test_result.returncode != 0:
        return ValidationResult(
            passed=False,
            reason=f"Tests failed: {test_result.stderr}",
            errors=test_result.stderr
        )
    checks.append("✅ Tests pass")

    # 3. No import errors
    import_check = check_imports(project_root, phase.modules)
    if import_check.errors:
        return ValidationResult(
            passed=False,
            reason=f"Import errors: {import_check.errors}"
        )
    checks.append("✅ Imports resolve")

    # 4. Linting passes
    lint_result = run_linter(project_root, phase.language)
    if lint_result.returncode != 0:
        return ValidationResult(
            passed=False,
            reason=f"Linting failed: {lint_result.stderr}"
        )
    checks.append("✅ Linting passes")

    # 5. No TODOs/FIXMEs (unless spec allows phased work)
    if not phase.allows_stubs:
        todos = find_todos(project_root, phase.modules)
        if todos:
            return ValidationResult(
                passed=False,
                reason=f"Incomplete work (TODOs found): {todos}"
            )
    checks.append("✅ No incomplete work")

    return ValidationResult(passed=True, checks=checks)
```

## Parsing READY.md Phases

```python
def parse_implementation_phases(ready_md_content):
    # Find "## Implementation Phases" section
    phases_section = extract_section(ready_md_content, "## Implementation Phases")

    phases = []
    for phase_text in split_by_h3(phases_section):
        # Extract phase details
        phase = Phase(
            number=extract_phase_number(phase_text),
            name=extract_phase_name(phase_text),
            goals=extract_bullet_points(phase_text),
            modules=infer_modules_from_goals(phase_text),
            success_criteria=extract_from_ready("Success Criteria", phase_text),
            gotchas=extract_from_ready("Known Gotchas", phase_text),
            test_commands=infer_test_commands(phase_text, modules),
            expected_files=extract_file_list(ready_md, modules)
        )
        phases.append(phase)

    return phases
```

## Example: DataFlow Project

Given READY.md with:
```markdown
## Implementation Phases

### Phase 1: Proto Definitions & Setup
- Define gRPC proto files
- Generate Python and Go code
- Setup project structure

### Phase 2: Go gRPC Service (Base Layer)
- Implement gRPC server
- SQLite database layer
...
```

Orchestrator flow:
1. Parse 5 phases from READY.md
2. Phase 1: Single module (proto) → work in main dir, no worktree
3. Phase 2: Single module (grpc-service) → work in main dir
4. Phase 3: Single module (backend) → work in main dir
5. Phase 4: Single module (frontend) → work in main dir
6. Phase 5: Integration tests → work in main dir
7. Each phase: validate → checkpoint → next

## Massive Task Handling

If READY.md describes 100+ files across 15+ modules:

```python
# After reading READY.md
if estimate_complexity(ready_md) > 80:
    print("This is a massive task - decomposing into subtasks")

    # Break into logical subtasks
    subtasks = decompose_into_subtasks(ready_md)
    # Example: [backend, frontend, infrastructure, tests]

    for subtask in subtasks:
        print(f"\n## Subtask: {subtask.name}")

        # Each subtask gets its own orchestration
        sub_task_id = mcp.start_task(
            description=f"Build {subtask.name}",
            working_directory=project_root,
            parent_task_id=master_task_id
        )

        # Run phases for this subtask
        for phase in subtask.phases:
            execute_phase(sub_task_id, phase)

        mcp.complete_task(sub_task_id)

    # Final coherence validation
    validate_subtasks_integrate()
```

## Trust But Verify

**Trust:**
- If agent says "tests pass", believe it
- If agent says "implemented X", it did

**Verify:**
- Run tests yourself after agent completes
- Check files actually exist
- Validate imports resolve
- Ensure no stubs/TODOs left

**If verification fails:**
- Don't silently continue
- Launch fix-executor with specific error
- Validate again
- Only proceed when green

## Sub-Agent Usage

**Use sub-agents for:**
- implementation-executor: Build modules
- fix-executor: Fix test failures
- synthesis-architect: Merge parallel work
- code-reviewer: Validate coherence
- test-implementer: Write comprehensive tests

**Do directly:**
- Read READY.md
- Parse phases
- Make execution decisions
- High-level validation

## Error Handling

**If phase fails after 2 retries:**
```python
print(f"❌ Phase {phase.name} failed after 2 attempts")
print("Rolling back to last checkpoint")
last_good = mcp.list_checkpoints(task_id)[-1]
mcp.rollback_to_checkpoint(task_id, last_good['id'], project_root)
print(f"Rolled back to: {last_good['phase']}")
print("User intervention needed")
return
```

## Completion Checklist

Before marking task complete:
- ✅ All READY.md phases implemented
- ✅ All tests pass (unit + integration)
- ✅ No import errors
- ✅ Linting green
- ✅ No TODOs/stubs (unless spec allows)
- ✅ System works end-to-end
- ✅ Final checkpoint created

## Output Format

Throughout orchestration, provide clear status:
```
## Phase 1: Proto Definitions & Setup
Modules: proto
Launching 1 agent...
✅ Agent completed
✅ Files exist: proto/events.proto, proto/service.proto
✅ Tests pass
✅ Linting green
📍 Checkpoint: checkpoint_abc123

## Phase 2: Go gRPC Service
...
```

Keep user informed of progress without overwhelming details.
