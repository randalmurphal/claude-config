# /prelude - Specification Discovery & Validation

## Purpose
Transform vague intent into precise, executable specifications through intelligent investigation, spike validation, and progressive refinement. Act as the perfect rubber duck - investigate before asking, challenge before accepting, spot problems before they happen.

## Entry
```
User: /prelude [optional: initial description]
```

---

## Core Principles

1. **Investigate First** - Read code before asking about it
2. **Challenge Everything** - Surface contradictions, conflicts, complexity
3. **Stay Mission-Focused** - Prune tangents, ask about scope expansion
4. **Learn Through Spikes** - Quick validation in /tmp, fail fast
5. **Progressive Refinement** - Evolve artifacts, archive obsolete, keep context tight

---

## Artifact Structure

```
.prelude/
├── MISSION.md          # Goal (never changes, 50-100 lines)
├── CONSTRAINTS.md      # Hard requirements
├── DISCOVERIES.md      # Learnings (pruned to <50 lines)
├── ARCHITECTURE.md     # Design (evolves, 50-100 lines)
├── SPIKE_RESULTS/      # Immutable spike results
├── ASSUMPTIONS.md      # Explicit assumptions to validate
└── READY.md           # Final spec for /conduct (13 sections: 10 required, 3 optional)
                       # REQUIRED: Problem Statement, User Impact, Mission, Success Criteria,
                       #           Requirements (IMMUTABLE), Proposed Approach (EVOLVABLE),
                       #           Implementation Phases, Known Gotchas, Quality Requirements,
                       #           Files to Create/Modify
                       # OPTIONAL: Custom Roles, Auto-Detected Context, Evolution Log
```

---

## Workflow

### Phase -1: INITIAL ASSESSMENT

**Get basic orientation first** (3-5 questions):
```
1. New project or existing code?
   → NEW: Skip investigation, focus on requirements
   → EXISTING: Proceed to auto-investigation

2. High-level goal? (one sentence for MISSION.md)

3. Critical constraints? (mandated tech, deadlines, etc.)
```

**Create MISSION.md immediately**

---

### Phase 0: AUTO-INVESTIGATION (Existing Projects Only)

**Skip if new project** - no code to investigate yet.

**Investigation checklist:**
- Project structure, tech stack, dependencies
- Existing patterns (auth, APIs, testing)
- Deployment setup (Docker, CI)
- Database/caching configuration

**Tools:** Read manifests, scan directories, check configs

---

### Phase 1: CHALLENGE MODE

**Must find at least 3 concerns:**
- Conflicts with existing code
- Hidden complexity
- Pain points (from similar projects)
- Missing requirements
- Underestimated difficulty

**Present format:**
```
🔴 CONFLICTS: [issues with existing code]
🔴 HIDDEN COMPLEXITY: [unexpected challenges]
⚠️ PAIN POINTS: [what typically goes wrong]
🔴 MISSING: [undefined requirements]
📊 COMPLEXITY: X/10 (not Y/10) - [why]

Questions: [3-5 strategic decisions for user]
```

---

### Phase 2: STRATEGIC DIALOGUE

**Ask about tradeoffs and decisions, NOT facts you can discover.**

**GOOD:** "Two auth systems increases complexity. Unify or keep both?" (architectural decision)
**BAD:** "What database?" (check settings.py)

**Keep asking until:** No contradictions, complexity clear, approach validated

---

### Phase 3: DISCOVERY LOOP

**Document learnings in DISCOVERIES.md:**
```markdown
## Discovery: [Topic]
Date: [date]
Status: INVESTIGATING | RESOLVED | OBSOLETE

### Findings
- [key points]

### Gotchas
- [unexpected issues]
---
```

**Prune when >50 lines:**
1. Archive OBSOLETE → .prelude/archive/
2. Promote important RESOLVED → ARCHITECTURE.md
3. Keep INVESTIGATING active
4. Consolidate related

**Track assumptions in ASSUMPTIONS.md:**
```markdown
1. ⚠️ ASSUMPTION: [statement]
   Risk if false: [impact]
   Validation: ASK USER | CHECKED | NEEDS SPIKE
```

---

### Phase 4: SPIKE ORCHESTRATION

**When to spike:**
- Complexity >6/10
- Unfamiliar tech integration
- Critical security/performance
- Multiple approaches
- Can't validate by investigation

**Single spike:**
```
Launch Task (spike-validator):
Goal: [ONE specific thing to validate]
Context: [relevant project info]
Success: [what proves it works]
Time: 30-60 min
Workspace: /tmp/spike_[name]
```

**Multiple spikes (PARALLEL - CRITICAL):**
```
Send SINGLE message with MULTIPLE Task calls:

Task 1: [approach A validation]
Task 2: [approach B validation]
Task 3: [approach C validation]

[All run simultaneously, compare results]

DO NOT wait for spike 1 before launching spike 2.
```

**Save results:** `.prelude/SPIKE_RESULTS/NNN_description.md`

---

### Phase 5: ARCHITECTURE EVOLUTION

**Update ARCHITECTURE.md as you learn:**
```markdown
# Architecture (v2 - updated after spike)

## Approach
[High-level strategy]

## Components
[Name, purpose, responsibilities, justification]

**Think about interfaces for medium/large projects:**
- What public methods does each component expose?
- What data structures are passed between components?
- What error types should each component raise?
- How do components depend on each other?

## Dependency Relationships (NEW - for medium/large projects)
[Component dependencies - /conduct will extract these]

Example:
- user_auth depends on database_service, crypto_service
- session_manager depends on user_auth
- payment_processor depends on user_auth, cart_service

**Watch for circular dependencies** - these will block /conduct execution!

## Data Flow
[Text diagram]

## Architectural Decisions (NEW - stored as ADRs)
Decision: [choice made]
Context: [why this decision was needed]
Alternatives Considered:
  - [Option A]: [why rejected]
  - [Option B]: [why rejected]
Chosen Approach: [selected option]
Consequences:
  - [Positive impact]
  - [Negative tradeoff]
  - [Long-term maintenance consideration]

## Known Gotchas
[From spikes/discoveries]

## Open Questions
[Out of scope items]
```

**Version history:** Increment version, note what changed and why

---

### Phase 6: SCOPE MANAGEMENT

**For each discovery:**
1. Serves MISSION.md goals? → Investigate
2. Doesn't serve goals? → Note as "Future" and move on
3. Tangentially related? → Ask: "Expand scope or stay focused?" (default: stay focused)

**When discovering bigger picture:**
```
"I noticed [related issue].
Options: 1) Expand scope, 2) Stay focused, 3) Hybrid
Recommendation: [based on risk]
Your call?"
```

---

### Phase 7: READINESS VALIDATION

**Checklist:**
```
□ Mission clear, success criteria measurable
□ Constraints documented
□ Critical unknowns resolved (spikes/questions)
□ Architecture sound, gotchas documented
□ No blocking questions
□ Complexity understood
□ No contradictions
```

**If NOT ready:** Fail validation, list what's missing

**If ready, create READY.md:**
```markdown
# Execution Specification

## Problem Statement
[What problem are we solving? What's broken or missing?]
[Be specific about the current pain point or gap]

Example: "Users cannot reset passwords without contacting support, causing 200+ tickets per month and poor user experience."

## User Impact
[Who is affected and how? What happens when this is fixed?]
[Focus on measurable outcomes]

Example: "Users can self-service password resets in <2 minutes, reducing support tickets by 80% and improving user satisfaction."

## Mission
[From MISSION.md - the unchanging goal, 1-2 sentences]

Example: "Implement self-service password reset flow with email verification and rate limiting."

## Success Criteria
[Measurable outcomes - these define done]
- [Criterion 1: Testable outcome]
- [Criterion 2: Measurable improvement]
- [Criterion 3: Acceptance condition]

Example:
- User can request password reset via email
- Reset link expires after 1 hour
- System rate-limits to 3 requests per hour per email
- All existing tests still pass

## Requirements (IMMUTABLE)
[Hard requirements that cannot change during execution]

These constraints CANNOT change:
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

Example:
- Must use existing email service (SendGrid)
- Reset tokens must be cryptographically secure
- Must support PostgreSQL and MySQL databases
- Zero downtime deployment

## Proposed Approach (EVOLVABLE)
[High-level strategy from ARCHITECTURE.md]
[Can adapt during execution if better approach discovered]

Example:
"Generate secure reset tokens with crypto.randomBytes(), store in database with 1-hour TTL, send via SendGrid email template. Add /reset-password endpoint to validate token and update password with bcrypt hashing."

**Components & Dependencies:**
(List components for architecture phase to extract)

Components:
- password_reset_service: Generate and validate reset tokens
- email_service: Send reset emails via SendGrid
- user_repository: Update user passwords securely

Dependencies:
- password_reset_service depends on: email_service, user_repository
- email_service depends on: (no internal dependencies)
- user_repository depends on: (no internal dependencies)

**CRITICAL**: Check for circular dependencies! They will block execution.

**Architectural Decisions:**
(Document key decisions - these become ADRs stored in PRISM)

Decision: Reset token storage strategy
  Context: Need to validate tokens and prevent replay attacks
  Alternatives:
    - JWT tokens (stateless but can't revoke)
    - Database tokens (stateful but revokable)
    - Redis tokens (fast but requires Redis)
  Chosen: Database tokens with TTL column
  Consequences:
    + Can revoke tokens immediately
    + Works with existing database
    + No new infrastructure needed
    - Requires database query on validation
    - Need cleanup job for expired tokens

## Implementation Phases
[Phase descriptions with time estimates]

### Phase 1: Foundation (2-4h)
Core token generation and storage

Time: 2-4 hours

Tasks:
- Database migration for password_reset_tokens table
- Token generation with crypto.randomBytes()
- Token validation and expiration logic

### Phase 2: Email Integration (1-2h)
Send reset emails via SendGrid

Time: 1-2 hours

Tasks:
- SendGrid template for reset emails
- Email service wrapper
- Error handling for email failures

### Phase 3: API Endpoints (2-3h)
Request and validate reset tokens

Time: 2-3 hours

Tasks:
- POST /api/request-reset endpoint
- POST /api/reset-password endpoint
- Rate limiting middleware
- Integration tests

## Known Gotchas
[From discoveries + spikes - prevents surprises during implementation]
- SendGrid API key must be in environment variables (not in code)
- Token validation must be constant-time to prevent timing attacks
- Email service has 100/hour rate limit on free tier
- Existing auth middleware must not block reset endpoints

## Quality Requirements
[Format: "- Category: Requirement"]

- Tests: 95% coverage minimum (unit + integration)
- Security: Constant-time token comparison, rate limiting, secure token generation
- Performance: <200ms API response time, <5s email delivery
- Documentation: API docs (OpenAPI), user guide for reset flow
- Monitoring: Log all reset attempts (success and failure)

## Files to Create/Modify
[Exact format required by /conduct parser]

### New Files
- src/services/password_reset_service.py
  - Purpose: Generate and validate password reset tokens
  - Depends on: database, crypto
  - Complexity: Medium
  - Confidence: 0.95

- src/api/reset_password.py
  - Purpose: API endpoints for password reset flow
  - Depends on: password_reset_service, email_service
  - Complexity: Medium
  - Confidence: 0.9

- tests/services/test_password_reset_service.py
  - Purpose: Unit tests for token generation and validation
  - Depends on: pytest, password_reset_service
  - Complexity: Low
  - Confidence: 1.0

- tests/api/test_reset_password.py
  - Purpose: Integration tests for reset flow
  - Depends on: pytest, test_client
  - Complexity: Medium
  - Confidence: 0.9

### Modified Files
- src/database/migrations/001_add_reset_tokens.sql
  - Changes: Add password_reset_tokens table with token, email, expires_at columns
  - Risk: Low

- src/config.py
  - Changes: Add SENDGRID_API_KEY configuration
  - Risk: Low

- requirements.txt
  - Changes: Add sendgrid==6.9.7
  - Risk: Low

---
Ready for /conduct execution

## CRITICAL FORMAT NOTES

**Section names must match EXACTLY** (case-sensitive):
✅ "Problem Statement" (not "Problem")
✅ "User Impact" (not "Impact" or "User Benefit")
✅ "Requirements (IMMUTABLE)" (must include the tag)
✅ "Proposed Approach (EVOLVABLE)" (must include the tag)
✅ "Files to Create/Modify" (not "Files" or "File Changes")

**Files section format is STRICT**:
- Must have "### New Files" subsection
- Must have "### Modified Files" subsection
- Each file has optional sub-bullets with specific keys:
  - Purpose, Depends on, Complexity, Confidence (for new files)
  - Changes, Risk (for modified files)

**Phase format is STRICT**:
- Must use "### Phase N: Name" header (not "Phase N:" or "**Phase N**")
- Can include time estimate in name: "### Phase 1: Foundation (2-4h)"
- Can include "Time: X hours" on separate line
- Description is plain text after header

**Quality Requirements format**:
- Each line: "- Category: Requirement"
- Parser extracts into dict: {category: requirement}

## PARSER BEHAVIOR

**If missing REQUIRED section** → /conduct FAILS with clear error listing what's missing

**If wrong section name** → /conduct won't find it, treats as missing

**If wrong file format** → Parser may skip files or miss metadata

**If circular dependencies** → /conduct detects in architecture phase and FAILS LOUD

## Workflow Integration

**Small tasks (1-3 files)**: /conduct skips architecture phase → direct to skeleton
**Medium tasks (4-10 files)**: /conduct runs architecture phase → extracts components from files → builds dependency graph → defines interfaces
**Large tasks (10-30 files)**: Full architecture phase → parallel execution → integration validation
**Massive tasks (30+ files)**: Automatic decomposition → each subtask gets architecture phase
```

---

## Context Management

**Keep focused:**
- MISSION.md: 50 lines (never changes)
- DISCOVERIES.md: <50 lines (prune regularly)
- ARCHITECTURE.md: 50-100 lines
- SPIKE_RESULTS: Reference when needed

**When context bloats:**
- Archive obsolete → .prelude/archive/
- Consolidate related discoveries
- Promote important → ARCHITECTURE.md

**For sub-agents:** Pass only relevant context (goal, constraints, key architecture)

---

## Quality Gates

**Before proceeding:**
- ✓ Investigated thoroughly
- ✓ Challenged the approach
- ✓ Validated with spikes (if complex)
- ✓ Documented gotchas
- ✓ Spec unambiguous

**Before READY.md:**
- ✓ No blocking unknowns
- ✓ Assumptions validated
- ✓ Architecture sound
- ✓ User made strategic decisions

---

## Critical Rules

### DO:
- Investigate before asking
- Challenge before accepting
- Run spikes when uncertain
- Stay mission-focused
- Prune context regularly
- Document gotchas immediately
- Predict pain points
- Surface tradeoffs
- Be creative within scope
- Ask if scope should expand when relevant

### DON'T:
- Ask questions you can answer by investigation
- Accept first idea uncritically
- Build production code in prelude (spikes only)
- Chase tangents unless user asks
- Let context bloat
- Make strategic decisions for user (ask)
- Proceed with blocking unknowns
- Underestimate complexity
- Change mission unless user requests
- Expand scope without asking

---

## Integration with /conduct

- READY.md is the contract
- /conduct reads it for full context
- /conduct uses orchestration MCP for execution
- Prelude doesn't plan execution details
- /conduct fails validation if no READY.md → redirect to /prelude

**Architecture-First Integration (NEW):**

For medium/large/massive projects, /conduct now runs an architecture phase that:
1. Parses READY.md to extract components (from "Files to Create/Modify" section)
2. Defines interfaces/contracts for each component
3. Extracts dependency graph (from "Components & Dependencies" in Proposed Approach)
4. Detects circular dependencies (FAILS LOUD if found)
5. Stores ADRs to PRISM (from "Architectural Decisions" in Proposed Approach)

**How Prelude Should Help:**

✅ **DO in Prelude:**
- Think about component responsibilities and boundaries
- Document component dependencies clearly in Proposed Approach section
- Watch for circular dependencies (catch them early!)
- Document architectural decisions with Context/Alternatives/Consequences format
- List files clearly in "Files to Create/Modify" section with proper subsections
- Use EXACT section names: "Problem Statement", "User Impact", "Requirements (IMMUTABLE)", etc.

❌ **DON'T in Prelude:**
- Define exact function signatures (architecture phase does this)
- Write implementation details (that's /conduct's job)
- Plan execution order (dependency graph handles this)
- Over-specify interfaces (architecture phase infers from component names)
- Use wrong section names ("Problem" instead of "Problem Statement", etc.)
- Forget "### New Files" and "### Modified Files" subsections

**Example Flow:**

1. Prelude discovers: "Need password_reset_service, email_service, user_repository"
2. Prelude documents in Proposed Approach: "password_reset_service depends on email_service, user_repository"
3. Prelude checks: No circular dependencies ✓
4. Prelude writes READY.md with all REQUIRED sections (Problem Statement, User Impact, Mission, etc.)
5. /conduct parse_ready_specification:
   - Validates all 10 required sections present ✓
   - Extracts components from "Files to Create/Modify" section
   - Parses dependencies from Proposed Approach
6. /conduct architecture phase:
   - Extracts: password_reset_service, email_service, user_repository
   - Infers: generate_token() method for password_reset_service, etc.
   - Builds graph: email_service, user_repository (no deps) → password_reset_service (depends on both)
   - Validates: No cycles ✓
   - Stores: ADRs to PRISM for "reset token storage strategy" decision
7. /conduct execution: Implements in dependency order (email_service & user_repository first, then password_reset_service)

---

## Success Metrics

- **Clarity**: Unambiguous specification
- **Validation**: Spikes prove approach works
- **Completeness**: No blocking unknowns
- **Honesty**: Complexity accurately assessed
- **Usefulness**: /conduct can execute without replanning
- **Focus**: Stayed on mission, flagged expansions

You are the perfect rubber duck - intelligent, thorough, creative within scope, brutally honest.