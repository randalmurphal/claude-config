---
name: spec
description: Transform vague intent into precise, executable specifications through investigation, spike validation, and progressive refinement
---

# /spec - Specification Discovery

## Your Mission

Turn vague intent into a validated, executable spec stored in `~/.claude/orchestrations/specs/`.

**Core principles:**
1. **Investigate first** - Read code before asking questions
2. **Challenge everything** - Find conflicts, complexity, missing pieces
3. **Validate with spikes** - When uncertain, prove it in /tmp
4. **Stay focused** - Prune tangents, serve the mission
5. **Use consensus** - Vote on architecture when multiple approaches exist

---

## Phase 1: Setup

### Determine Working Directory
- Search for relevant files/directories mentioned in task
- If task mentions specific component/service → that's the work_dir
- If unclear: ask user

### Create Spec Directory
```bash
python -m orchestrations new --project <project_name> --name <spec_name>
```

This creates:
```
~/.claude/orchestrations/specs/<project>/<name>-<hash>/
├── brainstorm/
├── components/
└── SPEC.md
```

**Set `$SPEC_DIR`** = the created directory path

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

Once brainstorm is complete, tell user:

```
Brainstorm complete. Ready to formalize into executable spec.

This will:
1. Convert brainstorm artifacts to manifest.json
2. Validate against schemas (dependencies, required fields)
3. Create component context files

Proceed? [Y/n]
```

If yes, the formalizer converts brainstorm to manifest:
- Reads MISSION.md, INVESTIGATION.md, DECISIONS.md, CONCERNS.md
- Generates manifest.json with components, dependencies, execution config
- Validates with Python (cycles, required fields, consistency)
- Creates component context files

**If validation fails:** Show specific errors, fix, retry.

---

## Phase 5: Completion

Once formalized, tell user:

```
✅ Spec created: <project>/<name>-<hash>

Summary:
- Components: N
- Complexity: X/10
- Risk: LOW/MEDIUM/HIGH
- Estimated reviewers: N

To validate:
  python -m orchestrations validate --spec <project>/<name>

To execute:
  python -m orchestrations run --spec <project>/<name>

To check status:
  python -m orchestrations status --spec <project>/<name>
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

---

## Guardrails

**DO:**
- Investigate before asking
- Challenge before accepting
- Spike when uncertain
- Document gotchas immediately
- Use voting for critical decisions

**DON'T:**
- Ask questions you can answer by investigation
- Accept first approach uncritically
- Build production code (spikes only)
- Chase tangents
- Proceed with blocking unknowns
- Skip voting when multiple approaches exist

---

## Output: manifest.json

The formalization creates a machine-readable manifest with:
- `name`, `project`, `work_dir`
- `complexity` (1-10), `risk_level`
- `components` with dependencies
- `execution` config (mode, reviewers, gates)
- `gotchas` list

This drives the execution phase via `python -m orchestrations run`.

---

**You are the investigator. Discover, challenge, validate, document. Don't proceed until ready for formalization.**
