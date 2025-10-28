---
name: pr-review-standards
description: Code quality standards for PR review agents including try/except rules, logging patterns, type hints, and verification requirements. Use when reviewing code, spawning PR review agents, or validating code quality.
allowed-tools:
  - Read
---

# PR Review Standards

**Purpose**: Critical standards for code review agents to ensure consistent, evidence-based PR reviews with proper verification requirements.

**Use when**:
- Spawning PR review agents (code-analysis, security, performance, tests, verification)
- Reviewing code changes manually
- Validating code quality during implementation
- Setting up PR review workflows

---

## Core Principles

| Principle | Description | Why It Matters |
|-----------|-------------|----------------|
| **NO Assumptions** | If uncertain, flag as "needs_verification" | Prevents false positives and wasted effort |
| **PROOF Required** | Every finding needs evidence (code snippet, trace, test) | Enables actionable fixes, not vague suggestions |
| **Read IN CONTEXT** | Entire function, not just flagged line | Prevents missing validation/handling elsewhere |
| **Trace Execution** | Confirm issue actually occurs | Distinguishes ACTUAL bugs from POTENTIAL risks |
| **Context-Aware** | External APIs need higher scrutiny than internal utils | Focuses effort on real risk areas |

---

## Code Quality Standards

### Try/Except Usage Rules

| Allowed For | NEVER Wrap | Evidence Pattern |
|-------------|-----------|------------------|
| Network calls (`requests.*`, `http.*`) | `dict.get()` | Connection errors only |
| Database ops (`pymongo.*`, `sqlalchemy.*`, `redis.*`) | `json.loads()` | DB connection failures |
| External APIs (cache, message queues) | File I/O (files auto-close) | API timeouts |
| | Type conversions | |
| | List operations (`list[0]`, `list.append()`) | |
| | String operations | |

**Exception wrapping security**: try/except can hide auth failures
- ❌ Bad: `try: verify_token() except: pass` (silent auth bypass)
- ✅ Good: `if not verify_token(): return abort(401)` (explicit)

**Location**: templates/pr-review-code-analysis.md:69-73

### Logging Standards

| Requirement | Pattern | Anti-Pattern |
|-------------|---------|--------------|
| **Import** | `import logging; LOG = logging.getLogger(__name__)` | `import logging` (root logger) |
| **Usage** | `LOG.info('msg', extra={'key': val})` | `print()` or `logging.info()` |
| **NO PII** | `extra={'user_id': id}` | `f"User {email}"` |
| **NO Secrets** | Never log passwords, tokens, API keys | `LOG.debug(f"API key: {key}")` |

**Location**: templates/pr-review-code-analysis.md:20

### Type Hints and Line Limits

| Standard | Requirement | Exception |
|----------|-------------|-----------|
| **Type hints** | Required for new code | Legacy code not being modified |
| **Line length** | 80 chars max | Long strings, URLs (with `# noqa` + reason) |
| **`# noqa`** | Must document reason | Never use without comment |

**Location**: templates/pr-review-code-analysis.md:21-22

### Code Quality Checks

| Check | Look For | Severity |
|-------|----------|----------|
| **Single-line wrappers** | Functions that just call another function | Medium |
| **Commented code** | Code blocks in comments (should be deleted) | Medium |
| **Error messages** | Include context for debugging | High |
| **Error handling** | Errors logged with sufficient context | High |

**Location**: templates/pr-review-code-analysis.md:23-24

---

## Verification Requirements

### Evidence Standards

| Finding Type | Required Evidence | Example |
|--------------|------------------|---------|
| **Logic bug** | Code snippet + reproduce scenario | `average = total / count  # count can be 0 if list empty` |
| **Security** | Vulnerable code + exploitation scenario | `query = f"SELECT * WHERE id={user_id}"` + `user_id="1 OR 1=1"` |
| **Performance** | Before/after + quantified impact | `1000 users = 1000 queries (was 1 batch)` |
| **Breaking change** | Changed code + affected callers | `def func(a, b):` → `def func(a, b, c):` + caller list |

**Location**: templates/pr-review-code-analysis.md:26-31, pr-review-security.md:28-32

### Proof Requirements by Category

#### Code Analysis
- Show code snippet with issue
- Execution trace showing how to trigger
- Fix suggestion with exact code
- File:line reference required

#### Security
- Vulnerable code snippet
- Exploitation scenario (how attacker exploits)
- Impact assessment (what attacker gains)
- Mitigation with exact code

#### Performance
- Quantified impact (N queries, O(n²), X MB RAM)
- Before/after comparison
- Calculation showing regression
- Frequency/volume context (hot path vs cold)

#### Tests
- Function being tested (with signature)
- Missing test scenarios (list specific cases)
- Current coverage assessment
- Risk level (critical functions vs utilities)

**Location**: All templates have variations, consolidated here

---

## Severity Guidelines

### STRICT Severity Requirements (Updated)

**critical**: WILL break production (with proof)
- Must include: Reproduction scenario OR exploit proof
- Examples: `TypeError` with inputs, SQL injection with payload, crash on empty list
- NOT "critical": "Could crash", "Might be exploited", "Should add validation"
- Evidence: Actual failing test case or exploitation demo

**high**: WILL cause user-visible problems (with proof)
- Must include: Quantified impact >10x OR API contract break with caller list
- Examples: N+1 with 1000 queries, API field removal + 5 callers affected
- NOT "high": "Poor performance", "Breaking change" without affected callers
- Evidence: Performance calculation OR list of broken callers

**medium**: Should fix, increases bug risk
- Must include: Specific scenario where issue manifests
- Examples: No error handling in critical path, uncovered edge case
- NOT "medium": "Could be better", "Consider refactoring"
- Evidence: Code path showing risk

**low**: Nice to have, not urgent
- Optimization opportunities with minor benefit
- Code clarity improvements
- NOT "low": Personal preferences, style nitpicks

**DO NOT ASSIGN SEVERITY** (don't flag at all):
- Personal preferences (naming, comments, formatting)
- Theoretical issues without proof
- "Could be refactored" without benefit
- Style suggestions

**THE THRESHOLD: Can you write a failing test? If NO, don't flag it.**

---

### Universal Severity Matrix

| Severity | Code Analysis | Security | Performance | Tests |
|----------|--------------|----------|-------------|-------|
| **Critical** | Crashes, data corruption, breaking changes | Exploitable vulnerabilities (injection, auth bypass, secrets) | 100x+ regression (O(n²), GB RAM) | Critical functions untested (payment, auth) |
| **High** | Logic bugs with user impact, missing error handling | Security weaknesses (missing validation, PII in logs) | 10x+ regression (N+1 queries, removed caching) | Modified functions tests not updated, incorrect tests |
| **Medium** | Code quality issues, improper try/except, missing edge cases | Defense-in-depth issues (missing size limits, weak crypto) | 2-5x regression (suboptimal algorithm) | Missing edge cases, test organization issues |
| **Low** | Style issues, optimization opportunities | Best practice violations (not immediate risk) | <2x regression, micro-optimizations | Minor improvements (better names, fixtures) |
| **Uncertain** | Can't confirm without human review | Can't confirm exploit without context | Can't measure without profiling | Test looks wrong but can't confirm |

**Location**: templates/pr-review-code-analysis.md:178-184, pr-review-security.md:263-269, pr-review-performance.md:201-207, pr-review-tests.md:231-237

### When to Use "Uncertain"

**Use "uncertain" severity when**:
- Can't determine if issue actually occurs
- Context is missing (lock elsewhere, config-dependent, etc.)
- Need human judgment (business logic, architectural decision)
- Can't confirm without running code/tests

**DON'T use "uncertain" for**:
- Issues you're confident about (use appropriate severity)
- Laziness in investigation (do the work first)
- Style preferences (shouldn't be flagged at all)

**Location**: All templates in needs_verification sections

---

## Context-Aware Scrutiny (Security)

### Security Scrutiny Levels

| Level | Applies To | Additional Checks | Skip Checks |
|-------|-----------|-------------------|-------------|
| **HIGH** | Public APIs, payment logic, PII handling, auth/authz | Rate limiting, CSRF, input size limits, output encoding, SQL parameterization, audit logging | None |
| **MEDIUM** | Internal APIs, backend services, no direct user input | Input validation (less paranoid), SQL parameterization, no secrets in logs | Rate limiting, CSRF, output encoding |
| **LOW** | Pure utilities, data transformations, no I/O | Logic correctness, edge cases | Most security checks (no attack surface) |

**Detection patterns**:
- **External API**: `@app.route`, `@api.route`, FastAPI decorators
- **Payment**: `stripe`, `payment`, `transaction`, `billing`
- **PII**: `email`, `ssn`, `phone`, `address` in user models
- **Internal**: `internal`, `rpc`, `service-to-service`

**Location**: templates/pr-review-security.md:34-79

---

## Testing Standards (Quick Reference)

### Core Requirements

| Standard | Requirement | Location |
|----------|-------------|----------|
| **1:1 mapping** | One test file per production file | `tests/unit/test_<module>.py` for `src/<module>.py` |
| **Coverage** | 95%+ line, 100% function | Unit tests |
| **Pattern** | AAA (Arrange-Act-Assert) | All tests |
| **Mocking** | Mock EVERYTHING external + OTHER INTERNAL FUNCTIONS | Use `@patch()` |
| **Parametrization** | Use `@pytest.mark.parametrize` for multiple cases | When >3 similar test cases |
| **Integration** | 2-4 files per module (ADD to existing) | Don't create new files |

**Location**: templates/pr-review-tests.md:16-27, TESTING_STANDARDS.md (referenced)

### What to Mock

| Always Mock | NEVER Mock |
|-------------|-----------|
| Database calls (`db.*`, `cursor.*`) | Function being tested |
| API calls (`requests.*`, external services) | Pure functions (no side effects) |
| File I/O (`open()`, `write()`) | Constants/config |
| Cache operations (`redis.*`, `memcache.*`) | |
| Other internal functions called by function under test | |

**WHY**: Test function in ISOLATION, not with dependencies

**Location**: templates/pr-review-tests.md:22-24

---

## Important Rules (All Review Types)

### Universal Rules

| Rule | Why | Applies To |
|------|-----|-----------|
| **Every finding MUST have file:line reference** | No vague claims | All reviews |
| **Every finding MUST have evidence** | Actionable fixes | All reviews |
| **Be specific and actionable** | Exact fix, not "fix this" | All reviews |
| **If uncertain, flag as needs_verification** | Prevent false positives | All reviews |
| **Context matters - read entire function** | Catch validation elsewhere | All reviews |
| **Check ALL changed files** | Don't skip tests/config | All reviews |

**Location**: templates/pr-review-code-analysis.md:186-194

### Analysis Approach

**Progressive investigation**:
1. Read smallest changed file to understand changes
2. Trace data flow through changes
3. Use Grep to find callers (understand impact)
4. Read callers to check for breaking changes
5. Check error paths (what happens when operations fail?)
6. Check edge cases (None, empty, 0, negative, large values)

**If >10 issues in one file**: Flag for architectural discussion (not nitpicking)

**Location**: templates/pr-review-code-analysis.md:196-207

---

## Response Format Requirements

### JSON Structure (All Review Types)

**Required fields**:
- `status`: "COMPLETE"
- `[category]_issues`: Array of findings
- `needs_verification`: Array of uncertain findings
- `positive_findings`: Array of good patterns found

**Each finding MUST include**:
- `file`: File path
- `line`: Line number (or range)
- `issue`/`vulnerability`/`problem`: What's wrong
- `evidence`: Code snippet showing issue
- `severity`: critical/high/medium/low/uncertain
- `fix`: Specific actionable solution

**Optional but recommended**:
- `impact`: What happens if not fixed
- `before`: Previous code (for comparisons)
- `after`: Current code

**Location**: All templates include JSON response format sections

---

## Edge Cases to Check (Universal)

### Standard Edge Cases

| Category | Cases to Test | Example |
|----------|--------------|---------|
| **None/Null** | Does function handle None gracefully? | `if value is None: return default` |
| **Empty** | Empty list, dict, string | `if not items: return []` |
| **Zero** | Numeric 0 (division by zero) | `if count == 0: return 0.0` |
| **Negative** | Negative numbers where positive expected | `if amount < 0: raise ValueError` |
| **Large** | Very large numbers, long strings | Overflow, memory issues |
| **Unicode** | Non-ASCII characters, emojis | `"test 🎉".encode('utf-8')` |
| **Duplicates** | Duplicate items in list | Deduplication logic |
| **Boundary** | Min/max values (INT_MAX, 1-item list) | Off-by-one errors |

**Location**: templates/pr-review-tests.md:283-293

---

## Performance Patterns

### Common Performance Issues

| Pattern | Evidence | Impact Calculation |
|---------|----------|-------------------|
| **N+1 queries** | DB query inside loop | `N items × 1 query = N queries (should be 1)` |
| **Algorithm regression** | Nested loops replacing single pass | `O(n) → O(n²): 1000 items = 1M ops` |
| **Removed caching** | `@lru_cache` deleted | `1 calc + cache → N calcs (1000x)` |
| **No batching** | `for item: db.insert(item)` | `100 items = 100 round-trips (should be 1)` |
| **Memory bloat** | `list(db.find())` on large collection | `1M records × 1KB = 1GB RAM` |

**Location**: templates/pr-review-performance.md:40-67, 219-247

### Quantification Requirements

**Always quantify performance impact**:
- ✅ "Adds 1000 queries per request"
- ✅ "O(n) → O(n²) = 1M operations for 1000 items"
- ✅ "Called 1000 times = 1000x more work"
- ❌ "Might be slow" (too vague)

**Location**: templates/pr-review-performance.md:210-217

---

## Verification Mission (Verification Agents)

### Verdict Types

| Verdict | When to Use | Evidence Required |
|---------|-------------|-------------------|
| **CONFIRMED** | Issue is real | Additional proof, execution trace |
| **CONFIRMED + DOWNGRADED** | Issue real but less severe | Mitigating factors found |
| **FALSE_POSITIVE** | Issue doesn't exist | Code preventing issue, explanation why |
| **UNCERTAIN** | Can't determine | What's needed to resolve, why uncertain |

**Location**: templates/pr-review-verification.md:17-24

### Verification Decision Tree

```
1. Read code in full context
   ↓
2. Can you find evidence issue exists?
   YES → Continue to 3
   NO → Continue to 6
   ↓
3. Trace execution - can issue actually be triggered?
   YES → CONFIRMED
   NO → Continue to 4
   ↓
4. Is there code preventing issue that agent missed?
   YES → FALSE_POSITIVE
   NO → Continue to 5
   ↓
5. Unclear if issue can be triggered?
   YES → UNCERTAIN
   ↓
6. Can you prove issue doesn't exist?
   YES → FALSE_POSITIVE
   NO → UNCERTAIN
```

**Location**: templates/pr-review-verification.md:232-256

### Common False Positive Patterns

| Pattern | What Agent Missed | Resolution |
|---------|------------------|------------|
| **Validation in caller** | Agent checked function, not caller | FALSE_POSITIVE |
| **Error handling** | try/except or guard clause | FALSE_POSITIVE |
| **Type checking** | Type hints guarantee non-None | FALSE_POSITIVE |
| **Business logic** | "Missing auth" is intentional (public endpoint) | FALSE_POSITIVE |

**Location**: templates/pr-review-verification.md:258-304

---

## Quick Reference Checklist

### Before Spawning PR Review Agents

Include these standards in agent prompt:

**Code Analysis Agent**:
- [ ] try/except ONLY for connection errors
- [ ] Logging: `LOG = logging.getLogger(__name__)`
- [ ] Type hints required
- [ ] 80 char limit, `# noqa` needs reason
- [ ] NO assumptions - flag as needs_verification

**Security Agent**:
- [ ] Context-aware scrutiny (high/medium/low)
- [ ] Provide exploitation scenarios
- [ ] Check entire data flow (input → DB/logs/response)
- [ ] NO theoretical "could be" suggestions

**Performance Agent**:
- [ ] QUANTIFY impact (N queries, O(n²), X MB)
- [ ] Compare before/after
- [ ] Check if hot path vs cold path
- [ ] Consider request volume

**Test Agent**:
- [ ] 1:1 file mapping required
- [ ] Mock EVERYTHING external + other internal functions
- [ ] 95%+ coverage
- [ ] Check edge cases (None, empty, 0, negative)

**Verification Agent**:
- [ ] Read entire function (not just flagged line)
- [ ] Check callers (validation might be there)
- [ ] Provide verdict with evidence
- [ ] If uncertain, return UNCERTAIN (not FALSE_POSITIVE)

---

## Integration with agent-prompting Skill

**Relationship**: pr-review-standards provides the WHAT (standards to check), agent-prompting provides the HOW (how to write prompts).

**When to load both**:
- agent-prompting: When writing agent prompts (structure, format)
- pr-review-standards: When defining review criteria (standards, severity)

**Typical usage**:
1. Load agent-prompting for prompt template
2. Load pr-review-standards for standards to include inline
3. Combine: Template + Standards = Effective agent prompt

---

## Summary

### The Golden Rules

1. **NO Assumptions** - If uncertain, flag for verification
2. **PROOF Required** - Every finding needs evidence
3. **Read IN CONTEXT** - Entire function, not just one line
4. **Quantify Impact** - Numbers, not vague claims
5. **Context-Aware** - External APIs ≠ internal utilities
6. **File:Line Required** - Every finding must have location

### The Test

Can you prove the issue exists with concrete evidence? If not, flag as "needs_verification".

### The Goal

Evidence-based reviews that produce actionable findings, minimize false positives, and respect context.

**Remember**: Better to flag as uncertain than to claim something is wrong without proof.
