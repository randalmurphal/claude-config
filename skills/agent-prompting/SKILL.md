---
name: agent-prompting
description: Write effective prompts for Task tool sub-agents, slash commands, and system prompts. Covers Claude 4.x prompting patterns, context engineering, output format specification, and parallel delegation. Use when spawning sub-agents, creating slash commands, or writing system prompts.
---

# Agent Prompting & Delegation

**Purpose**: Write effective prompts that produce clear, structured outputs from sub-agents and custom commands.

**Related**: For CLAUDE.md/AGENTS.md file structure, see `ai-documentation` skill.

---

## Claude 4.x Prompting Changes

**Claude 4.x models follow instructions more precisely.** Adjust your prompting style:

| Old Style (Pre-4.x) | New Style (4.x) | Why |
|---------------------|-----------------|-----|
| `CRITICAL: You MUST always...` | `Use this pattern when...` | 4.x responds to normal language |
| `NEVER do X under any circumstances` | `Avoid X because [reason]` | Reasoning helps more than shouting |
| `IMPORTANT: Remember to...` | Just state it directly | 4.x pays attention without emphasis |
| Aggressive repetition | State once clearly | 4.x doesn't need reinforcement |

**Context awareness**: Claude 4.x tracks its token budget. For long tasks, it may try to wrap up as context fills. Add this if needed:

```
Your context will be compacted as needed - continue working fully without stopping early due to token concerns.
```

**Parallel tool calling**: Claude 4.x aggressively parallelizes. If you need sequential execution, say so explicitly.

---

## Core Principles

1. **Clear over clever** - Ambiguity is the enemy
2. **Structure over prose** - Bullets, tables, code blocks
3. **Examples over explanations** - Show what you want
4. **Context engineering > prompt engineering** - Right context matters more than perfect wording
5. **Reasoning over commands** - Explain WHY, not just WHAT

---

## Essential Prompt Components

### Required

1. **Clear Objective** - What success looks like in one sentence
2. **Success Criteria** - Measurable outcomes
3. **Expected Output Format** - Structure specified

### Recommended

4. **Context** - Only what's directly relevant (not everything)
5. **Error Handling** - What to do if not found/fails
6. **Files Hint** - Where to start looking

---

## Prompt Template

```
[Clear objective in one sentence]

Success criteria:
- [Measurable outcome 1]
- [Measurable outcome 2]

Context: [Only what's directly relevant]

Expected output:
[Specific structure]

If [error condition]:
- [How to handle]

Start looking in: [Files hint]
```

---

## When to Use Agents vs Tools

| Condition | Action |
|-----------|--------|
| Know exact file | Read tool directly |
| Know exact pattern | Grep tool directly |
| Need to explore/discover | Use Task (agent) |
| Need to analyze/synthesize | Use Task (agent) |
| >3 files to investigate | Use Task (agent) |

---

## Parallel vs Sequential

**PARALLEL** (single message, multiple Tasks):
- Tasks are independent
- No shared state
- 5-10x speedup

**SEQUENTIAL:**
- Task B depends on Task A output
- Shared state (file modifications)
- Order matters

---

## Inline Standards by Agent Type

**Include key standards in prompts.** Even with CLAUDE.md, inline standards guarantee visibility.

### Implementation Agents

```
Standards:
- Logging: import logging; LOG = logging.getLogger(__name__)
- try/except only for connection errors (network, DB, cache)
- Type hints required, 80 char limit
- Don't run tests unless instructed

Output: Brief summary (3-5 sentences)
```

### Test Agents

```
Standards:
- 1:1 file mapping: tests/unit/test_<module>.py
- 95% coverage target
- Mock everything external to the function being tested
- Don't run tests unless instructed

Load: testing-standards skill
```

### Review Agents

```
Focus areas:
- Improper try/except (wrapping safe operations like dict.get)
- Logging setup (logging.getLogger(__name__))
- Type hints, line length

Output format:
{"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
```

### Fix Agents

```
Standards:
- Fix properly - no workarounds or # noqa shortcuts
- If architectural issue: escalate with options
- Max 3 attempts, then escalate

Output: Brief summary of what was fixed
```

### Investigation Agents

```
Approach:
- Start narrow, expand if needed
- Use Grep before Read (cheaper)
- Include file:line references in findings
```

### Documentation Agents

```
Load ai-documentation skill first.

Standards:
- Concise over comprehensive
- Tables/bullets over paragraphs
- Include file:line references
- Context-loaded files: 100-400 lines
- Reference docs (docs/): can be longer
```

---

## Slash Commands

**Location**: `.claude/commands/<command-name>.md`

**Structure**:
```markdown
Description of what this command does.

$ARGUMENTS will be replaced with user input after the command.

[Your prompt template here]
```

**Example** (`.claude/commands/review-pr.md`):
```markdown
Review the PR for ticket $ARGUMENTS.

1. Fetch PR context using gitlab scripts
2. Check code against project standards
3. Look for:
   - Improper error handling
   - Missing tests
   - Style violations
4. Output findings as inline comments
```

**Usage**: `/review-pr INT-1234`

### Slash Command Best Practices

| Do | Don't |
|----|-------|
| Single clear purpose | Multi-purpose commands |
| Use $ARGUMENTS for input | Hardcode values |
| Reference skills to load | Duplicate skill content |
| Keep under 50 lines | Write essays |

---

## System Prompts (CLAUDE.md)

**For file structure and organization**: See `ai-documentation` skill.

**For content tone** (Claude 4.x):

```markdown
# Good - Direct and clear
When modifying shared code, check who calls it first.
Use retry_run() for all MongoDB writes.

# Avoid - Aggressive/shouting
CRITICAL: You MUST ALWAYS check callers before modifying shared code!!!
NEVER forget to use retry_run() - THIS IS MANDATORY!
```

**Key sections for CLAUDE.md**:
1. Project purpose (1-2 sentences)
2. Key commands (build, test, lint)
3. Code patterns to follow
4. Common gotchas
5. What to ask about vs proceed

---

## Hooks

**Location**: `.claude/settings.json` or project settings

**Types**:
- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution
- `Notification` - On events

**Example** (lint on file write):
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "python-code-quality --fix $FILE"
      }
    ]
  }
}
```

**Hook outputs** appear as `<user-prompt-submit-hook>` in conversation - treat as user feedback.

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Vague objective | "Find JWT verification" → "Find JWT verification with file:line" |
| Over-emphasis | Remove CRITICAL/MUST/NEVER - state directly |
| Context overload | Only what's directly relevant |
| Missing output format | Specify structure explicitly |
| Too simple tasks | Use tools directly instead of agents |
| Aggressive language | Claude 4.x responds to normal instructions |

---

## Quick Reference

**Before spawning an agent:**
1. Is my objective clear in one sentence?
2. Will the agent know when it's done?
3. Have I specified the output format?
4. Can I run this in parallel with other tasks?
5. Am I using normal language (not SHOUTING)?

**Before writing a slash command:**
1. Does this need to be reusable?
2. Is there a single clear purpose?
3. Am I using $ARGUMENTS for variable input?

**Before updating CLAUDE.md:**
1. Load ai-documentation skill
2. Is this context-loaded? Keep it concise
3. Am I stating things once, clearly?
