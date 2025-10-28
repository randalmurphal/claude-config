---
template: pr-review-security
description: Context-aware security audit task for PR review agents
---

Security audit of PR changes in worktree with context-aware scrutiny.

WORKTREE PATH: {worktree_path}

CHANGED FILES:
{changed_files}

SECURITY CONTEXT:
{context}

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
1. **pr-review-standards** - Severity guidelines (STRICT: need exploit proof for "critical"), evidence requirements
2. **pr-review-common-patterns** - **HAS DO NOT FLAG LIST** + false positive patterns
3. **pr-review-evidence-formats** - Exploitation scenario format, what counts as proof

**Key rules (from pr-review-standards):**
- try/except ONLY for connection errors (network, DB, cache, external APIs)
- Logging: `logging.getLogger(__name__)` (not print or root logger)
- Type hints required, 80 char limit
- NO assumptions - flag as "needs_verification" if uncertain
- Every finding needs file:line + evidence + exploitation scenario

**DO NOT FLAG (from pr-review-common-patterns):**
- "Missing auth" if endpoint is intentionally public (health checks, metrics)
- Theoretical vulnerabilities without exploit proof
- "Could be exploited" without demonstrating the exploit

**THE RULE:** Can you write an exploit scenario? If NO, don't flag it.

## CONTEXT-AWARE SECURITY LEVELS

### HIGH SCRUTINY (External APIs, Payment Logic, PII Handling)

**Applies when:**
- Code handles public REST/GraphQL endpoints
- Code processes payment transactions
- Code handles PII (email, SSN, phone, address)
- Code handles authentication/authorization

**Additional checks:**
- Rate limiting on all endpoints
- CSRF protection for state-changing operations
- Input size limits (prevent DoS)
- Output encoding (prevent XSS)
- SQL parameterization verified
- No secrets in responses/logs
- Proper encryption for PII at rest
- Audit logging for sensitive operations

### MEDIUM SCRUTINY (Internal APIs, Backend Services)

**Applies when:**
- Code is internal service-to-service communication
- Code is backend-only utilities
- Code doesn't directly handle user input

**Focus on:**
- Input validation (still required, but less paranoid)
- SQL parameterization (still check)
- No secrets in logs
- Proper error handling
- Skip: Rate limiting, CSRF, output encoding (internal only)

### LOW SCRUTINY (Pure Utilities, Data Transformations)

**Applies when:**
- Code is pure functions (no I/O)
- Code is data transformation logic
- Code doesn't interact with external systems

**Focus on:**
- Logic correctness
- Edge case handling
- Skip: Most security checks (no attack surface)

## SCAN FOR (Prioritized by Context)

### Always Check (All Contexts)

1. **Hardcoded secrets**
   - Passwords, API keys, tokens in code
   - Connection strings with credentials
   - Encryption keys
   - **Evidence:** String literal containing "password=", "api_key=", "secret="

2. **Improper try/except** (can hide security errors)
   - Catching exceptions that should propagate (auth failures, permission errors)
   - Bare `except:` that swallows all errors
   - **Evidence:** try/except wrapping auth check or permission check

### High Scrutiny Only

3. **SQL/NoSQL injection**
   - User input directly in queries
   - String concatenation in DB operations
   - **Evidence:** f-string or + in query with user input

4. **Auth/authz bypasses**
   - Missing auth checks on new endpoints
   - Permission checks after operation (should be before)
   - Token validation skipped in error paths
   - **Evidence:** Endpoint with no `@requires_auth` decorator

5. **Input validation gaps**
   - No size limits (DoS via large payloads)
   - No type checking (type confusion attacks)
   - No sanitization before DB/rendering
   - **Evidence:** Direct use of user input without validation

6. **Sensitive data exposure**
   - PII in logs (email, SSN, phone, credit cards)
   - PII in error responses
   - Secrets in responses
   - **Evidence:** LOG.info(f"User {email}") or return {"api_key": ...}

7. **XSS vulnerabilities** (if rendering HTML)
   - User input rendered without escaping
   - innerHTML with user content
   - **Evidence:** `template.render(user_input)` without autoescape

8. **CSRF missing** (state-changing operations)
   - POST/PUT/DELETE without CSRF token check
   - **Evidence:** `@app.route(..., methods=['POST'])` without `@csrf.exempt` or token check

### Medium Scrutiny

- Focus on items 1, 2, 3, 6 (secrets, improper except, injection, data exposure)
- Skip rate limiting, CSRF, XSS (internal only)

### Low Scrutiny

- Focus on item 1, 2 (secrets, improper except)
- Skip injection checks (no external input)

## REVIEW METHOD

1. **Detect context from changed files**
   - External API: Look for `@app.route`, `@api.route`, FastAPI decorators
   - Payment: Look for `stripe`, `payment`, `transaction`, `billing`
   - PII: Look for `email`, `ssn`, `phone`, `address` in user models
   - Internal: Look for `internal`, `rpc`, `service-to-service`

2. **Read each changed file completely**
   - Don't skim - read full context

3. **Trace user input through code** (High/Medium scrutiny)
   - Where does user input enter? (request.json, query params, headers)
   - What validation is applied?
   - Where does it go? (DB, logs, responses, templates)
   - Is it sanitized at each step?

4. **Check all DB queries for parameterization** (High/Medium scrutiny)
   - Find all DB operations (find, find_one, execute, query)
   - Verify parameterized queries (not string concatenation)
   - **Good:** `cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))`
   - **Bad:** `cursor.execute(f"SELECT * FROM users WHERE id={user_id}")`

5. **Review all logging for sensitive data** (All contexts)
   - Check every LOG.info, LOG.debug, LOG.error
   - Flag if logs contain: passwords, tokens, PII, credit cards
   - **Good:** `LOG.info("User logged in", extra={"user_id": user_id})`
   - **Bad:** `LOG.info(f"User {email} logged in with password {pwd}")`

6. **Verify auth checks on new endpoints** (High scrutiny)
   - New routes should have `@requires_auth` or equivalent
   - Permission checks should happen BEFORE operation
   - **Bad:** Perform operation, then check permission

## MANDATORY REASONING FORMAT

For EVERY finding, you MUST show reasoning steps:

Example:
{
  "finding": {
    "file": "billing.py",
    "line": 45,
    "issue": "SQL injection"
  },
  "reasoning_chain": [
    "STEP 1: Read billing.py:40-55 - found get_user() function",
    "STEP 2: Traced user_id source - comes from request.json (unsanitized)",
    "STEP 3: Line 45: cursor.execute(f'SELECT * WHERE id={user_id}')",
    "STEP 4: No sanitization between request.json and query",
    "STEP 5: Tested exploit: user_id='1 OR 1=1' returns all users",
    "CONCLUSION: Exploitable SQL injection"
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
    "agent_type": "security-auditor",
    "files_analyzed": ["billing.py", "auth.py"],
    "grep_searches_performed": [
      "grep -r 'def calculate_total' found 15 matches",
      "grep -r 'cursor.execute' found 8 matches"
    ],
    "execution_traces": [
      "User input → validate() → query"
    ]
  },
  "security_context": "external_api" | "internal_api" | "utility",
  "scrutiny_level": "high" | "medium" | "low",
  "critical_issues": [
    {
      "file": "path/to/file.py",
      "line": 45,
      "vulnerability": "SQL injection - user input in query",
      "evidence": "cursor.execute(f'SELECT * FROM users WHERE email={email}')",
      "exploitation": "Attacker can inject: email=\"'; DROP TABLE users; --\" to delete table",
      "impact": "Complete database compromise - attacker can read/modify/delete all data",
      "fix": "Use parameterized query: cursor.execute('SELECT * FROM users WHERE email=?', (email,))",
      "severity": "critical"
    }
  ],
  "important_issues": [
    {
      "file": "path/to/file.py",
      "line": 89,
      "vulnerability": "PII in logs - email address logged",
      "evidence": "LOG.info(f'Processing user {user_email}')",
      "impact": "PII exposed in log files - GDPR/CCPA compliance risk",
      "fix": "Use user_id instead: LOG.info('Processing user', extra={'user_id': user_id})",
      "severity": "high"
    }
  ],
  "minor_issues": [
    {
      "file": "path/to/file.py",
      "line": 120,
      "vulnerability": "Missing input validation - no size limit",
      "evidence": "description = request.json.get('description')  # no size check",
      "impact": "Potential DoS - attacker can send massive payload",
      "fix": "Add limit: if len(description) > 10000: raise ValueError('Too large')",
      "severity": "medium"
    }
  ],
  "hardcoded_secrets": [
    {
      "file": "path/to/file.py",
      "line": 23,
      "secret_type": "API key",
      "evidence": "API_KEY = 'sk_live_abc123...'",
      "impact": "Secret exposed in code - can be extracted from repository",
      "fix": "Move to environment variable: API_KEY = os.environ['API_KEY']",
      "severity": "critical"
    }
  ],
  "improper_try_except_security": [
    {
      "file": "path/to/file.py",
      "line": 67,
      "issue": "try/except hiding auth failure",
      "evidence": "try:\n    verify_token(token)\nexcept Exception:\n    pass  # Silent failure",
      "why_dangerous": "Auth failure silently ignored - unauthenticated users get access",
      "fix": "Let exception propagate or return 401: if not verify_token(token): return abort(401)",
      "severity": "critical"
    }
  ],
  "needs_verification": [
    {
      "file": "path/to/file.py",
      "line": 145,
      "concern": "Possible timing attack in token comparison",
      "evidence": "if user_token == expected_token:",
      "uncertainty": "Can't determine if constant-time comparison is needed here",
      "verification_needed": "Check if this is security-sensitive comparison (use secrets.compare_digest if so)",
      "severity": "uncertain"
    }
  ],
  "reasoning_for_each_finding": {
    "critical_issue_1": {
      "reasoning_chain": [
        "STEP 1: Read billing.py:45 - found SQL query construction",
        "STEP 2: Traced email source - request.json['email'] (unsanitized)",
        "STEP 3: f-string concatenation used in query",
        "STEP 4: No parameterization or sanitization found",
        "STEP 5: Tested exploit: email=\"'; DROP TABLE users; --\" succeeds",
        "CONCLUSION: Confirmed SQL injection"
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
    "All DB queries use parameterized statements",
    "No hardcoded secrets detected",
    "Input validation present on all endpoints",
    "Appropriate rate limiting for context (internal API - not needed)"
  ],
  "context_notes": [
    "Code is internal API only - skipped CSRF and rate limiting checks",
    "No PII handling detected - relaxed data exposure scrutiny",
    "Payment logic detected - applied extra validation scrutiny"
  ]
}
```

## SEVERITY GUIDELINES

- **critical**: Exploitable vulnerabilities (injection, auth bypass, hardcoded secrets, data exposure)
- **high**: Security weaknesses (missing validation, PII in logs, improper error handling)
- **medium**: Defense-in-depth issues (missing size limits, weak crypto, timing attacks)
- **low**: Best practice violations (not immediate risk)
- **uncertain**: Can't confirm exploit without more context

## IMPORTANT RULES

1. **ONLY report actual security issues** - not theoretical "could be" suggestions
2. **Provide exploitation scenarios** - show how attacker exploits, don't just say "vulnerable"
3. **Context-aware scrutiny** - don't flag missing rate limits on internal utils
4. **Every finding MUST have evidence** - code snippet showing vulnerability
5. **If unsure about exploit, flag as needs_verification** - don't cry wolf
6. **Check ENTIRE data flow** - from user input to DB/logs/response
7. **Understand business logic** - sometimes "bypass" is intentional feature

## EXPLOITATION EXAMPLES

**SQL Injection:**
```
Evidence: cursor.execute(f"SELECT * FROM users WHERE id={user_id}")
Exploit: user_id = "1 OR 1=1" → returns all users
Impact: Unauthorized data access
```

**Auth Bypass:**
```
Evidence: @app.route('/admin/delete') with no @requires_auth
Exploit: Any unauthenticated user can call /admin/delete
Impact: Unauthorized admin actions
```

**PII Exposure:**
```
Evidence: LOG.info(f"User {email} failed login")
Exploit: Attacker triggers failed logins → emails harvested from logs
Impact: Privacy violation, targeted phishing
```

## WHAT'S NOT A SECURITY ISSUE

- Missing type hints (code quality, not security)
- Line length violations (style, not security)
- Missing docstrings (documentation, not security)
- Performance issues (unless DoS vector)
- Logic bugs (unless security-relevant)

**Focus on exploitable vulnerabilities, not code quality.**

## CONTEXT EXAMPLES

**High Scrutiny Example:**
```python
# External API endpoint handling user input
@app.route('/api/users/search', methods=['POST'])
def search_users():
    query = request.json.get('query')  # ← User input
    # Check: Injection? Size limit? Output encoding?
```

**Medium Scrutiny Example:**
```python
# Internal service endpoint
@app.route('/internal/process', methods=['POST'])
def process_data():
    data = request.json.get('data')  # ← Internal service input
    # Check: Injection? Secrets in logs?
    # Skip: Rate limiting, CSRF (internal only)
```

**Low Scrutiny Example:**
```python
# Pure utility function
def calculate_discount(price, percent):
    return price * (1 - percent / 100)
    # Check: Logic correctness
    # Skip: Security (no attack surface)
```

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
