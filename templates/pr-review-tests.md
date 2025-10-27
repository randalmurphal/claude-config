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

1. **Read all code files to understand changes**
   - What new functions were added?
   - What existing functions were modified?
   - What are the edge cases? (None, empty, 0, negative, large values)
   - What are the error scenarios? (DB down, invalid input, network timeout)

2. **Read all test files to see what's tested**
   - Which functions have tests?
   - What scenarios are covered?
   - Are tests actually testing what they claim?

3. **Identify untested code paths**
   - New functions without tests
   - Modified functions without updated tests
   - Error handlers not tested
   - Edge cases not tested

4. **Verify test correctness**
   - Does test actually test claimed behavior?
   - Is test using proper mocks? (external dependencies mocked)
   - Is test too broad? (integration test disguised as unit test)
   - Is test asserting on correct variable?

5. **Find missing edge cases and error scenarios**
   - What happens with None, empty list, 0, negative numbers?
   - What happens when DB query returns nothing?
   - What happens when external API fails?
   - What happens with Unicode, very large inputs, special characters?

6. **Check test organization**
   - 1:1 file mapping (correct location)?
   - Tests grouped appropriately?
   - Parametrized tests for multiple similar cases?
   - Integration tests in right location?

## ANALYSIS

**Map each changed function to its tests:**
```
Function: calculate_total() in billing.py:45-67
Tests:
  ✅ test_calculate_total_happy_path() - covers basic case
  ✅ test_calculate_total_with_discount() - covers discount scenario
  ❌ Missing: test with tax_rate=0 (edge case)
  ❌ Missing: test with negative amount (error scenario)
  ❌ Missing: test with None amount (error scenario)
```

**Identify code with no corresponding tests:**
```
New function: process_refund() in billing.py:120-145
  ❌ NO TESTS FOUND
  Risk: Financial logic untested - refunds could double-charge
```

**Check if tests cover error paths:**
```
Function has try/except for DB connection error
Test only covers happy path - doesn't test exception handling
```

**Verify integration tests exist for multi-component changes:**
```
Changes touch: billing.py, invoices.py, payment_gateway.py
Integration test needed: Full billing flow (cart → invoice → payment → confirmation)
Status: ✅ Found in tests/integration/test_billing_flow.py
```

## MANDATORY REASONING FORMAT

For EVERY finding, you MUST show reasoning steps:

Example:
{
  "finding": {
    "file": "billing.py",
    "function": "process_refund()",
    "issue": "No tests found"
  },
  "reasoning_chain": [
    "STEP 1: Read billing.py:120-145 - found process_refund() function",
    "STEP 2: grep 'test_process_refund' in tests/ - no matches",
    "STEP 3: Read tests/unit/test_billing.py - no refund tests",
    "STEP 4: Function handles financial logic (critical)",
    "STEP 5: No tests = untested financial code",
    "CONCLUSION: Critical test gap"
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
  "confidence_reasoning": "Strong evidence (grep + file read) but might have missed test location"
}

## RESPONSE FORMAT

**Return ONLY valid JSON (no markdown, no prose):**

```json
{
  "status": "COMPLETE",
  "agent_metadata": {
    "agent_type": "test-coverage-analyzer",
    "files_analyzed": ["billing.py", "tests/unit/test_billing.py"],
    "grep_searches_performed": [
      "grep -r 'test_process_refund' found 0 matches",
      "grep -r 'def process_refund' found 1 match"
    ],
    "execution_traces": [
      "process_refund() → validate() → db.update()"
    ]
  },
  "missing_test_coverage": [
    {
      "file": "path/to/file.py",
      "line_range": "120-145",
      "function": "process_refund()",
      "reason": "New function with NO tests",
      "risk": "Financial logic untested - refunds could double-charge or fail silently",
      "test_file_should_be": "tests/unit/test_billing.py",
      "scenarios_to_test": [
        "Happy path: successful refund",
        "Error: insufficient balance",
        "Error: refund already processed (idempotency)",
        "Edge case: refund amount = 0",
        "Edge case: refund > original amount"
      ],
      "severity": "critical"
    }
  ],
  "incorrect_tests": [
    {
      "file": "tests/unit/test_billing.py",
      "line": 34,
      "test_name": "test_calculate_total()",
      "claimed_behavior": "Test calculates total with tax",
      "actual_behavior": "Test asserts on subtotal, not total (wrong variable)",
      "evidence": "assert result.subtotal == 100  # Should be: assert result.total == 110",
      "fix": "Change assertion to: assert result.total == expected_total",
      "severity": "high"
    },
    {
      "file": "tests/integration/test_billing_flow.py",
      "line": 67,
      "test_name": "test_end_to_end_billing()",
      "claimed_behavior": "Integration test with real DB",
      "actual_behavior": "Uses mocked DB (not real integration test)",
      "evidence": "@patch('billing.db.insert') # Mocking defeats purpose of integration test",
      "fix": "Remove mock, use real test database",
      "severity": "medium"
    }
  ],
  "missing_edge_cases": [
    {
      "file": "path/to/file.py",
      "function": "calculate_discount(price, percent)",
      "existing_tests": ["test_calculate_discount() - tests 10% on $100"],
      "missing_cases": [
        "percent = 0 (edge case: no discount)",
        "percent = 100 (edge case: free)",
        "percent > 100 (error: invalid discount)",
        "percent < 0 (error: negative discount)",
        "price = 0 (edge case: free item)",
        "price < 0 (error: negative price)"
      ],
      "test_file": "tests/unit/test_pricing.py",
      "suggestion": "Use @pytest.mark.parametrize to test all edge cases",
      "severity": "medium"
    }
  ],
  "missing_error_scenarios": [
    {
      "file": "path/to/file.py",
      "line_range": "45-67",
      "function": "fetch_user_data(user_id)",
      "error_handling_code": "try:\n    data = db.find_one(...)\nexcept pymongo.errors.ConnectionFailure:\n    LOG.error(...)\n    raise",
      "missing_tests": [
        "Test DB connection failure (should raise with helpful message)",
        "Test DB timeout (should not hang forever)",
        "Test user not found (should return None or raise NotFoundError)"
      ],
      "severity": "high"
    }
  ],
  "test_coverage_summary": {
    "new_functions": {
      "total": 5,
      "tested": 3,
      "untested": 2,
      "untested_list": ["process_refund()", "validate_payment()"]
    },
    "modified_functions": {
      "total": 8,
      "tests_updated": 6,
      "tests_not_updated": 2,
      "not_updated_list": ["calculate_total()", "apply_discount()"]
    },
    "edge_cases_covered": "60%",
    "error_scenarios_covered": "40%"
  },
  "integration_test_gaps": [
    {
      "components_changed": ["billing.py", "invoices.py", "payment_gateway.py"],
      "integration_test_needed": "Full billing flow (cart → invoice → payment → confirmation)",
      "current_status": "Missing - only unit tests exist",
      "risk": "Components may work individually but fail when integrated",
      "test_file_should_be": "tests/integration/test_billing_flow.py",
      "severity": "high"
    }
  ],
  "needs_verification": [
    {
      "file": "tests/unit/test_auth.py",
      "line": 89,
      "test_name": "test_token_validation()",
      "concern": "Test might be testing mock, not real validation logic",
      "uncertainty": "Can't determine if mock is set up correctly",
      "verification_needed": "Run test and verify it catches invalid tokens",
      "severity": "uncertain"
    }
  ],
  "reasoning_for_each_finding": {
    "missing_coverage_1": {
      "reasoning_chain": [
        "STEP 1: Read billing.py:120-145 - found process_refund()",
        "STEP 2: grep 'test_process_refund' - no matches",
        "STEP 3: Read test_billing.py - confirmed no refund tests",
        "STEP 4: Function is financial (critical)",
        "CONCLUSION: Critical untested function"
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
    "Good test coverage for core billing logic (98%)",
    "Edge cases tested: None, empty list, 0, negative values",
    "Error scenarios tested: DB down, invalid input",
    "Integration tests exist for multi-component changes"
  ]
}
```

## SEVERITY GUIDELINES

- **critical**: New critical functions untested (payment, auth, data integrity)
- **high**: Missing tests for modified functions, incorrect tests, missing error scenarios
- **medium**: Missing edge cases, test organization issues, incomplete parametrization
- **low**: Minor improvements (more descriptive names, better fixtures)
- **uncertain**: Test looks wrong but can't confirm without running

## IMPORTANT RULES

1. **Focus on NEW/CHANGED code only** - don't review unchanged code's test coverage
2. **Verify tests actually test their claimed behavior** - read assertions carefully
3. **Check if mocks are appropriate** - unit tests mock external, integration don't
4. **Map every function to its tests** - systematic coverage check
5. **Distinguish risk levels** - untested payment logic = critical, untested util = low
6. **If test looks suspicious but uncertain, flag as needs_verification**
7. **Count what's covered vs missing** - provide percentages in summary

## TEST CORRECTNESS CHECK

**Bad test (asserts on wrong variable):**
```python
def test_calculate_total():
    result = calculate_total(100, tax_rate=0.1)
    assert result.subtotal == 100  # ❌ WRONG - should check result.total == 110
```

**Bad test (too broad - integration disguised as unit):**
```python
@patch('db.connection')  # ❌ WRONG - integration test should use real DB
def test_end_to_end_flow(mock_db):
    ...
```

**Bad test (mocking function under test):**
```python
@patch('billing.calculate_total')  # ❌ WRONG - don't mock what you're testing
def test_process_order(mock_calc):
    ...
```

**Good test (properly isolated):**
```python
@patch('billing.send_email')  # ✅ GOOD - mock external dependency
@patch('billing.save_to_db')  # ✅ GOOD - mock DB
def test_process_order(mock_db, mock_email):
    result = process_order(order_data)
    assert result.total == 110  # Test actual function logic
    mock_email.assert_called_once()  # Verify side effects
```

## EDGE CASES TO CHECK

**For every function, check tests for:**
- **None:** Does function handle None gracefully?
- **Empty:** Empty list [], empty dict {}, empty string ""
- **Zero:** Numeric 0, could cause division by zero
- **Negative:** Negative numbers where positive expected
- **Large:** Very large numbers (overflow?), very long strings
- **Unicode:** Non-ASCII characters, emojis
- **Duplicates:** Duplicate items in list
- **Boundary:** Min/max values (INT_MAX, empty vs 1-item list)

## ERROR SCENARIOS TO CHECK

**For functions with try/except:**
- Test the exception path (not just happy path)
- Verify error message is helpful
- Verify cleanup happens (files closed, connections released)

**For functions with external calls:**
- Test when external service is down
- Test when external service returns error
- Test when external service times out

## WHAT'S NOT A TEST ISSUE

- Code style in production code (reviewed elsewhere)
- Missing docstrings in production code
- Performance issues in production code
- **Focus only on test coverage and test correctness**

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
