---
name: verification-before-completion
description: Use before claiming any task is complete, any test passes, any build succeeds, or any fix works. Prevents false completion claims by requiring fresh verification evidence before every success statement.
---

# Verification Before Completion

## Overview

Never claim something works without fresh evidence proving it.

**Core principle:** NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.

## The Rule

Before saying anything is done, working, passing, or fixed:

1. **Identify** what command proves the claim
2. **Execute** the complete command freshly (not from memory)
3. **Read** the full output, check exit codes
4. **Verify** the output actually confirms your claim
5. **Then** make the claim

**Skip any step = lying, not verifying.**

## Forbidden Language (Without Evidence)

These phrases are BANNED unless you just ran verification:

| Phrase | Problem |
|--------|---------|
| "Tests pass" | Did you run them? Right now? |
| "Should work" | Should != does |
| "Build succeeds" | Show me the output |
| "Fixed" | Prove it |
| "Done" | Verified how? |
| "Looks good" | Based on what evidence? |
| "Probably works" | Probably != verified |
| "That should do it" | Run the tests |

This applies to **paraphrases and synonyms** too. Any implication of completion without evidence violates this rule.

## What Counts as Evidence

| Claim | Required Evidence |
|-------|-------------------|
| "Tests pass" | Fresh test run output showing all pass |
| "Build succeeds" | Fresh build output with exit code 0 |
| "Bug is fixed" | Test that reproduced bug now passes |
| "Feature works" | Test exercising the feature passes |
| "No regressions" | Full test suite output, all green |
| "Linting clean" | Fresh linter output, no violations |

**Partial evidence is NOT evidence:**
- Linter passing != build succeeds
- One test passing != all tests pass
- Agent reporting success != independently verified
- "It compiled" != "it works"

## Common Violations

### The Premature "Done!"
```
# BAD: Claiming done after writing code
"Added the validation. Done!"

# GOOD: Verify first
*runs tests*
"Added the validation. Tests pass (47/47). Done."
```

### The Optimistic Fix
```
# BAD: Assuming fix works
"Fixed the null check. That should resolve the crash."

# GOOD: Prove it
*runs failing test*
"Fixed the null check. The reproducer test now passes, full suite green (128/128)."
```

### The Stale Memory
```
# BAD: Remembering a previous run
"Tests were passing earlier."

# GOOD: Run again
*runs tests now*
"Tests pass as of right now (output above)."
```

## Quick Reference

```
About to say "done" / "works" / "passes" / "fixed"?
  ├── Did you JUST run the verification command?
  │   ├── Yes → Did the output confirm your claim?
  │   │   ├── Yes → Make the claim (with evidence)
  │   │   └── No → Fix the issue, verify again
  │   └── No → Run it now. Then decide.
  └── Not sure what command to run?
      └── Figure that out first. Can't verify = can't claim.
```

## Red Flags

**Stop if you catch yourself:**
- Saying "done" without running tests
- Using words like "should", "probably", "likely" about completion
- Relying on a test run from 5 minutes ago
- Trusting a subagent's report without checking
- Claiming something works because "the code looks right"
- Expressing satisfaction ("Great!", "Perfect!") before verification

**Honesty is a core value.** Claiming success without evidence is dishonest, even if you believe it's true.
