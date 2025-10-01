# Transcript Parsing Tools

Tools and documentation for parsing Claude Code conversation transcripts.

## What's Here

**Documentation:**
- `TRANSCRIPT_PARSING_GUIDE.md` - Complete guide to parsing `.jsonl` transcript files
- `SESSION_BRANCHING_FINDINGS.md` - Deep dive on session branching mechanics

**Working Scripts:**
- `working_parser.py` - Parse transcripts and detect corrections
- `analyze_branching.py` - Analyze branching structure in session
- `inspect_branches.py` - Inspect specific branching points
- `inspect_sidechains.py` - Analyze sidechain (sub-agent) messages

## Where Are Transcripts?

```
~/.claude/projects/[project-dir]/[session-uuid].jsonl
```

Example:
```
~/.claude/projects/-home-randy-repos-claude-mcp/55653782-179a-4cf2-b63f-1ba698038628.jsonl
```

## Quick Usage

**Parse current session for corrections:**
```bash
cd ~/.claude/hooks/transcript_parsing
./working_parser.py
```

**Analyze branching structure:**
```bash
./analyze_branching.py
```

**Inspect sidechains (sub-agent work):**
```bash
./inspect_sidechains.py
```

## Key Findings

1. **Within-session branching** - Retry branches and sidechains in SAME file
2. **Cross-session branching** - `claude --resume` creates NEW file with new UUID
3. **Sidechains** - Sub-agent work marked with `isSidechain=True`
4. **Corrections** - Detect via keywords + lookback to previous messages
5. **Frustration scoring** - Weight corrections by intensity of language

## Integration with PRISM

These tools were built to enable:
- Automatic correction detection from conversation history
- Pattern learning from repeated user corrections
- Long-term memory storage in PRISM ANCHORS tier
- Preference learning across sessions

See documentation for full implementation details.

## Created

2025-09-30 - Investigation of transcript structure and session branching
