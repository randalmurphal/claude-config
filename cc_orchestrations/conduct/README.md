# Conduct Orchestrator

External enforcement for Claude Code workflows. Claude can't skip validation loops because the script won't let it proceed until the JSON says "pass".

## Philosophy

> More capable models are also more confident about skipping steps they deem unnecessary.

This orchestrator solves that by:
1. Running Claude via `claude -p` with `--json-schema` for structured output
2. Parsing the JSON response in Python
3. Controlling flow externally (loops, gates, escalation)
4. Persisting state for recovery

## Quick Start

```bash
# From your project directory with .spec/SPEC.md ready:
python -m conduct run

# Or use the wrapper:
~/.claude/orchestrations/conduct/run.sh run

# Check status
python -m conduct status

# Resume after interruption
python -m conduct resume

# Start fresh (ignore saved state)
python -m conduct run --fresh
```

## Prerequisites

1. **Claude CLI** installed and authenticated
2. **SPEC.md** created via `/spec` command
3. **Python 3.10+**

## Workflow Phases

| Phase | Description | Voting Gate |
|-------|-------------|-------------|
| `parse_spec` | Extract components and dependencies | - |
| `impact_analysis` | Analyze blast radius | If >10 transitive deps |
| `component_loop` | skeleton → implement → validate for each | Fix strategy if same issue repeats |
| `integration_validation` | Run full test suite | - |
| `final_validation` | Full review scaled by risk | - |
| `production_gate` | Production readiness vote | High/critical risk only |
| `completion` | Finalize and report | - |

## Validation Loop

For each component:

```
                    ┌─────────────────────┐
                    │   Validate (2-6     │
                    │   reviewers based   │
              ┌────►│   on risk level)    │
              │     └──────────┬──────────┘
              │                │
              │         pass?──┴──►fail
              │           │           │
              │           ▼           ▼
              │        DONE      ┌─────────────┐
              │                  │    Fix      │
              └──────────────────┤   Executor  │
                                 └──────────┬──┘
                                            │
                               Same issue ──┴── Different issue
                               3 times?              │
                                  │                  │
                                  ▼                  │
                           ┌──────────────┐         │
                           │  Vote on     │         │
                           │  strategy    │         │
                           └──────────────┘         │
                                  │                  │
                                  ▼                  │
                           Consensus?               │
                              │   │                  │
                           yes    no                │
                              │   │                  │
                              ▼   ▼                  │
                           Apply  Escalate ◄────────┘
                                  to user       (max attempts)
```

## State Persistence

State is saved to `.spec/STATE.json` after every step:

```json
{
  "current_phase": "component_loop",
  "current_component": "auth/service.py",
  "components": {
    "models/user.py": {"status": "complete"},
    "auth/service.py": {"status": "validating", "fix_attempts": 1}
  },
  "voting_results": [...],
  "discoveries": [...]
}
```

## Configuration

Export default config:
```bash
python -m conduct config -o my_config.json
```

Key settings:
- `validation.max_fix_attempts`: Max attempts before escalation (default: 3)
- `validation.same_issue_threshold`: Same issue count triggering vote (default: 2)
- `risk.reviewers_by_risk`: Reviewers per risk level
- `agents.*`: Model, tools, timeout per agent type

## Agent Types

| Agent | Model | Purpose |
|-------|-------|---------|
| `spec_parser` | sonnet | Parse SPEC.md |
| `impact_analyzer` | opus | Blast radius analysis |
| `skeleton_builder` | sonnet | Create file structure |
| `implementation_executor` | sonnet | Fill in code |
| `validator` | sonnet | Code review |
| `security_auditor` | sonnet | Security review |
| `performance_reviewer` | sonnet | Performance review |
| `fix_executor` | sonnet | Fix issues |
| `investigator` | opus | Voting decisions |

## Directory Structure

```
orchestrations/conduct/
├── __init__.py
├── __main__.py          # Entry point
├── cli.py               # CLI commands
├── run.sh               # Shell wrapper
├── core/
│   ├── state.py         # State machine
│   ├── config.py        # Configuration
│   └── schemas.py       # JSON schemas
├── agents/
│   ├── runner.py        # Claude invocation
│   └── registry.py      # Agent types
├── workflow/
│   ├── engine.py        # Execution engine
│   ├── gates.py         # Voting gates
│   └── loops.py         # Validation loops
├── workflows/
│   └── conduct.py       # Conduct workflow
└── prompts/
    ├── skeleton.txt
    ├── implement.txt
    ├── validate.txt
    └── ...
```

## Extending

### Add a new agent type

```python
# In agents/registry.py
register_agent(
    AgentType(
        name="my_agent",
        description="What it does",
        model="sonnet",
        schema="my_schema",  # Define in schemas.py
        allowed_tools=["Read", "Write"],
        timeout=300,
    )
)
```

### Add a new phase

```python
# In workflows/conduct.py
def phase_my_phase(ctx: ExecutionContext, phase: PhaseConfig) -> PhaseResult:
    # Your logic
    return PhaseResult(success=True)

# Add to CONDUCT_CONFIG.phases and CONDUCT_HANDLERS
```

### Add a new voting gate

```python
# In config
VotingGateConfig(
    name="my_gate",
    trigger_condition="some_condition",
    num_voters=3,
    voter_agent="investigator",
    schema="my_vote_schema",
    options=["A", "B", "C"],
)
```

## Troubleshooting

**"SPEC.md not found"**
Run `/spec` first to create the specification.

**Workflow stuck in loop**
Check `.spec/STATE.json` for current state. Use `python -m conduct reset` to start over.

**Agent timeout**
Increase `timeout` in agent config or use `--config` with custom timeouts.

**No consensus on vote**
The orchestrator will prompt you for a decision. Your input is recorded in state.
