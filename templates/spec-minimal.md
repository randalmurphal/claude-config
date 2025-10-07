# Minimal SPEC Template (for /solo)

```markdown
# [Task Name]

## Goal
[Clear, concise outcome - what to build]

## Problem
[1-2 sentences - what gap are we filling]

## Approach
[Basic implementation strategy]

## Files
### New Files
- path/to/file.py: [purpose]
- path/to/test_file.py: [tests what]

### Modified Files
- path/to/existing.py: [what changes]

## Tests
- Unit tests for all new functions/classes
- Integration test for [workflow]
- Coverage target: 90%

## Quality
- Linting: Pass ruff check
- Security: [any specific concerns or "Standard practices"]
- Performance: [any specific requirements or "No specific requirements"]

## Context & Constraints
[Any important context the main agent and sub-agents need to stay on track]
- [Constraint or context 1]
- [Constraint or context 2]
```

## Usage Notes

This minimal format provides just enough structure for:
1. Main agent to stay focused on the goal
2. Sub-agents to understand their context
3. Validation to have clear quality criteria
4. Testing to know what coverage is expected

Not included (vs full SPEC):
- Implementation Phases (single pass)
- Component dependencies (straightforward)
- Architectural decisions (standard patterns)
- Success criteria (implied by goal)
