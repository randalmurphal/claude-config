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
6. **Consensus Decisions** - 3-agent voting for critical choices

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

### Phase 1: Load Agent Prompting Skill

**CRITICAL: Load before spawning any sub-agents (investigators, spike-testers).**

```
Skill: agent-prompting
```

**This skill contains:**
- Critical inline standards for each agent type
- What to include in prompts (especially spike-tester requirements)
- Prompt templates with examples

**You will use this throughout /spec when spawning investigators and spike-testers.**

---

### Phase 2: Determine Working Directory

**Infer from task description which directory/component is being worked on:**
- Search for relevant files/directories mentioned in task
- Check project structure (e.g., monorepo with services/api/, services/auth/)
- If task mentions specific component/service → that's the working dir

**If unclear after search, ask:**
"Which directory should I work in? (provide path relative to repo root, or '.' for current)"

**Once determined:**
- `$WORK_DIR` = that directory
- Create `.spec/` at `$WORK_DIR/.spec/`
- All paths relative to `$WORK_DIR`

---

### Phase 3: Initial Assessment

**Get orientation (3-5 questions):**
1. New project or existing code?
2. High-level goal? (one sentence for MISSION.md)
3. Critical constraints?

**Create MISSION.md immediately**

**Commit changes** (pre-commit validation runs automatically if in git repo)

### Phase 4: Auto-Investigation (Existing Projects Only)

**Check:**
- Project structure, tech stack, dependencies
- Existing patterns (auth, APIs, testing)
- Deployment setup, database/caching config

**Tools:** Read manifests, scan directories

**Commit changes** (document findings in DISCOVERIES.md)

### Phase 5: Challenge Mode

**Find ≥3 concerns:**
- Conflicts with existing code
- Hidden complexity
- Pain points from similar projects
- Missing requirements
- Underestimated difficulty
- Unstated assumptions

**Parallel investigation for unknowns:**
```
Send SINGLE message with MULTIPLE Task calls:

Task(general-investigator, """
Investigate auth flow.

CRITICAL STANDARDS (from agent-prompting skill):
- Start narrow, expand if needed
- Use Grep before Read
- Don't read >5 files without reporting
- Include file:line references

Objective: Understand how JWT authentication works in this codebase.
""")

Task(general-investigator, "Investigate database schema...")
Task(general-investigator, "Investigate error handling patterns...")
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

**Commit changes** (document in DISCOVERIES.md)

### Phase 6: Strategic Dialogue

Ask about **tradeoffs and decisions**, NOT facts you can discover.

**GOOD:** "Two auth systems increases complexity. Unify or keep both?"
**BAD:** "What database?" (check settings.py)

### Phase 7: Discovery Loop

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

**Commit changes** after significant discoveries

### Phase 8: Spike Orchestration

**When to spike:**
- Complexity >6/10
- Unfamiliar tech
- Critical security/performance
- Multiple approaches
- Can't validate by investigation

**Multiple spikes (parallel) with critical standards:**
```
Send SINGLE message with MULTIPLE Task calls:

Task(spike-tester, """
Validate approach A: [specific assumption to test]

CRITICAL STANDARDS (from agent-prompting skill):
- All work in /tmp/spike_<name>/
- Write LEGITIMATE tests - NO half-assed tests, NO workarounds allowed
- If you can't test something properly, EXPLAIN WHY in detail
- Tests must use proper mocking, proper assertions, proper structure
- Same quality standards as production tests (just throwaway location)
- Document findings clearly with evidence from test results

Load testing-standards skill.

Goal: [what to prove/disprove]
""")

Task(spike-tester, """
Validate approach B: [specific assumption to test]

[Same critical standards as above]

Goal: [what to prove/disprove]
""")
```

**Save:** `.spec/SPIKE_RESULTS/NNN_description.md`

**Commit changes** (archive spike results)

### Phase 9: Architecture Evolution with Voting

**VOTING GATE 1: Architecture Decision Voting**

**When to use voting:**
- Multiple valid approaches exist OR
- Complexity > 6/10 OR
- High-stakes decision (security, scalability, maintainability)

**Single-approach scenario (no voting needed):**
```
IF only_one_viable_approach:
  Update ARCHITECTURE.md with single approach
  Document decision rationale
  Skip voting, proceed to Phase 10
```

**Multi-approach scenario (requires voting):**
```
IF multiple_approaches OR complexity > 6:
  # Spawn 3 architecture evaluators in PARALLEL (single message, 3 Task calls)

  For each approach (A, B, C...):
    Task(architecture-planner, """
    Evaluate Approach {X}: {approach_name}

    Approach description:
    {detailed description from spikes/discoveries}

    Score 1-10 on these weighted criteria:
    - Scalability (weight: 0.30)
    - Maintainability (weight: 0.30)
    - Development velocity (weight: 0.20)
    - Operational complexity (weight: 0.20)

    For each criterion:
    - Score with justification
    - Specific examples from codebase/research
    - Comparison to alternatives

    Return JSON:
    {
      "approach": "{X}",
      "scores": {
        "scalability": X,
        "maintainability": Y,
        "dev_velocity": Z,
        "operational_complexity": W
      },
      "weighted_total": calculated_score,
      "rationale": "Why this score...",
      "risks": ["risk 1", "risk 2"],
      "tradeoffs": ["tradeoff 1", "tradeoff 2"]
    }
    """)

  # Consolidate votes
  results = [agent1_result, agent2_result, agent3_result]

  # Group by approach
  scores_by_approach = {}
  for result in results:
    approach = result["approach"]
    if approach not in scores_by_approach:
      scores_by_approach[approach] = []
    scores_by_approach[approach].append(result["weighted_total"])

  # Calculate average scores
  avg_scores = {
    approach: sum(scores) / len(scores)
    for approach, scores in scores_by_approach.items()
  }

  # Determine winner
  winner = max(avg_scores, key=avg_scores.get)
  runner_up = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)[1]

  margin = (avg_scores[winner] - runner_up[1]) / avg_scores[winner]

  # Decision based on consensus
  IF margin < 0.15:  # Scores within 15% (close call)
    Present to user:
    """
    🗳️ ARCHITECTURE VOTING: CLOSE DECISION

    Approach {winner}: {avg_scores[winner]:.1f}/10
    Approach {runner_up[0]}: {runner_up[1]:.1f}/10

    Margin: {margin*100:.0f}% (too close for automatic decision)

    === Approach {winner} ===
    Pros: [consolidated from 3 evaluations]
    Cons: [consolidated]
    Risks: [consolidated]

    === Approach {runner_up[0]} ===
    Pros: [consolidated]
    Cons: [consolidated]
    Risks: [consolidated]

    Recommendation: {winner} (slight edge), but {runner_up[0]} is viable alternative.

    Your decision?
    """

    User decides, document choice

  ELSE:  # Clear winner (margin >= 15%)
    Document decision:
    """
    ✅ ARCHITECTURE DECISION: {winner}

    Consensus score: {avg_scores[winner]:.1f}/10
    Runner-up: {runner_up[0]} ({runner_up[1]:.1f}/10)
    Confidence: {(1-margin)*100:.0f}%

    Rationale:
    [Consolidated from 3 independent evaluations]

    Approaches considered:
    {list all approaches with scores}

    Decision: Proceed with {winner}
    """

    Proceed automatically with winner
```

**Update ARCHITECTURE.md:**
```markdown
# Architecture (vN - updated after voting)

## Chosen Approach
[Winner from voting]

## Approach
[Strategy details]

## Components
[Name, purpose, responsibilities]

## Dependency Relationships
- component_a depends on: component_b, component_c
- component_b depends on: (none)

**Watch for circular dependencies**

## Data Flow
[Text diagram]

## Architectural Decisions
Decision: [approach chosen]
Context: [why decision needed]
Alternatives Evaluated: [list with scores from voting]
Voting Results:
- Approach A: X.X/10 (rationale)
- Approach B: Y.Y/10 (rationale)
- Approach C: Z.Z/10 (rationale)
Chosen: [winner] (margin: XX%, consensus: HIGH/MEDIUM/LOW)
Consequences: [impacts, tradeoffs accepted]

## Known Gotchas
[From spikes/discoveries]

## Risks
[From voting evaluation]
```

**Commit changes**

---

### Phase 10: Scope Management

For each discovery:
- Serves MISSION.md? → Investigate
- Doesn't serve? → Note as "Future"
- Tangent? → Ask: "Expand scope?" (default: stay focused)

### Phase 11: Documentation Library Setup

**Goal:** Create AI-readable documentation structure if it doesn't exist, before finalizing spec.

**Check for existing documentation library:**
```bash
# Check for docs/ directory and key files
ls $WORK_DIR/docs/llms.txt 2>/dev/null
ls $WORK_DIR/CLAUDE.md 2>/dev/null
```

**IF documentation library missing OR incomplete:**

1. **Invoke ai-documentation skill** to load best practices:
   ```
   Skill: ai-documentation
   ```

2. **Create minimal documentation structure:**
   ```
   $WORK_DIR/
   ├── CLAUDE.md                # Quick reference (use ~/.claude/docs/AI_DOCUMENTATION_STANDARDS.md templates)
   └── docs/                    # Optional: For complex tools only
       ├── llms.txt            # AI navigation index
       ├── OVERVIEW.md         # <5 min mental model
       └── business_logic/     # Critical business rules
   ```

3. **Populate CLAUDE.md** using appropriate template:
   - **Simple Tool** (~200 lines): Purpose, patterns, config, gotchas
   - **Complex Tool** (300-400 lines): + architecture, business logic table
   - Follow hierarchical inheritance (don't duplicate parent content)
   - Include file:line refs for critical functions
   - Reference ai-documentation skill for standards

4. **Create llms.txt** (if complex tool with docs/ directory):
   - Links to all documentation with descriptions
   - Quick start section at top
   - Business logic, architecture, guides sections

5. **Defer detailed docs to post-implementation:**
   - Don't write detailed API_REFERENCE.md yet (functions don't exist)
   - Don't write HOW_TO.md yet (workflows unknown)
   - Mark these as "TODO: Create after /conduct Phase N+2"

**Documentation library complete criteria:**
- ✅ CLAUDE.md exists with basic structure
- ✅ Follows hierarchical inheritance (no parent duplication)
- ✅ Line count within target for hierarchy level
- ✅ llms.txt exists (if docs/ directory created)
- ✅ Clear TODOs for post-implementation docs

**Note for user:**
```
📚 Documentation library created. Detailed docs (API_REFERENCE, HOW_TO, etc.)
will be generated after implementation in /conduct Phase N+2.
```

**Commit changes**

---

### Phase 12: Readiness Validation with Voting

**VOTING GATE 2: Spec Readiness Voting**

**Goal:** Ensure spec is complete, unambiguous, implementable before /conduct starts.

**Initial checklist:**
- Mission clear, success measurable
- Constraints documented
- Critical unknowns resolved
- Architecture sound, gotchas documented
- No blocking questions
- Complexity understood
- No contradictions
- Documentation library exists (CLAUDE.md + optional docs/)

**Spawn 3 spec reviewers in PARALLEL:**
```
Task(general-investigator, """
Review SPEC.md and all .spec/ artifacts for completeness and readiness for /conduct.

Artifacts to review:
- MISSION.md
- CONSTRAINTS.md
- DISCOVERIES.md
- ARCHITECTURE.md
- ASSUMPTIONS.md
- SPEC.md (if created)

Check for:
1. Completeness:
   - All requirements unambiguous (no "TBD", "maybe", "probably")
   - Dependencies complete with "Depends on:" fields
   - Success criteria measurable (specific metrics)
   - Known gotchas documented

2. Implementability:
   - Architecture feasible with documented tradeoffs
   - No circular dependencies in component graph
   - All external dependencies identified
   - Technical approach validated (spikes complete)

3. Blockers:
   - No unresolved critical questions
   - No missing architectural decisions
   - No unstated assumptions
   - No scope ambiguity

Score readiness 1-10:
- 9-10: Ready for immediate /conduct
- 7-8: Minor gaps, easy fixes
- 4-6: Significant gaps, requires work
- 1-3: Major issues, not ready

Return JSON:
{
  "score": X,
  "vote": "READY" | "NOT_READY",
  "gaps": ["gap 1", "gap 2"],
  "blockers": ["blocker 1", "blocker 2"],
  "missing": ["missing 1", "missing 2"],
  "recommendations": ["rec 1", "rec 2"]
}

Vote READY if score >= 8 AND no critical blockers.
Vote NOT_READY otherwise.
""")

# Similar for 2 more reviewers (same prompt, independent evaluation)
```

**Consolidate votes:**
```
votes = [reviewer1_vote, reviewer2_vote, reviewer3_vote]
ready_count = sum(1 for v in votes if v["vote"] == "READY")

# Consolidate findings
all_gaps = consolidate_unique([v["gaps"] for v in votes])
all_blockers = consolidate_unique([v["blockers"] for v in votes])
all_missing = consolidate_unique([v["missing"] for v in votes])

avg_score = sum([v["score"] for v in votes]) / 3
```

**Decision based on consensus:**
```
IF ready_count >= 2 AND len(all_blockers) == 0:
  # 2/3 consensus: READY
  ✅ SPEC READINESS: APPROVED

  Consensus: {ready_count}/3 vote READY
  Average score: {avg_score:.1f}/10

  Minor gaps identified (non-blocking):
  {list all_gaps if any}

  Recommendations for /conduct:
  {consolidated recommendations}

  ✅ Ready to proceed with /conduct

  # Create SPEC.md and component phase specs (see format below)

ELIF ready_count == 0:
  # Unanimous NOT_READY
  ❌ SPEC READINESS: BLOCKED

  Consensus: 0/3 vote READY (unanimous rejection)
  Average score: {avg_score:.1f}/10

  Critical blockers:
  {list all_blockers}

  Gaps:
  {list all_gaps}

  Missing:
  {list all_missing}

  Required fixes:
  {consolidated recommendations from all 3 reviewers}

  ❌ Must fix blockers before /conduct

  STOP - address issues, then re-run Phase 12 voting

ELSE:
  # Split vote (1-2 or 2-1)
  ⚠️ SPEC READINESS: SPLIT DECISION

  Votes: {ready_count}/3 vote READY
  Average score: {avg_score:.1f}/10

  === Reviewers voting READY ===
  {summarize ready votes}

  === Reviewers voting NOT_READY ===
  Blockers: {list blockers}
  Gaps: {list gaps}
  Concerns: {list concerns}

  Recommendation:
  IF len(all_blockers) > 0:
    "Address critical blockers before proceeding"
  ELSE:
    "Minor gaps exist but likely can proceed with caution"

  User decides: Proceed or fix gaps?
```

**If approved, create SPEC.md and component phase specs** (see format below)

**If not ready:** Fix identified issues, then re-run Phase 12 voting

**Commit changes** (final spec artifacts)

---

## SPEC.md Format (High-Level Architecture)

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
11. Testing Strategy (recommended - see `~/.claude/docs/TESTING_STANDARDS.md`)
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

**IMPORTANT:** The "Depends on:" field is CRITICAL. /conduct uses it to build dependency graph and determine component execution order.

---

## Component Phase Specs (SPEC_N_component.md)

**After creating SPEC.md, generate component phase specs for /conduct:**

For each component in dependency order (topologically sorted):

Create `.spec/SPEC_{phase_num}_{component_name}.md`:

```markdown
# Phase {N}: {Component Name}

## Components in This Phase
- {file_path}
  - Purpose: {from SPEC.md}
  - Complexity: {from SPEC.md}

## Dependencies
{What this component depends on from previous phases}

## What's Available from Previous Phases
{Initially empty - /conduct will populate as phases complete}

## Success Criteria
{Extract from SPEC.md for this component}
- Component compiles without errors
- Unit tests pass with 95%+ coverage
- All validation checks pass
- No linter warnings

## Known Gotchas
{Extract from SPEC.md "Known Gotchas" section relevant to this component}
{/conduct will enhance this as earlier phases complete}

## Implementation Requirements
{Extract from SPEC.md "Proposed Approach" and "Requirements" relevant to this component}

## Testing Requirements
{Extract from SPEC.md "Testing Strategy" relevant to this component}

Follow `~/.claude/docs/TESTING_STANDARDS.md`:
- Unit test: 1:1 file mapping (one test file for this component)
- Coverage: 95%+ for all public functions
- Test happy path + error cases + edge cases
- Choose test organization: single function, parametrized, or separate methods

Edge cases for this component:
{list relevant edge cases}

Error scenarios for this component:
{list error scenarios}
```

**Why generate these during /spec:**
- You understand the architecture and component boundaries
- You've validated dependencies through investigation
- You know which gotchas affect which components
- /conduct can focus on execution, not architecture decisions

**Result structure:**
```
.spec/
├── MISSION.md
├── CONSTRAINTS.md
├── DISCOVERIES.md
├── ARCHITECTURE.md
├── ASSUMPTIONS.md
├── SPEC.md                        # High-level architecture
├── SPEC_1_foundation.md          # Component 1 details
├── SPEC_2_database.md            # Component 2 details
├── SPEC_3_api.md                 # Component 3 details
├── ...
└── SPIKE_RESULTS/
```

**Dependency order example:**
```
Component dependencies from SPEC.md:
- auth.py: depends on (none)
- database.py: depends on (none)
- api.py: depends on auth.py, database.py
- frontend.py: depends on api.py

Topological sort (execution order):
1. auth.py, database.py (parallel - no dependencies)
2. api.py (depends on 1)
3. frontend.py (depends on 2)

Generate:
- SPEC_1_auth.md + SPEC_1_database.md (can be parallel)
- SPEC_2_api.md
- SPEC_3_frontend.md
```

**Commit changes**

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

**Commit changes** after pruning

---

## Recovering from Failed /conduct

**If /conduct fails:**
1. Review what happened (check .spec/, partial implementation)
2. Update .spec/ docs (add gotchas, update constraints/assumptions)
3. Re-spike if approach failed
4. Update SPEC.md (fix assumptions, add gotchas, clarify ambiguities)
5. Re-run Phase 12 voting to validate fixes
6. Document recovery in SPEC.md

**Key:** Failed orchestrations are learning opportunities

**Commit changes** (updated learnings)

---

## Integration with /conduct and /solo

**Your SPEC.md feeds into /conduct:**
- SPEC.md is the contract for /conduct
- /conduct reads it for full orchestration (6 phases)
- /conduct requires SPEC.md (will fail if missing)

**What /conduct does with your SPEC.md:**
1. Parses SPEC.md → extracts components + dependencies
2. Validates component phase specs exist (SPEC_N_*.md) or generates fallback
3. Detects circular dependencies (fails if found)
4. For each component in dependency order:
   - Creates skeleton
   - Implements component
   - Validates & fixes (6 reviewers + voting gates)
   - Unit tests (95%+ coverage with voting gate)
   - Documents discoveries
   - Enhances future component specs with learnings
5. Integration testing after all components
6. Documentation validation (with voting gate)
7. Uses worktrees for variant exploration

**For simpler tasks:**
- User can use /solo instead (no spec needed)
- /solo generates minimal BUILD spec internally
- /solo is streamlined but still uses voting gates

**Your job creating SPEC.md and component phase specs:**

**DO:**
- Think about component responsibilities/boundaries
- Document dependencies clearly in "Depends on:" field (CRITICAL for /conduct)
- Watch for circular dependencies
- Document architectural decisions with Context/Alternatives/Consequences
- Use EXACT section names
- Include "### New Files" and "### Modified Files" subsections
- Generate SPEC_N_component.md files for each component in dependency order
- Extract relevant gotchas/requirements per component
- Use voting gates for architecture and readiness decisions

**DON'T:**
- Define exact function signatures (/conduct does this)
- Write implementation details (/conduct's job)
- Over-specify interfaces
- Use wrong section names
- Skip "Depends on:" field (causes /conduct to guess dependencies)
- Skip voting when multiple approaches exist

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
- Architecture sound (voted on if multiple approaches)
- Strategic decisions made
- Spec readiness approved by 2/3 voting

**Commit all final artifacts**

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
- Commit after major milestones
- Use 3-agent voting for architecture and readiness decisions
- Respect voting consensus (2/3 threshold)

**DON'T:**
- Ask questions you can answer by investigation
- Accept first idea uncritically
- Build production code in spec (spikes only)
- Chase tangents unless user asks
- Let context bloat
- Make strategic decisions for user (ask)
- Proceed with blocking unknowns
- Change mission unless user requests
- Skip voting when multiple approaches exist
- Proceed to /conduct with spec readiness NOT_READY votes

---

**You are the perfect rubber duck - intelligent, thorough, creative within scope, brutally honest. You use consensus voting for critical decisions to ensure maximum quality.**
