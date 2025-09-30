---
name: conduct continue
description: Resume orchestration after /clear - loads state from Redis and continues where you left off
---

# /conduct continue - Resume Orchestration

**USE THIS FOR:** Resuming long-running orchestration tasks after `/clear` or session restart.

## What This Does

Loads task state from Redis and continues execution from the last completed phase. Designed for tasks that span multiple context windows or sessions.

## When to Use

✅ **DO use /conduct continue for:**
- After `/clear` when context gets large
- Resuming multi-day tasks
- Recovering from crashes or network issues
- Continuing after overnight breaks

❌ **DON'T use /conduct continue for:**
- Starting new tasks (use `/conduct` instead)
- Tasks that haven't been started yet
- When you want to start over (just use `/conduct` fresh)

## How It Works

### 1. Load State from Redis

```
# Get complete state
state = mcp.get_full_state(task_id)

Loads:
- Task description and working directory
- All completed phases with results
- Current phase (if in progress)
- All phase results (files created, tests status, gotchas)
- Parent task (if subtask)
```

### 2. Resume Context

```
print(f"Resuming: {state['description']}")
print(f"Working Directory: {state['working_directory']}")
print(f"\n## Progress Summary")

for phase_info in state['phases_complete']:
    phase_num = phase_info['phase_num']
    result = state['phase_results'][phase_num]

    print(f"\n### Phase {phase_num}: {result['phase_name']} ✅")
    print(f"Files: {len(result['files_created'])} created/modified")
    print(f"Tests: {'PASS' if result['tests_passing'] else 'FAIL'}")

    if result.get('gotchas_encountered'):
        print(f"Gotchas: {', '.join(result['gotchas_encountered'])}")

print(f"\n## Next Steps")
next_phase = len(state['phases_complete']) + 1
print(f"Continuing from Phase {next_phase}")
```

### 3. Continue Execution

```
# Parse READY.md to get phases
ready_md = read_file(".prelude/READY.md")
phases = parse_implementation_phases(ready_md)

# Find next phase to execute
next_phase_num = len(state['phases_complete']) + 1
next_phase = phases[next_phase_num - 1]

# Resume normal orchestration workflow
execute_phase(next_phase)
```

## Usage Examples

### Simple Continue
```bash
# After 3 phases complete, context getting large
/clear
/conduct continue abc-123-def
```

### Multi-Day Task
```bash
# Day 1 - Start work
/conduct "Build e-commerce platform"
[Work on phases 1-4, ~80k tokens]
Orchestrator: "Suggest /clear and continue"

# End of Day 1
/clear

# Day 2 - Resume
/conduct continue {task_id}
[Loads state, continues Phase 5-8]

# Day 3 - Resume again
/conduct continue {task_id}
[Continues Phase 9-12, completes]
```

### After Crash/Network Issue
```bash
# Task was running, crashed at Phase 7
/conduct continue {task_id}

System: "Resuming task..."
Phase 1-6: ✅ Complete
Phase 7: ⚠️ In progress but not saved
Restarting Phase 7 from checkpoint...
```

## What Gets Restored

**From Redis:**
- ✅ Task ID and description
- ✅ Working directory path
- ✅ All completed phases (names, numbers, timestamps)
- ✅ Phase results (files, tests, validation output, gotchas, duration)
- ✅ Current phase name (if any)
- ✅ Parent task ID (for subtasks)

**From Git:**
- ✅ All checkpoints still available
- ✅ Code changes persisted in commits
- ✅ Rollback capability intact

**From READY.md:**
- ✅ Remaining phases to execute
- ✅ Success criteria
- ✅ Test commands
- ✅ Architecture decisions

## State Storage Schema

Each phase result stored in Redis contains:
```json
{
  "phase_num": 1,
  "phase_name": "Proto Definitions & Setup",
  "files_created": [
    "proto/events.proto",
    "proto/service.proto",
    "proto/__init__.py"
  ],
  "tests_passing": true,
  "validation_output": "✅ All tests pass\n✅ Imports resolve\n✅ Linting green",
  "gotchas_encountered": [
    "Protobuf compiler requires v3.21+ (installed v3.19, upgraded)",
    "Python bindings need manual import path fix"
  ],
  "duration_minutes": 45,
  "completed_at": "2025-09-30T14:23:45Z"
}
```

## Natural Boundaries for Clearing

The orchestrator suggests `/clear` at these points:
- **Every 3-4 phases** - Natural checkpoint boundaries
- **After parallel merges** - Large context from multiple agents
- **Before massive subtasks** - Start fresh for big work
- **After validation failures** - Clean slate for fixes

## Continue Workflow

```python
def conduct_continue(task_id):
    # 1. Load state
    state = mcp.get_full_state(task_id)

    if not state['success']:
        print(f"❌ Task {task_id} not found in Redis")
        print("Either task doesn't exist or state was cleared")
        return

    # 2. Display progress
    display_progress_summary(state)

    # 3. Load READY.md
    ready_path = f"{state['working_directory']}/.prelude/READY.md"
    ready_md = read_file(ready_path)
    phases = parse_implementation_phases(ready_md)

    # 4. Calculate next phase
    phases_done = len(state['phases_complete'])
    next_phase_num = phases_done + 1

    if next_phase_num > len(phases):
        print("✅ All phases complete!")
        print("Run final validation and complete task")
        finalize_task(task_id, state['working_directory'])
        return

    # 5. Resume from next phase
    print(f"\n## Resuming: Phase {next_phase_num}/{len(phases)}")
    next_phase = phases[next_phase_num - 1]

    # 6. Execute remaining phases
    for phase in phases[next_phase_num - 1:]:
        execute_phase(task_id, phase, state['working_directory'])

        # Suggest clear every 3-4 phases
        if phase.number % 3 == 0 and phase.number < len(phases):
            print(f"\n💡 Context getting large ({phase.number} phases complete)")
            print(f"Suggest: `/clear` then `/conduct continue {task_id}`")
            print("State is safely stored in Redis")
```

## Error Handling

### Task Not Found
```
/conduct continue nonexistent-task

❌ Task 'nonexistent-task' not found in Redis
Either:
- Task was never created (use /conduct to start)
- Task was completed and cleaned up
- Redis state was cleared
```

### State Corruption
```
/conduct continue abc-123-def

⚠️ Warning: Phases complete (3) but phase results only has 2 entries
This indicates state corruption or partial save.

Recommendation: Check last checkpoint
list_checkpoints → see checkpoint_phase2
Continue from Phase 2 checkpoint to rebuild state
```

### READY.md Missing
```
/conduct continue abc-123-def

✅ Loaded state (3 phases complete)
❌ Cannot find .prelude/READY.md at {working_directory}

Options:
1. Create READY.md with remaining phases
2. Use /conduct to start fresh
3. Check working_directory path is correct
```

## Benefits of Stateless Pattern

**Context Immunity:**
- Conversation can be compacted anytime
- No critical state lost to auto-compaction
- User controls when to clear

**Multi-Session Support:**
- Pause at any phase boundary
- Resume days/weeks later
- State survives restarts

**Crash Recovery:**
- Network issues don't lose progress
- Claude Code crashes recoverable
- Redis state is ground truth

**Parallel Sessions:**
- Multiple users can query same task state
- No conversation lock-in
- State synchronized in Redis

## Quick Reference

**Continue after clear:**
```bash
/clear
/conduct continue {task_id}
```

**Check task state (without continuing):**
```bash
# Use PRISM MCP directly
mcp.get_full_state(task_id)
```

**List all tasks (future):**
```bash
# Not yet implemented, but planned:
/conduct list
→ Shows all active tasks with progress
```

---

**Bottom Line:**
- State lives in Redis, not conversation
- Resume anytime after /clear
- Multi-day tasks supported
- Crash/network recovery built-in
- Stateless orchestration = context freedom

**When you run `/conduct continue`, you pick up exactly where you left off - no context required.**
