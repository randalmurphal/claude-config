---
name: ralph-loop
description: Use when setting up autonomous agent execution loops for a project. Takes a completed design doc and produces IMPLEMENTATION.md, PROMPT files per loop, progress trackers, cross-validation, and ralph.sh runner. Use after brainstorming/design is done, before coding starts.
---

# Ralph Loop Setup

## Overview

Produce the full infrastructure for autonomous agent execution loops. Takes a validated design and generates everything agents need to build the project without improvisation.

**Core principle:** If an agent would have to make a judgment call, the spec isn't specific enough. Resolve all ambiguity before agents start.

**Announce at start:** "I'm using the ralph-loop skill to set up autonomous agent execution infrastructure."

## When to Use

- After `/brainstorm` or equivalent design work is validated
- Project needs autonomous agent building (ralph loops)
- Greenfield or existing projects with a design doc

**Skip for:** Projects where you're coding directly, one-off tasks, anything without a design doc.

## Prerequisites

Before starting, verify:

1. **Design doc exists** — `DESIGN.md`, `docs/specs/DESIGN.md`, `docs/DESIGN.md`, or user-specified path. Must be substantive, not a stub.
2. **Git repo initialized** — the project has a `.git` directory.
3. **ralph.sh source** — `~/.claude/scripts/ralph.sh` exists. If not, create it from the template in `reference.md`.

If no design doc is found and the brainstorm just happened in-session, use conversation context as the design input.

## The Pipeline

4 phases, sequential, with checkpoints. Never skip a phase.

```
Design Doc ──> Phase 1: IMPLEMENTATION.md ──[checkpoint]──>
              Phase 2: Loop Split         ──[checkpoint]──>
              Phase 3: PROMPT Generation  ──[checkpoint]──>
              Phase 4: Finalize           ──> Done
```

### Checkpoint Protocol

At every checkpoint:

1. Present the work produced
2. Ask: "Want me to run a reviewer on this before you look at it?"
3. If yes -> launch Reviewer agent with phase-specific checks (see Phase-Specific Reviews below)
4. Apply fixes from reviewer findings
5. User reviews and approves
6. Proceed to next phase

---

## Phase 1: IMPLEMENTATION.md

Read the design doc thoroughly. If the project uses external libraries, read the actual library code to get exact API signatures — no guessing at interfaces.

Produce an IMPLEMENTATION.md that locks down every decision. See `reference.md` for the full section template.

### Required Sections

| # | Section | What It Locks Down |
|---|---------|-------------------|
| 1 | Module/directory layout | Every file path, package structure |
| 2 | Database schema | Full DDL — CREATE TABLE statements, not descriptions |
| 3 | Shared types | Enums, constants, common structs in root package |
| 4 | Package interfaces | Every public method signature, every Store interface |
| 5 | External library integration | Exact API calls with real types from the library |
| 6 | State machines | Valid transitions enumerated, invalid = error |
| 7 | Configuration format | Struct with defaults, validated on load |
| 8 | Error handling patterns | Error types, user-facing error format |
| 9 | Testing strategy | Per-component approach, mock boundaries |
| 10 | v1 constraints / v2 deferrals | What's in scope, what's explicitly not |

### Key Principle

Every section must be specific enough that an agent can implement it without interpretation. Not "use library X" — show the exact constructor call, option flags, and return types.

**Read library source code** when the project depends on external packages. Use Explore agents to get exact types, method signatures, and option patterns.

### Phase 1 Review Focus

Reviewer checks for:
- Types referenced but not defined
- Interface methods that don't match schemas
- Conflicting field names across packages
- Import cycles (package A returns type from package B which implements A's interface)
- Missing Store methods that consumers will need

---

## Phase 2: Loop Split

Analyze the IMPLEMENTATION.md and propose how to split work into loops.

### Splitting Methodology

1. Map every package/component to a dependency graph
2. Identify natural tiers:
   - **Foundation** (no external deps, no LLM, pure logic)
   - **Mid-layer** (uses foundation + external services)
   - **Integration** (wires everything together, e2e)
3. Each loop must be independently testable via interfaces/mocks
4. A loop should never modify files from a previous loop (exception: adding new files to existing packages when the directory layout requires it)

### Splitting Heuristics

- Loop 1 is always "no external services, pure logic" — the foundation
- Final loop is always integration/e2e — wires real services
- Middle loops sliced by domain
- 2-4 loops is typical. More than 5 is a smell.
- Fewer loops is better.

### Proposal Format

For each proposed loop, present:

| Field | Description |
|-------|-------------|
| Name | Short identifier (e.g., "core", "brain", "integration") |
| Purpose | One-line description |
| Packages | Which packages/components it builds |
| Dependencies | Which previous loops it requires |
| Mocks | What it stubs from later loops |
| Work items | Approximate count |
| Quality gate | Language-specific test command |

### Phase 2 Review Focus

Reviewer checks for:
- Every component in IMPLEMENTATION.md maps to exactly one loop
- No orphaned components
- Dependency direction is always forward (later depends on earlier, never reverse)
- Each loop is independently testable

---

## Phase 3: PROMPT Generation

Generate one PROMPT file per loop, one progress file per loop. Use parallel Task agents (Builder type) for PROMPT files — they're independent.

### PROMPT File Structure

Every PROMPT file has exactly 9 sections, in this order. See `reference.md` for the full template with placeholders.

| # | Section | Purpose |
|---|---------|---------|
| 1 | Housekeeping | Files to ignore (logs, coverage artifacts) |
| 2 | Prime Directive | What this loop builds, scope boundaries |
| 3 | Authority Hierarchy | DESIGN.md > IMPLEMENTATION.md > PROMPT |
| 4 | Rules of Engagement | Non-negotiable rules + prohibited behaviors |
| 5 | Environment | Language, tools, working directory |
| 6 | Quality Gate | Exact shell command, must pass before commit |
| 7 | Workflow Per Iteration | Step-by-step iteration process |
| 8 | Work Items | Grouped by phase, with full specification |
| 9 | Reminders | Key decisions easy to forget |

### Work Item Requirements

Every work item MUST include:

| Field | Description |
|-------|-------------|
| Spec references | Which DESIGN.md and IMPLEMENTATION.md sections to read |
| Target files | Exact package and file paths |
| Deliver criteria | What the code must do |
| Test list | Thorough test scenarios (see Testing Standard below) |
| Done when | One-sentence completion condition |

### Testing Standard

Work item test lists are NOT checkbox exercises. They are the spec expressed as assertions. Every work item's tests must cover:

| Category | What to Test |
|----------|-------------|
| Happy path | The thing does what it's supposed to |
| Error paths | Every way it can fail, and what happens |
| Edge cases | Empty inputs, nil/null, zero, max limits, boundaries |
| Invariant enforcement | Things that must NEVER happen |
| Integration with neighbors | Correct interaction with adjacent components |

**Reject vague test descriptions.** Not "test error handling" — instead "test that `Process()` returns `ErrInvalidJSON` when LLM returns malformed response, and that no `BrainDecision` is saved to store."

A test description should be specific enough to write the test from reading it alone.

Coverage threshold is a floor, not the goal. If a behavior is in the spec and there's no test proving it, the work item isn't done.

### Progress File Template

```markdown
# [Loop Name] — Progress Tracker

## Status: NOT STARTED

## Codebase Patterns

(Populated as iterations discover important patterns.)

## Known Issues

(Issues found during review phase. Highest severity first. Agent resolves these before doing new adversarial reviews.)

## Resolved Issues

(Issues moved here after being fixed and committed.)

## Completed Work Items

(None yet.)

## Iteration Log

(Entries added after each commit.)

## Review Log

(Entries added during review phase — category reviewed, what was checked, what was fixed.)
```

### Phase 3 Review Focus

Reviewer performs cross-loop validation:

| Check | What It Catches |
|-------|----------------|
| Import cycle detection | Package A returns type from B, but B implements A's interface |
| Type consistency | Same concept defined differently across loops |
| Interface completeness | PROMPT references methods not in IMPLEMENTATION.md |
| Work item coverage | Every IMPLEMENTATION.md component has at least one work item |
| Work item orphans | No items reference files not in the directory layout |
| Loop boundary violations | Rules say "don't modify Loop N" but items place files there |
| Authority violations | PROMPT invents types/interfaces not in IMPLEMENTATION.md |
| Dependency direction | Later loops depend on earlier, never reverse |
| Test specificity | Every item has concrete test descriptions |
| Quality gate consistency | All loops use compatible commands |

---

## Phase 4: Finalize

1. Copy `~/.claude/scripts/ralph.sh` into the project root
2. Present the complete file inventory with line counts
3. Show "how to run" instructions:

```bash
./ralph.sh                   # PROMPT.md with Claude
./ralph.sh - codex           # PROMPT.md with Codex
./ralph.sh core              # PROMPT-core.md with Claude
./ralph.sh brain codex       # PROMPT-brain.md with Codex
RALPH_AGENT_CMD="custom-cli --flags" ./ralph.sh core  # Custom agent
```

4. Remind: loop progression is manual. The user decides when a loop is done and starts the next one. Ralph has no opinion about this.

---

## Review Phase

Every PROMPT file must include a Review Phase section after the Work Items. This is critical — without it, agents declare "Loop Complete" when work items run out, which violates the manual progression rule.

### What the Review Phase Does

After all work items are done, the agent enters an indefinite review/fix cycle:

1. Check progress file for known issues — fix ALL of them (highest severity first)
2. If no known issues, do a FULL SWEEP of one category — scan every relevant file, collect all findings, then fix everything
3. Run quality gate, commit all fixes together
4. Update progress file (never write "Loop Complete")
5. Repeat forever until human Ctrl+C's

The key efficiency gain: each iteration sweeps an entire category instead of finding one issue at a time. One commit per category, not one commit per bug.

### Review Categories

Every PROMPT's review phase cycles through these categories:

| # | Category | What to Check |
|---|----------|---------------|
| 1 | Spec Compliance | Every interface/type/method matches IMPLEMENTATION.md exactly |
| 2 | Error Handling | Every `_ = err` is a defect unless it matches a closed list of acceptable patterns (error unwind, standard I/O, spec-designated non-critical). Must cite spec section for exceptions. |
| 3 | Test Coverage | Functions below 80%, missing edge case tests |
| 4 | Code Consistency | Same patterns across all packages |
| 5 | Dead Code | Unused exports, dead DB columns, unreferenced types. Remove them. "For a future loop" must cite the specific loop name and work item number. |
| 6 | Integration Wiring | Every interface has a real implementation. "Deferred" must name the specific blocker (loop + work item). |
| 7 | Security | Data corruption risks, injection patterns, unsafe fallbacks |

### Key Rules

- The review phase section in the PROMPT MUST include: "You NEVER write 'Loop Complete' or 'Loop Done' in the progress file. The human decides when the loop is done."
- **No rubber stamps.** Agents cannot mark findings as "INTENTIONAL" or "by design" without citing the specific DESIGN.md section or IMPLEMENTATION.md section number. No spec citation = defect to fix.
- **No self-referencing.** Each review cycle evaluates findings independently against the spec. "Same set as prior cycle" is not a valid assessment.
- **The spec is 100% mandatory.** The only valid deferral is when something is literally impossible in this loop (requires later loop infrastructure) AND the agent can cite the specific later loop work item.

See `reference.md` for the full review phase template text.

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Vague IMPLEMENTATION.md | If an agent would guess, it's not specific enough |
| Guessing at library APIs | Read actual library source code |
| Too many loops | 2-4 is typical. Combine if dependencies are tight. |
| Weak test descriptions | "test error handling" -> specific scenario with expected behavior |
| Skipping cross-validation | The reviewer catches real bugs. Always offer it. |
| Auto-progressing loops | User controls loop progression. Always. |
| PROMPT inventing types | Everything must trace to IMPLEMENTATION.md |
| No review phase | Agent runs out of work items and stops. Always include review phase. |
| Rubber-stamp reviews | Agent marks everything "INTENTIONAL" without spec citation. Tighten review category language with closed lists of acceptable patterns. |
| Self-referencing reviews | Agent says "same as prior cycle" instead of re-evaluating. Each cycle is independent. |
| Vague deferrals | "Deferred to Loop 3" without citing the specific work item. Require loop name + item number. |

## Red Flags

- IMPLEMENTATION.md says "use library X" without showing exact API calls
- Work item says "add tests" without listing specific test scenarios
- Loop N modifies Loop M's existing files (adding new files is OK)
- PROMPT defines interfaces not present in IMPLEMENTATION.md
- No reviewer offered at checkpoints
- Agent decides when a loop is "complete"
- PROMPT has no Review Phase section after work items
- Review log shows "0 findings" with "INTENTIONAL" items that don't cite spec sections
- Review log says "same set as prior cycle" — agent is coasting, not reviewing
- Dead code justified as "for future loop" without citing a specific work item number
