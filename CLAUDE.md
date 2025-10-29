# Claude Work Contract

## ⚡ CORE PRINCIPLES (NON-NEGOTIABLE)

**RUN HOT:** 200K token budget is a CEILING, not a target. Thorough work first time costs fewer tokens than shortcuts + rework. Get cut off doing great work > finish early doing mediocre work. Read all needed files, spawn agents appropriately, validate everything. Better to hit 200K limit mid-excellence than conserve your way to half-assed answers.

**NO PARTIAL WORK:** Full implementation or explain why blocked. Exception: spec phases work.

**FAIL LOUD:** Errors surface with clear messages. Never catch and ignore. Silent failures are bugs.

**QUALITY GATES:** Tests + linting pass. Fix errors, don't suppress. Stop if can't fix.

**MULTIEDIT FOR SAME FILE:** Multiple changes to one file MUST use MultiEdit tool. Parallel Edit calls on the same file cause race conditions and hook failures. NEVER use parallel Edits on the same file.

**PORTABILITY:** Never hardcode system paths. Use `python3` not `/opt/envs/py3.12/bin/python3`.

**NO MASS UPDATES:** Never use scripts/sed/awk for bulk code changes. Use sub-agents (Task tool) to update files manually. Scripts miss context and introduce subtle bugs. Manual updates = eyes on each change.

---

## Critical State
User is tired and can't watch over everything. Review work skeptically. Validate before claiming things work.

## Workflow Modes
- **Casual/Research**: Exploration, quick fixes
- **SPEC**: Discovery and spec creation (no implementation, spikes in /tmp)
- **Conduct**: Implementation from SPEC.md spec

**Artifacts**: Discovery in `.spec/`, spikes in `/tmp/spike_[name]/`, production in project structure

**Agents**: Use for parallel work/specialized analysis/long validation. Do directly: quick fixes/file reading/simple responses.

## Parallel Execution (Critical)

**Run independent operations in parallel - single message, multiple tool calls.**

**Tools:** Read multiple files, grep multiple patterns, run independent bash commands
**Agents:** Launch multiple Task tools in one message

**Why:** Saves context, faster execution, less back-and-forth

**Example Bad:** Read file1 → wait → Read file2 → wait → Read file3
**Example Good:** Read file1 + Read file2 + Read file3 (single message)

**Exception:** Sequential when output of one feeds into next

## Search Strategy
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
**Python:** Use `~/.claude/scripts/python-code-quality` script (runs ruff, pyright, bandit, semgrep)
**JS/TS:** `prettier/eslint`
**Go:** `golangci-lint run`

Check project config first, fall back to `~/.claude/configs/`

**Python code quality:**
- **Script:** `~/.claude/scripts/python-code-quality` (unified quality + security)
- **Skill:** `python-code-quality` (load for guidance)
- **Usage:** `~/.claude/scripts/python-code-quality --fix <path>` (auto-format, lint, type-check, security scan)
- **When:** Before claiming Python code done, during PR reviews, for security audits

## Git Safety
**NEVER:** update config, force push to main, skip hooks, amend others' commits
**Before committing:** Run git status + diff in parallel, draft WHY message
**Before amending:** Check authorship first

## Task Completion Checklist
- Fully functional (no TODOs unless spec phases work)
- Tests pass (follow `~/.claude/docs/TESTING_STANDARDS.md`)
- **Python:** Run `~/.claude/scripts/python-code-quality --fix <path>` (linting, types, security)
- Errors surface (no silent failures)
- No commented code
- WHY comments for non-obvious decisions

## Skills Usage

**Proactively load relevant skills** - don't rely on default knowledge when specialized guidance exists.

**When to load**: At start of relevant work, not halfway through.
**Why**: Skills contain specific standards and context that override general knowledge.

**How to check available skills**: Check skill descriptions in the Skill tool's available_skills list.

**Usage pattern**:
- **Writing Python?** Load `python-style` (code patterns) AND `python-code-quality` (quality/security) first.
- **Writing tests?** Load `testing-standards` first.
- **Spawning agents?** Load `agent-prompting` first. **MANDATORY before spawning any sub-agents.**
- **Working on MongoDB?** Load `mongodb-aggregation-optimization` first.
- **Writing docs?** Load `ai-documentation` first.
- **Python quality checks?** Run `~/.claude/scripts/python-code-quality --fix <path>` before claiming done.

**Be generous with skill loading** - if a skill exists for the domain, use it.

## Agent Delegation (Critical)

**BEFORE spawning ANY sub-agents:**
1. **Load `agent-prompting` skill** - contains critical inline standards for each agent type
2. **Review "Critical Inline Standards by Agent Type" section** - know what to include in prompts
3. **Include critical standards inline** - copy relevant standards into agent prompt
4. **Specify skill loads** - tell agent which skills to load (testing-standards, python-style, ai-documentation)

**Why this matters:**
- Sub-agents don't automatically know corrected standards (try/except only for connections, logging.getLogger, mock everything external)
- Inline standards in prompt override default knowledge
- Ensures consistent quality across all delegated work

**Example:**
```
# WRONG - vague prompt
Task(implementation-executor, "Implement rate limiting")

# RIGHT - includes critical standards
Task(implementation-executor, """
Implement rate limiting.

Spec: $WORK_DIR/.spec/BUILD_rate_limit.md

CRITICAL STANDARDS:
- Logging: import logging; LOG = logging.getLogger(__name__)
- try/except ONLY for connection errors
- Type hints required, 80 char limit
- DO NOT run tests

Load python-style skill if needed.

[task-specific context]
""")
```

**agent-prompting skill contains:**
- Critical inline standards for each agent type (implementation, test, fix, review, documentation)
- Prompt templates with examples
- Common pitfalls and anti-patterns

## Testing Standards
**Location:** `~/.claude/docs/TESTING_STANDARDS.md`

**Key rules:**
- 1:1 file mapping: One test file per production file (unit tests)
- Coverage: 95%+ for unit tests, all public functions tested
- Test organization: Choose based on complexity (single function, parametrized, or separate methods)
- Every function tested for: Happy path + error cases + edge cases
- Integration tests: 2-4 files per module, add to existing files rather than creating new ones

## Non-Negotiable
1. Security: Never log secrets
2. Completeness: Full implementation or explain
3. Quality: Pass checks before claiming done
4. Validation: Test claims (especially in spec)
5. Honesty: Say "uncertain" explicitly

## Rule Override
These are defaults, not laws. Override when spec/user requests it or project conventions differ.
Note why when deviating.
