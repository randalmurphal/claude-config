---
name: systematic-debugging
description: Use when debugging any failure, bug, or unexpected behavior - especially before attempting any fix. Enforces root cause investigation before implementation to prevent fix-thrashing and symptom-masking.
---

# Systematic Debugging

## Overview

Find the root cause before writing any fix.

**Core principle:** NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

**Announce at start:** "I'm using the systematic-debugging skill to investigate before fixing."

## When to Use

- Test failures
- Unexpected behavior
- Production bugs
- "It worked before and now it doesn't"
- Any time you're tempted to "just try something"

## The Four Phases

Complete each phase before moving to the next. No skipping.

### Phase 1: Root Cause Investigation

1. **Read the error carefully** - The actual message, not what you assume it says
2. **Reproduce consistently** - If you can't reproduce it, you can't verify a fix
3. **Check recent changes** - `git log`, `git diff` - what changed?
4. **Gather evidence** - Logs, stack traces, state at time of failure
5. **Trace the data flow** - Follow the data from input to error point

**Do NOT propose solutions during this phase.**

### Phase 2: Pattern Analysis

1. **Find a working example** - Where does similar code work correctly?
2. **Compare working vs broken** - What's specifically different?
3. **Check assumptions** - Is the API actually behaving as you assumed?
4. **Read the docs** - Not what you remember, what they actually say

### Phase 3: Hypothesis Testing

1. **Form ONE hypothesis** - "The bug is caused by X because Y"
2. **Make the minimal change** to test that hypothesis
3. **Verify** - Did it fix the issue? Did it break anything else?
4. **If wrong** - Revert. Form new hypothesis. Don't stack changes.

**Never test multiple hypotheses simultaneously.** You won't know which change fixed it.

### Phase 4: Implementation

1. **Write a failing test** that reproduces the bug
2. **Apply the root-cause fix** (not a workaround)
3. **Verify the test passes**
4. **Run full test suite** - No regressions
5. **Don't bundle unrelated improvements** - Fix the bug, nothing else

## The 3+ Failures Rule

**When 3 or more fix attempts fail, STOP.**

You're not debugging anymore - you're thrashing. Step back and question:
- Is the architecture itself flawed?
- Am I debugging the wrong layer?
- Do I misunderstand how this system works?
- Should I read the source code of the dependency?

Three failures means your mental model is wrong. Fix the model first.

## What NOT to Do

| Anti-Pattern | Why It Fails |
|-------------|-------------|
| "Let me just try X" | Random fixes mask symptoms, introduce new bugs |
| Fix multiple things at once | Can't tell what actually fixed it |
| Skip reproduction | Can't verify the fix works |
| Assume you know the cause | Assumptions are often wrong - verify |
| Add workarounds | Hides the real bug, creates tech debt |
| Keep trying after 3 failures | Mental model is wrong, more tries won't help |

## Quick Decision Guide

```
Error occurs
  ├── Can you reproduce it?
  │   ├── Yes → Phase 1: Investigate
  │   └── No → Make it reproducible first (add logging, narrow conditions)
  │
  ├── Do you understand the root cause?
  │   ├── Yes → Phase 3: Test ONE hypothesis
  │   └── No → Phase 2: Find working example, compare
  │
  └── 3+ failed fixes?
      └── STOP. Question your assumptions. Read source code.
```

## Real Impact

| Approach | Time per Fix | First-Time Success |
|----------|-------------|-------------------|
| Systematic investigation | 15-30 min | ~95% |
| "Just try things" | 2-3 hours | ~40% |

The systematic approach feels slower at the start. It's dramatically faster overall.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Proposing fix before understanding cause | Complete Phase 1 first |
| Testing multiple changes at once | One hypothesis at a time |
| No failing test for the bug | Write test before fix |
| "It probably works now" | Run the test suite, verify |
| Skipping Phase 2 (pattern analysis) | Find working code, compare |
| Continuing after 3 failures | Stop, reassess mental model |

## Red Flags

**Stop immediately if you catch yourself:**
- Writing a fix without being able to explain the root cause
- Saying "let me just try..." without a hypothesis
- Making a second change before verifying the first
- Assuming you know the cause without tracing the data flow
- Stacking workarounds on top of each other
