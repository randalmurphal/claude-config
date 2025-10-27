# Testing Standards Reference Guide

**Companion to SKILL.md** - Comprehensive examples, detailed patterns, and language-specific implementations.

For quick reference and core principles, see SKILL.md. This document provides the detailed examples and advanced patterns.

---

## Table of Contents

1. [Detailed Layer Examples](#detailed-layer-examples)
2. [Test Organization Patterns](#test-organization-patterns)
3. [Fixtures and Test Data](#fixtures-and-test-data)
4. [Best Practices (Detailed)](#best-practices-detailed)
5. [Common Patterns by Language](#common-patterns-by-language)

---

## Detailed Layer Examples

### Layer 1: Unit Tests - Full Example

**File:** `tests/unit/test_auth_service.py`

```python
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

    async def test_failure_user_not_found(self, auth_service, mock_user_repo):
        """Should raise AuthError when user not found."""
        # Arrange
        mock_user_repo.find_by_email.return_value = None

        # Act & Assert
        with pytest.raises(AuthError, match="Invalid credentials"):
            await auth_service.authenticate("notfound@example.com", "password123")

    async def test_failure_empty_email(self, auth_service):
        """Should raise ValidationError when email empty."""
        with pytest.raises(ValidationError, match="Email required"):
            await auth_service.authenticate("", "password123")

    async def test_failure_empty_password(self, auth_service):
        """Should raise ValidationError when password empty."""
        with pytest.raises(ValidationError, match="Password required"):
            await auth_service.authenticate("test@example.com", "")
```

**Key characteristics:**
- Fast (<100ms per test)
- Isolated (mock all external dependencies)
- Deterministic (same input = same output)
- Don't hit database/network/filesystem

---

### Layer 2: Integration Tests - Full Example

**File:** `tests/integration/test_auth_flow.py`

```python
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

    async def test_register_duplicate_email(self, auth_service):
        """Should fail when registering duplicate email."""
        # First registration
        await auth_service.register(
            email="test@example.com",
            password="password123"
        )

        # Duplicate registration should fail
        with pytest.raises(DuplicateEmailError):
            await auth_service.register(
                email="test@example.com",
                password="different_password"
            )

    async def test_password_reset_flow(self, auth_service, db):
        """Should reset password and login with new password."""
        # Register user
        user = await auth_service.register(
            email="test@example.com",
            password="old_password"
        )

        # Request password reset
        reset_token = await auth_service.request_password_reset("test@example.com")

        # Reset password
        await auth_service.reset_password(reset_token, "new_password")

        # Login with new password should work
        token = await auth_service.authenticate("test@example.com", "new_password")
        assert token.access_token is not None

        # Login with old password should fail
        with pytest.raises(AuthError):
            await auth_service.authenticate("test@example.com", "old_password")
```

**Key characteristics:**
- Use real dependencies (test database, cache)
- Test actual interactions between components
- Verify data persistence, transactions
- Don't test external APIs (mock those)

---

### Layer 3: E2E Tests - Full Example

**File:** `tests/e2e/test_user_workflows.py`

```python
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

    async def test_invalid_token_rejected(self, client):
        """Protected endpoints should reject invalid tokens."""
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid_token_123"}
        )
        assert response.status_code == 401

class TestUserProfileFlow:
    """Test user profile management."""

    async def test_update_profile(self, client):
        """User can update their profile."""
        # Register and login
        await client.post("/api/auth/register", json={
            "email": "user@example.com",
            "password": "SecurePass123!"
        })
        response = await client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "SecurePass123!"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Update profile
        response = await client.patch("/api/users/me", json={
            "name": "John Doe",
            "bio": "Software developer"
        }, headers=headers)
        assert response.status_code == 200

        # Verify update
        response = await client.get("/api/users/me", headers=headers)
        assert response.json()["name"] == "John Doe"
        assert response.json()["bio"] == "Software developer"
```

**Key characteristics:**
- HTTP requests to real API
- Full database, cache, all services
- Test realistic user scenarios
- Don't test every edge case (that's what unit tests are for)

---

## Test Organization Patterns

Choose based on complexity and testing needs:

### 1. Simple Functions: Single Test Function

**When to use:** Simple functions, independent cases, signature changes often

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

**Pros:** One place to update when function signature changes
**Cons:** Less clear which case failed

---

### 2. Complex Functions: Parametrized Tests (Recommended)

**When to use:** Many cases, need clear failure reporting

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

**Pros:** Single definition + individual case isolation + clear test names
**Cons:** Slightly more complex syntax

---

### 3. Critical Functions: Separate Test Methods

**When to use:** Security-critical code, complex setup per case

```python
class TestAuthenticate:
    async def test_success_valid_credentials(self, auth_service):
        token = await auth_service.authenticate("test@example.com", "password")
        assert token.access_token is not None

    async def test_failure_invalid_password(self, auth_service):
        with pytest.raises(AuthError, match="Invalid credentials"):
            await auth_service.authenticate("test@example.com", "wrong")

    async def test_failure_user_not_found(self, auth_service):
        with pytest.raises(AuthError, match="Invalid credentials"):
            await auth_service.authenticate("notfound@example.com", "password")
```

**Pros:** Maximum clarity, can skip/run individual cases easily
**Cons:** More maintenance when signature changes

---

## Fixtures and Test Data

### Shared Fixtures (conftest.py)

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

### Fixture Scopes

- `scope="session"` - Created once for entire test run (databases, connections)
- `scope="module"` - Created once per test file
- `scope="function"` - Created for each test (default)

### Loading Test Data from Files

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

## Best Practices (Detailed)

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

---

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

---

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

---

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

---

### 5. Mock Properly (Critical)

**CRITICAL: Mock everything external to the function being tested, including other internal functions.**

Unit tests should test ONLY the function itself, not its dependencies.

```python
# GOOD - mock all dependencies external to the function
@pytest.fixture
def mock_user_repo():
    """Mock user repository (external to authenticate function)"""
    repo = Mock()
    repo.find_by_email = AsyncMock(return_value=User(id="123", email="test@example.com"))
    return repo

@pytest.fixture
def mock_password_hasher():
    """Mock password verification (external to authenticate function)"""
    hasher = Mock()
    hasher.verify = Mock(return_value=True)
    return hasher

async def test_authenticate_success(mock_user_repo, mock_password_hasher):
    """Test authenticate function in isolation"""
    auth_service = AuthService(user_repo=mock_user_repo, hasher=mock_password_hasher)

    # Test ONLY authenticate, not user_repo.find_by_email or hasher.verify
    token = await auth_service.authenticate("test@example.com", "password")

    assert token.access_token is not None
    mock_user_repo.find_by_email.assert_called_once_with("test@example.com")
    mock_password_hasher.verify.assert_called_once()

# GOOD - even mock internal helper functions when testing orchestration function
def test_process_user_data():
    """Test process_user_data orchestration logic only"""
    with patch('src.services.user_service._validate_user') as mock_validate:
        with patch('src.services.user_service._transform_user') as mock_transform:
            with patch('src.services.user_service._save_user') as mock_save:
                mock_validate.return_value = True
                mock_transform.return_value = {"id": "123"}

                # Test ONLY the orchestration logic, not helper implementations
                result = process_user_data({"email": "test@example.com"})

                mock_validate.assert_called_once()
                mock_transform.assert_called_once()
                mock_save.assert_called_once_with({"id": "123"})

# BAD - testing multiple functions together (not a unit test)
async def test_authenticate_integration():
    """This is an integration test, not a unit test"""
    # Using real user_repo and real password hasher
    auth_service = AuthService(user_repo=UserRepository(db), hasher=PasswordHasher())
    token = await auth_service.authenticate("test@example.com", "password")
    # This tests authenticate + find_by_email + password verification together
```

**What to mock:**
- Database/repository calls
- External API calls
- File I/O operations
- Cache operations
- Other internal functions called by the function under test
- Password hashers, crypto operations
- Time/date functions (if testing time-sensitive logic)

**What NOT to mock:**
- The function you're testing
- Simple data transformations (let them run)
- Pure functions with no side effects (unless part of external dependency)

**Testing strategy:**
- **Unit tests**: Mock everything external to the function (test function in isolation)
- **Integration tests**: Use real dependencies to test components working together
- **E2E tests**: No mocks, test complete workflows

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

# Parametrized tests
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected

# Async tests
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

---

### JavaScript/TypeScript (Jest/Vitest)

```javascript
// test_module.test.js
import { describe, it, expect, beforeEach, vi } from 'vitest';
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

// Mocking
const mockUserRepo = {
  findByEmail: vi.fn().mockResolvedValue({
    id: '123',
    email: 'test@example.com'
  })
};

// Setup/teardown
beforeEach(() => {
  vi.clearAllMocks();
});
```

---

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
        {"user not found", "notfound@example.com", "password", true},
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

// Table-driven tests with expected values
func TestCalculate(t *testing.T) {
    tests := []struct {
        name     string
        input    int
        expected int
    }{
        {"zero", 0, 0},
        {"positive", 5, 10},
        {"negative", -5, -10},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Calculate(tt.input)
            if result != tt.expected {
                t.Errorf("Calculate(%d) = %d; want %d", tt.input, result, tt.expected)
            }
        })
    }
}
```

---

**Bottom line:** These patterns provide comprehensive examples for implementing the testing standards. Always refer to SKILL.md for core principles and quick reference, and this document for detailed implementation guidance.
