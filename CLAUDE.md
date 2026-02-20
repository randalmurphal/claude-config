# Quality Standards

## Code Philosophy

Obvious over clever. Readable over terse. Traceable over elegant.

Every line of code should be understandable without needing to hold surrounding context in your head. Prefer explicit names, flat control flow, and visible data transformations. If someone reading the code has to ask "where does this come from?" or "what does this do?", it needs to be clearer.

Prefer functional patterns - pure functions, immutable data, transformations over mutations. Avoid side effects where possible. When side effects are necessary, make them visible and isolated.

Don't abstract until repetition is a real, present problem - not a hypothetical one. Inline and explicit beats DRY when it improves traceability. Three similar blocks of code are fine if each is immediately understandable on its own.

## Before Writing Code

Read and understand relevant code before proposing changes. Never speculate about code you haven't inspected. If I reference a file, open it first.

Investigate downstream impact before modifying shared code. Who calls this? Who imports it? What tests cover it? What breaks if this changes?

Think about verification first. Before writing the implementation, identify: what tests will prove this works? What edge cases matter? What existing tests might need to change? This isn't optional - understanding how to verify correctness shapes how you write the code.

## While Writing Code

Write the simplest correct solution. No abstraction layers, helper utilities, or configurability unless the current task demands it. But "simple" means easy to understand, not easy to write - sometimes the obvious approach takes more lines and that's fine.

Complete implementations. No TODOs, no placeholders, no "you could add X later" suggestions. Finish the work or explain what's blocking.

Match existing patterns. Study the codebase's conventions before introducing new ones. When in doubt, follow what's already there.

## Testing & Verification

Write tests before or alongside implementation, not as an afterthought. Tests are how you prove the logic is correct - treat them as first-class work, not a chore tacked on at the end.

Think about what each test is actually verifying. A test that just confirms "the function runs without crashing" isn't useful. Test the logic, the edge cases, the contracts.

When modifying existing code, run the existing tests first to establish a baseline. If they fail before your changes, that's important context.

## Ownership

If you find a problem - fix it. Don't leave broken things because "that wasn't part of the request." Adjacent bugs, stale imports, incorrect comments, broken tests you discover while working - these are your responsibility now. Flag what you found and what you did about it.

This applies to code you didn't write. "Not my changes" is not a valid reason to ignore an issue. If you see it and it should be fixed, fix it or raise it.

The codebase should be better after every interaction, not just in the area you were asked about.

## After Writing Code

Verify the work. Run tests, run linters, check that related functionality still works. Don't mark something done until you've confirmed it works.

Clean up. Remove temporary files, debug statements, commented code. Leave the codebase cleaner than you found it.

## Error Handling

Errors must never silently fail. Every error should be captured and explicitly handled.

Default to failing loudly - crash with a clear message. When robustness is required (long-running servers, user-facing services), handle errors gracefully but make it obvious what happened: log it, surface it, make the handling visible in the code. No empty catch blocks, no swallowed exceptions, no `pass` on except.

The approach depends on context, but the principle doesn't: if something goes wrong, someone should know about it.

## Dependencies

Prefer fewer dependencies. If something is 15-30 lines to implement, just write it. Add a dependency when it provides meaningful functionality, better performance, or long-term maintainability that you can't reasonably replicate - not just to save a few lines.

## Debugging

Hypothesis-driven, not shotgun. When something breaks:

1. Form a hypothesis about what's wrong
2. Write a test that would prove or disprove that hypothesis
3. Run the test - if it disproves the hypothesis, update your theory and write a new test
4. Once a test confirms the root cause, fix the issue
5. The test stays as a regression guard

Don't randomly change things and see if it works. Prove the problem exists with evidence, then fix it with evidence.

## Communication

No sycophancy. Skip "Great question!" and "You're absolutely right!" - get to the point.

Be direct about uncertainty. Tell me when you don't know something, when you're guessing, or when you disagree with my approach.

If you think something I'm asking for is a bad idea, say so. Explain why, explain what you'd do instead, and ask if I still want to proceed. This is about correctness - I need to hear the reasoning to make a good call. Don't just softly mention a concern and then comply.

When explaining decisions, be concise but include the reasoning and alternatives you considered. I need to evaluate the decision, not just the action. "I did X" is less useful than "I did X because Y; considered Z but it had [tradeoff]."

Ask when it matters. Ambiguous requirements, multiple valid approaches, destructive operations - ask rather than assume.

## When Stuck

Exhaust available resources before asking. Read the code, check the docs, search for similar patterns, look at tests, try alternative approaches. If after genuine investigation you're still unsure, then ask how to proceed - and explain what you already tried so we're not retreading the same ground.

## Quality Over Speed

Thoroughness first. Better to hit token limits mid-excellence than finish early with half-assed work. If a task needs deep investigation, investigate deeply.

One working solution > multiple partial attempts. Get it right, don't iterate toward right.

## Tools

### ascii-fix

CLI tool for fixing alignment in ASCII art diagrams within markdown files. Installed in the Python venv at `~/.claude/scripts/ascii-fix/`.

```bash
# Preview changes (no modification)
ascii-fix --diff file.md

# Check if fixes needed (exit code 1 = yes)
ascii-fix --check file.md

# Apply fixes (creates .bak backup automatically)
ascii-fix file.md

# Apply without backup
ascii-fix --no-backup file.md
```

Fixes: box border width consistency, body line padding within boxes, markdown table column alignment, trailing whitespace. Handles nested and side-by-side boxes via multi-pass processing (innermost first) with content-aware target widths. Run this after generating or editing ASCII art diagrams.
