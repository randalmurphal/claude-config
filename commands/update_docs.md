---
name: update_docs
description: Update documentation AND skills to match current implementation using parallel agents with session knowledge capture
---

# /update_docs - Parallel Documentation & Skills Update

## 🎯 Purpose

Update all documentation (CLAUDE.md/AGENTS.md + docs/) AND skills hierarchy to match current implementation. Captures session knowledge and spawns parallel agents for each component.

**When to use:**
- After implementation changes
- After /conduct or /solo completion
- Periodic maintenance
- Post-refactor

**Prerequisites:** None

---

## Workflow

### Step 0: Determine Working Directory

Infer from session context:
- User-mentioned component/directory
- Recent file operations
- Current working directory

If unclear, ask:
```
Which directory should I update documentation for?
- Current directory (.)
- Specific path
```

`$WORK_DIR` = determined directory

---

### Step 0.5: Extract Session Knowledge

Analyze recent conversation (last 30-50 messages):

```python
session_knowledge = {
    "gotchas": [
        {
            "pattern": str,
            "why": str,
            "fix": str,
            "location": "file.py:line",
            "scope": "project_local|parent_scope|repo_scope"
        }
    ],
    "decisions": [
        {
            "decision": str,
            "rationale": str,
            "trade_offs": str,
            "scope": "project_local|parent_scope|repo_scope"
        }
    ],
    "performance": [
        {
            "insight": str,
            "metrics": str,
            "location": "file.py:line",
            "scope": "project_local|parent_scope|repo_scope"
        }
    ],
    "business_rules": [
        {
            "rule": str,
            "condition": str,
            "behavior": str,
            "why": str,
            "location": "file.py:line",
            "scope": "project_local|parent_scope|repo_scope"
        }
    ],
    "patterns": [
        {
            "pattern": str,
            "description": str,
            "benefits": str,
            "example": str,
            "scope": "project_local|parent_scope|repo_scope"
        }
    ]
}
```

**Scope:**
- `project_local`: $WORK_DIR only
- `parent_scope`: Parent directory (framework/subsystem)
- `repo_scope`: Entire repository

Store for Steps 3 and 6.

---

### Step 1: Discovery

Find components:

```bash
# Python modules
find $WORK_DIR -name "__init__.py" -type f | xargs dirname | sort -u

# Standalone files
find $WORK_DIR -name "*.py" -type f -not -path "*/tests/*" -not -name "__init__.py"

# Documentation
find $WORK_DIR -name "*.md" -type f
find $WORK_DIR -name "CLAUDE.md" -o -name "AGENTS.md"
ls $WORK_DIR/docs/ 2>/dev/null
```

Catalog:
- Modules: Directories with `__init__.py`
- Standalone files: Top-level `.py` files
- Existing docs: All `.md` files
- Doc format: CLAUDE.md or AGENTS.md (detect which)

Check context sources:
```bash
ls $WORK_DIR/.spec/SPEC*.md 2>/dev/null
git diff --name-only HEAD~5..HEAD -- $WORK_DIR 2>/dev/null
```

**If no documentation exists:**

```python
Task(documentation-writer, """
Create documentation library from scratch.

Working directory: $WORK_DIR
Workflow: update_docs (bootstrap mode)

Tasks:
1. Invoke ai-documentation skill
2. Analyze codebase structure
3. Detect parent doc format (CLAUDE.md or AGENTS.md - use same)
4. Create main doc:
   - Hierarchy level from parent
   - Simple tool (~200 lines) or Complex (300-400 lines)
   - Purpose, Architecture, Key Components, Gotchas
   - file:line references
5. Create docs/:
   - llms.txt (navigation)
   - OVERVIEW.md
   - API_REFERENCE.md
   - HOW_TO.md
   - business_logic/ (if needed)
6. Populate from code analysis

Return structured summary.
""")
```

---

### Step 1.5: Determine Validation Strategy

Calculate complexity:

```python
total_components = len(python_modules) + len(standalone_files)
total_doc_lines = sum(count_lines(f) for f in glob("$WORK_DIR/**/*.md"))
rule_count = count_rule_rows("BUSINESS_RULES.md") if exists else 0

complexity_score = (total_components * 100) + (total_doc_lines / 10) + (rule_count * 50)

# Determine reviewers
if complexity_score < 1000:
    reviewers = 1
elif complexity_score < 3000:
    reviewers = 2
elif complexity_score < 6000:
    reviewers = 4
else:
    reviewers = 6

# Group docs
review_groups = partition_docs(
    components=all_components,
    docs=all_md_files,
    num_groups=reviewers,
    strategy="balance_lines"  # ~2000 lines per reviewer
)
```

Grouping:
- Related components together
- CLAUDE.md/AGENTS.md hierarchy in single reviewer
- Balance lines (~2000 each)
- Dedicated hierarchy reviewer if >3 levels

---

### Step 2: Parallel Validation

Spawn documentation-reviewer agents (SINGLE message):

```python
# Example: 3 reviewers

Task(documentation-reviewer, """
Validate Group 1.

Working directory: $WORK_DIR
Scope:
- processors/ (7 files, 14 functions)
- Main doc: processors sections

Tasks:
1. Invoke ai-documentation skill
2. Verify file:line references
3. Verify function signatures
4. Verify architecture claims
5. Check constants/values
6. Check line counts

Return JSON with Group 1 issues.
""")

Task(documentation-reviewer, """
Validate Group 2.

Working directory: $WORK_DIR
Scope:
- cache/ (3 files, 8 functions)
- api_handler/ (3 files, 6 functions)
- Main doc: cache + API sections

Tasks:
[Same as Group 1]

Return JSON with Group 2 issues.
""")

Task(documentation-reviewer, """
Validate Group 3.

Working directory: $WORK_DIR
Scope:
- docs/OVERVIEW.md
- docs/BUSINESS_RULES.md
- docs/ARCHITECTURE.md
- docs/TROUBLESHOOTING.md

Tasks:
[Same as Group 1]

Return JSON with Group 3 issues.
""")

# If >3 hierarchy levels:
Task(documentation-reviewer, """
Validate hierarchy integrity.

Working directory: $WORK_DIR
Scope:
- All CLAUDE.md/AGENTS.md in hierarchy
- Parent/child relationships

Tasks:
1. Invoke ai-documentation skill
2. Check no parent duplication
3. Check line counts
4. Check cross-references
5. Check hierarchical inheritance

Return JSON with hierarchy issues.
""")
```

Aggregate:

```python
all_issues = merge([r1.issues, r2.issues, r3.issues])
critical_issues = [i for i in all_issues if i.severity == "CRITICAL"]
important_issues = [i for i in all_issues if i.severity == "IMPORTANT"]
```

---

### Step 3: Parallel Documentation Updates

Spawn documentation-writer agents (SINGLE message):

```python
# Example: 3 components

Task(documentation-writer, """
Update processors/ documentation.

Working directory: $WORK_DIR/processors
Files:
- base_processor.py
- asset_processor.py
- known_vuln_processor.py
- detected_vuln_processor.py

Validation issues:
[JSON for this component]

Session knowledge:
[gotchas/decisions/performance/rules for this component with scope=project_local|parent_scope]

Context:
- .spec/SPEC.md (if exists)
- Git diff: [recent changes]

Tasks:
1. Invoke ai-documentation skill
2. Detect doc format (CLAUDE.md or AGENTS.md)
3. Update docs/API_REFERENCE.md
4. Add/update gotchas in main doc
5. Integrate session knowledge:
   - Gotchas → main doc "Common Gotchas"
   - Decisions → ARCHITECTURE.md or QUICKREF.md
   - Performance → QUICKREF.md or HOW_TO.md
   - Business rules → BUSINESS_RULES.md
   - Patterns → ARCHITECTURE.md or QUICKREF.md
6. Fix CRITICAL and IMPORTANT issues
7. Update docs/llms.txt if new docs
8. Track changes (created/removed/moved)

Return summary with doc changes.
""")

Task(documentation-writer, """
Update cache/ documentation.

Working directory: $WORK_DIR/cache
Files:
- tenable_sc_cache.py
- persistent_daa_staging_handler.py

Validation issues:
[JSON for this component]

Session knowledge:
[relevant session knowledge]

Context:
- .spec/SPEC.md (if exists)
- Git diff: [changes]

Tasks:
[Same as processors]

Return summary with doc changes.
""")

Task(documentation-writer, """
Update api_handler/ documentation.

Working directory: $WORK_DIR/api_handler
Files:
- download_manager.py
- handler.py
- tenable_client.py

Validation issues:
[JSON for this component]

Session knowledge:
[relevant session knowledge]

Context:
- .spec/SPEC.md (if exists)
- Git diff: [changes]

Tasks:
[Same as processors]

Return summary with doc changes.
""")
```

---

### Step 3.5: Update Documentation References

Collect doc changes:

```python
doc_changes = {
    "created": [],
    "removed": [],
    "moved": [],
    "renamed": []
}

# For each change, update references:
for change in doc_changes["created"] + doc_changes["moved"] + doc_changes["renamed"]:
    # Find references
    grep -r "old_path|old_name" $WORK_DIR/*.md
    grep -r "old_path|old_name" $WORK_DIR/docs/*.md

    # Update in:
    # - Main doc (CLAUDE.md or AGENTS.md)
    # - docs/llms.txt
    # - Cross-referencing docs
    # - Parent directory docs

check_broken_links($WORK_DIR)
```

---

### Step 4: Main Doc Optimization

Re-validate main doc:

```python
Task(documentation-reviewer, """
Validate main doc optimization.

Working directory: $WORK_DIR
Files: [CLAUDE.md or AGENTS.md in hierarchy]

Invoke ai-documentation skill.

Check:
1. Line count within target
2. No parent duplication
3. Business logic in tables
4. File structure condensed
5. Deep-dive extracted to QUICKREF.md if >400 lines

Return JSON with optimization recommendations.
""")
```

If issues found:

```python
Task(documentation-writer, """
Optimize main doc.

Files: [files needing optimization]
Working directory: $WORK_DIR

Invoke ai-documentation skill.

Issues:
[JSON from reviewer]

Tasks:
1. Remove duplicate content
2. Convert prose to tables/bullets
3. Extract deep-dive to QUICKREF.md if >400 lines
4. Condense file structure trees
5. Ensure line count within target

Return summary.
""")
```

---

### Step 5: Final Validation

```python
Task(documentation-reviewer, """
Final validation.

Working directory: $WORK_DIR
Scope: ALL documentation

Check:
1. All CRITICAL issues resolved
2. All IMPORTANT issues resolved
3. File:line references accurate
4. Line counts within targets
5. No new issues
6. All references updated (no broken links)

Return JSON with final status.
""")
```

Completion criteria:
- ✅ Zero CRITICAL issues
- ✅ Zero IMPORTANT issues
- ✅ Line counts within targets
- ✅ All components documented
- ✅ All references updated

If issues remain after 2 passes, report blockers.

---

### Step 6: Skill Hierarchy Updates

Analyze session knowledge for skill updates:

```python
skill_updates = {
    "project_skills": [
        # scope=project_local from Step 0.5
        # Update $WORK_DIR/.claude/skills/
    ],
    "repo_skills": [
        # scope=repo_scope from Step 0.5
        # Update $REPO_ROOT/.claude/skills/ (ASK)
    ],
    "global_skills": [
        # Universal patterns (ASK)
        # Update ~/.claude/skills/
    ]
}
```

#### 6.1: Update Project Skills (Auto)

```python
for pattern in skill_updates["project_skills"]:
    Task(documentation-writer, """
    Update project skill: {pattern.category}

    Skill location: $WORK_DIR/.claude/skills/{category}/
    Type: Project-specific

    Session changes:
    [pattern details from Step 0.5]

    Tasks:
    1. Invoke ai-documentation skill
    2. Create/update SKILL.md
    3. Add code examples
    4. Document usage
    5. Include gotchas

    Validate against $WORK_DIR code.

    Return summary.
    """)
```

#### 6.2: Propose Repo Skills (Ask User)

```markdown
## 🔄 Repo-Level Skill Updates

**Pattern**: {pattern_name}
**Used in**: {components}
**Scope**: Multiple projects in repo

**Would update**: $REPO_ROOT/.claude/skills/{skill_name}/

**Approve? (y/n)**
```

#### 6.3: Propose Global Skills (Ask User)

```markdown
## 🌍 Global Skill Updates

**Pattern**: {pattern_name}
**Scope**: ALL projects

**Example**:
{code_snippet}

**Would update**: ~/.claude/skills/{skill_name}/

**Approve? (y/n)**
```

#### 6.4: Execute Approved Skills

```python
# SINGLE message, parallel execution
for approved in approved_repo + approved_global:
    Task(documentation-writer, """
    Update skill: {skill_name}

    Location: {skill_path}
    Section: {section}

    Pattern:
    [from session knowledge]

    Tasks:
    1. Invoke ai-documentation skill
    2. Read existing SKILL.md
    3. Add/update section
    4. Include examples (validated)
    5. Document usage, benefits, gotchas
    6. Update index

    Validate scope (project/repo/global).

    Return summary.
    """)
```

#### 6.5: Validate Skill Consistency

```python
Task(documentation-reviewer, """
Validate skill hierarchy consistency.

Skills updated:
- Project: $WORK_DIR/.claude/skills/
- Repo: $REPO_ROOT/.claude/skills/
- Global: ~/.claude/skills/

Check:
1. No contradictions between levels
2. No duplication (project/repo/global)
3. Correct scoping
4. Examples match implementation
5. Cross-references working

Return JSON with issues.
""")
```

---

### Step 7: Summary Report

```markdown
## 📚 Documentation & Skills Updated

### 📄 Documentation

**Components**: processors/ (4 files), cache/ (2 files), api_handler/ (3 files)

**Modified**:
- {Main doc}: 5 gotchas, 450→380 lines
- docs/API_REFERENCE.md: +26 signatures, ~8 updated
- docs/BUSINESS_RULES.md: +3 rules

**Created**:
- docs/QUICKREF.md: 70 lines extracted
- docs/TROUBLESHOOTING.md: 5 errors

**Validation**:
✅ 0 CRITICAL (was 8)
✅ 0 IMPORTANT (was 15)
⚠️  2 MINOR

**Line Counts**:
- {Main doc}: 380/400 ✅
- docs/OVERVIEW.md: 205/200 (acceptable)

### 🎓 Skills

**Project** (Auto): ✅ Created $WORK_DIR/.claude/skills/{name}/
**Repo** (Approved): ✅ Updated $REPO_ROOT/.claude/skills/{name}/
**Global** (Approved): ✅ Updated ~/.claude/skills/{name}/

### 📊 Session Knowledge

- Gotchas: {N} → main doc
- Decisions: {N} → ARCHITECTURE.md
- Performance: {N} → QUICKREF.md
- Business rules: {N} → BUSINESS_RULES.md
- Patterns: {N} → skills

### ⚡ Efficiency

- Documentation agents: {N}
- Reviewer agents: {N}
- Skill agents: {N}
- Wall time: ~{X} min

### 📊 Impact

- Docs: {N} updated, {N} created
- Skills: {N} project, {N} updated
- Validation: All resolved
- Knowledge: Session preserved
```

---

## Parallelism Strategy

**Max parallelism**: 1 agent per component

- Small (3 components): 3 agents
- Medium (8 components): 8 agents
- Large (20+ components): Group, 8-12 agents max

Component grouping:
```python
processors_group = [files]  # 1 agent
cache_group = [files]       # 1 agent
api_group = [files]         # 1 agent
```

---

## Context Sources Priority

1. Session knowledge (Step 0.5)
2. Validation issues (Step 2)
3. .spec/ files
4. Git diff
5. Existing docs
6. Code files

---

## Critical Rules

**DO:**
- Spawn ALL agents in SINGLE message (parallel)
- Extract session knowledge
- Detect doc format (CLAUDE.md or AGENTS.md)
- Update all references
- Re-validate after updates

**DON'T:**
- Launch sequentially
- Skip session extraction
- Skip validation
- Mix CLAUDE.md/AGENTS.md formats
- Proceed if validation fails

**Coordinator orchestrates all sub-agents. No nested spawning.**
