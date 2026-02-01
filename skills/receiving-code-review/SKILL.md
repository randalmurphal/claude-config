---
name: receiving-code-review
description: Use when receiving code review feedback - before implementing suggestions, especially if feedback seems unclear or technically questionable. Requires technical verification and honest evaluation, not performative agreement.
---

# Receiving Code Review

## Overview

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social comfort.

## The Response Pattern

```
WHEN receiving code review feedback:

1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask)
3. VERIFY: Check against codebase reality
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each
```

## Forbidden Responses

**NEVER say:**
- "You're absolutely right!"
- "Great point!" / "Excellent feedback!"
- "Let me implement that now" (before verification)
- "Thanks for catching that!"
- Any gratitude expression

**INSTEAD:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if wrong
- Just start working (actions > words)

**Why no thanks:** Actions speak. Just fix it. The code shows you heard the feedback.

## Handling Unclear Feedback

```
IF any item is unclear:
  STOP - do not implement anything yet
  ASK for clarification on unclear items first

WHY: Items may be related. Partial understanding = wrong implementation.
```

**Example:**
```
Reviewer: "Fix items 1-6"
You understand 1,2,3,6. Unclear on 4,5.

BAD:  Implement 1,2,3,6 now, ask about 4,5 later
GOOD: "I understand 1,2,3,6. Need clarification on 4 and 5 before proceeding."
```

## Evaluating External Feedback

Before implementing suggestions from reviewers:

1. **Technically correct** for THIS codebase?
2. **Breaks existing functionality?**
3. **Reason for current implementation?** (it might be intentional)
4. **Works on all platforms/versions?**
5. **Does reviewer understand full context?**

**If suggestion seems wrong:** Push back with technical reasoning.

**If can't verify:** Say so: "I can't verify this without [X]. Should I investigate or proceed?"

**If conflicts with prior decisions:** Stop and discuss with the decision-maker first.

## When to Push Back

Push back when:
- Suggestion breaks existing functionality
- Reviewer lacks full context
- Violates YAGNI (unused feature being "properly implemented")
- Technically incorrect for this stack
- Legacy/compatibility reasons exist
- Conflicts with architectural decisions

**How to push back:**
- Technical reasoning, not defensiveness
- Specific questions
- Reference working tests/code
- Escalate if architectural

## YAGNI Check

```
IF reviewer suggests "implementing properly":
  grep codebase for actual usage

  IF unused: "This endpoint isn't called. Remove it (YAGNI)?"
  IF used: Then implement properly
```

## Implementation Order

For multi-item feedback:
1. **Clarify** anything unclear FIRST
2. **Then implement** in this order:
   - Blocking issues (breaks, security)
   - Simple fixes (typos, imports)
   - Complex fixes (refactoring, logic)
3. **Test each fix individually**
4. **Verify no regressions**

## Acknowledging Correct Feedback

When feedback IS correct:
```
GOOD: "Fixed. [Brief description of what changed]"
GOOD: "Good catch - [specific issue]. Fixed in [location]."
GOOD: [Just fix it and move on]

BAD:  "You're absolutely right!"
BAD:  "Great point!"
BAD:  "Thanks for catching that!"
```

## Correcting Your Pushback

If you pushed back and were wrong:
```
GOOD: "You were right - I checked [X] and it does [Y]. Implementing now."
GOOD: "Verified and you're correct. My understanding was wrong because [reason]. Fixing."

BAD:  Long apology
BAD:  Defending why you pushed back
```

State the correction factually and move on.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State requirement or just act |
| Blind implementation | Verify against codebase first |
| Batch without testing | One at a time, test each |
| Assuming reviewer is right | Check if it breaks things |
| Avoiding pushback | Technical correctness > comfort |
| Partial implementation | Clarify all items first |

## GitHub Thread Replies

When replying to inline review comments, reply in the comment thread (`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`), not as a top-level PR comment.
