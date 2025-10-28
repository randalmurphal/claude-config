---
name: test-driven-development
description: Test-Driven Development workflows including red-green-refactor cycle, test-first implementation, outside-in vs inside-out testing, TDD for debugging, and TDD for refactoring. Use when implementing new features, refactoring existing code, using tests to drive design, or debugging with failing tests.
allowed-tools:
  - Read
  - Bash
  - Grep
---

# Test-Driven Development (TDD)

**Purpose:** Drive development with tests to ensure correctness, enable confident refactoring, and create better designs.

**When to use:** Implementing new features, refactoring existing code, debugging complex issues, designing APIs, or when tests should drive implementation.

**Synergy with testing-standards:** This skill covers TDD *workflow* (red-green-refactor cycle, test-first process). Load `testing-standards` skill for test *structure* (1:1 file mapping, coverage targets, fixture patterns).

**For detailed examples and code patterns:** See reference.md

---

## Core Principles

1. **Red-Green-Refactor** - Write failing test, make it pass, improve code
2. **Test-first** - Write test before implementation (forces clear requirements)
3. **Small steps** - One test case at a time, one behavior at a time
4. **Tests drive design** - Good tests lead to better API designs
5. **Fail fast** - Tests should fail quickly and clearly when broken
6. **Refactor fearlessly** - Passing tests enable confident code improvements

---

## The Red-Green-Refactor Cycle

**Core TDD workflow - repeat for every behavior:**

```
┌──────────────────────────────────────────────┐
│  RED: Write failing test (proves it fails)  │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  GREEN: Write minimal code to pass          │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  REFACTOR: Improve code (tests still pass)  │
└──────────────┬───────────────────────────────┘
               │
               ▼ (repeat for next behavior)
```

### Phase 1: RED (Write Failing Test)

**Goal:** Prove test fails before implementation exists.

**Why RED phase matters:**
- Proves test actually tests something (not a false positive)
- Verifies test failure message is clear
- Confirms test setup works

**Common RED phase issues:**

| Issue | Symptom | Fix |
|-------|---------|-----|
| Test passes immediately | No failure message | Check if function already exists or test is trivial |
| Unclear error message | Hard to diagnose | Improve assertions, add context |
| Test won't run | Import/syntax errors | Fix test setup first |

### Phase 2: GREEN (Make Test Pass)

**Goal:** Write simplest code to make test pass (not perfect code).

**GREEN phase rules:**
- Write simplest code that makes test pass
- Don't add features not tested yet
- Hardcoding is OK if it passes test
- Don't refactor yet (GREEN then REFACTOR, not at once)

**For detailed progression examples:** See reference.md

### Phase 3: REFACTOR (Improve Code)

**Goal:** Improve code quality while keeping tests passing.

**REFACTOR targets:**
- Extract helper functions (reduce complexity)
- Improve naming (clarity)
- Remove duplication (DRY principle)
- Add type hints (safety)
- Optimize performance (if needed)
- Improve error messages (usability)

**REFACTOR safety rules:**
- Run tests after each refactor
- Refactor in small steps
- If tests fail, undo and try smaller step
- Don't add new behavior (that needs new test first)

---

## Test-First Implementation Workflow

**Complete workflow for implementing new feature:**

### Step 1: Clarify Requirements

Before writing any code, understand WHAT and WHY.

**Requirements checklist:**
- [ ] What is the expected input?
- [ ] What is the expected output?
- [ ] What are the error cases?
- [ ] What are the edge cases?
- [ ] What are the performance requirements?

### Steps 2-7: RED → GREEN → REFACTOR Loop

| Step | Action | Expected Result |
|------|--------|----------------|
| 2. Write test | Test for simplest case (happy path) | - |
| 3. Run test | Execute test | RED (should fail) |
| 4. Write code | Minimal implementation | - |
| 5. Run test | Execute test | GREEN (should pass) |
| 6. Add test | Test for next case | - |
| 7. Repeat | Loop until complete | All behaviors tested |

**Test progression order:**
1. Happy path (valid input → expected output)
2. Error cases (invalid input → proper exceptions)
3. Edge cases (empty, null, max values, boundary conditions)
4. Security cases (injection, authentication bypass)
5. Performance cases (if requirements exist)

**For detailed step-by-step examples:** See reference.md

---

## Outside-In vs Inside-Out TDD

**Two approaches to TDD - choose based on context:**

### Comparison Table

| Aspect | Outside-In | Inside-Out |
|--------|-----------|------------|
| **Start** | User-facing behavior | Core utilities |
| **Direction** | Top-down (API → utilities) | Bottom-up (utilities → API) |
| **Mocking** | More (internal layers not built) | Less (components already built) |
| **API Design** | Early (forced by acceptance tests) | Late (emerges from components) |
| **Risk** | Implementation may not fit API | API may not match user needs |
| **Best for** | New features, user stories | Libraries, algorithms, refactoring |

### Outside-In (Top-Down, Acceptance Test First)

**Start with user-facing behavior, work inward to implementation.**

```
User Interface / API
      ↓
Service Layer
      ↓
Data Layer
```

**When to use:**
- Building new features with clear user stories
- API-first development
- When contract/interface more important than implementation
- Agile/BDD environments

**Characteristics:**
- Tests read like user stories
- Forces API design up-front
- May require mocking internal layers initially
- Better for integration testing

### Inside-Out (Bottom-Up, Unit Test First)

**Start with lowest-level components, build up to features.**

```
Core Utilities
      ↓
Service Layer
      ↓
User Interface / API
```

**When to use:**
- Building reusable libraries
- Complex algorithms (need solid foundation)
- When implementation details are critical
- Refactoring existing code

**Characteristics:**
- Build solid foundation first
- Less mocking needed (real implementations exist)
- May delay discovering API design issues
- Better for unit testing

**Hybrid approach (common):** Outside-in for features, inside-out for complex algorithms within features.

**For detailed code examples:** See reference.md

---

## TDD for Refactoring

**Use TDD to safely refactor existing code:**

### Workflow: Test Behavior, Then Refactor

```
┌─────────────────────────────────────┐
│ 1. Write tests for current behavior │
│    (characterization tests)         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. Verify tests pass                │
│    (tests capture current behavior) │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Refactor code                    │
│    (improve structure)              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. Verify tests still pass          │
│    (behavior unchanged)             │
└─────────────────────────────────────┘
```

**Key points:**
- Write characterization tests first (capture current behavior, even if buggy)
- Tests prove behavior unchanged after refactor
- Refactor in small steps, run tests frequently
- Extract focused helpers, improve naming, reduce nesting

**For refactoring code examples:** See reference.md

---

## TDD for Debugging

**Use failing tests to drive bug fixes:**

### Workflow: Reproduce, Test, Fix

```
┌────────────────────────────────────┐
│ 1. Reproduce bug with failing test│
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│ 2. Verify test fails (RED)        │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│ 3. Fix bug (GREEN)                │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│ 4. Verify test passes             │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│ 5. Add regression prevention tests│
└────────────────────────────────────┘
```

**TDD debugging benefits:**
- Bug reproduced reliably (test proves it)
- Bug stays fixed (test prevents regression)
- Root cause identified (test clarifies issue)
- Documentation (test shows expected behavior)

**For debugging examples:** See reference.md and debugging-strategies skill

---

## When TDD Is Appropriate (and When It's Not)

### Decision Framework

**Use TDD when:**
- Requirements are clear
- Behavior is well-defined
- Tests can run quickly (<1 second)
- Failure modes are known
- Code will be maintained long-term

**Skip TDD when:**
- Rapid prototyping (throw-away code)
- Requirements highly uncertain
- Visual/interactive design phase
- One-off scripts (not maintained)
- Learning phase (don't know domain yet)

### ✅ TDD Works Well For:

| Scenario | Why TDD Helps |
|----------|---------------|
| **Business logic** | Requirements clear, behavior testable |
| **Algorithms** | Input/output well-defined, edge cases known |
| **API design** | Tests drive clean interface design |
| **Bug fixes** | Reproduce with test, fix, prevent regression |
| **Refactoring** | Tests ensure behavior unchanged |
| **Complex validation** | Edge cases numerous, tests catch omissions |

### ❌ TDD Less Effective For:

| Scenario | Why TDD Struggles | Alternative |
|----------|-------------------|-------------|
| **UI/UX design** | Visual design requires iteration | Prototype first, test after |
| **Exploratory coding** | Requirements unclear | Spike/prototype, then TDD |
| **External API integration** | Behavior outside your control | Integration tests, not TDD |
| **Performance tuning** | Benchmarks, not correctness | Profile first, optimize, benchmark |
| **Learning new tech** | Don't know what to test yet | Tutorial first, TDD after understanding |

**Hybrid approach (common):**
- Prototype to understand requirements
- Once requirements clear, switch to TDD
- Keep prototype tests as integration tests

---

## Common TDD Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Writing tests after implementation** | Tests confirm implementation, not requirements | Write test first (forces thinking about behavior) |
| **Testing implementation details** | Refactoring breaks tests even when behavior unchanged | Test public behavior, not internal implementation |
| **Large steps (skipping RED)** | Lose benefits of small feedback cycles | One test at a time - RED, GREEN, REFACTOR, repeat |
| **Not running tests frequently** | Hard to identify which change broke what | Run tests after every change |
| **Over-refactoring in GREEN phase** | Premature optimization, scope creep | Write minimal code in GREEN, refactor in REFACTOR phase |

**For detailed anti-pattern examples:** See reference.md

---

## Quick Reference Workflow

### Standard TDD Cycle

```bash
# 1. RED - Write failing test
vim tests/test_feature.py  # Add new test
pytest tests/test_feature.py::test_new_behavior -v  # Should FAIL

# 2. GREEN - Make test pass
vim src/feature.py  # Write minimal code
pytest tests/test_feature.py::test_new_behavior -v  # Should PASS

# 3. REFACTOR - Improve code
vim src/feature.py  # Extract functions, improve names
pytest tests/test_feature.py -v  # All tests should PASS

# 4. Repeat for next behavior
```

### TDD Commands

```bash
# Run single test (fast feedback)
pytest tests/test_auth.py::test_authenticate -v

# Run all tests (verify nothing broken)
pytest tests/ -v

# Watch mode (rerun on changes)
pytest-watch

# Run tests on commit (git hook)
git commit  # Runs pytest in pre-commit hook
```

### TDD Checklist

**Before writing code:**
- [ ] Requirements clear (input, output, errors, edge cases)
- [ ] Test file exists (follow 1:1 mapping from testing-standards)
- [ ] Test framework configured (pytest, fixtures ready)

**RED phase:**
- [ ] Test written for single behavior
- [ ] Test fails with clear message
- [ ] Failure is expected failure (not syntax error)

**GREEN phase:**
- [ ] Minimal code written (simplest thing that works)
- [ ] Test passes
- [ ] No extra features added (only what test requires)

**REFACTOR phase:**
- [ ] Code improved (extract functions, better names)
- [ ] All tests still pass
- [ ] No behavior changes (only structure)

---

## Integration with testing-standards Skill

**This skill (test-driven-development):**
- RED-GREEN-REFACTOR workflow
- Test-first implementation process
- Outside-in vs inside-out approaches
- TDD for debugging and refactoring

**Load testing-standards skill for:**
- Test file structure (1:1 mapping)
- Coverage requirements (95%+ unit, 85%+ integration)
- Test organization patterns (parametrized, separate methods)
- Fixture patterns and best practices
- Mocking strategies (what to mock, what not to mock)

**Typical workflow:**
```
1. Load test-driven-development skill (this one)
   → Understand TDD cycle and workflow

2. Load testing-standards skill
   → Know where to put tests, how to organize them

3. Follow TDD cycle:
   RED → GREEN → REFACTOR (from this skill)

4. Structure tests correctly:
   1:1 file mapping, fixtures, coverage (from testing-standards)
```

---

## Remember

**TDD Success Formula:**
1. **Write test first** - Forces clear thinking about requirements
2. **Small steps** - One test, one behavior, one cycle
3. **RED before GREEN** - Verify test actually tests something
4. **Simplest code in GREEN** - Resist urge to over-engineer
5. **Refactor fearlessly** - Passing tests enable confident improvements
6. **Run tests frequently** - Fast feedback catches issues immediately

**Bottom line:** TDD is a design discipline. Tests drive better code by forcing clear requirements, small iterations, and continuous validation.

---

**For detailed examples, code patterns, and language-specific TDD techniques:** See reference.md
