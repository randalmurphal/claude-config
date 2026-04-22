---
name: post-task-review
description: Use after completing non-trivial work — new features, refactors, multi-file changes, non-trivial bug fixes — before reporting the task complete. Guides parallel review across six lenses (performance & memory, code quality & maintainability, architecture, testing, security, codebase consistency) by spawning focused review agents. Validated findings are fixed directly; architectural red flags and changes to product behavior surface for user discussion. Skip for typos, one-line fixes, pure renames, or config-value tweaks.
---

# Post-Task Review

## Purpose

Catch issues in your own in-flight work before declaring the task done. Parallel read-only agents review the change set through focused lenses, you synthesize and validate, then fix everything except items that genuinely need user input.

Announce at start: "Running post-task review before wrapping up."

## When to Use

Trigger after any non-trivial change is done but before reporting task completion.

**Use for:**
- New features or components
- Refactors
- Non-trivial bug fixes (logic changes, new branches, not one-liners)
- Multi-file changes
- Changes to shared, core, or boundary code
- Anything touching architecture, data flow, or product behavior

**Skip for:**
- Typos, wording-only edits
- Single-line fixes with obvious intent
- Pure renames
- Config-value tweaks with no logic change
- Docs-only changes

Use judgment. If in doubt, run it — a redundant review costs less than a missed issue.

## Process

### 1. Assemble the change set

Collect exactly what changed during this task:
- File paths touched
- Functions/classes added or modified
- A short description of the original task (what the user asked for)
- Any architectural or behavioral decisions made along the way

Use `git diff` against the pre-task baseline if available, otherwise track from session context. This context is what each review agent needs to do its job — a vague change set produces vague reviews.

### 2. Spawn six review agents in parallel

All agents:
- `model: "opus"`
- Read-only — no worktrees needed
- Receive the same change-set context
- Get one focused lens each
- Return findings in a consistent format

**Output format each agent must use:**

```
Severity | file:line | Issue | Concrete fix
```

Severities: **Blocking** (must fix — correctness, security, or clear defect), **Recommended** (should fix — quality, clarity, maintainability), **Optional** (minor).

Each agent is also instructed: if you spot something outside your lens that's a real red flag, flag it anyway — lens boundaries are guidance, not a cage.

#### The six lenses

**1. Performance & Memory**
Hot paths, allocations inside loops, N+1 queries, algorithmic complexity (quadratic behavior on potentially large inputs), unbounded growth, leaks, sync work that blocks, I/O on the critical path, redundant computation, missing caching where it matters, oversized data in memory.

**2. Code Quality, Readability & Maintainability**
Clarity and naming, flat vs nested control flow, dead code, duplication, error handling gaps, comments that explain *what* instead of *why*, magic numbers, functions doing multiple things, single-responsibility violations. **God files** (one file owning many unrelated concerns, or growing beyond what a reader can hold in their head) and **god functions** (too long, multiple responsibilities, deep nesting) are explicit targets — flag them and propose the split.

**3. Architecture & Organization**
Layer violations, business logic leaking into controllers, ORM models, or framework code, dependency direction (domain must not depend on infrastructure), module boundaries, coupling, cohesion, where state lives, abstractions that leak their internals, missing or wrong seams between components.

**4. Testing & Correctness**
Coverage for each changed behavior, edge cases, regression risks, tests that only prove "it runs" vs validate logic, missing tests for new branches or error paths, tests coupled to implementation details instead of observable behavior, missing negative tests for bug fixes.

**5. Security**
Input validation at system boundaries, injection vectors (SQL, command, template), auth/authz checks on new endpoints or handlers, secret handling, unsafe deserialization, path traversal, SSRF, privilege boundaries, dependency risks. If a `security-review` or `Security-Auditor` skill/agent is available and the change touches security-relevant code, delegate this lens to it.

**6. Codebase Consistency**
Existing patterns ignored, reinvented utilities that already exist elsewhere, naming and style drift from surrounding code, framework idioms not followed, test infrastructure bypassed, common code not reused.

### 3. Synthesize

When all six return:

- **Deduplicate** — several agents may flag the same issue from different angles; merge them
- **Validate** — open the referenced file and confirm the issue exists. Subagents hallucinate confidently. Do not act on a claim you haven't seen with your own eyes
- **Rank** by severity
- **Group** related findings so the fix can be coherent

Drop findings that don't survive validation. Note them internally if relevant but don't waste the user's time with false positives.

### 4. Present summary and act

Give the user a concise summary — what was found, what you're about to do, what needs their input. Structure:

- **Found:** N blocking, M recommended, K optional
- **Fixing directly:** one-line description of each fix (keep this tight — the user doesn't need every file:line)
- **Surfacing for discussion:** architectural red flags or behavioral changes, each with context and proposed path
- **Verification plan:** which tests/lint will run after

Then fix everything in the "fixing directly" list. **Except:**

- **Architectural red flags** — findings that imply a larger redesign, questionable layering decisions, or a structural problem that predates this task and would benefit from user input. Surface these instead of silently fixing. The user explicitly wants bigger design issues surfaced and resolved together, not patched over.
- **Changes to product behavior or user-facing functionality** — anything that alters features, UX, API contracts, defaults, error messages users see, or observable behavior of the product. Surface for user sign-off before touching.

Everything else: fix it. Don't prompt for approval on quality, consistency, dead code, performance, missing tests, or security fixes — those are in-scope.

### 5. Verify and report

After fixes:
- Run tests
- Run linters/type checkers
- Confirm nothing regressed

Final report is short:
- Fixed N of N findings (list the concrete changes)
- Surfaced for discussion: the architectural/behavioral items (if any)
- Tests: passing / failing with detail
- Lint: clean / issues with detail

Then return to the original task's completion message. The review is a gate, not the whole conversation.

## Rules

- Never trust a subagent finding without opening the file. Validate first, act second.
- Never silently change product behavior. Surface it.
- Never silently rework the architecture because one review agent said so. Surface it.
- Do fix quality, consistency, dead code, test gaps, performance issues, security issues, and codebase-pattern violations directly — that's the point of the skill.
- If a finding contradicts something the user said earlier in the conversation, surface it — don't override user intent.
- If tests fail after your fixes, do not declare done. Fix the regression or roll back that specific change and surface the conflict.

## Notes

- All six agents run in parallel in a single message (six `Agent` tool calls in one response) so the wall-clock cost is one agent's runtime, not six.
- Read-only agents do not need worktrees. Spawn them without `isolation: "worktree"`.
- Brief each agent with: (1) the original user task, (2) the full change set with file paths, (3) its specific lens, (4) the output format, (5) permission to flag cross-lens issues. Vague briefings produce vague reviews.
- This skill is for reviewing *your own in-flight work* before reporting complete. It is not for reviewing existing codebases, PRs, or someone else's code — other skills cover those.
