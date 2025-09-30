# Orchestration Templates

**Agent-optimized specifications for /prelude and /conduct workflows**

## Files

### PRELUDE_INSTRUCTIONS.md
**Use during:** `/prelude` command
**Purpose:** Build agent-executable specifications through spike testing

**Core workflow:**
1. Spike test every component
2. Document exact validation commands
3. Map dependencies and parallel opportunities
4. Capture gotchas with recovery steps
5. Produce READY.md using READY_TEMPLATE.md

**Key principle:** Don't guess - validate everything in /tmp spikes

### CONDUCT_INSTRUCTIONS.md
**Use during:** `/conduct` command
**Purpose:** Execute READY.md as staff engineer orchestrator

**Core workflow:**
1. Read READY.md phases
2. Launch sub-agents for parallel work
3. Validate between phases
4. Create checkpoints
5. Trust but verify all sub-agent work

**Key principle:** Follow the spec, validate at every gate

### READY_TEMPLATE.md
**Use during:** `/prelude` output
**Purpose:** Template for agent-executable specifications

**Sections:**
- Orchestration Plan (execution graph with parallel markers)
- Per Phase (modules, dependencies, validation commands, gotchas)
- Merge Strategy (for parallel work)
- Quality Gates (validation at each step)
- Component Contracts (inputs/outputs/interfaces)

**Key principle:** Exact commands, zero ambiguity

### ORCHESTRATOR_PATTERN.md
**Use during:** `/conduct` reference
**Purpose:** General orchestration patterns and best practices

**Topics:**
- When to use worktrees vs direct work
- Trust but verify pattern
- Sub-agent delegation
- Context management

## Quick Reference

### For /prelude:
```
1. Read PRELUDE_INSTRUCTIONS.md
2. Spike test every component
3. Fill out READY_TEMPLATE.md with findings
4. Validate: could another agent execute this?
```

### For /conduct:
```
1. Read CONDUCT_INSTRUCTIONS.md
2. Parse READY.md execution graph
3. Execute phases with validation
4. Use MCP for state + git safety only
```

## MCP Tools Available

**State management:**
- start_task(description, working_dir, parent_task_id?)
- get_task_state(task_id)
- mark_phase_complete(task_id, phase_name, checkpoint_id)
- complete_task(task_id, commit_changes)

**Git checkpoints:**
- create_checkpoint(task_id, phase, working_dir)
- list_checkpoints(task_id, working_dir)
- rollback_to_checkpoint(task_id, checkpoint_id, working_dir)

**Git worktrees (for parallel work):**
- create_worktree(task_id, name, base_dir)
- cleanup_worktrees(task_id, base_dir)
- list_worktrees(task_id)

## Philosophy

**Prelude = Build knowledge**
- Spike test to understand
- Document for agent execution
- No guessing allowed

**Conduct = Execute knowledge**
- Read READY.md
- Launch agents
- Validate continuously
- Trust but verify

**MCP = Dumb state machine**
- State persistence (Redis)
- Git safety (worktrees, checkpoints)
- No intelligence, no decisions

**Agent = Intelligence layer**
- Make all decisions
- Understand full context
- Delegate grunt work to sub-agents
- Validate everything
