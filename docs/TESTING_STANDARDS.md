# Testing Standards

**Purpose:** Define testing approach, coverage requirements, and file organization for all projects.

---

## Core Principles

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

### Layer 1: Unit Tests

**What:** Test individual functions/classes in isolation
**When:** Written during implementation phase
**Coverage:** 95% of production code
**File Organization:** 1 test file per production file

```
src/auth/service.py       → tests/unit/test_auth_service.py
src/auth/models.py        → tests/unit/test_auth_models.py
src/api/endpoints.py      → tests/unit/test_api_endpoints.py
```

**Characteristics:**
- ✅ Fast (<100ms per test)
- ✅ Isolated (mock all external dependencies)
- ✅ Deterministic (same input = same output)
- ❌ Don't hit database/network/filesystem

**Example:**
```python
# tests/unit/test_auth_service.py

import pytest
from unittest.mock import Mock, AsyncMock
from src.auth.service import AuthService
from src.auth.models import User

@pytest.fixture
def mock_user_repo():
    """Mock user repository."""
    repo = Mock()
    repo.find_by_email = AsyncMock()
    repo.update = AsyncMock()
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

    async def test_failure_user_not_found(self, auth_service, mock_user_repo):
        """Should raise AuthError when user doesn't exist."""
        # Arrange
        mock_user_repo.find_by_email.return_value = None

        # Act & Assert
        with pytest.raises(AuthError, match="Invalid credentials"):
            await auth_service.authenticate("test@example.com", "password123")
```

### Layer 2: Integration Tests

**What:** Test components working together (database, cache, etc.)
**When:** Written after implementation batches complete
**Coverage:** 85% of critical integration points
**File Organization:** 2-4 test files per module/major component

```
Auth module          → tests/integration/test_auth_flow.py
                       tests/integration/test_auth_sessions.py

API module           → tests/integration/test_api_endpoints.py
                       tests/integration/test_api_middleware.py

Payment module       → tests/integration/test_payment_processing.py
```

**Characteristics:**
- ✅ Use real dependencies (test database, cache)
- ✅ Test actual interactions between components
- ✅ Verify data persistence, transactions
- ❌ Don't test external APIs (mock those)

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
def user_repo(db):
    """Real user repository with test database."""
    return UserRepository(db)

@pytest.fixture
def auth_service(user_repo):
    """Real auth service with real repository."""
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

    async def test_password_reset_flow(self, auth_service, user_repo, db):
        """Should reset password and invalidate old sessions."""
        # Create user
        user = await auth_service.register("test@example.com", "oldpassword")

        # Login (creates session)
        old_token = await auth_service.authenticate("test@example.com", "oldpassword")

        # Reset password
        await auth_service.reset_password(user.id, "newpassword")

        # Old token should be invalid
        with pytest.raises(AuthError, match="Invalid token"):
            await auth_service.validate_token(old_token.access_token)

        # New password should work
        new_token = await auth_service.authenticate("test@example.com", "newpassword")
        assert new_token.access_token is not None
```

### Layer 3: E2E Tests

**What:** Test complete user workflows through API
**When:** Written at major milestones
**Coverage:** Critical paths (happy path + major error cases)
**File Organization:** 1-3 files total for entire project

```
tests/e2e/test_user_workflows.py
tests/e2e/test_admin_workflows.py
```

**Characteristics:**
- ✅ HTTP requests to real API
- ✅ Full database, cache, all services
- ✅ Test realistic user scenarios
- ❌ Don't test every edge case (that's what unit tests are for)

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

        # Verify email (simulate clicking link)
        verify_token = response.json()["verify_token"]
        response = await client.post(f"/api/auth/verify/{verify_token}")
        assert response.status_code == 200

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
- Unit tests: **≥95%** of production code
- Integration tests: **≥85%** of integration points
- E2E tests: **Critical paths covered** (not measured by coverage %)

**How to measure:**
```bash
# Unit + Integration combined
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=95

# See what's missing
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html
```

**What to test:**
- ✅ Business logic
- ✅ Error handling
- ✅ Edge cases (empty, null, max values)
- ✅ Security-critical code (auth, permissions)
- ✅ Data validation

**What NOT to test:**
- ❌ Framework code (don't test FastAPI itself)
- ❌ Trivial getters/setters
- ❌ Generated code
- ❌ Third-party libraries

---

## File Naming Conventions

**Pattern:** `test_<module_name>.py`

```
Production:                     Tests:
src/auth/service.py        →   tests/unit/test_auth_service.py
src/auth/models.py         →   tests/unit/test_auth_models.py
src/api/endpoints.py       →   tests/unit/test_api_endpoints.py

Auth module                →   tests/integration/test_auth_flow.py
API module                 →   tests/integration/test_api_endpoints.py

Complete workflows         →   tests/e2e/test_user_workflows.py
```

**Directory structure:**
```
tests/
├── unit/
│   ├── test_auth_service.py
│   ├── test_auth_models.py
│   ├── test_session_service.py
│   └── test_api_endpoints.py
├── integration/
│   ├── test_auth_flow.py
│   ├── test_payment_processing.py
│   └── test_api_middleware.py
├── e2e/
│   ├── test_user_workflows.py
│   └── test_admin_workflows.py
├── conftest.py              # Shared fixtures
└── fixtures/                # Test data files
    ├── users.json
    └── sample_requests.json
```

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

### 2. One Assertion Per Test (Usually)

```python
# GOOD - focused test
async def test_returns_token_on_success(self, auth_service):
    token = await auth_service.authenticate("test@example.com", "password")
    assert token.access_token is not None

async def test_token_type_is_bearer(self, auth_service):
    token = await auth_service.authenticate("test@example.com", "password")
    assert token.token_type == "bearer"

# ACCEPTABLE - related assertions
async def test_returns_valid_token(self, auth_service):
    token = await auth_service.authenticate("test@example.com", "password")
    assert token.access_token is not None
    assert token.token_type == "bearer"
    assert token.expires_in > 0
```

### 3. Descriptive Test Names

```python
# GOOD - clear what's being tested
async def test_authenticate_success_with_valid_credentials()
async def test_authenticate_fails_with_invalid_password()
async def test_authenticate_fails_when_user_not_found()

# BAD - unclear
async def test_auth_1()
async def test_login()
async def test_failure()
```

### 4. Test Error Cases

```python
class TestAuthenticate:
    async def test_success_valid_credentials(self):
        """Happy path."""
        ...

    async def test_failure_invalid_password(self):
        """Test error handling."""
        with pytest.raises(AuthError, match="Invalid credentials"):
            await auth_service.authenticate("test@example.com", "wrong")

    async def test_failure_user_not_found(self):
        """Test missing user."""
        with pytest.raises(AuthError):
            await auth_service.authenticate("notfound@example.com", "password")

    async def test_failure_empty_email(self):
        """Test validation."""
        with pytest.raises(ValidationError, match="Email required"):
            await auth_service.authenticate("", "password")
```

### 5. Don't Test Implementation Details

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

## Quick Reference

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
```

**Run in parallel (faster):**
```bash
pytest tests/ -n auto  # Requires pytest-xdist
```

---

**Bottom line:** Write tests that would catch real bugs. Coverage is a metric, not a goal.
