---
name: AI Documentation Standards
description: Write AI-readable documentation following concise-over-comprehensive principle, hierarchical CLAUDE.md inheritance (100-200 line rule), and structured formats (tables over prose). Use when writing CLAUDE.md files, creating project documentation, or optimizing existing docs.
allowed-tools: Read, Write, Edit, Grep, Glob
---

# AI Documentation Standards

**Purpose**: Create documentation optimized for AI code agents in large monorepos and complex systems.

**Key Insight**: AI agents need concise, structured, scannable information with clear context boundaries - not comprehensive tutorials. Documentation should be a MAP to the codebase, not a REPLACEMENT for reading code.

---

## Core Principles for AI-Readable Docs

### 1. Concise Over Comprehensive
**AI agents can read code.** Documentation = MAP to codebase, not replacement. Provide structure and location references (file:line), not exhaustive explanations.

### 2. Structure Over Prose
**Tables, bullets, code snippets >>> Paragraphs.** AI agents parse structured content faster and more accurately.

### 3. Location References Over Explanations
**Always include file:line_number** for implementation details. AI agents need to know WHERE to look, then they read the code.

### 4. Hierarchical Context Boundaries
**Create clear "entry points"** for different detail levels:
- OVERVIEW.md (what/why)
- architecture/ (how it works)
- implementation/ (where specific logic lives)
- guides/ (when to use approaches)

### 5. Searchable Keywords
**Use consistent terminology.** Include searchable keywords, related components. AI agents use semantic search.

---

## CLAUDE.md Hierarchical Inheritance

### The 100-200 Line Rule

**Most CLAUDE.md files should be 100-200 lines.** Exceptions: Complex production systems (300-400 lines max).

**WHY**: Claude recursively loads CLAUDE.md from root → current directory. Everything becomes agent context, so verbosity = wasted tokens.

**Principle**: Child CLAUDE.md files should ONLY contain information unique to their level. Never duplicate parent content.

### Line Count Targets by Level

| Level | Lines | Focus | What to Include | What to Exclude |
|-------|-------|-------|-----------------|-----------------|
| **Global** (`~/.claude/CLAUDE.md`) | 100-120 | Decision framework, workflow modes | Thinking budget, core principles, parallel execution, git safety | Tool-specific commands, project patterns, testing details |
| **Project** (e.g., `project/CLAUDE.md`) | 150-180 | Project standards, tool configs | Linting commands, testing structure, code style | Core principles (in global), subsystem details |
| **Subsystem** (e.g., `subsystem/CLAUDE.md`) | 120-150 | Architecture overview, design patterns | System architecture, data flow, major components | Testing patterns (in project), code style (in project) |
| **Framework** (e.g., `imports/CLAUDE.md`) | 100-120 | Framework patterns, conventions | Three-phase pattern, base classes, directory structure | Subscription handling (in parent), testing (in project) |
| **Simple Tool** | 200-250 | Purpose, architecture | Tool-specific logic, configuration, gotchas | Code quality (in project), testing (in project) |
| **Complex Tool** | 300-400 | Architecture, business logic | Critical business logic, patterns, gotchas | Code standards, testing strategy, base patterns |

### What NOT to Duplicate Across Hierarchy

**Never duplicate across hierarchy levels:**

1. **Core Principles** (global only) - NO PARTIAL WORK, FAIL LOUD, parallel execution, decision framework
2. **Testing Patterns** (project only) - Coverage requirements, test organization, location conventions
3. **Code Style** (project only) - Line length, type hints, naming conventions, documentation rules
4. **Tool Configurations** (project only) - Linting command paths, formatter configs, build settings
5. **Error Handling Philosophy** (global only) - CRASH/RETRY/SKIP/WARN strategies, try/except usage
6. **Subsystem Patterns** (subsystem only) - Multi-tenancy, database operations, caching strategies

### Hierarchical Inheritance Example

**Bad**: Testing standards repeated in global, project, and tool CLAUDE.md (3x duplication)

**Good**: Define once in global, reference in project ("See global CLAUDE.md for coverage requirements"), reference in tool ("See project CLAUDE.md for structure")

**Result**: 50% reduction in duplication

**For full examples:** See reference.md

---

## When to Extract to QUICKREF.md

### Triggers (any one means extract)
1. CLAUDE.md exceeds 400 lines
2. More than 5 code examples with before/after patterns
3. Detailed implementation walkthroughs (>50 lines per pattern)
4. Comprehensive testing strategies with mock examples
5. Refactoring guides with line-by-line explanations

### What Goes Where

**QUICKREF.md (deep-dive)**: Full code examples, detailed patterns, testing strategies with mocks, performance optimization, debugging strategies, architecture deep dives

**CLAUDE.md (quick reference)**: Critical business logic (table format), architecture overview (bullets), common gotchas (condensed with file:line), key constants, "See QUICKREF.md for details"

---

## AI-Specific Documentation Types

**For full templates:** See reference.md

### Quick Reference

**Type 1: OVERVIEW.md** (100-200 lines)
- Purpose + Performance metrics
- Key components table
- Data flow (bullet points)
- Critical decisions table
- Common gotchas (numbered)

**Type 2: BUSINESS_RULES.md** (300-800 lines)
- Rules index for quick navigation
- Rule definitions table: # | Rule | Condition | Behavior | WHY | Implementation
- Detailed section per rule with test coverage and edge cases

**Type 3: ARCHITECTURE.md** (200-400 lines)
- Design principles (bullet points)
- Processing pipeline (phases with file:line refs)
- Key patterns with examples
- Integration points + performance characteristics

**Type 4: API_REFERENCE.md** (200-600 lines)
- Public functions table: Function | Purpose | Input | Output | Location
- Detailed signature per function with examples
- Internal functions reference (condensed)

**Type 5: TROUBLESHOOTING.md** (150-300 lines)
- Quick diagnosis table: Symptom | Likely Cause | Fix
- Problem/Solution pairs with validation steps
- Debug workflows (numbered steps)
- Log analysis patterns

---

## llms.txt Index Pattern

**Purpose**: Help AI agents find relevant docs quickly in large monorepos

**When to Create**:
- Monorepo has >10 documentation files
- Multiple subsystems with separate docs
- Documentation spread across directories

**Structure**: Organized sections (Quick Start, Business Logic, Architecture, Implementation, Troubleshooting) with file paths + line counts, plus task-specific navigation guides

**For full template:** See reference.md

---

## Content Optimization Strategies

**For full examples with before/after:** See reference.md

### Quick Reference

**1. Extract-Consolidate-Reference (ECR)**
- Problem: Duplicate information across files
- Solution: Single source of truth, reference from other docs
- Example savings: 1,500 lines across 4 files

**2. Split Large Monoliths (SLM)**
- Problem: Single file >1,000 lines
- Solution: Split by responsibility (OVERVIEW, PIPELINE, BUSINESS_LOGIC, etc.)
- Benefit: Each file fits on one screen

**3. Table-ify Prose (T2T)**
- Problem: Long paragraphs explaining logic
- Solution: Convert to tables with What/When/Why/Where columns
- Example savings: 85% reduction (200 lines → 30 lines)

**4. Add llms.txt Index**
- Problem: AI agents can't find relevant docs
- Solution: Create index with doc summaries and task-specific navigation

**5. Condense File Structure Trees**
- Show only key files, collapse similar items with [N more files]
- Example savings: 67% reduction (60 lines → 20 lines)

**6. Bullet Points Over Paragraphs**
- Convert prose to dense bullet points or single-sentence summaries
- Example savings: 75% reduction (4 lines → 1 line)

---

## Anti-Patterns to Avoid

**For detailed examples:** See reference.md

### Quick Reference

**1. Don't Write Tutorials**
- Why: AI agents need REFERENCE, not teaching
- Bad: Step-by-step walkthroughs explaining every detail
- Good: Checklist with base class, required methods, file:line references

**2. Don't Explain Obvious Code**
- Why: AI can read code directly
- Bad: Line-by-line prose restating code logic
- Good: One-line summary with file:line reference + WHY

**3. Don't Mix Abstraction Levels**
- Why: Confuses readers, mixes strategic and tactical
- Bad: OVERVIEW.md with implementation details (asyncio.gather, table indexes)
- Good: OVERVIEW.md stays high-level, links to detailed architecture docs

**4. Don't Create Deep Directory Nesting**
- Why: AI agents struggle with deep hierarchies
- Bad: 7+ levels of nested directories
- Good: 2-3 levels max (docs/architecture/COMPONENT.md)

**5. Don't Use Relative Paths Without Context**
- Why: AI can't resolve without knowing current location
- Bad: `../processors/base.py`
- Good: `processors/base_processor.py` or absolute path

**6. Don't Duplicate Content Across Hierarchy**
- Why: Wastes context tokens, creates maintenance burden
- Bad: Testing standards repeated in global, project, and tool CLAUDE.md
- Good: Define once (global), reference elsewhere (project, tool)

---

## Validation Checklist

Before committing documentation changes:

### Duplication Check
- [ ] No duplicate core principles (defined in global only)
- [ ] No duplicate testing patterns (defined in project only)
- [ ] No duplicate code style rules (defined in project only)
- [ ] No duplicate subsystem patterns (defined in parent subsystem only)

### Content Optimization
- [ ] Business logic in table format (not prose)
- [ ] Decision matrices for strategies (not paragraphs)
- [ ] File structure condensed (not full tree)
- [ ] Bullet points over paragraphs where possible
- [ ] Location references include file:line when relevant

### Line Count Targets
- [ ] Global CLAUDE.md: 100-120 lines
- [ ] Project CLAUDE.md: 150-180 lines
- [ ] Subsystem CLAUDE.md: 120-150 lines
- [ ] Framework CLAUDE.md: 100-120 lines
- [ ] Simple Tool CLAUDE.md: 200-250 lines
- [ ] Complex Tool CLAUDE.md: 300-400 lines max

### Deep-Dive Extraction
- [ ] If CLAUDE.md > 400 lines, extract to QUICKREF.md
- [ ] Code examples with before/after → QUICKREF.md
- [ ] Detailed implementations → QUICKREF.md
- [ ] Keep quick reference + "See QUICKREF for details"

### Hierarchy Integrity
- [ ] Child files reference parent files (not duplicate)
- [ ] Each level focuses on unique information
- [ ] Clear separation of concerns across levels

### AI-Readability
- [ ] Can AI find relevant doc in <30 seconds via llms.txt?
- [ ] Can AI understand component in <5 min reading OVERVIEW?
- [ ] Can AI find specific function via API_REFERENCE?
- [ ] Can AI debug issue via TROUBLESHOOTING?

### Structure
- [ ] llms.txt index exists and is accurate (if needed)
- [ ] No file >600 lines (except BUSINESS_RULES if needed)
- [ ] Directory depth ≤3 levels
- [ ] No duplicate files

### Maintenance
- [ ] Single source of truth for business rules
- [ ] No scattered duplicates
- [ ] Archive clearly marked as historical (if applicable)
- [ ] Cross-references use file paths, not relative links

---

## Templates

### Template: Simple Tool CLAUDE.md (200-250 lines)

```markdown
# [Tool Name] Import

**Purpose**: [One sentence describing what this import does]

**Key Patterns**:
- Extends framework base classes (see `framework/CLAUDE.md`)
- [Tool-specific pattern 1]
- [Tool-specific pattern 2]

**Configuration**:
- Config location: `/path/to/config.json` → `[tool_name]` section
- Required keys: [list required config keys]

**Critical Logic**:
[Only if tool has unique business logic - DELETE section if not applicable]

**Common Gotchas**:
[Only if tool has known edge cases - DELETE section if not applicable]

**Testing**:
- Unit tests: `tests/test_[tool_name]/unit_tests/`
- Integration tests: `tests/test_[tool_name]/integration_tests/`
- See project CLAUDE.md for testing standards

**References**:
- Framework: `framework/CLAUDE.md`
- Testing standards: Project CLAUDE.md
```

### Template: Complex Tool CLAUDE.md (300-400 lines)

**Structure**:
1. **Purpose + Performance Metrics** (5-10 lines)
2. **Architecture Overview** (40-60 lines) - Core design, storage architecture table, processing pipeline
3. **File Structure** (20-40 lines, condensed tree)
4. **Critical Business Logic** (60-80 lines, table format)
5. **Key Architecture Patterns** (60-80 lines) - Pattern name, summary, benefits, "See QUICKREF.md"
6. **Common Gotchas** (40-60 lines, 8-10 condensed subsections)
7. **Key Constants** (10-20 lines, bullet list)
8. **When in Doubt** (10-15 lines, numbered list with references)

**Total**: 300-400 lines max

**For full example structure:** See reference.md

---

## Summary

### The Golden Rules

1. **Hierarchical Inheritance** - Never duplicate parent content, always reference
2. **100-200 Line Target** - Most files should be this range (complex tools 300-400 max)
3. **Tables Over Prose** - Business logic, gotchas, decisions all in table format
4. **Extract Deep-Dive** - Code examples and detailed implementations → QUICKREF.md
5. **Define Once** - Testing, code style, core principles defined once at appropriate level
6. **Location References** - Always include file:line for implementation details
7. **Concise Over Comprehensive** - Documentation is a MAP, not a TUTORIAL

### The Test

Can you scan the documentation in 30 seconds and find critical information? If not, it's too verbose.

### The Goal

Minimize agent context, maximize information utility, maintain hierarchical clarity.

**Remember**: Less is more. Every line consumes agent context. Make every line count.

---

**For comprehensive templates and examples:** See reference.md
