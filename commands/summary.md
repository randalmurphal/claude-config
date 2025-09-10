---
name: summary
description: Generate intelligent context summary for handoffs
---

# Summary - Intelligent Context Handoff

Creates a concise, actionable summary of the current conversation state suitable for passing to another agent or session.

## Usage

`/summary` - Generate a comprehensive handoff summary

## What It Produces

The summary includes:

### 1. **Current State**
- What task/problem we're working on
- Current phase or step in progress
- Any blockers or pending decisions

### 2. **Key Decisions Made**
- Architectural choices
- Implementation approaches selected
- Trade-offs accepted

### 3. **Work Completed**
- Files created/modified
- Systems configured
- Tests written

### 4. **Critical Context**
- Project structure
- Key file paths
- Important constraints or requirements
- Technology stack being used

### 5. **Next Steps**
- Immediate tasks to continue
- Open questions needing answers
- Validation or testing needed

## Example Output

```markdown
## Task Summary
Working on: Forex trading platform orchestration improvements
Phase: Completed implementation, ready for testing
Status: All changes committed and pushed

## Key Decisions
- Replaced LEARNED_PATTERNS with MODULE_CACHE.json for caching
- Using GOTCHAS.md for project-specific rules
- Git worktrees for parallel work, applied safely to working directory
- Test impact analysis for selective test execution

## Completed Work
- ✅ Updated /conduct orchestration command
- ✅ Created merge-coordinator agent
- ✅ Added AGENT_METRICS.json tracking
- ✅ Enhanced preflight validation

## Critical Context
- Project: ~/repos/forex_trader
- Config: ~/.claude (orchestration system)
- Stack: Python/Go/JavaScript
- Database: PostgreSQL (forex_trader)

## Next Steps
1. Test the orchestration with a real task
2. Monitor agent performance metrics
3. Verify test impact analysis works correctly
```

## Use Cases

### Handoff to Another Session
When context is getting full and you need to continue in a new session:
```
/summary
[Copy output to new session as first message]
```

### Handoff to Another Agent
When delegating work to a specialized agent:
```
/summary
[Include relevant parts in agent prompt]
```

### Progress Checkpoint
When you need to document current state:
```
/summary
[Save to project notes or documentation]
```

### Team Collaboration
When another developer needs to understand current state:
```
/summary
[Share via Slack/email/PR description]
```

## Important Notes

- Focuses on **actionable information** not history
- Includes **file paths and locations** for quick navigation
- Omits **failed attempts and debugging** unless relevant
- Structures information for **immediate use**
- Can be used as the **first message** in a new conversation

## Integration with /conduct

The conductor can use summary at phase transitions to create checkpoint documentation, making it easier to recover from failures or hand off complex tasks.