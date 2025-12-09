---
name: cursor-agent
description: Use cursor-agent CLI for non-Anthropic models (GPT-5.1, Gemini, Grok, Composer). NEVER use for Claude models - use Claude Code CLI instead. Load when needing diverse model opinions for voting or fast drafts with Composer.
---

# cursor-agent CLI Integration

Use cursor-agent for **non-Anthropic models only**. Claude models (opus, sonnet, haiku) always go through Claude Code CLI.

## CRITICAL RULES

1. **NEVER use cursor-agent for Claude models** - opus, sonnet, haiku ALWAYS use `claude` CLI
2. **cursor-agent is for diversity** - different perspective, council votes, fast drafts
3. **cursor-agent has fewer features** - no tool restrictions, no schema enforcement
4. **Budget-aware** - Cursor Pro $20/mo ≈ 500 GPT-5 requests or 550 Gemini requests

## Available Models (cursor-agent)

| Logical Name | cursor-agent Model | Best For |
|--------------|-------------------|----------|
| `composer` | composer-1 | Fast drafts, skeletons, mockups |
| `gpt5` | gpt-5.1 | General coding, diverse opinion |
| `gpt5-high` | gpt-5.1-high | Complex tasks needing more capability |
| `gpt5-codex` | gpt-5.1-codex | Backend implementation |
| `gemini` | gemini-3-pro | Google's perspective, council votes |
| `grok` | grok | Fast but "confidently wrong" sometimes |

## CLI Usage

```bash
# Basic print mode (non-interactive)
cursor-agent -p --model composer-1 "Your prompt here"

# JSON output for parsing
cursor-agent -p --output-format json --model gpt-5.1 "Return JSON: {...}"

# Specify workspace
cursor-agent -p --model gemini-3-pro --workspace /path/to/project "Prompt"
```

## Output Format

cursor-agent JSON output structure:
```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "result": "```json\n{...}\n```",  // Often wrapped in markdown
  "duration_ms": 7103,
  "session_id": "...",
  "request_id": "..."
}
```

Note: Result content is often wrapped in markdown code blocks - extract the JSON.

## When to Use Each Model

### Composer (Fast Drafts)
```bash
# Quick skeleton generation
cursor-agent -p --model composer-1 "Create a skeleton for a rate limiter class with methods: check_limit(), increment(), reset()"

# Fast mockup to see structure
cursor-agent -p --model composer-1 "Show me what a complete implementation might look like for X"
```
**Good for:** Skeletons, mockups, rough drafts, any "haiku-level" tasks
**Bad for:** Complex reasoning, architecture decisions

### GPT-5.1 / Gemini (Council Votes)
```bash
# Get diverse opinion for decision
cursor-agent -p --output-format json --model gpt-5.1 "
Given this implementation choice:
Option A: Use Redis for caching
Option B: Use in-memory cache

Vote: {\"choice\": \"A\" or \"B\", \"reasoning\": \"...\"}"
```
**Good for:** Second opinions, council voting, diverse perspectives
**Bad for:** Primary implementation work (use Claude Code)

## Orchestration Integration

The orchestration runner automatically routes models:

```python
# In agent configs
agent_config = AgentConfig(
    name='council-voter',
    model='gpt5',  # Auto-routes to cursor-agent
)

# Claude models always use Claude Code
agent_config = AgentConfig(
    name='validator',
    model='opus',  # Auto-routes to claude CLI
)
```

## Cost Awareness

Cursor Pro ($20/month) = $20 credit pool at API prices:
- ~500 GPT-5 requests
- ~550 Gemini requests
- ~225 Sonnet 4.5 requests (but don't use cursor for Claude!)

**For council votes:** 3-5 votes per decision × occasional decisions = plenty of budget
**For continuous work:** Will exceed budget - use Claude Code instead

## Best Practices

1. **Use Composer for fast iteration** - See rough draft before investing in /spec
2. **Use GPT-5/Gemini for diversity** - Council votes benefit from different perspectives
3. **Never replace Claude with cursor** - Different tools for different purposes
4. **Check cursor availability** - Falls back to Claude if cursor-agent not installed

## Example: Quick Draft Before Spec

```bash
# See rough implementation before formal spec
cursor-agent -p --model composer-1 "
I need to add rate limiting middleware to a Flask API.
Show me a complete rough draft implementation including:
- Rate limiter class
- Flask middleware decorator
- Redis integration for distributed limiting
- Configuration options

This is just a draft to understand the scope."
```

Then use Claude Code for the formal implementation with proper validation.
