---
name: conduct pause
description: Pause orchestration and save session state for multi-day workflows
---

# /conduct pause - Pause Orchestration Session

**USE THIS FOR:** Pausing long-running orchestration tasks for multi-day workflows or when context gets large.

## What This Does

Saves complete session state to Redis including:
- Current phase and progress
- Conversation summary
- Next steps to resume
- Token usage tracking
- Compressed phase summaries

Designed for **true multi-day workflows** where you want to pause and resume with full context.

## When to Use

✅ **DO use /conduct pause for:**
- End of work day (multi-day tasks)
- Before long breaks (overnight, weekend)
- When context gets large (>100k tokens)
- Natural stopping points (between major phases)

❌ **DON'T use /conduct pause for:**
- Quick breaks (just continue working)
- When task is almost complete (finish it!)
- If you want to start over (use fresh `/conduct`)

## How It Works

### 1. Orchestrator Generates Session Summary

```
# Analyze what's been done
phases_complete = [Phase 1, Phase 2, Phase 3]
current_phase = "Phase 4 (Backend API)"

# Summarize conversation
summary = """
Completed infrastructure setup (Phase 1-3):
- Database schema created with migrations
- gRPC proto defined and generated
- Auth service stubbed with JWT support

Currently implementing:
- Phase 4: Backend API endpoints for user management

Key gotchas discovered:
- Proto requires protoc v3.21+ (upgraded)
- SQLite needs WAL mode for concurrent writes
"""

# Identify next steps
next_steps = [
    "Complete Phase 4: Backend API implementation",
    "Run integration tests",
    "Merge parallel worktrees if any",
    "Proceed to Phase 5: Frontend integration"
]
```

### 2. Save Session State

```python
# Track token usage
token_budget = mcp.get_token_budget(task_id)

# Save full session state
session_result = mcp.save_session_state(
    task_id=task_id,
    session_data={
        "current_phase": current_phase,
        "next_steps": next_steps,
        "conversation_summary": summary,
        "compressed_phases": [1, 2, 3],  # Phases to load compressed
        "ready_md_path": f"{working_dir}/.prelude/READY.md",
        "estimated_total_phases": 8,
        "token_usage": token_budget,
    }
)

session_id = session_result['session_id']
```

### 3. Display Pause Confirmation

```
✅ Orchestration paused: sess_abc123xyz

Task: Build DataFlow Platform - Backend Services
Working Directory: /home/user/projects/dataflow
Phases complete: 3/8

Progress Summary:
- ✅ Phase 1: Infrastructure Setup (45 min)
- ✅ Phase 2: Proto Definitions (30 min)
- ✅ Phase 3: Auth Service Skeleton (40 min)
- ⏸️  Phase 4: Backend API (IN PROGRESS)

Next Steps When Resuming:
1. Complete Phase 4: Backend API implementation
2. Run integration tests
3. Merge parallel worktrees if any
4. Proceed to Phase 5: Frontend integration

Token Usage: 85,000 / 200,000 (42.5%)
Estimated Remaining: ~6-8 hours

Resume with:
/conduct resume sess_abc123xyz
```

## Multi-Day Workflow Pattern

### Day 1: Start and Pause
```bash
# Morning - Start orchestration
/conduct "Build complete e-commerce platform"

# System analyzes: complexity="massive", 12 phases estimated

# Work through phases 1-4 (~6-8 hours)
Phase 1: Database models ✅
Phase 2: Auth system ✅
Phase 3: Product catalog ✅
Phase 4: Shopping cart (in progress...)

# End of day - Pause
Orchestrator: "Context at 85k tokens, good stopping point"
/conduct pause

System saves:
- Session ID: sess_day1_abc123
- Phases 1-3 complete
- Phase 4 partially complete
- Next: Finish Phase 4, start Phase 5
- Token usage: 85k
```

### Day 2: Resume and Continue
```bash
# Morning - Resume
/conduct resume sess_day1_abc123

System loads:
- Full task context
- Phases 1-3 summaries (compressed)
- Phase 4 status (in progress)
- Next steps clearly defined

# Continue phases 5-8
Phase 4: Shopping cart (complete) ✅
Phase 5: Payment processing ✅
Phase 6: Order management ✅
...

# End of day - Pause again
/conduct pause
Session: sess_day2_def456
```

### Day 3: Final Push
```bash
# Morning - Resume
/conduct resume sess_day2_def456

# Complete remaining phases
Phase 9-12 (final work)

# Complete task
All phases ✅
/conduct complete
```

## Pause Command Workflow

```python
async def conduct_pause():
    # 1. Get current task state
    task_state = await mcp.get_task_state(task_id)

    # 2. Get token usage
    token_budget = await mcp.get_token_budget(task_id)

    if token_budget['usage_percent'] > 70:
        print("⚠️ Token usage high - compression recommended on resume")

    # 3. Generate conversation summary
    # Orchestrator analyzes last 50-100 messages
    summary = generate_conversation_summary(
        phases_complete=task_state['phases_complete'],
        current_phase=task_state['current_phase'],
    )

    # 4. Identify next steps from READY.md
    ready_md = read_file(f"{working_dir}/.prelude/READY.md")
    next_steps = extract_next_steps(ready_md, task_state['phases_complete'])

    # 5. Save session state
    session_result = await mcp.save_session_state(
        task_id=task_id,
        session_data={
            "current_phase": task_state['current_phase'],
            "next_steps": next_steps,
            "conversation_summary": summary,
            "ready_md_path": f"{working_dir}/.prelude/READY.md",
            "estimated_total_phases": len(all_phases),
            "token_usage": token_budget,
        }
    )

    # 6. Display confirmation
    display_pause_confirmation(session_result, task_state, token_budget)
```

## What Gets Saved

**Session State (Redis):**
- ✅ Session ID (unique identifier)
- ✅ Task ID (links to task data)
- ✅ Current phase name and number
- ✅ Phases complete (full list)
- ✅ Next steps (3-5 action items)
- ✅ Conversation summary (last 3-5 phases)
- ✅ Token usage (input/output totals)
- ✅ Compressed phases (which to load light)
- ✅ Working directory path
- ✅ READY.md path
- ✅ Estimated total phases
- ✅ Paused timestamp

**Task Data (Already in Redis):**
- ✅ All phase results (files, tests, gotchas, duration)
- ✅ Git checkpoints (rollback capability)
- ✅ Worktree tracking (parallel work)

**Not Saved (Recoverable):**
- ❌ Full conversation history (summarized instead)
- ❌ Old phase details (compressed, available if needed)
- ❌ Orchestrator agent state (rebuilt on resume)

## Context Compression

When pausing, older phases are marked for compression:

**Full Detail (Recent Work):**
```json
{
  "phase_num": 3,
  "phase_name": "Auth Service",
  "files_created": ["auth/service.py", "auth/models.py", "auth/tests.py"],
  "tests_passing": true,
  "validation_output": "pytest: 15 passed, coverage 95%\nruff: no issues",
  "gotchas_encountered": ["JWT needs secret key in env"],
  "duration_minutes": 40
}
```

**Compressed (Older Work):**
```json
{
  "phase_num": 1,
  "phase_name": "Infrastructure",
  "status": "✅ Complete",
  "key_files": ["schema.sql", "docker-compose.yml"],
  "critical_gotchas": ["SQLite needs WAL mode"],
  "tests_passing": true
}
```

Compression saves ~60-70% context for older phases.

## Token Budget Management

```
Token Usage: 85,000 / 200,000 (42.5%)

Breakdown by Phase:
- Phase 1: 15,000 tokens
- Phase 2: 20,000 tokens
- Phase 3: 25,000 tokens
- Phase 4: 25,000 tokens (in progress)

Estimated Remaining: 115,000 tokens
Compression recommended: No (usage < 70%)

When resuming:
- Phases 1-2: Compressed summaries (~5k tokens)
- Phase 3-4: Full context (~50k tokens)
- Fresh start: ~55k tokens for resume
```

## Error Handling

### No Active Task
```bash
/conduct pause

❌ No active orchestration task found
Use '/conduct' to start a new task first
```

### Task Already Complete
```bash
/conduct pause

❌ Task abc-123 is already complete
No need to pause - task finished!
```

### Save Failed
```bash
/conduct pause

⚠️ Failed to save session state to Redis
Error: Connection timeout

Recommendation:
- Check Redis is running (port 6380)
- State is still safe in git checkpoints
- Can resume using: /conduct continue {task_id}
```

## Pause vs Continue

**`/conduct pause` (New):**
- Saves FULL session context
- Includes conversation summary
- Tracks token usage
- Designed for multi-day workflows
- Restores with `/conduct resume`

**`/conduct continue {task_id}` (Existing):**
- Loads ONLY phase results
- No conversation summary
- Lighter weight resume
- Designed for context clearing
- Good for quick restarts

**When to use which:**
- **Pause/Resume**: Multi-day workflows, end of day breaks
- **Continue**: After `/clear`, context too large, quick restarts

## Quick Reference

**Pause current orchestration:**
```bash
/conduct pause
```

**Resume from session:**
```bash
/conduct resume sess_abc123xyz
```

**List paused sessions (future):**
```bash
/conduct sessions
# Shows all paused sessions with progress
```

**Continue from task (lighter):**
```bash
/conduct continue task_abc123
# Uses existing /conduct continue
```

---

**Bottom Line:**
- Saves complete session state for multi-day workflows
- Compresses old phases to save context
- Tracks token usage for budget management
- Resume with full context intact
- Designed for 30+ hour orchestration tasks

**When you run `/conduct pause`, you can safely stop work and resume days later with full context restored.**
