---
name: agent-prompting
description: Best practices for writing effective Task tool prompts that produce clear, structured outputs from sub-agents. Covers context engineering, instruction clarity, output format specification, and parallel delegation patterns. MUST BE USED PROACTIVELY when spawning sub-agents to ensure high-quality results.
---

# Agent Prompting & Delegation

## Core Principles

1. **Clear over clever** - Ambiguity is the enemy
2. **Structure over prose** - XML tags, bullets, code blocks
3. **Examples over explanations** - Show what you want
4. **Context engineering > prompt engineering** - Right context matters more than perfect wording

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

## Critical Inline Standards by Agent Type

**Include these in prompts.** Even with CLAUDE.md, inline standards guarantee they're seen.

### Implementation Agents

```
CRITICAL STANDARDS:
- Logging: import logging; LOG = logging.getLogger(__name__)
- try/except ONLY for connection errors (network, DB, cache)
  - NEVER wrap: dict.get(), file I/O, JSON parsing
- Type hints required, 80 char limit
- No # noqa without documented reason
- DO NOT run tests unless instructed

OUTPUT (during orchestration):
- If gotchas found: Append to $WORK_DIR/.spec/DISCOVERIES.md
- Return brief summary (3-5 sentences)
```

### Test Agents

```
CRITICAL STANDARDS:
- 1:1 file mapping: tests/unit/test_<module>.py
- 95% coverage minimum
- Mock EVERYTHING external to function being tested
- DO NOT run tests unless instructed
- NO shortcuts or workarounds

Load: testing-standards skill
```

### Review Agents

```
CRITICAL STANDARDS:
- Check for improper try/except (wrapping safe operations)
- Check logging (logging.getLogger(__name__))
- Check type hints, 80 char limit

OUTPUT (during orchestration):
1. Write findings to: $WORK_DIR/.spec/review_findings/[phase]/[role].md
2. Return ONLY 2-3 sentence summary

JSON format:
{"status": "COMPLETE", "critical": [...], "important": [...], "minor": [...]}
```

### Fix Agents

```
CRITICAL STANDARDS:
- Fix PROPERLY - no workarounds
- DO NOT use # noqa as a "fix"
- If architectural issue: ESCALATE with options
- Max 3 attempts, then ESCALATE

OUTPUT (during orchestration):
- Return brief summary (3-5 sentences)
- 2 reviewers will validate after
```

### Investigation Agents

```
CRITICAL STANDARDS:
- Start narrow, expand if needed
- Use Grep (cheap) before Read (focused)
- Don't read >5 files without reporting
- Include file:line references
```

### Documentation Agents

```
CRITICAL STANDARDS:
- Load ai-documentation skill first
- Concise over comprehensive
- Tables/bullets >>> paragraphs
- Location references with file:line
- 100-200 line target (300-400 max for complex)
```

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Vague objective | "Find JWT verification with file:line" |
| Under-specification | Include test scenarios, coverage target |
| Context overload | Only what's directly relevant |
| Resource conflicts | Assign file ranges OR sequential |
| Missing output format | Specify structure explicitly |
| Too simple tasks | Use tools directly |

---

## Bottom Line

Before every Task call:
1. Is my objective clear?
2. Will the agent know when it's done?
3. Have I specified the output format?
4. Can I run this in parallel?

**Better prompts → better outputs → more effective delegation.**
