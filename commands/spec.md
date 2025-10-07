---
name: spec
description: Transform vague intent into precise, executable specifications through investigation, spike validation, and progressive refinement
---

# /spec - Specification Discovery & Validation

## Core Principles

1. **Investigate First** - Read code before asking
2. **Challenge Everything** - Surface contradictions, conflicts, complexity
3. **Stay Mission-Focused** - Prune tangents
4. **Learn Through Spikes** - Quick validation in /tmp
5. **Progressive Refinement** - Evolve artifacts, archive obsolete

---

## Artifact Structure

```
.spec/
├── MISSION.md          # Goal (never changes, 50-100 lines)
├── CONSTRAINTS.md      # Hard requirements
├── DISCOVERIES.md      # Learnings (pruned to <50 lines)
├── ARCHITECTURE.md     # Design (evolves, 50-100 lines)
├── SPIKE_RESULTS/      # Immutable spike results
├── ASSUMPTIONS.md      # Explicit assumptions to validate
└── SPEC.md            # Final spec for /conduct (10 required + 3 optional sections)
```

---

## Workflow

### Phase -1: Initial Assessment

**Get orientation (3-5 questions):**
1. New project or existing code?
2. High-level goal? (one sentence for MISSION.md)
3. Critical constraints?

**Create MISSION.md immediately**

### Phase 0: Auto-Investigation (Existing Projects Only)

**Check:**
- Project structure, tech stack, dependencies
- Existing patterns (auth, APIs, testing)
- Deployment setup, database/caching config

**Tools:** Read manifests, scan directories

### Phase 1: Challenge Mode

**Find ≥3 concerns:**
- Conflicts with existing code
- Hidden complexity
- Pain points from similar projects
- Missing requirements
- Underestimated difficulty
- Unstated assumptions

**Parallel investigation for unknowns:**
```
Task(investigator, "Investigate auth flow")
Task(investigator, "Investigate database schema")
Task(investigator, "Investigate error handling patterns")
```

**Present:**
```
🔴 CONFLICTS: [issues]
🔴 HIDDEN COMPLEXITY: [challenges]
⚠️ PAIN POINTS: [what goes wrong]
🔴 MISSING: [undefined requirements]
🔴 ASSUMPTIONS: [must validate]
📊 COMPLEXITY: X/10 - [why]

Questions: [3-5 strategic decisions]
```

### Phase 2: Strategic Dialogue

Ask about **tradeoffs and decisions**, NOT facts you can discover.

**GOOD:** "Two auth systems increases complexity. Unify or keep both?"
**BAD:** "What database?" (check settings.py)

### Phase 3: Discovery Loop

**Document in DISCOVERIES.md:**
```markdown
## Discovery: [Topic]
Date: [date]
Status: INVESTIGATING | RESOLVED | OBSOLETE

### Findings
- [key points]

### Gotchas
- [issues]
```

**Prune when >50 lines:**
- Archive OBSOLETE → .spec/archive/
- Promote RESOLVED → ARCHITECTURE.md
- Keep INVESTIGATING active

**Track in ASSUMPTIONS.md:**
```markdown
⚠️ ASSUMPTION: [statement]
Risk: [impact]
Validation: ASK USER | CHECKED | NEEDS SPIKE
```

### Phase 4: Spike Orchestration

**When to spike:**
- Complexity >6/10
- Unfamiliar tech
- Critical security/performance
- Multiple approaches
- Can't validate by investigation

**Multiple spikes (parallel):**
```
Send SINGLE message with MULTIPLE Task calls:
Task(spike-tester, "Validate approach A")
Task(spike-tester, "Validate approach B")
Task(spike-tester, "Validate approach C")
```

**Save:** `.spec/SPIKE_RESULTS/NNN_description.md`

### Phase 5: Architecture Evolution

**Update ARCHITECTURE.md:**
```markdown
# Architecture (vN - updated after spike)

## Approach
[Strategy]

## Components
[Name, purpose, responsibilities]

## Dependency Relationships
- component_a depends on: component_b, component_c
- component_b depends on: (none)

**Watch for circular dependencies**

## Data Flow
[Text diagram]

## Architectural Decisions
Decision: [choice]
Context: [why needed]
Alternatives: [options rejected]
Chosen: [selected]
Consequences: [impacts]

## Known Gotchas
[From spikes/discoveries]
```

### Phase 6: Scope Management

For each discovery:
- Serves MISSION.md? → Investigate
- Doesn't serve? → Note as "Future"
- Tangent? → Ask: "Expand scope?" (default: stay focused)

### Phase 7: Readiness Validation

**Checklist:**
- Mission clear, success measurable
- Constraints documented
- Critical unknowns resolved
- Architecture sound, gotchas documented
- No blocking questions
- Complexity understood
- No contradictions

**If ready, create SPEC.md** (see format in /conduct instructions)

**If not ready:** List what's missing

---

## SPEC.md Format

**10 Required Sections:**
1. Problem Statement
2. User Impact
3. Mission
4. Success Criteria
5. Requirements (IMMUTABLE)
6. Proposed Approach (EVOLVABLE)
7. Implementation Phases
8. Known Gotchas
9. Quality Requirements
10. Files to Create/Modify

**3 Optional Sections:**
11. Testing Strategy (recommended)
12. Custom Roles
13. Evolution Log

**Section names must be EXACT** (case-sensitive)

**Files section format:**
```
### New Files
- path/to/file.py
  - Purpose: [description]
  - Depends on: [files]
  - Complexity: Low|Med|High

### Modified Files
- path/to/file.py
  - Changes: [description]
  - Risk: Low|Med|High
```

---

## Context Management

**Keep focused:**
- MISSION.md: 50 lines (never changes)
- DISCOVERIES.md: <50 lines (prune regularly)
- ARCHITECTURE.md: 50-100 lines

**When bloated:**
- Archive obsolete → .spec/archive/
- Consolidate related
- Promote important → ARCHITECTURE.md

**For sub-agents:** Pass only relevant context

---

## Recovering from Failed /conduct

**If /conduct fails:**
1. Review what happened (check .spec/, partial implementation)
2. Update .spec/ docs (add gotchas, update constraints/assumptions)
3. Re-spike if approach failed
4. Update SPEC.md (fix assumptions, add gotchas, clarify ambiguities)
5. Document recovery in SPEC.md

**Key:** Failed orchestrations are learning opportunities

---

## Integration with /conduct and /solo

**Your SPEC.md feeds into /conduct:**
- SPEC.md is the contract for /conduct
- /conduct reads it for full orchestration (6 phases)
- /conduct requires SPEC.md (will fail if missing)

**What /conduct does with your SPEC.md:**
1. Parses SPEC.md → extracts components + dependencies
2. Detects circular dependencies (fails if found)
3. Creates production + test skeletons
4. Implements in dependency order
5. Runs comprehensive testing + validation (6 reviewers)
6. Uses worktrees for variant exploration

**For simpler tasks:**
- User can use /solo instead (no spec needed)
- /solo generates minimal BUILD spec internally
- /solo is streamlined but still validates properly

**Your job creating SPEC.md:**

**DO:**
- Think about component responsibilities/boundaries
- Document dependencies clearly
- Watch for circular dependencies
- Document architectural decisions with Context/Alternatives/Consequences
- Use EXACT section names
- Include "### New Files" and "### Modified Files" subsections

**DON'T:**
- Define exact function signatures (/conduct does this)
- Write implementation details (/conduct's job)
- Plan execution order (dependency graph handles this)
- Over-specify interfaces
- Use wrong section names

---

## Quality Gates

**Before proceeding:**
- Investigated thoroughly
- Challenged approach
- Validated with spikes (if complex)
- Documented gotchas
- Spec unambiguous

**Before SPEC.md:**
- No blocking unknowns
- Assumptions validated
- Architecture sound
- Strategic decisions made

---

## Critical Rules

**DO:**
- Investigate before asking
- Challenge before accepting
- Run spikes when uncertain
- Stay mission-focused
- Prune context regularly
- Document gotchas immediately
- Predict pain points
- Surface tradeoffs

**DON'T:**
- Ask questions you can answer by investigation
- Accept first idea uncritically
- Build production code in spec (spikes only)
- Chase tangents unless user asks
- Let context bloat
- Make strategic decisions for user (ask)
- Proceed with blocking unknowns
- Change mission unless user requests

---

**You are the perfect rubber duck - intelligent, thorough, creative within scope, brutally honest.**
