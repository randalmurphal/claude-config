# Claude Code Orchestration System

## Overview

Three commands for different task complexities:

1. **/solo** - Streamlined execution (straightforward tasks)
2. **/spec** - Investigation & planning (complex features)
3. **/conduct** - Full orchestration (complex features requiring /spec)

---

## Command Decision Tree

```
Do you have a clear, straightforward task?
├─ YES → /solo
│  ├─ Generates minimal spec internally
│  ├─ Delegates to sub-agents
│  ├─ Tests + validates (3 reviewers)
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
         ├─ 6 phases (full orchestration)
         ├─ Worktree variants
         ├─ 6 reviewers
         └─ Comprehensive (~50k+ tokens)
```

---

## File Structure

### Commands
```
~/.claude/commands/
├── solo.md         # Streamlined execution (309 lines)
├── spec.md         # Investigation & planning (337 lines)
└── conduct.md      # Full orchestration (278 lines)
```

### Templates (Referenced by Commands)
```
~/.claude/templates/
├── spec-minimal.md       # Minimal spec format (for /solo)
├── spec-full.md          # Full SPEC format (for /conduct)
├── agent-responses.md    # All agent response templates
└── operational.md        # Algorithms & procedures
```

### Working Directory (Created by Commands)
```
.spec/
├── SPEC.md                   # Full spec (from /spec, for /conduct)
├── BUILD_taskname.md         # Minimal spec (from /solo)
├── PROGRESS.md               # Detailed tracking
├── DISCOVERIES.md            # Gotchas
├── MISSION.md                # Goal (from /spec)
├── CONSTRAINTS.md            # Hard requirements (from /spec)
├── ARCHITECTURE.md           # Design (from /spec)
└── SPIKE_RESULTS/            # Validation results (from /spec)
```

---

## /solo - Streamlined Execution

**Use when:**
- Single component or few related files
- Clear, straightforward implementation
- Standard patterns apply
- Fast iteration needed

**Workflow:**
1. Generate minimal spec (BUILD_taskname.md)
2. Spawn implementation-executor
3. Spawn test-implementer
4. Run tests (fix-validate loop, 3 attempts)
5. Spawn 6 reviewers (security, performance, quality 2x, style, documentation)
6. Fix critical/important issues
7. Done

**Sub-agents:** 8-10 total
**Validation:** 6 reviewers (SAME as /conduct - NO SKIMPING)
**Time:** Fast (~10-20k tokens)
**Prerequisites:** None

---

## /spec - Investigation & Planning

**Use when:**
- Need to explore problem space
- Architecture requires thought
- Multiple approaches possible
- High complexity/uncertainty

**Workflow:**
1. Initial assessment (3-5 questions)
2. Auto-investigation (read codebase)
3. Challenge mode (find ≥3 concerns)
4. Strategic dialogue (decisions, not facts)
5. Discovery loop (document findings)
6. Spike orchestration (validate approaches)
7. Architecture evolution (refine design)
8. Create SPEC.md → ready for /conduct

**Output:** `.spec/SPEC.md` (10 required sections)
**Feeds into:** /conduct

---

## /conduct - Full Orchestration

**Use when:**
- Complex multi-component features
- Dependencies need management
- Variant exploration beneficial
- High stakes (security, payments, auth)

**Prerequisites:** `.spec/SPEC.md` (from /spec) - REQUIRED

**Workflow:**
1. **Phase -1:** Task analysis (resume or new)
2. **Phase 0:** Parse spec (extract components/deps)
3. **Phase 1:** Skeleton (create interfaces, check circular deps)
4. **Phase 2:** Implementation (dependency-aware batching)
5. **Phase 3:** Testing (implement tests, fix bugs)
6. **Phase 4:** Validation (6 reviewers, fix issues)
7. **Phase 5:** Complete (summary, report)

**Worktree Variants:**
- Multiple approaches → multiple worktrees
- Parallel implementation → compare results
- Pick winner OR merge best parts

**Sub-agents:** 15-30+ total
**Validation:** 6 reviewers
**Time:** Comprehensive (~50k+ tokens)

---

## Templates System

Commands reference templates for details, keeping commands concise.

**spec-full.md:**
- Complete SPEC.md format
- All 10 required sections
- Section naming requirements
- Used by /conduct

**spec-minimal.md:**
- Streamlined BUILD spec format
- Just enough for context
- Used by /solo

**agent-responses.md:**
- All agent response templates
- How to embed in prompts
- JSON formats for reviewers

**operational.md:**
- Circular dependency algorithm
- Fix-validate loop structure
- Combining reviewer findings
- PROGRESS.md formats
- TodoWrite patterns
- Git commit conventions

---

## Sub-Agents Roster

**Implementation:**
- skeleton-builder
- test-skeleton-builder
- implementation-executor
- test-implementer

**Validation:**
- security-auditor
- performance-optimizer
- code-reviewer (2x in /conduct, 1x in /solo)
- code-beautifier (/conduct only)
- documentation-reviewer

**Fixing:**
- fix-executor

**Analysis:**
- investigator
- merge-coordinator

---

## Quality Standards

**Testing:**
- Unit: 1 test file per production file (95% coverage)
- Integration: 2-4 per module (85% coverage)
- E2E: Critical paths
- See: `~/.claude/docs/TESTING_STANDARDS.md`

**Validation:**
- /solo: 6 reviewers (security, performance, quality 2x, style, documentation)
- /conduct: 6 reviewers (security, performance, quality 2x, style, documentation)
- **SAME validation rigor in both** - quality is non-negotiable

**Git Commits:**
- After each phase/step
- Include Claude co-author
- Descriptive messages

---

## Utilities

**Worktree Script:**
```bash
~/.claude/scripts/git-worktree variant-a variant-b variant-c
~/.claude/scripts/git-worktree --list
~/.claude/scripts/git-worktree --cleanup
```

**Auto-detects:**
- Git repo root
- Creates in `../.worktrees/<repo-name>/`
- Manages branches automatically

---

## Line Count Summary

**Commands:** 924 lines
- /solo: 309
- /spec: 337
- /conduct: 278

**Templates:** 659 lines
- spec-minimal.md: 51
- spec-full.md: 119
- agent-responses.md: 192
- operational.md: 297

**Total:** 1,583 lines (was 2,457 before refactor)
**Reduction:** 35% with improved clarity and power

---

## Migration from Old System

**Old /conduct (1754 lines):**
- Tried to handle both simple and complex tasks
- Branching logic for complexity assessment
- Examples bloated instructions
- Templates inline
- No variant exploration as standard

**New system:**
- /solo for simple (clear separation)
- /conduct for complex only (focused)
- Templates external (referenced as needed)
- Worktrees are standard practice in /conduct
- Each command is clear in scope

---

## Best Practices

1. **Start simple:** Try /solo first, escalate if needed
2. **Plan complex:** Use /spec before /conduct for multi-component work
3. **Trust delegation:** Sub-agents handle implementation details
4. **Validate thoroughly:** Don't skip testing/review phases
5. **Use templates:** Reference for exact formats
6. **Git commits:** After each phase for resumability
7. **Escalate clearly:** Structured format with options

---

**The system is now clearer, more powerful, and easier to maintain.**
