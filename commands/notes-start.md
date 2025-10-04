---
name: notes-start
description: Load complete context for a topic from Obsidian and PRISM before starting work. Auto-detects topic from session if not specified.
---

# /notes-start - Load Topic Context

**USE THIS FOR:** Loading all relevant context before starting work on a topic/project.

## What This Does

Intelligently loads complete context from Obsidian + PRISM:

1. **Auto-detect topic** from current session or use provided argument
2. **Query Obsidian** for all relevant notes (consolidated, current specs, decisions, sessions)
3. **Query PRISM** for related memories, decisions, gotchas
4. **Present clean context** with current state and history
5. **Surface gotchas** and known issues upfront
6. **Ready to work** with full knowledge

## Command

```
/notes-start [topic]
/notes-start              # Auto-detect from session
```

## When to Use

✅ **DO use /notes-start for:**
- Beginning work on an existing project
- Resuming work after time away
- Before major implementation
- When you need context but don't remember details
- After `/consolidate` to load clean context
- Starting a new session on familiar topic

❌ **DON'T use /notes-start for:**
- Brand new topics (no context to load)
- Middle of active session (you already have context)
- When you just want to consolidate notes (use `/consolidate`)

## How It Works

### Phase 1: Topic Detection

```python
# Auto-detect topic if not provided
if not topic_provided:
    # Check current working directory
    if is_in_project_dir():
        topic = extract_project_name(cwd)

    # Check recent Obsidian activity
    elif recent_obsidian_notes := get_recent_notes(hours=24):
        topic = extract_common_topic(recent_obsidian_notes)

    # Check session context
    elif session_mentions := extract_topics_from_messages():
        topic = most_common(session_mentions)

    # Ask user
    else:
        print("Available topics from recent notes:")
        for t in list_recent_topics():
            print(f"  - {t}")
        topic = input("Which topic? ")

print(f"📚 Loading context for: {topic}")
```

### Phase 2: Obsidian Query

```python
# Find consolidated knowledge hub
consolidated = obsidian.search(
    path=f"{topic}-consolidated.md"
) or obsidian.search(
    tag=f"#consolidated",
    content=f"topic: {topic}"
)

# Find current specs and implementations
current_notes = obsidian.search(
    tags=[f"#project/{topic}", f"#topic/{topic}"],
    status="current"
)

# Find recent sessions (last 30 days)
recent_sessions = obsidian.search(
    path="sessions/",
    tags=[f"#project/{topic}"],
    modified_since="30 days ago"
)

# Find key decisions
decisions = obsidian.search(
    path="decisions/",
    tags=[f"#project/{topic}"],
    status="current"
)

# Find known gotchas
gotchas = obsidian.search(
    path="gotchas/",
    tags=[f"#project/{topic}"]
)

print(f"""
Found in Obsidian:
- Consolidated note: {consolidated.path if consolidated else 'None'}
- Current specs: {len(current_notes)}
- Recent sessions: {len(recent_sessions)}
- Decisions: {len(decisions)}
- Gotchas: {len(gotchas)}
""")
```

### Phase 3: PRISM Query

```python
# Query PRISM for related memories
prism_memories = prism.retrieve_memories(
    query=f"topic:{topic} OR project:{topic}",
    session_id=current_session,
    limit=50,
    retrieval_mode="comprehensive"
)

# Get architectural decisions from PRISM
prism_adrs = prism.query_adrs(
    query=topic,
    session_id=current_session,
    status="accepted"
)

# Get known gotchas
prism_gotchas = prism.retrieve_memories(
    query=f"topic:{topic} gotchas OR problems OR failures",
    session_id=current_session,
    limit=20
)

print(f"""
Found in PRISM:
- Memories: {len(prism_memories)}
- ADRs: {len(prism_adrs)}
- Gotchas: {len(prism_gotchas)}
""")
```

### Phase 4: Context Synthesis

```python
# Read and synthesize all sources
context = {
    "topic": topic,
    "current_state": {},
    "history": {},
    "decisions": [],
    "gotchas": [],
    "next_steps": []
}

# Read consolidated note if exists
if consolidated:
    consolidated_content = obsidian.read_note(consolidated.path)
    context["current_state"] = extract_current_approach(consolidated_content)
    context["history"] = extract_evolution(consolidated_content)
    context["gotchas"].extend(extract_gotchas(consolidated_content))

# Read current spec
if current_notes:
    main_spec = current_notes[0]  # Most recent
    spec_content = obsidian.read_note(main_spec.path)
    context["current_state"]["spec"] = main_spec.path
    context["current_state"]["details"] = extract_key_points(spec_content)

    # Check for "What We Kept" section
    if kept_section := extract_section(spec_content, "What We Kept"):
        context["history"]["carried_forward"] = kept_section

# Extract decisions
for decision_note in decisions:
    decision_content = obsidian.read_note(decision_note.path)
    context["decisions"].append({
        "title": decision_note.title,
        "decision": extract_decision(decision_content),
        "rationale": extract_rationale(decision_content),
        "source": decision_note.path
    })

# Combine Obsidian + PRISM gotchas
all_gotchas = set()
for gotcha_note in gotchas:
    content = obsidian.read_note(gotcha_note.path)
    all_gotchas.update(extract_gotchas(content))
for memory in prism_gotchas:
    all_gotchas.add(memory['content'])
context["gotchas"] = list(all_gotchas)

# Merge PRISM ADRs
for adr in prism_adrs:
    if not any(d['title'] == adr['decision'] for d in context['decisions']):
        context["decisions"].append({
            "title": adr['decision'],
            "decision": adr['decision'],
            "rationale": adr['context'],
            "source": "PRISM"
        })

# Extract next steps from recent sessions
if recent_sessions:
    latest_session = recent_sessions[0]
    session_content = obsidian.read_note(latest_session.path)
    context["next_steps"] = extract_next_steps(session_content)
    context["last_worked"] = latest_session.modified_date
```

### Phase 5: Present Context

```python
# Generate comprehensive context summary
print(f"""
{'='*60}
📚 CONTEXT LOADED: {topic}
{'='*60}

📍 Current State:
{format_current_state(context['current_state'])}

📅 Last Worked: {context.get('last_worked', 'Unknown')}

🎯 Current Spec: [[{context['current_state'].get('spec', 'None')}]]

🏗️ Architecture:
{format_architecture(context['current_state'])}

📋 Key Decisions ({len(context['decisions'])}):
{format_decisions(context['decisions'], limit=5)}
{f"  ... and {len(context['decisions']) - 5} more" if len(context['decisions']) > 5 else ""}

⚠️ Known Gotchas ({len(context['gotchas'])}):
{format_gotchas(context['gotchas'], limit=10)}
{f"  ... and {len(context['gotchas']) - 10} more" if len(context['gotchas']) > 10 else ""}

📖 Evolution:
{format_evolution(context['history'], limit=3)}

🔗 Key Resources:
{format_resources(consolidated, current_notes, decisions)}

🎯 Next Steps:
{format_next_steps(context['next_steps'])}

{'='*60}
Ready to work on {topic}!
{'='*60}

What would you like to do?
""")
```

## Example Usage

### Scenario 1: Resume Work on Auth System

```bash
/notes-start auth

# Output:
============================================================
📚 CONTEXT LOADED: auth
============================================================

📍 Current State:
Implementing JWT-based authentication with refresh tokens.
Using bcrypt for password hashing (rounds=10).
Token expiry: access=15min, refresh=7days.

📅 Last Worked: 2025-10-01 (2 days ago)

🎯 Current Spec: [[tasks/auth-spec-v3]]

🏗️ Architecture:
- JWT tokens for stateless auth
- Redis for refresh token storage
- Middleware validates on every request
- /auth/login returns access + refresh tokens
- /auth/refresh exchanges refresh for new access

📋 Key Decisions (3):
1. Use JWT instead of sessions (distributed system needs)
   → See [[decisions/adr-001-session-vs-jwt]]
2. Bcrypt rounds=10 (balance security vs performance)
   → See [[decisions/adr-002-bcrypt-rounds]]
3. Refresh token rotation for security
   → See [[decisions/adr-003-refresh-rotation]]

⚠️ Known Gotchas (5):
1. JWT secret MUST be in environment, not hardcoded
2. Token expiry must be shorter than refresh window
3. Redis connection pool needs max=20 for load
4. Bcrypt is CPU-intensive, use async workers
5. HTTPS required for production (token security)

📖 Evolution:
v1: Session-based auth (abandoned - doesn't work distributed)
v2: JWT without refresh (abandoned - security concern)
v3: JWT + refresh tokens (current)

🔗 Key Resources:
- Consolidated: [[auth-consolidated]]
- Spec: [[tasks/auth-spec-v3]]
- Decisions: [[decisions/adr-001]], [[decisions/adr-002]], [[decisions/adr-003]]
- Sessions: [[sessions/2025-10-01-auth]], [[sessions/2025-09-28-auth]]

🎯 Next Steps:
1. Implement refresh token rotation
2. Add token validation tests
3. Set up Redis connection pool

============================================================
Ready to work on auth!
============================================================

What would you like to do?
```

### Scenario 2: Auto-Detect from Session

```bash
# User mentions "Let's work on the payment system"

/notes-start

# Detects "payment" from session context
# Loads payment-related context automatically
```

### Scenario 3: No Context Available (New Topic)

```bash
/notes-start new-feature

# Output:
📚 Loading context for: new-feature

Found in Obsidian:
- Consolidated note: None
- Current specs: 0
- Recent sessions: 0
- Decisions: 0
- Gotchas: 0

Found in PRISM:
- Memories: 0
- ADRs: 0
- Gotchas: 0

============================================================
📚 CONTEXT LOADED: new-feature
============================================================

⚠️ No existing context found for "new-feature"

This appears to be a new topic. Consider:
1. Starting with `/prelude` for discovery
2. Creating initial spec in Obsidian
3. Documenting decisions as you go

Would you like to create a new project note? [y/n]
============================================================
```

### Scenario 4: Multiple Topics Available

```bash
/notes-start

# Can't auto-detect clear topic

Available topics from recent notes:
  - auth (last worked: 2 days ago)
  - payments (last worked: 1 week ago)
  - notifications (last worked: 2 weeks ago)

Which topic? auth

# Proceeds to load auth context
```

## Integration with Other Commands

### With `/consolidate`

```bash
# Clean up messy notes first
/consolidate auth

# Then load clean context
/notes-start auth

# Now work with perfect context
```

### With `/conduct`

```bash
# Load context before starting orchestration
/notes-start backend-api

# Start implementation with full context
/conduct "Implement the backend API"
```

### With `/prelude`

```bash
# Notes-start loads existing knowledge
/notes-start auth

# Prelude discovers NEW requirements
/prelude "Add OAuth support to auth"
```

## What Gets Displayed

**Always:**
- Current state summary
- Current spec link
- Key decisions (top 5)
- Known gotchas (top 10)
- Last worked date

**If Available:**
- Consolidated knowledge hub link
- Evolution timeline
- Next steps from last session
- Recent session links
- Related resources

**Smart Limits:**
- Decisions: Show 5, mention if more exist
- Gotchas: Show 10, mention if more exist
- Evolution: Show last 3 major changes
- Sessions: Link most recent 3

**Prevents information overload while ensuring critical context is visible.**

## Auto-Detection Priority

When no topic specified:

1. **Working Directory** - If in project dir, use project name
2. **Recent Obsidian** - Most edited topic in last 24 hours
3. **Session Context** - Topic mentioned in recent messages
4. **User Selection** - Show list, let user choose

## PRISM + Obsidian Synergy

**How they complement:**

**Obsidian:**
- Structured notes with links
- Explicit specs and decisions
- Organized by folders/tags
- Human-readable

**PRISM:**
- Semantic memory search
- Cross-session learning
- Automated memory promotion
- AI-optimized retrieval

**Together:**
- PRISM finds relevant memories
- Memories link to Obsidian notes
- Read Obsidian for details
- Get both semantic + structured context

## Performance

**Typical load times:**
- Small topic (3-5 notes): 2-5 seconds
- Medium topic (5-10 notes): 5-10 seconds
- Large topic (10+ notes): 10-20 seconds

**Token usage:**
- Small: 5k-10k tokens
- Medium: 10k-20k tokens
- Large: 20k-40k tokens

**Worth it because:**
- Prevents working with outdated info
- Surfaces gotchas before they bite
- Loads complete context once
- Saves tokens during actual work

## Error Handling

### Topic Not Found

```bash
/notes-start nonexistent

# Output:
📚 Loading context for: nonexistent

Found in Obsidian: 0 notes
Found in PRISM: 0 memories

⚠️ No context found for "nonexistent"

Did you mean:
- auth (85% match)
- oauth (75% match)
- authentication (70% match)

Or is this a new topic? [select/new]
```

### Obsidian Connection Failed

```bash
/notes-start auth

# Output:
📚 Loading context for: auth

⚠️ Could not connect to Obsidian
Error: Connection refused on port 27123

Falling back to PRISM only...

Found in PRISM:
- Memories: 15
- ADRs: 3
- Gotchas: 5

[Shows context from PRISM only]

Fix: Ensure Obsidian Local REST API is running
```

### Ambiguous Topic

```bash
/notes-start api

# Output:
📚 Loading context for: api

Found multiple potential matches:
1. backend-api (12 notes, last worked 2 days ago)
2. frontend-api (5 notes, last worked 1 week ago)
3. api-gateway (3 notes, last worked 2 weeks ago)

Which topic? [1/2/3/all/cancel]
```

## Safety

**Read-only operation** - Never modifies notes, only reads context.

**Privacy:** Only loads context for topics you're working on (no broad scanning).

**Permissions:** Requires Obsidian MCP server + PRISM access.

## Quick Reference

**Load context for specific topic:**
```bash
/notes-start auth
```

**Auto-detect topic:**
```bash
/notes-start
```

**See what would be loaded (dry run):**
```bash
/notes-start auth --preview
```

**Load context and start session note:**
```bash
/notes-start auth --create-session
```

---

**Bottom Line:**
Use `/notes-start` at the beginning of work to load complete, accurate context from both Obsidian and PRISM. Prevents working with outdated info and surfaces known gotchas upfront. After `/consolidate`, this gives you perfectly clean context to work with.
