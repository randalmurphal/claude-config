# SPEC.md Format for Orchestration

The SPEC.md must be structured for the orchestrator to extract parallelization info, dependencies, and execution order.

---

## Required Sections

### 1. Metadata

```markdown
# SPEC: [Feature Name]

**Ticket:** JIRA-1234
**Mode:** quick | standard | full
**Risk:** low | medium | high | critical
**Estimated Files:** 5
**Estimated Complexity:** medium
```

### 2. Mission (Immutable)

```markdown
## Mission

One paragraph describing what this implementation achieves.
This is the north star - all work must serve this mission.
```

### 3. Requirements (Immutable)

```markdown
## Requirements

These are IMMUTABLE. Implementation must satisfy ALL of these.

### Functional Requirements
- [ ] FR-1: User can do X
- [ ] FR-2: System handles Y

### Non-Functional Requirements
- [ ] NFR-1: Response time < 200ms
- [ ] NFR-2: Backwards compatible with existing API
```

### 4. Scope Boundaries

```markdown
## Scope

### In Scope
- Implementing new handler in imports/
- Adding BO type for X
- Tests for new functionality

### Out of Scope (DO NOT TOUCH)
- Existing handlers
- Unrelated utilities
- Performance optimization of other code
- Refactoring beyond what's needed

### Flag for Future (discover but don't fix)
- Pre-existing issues found during review
- Improvements that would be nice
- Technical debt in related code
```

### 5. Files to Create/Modify

**CRITICAL: This section drives parallelization.**

```markdown
## Files to Create/Modify

### Component: data_models
**Files:**
- `fisio/imports/new_scanner/models.py` (CREATE)
- `fisio/imports/new_scanner/types.py` (CREATE)

**Depends on:** (none)
**Parallelization:** independent
**Complexity:** low

---

### Component: handler
**Files:**
- `fisio/imports/new_scanner/handler.py` (CREATE)
- `fisio/imports/new_scanner/__init__.py` (CREATE)

**Depends on:** data_models
**Parallelization:** after data_models
**Complexity:** high

---

### Component: api_endpoint
**Files:**
- `fortress_api/endpoints/new_scanner.py` (CREATE)
- `fortress_api/endpoints/__init__.py` (MODIFY - add import)

**Depends on:** handler
**Parallelization:** after handler
**Complexity:** medium

---

### Component: tests
**Files:**
- `fisio/tests/unit/imports/test_new_scanner.py` (CREATE)
- `fisio/tests/integration/imports/test_new_scanner_integration.py` (CREATE)

**Depends on:** handler, api_endpoint
**Parallelization:** after handler, api_endpoint
**Complexity:** medium
```

### 6. Dependency Graph (Visual)

```markdown
## Dependency Graph

```
Level 0 (parallel):     [data_models]
                              │
Level 1:                [handler]
                              │
Level 2:                [api_endpoint]
                              │
Level 3:                [tests]
```

Parallel groups:
- Group A: data_models (no deps, runs first)
- Group B: handler (after A)
- Group C: api_endpoint (after B)
- Group D: tests (after B, C)
```

### 7. Implementation Phases

```markdown
## Implementation Phases

### Phase 1: Foundation
**Components:** data_models
**Tasks:**
1. Create type definitions
2. Create data model classes
3. Add validation logic

**Validation:** Lint check, type check

---

### Phase 2: Core Logic
**Components:** handler
**Tasks:**
1. Create scanner base
2. Implement fetch logic
3. Implement parse logic
4. Add BO creation
5. Add import tracking

**Validation:** Full review (mongo, import validators)

---

### Phase 3: API Integration
**Components:** api_endpoint
**Tasks:**
1. Create endpoint
2. Wire to handler
3. Add auth checks

**Validation:** Quick review

---

### Phase 4: Testing
**Components:** tests
**Tasks:**
1. Unit tests for handler
2. Integration tests for full flow

**Validation:** Test run + coverage check
```

### 8. Success Criteria

```markdown
## Success Criteria

### Must Pass
- [ ] All requirements implemented
- [ ] All tests pass
- [ ] No critical/high issues in final review
- [ ] python-code-quality clean
- [ ] Import tracking paired (insert + complete)
- [ ] All MongoDB ops have retry_run
- [ ] subID filtering on all businessObjects queries

### Nice to Have
- [ ] 80%+ test coverage
- [ ] All minor issues addressed
- [ ] Documentation updated
```

### 9. Known Gotchas

```markdown
## Known Gotchas

- This scanner's API returns paginated results - need to handle
- Scanner uses OAuth2 - reuse existing auth pattern from X
- Rate limiting: max 100 requests/minute
- Field mapping: scanner "assetId" → our "md.extId"
```

### 10. Skills to Load

```markdown
## Skills Required

For orchestrator to inject via --append-system-prompt:

- m32rimm-pr-patterns (flush, subID, retry_run)
- mongodb-aggregation-optimization (if aggregations)
- testing-standards (for test phase)
```

---

## Parallelization Parsing

The orchestrator parses the "Files to Create/Modify" section to build:

```python
{
  "components": [
    {
      "name": "data_models",
      "files": ["fisio/imports/.../models.py", "fisio/imports/.../types.py"],
      "depends_on": [],
      "complexity": "low",
      "level": 0
    },
    {
      "name": "handler",
      "files": ["fisio/imports/.../handler.py", "fisio/imports/.../__init__.py"],
      "depends_on": ["data_models"],
      "complexity": "high",
      "level": 1
    },
    ...
  ],
  "levels": {
    0: ["data_models"],
    1: ["handler"],
    2: ["api_endpoint"],
    3: ["tests"]
  },
  "parallel_groups": [
    {"level": 0, "components": ["data_models"]},
    {"level": 1, "components": ["handler"]},
    {"level": 2, "components": ["api_endpoint"]},
    {"level": 3, "components": ["tests"]}
  ]
}
```

---

## Example: Multi-Component Parallel

```markdown
## Files to Create/Modify

### Component: scanner_a_models
**Files:** `imports/scanner_a/models.py`
**Depends on:** (none)
**Parallelization:** independent

### Component: scanner_b_models
**Files:** `imports/scanner_b/models.py`
**Depends on:** (none)
**Parallelization:** independent

### Component: scanner_a_handler
**Files:** `imports/scanner_a/handler.py`
**Depends on:** scanner_a_models
**Parallelization:** after scanner_a_models

### Component: scanner_b_handler
**Files:** `imports/scanner_b/handler.py`
**Depends on:** scanner_b_models
**Parallelization:** after scanner_b_models

### Component: aggregator
**Files:** `imports/multi_scanner/aggregator.py`
**Depends on:** scanner_a_handler, scanner_b_handler
**Parallelization:** after scanner_a_handler, scanner_b_handler
```

**Parsed dependency graph:**
```
Level 0: [scanner_a_models] [scanner_b_models]  ← parallel
              │                    │
Level 1: [scanner_a_handler] [scanner_b_handler]  ← parallel
              │                    │
              └────────┬───────────┘
                       │
Level 2:         [aggregator]
```

---

## Validation Rules

The orchestrator validates SPEC.md before execution:

1. **All components have files** - No empty component
2. **Dependencies exist** - Can't depend on non-existent component
3. **No cycles** - Topological sort must succeed
4. **Levels are consistent** - Deps must be in lower level
5. **Requirements are checkable** - Each has clear pass/fail
6. **Scope is defined** - In/out/flag sections present
