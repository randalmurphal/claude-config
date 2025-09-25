# Orchestration Tools Quick Reference

## Tool Location
`{working_directory}/.claude/tools/orchestration.py`

## Key Commands for Main Orchestrator (YOU)

### 1. Initialize Task (via MCP)
```python
# YOU call this directly via MCP, not through a script:
task_id = mcp__orchestration__start_task({
    "description": "User's original request",
    "complexity": "auto-detect"
})
```

### 2. Set Up Parallel Work (via MCP)
```python
# YOU create git worktrees for parallel agents:
mcp__orchestration__create_chambers_batch({
    "task_id": task_id,
    "chamber_names": ["auth", "database", "api"]
})

# Then launch agents in parallel (one message, multiple Tasks)
```

### 3. Record Agent Actions (via MCP)
```python
# YOU record agent discoveries to Redis:
mcp__orchestration__record_agent_action({
    "task_id": task_id,
    "agent_id": "implementation-executor-auth",
    "action": "Completed auth module",
    "result": "Implementation successful",
    "patterns": ["JWT auth", "rate limiting"]
})
```

### 4. Task Completion
```python
# YOU complete the task when all work is done:
mcp__orchestration__complete_task({
    "task_id": task_id,
    "commit_changes": True,
    "summary": "Built complete system as requested"
})
```

## Important Note: MCP-Based Orchestration

**The orchestration is now handled through the MCP server, not Python scripts.**

All state is managed in Redis through MCP tools:
- Task tracking
- Agent coordination
- Context sharing
- Progress monitoring

### Key Differences:
1. **No file-based coordination** - Everything in Redis
2. **YOU orchestrate directly** - No delegation to sub-agents
3. **MCP tools only** - No Python scripts for orchestration
4. **Git worktrees via MCP** - Created through `mcp__orchestration__create_chambers_batch`

## Path Handling

**Working Directory**: Main project directory (absolute path)
- Example: `/Users/alice/projects/myapp`
- This is where the main code lives
- Contains `.claude/` infrastructure

**Workspace Directory**: Individual worker directory (absolute path)
- Example: `/Users/alice/projects/myapp/.claude/workspaces/auth-impl`
- This is a git worktree
- Worker does implementation here
- Has its own `.claude/WORKER_CONTEXT.json`

## Files Created

### In Main Working Directory
```
{working_directory}/.claude/
├── tools/
│   └── orchestration.py          # The tool itself
├── MISSION_CONTEXT.json          # Original request
├── PHASE_PROGRESS.json           # Current progress
├── WORKFLOW_STATE.json           # Phase tracking
├── PARALLEL_STATUS.json          # Active workspaces
├── DISCOVERIES.json              # Non-critical discoveries
└── workspaces/                   # Git worktrees
    ├── auth-impl/
    │   └── .claude/
    │       ├── WORKER_CONTEXT.json
    │       └── hooks/
    │           └── interrupt_monitor.py
    └── db-impl/
        └── .claude/
            ├── WORKER_CONTEXT.json
            └── hooks/
                └── interrupt_monitor.py
```

### In Each Workspace
```
{workspace_directory}/
├── .INTERRUPT                    # Critical discoveries (auto-deleted)
├── .claude/
│   ├── WORKER_CONTEXT.json      # This worker's context
│   ├── settings.local.json      # Hook configuration
│   └── hooks/
│       └── interrupt_monitor.py # Auto-check hook
└── src/                         # Copied skeleton files
    └── [module files]
```

## For Agents

Agents receive context from YOU (the main orchestrator):
1. Context passed in their prompt (they can't call MCP)
2. Work in git worktrees if available
3. Create files/code as their output
4. YOU read their output and update Redis
5. No direct agent-to-agent communication