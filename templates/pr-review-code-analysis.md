---
template: pr-review-code-analysis
description: Code analysis task for PR review agents
---

Analyze code changes in worktree for correctness and logic issues.

WORKTREE PATH: {worktree_path}

CHANGED FILES:
{changed_files}

EXISTING MR COMMENTS:
{mr_comments}

## CRITICAL STANDARDS

**LOAD SKILL FIRST**: pr-review-standards

Key rules from skill:
- try/except ONLY for connection errors (network, DB, cache, external APIs)
- Logging: `logging.getLogger(__name__)` (not print or root logger)
- Type hints required, 80 char limit
- NO assumptions - flag as "needs_verification" if uncertain
- Every finding needs file:line + evidence

**For complete standards:** Load pr-review-standards skill

## SUPPORTING SKILLS

- pr-review-standards: Code quality standards and verification rules
- pr-review-evidence-formats: What counts as valid evidence
- pr-review-common-patterns: Common false positives and issue patterns

Load on-demand if you need examples or guidance.

## YOUR TASKS

1. **Read ALL changed files completely** (use Read tool)
   - Don't skim - read full functions and their context
   - Understand data flow and execution paths

2. **Trace execution paths through changes**
   - What happens on happy path?
   - What happens on error paths?
   - What happens with edge cases (None, empty, 0, negative)?

3. **Identify logic bugs and unhandled edge cases**
   - Off-by-one errors
   - Division by zero
   - Null/None dereferences
   - Empty list/dict access
   - Integer overflow
   - Unicode handling
   - Race conditions

4. **Find breaking changes**
   - API signature changes (added/removed parameters)
   - Behavior changes (function returns different type)
   - Data schema changes (field renames, type changes)
   - Removed functions/classes still referenced elsewhere

5. **Map dependencies**
   - What calls this changed code? (use Grep to find callers)
   - What does this changed code call?
   - What DB operations does it perform?
   - What external services does it depend on?

6. **Check error handling**
   - Are exceptions caught appropriately?
   - Are error messages helpful for debugging?
   - Are errors logged with sufficient context?
   - **CRITICAL:** try/except should ONLY be used for connection errors (network, DB, cache, external APIs)
     - Network: `requests.Timeout`, `requests.ConnectionError`, `requests.HTTPError`
     - Database: `pymongo` errors, `sqlalchemy` errors, `redis` errors
     - **NEVER wrap:** `dict.get()`, file I/O, JSON parsing, type conversions, list operations

7. **Address existing MR comments**
   - Check if concerns raised in MR comments were resolved
   - Report: ✅ Resolved, ⚠️ Partially resolved, ❌ Not addressed

## MANDATORY REASONING FORMAT

For EVERY finding, you MUST show reasoning steps:

Example:
{
  "finding": {
    "file": "billing.py",
    "line": 45,
    "issue": "Division by zero"
  },
  "reasoning_chain": [
    "STEP 1: Read billing.py:40-55 - found calculate_average() function",
    "STEP 2: Traced data source - count comes from len(items)",
    "STEP 3: Line 45: average = total / count",
    "STEP 4: No check for empty items list (count = 0)",
    "STEP 5: Tested scenario: calculate_average([]) crashes with ZeroDivisionError",
    "CONCLUSION: Unhandled division by zero"
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
  "confidence_reasoning": "Strong evidence (code snippet + trace) but didn't test exploit"
}

## RESPONSE FORMAT

**Return ONLY valid JSON (no markdown, no prose):**

```json
{
  "status": "COMPLETE",
  "agent_metadata": {
    "agent_type": "code-analysis",
    "files_analyzed": ["billing.py", "invoices.py"],
    "grep_searches_performed": [
      "grep -r 'calculate_total' found 15 matches",
      "grep -r 'def process_order' found 3 matches"
    ],
    "execution_traces": [
      "User cart → calculate_total() → apply_discounts() → DB update"
    ]
  },
  "breaking_changes": [
    {
      "file": "path/to/file.py",
      "line": 123,
      "change": "calculate_total() added required parameter 'tax_rate'",
      "evidence": "def calculate_total(amount, tax_rate): # was: def calculate_total(amount):",
      "impact": "All callers must be updated to pass tax_rate",
      "affected_files": ["invoices.py:89", "reports.py:145"],
      "severity": "critical"
    }
  ],
  "logic_issues": [
    {
      "file": "path/to/file.py",
      "line": 67,
      "issue": "Division by zero when count is 0",
      "evidence": "average = total / count  # count can be 0 if list is empty",
      "reproduce": "Call with empty list: calculate_average([])",
      "fix": "Add check: if count == 0: return 0.0",
      "severity": "high"
    }
  ],
  "improper_try_except": [
    {
      "file": "path/to/file.py",
      "line": 45,
      "issue": "try/except wrapping safe dict.get() operation",
      "evidence": "try:\n    value = data.get('key')\nexcept Exception:\n    value = None",
      "why_wrong": "dict.get() never raises exception - returns None if key missing",
      "fix": "Remove try/except: value = data.get('key')",
      "severity": "medium"
    }
  ],
  "logging_issues": [
    {
      "file": "path/to/file.py",
      "line": 89,
      "issue": "Using print() instead of logging",
      "evidence": "print(f'Processing {item_id}')",
      "fix": "Replace with: LOG.info('Processing item', extra={'item_id': item_id})",
      "severity": "medium"
    }
  ],
  "edge_cases": [
    {
      "file": "path/to/file.py",
      "line": 120,
      "case": "Empty list not handled",
      "evidence": "first_item = items[0]  # crashes if items is empty",
      "fix": "Add check: if not items: return None",
      "severity": "medium"
    }
  ],
  "execution_flow": {
    "summary": "Changes add tax calculation to billing module",
    "data_flow": "User cart → calculate_total(amount, tax_rate) → apply_discounts() → DB update",
    "dependencies": {
      "calls": ["apply_discounts()", "save_to_db()"],
      "called_by": ["checkout_handler()", "invoice_generator()"],
      "db_operations": ["INSERT into orders", "UPDATE users.balance"],
      "external_services": ["payment_gateway.charge()"]
    }
  },
  "mr_comments_addressed": [
    {
      "comment": "Missing validation for negative amounts",
      "status": "resolved",
      "evidence": "Added validation at file.py:78: if amount < 0: raise ValueError"
    },
    {
      "comment": "Should we batch these DB calls?",
      "status": "not_addressed",
      "notes": "Still making N individual calls in loop at file.py:123-130"
    }
  ],
  "needs_verification": [
    {
      "file": "path/to/file.py",
      "line": 200,
      "concern": "Potential race condition in cache update",
      "uncertainty": "Can't determine if lock exists elsewhere",
      "verification_needed": "Check if Redis lock is acquired before this line",
      "severity": "uncertain"
    }
  ],
  "reasoning_for_each_finding": {
    "breaking_change_1": {
      "reasoning_chain": [
        "STEP 1: Read billing.py:123 - calculate_total() signature changed",
        "STEP 2: grep -r 'calculate_total(' found 15 callers",
        "STEP 3: Read invoices.py:89 - caller passes 1 arg, function needs 2",
        "STEP 4: Traced execution - function will raise TypeError",
        "CONCLUSION: Confirmed breaking change"
      ],
      "confidence": 0.95,
      "evidence_quality": "strong"
    },
    "logic_issue_1": {
      "reasoning_chain": [
        "STEP 1: Read file.py:67 - found average = total / count",
        "STEP 2: Traced count source - comes from len(items)",
        "STEP 3: No validation for empty items list",
        "STEP 4: Empty list → count=0 → division by zero",
        "CONCLUSION: Exploitable bug"
      ],
      "confidence": 0.90,
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
    "Good separation of concerns - billing logic separated from display logic",
    "Proper type hints on all new functions",
    "Error messages include helpful context for debugging"
  ]
}
```

## SEVERITY GUIDELINES

- **critical**: Crashes, data corruption, security vulnerabilities, breaking changes without migration
- **high**: Logic bugs with user impact, performance regressions, missing error handling
- **medium**: Code quality issues, improper try/except, logging problems, missing edge cases
- **low**: Style issues, optimization opportunities, minor improvements
- **uncertain**: Can't confirm without human review

## IMPORTANT RULES

1. **Every finding MUST have file:line reference** - no vague claims
2. **Every finding MUST have evidence** - code snippet or trace
3. **NO style comments** - focus on correctness only (PEP 8 checked elsewhere)
4. **Be specific and actionable** - exact fix suggestion, not just "fix this"
5. **If uncertain, flag as needs_verification** - don't claim something is wrong without proof
6. **Context matters** - read entire function, not just the line
7. **Check ALL changed files** - don't skip test files or config files

## ANALYSIS APPROACH

**Progressive investigation:**
1. Start by reading smallest changed file to understand changes
2. Trace data flow through changes
3. Use Grep to find callers (understand impact)
4. Read callers to check for breaking changes
5. Check error paths (what happens when operations fail?)
6. Check edge cases (None, empty, 0, negative, large values)

**If you find >10 issues in one file:** This likely indicates fundamental problems. Flag for architectural discussion rather than nitpicking each issue.

**If you can't determine if something is an issue:** Flag as "needs_verification" with specific question for human review.

## VERIFICATION CHECKLIST (MUST COMPLETE)

Before returning results, verify:

- [ ] I read EVERY file in {changed_files} completely (not skimmed)
- [ ] I checked EVERY function in those files (not just some)
- [ ] I provided file:line for EVERY finding (no vague claims)
- [ ] I included code snippet for EVERY finding (evidence required)
- [ ] I traced execution paths (not just read code statically)
- [ ] I checked for edge cases (None, empty, 0, negative)
- [ ] I used Grep to find references across ENTIRE codebase (not just changed files)
- [ ] I marked uncertain findings as "needs_verification"

RETURN THIS CHECKLIST with your results in `verification_checklist` field.
