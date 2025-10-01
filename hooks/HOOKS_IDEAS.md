# PRISM Hooks - Future Implementation Ideas

**Status:** Archived - Not currently implemented
**Last Updated:** 2025-09-30
**Decision:** Focus on validating core PRISM indexing/research value first

---

## Why Archived

Before implementing complex hooks integration, we need to:
1. **Validate PRISM's core value** - Index real codebases, test retrieval quality
2. **Use it for research** - See if pattern retrieval actually helps with coding
3. **Identify actual pain points** - What mistakes do I actually repeat?

**Only after validation:** Consider building hooks to prevent those specific mistakes.

---

## Hook Concepts Discussed

### 1. UserPromptSubmit: Context Injection (<10ms)

**What it would do:**
- Before Claude responds, inject relevant patterns from PRISM
- Based on: current file, active task, recent tool uses

**Example:**
```
User: "Add error handling here"
→ Hook retrieves: "User prefers explicit try/except with logging"
→ Claude sees this BEFORE writing code
→ Does it right the first time
```

**Implementation:**
- Query PRISM ANCHORS tier (high-priority patterns)
- Fast retrieval (<10ms via lightning mode)
- Inject as system message into Claude's context

**Value:** Claude sees your past corrections/decisions before responding

---

### 2. PreToolUse: Violation Prevention

**What it would do:**
- Before Claude uses Write/Edit/Bash, check for known violations
- Warn or block if about to repeat a mistake

**Example:**
```
Claude about to: Write error_handler.py with try/except pass
→ Hook queries PRISM: "NEVER use try/except pass (corrected 3x)"
→ Warning shown to Claude
→ Claude writes proper error handling instead
```

**Implementation:**
- Parse tool input to extract intent
- Query PRISM for correction patterns
- Block if frustration_score > 0.8
- Warn if frustration_score > 0.5

**Value:** Prevents repeating mistakes you've already corrected

---

### 3. PostToolUse: Real-Time Learning

**What it would do:**
- After Claude uses a tool, detect if you correct immediately
- Auto-store that correction in PRISM

**Example:**
```
Claude: Uses Write tool to create error handler with try/except pass
You: "No, don't suppress errors"
→ Hook detects correction keywords
→ Stores: "Don't suppress errors - use explicit handling" in ANCHORS
→ Next time PreToolUse hook catches this
```

**Implementation:**
- Watch for correction keywords in next user message
- Extract what was wrong + what's right
- Auto-store in PRISM with frustration score
- ANCHORS if high frustration, EPISODIC otherwise

**Value:** Builds up violation database automatically as mistakes happen

---

## Transcript Parsing Concepts

**More complex, lower immediate value:**

### What It Would Enable

**Cross-session pattern detection:**
- Parse all session transcripts
- Find repeated corrections across weeks
- Cluster similar mistakes
- Elevate to permanent ANCHORS

**Example:**
```
Session 1 (Monday): "No, don't use try/except pass"
Session 3 (Wednesday): "Again, no error suppression"
Session 5 (Friday): "I've told you this 3 times"
→ Transcript parser clusters these
→ Stores: "NEVER suppress errors - corrected 3x, frustration HIGH"
```

### Why It's Lower Priority

**PostToolUse hook** already stores corrections in real-time.

**Transcript parsing adds:** Cross-session clustering and pattern aggregation.

**Question:** Is real-time learning enough, or do you need clustering?
**Answer:** Unknown until we validate real-time learning value.

---

## Implementation Phases (If We Proceed)

### Phase 1: Real-Time Hooks (Weeks 1-2)

**Build:**
1. UserPromptSubmit: Context injection
2. PreToolUse: Violation checking
3. PostToolUse: Immediate correction learning

**Test:**
- Does context injection help? (measure: fewer corrections)
- Does violation prevention work? (measure: blocked bad actions)
- Does real-time learning build useful database?

**Validate before proceeding to Phase 2**

---

### Phase 2: Transcript Parsing (Weeks 3-4)

**Only if Phase 1 proves valuable:**

**Build:**
- Manual trigger: `/learn-from-session`
- Parse JSONL transcripts
- Cluster corrections across sessions
- Store cross-session patterns

**Test:**
- Does clustering find patterns hooks missed?
- Are cross-session patterns more valuable than real-time?

---

### Phase 3: Automation (Week 5+)

**Only if Phase 2 proves valuable:**

**Build:**
- Auto-detect corrections (count in session)
- File watcher for idle sessions
- Background periodic analysis

**Make it transparent:** No manual triggers needed

---

## Technical Notes

### Hook Script Location
`~/.claude/hooks/` - Claude Code automatically runs scripts here

### PRISM Integration
Hooks call PRISM HTTP API (localhost:8090) with auth:
```bash
curl -X POST http://localhost:8090/api/hooks/pre-tool-use \
  -H "Authorization: Bearer prism_development_key_2024"
```

### Performance Targets
- UserPromptSubmit: <10ms (lightning mode)
- PreToolUse: <100ms (fast mode)
- PostToolUse: async (no blocking)

### Transcript Parsing
Transcripts at: `~/.claude/projects/[project]/[session].jsonl`

**See:** `/tmp/TRANSCRIPT_PARSING_GUIDE.md` for format details

---

## Risks & Unknowns

**Before implementing:**

1. **False positives**: Will PreToolUse block valid actions?
2. **Noise**: Will PostToolUse create too many low-value patterns?
3. **Latency**: Will hooks slow down the workflow?
4. **Complexity**: Is the maintenance burden worth the value?

**Mitigation:** Start with Phase 1, measure everything, validate before proceeding.

---

## Current Archived Hooks

**Files in `~/.claude/hooks/archive/`:**
- `pre_tool_use.sh` - Pattern retrieval and violation blocking
- `post_tool_use.sh` - Async pattern detection

**Implementation code:**
- `prism_mcp/prism_mcp/integrations/hook_integration.py`

**Status:** Disabled, not in active use

---

## Decision Log

**2025-09-30:** Archived hooks, focusing on core PRISM validation first

**Next Review:** After 2-4 weeks of using PRISM for indexing/research

**Question to Answer:** Does PRISM retrieval actually help with coding? If yes, consider hooks. If no, skip the complexity.

---

## References

- Transcript parsing guide: `/tmp/TRANSCRIPT_PARSING_GUIDE.md`
- Session branching: `/tmp/SESSION_BRANCHING_FINDINGS.md`
- Working parser: `/tmp/working_parser.py`
- PRISM architecture: `~/repos/claude_mcp/prism_mcp/CLAUDE.md`
