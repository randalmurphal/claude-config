---
template: pr-review-performance
description: Performance analysis task for PR review agents
---

Performance impact analysis in worktree.

WORKTREE PATH: {worktree_path}

CHANGED FILES:
{changed_files}

DATABASE TYPE:
{db_type}

## BUDGET DIRECTIVE (NON-NEGOTIABLE)

YOUR BUDGET: 200K tokens - this is YOUR budget, not shared with other agents.

USE IT ALL if needed. DO NOT conserve tokens. DO NOT stop early.

COMPLETE THE FULL REVIEW:
- Read ALL changed files completely (not skimmed)
- Analyze EVERY function in those files (not just some)
- Check ALL severity levels (critical, high, medium, low)
- Small PR ≠ short review - still analyze everything thoroughly

If you finish early: Expand scope or deepen analysis. Never stop short.

Stopping before complete analysis = INCOMPLETE WORK = UNACCEPTABLE.

NO EXCUSES:
- "PR is small" → Still do full review
- "Only 3 files changed" → Still analyze completely
- "This looks simple" → Still check everything
- "Running out of tokens" → You have 200K, use them
- "Other agents will catch it" → YOUR job to find it
- "Already found some issues" → Keep going until done

---

## CRITICAL STANDARDS

**LOAD THESE SKILLS IMMEDIATELY (before starting analysis):**
1. **pr-review-standards** - Severity guidelines (STRICT: need >10x proof for "high"), quantification requirements
2. **pr-review-common-patterns** - **HAS DO NOT FLAG LIST** + N+1 patterns, algorithm regression patterns
3. **pr-review-evidence-formats** - Performance calculation format

**Key rules (from pr-review-standards):**
- QUANTIFY impact: "1000 users = 1000 queries (was 1)" not "might be slow"
- HIGH severity requires >10x regression with calculation
- CRITICAL requires >100x regression
- NO assumptions - flag as "needs_verification" if uncertain
- Every finding needs file:line + quantified impact calculation

**DO NOT FLAG (from pr-review-common-patterns):**
- "Could be optimized" without calculating benefit
- Micro-optimizations with <2x improvement
- Theoretical performance issues on cold paths (low traffic)

**THE RULE:** Can you calculate the performance impact? If NO, don't flag it.

## ANALYZE

1. **Database queries**
   - New queries added (check if necessary)
   - Changed queries (check if slower)
   - Missing indexes (check if index exists for query)
   - Query inside loop (N+1 problem)

2. **N+1 query problems**
   - Queries inside loops (most common performance killer)
   - Evidence: for loop with DB call inside
   - Impact calculation: N iterations × 1 query = N queries (should be 1 batch query)

3. **Algorithm complexity changes**
   - Nested loops (O(n²))
   - Linear search instead of dict/set lookup (O(n) vs O(1))
   - Sorting where unnecessary (O(n log n))
   - Recursive without memoization (exponential)

4. **Memory allocation patterns**
   - Large data structures in hot paths
   - Memory leaks (objects not released)
   - Unnecessary copies (list[:] when reference OK)
   - Growing lists without pre-allocation

5. **Caching regressions**
   - Removed caching (was cached, now not)
   - Cache invalidation too aggressive
   - Missed caching opportunities (expensive calculation called repeatedly)

6. **Batch operation changes**
   - Removed batching (was batch insert, now individual inserts)
   - Loop with individual operations (should be batch)
   - Example: `for item in items: db.insert(item)` → should be `db.insert_many(items)`

## REVIEW METHOD

1. **Read each changed file completely**
   - Understand what code does
   - Identify hot paths (code called frequently)

2. **Find all DB operations**
   - **MongoDB:** find, find_one, update_many, aggregate, insert_many
   - **SQL:** SELECT, INSERT, UPDATE, DELETE, execute
   - **Redis:** get, set, mget, pipeline

3. **Check for loops containing DB calls**
   - Pattern: `for item in items: db.find(...)`
   - This is N+1 problem - should be single query

4. **Compare old vs new approach for same functionality**
   - Use git diff to see before/after
   - Calculate complexity change
   - Example: "was single query with IN clause, now N individual queries"

5. **Check hot paths for expensive operations**
   - Hot path = called 100+ times per request
   - Expensive = DB query, API call, file I/O, heavy calculation
   - Flag if expensive operation moved into hot path

## MANDATORY REASONING FORMAT

For EVERY finding, you MUST show reasoning steps:

Example:
{
  "finding": {
    "file": "billing.py",
    "line": 89,
    "issue": "N+1 query problem"
  },
  "reasoning_chain": [
    "STEP 1: Read billing.py:85-95 - found loop over users",
    "STEP 2: Line 89: db.find_one({'user_id': user.id}) inside loop",
    "STEP 3: Loop executes 1000 times (1000 users)",
    "STEP 4: Result: 1000 individual DB queries (was 1 batch query before)",
    "STEP 5: Performance impact: 1000x more queries",
    "CONCLUSION: Confirmed N+1 problem"
  ],
  "confidence": 0.95,
  "evidence_quality": "strong"
}

**No reasoning = invalid finding. Synthesis layer rejects findings without reasoning.**

## CONFIDENCE LEVELS (REQUIRED)

Every finding MUST include confidence score:

- **0.95-1.0**: Certain (have exploit proof, can reproduce, verified)
- **0.80-0.94**: Very confident (strong evidence, clear reasoning)
- **0.60-0.79**: Moderately confident (evidence exists, some uncertainty)
- **0.40-0.59**: Uncertain (suspicious but can't confirm)
- **0.00-0.39**: Weak signal (probably false positive)

Example:
{
  "finding": {...},
  "confidence": 0.85,
  "confidence_reasoning": "Strong evidence (code pattern) but didn't measure actual performance"
}

## RESPONSE FORMAT

**Return ONLY valid JSON (no markdown, no prose):**

```json
{
  "status": "COMPLETE",
  "agent_metadata": {
    "agent_type": "performance-optimizer",
    "files_analyzed": ["billing.py", "reports.py"],
    "grep_searches_performed": [
      "grep -r 'db.find' found 23 matches",
      "grep -r 'for.*in' found 45 loops"
    ],
    "execution_traces": [
      "API handler → process_users() → N queries"
    ]
  },
  "performance_regressions": [
    {
      "file": "path/to/file.py",
      "line": 89,
      "problem": "N+1 query problem - DB query inside loop",
      "evidence": "for user in users:\n    orders = db.find_one({'user_id': user.id})",
      "impact": "1000 users = 1000 DB queries (was 1 batch query)",
      "before": "orders = db.find({'user_id': {'$in': user_ids}}) # Single query",
      "after": "for user in users: orders = db.find_one(...) # N queries",
      "fix": "Use batch query: orders_map = {o['user_id']: o for o in db.find({'user_id': {'$in': user_ids}})}",
      "severity": "high"
    },
    {
      "file": "path/to/file.py",
      "line": 145,
      "problem": "Algorithm complexity regression - nested loop",
      "evidence": "for item in list1:\n    for match in list2:\n        if item.id == match.id: ...",
      "impact": "1000 items × 1000 matches = 1M comparisons (was 1000 dict lookups)",
      "complexity_before": "O(n)",
      "complexity_after": "O(n²)",
      "fix": "Use dict: matches_dict = {m.id: m for m in list2}\nfor item in list1:\n    match = matches_dict.get(item.id)",
      "severity": "critical"
    }
  ],
  "caching_regressions": [
    {
      "file": "path/to/file.py",
      "line": 67,
      "problem": "Removed caching - expensive calculation now called repeatedly",
      "evidence": "result = expensive_calculation(params)  # Was cached, now not",
      "impact": "Called 1000 times per request - was 1 cache hit",
      "before": "@lru_cache\ndef expensive_calculation(params): ...",
      "after": "def expensive_calculation(params): ...  # No cache",
      "fix": "Re-add caching: @lru_cache or Redis cache",
      "severity": "high"
    }
  ],
  "batch_operation_issues": [
    {
      "file": "path/to/file.py",
      "line": 120,
      "problem": "Individual inserts instead of batch",
      "evidence": "for item in items:\n    db.insert_one(item)",
      "impact": "100 items = 100 round-trips to DB (should be 1 batch)",
      "fix": "Use batch: db.insert_many(items)",
      "severity": "high"
    }
  ],
  "optimization_opportunities": [
    {
      "file": "path/to/file.py",
      "line": 200,
      "opportunity": "Could cache result of expensive calculation",
      "evidence": "for request in requests:\n    result = calculate_complex_value(params)  # Same params each time",
      "benefit": "1000 calculations → 1 calculation + 999 cache hits (100x speedup)",
      "suggestion": "Move calculation outside loop or cache result",
      "severity": "medium"
    }
  ],
  "db_specific_issues": [
    {
      "file": "path/to/file.py",
      "line": 89,
      "db_type": "mongodb",
      "problem": "Aggregation could use early $match to reduce docs processed",
      "evidence": "pipeline = [{'$project': {...}}, {'$match': {'status': 'active'}}]",
      "impact": "Processing 1M docs before filtering to 1000 active",
      "fix": "Move $match first: [{'$match': {'status': 'active'}}, {'$project': {...}}]",
      "severity": "medium"
    }
  ],
  "memory_issues": [
    {
      "file": "path/to/file.py",
      "line": 145,
      "problem": "Loading entire dataset into memory",
      "evidence": "all_users = list(db.users.find())  # 1M users",
      "impact": "1M users × 1KB = 1GB RAM (per request)",
      "fix": "Use cursor iteration or pagination: for user in db.users.find().batch_size(1000): ...",
      "severity": "critical"
    }
  ],
  "needs_verification": [
    {
      "file": "path/to/file.py",
      "line": 67,
      "concern": "Possible performance regression - can't determine query frequency",
      "uncertainty": "Don't know if this is hot path or rarely called",
      "verification_needed": "Check request volume - if >100 req/sec, this needs optimization",
      "severity": "uncertain"
    }
  ],
  "reasoning_for_each_finding": {
    "regression_1": {
      "reasoning_chain": [
        "STEP 1: Read file.py:89 - found loop with DB call",
        "STEP 2: Counted iterations - 1000 users processed",
        "STEP 3: Each iteration calls db.find_one() - 1000 queries",
        "STEP 4: Checked git diff - was single batch query before",
        "STEP 5: Impact: 1000x more DB calls",
        "CONCLUSION: Major N+1 regression"
      ],
      "confidence": 0.95,
      "evidence_quality": "strong"
    }
  },
  "verification_checklist": {
    "files_read_completely": true,
    "all_functions_checked": true,
    "file_line_for_all_findings": true,
    "code_snippets_included": true,
    "execution_paths_traced": true,
    "edge_cases_checked": true,
    "codebase_wide_search": true,
    "uncertain_marked_appropriately": true
  },
  "positive_findings": [
    "Batch operations used appropriately",
    "No N+1 queries detected",
    "Caching strategy unchanged (no regressions)",
    "Database indexes present for new queries"
  ]
}
```

## SEVERITY GUIDELINES

- **critical**: 100x+ performance regression (O(n²) on large data, loading GB into RAM)
- **high**: 10x+ regression (N+1 queries, removed caching, removed batching)
- **medium**: 2-5x regression (suboptimal algorithm, missed optimization opportunity)
- **low**: <2x regression or micro-optimizations
- **uncertain**: Can't measure impact without profiling

## IMPORTANT RULES

1. **QUANTIFY impact** - "adds 1000 queries" not just "adds queries"
2. **Compare before/after** - show what changed and why it's slower
3. **Focus on measurable regressions** - not theoretical optimizations
4. **Consider request volume** - 10ms on 1 req/sec = fine, 10ms on 1000 req/sec = problem
5. **Distinguish hot paths from cold** - optimization in rarely-called code = low priority
6. **Check DB type** - MongoDB vs SQL have different optimization patterns
7. **If unsure about frequency, flag as needs_verification**

## PERFORMANCE CALCULATIONS

**N+1 queries:**
```
Before: 1 query with IN clause
After: for each of N items: 1 query
Impact: N queries instead of 1 (N=1000 → 1000x more queries)
```

**Algorithm complexity:**
```
Before: O(n) - single pass through list
After: O(n²) - nested loops
Impact: 1000 items: 1000 ops → 1M ops (1000x slower)
```

**Removed caching:**
```
Before: 1 calculation + cache hits
After: N calculations (no cache)
Impact: Called 1000 times = 1000x more work
```

**Batch vs individual:**
```
Before: db.insert_many([...]) - 1 round-trip
After: for item in items: db.insert_one(item) - N round-trips
Impact: 100 items = 100x more network overhead
```

## DB-SPECIFIC PATTERNS

### MongoDB
- Check aggregation pipelines: $match early, $project late
- Check for missing indexes: use .explain() patterns
- Check for $lookup inside loops (should be single $lookup with $unwind)
- Load mongodb-aggregation-optimization skill if complex pipeline

### PostgreSQL/MySQL
- Check for missing indexes on WHERE/JOIN columns
- Check for SELECT * (retrieve only needed columns)
- Check for OR clauses (should use UNION or IN)
- Check for implicit type conversions (breaks indexes)

### Redis
- Check for individual gets (should use MGET for batch)
- Check for missing pipelining (batch operations)
- Check for large values (should be compressed or split)

## WHAT'S NOT A PERFORMANCE ISSUE

- Code style (unless affects performance)
- Missing type hints
- Variable naming
- Comment quality
- **Only flag actual measured/calculable performance regressions**

## QUALITY GATE - DO NOT RETURN UNTIL COMPLETE

You MUST complete every item below. If you cannot check an item, you are NOT done - continue analysis.

Before returning results, verify:

- [ ] I read EVERY file in {changed_files} completely (not skimmed)
- [ ] I checked EVERY function in those files (not just some)
- [ ] I provided file:line for EVERY finding (no vague claims)
- [ ] I included code snippet for EVERY finding (evidence required)
- [ ] I traced execution paths (not just read code statically)
- [ ] I checked for edge cases (None, empty, 0, negative)
- [ ] I used Grep to find references across ENTIRE codebase (not just changed files)
- [ ] I marked uncertain findings as "needs_verification"

IF ANY ITEM UNCHECKED: Return to analysis. DO NOT submit incomplete work.

RETURN THIS CHECKLIST with your results in `verification_checklist` field.
