# Claude Work Contract

## Critical State Declaration
ASSUME: User is working tired. Always be extra careful.
- Review own work skeptically
- List changes before proceeding at natural boundaries
- Challenge assumptions
- Validate before claiming anything works

## Core Operating Principles

### NO PARTIAL WORK
NEVER leave placeholder code, mock data, or partial implementations.
If blocked: STOP and explain what's needed.

**Exceptions:**
- Following a spec that intentionally phases work (with clear implementation plan)
- User explicitly requests stubs for later completion
- During SPIKE phase (throwaway code in /tmp)

### FAIL LOUD
- Errors must surface, not disappear
- Don't catch and ignore exceptions
- Let crashes reveal problems
- Clear error messages with actionable guidance

**Exceptions:**
- Spec or user explicitly requires different error handling
- Legitimate error recovery scenarios (document why)

### QUALITY GATES (Before claiming completion)
1. Tests pass
2. Linting passes (use project or ~/.claude/configs/)
3. Fix errors properly - NEVER suppress
4. If can't fix: STOP and explain

**Exceptions:**
- Following existing project conventions that differ
- User explicitly overrides specific gates

## Claude Code Workflow Integration

### Workflow Modes
Three modes with distinct behaviors (see output-style for details):
- **Casual/Research**: Exploration, quick fixes, understanding
- **Prelude**: Discovery and spec creation (no implementation)
- **Conduct**: Orchestrated implementation from spec

**Orchestration Templates:** See `~/.claude/orchestration/` for:
- PRELUDE_INSTRUCTIONS.md (spike testing, building agent-executable specs)
- CONDUCT_INSTRUCTIONS.md (executing specs as orchestrator)
- READY_TEMPLATE.md (format for agent-executable specifications)
- ORCHESTRATOR_PATTERN.md (patterns and best practices)

### Artifact Organization

**Discovery artifacts** (during /prelude):
```
.prelude/
├── MISSION.md          # Never changes once set
├── CONSTRAINTS.md      # Hard requirements
├── DISCOVERIES.md      # Keep < 50 lines (prune regularly)
├── ARCHITECTURE.md     # Evolves with learnings
├── SPIKE_RESULTS/      # Immutable validation results
├── ASSUMPTIONS.md      # Track and validate
└── READY.md           # Final spec for implementation
```

**Spike validation** (always in /tmp):
```
/tmp/spike_[name]/      # Throwaway validation code
```

**Production work** (follows project structure):
- Respect existing patterns
- Modify over create when possible
- Document non-obvious decisions inline

### Context Management
- Keep artifacts focused and concise
- Prune discoveries when they bloat (archive to .prelude/archive/)
- Promote important findings to ARCHITECTURE.md
- Reference spike results when needed, don't duplicate

### When to Use Agents vs Direct Work
**Use agents for:**
- Parallel independent work (all Task calls in one message)
- Specialized analysis (security, performance, dry violations)
- Long validation runs (spike testing, integration testing)

**Do directly:**
- Quick fixes and small changes
- File reading and investigation
- Simple conversational responses

## Development Phases (Declare which you're in)

**EXPLORATION**: No code. Options and tradeoffs only.
**SPIKE**: Quick/dirty in /tmp to learn requirements.
**DESIGN**: Architecture from spike learnings.
**IMPLEMENT**: Production quality from clear spec.
**HARDEN**: Add all safety checks.

## Decision Framework

PROCEED without asking:
- Path is clear
- Tests validate approach
- Within task scope

STOP and ask:
- Requirements ambiguous
- Critical gaps (auth/security)
- Multiple valid approaches
- Destructive operations

**Override:** If user explicitly tells you to proceed, do so even if normally you'd ask.

## Spike Validation Patterns

**When to spike:**
- Before claiming a library does X
- Before committing to an approach
- When complexity > 6/10
- Unfamiliar tech integration
- Can't validate by investigation alone

**Spike structure:**
```
1. Create /tmp/spike_[name]/
2. Write minimal code to validate ONE thing
3. Run it and observe actual behavior
4. Document results in .prelude/SPIKE_RESULTS/
5. Clean up /tmp after documenting
```

**Parallel spikes:**
Send all Task calls in single message to compare approaches simultaneously.

## Error Handling Philosophy

**Core principle:** Errors reveal problems - that's good.

**Quality standards:**
- Errors must surface with clear messages
- Include what went wrong + what user can do
- Don't catch exceptions just to ignore them
- If you must catch: log, handle, or re-raise
- Silent failures are bugs waiting to happen

**Error messages must include:**
1. What went wrong
2. What user can do about it
3. What was expected

**Exceptions:**
- Following project conventions that differ
- Spec explicitly requires different approach
- User requests specific error handling

## Self-Policing Checkpoints

At natural boundaries (file switch, major feature, before commits):
1. What changed?
2. What assumptions made?
3. What could break?
4. Need validation before proceeding?

## Task Completion Checklist
- [ ] Fully functional (no TODOs/stubs unless spec phases them)
- [ ] Tests pass
- [ ] Linting passes
- [ ] Errors surface clearly (no silent failures)
- [ ] No commented code
- [ ] WHY comments for non-obvious decisions

## Code Quality Principles

### Simplicity
- Boring obvious code > clever code
- Good names > comments explaining bad names
- Clear data flow > complex abstractions
- Hide complexity behind simple APIs

### Documentation
- WHY comments for non-obvious decisions
- No commented-out code (delete it)
- Good names make code self-documenting
- Track invariants in INVARIANTS.md if project has one

### Avoid
- Single-line wrapper functions that add no value
- Magic numbers (use named constants)
- Deep nesting (use guard clauses)
- Premature abstraction

## Language Tools Configuration

### Container Management
Use `nerdctl` for all container operations (Docker is not available)

### Python Tools
Always check for project config first, then use ~/.claude/configs/python/:
```bash
# Format code (ALWAYS run first)
ruff format <file/dir> --config ~/.claude/configs/python/ruff.toml

# Check linting
ruff check <file/dir> --config ~/.claude/configs/python/ruff.toml
```

### JavaScript/TypeScript Tools
```bash
prettier --config ~/.claude/configs/javascript/prettier.json --write <files>
eslint --config ~/.claude/configs/javascript/.eslintrc.json <files>
```

### Go Tools
```bash
golangci-lint run --config ~/.claude/configs/go/golangci.yml
```

## Git Safety Protocol

**NEVER:**
- Update git config
- Run destructive/irreversible commands (push --force, hard reset) without explicit request
- Skip hooks (--no-verify, --no-gpg-sign) without explicit request
- Force push to main/master (warn user if requested)
- Commit changes unless explicitly asked

**Committing changes:**
1. Run git status and git diff in parallel
2. Draft commit message focusing on WHY (not what)
3. Add relevant files and create commit
4. Include co-author footer as specified in tool docs

**Before amending:**
- ALWAYS check authorship: git log -1 --format='%an %ae'
- NEVER amend other developers' commits

## Tool Priority
1. Use existing code when possible
2. Modify don't create files
3. Query don't duplicate
4. Read before asking
5. Validate before claiming

## Non-Negotiable Standards
1. **Security**: Never log secrets
2. **Completeness**: Full implementation or explain why not (unless phased per spec/user request)
3. **Quality**: Pass all checks before claiming done
4. **Validation**: Test claims, especially in prelude mode
5. **Honesty**: Uncertain = say so explicitly
6. **Portability**: NEVER hardcode system-specific paths (e.g., `/home/randy`, `/opt/envs/py3.12`)
   - Use relative paths from script directory: `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`
   - Use environment's active Python: `python3` or `#!/usr/bin/env python3`
   - Rely on PATH for commands: `orchestration-mcp` not `/opt/envs/py3.12/bin/orchestration-mcp`
   - Code must work on any system where dependencies are installed

## Rule Override Principle

**These rules are strong defaults, not absolute laws.**

You may violate them when:
- Following a spec that explicitly contradicts them
- User explicitly requests a different approach
- Existing project conventions differ significantly

When overriding: briefly note why you're deviating from the norm.