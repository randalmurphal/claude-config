---
name: conduct resume
description: Resume paused orchestration session with full context restoration
---

# /conduct resume - Resume Paused Session

**USE THIS FOR:** Resuming orchestration from a paused session with full context restoration.

## What This Does

Loads complete session state from Redis including:
- All completed phases (with compressed summaries)
- Current phase and progress
- Conversation summary (what's been done)
- Next steps (what to do)
- Token usage tracking
- Full phase results for recent work

Designed for **resuming multi-day workflows** with maximum context efficiency.

## When to Use

✅ **DO use /conduct resume for:**
- After using `/conduct pause`
- Starting work on multi-day tasks
- Resuming after overnight/weekend breaks
- When you have session_id from pause

❌ **DON'T use /conduct resume for:**
- Starting new tasks (use `/conduct`)
- Quick context clearing (use `/conduct continue`)
- When you only have task_id (use `/conduct continue`)

## How It Works

### 1. Load Session State from Redis

```python
# Restore full session state
state = await mcp.restore_session_state(session_id)

Loads:
- session_state: All session metadata
- phase_results: Complete results for all phases
- summary: Human-readable progress summary
```

### 2. Display Resume Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 RESUMING ORCHESTRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Session: sess_abc123xyz
Task: Build DataFlow Platform - Backend Services
Working Directory: /home/user/projects/dataflow
Paused: 2025-09-30 18:00:00 (16 hours ago)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PROGRESS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phases Complete: 3/8 (37.5%)
Estimated Remaining: 5 phases (~6-8 hours)

✅ Phase 1: Infrastructure Setup (45 min)
   Files: schema.sql, docker-compose.yml, migrations/
   Gotchas: SQLite needs WAL mode for concurrent writes

✅ Phase 2: Proto Definitions (30 min)
   Files: proto/events.proto, proto/service.proto
   Gotchas: Protoc requires v3.21+ (upgraded)

✅ Phase 3: Auth Service Skeleton (40 min)
   Files: auth/service.py, auth/models.py, auth/tests.py
   Tests: PASSING (15/15, coverage 95%)
   Gotchas: JWT needs secret key in environment

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 CONTEXT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Completed infrastructure setup with database schema and migrations.
Defined gRPC proto contracts for event streaming and service APIs.
Built auth service skeleton with JWT token support and basic tests.

Currently implementing:
- Phase 4: Backend API endpoints for user management

Key Decisions Made:
- Using SQLite with WAL mode for development
- JWT tokens for stateless authentication
- gRPC for internal service communication
- Proto-first approach for API contracts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Complete Phase 4: Backend API implementation
   - User registration endpoint
   - Login/logout endpoints
   - Token refresh endpoint

2. Run integration tests for auth flow

3. Merge parallel worktrees (if any active)

4. Proceed to Phase 5: Frontend integration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 TOKEN BUDGET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Used: 85,000 / 200,000 (42.5%)
Remaining: 115,000 tokens
Compression: Not needed (usage < 70%)

Phase Breakdown:
- Phase 1: 15,000 tokens
- Phase 2: 20,000 tokens
- Phase 3: 25,000 tokens
- Phase 4: 25,000 tokens (in progress)

Estimated for remaining phases: ~95,000 tokens
Context after compression: ~55,000 tokens loaded

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to continue. Starting Phase 4 execution...
```

### 3. Load READY.md and Resume

```python
# Load orchestration spec
ready_path = session_state['ready_md_path']
ready_md = read_file(ready_path)
phases = parse_implementation_phases(ready_md)

# Calculate where to resume
phases_done = len(session_state['phases_complete'])
current_phase_num = phases_done + 1

# Check if task complete
if current_phase_num > len(phases):
    print("✅ All phases complete!")
    finalize_and_complete_task()
    return

# Resume execution
current_phase = phases[current_phase_num - 1]
execute_phase(task_id, current_phase, working_directory)
```

### 4. Context Compression in Action

**When you resume, older phases are loaded compressed:**

Phase 1 (compressed):
```
✅ Infrastructure Setup
Key files: schema.sql, docker-compose.yml
Gotcha: SQLite WAL mode required
```

Phase 3 (full detail):
```
✅ Auth Service Skeleton (40 min)
Files:
- auth/service.py (145 lines)
- auth/models.py (89 lines)
- auth/tests.py (234 lines)
Tests: PASSING
  ✓ test_jwt_token_generation
  ✓ test_jwt_token_validation
  ✓ test_token_expiration
  ✓ test_invalid_token_rejected
  ... (15 tests total, 95% coverage)
Validation Output:
  pytest: 15 passed in 2.34s
  ruff check: no issues found
  mypy: success
Gotchas:
- JWT needs secret key in environment
- Token expiration tested at 1 hour
```

**Context savings: ~60-70% for older phases**

## Resume Command Workflow

```python
async def conduct_resume(session_id: str):
    # 1. Restore session state
    restore_result = await mcp.restore_session_state(session_id)

    if not restore_result['success']:
        print(f"❌ Session {session_id} not found")
        print("Check session_id or use '/conduct continue {task_id}'")
        return

    session_state = restore_result['session_state']
    phase_results = restore_result['phase_results']
    task_id = session_state['task_id']

    # 2. Display comprehensive resume summary
    display_resume_summary(
        session_state=session_state,
        phase_results=phase_results,
    )

    # 3. Check token budget
    token_budget = await mcp.get_token_budget(task_id)
    display_token_budget(token_budget)

    if token_budget['compression_recommended']:
        print("⚠️ Token usage >70% - compression active")
        apply_compression_to_old_phases(session_state)

    # 4. Load READY.md
    ready_path = session_state['ready_md_path']
    if not file_exists(ready_path):
        print(f"❌ Cannot find {ready_path}")
        print("Create READY.md or check working directory")
        return

    ready_md = read_file(ready_path)
    phases = parse_implementation_phases(ready_md)

    # 5. Resume from next phase
    phases_done = len(session_state['phases_complete'])
    next_phase_num = phases_done + 1

    if next_phase_num > len(phases):
        print("✅ All phases complete!")
        finalize_task(task_id)
        return

    print(f"\n▶️  Resuming: Phase {next_phase_num}/{len(phases)}")
    current_phase = phases[next_phase_num - 1]

    # 6. Execute remaining phases
    for phase in phases[next_phase_num - 1:]:
        # Track token usage per phase
        start_tokens = token_budget['total_tokens']

        execute_phase(task_id, phase, session_state['working_directory'])

        # Update token tracking
        end_tokens = estimate_current_tokens()
        await mcp.track_token_usage(
            task_id=task_id,
            input_tokens=(end_tokens - start_tokens) // 2,
            output_tokens=(end_tokens - start_tokens) // 2,
            phase_num=phase.number,
        )

        # Check if should pause again
        token_budget = await mcp.get_token_budget(task_id)
        if token_budget['usage_percent'] > 85:
            print(f"\n💡 Token usage high ({token_budget['usage_percent']}%)")
            print(f"Suggest: `/conduct pause` to compress context")
            print("Or continue and let auto-compression handle it")
```

## Usage Examples

### Simple Resume
```bash
# Yesterday you paused
/conduct pause
→ Session saved: sess_abc123xyz

# Today resume
/conduct resume sess_abc123xyz
→ Loads full context, continues work
```

### Multi-Day Task
```bash
# Day 1: Start and pause
/conduct "Build e-commerce platform"
[Phases 1-4 complete]
/conduct pause
→ Session: sess_day1_abc

# Day 2: Resume and pause
/conduct resume sess_day1_abc
[Phases 5-8 complete]
/conduct pause
→ Session: sess_day2_def

# Day 3: Resume and finish
/conduct resume sess_day2_def
[Phases 9-12 complete]
→ Task complete! ✅
```

### Resume After Week Break
```bash
# Last Friday
/conduct pause
→ Session: sess_friday_abc

# Next Monday (5 days later)
/conduct resume sess_friday_abc

System: "Resuming session paused 5 days ago"
System: "Phases 1-5 complete (compressed summaries)"
System: "Phase 6 in progress - full context restored"
System: "Ready to continue..."
```

## What Gets Restored

**From Session State:**
- ✅ Session ID and task ID
- ✅ Working directory path
- ✅ Current phase name
- ✅ All completed phases (compressed old, full recent)
- ✅ Conversation summary
- ✅ Next steps (actionable items)
- ✅ Token usage totals
- ✅ Estimated remaining work

**From Task Data:**
- ✅ All phase results (files, tests, gotchas, duration)
- ✅ Git checkpoints (rollback available)
- ✅ Worktree tracking (parallel work state)
- ✅ Phase validation history

**From READY.md:**
- ✅ Remaining phases to execute
- ✅ Success criteria per phase
- ✅ Test commands
- ✅ Architecture decisions

## Resume vs Continue

| Feature | `/conduct resume` | `/conduct continue` |
|---------|------------------|-------------------|
| **Input** | session_id | task_id |
| **Context** | Full (summary + phases) | Light (phases only) |
| **Next steps** | ✅ Included | ❌ Not included |
| **Conversation summary** | ✅ Included | ❌ Not included |
| **Token tracking** | ✅ Included | ❌ Not included |
| **Compression** | ✅ Automatic | ❌ Manual |
| **Use case** | Multi-day workflows | Quick restarts |
| **Created by** | `/conduct pause` | Any task start |

**Choose Resume when:**
- Paused with `/conduct pause`
- Need full context restoration
- Multi-day workflow
- Want conversation summary

**Choose Continue when:**
- Just cleared context with `/clear`
- Have task_id (not session_id)
- Quick restart needed
- Don't need conversation summary

## Error Handling

### Session Not Found
```bash
/conduct resume sess_nonexistent

❌ Session 'sess_nonexistent' not found in Redis

Options:
1. Check session_id (use '/conduct sessions' to list)
2. Use '/conduct continue {task_id}' if you have task_id
3. Session may have been cleaned up (task completed)
```

### Session Already Active
```bash
/conduct resume sess_abc123

⚠️ Session sess_abc123 is already active
Last activity: 5 minutes ago

This session is being used in another Claude Code instance.

Options:
1. Continue in current instance (will update to active)
2. Use different session
3. Check for abandoned sessions
```

### READY.md Missing
```bash
/conduct resume sess_abc123

✅ Session loaded successfully
❌ Cannot find READY.md at /home/user/project/.prelude/READY.md

Options:
1. Create READY.md with remaining phases
2. Check working_directory is correct
3. Use '/conduct continue {task_id}' to rebuild from phases
```

### Token Budget Exceeded
```bash
/conduct resume sess_abc123

✅ Session loaded
⚠️ Token usage: 195,000 / 200,000 (97.5%)

Applying aggressive compression:
- Phases 1-5: Compressed to summaries (~8k tokens)
- Phases 6-7: Compressed to key points (~15k tokens)
- Phase 8: Full context (~30k tokens)

Compressed context: ~53k tokens loaded
Remaining budget: ~147k tokens available

Ready to continue with compressed context...
```

## Token Budget Intelligence

The resume command automatically manages token budget:

**< 70% usage:** Load recent phases with full detail
**70-85% usage:** Compress phases older than 3
**> 85% usage:** Aggressive compression, keep only last 2 phases full

**Example with 85% usage:**
```
Before resume: 170k tokens used

Phase compression:
- Phases 1-3: Summaries only (~10k tokens)
- Phases 4-5: Key points (~20k tokens)
- Phases 6-7: Full context (~50k tokens)

After resume: ~80k tokens loaded (53% reduction)
Remaining budget: 120k tokens
```

## Quick Reference

**Resume from paused session:**
```bash
/conduct resume sess_abc123xyz
```

**List all paused sessions:**
```bash
# Use MCP directly
mcp.list_sessions(status="paused")
```

**Resume with session ID from pause:**
```bash
/conduct pause
→ Session: sess_abc123

/conduct resume sess_abc123
```

**If you only have task_id:**
```bash
# Use continue instead
/conduct continue task_xyz789
```

---

**Bottom Line:**
- Restores complete session context
- Automatic compression for token efficiency
- Full conversation summary included
- Next steps clearly defined
- Designed for multi-day workflows

**When you run `/conduct resume`, you get maximum context restoration with intelligent compression - ready to work as if you never left.**
