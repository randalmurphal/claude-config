# Orchestration System Refactor

## Problem Statement

The current orchestration system has spec creation coupled with execution, lacks Python validation, doesn't accumulate context between agent calls, and is structured around the conduct workflow rather than being a reusable core.

## User Impact

- Can only have one spec per project (stored in `.spec/`)
- No validation until runtime (spec parsing errors surface late)
- Context doesn't flow between agents (each call starts fresh)
- Can't easily add new workflow types (too much conduct-specific code in core)

## Mission

Restructure to separate spec creation from execution, add Python validation, accumulate context, and create a reusable core.

## Success Criteria

1. Multiple specs per project supported
2. Specs validated by Python before execution
3. Context accumulates and flows between agents
4. Core is reusable for different workflow types
5. Conduct workflow still works (dry-run passes)
6. No hardcoded paths

## Requirements (IMMUTABLE)

- Specs stored in `orchestrations/specs/<project>/<name>-<hash>/`
- `manifest.json` is machine-readable execution config
- Python validation using existing schema patterns
- Context files (CONTEXT.md, per-component) read/written by agents
- All paths use `~/.claude` or relative (no `/home/<user>`)

## Proposed Approach (EVOLVABLE)

### Phase 1: Foundation
- `paths.py` - Path utilities
- `manifest.py` - Manifest dataclass
- `context.py` - Context file management

### Phase 2: Validation
- `validator.py` - Python validation of manifests

### Phase 3: Core Restructure
- Move generic code from `conduct/core` to `orchestrations/core`
- Move `conduct/workflow` to `orchestrations/workflow`
- Update all imports

### Phase 4: Runner Enhancement
- Add context injection to runner
- Read context before prompt, write after response

### Phase 5: Spec Formalization
- `formalizer.py` - Brainstorm -> manifest translation
- Integration with validator

### Phase 6: Workflow Adaptation
- Adapt conduct to use new structure
- Update CLI for spec management

## Implementation Phases

| Phase | Components | Parallel |
|-------|------------|----------|
| 1 | paths, manifest, context | Yes |
| 2 | validator | No (needs manifest) |
| 3 | core_restructure, workflow_restructure | Yes |
| 4 | runner_context | No (needs core) |
| 5 | formalizer | No (needs validator, runner) |
| 6 | conduct_adapt, cli_update | No (needs all above) |

## Known Gotchas

1. **Import Changes**: Moving files changes import paths. All internal imports need updating.
2. **Dry-Run Tests**: Must keep passing throughout - validate after each phase.
3. **Context Injection**: Must not break existing prompt structure - add context as prefix, not replace.
4. **Validation Errors**: Should be specific and actionable, not generic "invalid spec".

## Quality Requirements

- All existing tests pass
- New code follows existing patterns (dataclasses with to_dict/from_dict)
- Type hints on all new functions
- Docstrings on all classes and public methods
- No hardcoded paths in any file

## Files to Create/Modify

### New Files
- `orchestrations/core/paths.py` - Path utilities
- `orchestrations/core/manifest.py` - Manifest dataclass
- `orchestrations/core/context.py` - Context management
- `orchestrations/spec/validator.py` - Python validation
- `orchestrations/spec/formalizer.py` - Brainstorm -> manifest
- `orchestrations/cli.py` - Unified CLI

### Modified Files
- `orchestrations/core/__init__.py` - Re-export moved modules
- `orchestrations/core/runner.py` - Add context injection
- `orchestrations/workflow/*` - Update imports
- `orchestrations/workflows/conduct/*` - Update imports, adapt to new structure

### Moved Files
- `conduct/core/config.py` -> `core/config.py`
- `conduct/core/state.py` -> `core/state.py`
- `conduct/core/schemas.py` -> `core/schemas.py`
- `conduct/agents/runner.py` -> `core/runner.py`
- `conduct/workflow/*` -> `workflow/*`
