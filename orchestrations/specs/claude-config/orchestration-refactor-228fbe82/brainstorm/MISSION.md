# Mission: Orchestration System Refactor

## Goal

Restructure the orchestration system to separate spec creation (brainstorm + formalize) from execution, with Python-validated manifests, accumulated context between agents, and a reusable core that supports multiple workflow types.

## Success Criteria

1. Specs stored in `orchestrations/specs/<project>/<name>-<hash>/`
2. Two-phase spec creation: interactive brainstorm -> automated formalization with validation
3. Python validation against existing schemas (no LLM guessing)
4. Context accumulates between agent calls (CONTEXT.md + per-component contexts)
5. Core is OOP, DRY, reusable across workflow types
6. No hardcoded paths (use `~/.claude` or relative paths)
7. Conduct workflow still works (dry-run validation passes)

## Non-Goals

- Changing the /spec or /conduct slash commands themselves (those stay as entry points)
- Changing how agents are invoked (still use `claude -p`)
- Adding new workflow types (just making the structure support them)
