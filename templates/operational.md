# Operational Procedures

## Circular Dependency Detection

**When:** Phase 1 (Skeleton), after all skeleton-builders return

**How:**
1. **Extract dependencies from skeleton responses**
   - Parse each skeleton response for "Depends on: [...]"
   - Build dependency map: `{ComponentA: [ComponentB, ComponentC], ComponentB: [], ...}`

2. **Build dependency graph**
   ```python
   graph = {
       'password_reset_service': ['email_service', 'user_repository'],
       'email_service': [],
       'user_repository': []
   }
   ```

3. **DFS cycle detection**
   ```
   visited = set()
   recursion_stack = set()

   for each component:
       if component not in visited:
           if has_cycle(component, visited, recursion_stack, graph):
               FAIL: Circular dependency detected
               Show cycle path
               STOP

   def has_cycle(node, visited, rec_stack, graph):
       visited.add(node)
       rec_stack.add(node)

       for neighbor in graph[node]:
           if neighbor not in visited:
               if has_cycle(neighbor, visited, rec_stack, graph):
                   return True
           elif neighbor in rec_stack:
               return True  # Cycle found!

       rec_stack.remove(node)
       return False
   ```

4. **On cycle detection:**
   ```
   🚨 CIRCULAR DEPENDENCY DETECTED

   Cycle path: C → A → B → C

   This must be fixed in SPEC.md before proceeding.

   Suggestions:
   - Introduce abstraction/interface to break cycle
   - Merge cyclic components into one
   - Invert dependency direction

   STOP - do not proceed
   ```

5. **On success:**
   - Compute topological sort for implementation order
   - Store in PROGRESS.md

---

## Fix-Validate Loop

**Pattern:** Used in testing and validation phases

**Structure:**
```
MAX_ATTEMPTS = 3

for attempt in 1 to 3:
    # Run validation
    run_validation_command()

    # Check result
    if PASSED:
        break  # Success, exit loop

    # Handle failure
    if FAILED:
        collect_errors()

        if attempt < 3:
            # Try to fix
            spawn_fix_executor(errors)
            wait_for_fix()
            # Loop continues to attempt + 1

        if attempt == 3:
            # Out of attempts
            escalate_to_user(errors, all_attempts)
            STOP
```

**Example (Testing Phase):**
```
for attempt in 1 to 3:
    bash: pytest tests/ --cov=src -v

    if all_tests_passing AND coverage >= target:
        break

    if attempt < 3:
        spawn fix-executor with test failures
        wait for fix

    if attempt == 3:
        ESCALATE:
        "Cannot fix test failures after 3 attempts.
         Failures: [list]
         Attempts: [what tried]
         Need guidance."
```

---

## Combining Reviewer Findings

**When:** Phase 4 (Validation), after 6 reviewers return

**How:**
1. **Parse JSON responses**
   ```
   Parse all 6 JSON responses:
   - security-auditor → sec_result
   - performance-optimizer → perf_result
   - code-reviewer (pass 1) → review1_result
   - code-reviewer (pass 2) → review2_result
   - code-beautifier → beauty_result
   - documentation-reviewer → doc_result
   ```

2. **Merge into combined lists**
   ```
   all_critical = []
   all_important = []
   all_minor = []

   for result in [sec, perf, review1, review2, beauty, doc]:
       all_critical.extend(result["critical"])
       all_important.extend(result["important"])
       all_minor.extend(result["minor"])
   ```

3. **Deduplicate**
   ```
   Remove duplicates where same file:line:issue
   (Multiple reviewers may flag same issue)
   ```

4. **Prioritize and fix**
   ```
   if all_critical OR all_important:
       spawn fix-executor with combined list
       wait for fixes
       re-run pytest + ruff (sanity check)
       if passed:
           re-run all 6 reviewers to verify
       loop until clean

   if only minor issues:
       review manually, accept or fix
   ```

---

## PROGRESS.md Updates

**When:** After each major step/phase completes

**Format:**
```markdown
# /conduct Progress Tracking

Started: 2025-01-15 14:30:00
Spec: .spec/SPEC_password-reset.md
Working Directory: /path/to/project

## Phase 0: Parse Spec
Status: COMPLETE
Timestamp: 2025-01-15 14:30:15
Components extracted: 3 (password_reset_service, email_service, user_repository)
Dependencies validated: ✓ No cycles
Git commit: abc123f

## Phase 1: Skeleton
Status: COMPLETE
Timestamp: 2025-01-15 14:35:22
Production files: 3
Test files: 3
Circular deps: None ✓
Syntax validation: ✓ All valid
Git commit: def456a

## Phase 2: Implementation
Status: IN_PROGRESS
Timestamp: 2025-01-15 14:40:00

### Batch 1 (no deps)
Files: email_service.py, user_repository.py
Status: COMPLETE
Git commit: ghi789b

### Batch 2 (depends on batch 1)
Files: password_reset_service.py
Status: IN_PROGRESS
...
```

**For /solo (simpler):**
```markdown
# /solo Progress Tracking

Started: 2025-01-15 14:30:00
Task: Add rate limiting middleware
Spec: .spec/BUILD_rate-limit.md

## Implementation
Status: COMPLETE
File: src/middleware/rate_limit.py (45 lines)
Git commit: abc123f

## Testing
Status: COMPLETE
File: tests/middleware/test_rate_limit.py (8 tests)
Coverage: 92%
Git commit: def456a

## Validation
Status: IN_PROGRESS
Linting: ✓ PASS
Security review: ✓ No issues
Code review: 1 important issue (fixing...)
...
```

---

## TodoWrite Timing & Content

**When:** After each major phase completes

**What to write:**
```json
[
  {"content": "Phase 0: Parse Spec", "status": "completed", "activeForm": "Parsing spec"},
  {"content": "Phase 1: Skeleton", "status": "completed", "activeForm": "Creating skeletons"},
  {"content": "Phase 2: Implementation", "status": "in_progress", "activeForm": "Implementing components"},
  {"content": "Phase 3: Testing", "status": "pending", "activeForm": "Testing implementation"},
  {"content": "Phase 4: Validation", "status": "pending", "activeForm": "Validating quality"},
  {"content": "Phase 5: Complete", "status": "pending", "activeForm": "Completing"}
]
```

**High-level only** - details go in PROGRESS.md

**For /solo (simpler):**
```json
[
  {"content": "Implementation", "status": "completed", "activeForm": "Implementing"},
  {"content": "Testing", "status": "completed", "activeForm": "Testing"},
  {"content": "Validation", "status": "in_progress", "activeForm": "Validating"},
  {"content": "Complete", "status": "pending", "activeForm": "Completing"}
]
```

---

## Git Commit Messages

**Pattern:** `[command]: [phase/step] - [brief description]`

**Examples:**
- `conduct: Phase 0 - Parse spec`
- `conduct: Phase 1 - Skeletons complete`
- `conduct: Phase 2, Batch 1 - email_service + user_repository`
- `conduct: Phase 3 - Testing complete`
- `conduct: Phase 4 - Validation passed`
- `solo: Implementation - rate limiting middleware`
- `solo: Testing complete - 8 tests passing`
- `solo: Complete - rate limiting added`

**Include co-author:**
```
[command]: [description]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```
