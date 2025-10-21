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

### Phase -2.0: Load Agent Prompting Skill

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

### Phase -1.5: Determine Working Directory

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

### Phase 7: Documentation Library Setup

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

---

### Phase 8: Readiness Validation

**Checklist:**
- Mission clear, success measurable
- Constraints documented
- Critical unknowns resolved
- Architecture sound, gotchas documented
- No blocking questions
- Complexity understood
- No contradictions
- Documentation library exists (CLAUDE.md + optional docs/)

**If ready, create SPEC.md and component phase specs** (see format below)

**If not ready:** List what's missing

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
2. Validates component phase specs exist (SPEC_N_*.md) or generates fallback
3. Detects circular dependencies (fails if found)
4. For each component in dependency order:
   - Creates skeleton
   - Implements component
   - Validates & fixes (6 reviewers)
   - Unit tests (95%+ coverage)
   - Documents discoveries
   - Enhances future component specs with learnings
5. Integration testing after all components
6. Documentation validation
7. Uses worktrees for variant exploration

**For simpler tasks:**
- User can use /solo instead (no spec needed)
- /solo generates minimal BUILD spec internally
- /solo is streamlined but still validates properly

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

**DON'T:**
- Define exact function signatures (/conduct does this)
- Write implementation details (/conduct's job)
- Over-specify interfaces
- Use wrong section names
- Skip "Depends on:" field (causes /conduct to guess dependencies)

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
