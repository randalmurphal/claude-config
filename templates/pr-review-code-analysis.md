---
template: pr-review-code-analysis
description: Code analysis task for PR review agents
---

Analyze code changes in worktree for correctness and logic issues.

WORKTREE PATH: {worktree_path}

CHANGED FILES:
{changed_files}

YOUR TASKS:
1. Read ALL changed files completely (use Read tool)
2. Trace execution paths through changes
3. Identify logic bugs and unhandled edge cases
4. Find breaking changes (API signatures, behavior, data schema)
5. Map dependencies (what calls this, what this calls)

REPORT FORMAT:
## Breaking Changes
- file.py:line - Description of break, impact, dependencies affected

## Logic Issues
- file.py:line - Bug description, edge case, how to reproduce

## Execution Flow
- Brief explanation of what changes do and data flow

REQUIREMENTS:
- Every finding MUST have file:line reference
- NO style comments - correctness only
- Be specific and actionable
