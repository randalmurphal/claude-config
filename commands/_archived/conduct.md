---
name: conduct
description: Full multi-agent orchestration for complex features - REQUIRES .spec/SPEC.md from /spec
---

# /conduct - Orchestrated Execution

## Prerequisites

**REQUIRED:** `.spec/SPEC.md` must exist (created by `/spec`).

If missing: "Run `/spec` first to create the specification."

## Skills to Load

```
Load: orchestration-standards, spec-formats
```

These contain quality bars, model selection, review scaling, and template formats.

---

## Your Mission

Execute SPEC.md through parallel, dependency-ordered implementation with scaled quality gates.

**You are the conductor.** Make judgment calls on:
- When to parallelize vs sequence
- How deep to review (based on risk)
- When voting helps vs wastes tokens
- When to escalate vs continue

---

## Execution Flow

### 1. Preflight

Read SPEC.md and validate:
- All required sections present
- Dependency graph is acyclic
- Files to create/modify are clear
- Success criteria are testable

If invalid: Stop and explain what's missing.

### 2. Risk Assessment

Assess using `orchestration-standards` criteria:
- Files changed
- API exposure
- Data operations
- Security implications
- Breaking changes

This determines review depth for all phases.

### 3. Build Dependency Graph

From SPEC.md "Files to Create/Modify":
- Extract each file's declared dependencies
- Topologically sort (fail if cycles)
- Verify declared deps match actual imports

Create `.spec/PROGRESS.md` to track component status.

### 4. Component Execution

For each component in dependency order:

**a) Skeleton Phase**
- Spawn `skeleton-builder` (Sonnet) for structure
- Spawn `test-skeleton-builder` (Sonnet) in parallel if tests needed
- Validate: Files compile, structure matches spec

**b) Implementation Phase**
- Spawn `implementation-executor` (Sonnet) to fill stubs
- Spawn `test-implementer` (Sonnet) in parallel if tests needed
- Validate: Tests pass, linting clean

**c) Component Validation**
- Spawn reviewers based on risk level (see orchestration-standards)
- Distinct focus areas: correctness, edge cases, security (if public-facing), performance
- If issues: Fix with `fix-executor`, re-validate

**d) Gate Decision**
- If clean: Mark complete, proceed
- If same issue repeats after 2 attempts: Vote on fix strategy (3 investigators)
- If blocked: Escalate with options

### 5. Integration Validation

After all components:
- Run full test suite
- Cross-component review (do pieces fit together?)
- Integration tests if multi-component interactions

### 6. Full Validation

Scale reviewers to risk (from orchestration-standards):

| Risk | Reviewers | Focus |
|------|-----------|-------|
| Low | 2 | Basic quality |
| Medium | 4 | + edge cases, performance |
| High | 6 | + security, breaking changes |
| Critical | 6 + synthesis | + human checkpoint |

### 7. Production Readiness Gate (High+ Risk Only)

- Vote with 3 reviewers
- 2/3 consensus required
- If split: Present options to user

### 8. Completion

- Commit with meaningful message
- Update PROGRESS.md
- Archive completed specs to `.spec/archive/`
- Report: What was built, what to test, any caveats

---

## Model Selection

| Agent | Model | Rationale |
|-------|-------|-----------|
| Conductor (you) | Opus | Orchestration, synthesis, judgment |
| skeleton-builder | Sonnet | Mechanical, well-defined structure |
| implementation-executor | Sonnet | Code generation |
| test-implementer | Sonnet | Well-defined task |
| code-reviewer | Sonnet | Pattern recognition |
| security-auditor | Sonnet | Focused domain |
| Tie-breaker/verification | Opus | When judgment required |

---

## Guardrails (Non-Negotiable)

1. **No placeholders or TODOs** - Complete implementation or explain why blocked
2. **No skipping reviews** - Scale depth by risk, but always validate
3. **No silent failures** - Every issue surfaced with clear message
4. **Escalate after 3 same-pattern failures** - Don't spin, get help
5. **Commit at checkpoints** - After each component, after validation phases

---

## Failure Handling

### Pattern Detection

After each fix attempt, classify:

| Pattern | Meaning | Action |
|---------|---------|--------|
| Same issue | Approach wrong | Vote on strategy (3 investigators) |
| Different issues | Making progress | Continue fixing |
| Cascading issues | Fix broke things | Step back, reassess |

### Escalation Format

```
BLOCKED: [Brief description]

Issue: [Specific problem]
Attempts: [What was tried, why it failed]
Pattern: [Same/different/cascading]
Options: [A, B, C with trade-offs]
Recommendation: [Your suggestion]
Need: [Specific decision from user]
```

---

## Voting Gates

Use voting when stakes are high or consensus needed. Skip when path is clear.

| Gate | Trigger | Process |
|------|---------|---------|
| Impact Analysis | >10 transitive dependents | 3 investigators vote on migration strategy |
| Fix Strategy | Same issue after 2 attempts | 3 investigators vote: FIX_IN_PLACE / REFACTOR / ESCALATE |
| Production Readiness | High+ risk component done | 3 reviewers vote: READY / NEEDS_WORK / RISKY |
| Test Adequacy | Tests pass with 95%+ coverage | 3 reviewers vote: ADEQUATE / NEEDS_MORE / WEAK |
| Doc Quality | After doc validation | 3 builders vote: READY / GAPS / INACCURATE |

All gates require 2/3 consensus. No consensus = escalate to user.

---

## Progress Tracking

Maintain `.spec/PROGRESS.md`:
```markdown
## Component Status
- [component]: NOT_STARTED | SKELETON | IMPLEMENTING | VALIDATING | COMPLETE
```

---

## Tools Available

| Tool | When |
|------|------|
| `python-code-quality --fix <path>` | Before marking Python complete |
| `git-worktree <name>` | Variant exploration when approach unclear |

---

## What NOT To Do

- Don't prescribe step-by-step algorithms (you can reason)
- Don't repeat instructions within agent prompts (reference skills)
- Don't run fixed number of reviewers regardless of risk
- Don't vote on everything (only high-stakes decisions)
- Don't panic about tokens (quality > conservation)

**Apply judgment. You're Opus. Act like it.**
