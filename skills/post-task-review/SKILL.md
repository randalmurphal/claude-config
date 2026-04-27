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
Clarity and naming, flat vs nested control flow, dead code, duplication, error handling gaps, comments that explain *what* instead of *why*, magic numbers, functions doing multiple things, single-responsibility violations. **God files** (one file owning many unrelated concerns, or growing beyond what a reader can hold in their head) and **god functions** (too long, multiple responsibilities, deep nesting) are explicit targets — flag them and propose the split. **Drift-prone duplication:** logic in this change that must stay behaviorally aligned with existing or sibling code (so a future change has to update both copies at once to stay correct) but isn't shared — propose extracting it. Distinguish from incidental similarity: pieces that only look alike but represent separate concepts that may evolve independently should stay apart, not get force-merged.

**3. Architecture & Organization**
Layer violations, business logic leaking into controllers, ORM models, or framework code, dependency direction (domain must not depend on infrastructure), module boundaries, coupling, cohesion, where state lives, abstractions that leak their internals, missing or wrong seams between components. **Functional-equivalence check:** could this be implemented with materially less code, fewer moving parts, or fewer layers while still meeting the requirements? Look for incidental complexity — speculative configurability, indirection that doesn't pay for itself, abstractions added without a clear cost they're paying down, single-implementation interfaces, wrappers that just forward calls. If yes, propose the concrete simpler version, not just a vibe.

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

### 4. Classify, summarize, act

Each surviving finding gets classified into **fix directly** or **surface for discussion**. Default is **fix** — surface only when one of the conditions below applies. The point of the skill is to clean up your own work, not to forward a checklist of every minor finding to the user.

**Fix directly when** the fix is obvious AND the code is related to what you just changed. "Related" means in or adjacent to your change set — same files, same module, same logical area. This covers quality, consistency, dead code, performance, missing tests, security, naming, small refactors. Don't ask permission for these even if they're a step beyond the original task — that's the skill working as intended.

**Surface for discussion when:**

- **The right fix is unclear** — multiple plausible approaches with real tradeoffs, and you'd be guessing at the user's preference. Don't guess; ask.
- **Intended behavior is unclear** — the fix would change user-visible behavior (features, UX, API contracts, defaults, error messages) and the correct behavior isn't obvious from context. Behavior calls belong to the user.
- **Genuinely out of scope** — the issue lives in code unrelated to this change set, and pulling it in would balloon the task. Flag it so the user can decide whether to take it on now, schedule it, or ignore.
- **Larger architectural redesign** — implies restructuring beyond a localized fix. Surface so the user can decide direction.

Then summarize and act:

- **Found:** N blocking, M recommended, K optional
- **Fixing directly:** one-line description of each fix (keep this tight — the user doesn't need every file:line)
- **Surfacing for discussion:** items in the categories above, each with context and proposed path
- **Verification plan:** which tests/lint will run after

Then fix everything in the "fixing directly" list.

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
- Default to fix, not surface — use the classification rule in step 4. Over-surfacing turns this skill into a checklist for the user instead of a self-cleanup pass.
- Do fix quality, consistency, dead code, test gaps, performance issues, security issues, and codebase-pattern violations directly when the fix is obvious and the code is related — that's the point of the skill.
- If a finding contradicts something the user said earlier in the conversation, surface it — don't override user intent.
- If tests fail after your fixes, do not declare done. Fix the regression or roll back that specific change and surface the conflict.

## Notes

- All six agents run in parallel in a single message (six `Agent` tool calls in one response) so the wall-clock cost is one agent's runtime, not six.
- Read-only agents do not need worktrees. Spawn them without `isolation: "worktree"`.
- Brief each agent with: (1) the original user task, (2) the full change set with file paths, (3) its specific lens, (4) the output format, (5) permission to flag cross-lens issues. Vague briefings produce vague reviews.
- This skill is for reviewing *your own in-flight work* before reporting complete. It is not for reviewing existing codebases, PRs, or someone else's code — other skills cover those.
