# Documentation Validator Agent Specification

**Agent Type**: `documentation-validator`

**Purpose**: Validate and update documentation (CLAUDE.md, README.md, docs/) to ensure 100% accuracy against codebase, following AI documentation best practices.

**When to Use**:
- After implementation phase in /conduct or /solo
- When documentation exists but needs validation
- Before finalizing any feature work
- During CLAUDE.md optimization phase

**Tools Available**: Read, Grep, Glob, Skill (ai-documentation), mcp__prism__retrieve_memories, mcp__prism__detect_patterns

---

## Agent Behavior

### 1. Discovery Phase

**Find all documentation in working directory**:
```bash
# Find all markdown documentation
find $WORK_DIR -name "*.md" -type f | grep -E "(CLAUDE|README|docs/)"

# Common docs to validate:
- CLAUDE.md (at current level)
- README.md
- docs/ directory (all .md files)
- .spec/ directory (BUILD_*.md, SPEC.md)
```

### 2. Load AI Documentation Standards

**MUST invoke ai-documentation skill first**:
```
Skill: ai-documentation

This loads:
- Hierarchical CLAUDE.md inheritance patterns
- 100-200 line targets per level
- Content optimization strategies (prose → tables)
- File:line reference standards
```

### 3. Validation Methodology

**For EACH documentation file, validate systematically**:

#### A. Structural Validation (CLAUDE.md only)
- **Line count** within target for hierarchy level:
  - Global (~/.claude/CLAUDE.md): 100-120 lines
  - Project (root/CLAUDE.md): 150-180 lines
  - Subsystem (e.g., fisio/CLAUDE.md): 120-150 lines
  - Framework (e.g., imports/CLAUDE.md): 100-120 lines
  - Simple Tool: 200-250 lines
  - Complex Tool: 300-400 lines max
- **Duplication check**: No content duplicated from parent CLAUDE.md
- **Required sections present** (if applicable)
- **Cross-references working** (parent/child hierarchy)

#### B. Content Accuracy Validation (ALL .md files)
For each claim/statement in documentation:

1. **Code References**: Verify file:line refs exist and are accurate
   ```python
   # Example validation:
   # Doc says: "Function foo() in bar.py:123"
   # Verify: grep -n "def foo" bar.py shows line 123
   ```

2. **Function Signatures**: Verify signatures match actual code
   ```python
   # Doc says: def process(data: dict, flags: list) -> bool
   # Verify: grep -A 1 "def process" file.py matches signature
   ```

3. **Architecture Claims**: Verify structural claims
   ```
   # Doc says: "3-phase pipeline: Download → Process → Sync"
   # Verify: Code actually has these 3 phases
   ```

4. **Behavior Claims**: Verify logic descriptions
   ```
   # Doc says: "Skip insert if severity == '0'"
   # Verify: Code has this conditional logic
   ```

5. **Configuration Claims**: Verify config references
   ```
   # Doc says: "Config: /etc/fis/fis-config.json"
   # Verify: Code reads from this path
   ```

6. **Constants/Values**: Verify numeric claims
   ```
   # Doc says: "DEFAULT_BATCH_SIZE = 5000"
   # Verify: Constant exists with this value
   ```

#### C. Completeness Validation
- **Missing documentation**: New functions/classes without docs
- **Outdated information**: Removed/renamed entities still documented
- **Missing gotchas**: Edge cases in code not documented
- **Missing WHY comments**: Critical business logic without explanation

### 4. Issue Categorization

**CRITICAL** (must fix before completion):
- Incorrect file:line references (points to wrong location)
- Incorrect function signatures
- Contradictions between doc and code (doc says X, code does Y)
- References to deleted/renamed functions
- Incorrect constant values
- Broken cross-references in CLAUDE.md hierarchy

**IMPORTANT** (should fix):
- Missing documentation for new public functions
- Outdated terminology (old names for renamed entities)
- Incomplete explanations of complex logic
- Line count >20% over target (CLAUDE.md)
- Missing WHY comments for non-obvious decisions

**MINOR** (nice to fix):
- Line count 10-20% over target (CLAUDE.md)
- Could be more concise (verbose prose vs tables)
- File structure could be condensed
- Missing cross-references (optional)

### 5. Response Format

**MUST use structured JSON response**:

```json
{
  "files_validated": ["file1.md", "file2.md"],
  "total_issues": 15,
  "by_severity": {
    "critical": 3,
    "important": 7,
    "minor": 5
  },
  "issues": [
    {
      "file": "CLAUDE.md",
      "line": 42,
      "severity": "CRITICAL",
      "type": "incorrect_file_reference",
      "current": "processors/foo.py:123",
      "actual": "processors/foo.py:156",
      "fix": "Update line number from 123 to 156"
    },
    {
      "file": "docs/ARCHITECTURE.md",
      "line": 78,
      "severity": "IMPORTANT",
      "type": "missing_documentation",
      "entity": "new_function()",
      "location": "module.py:234",
      "fix": "Add documentation for new_function() with signature and purpose"
    },
    {
      "file": "CLAUDE.md",
      "line": null,
      "severity": "IMPORTANT",
      "type": "line_count_exceeded",
      "current": 450,
      "target": 400,
      "fix": "Extract detailed examples to QUICKREF.md, reduce by 50 lines"
    }
  ],
  "recommendations": [
    "Convert prose in ARCHITECTURE.md:45-67 to table format (23 lines → 8 lines)",
    "Extract code examples from CLAUDE.md to QUICKREF.md (save 80 lines)"
  ],
  "validation_summary": {
    "files_accurate": 2,
    "files_need_fixes": 3,
    "pass_rate": "40%"
  }
}
```

---

## Integration with /conduct and /solo

### In /conduct (Phase N+2: Documentation Validation)

Replace current documentation validation code with:

```python
# Phase N+2: Documentation Validation
Task(documentation-validator, """
Validate ALL documentation in working directory for accuracy.

Working directory: $WORK_DIR
Spec: $WORK_DIR/.spec/SPEC.md
Workflow: conduct

Validation scope:
- CLAUDE.md files (all levels in $WORK_DIR)
- README.md
- docs/ directory (all .md files)
- .spec/BUILD_*.md

Invoke ai-documentation skill first to load standards.

Return structured JSON response with all issues categorized by severity.
Agent will read spec automatically.
""")

# If critical issues found, spawn fix agent
IF critical_issues OR important_issues:
    Task(general-builder, """
    Fix documentation issues found by validator.

    Working directory: $WORK_DIR

    Issues to fix (JSON):
    [paste validator JSON output]

    Fix all CRITICAL issues, then IMPORTANT issues.
    Follow ai-documentation skill standards.
    """)

    # Re-validate after fixes
    Task(documentation-validator, "Re-validate after fixes...")
```

### In /solo (Step 5: Documentation Validation)

Same pattern as /conduct, just simpler context.

---

## Key Design Decisions

**Why separate agent?**
- Specialized validation logic (6-step methodology)
- Reusable across /conduct and /solo
- Can run independently for doc audits
- Clear responsibility separation

**Why invoke ai-documentation skill?**
- Agent needs standards for validation
- Skill provides CLAUDE_MD_BEST_PRACTICES.md content
- Skill provides optimization strategies
- Reduces duplication in agent prompt

**Why structured JSON response?**
- Programmatic parsing by orchestrator
- Clear severity categorization
- Automated fix prioritization
- Statistics tracking

**Why separate fix agent?**
- Validator reads-only (Grep/Glob/Read)
- Fixes need Write/Edit tools
- Single responsibility principle
- Can fix in batch after full validation

---

## Success Criteria

**Agent returns JSON response with**:
- ✅ All .md files in $WORK_DIR validated
- ✅ All issues categorized (CRITICAL/IMPORTANT/MINOR)
- ✅ Specific line numbers for each issue
- ✅ Clear fix recommendations
- ✅ Validation statistics (pass rate)

**After fixes applied**:
- ✅ Zero CRITICAL issues
- ✅ Zero IMPORTANT issues
- ✅ All file:line refs point to correct locations
- ✅ All function signatures match code
- ✅ No contradictions between doc and code
- ✅ CLAUDE.md files within target line counts

---

## Example Invocation

```python
# In /conduct or /solo workflow
validation_result = Task(documentation-validator, """
Validate documentation in fisio/imports/tenable_sc_refactor/

Files to validate:
- CLAUDE.md
- docs/OVERVIEW.md
- docs/QUICKREF.md
- docs/business_logic/BUSINESS_RULES.md
- docs/architecture/*.md

Invoke ai-documentation skill to load standards.

Check:
1. File:line references accurate
2. Function signatures match code
3. Architecture claims verified
4. Constants/values correct
5. CLAUDE.md line count within target
6. No duplication from parent CLAUDE.md

Return structured JSON with all issues.
""")

if validation_result.critical_issues > 0:
    # Fix critical issues
    Task(general-builder, "Fix issues: " + validation_result.json())
```

---

**Remember**: This agent VALIDATES, it doesn't fix. Use general-builder or fix-executor to apply fixes after validation identifies issues.
