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

**Example:**
```python
# tests/unit/test_auth_service.py

import pytest
from unittest.mock import Mock, AsyncMock
from src.auth.service import AuthService

@pytest.fixture
def mock_user_repo():
    """Mock user repository."""
    repo = Mock()
    repo.find_by_email = AsyncMock()
    return repo

@pytest.fixture
def auth_service(mock_user_repo):
    """Auth service with mocked dependencies."""
    return AuthService(user_repo=mock_user_repo)

class TestAuthenticate:
    """Test AuthService.authenticate()"""

    async def test_success_valid_credentials(self, auth_service, mock_user_repo):
        """Should return token when credentials valid."""
        # Arrange
        user = User(id="123", email="test@example.com", password_hash="$2b$...")
        mock_user_repo.find_by_email.return_value = user

        # Act
        token = await auth_service.authenticate("test@example.com", "password123")

        # Assert
        assert token.access_token is not None
        assert token.token_type == "bearer"
        mock_user_repo.find_by_email.assert_called_once_with("test@example.com")

    async def test_failure_invalid_password(self, auth_service, mock_user_repo):
        """Should raise AuthError when password invalid."""
        # Arrange
        user = User(id="123", email="test@example.com", password_hash="$2b$...")
        mock_user_repo.find_by_email.return_value = user

        # Act & Assert
        with pytest.raises(AuthError, match="Invalid credentials"):
            await auth_service.authenticate("test@example.com", "wrongpassword")
```

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

**Example:**
```python
# tests/integration/test_auth_flow.py

import pytest
from src.auth.service import AuthService
from src.auth.repository import UserRepository
from src.database import get_test_db

@pytest.fixture
async def db():
    """Test database with migrations applied."""
    db = await get_test_db()
    await db.execute("DELETE FROM users")  # Clean slate
    yield db
    await db.close()

@pytest.fixture
def auth_service(db):
    """Real auth service with real repository."""
    user_repo = UserRepository(db)
    return AuthService(user_repo=user_repo)

class TestAuthFlow:
    """Test complete authentication flow."""

    async def test_register_then_login(self, auth_service, db):
        """Should register user and then login successfully."""
        # Register
        user = await auth_service.register(
            email="test@example.com",
            password="password123"
        )
        assert user.id is not None

        # Verify user in database
        result = await db.fetch_one("SELECT * FROM users WHERE email = ?", "test@example.com")
        assert result is not None

        # Login
        token = await auth_service.authenticate(
            email="test@example.com",
            password="password123"
        )
        assert token.access_token is not None
```

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

**Example:**
```python
# tests/e2e/test_user_workflows.py

import pytest
from httpx import AsyncClient

@pytest.fixture
async def client():
    """HTTP client for API."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client

class TestUserRegistrationFlow:
    """Test complete user registration and first login."""

    async def test_happy_path(self, client):
        """User registers, verifies email, and logs in."""
        # Register
        response = await client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
        user_id = response.json()["user_id"]

        # Login
        response = await client.post("/api/auth/login", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 200
        access_token = response.json()["access_token"]

        # Access protected endpoint
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "newuser@example.com"
```

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

### 1. Simple Functions: Single Test Function

```python
async def test_authenticate(self, auth_service):
    """Test authenticate with all cases."""
    # Happy path
    token = await auth_service.authenticate("test@example.com", "password")
    assert token.access_token is not None

    # Error cases
    with pytest.raises(AuthError, match="Invalid credentials"):
        await auth_service.authenticate("test@example.com", "wrong")

    with pytest.raises(AuthError):
        await auth_service.authenticate("notfound@example.com", "password")
```

**When:** Simple functions, independent cases, signature changes often
**Pros:** One place to update when function signature changes
**Cons:** Less clear which case failed

### 2. Complex Functions: Parametrized Tests (Recommended)

```python
@pytest.mark.parametrize("email,password,expected_error", [
    ("test@example.com", "password", None),  # Happy path
    ("test@example.com", "wrong", "Invalid credentials"),
    ("notfound@example.com", "password", "Invalid credentials"),
    ("", "password", "Email required"),
])
async def test_authenticate(self, auth_service, email, password, expected_error):
    if expected_error:
        with pytest.raises((AuthError, ValidationError), match=expected_error):
            await auth_service.authenticate(email, password)
    else:
        token = await auth_service.authenticate(email, password)
        assert token.access_token is not None
```

**When:** Many cases, need clear failure reporting
**Pros:** Single definition + individual case isolation + clear test names
**Cons:** Slightly more complex syntax

### 3. Critical Functions: Separate Test Methods

```python
class TestAuthenticate:
    async def test_success_valid_credentials(self, auth_service):
        token = await auth_service.authenticate("test@example.com", "password")
        assert token.access_token is not None

    async def test_failure_invalid_password(self, auth_service):
        with pytest.raises(AuthError, match="Invalid credentials"):
            await auth_service.authenticate("test@example.com", "wrong")
```

**When:** Security-critical code, complex setup per case
**Pros:** Maximum clarity, can skip/run individual cases easily
**Cons:** More maintenance when signature changes

---

## Fixtures and Test Data

**Use conftest.py for shared fixtures:**

```python
# tests/conftest.py

import pytest
from src.database import get_test_db

@pytest.fixture(scope="session")
async def db():
    """Test database (created once per test session)."""
    db = await get_test_db()
    yield db
    await db.close()

@pytest.fixture
async def clean_db(db):
    """Clean database before each test."""
    await db.execute("DELETE FROM users")
    await db.execute("DELETE FROM sessions")
    yield db

@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    }
```

**Fixture scopes:**
- `scope="session"` - Created once for entire test run (databases, connections)
- `scope="module"` - Created once per test file
- `scope="function"` - Created for each test (default)

**Use fixtures/ for complex test data:**

```python
# tests/unit/test_auth_service.py

import json
from pathlib import Path

@pytest.fixture
def user_data():
    """Load user test data from file."""
    path = Path(__file__).parent.parent / "fixtures" / "users.json"
    with open(path) as f:
        return json.load(f)
```

---

## Best Practices

### 1. Arrange-Act-Assert Pattern

```python
async def test_authenticate_success(self, auth_service, mock_user_repo):
    # ARRANGE: Set up test data and mocks
    user = User(id="123", email="test@example.com")
    mock_user_repo.find_by_email.return_value = user

    # ACT: Call the method under test
    token = await auth_service.authenticate("test@example.com", "password123")

    # ASSERT: Verify behavior
    assert token.access_token is not None
    mock_user_repo.find_by_email.assert_called_once()
```

### 2. Descriptive Test Names

```python
# GOOD - clear what's being tested
async def test_authenticate_success_with_valid_credentials()
async def test_authenticate_fails_with_invalid_password()
async def test_authenticate()  # If covers all cases in one function

# BAD - unclear
async def test_auth_1()
async def test_login()
async def test_failure()
```

### 3. Test Error Cases (Always Test Failure Paths)

```python
# Test happy path + all error cases
async def test_authenticate(self):
    # Happy path
    token = await auth_service.authenticate("test@example.com", "password")
    assert token.access_token is not None

    # Error cases
    with pytest.raises(AuthError, match="Invalid credentials"):
        await auth_service.authenticate("test@example.com", "wrong")

    with pytest.raises(AuthError):
        await auth_service.authenticate("notfound@example.com", "password")

    with pytest.raises(ValidationError, match="Email required"):
        await auth_service.authenticate("", "password")
```

### 4. Don't Test Implementation Details

```python
# BAD - testing private method
def test_hash_password():
    service = AuthService()
    hashed = service._hash_password("password")  # Private method!
    assert hashed != "password"

# GOOD - test public behavior
async def test_authenticate_uses_secure_password_hashing():
    # Register user
    user = await auth_service.register("test@example.com", "password123")

    # Password should be hashed in database
    db_user = await user_repo.find_by_id(user.id)
    assert db_user.password_hash != "password123"
    assert db_user.password_hash.startswith("$2b$")  # bcrypt
```

### 5. Mock Properly

```python
# GOOD - mock external dependencies
@pytest.fixture
def mock_external_api():
    with patch('src.services.external_api.ExternalAPI') as mock:
        mock.fetch_data.return_value = {"status": "ok"}
        yield mock

# BAD - mocking internal logic
@pytest.fixture
def mock_auth_logic():
    with patch('src.auth.service.AuthService._validate_password') as mock:
        # Don't mock internal logic - test the real thing!
        yield mock
```

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

### Python (pytest)

```python
# conftest.py
import pytest

@pytest.fixture
def sample_data():
    return {"key": "value"}

# test_module.py
def test_function(sample_data):
    assert sample_data["key"] == "value"
```

### JavaScript/TypeScript (Jest/Vitest)

```javascript
// test_module.test.js
import { describe, it, expect, beforeEach } from 'vitest';
import { authenticate } from './auth';

describe('authenticate', () => {
  it('should return token for valid credentials', async () => {
    const token = await authenticate('test@example.com', 'password');
    expect(token.accessToken).toBeDefined();
  });

  it('should throw error for invalid credentials', async () => {
    await expect(authenticate('test@example.com', 'wrong'))
      .rejects.toThrow('Invalid credentials');
  });
});
```

### Go (testing package)

```go
// auth_test.go
package auth

import (
    "testing"
)

func TestAuthenticate(t *testing.T) {
    tests := []struct {
        name      string
        email     string
        password  string
        expectErr bool
    }{
        {"valid credentials", "test@example.com", "password", false},
        {"invalid password", "test@example.com", "wrong", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := Authenticate(tt.email, tt.password)
            if (err != nil) != tt.expectErr {
                t.Errorf("expected error: %v, got: %v", tt.expectErr, err)
            }
        })
    }
}
```

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
