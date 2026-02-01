---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work correctly. Applies TDD methodology to process documentation - test with pressure scenarios, write the skill, verify compliance.
---

# Writing Skills

## Overview

Writing skills IS Test-Driven Development applied to process documentation.

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

## What is a Skill?

A **skill** is a reference guide for proven techniques, patterns, or tools. Skills help future Claude instances find and apply effective approaches.

**Skills are:** Reusable techniques, patterns, tools, reference guides
**Skills are NOT:** Narratives about solving a problem once

## When to Create

**Create when:**
- Technique wasn't intuitively obvious
- You'd reference this again across projects
- Pattern applies broadly (not project-specific)
- Others would benefit

**Don't create for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (put in CLAUDE.md)
- Mechanical constraints (if enforceable with regex/validation, automate it)

## Directory Structure

```
~/.claude/skills/
  skill-name/
    SKILL.md              # Main reference (required)
    supporting-file.*     # Only if needed (heavy reference, reusable tools)
```

## SKILL.md Structure

### Frontmatter (YAML)

Only two fields: `name` and `description`. Max 1024 characters total.

```yaml
---
name: skill-name-with-hyphens
description: Use when [specific triggering conditions and symptoms]
---
```

**CRITICAL: Description = When to Use, NOT What the Skill Does**

Descriptions that summarize workflow create a shortcut Claude will take instead of reading the full skill. Only describe triggering conditions.

```yaml
# BAD: Summarizes workflow
description: Use for TDD - write test first, watch it fail, write minimal code, refactor

# GOOD: Just triggering conditions
description: Use when implementing any feature or bugfix, before writing implementation code
```

### Body Structure

```markdown
# Skill Name

## Overview
What is this? Core principle in 1-2 sentences.

## When to Use
Bullet list with SYMPTOMS and use cases. When NOT to use.

## Core Pattern
Before/after code comparison (for techniques/patterns)

## Quick Reference
Table or bullets for scanning common operations

## Common Mistakes
What goes wrong + fixes

## Red Flags
Signs you're violating the skill's principles
```

## Skill Types

| Type | Examples | Test With |
|------|----------|-----------|
| **Technique** | Concrete method with steps | Application scenarios, edge cases |
| **Pattern** | Way of thinking about problems | Recognition scenarios, counter-examples |
| **Reference** | API docs, syntax guides | Retrieval scenarios, gap testing |
| **Discipline** | Rules/requirements (TDD, verification) | Pressure scenarios, rationalization resistance |

## Search Optimization (CSO)

Future Claude needs to FIND your skill. Optimize for discovery:

**Description field:**
- Start with "Use when..." focusing on triggering conditions
- Include specific symptoms, situations, and contexts
- NEVER summarize the skill's process or workflow
- Written in third person
- Under 500 characters

**Keywords throughout:**
- Error messages: "Hook timed out", "ENOTEMPTY", "race condition"
- Symptoms: "flaky", "hanging", "zombie", "pollution"
- Synonyms: "timeout/hang/freeze", "cleanup/teardown/afterEach"
- Actual commands, library names, file types

**Naming:**
- Active voice, verb-first: `creating-skills` not `skill-creation`
- Gerunds work well: `systematic-debugging`, `receiving-code-review`
- Name by what you DO or core insight

## Token Efficiency

Skills load into conversations. Every token counts.

**Targets:**
- Frequently-loaded skills: <200 words
- Other skills: <500 words (still be concise)

**Techniques:**
- Reference `--help` instead of documenting all flags
- Cross-reference other skills instead of repeating
- One good example beats three mediocre ones
- Don't repeat what's obvious from context

## Bulletproofing Discipline Skills

Skills that enforce discipline need to resist rationalization:

### Close Every Loophole Explicitly

```markdown
# BAD
Write code before test? Delete it.

# GOOD
Write code before test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete
```

### Build Rationalization Table

Capture every excuse agents make and counter each one explicitly:

```markdown
| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
```

### Create Red Flags List

Easy self-check when rationalizing:

```markdown
## Red Flags - STOP and Start Over
- Code before test
- "Just this once"
- "This is different because..."
```

## Code Examples

**One excellent example beats many mediocre ones.**

Choose the most relevant language for the skill's domain. Don't implement in 5+ languages. You're good at porting.

**Good examples are:** Complete, runnable, well-commented (WHY not WHAT), from real scenarios, ready to adapt.

## Anti-Patterns

| Anti-Pattern | Why Bad |
|-------------|---------|
| Narrative storytelling | "In session 2025-10-03 we found..." - too specific, not reusable |
| Multi-language dilution | Mediocre quality, maintenance burden |
| Code in flowcharts | Can't copy-paste, hard to read |
| Generic labels | "helper1", "step3" - labels need semantic meaning |
| Untested skills | Untested skills ALWAYS have issues |

## Skill Creation Checklist

- [ ] Name uses only letters, numbers, hyphens
- [ ] YAML frontmatter with name and description (max 1024 chars)
- [ ] Description starts with "Use when..." (triggering conditions only)
- [ ] Clear overview with core principle
- [ ] Keywords throughout for search
- [ ] One excellent example
- [ ] Quick reference table
- [ ] Common mistakes section
- [ ] Red flags section (for discipline skills)
- [ ] Rationalization table (for discipline skills)
- [ ] Supporting files only for heavy reference or reusable tools
- [ ] Total SKILL.md under 500 lines
