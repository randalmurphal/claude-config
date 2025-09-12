# Orchestration Tools Quick Reference

## Tool Location
`{working_directory}/.claude/tools/orchestration.py`

## Key Commands for Conductor

### 1. Initialize Task
```bash
python .claude/tools/orchestration.py create-mission \
  "User's original request here" \
  --criteria "What success looks like"
```

### 2. Set Up Parallel Work (Phase 4 or 5)
```bash
# Define workers in JSON format
python .claude/tools/orchestration.py setup-workspaces \
  --workers '[
    {"id": "auth-impl", "module": "auth", "scope": "src/auth/**"},
    {"id": "db-impl", "module": "database", "scope": "src/db/**"}
  ]'
```

### 3. Share Discovery (For Agents)
```bash
# Critical (interrupts others)
python .claude/tools/orchestration.py share-discovery \
  --agent "worker-id" \
  --discovery "What was found" \
  --severity critical \
  --impact "Why it matters" \
  --affects module1 module2

# Non-critical (just logged)
python .claude/tools/orchestration.py share-discovery \
  --agent "worker-id" \
  --discovery "Minor finding" \
  --severity info
```

### 4. Phase Transitions
```bash
# Transition without cleanup
python .claude/tools/orchestration.py transition 4 5

# Transition with workspace cleanup
python .claude/tools/orchestration.py transition 4 5 --cleanup
```

### 5. Clean Up Workspaces
```bash
python .claude/tools/orchestration.py cleanup
```

## What Each Command Does

### `create-mission`
- Creates MISSION_CONTEXT.json with original request
- Sets up .claude/ directory structure
- Records timestamp and working directory
- All paths are absolute

### `setup-workspaces`
- Creates git worktrees for each worker
- Copies relevant skeleton files
- Installs interrupt hooks
- Creates WORKER_CONTEXT.json in each workspace
- Updates PARALLEL_STATUS.json

### `share-discovery`
- For critical: Writes .INTERRUPT files to other workspaces
- For non-critical: Logs to DISCOVERIES.json
- Automatically determines who to interrupt
- Archives all discoveries

### `transition`
- Updates WORKFLOW_STATE.json
- Updates PHASE_PROGRESS.json
- Optionally cleans up workspaces
- Records transition timestamps

### `cleanup`
- Removes all git worktrees
- Deletes workspace directories
- Clears PARALLEL_STATUS.json
- Reports cleanup status

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

Agents receive workspace paths and can:
1. Read WORKER_CONTEXT.json to understand their scope
2. Explore main_directory for interfaces
3. Work in workspace_directory for implementation
4. Share discoveries using the tool
5. Automatically see interrupts via hook