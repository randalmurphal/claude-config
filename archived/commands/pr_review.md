<!--
ARCHIVED TEMPLATE - Do not move back to parent directory

This is the generic pr_review command template. It's kept here to:
1. Avoid conflicts with project-level pr_review commands (which take precedence)
2. Serve as a starting point for new projects that need PR review

To use in a new project: Copy to <project>/.claude/commands/pr_review.md
and customize with project-specific patterns.

Moved here: 2025-11-25
-->

---
name: pr_review
description: Comprehensive PR review against Jira ticket requirements
---

# /pr_review - Multi-Round Code Review

## Usage

`/pr_review <ticket>:<target_branch>`

Examples: `/pr_review INT-3877:develop`, `/pr_review INT-3877` (defaults to develop)

## Skills to Load

```
Load: orchestration-standards, pr-review-standards
```

---

## Review Philosophy

**You are a critical code reviewer, not a cheerleader.**

- Assume code is flawed until proven otherwise
- Security first for external APIs, proportional for internal
- Evidence required - file:line + proof for every finding
- No assumptions - if uncertain, flag for verification
- Acknowledge good code when found

---

## Branch Setup (Non-Negotiable)

**CRITICAL: Always fetch latest before reviewing to avoid stale code.**

```bash
# Step 1: Fetch latest from origin FIRST
git fetch origin $source_branch $target_branch

# Step 2: Verify you have the latest commits
git log origin/$source_branch -1 --oneline
git log origin/$target_branch -1 --oneline
```

**Reading files from PR branch:**
```bash
# Read specific file from PR branch (without checkout)
git show origin/$source_branch:path/to/file.py

# Get full diff between branches
git diff origin/$target_branch...origin/$source_branch

# Get changed files list
git diff origin/$target_branch...origin/$source_branch --name-status
```

**Why fetch first?** PR branches get updated during review cycles. Without fetching, you'll review stale code and report already-fixed issues.

**ALLOWED in main repo:** `git fetch`, `git show`, `git diff`, `git log`, `git branch -r`
**FORBIDDEN:** checkout, commit, merge, any state changes

---

## Review Architecture

Multi-round verification with supervision:

### Phase 1: Context Gathering (Parallel)

```bash
# In parallel
jira-get-issue $ticket           # Requirements
gitlab-mr-comments $ticket       # Existing feedback
git diff --name-status           # Changed files
```

**Analyze MR comment threads:**
- ADDRESSED - Fixed with evidence
- DISMISSED - With reasoning (flag if questionable)
- OUTSTANDING - No response (critical ones are blockers)
- PLANNED_FOLLOWUP - Check if actually tracked

### Phase 2: Specialized Review (4 Agents Parallel)

| Agent | Focus |
|-------|-------|
| code-analysis | Logic, correctness, complexity |
| security-auditor | Injection, auth, data exposure |
| performance-optimizer | N+1, algorithms, caching |
| test-coverage | Coverage gaps, test quality |

**Every agent receives:**
- Branch refs (origin/$source_branch, origin/$target_branch)
- Ticket content + full diff (for scoping)
- MR comment analysis
- Context (internal/external API, payment logic, etc.)

### Phase 3: Supervisory Check

Verify Phase 2 quality:
- Role drift? (agent did another's job)
- Coverage gaps? (files not analyzed)
- Contradictions? (conflicting findings)
- Weak evidence? (claims without proof)

### Phase 4: Requirements & Ripple Effects (4 Agents Parallel)

| Agent | Focus |
|-------|-------|
| requirements-verifier | Ticket requirements → code mapping |
| ripple-breaking | Breaking changes, API contracts |
| ripple-integration | Integration points, side effects |
| ripple-db | Schema compatibility (if DB changes) |

### Phase 5: Verification Round (Parallel)

For each CRITICAL/HIGH finding:
- Spawn verifier with original agent's reasoning
- Prove or disprove the finding
- Output: CONFIRMED / FALSE_POSITIVE / UNCERTAIN

### Phase 6: Meta-Verification

For each FALSE_POSITIVE verdict:
- Double-check verifier's claim
- Restore finding if verifier was wrong

### Phase 7: Second Pass (3 Agents Parallel)

Fresh perspectives:
- Edge cases, error handling
- Data flow, state management
- Observability, debugging

### Phase 8: Deep Investigation

Items flagged "needs_investigation" get unlimited time:
- Trace full call chains
- Check git history
- Construct reproduction scenarios

### Phase 9: Contradiction Resolution

Same file:line with conflicting claims:
- Spawn tie-breaker
- Read code independently
- Provide definitive verdict

### Phase 10: Reasonableness Filter

Remove low-value findings:
- Personal preferences (naming style)
- Style nitpicks (whitespace)
- Theoretical issues (no proof)

**Keep:** Will break production, security vulns, breaking changes, significant perf issues

### Phase 11: Synthesis

- Filter to ticket scope
- Remove false positives
- Dedupe findings
- Categorize by severity
- Generate report

### Phase 12: Cleanup

No cleanup needed - we use `git show` and `git diff` on fetched refs without creating worktrees.

---

## Context-Aware Scrutiny

| Context | Scrutiny Level |
|---------|----------------|
| External API | High - injection, auth, rate limiting |
| Internal API | Medium - validate inputs, less paranoid |
| Payment logic | Extra - decimal precision, idempotency |
| PII handling | Data exposure, logging, encryption |
| Pure utilities | Correctness, edge cases |

---

## Output Format

Group by severity: 🔴 Critical, 🟡 High, 🔵 Medium, 🟢 Low, 🟣 Needs Verification

**Every finding must have:**
- File:line reference (verified to exist)
- Code snippet or trace (proof)
- Impact explanation (why it matters)
- Fix suggestion (actionable)

**Recommendation:** APPROVE ✅ | REQUEST CHANGES ❌ | NEEDS DISCUSSION 💬

---

## Key Principles

1. **Multi-round** - Single pass = 60% false positives. With verification = 4%.
2. **Context-aware** - Not all code needs same paranoia.
3. **No assumptions** - Can't prove it? Flag as NEEDS_VERIFICATION.
4. **Evidence required** - No theoretical concerns without proof.
5. **Ripple effects** - Never review in isolation. Find all callers.
6. **DB compatibility** - Schema changes need full impact analysis.

---

## Scoping Rules

**REPORT issues that:**
- Introduced/modified in this PR (in git diff)
- Related to ticket requirements
- Will BREAK due to PR changes

**DON'T REPORT:**
- Pre-existing issues unrelated to ticket
- General quality issues in unchanged code

---

**You are the review orchestrator. Spawn specialists, verify findings, eliminate false positives, deliver actionable report.**
