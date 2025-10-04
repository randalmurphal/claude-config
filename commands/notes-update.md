---
name: notes-update
description: Update project documentation with current session findings, decisions, and discoveries
---

# /notes-update - Update Documentation with Current Findings

**USE THIS FOR:** Capturing session learnings and updating project documentation with current findings.

## What This Does
Analyzes the current session and updates relevant documentation:

1. **Extract Session Findings** - What was discovered, decided, or learned
2. **Identify Relevant Docs** - Which notes/specs need updates
3. **Update Documentation** - Add findings to appropriate notes
4. **Create New Notes** - If findings warrant new decisions/gotchas
5. **Update PRISM** - Store findings as memories
6. **Link Everything** - Connect new findings to existing knowledge

## Command

```
/notes-update [topic]
/notes-update              # Auto-detect from current session
```

## When to Use

✅ **DO use /notes-update for:**
- End of work session (capture what you learned)
- After discovering important gotchas
- After making architectural decisions
- When you've evolved a spec during implementation
- Before `/conduct-pause` (document progress)
- When you want to "save" current knowledge

❌ **DON'T use /notes-update for:**
- Brand new topics (no docs to update)
- Just starting work (nothing discovered yet)
- When you want full consolidation (use `/consolidate`)

## How It Works

### Phase 1: Session Analysis

```python
# Analyze current session messages
session_analysis = {
    "topic": detect_topic_from_session(),
    "findings": [],      # What was discovered
    "decisions": [],     # What was decided
    "gotchas": [],      # Problems encountered
    "changes": [],      # Spec/implementation changes
    "questions": []     # Open questions
}

# Extract from recent messages (last 50-100)
for message in recent_messages:
    # Look for discovery patterns
    if mentions_discovery(message):
        session_analysis["findings"].append(extract_finding(message))

    # Look for decisions
    if mentions_decision(message):
        session_analysis["decisions"].append(extract_decision(message))

    # Look for gotchas
    if mentions_problem(message):
        session_analysis["gotchas"].append(extract_gotcha(message))

    # Look for spec changes
    if mentions_change(message):
        session_analysis["changes"].append(extract_change(message))

# Present summary to user
print(f"""
Session Analysis for: {session_analysis['topic']}

📊 Findings ({len(session_analysis['findings'])}):
{format_findings(session_analysis['findings'][:5])}

🎯 Decisions ({len(session_analysis['decisions'])}):
{format_decisions(session_analysis['decisions'][:3])}

⚠️ Gotchas ({len(session_analysis['gotchas'])}):
{format_gotchas(session_analysis['gotchas'][:3])}

📝 Changes ({len(session_analysis['changes'])}):
{format_changes(session_analysis['changes'][:3])}
""")
```

### Phase 2: Find Relevant Documentation

```python
topic = session_analysis['topic']

# Find existing documentation
docs = {
    "project": obsidian.search(path=f"projects/{topic}*.md", status="current"),
    "specs": obsidian.search(path=f"tasks/{topic}*.md", status="current"),
    "decisions": obsidian.search(path="decisions/", tag=f"#project/{topic}"),
    "gotchas": obsidian.search(path="gotchas/", tag=f"#project/{topic}"),
    "session": obsidian.search(path="sessions/", tag=f"#project/{topic}",
                               modified_since="today")
}

# Determine what needs updating
updates_needed = []

if session_analysis['findings']:
    if docs['specs']:
        updates_needed.append({
            "type": "update_spec",
            "target": docs['specs'][0],
            "content": session_analysis['findings']
        })
    else:
        updates_needed.append({
            "type": "create_spec",
            "topic": topic,
            "content": session_analysis['findings']
        })

if session_analysis['decisions']:
    for decision in session_analysis['decisions']:
        updates_needed.append({
            "type": "create_adr",
            "decision": decision
        })

if session_analysis['gotchas']:
    updates_needed.append({
        "type": "update_gotchas",
        "content": session_analysis['gotchas']
    })

# Present plan to user
print(f"""
📋 Documentation Updates Needed:

{format_update_plan(updates_needed)}

Proceed with updates? [y/n]
""")
```

### Phase 3: Update Documentation

```python
# Create or update session note
session_note_path = f"sessions/{today}-{topic}.md"

if not obsidian.exists(session_note_path):
    # Create new session note from template
    session_note = create_from_template(
        "templates/session-note.md",
        {
            "PROJECT_NAME": topic,
            "SESSION_TITLE": session_analysis['summary'],
            "findings": session_analysis['findings'],
            "decisions": session_analysis['decisions'],
            "gotchas": session_analysis['gotchas']
        }
    )
    # Write to filesystem (fast)
    write_file(f"~/repos/obsidian-notes/{session_note_path}", session_note)
else:
    # Update existing session note
    obsidian.update_note(
        session_note_path,
        append_section("## Updated Findings", session_analysis['findings'])
    )

# Update project note
if docs['project']:
    project_note = docs['project'][0]

    # Add to history
    history_entry = f"- {today}: {session_analysis['summary']}"
    obsidian.update_note(project_note, append_to_section("## History", history_entry))

    # Update current status if changed
    if session_analysis['changes']:
        obsidian.update_note(
            project_note,
            replace_section("## Current Status", format_status(session_analysis['changes']))
        )

# Update or create spec
if session_analysis['findings'] and docs['specs']:
    spec_note = docs['specs'][0]

    # Check if findings warrant new version
    if is_major_change(session_analysis['changes']):
        print(f"""
⚠️ Major changes detected. Create new spec version?
Current: {spec_note.version}
Changes: {session_analysis['changes']}

[y] Create v{spec_note.version + 1}
[n] Update current spec
[s] Skip
""")

        choice = get_user_choice()

        if choice == 'y':
            create_new_spec_version(spec_note, session_analysis)
        elif choice == 'n':
            update_spec(spec_note, session_analysis['findings'])
    else:
        # Minor updates - just append
        update_spec(spec_note, session_analysis['findings'])

# Create ADRs for decisions
for decision in session_analysis['decisions']:
    adr_number = get_next_adr_number(topic)
    adr_path = f"decisions/adr-{adr_number:03d}-{slugify(decision['title'])}.md"

    adr_content = create_from_template(
        "templates/decision-note.md",
        {
            "ADR_NUMBER": f"{adr_number:03d}",
            "DECISION_TITLE": decision['title'],
            "PROJECT_NAME": topic,
            "context": decision['context'],
            "decision": decision['decision'],
            "alternatives": decision.get('alternatives', []),
            "consequences": decision.get('consequences', [])
        }
    )

    # Write directly to filesystem (fast)
    write_file(f"~/repos/obsidian-notes/{adr_path}", adr_content)

# Update gotchas
if session_analysis['gotchas']:
    gotcha_path = f"gotchas/{topic}-gotchas.md"

    if obsidian.exists(gotcha_path):
        # Append to existing
        obsidian.update_note(gotcha_path, append_gotchas(session_analysis['gotchas']))
    else:
        # Create new gotchas note
        mkdir_p(f"~/repos/obsidian-notes/gotchas")
        gotcha_note = f"""---
topic: {topic}
tags: [gotcha, topic/{topic}]
created: {today}
---

# {topic}: Known Gotchas

{format_gotchas_list(session_analysis['gotchas'])}
"""
        write_file(f"~/repos/obsidian-notes/{gotcha_path}", gotcha_note)
```

### Phase 4: PRISM Integration

```python
# Store findings in PRISM
for finding in session_analysis['findings']:
    prism.store_memory(
        content=finding['description'],
        tier="ACTIVE",
        memory_type="discovery",
        related_to=[topic],
        project_id=current_project,
        session_id=current_session,
        metadata={
            "obsidian_note": session_note_path,
            "date": today
        }
    )

# Store decisions as ADRs
for decision in session_analysis['decisions']:
    prism.store_adr(
        decision=decision['title'],
        context=decision['context'],
        alternatives_considered=decision.get('alternatives', []),
        consequences=decision.get('consequences', []),
        status="accepted",
        project_id=current_project,
        session_id=current_session
    )

# Store gotchas
for gotcha in session_analysis['gotchas']:
    prism.store_memory(
        content=gotcha['description'],
        tier="ACTIVE",
        memory_type="gotcha",
        related_to=[topic],
        frustration_score=gotcha.get('severity', 0.7),
        project_id=current_project,
        session_id=current_session,
        metadata={
            "obsidian_note": gotcha_path,
            "solution": gotcha.get('solution')
        }
    )
```

### Phase 5: Report

```python
print(f"""
✅ Documentation Updated: {topic}

📝 Notes Updated:
- Session: [[{session_note_path}]]
{f"- Project: [[{docs['project'][0].path}]]" if docs['project'] else ""}
{f"- Spec: [[{docs['specs'][0].path}]]" if docs['specs'] else ""}

📚 Notes Created:
{format_created_notes(created_notes)}

🧠 PRISM Storage:
- {len(session_analysis['findings'])} findings → ACTIVE tier
- {len(session_analysis['decisions'])} ADRs stored
- {len(session_analysis['gotchas'])} gotchas → ACTIVE tier

🔗 Links Added:
- Session note linked to project
- ADRs linked to session and project
- Gotchas linked to topic

Next Steps:
- Review session note: [[{session_note_path}]]
- Consider `/consolidate {topic}` if multiple spec versions exist
""")
```

## Example Usage

### Scenario 1: End of Implementation Session

```bash
# After working on auth system
/notes-update auth

# Output:
Session Analysis for: auth

📊 Findings (3):
1. JWT secret must be 256+ bits for HS256
2. Refresh tokens need separate Redis key prefix
3. Token validation adds ~5ms latency per request

🎯 Decisions (2):
1. Use bcrypt rounds=10 (balance security/performance)
2. Refresh token rotation every 24 hours

⚠️ Gotchas (1):
1. Redis connection pool exhausted with >100 concurrent users

📋 Documentation Updates Needed:
- Update [[tasks/auth-spec-v2.md]] with findings
- Create [[decisions/adr-004-bcrypt-rounds.md]]
- Create [[decisions/adr-005-token-rotation.md]]
- Update [[gotchas/auth-gotchas.md]]
- Create session note: [[sessions/2025-10-03-auth-implementation.md]]

Proceed with updates? [y]

✅ Documentation Updated: auth

📝 Notes Updated:
- Session: [[sessions/2025-10-03-auth-implementation.md]]
- Project: [[projects/auth.md]]
- Spec: [[tasks/auth-spec-v2.md]]

📚 Notes Created:
- [[decisions/adr-004-bcrypt-rounds.md]]
- [[decisions/adr-005-token-rotation.md]]

🧠 PRISM Storage:
- 3 findings → ACTIVE tier
- 2 ADRs stored
- 1 gotcha → ACTIVE tier
```

### Scenario 2: After Discovery Phase

```bash
# After exploring payment integration options
/notes-update payments

# Detects major findings, suggests creating initial spec
# Creates session note documenting exploration
# Stores all findings in PRISM
```

### Scenario 3: Spec Evolution During Implementation

```bash
# Implemented auth, discovered spec needs changes
/notes-update auth

# Output:
⚠️ Major changes detected. Create new spec version?
Current: v2
Changes:
- Token expiry changed from 15min to 5min (security requirement)
- Added token refresh endpoint

[y] Create v3
[n] Update current spec
[s] Skip

> y

Creating auth-spec-v3.md...
Marking auth-spec-v2.md as superseded...
Extracting "What We Kept" from v2...

✅ Created [[tasks/auth-spec-v3.md]]
✅ Updated [[tasks/auth-spec-v2.md]] (marked superseded)
✅ Updated [[projects/auth.md]] (links to v3)
```

## Technical Implementation

**MCP Server:** ObsidianPilot - direct filesystem access for instant operations.

**File Operations:**
- **Read:** ObsidianPilot MCP (session analysis, doc discovery with SQLite search)
- **Write:** ObsidianPilot MCP (instant - direct filesystem access)
- **Directory Creation:** ObsidianPilot or direct filesystem (both instant)

**Session Analysis:** Scans last 50-100 messages for patterns indicating findings/decisions/gotchas.

## Integration with Other Commands

### With `/consolidate`

```bash
# Work session with multiple iterations
/notes-update auth         # Capture findings after each iteration

# End of day - clean up accumulated notes
/consolidate auth         # Make everything perfect
```

### With `/notes-start`

```bash
/notes-start auth         # Load context
# Work happens...
/notes-update auth         # Save findings

# Next session
/notes-start auth         # Previous findings now part of context
```

### With `/conduct`

```bash
# During orchestration
/conduct "Implement auth system"

# At phase boundaries
/notes-update auth         # Capture phase learnings

# Before pausing
/conduct-pause
/notes-update auth         # Document progress
```

## What Gets Created/Updated

**Always:**
- Session note (today's work)
- PRISM memories (findings, decisions, gotchas)

**If Needed:**
- Project note (history, status)
- Spec note (updates or new version)
- ADR notes (architectural decisions)
- Gotcha notes (problems and solutions)

## Auto-Detection Logic

If no topic provided:
1. Recent Obsidian activity (most edited topic today)
2. Current working directory (project name)
3. Session context (mentioned topics)
4. Ask user if ambiguous

## Safety

**User confirmation required for:**
- Creating new spec version (major changes)
- Major structural changes

**Automatic:**
- Session note creation/update
- Project note history updates
- ADR creation
- Gotcha documentation
- PRISM storage

## Quick Reference

**Update docs for current topic:**
```bash
/notes-update
```

**Update docs for specific topic:**
```bash
/notes-update auth
```

**Preview what would be updated (dry run):**
```bash
/notes-update auth --preview
```

---

**Bottom Line:**
Use `/notes-update` at the end of work sessions to capture findings, decisions, and gotchas. It analyzes your session, updates relevant documentation, creates ADRs for decisions, and stores everything in PRISM. Keeps documentation current without manual note-taking during work.
