---
name: Orchestration Workflow
description: Choose and execute orchestration commands (/solo for straightforward tasks, /spec for planning, /conduct for complex features with SPEC.md). Covers decision tree, sub-agents, validation standards, and best practices. Use when planning complex tasks or understanding orchestration patterns.
allowed-tools: Read
---

# Orchestration Workflow

**Purpose:** Decision framework for choosing and executing orchestration commands based on task complexity.

---

## Command Decision Tree

```
Do you have a clear, straightforward task?
├─ YES → /solo
│  ├─ Generates minimal spec internally
│  ├─ Delegates to sub-agents
│  ├─ Tests + validates (6 reviewers)
│  └─ Fast iteration (~10-20k tokens)
│
└─ NO → Need to explore/plan first?
   ├─ YES → /spec
   │  ├─ Investigation
   │  ├─ Challenge mode
   │  ├─ Spikes
   │  ├─ Creates .spec/SPEC.md
   │  └─ Then → /conduct
   │
   └─ Have .spec/SPEC.md already?
      └─ YES → /conduct
         ├─ 7 phases (full orchestration)
         ├─ Worktree variants
         ├─ 6 reviewers per component
         └─ Comprehensive (~50k+ tokens)
```

**Golden rule:** Start simple (try /solo first), escalate if needed.

---

## Quick Comparison

| Aspect | /solo | /spec | /conduct |
|--------|-------|-------|----------|
| **Use Case** | Straightforward tasks | Investigation & planning | Complex multi-component features |
| **Prerequisites** | None | None | .spec/SPEC.md (from /spec) |
| **Spec Format** | Minimal (BUILD_taskname.md) | Creates full SPEC.md | Reads existing SPEC.md |
| **Sub-Agents** | 8-10 total | N/A (just main agent) | 15-30+ total |
| **Reviewers** | 6 reviewers | N/A | 6 reviewers per component |
| **Token Budget** | 10-20k tokens | Varies | 50k+ tokens |
| **File Scope** | 1-3 files | N/A | Multi-component |
| **Validation** | Same rigor as /conduct | Spikes in /tmp | Same rigor as /solo |

---

## /solo - Streamlined Execution

### When to Use

**YES to /solo:**
- Single component or few related files (1-3 files)
- Clear, straightforward implementation
- Standard patterns apply
- Fast iteration needed

**NO to /solo (escalate to /conduct):**
- Multiple interconnected components
- Dependencies need management
- Architecture needs planning
- Variant exploration beneficial
- High stakes (security, payments, auth)

### Workflow (7 Steps)

1. **Generate Minimal Spec** - Create `.spec/BUILD_taskname.md`
   - Goal, Problem, Approach
   - Files to create/modify
   - Tests required
   - Quality constraints
   - Template: `~/.claude/templates/spec-minimal.md`

2. **Implementation** - Spawn implementation-executor
   - Single Task call with spec reference
   - Review result for gotchas/blockers

3. **Validation & Fix Loop** - Get it working first
   - Run syntax/import checks
   - Spawn 6 reviewers in parallel:
     1. security-auditor
     2. performance-optimizer
     3. code-reviewer (pass 1: complexity, errors, clarity)
     4. code-reviewer (pass 2: responsibility, coupling, type safety)
     5. code-beautifier (DRY, magic numbers, dead code)
     6. code-reviewer (pass 3: documentation, comments, naming)
   - Fix ALL issues via fix-executor (3 attempts max)
   - Re-run reviewers to verify

4. **Testing** - Lock in behavior
   - Spawn test-implementer
   - 95% coverage target
   - Test & fix loop (3 attempts max)

5. **Documentation Validation** - Ensure accuracy
   - Find all .md files in working directory
   - Spawn code-reviewer to validate docs
   - Fix outdated/incorrect documentation

6. **CLAUDE.md Optimization** - Check hierarchical best practices
   - Validate line counts vs targets
   - Check for duplication across hierarchy
   - Extract deep-dive content to QUICKREF.md if needed

7. **Complete** - Update BUILD spec with gotchas, final summary

### Sub-Agents Used

- implementation-executor
- test-implementer
- security-auditor
- performance-optimizer
- code-reviewer (3x)
- code-beautifier
- fix-executor
- general-builder (for doc updates)

**Total:** 8-10 agents

### Validation Standards

**NO SKIMPING - Same rigor as /conduct:**
- 6 reviewers (security, performance, quality 3x, style)
- Fix ALL issues (critical + important + minor)
- No # noqa / # type: ignore unless documented
- 95% test coverage
- Documentation validated

---

## /spec - Investigation & Planning

### When to Use

**YES to /spec:**
- Need to explore problem space
- Architecture requires thought
- Multiple approaches possible
- High complexity/uncertainty
- Before running /conduct on complex features

**Output:** `.spec/SPEC.md` ready for /conduct

### Workflow (8 Phases)

**Phase -2:** Determine working directory
- Infer from task description
- Ask user if unclear

**Phase -1:** Initial assessment (3-5 questions)
- New project or existing code?
- High-level goal?
- Critical constraints?
- Create MISSION.md immediately

**Phase 0:** Auto-investigation (existing projects only)
- Project structure, tech stack, dependencies
- Existing patterns (auth, APIs, testing)
- Deployment setup, database/caching config

**Phase 1:** Challenge mode
- Find ≥3 concerns:
  - Conflicts with existing code
  - Hidden complexity
  - Pain points from similar projects
  - Missing requirements
  - Underestimated difficulty
  - Unstated assumptions
- Parallel investigation for unknowns

**Phase 2:** Strategic dialogue
- Ask about tradeoffs and decisions (NOT facts)
- GOOD: "Two auth systems increases complexity. Unify or keep both?"
- BAD: "What database?" (check settings.py)

**Phase 3:** Discovery loop
- Document in DISCOVERIES.md
- Track assumptions in ASSUMPTIONS.md
- Prune when >50 lines (archive obsolete)

**Phase 4:** Spike orchestration
- When: Complexity >6/10, unfamiliar tech, critical security/performance
- Run multiple spikes in parallel (single message, multiple Task calls)
- Save results to `.spec/SPIKE_RESULTS/NNN_description.md`

**Phase 5:** Architecture evolution
- Update ARCHITECTURE.md
- Document components, dependencies, data flow
- Watch for circular dependencies

**Phase 6:** Scope management
- Serves MISSION.md? → Investigate
- Doesn't serve? → Note as "Future"
- Tangent? → Ask user

**Phase 7:** Readiness validation & SPEC.md creation
- Validate checklist (mission clear, constraints documented, unknowns resolved)
- Create SPEC.md with 10 required sections
- Generate component phase specs (SPEC_N_component.md) in dependency order

### SPEC.md Format (10 Required Sections)

1. **Problem Statement** - What problem are we solving?
2. **User Impact** - Who is affected and how?
3. **Mission** - Unchanging goal (1-2 sentences)
4. **Success Criteria** - Measurable outcomes
5. **Requirements (IMMUTABLE)** - Hard requirements that cannot change
6. **Proposed Approach (EVOLVABLE)** - High-level strategy, can adapt
7. **Implementation Phases** - Phased breakdown with estimates
8. **Known Gotchas** - From discoveries and spikes
9. **Quality Requirements** - Tests, security, performance, documentation
10. **Files to Create/Modify** - CRITICAL for /conduct dependency parsing

**3 Optional Sections:**
11. Testing Strategy (recommended - see testing-standards skill)
12. Custom Roles
13. Evolution Log

**CRITICAL for /conduct:**
- "Depends on:" field in Files section (builds dependency graph)
- Watch for circular dependencies
- Generate SPEC_N_component.md files for each component

### Artifact Structure

```
.spec/
├── MISSION.md          # Goal (50-100 lines, never changes)
├── CONSTRAINTS.md      # Hard requirements
├── DISCOVERIES.md      # Learnings (<50 lines, prune regularly)
├── ARCHITECTURE.md     # Design (50-100 lines, evolves)
├── ASSUMPTIONS.md      # Explicit assumptions to validate
├── SPIKE_RESULTS/      # Immutable spike results
├── SPEC.md             # Final spec for /conduct (10+ sections)
├── SPEC_1_component.md # Component 1 phase spec
├── SPEC_2_component.md # Component 2 phase spec
└── ...
```

---

## /conduct - Full Orchestration

### When to Use

**YES to /conduct:**
- Complex multi-component features
- Dependencies need management
- Variant exploration beneficial
- High stakes (security, payments, auth)
- Have .spec/SPEC.md ready

**Prerequisites:** `.spec/SPEC.md` MUST exist (from /spec) - REQUIRED

**If no SPEC.md:** Tell user to run /spec first, then STOP.

### Workflow (7 Phases)

**Phase -2:** Determine working directory

**Phase -1:** Parse SPEC.md & build dependency graph
- Extract components from "Files to Create/Modify"
- Extract dependencies from "Depends on:" field
- Topologically sort components
- Detect circular dependencies (DFS cycle detection)
- FAIL LOUD if cycle found

**Phase 0:** Validate component phase specs exist
- Check for SPEC_N_*.md files
- If exist (created by /spec): Use them as-is
- If missing (fallback): Generate from SPEC.md now

**Phase 1-N:** Component phases (for EACH component in dependency order)

Per component:
1. **Skeleton** - Create skeleton for production + test files
2. **Implementation** - Spawn implementation-executor
3. **Validate & Fix Loop** - Get component working
   - Run validation (syntax, imports, linting)
   - Spawn 6 reviewers in parallel (same as /solo)
   - Fix ALL issues via fix-executor (3 attempts max)
   - Re-run reviewers to verify
4. **Unit Testing** - Lock in behavior
   - Spawn test-implementer
   - 95% coverage target
   - Test & fix loop (3 attempts max)
5. **Document Discoveries** - Update DISCOVERIES.md
6. **Enhance Future Phase Specs** - Add learnings to dependent components
7. **Checkpoint** - Component complete, commit

**Phase N+1:** Integration testing
- Spawn test-implementer for cross-component interactions
- Test & fix loop (3 attempts max)

**Phase N+2:** Documentation validation
- Find all .md files in working directory
- Spawn code-reviewer to validate docs
- Fix outdated/incorrect documentation

**Phase N+3:** CLAUDE.md optimization
- Validate line counts vs targets
- Check for duplication across hierarchy
- Extract deep-dive content to QUICKREF.md if needed

**Phase N+4:** Complete
- Update SPEC.md with major gotchas
- Final summary

### Worktree Variant Exploration

**When:** Multiple valid approaches, architectural uncertainty, high-risk changes

**Process:**
1. Decide on N approaches for component
2. Create worktrees: `~/.claude/scripts/git-worktree variant-a variant-b`
3. Run component phase in each worktree
4. Spawn investigator per variant (parallel)
5. Compare results:
   - Pick winner, OR
   - Spawn merge-coordinator to combine best parts
6. Cleanup: `~/.claude/scripts/git-worktree --cleanup`

### Sub-Agents Used

**Implementation:**
- skeleton-builder
- test-skeleton-builder
- implementation-executor
- test-implementer

**Validation:**
- security-auditor
- performance-optimizer
- code-reviewer (3x per component)
- code-beautifier

**Fixing:**
- fix-executor

**Analysis:**
- investigator
- merge-coordinator
- general-builder

**Total:** 15-30+ agents (scales with component count)

### Validation Standards

**Same rigor as /solo - NO SHORTCUTS:**
- 6 reviewers per component
- Fix ALL issues (critical + important + minor)
- No # noqa / # type: ignore unless documented
- 95% test coverage per component
- Integration tests after all components
- Documentation validated

---

## Quality Standards (All Commands)

### Testing Requirements

**See:** `~/.claude/docs/TESTING_STANDARDS.md` or testing-standards skill

**3-Layer Pyramid:**
1. **Unit Tests** (95% coverage)
   - 1:1 file mapping (one test file per production file)
   - Test happy path + error cases + edge cases
   - Choose organization: single function, parametrized, or separate methods
   - Mock all external dependencies
   - Fast (<100ms per test)

2. **Integration Tests** (85% coverage)
   - 2-4 test files per module (not per file)
   - Add to existing integration files (don't create new ones)
   - Test components working together
   - Use real dependencies (test database, cache)

3. **E2E Tests** (critical paths)
   - 1-3 files total for entire project
   - Test complete user workflows through API
   - HTTP requests to real API

**Coverage Targets:**
- Unit: ≥95%
- Integration: ≥85%
- E2E: Critical paths covered

### Validation Rigor

**Both /solo and /conduct use 6 reviewers:**
1. security-auditor
2. performance-optimizer
3. code-reviewer (pass 1: complexity, errors, clarity)
4. code-reviewer (pass 2: responsibility, coupling, type safety)
5. code-beautifier (DRY, magic numbers, dead code)
6. code-reviewer (pass 3: documentation, comments, naming)

**Fix-Validate Loop:**
- Max 3 attempts
- Fix ALL issues (critical + important + minor)
- No ignored errors unless documented
- Re-run ALL reviewers after fixes

**Documentation Validation:**
- All .md files reviewed
- Code examples match implementation
- No outdated information
- No contradictions between docs and code

### Git Commit Patterns

**When:** After each major step/phase

**Format:**
```
[type]([scope]): [description]

[body - why, not what]

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Examples:**
- After implementation: `feat(auth): add JWT authentication`
- After validation: `fix(auth): resolve security audit findings`
- After testing: `test(auth): add comprehensive unit tests (95% coverage)`

---

## Sub-Agents Roster

### Implementation Agents

- **skeleton-builder** - Create production file skeletons
- **test-skeleton-builder** - Create test file skeletons
- **implementation-executor** - Implement full functionality
- **test-implementer** - Implement comprehensive tests

### Validation Agents

- **security-auditor** - Security vulnerabilities, auth issues
- **performance-optimizer** - Performance bottlenecks, inefficiencies
- **code-reviewer** - Quality, clarity, best practices (used 3x with different focuses)
- **code-beautifier** - DRY violations, magic numbers, dead code
- **documentation-reviewer** - Doc accuracy and completeness

### Fixing Agents

- **fix-executor** - Fix validation issues, test failures

### Analysis Agents

- **investigator** - Deep code investigation, variant analysis
- **merge-coordinator** - Merge best parts of variants
- **general-builder** - General implementation tasks, doc updates

**All agents inherit parent tools:** Read, Write, Edit, Bash, Grep, Glob

---

## Tracking & Artifacts

### /solo Artifacts

```
.spec/
├── BUILD_taskname.md    # Minimal spec (goal, files, tests, quality)
└── PROGRESS.md          # Simple step tracking
```

### /spec Artifacts

```
.spec/
├── MISSION.md           # Goal (50-100 lines)
├── CONSTRAINTS.md       # Hard requirements
├── DISCOVERIES.md       # Learnings (<50 lines)
├── ARCHITECTURE.md      # Design (50-100 lines)
├── ASSUMPTIONS.md       # Explicit assumptions
├── SPIKE_RESULTS/       # Immutable spike results
├── SPEC.md              # 10 required sections
├── SPEC_1_component.md  # Component phase specs
└── ...
```

### /conduct Artifacts

```
.spec/
├── SPEC.md              # High-level architecture (from /spec)
├── SPEC_N_component.md  # Per-component specs (generated or from /spec)
├── DISCOVERIES.md       # Learnings captured as phases complete
└── PROGRESS.md          # Detailed component/step tracking
```

---

## Escalation Patterns

### When Blocked (Any Command)

**When:**
- 3 failed attempts
- Architectural decisions needed
- Critical security unfixable
- External deps missing

**Format:**
```
BLOCKED: [Component/Phase] - [Issue]

Issue: [description]
Attempts: [what tried]
Need: [specific question]
Options: [A, B, C with implications]
Recommendation: [your suggestion]
```

### When /solo Discovers Complexity

**If during /solo execution:**
- More components needed than anticipated
- Complex dependencies emerge
- Architecture needs planning
- Multiple valid approaches exist

**Tell user:**
```
This task is more complex than initially assessed.

Reasons:
- [what you discovered]

Recommend:
1. Stop current work
2. Run /spec to properly plan architecture
3. Run /conduct for full orchestration

OR

Continue with /solo if: [condition]
```

Let user decide.

---

## Best Practices

1. **Start simple** - Try /solo first, escalate if needed
2. **Plan complex** - Use /spec before /conduct for multi-component work
3. **Trust delegation** - Sub-agents handle implementation details
4. **Validate thoroughly** - Don't skip testing/review phases (same rigor in both /solo and /conduct)
5. **Use templates** - Reference `~/.claude/templates/` for exact formats
6. **Git commits** - After each phase for resumability
7. **Escalate clearly** - Structured format with options when blocked

---

## Quick Reference

### Choose Your Command

| Scenario | Command |
|----------|---------|
| Straightforward task, 1-3 files | /solo |
| Need to explore/plan architecture | /spec |
| Have SPEC.md, ready to implement | /conduct |
| Complex feature, no spec yet | /spec → /conduct |
| Uncertain which to use | Start /solo, escalate if needed |

### Token Budget Guidance

- **/solo:** 10-20k tokens (streamlined)
- **/spec:** Varies (thorough investigation)
- **/conduct:** 50k+ tokens (comprehensive)

### Commands Location

- `~/.claude/commands/solo.md` (309 lines)
- `~/.claude/commands/spec.md` (337 lines)
- `~/.claude/commands/conduct.md` (278 lines)

### Templates Location

- `~/.claude/templates/spec-minimal.md` (for /solo)
- `~/.claude/templates/spec-full.md` (for /conduct)
- `~/.claude/templates/agent-responses.md` (all agent response templates)
- `~/.claude/templates/operational.md` (algorithms & procedures)

### Testing Standards

- `~/.claude/docs/TESTING_STANDARDS.md` (comprehensive guide)
- testing-standards skill (quick reference)

---

**Bottom line:** Start with /solo for straightforward tasks. Use /spec to plan complex features, then /conduct to execute. Trust delegation, validate thoroughly, escalate when blocked.
