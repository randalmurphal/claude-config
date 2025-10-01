# Claude Code Transcript Parsing Guide

**Location:** `~/.claude/projects/[project-dir]/[session-uuid].jsonl`

**Format:** JSONL (JSON Lines) - one JSON object per line

---

## Entry Types

### 1. User Messages (`type: "user"`)

```json
{
  "type": "user",
  "uuid": "uuid-here",
  "timestamp": "2025-09-30T19:36:00.000Z",
  "sessionId": "session-uuid",
  "message": {
    "role": "user",
    "content": "Can you fix this bug?"
    // OR
    "content": [
      {
        "tool_use_id": "toolu_xyz",
        "type": "tool_result",
        "content": "tool output here",
        "is_error": false
      }
    ]
  }
}
```

**Key Fields:**
- `message.content` - Can be STRING (text) or ARRAY (tool results)
- Extract text for analysis, ignore tool result entries

### 2. Assistant Messages (`type: "assistant"`)

```json
{
  "type": "assistant",
  "uuid": "uuid-here",
  "timestamp": "2025-09-30T19:36:05.000Z",
  "message": {
    "id": "msg_xyz",
    "role": "assistant",
    "content": [
      {"type": "thinking", "thinking": "internal reasoning here"},
      {"type": "text", "text": "user-visible response"},
      {"type": "tool_use", "id": "toolu_abc", "name": "Bash", "input": {...}}
    ]
  }
}
```

**Key Fields:**
- `message.content` - ALWAYS an array of blocks
- **Blocks:**
  - `thinking` - My internal reasoning (NOT shown to user)
  - `text` - What I say to user
  - `tool_use` - Tool calls I made

### 3. File Snapshots (`type: "file-history-snapshot"`)

Skip these - just tracking file versions.

---

## What to Extract

### Correction Patterns

**Signals:**
- User says: "no", "don't", "wrong", "fix", "actually", "not like that"
- Appears AFTER assistant action
- High frustration: "i told you", "again", "remember"

**Structure:**
```python
{
  'user_message': "No, don't use try/except pass",
  'timestamp': "...",
  'previous_assistant_actions': [
    {
      'text': "I'll add error handling",
      'tools': [{'name': 'Write', 'input': {...}}]
    }
  ],
  'frustration_score': 0.8  # if "again" or "told you"
}
```

**Detection:**
1. Parse user message content
2. Check for correction keywords
3. Look back 1-3 messages for assistant actions
4. Extract what was corrected

### Approval Patterns

**Signals:**
- User says: "good", "yes", "perfect", "great", "right"
- Short responses (≤5 words)
- User moves on to new topic

**Structure:**
```python
{
  'user_message': "Perfect",
  'approved_action': "previous assistant text",
  'approved_tools': [tool uses],
  'timestamp': "..."
}
```

### Decision Moments

**Signals:**
- "let's use", "we'll use", "decided to", "going with"
- Both user AND assistant can make decisions
- Often followed by implementation

**Structure:**
```python
{
  'role': 'user',  # or 'assistant'
  'decision_text': "Let's use FastAPI for the HTTP layer",
  'timestamp': "...",
  'context': [surrounding messages]
}
```

---

## Parsing Algorithm

### 1. Sequential Parse
```python
messages = []
for line in jsonl:
    entry = json.loads(line)
    if entry['type'] == 'user':
        # Extract text or skip tool results
        content = entry['message']['content']
        if isinstance(content, str):
            messages.append({
                'role': 'user',
                'text': content,
                'timestamp': entry['timestamp'],
                'uuid': entry['uuid']
            })

    elif entry['type'] == 'assistant':
        # Extract text and tool calls
        text_blocks = []
        tool_uses = []
        thinking = None

        for block in entry['message']['content']:
            if block['type'] == 'text':
                text_blocks.append(block['text'])
            elif block['type'] == 'tool_use':
                tool_uses.append(block)
            elif block['type'] == 'thinking':
                thinking = block['thinking']

        messages.append({
            'role': 'assistant',
            'text': '\n'.join(text_blocks),
            'tools': tool_uses,
            'thinking': thinking,
            'timestamp': entry['timestamp'],
            'uuid': entry['uuid']
        })
```

### 2. Pattern Detection
```python
# For each user message
for i, msg in enumerate(messages):
    if msg['role'] != 'user':
        continue

    # Correction detection
    if any(kw in msg['text'].lower() for kw in CORRECTION_KW):
        # Look back 1-3 messages for assistant action
        prev_actions = get_previous_assistant(messages, i, window=3)

        store_correction({
            'user_text': msg['text'],
            'what_was_wrong': prev_actions,
            'frustration': detect_frustration(msg['text']),
            'timestamp': msg['timestamp']
        })
```

### 3. Clustering Similar Corrections
```python
# Group corrections about same topic
corrections = all_corrections
clusters = []

for corr in corrections:
    # Find similar past corrections
    similar = find_similar(corr, all_corrections, threshold=0.7)

    if len(similar) >= 2:
        # Repeated pattern!
        cluster = {
            'pattern': extract_common_theme(similar),
            'count': len(similar),
            'frustration': max(c['frustration'] for c in similar),
            'timestamps': [c['timestamp'] for c in similar]
        }
        clusters.append(cluster)
```

---

## Agent Work Split

### Main Agent (This Session)
- Parse current session transcript
- Detect immediate corrections
- Real-time learning

### Background Agent (Async)
- Parse ALL past sessions for this project
- Build correction clusters across time
- Identify long-term patterns
- Update PRISM ANCHORS

### Calibration Agent (On-Demand)
- Parse specific session after completion
- Detailed analysis for memory quality
- One-time deep dive

---

## Storage in PRISM

### Correction Pattern
```python
prism_store_memory(
    content="NEVER use try/except pass - user corrected this 3 times",
    memory_type="correction",
    tier="ANCHORS",
    metadata={
        'correction_count': 3,
        'frustration_score': 0.9,
        'pattern': 'error_suppression',
        'timestamps': [t1, t2, t3],
        'from_sessions': [uuid1, uuid2, uuid3]
    }
)
```

### Approval Pattern
```python
prism_store_memory(
    content="User prefers async/await for all I/O operations",
    memory_type="preference",
    tier="LONGTERM",
    metadata={
        'approval_count': 5,
        'pattern': 'async_io',
        'confidence': 0.8
    }
)
```

### Decision
```python
prism_store_memory(
    content="Decided: Use FastAPI for HTTP layer (not Flask)",
    memory_type="decision",
    tier="ANCHORS",
    metadata={
        'decision_type': 'architecture',
        'rationale': "Performance and async support",
        'timestamp': timestamp,
        'status': 'accepted'
    }
)
```

---

## Testing Approach

**In /tmp:**

1. Parse recent session:
   ```bash
   python3 parse_transcript.py ~/.claude/projects/.../latest.jsonl
   ```

2. Extract patterns:
   ```bash
   python3 detect_corrections.py /tmp/parsed.json
   ```

3. Verify clustering:
   ```bash
   python3 cluster_corrections.py /tmp/corrections.json
   ```

4. Test PRISM storage:
   ```bash
   python3 store_to_prism.py /tmp/clusters.json
   ```

---

## What Actually Works

✅ **Parsing transcripts** - Full conversation history available
✅ **Detecting corrections** - Keyword matching + context window
✅ **Clustering patterns** - Similarity matching on correction text
✅ **PRISM storage** - Standard memory storage API
✅ **Frustration scoring** - Count + keyword intensity

❌ **Real-time injection** - Hooks can't modify my mid-conversation context
❌ **Auto-detection during chat** - Would need Claude Code to expose live transcript
✅ **End-of-session analysis** - Run after conversation via slash command

---

## Recommended Flow

1. **User triggers:** `/learn-from-session` or auto on session end
2. **Parse current session:** Extract messages, corrections, approvals
3. **Cluster with history:** Find repeated patterns across all sessions
4. **Store in PRISM:** High-frustration → ANCHORS, preferences → LONGTERM
5. **Next session:** PreToolUse hook queries PRISM, warns/blocks violations

---

## Session Branching and Multi-Session Analysis

**See `/tmp/SESSION_BRANCHING_FINDINGS.md` for complete details.**

### Within-Session Branching

**Retry branches:** User retries same message after failure.
- Same parent UUID, different children
- Both children have `isSidechain=False`
- Stored in SAME session file

**Sidechains:** Sub-agent parallel work.
- `isSidechain=True` for all messages
- Root has `parentUuid=None`
- Independent chain in SAME session file
- **Recommendation:** Skip sidechains for correction detection

### Cross-Session Branching

**New session files:** `claude --resume <session-id>` creates NEW .jsonl file.
- Different session UUID
- Copies history up to branch point
- NO parent session reference in metadata
- **Implication:** Can't auto-detect branched sessions

### Multi-Session Parsing

**Options:**
1. **Single session:** Parse one file, detect corrections
2. **Project-wide:** Parse all .jsonl in project dir, cluster corrections

**Recommendation:** Start with single-session, add project-wide later.

---

## Pass to Other Agent

**Key Info:**
- Transcripts at `~/.claude/projects/[project]/[session].jsonl`
- Parse user messages for text, assistant messages for text+tools+thinking
- Corrections = user keywords + lookback to assistant actions
- Clustering = find similar corrections across time
- Storage = PRISM with appropriate tier (ANCHORS for high frustration)
- Trigger = slash command or session-end hook, NOT real-time
- **Branching:** Within-session (sidechains, retries) vs cross-session (new files)
- **Sidechains:** Skip for correction detection (agent work, not user corrections)

**What they need to build:**
1. Robust JSONL parser (handle sidechains, retries, file snapshots)
2. Correction detection with frustration scoring
3. Similarity clustering algorithm (single-session first, project-wide later)
4. PRISM storage integration
5. Slash commands:
   - `/learn-from-session` - Analyze current session
   - `/learn-from-project` - Analyze all project sessions
