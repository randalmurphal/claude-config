# Orchestration Workflow Reference Guide

**Companion to SKILL.md** - Detailed phase workflows, sub-agent descriptions, and troubleshooting.

---

## Detailed /spec Workflow

### Phase -2: Determine Working Directory
- Infer from task description
- Ask user if unclear
- Set this as $WORK_DIR for all operations

### Phase -1: Initial Assessment (3-5 Questions)
- New project or existing code?
- High-level goal?
- Critical constraints?
- **Create MISSION.md immediately** - captures unchanging goal

**MISSION.md Template:**
```markdown
# Mission

[1-2 sentence summary of goal]

## Context
[Background information]

## Non-Goals
[Explicitly out of scope]
```

### Phase 0: Auto-Investigation (Existing Projects Only)

**Project structure:**
- List top-level directories
- Identify entry points
- Find configuration files

**Tech stack:**
- Languages/frameworks
- Package managers
- Dependencies

**Existing patterns:**
- Auth/session management
- API patterns (REST/GraphQL)
- Database access patterns
- Testing patterns
- Error handling conventions

**Deployment:**
- Docker/containers
- CI/CD setup
- Environment config

**Database/Caching:**
- Database type
- ORM/query patterns
- Caching strategy

**Skip this phase for new projects** - start at Phase 1.

### Phase 1: Challenge Mode

**Find ≥3 concerns from:**
- Conflicts with existing code
- Hidden complexity
- Pain points from similar projects
- Missing requirements
- Underestimated difficulty
- Unstated assumptions

**Parallel investigation:**
- Spawn multiple Task(investigator) calls in single message
- Each investigator explores one unknown
- Faster than sequential investigation

**Document findings in DISCOVERIES.md:**
```markdown
# Discoveries

## [Date] - [Topic]
[What was learned]
[Implications]

## [Date] - [Topic]
[What was learned]
[Implications]
```

### Phase 2: Strategic Dialogue

**Ask about tradeoffs and DECISIONS, not facts:**

**GOOD Questions:**
- "Two auth systems increases complexity. Unify or keep both?"
- "Redis adds dependency. Worth it for this scale?"
- "API versioning now or later?"

**BAD Questions (check code instead):**
- "What database?" → Check settings.py
- "What auth library?" → Check requirements.txt
- "What test framework?" → Check imports

**When to ask:**
- Multiple valid approaches
- Tradeoffs affect scope
- User has domain knowledge you lack

### Phase 3: Discovery Loop

**DISCOVERIES.md (<50 lines):**
- Document learnings as you go
- Prune when >50 lines
- Archive obsolete discoveries

**ASSUMPTIONS.md:**
- Track explicit assumptions
- Mark as validated/invalidated
- Example: "Assume <10k users/day" → "VALIDATED: Traffic logs show 2k users/day"

**ARCHITECTURE.md (50-100 lines):**
- Components and responsibilities
- Dependencies between components
- Data flow
- External services
- **Watch for circular dependencies!**

### Phase 4: Spike Orchestration

**When to spike:**
- Complexity >6/10
- Unfamiliar tech
- Critical security/performance implications
- Uncertain feasibility

**Run spikes in parallel:**
```python
# Single message, multiple Task calls
Task(spike-tester, "Spike: Test Redis caching performance")
Task(spike-tester, "Spike: Test JWT vs session auth")
Task(spike-tester, "Spike: Test GraphQL subscriptions")
```

**Save results:**
`.spec/SPIKE_RESULTS/001_redis_performance.md`
`.spec/SPIKE_RESULTS/002_jwt_auth.md`
`.spec/SPIKE_RESULTS/003_graphql_subscriptions.md`

**SPIKE_RESULTS are immutable** - never modify after creation.

### Phase 5: Architecture Evolution

**Update ARCHITECTURE.md as understanding deepens:**

**Components section:**
```markdown
## Components

### Auth Service
- Responsibilities: JWT generation, validation, refresh
- Dependencies: User model, Redis (sessions)
- Exposed: auth_required decorator, validate_token()

### User Service
- Responsibilities: CRUD, password hashing
- Dependencies: Database
- Exposed: UserModel, get_user(), create_user()
```

**Check for:**
- Circular dependencies (A depends on B, B depends on A)
- Missing components
- Unclear responsibilities

### Phase 6: Scope Management

**For each potential feature:**
- **Serves MISSION.md?** → Investigate further
- **Doesn't serve mission?** → Note as "Future"
- **Tangent?** → Ask user

**Keep MISSION.md as north star** - prevents scope creep.

### Phase 7: Readiness Validation & SPEC.md Creation

**Validation checklist:**
- [ ] Mission is clear (MISSION.md exists)
- [ ] Constraints are documented (CONSTRAINTS.md)
- [ ] Architecture is stable (ARCHITECTURE.md)
- [ ] Unknowns are resolved (spikes complete or deferred)
- [ ] Dependencies are clear (no circular deps)
- [ ] Files to create/modify are listed

**Create SPEC.md with 10 required sections:**

1. **Problem Statement** - What problem are we solving?
2. **User Impact** - Who is affected and how?
3. **Mission** - Unchanging goal (1-2 sentences from MISSION.md)
4. **Success Criteria** - Measurable outcomes
5. **Requirements (IMMUTABLE)** - Hard requirements that cannot change
6. **Proposed Approach (EVOLVABLE)** - High-level strategy, can adapt
7. **Implementation Phases** - Phased breakdown with estimates
8. **Known Gotchas** - From discoveries and spikes
9. **Quality Requirements** - Tests, security, performance, documentation
10. **Files to Create/Modify** - CRITICAL for /conduct dependency parsing

**3 Optional Sections:**
11. Testing Strategy (recommended)
12. Custom Roles
13. Evolution Log

**Generate component phase specs:**

For each component in dependency order, create `SPEC_N_componentname.md`:

```markdown
# Phase N: [Component Name]

## Goal
[What this component does]

## Dependencies
[Other components this depends on - must be implemented first]

## Files to Create/Modify
- path/to/file.py - [description]
  - Depends on: [other files]

## Implementation Details
[Specific guidance for implementation-executor]

## Tests Required
[Specific test cases]

## Quality Constraints
[Component-specific requirements]

## Known Gotchas
[From discoveries/spikes relevant to this component]
```

---

## Detailed /conduct Workflow

### Phase -2: Determine Working Directory
- Same as /spec Phase -2
- Set $WORK_DIR for all operations

### Phase -1: Parse SPEC.md & Build Dependency Graph

**Extract components:**
Parse "Files to Create/Modify" section:
```markdown
## Files to Create/Modify

### auth/service.py
- Depends on: models/user.py

### models/user.py
- Depends on: None

### api/endpoints.py
- Depends on: auth/service.py, models/user.py
```

**Build dependency graph:**
```python
{
    "models/user.py": [],
    "auth/service.py": ["models/user.py"],
    "api/endpoints.py": ["auth/service.py", "models/user.py"]
}
```

**Topological sort:**
1. models/user.py (no dependencies)
2. auth/service.py (depends on models/user.py)
3. api/endpoints.py (depends on both)

**Cycle detection:**
Use DFS to detect circular dependencies:
```python
# Example cycle:
A depends on B
B depends on C
C depends on A  # CYCLE!
```

**FAIL LOUD if cycle detected:**
```
BLOCKED: Circular dependency detected

Cycle: auth/service.py → models/user.py → auth/middleware.py → auth/service.py

Cannot proceed until cycle is resolved.

Options:
A. Break dependency by moving shared code to utils
B. Restructure components to eliminate cycle
C. Reconsider architecture

Please update SPEC.md to resolve circular dependency.
```

### Phase 0: Validate Component Phase Specs Exist

**Check for SPEC_N_*.md files:**
- If exist (created by /spec): Use them as-is
- If missing (fallback): Generate from SPEC.md now

**Fallback generation:**
- Extract component details from SPEC.md
- Create basic SPEC_N_component.md for each
- Less detailed than /spec-generated specs, but sufficient

### Phase 1-N: Component Phases (For EACH Component)

**For each component in dependency order:**

#### 1. Skeleton Creation

**Production files:**
```python
Task(skeleton-builder, """
Create skeleton for: auth/service.py

Spec: $WORK_DIR/.spec/SPEC_2_auth_service.md

Include:
- Module docstring
- Imports (organized: stdlib → third-party → local)
- Class/function signatures with type hints
- Docstrings with Args/Returns
- raise NotImplementedError in function bodies
""")
```

**Test files:**
```python
Task(test-skeleton-builder, """
Create test skeleton for: tests/test_auth_service.py

Production file: auth/service.py
Spec: $WORK_DIR/.spec/SPEC_2_auth_service.md

Include:
- Test class structure
- Test method stubs for each public function
- Fixture stubs
- raise NotImplementedError in test bodies
""")
```

#### 2. Implementation

```python
Task(implementation-executor, """
Implement: auth/service.py

Spec: $WORK_DIR/.spec/SPEC_2_auth_service.md

CRITICAL STANDARDS:
- Logging: import logging; LOG = logging.getLogger(__name__)
- try/except ONLY for connection errors
- Type hints required, 80 char limit
- DO NOT run tests (will be done in testing phase)

Load python-style skill.

[Paste relevant sections from SPEC_2_auth_service.md]
""")
```

**Review result:**
- Check for blockers
- Check for gotchas
- Document in DISCOVERIES.md

#### 3. Validation & Fix Loop

**Run validation:**
```bash
# Syntax check
python -m py_compile auth/service.py

# Import check
python -c "import auth.service"

# Linting
ruff check auth/service.py

# Type checking
pyright auth/service.py
```

**Spawn 6 reviewers in parallel (single message):**
```python
Task(security-auditor, "Review: auth/service.py")
Task(performance-optimizer, "Review: auth/service.py")
Task(code-reviewer, "Review auth/service.py - Pass 1: Complexity, errors, clarity")
Task(code-reviewer, "Review auth/service.py - Pass 2: Responsibility, coupling, type safety")
Task(code-beautifier, "Review auth/service.py - DRY, magic numbers, dead code")
Task(code-reviewer, "Review auth/service.py - Pass 3: Documentation, comments, naming")
```

**Collect all issues:**
- Critical: Must fix
- Important: Must fix
- Minor: Must fix

**Fix via fix-executor (max 3 attempts):**
```python
Task(fix-executor, """
Fix issues in: auth/service.py

Issues from reviewers:
[Paste all issues from 6 reviewers]

CRITICAL STANDARDS:
- Fix ALL issues (critical + important + minor)
- No # noqa unless documented why
- No # type: ignore unless documented why

Max 3 attempts. Report if unable to fix.
""")
```

**Re-run ALL 6 reviewers after fixes:**
- Verify issues are resolved
- Check for new issues introduced
- Repeat until clean

#### 4. Unit Testing

```python
Task(test-implementer, """
Implement tests: tests/test_auth_service.py

Production file: auth/service.py
Spec: $WORK_DIR/.spec/SPEC_2_auth_service.md

CRITICAL STANDARDS:
- 95% coverage target
- Test happy path + error cases + edge cases
- Mock all external dependencies
- Fast tests (<100ms each)

Load testing-standards skill.
""")
```

**Test & fix loop (max 3 attempts):**
```bash
# Run tests
pytest tests/test_auth_service.py -v --cov=auth.service --cov-report=term-missing

# If tests fail or coverage <95%
Task(fix-executor, """
Fix test failures or improve coverage

Tests: tests/test_auth_service.py
Current coverage: [X%]

Issues:
[Test failures or missing coverage]
""")
```

#### 5. Document Discoveries

**Update DISCOVERIES.md:**
```markdown
## [Date] - Auth Service Implementation

### Gotcha: JWT expiry edge case
During testing, discovered that JWTs expiring exactly at midnight cause timezone issues.

Resolution: Always use UTC for token expiry checks.

### Performance: Token validation caching
Initial implementation validated token on every request (30ms overhead).

Resolution: Added Redis caching for validated tokens (reduced to 2ms).
```

#### 6. Enhance Future Phase Specs

**For dependent components:**
If current component revealed gotchas/patterns that affect downstream components, update their SPEC_N_*.md files:

```markdown
# Phase 3: API Endpoints

## Known Gotchas

### From Phase 2 (Auth Service):
- Always use UTC for token expiry checks
- Cache validated tokens in Redis to reduce overhead
- Handle token refresh edge cases (see DISCOVERIES.md)
```

#### 7. Checkpoint: Component Complete

**Git commit:**
```bash
git add auth/service.py tests/test_auth_service.py
git commit -m "$(cat <<'EOF'
feat(auth): implement JWT authentication service

- Token generation with configurable expiry
- Token validation with Redis caching
- Refresh token support
- Comprehensive unit tests (97% coverage)

Gotchas addressed:
- UTC timezone handling for token expiry
- Token validation caching (30ms → 2ms)

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Update PROGRESS.md:**
```markdown
# Progress

## Completed Components

### Phase 2: Auth Service ✅
- Status: COMPLETE
- Files: auth/service.py, tests/test_auth_service.py
- Coverage: 97%
- Commit: abc123f

## In Progress

### Phase 3: API Endpoints
- Status: IN_PROGRESS
- Step: Skeleton creation
```

---

### Phase N+1: Integration Testing

**Cross-component interactions:**
```python
Task(test-implementer, """
Implement integration tests: tests/integration/test_auth_flow.py

Components involved:
- Auth Service
- User Model
- API Endpoints

Test scenarios:
1. Full auth flow (register → login → access protected endpoint)
2. Token refresh flow
3. Invalid token handling
4. Session expiry handling

Load testing-standards skill (integration tests section).

Use real dependencies (test database, Redis).
""")
```

**Test & fix loop (max 3 attempts):**
- Same as unit testing
- Target: 85% integration coverage

### Phase N+2: Documentation Validation

**Find all .md files:**
```bash
find $WORK_DIR -name "*.md" -not -path "*/.spec/*"
```

**Spawn code-reviewer for each:**
```python
Task(code-reviewer, """
Validate documentation: README.md

Check:
- Code examples match implementation
- No outdated information
- No contradictions with code
- All public APIs documented
""")
```

**Fix via general-builder:**
```python
Task(general-builder, """
Fix documentation issues: README.md

Issues:
[Paste issues from code-reviewer]
""")
```

### Phase N+3: CLAUDE.md Optimization

**Check CLAUDE.md hierarchy:**
```
project/
├── CLAUDE.md (500 lines - target: 400-500)
├── agents/
│   └── custom-agent.md (300 lines - target: 300-400)
├── skills/
│   └── custom-skill.md (400 lines - target: 400-500)
└── docs/
    └── QUICKREF.md (deep-dive content)
```

**Validate line counts:**
```bash
wc -l CLAUDE.md agents/*.md skills/*.md
```

**Check for duplication:**
- Same content in multiple files?
- Deep-dive content in main CLAUDE.md?

**Extract to QUICKREF.md if needed:**
```python
Task(general-builder, """
Extract deep-dive content from CLAUDE.md to docs/QUICKREF.md

Content to extract:
- Detailed examples (keep concise examples in CLAUDE.md)
- Troubleshooting guides (keep common issues in CLAUDE.md)
- Historical context

Add pointer in CLAUDE.md: "See QUICKREF.md for detailed examples"
""")
```

### Phase N+4: Complete

**Update SPEC.md with major gotchas:**
```markdown
## Evolution Log

### Implementation Complete - [Date]

**Major Gotchas Discovered:**
1. JWT expiry timezone handling - always use UTC
2. Token validation caching critical for performance
3. Session refresh edge cases require careful handling

**Deviations from Original Spec:**
- Added Redis caching (not in original spec, but necessary for performance)
- Split auth middleware into separate file (better separation of concerns)

**Final Statistics:**
- Components: 3
- Files created: 8 (3 production, 3 unit tests, 2 integration tests)
- Test coverage: 96% (unit), 87% (integration)
- Token budget: 52k (under estimate of 60k)
```

**Final summary:**
```markdown
# Implementation Complete: JWT Authentication

## What Was Built
- JWT authentication service with token generation/validation
- User model with password hashing
- API endpoints with auth_required decorator
- Comprehensive test suite (96% unit coverage, 87% integration)

## Components Delivered
1. models/user.py - User model and CRUD operations
2. auth/service.py - JWT token generation and validation
3. api/endpoints.py - Protected API endpoints

## Quality Validation
- Tests: ✅ 96% unit coverage, 87% integration coverage
- Security: ✅ Passed security-auditor review
- Performance: ✅ Token validation <2ms (cached)
- Documentation: ✅ All public APIs documented

## Known Limitations
- Token refresh requires manual implementation in client
- Redis is now a required dependency (added during implementation)

## What's Next
- Implement refresh token rotation for enhanced security
- Add rate limiting to auth endpoints
- Consider OAuth2 integration
```

---

## Sub-Agents Detailed Roster

### Implementation Agents

#### skeleton-builder
**Purpose:** Create production file skeletons with structure but no implementation

**Output:**
- Module docstrings
- Import statements (organized)
- Class/function signatures with type hints
- Docstrings with Args/Returns/Raises
- `raise NotImplementedError` in bodies

**When:** Beginning of each component phase (production files)

#### test-skeleton-builder
**Purpose:** Create test file skeletons with structure but no tests

**Output:**
- Test class structure
- Test method stubs for each public function
- Fixture stubs
- `raise NotImplementedError` in test bodies

**When:** Beginning of each component phase (test files)

#### implementation-executor
**Purpose:** Implement full functionality from spec

**Input:**
- Spec reference (SPEC_N_component.md)
- Critical standards (inline in prompt)
- Skill to load (python-style)

**Output:**
- Fully implemented production code
- Follows project conventions
- Type hints, docstrings, error handling
- NO tests (testing phase separate)

**When:** After skeleton creation, before validation

#### test-implementer
**Purpose:** Implement comprehensive tests

**Input:**
- Production file reference
- Spec reference
- Coverage target (95% unit, 85% integration)
- Skill to load (testing-standards)

**Output:**
- Complete test suite
- Happy path + error cases + edge cases
- Mocked external dependencies
- Fast tests (<100ms each)

**When:** After validation & fix loop, for both unit and integration tests

---

### Validation Agents

#### security-auditor
**Purpose:** Find security vulnerabilities

**Focus:**
- SQL injection vulnerabilities
- Authentication/authorization issues
- Secret leakage (logs, errors)
- Input validation
- CSRF/XSS vulnerabilities

**Output:** List of security issues with severity

**When:** After implementation, before fix loop

#### performance-optimizer
**Purpose:** Find performance bottlenecks

**Focus:**
- N+1 queries
- Inefficient algorithms
- Missing database indexes
- Unnecessary computations
- Memory leaks

**Output:** List of performance issues with impact

**When:** After implementation, before fix loop

#### code-reviewer
**Purpose:** General code quality review (used 3x with different focuses)

**Pass 1 Focus:**
- Complexity (cyclomatic, cognitive)
- Error handling patterns
- Code clarity

**Pass 2 Focus:**
- Single Responsibility Principle
- Coupling between components
- Type safety

**Pass 3 Focus:**
- Documentation quality
- Comment usefulness
- Naming clarity

**Output:** List of quality issues with priority

**When:** After implementation, before fix loop (3 parallel calls)

#### code-beautifier
**Purpose:** Find style and maintainability issues

**Focus:**
- DRY violations (repeated code)
- Magic numbers (hardcoded values)
- Dead code (unused functions/variables)
- Unnecessary complexity

**Output:** List of style issues with fixes

**When:** After implementation, before fix loop

#### documentation-reviewer
**Purpose:** Validate documentation accuracy

**Focus:**
- Code examples match implementation
- No outdated information
- No contradictions between docs and code
- All public APIs documented

**Output:** List of documentation issues

**When:** Documentation validation phase

---

### Fixing Agents

#### fix-executor
**Purpose:** Fix validation issues and test failures

**Input:**
- File to fix
- List of issues from reviewers
- Critical standards
- Max 3 attempts

**Output:**
- Fixed code
- Explanation of changes
- Status (FIXED / BLOCKED)

**When:** After validation finds issues, after tests fail

**Process:**
1. Read file
2. Analyze issues
3. Apply fixes
4. Run validation
5. Repeat if needed (max 3 attempts)
6. Report BLOCKED if unable to fix

---

### Analysis Agents

#### investigator
**Purpose:** Deep code investigation and analysis

**Use cases:**
- Variant analysis (compare multiple approaches)
- Existing code patterns discovery
- Dependency analysis
- Performance profiling

**Output:** Analysis report with findings

**When:** /spec auto-investigation, variant exploration

#### merge-coordinator
**Purpose:** Merge best parts of multiple variants

**Input:**
- Multiple variant implementations
- Analysis reports from investigators

**Output:**
- Merged implementation
- Justification for choices

**When:** After variant exploration, when combining approaches

#### general-builder
**Purpose:** General implementation tasks not requiring specialized agent

**Use cases:**
- Documentation updates
- Configuration file changes
- Simple utility functions
- Refactoring

**Output:** Implemented changes

**When:** Documentation fixes, misc tasks

---

## Common Issues and Solutions

### Issue: Circular Dependencies

**Symptom:** DFS cycle detection finds A → B → C → A

**Solutions:**
1. **Break dependency by moving shared code:**
   - Extract common code to utils module
   - Both components depend on utils (no cycle)

2. **Restructure components:**
   - Combine A and B if tightly coupled
   - Split C into C1 and C2 if serving multiple purposes

3. **Use dependency injection:**
   - Pass dependencies as parameters
   - Break import-time dependency

**Prevention:** Review ARCHITECTURE.md carefully in /spec phase

---

### Issue: Tests Consistently Fail After 3 Attempts

**Symptom:** fix-executor reports BLOCKED after 3 failed test attempts

**Investigate:**
1. **Test is flaky:**
   - Uses sleep/timing
   - Depends on external state
   - Solution: Mock time, isolate state

2. **Test is wrong:**
   - Tests implementation detail, not behavior
   - Expects wrong result
   - Solution: Rewrite test

3. **Implementation is fundamentally broken:**
   - Architecture issue
   - Missing dependency
   - Solution: Escalate to user, may need /spec revision

**Escalation format:**
```
BLOCKED: Component X Tests - Failing After 3 Attempts

Issue: Tests for auth/service.py fail consistently

Attempts:
1. Fixed import error → revealed missing Redis dependency
2. Added Redis mock → tests timeout
3. Increased timeout → tests still fail with "Connection refused"

Root cause: Component assumes Redis is running, but tests don't start Redis

Options:
A. Use fakeredis library for testing (no real Redis needed)
B. Add Redis to test fixtures (slower but more realistic)
C. Refactor to make Redis dependency injectable

Recommendation: Option A (fakeredis) - fast tests, no infrastructure needed
```

---

### Issue: Validation Never Passes (6 Reviewers Keep Finding Issues)

**Symptom:** After multiple fix loops, reviewers still report issues

**Investigate:**
1. **Reviewers contradicting each other:**
   - Reviewer A says "split function", Reviewer B says "combine functions"
   - Solution: Prioritize reviewer hierarchy (security > performance > style)

2. **Standards unclear:**
   - Reviewers expect different conventions
   - Solution: Check project has clear CLAUDE.md standards, load skills

3. **Code is genuinely problematic:**
   - Trying to force bad architecture
   - Solution: Escalate, may need architectural revision

**Max iterations:** 3 fix loops per component. If not clean after 3, escalate.

---

### Issue: Integration Tests Fail But Unit Tests Pass

**Symptom:** All components pass unit tests individually, integration fails

**Investigate:**
1. **Mocking mismatch:**
   - Unit tests mock behavior that doesn't match reality
   - Solution: Check mocks match actual implementation

2. **Missing integration:**
   - Components don't actually communicate correctly
   - Unit tests didn't catch API mismatch
   - Solution: Fix integration code, ensure contracts match

3. **State contamination:**
   - Tests affect each other
   - Solution: Isolate test state, use fixtures properly

**Prevention:** Clear component contracts in SPEC_N_*.md files

---

### Issue: Coverage Below Target (95% Unit, 85% Integration)

**Symptom:** Tests run successfully but coverage report shows gaps

**Investigate:**
```bash
# Show uncovered lines
pytest --cov=module --cov-report=term-missing

# Example output:
# module/auth.py    87%   45-52, 78-80
```

**Solutions:**
1. **Untested error paths:**
   - Add tests for exceptions
   - Test validation failures

2. **Untested edge cases:**
   - Empty inputs
   - Boundary values
   - Null/None cases

3. **Dead code:**
   - Unreachable code
   - Solution: Remove or refactor

**Fix:**
```python
Task(test-implementer, """
Improve test coverage: tests/test_auth.py

Current coverage: 87%
Uncovered lines: 45-52 (error handling), 78-80 (edge case)

Add tests for:
- Invalid token format (lines 45-52)
- Empty token string (line 78)
- Expired token edge case (lines 79-80)

Target: 95% coverage
""")
```

---

### Issue: /solo Task More Complex Than Expected

**Symptom:** During /solo execution, discover:
- More components needed than anticipated
- Complex dependencies emerge
- Multiple valid approaches exist

**Decision:**
1. **Can still complete with /solo?**
   - Only slightly more complex
   - Dependencies manageable
   - Clear path forward
   - → Continue with /solo

2. **Too complex for /solo?**
   - Many interdependent components
   - Architecture unclear
   - High-stakes decisions needed
   - → Recommend /spec → /conduct

**Tell user:**
```
This task is more complex than initially assessed.

Discoveries:
- Requires 5 interconnected components (expected 2)
- Auth system affects 3 existing modules
- Multiple approaches possible (JWT vs sessions)

Recommendation:
1. Stop current /solo work
2. Run /spec to properly plan architecture
3. Run /conduct for full orchestrated implementation

This ensures:
- Proper dependency management
- Variant exploration for best approach
- Thorough integration testing

OR

Continue with /solo if: You want fastest path and accept potential rework

Your choice?
```

---

## Worktree Variant Exploration (Detailed)

### When to Use Variants

**Use variants when:**
- Multiple valid architectural approaches exist
- Uncertain which approach performs better
- High-risk changes (want to compare options)
- User explicitly requests exploring alternatives

**Don't use variants when:**
- Clear best approach
- Low stakes
- Time-constrained (variants add overhead)

### Variant Process (Step by Step)

#### 1. Decide on Approaches

**Example scenario:** Implementing caching layer

**Approaches:**
- **Variant A:** Redis with manual cache invalidation
- **Variant B:** In-memory cache with TTL
- **Variant C:** Database-backed cache with triggers

#### 2. Create Worktrees

```bash
~/.claude/scripts/git-worktree variant-redis variant-memory variant-database
```

**Creates:**
```
project/                    # Main worktree
../project-variant-redis/   # Variant A worktree
../project-variant-memory/  # Variant B worktree
../project-variant-database/# Variant C worktree
```

Each worktree is independent - changes don't affect others.

#### 3. Run Component Phase in Each Worktree

**Parallel implementation (single message):**
```python
Task(implementation-executor, """
Implement caching layer - REDIS APPROACH

Working directory: ../project-variant-redis
Spec: $WORK_DIR/.spec/SPEC_3_caching.md

Approach:
- Use Redis for distributed caching
- Manual cache invalidation on writes
- 5-minute TTL as fallback
""")

Task(implementation-executor, """
Implement caching layer - IN-MEMORY APPROACH

Working directory: ../project-variant-memory
Spec: $WORK_DIR/.spec/SPEC_3_caching.md

Approach:
- Python dict with TTL tracking
- Automatic expiry on read
- Single-process only
""")

Task(implementation-executor, """
Implement caching layer - DATABASE APPROACH

Working directory: ../project-variant-database
Spec: $WORK_DIR/.spec/SPEC_3_caching.md

Approach:
- Separate cache table
- Database triggers for invalidation
- Works with existing PostgreSQL
""")
```

#### 4. Spawn Investigator Per Variant

**Parallel analysis (single message):**
```python
Task(investigator, """
Analyze variant: Redis caching

Working directory: ../project-variant-redis

Evaluate:
- Performance (measure cache hit/miss times)
- Complexity (deployment requirements, code complexity)
- Reliability (failure modes, recovery)
- Scalability (multi-process, multi-server)
- Maintenance burden

Run benchmarks, count dependencies, assess failure scenarios.
""")

Task(investigator, """
Analyze variant: In-memory caching

Working directory: ../project-variant-memory

Evaluate:
- Performance (measure cache hit/miss times)
- Complexity (deployment requirements, code complexity)
- Reliability (failure modes, recovery)
- Scalability (multi-process, multi-server)
- Maintenance burden

Run benchmarks, count dependencies, assess failure scenarios.
""")

Task(investigator, """
Analyze variant: Database caching

Working directory: ../project-variant-database

Evaluate:
- Performance (measure cache hit/miss times)
- Complexity (deployment requirements, code complexity)
- Reliability (failure modes, recovery)
- Scalability (multi-process, multi-server)
- Maintenance burden

Run benchmarks, count dependencies, assess failure scenarios.
""")
```

#### 5. Compare Results

**Create comparison matrix:**

| Aspect | Redis | In-Memory | Database |
|--------|-------|-----------|----------|
| **Performance** | 2ms avg | 0.1ms avg | 15ms avg |
| **Complexity** | Medium (new dependency) | Low (stdlib only) | Low (existing DB) |
| **Reliability** | High (persistent) | Low (process restart = loss) | High (persistent) |
| **Scalability** | Excellent (multi-server) | Poor (single process) | Good (DB scales) |
| **Dependencies** | +1 (Redis) | None | None |

#### 6. Pick Winner OR Merge

**Option A: Clear winner**
```
Winner: Redis

Reasoning:
- Performance acceptable (2ms)
- Scalability critical for project
- Complexity worth the benefits

Action: Use ../project-variant-redis implementation
```

**Option B: Merge best parts**
```python
Task(merge-coordinator, """
Merge variants: Redis (primary) + In-Memory (fallback)

Sources:
- ../project-variant-redis (use as base)
- ../project-variant-memory (extract fallback logic)

Strategy:
- Use Redis when available
- Fall back to in-memory if Redis connection fails
- Best of both: Performance + reliability + graceful degradation

Create merged implementation in: project/cache/service.py
""")
```

#### 7. Cleanup Worktrees

```bash
~/.claude/scripts/git-worktree --cleanup variant-redis variant-memory variant-database
```

**Result:** Back to single main worktree with chosen implementation

---

## Token Budget Guidance (Detailed)

### /solo Token Breakdown

**Typical:** 10-20k tokens

**Phases:**
- Spec generation: 1-2k
- Implementation: 2-4k
- Validation (6 reviewers): 3-5k
- Fix loops: 2-4k
- Testing: 2-4k
- Documentation: 1-2k

**Factors increasing cost:**
- Complex logic (nested conditionals, algorithms)
- Many edge cases to test
- Multiple fix iterations
- Large existing codebase to read

### /spec Token Breakdown

**Typical:** 15-40k tokens (varies widely)

**Phases:**
- Auto-investigation: 5-10k (existing projects)
- Challenge mode: 2-4k
- Strategic dialogue: 1-3k (depends on user responses)
- Discovery loop: 3-8k (parallel investigations)
- Spike orchestration: 5-15k (if needed, varies by spike count)
- Architecture evolution: 2-4k
- SPEC.md creation: 2-3k

**Factors increasing cost:**
- Large existing codebase to investigate
- Many unknowns requiring spikes
- Complex architecture with many components
- Extensive parallel investigation

### /conduct Token Breakdown

**Typical:** 50k+ tokens (scales with component count)

**Formula:** `Base (10k) + (Components × 8k) + Integration (5k) + Documentation (3k)`

**Example (3 components):**
- Base: 10k
- Component 1: 8k (skeleton, implement, validate, test)
- Component 2: 8k
- Component 3: 8k
- Integration: 5k
- Documentation: 3k
- **Total: 42k**

**Factors increasing cost:**
- Many components (linear scaling)
- Variant exploration (+15k per variant per component)
- Complex integration tests (+5-10k)
- Multiple fix iterations per component (+2-4k each)

### Budget Management

**If approaching token limit:**

1. **Checkpoint progress:**
   - Git commit completed work
   - Update PROGRESS.md
   - Note: "Paused at Component 3 due to token limit"

2. **Resume next session:**
   - Read PROGRESS.md
   - Continue from last checkpoint
   - No context loss

3. **Optimize if possible:**
   - Reduce parallel investigations (sequential instead)
   - Skip optional validation steps
   - User decides: Speed vs thoroughness

**Token limit is not a failure** - orchestration is designed for checkpointing and resumption.

---

**Bottom line:** This reference contains detailed workflows that were too verbose for SKILL.md. Consult when you need step-by-step guidance for specific phases or troubleshooting specific issues.
