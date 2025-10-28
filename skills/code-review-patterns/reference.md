# Code Review Patterns - Detailed Reference

**Companion to:** SKILL.md (core patterns and quick reference)

**Purpose:** Extended examples, detailed workflows, and comprehensive troubleshooting for code review best practices.

---

## Extended Before/After Examples

### Example 1: Logic Bug Detection

**❌ BAD Review Comment:**
```
This function has issues.
```

**✅ GOOD Review Comment:**
```
**File:** src/calculator/stats.py:34-38
**Issue:** Division by zero not handled

**Evidence:**
```python
def calculate_average(numbers: list[int]) -> float:
    total = sum(numbers)
    count = len(numbers)
    return total / count  # Crashes if numbers is empty
```

**Reproduction:**
```python
calculate_average([])  # ZeroDivisionError
```

**Impact:** API endpoint `/api/stats` crashes when no data available

**Fix:**
```python
def calculate_average(numbers: list[int]) -> float:
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
```

**Severity:** High - Production endpoint crashes
**Test case needed:** `test_calculate_average_empty_list()`
```

**Why this works:**
- Specific file and line numbers
- Shows exact problematic code
- Demonstrates how to reproduce
- Quantifies impact (production crash)
- Provides complete working fix
- Suggests test case

---

### Example 2: Security Vulnerability

**❌ BAD Review Comment:**
```
Security problem here.
```

**✅ GOOD Review Comment:**
```
**File:** src/api/search.py:67
**Issue:** SQL injection vulnerability in search endpoint

**Evidence:**
```python
def search_users(query: str) -> list[dict]:
    sql = f"SELECT * FROM users WHERE name LIKE '%{query}%'"
    return db.execute(sql).fetchall()
```

**Exploitation scenario:**
```python
# Attacker sends: query = "'; DROP TABLE users; --"
# Resulting SQL: SELECT * FROM users WHERE name LIKE '%'; DROP TABLE users; --%'
# Result: users table deleted
```

**Impact:**
- Data exfiltration (access all user records)
- Data deletion (DROP TABLE)
- Privilege escalation (UNION SELECT from admin tables)

**Fix:**
```python
def search_users(query: str) -> list[dict]:
    sql = "SELECT * FROM users WHERE name LIKE ?"
    return db.execute(sql, (f"%{query}%",)).fetchall()
```

**Additional hardening:**
- Add input length limit (prevent DoS)
- Sanitize/escape special characters
- Rate limit search endpoint

**Severity:** Critical - Exploitable data breach vulnerability
**CVSS Score:** 9.1 (Critical)
```

**Why this works:**
- Shows vulnerable code with context
- Demonstrates actual exploitation
- Lists multiple impact scenarios
- Provides working fix
- Suggests additional security measures
- Uses industry-standard severity (CVSS)

---

### Example 3: Performance Regression

**❌ BAD Review Comment:**
```
This seems slow.
```

**✅ GOOD Review Comment:**
```
**File:** src/service/notification.py:89-95
**Issue:** N+1 query pattern introduced

**Before (optimized):**
```python
def notify_users(user_ids: list[int]) -> None:
    users = db.get_users_batch(user_ids)  # 1 query
    for user in users:
        send_email(user.email, generate_message(user))
```

**After (regression):**
```python
def notify_users(user_ids: list[int]) -> None:
    for user_id in user_ids:
        user = db.get_user(user_id)  # N queries!
        send_email(user.email, generate_message(user))
```

**Impact calculation:**
- 1000 users = 1000 database queries (was 1 batch query)
- Current: ~5 seconds (1000 × 5ms per query)
- Previous: ~50ms (1 batch query)
- **100x performance regression**

**Frequency:** Called hourly for 5000+ users
**Total impact:** 5 seconds → 25 seconds per notification run

**Fix:** Revert to batch query approach

**Severity:** High - Significant performance regression on scheduled job
```

**Why this works:**
- Shows before/after code comparison
- Quantifies exact impact (100x regression)
- Calculates real-world timing
- Mentions frequency/volume context
- Provides clear reversion path

---

### Example 4: Missing Test Coverage

**❌ BAD Review Comment:**
```
Where are the tests?
```

**✅ GOOD Review Comment:**
```
**File:** src/auth/password_reset.py:45-78 (new function)
**Issue:** Missing test coverage for critical authentication function

**New function:**
```python
def reset_password(email: str, token: str, new_password: str) -> bool:
    """Reset user password if token valid."""
    user = get_user_by_email(email)
    if not user:
        return False

    if not verify_reset_token(user, token):
        return False

    hash_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    update_user_password(user.id, hash_password)
    invalidate_reset_token(token)
    return True
```

**Missing test cases:**
1. **Happy path:** Valid email + token → password updated, token invalidated
2. **Error:** Invalid email → returns False
3. **Error:** Expired token → returns False
4. **Error:** Token for different user → returns False
5. **Edge case:** Empty password → should reject
6. **Edge case:** Password = previous password → should accept (no check)
7. **Security:** Old password no longer works after reset
8. **Security:** Reset token can't be reused

**Expected test file:** `tests/unit/test_password_reset.py`

**Coverage requirement:** 100% for authentication code (95%+ normally)

**Risk assessment:**
- Function: Password reset (critical security function)
- Attack surface: External API endpoint
- Impact if broken: Account takeover vulnerability

**Severity:** Critical - Untested authentication code in production
```

**Why this works:**
- Identifies specific new function
- Lists comprehensive test scenarios
- Groups by type (happy/error/edge/security)
- Explains coverage requirement for auth code
- Assesses security risk
- References testing standards

---

## Detailed Review Workflow

### Full Review Process (Step-by-Step)

#### Stage 1: Pre-Review Automation (5 min)

**Automated checks run via CI:**

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - security

format-check:
  stage: validate
  script:
    - ruff format --check .
  allow_failure: false

lint:
  stage: validate
  script:
    - ruff check .
    - pyright .
  allow_failure: false

unit-tests:
  stage: test
  script:
    - pytest tests/unit/ -v --cov=src --cov-fail-under=95
  coverage: '/TOTAL.*\s+(\d+%)$/'
  allow_failure: false

integration-tests:
  stage: test
  script:
    - pytest tests/integration/ -v
  allow_failure: false

security-scan:
  stage: security
  script:
    - bandit -r src/ -ll  # Medium and high severity only
    - safety check --json
  allow_failure: true  # Security findings reviewed manually
```

**Review blocker:** If linting or unit tests fail, request author fix before review.

---

#### Stage 2: Context Gathering (10 min)

**Read PR metadata:**
```bash
# Using gitlab-scripts
gitlab-mr-comments INT-3877
```

**Understand:**
- What changed (feature, fix, refactor)
- Why it changed (business need, bug report)
- Scope (which systems affected)

**Check linked resources:**
- Jira ticket for requirements
- Design docs for architectural context
- Previous related PRs

**Identify file types:**
```
Production code:  src/auth/service.py (150 lines changed)
Tests:           tests/unit/test_auth_service.py (80 lines)
Config:          config/settings.yaml (5 lines)
Docs:            README.md (10 lines)
```

**Review strategy:**
- Large files first (highest risk)
- Production code before tests
- Cross-reference tests with production changes

---

#### Stage 3: Architecture Review (15 min)

**High-level questions:**

| Question | What to Check | Red Flags |
|----------|---------------|-----------|
| **Does design make sense?** | Separation of concerns, layering | Business logic in views, tight coupling |
| **Is scope appropriate?** | PR matches description | Unrelated changes, scope creep |
| **Breaking changes?** | API compatibility | Changed function signatures, removed fields |
| **Dependencies justified?** | New libraries necessary | Heavy dependency for simple task |
| **Performance impact?** | Algorithm complexity changes | O(n) → O(n²), removed caching |

**Integration with code-refactoring:**
```bash
# Check complexity metrics
ruff check --select C901,PLR0915,PLR0912 src/

# Flags:
# C901: McCabe complexity >10
# PLR0915: Too many statements (>50)
# PLR0912: Too many branches (>12)
```

**If complexity issues found:** Reference code-refactoring skill for extraction patterns.

---

#### Stage 4: Detailed Code Review (30-60 min)

**Review order:**
1. Read smallest file first (build context)
2. Trace data flow through changes
3. Check error handling paths
4. Verify edge cases handled

**Functionality checks:**

| Check | How to Verify | Tools |
|-------|--------------|-------|
| **Logic correct** | Trace execution mentally | Read code |
| **Edge cases** | Check None, empty, 0, negative | Grep for validations |
| **Error handling** | Verify failures handled | Look for try/except, checks |
| **Breaking changes** | Find all callers | `grep -r "function_name"` |

**Security checks (context-aware):**

**High scrutiny** (public APIs, auth, PII):
```python
# Check for:
- Input validation (length, type, format)
- SQL injection (parameterized queries)
- XSS prevention (output encoding)
- CSRF tokens (state-changing endpoints)
- Rate limiting (prevent abuse)
- Authentication/authorization
- No secrets in logs
```

**Medium scrutiny** (internal services):
```python
# Check for:
- Input validation (basic)
- SQL injection (if DB access)
- No secrets in logs
```

**Low scrutiny** (pure utilities):
```python
# Check for:
- Logic correctness
- Edge cases
```

**Integration with vulnerability-triage:**
- Use CVSS scoring for severity
- Check exploit availability
- Assess risk score (CVSS × criticality × exposure)

**Performance checks:**

| Pattern | Detection | Impact Calculation |
|---------|-----------|-------------------|
| **N+1 queries** | DB call in loop | `N items × 1 query = N queries` |
| **Removed caching** | Deleted `@lru_cache` | `1 calc → N calcs` |
| **Algorithm change** | Nested loops | `O(n) → O(n²) = 1000 items = 1M ops` |
| **Memory growth** | `list()` on large collection | `1M items × 1KB = 1GB RAM` |

---

#### Stage 5: Test Review (20 min)

**Coverage check:**
```bash
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=95
```

**Review tests for:**

| Aspect | Check | Red Flag |
|--------|-------|----------|
| **Completeness** | All new functions tested | Missing test files |
| **Quality** | Tests actually test behavior | Trivial assertions |
| **Edge cases** | None, empty, 0, negative covered | Only happy path |
| **Mocking** | External deps mocked | Tests hit real DB/API |
| **Organization** | 1:1 file mapping (unit tests) | Wrong directory structure |

**Test anti-patterns:**

```python
# ❌ BAD: Doesn't actually test
def test_process_data():
    result = process_data({'key': 'value'})
    assert result  # Too vague

# ✅ GOOD: Tests specific behavior
def test_process_data_extracts_key():
    result = process_data({'key': 'value'})
    assert result['key'] == 'VALUE'  # Specific assertion
```

**Integration with testing-standards:**
- Reference 3-layer pyramid
- Verify 1:1 file mapping
- Check coverage requirements (95%+ unit, 85%+ integration)
- Validate mocking strategy (mock everything external)

---

#### Stage 6: Documentation Review (10 min)

**Check:**
- [ ] **API docs:** Public functions documented
- [ ] **Non-obvious logic:** Complex algorithms explained
- [ ] **Breaking changes:** Migration guide provided
- [ ] **README:** Updated if user-facing changes
- [ ] **CHANGELOG:** Entry added (if project uses)

**Documentation anti-patterns:**

```python
# ❌ BAD: Restates obvious code
def get_user(user_id: int) -> User:
    """Get a user by user ID.

    Args:
        user_id: The user ID

    Returns:
        The user
    """
    return db.get_user(user_id)

# ✅ GOOD: Explains non-obvious WHY
def get_user(user_id: int) -> User:
    """Fetch user with eager-loaded relationships.

    WHY: Avoids N+1 queries when accessing user.profile later.
    """
    return db.get_user(user_id).with_relationships()
```

---

## Handling Difficult Review Situations

### Situation 1: Author Defensive About Feedback

**Problem:** Author responds negatively to valid feedback.

**Approach:**
1. **Acknowledge their work:** "I can see you put a lot of thought into this"
2. **Frame as collaboration:** "Let's work together to make this even better"
3. **Provide evidence:** Show concrete examples, not opinions
4. **Ask questions:** "What do you think about X approach?" vs "Do X"
5. **Focus on code, not person:** "This code has an issue" not "You made a mistake"

**Example response:**
```
I appreciate the effort on this implementation. The core logic looks solid.

I have a concern about the error handling approach - specifically the broad
try/except that could hide authentication failures.

What are your thoughts on using explicit checks instead? Happy to discuss
the tradeoffs.
```

---

### Situation 2: Massive PR (500+ lines)

**Problem:** PR too large to review effectively.

**Approach:**
1. **Request split if possible:** "Can we break this into smaller PRs?"
2. **If can't split:** Review in logical chunks
3. **Focus on high-risk areas first:** Auth, payment, data persistence
4. **Use progressive review:** Review chunks over multiple sessions
5. **Request architectural overview:** "Can you explain the flow?"

**Example response:**
```
This PR is substantial (687 lines across 15 files). To ensure thorough review:

1. Can you provide a high-level overview of the changes?
2. Which areas are highest risk and should be reviewed first?
3. Is it possible to split into smaller PRs (e.g., core logic, then tests)?

If splitting isn't feasible, I'll review in chunks focusing on:
- Authentication changes (highest risk)
- Database schema migrations
- Business logic
- Tests
```

---

### Situation 3: Unclear Requirements

**Problem:** PR doesn't match description or requirements unclear.

**Approach:**
1. **Ask for clarification:** Don't assume intent
2. **Reference ticket:** "Does this match JIRA-1234 requirements?"
3. **Identify discrepancies:** "Description says X but code does Y"
4. **Request updated description:** "Can you update PR description to match?"

**Example response:**
```
I'm having trouble matching the code to the requirements. The PR description
says "Add rate limiting to all API endpoints" but I only see changes to the
auth endpoints.

Can you clarify:
1. Which endpoints should have rate limiting?
2. Is this PR intended to be partial (auth only)?
3. Should I expect follow-up PRs for other endpoints?

This will help ensure the review focuses on the right scope.
```

---

### Situation 4: Scope Creep

**Problem:** PR includes unrelated changes.

**Approach:**
1. **Identify scope:** What's the core change vs extras?
2. **Assess necessity:** Are extras required for core change?
3. **Suggest separation:** "Can we move X to separate PR?"
4. **Explain benefits:** Easier review, clearer git history, faster merge

**Example response:**
```
I notice this PR includes:
- Core: Rate limiting implementation (150 lines)
- Extra: Refactoring of unrelated utility functions (200 lines)

The refactoring is valuable but unrelated to rate limiting. Suggestion:

1. Keep rate limiting in this PR
2. Move refactoring to separate PR

Benefits:
- Easier to review each change independently
- Clearer git history
- Faster merge of rate limiting (if needed urgently)

Thoughts?
```

---

## Advanced Feedback Patterns

### Pattern 1: Trade-off Discussion

**When:** Multiple valid approaches exist.

**Template:**
```
💭 **Design consideration:** src/cache/strategy.py:45

I notice you chose approach A (in-memory caching). Have you considered approach B (Redis)?

**Approach A (current):**
Pros: Simple, no external dependency
Cons: Doesn't scale across instances, lost on restart

**Approach B (alternative):**
Pros: Distributed, persistent, proven at scale
Cons: Additional dependency, complexity

**Context:** If we're deploying multiple instances, Redis might be worth it.

Thoughts on the tradeoff? Happy with current approach if single-instance.
```

---

### Pattern 2: Teaching Moment

**When:** Author is learning, pattern could be applied elsewhere.

**Template:**
```
✅ **Nice pattern:** src/validators/email.py:23

Great use of regex for email validation. This is a solid pattern.

**Learning opportunity:** This pattern could be extracted to a reusable validator:

```python
# validators/common.py
class RegexValidator:
    def __init__(self, pattern: str, error_msg: str):
        self.pattern = re.compile(pattern)
        self.error_msg = error_msg

    def validate(self, value: str) -> bool:
        if not self.pattern.match(value):
            raise ValidationError(self.error_msg)
        return True

# Usage
email_validator = RegexValidator(r'^[\w\.-]+@[\w\.-]+\.\w+$', "Invalid email")
```

**Benefit:** Reusable across all validators (phone, URL, etc.)

No need to change now, but worth considering for future validators.
```

---

### Pattern 3: Positive Reinforcement

**When:** Author does something exemplary.

**Template:**
```
✅ **Excellent error handling:** src/api/payment.py:67-82

This is a great example of defensive programming:

```python
try:
    result = stripe.charge(amount, token)
except stripe.error.CardError as e:
    LOG.warning(f"Card declined", extra={'user_id': user.id})
    return {'error': 'Payment declined'}
except stripe.error.APIError as e:
    LOG.error(f"Stripe API error", extra={'error': str(e)})
    return {'error': 'Payment system unavailable'}
```

**Why this is good:**
- Specific exception types (not broad except)
- Appropriate logging levels (warning vs error)
- User-friendly error messages (no technical details leaked)
- Preserves error context for debugging

Consider using this pattern in other payment endpoints.
```

---

## Metrics and Continuous Improvement

### Review Quality Metrics

Track these metrics to improve review process:

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Time to first review** | <24 hours | Fast feedback loop |
| **Review thoroughness** | >80% issues caught | Prevent production bugs |
| **False positive rate** | <10% | Reviewer credibility |
| **Bugs found in review** | Track trend | Review effectiveness |
| **Bugs escaped to prod** | Minimize | Review gaps |
| **Review turnaround time** | <48 hours total | Don't block development |

### Team Review Calibration

**Monthly calibration session:**
1. Review sample PR as team
2. Compare findings independently
3. Discuss discrepancies
4. Align on severity thresholds
5. Update standards based on learnings

**Benefits:**
- Consistent review standards
- Knowledge sharing
- Identify blind spots
- Reduce false positives

---

## Tooling and Automation

### Recommended Tools

| Tool | Purpose | Integration |
|------|---------|-------------|
| **ruff** | Linting + formatting | CI/CD pre-review |
| **pyright** | Type checking | CI/CD pre-review |
| **bandit** | Security scanning | CI/CD (review findings) |
| **pytest-cov** | Coverage measurement | CI/CD (block <95%) |
| **SonarQube** | Code quality analysis | Weekly scans |
| **GitLab MR** | Review platform | gitlab-scripts integration |

### Custom Review Checklist Bot

**Example GitLab CI integration:**

```yaml
review-checklist:
  stage: validate
  script:
    - python scripts/review_checklist.py
  artifacts:
    reports:
      quality: gl-code-quality-report.json
```

**Checklist validates:**
- [ ] PR description not empty
- [ ] Linked to ticket (JIRA-XXXX in title)
- [ ] Tests added for new code
- [ ] No commented code
- [ ] No debug prints
- [ ] No secrets in diff

---

## Summary: The Complete Review Process

### Quick Review Checklist (Print This)

**Pre-Review:**
- [ ] Automated checks passed (linting, tests, security)
- [ ] PR description clear and complete
- [ ] Linked to requirements (ticket, design doc)

**Context:**
- [ ] Understand WHAT changed
- [ ] Understand WHY changed
- [ ] Checked existing MR comments

**Architecture:**
- [ ] Design makes sense
- [ ] No scope creep
- [ ] No breaking changes (or justified)
- [ ] Dependencies justified

**Code Quality:**
- [ ] Logic correct (happy path + edge cases)
- [ ] Error handling appropriate
- [ ] Security issues addressed
- [ ] Performance acceptable
- [ ] Code readable and maintainable

**Tests:**
- [ ] Tests exist for new code
- [ ] Tests cover edge cases
- [ ] Coverage ≥95% (unit)
- [ ] Tests actually test behavior

**Documentation:**
- [ ] Public APIs documented
- [ ] Non-obvious logic explained
- [ ] README updated if needed

**Feedback:**
- [ ] Every finding has file:line reference
- [ ] Evidence provided (code snippets)
- [ ] Impact explained
- [ ] Fix suggested
- [ ] Severity assigned
- [ ] Tone respectful and constructive

### The Review Mantra

**"Be kind, be specific, be helpful"**

Every review comment should pass this test:
- **Kind:** Would I want to receive this feedback?
- **Specific:** Can the author act on it immediately?
- **Helpful:** Does it improve code quality or team knowledge?

**Remember:** Reviews are collaborative improvement, not criticism.
