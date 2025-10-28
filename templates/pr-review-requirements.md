---
template: pr-review-requirements
description: Jira ticket requirements verification task for PR review agents
---

Verify that PR changes implement all Jira ticket requirements.

WORKTREE PATH: {worktree_path}

CHANGED FILES:
{changed_files}

JIRA TICKET CONTENT:
{ticket_content}

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
1. **pr-review-standards** - Evidence requirements, severity guidelines
2. **pr-review-common-patterns** - **HAS DO NOT FLAG LIST**

**Key rules (from pr-review-standards):**
- Compare code against ticket requirements (ALL sections: Description, Acceptance Criteria, Test Plan, Comments)
- Flag MISSING requirements (code doesn't implement ticket)
- Flag EXTRA functionality not in ticket (scope creep)
- NO assumptions - flag as "needs_verification" if uncertain
- Every finding needs file:line + ticket requirement reference

**DO NOT FLAG (from pr-review-common-patterns):**
- Implementation details different from your preference
- Code quality issues (reviewed elsewhere)
- "Could be implemented differently" (subjective)

**THE RULE:** Does ticket require this? If NO (or uncertain), don't flag it.

## YOUR TASKS

1. **Parse Jira ticket for requirements**
   - Extract all explicit requirements (listed in description, acceptance criteria)
   - Extract implicit requirements (mentioned in comments, related tickets)
   - Group by feature/functionality

2. **Map each requirement to code changes**
   - Find file:line where requirement is implemented
   - If requirement not implemented → flag as MISSING
   - If partially implemented → flag as PARTIAL with gap description

3. **Verify tests exist for each requirement**
   - Does test file exist for implementing file?
   - Does test cover the requirement scenario?
   - If no test → flag test gap

4. **Check for scope creep**
   - Are there changes NOT in ticket?
   - Are they related (bug fixes discovered) or unrelated (scope creep)?

5. **Flag ambiguous requirements**
   - If ticket requirement is vague/unclear
   - If implementation doesn't match ticket (but might be correct)
   - Needs human clarification

## ANALYSIS APPROACH

### Step 1: Extract Requirements from Ticket

**Example ticket parsing:**
```
Ticket: Add tax calculation to billing

Description:
- Calculate tax based on user's state
- Support both sales tax and VAT
- Store tax rate in user preferences

Acceptance Criteria:
- [ ] Tax calculated correctly for US states
- [ ] Tax calculated correctly for EU VAT
- [ ] User can set tax rate preference
- [ ] Tax shown separately on invoice

Requirements extracted:
1. Calculate tax based on state/country
2. Support sales tax (US)
3. Support VAT (EU)
4. Store tax rate in user.preferences
5. Display tax separately on invoice
```

### Step 2: Map to Code Changes

**For each requirement, find implementation:**
```
Requirement 1: Calculate tax based on state/country
✅ IMPLEMENTED:
  - File: billing.py:45-67
  - Code: def calculate_tax(amount, location): ...
  - Test: tests/unit/test_billing.py:89-120

Requirement 2: Support sales tax (US)
✅ IMPLEMENTED:
  - File: billing.py:52-55
  - Code: if location.country == 'US': return amount * state_tax_rates[location.state]
  - Test: tests/unit/test_billing.py:95

Requirement 3: Support VAT (EU)
⚠️ PARTIALLY IMPLEMENTED:
  - File: billing.py:56-59
  - Code: if location.country in EU_COUNTRIES: return amount * 0.20
  - Gap: Hardcoded 20% VAT - should vary by country
  - Missing: Different VAT rates for different EU countries

Requirement 4: Store tax rate in user.preferences
❌ MISSING:
  - No code found implementing user preference storage
  - No database migration adding preference field
  - No API endpoint for setting preference

Requirement 5: Display tax separately on invoice
✅ IMPLEMENTED:
  - File: invoices.py:123-130
  - Code: invoice.tax = calculate_tax(...); invoice.total = subtotal + tax
  - Test: tests/integration/test_invoicing.py:67
```

### Step 3: Check for Scope Creep

```
Changes NOT in ticket:
- added discount calculation to billing.py:78-95
  - Analysis: Related - discovered bug while implementing tax
  - Verdict: ACCEPTABLE (bug fix)

- refactored invoice.py formatting
  - Analysis: Unrelated to tax calculation
  - Verdict: SCOPE CREEP (should be separate PR)
```

## MANDATORY REASONING FORMAT

For EVERY finding, you MUST show reasoning steps:

Example:
{
  "finding": {
    "requirement": "REQ-4: Store tax rate in user preferences",
    "status": "MISSING"
  },
  "reasoning_chain": [
    "STEP 1: Read ticket - requirement: store tax rate in user.preferences",
    "STEP 2: grep 'tax_rate' in models/ - no user.preferences field",
    "STEP 3: grep 'preferences' in migrations/ - no migration found",
    "STEP 4: Read billing.py - no code reads preferences",
    "STEP 5: Requirement completely unimplemented",
    "CONCLUSION: Critical requirement missing"
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
  "confidence_reasoning": "Strong evidence (grep + file read) but might have missed implementation location"
}

## RESPONSE FORMAT

**Return ONLY valid JSON (no markdown, no prose):**

```json
{
  "status": "COMPLETE",
  "agent_metadata": {
    "agent_type": "requirements-verifier",
    "files_analyzed": ["billing.py", "invoices.py", "models.py"],
    "grep_searches_performed": [
      "grep -r 'tax_rate' found 15 matches",
      "grep -r 'user.preferences' found 0 matches"
    ],
    "execution_traces": [
      "Ticket REQ-1 → billing.py:45 (implemented)",
      "Ticket REQ-4 → not found (missing)"
    ]
  },
  "ticket_id": "INT-3877",
  "ticket_summary": "Add tax calculation to billing",
  "requirements_extracted": [
    {
      "id": "REQ-1",
      "description": "Calculate tax based on state/country",
      "source": "Ticket description"
    },
    {
      "id": "REQ-2",
      "description": "Support sales tax (US)",
      "source": "Acceptance criteria #1"
    },
    {
      "id": "REQ-3",
      "description": "Support VAT (EU)",
      "source": "Acceptance criteria #2"
    },
    {
      "id": "REQ-4",
      "description": "Store tax rate in user preferences",
      "source": "Ticket description"
    },
    {
      "id": "REQ-5",
      "description": "Display tax separately on invoice",
      "source": "Acceptance criteria #4"
    }
  ],
  "implementation_mapping": [
    {
      "requirement_id": "REQ-1",
      "status": "IMPLEMENTED",
      "file": "billing.py",
      "line_range": "45-67",
      "evidence": "def calculate_tax(amount, location): ...",
      "test_file": "tests/unit/test_billing.py",
      "test_line_range": "89-120",
      "test_coverage": "complete"
    },
    {
      "requirement_id": "REQ-2",
      "status": "IMPLEMENTED",
      "file": "billing.py",
      "line_range": "52-55",
      "evidence": "if location.country == 'US': return amount * state_tax_rates[location.state]",
      "test_file": "tests/unit/test_billing.py",
      "test_line_range": "95",
      "test_coverage": "complete"
    },
    {
      "requirement_id": "REQ-3",
      "status": "PARTIAL",
      "file": "billing.py",
      "line_range": "56-59",
      "evidence": "if location.country in EU_COUNTRIES: return amount * 0.20",
      "gap": "Hardcoded 20% VAT - should vary by country (Germany=19%, France=20%, UK=20%, etc)",
      "missing": "Different VAT rates for different EU countries",
      "test_file": "tests/unit/test_billing.py",
      "test_line_range": "98",
      "test_coverage": "incomplete - only tests 20% rate",
      "severity": "high"
    },
    {
      "requirement_id": "REQ-4",
      "status": "MISSING",
      "reason": "No code found implementing user preference storage",
      "missing_components": [
        "Database migration to add user.tax_rate_preference field",
        "API endpoint to set/get tax preference",
        "UI for user to configure preference",
        "Code to read preference and apply to calculation"
      ],
      "test_file": null,
      "test_coverage": "none",
      "severity": "critical"
    },
    {
      "requirement_id": "REQ-5",
      "status": "IMPLEMENTED",
      "file": "invoices.py",
      "line_range": "123-130",
      "evidence": "invoice.tax = calculate_tax(...); invoice.total = subtotal + tax",
      "test_file": "tests/integration/test_invoicing.py",
      "test_line_range": "67",
      "test_coverage": "complete"
    }
  ],
  "scope_creep": [
    {
      "file": "billing.py",
      "line_range": "78-95",
      "change": "Added discount calculation logic",
      "in_ticket": false,
      "related": true,
      "justification": "Bug fix discovered while implementing tax - discount was applied before tax instead of after",
      "verdict": "ACCEPTABLE",
      "severity": "low"
    },
    {
      "file": "invoice.py",
      "line_range": "200-250",
      "change": "Refactored invoice formatting",
      "in_ticket": false,
      "related": false,
      "justification": null,
      "verdict": "SCOPE_CREEP - should be separate PR",
      "severity": "medium"
    }
  ],
  "ambiguous_requirements": [
    {
      "requirement": "Support both sales tax and VAT",
      "ambiguity": "Ticket doesn't specify what happens for users in both US and EU",
      "current_implementation": "Code assumes location is either US or EU, not both",
      "needs_clarification": "Should we support users with multiple locations? Or just primary location?",
      "severity": "medium"
    }
  ],
  "test_gaps": [
    {
      "requirement_id": "REQ-3",
      "gap": "Only tests 20% VAT rate - missing tests for different EU countries",
      "risk": "Could break for Germany (19%), Italy (22%), etc",
      "severity": "high"
    },
    {
      "requirement_id": "REQ-4",
      "gap": "No tests (requirement not implemented)",
      "risk": "Critical feature untested",
      "severity": "critical"
    }
  ],
  "summary": {
    "total_requirements": 5,
    "implemented": 3,
    "partially_implemented": 1,
    "missing": 1,
    "implementation_rate": "60%",
    "test_coverage_rate": "60%",
    "recommendation": "REQUEST_CHANGES - missing critical requirement REQ-4, partial implementation of REQ-3"
  },
  "needs_verification": [
    {
      "requirement_id": "REQ-1",
      "concern": "Tax calculation might not handle edge cases",
      "uncertainty": "Can't determine from ticket if 0% tax (tax-exempt) should be supported",
      "verification_needed": "Check with product owner if tax-exempt purchases supported",
      "severity": "uncertain"
    }
  ],
  "reasoning_for_each_finding": {
    "req_4_missing": {
      "reasoning_chain": [
        "STEP 1: Read ticket REQ-4 - store tax_rate in preferences",
        "STEP 2: grep 'user.preferences' - no matches",
        "STEP 3: grep migration files - no preferences field added",
        "STEP 4: Read billing.py - no preferences access",
        "CONCLUSION: Requirement not implemented"
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
    "Core tax calculation implemented correctly",
    "Good test coverage for implemented requirements (3/3 tested)",
    "Tax displayed separately on invoice as requested"
  ]
}
```

## SEVERITY GUIDELINES

- **critical**: Missing core functionality, no implementation of main requirement
- **high**: Partial implementation with significant gaps, missing tests for requirement
- **medium**: Ambiguous requirements, scope creep, minor gaps in implementation
- **low**: Edge cases not covered, documentation missing
- **uncertain**: Can't determine if requirement met without clarification

## IMPORTANT RULES

1. **Extract ALL requirements from ticket** - not just acceptance criteria
2. **Map EVERY requirement to code** - systematic coverage check
3. **Distinguish PARTIAL from MISSING** - partial = some code, missing = no code
4. **Verify tests exist** - requirement implemented but not tested = gap
5. **Flag scope creep** - changes not in ticket (but distinguish related vs unrelated)
6. **If requirement ambiguous, flag for clarification** - don't guess intent
7. **Provide percentages** - X% of requirements implemented, Y% tested

## TICKET PARSING PATTERNS

**Look for requirements in:**
- **Description section:** Main functionality description
- **Acceptance Criteria:** Explicit checklist
- **Comments:** Clarifications added later
- **Subtasks:** Breakdown of work
- **Related Tickets:** Dependencies or context

**Keywords indicating requirements:**
- "Must", "Should", "Need to", "Required"
- "User can", "System will", "Application should"
- Acceptance criteria bullets
- "Given...When...Then" (BDD format)

## COMMON GAPS

**Partially implemented patterns:**
- Hardcoded values instead of configurable
- Only happy path, no error handling
- Only one case of multiple required cases
- No UI but backend implemented
- No migration but code implemented

**Missing implementation patterns:**
- Feature mentioned in ticket but no code
- Configuration/settings changes not done
- Database changes not done
- API endpoints not created
- Tests not written

## WHAT'S NOT A REQUIREMENTS ISSUE

- Code quality (reviewed elsewhere)
- Performance (reviewed elsewhere)
- Security (reviewed elsewhere)
- **Focus only on: Does code implement what ticket asked for?**

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
