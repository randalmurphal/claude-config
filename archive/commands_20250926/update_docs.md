---
name: update_docs
description: Update project documentation in project_notes directory
---

You are managing documentation updates for the project using the two-document approach.

## Command Usage

- `/update_docs [component]` - Update technical documentation for a specific component
- `/update_docs --all` - Update documentation for all changed components
- `/update_docs --review [component] "notes"` - Add review notes only

## Examples

```bash
/update_docs tenable_sc              # Update tenable_sc import docs
/update_docs common/mongodb          # Update common MongoDB docs
/update_docs --all                   # Update all changed components
/update_docs --review tenable_sc "Refactored to 3-phase architecture for performance"
```

## Documentation Structure

All documentation lives in `project_notes/` mirroring implementation:
```
project_notes/
├── imports/
│   ├── tenable_sc/
│   │   ├── README.md          # Technical docs (current state)
│   │   └── REVIEW_NOTES.md    # Historical notes (accumulates)
│   └── [other imports]/
└── common/
    └── [components]/
```

## Workflow

### For Technical Updates (`README.md`):

1. **Identify Scope**
   - If specific component: Focus on that path
   - If `--all`: Use `git diff` to find changed files
   
2. **Analyze Current Implementation**
   - Read the actual code files
   - Understand current architecture
   - Identify what changed
   
3. **Delegate to doc-maintainer**
   Use Task tool to launch doc-maintainer with instructions:
   ```
   "Update technical documentation for [component] at project_notes/[path]/README.md
   Current implementation: [summary of what you found]
   Key changes: [what changed]
   Remove any references to: [deleted features]
   Add documentation for: [new features]"
   ```

4. **Verify Updates**
   - Ensure README.md reflects ONLY current code
   - No outdated information remains
   - All new features documented

### For Review Notes (`--review`):

1. **Delegate to doc-maintainer**
   Use Task tool to launch doc-maintainer with instructions:
   ```
   "Add review notes to project_notes/[path]/REVIEW_NOTES.md
   Date: [today]
   Type: [refactor/feature/bugfix]
   Notes: [provided notes]
   Do not modify README.md"
   ```

## Key Principles

### README.md (Technical)
- **REPLACE** outdated sections
- **REMOVE** deleted feature docs
- **CURRENT** state only
- **CLEAN** - no accumulation

### REVIEW_NOTES.md (Historical)
- **APPEND** only
- **TIMESTAMPED** entries
- **PRESERVE** all history
- **INSIGHTS** and decisions

## Example doc-maintainer Instructions

### For a refactored import:
```
"Update documentation for tenable_sc import at project_notes/imports/tenable_sc/
Changes:
- Now uses 3-phase architecture (was 5-phase)
- Added Redis caching for deduplication
- Removed old XML parsing logic
Update README.md to reflect current architecture.
Add refactor notes to REVIEW_NOTES.md with today's date."
```

### For a new feature:
```
"Update documentation for common/mongodb at project_notes/common/mongodb/
New feature: Bulk write operations with retry logic
Add to README.md under 'API Reference' section.
Do not modify REVIEW_NOTES.md unless insights to add."
```

## What You Must Do

1. **Always delegate to doc-maintainer** - Never write docs directly
2. **Provide clear scope** - Exactly which files/components changed
3. **Specify what to remove** - Outdated features that no longer exist
4. **Maintain structure** - Keep project_notes mirroring implementation

## What You Must NOT Do

- Never create excessive documentation files
- Never mix technical docs with review notes
- Never append endlessly to README.md
- Never remove content from REVIEW_NOTES.md
- Never create docs outside project_notes structure

## Success Response

After doc-maintainer completes:
```
Documentation updated successfully:
- Technical docs: project_notes/imports/tenable_sc/README.md
- Review notes: project_notes/imports/tenable_sc/REVIEW_NOTES.md (if applicable)
- Changes: Updated architecture, removed old XML logic, added caching docs
```