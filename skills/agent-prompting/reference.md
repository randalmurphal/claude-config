# Agent Prompting Reference Guide

**Companion to SKILL.md** - Detailed prompt examples, advanced techniques, and role-specific patterns.

## Table of Contents

1. [Structured Output Patterns](#structured-output-patterns)
2. [Effective Prompt Patterns](#effective-prompt-patterns)
3. [Advanced Techniques](#advanced-techniques)
4. [Examples by Agent Role](#examples-by-agent-role)
5. [Proactive Usage Patterns](#proactive-usage-patterns)
6. [Context Optimization](#context-optimization)

---

## Structured Output Patterns

### XML Tags for Sections

```
Expected output format:

<verification-logic>
Location: path/to/file.py:line
Library: [library name]
Code: [snippet]
</verification-logic>

<dependencies>
- Dependency 1: [description]
- Dependency 2: [description]
</dependencies>

<notes>
Any relevant observations
</notes>
```

**Why:** XML tags are unambiguous delimiters. Easy to parse, clear structure.

### Prefilling Response Start

```
Begin your response with:

### JWT Verification Analysis
**Status:** [FOUND / NOT_FOUND / EXTERNAL_SERVICE]
**Location:** [file:line or "N/A"]
...
```

**Why:** Guides output format from the first line. Prevents agent from choosing own structure.

### Markdown Structure

```
Expected output:

# Analysis Results

## Files Modified
- path/to/file1.py - [description]
- path/to/file2.py - [description]

## Implementation Summary
[2-3 sentences]

## Gotchas Discovered
- **Issue:** [description]
  - **Evidence:** [what revealed it]
  - **Resolution:** [how handled]
```

**Why:** Clear hierarchy, easy to scan, familiar format.

### Separators Between Sections

```
Use .=== as section separator:

.===
SECTION 1: Discovery
.===
[content]

.===
SECTION 2: Implementation
.===
[content]
```

**Why:** Makes it easy to programmatically parse agent responses.

### Chain-of-Thought for Complex Tasks

```
Think through this step-by-step:

1. First, identify all authentication endpoints (list them)
2. Then, trace each endpoint to its verification logic
3. Finally, determine which library performs actual JWT verification

Show your reasoning for each step before proceeding to the next.
```

**Why:** Forces systematic approach, prevents jumping to conclusions.

---

## Effective Prompt Patterns

Comprehensive before/after examples demonstrating clear, structured prompts.

### Example 1: Code Investigation

**BEFORE (Vague):**
```
Investigate the authentication system.
```

**AFTER (Clear):**
```
Find how JWT tokens are verified in the API.

Success criteria:
- File path + line number where verification happens
- What library is used (name + version)
- Code snippet of verification logic (5-10 lines)
- Any dependencies (Redis, database, external service)

Context: I know middleware exists, just need verification logic location.

Expected output format:
### Verification Logic
**Location:** path/to/file.py:45-52
**Library:** PyJWT v2.8.0
**Code:**
```python
[actual verification code snippet]
```
**Dependencies:** Redis for token blacklist lookup

If not found: Check for external auth service (Auth0, Cognito) and report.
```

**Why better:** Specific goal, measurable success, clear format, error handling.

---

### Example 2: Implementation Task

**BEFORE (Under-specified):**
```
Add rate limiting to the API.
```

**AFTER (Detailed):**
```
Implement rate limiting for JWT authentication endpoints.

Requirements:
- Limit: 5 login attempts per minute per IP
- Use Redis for rate limit tracking (existing Redis connection in src/db/redis.js)
- Return 429 status with Retry-After header when exceeded
- Log rate limit violations to auth.log

Files to modify:
- src/middleware/auth.js (add rate limit check before JWT verification)
- src/lib/rate_limiter.js (create new - rate limiting logic)

Success criteria:
- Rate limiting works (test with 6 rapid requests)
- Tests pass (unit tests for rate limiter, integration test for auth flow)
- No breaking changes to existing auth flow
- Linting passes (eslint)

Expected output:
### Files Modified
- path/to/file.js - [what changed]

### Implementation Summary
[2-3 sentences on approach]

### Test Results
**Unit:** ✅ PASS (N tests)
**Integration:** ✅ PASS (N tests)
**Linting:** ✅ PASS

### Gotchas Encountered
[Any issues and resolutions, or NONE]
```

**Why better:** Clear requirements, existing context, measurable success, output format specified.

---

### Example 3: Testing Task

**BEFORE (Generic):**
```
Write tests for authentication.
```

**AFTER (Specific):**
```
Write unit tests for JWT verification logic in src/middleware/auth.js.

Coverage requirements:
- Happy path: Valid token → user object returned
- Error cases: Invalid signature, expired token, malformed token, missing token
- Edge cases: Empty string, null, token with extra fields

Test framework: pytest
File location: tests/unit/test_auth_middleware.py
Coverage target: 95% line coverage

Success criteria:
- All tests pass
- Coverage report shows ≥95%
- No flaky tests (run 3 times, all pass)
- Follows testing-standards skill (1:1 file mapping, AAA pattern)

Expected output:
### Tests Implemented
- tests/unit/test_auth_middleware.py - [N tests covering verification logic]

### Coverage Results
**Line coverage:** 97%
**Function coverage:** 100%

### Test Results
```
pytest output showing all tests passing
```

### What's Tested
- test_valid_token_success
- test_invalid_signature_error
- test_expired_token_error
- test_malformed_token_error
- test_missing_token_error
- test_null_token_error
```

**Why better:** Specific file, clear coverage target, test cases enumerated, output format defined.

---

### Example 4: Parallel Investigation

**BEFORE (Sequential, slow):**
```
Message 1: Investigate auth module
[Wait]

Message 2: Investigate API routes
[Wait]

Message 3: Investigate middleware
[Wait]
```

**AFTER (Parallel, 5x faster):**
```
Find JWT verification logic across the codebase. Run these investigations in parallel:

Task 1 - Auth Module:
Search src/auth/ for JWT verification logic.
Return: File paths, line numbers, libraries used.

Task 2 - API Routes:
Search src/routes/ for JWT verification in route handlers.
Return: Which routes use JWT, how they verify.

Task 3 - Middleware:
Search src/middleware/ for JWT verification middleware.
Return: Middleware functions, where they're applied.

Task 4 - Dependencies:
Check package.json and node_modules for JWT libraries installed.
Return: Library names, versions.

Expected output per task:
### [Task Name] Results
**Found:** YES/NO
**Locations:** [file:line, file:line, ...]
**Details:** [brief description]

I will aggregate results after all tasks complete.
```

**Why better:** 4 parallel tasks (5x faster), clear boundaries, consistent output format, explicit aggregation plan.

---

## Advanced Techniques

### Step-by-Step Confirmation (Prevent Excessive Tool Use)

**Problem:** Agent reads 500 files looking for something.

**Solution:**
```
Find JWT verification logic using this process:

Step 1: Check src/middleware/auth.js (most likely location)
- If found, STOP and report
- If not found, proceed to Step 2

Step 2: Search src/lib/ for JWT-related files
- If found, STOP and report
- If not found, proceed to Step 3

Step 3: Grep entire src/ for "jsonwebtoken" or "jwt.verify"
- Report findings or "Not found"

At each step, report what you checked and whether you found it before proceeding.
```

**Why:** Prevents wasteful broad searches. Guides systematic approach.

### Multi-Mode Systems (Plan Mode vs Act Mode)

**Pattern:**
```
Mode: PLAN
Task: Analyze authentication codebase and create implementation plan
Output: Detailed plan with file modifications, dependencies, risks

[Review plan, approve]

Mode: ACT
Task: Execute plan from PLAN mode analysis
Input: [approved plan]
Output: Implementation results
```

**Why:** Separates thinking from doing. Allows review before execution.

### Reflection Pattern (Agent Reviews Own Work)

**Pattern:**
```
Task 1: Implement rate limiting
[Implementation complete]

Task 2 (same agent): Review your implementation from Task 1
Check for:
- Security vulnerabilities
- Performance issues
- Edge cases not handled
- Test coverage gaps

Output: Issues found + severity + fix recommendations
```

**Why:** Catches mistakes before dedicated reviewer. Self-correction loop.

### Tool Use Specification (Which Tools, When, How)

**Pattern:**
```
Find JWT verification logic.

Tools available: Read, Grep, Bash
Tool usage rules:
1. Start with Grep to find candidate files (fast)
2. Use Read on up to 5 most promising files (focused)
3. Do NOT read entire directories
4. If >5 files needed, ask for guidance

Expected tool usage:
- Grep: 1-2 calls (find JWT-related files)
- Read: 3-5 calls (read specific files)
- Bash: 0 calls (not needed for this task)
```

**Why:** Prevents inefficient tool usage. Guides systematic approach.

---

## Examples by Agent Role

Detailed role-specific prompt examples with full context.

### investigator (Discovery)

```
Find all API endpoints that use JWT authentication.

Success criteria:
- List of endpoint paths (e.g., /api/users, /api/posts)
- File locations where endpoints are defined (file:line)
- Middleware or decorators used for auth

Context: API routes defined in src/routes/, middleware in src/middleware/.

Expected output:
### Authenticated Endpoints
1. **GET /api/users**
   - Location: src/routes/users.js:15
   - Auth: requireAuth middleware

2. **POST /api/posts**
   - Location: src/routes/posts.js:23
   - Auth: @authenticated decorator

[etc.]

Start in src/routes/, check for authentication middleware usage.
```

### implementation-executor (Implementation)

```
Implement rate limiting for JWT authentication endpoints.

Requirements:
- Limit: 5 requests/minute per IP
- Use existing Redis connection (src/db/redis.js)
- Return 429 with Retry-After header
- Log violations to auth.log

Files to modify:
- src/middleware/auth.js - Add rate limit check
- src/lib/rate_limiter.js - Create new rate limiter

Success criteria:
- Tests pass (run pytest tests/test_rate_limit.py)
- Linting passes (ruff check src/)
- No breaking changes to existing auth

Expected output:
### Files Modified
- src/middleware/auth.js - Added rate limit check before JWT verification
- src/lib/rate_limiter.js - New rate limiter using Redis

### Test Results
**Tests:** ✅ PASS (5/5)
**Linting:** ✅ PASS

### Gotchas Encountered
[Any issues, or NONE]
```

### security-auditor (Security Review)

```
Review authentication code for security vulnerabilities.

Files to review:
- src/middleware/auth.js
- src/lib/jwt.js
- src/services/auth_service.py

Check for:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Authentication bypass opportunities
- Timing attacks
- Missing input validation
- Hardcoded secrets

Expected output:
### Security Findings

#### Critical Issues
- **Issue:** [description]
  - **Location:** file:line
  - **Impact:** [what attacker could do]
  - **Fix:** [how to resolve]

#### Important Issues
[same format]

#### Minor Issues
[same format]

If no issues: "No security vulnerabilities found."
```

### test-implementer (Testing)

```
Write unit tests for JWT verification in src/middleware/auth.js.

Coverage requirements:
- Happy path: Valid token → success
- Error cases: Invalid signature, expired, malformed, missing
- Edge cases: Null, empty string, token with extra fields

Test framework: pytest
Location: tests/unit/test_auth_middleware.py
Target: 95% line coverage

Success criteria:
- All tests pass
- Coverage ≥95%
- Follows AAA pattern (Arrange-Act-Assert)
- No flaky tests

Expected output:
### Tests Implemented
- tests/unit/test_auth_middleware.py - 8 tests covering verification

### Coverage
**Line:** 97%
**Function:** 100%

### Test Results
```
[pytest output]
```

Follow testing-standards skill for structure.
```

### code-reviewer (Quality Review)

```
Review authentication code for quality issues.

Focus areas:
- Code complexity (functions >50 lines, cyclomatic >10)
- Naming clarity (vague names, abbreviations)
- Error handling (bare except, silent failures)
- Documentation (missing docstrings, outdated comments)

Files to review:
- src/middleware/auth.js
- src/lib/jwt.js

Expected output:
### Code Quality Issues

#### Complexity
- **Function:** verify_jwt() at auth.js:45
  - **Issue:** 85 lines, cyclomatic complexity 15
  - **Fix:** Extract token parsing, validation, error handling to separate functions

#### Naming
- **Variable:** x at auth.js:67
  - **Issue:** Single-letter variable name
  - **Fix:** Rename to decoded_token

[etc.]

If no issues: "No quality issues found."
```

---

## Proactive Usage Patterns

### Explicit Delegation Instructions in Main Prompt

**In orchestration commands (/solo, /conduct):**
```
Phase 2: Implementation
- Spawn implementation-executor agent
- BEFORE spawning, consult agent-prompting skill
- Provide clear objective, success criteria, output format
- Run in parallel with other independent tasks when possible
```

**Why:** Makes delegation quality part of the workflow, not an afterthought.

### Parallel Task Patterns (7 parallel = 5x faster)

**Real example from /solo workflow:**
```
Phase 3: Validation & Fix Loop
Spawn 6 reviewers in parallel (single message):
1. security-auditor
2. performance-optimizer
3. code-reviewer (pass 1: complexity, errors, clarity)
4. code-reviewer (pass 2: responsibility, coupling, type safety)
5. code-beautifier (DRY, magic numbers, dead code)
6. code-reviewer (pass 3: documentation, comments, naming)

Wait for all results, then analyze consolidated findings.
```

**Why:** 6 parallel tasks complete in time of 1 sequential task. Saves 5 round-trips.

### Save Main Context for Synthesis Work

**Anti-pattern:**
```
[Main agent reads 50 files, analyzes each, implements changes]
Context: 150k tokens burned on mechanical work
```

**Better pattern:**
```
[Main agent delegates reading/analysis to sub-agents]
[Main agent receives summaries]
[Main agent synthesizes and makes decisions]
Context: 20k tokens on high-level orchestration
```

**Why:** Sub-agents have isolated context. Their tokens don't pollute main agent's context window.

---

## Context Optimization

### Progressive Disclosure (Only Load What's Needed)

**Anti-pattern:**
```
Context: [entire project architecture, all docs, all code]
Task: Find JWT verification
```

**Better:**
```
Context: Auth uses JWT. Middleware likely in src/middleware/.
Task: Find JWT verification starting in src/middleware/, expand to src/ if needed.
```

**Even better:**
```
Task: Find JWT verification in src/middleware/auth.js lines 1-100.
If not found, expand search to src/lib/, src/services/.
Report search path taken.
```

**Why:** Start narrow, expand if needed. Don't pay context cost upfront.

### Agent Context is Separate (No Pollution)

**Remember:**
- Each Task call creates isolated agent
- Agent's context is separate from your context
- Agent reads 100 files → your context unaffected

**Use this to your advantage:**
```
# Main agent (you): Clean context
Task(query="Investigate entire codebase for security vulnerabilities", role="security-auditor")
# Sub-agent: Burns its own context on exploration
# Returns: Summary of findings

# Main agent: Receives concise summary, context still clean
```

### Domain-Specific Context (Not Complete Project)

**Anti-pattern:**
```
Context for auth investigation:
- Project README
- Architecture docs
- Database schema
- API documentation
- Deployment guide
- All CLAUDE.md files
```

**Better:**
```
Context for auth investigation:
- Auth architecture: JWT-based, tokens in Redis
- Auth module location: src/auth/, src/middleware/
- Libraries used: jsonwebtoken v9.0.0
```

**Why:** Agent needs auth domain context, not entire project context.

### Feedback Loop (Prompts Guide Learning)

**Pattern:**
```
Task 1: Investigate auth logic
[Receives vague response]

Task 2 (refined): Investigate JWT verification in src/middleware/auth.js
Provide: File paths, line numbers, code snippets, library names
[Receives structured response]

Task 3 (even better): Use template from previous response format
[Receives consistent, structured response]
```

**Why:** Each iteration teaches you how to write better prompts for next time.
