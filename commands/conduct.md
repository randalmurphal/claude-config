---
name: conduct
description: Orchestrate complex development tasks using orchestration MCP - BUILD what the user requests with REAL validation
---

# /conduct - Orchestrated Development with MCP

**USE THIS FOR:** Complex multi-module tasks that need intelligent coordination with bulletproof validation.

## What Changed from Previous Version

**Previous Issues:**
- Self-validation (finalize_phase asked "did tests pass?")
- No real checkpoints (couldn't recover from failures)
- No parallel work support
- Same workflow for 1-file and 100-file tasks
- 15 phantom tools documented but not implemented

**Current Version:**
- **REAL validation** - Actually runs pytest/ruff/imports
- **Git checkpoints** - Rollback on failures
- **Parallel work** - Git worktrees with smart merging
- **Complexity scaling** - Adapts workflow to task size
- **Task decomposition** - Breaks massive tasks into subtasks
- **Architecture-first workflow** - Define interfaces before implementation (NEW)
- **Dependency-aware execution** - Parallel execution respecting dependencies (NEW)
- **ADR storage** - Architectural decisions stored to PRISM (NEW)
- **21 working tools** - All implemented and tested

## When to Use /conduct

✅ **DO use /conduct for:**
- Multi-module features (3+ files across different modules)
- System refactors (touching 10+ files)
- Architecture changes (affects multiple layers)
- Massive tasks (30+ files, 20+ hours)

❌ **DON'T use /conduct for:**
- Single file changes (just edit directly)
- Quick fixes (faster without orchestration overhead)
- Exploratory work (use spikes first)

## Architecture-First Workflow (NEW)

For medium/large/massive tasks, /conduct now uses an architecture-first approach that defines interfaces BEFORE writing any implementation code.

### What Happens During Architecture Phase

**1. Parse READY.md (if present):**
```
Extracts:
- Components to build (from "Files to Create/Modify" section)
- Requirements (IMMUTABLE section)
- Proposed approach (EVOLVABLE section)
- Implementation phases
- Quality requirements
```

**2. Define Interfaces:**
```
For each component, generates:
- Public methods with signatures
- Data structures with fields
- Error types
- Dependencies on other components

Example architecture.yaml:
components:
  user_auth:
    public_methods:
      - name: authenticate
        parameters: [{name: credentials, type: Dict}]
        return_type: AuthToken
    data_structures:
      - name: AuthToken
        fields: [{name: token, type: str}, {name: expires_at, type: datetime}]
    error_types: [AuthenticationError, InvalidCredentialsError]
    dependencies: [database_service]
```

**3. Extract Dependencies:**
```
Builds dependency graph:
user_auth → depends on → database_service
payment_processor → depends on → user_auth, transaction_log
transaction_log → depends on → database_service

Parallel execution plan:
Wave 1: database_service (no dependencies)
Wave 2: user_auth, transaction_log (database ready)
Wave 3: payment_processor (auth + log ready)
```

**4. Detect Circular Dependencies:**
```
FAIL LOUD if found:
ERROR: Circular dependency detected:
  user_auth → session_manager → user_auth

System stops and asks user to resolve before continuing.
```

**5. Store Architectural Decisions:**
```
ADRs stored to PRISM (ANCHORS tier, never expires):
- "Why we chose JWT for authentication" (alternatives: sessions, OAuth)
- "Payment processor abstraction" (alternatives: direct Stripe integration)
- "Database connection pooling strategy" (alternatives: connection per request)

Queryable in future sessions for consistent decisions.
```

**6. Validate Architecture:**
```
Checks:
- All dependencies reference defined components
- No circular dependencies
- All components have public interfaces
- Interface signatures are valid Python types
```

### Benefits

✅ **Prevents integration issues** - Interfaces defined upfront, no surprises during implementation
✅ **Enables intelligent parallelization** - Dependency graph ensures correct execution order
✅ **Blocks on circular dependencies** - Catches architectural problems before code is written
✅ **Documents decisions** - ADRs stored to PRISM for future reference
✅ **Supports user queries** - When unknowns block progress, asks clear questions

### When Architecture Phase Runs

- **Small tasks** (1-3 files): SKIPPED - Goes straight to skeleton for fast iteration
- **Medium tasks** (4-10 files): RUNS - Defines interfaces for modules
- **Large tasks** (10-30 files): RUNS - Full interface definition + dependency graph
- **Massive tasks** (30+ files): RUNS - Architecture for each subtask

## Real Workflow

### Small Task (1-3 files, <3h)
```
You: "/conduct Add logging to user service"

1. start_task → complexity="small"
2. skeleton phase → validate imports
3. implementation phase → VALIDATE (pytest/ruff/imports) → CHECKPOINT
4. complete_task
```

### Medium Task (4-10 files, 3-8h)
```
You: "/conduct Implement user authentication with JWT tokens"

1. start_task → complexity="medium"
2. architecture phase →
   - Parse READY.md (if present)
   - Define interfaces: authenticate(), generate_token(), validate_token()
   - Extract dependencies: user_auth → database_service, crypto_service
   - Detect no circular dependencies ✓
   - Store architecture.yaml with interface contracts
   - Store ADR: "JWT chosen over sessions for stateless auth"
3. skeleton phase →
   - Build stubs following architecture.yaml interfaces EXACTLY
   - VALIDATE (imports) → CHECKPOINT
4. implementation phase →
   - Implement methods following interface contracts
   - Dependency-aware: database_service ready first, then user_auth
   - VALIDATE (pytest/ruff/imports) → CHECKPOINT
5. testing phase → VALIDATE
6. complete_task
```

### Large Task (10-30 files, 8-20h, parallel work)
```
You: "/conduct Refactor API layer across auth, cart, and payment modules"

1. start_task → complexity="large" → recommends parallel
2. architecture phase →
   - Parse READY.md or discover components
   - Define interfaces for auth, cart, payment modules
   - Extract dependencies:
     * cart → depends on → auth (needs user session)
     * payment → depends on → cart, auth (needs cart items + user)
   - Build dependency graph: auth (wave 1) → cart (wave 2) → payment (wave 3)
   - Store architecture.yaml + ADRs
   - VALIDATE architecture (no circular deps) ✓
3. create_worktree("auth"), create_worktree("cart"), create_worktree("payment")
4. skeleton phase →
   - Wave 1: auth (no dependencies, starts immediately)
   - Wave 2: cart (waits for auth skeleton complete)
   - Wave 3: payment (waits for cart + auth complete)
   - merge → VALIDATE (interface contracts satisfied) → CHECKPOINT
5. implementation phase (dependency-aware parallel) →
   - Wave 1: auth implementation
   - Wave 2: cart implementation (auth ready)
   - Wave 3: payment implementation (cart + auth ready)
   - merge → VALIDATE → CHECKPOINT
6. integration phase →
   - Validate imports resolve
   - Validate interface contracts
   - Check for circular dependencies
   - Run integration tests
   - Detect code duplication
   - VALIDATE → CHECKPOINT
7. complete_task → cleanup worktrees
```

### Massive Task (30+ files, 20-100h, decomposed)
```
You: "/conduct Build complete e-commerce platform"

1. start_task → complexity="massive"
2. decompose_task → 5 subtasks:
   - Foundation (data models)
   - Authentication
   - Shopping cart
   - Payment processing
   - Admin dashboard
3. For each subtask:
   a. get_next_subtask
   b. Run LARGE workflow
   c. mark_subtask_complete → CHECKPOINT
4. Integration testing
5. complete_task
```

### With Validation Failure (blocks progression)
```
You: "/conduct Implement user registration"

1. start_task
2. skeleton phase → imports pass → CHECKPOINT
3. implementation phase
4. finalize_phase("implementation") → TESTS FAIL

System: "Cannot proceed to next phase. Validation failed:
- test_registration.py::test_email_validation FAILED
- Coverage: 87% (need 90%+)

Suggestion: Fix failing test and add tests for edge cases."

5. You fix tests
6. finalize_phase("implementation") → TESTS PASS → CHECKPOINT
7. Continue...
```

### With Rollback
```
You: "/conduct Refactor authentication system"

1. start_task
2. skeleton phase → CHECKPOINT (checkpoint_a)
3. implementation phase → CHECKPOINT (checkpoint_b)
4. testing phase → something breaks badly
5. list_checkpoints → see checkpoint_a and checkpoint_b
6. rollback_to_checkpoint(checkpoint_b) → restore to implementation
7. Fix implementation
8. Continue from implementation phase
```

### With Circular Dependency Detection (NEW)
```
You: "/conduct Implement session management system"

1. start_task → complexity="medium"
2. architecture phase →
   - Define interfaces for session_manager, user_auth
   - Extract dependencies:
     * user_auth → depends on → session_manager (needs session context)
     * session_manager → depends on → user_auth (needs user validation)
   - ERROR: Circular dependency detected!

System: "Architecture validation failed. Circular dependency found:
  user_auth → session_manager → user_auth

Suggestion: Break the cycle by:
1. Introduce session_storage as independent component
2. Have both user_auth and session_manager depend on session_storage
3. Remove direct dependency between user_auth and session_manager"

3. You fix architecture (update READY.md or provide new approach)
4. Re-run architecture phase → no cycles detected ✓
5. Continue with skeleton phase
```

### With User Query Generation (NEW)
```
You: "/conduct Implement payment processing"

1. start_task → complexity="medium"
2. architecture phase →
   - Define interfaces for payment_processor
   - Unknown detected: "How should payment provider credentials be stored?"
   - Unknown detected: "Which payment providers to support (Stripe, PayPal, both)?"
   - Generate queries, store as pending in Redis

System: "Architecture phase blocked on 2 unknowns. Generated queries:

Query 1 [PENDING]: How should payment provider credentials be stored?
Options: environment variables, encrypted config file, secret manager
Impact: Affects initialization and security model

Query 2 [PENDING]: Which payment providers to support?
Options: Stripe only, PayPal only, both with abstraction layer
Impact: Affects interface design and testing complexity

Continuing with independent components while waiting for answers..."

3. System continues working on unblocked components (logging, database models)
4. You answer queries: "Use environment variables" + "Stripe only for MVP"
5. System marks queries as answered, resumes payment_processor implementation
```

## Available Tools (21 total, all working)

**Core Workflow (7):**
- start_task (with complexity detection)
- prepare_phase
- finalize_phase (with REAL validation)
- record_phase_result
- complete_task
- get_task_status
- parse_ready_specification

**Validation (1):**
- validate_phase (runs pytest/ruff/imports)

**Checkpoints (3):**
- create_checkpoint
- rollback_to_checkpoint
- list_checkpoints

**Worktrees (2):**
- create_worktree
- merge_worktrees

**Complexity (1):**
- analyze_task_complexity

**Decomposition (3):**
- decompose_task
- get_next_subtask
- mark_subtask_complete

**Intelligence (4):**
- analyze_project
- augment_ready_spec
- validate_ready_spec
- synthesize_learnings

## Success Criteria (How to know it's working)

✅ **Validation blocks progression** - Can't move forward with failing tests
✅ **Checkpoints auto-created** - After each validated phase
✅ **Rollback works** - Can recover from failures without losing all work
✅ **Parallel work isolated** - Modules don't conflict in worktrees
✅ **Complexity detected accurately** - Right workflow for task size
✅ **Progress preserved** - Redis state + git commits = full recovery

## Key Features in Action

### 1. Real Validation (Biggest Change)

**Previous (broken):**
```
finalize_phase → "Did tests pass?" → you say "yes" → chaos
```

**Current (bulletproof):**
```
finalize_phase → runs pytest → tests fail → progression BLOCKED
→ "Fix test_auth.py::test_login before proceeding"
→ you fix tests
→ finalize_phase → tests pass → CHECKPOINT created → proceed
```

### 2. Git Checkpoints (Automatic Snapshots)

**Automatic:**
```
skeleton phase complete → VALIDATE → CHECKPOINT (checkpoint_a)
implementation phase complete → VALIDATE → CHECKPOINT (checkpoint_b)
testing phase fails badly → rollback_to_checkpoint(checkpoint_b)
→ git reset --hard to checkpoint_b
→ Redis state cleared to checkpoint_b
→ continue from implementation
```

**Manual:**
```
# Create checkpoint manually
create_checkpoint(task_id, phase="custom", validation_passed=True)

# List all checkpoints
list_checkpoints(task_id) → shows all snapshots

# Rollback to any checkpoint
rollback_to_checkpoint(task_id, checkpoint_id)
```

### 3. Parallel Work with Worktrees

**For multi-module tasks:**
```
# Architecture identifies 3 modules
architecture_phase → ["auth", "cart", "payment"]

# Create isolated worktrees
create_worktree(task_id, module="auth") → worktree_auth/
create_worktree(task_id, module="cart") → worktree_cart/
create_worktree(task_id, module="payment") → worktree_payment/

# Agents work in parallel (no conflicts!)
skeleton_phase → all 3 agents work simultaneously

# Merge when done
merge_worktrees(task_id, modules=["auth", "cart", "payment"])
→ smart conflict resolution
→ validates after merge
→ CHECKPOINT created
```

### 4. Complexity Scaling (Right Workflow for Size)

**Auto-detection:**
```
"Add logging" → small → skeleton → implement → validate
"Implement auth" → medium → arch → skeleton → implement → test → validate
"Refactor API" → large → arch → skeleton → validate → implement → test → integrate
"Build platform" → massive → decompose into 5 subtasks
```

**Manual override:**
```
start_task(description="...", complexity="large")  # Force large workflow
```

### 5. Task Decomposition (Massive Tasks)

**Automatic breakdown:**
```
"Build e-commerce platform"
→ decompose_task
→ Returns 5 subtasks:
   1. Foundation (models, DB schema)
   2. Authentication (register, login, JWT)
   3. Product catalog (CRUD, search)
   4. Shopping cart (persistence, checkout)
   5. Admin dashboard (orders, users)

→ For each subtask:
   get_next_subtask → run full workflow → mark_subtask_complete

→ Integration testing
→ complete_task
```

## Migration from V1

If you have old V1 tasks:
- Remove references to phantom tools (many were documented but not implemented)
- Add complexity hints to description ("small change" vs "major refactor")
- Expect validation to actually run (tests must pass!)
- Use checkpoints for recovery (no more manual git operations)

## Tips for Best Results

1. **Write good descriptions** - "small change" vs "complete refactor" affects complexity detection
2. **Trust the validation** - If tests fail, fix them (don't bypass)
3. **Use checkpoints** - Don't be afraid to rollback and try again
4. **Let it decompose massive tasks** - Easier than doing all at once
5. **Review merge conflicts** - Smart strategy isn't perfect, check its work
6. **Check complexity recommendations** - Helps select right workflow

## Example Usage

```bash
# In your project directory (optionally with .prelude/READY.md)
/conduct "implement user authentication with JWT tokens"

# System analyzes complexity → "medium"
# Selects workflow: architecture → skeleton → implementation → testing
# Runs REAL validation at each checkpoint
# Blocks progression if tests fail
# Creates git checkpoints after validated phases
# Result: Bulletproof autonomous development
```

## Common Patterns

### Pattern: Fix Until It Works
```
finalize_phase("implementation") → tests fail
→ fix tests
→ finalize_phase("implementation") → tests fail again
→ fix more tests
→ finalize_phase("implementation") → tests pass → CHECKPOINT
→ proceed to next phase
```

### Pattern: Rollback and Retry
```
implementation complete → CHECKPOINT
testing complete → CHECKPOINT
integration breaks everything
→ list_checkpoints → see all checkpoints
→ rollback_to_checkpoint(testing_checkpoint)
→ fix implementation
→ finalize_phase("implementation") → CHECKPOINT
→ continue to testing
```

### Pattern: Parallel Module Work
```
architecture identifies N modules
→ create_worktree for each module
→ agents work in parallel (no conflicts)
→ merge_worktrees(all modules)
→ VALIDATE → CHECKPOINT
→ if merge validation fails:
   → fix conflicts
   → merge_worktrees again
   → VALIDATE → CHECKPOINT
```

### Pattern: Massive Task Decomposition
```
"Build complete system"
→ decompose_task → 5 subtasks
→ while get_next_subtask has work:
   → run full workflow for subtask
   → VALIDATE → CHECKPOINT
   → mark_subtask_complete
   → get_next_subtask
→ all subtasks complete
→ integration testing
→ complete_task
```

## Workflow Visualization

### Small Task Flow
```
start → skeleton → [validate] → implement → [validate+checkpoint] → done
```

### Medium Task Flow
```
start → arch → skeleton → [validate+checkpoint]
→ implement → [validate+checkpoint]
→ test → [validate] → done
```

### Large Task Flow (with parallel)
```
start → arch → [identify modules]
→ create_worktrees
→ skeleton (parallel) → merge → [validate+checkpoint]
→ implement (parallel) → merge → [validate+checkpoint]
→ integrate → [validate] → cleanup → done
```

### Massive Task Flow (with decomposition)
```
start → decompose → [5 subtasks]
→ subtask 1: [full large workflow] → [checkpoint]
→ subtask 2: [full large workflow] → [checkpoint]
→ subtask 3: [full large workflow] → [checkpoint]
→ subtask 4: [full large workflow] → [checkpoint]
→ subtask 5: [full large workflow] → [checkpoint]
→ integrate all → [validate] → done
```

## Error Recovery Patterns

### When Validation Fails
```
1. Read the validation error message
2. Fix the specific issue (failing test, linting error, import error)
3. Re-run finalize_phase until it passes
4. Validation blocks progression until fixed
```

### When Implementation Breaks
```
1. list_checkpoints → see all snapshots
2. rollback_to_checkpoint(last_good_checkpoint)
3. Fix implementation with better approach
4. finalize_phase → VALIDATE → new CHECKPOINT
5. Continue forward
```

### When Merge Conflicts Occur
```
1. merge_worktrees uses "smart" strategy (prefers simpler code)
2. Review conflicts in response
3. If conflicts unacceptable:
   → Fix conflicted files manually
   → validate_phase to ensure nothing broke
   → create_checkpoint to snapshot fix
4. Continue workflow
```

## What Makes It Bulletproof

1. **Real validation blocks bad code** - Can't proceed with failing tests
2. **Git checkpoints preserve progress** - Never lose hours of work
3. **Worktrees eliminate conflicts** - Parallel work without stepping on toes
4. **Complexity detection** - Right workflow for task size
5. **Decomposition handles massive tasks** - Break 100-file tasks into chunks
6. **Architecture-first prevents integration issues** (NEW) - Interfaces defined before code, no surprises
7. **Circular dependency detection** (NEW) - Catches architectural problems before implementation
8. **Dependency-aware parallelization** (NEW) - Smart execution order respects dependencies
9. **User query generation** (NEW) - Continues work on unblocked tasks while waiting for answers
10. **ADR storage to PRISM** (NEW) - Architectural decisions persist across sessions
11. **All tools implemented** - No phantom features, everything works

## Quick Reference

**Start orchestration:**
```
/conduct "your task description"
```

**If validation fails:**
- Fix the issue
- Re-run finalize_phase
- System blocks until tests pass

**If things go wrong:**
- list_checkpoints
- rollback_to_checkpoint(checkpoint_id)
- Continue from checkpoint

**For massive tasks:**
- System decomposes automatically
- Work through subtasks sequentially
- Each subtask checkpointed

**For parallel work:**
- System creates worktrees automatically
- Merges with smart conflict resolution
- Validates after merge

---

**Bottom Line:**
- REAL validation (no more self-validation lies)
- Git checkpoints (rollback on failures)
- Parallel worktrees (isolated module work)
- Complexity scaling (right workflow for size)
- Task decomposition (handle massive tasks)
- Architecture-first workflow (interfaces before implementation) ✨ NEW
- Dependency-aware execution (smart parallel ordering) ✨ NEW
- Circular dependency detection (fail loud before code) ✨ NEW
- User query generation (continue on unblocked tasks) ✨ NEW
- ADR storage to PRISM (decisions persist forever) ✨ NEW
- 21 working tools (all implemented, all tested)

**When you run /conduct, you get bulletproof autonomous development with architecture-first planning, dependency-aware parallelization, and validation that actually works.**