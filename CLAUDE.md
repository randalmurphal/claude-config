# Claude Work Contract

## Thinking Budget Optimization
32k character thinking budget consumes main context tokens.

**Default: NO THINKING.** Only when genuinely uncertain, weighing options, or debugging.
Otherwise: just act.

## Core Principles

**NO PARTIAL WORK:** Full implementation or explain why blocked. Exception: spec phases work.

**FAIL LOUD:** Errors surface with clear messages. Never catch and ignore. Silent failures are bugs.

**QUALITY GATES:** Tests + linting pass. Fix errors, don't suppress. Stop if can't fix.

**PORTABILITY:** Never hardcode system paths. Use `python3` not `/opt/envs/py3.12/bin/python3`.

## Critical State
User is tired. Review work skeptically. Validate before claiming things work.

## Workflow Modes (see ~/.claude/orchestration/ for details)
- **Casual/Research**: Exploration, quick fixes
- **Prelude**: Discovery and spec creation (no implementation, spikes in /tmp)
- **Conduct**: Implementation from READY.md spec

**Artifact locations:**
- Discovery: `.prelude/` directory
- Spikes: `/tmp/spike_[name]/` (throwaway validation)
- Production: Project structure

**Agent usage:**
- Use for: Parallel work, specialized analysis, long validation
- Do directly: Quick fixes, file reading, simple responses

## Obsidian Note Management

**CRITICAL: Always check note status before trusting content.**

### Note Status System

**Status meanings:**
- `status: current` - Canonical truth, use this
- `status: superseded` - Outdated, ignore unless asked for history
- `status: consolidated` - Knowledge hub combining multiple versions
- `status: draft` - Work in progress, verify before using
- `status: archived` - Historical/completed, reference only

### Reading Notes (Mandatory Checks)

1. **Check frontmatter status FIRST** before trusting any note content
2. **Only use `current` or `consolidated` notes** unless explicitly researching history
3. **If spec/decision is superseded**, follow `superseded-by` link to current version
4. **Flag broken state** if project note points to non-current spec

### Creating/Updating Notes

**When replacing a spec/decision:**
1. Extract valuable knowledge from old version
2. Update new note with "What We Kept From vX" section
3. Mark old version as `superseded` with reason and link to new version
4. Update old note with "Still Valid" section (anchor: `#Still Valid`)
5. Update project note to link to new version

**When creating session notes:**
1. Use template from `templates/session-note.md`
2. Link to project: `[[projects/PROJECT_NAME]]`
3. Tag appropriately: `#session #project/NAME`
4. Document gotchas as discovered
5. Link to related decisions/tasks

### Search Patterns

- **Current work:** `status:current`
- **History:** `status:superseded`
- **Consolidated knowledge:** `status:consolidated`
- **Active sessions:** `path:sessions/ date:>YYYY-MM-DD`
- **By project:** `tag:#project/NAME`

### Slash Commands

**`/notes-start [topic]`** - Load complete context before work
- Queries Obsidian (via ObsidianPilot) + PRISM for all relevant notes
- Auto-detects topic from session if not specified
- Presents current state, decisions, gotchas, next steps
- Fast: SQLite FTS5 search (<0.5s on large vaults)
- **Use at start of any non-trivial work session**

**`/consolidate [topic]`** - Nuclear option for perfect notes
- Scans ALL notes on topic (current, superseded, draft)
- Detects contradictions and determines truth
- Extracts valuable knowledge from all versions
- Reorganizes structure (split/merge as needed)
- Updates specs and fixes broken links
- Stores consolidated knowledge in PRISM
- **Uses unlimited tokens to make notes perfect**
- **Use after multiple spec iterations or when notes feel messy**

**`/notes-update [topic]`** - Capture session findings
- Analyzes current session for discoveries and decisions
- Updates relevant documentation automatically
- Creates ADRs, session notes, gotcha documentation
- Stores findings in PRISM
- **Use at end of work sessions to save knowledge**

### Templates (in Obsidian)

Located in `templates/` directory:
- `project-note.md` - Project overview with task tracking
- `spec-note.md` - Specification with version tracking
- `session-note.md` - Daily work log
- `decision-note.md` - ADR format
- `consolidated-note.md` - Knowledge hub across versions
- `superseded-spec.md` - Outdated spec with "Still Valid" sections

### Workflow Integration

**Start of session:**
```
/notes-start [topic]   # Load all context
# Work happens...
```

**After spec evolution:**
```
# Multiple iterations create messy notes
/consolidate [topic]   # Clean up and organize
/notes-start [topic]   # Load clean context
# Continue with perfect context
```

**During `/conduct`:**
- Phase boundaries → Update session notes
- Spec changes → Mark old as superseded, create new with "What We Kept"
- Decisions → Create ADR notes
- Gotchas → Document in session notes

### PRISM Integration

Obsidian and PRISM work together:
- **Obsidian:** Structured notes with explicit links
- **PRISM:** Semantic memory with cross-session learning
- **Consolidation:** Extracts from Obsidian → Stores in PRISM ANCHORS
- **Retrieval:** PRISM memories link back to Obsidian notes
- **Result:** Both semantic search AND structured documentation

### Rules Summary

1. **Always check status** before using note content
2. **Use `/notes-start`** at beginning of work sessions
3. **Use `/consolidate`** when notes get messy or contradictory
4. **Mark old versions** as superseded with "Still Valid" sections
5. **Extract knowledge forward** - never lose valuable insights
6. **Link everything** - notes should form a knowledge graph
7. **Update PRISM** - consolidated knowledge goes to ANCHORS tier

## Search Strategy
When looking for code/patterns:
1. Grep to find relevant files (cheap)
2. Read only matching files (focused)
3. Don't speculatively read entire codebases
4. Use Glob for file discovery, not ls/find

## Decision Framework

**Proceed:** Path clear, tests validate, within scope.
**Stop & ask:** Requirements ambiguous, critical gaps, destructive ops.
**Override:** User explicitly says proceed.

## Error Messages Must Include
1. What went wrong
2. What user can do
3. What was expected

## Language Tools
**Container:** `nerdctl` (docker not available)
**Python:** `ruff format/check --config ~/.claude/configs/python/ruff.toml`
**JS/TS:** `prettier/eslint --config ~/.claude/configs/javascript/...`
**Go:** `golangci-lint run --config ~/.claude/configs/go/golangci.yml`

Check project config first, fall back to ~/.claude/configs/

## Git Safety
**NEVER:** update config, force push to main, skip hooks, amend others' commits
**Before committing:** Run git status + diff in parallel, draft WHY message
**Before amending:** Check authorship first

## Task Completion Checklist
- Fully functional (no TODOs unless spec phases work)
- Tests pass
- Linting passes
- Errors surface (no silent failures)
- No commented code
- WHY comments for non-obvious decisions

## Non-Negotiable
1. Security: Never log secrets
2. Completeness: Full implementation or explain
3. Quality: Pass checks before claiming done
4. Validation: Test claims (especially in prelude)
5. Honesty: Say "uncertain" explicitly

## Rule Override
These are defaults, not laws. Override when spec/user requests it or project conventions differ.
Note why when deviating.
