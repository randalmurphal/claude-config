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

**AI agents can read code directly.** Documentation should provide structure and location references, not exhaustive explanations.

**Pattern**:
```markdown
❌ BAD (Tutorial-style):
The DV processor handles detected vulnerabilities by first checking if the
vulnerability already exists in the database. It does this by computing a hash
of the asset ID, sorted CVE list, plugin ID, port, protocol, IP address...
[200 more lines explaining every detail]

✅ GOOD (Map-style):
**DV Deduplication**
- Hash: MD5(asset_id + sorted_cves + plugin_id + port + protocol + ip + is_external)
- Location: `processors/detected_vuln_processor.py:_compute_dv_hash()`
- Purpose: Unique ID for DV deduplication
- Gotcha: Sort CVEs before hashing (order matters)
```

### 2. Structure Over Prose

**Tables, bullets, code snippets >>> Paragraphs**

AI agents parse structured content faster and more accurately.

**Before** (Prose-heavy):
```markdown
The asset matching cascade operates in ten distinct levels, with each level
representing a different quality tier. The highest quality matches are External
IP matches, followed by hostUUID and UUID matches...
```

**After** (Structured):
```markdown
## Asset Matching Cascade (10 Levels)

| Level | Match Fields | Quality | Location |
|-------|-------------|---------|----------|
| 1 | External IP | SPECIAL | Updates ALL matched assets |
| 2 | hostUUID | HIGH | asset_cascade_matcher.py:L234 |
| 3 | UUID | HIGH | asset_cascade_matcher.py:L289 |
| 4-7 | Compound (IP+MAC, IP+DNS, etc.) | MEDIUM | asset_cascade_matcher.py:L345 |
| 8-10 | Single field (MAC, DNS, IP) | LOW | asset_cascade_matcher.py:L456 |

See: `constants.py:CASCADE_LEVELS` for full configuration
```

### 3. Location References Over Explanations

**Always include file:line_number for implementation details.**

AI agents need to know WHERE to look, then they can read the code.

**Pattern**:
```markdown
## Business Rule: Compliance Pass/Info Handling

**Behavior**:
- ALWAYS read Pass/Info records
- Skip insert if '0' NOT in compliance_severities config
- Close DV when becomes Pass/Info
- NEVER reopen if Pass/Info disappears

**WHY**: Pass = compliant = stay closed. Disappearance doesn't mean failure.

**Implementation**:
- Read check: `should_process_record()` @ detected_vuln_processor.py:145
- Insert skip: `determine_if_should_skip_dv_insert()` @ detected_vuln_processor.py:234
- Close logic: `should_close_compliance_dv()` @ detected_vuln_processor.py:456
- Reopen prevention: `build_dv_update_fields()` Step 3.2 @ detected_vuln_processor.py:567

**Config**: `config['compliance_severities']` - List of severity IDs to process
```

### 4. Hierarchical Context Boundaries

**Create clear "entry points" for different levels of detail.**

AI agents should quickly find:
1. High-level overview (what/why)
2. Architecture patterns (how it works)
3. Implementation details (where/when)
4. Gotchas and edge cases (watch out)

**File organization pattern**:
```
docs/
├── OVERVIEW.md           # 100-200 lines - What/Why/Architecture diagram
├── QUICK_REF.md          # 300-400 lines - Common tasks, gotchas, locations
│
├── architecture/         # HOW each component works
│   ├── COMPONENT_A.md    # 200-300 lines - Component overview + patterns
│   ├── COMPONENT_B.md
│   └── PATTERNS.md       # Cross-component patterns
│
├── implementation/       # WHERE specific logic lives
│   ├── BUSINESS_RULES.md # Table format with file:line references
│   ├── ERROR_HANDLING.md # Decision matrices
│   └── API_REFERENCE.md  # Function signatures + purposes
│
└── guides/               # WHEN to use specific approaches
    ├── TROUBLESHOOTING.md
    ├── HOW_TO.md
    └── COMMON_TASKS.md
```

### 5. Searchable Keywords

**Use consistent terminology and include searchable keywords.**

AI agents use semantic search - help them find relevant docs.

**Pattern**:
```markdown
# DV Processing Architecture

**Keywords**: detected vulnerability, DV, vulnerability processing, compliance,
patched view, closure logic, flows integration

**Related**: KV processing, Solution processing, Asset matching, DAA creation

[Rest of document...]
```

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

1. **Core Principles** (define in global only):
   - NO PARTIAL WORK, FAIL LOUD, QUALITY GATES, PORTABILITY
   - Parallel execution patterns
   - Decision framework (Proceed/Stop & ask/Override)

2. **Testing Patterns** (define in project only):
   - Coverage requirements (95% line, 100% function)
   - Test organization (1:1 file mapping, unit vs integration)
   - Test location conventions

3. **Code Style** (define in project only):
   - Line length limits
   - Type hint requirements
   - Naming conventions (snake_case, PascalCase)
   - Documentation rules (WHY not WHAT)

4. **Tool Configurations** (define in project only):
   - Linting command paths (ruff, pylint, mypy)
   - Formatter configurations
   - Build tool settings

5. **Error Handling Philosophy** (define in global only):
   - CRASH/RETRY/SKIP/WARN/FAIL-FAST strategies
   - When to use try/except
   - Error message requirements

6. **Subsystem Patterns** (define in subsystem, not tool level):
   - Multi-tenancy patterns
   - Database operation patterns
   - Caching strategies

### Hierarchical Inheritance Examples

**❌ Bad (Duplication)**:

Global CLAUDE.md:
```markdown
## Testing Standards
- 95% line coverage required
- 100% function coverage required
- 1:1 file mapping (one test file per source file)
```

Project CLAUDE.md:
```markdown
## Testing Standards  ← DUPLICATE!
- 95% line coverage required
- 100% function coverage required
- 1:1 file mapping (one test file per source file)
```

**Problem**: 2x duplication, agent loads both copies into context.

**✅ Good (Hierarchical)**:

Global CLAUDE.md:
```markdown
## Testing Standards
**Location:** `~/.claude/docs/TESTING_STANDARDS.md`

**Key rules:**
- 1:1 file mapping, 95%+ line coverage, 100% function coverage
- Every function: happy path + error cases + edge cases
- Integration tests: 2-4 files per module
```

Project CLAUDE.md:
```markdown
## Testing Structure
- Unit tests: `tests/test_[module]/unit_tests/`
- Integration tests: `tests/test_[module]/integration_tests/`
- Run: `pytest tests/test_[module]/ --cov=project.[module] -v`
- See global CLAUDE.md for coverage requirements
```

**Result**: Information defined once, referenced when needed, 50% reduction in duplication.

---

## When to Extract to QUICKREF.md

### Triggers (any one means extract to QUICKREF)

1. CLAUDE.md exceeds 400 lines
2. More than 5 code examples with before/after patterns
3. Detailed implementation walkthroughs (>50 lines per pattern)
4. Comprehensive testing strategies with mock examples
5. Refactoring guides with line-by-line explanations

### What Goes Where

**QUICKREF.md (deep-dive reference)**:
- Full code examples (before/after patterns)
- Detailed pattern implementations with line-by-line explanation
- Comprehensive testing strategies with mock/fixture examples
- Performance optimization guides
- Debugging strategies and common pitfalls with solutions
- Architecture deep dives with data flow diagrams (ASCII)

**CLAUDE.md (quick reference)**:
- Critical business logic (table format)
- Architecture overview (bullet points)
- Common gotchas (condensed with file:line references)
- Key constants and configuration
- "See QUICKREF.md for detailed implementations"

---

## AI-Specific Documentation Types

### Type 1: OVERVIEW.md (Quick Context)

**Purpose**: Give AI agent complete mental model in <5 minutes reading time
**Length**: 100-200 lines
**Format**: Mostly bullets and tables

**Template**:
```markdown
# [Component] Overview

**Purpose**: [One sentence]
**Performance**: [Key metrics if relevant]

## What It Does
- [Core responsibility 1]
- [Core responsibility 2]
- [Core responsibility 3]

## Architecture Diagram (ASCII)
```
[Simple ASCII flowchart]
```

## Key Components
| Component | Purpose | Location |
|-----------|---------|----------|
| [Name] | [What it does] | path/to/file.py |

## Data Flow
1. Input → Process A → Process B → Output
2. [Each step one line with file references]

## Critical Decisions
| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| [What] | [Why] | [Downside] |

## Common Gotchas
- [Issue 1] - [Why it happens] - [How to avoid]
- [Issue 2] - [Why it happens] - [How to avoid]

## Related Docs
- [Link to detailed architecture]
- [Link to business rules]
- [Link to API reference]
```

### Type 2: BUSINESS_RULES.md (Authoritative Source)

**Purpose**: Single source of truth for all business logic
**Length**: Variable (300-800 lines)
**Format**: Numbered table with WHY column

**Template**:
```markdown
# [Component] Business Rules

**Last Updated**: [Date]
**Validation**: Run integration tests to verify rules preserved

## Rules Index
[Quick navigation - rule number + one-line description]

## Rule Definitions

| # | Rule | Condition | Behavior | WHY | Implementation |
|---|------|-----------|----------|-----|----------------|
| 1 | [Name] | When [X] | Do [Y] | [Reason] | file.py:L123 |
| 2 | [Name] | When [X] | Do [Y] | [Reason] | file.py:L234 |

### Rule 1: [Name] (Detailed)

**Condition**: [When does this apply]
**Behavior**: [What should happen]
**WHY**: [Business justification]

**Implementation**:
- Primary: `function_name()` @ file.py:123
- Related: `helper_function()` @ file.py:234

**Test Coverage**: test_file.py::test_rule_1()

**Edge Cases**:
- Case A: [Behavior]
- Case B: [Behavior]

**History**: [Why this rule exists - optional but valuable]

---

[Repeat for each rule]
```

### Type 3: ARCHITECTURE.md (How It Works)

**Purpose**: Explain patterns and coordination, not line-by-line implementation
**Length**: 200-400 lines
**Format**: Mix of text, tables, code snippets

**Template**:
```markdown
# [Component] Architecture

**Keywords**: [Searchable terms]

## Design Principles
- [Principle 1]: [Why this matters]
- [Principle 2]: [Why this matters]

## Processing Pipeline

### Phase 1: [Name]
**Purpose**: [What this phase does]
**Input**: [Data structure]
**Output**: [Data structure]
**Location**: `module/file.py:function_name()`

**Key Steps**:
1. [Step] - [Location reference]
2. [Step] - [Location reference]

**Patterns Used**:
- [Pattern name]: [One-line description] - See PATTERNS.md

### Phase 2: [Name]
[Repeat structure]

## Key Patterns

### Pattern: [Name]

**Purpose**: [Why this pattern exists]
**When to use**: [Conditions]

**Example**:
```python
# Good pattern
[Code snippet]

# Anti-pattern (don't do this)
[Code snippet with explanation]
```

**Used by**: [List of components using this pattern]

## Integration Points
- Depends on: [Component A, Component B]
- Used by: [Component C, Component D]
- Coordinates with: [Component E]

## Performance Characteristics
- Time complexity: [Big O]
- Space complexity: [Big O]
- Bottlenecks: [Known constraints]

## Common Gotchas
[Number them, include file:line references]
```

### Type 4: API_REFERENCE.md (Function Catalog)

**Purpose**: Quick lookup of function signatures and purposes
**Length**: 200-600 lines
**Format**: Tables and short code snippets

**Template**:
```markdown
# [Module] API Reference

## Public Functions

| Function | Purpose | Input | Output | Location |
|----------|---------|-------|--------|----------|
| `func_a()` | [What it does] | [Types] | [Type] | file.py:L123 |
| `func_b()` | [What it does] | [Types] | [Type] | file.py:L234 |

### `function_name(param1: Type, param2: Type) -> ReturnType`

**Purpose**: [One sentence]

**Parameters**:
- `param1`: [What it is]
- `param2`: [What it is]

**Returns**: [What it returns]

**Raises**:
- `ExceptionType`: [When this happens]

**Example**:
```python
result = function_name(value1, value2)
```

**Location**: `module/file.py:123`

**Related**: [Other functions in same workflow]

---

[Repeat for each function]

## Internal Functions (For Reference)

[Table format - less detail than public functions]
```

### Type 5: TROUBLESHOOTING.md (Problem → Solution)

**Purpose**: Fast resolution of common issues
**Length**: 150-300 lines
**Format**: Problem/Solution pairs

**Template**:
```markdown
# [Component] Troubleshooting

## Quick Diagnosis

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| [Error message] | [Root cause] | [Solution + file reference] |
| [Behavior] | [Root cause] | [Solution + file reference] |

## Common Issues

### Issue: [Symptom]

**Symptom**: [What you see]
**Cause**: [Why it happens]
**Fix**: [Step-by-step with file references]

**Validation**: [How to confirm it's fixed]

**Related Issues**: [Links to similar problems]

---

### Issue: [Next symptom]
[Repeat structure]

## Debug Workflows

### When [Scenario Happens]

1. Check [Location 1] for [What to verify]
2. Run [Command] to [What to check]
3. If [Condition], then [Action]
4. Validate with [Test]

## Log Analysis

**Key log patterns to search for**:
- `ERROR: [pattern]` → Indicates [issue] → See [section]
- `WARNING: [pattern]` → Indicates [issue] → See [section]
```

---

## llms.txt Index Pattern

### Purpose

Help AI agents find relevant documentation quickly in large monorepos.

### When to Create

Create `llms.txt` when:
- Monorepo has >10 documentation files
- Multiple subsystems with separate docs
- Documentation spread across directories
- AI agents struggle to find relevant context

### Template Structure

**Location**: Root of docs folder or project root

```markdown
# llms.txt - AI Agent Documentation Index

## Quick Start
- /docs/OVERVIEW.md - System architecture overview (150 lines)
- /docs/QUICK_REF.md - Common tasks and gotchas (300 lines)

## Business Logic
- /docs/BUSINESS_RULES.md - Authoritative business rules catalog (800 lines)
- /docs/ERROR_HANDLING.md - Error handling strategies (200 lines)

## Architecture
- /docs/architecture/COMPONENT_A.md - Component A design (400 lines)
- /docs/architecture/COMPONENT_B.md - Component B processing (300 lines)

## Implementation Reference
- /docs/implementation/API_REFERENCE.md - Function catalog (400 lines)
- /docs/implementation/DATA_STRUCTURES.md - Schema reference (600 lines)

## Troubleshooting
- /docs/guides/TROUBLESHOOTING.md - Common issues and fixes (250 lines)
- /docs/guides/HOW_TO.md - Step-by-step guides (200 lines)

## For Specific Tasks

**Adding new component**:
1. Read /docs/architecture/PATTERNS.md
2. Reference /docs/BUSINESS_RULES.md for rules to preserve
3. See /docs/implementation/API_REFERENCE.md for base class

**Debugging failed operation**:
1. Check /docs/guides/TROUBLESHOOTING.md
2. Reference /docs/ERROR_HANDLING.md for recovery strategies
3. See /docs/architecture/[relevant_component].md for logic

**Understanding data flow**:
1. Start with /docs/OVERVIEW.md (big picture)
2. Read /docs/architecture/ files for specific components
3. Reference /docs/implementation/DATA_STRUCTURES.md for schemas
```

---

## Content Optimization Strategies

### Strategy 1: Extract-Consolidate-Reference (ECR)

**Problem**: Duplicate information across multiple files
**Solution**: Extract to single source, consolidate, add references

**Example**:
```
BEFORE:
- BUSINESS_RULES.md (828 lines) - Full rules
- DV_ARCHITECTURE.md (1,575 lines) - DV rules embedded
- KV_SOLUTION_ARCHITECTURE.md (942 lines) - KV rules embedded
- APPLICATION_ARCHITECTURE.md (540 lines) - App rules embedded

AFTER:
- BUSINESS_RULES.md (800 lines) - Authoritative source with file:line refs
- DV_ARCHITECTURE.md (400 lines) - "For DV business rules see BUSINESS_RULES.md #5-12"
- KV_SOLUTION_ARCHITECTURE.md (300 lines) - "For KV rules see BUSINESS_RULES.md #13-18"
- APPLICATION_ARCHITECTURE.md (250 lines) - "For app rules see BUSINESS_RULES.md #24-27"

Savings: -1,500 lines, single source of truth, clearer references
```

### Strategy 2: Split Large Monoliths (SLM)

**Problem**: Single file >1,000 lines
**Solution**: Split by responsibility, keep index

**Pattern**:
```
BEFORE:
DV_ARCHITECTURE.md (1,575 lines)
- Overview (100 lines)
- Processing pipeline (400 lines)
- Business logic (500 lines)
- Parallel coordination (300 lines)
- Integration points (275 lines)

AFTER:
dv/
├── OVERVIEW.md (150 lines) - High-level + navigation to other files
├── PIPELINE.md (400 lines) - Processing flow
├── BUSINESS_LOGIC.md (300 lines) - Rules summary + refs to BUSINESS_RULES.md
├── PARALLEL.md (300 lines) - Worker coordination
└── INTEGRATION.md (250 lines) - How DV connects to other components

Benefit: Each file fits on one screen, easier to navigate
```

### Strategy 3: Table-ify Prose (T2T)

**Problem**: Long paragraphs explaining logic
**Solution**: Convert to tables with columns: What/When/Why/Where

**Example**:

BEFORE (200 lines of prose):
```markdown
External IP detection is handled by the asset processor. The algorithm uses
the Python ipaddress module to match against CIDR notation and IP ranges.
The configuration can specify IPs as single addresses like "10.0.0.1", CIDR
blocks like "10.0.0.0/24", or ranges like "10.0.0.1-10.0.0.255". When an IP
matches the external IP configuration, it gets stored in the
data.externalIpAddresses field instead of the data.ipAddresses field. This
is important because external IPs have a completely separate security posture...
[180 more lines]
```

AFTER (30 lines as table):
```markdown
## IP Classification

| Type | Pattern | Field | Location | WHY |
|------|---------|-------|----------|-----|
| Internal | Not in external config | `data.ipAddresses` | asset_processor.py:145 | Default assumption |
| External | Matches external config | `data.externalIpAddresses` | asset_processor.py:189 | Separate security posture |

**External IP Matching** (asset_processor.py:check_if_ip_is_external()):
- Single IP: `10.0.0.1`
- CIDR: `10.0.0.0/24`
- Range: `10.0.0.1-10.0.0.255`
- Algorithm: Python `ipaddress` module

**Config**: `config['external_ip_ranges']` - List of IP patterns
```

Savings: 170 lines (85% reduction)

### Strategy 4: Add llms.txt Index

**Problem**: AI agents don't know which docs are most relevant
**Solution**: Create llms.txt index with doc summaries

See "llms.txt Index Pattern" section above for template.

### Strategy 5: Condense File Structure Trees

**BEFORE (60 lines)**:
```markdown
```
tenable_sc_refactor/
├── tenable_sc_import.py          # Main orchestrator with dual-view download
├── constants.py                   # Business logic constants (CASCADE_LEVELS, VIEW constants)
├── CLAUDE.md                      # This file
│
├── processors/                    # Business object processors
│   ├── base_processor.py         # Shared MongoDB/SQLite operations + universal consolidation
│   ├── scan_file_processor.py    # Two-pass scan processing orchestration
│   ├── parallel_processor_handler.py # Generic parallel processing with multiprocessing.Process
│   ├── scan_database_handler.py  # SQLite scan database operations wrapper
[... 30 more lines ...]
```
```

**AFTER (20 lines)**:
```markdown
```
tenable_sc_refactor/
├── tenable_sc_import.py          # Main orchestrator
├── constants.py                   # Business logic constants
├── processors/                    # Business object processors
│   ├── base_processor.py         # Shared operations + consolidation
│   ├── asset_cascade_matcher.py  # 10-level cascade matching
│   ├── known_vuln_processor.py   # KV creation + parallel worker
│   └── [6 more processors]
├── cache/                         # SQLite caching layer
├── api_handler/                   # Async API operations
└── refactor_notes/                # Reference documentation
```
```

Savings: 40 lines (67% reduction)

### Strategy 6: Bullet Points Over Paragraphs

**BEFORE**:
```markdown
The import framework provides a standardized approach to data ingestion that ensures consistency across all import tools. By following the three-phase processing pattern of fetch, normalize, and store, all imports maintain a consistent architecture that makes the codebase easier to understand and maintain. This consistency also enables shared utilities and reduces code duplication across different import implementations.
```

**AFTER**:
```markdown
**Framework Benefits**: Standardized error handling, logging, configuration management across all imports. Shared base classes reduce duplication, consistent testing patterns, centralized utilities.
```

Savings: 4 lines → 1 line, same information

---

## Anti-Patterns to Avoid

### ❌ Don't: Write Tutorials

AI agents don't need to be "taught" - they need REFERENCE material.

**Bad**:
```markdown
# How to Add a New Processor

In this guide, we'll walk through adding a new business object processor
step by step. First, let's understand what a processor does...
[500 lines of tutorial]
```

**Good**:
```markdown
# Adding New Processor - Checklist

**Base class**: `processors/base_processor.py:BaseProcessor`
**Pattern**: See `detected_vuln_processor.py` as reference

**Required methods**:
- `should_process_record()` - Determine if record should be processed
- `build_insert_doc()` - Create new BO document
- `build_update_fields()` - Generate update fields
- `_stage_reverse_relationships()` - Bidirectional relationships

**Steps**:
1. Create `processors/[name]_processor.py` extending BaseProcessor
2. Implement required methods (see API_REFERENCE.md)
3. Register in `main_import.py:_initialize_processors()`
4. Add business rules to BUSINESS_RULES.md
5. Create unit tests in `tests/test_[name]_processor.py`

**Testing**: See TESTING_STRATEGY.md for coverage requirements
```

### ❌ Don't: Explain Obvious Code

AI can read code - don't restate what's already clear.

**Bad**:
```markdown
The function first checks if the record is None. If it is None, it returns
False. Otherwise, it extracts the severity field from the record using the
get method with a default value of '0'. Then it checks if the severity is
in the list ['0', 'Pass', 'Info']. If it is, it returns True...
```

**Good**:
```markdown
**Skip compliance insert**: severity in ['0', 'Pass', 'Info']
- Location: `determine_if_should_skip_dv_insert()` @ detected_vuln_processor.py:234
- WHY: Pass/Info = compliant, no vulnerability exists
```

### ❌ Don't: Mix Abstraction Levels

Keep high-level docs high-level, detailed docs detailed.

**Bad** (OVERVIEW.md with implementation details):
```markdown
# System Overview

The system processes vulnerability data through three phases. In phase 1,
the AsyncTenableSCClient uses sessionless API key authentication to download
scan data in parallel chunks of 5000 records with 10 concurrent workers.
The download_manager.py file implements this using asyncio.gather() with
a semaphore to limit concurrency. Each chunk is streamed to SQLite using
the vulndetails_records table which has indexes on pluginID and severity...
[Mixing architecture with implementation]
```

**Good** (OVERVIEW.md stays high-level):
```markdown
# System Overview

## Three-Phase Pipeline
1. **Download**: Async parallel chunking to SQLite (100x faster than sequential)
2. **Process**: Parallel workers with caching (2-5x throughput)
3. **Sync**: Batch MongoDB writes with consolidation (60% fewer ops)

**For implementation details**: See architecture/DOWNLOAD.md, architecture/PROCESS.md, architecture/SYNC.md
```

### ❌ Don't: Create Deep Directory Nesting

AI agents struggle with deep hierarchies - keep it 2-3 levels max.

**Bad**:
```
docs/
└── components/
    └── processing/
        └── business_objects/
            └── detected_vulnerabilities/
                └── parallel_coordination/
                    └── worker_patterns/
                        └── DV_WORKER_PATTERN.md
```

**Good**:
```
docs/
├── architecture/
│   └── DV_PARALLEL_WORKERS.md
```

### ❌ Don't: Use Relative Paths Without Context

Always provide enough context for AI to find files.

**Bad**:
```markdown
See ../processors/base.py for details
```

**Good**:
```markdown
See `processors/base_processor.py` for base class implementation
Or: See `/absolute/path/to/processors/base_processor.py` (absolute path)
```

### ❌ Don't: Duplicate Content Across Hierarchy

**Bad**:
```markdown
# Global CLAUDE.md
## Testing Standards
- 95% line coverage required
- 100% function coverage required

# Project CLAUDE.md
## Testing Standards  ← DUPLICATE!
- 95% line coverage required
- 100% function coverage required

# Tool CLAUDE.md
## Testing Standards  ← DUPLICATE AGAIN!
- 95% line coverage required
- 100% function coverage required
```

**Good**:
```markdown
# Global CLAUDE.md
## Testing Standards
- 95% line coverage required
- 100% function coverage required

# Project CLAUDE.md
## Testing Structure
- Unit tests: `tests/unit/`
- See global CLAUDE.md for coverage requirements

# Tool CLAUDE.md
## Testing
- Tests: `tests/test_tool.py`
- See project CLAUDE.md for structure, global CLAUDE.md for standards
```

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
2. **Architecture Overview** (40-60 lines)
   - Core design (bullet points)
   - Storage architecture (table format)
   - Processing pipeline (4-6 phases, bullet points)
3. **File Structure** (20-40 lines, condensed tree)
4. **Critical Business Logic** (60-80 lines, table format)
5. **Key Architecture Patterns** (60-80 lines)
   - Pattern name
   - Summary (3-5 lines)
   - Benefits (bullet points)
   - See QUICKREF.md for implementation
6. **Common Gotchas** (40-60 lines, 8-10 condensed subsections)
7. **Key Constants** (10-20 lines, bullet list)
8. **When in Doubt** (10-15 lines, numbered list with references)

**Total**: 300-400 lines max

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
