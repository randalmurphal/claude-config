---
name: Agent Prompting & Delegation
description: Best practices for writing effective Task tool prompts that produce clear, structured outputs from sub-agents. Covers context engineering, instruction clarity, output format specification, and parallel delegation patterns. MUST BE USED PROACTIVELY when spawning sub-agents to ensure high-quality results.
allowed-tools:
  - Read
---

# Agent Prompting & Delegation Skill

**Purpose:** Write effective prompts that produce clear, structured, actionable outputs from sub-agents.

**When to use:** PROACTIVELY before every Task tool invocation. This skill improves all agent delegation.

---

## Core Prompting Principles (2025 Best Practices)

1. **Clear over clever** - Ambiguity is the enemy. Explicit instructions beat clever wording.
2. **Structure over prose** - Use XML tags, bullets, code blocks. Not paragraphs.
3. **Examples over explanations** - Show what you want (multishot prompting).
4. **Iteration over perfection** - Test prompts, analyze outputs, refine approach.
5. **Context engineering > prompt engineering** - Right context matters more than perfect wording.

**Golden rule:** If a human would be confused by your prompt, an AI definitely will be.

---

## Essential Prompt Components

Every effective Task prompt should include:

### 1. Clear Objective (REQUIRED)

**What success looks like in one sentence.**

```
GOOD: "Find the JWT token verification logic and return file:line where it happens."

BAD: "Investigate authentication."
```

### 2. Success Criteria (REQUIRED)

**How to know when done - specific, measurable outcomes.**

```
GOOD:
Success criteria:
- File path + line number of verification logic
- Library/function name used
- Code snippet (5-10 lines) showing verification

BAD:
Success criteria:
- Understand how auth works
```

### 3. Context (OPTIONAL - use judiciously)

**What you already know - only what's needed, not everything.**

```
GOOD:
Context: I know auth middleware exists in src/middleware/. Just need to find where token validation logic lives.

BAD:
Context: [dumps entire project README, architecture docs, and 50 files]
```

**Context pollution:** Too much context = agent gets lost. Provide only what's directly relevant.

### 4. Expected Output Format (CRITICAL)

**Structure, not just content. Tell the agent exactly how to format results.**

```
GOOD:
Expected output:
- File path with line numbers
- Code snippet of verification logic
- Library name (e.g., jsonwebtoken, PyJWT)
- Dependencies (what verification depends on)

Format as:
### Verification Logic
**Location:** path/to/file.py:45-52
**Library:** PyJWT
**Code:**
```python
[snippet]
```
**Dependencies:** Redis for token blacklist

BAD:
Expected output: Tell me what you find.
```

### 5. Error Handling (RECOMMENDED)

**What to do with missing data or failures.**

```
GOOD:
If verification logic not found:
1. Check for external auth service (Auth0, Cognito)
2. Look for JWT in dependencies (package.json, requirements.txt)
3. Report "No internal JWT verification found, likely external service"

BAD:
[No error handling guidance - agent makes assumptions]
```

### 6. Files Hint (OPTIONAL - when you know)

**Where to start looking - saves agent time.**

```
GOOD:
Start looking in:
- src/middleware/auth.js
- src/lib/jwt.js
- src/services/authentication/

BAD:
[No hints - agent searches entire codebase]
```

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

## Multi-Agent Delegation

### Parallel vs Sequential Execution

**Use PARALLEL when:**
- Tasks are independent
- No shared state
- Can run simultaneously
- Want 5-10x speedup

**Example - Parallel (GOOD):**
```python
# Single message, multiple Task calls
Task(query="Find JWT verification in auth module", role="investigator")
Task(query="Find JWT verification in API routes", role="investigator")
Task(query="Find JWT verification in middleware", role="investigator")
Task(query="Check dependencies for JWT libraries", role="investigator")
```

**Use SEQUENTIAL when:**
- Task B depends on Task A output
- Shared state (file modifications)
- Order matters
- Need to pass context between tasks

**Example - Sequential (GOOD):**
```python
# Message 1: Discovery
Task(query="Find all auth endpoints", role="investigator")

# Wait for response, then Message 2: Implementation
Task(query="Implement rate limiting on endpoints: [list from previous task]", role="implementation-executor")
```

**Anti-pattern (BAD):**
```python
# DON'T: Running dependent tasks in parallel
Task(query="Find auth endpoints", role="investigator")
Task(query="Implement rate limiting on auth endpoints", role="implementation-executor")
# Second task starts before first finishes - missing context!
```

### Task Boundaries (Prevent Overlap/Gaps)

**Clear boundaries:**
```
GOOD:
- Agent A: Handle user authentication (login, logout, session management)
- Agent B: Handle authorization (permissions, roles, access control)
- Agent C: Handle token management (JWT creation, validation, refresh)

BAD:
- Agent A: Work on auth
- Agent B: Work on security
- Agent C: Work on users
```

**Why bad:** Overlapping responsibilities. "Auth" and "security" both cover tokens. "Users" covers auth too.

### Clear Role Definition

**Avoid duplication:**
```
GOOD:
- investigator: Find existing JWT logic (READ ONLY - no modifications)
- implementation-executor: Implement new rate limiting (WRITE - modify files)
- test-implementer: Add tests for rate limiting (WRITE - test files only)

BAD:
- Agent A: Investigate and implement JWT changes
- Agent B: Investigate and implement rate limiting
```

**Why bad:** Both agents might modify same files, race conditions.

### Context Handoff Between Agents

**Explicit handoff:**
```
Agent 1 output:
---
JWT verification found at:
- src/middleware/auth.js:45-67 (main verification)
- src/lib/jwt.js:12-34 (helper functions)

Dependencies:
- jsonwebtoken v9.0.0
- Redis for token blacklist
---

Agent 2 prompt:
Context from investigation:
JWT verification at src/middleware/auth.js:45-67 using jsonwebtoken v9.0.0.
Token blacklist stored in Redis.

Your task: Add rate limiting to JWT verification endpoint.
Must preserve existing Redis token blacklist logic.
```

**Why:** Agent 2 gets exactly what it needs, nothing more.

### Stats/Results Aggregation Patterns

**Collector pattern:**
```
After parallel tasks complete, aggregate results:

Agent A found: 3 vulnerabilities
Agent B found: 7 vulnerabilities
Agent C found: 2 vulnerabilities

Total: 12 vulnerabilities

Consolidated list:
1. SQL injection in auth.py:45
2. XSS in template.html:23
...
```

**Template for agents:**
```
Return results in this exact format:

STATS:
- Files analyzed: N
- Issues found: N
- Critical: N
- Important: N

DETAILS:
[detailed findings]
```

---

## Common Delegation Pitfalls

| Pitfall | Example (BAD) | Fix (GOOD) |
|---------|---------------|------------|
| **Vague objective** | "Investigate auth" | "Find JWT verification logic with file:line" |
| **Under-specification** | "Add tests" | "Add unit tests covering: happy path, invalid token, expired token. Use pytest. Target 95% coverage." |
| **Context overload** | [Dumps 50 files] | "Context: Auth uses JWT. Middleware in src/middleware/. Find verification logic." |
| **Resource conflicts** | 2 agents modifying same file simultaneously | "Agent A: auth.py lines 1-50. Agent B: auth.py lines 51-100" OR sequential |
| **Missing output format** | "Tell me what you find" | "Expected output: File path, line numbers, code snippet, library name" |
| **Too simple tasks** | Task("Read src/auth.py") | Use Read tool directly |
| **No error handling** | "Find config file" | "Find config file. If not found, check environment variables or report missing." |
| **Ambiguous success** | "Make auth better" | "Success: Auth has rate limiting (5 req/min), tested, no security audit failures" |

---

## Effective Prompt Patterns (Before/After Examples)

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

## When to Use Agents vs Direct Tools

### Decision Framework

| Can you specify exact path/pattern? | Tool to Use |
|-------------------------------------|-------------|
| **YES** - Know exact file to read | Read tool directly |
| **YES** - Know exact grep pattern | Grep tool directly |
| **YES** - Know exact bash command | Bash tool directly |
| **NO** - Need to explore/discover | Use Task (agent) |
| **NO** - Need to analyze/synthesize | Use Task (agent) |
| **NO** - Need to validate/review | Use Task (agent) |

### Examples: Tools vs Agents

**USE TOOLS DIRECTLY:**
```
# Specific file read
Read(file_path="/home/user/src/auth.py")

# Known grep pattern
Grep(pattern="def verify_jwt", path="src/", output_mode="content")

# Simple bash command
Bash(command="pytest tests/unit/test_auth.py -v")
```

**USE AGENTS:**
```
# Exploration (don't know exact file)
Task(query="Find where JWT verification happens in codebase", role="investigator")

# Complex analysis
Task(query="Analyze auth flow and identify security vulnerabilities", role="security-auditor")

# Validation requiring judgment
Task(query="Review authentication code for best practices violations", role="code-reviewer")

# Multiple operations
Task(query="Find JWT logic, analyze it, and suggest improvements", role="investigator")
```

### Threshold: >3 Files = Use Agent

**Rule of thumb:**
- 1-3 known files → Read tools in parallel
- >3 files OR unknown files → Use agent

**Example - 2 files (use tools):**
```
Read(file_path="/src/auth.py")
Read(file_path="/src/middleware/jwt.py")
```

**Example - 5 files (use agent):**
```
Task(query="Read and analyze authentication logic across src/auth/, src/middleware/, src/lib/. Summarize verification flow.", role="investigator")
```

---

## Proactive Usage Patterns

### Skill Descriptions: "MUST BE USED"

**In skill frontmatter:**
```yaml
description: Best practices for agent prompting. MUST BE USED PROACTIVELY when spawning sub-agents to ensure high-quality results.
```

**Why:** Signals to main agent that this skill should be consulted automatically, not just when asked.

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

## Practical Checklist: Before Every Task Call

**Before spawning any agent, verify:**

- [ ] Clear objective (one sentence: what success looks like)
- [ ] Success criteria (measurable outcomes: file paths, test pass, etc.)
- [ ] Expected output format (structure specified: sections, fields, format)
- [ ] Context provided (only what's needed, not everything)
- [ ] Error handling (what to do if not found / fails)
- [ ] Role appropriate (investigator for discovery, implementer for code, etc.)
- [ ] Parallel tasks grouped (independent tasks in single message)
- [ ] Sequential dependencies clear (Task B depends on Task A output)
- [ ] Task boundaries non-overlapping (no resource conflicts)

**Optional but recommended:**
- [ ] Files hint (where to start looking)
- [ ] Tool usage guidance (which tools, how many calls)
- [ ] Step-by-step process (prevent excessive exploration)
- [ ] Examples (show what you want)

---

## Quick Reference: Prompt Template

```
[Clear objective in one sentence]

Success criteria:
- [Measurable outcome 1]
- [Measurable outcome 2]
- [Measurable outcome 3]

Context: [Only what's directly relevant]

Expected output format:
[Specific structure with sections, fields, format]

If [error condition]:
- [How to handle]

Start looking in: [Files hint if you know]
```

---

## Examples by Agent Role

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

## Bottom Line

**Writing effective agent prompts is a skill - practice makes perfect.**

**Remember:**
1. Clear objective (what success looks like)
2. Success criteria (measurable outcomes)
3. Expected output format (structure specified)
4. Context (only what's needed)
5. Error handling (what to do if fails)

**Before every Task call, ask:**
- Is my objective clear?
- Will the agent know when it's done?
- Have I specified the output format?
- Can I run this in parallel with other tasks?

**The skill compounds:** Better prompts → better outputs → more effective delegation → faster iteration → better results.

Use this skill PROACTIVELY. Don't wait until you get bad results to improve your prompts.
