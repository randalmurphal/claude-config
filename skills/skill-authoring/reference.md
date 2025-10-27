# Skill Authoring Reference Guide

**Companion to SKILL.md** - Detailed examples, patterns, and troubleshooting.

---

## Table of Contents

1. [Description Examples](#description-examples)
2. [Content Organization Examples](#content-organization-examples)
3. [Before/After Examples](#beforeafter-examples)
4. [Migration Guide](#migration-guide)
5. [Real-World Examples](#real-world-examples)
6. [Troubleshooting](#troubleshooting)

---

## Description Examples

### Example 1: Testing Skill

**❌ BAD (Too vague):**
```yaml
description: Helps with testing
```
**Issues:** No technology, no patterns, no triggers

**✅ GOOD (Specific):**
```yaml
description: Write tests following 3-layer pyramid (unit 95%, integration 85%, E2E critical paths) with 1:1 file mapping for unit tests. Covers test organization, coverage requirements, fixtures, and best practices. Use when writing tests, checking coverage, or validating test structure.
```
**Why good:**
- Specific approach (3-layer pyramid)
- Coverage targets (95%, 85%)
- Clear pattern (1:1 file mapping)
- Multiple triggers (writing, checking, validating)

---

### Example 2: Code Style Skill

**❌ BAD (Too generic):**
```yaml
description: Python coding standards
```
**Issues:** No specific standards mentioned, no triggers

**✅ GOOD (Specific):**
```yaml
description: Python coding standards including line length (80 chars), naming conventions (snake_case, PascalCase), type hints, docstrings, exception handling, and logging patterns. Use when writing new Python code or reviewing code quality.
```
**Why good:**
- Specific standards (80 chars, naming conventions)
- Technologies mentioned (Python)
- Clear triggers (writing code, reviewing quality)

---

### Example 3: Documentation Skill

**❌ BAD (First person):**
```yaml
description: I can help you write documentation for your project
```
**Issues:** First person (should be third person), vague

**✅ GOOD (Third person, specific):**
```yaml
description: Write AI-readable documentation following concise-over-comprehensive principle, hierarchical CLAUDE.md inheritance (100-200 line rule), and structured formats (tables over prose). Use when writing CLAUDE.md files, creating project documentation, or optimizing existing docs.
```
**Why good:**
- Third person
- Specific approach (AI-readable, hierarchical inheritance)
- Clear patterns (100-200 line rule, tables over prose)
- Multiple triggers (writing, creating, optimizing)

---

### Example 4: Security Skill

**❌ BAD (Too broad):**
```yaml
description: Security best practices for applications
```
**Issues:** Too broad, no specific focus, no triggers

**✅ GOOD (Focused):**
```yaml
description: Audit code for security vulnerabilities following OWASP Top 10. Use when analyzing vulnerability data, calculating risk scores, or determining remediation priority.
```
**Why good:**
- Specific framework (OWASP Top 10)
- Clear triggers (analyzing, calculating, determining)
- Focused scope (auditing, not implementing)

---

## Content Organization Examples

### Full Example: Testing Standards Pattern

```markdown
---
name: testing-standards
description: Write tests following 3-layer pyramid with 1:1 file mapping. Use when writing tests, checking coverage, or validating test structure.
allowed-tools:
  - Read
  - Bash
  - Grep
---

# Testing Standards Skill

**Purpose:** Guide test writing with clear structure, coverage targets, quality standards.

**When to use:** Writing tests, checking coverage, validating test organization, debugging test failures.

---

## Core Principles (Remember These)

1. **Tests prove correctness** - Not just coverage numbers
2. **Write tests that would catch real bugs** - No useless assertions
3. **Test behavior, not implementation** - Don't test private methods
4. **Keep tests maintainable** - DRY applies to tests too
5. **Fast feedback** - Unit tests run in <5s, integration <30s

---

## 3-Layer Testing Pyramid

| Layer | Coverage | Organization | Characteristics |
|-------|----------|--------------|-----------------|
| Unit | 95%+ | 1:1 file mapping | Fast, isolated, mocked |
| Integration | 85%+ | 2-4 files per module | Real dependencies |
| E2E | Critical paths | 1-3 files total | Full workflows |

**For detailed layer examples:** See examples.md

---

## Quick Reference

**Run tests:**
```bash
pytest tests/ -v                                    # All tests
pytest tests/ --cov=src --cov-report=term-missing  # With coverage
pytest tests/unit/ -v                               # Unit only
```

**Checklist:**
- [ ] All tests pass
- [ ] Coverage ≥95%
- [ ] Test names descriptive
- [ ] Mock external dependencies

---

**For comprehensive examples and advanced patterns:** See reference.md
```

**Why this structure works:**
1. **Front-loaded critical info** - Principles and pyramid upfront
2. **Table for key info** - Scannable layer comparison
3. **Quick reference** - Copy-paste ready commands
4. **Progressive disclosure** - Points to detailed files

---

### Full Example: Security Audit Pattern

```markdown
---
name: security-auditor
description: Audit code for security vulnerabilities following OWASP Top 10. Use for production-bound code.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebSearch
  - Write
---

# Security Auditor Skill

**Purpose:** Identify security vulnerabilities following industry standards.

**When to use:** Auditing production-bound code, security reviews, vulnerability assessment.

---

## OWASP Top 10 Checklist

| # | Vulnerability | Check For | Location Pattern |
|---|---------------|-----------|------------------|
| 1 | Injection | Unsanitized SQL/command inputs | Query builders, exec calls |
| 2 | Auth Failure | Weak passwords, no MFA | Auth modules, session mgmt |
| 3 | Data Exposure | Secrets in code/logs | Config files, log statements |
| 4 | XXE | XML parsing without protection | XML parsers, SOAP endpoints |
| 5 | Access Control | Missing auth checks | Route handlers, API endpoints |

**For complete checklist and examples:** See reference.md

---

## Quick Scan Commands

```bash
# Find potential SQL injection
grep -r "execute.*\+.*request" src/

# Find hardcoded secrets
grep -rE "(password|secret|api_key).*=.*['\"]" src/

# Find unsafe XML parsing
grep -r "XMLParser.*resolve_entities=True" src/
```

---

## Review Output Format

**Return valid JSON only:**
```json
{
  "status": "COMPLETE",
  "critical": [
    {"file": "path/to/file.py", "line": 123, "issue": "...", "fix": "..."}
  ],
  "important": [...],
  "minor": [...]
}
```

---

**For detailed vulnerability patterns and remediation:** See reference.md
```

**Why this structure works:**
1. **Actionable checklist** - OWASP Top 10 in table format
2. **Quick scan commands** - Immediate value
3. **Structured output** - JSON format specification
4. **Tool restrictions** - Read-only with web search for latest vulns

---

## Before/After Examples

### Example: Converting Prose to Tables

**❌ BEFORE (Prose-heavy, hard to scan):**
```markdown
The testing pyramid has three layers. The bottom layer is unit tests which should
have 95% or higher line coverage and 100% function coverage. Unit tests should be
organized with 1:1 file mapping meaning one test file per production file. The
middle layer is integration tests which should have 85% or higher coverage and
should be organized with 2 to 4 test files per module rather than per file. The
top layer is E2E tests which don't have a coverage percentage but should cover
all critical user workflows. E2E tests should be organized with 1 to 3 test files
for the entire project.
```

**✅ AFTER (Table format, scannable):**
```markdown
## Testing Pyramid

| Layer | Coverage | Organization | Purpose |
|-------|----------|--------------|---------|
| Unit | ≥95% line, 100% function | 1:1 file mapping | Isolated function testing |
| Integration | ≥85% | 2-4 files per module | Component interaction |
| E2E | Critical paths | 1-3 files total | Complete user workflows |
```

**Benefits:**
- 75% shorter
- Scannable in 5 seconds
- Clear structure
- Easy to reference

---

### Example: Adding Before/After Code Examples

**❌ BEFORE (Explanation only):**
```markdown
## Naming Conventions

Functions should use snake_case naming. Classes should use PascalCase. Constants
should use UPPER_CASE with underscores between words. Variable names should be
descriptive rather than abbreviated.
```

**✅ AFTER (With code examples):**
```markdown
## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Functions | snake_case | `process_scan_results()` |
| Classes | PascalCase | `AssetProcessor` |
| Constants | UPPER_CASE | `DEFAULT_BATCH_SIZE` |

**❌ BAD:**
```python
def get_a(u: str) -> dict | None:
    return cache.lookup_and_parse('assets', 'uuid', u)
```
**Why bad:** Cryptic abbreviations (a, u)

**✅ GOOD:**
```python
def get_asset_by_uuid(uuid: str) -> dict | None:
    return cache.lookup_and_parse('assets', 'uuid', uuid)
```
**Why good:** Descriptive names, obvious meaning
```

**Benefits:**
- Shows exactly what to do
- Explains why with specific examples
- Scannable with ❌/✅ markers

---

### Example: Progressive Disclosure

**❌ BEFORE (Everything in SKILL.md, 800 lines):**
```markdown
# Testing Standards

## Unit Testing

[100 lines of detailed unit test patterns]

## Integration Testing

[150 lines of integration test patterns]

## E2E Testing

[120 lines of E2E patterns]

## Fixtures and Mocking

[200 lines of fixture patterns with examples]

## Test Organization

[80 lines of directory structure patterns]

## Common Testing Pitfalls

[150 lines of anti-patterns with solutions]
```

**✅ AFTER (Progressive disclosure, SKILL.md 350 lines):**

**SKILL.md:**
```markdown
# Testing Standards

## Core Principles
[20 lines]

## 3-Layer Pyramid
[Table with key info - 30 lines]

## Coverage Requirements
[Table - 15 lines]

## File Organization
[Quick overview - 25 lines]

## Quick Reference
[Commands and checklist - 30 lines]

**For comprehensive examples:** See reference.md
**For fixture patterns:** See examples.md
```

**reference.md:**
```markdown
# Testing Standards Reference

## Detailed Unit Test Patterns
[100 lines with comprehensive examples]

## Detailed Integration Test Patterns
[150 lines]

## Detailed E2E Test Patterns
[120 lines]

## Fixtures and Mocking Deep Dive
[200 lines with multiple examples]

## Common Pitfalls with Solutions
[150 lines]
```

**Benefits:**
- SKILL.md scannable in 2 minutes
- Details loaded only when needed
- Saves context tokens
- Easier to maintain

---

## Migration Guide

### Step-by-Step: Improving an Existing Skill

#### Step 1: Audit Current State

**Run these checks:**
```bash
# Check line count
wc -l skills/my-skill/SKILL.md

# Check description
head -n 10 skills/my-skill/SKILL.md | grep "description:"

# Check for tables vs prose
grep -c "^|" skills/my-skill/SKILL.md  # Count table rows
grep -c "^[A-Z]" skills/my-skill/SKILL.md  # Count prose lines
```

**Questions to ask:**
- [ ] Is SKILL.md >500 lines? → Need to extract content
- [ ] Does description include "Use when"? → Need to add triggers
- [ ] Are there before/after examples? → Need to add them
- [ ] Is critical info in tables? → Need to convert prose
- [ ] Is description third-person? → Need to fix

---

#### Step 2: Enhance Description

**BEFORE (Vague):**
```yaml
description: Helps with Python code quality
```

**IDENTIFY:** What's missing?
- No specific standards mentioned
- No technologies (already have "Python")
- No trigger scenarios

**AFTER (Enhanced):**
```yaml
description: Python coding standards including line length (80 chars), naming conventions (snake_case, PascalCase), type hints, docstrings, exception handling, and logging patterns. Use when writing new Python code or reviewing code quality.
```

**What changed:**
- Added specifics: 80 chars, naming conventions
- Added patterns: type hints, docstrings, logging
- Added triggers: "writing new Python code", "reviewing code quality"

---

#### Step 3: Convert Prose to Tables

**BEFORE:**
```markdown
## Error Handling

You should only use try/except for connection errors. This includes network
calls using requests, database connections with pymongo or sqlalchemy, and
cache connections to redis or memcached. Don't use try/except for dict.get()
operations, list access, file I/O, JSON parsing, or type conversions. Always
use specific exceptions, never bare except clauses.
```

**AFTER:**
```markdown
## Error Handling

**Use try/except ONLY for:**

| Category | Examples |
|----------|----------|
| Network | requests.Timeout, requests.ConnectionError, requests.HTTPError |
| Database | pymongo errors, sqlalchemy errors |
| Cache | redis errors, memcached errors |

**DO NOT use try/except for:**
- dict.get() operations (returns None safely)
- List/dict access with defaults
- File I/O (let it fail with clear error)
- JSON parsing (let it fail with clear error)
- Type conversions (validate first)

**Always:** Use specific exceptions, never `except:` (bare except)
```

**Benefits:**
- Scannable categories
- Clear DO and DON'T lists
- 60% more readable
- Easier to reference

---

#### Step 4: Add Before/After Examples

**BEFORE (No examples):**
```markdown
## Logging Standards

Use logging.getLogger(__name__) at module level. Include context in log messages
like IDs and counts. Use appropriate log levels.
```

**AFTER (With examples):**
```markdown
## Logging Standards

**Setup (once per module):**
```python
import logging
LOG = logging.getLogger(__name__)
```

**❌ BAD:**
```python
print("Processing record")
LOG.info("Done")
```
**Why bad:** No context, using print(), vague "Done"

**✅ GOOD:**
```python
LOG.debug(f"Processing record {record_id}")
LOG.info(f"Processed batch of {count} records in {elapsed:.2f}s")
```
**Why good:** Context included (IDs, counts, timing), appropriate levels
```

**Benefits:**
- Shows exact pattern to follow
- Explains specific mistakes
- Copy-paste ready code

---

#### Step 5: Extract Content Over 500 Lines

**If SKILL.md is 750 lines:**

**Keep in SKILL.md (target 400 lines):**
- Core principles (3-6 rules)
- Quick reference table/commands
- Common patterns (brief overview)
- Validation checklist
- Common issues table

**Move to reference.md (350 lines):**
- Detailed pattern explanations
- Comprehensive examples
- Advanced techniques
- Troubleshooting guide
- Edge cases

**Add at bottom of SKILL.md:**
```markdown
---

**For comprehensive examples and advanced patterns:** See reference.md
```

**Add at top of reference.md:**
```markdown
# [Skill Name] Reference Guide

**Companion to SKILL.md** - Detailed examples, patterns, and troubleshooting.
```

---

#### Step 6: Test Discovery

**Write realistic prompts:**
```
# For testing skill
"Help me write tests for my authentication module"

# For documentation skill
"I need to document this API endpoint"

# For code quality skill
"Review this function for quality issues"
```

**Check if skill loaded:**
1. Look for skill-specific guidance in response
2. Check if Claude follows patterns from skill
3. Run with `--debug` flag to see skill loading

**If skill not discovered:**
- Add more trigger keywords to description
- Make description more specific
- Check YAML validation errors

---

## Real-World Examples

### Example 1: agent-prompting Skill

**What makes it excellent:**

1. **Proactive trigger in description:**
   ```yaml
   description: MUST BE USED PROACTIVELY when spawning sub-agents
   ```

2. **Comprehensive prompt templates:**
   - Clear objective (REQUIRED)
   - Success criteria (REQUIRED)
   - Expected output format (CRITICAL)
   - Context (OPTIONAL)

3. **Decision frameworks:**
   - Parallel vs sequential table
   - When to use agents vs tools
   - Task boundary patterns

4. **Before/after for every pattern:**
   ```markdown
   **BEFORE (Vague):**
   Investigate authentication system.

   **AFTER (Clear):**
   Find JWT verification logic.
   Success: File path + line number + library name + code snippet
   ```

5. **Critical inline standards section:**
   - Standards to copy into agent prompts
   - Belt + suspenders approach
   - Guarantees sub-agents see critical rules

**Why it works:**
- Mandatory usage ("MUST BE USED PROACTIVELY")
- Actionable templates
- Clear decision frameworks
- Every concept has example

---

### Example 2: testing-standards Skill

**What makes it excellent:**

1. **Specific coverage targets in description:**
   ```yaml
   description: 3-layer pyramid (unit 95%, integration 85%, E2E critical paths)
   ```

2. **Visual pyramid diagram:**
   ```
          /\
         /E2E\
        /------\
       /  INT   \
      /----------\
     /    UNIT    \
    /--------------\
   ```

3. **Comprehensive table for organization:**
   | Layer | Coverage | Organization | Characteristics |
   |-------|----------|--------------|-----------------|
   | Unit | ≥95% | 1:1 file mapping | Fast, isolated |

4. **Three organization patterns:**
   - Single test function (simple)
   - Parametrized tests (recommended)
   - Separate test methods (critical)

5. **Copy-paste ready commands:**
   ```bash
   pytest tests/ --cov=src --cov-report=term-missing
   ```

**Why it works:**
- Clear structure (pyramid)
- Specific targets (95%, 85%)
- Multiple approaches for different scenarios
- Actionable commands

---

### Example 3: ai-documentation Skill

**What makes it excellent:**

1. **Clear principle upfront:**
   ```
   Concise over comprehensive - Documentation is a MAP not a TUTORIAL
   ```

2. **Hierarchical inheritance with line count targets:**
   | Level | Lines | Focus |
   |-------|-------|-------|
   | Global | 100-120 | Decision framework |
   | Project | 150-180 | Project standards |
   | Subsystem | 120-150 | Architecture overview |

3. **Before/after for every pattern:**
   - Extract-Consolidate-Reference (ECR) with line savings
   - Split Large Monoliths (SLM) with before/after structure
   - Table-ify Prose (T2T) with 85% reduction example

4. **Multiple document type templates:**
   - OVERVIEW.md (100-200 lines)
   - BUSINESS_RULES.md (300-800 lines)
   - ARCHITECTURE.md (200-400 lines)
   - API_REFERENCE.md (200-600 lines)

5. **Comprehensive anti-patterns section:**
   - Don't write tutorials
   - Don't explain obvious code
   - Don't mix abstraction levels
   - Don't create deep nesting

**Why it works:**
- Principle-driven (concise over comprehensive)
- Specific line count targets
- Savings quantified (85% reduction)
- Multiple templates for different needs

---

## Troubleshooting

### Issue: Skill Not Being Discovered

**Symptoms:**
- Relevant prompt doesn't trigger skill
- Claude gives generic advice instead of skill guidance
- Skill works when explicitly invoked but not automatically

**Diagnosis:**
```bash
# Check description
head -n 10 skills/my-skill/SKILL.md | grep "description:"

# Verify YAML syntax
python3 -c "import yaml; yaml.safe_load(open('skills/my-skill/SKILL.md'))"
```

**Fixes:**

1. **Add trigger keywords:**
   ```yaml
   # Before
   description: Testing best practices

   # After
   description: Write pytest tests with fixtures. Use when writing tests, checking coverage, debugging test failures, or validating test structure.
   ```

2. **Make description more specific:**
   ```yaml
   # Before
   description: Documentation standards

   # After
   description: Write AI-readable documentation following concise-over-comprehensive principle and 100-200 line rule. Use when writing CLAUDE.md files or optimizing existing docs.
   ```

3. **Include technology names:**
   ```yaml
   # Before
   description: Database query optimization

   # After
   description: MongoDB aggregation pipeline optimization including early filtering, index usage, and $lookup optimization. Use when writing aggregation queries or debugging slow pipelines.
   ```

---

### Issue: Skill Loaded But Ignored

**Symptoms:**
- Skill shows up in debug output
- Claude doesn't follow patterns from skill
- Claude gives different advice than skill

**Diagnosis:**
```bash
# Check if critical info is buried
head -n 50 skills/my-skill/SKILL.md | grep -c "^##"  # Should have 3-5 sections
grep -c "^|" skills/my-skill/SKILL.md  # Should have tables
```

**Fixes:**

1. **Move critical info to top:**
   ```markdown
   # BEFORE (principles buried at line 200)
   [Long introduction]
   [History]
   [Background]
   ## Core Principles  <- Too late

   # AFTER (principles upfront)
   ## Core Principles  <- Right after intro
   [Principles here]
   ```

2. **Convert prose to tables:**
   ```markdown
   # BEFORE (prose)
   The unit tests should have 95% coverage and use 1:1 file mapping...

   # AFTER (table)
   | Layer | Coverage | Organization |
   |-------|----------|--------------|
   | Unit | 95% | 1:1 file mapping |
   ```

3. **Add more examples:**
   ```markdown
   ## Pattern

   **❌ BAD:**
   [bad example]

   **✅ GOOD:**
   [good example]
   ```

---

### Issue: Skill Too Long (>500 Lines)

**Symptoms:**
- SKILL.md is 600+ lines
- Takes long time to load
- Claude context filling up quickly

**Diagnosis:**
```bash
wc -l skills/my-skill/SKILL.md  # Should be <500
```

**Fixes:**

1. **Extract to reference.md:**
   ```bash
   # Create reference file
   touch skills/my-skill/reference.md
   ```

2. **Move detailed content:**
   - Comprehensive examples → reference.md
   - Advanced patterns → reference.md
   - Troubleshooting → reference.md
   - Edge cases → reference.md

3. **Keep in SKILL.md:**
   - Core principles
   - Quick reference table
   - Common patterns (brief)
   - Validation checklist

4. **Add pointer at bottom of SKILL.md:**
   ```markdown
   ---

   **For comprehensive examples and advanced patterns:** See reference.md
   ```

---

### Issue: Multiple Skills Match Same Prompt

**Symptoms:**
- Claude seems confused about which skill to use
- Mixes guidance from multiple skills
- Inconsistent responses

**Diagnosis:**
```bash
# Check for overlapping descriptions
grep "^description:" skills/*/SKILL.md
```

**Fixes:**

1. **Make descriptions more specific:**
   ```yaml
   # Skill A - Too broad
   description: Testing best practices

   # Skill B - Too broad
   description: Code quality standards

   # AFTER - Specific domains
   # Skill A
   description: Write pytest unit tests with 95% coverage. Use when writing Python unit tests or checking test coverage.

   # Skill B
   description: Python code style including naming, type hints, and documentation. Use when writing new Python code or reviewing code style.
   ```

2. **Narrow trigger scenarios:**
   ```yaml
   # BEFORE (overlapping)
   description: Use when reviewing code
   description: Use when improving code quality

   # AFTER (distinct)
   description: Use when reviewing code for security vulnerabilities
   description: Use when refactoring complex functions
   ```

---

### Issue: YAML Validation Error

**Symptoms:**
- Skill doesn't load at all
- Error messages about YAML syntax
- Skill not showing in skill list

**Diagnosis:**
```bash
# Validate YAML
python3 -c "import yaml; print(yaml.safe_load(open('skills/my-skill/SKILL.md').read().split('---\n')[1]))"
```

**Common Errors:**

1. **Field too long:**
   ```yaml
   # ERROR - name >64 chars
   name: my-really-long-skill-name-that-exceeds-the-maximum-allowed-length

   # FIX - shorten name
   name: my-skill-name
   ```

2. **XML tags in description:**
   ```yaml
   # ERROR - XML tags not allowed
   description: Use <code> tags for examples

   # FIX - remove XML
   description: Use code blocks for examples
   ```

3. **Reserved words:**
   ```yaml
   # ERROR - reserved word
   name: skill

   # FIX - use different name
   name: my-skill
   ```

4. **Missing required field:**
   ```yaml
   # ERROR - no description
   name: my-skill

   # FIX - add description
   name: my-skill
   description: What it does and when to use it
   ```

---

## Advanced Patterns

### Pattern: Multi-Language Skill

**Use when:** Skill applies to multiple programming languages

**Structure:**
```markdown
## Quick Reference by Language

### Python
```python
[Python example]
```

### JavaScript
```javascript
[JavaScript example]
```

### Go
```go
[Go example]
```
```

**Example:** testing-standards skill shows pytest, Jest, and Go testing patterns

---

### Pattern: Command Reference Skill

**Use when:** Skill primarily documents commands/tools

**Structure:**
```markdown
## Commands by Task

| Task | Command | Options |
|------|---------|---------|
| Run all tests | `pytest tests/` | `-v` for verbose |
| Check coverage | `pytest --cov=src` | `--cov-report=html` |

## Common Workflows

**Test-driven development:**
```bash
pytest-watch  # Re-run on file changes
```
```

---

### Pattern: Decision Tree Skill

**Use when:** Skill helps choose between options

**Structure:**
```markdown
## Decision Framework

| If... | Then use... | Why |
|-------|-------------|-----|
| Task <3 files | Tools directly | Faster |
| Task >3 files | Task agent | Context management |
| Multiple tasks | Parallel agents | Speed |
| Sequential deps | Sequential agents | Dependencies |
```

---

## Summary Checklist

**Creating a new skill:**
- [ ] Name ≤64 chars, lowercase/numbers/hyphens
- [ ] Description includes WHAT, technologies, and WHEN triggers
- [ ] Description is third-person
- [ ] SKILL.md <500 lines (extract to reference.md if needed)
- [ ] Core principles upfront
- [ ] Tables for structured info
- [ ] Before/after examples for key concepts
- [ ] Quick reference with commands/checklists
- [ ] Tested with realistic prompts
- [ ] YAML validates correctly

**Migrating existing skill:**
- [ ] Enhanced description with triggers
- [ ] Converted prose to tables
- [ ] Added before/after examples
- [ ] Extracted to reference.md if >500 lines
- [ ] Added progressive disclosure pointers
- [ ] Tested discovery with prompts
- [ ] Verified YAML still valid

---

**For quick reference and core principles:** See SKILL.md
