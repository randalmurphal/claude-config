---
template: pr-review-tests
description: Test coverage analysis task for PR review agents
---

Test coverage analysis in worktree.

WORKTREE PATH: {worktree_path}

CODE FILES CHANGED:
{code_files}

TEST FILES:
{test_files}

YOUR TASKS:
1. Read all code files to understand changes
2. Read all test files to see what's tested
3. Identify untested code paths (new functions, branches, error handlers)
4. Verify test correctness (do tests actually test what they claim?)
5. Find missing edge cases and error scenarios

ANALYSIS:
- Map each changed function to its tests
- Identify code with no corresponding tests
- Check if tests cover error paths (exceptions, None, empty lists)
- Verify integration tests exist for multi-component changes

REPORT FORMAT:
## Missing Test Coverage
- file.py:line-range - Function/code block, what's not tested, why it matters

## Incorrect Tests
- test_file.py:line - What test claims vs what it actually tests, fix needed

## Missing Edge Cases
- file.py:function - Edge case scenario, test suggestion

REQUIREMENTS:
- Focus on NEW/CHANGED code only
- Don't review unchanged code's test coverage
- Verify tests actually test their claimed behavior
