---
template: pr-review-performance
description: Performance analysis task for PR review agents
---

Performance impact analysis in worktree.

WORKTREE PATH: {worktree_path}

CHANGED FILES:
{changed_files}

ANALYZE:
1. Database queries (new queries, changed queries, missing indexes)
2. N+1 query problems (queries inside loops)
3. Algorithm complexity changes (O(n) → O(n²))
4. Memory allocation patterns (large data structures, leaks)
5. Caching regressions (removed caching, missed opportunities)
6. Batch operation changes (removed batching, inefficient processing)

REVIEW METHOD:
- Read each changed file completely
- Find all DB operations (find, find_one, update_many, aggregate)
- Check for loops containing DB calls
- Compare old vs new approach for same functionality

REPORT FORMAT:
## Performance Regressions (fix)
- file.py:line - Problem, impact estimate, fix

## Optimization Opportunities (consider)
- file.py:line - Current approach, better approach, benefit estimate

REQUIREMENTS:
- QUANTIFY impact (e.g., "adds N+1 queries = 1000 extra DB calls")
- Compare before/after performance characteristics
- Focus on measurable regressions
