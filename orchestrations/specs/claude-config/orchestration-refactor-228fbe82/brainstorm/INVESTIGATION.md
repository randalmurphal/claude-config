# Investigation Findings

## Current Architecture

```
orchestrations/
└── conduct/
    ├── core/
    │   ├── config.py      # Config dataclasses, modes, risk scaling
    │   ├── state.py       # State machine, ComponentState, StateManager
    │   └── schemas.py     # JSON schemas for agent responses
    ├── workflow/
    │   ├── engine.py      # WorkflowEngine, ExecutionContext, ComponentLoop
    │   ├── gates.py       # VotingGate, tally_votes
    │   └── loops.py       # ValidationLoop, FixLoop
    ├── agents/
    │   ├── runner.py      # AgentRunner - invokes claude -p
    │   └── registry.py    # Agent type definitions
    ├── workflows/
    │   └── conduct.py     # Conduct-specific phases and config
    └── prompts/           # Prompt templates
```

## What's Conduct-Specific vs Generic

### Generic (should be in core):
- `config.py` - Config, AgentConfig, ValidationConfig, RiskConfig
- `state.py` - State, ComponentState, StateManager, Issue
- `schemas.py` - Schema registry, base schemas
- `runner.py` - AgentRunner (invokes claude -p)
- `gates.py` - VotingGate, tally_votes
- `loops.py` - ValidationLoop, FixLoop
- `engine.py` - WorkflowEngine, ExecutionContext

### Conduct-Specific (stays in workflows/conduct):
- Phase handlers (phase_parse_spec, phase_component_loop, etc.)
- CONDUCT_CONFIG with specific phases
- Conduct-specific schemas (spec_parser, impact_analysis)
- Conduct-specific prompts

## Path Hardcoding Issues Found

1. `runner.py:53` - uses `self.work_dir` correctly (relative)
2. `state.py:276` - uses `state_dir: Path` parameter (good)
3. `conduct.py` - references `.spec/` directory (relative, good)
4. No hardcoded `/home/` paths in Python files

But specs currently go to:
- `$PROJECT/.spec/` - tied to project directory
- Only one spec at a time per project

## Context Flow Analysis

Current: Each `claude -p` call is stateless
- Prompt is built fresh each time
- No reading of previous agent outputs
- Discoveries recorded in state but not injected into prompts

Missing:
- CONTEXT.md that agents read/write
- Per-component context files
- Automatic context injection in runner

## Validation Gap

Current: Spec parsing is done by LLM
- `phase_parse_spec` asks agent to parse SPEC.md
- No Python validation of structure
- Dependency cycles could be missed
- Missing fields not caught until execution

Need: Python validation using existing schemas
- Manifest schema defines required fields
- Dependency graph validation (cycle detection)
- Consistency checks (risk level vs reviewers)
