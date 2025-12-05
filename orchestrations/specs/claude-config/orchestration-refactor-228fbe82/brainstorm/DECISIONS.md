# Architectural Decisions

## Decision 1: Spec Storage Location

**Choice:** `orchestrations/specs/<project>/<name>-<hash>/`

**Rationale:**
- Self-contained within orchestrations directory
- Project grouping for organization
- Hash suffix prevents name collisions
- Can have multiple specs per project

**Alternatives Considered:**
- `~/.claude/specs/` - Global, but separates specs from orchestration code
- `$PROJECT/.spec/` - Current approach, limited to one spec per project

## Decision 2: Two-Phase Spec Creation

**Choice:** Brainstorm (interactive) + Formalize (automated with validation)

**Rationale:**
- Brainstorm can be messy, exploratory, iterative
- Formalization is a translation task LLM is good at
- Validation is deterministic Python code
- Clear separation of concerns

**Phases:**
1. `/spec` (interactive) -> brainstorm artifacts
2. Formalization agent -> manifest.json (draft)
3. Python validation -> specific errors or success
4. If errors -> fix and retry
5. Output: validated manifest + component contexts

## Decision 3: Manifest as Execution Config

**Choice:** Machine-readable `manifest.json` drives execution

**Rationale:**
- No parsing/inference during execution
- Validation happens once at spec creation
- Can modify manifest without re-running /spec
- Execution engine is simple: read manifest, follow it

**Manifest Contains:**
- Components with dependencies (pre-sorted)
- Execution config (mode, reviewers, gates)
- Complexity/risk (pre-calculated)
- Gotchas (machine-readable list)

## Decision 4: Context Accumulation

**Choice:** File-based context that agents read/write

**Files:**
- `CONTEXT.md` - Global context (current state, critical discoveries)
- `components/<name>.md` - Per-component context
- `DECISIONS.md` - Architectural decisions (append-only)

**Mechanism:**
- Runner reads context before building prompt
- Agent returns `context_update`, `discoveries`, `blockers`
- Runner writes updates to context files

## Decision 5: Core Structure

**Choice:** Extract generic code to `orchestrations/core/`

**Structure:**
```
orchestrations/
├── core/               # Generic, reusable
│   ├── config.py       # Base configs
│   ├── state.py        # State machine
│   ├── schemas.py      # Schema registry
│   ├── runner.py       # Agent invocation
│   ├── context.py      # NEW: Context management
│   ├── manifest.py     # NEW: Manifest loading/validation
│   └── paths.py        # NEW: Path resolution (~ expansion)
├── workflow/           # Generic workflow primitives
│   ├── engine.py
│   ├── gates.py
│   └── loops.py
├── spec/               # Spec creation
│   ├── formalizer.py   # NEW: Brainstorm -> manifest
│   └── validator.py    # NEW: Python validation
├── workflows/          # Specific workflows
│   └── conduct/
└── specs/              # Spec storage
```

## Decision 6: Path Handling

**Choice:** Use `~` or relative paths, resolve at runtime

**Rules:**
- Specs can use full paths (they're instance-specific)
- Core code uses `~/.claude` or relative paths
- `paths.py` provides resolution utilities
- No `/home/<user>` in any committed code
