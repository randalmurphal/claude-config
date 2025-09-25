# Memory MCP Design - Shared Project Knowledge System

## Overview
Design for a shared, git-friendly memory system using Memory MCP for project discoveries that avoids merge conflicts and automatically manages lifecycle based on sprint/branch status.

## Core Architecture

### 1. File Format: JSONL (Append-Only)
```jsonl
{"id":"2024-01-15T10:30:00Z-sarah-001","author":"sarah","date":"2024-01-15","observation":"Rate limit is 50/min for auth endpoints","reasoning":{"why":"JWT validation is expensive","impact":"Batch operations will fail","workaround":"Implement queuing"},"tags":["auth","rate-limit","permanent"]}
```

**Why JSONL:**
- Each line is independent = no merge conflicts ever
- Append-only = git always merges cleanly  
- Each entry has unique ID = deduplication is easy

### 2. Memory Types & Lifecycle

#### Permanent Memories (Never Expire)
- API rate limits
- External system constraints
- Architecture decisions
- Security requirements
- System gotchas/quirks

#### Sprint-Based Memories (Expire with ticket completion)
- Current bugs (expires when ticket closed)
- TODOs (expires when code ships)
- Performance issues (expires when resolved)
- Incomplete features (expires when done)
- Refactoring needs (expires when complete)

#### Branch-Based Memories (Fallback when no Jira)
- Tied to feature branches
- Expire when branch merges to main/develop
- Archive when branch deleted without merge

## Implementation Strategy

### Memory Creation Flow
1. Discovery made during work
2. Importance scoring (crashes=3.0, workarounds=2.5, trivial=-1.0)
3. Duplicate detection (fuzzy matching >80% similarity)
4. Conflict detection (conflicting values for same fact)
5. Append to `.claude/discoveries.jsonl`
6. Load into Memory MCP with appropriate tags

### Memory Retrieval
```
Hierarchical entities for efficient retrieval:
- tenable_sc.auth.jwt (specific)
- tenable_sc.auth.* (auth-related)
- tenable_sc.* (all Tenable)
```

### Sprint Integration
- Sprint start: Load memories for tickets in sprint
- During sprint: Memories stay active for current work
- Sprint end: 
  - Completed tickets → Expire memories
  - Moved tickets → Update sprint tag
  - Removed tickets → Ask user (deprioritized vs abandoned)

### Automatic Expiry Triggers
- Jira ticket marked "Done"
- Git branch merged to main/develop
- Specific test now passes
- File/line mentioned has changed
- PR with fix keywords merged

## Integration with /conduct

### What Moves to Memory MCP
- GOTCHAS.md → Memory MCP (permanent gotchas)
- Architecture decisions from DECISION_MEMORY.json
- Discoveries from agents during orchestration

### What Stays in Filesystem
- MISSION_CONTEXT.json (live orchestration state)
- PHASE_PROGRESS.json (current phase tracking)
- INVARIANTS.md (human-readable critical rules)
- Active orchestration state

## Critical Considerations

### 1. Memory MCP Failure Handling
- Always check MCP health on startup
- Fall back to static files if unavailable
- Never block work due to memory issues

### 2. Cross-Project Isolation
- Every memory tagged with project (from git repo name)
- Filter memories by current project
- Personal preferences have no project tag (global)

### 3. Sensitive Information
- Pattern detection before storage
- Reject API keys, passwords, internal URLs
- Sanitize client names

### 4. Performance at Scale
- Hierarchical entity structure
- Only load relevant subset
- Cache frequently accessed memories
- Bloom filters for quick "no relevant memories"

### 5. Conflict Resolution
- Code is truth, memory is advisory
- When conflict detected, update memory to match code
- Track superseded memories with reason

### 6. Team Synchronization
- `.claude/critical-knowledge.jsonl` in git
- New team members auto-import on first run
- Shared discoveries through git pull
- Personal preferences stay local

## Practical Workflows

### Regular Development
```
1. Open file in project
2. Auto-detect context (file, component, sprint ticket)
3. Query Memory MCP for relevant memories only
4. Load 2-3 most relevant discoveries
5. Work with perfect context
```

### During /conduct
```
1. Orchestration starts, creates filesystem state
2. Queries Memory MCP for permanent knowledge
3. Agents make discoveries → Both filesystem and Memory MCP
4. Orchestration completes → Filesystem cleans up
5. Permanent discoveries remain in Memory MCP
```

### Sprint Boundaries
```
Sprint ends:
- Check all memories tagged with sprint
- Completed tickets → Expire
- Ongoing tickets → Move to next sprint  
- Removed tickets → Ask user
```

## Implementation Order

1. **Phase 1**: Read-only experiment
   - Memory MCP stores discoveries
   - /conduct still uses filesystem
   - Monitor effectiveness

2. **Phase 2**: Parallel run
   - Both systems active
   - Compare discovery retrieval
   - Refine filtering

3. **Phase 3**: Migration
   - Import existing GOTCHAS.md
   - Convert DECISION_MEMORY.json
   - Team onboarding

4. **Phase 4**: Full cutover
   - Memory MCP primary
   - Filesystem for orchestration state only
   - Fallback ready

## Key Benefits

1. **No merge conflicts** - Append-only JSONL
2. **Automatic cleanup** - Sprint/branch lifecycle
3. **Contextual loading** - Only relevant memories
4. **Team knowledge sharing** - Through git
5. **Preserves history** - Versioning, not deletion
6. **Performance** - Hierarchical retrieval
7. **Resilient** - Fallback to files if needed

## Next Steps

1. Create memory-sync.py script for import/export
2. Design hook for automatic capture
3. Build sprint boundary checker
4. Test with small project first
5. Document team onboarding process

## Configuration Examples

### Memory MCP Setup (Multiple Instances)
```json
{
  "memory-me": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory", "--db-path", "~/.claude/memory/personal.db"]
  },
  "memory-project": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory", "--db-path", "./.claude-memory.db"]
  }
}
```

### Discovery Entry Structure
```json
{
  "id": "unique-timestamp-author-counter",
  "observation": "The core discovery",
  "reasoning": {
    "why": "Root cause",
    "impact": "What breaks",
    "workaround": "How to handle"
  },
  "lifecycle": {
    "type": "sprint|permanent|branch",
    "expires": "condition",
    "linked_to": "JIRA-1234"
  },
  "metadata": {
    "author": "git-user",
    "project": "repo-name",
    "confidence": 0.95
  }
}
```

---

*This design emerged from extensive discussion about balancing automation with accuracy, team collaboration with personal preferences, and permanent knowledge with temporary development state.*