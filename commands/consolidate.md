---
name: consolidate
description: Comprehensive note consolidation - scan all notes on a topic, fix contradictions, update specs, reorganize structure. Uses as many tokens as needed to make notes perfect.
---

# /consolidate - Nuclear Option for Perfect Notes

**USE THIS FOR:** Making all Obsidian notes on a topic 100% accurate, organized, and consolidated.

## What This Does

Thorough, token-unlimited analysis and consolidation of all notes related to a topic:

1. **Scan Everything** - Find all notes (current, superseded, draft, archived)
2. **Detect Contradictions** - Find conflicting information across notes
3. **Determine Truth** - Figure out what's current vs outdated
4. **Consolidate Knowledge** - Extract valuable insights from all versions
5. **Reorganize Structure** - Split/merge notes as needed
6. **Update Specs** - Ensure all specs are current and correct
7. **Clean Links** - Fix broken references, update project notes
8. **Store in PRISM** - Save consolidated knowledge as ANCHOR memories

**This uses as many tokens as it takes to get it right.**

## Technical Implementation

**MCP Server:** ObsidianPilot - direct filesystem access with SQLite FTS5 indexing (100-1000x faster than REST API).

**File Operations:**
- **Read:** ObsidianPilot MCP (intelligent queries, frontmatter parsing, SQLite FTS5 search)
- **Write:** ObsidianPilot MCP (instant - direct filesystem access)
- **Search:** SQLite FTS5 indexing (<0.5s even on large vaults)
- **Directory Creation:** Direct or via MCP (both instant)

## Command

```
/consolidate [topic]
/consolidate            # Auto-detect topic from current session
```

## When to Use

✅ **DO use /consolidate for:**
- After multiple spec iterations on same topic
- When notes feel messy or contradictory
- Before major implementation work
- After discovering old notes are misleading
- End of day cleanup for active topics
- Before sharing project with others

❌ **DON'T use /consolidate for:**
- Brand new topics (nothing to consolidate)
- Quick sessions with no note evolution
- When you just want to read notes (use `/notes-start`)

## How It Works

### Phase 1: Discovery & Analysis

```python
# Auto-detect topic or use provided argument
topic = detect_topic_from_session() or provided_topic

# Find ALL notes related to topic
notes = obsidian.search(
    tags=[f"#project/{topic}", f"#topic/{topic}"],
    OR=True
)

# Group by status
current_notes = filter(status="current")
superseded_notes = filter(status="superseded")
draft_notes = filter(status="draft")
archived_notes = filter(status="archived")

# Report findings
print(f"""
Found {len(notes)} notes on topic: {topic}
- Current: {len(current_notes)}
- Superseded: {len(superseded_notes)}
- Draft: {len(draft_notes)}
- Archived: {len(archived_notes)}
""")
```

### Phase 2: Contradiction Detection

```python
# Read ALL notes thoroughly
for note in all_notes:
    content = obsidian.read_note(note)
    extract_claims(content)

# Find contradictions
contradictions = []
for claim1, claim2 in combinations(all_claims, 2):
    if contradicts(claim1, claim2):
        contradictions.append({
            "claim1": claim1,
            "claim2": claim2,
            "source1": claim1.source_note,
            "source2": claim2.source_note,
            "severity": assess_severity()
        })

# Report contradictions
if contradictions:
    print(f"""
⚠️ Found {len(contradictions)} contradictions:

HIGH SEVERITY:
- Auth spec v1 says "use sessions" (superseded)
- Auth spec v2 says "use JWT" (current)
- Decision needed: Mark v1 as explicitly superseded

MEDIUM SEVERITY:
- Session note says "4 workers optimal"
- Config file has 6 workers
- Decision needed: Which is correct?
""")
```

### Phase 3: Determine Current Truth

```python
# For each contradiction, determine truth
resolutions = []

for contradiction in contradictions:
    # Check note status
    if contradiction['source1']['status'] == 'current':
        truth = contradiction['claim1']
    elif contradiction['source2']['status'] == 'current':
        truth = contradiction['claim2']
    else:
        # Both superseded or unclear - ask user
        print(f"""
Unclear which is correct:
1. {contradiction['claim1']} (from {contradiction['source1']})
2. {contradiction['claim2']} (from {contradiction['source2']})

Which is correct? [1/2/neither/unsure]
""")
        user_input = get_user_resolution()
        truth = resolve_from_user_input(user_input)

    resolutions.append({
        "contradiction": contradiction,
        "resolution": truth,
        "action": "update_note" or "mark_superseded"
    })
```

### Phase 4: Knowledge Extraction

```python
# Extract valuable knowledge from ALL notes
knowledge_base = {
    "core_concepts": [],      # Unchanged across versions
    "evolution": [],          # How understanding evolved
    "lessons_learned": [],    # What failed and why
    "current_approach": {},   # What we're doing now
    "gotchas": [],           # Pain points discovered
    "decisions": []          # Key decisions made
}

# Process each note
for note in all_notes:
    if note.status == "current":
        # Extract current approach
        knowledge_base["current_approach"].update(
            extract_approach(note)
        )

    if note.status == "superseded":
        # Extract what's still valid
        still_valid = extract_still_valid_sections(note)
        knowledge_base["core_concepts"].extend(still_valid)

        # Extract why it was abandoned
        lessons = extract_abandonment_reasons(note)
        knowledge_base["lessons_learned"].extend(lessons)

    # Extract gotchas from all notes
    knowledge_base["gotchas"].extend(extract_gotchas(note))

    # Track evolution
    if note.version:
        knowledge_base["evolution"].append({
            "version": note.version,
            "date": note.date,
            "key_changes": extract_changes(note),
            "why": extract_rationale(note)
        })
```

### Phase 5: Structural Reorganization

```python
# Decide if notes should be split/merged/reorganized
recommendations = analyze_structure(all_notes, knowledge_base)

# Example recommendations:
"""
📋 Structural Recommendations:

MERGE:
- auth-spec-v1.md (superseded)
- auth-spec-v2.md (current)
- auth-decisions.md
→ INTO: auth-consolidated.md (single source of truth)

SPLIT:
- backend-implementation.md (too large)
→ INTO:
  - backend-api-endpoints.md
  - backend-database-schema.md
  - backend-auth-middleware.md

UPDATE:
- project-overview.md → Update links to point to consolidated notes
- sessions/2025-10-01-auth.md → Mark as referencing outdated spec

DELETE:
- auth-scratch.md (draft, abandoned)
- old-approach.md (superseded, no valuable content)
"""

# Execute reorganization with user approval
if user_approves(recommendations):
    execute_restructuring(recommendations)
```

### Phase 6: Consolidation & Updates

```python
# Create consolidated note
consolidated = create_note(f"{topic}-consolidated.md", content=f"""
---
status: consolidated
topic: {topic}
consolidates: {[all note links]}
created: {today}
updated: {today}
---

# {topic}: Consolidated Knowledge

**Current Implementation:** [[{current_spec_link}]]

## What We Know (Across All Versions)

{format_core_concepts(knowledge_base['core_concepts'])}

## Current Approach

{format_current_approach(knowledge_base['current_approach'])}

## Evolution Timeline

{format_evolution(knowledge_base['evolution'])}

## Lessons Learned

{format_lessons(knowledge_base['lessons_learned'])}

## Known Gotchas

{format_gotchas(knowledge_base['gotchas'])}

## Key Decisions

{format_decisions(knowledge_base['decisions'])}

## Related Notes
- Current spec: [[{current_spec}]]
- Sessions: {[session links]}
- Decisions: {[decision links]}
""")

# Update current spec with consolidation
current_spec.add_section("""
## Consolidated Knowledge

See [[{topic}-consolidated]] for full context across all versions.

This spec builds on previous versions. Key points carried forward:
{list_key_points_from_previous_versions()}
""")

# Update superseded notes
for note in superseded_notes:
    note.add_section("""
## Still Valid

These concepts were carried to [[{current_spec}]]:
{extract_still_valid_sections(note)}

See [[{topic}-consolidated]] for full historical context.
""")
    note.status = "superseded"
    note.metadata["superseded-by"] = current_spec.path
    note.metadata["superseded-date"] = today
```

### Phase 7: Link Cleanup

```python
# Find all notes that link to any topic notes
referring_notes = find_notes_linking_to(all_notes)

# Update links to point to current/consolidated
for note in referring_notes:
    for link in note.links:
        if link.target in superseded_notes:
            # Suggest updating to current
            print(f"""
{note.path} links to superseded note:
- Current: [[{link.target}]] (superseded)
- Should be: [[{current_spec}]] (current)

Update link? [y/n]
""")
            if user_confirms():
                note.replace_link(link.target, current_spec)

        # Update project notes
        if note.path.startswith("projects/"):
            ensure_project_note_current(note, topic)
```

### Phase 8: PRISM Integration

```python
# Store consolidated knowledge in PRISM
for concept in knowledge_base['core_concepts']:
    prism.store_memory(
        content=concept['description'],
        tier="ANCHORS",  # Permanent storage
        memory_type="architectural_decision",
        related_to=[topic],
        project_id=current_project,
        metadata={
            "obsidian_note": consolidated.path,
            "confidence": "verified",
            "source": "consolidation"
        }
    )

# Store lessons learned
for lesson in knowledge_base['lessons_learned']:
    prism.store_memory(
        content=lesson['what_failed'] + " → " + lesson['why'],
        tier="ACTIVE",
        memory_type="gotcha",
        related_to=[topic],
        frustration_score=lesson.get('severity', 0.5),
        metadata={
            "obsidian_note": consolidated.path,
            "version": lesson.get('version')
        }
    )

# Store ADRs
for decision in knowledge_base['decisions']:
    prism.store_adr(
        decision=decision['what'],
        context=decision['context'],
        alternatives_considered=decision.get('alternatives', []),
        consequences=decision.get('consequences', []),
        status="accepted",
        related_symbols=decision.get('code_references', []),
        project_id=current_project,
        session_id=current_session
    )
```

### Phase 9: Validation & Report

```python
# Validate consolidation
validation = {
    "contradictions_resolved": len(resolutions),
    "notes_consolidated": len(all_notes),
    "knowledge_items_extracted": sum(len(v) for v in knowledge_base.values()),
    "links_fixed": count_links_fixed,
    "prism_memories_stored": count_prism_stores,
    "structural_changes": len(recommendations)
}

# Generate report
print(f"""
✅ Consolidation Complete: {topic}

📊 Summary:
- Scanned {len(all_notes)} notes
- Resolved {validation['contradictions_resolved']} contradictions
- Extracted {validation['knowledge_items_extracted']} knowledge items
- Fixed {validation['links_fixed']} broken links
- Stored {validation['prism_memories_stored']} memories in PRISM

📝 Structural Changes:
{format_structural_changes(recommendations)}

📚 Created/Updated:
- [[{consolidated.path}]] - Consolidated knowledge hub
- [[{current_spec.path}]] - Updated with "What We Kept" sections
- {len(superseded_notes)} superseded notes marked with "Still Valid"
- {len(project_notes)} project notes updated

🧠 PRISM Integration:
- {len(knowledge_base['core_concepts'])} concepts → ANCHORS tier
- {len(knowledge_base['lessons_learned'])} lessons → ACTIVE tier
- {len(knowledge_base['decisions'])} ADRs stored

Next Steps:
- Review [[{consolidated.path}]] for accuracy
- Use `/notes-start {topic}` to load clean context
- Consider archiving very old notes (>90 days superseded)

Token usage: {token_count} tokens
""")
```

## Example Usage

### Scenario 1: Auth System Evolved Over Time

```bash
# You've iterated on auth design 3 times
# Notes are scattered and contradictory

/consolidate auth

# Output:
Found 8 notes on topic: auth
- Current: 2 (auth-spec-v3.md, auth-implementation.md)
- Superseded: 2 (auth-spec-v1.md, auth-spec-v2.md)
- Draft: 1 (auth-oauth-exploration.md)
- Sessions: 3 (various dates)

⚠️ Found 5 contradictions:
1. V1 says "use sessions", v3 says "use JWT"
2. V2 mentions "redis for sessions", v3 doesn't use redis
3. Session note says "bcrypt rounds=12", code has rounds=10

Resolving contradictions...
- V1 & V2 marked as superseded (expected)
- Bcrypt rounds: code is correct (10), updating note

Extracting knowledge from all versions...
✅ 23 core concepts extracted
✅ 5 lessons learned documented
✅ 3 key decisions captured

Creating consolidated note...
✅ Created: auth-consolidated.md

Updating structure...
✅ Updated auth-spec-v3.md with "What We Kept" section
✅ Marked v1 and v2 with "Still Valid" sections
✅ Fixed 3 broken links in project notes

Storing in PRISM...
✅ 23 memories → ANCHORS tier
✅ 5 gotchas → ACTIVE tier
✅ 3 ADRs stored

Total: 127,000 tokens used
Consolidation complete!
```

### Scenario 2: Auto-Detect from Session

```bash
# Currently working on database migration
# Claude detects topic from session context

/consolidate

# Auto-detects "database-migration" from session
# Same thorough process as above
```

### Scenario 3: Find No Issues (Best Case)

```bash
/consolidate payments

# Output:
Found 3 notes on topic: payments
- Current: 1 (payments-spec.md)
- Sessions: 2 (recent work)

✅ No contradictions found
✅ Structure is clean
✅ All links valid

Notes are already well-organized!
Consider creating a consolidated note for historical context? [y/n]
```

## What Gets Created/Updated

**New Notes:**
- `{topic}-consolidated.md` - Central knowledge hub

**Updated Notes:**
- Current specs → Add "What We Kept" sections
- Superseded notes → Add "Still Valid" sections
- Project notes → Update links to current
- Session notes → Fix references to outdated specs

**PRISM Storage:**
- Core concepts → ANCHORS tier (permanent)
- Lessons learned → ACTIVE tier (gotchas)
- Decisions → ADR storage
- All linked to Obsidian notes

## Auto-Detection Logic

If no topic provided, detect from:
1. Recent session notes (last worked topic)
2. Current working directory (project name)
3. Recent Obsidian updates (most edited topic)
4. Ask user if ambiguous

## Integration with Other Commands

**Works with `/notes-start`:**
```bash
/consolidate auth    # Clean up notes
/notes-start auth    # Load clean context
# Now start work with perfect context
```

**Works with `/conduct`:**
```bash
/conduct-pause
/consolidate [topic]  # Clean up notes from session
/conduct-resume
```

**Works with PRISM:**
- Consolidation feeds PRISM memory
- Future sessions benefit from consolidated knowledge
- `/notes-start` queries both Obsidian + PRISM

## Token Budget

**No token limit on consolidation.** This command uses however many tokens it takes to:
- Read all notes thoroughly
- Detect all contradictions
- Extract all knowledge
- Create comprehensive consolidated notes
- Store everything in PRISM

Typical usage:
- Small topics (3-5 notes): 30k-50k tokens
- Medium topics (5-10 notes): 50k-100k tokens
- Large topics (10+ notes): 100k-200k tokens

**Worth it** because future sessions save tokens by having clean, consolidated context.

## Safety

**User confirmation required for:**
- Deleting notes (even drafts)
- Merging multiple notes into one
- Major structural changes
- Resolving ambiguous contradictions

**Automatic (no confirmation):**
- Reading notes
- Creating consolidated note
- Updating "What We Kept" sections
- Marking superseded notes
- Storing in PRISM
- Fixing broken links

## When NOT to Use

- ❌ Brand new topic with only 1-2 notes
- ❌ Notes are already clean and organized
- ❌ Quick lookup (use `/notes-start` instead)
- ❌ In the middle of implementation (finish first)

## Success Criteria

After `/consolidate`, the topic notes should be:
- ✅ No contradictions between notes
- ✅ Clear "current" vs "historical" distinction
- ✅ Consolidated knowledge hub exists
- ✅ All valuable insights preserved
- ✅ Links updated to point to current
- ✅ PRISM has all key knowledge
- ✅ Structure makes sense (no redundant notes)

**If any of these aren't true, consolidation continues until they are.**

---

**Bottom Line:**
Use `/consolidate` when you want notes to be **perfect**. It will use as many tokens as needed to scan everything, fix contradictions, extract knowledge, and make the notes a reliable source of truth. Then `/notes-start` gives you clean context to work with.
