---
name: orchestration
description: Run and manage orchestrated workflows via Python CLI. Use when executing specs, checking status, or creating new specs for complex multi-component tasks.
---

# Orchestration System

External enforcement for complex multi-component tasks. Python controls flow, Claude executes steps.

## Quick Reference

```bash
# List all specs
python -m cc_orchestrations list

# Create new spec
python -m cc_orchestrations new --project <project> --name <name>

# Validate spec
python -m cc_orchestrations validate --spec <project>/<name>

# Check status
python -m cc_orchestrations status --spec <project>/<name>

# Run spec (after /spec creates it)
python -m cc_orchestrations run --spec <project>/<name>

# Run fresh (ignore saved state)
python -m cc_orchestrations run --spec <project>/<name> --fresh
```

## When to Use

**Use orchestration when:**
- Multi-component features with dependencies
- Need validation at each step (can't skip)
- Complex tasks requiring external enforcement
- Want context to accumulate across phases

**Don't use for:**
- Simple single-file changes
- Quick fixes
- Research/investigation tasks

## Spec Storage

Specs live in `~/.claude/cc_orchestrations/specs/`:
```
specs/
├── <project>/
│   └── <name>-<hash>/
│       ├── manifest.json      # Execution config
│       ├── SPEC.md            # Human-readable spec
│       ├── CONTEXT.md         # Accumulated context
│       ├── brainstorm/        # From /spec phase
│       │   ├── MISSION.md
│       │   ├── INVESTIGATION.md
│       │   └── DECISIONS.md
│       └── components/        # Per-component context
```

## Workflow

1. **User runs `/spec`** → Interactive brainstorm, creates spec
2. **Formalization** → Brainstorm artifacts → validated manifest.json
3. **User runs `python -m cc_orchestrations run`** → Executes spec
4. **Python enforces** → Validation gates, fix loops, voting

## Key Concepts

### Manifest (manifest.json)
Machine-readable execution config:
- Components with dependencies
- Complexity/risk levels
- Execution mode (quick/standard/full)
- Voting gates to enable

### Context Accumulation
Agents read context before work, write updates after:
- `CONTEXT.md` - Global state, discoveries, blockers
- `components/<id>.md` - Per-component context

### External Enforcement
Python controls flow, Claude can't skip validation:
- Validation loop runs until pass or escalate
- Same issue 2x → vote on strategy
- Max attempts → escalate to user

## Execution Modes

| Mode | Parallelization | Validation | Use When |
|------|-----------------|------------|----------|
| quick | Aggressive | End only | Low risk, fast iteration |
| standard | By level | Per component | Default, balanced |
| full | Conservative | Every step | High risk, critical code |

## Common Tasks

### Create and Run New Spec
```bash
# 1. Create spec directory
python -m cc_orchestrations new --project myproject --name myfeature

# 2. Run /spec to populate it (interactive)
/spec

# 3. Validate
python -m cc_orchestrations validate --spec myproject/myfeature-abc123

# 4. Execute
python -m cc_orchestrations run --spec myproject/myfeature-abc123
```

### Check Progress
```bash
python -m cc_orchestrations status --spec myproject/myfeature-abc123
```

### Resume After Interruption
```bash
# Resumes from saved state by default
python -m cc_orchestrations run --spec myproject/myfeature-abc123

# Or start fresh
python -m cc_orchestrations run --spec myproject/myfeature-abc123 --fresh
```

## Integration with /spec

The `/spec` command creates brainstorm artifacts:
1. MISSION.md - What we're building
2. INVESTIGATION.md - What we found
3. DECISIONS.md - Architecture choices
4. CONCERNS.md - Risks and gotchas

Then formalization converts to manifest.json which drives execution.
