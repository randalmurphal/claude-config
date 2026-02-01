---
name: brainstorm
description: Use when starting any non-trivial feature, design, or behavior change - before writing code or creating tasks. Guides collaborative design exploration through focused questioning to produce a validated spec.
---

# Brainstorming

## Overview

Turn ideas into fully formed designs through focused collaborative dialogue before any implementation begins.

**Core principle:** Understand the problem completely before proposing solutions. One question at a time. YAGNI ruthlessly.

**Announce at start:** "I'm using the brainstorming skill to explore the design before we build anything."

## When to Use

- New features or components
- Behavior changes to existing systems
- Refactors with multiple valid approaches
- Anything where jumping straight to code would be premature

**Skip for:** Typos, one-line fixes, config changes, tasks with crystal-clear requirements already written.

## The Process

### Phase 1: Understand the Idea

Ask questions to understand what's actually needed. **One question per message.** Prefer multiple-choice when possible (reduces cognitive load).

**Good questions:**
- "Is this for internal use or public-facing?" (scoped)
- "Which of these matters more: speed or correctness?" (prioritization)
- "Does this need to work with X, or is it standalone?" (boundaries)

**Bad questions:**
- "Can you describe the entire feature?" (too broad)
- "What are all the requirements?" (lazy, makes human do the work)

**Stop asking when you can explain the feature back to them and they say "yes, that's it."**

### Phase 2: Explore Approaches

Propose 2-3 approaches with clear trade-offs. Always include a recommendation and why.

```markdown
## Approaches

### A: [Name] (Recommended)
- How: [brief description]
- Pro: [main advantage]
- Con: [main disadvantage]

### B: [Name]
- How: [brief description]
- Pro: [main advantage]
- Con: [main disadvantage]

**Recommendation:** A because [specific reason for this project].
```

**YAGNI ruthlessly** - Remove unnecessary features from all proposals. "We could also add X" is not helpful unless X was requested.

### Phase 3: Present the Design

Once approach is agreed, present the design in **chunks of 200-300 words**. Ask after each chunk: "Does this look right so far?"

Don't dump a 2000-word spec. Break it up:
1. Architecture / high-level approach
2. Key interfaces / data structures
3. Edge cases / error handling
4. Testing strategy

### Phase 4: Document

After validation, produce a clean design document:

```markdown
# [Feature Name] Design

## Goal
[One sentence]

## Approach
[2-3 sentences]

## Success Criteria
- [ ] Measurable outcome 1
- [ ] Measurable outcome 2

## Key Decisions
- [Decision]: [Rationale]

## Non-Goals
- [Thing we're explicitly NOT doing]

## Constraints
- [Hard requirement]

## Testing Strategy
- [How we verify this works]
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Asking too many questions at once | One question per message |
| Proposing solutions before understanding | Finish Phase 1 first |
| Including unrequested features | YAGNI - remove them |
| Presenting one approach | Always 2-3 with recommendation |
| Giant spec dump | Break into 200-300 word chunks |
| Skipping validation | Ask "does this look right?" after each section |

## Red Flags

**Never:**
- Start coding before design is validated
- Add "nice to have" features unprompted
- Present design without getting approach agreement first
- Skip the chunked presentation (giant dumps get skimmed, not read)

**Always:**
- One question at a time
- Multiple-choice when possible
- YAGNI every proposal
- Get explicit sign-off before proceeding
