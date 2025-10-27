---
name: Testing Standards
description: Write tests following 3-layer pyramid (unit 95%, integration 85%, E2E critical paths) with 1:1 file mapping for unit tests. Covers test organization, coverage requirements, fixtures, and best practices. Use when writing tests, checking coverage, or validating test structure.
allowed-tools:
  - Read
  - Bash
  - Grep
---

# Testing Standards Skill

**Purpose:** Guide test writing with clear structure, coverage targets, and quality standards.

**When to use:** Writing tests, checking coverage, validating test organization, debugging test failures.

**For detailed examples and language-specific patterns:** See [reference.md](./reference.md)

---

## Core Principles (Remember These)

1. **Tests prove correctness** - Not just coverage numbers
2. **Write tests that would catch real bugs** - No useless assertions
3. **Test behavior, not implementation** - Don't test private methods
4. **Keep tests maintainable** - DRY applies to tests too
5. **Fast feedback** - Unit tests run in <5s, integration <30s

---

## 3-Layer Testing Pyramid

```
        /\
       /E2E\      <- Few tests, full workflows (critical paths)
      /------\
     /  INT   \   <- Moderate tests, component integration
    /----------\
   /    UNIT    \ <- Many tests, isolated functions/classes
  /--------------\
```

### Layer 1: Unit Tests (95% coverage)

**What:** Test individual functions/classes in isolation
**File Organization:** 1:1 mapping - one test file per production file

**Example mapping:**
```
src/auth/service.py       → tests/unit/test_auth_service.py
src/auth/models.py        → tests/unit/test_auth_models.py
src/api/endpoints.py      → tests/unit/test_api_endpoints.py
```

**Every public function/method gets tests for:**
- Happy path (expected input → expected output)
- Error cases (invalid input → proper exceptions)
- Edge cases (empty, null, max values, boundary conditions)

**Characteristics:**
- Fast (<100ms per test)
- Isolated (mock all external dependencies)
- Deterministic (same input = same output)
- Don't hit database/network/filesystem

**For full example:** See reference.md Layer 1 section

### Layer 2: Integration Tests (85% coverage)

**What:** Test components working together (database, cache, etc.)
**File Organization:** 2-4 test files per module (not per file)

**IMPORTANT:** Add to existing integration files rather than creating new ones.

**Example mapping:**
```
Auth module          → tests/integration/test_auth_flow.py
                       tests/integration/test_auth_sessions.py

API module           → tests/integration/test_api_endpoints.py
                       tests/integration/test_api_middleware.py
```

**Characteristics:**
- Use real dependencies (test database, cache)
- Test actual interactions between components
- Verify data persistence, transactions
- Don't test external APIs (mock those)

**For full example:** See reference.md Layer 2 section

### Layer 3: E2E Tests (Critical paths)

**What:** Test complete user workflows through API
**File Organization:** 1-3 files total for entire project

**Example:**
```
tests/e2e/test_user_workflows.py
tests/e2e/test_admin_workflows.py
```

**Characteristics:**
- HTTP requests to real API
- Full database, cache, all services
- Test realistic user scenarios
- Don't test every edge case (that's what unit tests are for)

**For full example:** See reference.md Layer 3 section

---

## Coverage Requirements

**Targets:**
- Unit tests: **≥95%** line coverage, **100%** function coverage
- Integration tests: **≥85%** of integration points
- E2E tests: **Critical paths covered** (not measured by coverage %)

**Commands:**
```bash
# Check coverage (unit + integration)
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=95

# Generate HTML report
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html

# Check function coverage
pytest tests/ --cov=src --cov-branch --cov-report=term-missing
```

**What to test:**
- ✅ Business logic
- ✅ Error handling
- ✅ Edge cases (empty, null, max values)
- ✅ Security-critical code (auth, permissions)
- ✅ Data validation

**What NOT to test:**
- ❌ Framework code (don't test FastAPI/Django itself)
- ❌ Trivial getters/setters
- ❌ Generated code
- ❌ Third-party libraries

---

## File Organization: 1:1 Mapping (Critical)

**Rule:** One test file per production file (unit tests only)

**Pattern:** `test_<module_name>.py`

**Directory structure:**
```
tests/
├── unit/                    # 1:1 mapping to production files
│   ├── test_auth_service.py
│   ├── test_auth_models.py
│   ├── test_session_service.py
│   └── test_api_endpoints.py
├── integration/             # 2-4 files per module
│   ├── test_auth_flow.py
│   ├── test_payment_processing.py
│   └── test_api_middleware.py
├── e2e/                     # 1-3 files total
│   ├── test_user_workflows.py
│   └── test_admin_workflows.py
├── conftest.py              # Shared fixtures
└── fixtures/                # Test data files
    ├── users.json
    └── sample_requests.json
```

**Production to test mapping:**
```
Production:                     Tests:
src/auth/service.py        →   tests/unit/test_auth_service.py
src/auth/models.py         →   tests/unit/test_auth_models.py
src/api/endpoints.py       →   tests/unit/test_api_endpoints.py

Auth module                →   tests/integration/test_auth_flow.py
API module                 →   tests/integration/test_api_endpoints.py

Complete workflows         →   tests/e2e/test_user_workflows.py
```

---

## Test Organization Patterns

**Choose based on complexity:**

1. **Simple Functions:** Single test function covering all cases (good when signature changes often)
2. **Complex Functions:** Parametrized tests (recommended - clear failure reporting)
3. **Critical Functions:** Separate test methods (security-critical code, complex setup)

**For detailed examples:** See reference.md Test Organization Patterns section

---

## Fixtures and Test Data

**Use conftest.py for shared fixtures** across test files

**Fixture scopes:**
- `scope="session"` - Created once for entire test run (databases, connections)
- `scope="module"` - Created once per test file
- `scope="function"` - Created for each test (default)

**Use fixtures/ directory** for complex test data (JSON, CSV, etc.)

**For detailed examples:** See reference.md Fixtures and Test Data section

---

## Best Practices

### 1. Arrange-Act-Assert Pattern
Structure tests clearly: Set up → Execute → Verify

### 2. Descriptive Test Names
Use clear names like `test_authenticate_fails_with_invalid_password` not `test_auth_1`

### 3. Test Error Cases
Always test happy path + error cases + edge cases

### 4. Don't Test Implementation Details
Test public behavior, not private methods

### 5. Mock Properly (Critical)

**Unit tests:** Mock everything external to the function being tested (even other internal functions)
**Integration tests:** Use real dependencies (test database, cache)
**E2E tests:** No mocks, test complete workflows

**What to mock in unit tests:**
- Database/repository calls
- External API calls
- File I/O operations
- Cache operations
- Other internal functions called by the function under test
- Password hashers, crypto operations
- Time/date functions (if testing time-sensitive logic)

**What NOT to mock:**
- The function you're testing
- Simple data transformations
- Pure functions with no side effects (unless part of external dependency)

**For detailed examples and code samples:** See reference.md Best Practices section

---

## Quick Reference Commands

**Run all tests:**
```bash
pytest tests/ -v
```

**Run with coverage:**
```bash
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=95
```

**Run specific layer:**
```bash
pytest tests/unit/ -v          # Unit only
pytest tests/integration/ -v   # Integration only
pytest tests/e2e/ -v           # E2E only
```

**Run specific test:**
```bash
pytest tests/unit/test_auth_service.py::TestAuthenticate::test_success_valid_credentials -v
```

**Run failed tests only:**
```bash
pytest --lf  # Last failed
pytest --ff  # Failed first, then others
```

**Run in parallel (faster):**
```bash
pytest tests/ -n auto  # Requires pytest-xdist
```

**Watch mode (re-run on file changes):**
```bash
pytest-watch  # Requires pytest-watch
```

---

## Testing Philosophy

**Tests should:**
- ✅ Catch bugs before production
- ✅ Document expected behavior
- ✅ Enable confident refactoring
- ✅ Run fast (unit tests < 5s total)
- ✅ Be deterministic (no flaky tests)

**Tests should NOT:**
- ❌ Test the framework
- ❌ Test third-party libraries
- ❌ Be brittle (break on every refactor)
- ❌ Have side effects (pollute database)
- ❌ Depend on external services

---

## Common Patterns by Language

**Python (pytest):** Fixtures in conftest.py, parametrize decorator, pytest.raises
**JavaScript/TypeScript (Jest/Vitest):** describe/it blocks, expect assertions, mocking with vi
**Go (testing package):** Table-driven tests, t.Run for subtests, t.Errorf for failures

**For detailed syntax and examples:** See reference.md Common Patterns by Language section

---

## Checklist for Adding Tests

**Before writing tests:**
- [ ] Identify all public functions/methods to test
- [ ] Determine test layer (unit/integration/e2e)
- [ ] Check if test file exists (1:1 mapping for unit tests)

**While writing tests:**
- [ ] Test happy path
- [ ] Test error cases
- [ ] Test edge cases (empty, null, max values)
- [ ] Use Arrange-Act-Assert pattern
- [ ] Mock external dependencies (unit tests)
- [ ] Use descriptive test names

**After writing tests:**
- [ ] Run tests: `pytest tests/ -v`
- [ ] Check coverage: `pytest tests/ --cov=src --cov-report=term-missing`
- [ ] Verify ≥95% coverage for unit tests
- [ ] Verify all tests pass
- [ ] Verify tests are fast (<5s for unit tests)

---

**Bottom line:** Write tests that would catch real bugs. Coverage is a metric, not a goal.
