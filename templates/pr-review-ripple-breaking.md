---
template: pr-review-ripple-breaking
description: Breaking change analysis from function signature modifications
---

Analyze breaking changes from modified function signatures across entire codebase.

WORKTREE PATH: {worktree_path}
CHANGED FILES: {changed_files}

## SUPPORTING SKILLS

Load these skills FIRST for standards and common patterns:
- `pr-review-standards` - Verification rules, confidence scoring
- `pr-review-evidence-formats` - Response format standards
- `pr-review-common-patterns` - Common breaking change patterns

## YOUR SINGLE FOCUS

Find ALL callers of changed functions and verify signature/behavior compatibility.

**Scope**: Function signature changes ONLY
- Added/removed parameters
- Changed return types
- Changed behavior (different return values)
- Type signature changes

**Out of scope**: Integration points (APIs, queues, caches), DB schema changes

## MANDATORY REASONING FORMAT

**Include chain-of-thought reasoning for EVERY finding:**

```json
"reasoning_chain": [
  "Step 1: Identified function signature change: calculate_total() added required parameter 'tax_rate'",
  "Step 2: Searched entire codebase with grep pattern 'calculate_total(' - found 15 callers",
  "Step 3: Read each caller to check if tax_rate parameter provided",
  "Step 4: Found 5 callers missing tax_rate parameter - these will break",
  "Step 5: Checked test files - found 3 test methods not updated",
  "Step 6: Searched for indirect callers (functions calling calculate_total callers) - found 2 chain impacts"
]
```

## CONFIDENCE LEVELS

Rate your confidence for EACH finding:

- `1.0` - Definite breaking change (missing required parameter, wrong type)
- `0.8-0.9` - Very likely breaking (behavior change, return type change)
- `0.5-0.7` - Possibly breaking (indirect impacts, kwargs usage)
- `0.3-0.4` - Uncertain (dynamic calls, reflection)
- `0.0-0.2` - Needs verification (can't determine from static analysis)

**Include confidence in every finding.**

## YOUR TASKS

### 1. Identify Changed Function Signatures

**Search changed files for**:
- Function definitions (`def function_name(`)
- Parameter changes (added, removed, reordered)
- Type hint changes (`-> int` vs `-> str`)
- Default value changes

**Record**:
- Function name
- File and line number
- Before signature (from git diff if available)
- After signature (from current code)
- Change type (added_parameter, removed_parameter, return_type_change, behavior_change)

### 2. Find ALL Callers Across Codebase

**Use Grep patterns** (see GREP PATTERNS section below):
- Search for function name calls
- Include production AND test code
- Check imports (function might be renamed at import)

**Don't limit to changed files** - search ENTIRE codebase.

### 3. Analyze Each Caller

For each caller found:
- Read caller code context (5-10 lines around call)
- Check parameter compatibility
- Check return type handling
- Determine status: OK, BROKEN, AT_RISK, NEEDS_VERIFICATION
- Include confidence score
- Provide fix suggestion if broken

### 4. Find Indirect Callers

**Chain analysis**:
- If function A calls changed function B
- Find what calls function A (could break too)
- Track call chains up to 2 levels deep
- Flag as POTENTIALLY_BROKEN with lower confidence

### 5. Check Test Coverage

**Test file analysis**:
- Do tests call changed functions?
- Are tests updated for new signatures?
- Missing test updates = broken tests = CI failure

## GREP PATTERNS

**Finding direct callers**:
```bash
# Function calls
grep -r "function_name(" --include="*.py"

# Method calls
grep -r "\.function_name(" --include="*.py"

# Imports
grep -r "from .* import.*function_name" --include="*.py"
grep -r "import.*function_name" --include="*.py"
```

**Finding indirect callers** (for changed function B, find callers of A that calls B):
```bash
# First find immediate caller function name
grep -r "def caller_function_a(" --include="*.py"

# Then search for calls to that
grep -r "caller_function_a(" --include="*.py"
```

## RESPONSE FORMAT

```json
{
  "agent_metadata": {
    "agent_type": "pr-review-ripple-breaking",
    "focus": "Breaking changes from function signature modifications",
    "analysis_complete": true,
    "timestamp": "2025-10-27T10:30:00Z"
  },
  "status": "COMPLETE",
  "reasoning_chain": [
    "Step 1: ...",
    "Step 2: ...",
    "Step N: ..."
  ],
  "breaking_changes": [
    {
      "changed_function": "calculate_total(amount, tax_rate)",
      "file": "billing.py",
      "line": 45,
      "change_type": "added_parameter",
      "change_description": "Added required parameter 'tax_rate'",
      "before_signature": "def calculate_total(amount):",
      "after_signature": "def calculate_total(amount, tax_rate):",
      "total_callers_found": 15,
      "confidence": 1.0,
      "callers_analysis": [
        {
          "file": "invoices.py",
          "line": 123,
          "caller_code": "total = calculate_total(cart.amount)",
          "status": "BROKEN",
          "reason": "Missing required parameter 'tax_rate'",
          "fix": "total = calculate_total(cart.amount, tax_rate=user.tax_rate)",
          "severity": "critical",
          "confidence": 1.0
        },
        {
          "file": "reports.py",
          "line": 67,
          "caller_code": "total = calculate_total(amount, tax_rate=0.1)",
          "status": "OK",
          "reason": "Already passing tax_rate parameter",
          "severity": "none",
          "confidence": 1.0
        }
      ]
    }
  ],
  "behavior_changes": [
    {
      "changed_function": "get_user_balance(user_id)",
      "file": "accounts.py",
      "line": 89,
      "change_description": "Now returns Decimal instead of float",
      "before_return_type": "float",
      "after_return_type": "Decimal",
      "impact": "Callers doing float math may lose precision or break",
      "total_callers_found": 8,
      "confidence": 0.8,
      "callers_at_risk": [
        {
          "file": "billing.py",
          "line": 145,
          "caller_code": "balance = get_user_balance(user_id)\nif balance > 0.0:",
          "status": "AT_RISK",
          "reason": "Comparing Decimal to float may not work as expected",
          "fix": "if balance > Decimal('0.0'):",
          "severity": "medium",
          "confidence": 0.7
        }
      ]
    }
  ],
  "indirect_impacts": [
    {
      "function_chain": "checkout() → calculate_total() → apply_tax()",
      "description": "apply_tax() changed, calculate_total() calls it, checkout() calls that",
      "file": "checkout.py",
      "line": 234,
      "status": "POTENTIALLY_BROKEN",
      "reason": "Indirect dependency on changed tax calculation",
      "verification_needed": "Test full checkout flow with new tax logic",
      "severity": "medium",
      "confidence": 0.5
    }
  ],
  "needs_verification": [
    {
      "file": "legacy_import.py",
      "line": 89,
      "concern": "Uses calculate_total but passed via kwargs dict",
      "evidence": "result = calculate_total(**params)",
      "uncertainty": "Can't determine if params dict includes tax_rate",
      "verification_needed": "Check where params dict is constructed",
      "severity": "uncertain",
      "confidence": 0.3
    }
  ],
  "summary": {
    "total_breaking_changes": 2,
    "total_callers_analyzed": 23,
    "broken_callers": 5,
    "ok_callers": 15,
    "uncertain_callers": 3,
    "average_confidence": 0.85
  }
}
```

## VERIFICATION CHECKLIST

Before returning response, verify:

- [ ] Loaded pr-review-standards, pr-review-evidence-formats, pr-review-common-patterns skills
- [ ] Searched ENTIRE codebase for callers (not just changed files)
- [ ] Included production AND test code in search
- [ ] Every finding has file:line reference
- [ ] Every finding has confidence score (0.0-1.0)
- [ ] Reasoning chain documents analysis process
- [ ] Quantified impact (X callers broken, Y at risk, Z uncertain)
- [ ] Checked indirect callers (functions calling changed function's callers)
- [ ] Provided fix suggestions for broken callers
- [ ] Included agent_metadata in response
- [ ] Summary statistics accurate
- [ ] No vague claims without evidence

## IMPORTANT RULES

1. **Search ENTIRE codebase** - Use Grep extensively, don't assume
2. **File:line for EVERY finding** - No vague claims
3. **Include confidence scores** - Honesty about certainty
4. **Check test files** - Broken tests = CI failure
5. **Quantify impact** - "8 callers broken" not "some callers broken"
6. **Distinguish statuses** - BROKEN vs AT_RISK vs OK vs NEEDS_VERIFICATION
7. **Chain-of-thought reasoning** - Document analysis process
8. **If uncertain, flag as needs_verification** - Don't guess
9. **Load skills FIRST** - Standards and patterns are critical
10. **Focus ONLY on function signatures** - Not APIs, queues, DB schemas

## SEVERITY GUIDELINES

- **critical**: Breaking changes with no backward compatibility, many callers broken
- **high**: Type incompatibilities, test failures, widespread impact
- **medium**: Behavior changes that might break callers, indirect impacts
- **low**: Minor changes, few callers affected
- **uncertain**: Can't determine impact without runtime analysis or testing
