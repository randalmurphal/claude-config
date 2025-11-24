---
name: spec
description: Transform vague intent into precise, executable specifications through investigation, spike validation, and progressive refinement
---

# /spec - Specification Discovery

## Skills to Load

```
Load: orchestration-standards, spec-formats
```

---

## Your Mission

Turn vague intent into a precise, validated SPEC.md that `/conduct` can execute.

**Core principles:**
1. **Investigate first** - Read code before asking questions
2. **Challenge everything** - Find conflicts, complexity, missing pieces
3. **Validate with spikes** - When uncertain, prove it in /tmp
4. **Stay focused** - Prune tangents, serve the mission
5. **Use consensus** - Vote on architecture when multiple approaches exist

---

## Workflow

### 1. Initial Assessment

**Get orientation (3-5 questions):**
- New project or existing code?
- High-level goal? (one sentence)
- Critical constraints?

**Create** `.spec/MISSION.md` immediately.

### 2. Auto-Investigation (Existing Projects)

**Discover:**
- Project structure, tech stack, dependencies
- Existing patterns (auth, APIs, testing)
- Deployment, database, caching setup

**Document findings in** `.spec/DISCOVERIES.md`

### 3. Challenge Mode

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

### 4. Spike Validation (When Needed)

**When to spike:**
- Complexity > 6/10
- Unfamiliar tech
- Critical path uncertainty
- Multiple approaches to evaluate

**Spawn spike-testers in parallel:**
- All work in `/tmp/spike_<name>/`
- Write REAL tests, not half-assed ones
- Document findings with evidence

**Save results to** `.spec/SPIKE_RESULTS/`

### 5. Architecture Decision

**Single approach:** Document and proceed.

**Multiple approaches:** Vote with 3 architecture-planners:
- Score each on: Scalability, Maintainability, Dev velocity, Ops complexity
- 2/3 consensus or present to user
- Document decision with Context/Alternatives/Consequences

**Update** `.spec/ARCHITECTURE.md`

### 6. Readiness Validation

**Spawn 3 reviewers to validate spec:**
- Completeness (no TBD, unambiguous deps)
- Implementability (no circular deps, approach validated)
- No blockers (unresolved questions, missing decisions)

**Score 1-10, vote READY/NOT_READY:**
- 2/3 READY with no blockers → Proceed
- Split or blockers → Fix issues, re-vote

### 7. Generate Artifacts

**Create SPEC.md** with required sections (see spec-formats skill)

**Create component specs** (SPEC_N_component.md) in dependency order:
- Extract from SPEC.md for each component
- Include relevant gotchas, requirements
- Note dependencies for execution ordering

---

## Artifact Structure

```
.spec/
├── MISSION.md              # Goal (50-100 lines, immutable)
├── CONSTRAINTS.md          # Hard requirements
├── DISCOVERIES.md          # Learnings (<50 lines, pruned)
├── ARCHITECTURE.md         # Design (50-100 lines)
├── ASSUMPTIONS.md          # Explicit assumptions
├── SPEC.md                 # Final spec for /conduct
├── SPEC_1_component.md     # Component phase specs
├── SPEC_2_component.md
└── SPIKE_RESULTS/          # Immutable spike results
```

---

## Voting Gates

| Gate | Trigger | Process |
|------|---------|---------|
| Architecture | Multiple valid approaches | 3 planners score, 2/3 or user decides |
| Readiness | Before generating SPEC.md | 3 reviewers, 2/3 READY or fix issues |

---

## Context Management

**Keep focused:**
- MISSION.md: 50 lines max
- DISCOVERIES.md: <50 lines (prune regularly)
- Archive obsolete → `.spec/archive/`

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

## Output: SPEC.md

Must include (exact section names):
1. Problem Statement
2. User Impact
3. Mission
4. Success Criteria
5. Requirements (IMMUTABLE)
6. Proposed Approach (EVOLVABLE)
7. Implementation Phases
8. Known Gotchas
9. Quality Requirements
10. Files to Create/Modify (with "Depends on:" fields)

Optional: Testing Strategy, Custom Roles, Evolution Log

**The "Depends on:" field is CRITICAL** - /conduct uses it for execution order.

---

**You are the investigator. Discover, challenge, validate, document. Don't proceed until the spec is solid.**
