# cc_orchestrations

Multi-agent workflow automation for Claude Code. Orchestrates complex tasks through phases with validation loops and voting gates.

---

## Architecture Overview

```
cc_orchestrations/
├── core/           # Foundation: config, runner, state, workspace (see core/CLAUDE.md)
├── workflow/       # Engine: phases, loops, voting gates
├── conduct/        # Implementation orchestration (/conduct)
├── pr_review/      # PR review workflow (/pr_review)
├── implement/      # Ticket-to-PR pipeline
├── prompts/        # Prompt templates (extensible)
└── extensions/     # Project-specific hooks (e.g., m32rimm)
```

---

## Module Responsibilities

| Module | Purpose | Key Entry Point |
|--------|---------|-----------------|
| `core/` | Shared infrastructure | See `core/CLAUDE.md` for details |
| `workflow/` | Execution engine | `engine.py:WorkflowEngine` |
| `conduct/` | Multi-component builds | `workflow.py:run_conduct()` |
| `pr_review/` | Code review automation | `phases.py:run_pr_review()` |
| `implement/` | Jira ticket to MR | `pipeline.py:ImplementPipeline` |
| `prompts/` | Base prompt templates | `conduct.py`, `implement.py` |
| `extensions/` | Project customizations | `m32rimm/` |

---

## Workflow Patterns

### Execution Flow

```
WorkflowEngine.run()
    → Load/create State
    → For each PhaseConfig:
        → Check skip_condition
        → Execute phase (parallel or sequential agents)
        → Handle PhaseResult (success/failure/escalation)
        → Save state after each phase
```

### Validation Loop (`workflow/loops.py`)

```
ValidationLoop.run()
    → Checkpoint before each attempt (if state_manager provided)
    → Run validators in parallel
    → Collect and deduplicate issues
    → If critical/major issues:
        → Run fix_executor (with failure history from previous attempts)
        → Checkpoint after fix
        → Re-validate (up to max_attempts)
    → If same issue repeats:
        → Trigger voting gate
        → Escalate to user if no consensus
```

**Failure history**: Fix prompts include what was tried before and why it failed, helping avoid repeat mistakes.

**End-state validation**: `ValidationLoop.run_end_state_validation()` checks component integration after all components complete.

### Voting Gates (`workflow/gates.py`)

Multi-agent consensus with **confidence-weighted voting**:

```python
outcome = run_voting_gate(
    runner, gate_name="fix_strategy",
    num_voters=3, options=["FIX", "REFACTOR", "ESCALATE"],
    threshold=0.67  # High-confidence votes count more
)
```

Votes include confidence scores (0.0-1.0). A vote with 0.9 confidence outweighs two votes with 0.3 confidence.

---

## Extension System

Extensions provide project-specific customizations:

| Hook | Purpose |
|------|---------|
| `PROMPTS` | Override/add prompt templates |
| `VALIDATORS` | Custom validation agents |
| `CONTEXT` | Project knowledge for prompts |
| `conduct/` | Conduct config overrides |
| `pr_review/` | PR review agent config |

Detection: `core/extensions.py:54` - Uses heuristics (directory names, file presence).

---

## CLI Entry Points

```bash
cc-orchestrations implement INT-1234      # Ticket to PR
cc-orchestrations conduct --spec SPEC.md  # Multi-component build
cc-orchestrations pr-review INT-1234      # Review MR
cc-orchestrations pr-review-batch         # Batch review
cc-orchestrations extensions              # List installed
```

Implementation: `cli.py` dispatches to submodule CLIs.

---

## Model Selection & Escalation

**Default model timeouts** (`core/config.py`):
| Model | Timeout |
|-------|---------|
| opus | 600s (10 min) |
| sonnet | 480s (8 min) |
| haiku | 180s (3 min) |

**Risk-based escalation** - Opus used instead of Sonnet when:
- Risk level is `high` or `critical`
- Component complexity is `high`
- Component path contains shared patterns (`common/`, `helpers/`, `utils/`)

**Fix attempt escalation**: First attempt Sonnet, second+ attempts Opus.

---

## Key Constants

- `WORKTREES_BASE`: `~/.claude-worktrees/`
- `MAX_DRAFT_ATTEMPTS`: 3
- `MAX_REVIEW_FIX_ATTEMPTS`: 3
- Default consensus threshold: 0.67 (2/3 majority)

---

## Common Gotchas

1. **State file locking** - Don't manipulate `.state/` manually during runs
2. **Worktree isolation** - Changes in worktree won't affect main repo
3. **Cursor fallback** - Runner routes non-Anthropic models to cursor-agent
4. **Schema validation** - Agents must return JSON matching `core/schemas.py`
5. **Draft mode commits** - `[DRAFT]` prefix; reset before full orchestration

---

## Testing

```bash
python -m pytest cc_orchestrations/tests/
```

---

## When Modifying

- **Adding agents**: `core/registry.py` or `.claude/agents/*.md`
- **Adding prompts**: `prompts/*.py` + update `PROMPTS` dict
- **New workflow**: Extend `WorkflowEngine` via `PhaseHandler` protocol
- **Project extensions**: Create `cc_orchestrations_<name>` package (see m32rimm)
