# cc_orchestrations/core

Foundation infrastructure for all orchestration workflows. See parent `cc_orchestrations/CLAUDE.md` for architecture overview.

---

## Module Map

| File | Responsibility | Key Exports |
|------|----------------|-------------|
| `config.py` | All dataclass configs | `Config`, `AgentConfig`, `PhaseConfig`, `ExecutionMode` |
| `runner.py` | Agent execution | `AgentRunner`, `AgentResult` |
| `state.py` | Workflow state persistence | `State`, `StateManager`, `ComponentState` |
| `trajectory.py` | Execution trace logging | `TrajectoryLogger`, `AgentTrajectory` |
| `workspace.py` | PULL-based context management | `Workspace`, `WorkspaceConfig` |
| `schemas.py` | JSON output schemas | `get_schema()`, `SCHEMAS` |
| `registry.py` | Agent type definitions | `REGISTRY`, `register_agent()` |
| `agents.py` | Agent file loader | `AgentLoader` |
| `extensions.py` | Extension discovery | `detect_project_extensions()`, `merge_prompts()` |
| `worktree.py` | Git worktree management | `WorktreeManager` |
| `git.py` | Git utilities | `git_commit()`, `git_has_changes()` |
| `paths.py` | Path resolution | `get_git_root()`, `get_project_name()` |

---

## Config System (`config.py`)

```
Config (main)
├── mode: ExecutionMode (QUICK | STANDARD | FULL)
├── mode_config: auto-set in __post_init__()
├── agents: dict[str, AgentConfig]
├── phases: list[PhaseConfig]
└── voting_gates: list[VotingGateConfig]
```

| Mode | Reviewers | Parallelization | Use Case |
|------|-----------|-----------------|----------|
| `QUICK` | 1 | Aggressive | Fast iteration |
| `STANDARD` | 2 | By level | Balanced |
| `FULL` | 3+ | Conservative | Production |

---

## Agent Runner (`runner.py`)

```python
runner.run(agent_name, prompt, context={})
    → _resolve_agent()       # Get AgentConfig from registry/files
    → _get_model_backend()   # Select claude/cursor backend (line 189)
    → _run_with_retry()      # Execute with timeout/retries
    → _parse_result()        # Extract JSON from response
    → AgentResult
```

**Backend selection**:
| Model | Backend |
|-------|---------|
| `opus`, `sonnet`, `haiku` | Claude CLI (`claude -p ...`) |
| `composer-*`, `gpt-*`, `gemini-*` | cursor-agent |

**Parallel execution**: `runner.run_parallel([...])` - uses `ThreadPoolExecutor`.

---

## State Management (`state.py`)

```python
State:
    current_phase: str
    phase_status: dict[str, PhaseStatus]
    components: dict[str, ComponentState]
    discoveries: list[str]
    votes: list[VoteResult]
    error: str | None
```

**Atomic persistence**: `StateManager.save()` uses file lock at `.state/STATE.json.lock`.

---

## Workspace System (`workspace.py`)

PULL-based context: ~90% token reduction (15K → 1K per agent).

```
.workspace/
├── INDEX.md              # Navigation (~200 tokens, always injected)
├── spec/
│   ├── OVERVIEW.md       # High-level summary
│   ├── requirements.md   # Parsed from spec
│   ├── architecture.md   # Technical approach
│   └── ...
├── components/<id>.md    # Per-component context
├── DISCOVERIES.md        # Append-only findings
└── BLOCKERS.md           # Current blockers
```

**Agent defaults** (`AGENT_WORKSPACE_DEFAULTS`):
| Agent | Injected |
|-------|----------|
| `skeleton_builder` | INDEX + OVERVIEW + architecture |
| `implementation_executor` | INDEX + OVERVIEW + component |
| `validator` | INDEX + OVERVIEW + testing + gotchas |
| `fix_executor` | INDEX only |

**Usage**: `Config(use_workspace=True)` (default). Set `False` for legacy full-context.

---

## Trajectory Logging (`trajectory.py`)

Opt-in execution trace logging for debugging failed orchestrations.

```python
runner = AgentRunner(config, work_dir, enable_trajectory=True)
# Creates .workspace/trajectories/<session>_<idx>_<agent>_<hash>.json
```

**Session summary**: `runner.trajectory_logger.get_session_summary()` returns aggregate stats.

**Debugging**: `runner.trajectory_logger.get_failed_traces()` returns only failures.

---

## Agent Registry (`registry.py`)

**Code-defined** (built-in):
```python
register_agent(AgentType(
    name='validator', model='sonnet',
    allowed_tools=['Read', 'Glob', 'Grep'],
    disallowed_tools=['Write', 'Edit'],
))
```

**File-defined** (project): `.claude/agents/*.md` via `AgentLoader`.

| Built-in Agent | Model | Purpose |
|----------------|-------|---------|
| `skeleton_builder` | sonnet | Create file structure |
| `implementation_executor` | sonnet | Fill stubs |
| `validator` | sonnet | Review code |
| `fix_executor` | sonnet | Fix issues |
| `investigator` | opus | Complex analysis |
| `security_auditor` | sonnet | Security review |

---

## Extension Discovery (`extensions.py`)

```python
detect_project_extensions(work_dir)
    → Check KNOWN_EXTENSIONS patterns
    → Try importing cc_orchestrations_<name>
    → Return applicable names
```

**Hooks**: `get_extension_prompts()`, `get_extension_validators()`, `get_extension_context()`, `merge_prompts()`.

---

## Common Gotchas

1. **mode_config** - Auto-set in `__post_init__()`; don't set manually
2. **Agent timeout** - Stored in `AgentConfig._timeout`, not `timeout`
3. **State locking** - Don't hold StateManager objects long
4. **Schema names** - Must match exactly; use `get_schema()` to validate
5. **Extension detection** - Lambdas on Path objects; handle exceptions
6. **Workspace init** - Call `initialize()` before `get_context_for_agent()`
7. **Component IDs** - Derived: `Path(file).stem.replace('-', '_').replace('.', '_')`
