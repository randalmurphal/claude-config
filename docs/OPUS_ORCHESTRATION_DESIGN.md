# Opus Orchestration Architecture

## Design Philosophy

### The Problem with Prescriptive Orchestration

The old system treated Claude like a junior developer needing step-by-step instructions:
- 2400 lines to say "build software properly"
- Repeated instructions 20+ times (token warnings, parallelization)
- Pseudocode for things Claude knows (topological sort, voting)
- Same workflow for 3-file change and 50-file rewrite

### The New Approach: Intent + Standards + Judgment

Tell Claude:
1. **What quality bar you expect** (not how to achieve it)
2. **What tools are available** (not how to use basic tools)
3. **What guardrails are non-negotiable** (not obvious best practices)
4. **What domain knowledge to load** (skills, not inline repetition)

Let Claude figure out the optimal path.

---

## Model Selection Strategy

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| **Orchestration** | Opus | Needs judgment, synthesis, planning |
| **Architecture decisions** | Opus | High-stakes, needs careful reasoning |
| **Complex investigation** | Opus | Multi-file, cross-cutting concerns |
| **Tie-breaking/verification** | Opus | Needs to resolve contradictions |
| **Implementation** | Sonnet | Good at code generation, faster |
| **Code review** | Sonnet | Good at pattern recognition |
| **Test implementation** | Sonnet | Mechanical task, well-defined |
| **Documentation** | Sonnet | Straightforward writing |
| **Simple file search** | Haiku | Fast, cheap, sufficient |
| **Basic validation** | Haiku | Syntax checks, simple queries |

### Selection Heuristics

```
IF task requires:
  - Cross-cutting analysis across >10 files → Opus
  - Architectural decisions → Opus
  - Resolving contradictions → Opus
  - Synthesis of multiple agent outputs → Opus

ELIF task is:
  - Implementation with clear spec → Sonnet
  - Code review (single focus) → Sonnet
  - Test writing → Sonnet
  - Documentation → Sonnet

ELSE:
  - Simple searches → Haiku
  - Basic validation → Haiku
```

---

## Quality Scaling (Not Fixed)

Instead of "always 6 reviewers", scale to task risk:

### Risk Assessment

| Factor | Low Risk | Medium Risk | High Risk |
|--------|----------|-------------|-----------|
| Files changed | 1-3 | 4-10 | 10+ |
| Public API | No | Internal | External |
| Data handling | None | Read-only | Write/delete |
| Auth/security | None | Uses existing | Implements new |
| Breaking changes | None | Backward compat | Breaking |

### Review Scaling

| Risk Level | Per-Task Reviews | Full Validation |
|------------|------------------|-----------------|
| Low | 1 Sonnet reviewer | 2 reviewers |
| Medium | 2 Sonnet reviewers | 4 reviewers |
| High | 2 Sonnet + Opus verification | 6 reviewers + Opus synthesis |
| Critical | Full review suite | All gates + human checkpoint |

### Voting Gates (When Needed)

Use voting for:
- Architecture decisions with multiple valid approaches
- Repeated fix failures (same issue 2+ times)
- Production-readiness assessment (high-risk only)
- Contradictions between reviewers

Skip voting for:
- Clear single path
- Low-risk changes
- Mechanical tasks

---

## Skill Architecture

### Core Skills (Load by Default)

| Skill | Purpose |
|-------|---------|
| `orchestration-standards` | Quality bars, review scaling, model selection |
| `agent-prompting` | How to write effective agent prompts (trimmed) |

### Domain Skills (Load When Relevant)

| Skill | When to Load |
|-------|--------------|
| `spec-formats` | Creating SPEC.md, BUILD specs |
| `testing-standards` | Writing/reviewing tests |
| `python-style` | Python implementation |
| `security-context` | Security-sensitive code |
| `mongodb-aggregation-optimization` | MongoDB queries |
| `ai-documentation` | Documentation work |

### Skill Loading Strategy

```
Orchestrator loads: orchestration-standards
Sub-agents receive: Relevant domain skills in prompt

NOT: Copy-paste entire skill into every prompt
YES: "Load testing-standards skill" instruction
```

---

## Slash Command Architecture

### Old: Prescriptive (2400 lines)
```markdown
## Phase 1: Do X
## Phase 2: Do Y
## Phase 3: Here's pseudocode for Z
## Phase 4: Here's the exact bash commands
## Phase 5: Here's the exact JSON format
... (repeat for 50 phases)
```

### New: Intent-Based (~200 lines)
```markdown
## Purpose
What this workflow accomplishes

## Prerequisites
What must exist before starting

## Quality Requirements
Specific numbers/thresholds (your preferences)

## Available Tools
Project-specific tools I might not know

## Guardrails
Non-negotiable rules

## Skills to Load
Domain knowledge needed

## Your Mission
High-level goal, trust judgment on execution
```

---

## Error Handling Philosophy

### Old: Prescriptive
"After 2 failures, spawn 3 investigators, collect votes, tally..."

### New: Principle-Based
```
When stuck:
1. Analyze failure pattern (same issue? different issues?)
2. If same issue repeats: architectural problem, escalate or vote
3. If different issues: making progress, continue
4. If >3 attempts with no progress: stop and explain

Use judgment on when voting helps vs wastes tokens.
```

---

## Implementation Plan

### Phase 1: Core Infrastructure
1. Create `orchestration-standards` skill
2. Create `spec-formats` skill
3. Update `agent-prompting` skill (trim 70%)

### Phase 2: Slash Commands
1. Rewrite `/conduct` (~200 lines)
2. Rewrite `/spec` (~150 lines)
3. Rewrite `/solo` (~100 lines)
4. Rewrite `/pr_review` (~300 lines)
5. Simplify `/update_docs` (~100 lines)
6. Keep `/coda` as-is (already minimal)

### Phase 3: Integration
1. Update CLAUDE.md with new philosophy
2. Remove redundant content from existing skills
3. Test with real tasks

---

## Success Metrics

### Context Efficiency
- Old: ~7000 lines loaded for orchestration
- Target: ~1000 lines for same capability

### Quality Maintenance
- Same or better output quality
- Faster execution (less prompt processing)
- More adaptive to task complexity

### Judgment Utilization
- Model selects appropriate review depth
- Model selects appropriate sub-agent models
- Model adapts workflow to task, not task to workflow
