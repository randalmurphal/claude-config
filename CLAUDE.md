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

**NO MASS UPDATES:** Never use scripts/sed/awk for bulk code changes. Use sub-agents (Task tool) to update files manually. Scripts miss context and introduce subtle bugs. Manual updates = eyes on each change.

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

## Parallel Execution (Critical for Performance)

**Run independent operations in parallel - single message, multiple tool calls.**

**Tools:** Read multiple files, grep multiple patterns, run independent bash commands
**Agents:** Launch multiple Task tools in one message for parallel work

**Why:** Saves context, faster execution, less back-and-forth

**Example - Bad:**
- Read file1 → wait → Read file2 → wait → Read file3

**Example - Good:**
- Read file1 + Read file2 + Read file3 (single message)
- Task(agent1, "implement X") + Task(agent2, "implement Y") (single message)

**Exception:** Sequential when output of one feeds into next

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
