---
name: update_docs
description: Update documentation AND skills to match current implementation using parallel document-writer agents with cascading skill hierarchy updates
---

# /update_docs - Parallel Documentation & Skills Update

## 🎯 Purpose

Update all documentation (CLAUDE.md + docs/) AND skills hierarchy to match current implementation by spawning parallel document-writer agents for each component.

**When to use:**
- After implementation changes (code evolved, docs stale)
- After /conduct or /solo completion
- Periodic maintenance (keep docs accurate)
- Post-refactor (architecture/patterns changed)

**Prerequisites:** None (works with or without .spec/ files)

---

## Workflow

### Step 0: Determine Working Directory

**Infer from current session context:**
- Check if user mentioned specific component/directory
- Look at recent file operations (what was just modified)
- Check current working directory

**If unclear after context check, ask:**
```
Which directory should I update documentation for?
- Current directory (.)
- Specific path (provide path relative to repo root)
```

**Once determined:**
- `$WORK_DIR` = that directory
- All documentation updates scoped to this directory

---

### Step 1: Discovery Phase

**Find all components in working directory:**

```bash
# Find Python modules (directories with __init__.py)
find $WORK_DIR -name "__init__.py" -type f | xargs dirname | sort -u

# Find standalone Python files (not in modules)
find $WORK_DIR -name "*.py" -type f -not -path "*/tests/*" -not -name "__init__.py"

# Find existing documentation
find $WORK_DIR -name "*.md" -type f
find $WORK_DIR -name "CLAUDE.md" -type f
ls $WORK_DIR/docs/ 2>/dev/null
```

**Catalog components:**
- **Modules**: Directories with `__init__.py` (e.g., `processors/`, `cache/`, `api_handler/`)
- **Standalone files**: Top-level `.py` files (e.g., `tenable_sc_import.py`, `constants.py`)
- **Existing docs**: All `.md` files for validation

**Check for context sources:**
```bash
# Check for .spec/ files (implementation context)
ls $WORK_DIR/.spec/SPEC*.md 2>/dev/null
ls $WORK_DIR/.spec/BUILD*.md 2>/dev/null

# Check git diff (recent changes)
git diff --name-only HEAD~5..HEAD -- $WORK_DIR 2>/dev/null
```

**Check if documentation library exists:**
```bash
# Critical files for documentation library
ls $WORK_DIR/CLAUDE.md 2>/dev/null
ls $WORK_DIR/docs/llms.txt 2>/dev/null
```

**If documentation library missing (CRITICAL - CREATE FIRST):**

```python
# BEFORE proceeding with validation/updates, bootstrap documentation

Task(documentation-writer, """
Create documentation library from scratch for existing implementation.

Working directory: $WORK_DIR
Workflow: update_docs (bootstrap mode)

Code exists but NO documentation found. Create complete library:

1. Invoke ai-documentation skill FIRST to load templates
2. Analyze codebase structure (find all modules, files, functions)
3. Create CLAUDE.md using appropriate template:
   - Determine hierarchy level (check parent CLAUDE.md)
   - Simple tool (~200 lines) or Complex tool (300-400 lines)
   - Include: Purpose, Architecture, Key Components, Gotchas
   - Add file:line references for critical functions
4. Create docs/ directory structure:
   - docs/llms.txt (navigation index)
   - docs/OVERVIEW.md (5-min mental model)
   - docs/API_REFERENCE.md (all public functions)
   - docs/HOW_TO.md (common workflows)
   - docs/business_logic/ (if complex business rules exist)
5. Populate each doc with content from code analysis

This is CREATION not UPDATE - build from implementation.

Return structured summary with all files created.
""")

# Wait for library creation before proceeding
# Then continue with normal validation/update workflow
```

**WHY bootstrap first:**
- Validation (Step 2) requires docs to exist
- Update agents (Step 3) expect existing structure
- Better to create complete library once than patch incrementally

**Component grouping strategy:**
- **Simple project** (<5 components): 1 agent per component
- **Medium project** (5-15 components): 1 agent per major module
- **Large project** (>15 components): Group related components (e.g., all processors together)

---

### Step 2: Parallel Validation

**Invoke documentation-validator to identify issues:**

```python
validation_result = Task(documentation-validator, """
Validate ALL documentation in working directory for accuracy.

Working directory: $WORK_DIR
Workflow: update_docs

Validation scope:
- CLAUDE.md (all levels in $WORK_DIR)
- README.md (if exists)
- docs/ directory (all .md files)
- .spec/ files (if exists)

Steps:
1. Invoke ai-documentation skill to load standards
2. Find all .md files in $WORK_DIR
3. Validate systematically:
   - File:line references accurate
   - Function signatures match code
   - Architecture claims verified
   - Constants/values correct
   - CLAUDE.md line count within target
   - No duplication from parent CLAUDE.md

Return structured JSON with all issues categorized by severity.

See ~/.claude/docs/DOCUMENTATION_VALIDATOR_AGENT.md for full methodology.
""")
```

**Parse validation results:**
- Extract CRITICAL issues (incorrect refs, contradictions)
- Extract IMPORTANT issues (missing docs, outdated info)
- Extract MINOR issues (line count, optimization)
- Group issues by file/component

---

### Step 3: Spawn Parallel document-writer Agents

**ONE agent per component** (maximize parallelism):

**For each component, determine scope:**
- Python files in component
- Existing documentation for component
- Issues from validation affecting this component
- Context from .spec/ files (if available)

**Launch ALL agents in SINGLE message (critical for parallelism):**

```python
# Example: 3 components = 3 parallel agents

Task(documentation-writer, """
Update documentation for processors/ component.

Working directory: $WORK_DIR/processors
Component files:
- base_processor.py
- asset_processor.py
- known_vuln_processor.py
- detected_vuln_processor.py

Validation issues to fix:
[paste JSON issues for this component]

Context sources:
- .spec/SPEC.md (if exists)
- Git diff: [recent changes to this component]

Tasks:
1. Invoke ai-documentation skill FIRST
2. Update docs/API_REFERENCE.md for this component's functions
3. Add/update gotchas in CLAUDE.md for this component
4. Fix all CRITICAL and IMPORTANT validation issues
5. Update docs/llms.txt if new docs created

Return structured summary (see documentation-writer spec).
""")

Task(documentation-writer, """
Update documentation for cache/ component.

Working directory: $WORK_DIR/cache
Component files:
- tenable_sc_cache.py
- persistent_daa_staging_handler.py

Validation issues to fix:
[paste JSON issues for this component]

Context sources:
- .spec/SPEC.md (if exists)
- Git diff: [recent changes to this component]

Tasks:
1. Invoke ai-documentation skill FIRST
2. Update docs/API_REFERENCE.md for this component's functions
3. Add/update gotchas in CLAUDE.md for this component
4. Fix all CRITICAL and IMPORTANT validation issues
5. Update docs/llms.txt if new docs created

Return structured summary.
""")

Task(documentation-writer, """
Update documentation for api_handler/ component.

Working directory: $WORK_DIR/api_handler
Component files:
- download_manager.py
- handler.py
- tenable_client.py

Validation issues to fix:
[paste JSON issues for this component]

Context sources:
- .spec/SPEC.md (if exists)
- Git diff: [recent changes to this component]

Tasks:
1. Invoke ai-documentation skill FIRST
2. Update docs/API_REFERENCE.md for this component's functions
3. Add/update gotchas in CLAUDE.md for this component
4. Fix all CRITICAL and IMPORTANT validation issues
5. Update docs/llms.txt if new docs created

Return structured summary.
""")
```

**Key pattern**: SINGLE message with MULTIPLE Task() calls for true parallelism.

---

### Step 4: CLAUDE.md Optimization (After Agents Complete)

**After all document-writer agents complete:**

```python
# Re-validate CLAUDE.md specifically
Task(documentation-validator, """
Validate CLAUDE.md optimization (focus on line count and structure).

Working directory: $WORK_DIR
CLAUDE.md files: [list all CLAUDE.md files in $WORK_DIR hierarchy]

Invoke ai-documentation skill to load best practices.

Check:
1. Line count within target for hierarchy level
2. No duplication from parent CLAUDE.md
3. Business logic in table format (not prose)
4. File structure condensed
5. Deep-dive content extracted to QUICKREF.md if >400 lines

Return structured JSON with optimization recommendations.

See ~/.claude/docs/DOCUMENTATION_VALIDATOR_AGENT.md for methodology.
""")
```

**If CLAUDE.md issues found:**

```python
Task(documentation-writer, """
Optimize CLAUDE.md following AI documentation best practices.

Files with issues: [list CLAUDE.md files needing optimization]
Working directory: $WORK_DIR

Invoke ai-documentation skill to load best practices.

Issues to fix:
[paste JSON from validator]

Optimization strategy:
1. Remove duplicate content (reference parent CLAUDE.md files)
2. Convert prose to tables/bullets (content optimization)
3. Extract deep-dive content to QUICKREF.md if >400 lines
4. Condense file structure trees
5. Ensure line count within target for hierarchy level

Maintain all critical information - reorganize for AI readability.
""")
```

---

### Step 5: Final Validation

**Re-run documentation-validator on ALL updated docs:**

```python
final_validation = Task(documentation-validator, """
Final validation after updates.

Working directory: $WORK_DIR
Scope: ALL documentation

Check:
1. All CRITICAL issues resolved
2. All IMPORTANT issues resolved
3. File:line references accurate
4. CLAUDE.md line counts within targets
5. No new issues introduced

Return structured JSON with final status.
""")
```

**Completion criteria:**
- ✅ Zero CRITICAL issues
- ✅ Zero IMPORTANT issues
- ✅ All CLAUDE.md files within line count targets
- ✅ All components documented

**If issues remain after 2 passes**: Report blockers and exit.

---

### Step 6: Cascading Skill Hierarchy Updates

**After documentation updates complete, analyze changes for skill updates.**

#### Skill Hierarchy Levels

```
~/.claude/skills/           # Global skills (all projects)
  ├── python-style/
  ├── testing-standards/
  ├── code-refactoring/
  ├── ai-documentation/
  ├── mcp-integration/
  └── orchestration-workflow/

$REPO_ROOT/.claude/skills/  # Repo-level skills (this repo only)
  └── (custom repo patterns)

$WORK_DIR/.claude/skills/   # Project-level skills (this project/tool)
  └── (project-specific patterns)
```

#### 6.1: Detect Changes That Affect Skills

**Analyze documentation updates from Steps 3-5:**

```python
# Extract patterns from updated documentation
patterns_analysis = analyze_documentation_changes(
    updated_docs=all_updated_docs,
    work_dir=WORK_DIR,
    git_diff=recent_changes
)

# Questions to answer:
# 1. Did coding standards change? (python-style skill)
# 2. Did testing patterns change? (testing-standards skill)
# 3. Did refactoring thresholds change? (code-refactoring skill)
# 4. Did new project-specific patterns emerge?
# 5. Are there gotchas worth promoting to skills?
```

**Categories of changes:**

1. **Project-level changes** (local to $WORK_DIR)
   - New patterns specific to this tool/project
   - Gotchas only relevant to this codebase
   - Example: "Tenable SC compliance severity mapping"

2. **Repo-level changes** (affects multiple projects in repo)
   - Pattern used across multiple imports/tools
   - Common utility pattern
   - Example: "Redis deduplication cache pattern"

3. **Global-level changes** (~/.claude/skills/)
   - Universal pattern applicable to ALL projects
   - New best practice discovered
   - Example: "SQLite WAL checkpoint timing for multiprocessing"

#### 6.2: Determine Skill Hierarchy to Update

**Cascading logic (bottom-up analysis):**

```python
# Start at project level, cascade up to global

# Level 1: Project-level skills ($WORK_DIR/.claude/skills/)
project_skills_to_update = identify_project_skill_updates(
    changes=patterns_analysis,
    existing_project_skills=scan_project_skills(WORK_DIR)
)

# Level 2: Repo-level skills ($REPO_ROOT/.claude/skills/)
repo_skills_to_update = identify_repo_skill_updates(
    changes=patterns_analysis,
    project_changes=project_skills_to_update,
    existing_repo_skills=scan_repo_skills(REPO_ROOT)
)

# Level 3: Global skills (~/.claude/skills/)
global_skills_to_update = identify_global_skill_updates(
    changes=patterns_analysis,
    universal_patterns=extract_universal_patterns(changes)
)
```

**Validation rules:**

- **Project → Repo**: Only cascade if pattern used in 2+ projects in repo
- **Repo → Global**: Only cascade if pattern applicable across ALL repos
- **Specificity**: More specific beats more general (project overrides global)

#### 6.3: Update Project-Level Skills (Automatic)

**Create or update project skills automatically (no user approval needed):**

```python
# Spawn parallel document-writer agents for project skills

Task(documentation-writer, """
Update project-level skill: tenable-sc-patterns

Skill location: $WORK_DIR/.claude/skills/tenable-sc-patterns/
Skill type: Project-specific patterns

Changes detected:
1. New compliance severity mapping pattern (Pass/Info handling)
2. Updated SQLite work distribution pattern (hash-based grouping)
3. New cascade matching pattern (10-level asset matching)

Tasks:
1. Invoke ai-documentation skill FIRST
2. Create/update SKILL.md with new patterns
3. Add code examples from implementation
4. Document when to use each pattern
5. Include gotchas from CLAUDE.md

Validate against code in $WORK_DIR to ensure accuracy.

Return structured summary.
""")

Task(documentation-writer, """
Update project-level skill: tenable-cache-patterns

Skill location: $WORK_DIR/.claude/skills/tenable-cache-patterns/
Skill type: Project-specific caching patterns

Changes detected:
1. New persistent DAA staging pattern (cross-scan accumulation)
2. Updated batch fetch optimization pattern (eliminate N+1 queries)
3. New WAL checkpoint timing pattern (worker visibility)

Tasks:
1. Invoke ai-documentation skill FIRST
2. Create/update SKILL.md with new patterns
3. Add code examples from cache/ implementation
4. Document performance characteristics
5. Include timing gotchas

Validate against code in $WORK_DIR/cache to ensure accuracy.

Return structured summary.
""")
```

**Project skills are AUTO-UPDATED** because:
- Scoped to this project only
- Low risk (doesn't affect other projects)
- Directly derived from code changes

#### 6.4: Propose Repo-Level Skill Updates (Ask User)

**If patterns apply across multiple projects in repo:**

```markdown
## 🔄 Repo-Level Skill Updates Recommended

**Detected patterns that apply across multiple projects in this repo:**

### 1. Redis Deduplication Cache Pattern
**Used in:** tenable_sc_refactor, nvd_api, vulndb
**Pattern:** SQLite-based caching with Redis fallback
**Propose:** Create `$REPO_ROOT/.claude/skills/redis-cache-patterns/`

**Rationale:**
- Used in 3+ import tools
- Consistent performance pattern (0.004ms lookups)
- Common batch fetch optimization

**Would update:**
- Create new repo-level skill: `$REPO_ROOT/.claude/skills/redis-cache-patterns/`
- Document pattern, performance characteristics, gotchas

**Approve? (y/n)**

### 2. MongoDB Batch Operations Pattern
**Used in:** tenable_sc_refactor, disa, nvd_api
**Pattern:** 5000-document batches with retry logic
**Propose:** Update `python-style` skill with batch operation standards

**Rationale:**
- Consistent across all imports (DEFAULT_BATCH_SIZE = 5000)
- Standard retry_run pattern
- Common error handling

**Would update:**
- Add to existing repo-level skill (or create if needed)
- Document batch size rationale, retry logic

**Approve? (y/n)**
```

**User approval required because:**
- Affects multiple projects (higher impact)
- May conflict with existing patterns in other projects
- Establishes repo-wide conventions

#### 6.5: Propose Global Skill Updates (Ask User)

**If patterns are universally applicable:**

```markdown
## 🌍 Global Skill Updates Recommended

**Detected patterns that apply to ALL Python projects:**

### 1. SQLite WAL Checkpoint Timing for Multiprocessing
**Universal pattern:** Force WAL checkpoint before spawning workers
**Propose:** Add to `~/.claude/skills/python-style/` under "Concurrency Patterns"

**Rationale:**
- Applies to ANY Python project using SQLite + multiprocessing
- Prevents worker isolation bugs (workers can't see main thread writes)
- Not project-specific (universal SQLite behavior)

**Code example:**
```python
# CRITICAL: Checkpoint WAL before workers spawn
conn.execute("PRAGMA wal_checkpoint(FULL)")
# Now workers can see main thread writes
```

**Would update:**
- ~/.claude/skills/python-style/SKILL.md
- Add new section: "SQLite + Multiprocessing Patterns"
- Document timing requirements, gotchas

**Approve? (y/n)**

### 2. Complexity Threshold for Parallel Work Distribution
**Universal pattern:** Use SQL-based work groups for parallel processing
**Propose:** Add to `~/.claude/skills/code-refactoring/` under "Parallelism Patterns"

**Rationale:**
- Applies to ANY project needing parallel processing
- Eliminates race conditions (natural work boundaries)
- Cleaner than queue-based approaches

**Code example:**
```python
# Group work by natural boundary (CVE, hash, etc.)
CREATE TABLE work_groups (group_id, group_key, record_count)
# Workers process one group at a time (no races)
```

**Would update:**
- ~/.claude/skills/code-refactoring/SKILL.md
- Add section: "SQL-Based Work Distribution for Parallelism"
- Document when to use vs queues

**Approve? (y/n)**
```

**User approval REQUIRED because:**
- Affects ALL future projects (highest impact)
- Establishes global conventions
- May conflict with existing global patterns

#### 6.6: Execute Approved Skill Updates

**For EACH approved skill update, spawn parallel document-writer agents:**

```python
# Execute ALL approved updates in SINGLE message (parallel)

Task(documentation-writer, """
Update global skill: python-style

Skill location: ~/.claude/skills/python-style/
Section: Concurrency Patterns (new section)

Pattern to add:
- SQLite WAL checkpoint timing for multiprocessing
- Code examples from tenable_sc_refactor
- Gotchas: Must checkpoint BEFORE worker spawn
- WHY: Worker processes see snapshot at fork time

Tasks:
1. Invoke ai-documentation skill FIRST
2. Read existing python-style/SKILL.md
3. Add new "Concurrency Patterns" section
4. Include code examples (validated against implementation)
5. Document timing requirements and gotchas
6. Update skill index if needed

Validate pattern is truly universal (not project-specific).

Return structured summary.
""")

Task(documentation-writer, """
Update global skill: code-refactoring

Skill location: ~/.claude/skills/code-refactoring/
Section: Parallelism Patterns (new section)

Pattern to add:
- SQL-based work distribution for parallel processing
- Code examples from tenable_sc_refactor work_groups tables
- When to use: Natural work boundaries, avoid race conditions
- Alternatives: Queue-based (when to use instead)

Tasks:
1. Invoke ai-documentation skill FIRST
2. Read existing code-refactoring/SKILL.md
3. Add new "Parallelism Patterns" section
4. Include comparison with queue-based approaches
5. Document trade-offs and when to use each
6. Add code examples

Validate pattern is universal.

Return structured summary.
""")
```

**Execute in parallel** (same pattern as documentation updates).

#### 6.7: Validate Skill Hierarchy Consistency

**After skill updates complete:**

```python
Task(documentation-validator, """
Validate skill hierarchy consistency.

Skills updated:
- Project: $WORK_DIR/.claude/skills/ (X skills)
- Repo: $REPO_ROOT/.claude/skills/ (Y skills)
- Global: ~/.claude/skills/ (Z skills)

Check for:
1. No contradictions between hierarchy levels
2. Project skills don't duplicate repo/global skills
3. Patterns correctly scoped (project vs repo vs global)
4. Code examples match actual implementation
5. Cross-references working (project → repo → global)

Return structured JSON with any issues.
""")
```

**Consistency rules:**
- Project skills can override repo/global (more specific)
- Repo skills can override global (repo-specific conventions)
- No duplicate content across levels (DRY principle)

#### 6.8: Skill Update Decision Tree

```
Code changes detected
    ↓
Analyze patterns in updated docs
    ↓
    ├─→ Project-only pattern? → AUTO-UPDATE project skill
    ├─→ Multi-project pattern? → ASK USER → Update repo skill
    └─→ Universal pattern?     → ASK USER → Update global skill
    ↓
For each level:
    ├─→ Create new skill? → ASK USER (repo/global only)
    └─→ Update existing?  → AUTO (project), ASK (repo/global)
    ↓
Execute approved updates (parallel agents)
    ↓
Validate consistency across hierarchy
    ↓
Report what changed
```

**Key rules:**
- **Project skills**: Auto-create, auto-update (low impact)
- **Repo/Global skills**: Ask before create, ask before update (high impact)
- **New skill recommendations**: Always present rationale and ask

---

### Step 7: Summary Report

**Aggregate results from all agents:**

```markdown
## 📚 Documentation & Skills Updated

### 📄 Documentation Updates

#### Components Processed:
- processors/ (4 files, 12 functions documented)
- cache/ (2 files, 8 functions documented)
- api_handler/ (3 files, 6 functions documented)

#### Files Modified:
- CLAUDE.md: Updated 5 gotchas, optimized from 450→380 lines
- docs/API_REFERENCE.md: Added 26 function signatures, updated 8 existing
- docs/business_logic/BUSINESS_RULES.md: Added 3 new rules
- docs/HOW_TO.md: Updated 2 workflows with new patterns

#### Files Created:
- docs/QUICKREF.md: Extracted 70 lines from CLAUDE.md (deep-dive content)
- docs/TROUBLESHOOTING.md: 5 common errors documented

#### Validation Results:
✅ Zero CRITICAL issues (was: 8)
✅ Zero IMPORTANT issues (was: 15)
⚠️  2 MINOR issues (line count slightly over in OVERVIEW.md)

#### Line Counts:
- CLAUDE.md: 380/400 (target met ✅)
- docs/OVERVIEW.md: 205/200 (5 lines over, acceptable)
- docs/API_REFERENCE.md: 450 lines (comprehensive ✅)

### 🎓 Skill Hierarchy Updates

#### Project-Level Skills (Auto-Updated):
✅ Created: $WORK_DIR/.claude/skills/tenable-sc-patterns/
   - Compliance severity mapping (Pass/Info handling)
   - Cascade matching (10-level asset matching)
   - Patched view closure logic

✅ Created: $WORK_DIR/.claude/skills/tenable-cache-patterns/
   - Persistent DAA staging (cross-scan accumulation)
   - Batch fetch optimization (eliminate N+1 queries)
   - WAL checkpoint timing (worker visibility)

#### Repo-Level Skills (User-Approved):
✅ Updated: $REPO_ROOT/.claude/skills/mongodb-patterns/
   - Added batch operations section (DEFAULT_BATCH_SIZE = 5000)
   - Documented retry_run pattern
   - Used in: tenable_sc_refactor, disa, nvd_api

#### Global Skills (User-Approved):
✅ Updated: ~/.claude/skills/python-style/SKILL.md
   - Added "Concurrency Patterns" section
   - SQLite WAL checkpoint timing for multiprocessing
   - Universal pattern applicable to ALL Python projects

✅ Updated: ~/.claude/skills/code-refactoring/SKILL.md
   - Added "Parallelism Patterns" section
   - SQL-based work distribution vs queue-based
   - Trade-offs and when to use each approach

#### Skills Validation:
✅ No contradictions across hierarchy
✅ No duplicate content between levels
✅ Patterns correctly scoped (project → repo → global)
✅ Code examples validated against implementation

### ⚡ Parallel Efficiency:
- **Documentation**: 3 document-writer agents (2 min vs 6 min sequential)
- **Skills**: 4 document-writer agents (parallel execution)
- **Total wall time**: ~3 minutes (docs + skills)
- **Context saved**: ~60k tokens (agents work independently)

### 📊 Overall Impact:
- **Documentation**: 8 files updated, 2 created
- **Skills**: 2 project skills created, 3 skills updated (1 repo, 2 global)
- **Validation**: All CRITICAL/IMPORTANT issues resolved
- **Knowledge capture**: Project patterns promoted to skills for reuse
```

---

## Agent Coordination Pattern

### Parallelism Strategy

**Maximum parallelism = 1 agent per component:**
- Small project (3 components): 3 agents in parallel
- Medium project (8 components): 8 agents in parallel
- Large project (20+ components): Group related, still 8-12 agents max

**Component grouping for large projects:**
```python
# Example: tenable_sc_refactor with 20+ files
# Group into logical components:

processors_group = [
    'base_processor.py',
    'asset_processor.py',
    'known_vuln_processor.py',
    'solution_processor.py',
    'detected_vuln_processor.py',
    'application_processor.py',
    'daa_processor.py',
]  # 1 agent

cache_group = [
    'tenable_sc_cache.py',
    'persistent_daa_staging_handler.py',
    'preflight_config_handler.py',
]  # 1 agent

api_handler_group = [
    'download_manager.py',
    'handler.py',
    'tenable_client.py',
]  # 1 agent

# Total: 3 agents instead of 15+ (efficient grouping)
```

### Context Sources Priority

**Agents receive context in this order:**

1. **Validation issues** (CRITICAL/IMPORTANT from Step 2)
2. **.spec/ files** (implementation context if available)
3. **Git diff** (recent changes if available)
4. **Existing documentation** (current state)
5. **Code files** (ground truth)

**Agents DO NOT receive:**
- Full codebase context (too large)
- Other agents' results (independent execution)
- Parent agent context (clean slate per agent spec)

---

## Special Cases

### Case 1: No .spec/ Files

**If no .spec/ files exist:**
- Agents still work (read code directly)
- Focus on code-to-docs validation
- May miss "why" context (only capture "what")

**Mitigation:**
- Document-writer reads implementation comments
- Extracts WHY comments from code
- Infers patterns from code structure

### Case 2: Massive Project (>50 files)

**If component count exceeds 15:**
- Group by directory structure (natural boundaries)
- Prioritize recently changed components (git diff)
- Run in batches if needed (8-12 agents at a time)

**Example batching:**
```python
# Batch 1: Core processors (8 agents)
# Wait for completion
# Batch 2: Utilities and helpers (6 agents)
# Wait for completion
# Batch 3: CLAUDE.md optimization (1 agent)
```

### Case 3: No Existing Documentation (Bootstrap Mode)

**Handled automatically in Step 1:**
- Detects missing CLAUDE.md or docs/llms.txt
- Spawns single documentation-writer agent in bootstrap mode
- Agent creates COMPLETE library from codebase analysis:
  - CLAUDE.md (appropriate template for hierarchy level)
  - docs/llms.txt (navigation index)
  - docs/OVERVIEW.md (5-min overview)
  - docs/API_REFERENCE.md (all public functions)
  - docs/HOW_TO.md (common workflows)
  - docs/business_logic/ (if needed)
- Then proceeds with normal validation/update workflow

**Bootstrap is ONE-SHOT:**
- Single agent analyzes entire codebase
- Creates all documentation at once
- Ensures consistency across all docs
- After creation, switches to normal update mode

---

## Critical Rules

**DO:**
- Spawn ALL document-writer agents in SINGLE message (parallelism)
- Group components logically (avoid over-parallelization)
- Use validation results to guide updates (don't guess what's wrong)
- Check parent CLAUDE.md for duplication (hierarchical inheritance)
- Re-validate after updates (ensure fixes worked)

**DON'T:**
- Launch agents sequentially (defeats purpose of parallel updates)
- Skip validation step (need to know what's wrong)
- Update docs without reading code (must verify accuracy)
- Ignore CLAUDE.md line count targets (enforced limits)
- Proceed if final validation fails (report blockers)

---

## Example Execution

**User:** `/update_docs`

**Agent determines working directory:**
- Checks session context: User just finished work on `fisio/imports/tenable_sc_refactor/`
- Working directory: `fisio/imports/tenable_sc_refactor/`

**Discovery:**
- Found 15 Python files in 5 directories
- Found CLAUDE.md, docs/OVERVIEW.md, docs/API_REFERENCE.md
- Found .spec/SPEC.md (implementation context available)
- Git diff shows 8 files changed in last week

**Validation:**
- 12 CRITICAL issues (incorrect file:line refs, outdated signatures)
- 18 IMPORTANT issues (missing functions, stale gotchas)
- 5 MINOR issues (CLAUDE.md 450 lines, target 400)

**Parallel execution:**
- Spawns 5 document-writer agents (1 per directory)
- All agents run simultaneously
- Total completion: ~2 minutes

**CLAUDE.md optimization:**
- Extracts 70 lines to QUICKREF.md
- Removes duplicate content from parent CLAUDE.md
- Converts prose to tables (business logic section)
- Final size: 380 lines ✅

**Final validation:**
- Zero CRITICAL issues
- Zero IMPORTANT issues
- All targets met

**Report:** Shows what was updated, validation status, efficiency gains.

---

**You are efficient. Parallel agents, accurate updates, validated results.**
