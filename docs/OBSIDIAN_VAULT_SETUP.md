# Obsidian Vault Setup for Claude Code

This document contains the complete structure and templates needed to set up a new Obsidian vault for Claude Code session management.

## Directory Structure

Create these directories in your vault root:

```
vault-root/
├── projects/          # Project overview notes with task tracking
├── sessions/          # Daily work logs linked to projects
├── tasks/             # Specifications and implementation plans
├── decisions/         # Architectural Decision Records (ADRs)
├── gotchas/           # Known issues and pain points
└── templates/         # Note templates for consistency
```

## Setup Commands

```bash
# Navigate to your vault
cd /path/to/your/vault

# Create directory structure
mkdir -p projects sessions tasks decisions gotchas templates

# Copy templates (see below for content)
```

## README.md

Place this in vault root:

```markdown
# Claude Code Session Notes

This vault is organized to work with Claude Code's `/notes-start` and `/consolidate` commands.

## Structure

- **projects/** - Project overview notes with task tracking
- **tasks/** - Specifications and implementation plans
- **sessions/** - Daily work logs linked to projects
- **decisions/** - Architectural Decision Records (ADRs)
- **gotchas/** - Known issues and pain points
- **templates/** - Note templates for consistency

## Workflows

### Starting Work
```
/notes-start [topic]   # Loads all context from Obsidian + PRISM
```

### Cleaning Up Notes
```
/consolidate [topic]   # Scans, fixes contradictions, organizes
```

## Note Status

All notes use frontmatter status:
- `status: current` - Use this
- `status: superseded` - Outdated, see link to current
- `status: consolidated` - Knowledge hub combining versions
- `status: draft` - Work in progress
- `status: archived` - Historical reference

## Templates

Located in `templates/` - copy and customize for your needs.

## Integration

- Notes link together with `[[wiki-style-links]]`
- Status system prevents using outdated info
- PRISM stores consolidated knowledge for cross-session memory
- Graph view shows relationships between topics

---

For full documentation, see `~/.claude/CLAUDE.md` (Obsidian Note Management section)
```

---

## Templates

### templates/project-note.md

```markdown
---
project: PROJECT_NAME
status: current
created: {{date}}
updated: {{date}}
tags: [project]
---

# PROJECT_NAME

## Current Spec
[[link-to-current-spec]] (vX - brief description)

## Task Status
- [ ] Initial task

## History
- {{date}}: Project created

## Current Blockers
None

## Links
- Spec: [[link-to-spec]]
- Sessions: [[sessions/]]
- Decisions: [[decisions/]]

## Notes
Brief project description and context.
```

---

### templates/spec-note.md

```markdown
---
status: current
version: 1
project: PROJECT_NAME
created: {{date}}
updated: {{date}}
tags: [spec, project/PROJECT_NAME]
---

# SPEC_NAME (CURRENT)

✅ **CURRENT SPEC**

## What We Kept From Previous Version
(If v2+, list what carried forward from v1)
- Key concept 1
- Key concept 2

## What Changed From Previous Version
(If v2+, list what's different)
- Change 1: Old approach → New approach (why)

## Specification

### Overview
What this spec covers and why it exists.

### Requirements
- Requirement 1
- Requirement 2

### Architecture
How this will be implemented.

### Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Related
- Project: [[projects/PROJECT_NAME]]
- Previous version: [[if applicable]]
- Decisions: [[decisions/]]
```

---

### templates/session-note.md

```markdown
---
date: {{date}}
project: PROJECT_NAME
tags: [session, project/PROJECT_NAME]
status: active
---

# SESSION_TITLE - {{date}}

Related: [[projects/PROJECT_NAME]]

## Context
What we're working on and why.

## What We Found
- Discovery 1
- Discovery 2

## What We Did
- [ ] Task 1
- [ ] Task 2

## Decisions Made
- Decision 1: See [[decisions/adr-XXX]]

## Gotchas Discovered
- Gotcha 1: Description and how to avoid

## Next Steps
- [ ] Next action 1
- [ ] Next action 2

## Links
- Related sessions: [[sessions/]]
- Related tasks: [[tasks/]]
```

---

### templates/decision-note.md

```markdown
---
status: current
project: PROJECT_NAME
created: {{date}}
tags: [decision, adr, project/PROJECT_NAME]
---

# ADR-XXX: DECISION_TITLE

**Status:** Accepted
**Date:** {{date}}
**Project:** [[projects/PROJECT_NAME]]

## Context
What problem or situation led to this decision?

## Decision
We will [decision statement].

## Alternatives Considered

### Alternative 1: [Name]
**Description:** Brief description
**Pros:** What's good
**Cons:** What's bad
**Why Rejected:** Specific reason

### Alternative 2: [Name]
**Description:** Brief description
**Pros:** What's good
**Cons:** What's bad
**Why Rejected:** Specific reason

## Consequences

### Positive
- Benefit 1
- Benefit 2

### Negative
- Tradeoff 1
- Tradeoff 2

### Risks
- Risk 1 and mitigation
- Risk 2 and mitigation

## Related
- Spec: [[tasks/]]
- Sessions: [[sessions/]]
- Other decisions: [[decisions/]]
```

---

### templates/consolidated-note.md

```markdown
---
status: consolidated
topic: TOPIC_NAME
consolidates: []
created: {{date}}
updated: {{date}}
tags: [consolidated, topic/TOPIC_NAME]
---

# TOPIC_NAME: Consolidated Knowledge

**Current Implementation:** [[link-to-current-spec]]

## What We Know (Across All Versions)

### Core Concept 1
- Key insight from v1 (still valid)
- Refinement from v2
**Sources:** [[note1#section]], [[note2]]

### Core Concept 2
- Another important concept
**Sources:** [[note3]]

## Current Approach

### How It Works
Current implementation details.

### Why This Way
Rationale for current approach.

## Evolution Timeline

### Version 1 (Date)
- Initial approach: X
- Learned: Y
- Why changed: Z

### Version 2 (Date)
- Revised approach: A
- Improvement: B

## Lessons Learned

### What Failed
- Approach X didn't work because Y
- **Lesson:** Don't do Z

### What Worked
- Approach A succeeded because B
- **Lesson:** Always do C

## Known Gotchas

1. **Gotcha 1 Description**
   - **Problem:** What breaks
   - **Solution:** How to avoid
   - **Source:** [[session-note]]

2. **Gotcha 2 Description**
   - **Problem:** What breaks
   - **Solution:** How to avoid
   - **Source:** [[another-note]]

## Key Decisions

- [[decisions/adr-001]]: Decision summary
- [[decisions/adr-002]]: Decision summary

## Related Notes
- Current spec: [[tasks/current-spec]]
- Project: [[projects/PROJECT_NAME]]
- Sessions: [[sessions/YYYY-MM-DD]]
- Decisions: [[decisions/]]
```

---

### templates/superseded-spec.md

```markdown
---
status: superseded
superseded-by: [[link-to-new-version]]
superseded-date: {{date}}
reason: Brief reason for supersession
version: X
project: PROJECT_NAME
tags: [spec, superseded, project/PROJECT_NAME]
---

# SPEC_NAME vX (SUPERSEDED)

⚠️ **SUPERSEDED** - See [[link-to-new-version]]

## Still Valid {#Still Valid}
These concepts were carried forward to the new version:
- Concept 1: Brief description
- Concept 2: Brief description

See [[new-version#What We Kept]] for how these were integrated.

## Why This Was Abandoned {#Why Abandoned}
Explanation of what didn't work and why we moved on.

Key issues:
- Issue 1
- Issue 2

See [[decisions/adr-XXX]] for the decision to move to new approach.

## Original Specification
[Original spec content preserved for historical reference]

## Related
- Current version: [[link-to-current]]
- Project: [[projects/PROJECT_NAME]]
- Decision: [[decisions/adr-XXX]]
```

---

## Quick Setup Script

For bash/zsh (run in vault root):

```bash
#!/bin/bash
# setup-obsidian-vault.sh

VAULT_DIR="${1:-.}"

cd "$VAULT_DIR" || exit 1

echo "Setting up Obsidian vault in: $VAULT_DIR"

# Create directories
mkdir -p projects sessions tasks decisions gotchas templates

# Create README
cat > README.md << 'READMEEOF'
# Claude Code Session Notes

This vault is organized to work with Claude Code's `/notes-start` and `/consolidate` commands.

## Structure

- **projects/** - Project overview notes with task tracking
- **tasks/** - Specifications and implementation plans
- **sessions/** - Daily work logs linked to projects
- **decisions/** - Architectural Decision Records (ADRs)
- **gotchas/** - Known issues and pain points
- **templates/** - Note templates for consistency

## Workflows

### Starting Work
```
/notes-start [topic]   # Loads all context from Obsidian + PRISM
```

### Cleaning Up Notes
```
/consolidate [topic]   # Scans, fixes contradictions, organizes
```

## Note Status

All notes use frontmatter status:
- `status: current` - Use this
- `status: superseded` - Outdated, see link to current
- `status: consolidated` - Knowledge hub combining versions
- `status: draft` - Work in progress
- `status: archived` - Historical reference

## Templates

Located in `templates/` - copy and customize for your needs.
READMEEOF

echo "✅ Created directory structure"
echo "✅ Created README.md"
echo ""
echo "Next steps:"
echo "1. Copy template files from ~/.claude/docs/OBSIDIAN_VAULT_SETUP.md"
echo "2. Or run: grep -A 999 '^### templates/' ~/.claude/docs/OBSIDIAN_VAULT_SETUP.md"
echo "3. Configure ObsidianPilot to point to this vault"
echo ""
echo "Vault setup complete!"
```

---

## MCP Configuration

Update `~/.claude.json`:

```json
{
  "mcpServers": {
    "obsidian": {
      "type": "stdio",
      "command": "/home/username/.local/bin/uvx",
      "args": ["obsidianpilot"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/path/to/your/vault"
      }
    }
  }
}
```

Replace:
- `/home/username/.local/bin/uvx` with your actual path
- `/path/to/your/vault` with your vault location

---

## Verification

After setup, verify with ObsidianPilot:

```bash
# List notes (should show templates)
# Use Claude Code and run:
# mcp__obsidian__list_notes_tool with directory=""

# Expected output:
# templates/project-note.md
# templates/spec-note.md
# templates/session-note.md
# templates/decision-note.md
# templates/consolidated-note.md
# templates/superseded-spec.md
```

---

## Usage Pattern

1. **Start a project:**
   - Copy `templates/project-note.md` → `projects/my-project.md`
   - Fill in project details

2. **Create initial spec:**
   - Copy `templates/spec-note.md` → `tasks/my-project-spec.md`
   - Link from project note

3. **Work session:**
   - Copy `templates/session-note.md` → `sessions/YYYY-MM-DD-topic.md`
   - Document as you work
   - Use `/notes-update` at end of session

4. **Make decision:**
   - Copy `templates/decision-note.md` → `decisions/adr-001-topic.md`
   - Document the why

5. **Spec evolves:**
   - Mark old spec as superseded (use `templates/superseded-spec.md` format)
   - Create new spec version with "What We Kept" section

6. **Cleanup:**
   - Run `/consolidate topic` when notes feel messy
   - Creates consolidated note with all knowledge

---

## Template Variable Substitutions

When copying templates, replace:
- `{{date}}` → Today's date (YYYY-MM-DD)
- `PROJECT_NAME` → Your project name
- `SPEC_NAME` → Your spec name
- `SESSION_TITLE` → Brief session description
- `DECISION_TITLE` → Decision title
- `TOPIC_NAME` → Topic being consolidated
- `ADR-XXX` → Next ADR number (e.g., ADR-001, ADR-002)

ObsidianPilot and Claude can help with these substitutions automatically when creating notes via `/notes-update` or `/consolidate`.
