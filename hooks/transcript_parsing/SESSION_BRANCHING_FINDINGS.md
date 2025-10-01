# Claude Code Session Branching: How It Actually Works

## Discovery Summary

Investigation of transcript files in `~/.claude/projects/[project-dir]/[session-uuid].jsonl`

---

## Session File Structure

### Entry Types Found

1. **Summary entries** (file header)
   - Type: `"summary"`
   - Contains: `leafUuid`, summary text
   - Purpose: Conversation summaries from previous sessions

2. **User messages**
   - Type: `"user"`
   - Has: `uuid`, `parentUuid`, `timestamp`, `isSidechain`
   - Content: String (text) OR Array (tool results)

3. **Assistant messages**
   - Type: `"assistant"`
   - Has: `uuid`, `parentUuid`, `timestamp`, `isSidechain`
   - Content: Array of blocks (thinking, text, tool_use)

4. **File history snapshots**
   - Type: `"file-history-snapshot"`
   - No `uuid` field
   - Purpose: Track file versions

---

## Conversation Branching (Within Same Session)

### Retry Branches

**What it is:** When a response fails (OAuth error, timeout), user can retry from same parent.

**Example from current session:**
```
Parent: 912ed541-911e-49f3-9f99-498d91173ebe (assistant, 23:28:47)
  ├─ Child 1: b0f4c02a-... (user, 23:32:00) → OAuth error
  └─ Child 2: 4ecae0b8-... (user, 23:36:09) → Continued conversation
```

**Both children:**
- Have IDENTICAL content (user typed same message)
- Have `isSidechain=False`
- Stored in SAME .jsonl file
- Different timestamps

**Detection:** Parent UUID appears in multiple messages' `parentUuid` field.

---

## Sub-Agent Work (Sidechains)

**What it is:** Parallel agent tasks running alongside main conversation.

**Example from current session:**
- 120 sidechain messages total
- 2 sidechain roots (both `isSidechain=True`, `parentUuid=None`)
  1. "Update Orchestration MCP documentation" (21 messages)
  2. "Update PRISM MCP documentation" (21 messages)

**Characteristics:**
- `isSidechain=True` for ALL messages in the chain
- Root has `parentUuid=None` (not connected to main conversation)
- Forms independent chain (agent's own back-and-forth)
- Stored in SAME .jsonl file as main session

**Detection:** Filter by `isSidechain=True` to separate from main conversation.

---

## Session Branching (New Session Files)

### How It Works

**Command:** `claude --resume <session-id>`

**Result:** Creates a NEW session file with:
- New session UUID
- Copy of conversation history UP TO that point
- Independent future messages

**Key Point:** Branched session is a SEPARATE .jsonl file, not in same file.

**Storage:**
```
~/.claude/projects/[project-dir]/
  ├─ 55653782-...-038628.jsonl  (original session)
  └─ abc12345-...-xyz789.jsonl  (branched session, if created)
```

### Session Files Don't Link to Each Other

**Found:**
- No `parentSessionId` field in entries
- No reference to original session UUID in branched file
- Summary entries at file start (from previous sessions)

**Implication:** Can't easily detect branched sessions from file inspection alone.

---

## Multi-Session Scenarios

### Concurrent Sessions (Git Worktrees)

**Setup:** Multiple Claude Code instances in different worktree directories.

**Result:**
- Each gets own session UUID
- Each has own .jsonl file
- Same project, different working directories
- NO cross-reference between sessions

### Continuation Sessions

**Setup:** Session runs out of context → user starts new session with `--continue`.

**Result:**
- New session UUID
- New .jsonl file
- Summary entries reference previous work
- No explicit link to parent session in metadata

---

## Transcript Parsing Implications

### For Single Session Analysis

**Easy:**
- Parse main conversation (filter `isSidechain=False`)
- Parse sub-agent work (filter `isSidechain=True`)
- Detect retry branches (multiple children of same parent)

**Structure:**
```python
messages = parse_transcript(session_file)

# Main conversation
main = [m for m in messages if not m.get('sidechain')]

# Sub-agent work
agents = [m for m in messages if m.get('sidechain')]

# Branching points
branches = find_multiple_children(messages)
```

### For Multi-Session Analysis

**Hard Problems:**

1. **No parent session link**
   - Can't programmatically find "test" branch from original session
   - Must rely on file timestamps, project directory, or user knowledge

2. **Correction clustering across sessions**
   - Should corrections in Branch A affect memories in Branch B?
   - Likely YES if both branches are production work
   - Likely NO if one branch is experimentation

3. **Sub-agent sessions**
   - Unknown if sub-agents create separate session files
   - Current evidence: Sub-agents use sidechains in SAME file
   - But may depend on how they're launched

**Practical Approach:**

```python
# Parse all sessions in project directory
project_dir = "~/.claude/projects/[project]/"
all_sessions = glob(f"{project_dir}/*.jsonl")

for session_file in all_sessions:
    messages = parse_transcript(session_file)
    corrections = detect_corrections(messages)

    # Store with session ID
    store_corrections(session_id, corrections)

# Cluster across ALL sessions
all_corrections = fetch_all_corrections(project_id)
patterns = cluster_corrections(all_corrections)
```

---

## Recommendations for Parser Implementation

### 1. Single-Session Mode (Default)
- Parse one session file
- Detect corrections in main conversation only
- Ignore sidechains for pattern detection (agent work, not user corrections)

### 2. Project-Wide Mode (Optional)
- Parse ALL .jsonl files in project directory
- Cluster corrections across all sessions
- Treat each session independently for frustration scoring
- Aggregate patterns project-wide

### 3. Sidechain Handling
- **Skip for correction detection** (not user-agent interaction)
- **Use for context** (what work was done in parallel)
- **Separate tier** (maybe store as context, not corrections)

### 4. Branch Detection
- **Within-session branches:** Detect via multiple children
- **Cross-session branches:** Can't reliably detect
- **Solution:** User specifies session IDs to analyze, or analyze all

### 5. Storage in PRISM

**Per-session corrections:**
```python
prism_store_memory(
    content="User corrected X 3 times",
    memory_type="correction",
    tier="ANCHORS",
    metadata={
        'session_id': 'abc123',
        'project_id': 'project-dir',
        'count': 3,
        'frustration': 0.9
    }
)
```

**Project-wide patterns:**
```python
prism_store_memory(
    content="NEVER use try/except pass - corrected across 5 sessions",
    memory_type="pattern",
    tier="ANCHORS",
    metadata={
        'project_id': 'project-dir',
        'session_count': 5,
        'total_corrections': 12,
        'avg_frustration': 0.85
    }
)
```

---

## Testing Structure

1. **Single session with retry branch**
   - Current session (55653782-...) has 1 retry branch
   - Both branches in same file
   - Easy to parse and detect

2. **Single session with sidechains**
   - Current session has 120 sidechain messages
   - 2 agent tasks (documentation updates)
   - Filter by `isSidechain` to separate

3. **Multiple session files** (unknown structure)
   - User mentioned "test" branch - separate file
   - No automatic way to find it
   - Need project-wide parsing approach

---

## What We CANNOT Determine

1. Where "test" branch session file is
   - No parent reference in session metadata
   - Would need to scan all .jsonl files for content match
   - Or rely on file timestamps (unreliable)

2. Whether sub-agents always use sidechains
   - Current evidence: YES (2 agent tasks = sidechains)
   - But may vary based on how agents are launched

3. Cross-session causality
   - Can't tell if Session B was branched from Session A
   - Can't tell if Session C was continuation of Session B
   - Summary entries suggest history, but no explicit link

---

## Next Steps for Other Agent

1. **Implement single-session parser first**
   - Parse main conversation
   - Detect corrections with frustration scoring
   - Store in PRISM

2. **Add project-wide clustering**
   - Scan all .jsonl files in project directory
   - Cluster similar corrections across sessions
   - Build pattern library

3. **Create slash command**
   - `/learn-from-session` - Analyze current session
   - `/learn-from-project` - Analyze all project sessions
   - Store high-frustration patterns as ANCHORS

4. **Hook integration**
   - PreToolUse: Query PRISM for violations before action
   - PostToolUse: Detect new corrections in current session
   - SessionEnd: Run full analysis and store patterns
