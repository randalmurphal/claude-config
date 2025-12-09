---
name: spec
description: Transform vague intent into precise, executable specifications through investigation, spike validation, and progressive refinement
---

# /spec - Specification Discovery

## Your Mission

Turn vague intent into a validated, executable spec stored in `~/.claude/cc_orchestrations/specs/`.

**Core principles:**
1. **Investigate first** - Read code before asking questions
2. **Challenge everything** - Find conflicts, complexity, missing pieces
3. **Validate with spikes** - When uncertain, prove it in /tmp
4. **Stay focused** - Prune tangents, serve the mission
5. **Use consensus** - Vote on architecture when multiple approaches exist

---

## Phase 1: Setup

### Determine Working Directory
- You should be in the project root (e.g., `m32rimm/`)
- If task mentions specific component/service → note it for later
- If unclear: ask user which project

### Create Spec Directory

Create the spec directory structure in the project:
```
<project>/.claude/specs/<name>-<hash>/
├── brainstorm/
│   ├── MISSION.md
│   ├── INVESTIGATION.md
│   ├── DECISIONS.md
│   └── CONCERNS.md
├── components/
├── SPEC.md
└── manifest.json (created in Phase 4)
```

Use Bash to create:
```bash
mkdir -p .claude/specs/<name>-<hash>/brainstorm
mkdir -p .claude/specs/<name>-<hash>/components
```

**Set `$SPEC_DIR`** = `.claude/specs/<name>-<hash>/`

---

## Phase 2: Brainstorm (Interactive)

### 2.1 Initial Assessment

**Get orientation (3-5 questions):**
- New project or existing code?
- High-level goal? (one sentence)
- Critical constraints?

**Create** `$SPEC_DIR/brainstorm/MISSION.md` immediately.

### 2.2 Auto-Investigation (Existing Projects)

**Discover:**
- Project structure, tech stack, dependencies
- Existing patterns (auth, APIs, testing)
- Deployment, database, caching setup

**Document in** `$SPEC_DIR/brainstorm/INVESTIGATION.md`

### 2.3 Challenge Mode

**Find ≥3 concerns:**
- Conflicts with existing code
- Hidden complexity
- Missing requirements
- Unstated assumptions

**Present complexity assessment:**
```
🔴 CONFLICTS: [issues]
🔴 HIDDEN COMPLEXITY: [challenges]
⚠️ PAIN POINTS: [what goes wrong]
🔴 MISSING: [undefined requirements]
📊 COMPLEXITY: X/10 - [why]
```

**For unknowns:** Spawn parallel investigators

**Document in** `$SPEC_DIR/brainstorm/CONCERNS.md`

### 2.4 Spike Validation (When Needed)

**When to spike:**
- Complexity > 6/10
- Unfamiliar tech
- Critical path uncertainty
- Multiple approaches to evaluate

**Spawn spike-testers in parallel:**
- All work in `/tmp/spike_<name>/`
- Write REAL tests, not half-assed ones
- Document findings with evidence

**Save results to** `$SPEC_DIR/brainstorm/SPIKE_RESULTS/`

### 2.5 Architecture Decision

**Single approach:** Document and proceed.

**Multiple approaches:** Vote with 3 architecture-planners:
- Score each on: Scalability, Maintainability, Dev velocity, Ops complexity
- 2/3 consensus or present to user
- Document decision with Context/Alternatives/Consequences

**Document in** `$SPEC_DIR/brainstorm/DECISIONS.md`

---

## Phase 3: Readiness Validation

**Spawn 3 reviewers to validate brainstorm artifacts:**
- Completeness (no TBD, clear understanding)
- Implementability (approach is sound)
- No blockers (unresolved questions, missing decisions)

**Score 1-10, vote READY/NOT_READY:**
- 2/3 READY with no blockers → Proceed to formalization
- Split or blockers → Fix issues, re-vote

---

## Phase 4: Formalization

Once brainstorm is complete, assess execution configuration BEFORE formalizing.

### 4.1 Parallelization Assessment

Analyze component dependencies and determine parallel groups:

```
For each component:
1. Identify all dependencies
2. Assign parallel_group = max(dependencies' groups) + 1
3. Components with no deps → Group 0

Parallel safety check:
- Components in same group MUST NOT write to same file
- skeleton + test-skeleton: ALWAYS parallelizable
- implementation + test: Parallelizable if isolated
```

Document in DECISIONS.md:
```markdown
## Parallelization Decision

**Parallel Groups:**
- Group 0: [A, B] - no dependencies, run in parallel
- Group 1: [C, D] - depend on group 0, run in parallel
- Group 2: [E] - depends on C and D

**Phase Parallelization:**
- skeleton_parallel: true (skeleton + test-skeleton)
- implementation_parallel: true (impl + test in parallel)
- validation_parallel: false (validators may edit)
```

### 4.2 Agent Configuration (Project-Specific)

**For m32rimm projects**, check which validators are needed:

| Validator | Trigger Condition | Add If |
|-----------|-------------------|--------|
| `mongo_validator` | db., pymongo, DBOpsHelper, retry_run | Any MongoDB ops |
| `import_validator` | imports/, data_importer | Import framework |
| `bo_structure_validator` | upsert_bo, BOUpsert | BO creation |
| `general_validator` | Always | All code |
| `finding_validator` | Always | Filter false positives |

Document in DECISIONS.md:
```markdown
## Agent Selection

**Project validators:**
- mongo_validator: component X uses DBOpsHelper
- import_validator: component Y is in imports/
- general_validator: all components

**Model overrides:**
- [component_id]: opus (requires complex judgment)
```

### 4.3 Risk Assessment

Calculate risk score (5-15):

| Factor | Low (1) | Medium (2) | High (3) |
|--------|---------|------------|----------|
| Files | 1-3 | 4-10 | 10+ |
| API exposure | Internal | Service | Public |
| Data ops | Read | Create/Update | Delete |
| Auth/security | None | Uses existing | New |
| Breaking | None | Backward compat | Breaking |

**Risk Score → Reviewers:**
- 5-7: Low → 2 reviewers
- 8-10: Medium → 4 reviewers
- 11-13: High → 6 reviewers
- 14-15: Critical → 6 + human checkpoint

### 4.4 Formalize

Once execution config is determined, tell user:

```
Ready to formalize into executable spec.

Execution Configuration:
- Parallel Groups: [show groups]
- Validators: [list active validators]
- Risk Score: X/15 ([level])
- Reviewers: N
- Voting Gates: [list]

This will create manifest.json with all configs.
Proceed? [Y/n]
```

If yes, the formalizer converts brainstorm to manifest:
- Reads MISSION.md, INVESTIGATION.md, DECISIONS.md, CONCERNS.md
- Generates manifest.json with components, dependencies, parallelization, agents
- Validates: cycles, required fields, parallel safety, consistency
- Creates component context files

**If validation fails:** Show specific errors, fix, retry.

---

## Phase 5: Draft Validation

**Purpose:** Validate the spec actually works by running a fast draft implementation.

### 5.1 Initiate Draft Run

After formalization, tell user:

```
📝 Spec formalized. Now let's validate it with a draft run.

The draft run uses Composer for ALL agents - fast but imperfect.
It creates real code to verify your spec instructions work.
Commits are prefixed with [DRAFT] for easy identification.

Run this command (in another terminal or here):
  cd <worktree_path> && python3 -m cc_orchestrations.conduct run --draft --spec <spec_path>

Let me know when it's done and I'll review the results.
```

**WAIT for user.** Do not proceed until user confirms draft is complete.

### 5.2 Review Draft Results

When user says draft is done, analyze the commit history:

```bash
# Get conduct commits from the worktree
git log --oneline --grep="\[conduct\]" | head -30
```

**Parse commit patterns:**
- `[DRAFT] [conduct] skeleton: <file>` → Skeleton created
- `[DRAFT] [conduct] implementation: <file>` → Implementation done
- `[DRAFT] [conduct] validation: <file>` → Validation passed
- `[DRAFT] [conduct] validation-blocked: <file>` → ⚠️ PROBLEM

**For each validation-blocked commit:**
1. Check the state file: `<worktree>/.spec/STATE.json`
2. Look at `components.<file>.error` for the failure reason
3. Check `components.<file>.issues` for validation issues

### 5.3 Diagnose Spec Issues

**Common patterns that indicate spec problems:**

| Symptom | Likely Spec Issue |
|---------|-------------------|
| Blocked at skeleton | Missing dependencies, unclear component purpose |
| Blocked at implementation | Spec instructions ambiguous, missing context |
| Blocked at validation | Quality requirements unclear, missing gotchas |
| Multiple components blocked | Architectural decision was wrong |
| Same issue across files | Missing global context/gotcha |

**Report to user:**
```
📊 Draft Run Analysis:

Components: N total
✅ Completed: X
⚠️ Blocked: Y

Issues Found:
1. [file.py] blocked at [phase]: [reason]
   → Spec issue: [diagnosis]
   → Fix: [specific change to spec]

2. [another.py] blocked at [phase]: [reason]
   → Spec issue: [diagnosis]
   → Fix: [specific change to spec]
```

### 5.4 Fix and Re-validate

**If issues found:**
1. Update the spec files (SPEC.md, manifest.json, component contexts)
2. Tell user: "Spec updated. Run draft again to verify fixes."
3. Return to 5.1

**If clean run (all components completed):**
```
✅ Draft validation passed!

All N components completed successfully.
The spec instructions are validated and ready for full execution.

Proceeding to finalization...
```

→ Proceed to Phase 6.

---

## Phase 6: Completion

Once draft validation passes, tell user:

```
✅ Spec VALIDATED: <project>/<name>-<hash>

Summary:
- Components: N (in M parallel groups)
- Complexity: X/10
- Risk: [score]/15 ([level])
- Reviewers: N
- Draft validation: PASSED ✅

Parallelization:
- Group 0: [components] (parallel)
- Group 1: [components] (after group 0)
...

Validators Active:
- [list of validators for this spec]

Execution:
- skeleton_parallel: true/false
- implementation_parallel: true/false

To execute FULL run:
  cd <worktree_path> && python3 -m cc_orchestrations.conduct run --spec <spec_path>

Note: Full run uses Opus/Sonnet for quality. Draft commits should be reset first:
  git reset --hard HEAD~N  (where N = number of [DRAFT] commits)
```

---

## Brainstorm Artifact Formats

### MISSION.md (50-100 lines)
```markdown
# Mission

## Goal
[One sentence]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Non-Goals
- Thing we're NOT doing
```

### INVESTIGATION.md
```markdown
# Investigation Findings

## Project Structure
[What we found]

## Existing Patterns
[Auth, API, testing patterns]

## Dependencies
[External deps, internal deps]

## Blast Radius
[What this change affects]
```

### DECISIONS.md
```markdown
# Architectural Decisions

## Decision 1: [Topic]
**Choice:** [What we chose]
**Rationale:** [Why]
**Alternatives Considered:** [What else we looked at]
**Consequences:** [Trade-offs accepted]
```

### CONCERNS.md
```markdown
# Concerns & Gotchas

## Conflicts
- [Issue 1]

## Hidden Complexity
- [Challenge 1]

## Assumptions
- [Assumption 1] - VALIDATED/NEEDS_SPIKE/ASK_USER
```

---

## Voting Gates

| Gate | Trigger | Process |
|------|---------|---------|
| Architecture | Multiple valid approaches | 3 planners score, 2/3 or user decides |
| Readiness | Before formalization | 3 reviewers, 2/3 READY or fix issues |
| Draft Validation | After formalization | Run `--draft`, review commits, fix spec if blocked |

---

## Guardrails

**DO:**
- Investigate before asking
- Challenge before accepting
- Spike when uncertain
- Document gotchas immediately
- Use voting for critical decisions
- Run draft validation before declaring spec "ready"

**DON'T:**
- Ask questions you can answer by investigation
- Accept first approach uncritically
- Build production code (spikes only, draft uses Composer)
- Chase tangents
- Proceed with blocking unknowns
- Skip voting when multiple approaches exist
- Skip draft validation - specs MUST be validated before full run

---

## Output: manifest.json

The formalization creates a machine-readable manifest with:
- `name`, `project`, `work_dir`
- `complexity` (1-10), `risk_level`
- `components` with dependencies
- `execution` config (mode, reviewers, gates)
- `gotchas` list

This drives the execution phase.

---

**You are the investigator. Discover, challenge, validate, document. Don't proceed until draft validation passes.**
