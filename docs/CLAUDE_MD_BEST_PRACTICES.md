# CLAUDE.md Best Practices for Large Monorepos

**Purpose**: Guide for creating optimal CLAUDE.md files in hierarchical codebases to minimize agent context while maximizing information utility.

**Research Date**: 2025-10-17
**Source**: Analysis of M32RIMM codebase optimization (3,396 lines → 1,422 lines, 50% reduction)

---

## Core Principle

**Hierarchical Inheritance**: Child CLAUDE.md files should ONLY contain information unique to their level. Never duplicate parent content.

**Agent Context Loading**: Claude recursively loads CLAUDE.md files from root → current directory. Everything becomes agent context, so verbosity = wasted tokens.

**The 100-200 Line Rule**: Most CLAUDE.md files should be 100-200 lines. Exceptions: Complex production systems (300-400 lines max).

---

## Optimal File Structure by Hierarchy Level

| Level | Lines | Focus | What to Include | What to Exclude |
|-------|-------|-------|-----------------|-----------------|
| **Global** (`~/.claude/CLAUDE.md`) | 100-120 | Decision framework, workflow modes, core principles | Thinking budget, NO PARTIAL WORK, parallel execution, git safety, decision framework | Tool-specific commands, project patterns, testing details |
| **Project** (e.g., `m32rimm/CLAUDE.md`) | 150-180 | Project standards, tool configs, testing conventions | Linting commands, testing structure, project-specific patterns, code style | Core principles (in global), subsystem details |
| **Subsystem** (e.g., `fisio/CLAUDE.md`) | 120-150 | Architecture overview, design patterns, data flow | System architecture, multi-tenancy patterns, major components | Testing patterns (in project), code style (in project) |
| **Framework** (e.g., `fisio/imports/CLAUDE.md`) | 100-120 | Framework patterns, conventions, registry | Three-phase pattern, base classes, directory structure | Subscription handling (in parent), testing (in project) |
| **Simple Tool** | 200-250 | Purpose, architecture, patterns | Tool-specific logic, configuration, gotchas | Code quality (in project), testing (in project), error handling (in global) |
| **Complex Tool** | 300-400 | Architecture, business logic, gotchas | Critical business logic, architecture patterns, common gotchas | Code standards, testing strategy, base patterns |

---

## What NOT to Duplicate

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
   - Subscription handling
   - Database operation patterns
   - Caching strategies

---

## Content Optimization Strategies

### 1. Prose → Tables

**BEFORE (200 lines of prose)**:
```markdown
### External IP Detection
- **Algorithm**: CIDR/range matching using Python `ipaddress` module
- **Function**: `asset_processor.check_if_ip_is_external()`
- **Fields**: `data.externalIpAddresses` (external) vs `data.ipAddresses` (internal)
- **Formats**: Single IP, CIDR ("2.2.2.0/24"), Range ("2.2.2.1-2.2.2.255")
- **WHY**: External IPs have completely separate security posture and monitoring requirements

[... 9 more similar sections ...]
```

**AFTER (40 lines as table)**:
```markdown
## Critical Business Logic

| # | Logic | Key Function/Location | Behavior | WHY |
|---|-------|----------------------|----------|-----|
| 1 | External IP Detection | `asset_processor.check_if_ip_is_external()` | CIDR/range matching, `data.externalIpAddresses` vs `data.ipAddresses` | Separate security posture |
| 2 | Compliance Pass/Info | `should_close_compliance_dv()` | ALWAYS read, skip insert if '0' not in config | Pass = compliant = stay closed |
[... 8 more rows ...]
```

**Savings**: 160 lines (80% reduction), same information, more scannable.

### 2. Extract Deep-Dive Content

**Pattern**: Create `QUICKREF.md` or `DEEP_DIVE.md` for detailed implementations.

**CLAUDE.md (quick reference)**:
- Architecture overview (bullet points)
- Critical business logic (table format)
- Common gotchas (condensed with file:line references)
- Key constants
- "See QUICKREF.md for detailed patterns and code examples"

**QUICKREF.md (deep-dive reference)**:
- Full code examples with before/after
- Detailed pattern implementations
- Comprehensive testing strategies
- Refactoring guides with examples

**When to use**: When CLAUDE.md exceeds 400 lines, extract examples/details to QUICKREF.md.

### 3. Decision Matrices Over Explanations

**BEFORE (60 lines)**:
```markdown
## Error Handling Strategy

When you encounter a MongoDB connection failure, you should let Python fail naturally because this indicates a configuration problem that needs to be fixed...

When you encounter network timeouts, you should use retry_run because these are transient failures...

[... verbose explanations ...]
```

**AFTER (20 lines)**:
```markdown
## Error Handling Strategy

| Strategy | When | Examples |
|----------|------|----------|
| **CRASH** (let Python fail) | Config/setup errors | MongoDB/Redis connection failures, invalid configuration, missing required files |
| **RETRY** (use retry_run) | Transient failures | Network timeouts, rate limits (429), temporary API failures (500/502/503) |
| **SKIP** (log warning, continue) | Data issues | No asset match for DV, invalid/corrupt record |
| **WARN** (log info, continue) | Non-critical issues | Missing optional fields, IP-only asset match |
```

**Savings**: 40 lines (67% reduction), easier to scan under pressure.

### 4. Condense File Structure Trees

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
│   ├── scans_registry_handler.py # Scan registry management (metadata + status tracking)
│   │
│   ├── asset_cascade_matcher.py  # 10-level cascade matching orchestration
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

**Savings**: 40 lines (67% reduction), still shows structure.

### 5. Bullet Points Over Paragraphs

**BEFORE**:
```markdown
The import framework provides a standardized approach to data ingestion that ensures consistency across all import tools. By following the three-phase processing pattern of fetch, normalize, and store, all imports maintain a consistent architecture that makes the codebase easier to understand and maintain. This consistency also enables shared utilities and reduces code duplication across different import implementations.
```

**AFTER**:
```markdown
**Framework Benefits**: Standardized error handling, logging, configuration management across all imports. Shared base classes reduce duplication, consistent testing patterns, centralized utilities.
```

**Savings**: 4 lines → 1 line, same information.

---

## Hierarchical Inheritance Examples

### Bad (Duplication)

**Global CLAUDE.md**:
```markdown
## Testing Standards
- 95% line coverage required
- 100% function coverage required
- 1:1 file mapping (one test file per source file)
```

**Project CLAUDE.md**:
```markdown
## Testing Standards  ← DUPLICATE!
- 95% line coverage required
- 100% function coverage required
- 1:1 file mapping (one test file per source file)
```

**Subsystem CLAUDE.md**:
```markdown
## Testing Standards  ← DUPLICATE!
- 95% line coverage required
- 100% function coverage required
- 1:1 file mapping (one test file per source file)
```

**Problem**: 3x duplication, agent loads all 3 copies into context.

### Good (Hierarchical)

**Global CLAUDE.md**:
```markdown
## Testing Standards
**Location:** `~/.claude/docs/TESTING_STANDARDS.md`

**Key rules:**
- 1:1 file mapping, 95%+ line coverage, 100% function coverage
- Every function: happy path + error cases + edge cases
- Integration tests: 2-4 files per module
```

**Project CLAUDE.md**:
```markdown
## Testing Structure
- Unit tests: `tests/test_[module]/unit_tests/`
- Integration tests: `tests/test_[module]/integration_tests/`
- Run: `pytest tests/test_[module]/ --cov=fisio.[module] -v`
- See global CLAUDE.md for coverage requirements
```

**Subsystem CLAUDE.md**:
```markdown
[No testing section - covered in parent files]
```

**Result**: Information defined once, referenced when needed, 67% reduction in duplication.

---

## When to Create QUICKREF.md

**Triggers** (any one means extract to QUICKREF):
1. CLAUDE.md exceeds 400 lines
2. More than 5 code examples with before/after patterns
3. Detailed implementation walkthroughs (>50 lines per pattern)
4. Comprehensive testing strategies with mock examples
5. Refactoring guides with line-by-line explanations

**What goes in QUICKREF.md**:
- Full code examples (before/after patterns)
- Detailed pattern implementations with line-by-line explanation
- Comprehensive testing strategies with mock/fixture examples
- Performance optimization guides
- Debugging strategies and common pitfalls with solutions
- Architecture deep dives with data flow diagrams (ASCII)

**What stays in CLAUDE.md**:
- Critical business logic (table format)
- Architecture overview (bullet points)
- Common gotchas (condensed with file:line references)
- Key constants and configuration
- "See QUICKREF.md for detailed implementations"

---

## Template: Simple Tool CLAUDE.md (25 lines)

```markdown
# [Tool Name] Import

**Purpose**: [One sentence describing what this import does]

**Key Patterns**:
- Extends import framework base classes (see `fisio/imports/CLAUDE.md`)
- [Tool-specific pattern 1]
- [Tool-specific pattern 2]

**Configuration**:
- Config location: `/etc/fis/fis-config.json` → `[tool_name]` section
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
- Import framework: `fisio/imports/CLAUDE.md`
- Testing standards: Project CLAUDE.md
```

---

## Template: Complex Tool CLAUDE.md (300-400 lines)

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

## Validation Checklist

Before committing CLAUDE.md changes:

**Duplication Check**:
- [ ] No duplicate core principles (defined in global only)
- [ ] No duplicate testing patterns (defined in project only)
- [ ] No duplicate code style rules (defined in project only)
- [ ] No duplicate subsystem patterns (defined in parent subsystem only)

**Content Optimization**:
- [ ] Business logic in table format (not prose)
- [ ] Decision matrices for strategies (not paragraphs)
- [ ] File structure condensed (not full tree)
- [ ] Bullet points over paragraphs where possible

**Line Count**:
- [ ] Global: 100-120 lines
- [ ] Project: 150-180 lines
- [ ] Subsystem: 120-150 lines
- [ ] Framework: 100-120 lines
- [ ] Simple Tool: 200-250 lines
- [ ] Complex Tool: 300-400 lines max

**Deep-Dive Extraction**:
- [ ] If CLAUDE.md > 400 lines, extract to QUICKREF.md
- [ ] Code examples with before/after → QUICKREF.md
- [ ] Detailed implementations → QUICKREF.md
- [ ] Keep quick reference + "See QUICKREF for details"

**Hierarchy Integrity**:
- [ ] Child files reference parent files (not duplicate)
- [ ] Each level focuses on unique information
- [ ] Clear separation of concerns across levels

---

## Real-World Example: M32RIMM Optimization

**Before Optimization** (October 2025):
- Total CLAUDE.md lines: 3,396
- tenable_sc_refactor/CLAUDE.md: 871 lines
- Duplication: ~60% across hierarchy
- Problem: Information overload, scroll fatigue, wasted agent context

**After Optimization**:
- Total CLAUDE.md lines: 1,422 (50% reduction)
- tenable_sc_refactor/CLAUDE.md: 242 lines (72% reduction)
- QUICKREF.md created: 654 lines (extracted deep-dive content)
- Duplication eliminated: Hierarchical inheritance working

**Key Changes**:
1. **Prose → Tables**: Business logic (200 lines → 40 lines)
2. **Deleted Duplication**: 180+ lines of standards removed
3. **Extracted Examples**: Code patterns moved to QUICKREF.md
4. **Condensed Sections**: Architecture patterns (150 lines → 60 lines)

**Result**: Agent context 50% lighter, nothing lost, better organized.

---

## Anti-Patterns to Avoid

❌ **Don't**: Copy entire parent CLAUDE.md sections into child files
✅ **Do**: Reference parent files ("See project CLAUDE.md for testing standards")

❌ **Don't**: Write 200-line prose explanations of business logic
✅ **Do**: Use table format with 10 rows (Logic | Function | Behavior | WHY)

❌ **Don't**: Include full code examples with before/after in CLAUDE.md
✅ **Do**: Extract to QUICKREF.md, add "See QUICKREF for implementation"

❌ **Don't**: Create 800+ line CLAUDE.md files
✅ **Do**: Cap at 400 lines, extract deep-dive to QUICKREF.md

❌ **Don't**: Repeat testing/code style rules at every level
✅ **Do**: Define once (project level), reference elsewhere

❌ **Don't**: Write verbose paragraphs explaining obvious code
✅ **Do**: Use bullet points, let code speak (type hints replace docs)

❌ **Don't**: Include every file in directory tree
✅ **Do**: Show structure, condense with "[6 more processors]"

---

## Integration with Workflows

### For /conduct and /solo Commands

**After implementation phase**, run CLAUDE.md optimization:

```markdown
## Phase N: Documentation Update & CLAUDE.md Optimization

1. **Update CLAUDE.md**:
   - Add new patterns/gotchas discovered during implementation
   - Update critical business logic table if rules changed
   - Reference any new QUICKREF sections

2. **Check for duplication**:
   - Verify no duplicate content from parent CLAUDE.md files
   - Confirm testing/code style not redefined (use parent references)
   - Ensure hierarchical inheritance maintained

3. **Optimize if needed**:
   - If CLAUDE.md > 400 lines: Extract deep-dive to QUICKREF.md
   - Convert any new prose explanations to table/bullet format
   - Condense any verbose sections using decision matrices

4. **Validation**:
   - Line count within target for hierarchy level
   - No duplication across parent/child files
   - Critical information preserved in quick-reference format
```

**Benefits**:
- Documentation stays current with implementation
- CLAUDE.md files don't bloat over time
- Hierarchical structure maintained automatically
- Agent context stays optimized

---

## Summary

**The Golden Rules**:

1. **Hierarchical Inheritance** - Never duplicate parent content, always reference
2. **100-200 Line Target** - Most files should be this range (complex tools 300-400 max)
3. **Tables Over Prose** - Business logic, gotchas, decisions all in table format
4. **Extract Deep-Dive** - Code examples and detailed implementations → QUICKREF.md
5. **Define Once** - Testing, code style, core principles defined once at appropriate level

**The Test**: Can you scan the CLAUDE.md file in 30 seconds and find critical information? If not, it's too verbose.

**The Goal**: Minimize agent context, maximize information utility, maintain hierarchical clarity.

**Remember**: Less is more. Every line in CLAUDE.md consumes agent context. Make every line count.
