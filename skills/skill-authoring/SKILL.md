---
name: skill-authoring
description: Best practices for creating and updating Claude Code skills including YAML frontmatter structure, description patterns for discoverability, content organization, progressive disclosure, and testing strategies. Use when creating new skills or updating existing skills to follow proven patterns.
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
---

# Skill Authoring Best Practices

**Purpose:** Create effective Claude Code skills that are discoverable, maintainable, and follow community best practices.

**When to use:** Before creating new skills, when updating existing skills, or when skills aren't being discovered/used as expected.

---

## Core Principles (2025 Best Practices)

1. **Description is everything** - Claude uses description to decide when to load your skill
2. **Single purpose wins** - Focused skills beat Swiss Army knives
3. **Structure over prose** - Tables, bullets, code blocks >>> paragraphs
4. **Progressive disclosure** - SKILL.md core (under 500 lines), details in reference.md
5. **Examples over explanations** - Show don't tell (before/after patterns)
6. **Third person descriptions** - "Extracts text" not "I extract text"

**For detailed examples and patterns:** See reference.md

---

## Required Structure

### YAML Frontmatter (Required)

**Required fields:**

| Field | Rules | Example |
|-------|-------|---------|
| `name` | Max 64 chars, lowercase/numbers/hyphens only | `python-testing` |
| `description` | Max 1024 chars, specific about WHAT and WHEN | `Write pytest tests with fixtures. Use when writing Python tests.` |

**Optional fields:**

| Field | Purpose | Example |
|-------|---------|---------|
| `allowed-tools` | Restrict which tools skill can use | `[Read, Grep, Glob]` |

**Validation rules:**
- No XML tags in name or description
- No reserved words in name
- Description must be non-empty
- Use third-person ("Extracts text" not "I extract text")

---

## Writing Discoverable Descriptions

**The description determines whether Claude loads your skill.**

### Description Formula

```
[What it does] + [Technologies/domain] + "Use when" + [Trigger scenarios]
```

### Quick Examples

**❌ BAD:** `description: Helps with testing`
**Why:** Too vague, no triggers

**✅ GOOD:** `description: Write pytest tests following 3-layer pyramid with 1:1 file mapping. Use when writing tests, checking coverage, or validating test structure.`
**Why:** Specific technology, patterns, clear triggers

**For more description examples:** See reference.md

---

### Trigger Words for Discoverability

**Include domain-specific trigger words in descriptions:**

| Domain | Trigger Words |
|--------|---------------|
| **Testing** | "write tests", "test coverage", "debugging test failures", "pytest", "jest" |
| **Documentation** | "write documentation", "CLAUDE.md", "README", "API docs" |
| **Code Quality** | "refactoring", "complexity", "code review", "linting" |
| **Performance** | "optimization", "profiling", "bottlenecks", "slow queries" |
| **Security** | "security audit", "vulnerabilities", "OWASP", "authentication" |

---

## Content Organization Patterns

### Pattern 1: Core Principles + Sections + Examples (Most Common)

```markdown
# Skill Name

**Purpose:** [One sentence]
**When to use:** [Trigger scenarios]

## Core Principles
[3-6 key rules]

## [Section 1]
[Content with examples]

## Quick Reference
[Checklists, commands, templates]
```

**When:** Most skills (testing, code style, documentation)

### Pattern 2: Decision Framework + Guidance

```markdown
# Skill Name

## Decision Framework
[When to use A vs B - table format]

## Approach A
[Detailed guidance]

## Common Pitfalls
[What to avoid]
```

**When:** Skills involving choices (orchestration, refactoring strategies)

### Pattern 3: Reference Catalog

```markdown
# Skill Name

## Quick Index
[Searchable list]

## Detailed Reference
[Items with structure, rules, examples]
```

**When:** API references, business rules, error codes

**For detailed pattern examples:** See reference.md

---

## Content Best Practices

### Use Tables for Structured Information

**Tables are scannable and clear:**

| Field | Max Length | Allowed Characters | Required |
|-------|-----------|-------------------|----------|
| name | 64 | lowercase, numbers, hyphens | Yes |
| description | 1024 | Any text (no XML tags) | Yes |

### Use Before/After Examples

**Pattern:**
```markdown
**❌ BAD:**
[bad example]
**Why bad:** [Reason]

**✅ GOOD:**
[good example]
**Why good:** [Reason]
```

### Use Progressive Disclosure

**SKILL.md (Core):**
- Core principles
- Quick reference
- Common patterns overview

**reference.md (Details):**
- Comprehensive examples
- Edge cases
- Advanced patterns
- Troubleshooting

**examples.md (Code):**
- Copy-paste ready code
- Multiple languages
- Real-world scenarios

---

## File Organization

### Single-File Skill (Simple)

```
skills/my-skill/
└── SKILL.md         # Everything (under 500 lines)
```

**When:** Simple skills, <500 lines

### Multi-File Skill (Complex)

```
skills/my-skill/
├── SKILL.md         # Core (under 500 lines)
├── reference.md     # Detailed documentation
├── examples.md      # Code examples
├── scripts/         # Helper scripts
└── templates/       # Reusable templates
```

**When:** Complex skills, >500 lines total

---

## Common Skill Patterns

### Pattern: Proactive Skill

**Trigger phrase in description:**
```yaml
description: [What it does]. MUST BE USED PROACTIVELY when [trigger] to ensure [benefit].
```

**Example:**
```yaml
description: Best practices for agent prompts. MUST BE USED PROACTIVELY when spawning sub-agents to ensure high-quality results.
```

### Pattern: Tool-Restricted Skill

**For read-only skills:**
```yaml
allowed-tools:
  - Read
  - Grep
  - Glob
```

**Why:** Prevents accidental modifications during review

---

## Testing Your Skill

### Discovery Testing

1. **Write test prompt matching description:**
   ```
   "Help me write tests for my authentication module"
   ```

2. **Check if skill loaded** (look for skill content in response or use `--debug`)

3. **Refine description if not loaded:**
   - Add trigger keywords
   - Be more specific
   - Check validation errors

### Validation Checklist

- [ ] **YAML valid:** No syntax errors, required fields present
- [ ] **Name valid:** ≤64 chars, lowercase/numbers/hyphens only
- [ ] **Description specific:** Includes WHAT, technologies, WHEN triggers
- [ ] **Third-person:** Uses "Extracts" not "I extract"
- [ ] **Under 500 lines:** SKILL.md length (extract to reference.md if over)
- [ ] **Structure over prose:** Tables, bullets, code blocks
- [ ] **Examples included:** Before/after patterns
- [ ] **Tested:** Claude discovers and uses skill correctly
- [ ] **Quick reference:** Commands, checklists, templates

---

## Common Issues and Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Skill not discovered** | Claude doesn't use skill | Add trigger keywords to description, be more specific about WHEN |
| **Skill ignored** | Loaded but not followed | Move critical info higher, use tables/bullets |
| **Too much context** | Skill too long | Split to SKILL.md (core) + reference.md (details) |
| **YAML error** | Skill fails to load | Validate syntax, check field lengths, remove XML tags |
| **Overlapping skills** | Multiple skills match | Make descriptions more specific |

---

## Quick Reference: Skill Template

```markdown
---
name: my-skill-name
description: [What] + [domain] + "Use when" + [triggers]
---

# My Skill Name

**Purpose:** [One sentence]
**When to use:** [Scenarios]

## Core Principles

1. **[Principle]** - [Why it matters]
2. **[Principle]** - [Why it matters]

## [Section]

**❌ BAD:**
[bad example]

**✅ GOOD:**
[good example]

## Quick Reference

**Commands:**
```bash
[command]
```

**Checklist:**
- [ ] [Item]
```

**For complete template with all sections:** See reference.md

---

## Migrating Existing Skills

### Quick Audit

```bash
# Check line count
wc -l skills/my-skill/SKILL.md

# Check description
grep "^description:" skills/my-skill/SKILL.md
```

### Enhancement Steps

1. **Enhance description** - Add trigger keywords and "Use when" clause
2. **Add tables** - Convert prose to tables where applicable
3. **Add examples** - Include before/after patterns
4. **Extract content** - If >500 lines, move details to reference.md
5. **Test discovery** - Verify Claude finds skill with realistic prompts

**For detailed migration guide:** See reference.md

---

## Summary: The Golden Rules

1. **Description determines discoverability** - Spend time making it specific
2. **Under 500 lines in SKILL.md** - Extract details to reference.md
3. **Structure over prose** - Tables, bullets, code blocks
4. **Show don't tell** - Before/after examples
5. **Single purpose** - Focused skills beat Swiss Army knives
6. **Third person** - "Extracts text" not "I extract text"
7. **Test thoroughly** - Try realistic prompts
8. **Progressive disclosure** - Core in SKILL.md, details in supporting files

---

## The Test

**Can Claude discover your skill** with a realistic prompt? If not, the description needs work.

**Can Claude find information** in your skill in <30 seconds? If not, restructure with tables/bullets.

**Is SKILL.md under 500 lines?** If not, extract to reference.md.

**Remember:** Skills are loaded into Claude's context. Every line costs tokens. Make every line count.

---

**For comprehensive examples, detailed patterns, and troubleshooting:** See reference.md
