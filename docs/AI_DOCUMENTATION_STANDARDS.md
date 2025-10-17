# AI-Optimized Documentation Standards

**Purpose**: Guide for creating documentation optimized for AI code agents (Claude, GPT, etc.) in large monorepos and complex systems.

**Research Date**: 2025-10-17
**Sources**: Anthropic Claude Code best practices, llms.txt standard, community patterns, M32RIMM refactor_notes analysis

**Key Insight**: Documentation for AI agents is FUNDAMENTALLY DIFFERENT from human documentation. AI agents need concise, structured, scannable information with clear context boundaries - not comprehensive tutorials.

---

## Core Principles for AI-Readable Docs

### 1. Concise Over Comprehensive

**Human docs**: Explain every detail, provide context, walk through examples
**AI docs**: Provide clear structure, reference locations, let AI read source code

**Why**: AI agents can read code directly. Documentation should be a MAP, not a TUTORIAL.

**Example**:
```markdown
❌ BAD (Human-style):
The DV processor handles detected vulnerabilities by first checking if the
vulnerability already exists in the database. It does this by computing a hash
of the asset ID, sorted CVE list, plugin ID, port, protocol, IP address, and
external IP flag. This hash is used as a unique identifier. The hash computation
uses MD5 and follows this pattern: MD5(asset_id + sorted_cves + plugin_id +
port + protocol + ip + is_external). Once the hash is computed...
[200 more lines of detailed explanation]

✅ GOOD (AI-style):
**DV Deduplication**
- Hash: MD5(asset_id + sorted_cves + plugin_id + port + protocol + ip + is_external)
- Location: `processors/detected_vuln_processor.py:_compute_dv_hash()`
- Purpose: Unique ID for DV deduplication
- Gotcha: Sort CVEs before hashing (order matters)
```

### 2. Structure Over Prose

**Tables, bullets, and code snippets >>> Paragraphs**

AI agents parse structured content faster and more accurately.

**Before** (Prose-heavy):
```markdown
The asset matching cascade operates in ten distinct levels, with each level
representing a different quality tier. The highest quality matches are External
IP matches, followed by hostUUID and UUID matches. Medium quality matches include
compound field combinations like IP+MAC, IP+DNS, MAC+DNS, and IP+MAC+DNS...
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

**Always include file:line_number for implementation details**

AI agents can read code directly - they just need to know WHERE to look.

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

**Create clear "entry points" for different levels of detail**

AI agents should be able to quickly find:
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

**Use consistent terminology and include searchable keywords**

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

## Optimization Strategies for Existing Docs

### Strategy 1: Extract-Consolidate-Reference (ECR)

**Problem**: Duplicate information across multiple files
**Solution**: Extract to single source, consolidate, add references

**Example** (Your refactor_notes):
```
BEFORE:
- BUSINESS_RULES.md (828 lines) - Full rules
- DV_ARCHITECTURE.md (1,575 lines) - DV rules embedded
- KV_SOLUTION_ARCHITECTURE.md (942 lines) - KV rules embedded
- APPLICATION_ARCHITECTURE.md (540 lines) - App rules embedded

AFTER:
- BUSINESS_RULES.md (800 lines) - Authoritative source with file:line refs
- DV_ARCHITECTURE.md (400 lines) - "For DV business rules see BUSINESS_RULES.md #5-12"
- KV_SOLUTION_ARCHITECTURE.md (300 lines) - "For KV business rules see BUSINESS_RULES.md #13-18"
- APPLICATION_ARCHITECTURE.md (250 lines) - "For app business rules see BUSINESS_RULES.md #24-27"

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
```markdown
BEFORE (200 lines of prose):
External IP detection is handled by the asset processor. The algorithm uses
the Python ipaddress module to match against CIDR notation and IP ranges.
The configuration can specify IPs as single addresses like "10.0.0.1", CIDR
blocks like "10.0.0.0/24", or ranges like "10.0.0.1-10.0.0.255". When an IP
matches the external IP configuration, it gets stored in the
data.externalIpAddresses field instead of the data.ipAddresses field. This
is important because external IPs have a completely separate security posture...
[180 more lines]

AFTER (30 lines as table):
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

### Strategy 4: Add llms.txt Index (for Monorepos)

**Problem**: AI agents don't know which docs are most relevant
**Solution**: Create llms.txt index with doc summaries

**Template** (root of docs folder):
```
# llms.txt - AI Agent Documentation Index

## Quick Start
- /docs/OVERVIEW.md - System architecture overview (150 lines)
- /docs/QUICK_REF.md - Common tasks and gotchas (300 lines)

## Business Logic
- /docs/BUSINESS_RULES.md - Authoritative business rules catalog (800 lines)
- /docs/ERROR_HANDLING.md - Error handling strategies (200 lines)

## Architecture
- /docs/architecture/DV_PROCESSING.md - DV processor design (400 lines)
- /docs/architecture/KV_SOLUTION.md - KV/Solution processing (300 lines)
- /docs/architecture/ASSET_MATCHING.md - Asset matching cascade (350 lines)

## Implementation Reference
- /docs/implementation/API_REFERENCE.md - Function catalog (400 lines)
- /docs/implementation/DATA_STRUCTURES.md - Schema reference (600 lines)

## Troubleshooting
- /docs/guides/TROUBLESHOOTING.md - Common issues and fixes (250 lines)
- /docs/guides/HOW_TO.md - Step-by-step guides (200 lines)

## For Specific Tasks

**Adding new business object processor**:
1. Read /docs/architecture/PATTERNS.md
2. Reference /docs/BUSINESS_RULES.md for rules to preserve
3. See /docs/implementation/API_REFERENCE.md for base class

**Debugging failed import**:
1. Check /docs/guides/TROUBLESHOOTING.md
2. Reference /docs/ERROR_HANDLING.md for recovery strategies
3. See /docs/architecture/[relevant_component].md for logic

**Understanding data flow**:
1. Start with /docs/OVERVIEW.md (big picture)
2. Read /docs/architecture/ files for specific components
3. Reference /docs/implementation/DATA_STRUCTURES.md for schemas
```

---

## Anti-Patterns for AI Docs

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
3. Register in `tenable_sc_import.py:_initialize_processors()`
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
Or: See `/home/user/project/processors/base_processor.py` (absolute path)
```

---

## Recommended Structure for Your refactor_notes/

Based on analysis of 37 files (17,000+ lines) in your current refactor_notes:

### Current Issues
1. **Duplication**: CODE_BEAUTY_STANDARDS in 2 places, business rules scattered across 5+ files
2. **Monoliths**: DV_ARCHITECTURE (1,575 lines), CODE_BEAUTY (1,416 lines)
3. **Missing**: llms.txt index, OVERVIEW.md, TROUBLESHOOTING.md
4. **Archive**: 4,700 lines of research artifacts without clear status

### Proposed AI-Optimized Structure

```
refactor_notes/
├── llms.txt                  # NEW - AI agent index (100 lines)
├── OVERVIEW.md               # NEW - Complete mental model (150 lines)
├── QUICK_REF.md              # KEEP - Deep-dive examples (654 lines)
│
├── business_logic/           # KEEP - Authoritative source
│   ├── BUSINESS_RULES.md     # CONSOLIDATE - Single source (800 lines)
│   └── ERROR_HANDLING.md     # RENAME from ERROR_SCENARIOS (400 lines)
│
├── architecture/             # REORGANIZE - Component patterns
│   ├── ASSET_PROCESSING.md   # CONSOLIDATE from 5 files (400 lines)
│   ├── KV_SOLUTION.md        # KEEP (400 lines, extract rules to BUSINESS_RULES)
│   ├── DV_PROCESSING.md      # SPLIT from 1,575 lines
│   │   ├── DV_OVERVIEW.md    (200 lines)
│   │   ├── DV_PIPELINE.md    (300 lines)
│   │   ├── DV_LOGIC.md       (250 lines, refs to BUSINESS_RULES)
│   │   └── DV_PARALLEL.md    (250 lines)
│   ├── APPLICATION.md        # KEEP (300 lines, extract rules)
│   ├── DAA.md                # KEEP (250 lines)
│   └── PATTERNS.md           # CONSOLIDATE cross-component patterns (300 lines)
│
├── implementation/           # NEW - Reference material
│   ├── API_REFERENCE.md      # NEW - Function catalog (400 lines)
│   ├── DATA_STRUCTURES.md    # MOVE from specifications/ (600 lines)
│   ├── CONFIGURATION.md      # MOVE + MERGE (400 lines)
│   └── CODE_QUALITY.md       # MOVE from standards/ (400 lines, split from 1,416)
│
├── guides/                   # NEW - Task-oriented
│   ├── TROUBLESHOOTING.md    # NEW (250 lines)
│   ├── HOW_TO.md             # NEW (200 lines)
│   └── COMMON_TASKS.md       # NEW (150 lines)
│
└── archive/                  # KEEP - Add deprecation markers
    ├── ARCHIVE_README.md     # NEW - Explains purpose (50 lines)
    └── 2025-10-17-research-artifacts/  # KEEP with headers
```

### Metrics Comparison

| Metric | Current | Proposed | Change |
|--------|---------|----------|--------|
| Total files | 37 | 25-30 | -20-32% |
| Total lines | ~17,000 | ~7,500-8,500 | -50-55% |
| Largest file | 1,575 | 600 | -62% |
| Duplicate lines | ~3,000 | <500 | -83% |
| AI-scannable | 60% | 95% | +35% |
| llms.txt index | No | Yes | NEW |

---

## Implementation Priority

### Phase 1: Quick Wins (2-3 hours)
1. Create `llms.txt` index (30 min)
2. Create `OVERVIEW.md` (1 hour)
3. Delete duplicate `CODE_BEAUTY_STANDARDS.md` from architecture/ (5 min)
4. Add deprecation headers to archive/ files (30 min)
5. Create `ARCHIVE_README.md` (30 min)

### Phase 2: Consolidation (4-6 hours)
1. Consolidate asset docs (5 files → 1) (1.5 hours)
2. Extract business rules from architecture docs to BUSINESS_RULES.md (2 hours)
3. Split DV_ARCHITECTURE.md (1,575 → 4 files of ~250 each) (2 hours)
4. Reorganize CODE_BEAUTY_STANDARDS (1,416 → 400 in implementation/) (1 hour)

### Phase 3: Fill Gaps (3-4 hours)
1. Create TROUBLESHOOTING.md (1.5 hours)
2. Create HOW_TO.md (1 hour)
3. Create API_REFERENCE.md (1.5 hours)

**Total effort**: 9-13 hours
**Result**: AI-optimized docs, 50% reduction in lines, 95% scannable, single sources of truth

---

## Validation Checklist

After optimization, verify:

**Structure**:
- [ ] llms.txt index exists and is accurate
- [ ] No file >600 lines (except BUSINESS_RULES if needed)
- [ ] Directory depth ≤3 levels
- [ ] No duplicate files

**Content**:
- [ ] Every business rule has file:line reference
- [ ] Tables used for structured data (not prose)
- [ ] Code examples are minimal (not tutorials)
- [ ] Clear separation: Overview/Architecture/Implementation/Guides

**AI-Readability**:
- [ ] Can AI find relevant doc in <30 seconds via llms.txt?
- [ ] Can AI understand component in <5 min reading OVERVIEW?
- [ ] Can AI find specific function via API_REFERENCE?
- [ ] Can AI debug issue via TROUBLESHOOTING?

**Maintenance**:
- [ ] Single source of truth for business rules
- [ ] No scattered duplicates
- [ ] Archive clearly marked as historical
- [ ] Cross-references use file paths, not relative links

---

## Remember

**For AI agents**:
- **Concise > Comprehensive** (they can read code)
- **Structure > Prose** (tables/bullets/code over paragraphs)
- **Location > Explanation** (file:line refs over detailed walkthroughs)
- **Scannable > Complete** (quick reference over exhaustive guides)

**The test**: Can AI agent find and understand critical information in <5 minutes? If not, docs need optimization.

**The goal**: Documentation as a MAP to the codebase, not a REPLACEMENT for reading code.
