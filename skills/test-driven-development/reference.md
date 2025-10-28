# Test-Driven Development - Reference Guide

This document contains detailed examples, code patterns, and advanced TDD techniques to complement the core TDD skill.

---

## Table of Contents

1. [RED-GREEN-REFACTOR Detailed Examples](#red-green-refactor-detailed-examples)
2. [Test-First Implementation Complete Example](#test-first-implementation-complete-example)
3. [Outside-In TDD Complete Example](#outside-in-tdd-complete-example)
4. [Inside-Out TDD Complete Example](#inside-out-tdd-complete-example)
5. [TDD for Refactoring Complete Example](#tdd-for-refactoring-complete-example)
6. [TDD for Debugging Complete Example](#tdd-for-debugging-complete-example)
7. [Common Pitfalls with Anti-Patterns](#common-pitfalls-with-anti-patterns)
8. [Language-Specific TDD Patterns](#language-specific-tdd-patterns)
9. [Advanced TDD Techniques](#advanced-tdd-techniques)

---

## RED-GREEN-REFACTOR Detailed Examples

### Example: Minimal Implementation Progression

This example shows how multiple tests gradually force a more complete implementation.

**Test 1: Returns user**

```python
# RED
def test_authenticate_returns_user():
    """Authenticate should return a user object."""
    user = authenticate("alice@example.com", "password")
    assert user is not None

# Run test - FAIL
# $ pytest tests/test_auth.py::test_authenticate_returns_user -v
# FAILED - NameError: name 'authenticate' is not defined
```

```python
# GREEN (minimal implementation)
def authenticate(email: str, password: str) -> User:
    return User(email=email, authenticated=True)  # Hardcoded!

# Run test - PASS
# $ pytest tests/test_auth.py::test_authenticate_returns_user -v
# PASSED
```

**Test 2: Validates credentials**

```python
# RED
def test_authenticate_fails_with_invalid_password():
    """Authentication should fail with wrong password."""
    with pytest.raises(AuthenticationError):
        authenticate("alice@example.com", "wrong_password")

# Run test - FAIL (no validation yet, always returns user)
# $ pytest tests/test_auth.py::test_authenticate_fails_with_invalid_password -v
# FAILED - Did not raise AuthenticationError
```

```python
# GREEN (add minimal password check)
def authenticate(email: str, password: str) -> User:
    if password != "secure_password":  # Still hardcoded!
        raise AuthenticationError("Invalid credentials")
    return User(email=email, authenticated=True)

# Run test - PASS
# $ pytest tests/test_auth.py::test_authenticate_fails_with_invalid_password -v
# PASSED
```

**Test 3: Checks database**

```python
# RED
def test_authenticate_checks_user_exists():
    """Authentication should fail if user doesn't exist."""
    with pytest.raises(AuthenticationError):
        authenticate("nobody@example.com", "password")

# Run test - FAIL (no DB check, still hardcoded)
# $ pytest tests/test_auth.py::test_authenticate_checks_user_exists -v
# FAILED - Did not raise AuthenticationError
```

```python
# GREEN (finally add real DB lookup)
def authenticate(email: str, password: str) -> User:
    user = db.find_user_by_email(email)
    if not user:
        raise AuthenticationError("User not found")
    if not check_password(password, user.password_hash):
        raise AuthenticationError("Invalid password")
    return User(email=user.email, authenticated=True)

# Run all tests - PASS
# $ pytest tests/test_auth.py -v
# test_authenticate_returns_user PASSED
# test_authenticate_fails_with_invalid_password PASSED
# test_authenticate_checks_user_exists PASSED
```

**REFACTOR (improve code quality)**

```python
def authenticate(email: str, password: str) -> User:
    """Authenticate user with email and password.

    Args:
        email: User email address
        password: Plain text password

    Returns:
        User object with authenticated=True

    Raises:
        AuthenticationError: If credentials invalid or user not found
    """
    user = _find_and_validate_user(email)
    _verify_password(password, user.password_hash)
    return User(email=user.email, authenticated=True)


def _find_and_validate_user(email: str) -> DBUser:
    """Find user by email or raise AuthenticationError."""
    user = db.find_user_by_email(email)
    if not user:
        # Don't leak whether user exists - generic message
        raise AuthenticationError("Invalid credentials")
    return user


def _verify_password(password: str, password_hash: str) -> None:
    """Verify password matches hash or raise AuthenticationError."""
    if not check_password(password, password_hash):
        raise AuthenticationError("Invalid credentials")

# Run all tests - still PASS
# $ pytest tests/test_auth.py -v
# All tests PASSED (behavior unchanged, structure improved)
```

**Notice the progression:**
1. First test forces function to exist and return something
2. Second test forces password validation
3. Third test forces database lookup
4. Refactor extracts helpers, improves naming, adds security (no user enumeration)

---

## Test-First Implementation Complete Example

### Feature: User Registration System

**Step 1: Clarify Requirements**

```
Feature: User Registration
- Input: email (string), password (string), username (string)
- Output: User object with id, email, username, created_at
- Errors:
  - Email already exists
  - Invalid email format
  - Password too weak (<8 chars, no special char)
  - Username too short (<3 chars)
- Edge cases:
  - Email case insensitive (alice@example.com == ALICE@example.com)
  - Whitespace trimmed from username
  - Username uniqueness
- Performance: <200ms for successful registration
```

**Step 2: Write test for simplest case (happy path)**

```python
# tests/test_registration.py
import pytest
from auth.registration import register_user, RegistrationError


def test_register_user_with_valid_data():
    """User can register with valid email, password, username."""
    # Arrange
    email = "alice@example.com"
    password = "SecurePass123!"
    username = "alice"

    # Act
    user = register_user(email, password, username)

    # Assert
    assert user.email == "alice@example.com"
    assert user.username == "alice"
    assert user.id is not None
    assert user.created_at is not None
    # Password should be hashed, not stored plain
    assert user.password_hash != password
```

**Step 3: Run test (RED)**

```bash
$ pytest tests/test_registration.py::test_register_user_with_valid_data -v
FAILED - ModuleNotFoundError: No module named 'auth.registration'
```

**Step 4: Write minimal implementation (GREEN)**

```python
# auth/registration.py
from datetime import datetime
from dataclasses import dataclass
from typing import Optional


class RegistrationError(Exception):
    """Raised when user registration fails."""
    pass


@dataclass
class User:
    id: int
    email: str
    username: str
    password_hash: str
    created_at: datetime


def register_user(email: str, password: str, username: str) -> User:
    """Register new user with email, password, and username."""
    # Minimal implementation - just enough to pass test
    password_hash = hash_password(password)
    user = User(
        id=1,  # Hardcoded for now
        email=email,
        username=username,
        password_hash=password_hash,
        created_at=datetime.now()
    )
    return user


def hash_password(password: str) -> str:
    """Hash password (placeholder implementation)."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()
```

**Step 5: Run test (GREEN)**

```bash
$ pytest tests/test_registration.py::test_register_user_with_valid_data -v
PASSED
```

**Step 6: Add test for next case (error: duplicate email)**

```python
def test_register_user_fails_with_duplicate_email():
    """Registration fails if email already exists."""
    # Arrange: Create first user
    register_user("alice@example.com", "SecurePass123!", "alice")

    # Act & Assert: Second registration with same email should fail
    with pytest.raises(RegistrationError) as exc_info:
        register_user("alice@example.com", "DifferentPass456!", "alice2")

    assert "already registered" in str(exc_info.value).lower()
```

**Step 7: Run test (RED)**

```bash
$ pytest tests/test_registration.py::test_register_user_fails_with_duplicate_email -v
FAILED - Did not raise RegistrationError
```

**Step 8: Implement duplicate check (GREEN)**

```python
# Simple in-memory storage for example (would be DB in production)
_registered_users = {}


def register_user(email: str, password: str, username: str) -> User:
    """Register new user with email, password, and username."""
    # Check for duplicate email
    normalized_email = email.lower()
    if normalized_email in _registered_users:
        raise RegistrationError(f"Email {email} is already registered")

    password_hash = hash_password(password)
    user = User(
        id=len(_registered_users) + 1,
        email=email,
        username=username,
        password_hash=password_hash,
        created_at=datetime.now()
    )

    # Store user
    _registered_users[normalized_email] = user
    return user
```

**Step 9: Continue cycle for all cases**

```python
# Test: Invalid email format
def test_register_user_fails_with_invalid_email():
    """Registration fails with invalid email format."""
    with pytest.raises(RegistrationError) as exc_info:
        register_user("not-an-email", "SecurePass123!", "alice")
    assert "invalid email" in str(exc_info.value).lower()


# Test: Weak password
def test_register_user_fails_with_weak_password():
    """Registration fails with password < 8 chars."""
    with pytest.raises(RegistrationError) as exc_info:
        register_user("alice@example.com", "weak", "alice")
    assert "password" in str(exc_info.value).lower()


# Test: Short username
def test_register_user_fails_with_short_username():
    """Registration fails with username < 3 chars."""
    with pytest.raises(RegistrationError) as exc_info:
        register_user("alice@example.com", "SecurePass123!", "ab")
    assert "username" in str(exc_info.value).lower()


# Test: Email case insensitive
def test_register_user_email_case_insensitive():
    """Email comparison is case insensitive."""
    register_user("alice@example.com", "SecurePass123!", "alice")

    with pytest.raises(RegistrationError):
        register_user("ALICE@EXAMPLE.COM", "SecurePass123!", "alice2")


# Test: Username whitespace trimmed
def test_register_user_trims_username_whitespace():
    """Username whitespace is trimmed."""
    user = register_user("alice@example.com", "SecurePass123!", "  alice  ")
    assert user.username == "alice"
```

**Final implementation after all tests pass:**

```python
import re
from datetime import datetime
from dataclasses import dataclass


class RegistrationError(Exception):
    """Raised when user registration fails."""
    pass


@dataclass
class User:
    id: int
    email: str
    username: str
    password_hash: str
    created_at: datetime


_registered_users = {}


def register_user(email: str, password: str, username: str) -> User:
    """Register new user with email, password, and username.

    Args:
        email: User email address
        password: Plain text password (min 8 chars, must contain special char)
        username: Username (min 3 chars)

    Returns:
        User object with id, hashed password, and timestamp

    Raises:
        RegistrationError: If validation fails or email already registered
    """
    # Validate and normalize inputs
    normalized_email = _validate_and_normalize_email(email)
    validated_password = _validate_password(password)
    normalized_username = _validate_and_normalize_username(username)

    # Check for duplicate email
    if normalized_email in _registered_users:
        raise RegistrationError(f"Email {email} is already registered")

    # Create user
    password_hash = hash_password(validated_password)
    user = User(
        id=len(_registered_users) + 1,
        email=email,
        username=normalized_username,
        password_hash=password_hash,
        created_at=datetime.now()
    )

    # Store user
    _registered_users[normalized_email] = user
    return user


def _validate_and_normalize_email(email: str) -> str:
    """Validate email format and return normalized version."""
    # Simple email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise RegistrationError(f"Invalid email format: {email}")
    return email.lower()


def _validate_password(password: str) -> str:
    """Validate password meets security requirements."""
    if len(password) < 8:
        raise RegistrationError("Password must be at least 8 characters")

    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise RegistrationError("Password must contain special character")

    return password


def _validate_and_normalize_username(username: str) -> str:
    """Validate username and return normalized (trimmed) version."""
    normalized = username.strip()
    if len(normalized) < 3:
        raise RegistrationError("Username must be at least 3 characters")
    return normalized


def hash_password(password: str) -> str:
    """Hash password using SHA-256 (use bcrypt in production)."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()
```

**Run all tests:**

```bash
$ pytest tests/test_registration.py -v
test_register_user_with_valid_data PASSED
test_register_user_fails_with_duplicate_email PASSED
test_register_user_fails_with_invalid_email PASSED
test_register_user_fails_with_weak_password PASSED
test_register_user_fails_with_short_username PASSED
test_register_user_email_case_insensitive PASSED
test_register_user_trims_username_whitespace PASSED

7 passed in 0.03s
```

---

## Outside-In TDD Complete Example

### Feature: User Authentication API

**Start from the outside (API endpoint) and work inward to implementation.**

**Level 1: API Endpoint (Outside)**

```python
# tests/e2e/test_auth_api.py
def test_login_endpoint_with_valid_credentials():
    """POST /api/login returns JWT token for valid credentials."""
    # Arrange: Create user first
    client.post("/api/register", json={
        "email": "alice@example.com",
        "password": "SecurePass123!",
        "username": "alice"
    })

    # Act: Login
    response = client.post("/api/login", json={
        "email": "alice@example.com",
        "password": "SecurePass123!"
    })

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "alice@example.com"
```

**Run test (RED) - endpoint doesn't exist yet:**

```bash
$ pytest tests/e2e/test_auth_api.py::test_login_endpoint_with_valid_credentials -v
FAILED - 404 Not Found
```

**Implement endpoint (GREEN) - mock the service layer:**

```python
# api/endpoints.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: dict


@router.post("/api/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Login endpoint - authenticate and return JWT token."""
    # For now, mock the authentication service
    # (This will fail once we add real tests, driving us to implement it)
    if request.email == "alice@example.com":
        return LoginResponse(
            token="fake_jwt_token",
            user={"email": request.email, "username": "alice"}
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

**Run test (GREEN):**

```bash
$ pytest tests/e2e/test_auth_api.py::test_login_endpoint_with_valid_credentials -v
PASSED
```

**Level 2: Service Layer (Middle)**

Now drop down to test the authentication service that the endpoint will use.

```python
# tests/unit/test_auth_service.py
from auth.service import AuthenticationService, AuthenticationError


def test_authenticate_with_valid_credentials():
    """Authentication service validates credentials and returns user."""
    # Arrange
    service = AuthenticationService()
    # Assume user exists in DB (would use fixture in real test)

    # Act
    user = service.authenticate("alice@example.com", "SecurePass123!")

    # Assert
    assert user.email == "alice@example.com"
    assert user.authenticated is True
```

**Run test (RED):**

```bash
$ pytest tests/unit/test_auth_service.py::test_authenticate_with_valid_credentials -v
FAILED - ModuleNotFoundError: No module named 'auth.service'
```

**Implement service (GREEN) - mock the password checking:**

```python
# auth/service.py
from dataclasses import dataclass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


@dataclass
class AuthenticatedUser:
    email: str
    username: str
    authenticated: bool = True


class AuthenticationService:
    """Service for user authentication."""

    def authenticate(self, email: str, password: str) -> AuthenticatedUser:
        """Authenticate user with email and password."""
        # For now, mock the password verification
        # (This will fail once we add real tests, driving us to implement it)
        user = self._find_user(email)
        if not user:
            raise AuthenticationError("Invalid credentials")

        # Mock password check (will implement later)
        if password == "SecurePass123!":
            return AuthenticatedUser(
                email=user["email"],
                username=user["username"]
            )

        raise AuthenticationError("Invalid credentials")

    def _find_user(self, email: str):
        """Find user in database (mocked for now)."""
        # Mock user lookup (would query DB in production)
        if email == "alice@example.com":
            return {"email": email, "username": "alice"}
        return None
```

**Run test (GREEN):**

```bash
$ pytest tests/unit/test_auth_service.py::test_authenticate_with_valid_credentials -v
PASSED
```

**Level 3: Password Verification (Inside)**

Drop down to test password hashing and verification.

```python
# tests/unit/test_password.py
from auth.password import hash_password, verify_password


def test_password_hashing_and_verification():
    """Password can be hashed and verified."""
    # Arrange
    password = "SecurePass123!"

    # Act
    hashed = hash_password(password)

    # Assert
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False
    assert hashed != password  # Should be hashed, not plain text
```

**Run test (RED):**

```bash
$ pytest tests/unit/test_password.py::test_password_hashing_and_verification -v
FAILED - ModuleNotFoundError: No module named 'auth.password'
```

**Implement password utilities (GREEN):**

```python
# auth/password.py
import hashlib


def hash_password(password: str) -> str:
    """Hash password using SHA-256 (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password matches hash."""
    return hash_password(password) == password_hash
```

**Run test (GREEN):**

```bash
$ pytest tests/unit/test_password.py::test_password_hashing_and_verification -v
PASSED
```

**Level 4: Wire Everything Together**

Now update the service to use real password verification:

```python
# auth/service.py
from auth.password import verify_password
from auth.database import find_user_by_email  # Assume DB layer exists


class AuthenticationService:
    """Service for user authentication."""

    def authenticate(self, email: str, password: str) -> AuthenticatedUser:
        """Authenticate user with email and password."""
        user = find_user_by_email(email)
        if not user:
            raise AuthenticationError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")

        return AuthenticatedUser(
            email=user.email,
            username=user.username
        )
```

**Update endpoint to use real service:**

```python
# api/endpoints.py
from auth.service import AuthenticationService, AuthenticationError
from auth.tokens import create_jwt_token


@router.post("/api/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Login endpoint - authenticate and return JWT token."""
    service = AuthenticationService()

    try:
        user = service.authenticate(request.email, request.password)
        token = create_jwt_token(user.email)

        return LoginResponse(
            token=token,
            user={"email": user.email, "username": user.username}
        )
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

**Run all tests (full stack now integrated):**

```bash
$ pytest tests/ -v
tests/e2e/test_auth_api.py::test_login_endpoint_with_valid_credentials PASSED
tests/unit/test_auth_service.py::test_authenticate_with_valid_credentials PASSED
tests/unit/test_password.py::test_password_hashing_and_verification PASSED

All tests PASSED
```

**Outside-In summary:**
1. Started with API endpoint test (user-facing behavior)
2. Dropped down to service layer test
3. Dropped down to password utility test
4. Wired everything together
5. All tests pass - feature complete

---

## Inside-Out TDD Complete Example

### Feature: Password Strength Validator

**Start from the inside (core utilities) and build up to API.**

**Level 1: Core Utility (Inside)**

```python
# tests/unit/test_password_strength.py
from auth.password_strength import check_password_strength, PasswordStrength


def test_password_strength_weak():
    """Short password is weak."""
    result = check_password_strength("abc")
    assert result == PasswordStrength.WEAK


def test_password_strength_medium():
    """Password with letters and numbers is medium."""
    result = check_password_strength("abc123")
    assert result == PasswordStrength.MEDIUM


def test_password_strength_strong():
    """Password with letters, numbers, and special chars is strong."""
    result = check_password_strength("Abc123!@#")
    assert result == PasswordStrength.STRONG
```

**Run test (RED):**

```bash
$ pytest tests/unit/test_password_strength.py -v
FAILED - ModuleNotFoundError
```

**Implement password strength checker (GREEN):**

```python
# auth/password_strength.py
from enum import Enum
import re


class PasswordStrength(Enum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


def check_password_strength(password: str) -> PasswordStrength:
    """Check password strength based on length and character types."""
    if len(password) < 6:
        return PasswordStrength.WEAK

    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_number = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

    if has_letter and has_number and has_special:
        return PasswordStrength.STRONG
    elif has_letter and has_number:
        return PasswordStrength.MEDIUM
    else:
        return PasswordStrength.WEAK
```

**Run test (GREEN):**

```bash
$ pytest tests/unit/test_password_strength.py -v
PASSED
```

**Level 2: Validation Service (Middle)**

Build up to validation service that uses password strength checker.

```python
# tests/unit/test_password_validator.py
from auth.password_validator import PasswordValidator, PasswordValidationError


def test_password_validator_accepts_strong_password():
    """Validator accepts strong password."""
    validator = PasswordValidator(min_strength="medium")
    validator.validate("Abc123!@#")  # Should not raise


def test_password_validator_rejects_weak_password():
    """Validator rejects weak password."""
    validator = PasswordValidator(min_strength="medium")

    with pytest.raises(PasswordValidationError) as exc_info:
        validator.validate("abc")

    assert "too weak" in str(exc_info.value).lower()


def test_password_validator_checks_length():
    """Validator checks minimum length."""
    validator = PasswordValidator(min_length=10)

    with pytest.raises(PasswordValidationError):
        validator.validate("Abc123!")  # Only 7 chars
```

**Run test (RED):**

```bash
$ pytest tests/unit/test_password_validator.py -v
FAILED - ModuleNotFoundError
```

**Implement validator (GREEN):**

```python
# auth/password_validator.py
from auth.password_strength import check_password_strength, PasswordStrength


class PasswordValidationError(Exception):
    """Raised when password validation fails."""
    pass


class PasswordValidator:
    """Validate password meets security requirements."""

    def __init__(
        self,
        min_length: int = 8,
        min_strength: str = "medium"
    ):
        self.min_length = min_length
        self.min_strength = PasswordStrength(min_strength)

    def validate(self, password: str) -> None:
        """Validate password meets requirements.

        Raises:
            PasswordValidationError: If validation fails
        """
        if len(password) < self.min_length:
            raise PasswordValidationError(
                f"Password must be at least {self.min_length} characters"
            )

        strength = check_password_strength(password)
        strength_values = {
            PasswordStrength.WEAK: 1,
            PasswordStrength.MEDIUM: 2,
            PasswordStrength.STRONG: 3
        }

        if strength_values[strength] < strength_values[self.min_strength]:
            raise PasswordValidationError(
                f"Password too weak (got {strength.value}, "
                f"need {self.min_strength.value})"
            )
```

**Run test (GREEN):**

```bash
$ pytest tests/unit/test_password_validator.py -v
PASSED
```

**Level 3: Registration Service (Higher)**

Build up to registration service that uses validator.

```python
# tests/unit/test_registration_service.py
from auth.registration_service import RegistrationService, RegistrationError


def test_registration_accepts_strong_password():
    """Registration succeeds with strong password."""
    service = RegistrationService()
    user = service.register("alice@example.com", "Abc123!@#", "alice")
    assert user.email == "alice@example.com"


def test_registration_rejects_weak_password():
    """Registration fails with weak password."""
    service = RegistrationService()

    with pytest.raises(RegistrationError) as exc_info:
        service.register("alice@example.com", "weak", "alice")

    assert "password" in str(exc_info.value).lower()
```

**Implement registration service (GREEN):**

```python
# auth/registration_service.py
from auth.password_validator import PasswordValidator, PasswordValidationError
from auth.models import User


class RegistrationError(Exception):
    """Raised when registration fails."""
    pass


class RegistrationService:
    """Service for user registration."""

    def __init__(self):
        self.password_validator = PasswordValidator()

    def register(
        self,
        email: str,
        password: str,
        username: str
    ) -> User:
        """Register new user.

        Raises:
            RegistrationError: If validation fails
        """
        # Validate password
        try:
            self.password_validator.validate(password)
        except PasswordValidationError as e:
            raise RegistrationError(str(e))

        # Create user (simplified)
        user = User(email=email, username=username)
        return user
```

**Level 4: API Endpoint (Outside)**

Finally build API endpoint that uses registration service.

```python
# tests/e2e/test_registration_api.py
def test_registration_endpoint_with_strong_password():
    """POST /api/register succeeds with strong password."""
    response = client.post("/api/register", json={
        "email": "alice@example.com",
        "password": "Abc123!@#",
        "username": "alice"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"


def test_registration_endpoint_rejects_weak_password():
    """POST /api/register fails with weak password."""
    response = client.post("/api/register", json={
        "email": "alice@example.com",
        "password": "weak",
        "username": "alice"
    })

    assert response.status_code == 400
    assert "password" in response.json()["detail"].lower()
```

**Implement API endpoint (GREEN):**

```python
# api/endpoints.py
from auth.registration_service import RegistrationService, RegistrationError


@router.post("/api/register", status_code=201)
def register(request: RegistrationRequest):
    """Register new user."""
    service = RegistrationService()

    try:
        user = service.register(
            request.email,
            request.password,
            request.username
        )

        return {
            "email": user.email,
            "username": user.username
        }
    except RegistrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Run all tests (full stack):**

```bash
$ pytest tests/ -v
tests/unit/test_password_strength.py::test_password_strength_weak PASSED
tests/unit/test_password_strength.py::test_password_strength_medium PASSED
tests/unit/test_password_strength.py::test_password_strength_strong PASSED
tests/unit/test_password_validator.py::test_password_validator_accepts_strong_password PASSED
tests/unit/test_password_validator.py::test_password_validator_rejects_weak_password PASSED
tests/unit/test_password_validator.py::test_password_validator_checks_length PASSED
tests/unit/test_registration_service.py::test_registration_accepts_strong_password PASSED
tests/unit/test_registration_service.py::test_registration_rejects_weak_password PASSED
tests/e2e/test_registration_api.py::test_registration_endpoint_with_strong_password PASSED
tests/e2e/test_registration_api.py::test_registration_endpoint_rejects_weak_password PASSED

All tests PASSED
```

**Inside-Out summary:**
1. Started with password strength checker (core utility)
2. Built up to password validator
3. Built up to registration service
4. Finally built API endpoint
5. All tests pass - feature complete with solid foundation

---

## TDD for Refactoring Complete Example

### Scenario: Refactor Complex Function

**Starting code (messy, deeply nested):**

```python
# Original code - complex and hard to test
def process_record(record):
    """Process a vulnerability record."""
    if record:
        if record.get('type') == 'vulnerability':
            if record.get('severity'):
                severity = record.get('severity')
                if severity in ['critical', 'high']:
                    if record.get('asset_id'):
                        asset_id = record.get('asset_id')
                        if validate_asset_id(asset_id):
                            vuln = {
                                'asset_id': asset_id,
                                'severity': severity,
                                'title': record.get('title', 'Unknown'),
                                'status': 'open'
                            }
                            if record.get('cvss_score'):
                                vuln['cvss_score'] = float(record['cvss_score'])
                            return vuln
    return None
```

**Step 1: Write characterization tests (capture current behavior)**

```python
# tests/test_process_record.py
from processor import process_record


def test_process_record_with_valid_critical_vulnerability():
    """Process valid critical vulnerability."""
    record = {
        'type': 'vulnerability',
        'severity': 'critical',
        'asset_id': 'asset-123',
        'title': 'SQL Injection',
        'cvss_score': '9.8'
    }

    result = process_record(record)

    assert result is not None
    assert result['asset_id'] == 'asset-123'
    assert result['severity'] == 'critical'
    assert result['title'] == 'SQL Injection'
    assert result['cvss_score'] == 9.8
    assert result['status'] == 'open'


def test_process_record_with_valid_high_vulnerability():
    """Process valid high severity vulnerability."""
    record = {
        'type': 'vulnerability',
        'severity': 'high',
        'asset_id': 'asset-456',
        'title': 'XSS'
    }

    result = process_record(record)

    assert result is not None
    assert result['severity'] == 'high'


def test_process_record_skips_medium_severity():
    """Skip vulnerabilities with medium/low severity."""
    record = {
        'type': 'vulnerability',
        'severity': 'medium',
        'asset_id': 'asset-789'
    }

    result = process_record(record)

    assert result is None


def test_process_record_skips_non_vulnerability():
    """Skip non-vulnerability records."""
    record = {
        'type': 'asset',
        'asset_id': 'asset-123'
    }

    result = process_record(record)

    assert result is None


def test_process_record_skips_missing_asset_id():
    """Skip vulnerability without asset_id."""
    record = {
        'type': 'vulnerability',
        'severity': 'critical',
        'title': 'SQL Injection'
    }

    result = process_record(record)

    assert result is None


def test_process_record_skips_invalid_asset_id():
    """Skip vulnerability with invalid asset_id."""
    record = {
        'type': 'vulnerability',
        'severity': 'critical',
        'asset_id': 'invalid'  # Assume validate_asset_id returns False
    }

    result = process_record(record)

    assert result is None


def test_process_record_handles_missing_title():
    """Use 'Unknown' for missing title."""
    record = {
        'type': 'vulnerability',
        'severity': 'critical',
        'asset_id': 'asset-123'
    }

    result = process_record(record)

    assert result['title'] == 'Unknown'


def test_process_record_handles_none_record():
    """Handle None record gracefully."""
    result = process_record(None)
    assert result is None
```

**Step 2: Verify tests pass (capture current behavior)**

```bash
$ pytest tests/test_process_record.py -v
All tests PASSED
# Current behavior successfully captured
```

**Step 3: Refactor code (improve structure, keep behavior)**

```python
# Refactored version - cleaner, easier to test
def process_record(record: dict | None) -> dict | None:
    """Process a vulnerability record.

    Args:
        record: Vulnerability record dict

    Returns:
        Processed vulnerability dict or None if should be skipped
    """
    if not _should_process_record(record):
        return None

    return _create_vulnerability(record)


def _should_process_record(record: dict | None) -> bool:
    """Check if record should be processed."""
    if not record:
        return False

    if record.get('type') != 'vulnerability':
        return False

    severity = record.get('severity')
    if severity not in ['critical', 'high']:
        return False

    asset_id = record.get('asset_id')
    if not asset_id:
        return False

    if not validate_asset_id(asset_id):
        return False

    return True


def _create_vulnerability(record: dict) -> dict:
    """Create vulnerability dict from record."""
    vuln = {
        'asset_id': record['asset_id'],
        'severity': record['severity'],
        'title': record.get('title', 'Unknown'),
        'status': 'open'
    }

    if 'cvss_score' in record:
        vuln['cvss_score'] = float(record['cvss_score'])

    return vuln
```

**Step 4: Verify tests still pass (behavior unchanged)**

```bash
$ pytest tests/test_process_record.py -v
All tests PASSED
# Behavior unchanged, structure improved!
```

**Refactoring benefits proven by tests:**
- Reduced nesting (6 levels → 2 levels)
- Extracted focused helpers
- Added type hints
- Improved readability
- Same behavior (all tests still pass)

---

## TDD for Debugging Complete Example

### Bug Report: Email Validation Allows Invalid Emails

**Bug report:** "Users can register with invalid email addresses like 'user@' or '@example.com'"

**Step 1: Write failing test reproducing bug**

```python
# tests/test_email_validation.py
import pytest
from auth.email import validate_email, EmailValidationError


def test_validate_email_rejects_missing_domain():
    """Bug: Email without domain should be rejected."""
    with pytest.raises(EmailValidationError):
        validate_email("user@")  # Missing domain


def test_validate_email_rejects_missing_local_part():
    """Bug: Email without local part should be rejected."""
    with pytest.raises(EmailValidationError):
        validate_email("@example.com")  # Missing local part


def test_validate_email_rejects_no_at_sign():
    """Bug: Email without @ should be rejected."""
    with pytest.raises(EmailValidationError):
        validate_email("userexample.com")  # Missing @
```

**Step 2: Run tests - verify they fail (RED)**

```bash
$ pytest tests/test_email_validation.py -v
test_validate_email_rejects_missing_domain FAILED  # Bug reproduced
test_validate_email_rejects_missing_local_part FAILED  # Bug reproduced
test_validate_email_rejects_no_at_sign FAILED  # Bug reproduced

# Current buggy implementation accepts these invalid emails
```

**Current buggy implementation:**

```python
# auth/email.py (BEFORE fix)
class EmailValidationError(Exception):
    pass


def validate_email(email: str) -> str:
    """Validate email format (BUGGY VERSION)."""
    if '@' in email:  # Too simple - bug!
        return email.lower()
    raise EmailValidationError(f"Invalid email: {email}")
```

**Step 3: Fix bug (GREEN)**

```python
# auth/email.py (AFTER fix)
import re


class EmailValidationError(Exception):
    pass


def validate_email(email: str) -> str:
    """Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Normalized (lowercase) email address

    Raises:
        EmailValidationError: If email format is invalid
    """
    # Proper email validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        raise EmailValidationError(f"Invalid email format: {email}")

    return email.lower()
```

**Step 4: Run tests - verify they pass (GREEN)**

```bash
$ pytest tests/test_email_validation.py -v
test_validate_email_rejects_missing_domain PASSED  # Bug fixed!
test_validate_email_rejects_missing_local_part PASSED  # Bug fixed!
test_validate_email_rejects_no_at_sign PASSED  # Bug fixed!
```

**Step 5: Add regression prevention tests**

```python
@pytest.mark.parametrize("invalid_email", [
    "user@",                    # Missing domain
    "@example.com",             # Missing local part
    "userexample.com",          # Missing @
    "user@@example.com",        # Double @
    "user@.com",                # Domain starts with dot
    "user@example",             # Missing TLD
    "user name@example.com",    # Space in local part
])
def test_validate_email_rejects_invalid_formats(invalid_email):
    """Prevent regression: Reject various invalid email formats."""
    with pytest.raises(EmailValidationError):
        validate_email(invalid_email)


@pytest.mark.parametrize("valid_email,expected", [
    ("user@example.com", "user@example.com"),
    ("User@Example.COM", "user@example.com"),  # Normalized to lowercase
    ("user.name@example.com", "user.name@example.com"),
    ("user+tag@example.com", "user+tag@example.com"),
])
def test_validate_email_accepts_valid_formats(valid_email, expected):
    """Ensure valid emails still accepted after fix."""
    result = validate_email(valid_email)
    assert result == expected
```

**Run all tests:**

```bash
$ pytest tests/test_email_validation.py -v
test_validate_email_rejects_missing_domain PASSED
test_validate_email_rejects_missing_local_part PASSED
test_validate_email_rejects_no_at_sign PASSED
test_validate_email_rejects_invalid_formats[user@] PASSED
test_validate_email_rejects_invalid_formats[@example.com] PASSED
test_validate_email_rejects_invalid_formats[userexample.com] PASSED
test_validate_email_rejects_invalid_formats[user@@example.com] PASSED
test_validate_email_rejects_invalid_formats[user@.com] PASSED
test_validate_email_rejects_invalid_formats[user@example] PASSED
test_validate_email_rejects_invalid_formats[user name@example.com] PASSED
test_validate_email_accepts_valid_formats[user@example.com-user@example.com] PASSED
test_validate_email_accepts_valid_formats[User@Example.COM-user@example.com] PASSED
test_validate_email_accepts_valid_formats[user.name@example.com-user.name@example.com] PASSED
test_validate_email_accepts_valid_formats[user+tag@example.com-user+tag@example.com] PASSED

All tests PASSED
```

**TDD debugging benefits demonstrated:**
- Bug reproduced reliably
- Bug stays fixed (regression tests)
- Edge cases now covered
- Documentation of expected behavior

---

## Common Pitfalls with Anti-Patterns

### Pitfall 1: Writing Tests After Implementation

**Anti-pattern example:**

```python
# 1. Write implementation first
def calculate_total(items: list[dict]) -> float:
    """Calculate total price with tax and discount."""
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    tax = subtotal * 0.1
    discount = subtotal * 0.05 if subtotal > 100 else 0
    return subtotal + tax - discount


# 2. Write tests to match implementation (confirmation bias!)
def test_calculate_total():
    """Test calculate_total function."""
    items = [
        {'price': 10.0, 'quantity': 5},
        {'price': 20.0, 'quantity': 2}
    ]

    result = calculate_total(items)

    # Test written to pass - but is this correct?
    assert result == pytest.approx(94.5)  # Just confirms implementation
```

**Problem:** Test confirms implementation, not requirements. If implementation is wrong, test won't catch it.

**Better approach (TDD):**

```python
# 1. Write test first (from requirements)
def test_calculate_total_applies_tax():
    """Total should include 10% tax."""
    items = [{'price': 100.0, 'quantity': 1}]
    # Expected: 100 + (100 * 0.10) = 110.0
    assert calculate_total(items) == pytest.approx(110.0)


def test_calculate_total_applies_discount_over_100():
    """5% discount applied when subtotal > $100."""
    items = [{'price': 60.0, 'quantity': 2}]
    # Subtotal: 120, Tax: 12, Discount: 6, Total: 126
    assert calculate_total(items) == pytest.approx(126.0)


def test_calculate_total_no_discount_under_100():
    """No discount when subtotal <= $100."""
    items = [{'price': 50.0, 'quantity': 2}]
    # Subtotal: 100, Tax: 10, No discount, Total: 110
    assert calculate_total(items) == pytest.approx(110.0)


# Now implement to make tests pass
def calculate_total(items: list[dict]) -> float:
    """Calculate total price with tax and discount."""
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    tax = subtotal * 0.10
    discount = subtotal * 0.05 if subtotal > 100 else 0
    return subtotal + tax - discount
```

### Pitfall 2: Testing Implementation Details

**Anti-pattern example:**

```python
class UserRepository:
    def __init__(self):
        self._cache = {}  # Internal implementation detail

    def find_user(self, user_id: str) -> User:
        """Find user by ID."""
        if user_id in self._cache:
            return self._cache[user_id]

        user = db.query_user(user_id)
        self._cache[user_id] = user
        return user


# BAD TEST - tests implementation detail (cache)
def test_find_user_uses_cache():
    """Test that find_user caches results."""
    repo = UserRepository()

    # First call
    user1 = repo.find_user("user-123")

    # Check cache (testing implementation detail!)
    assert "user-123" in repo._cache
    assert repo._cache["user-123"] == user1

    # Second call should use cache
    user2 = repo.find_user("user-123")
    assert user2 is user1  # Same object from cache
```

**Problem:** Test breaks if caching implementation changes (e.g., switch to external cache), even though behavior is unchanged.

**Better approach (test behavior, not implementation):**

```python
# GOOD TEST - tests behavior (what), not implementation (how)
def test_find_user_returns_correct_user():
    """find_user returns correct user by ID."""
    repo = UserRepository()

    user = repo.find_user("user-123")

    assert user.id == "user-123"
    assert user.email is not None  # Verify it's a real user


def test_find_user_returns_none_for_nonexistent_user():
    """find_user returns None for invalid ID."""
    repo = UserRepository()

    user = repo.find_user("nonexistent")

    assert user is None


# If performance is a concern, test performance, not caching mechanism
def test_find_user_performance():
    """find_user should be fast (testing behavior: performance)."""
    repo = UserRepository()

    import time
    start = time.time()

    # First call
    repo.find_user("user-123")

    # Second call (should be faster if cached, but we don't test cache directly)
    repo.find_user("user-123")

    elapsed = time.time() - start

    # Test performance characteristic, not caching implementation
    assert elapsed < 0.1  # Should be fast (however implemented)
```

### Pitfall 3: Large Steps (Skipping RED Phase)

**Anti-pattern example:**

```python
# Write multiple tests at once without running them
def test_authenticate_valid_credentials():
    ...

def test_authenticate_invalid_password():
    ...

def test_authenticate_user_not_found():
    ...

def test_authenticate_account_locked():
    ...

def test_authenticate_expired_token():
    ...

# Then implement everything
def authenticate(...):
    # Implement all cases at once
    ...

# Then run tests for first time
$ pytest tests/test_auth.py -v
# 3 PASSED, 2 FAILED - but which implementation caused which failure?
```

**Problem:** Hard to debug when tests fail. Lose benefits of small feedback cycles.

**Better approach (one test at a time):**

```python
# Step 1: Write first test
def test_authenticate_valid_credentials():
    user = authenticate("alice@example.com", "password")
    assert user.email == "alice@example.com"

# Step 2: Run test (RED)
$ pytest tests/test_auth.py::test_authenticate_valid_credentials -v
FAILED - NameError

# Step 3: Implement minimal code (GREEN)
def authenticate(email, password):
    return User(email=email)

# Step 4: Run test (GREEN)
$ pytest tests/test_auth.py::test_authenticate_valid_credentials -v
PASSED

# Step 5: Write second test
def test_authenticate_invalid_password():
    with pytest.raises(AuthenticationError):
        authenticate("alice@example.com", "wrong")

# Step 6: Run test (RED)
$ pytest tests/test_auth.py::test_authenticate_invalid_password -v
FAILED

# Step 7: Implement password check (GREEN)
def authenticate(email, password):
    if password != "password":
        raise AuthenticationError()
    return User(email=email)

# Continue one test at a time...
```

### Pitfall 4: Not Running Tests Frequently

**Anti-pattern example:**

```python
# Make many changes without running tests
def authenticate(email, password):
    user = db.find_user(email)  # Change 1
    if not user:
        raise AuthenticationError()  # Change 2
    if not verify_password(password, user.hash):  # Change 3
        log_failed_attempt(user.id)  # Change 4
        increment_failed_count(user.id)  # Change 5
        if user.failed_attempts > 3:  # Change 6
            lock_account(user.id)  # Change 7
        raise AuthenticationError()
    return user

# Run tests once after all changes
$ pytest tests/test_auth.py -v
FAILED - AttributeError: 'NoneType' object has no attribute 'hash'
# Which of the 7 changes caused this? Hard to tell!
```

**Problem:** When tests fail, hard to identify which change broke what.

**Better approach (run tests after each change):**

```python
# Change 1: Add DB lookup
def authenticate(email, password):
    user = db.find_user(email)
    return User(email=email)

# Run tests
$ pytest tests/test_auth.py -v
PASSED

# Change 2: Add null check
def authenticate(email, password):
    user = db.find_user(email)
    if not user:
        raise AuthenticationError()
    return User(email=email)

# Run tests
$ pytest tests/test_auth.py -v
PASSED

# Change 3: Add password verification
def authenticate(email, password):
    user = db.find_user(email)
    if not user:
        raise AuthenticationError()
    if not verify_password(password, user.hash):
        raise AuthenticationError()
    return user

# Run tests
$ pytest tests/test_auth.py -v
FAILED - AttributeError: 'NoneType' object has no attribute 'hash'
# Found it! Change 3 caused the failure. Easy to fix.
```

**Use watch mode for instant feedback:**

```bash
# Terminal 1: Code
vim src/auth.py

# Terminal 2: Watch mode (reruns tests on file changes)
pytest-watch tests/

# Every time you save, tests run automatically
# Immediate feedback on whether changes break anything
```

### Pitfall 5: Over-Refactoring in GREEN Phase

**Anti-pattern example:**

```python
# Test
def test_calculate_discount():
    """Calculate 10% discount for orders over $100."""
    discount = calculate_discount(150.0)
    assert discount == 15.0

# GREEN phase - but trying to be too clever
def calculate_discount(amount: float) -> float:
    """Calculate discount with configurable tiers and strategies."""
    # This is premature! Test only requires simple 10% discount.
    discount_tiers = [
        (1000, 0.20),  # 20% for $1000+
        (500, 0.15),   # 15% for $500+
        (100, 0.10),   # 10% for $100+
    ]

    strategy = DiscountStrategy(tiers=discount_tiers)
    calculator = DiscountCalculator(strategy)
    return calculator.calculate(amount)

# Way too complex for a test that just needs 10% discount!
```

**Problem:** Premature optimization, over-engineering, scope creep beyond what test requires.

**Better approach (simplest code in GREEN, refactor later):**

```python
# GREEN phase - simplest code that passes
def calculate_discount(amount: float) -> float:
    """Calculate 10% discount for orders over $100."""
    if amount > 100:
        return amount * 0.10
    return 0.0

# Test passes with simple code!

# Later, if ANOTHER test requires tiers, THEN refactor:
def test_calculate_discount_multiple_tiers():
    """Higher discounts for larger orders."""
    assert calculate_discount(150) == 15.0   # 10%
    assert calculate_discount(600) == 90.0   # 15%
    assert calculate_discount(1200) == 240.0  # 20%

# NOW refactor to support multiple tiers (driven by new test)
def calculate_discount(amount: float) -> float:
    """Calculate tiered discount."""
    if amount >= 1000:
        return amount * 0.20
    elif amount >= 500:
        return amount * 0.15
    elif amount >= 100:
        return amount * 0.10
    return 0.0

# Add complexity only when tests require it
```

---

## Language-Specific TDD Patterns

### Python (pytest)

**Minimal test structure:**

```python
# tests/test_feature.py
import pytest
from feature import process


def test_process_valid_input():
    """Process should handle valid input."""
    result = process("valid")
    assert result == "expected"


def test_process_invalid_input():
    """Process should raise error for invalid input."""
    with pytest.raises(ValueError) as exc_info:
        process("invalid")
    assert "invalid input" in str(exc_info.value)


@pytest.mark.parametrize("input,expected", [
    ("abc", "ABC"),
    ("123", "123"),
    ("", ""),
])
def test_process_multiple_cases(input, expected):
    """Process handles multiple input cases."""
    assert process(input) == expected
```

**Fixtures for setup:**

```python
# tests/conftest.py
import pytest


@pytest.fixture
def database():
    """Provide test database."""
    db = Database(":memory:")
    db.create_tables()
    yield db
    db.close()


@pytest.fixture
def sample_user(database):
    """Provide sample user."""
    user = database.create_user("alice@example.com", "password")
    return user


# tests/test_auth.py
def test_authenticate_with_valid_credentials(sample_user):
    """Authenticate with valid credentials."""
    user = authenticate("alice@example.com", "password")
    assert user.email == sample_user.email
```

### JavaScript/TypeScript (Jest)

**Minimal test structure:**

```javascript
// __tests__/feature.test.js
import { process } from '../feature';


describe('process', () => {
  it('should handle valid input', () => {
    const result = process('valid');
    expect(result).toBe('expected');
  });

  it('should throw error for invalid input', () => {
    expect(() => {
      process('invalid');
    }).toThrow('invalid input');
  });

  it.each([
    ['abc', 'ABC'],
    ['123', '123'],
    ['', ''],
  ])('should process %s to %s', (input, expected) => {
    expect(process(input)).toBe(expected);
  });
});
```

**Mocking:**

```javascript
// __tests__/auth.test.js
import { authenticate } from '../auth';
import { database } from '../database';

// Mock database
jest.mock('../database');

describe('authenticate', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  it('should authenticate valid user', async () => {
    // Arrange
    const mockUser = { id: 1, email: 'alice@example.com' };
    database.findUser.mockResolvedValue(mockUser);

    // Act
    const user = await authenticate('alice@example.com', 'password');

    // Assert
    expect(user).toEqual(mockUser);
    expect(database.findUser).toHaveBeenCalledWith('alice@example.com');
  });
});
```

### Go (testing package)

**Table-driven tests:**

```go
// feature_test.go
package feature

import "testing"

func TestProcess(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
        wantErr  bool
    }{
        {
            name:     "valid input",
            input:    "valid",
            expected: "expected",
            wantErr:  false,
        },
        {
            name:     "invalid input",
            input:    "invalid",
            expected: "",
            wantErr:  true,
        },
        {
            name:     "empty input",
            input:    "",
            expected: "",
            wantErr:  false,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result, err := Process(tt.input)

            if (err != nil) != tt.wantErr {
                t.Errorf("Process() error = %v, wantErr %v", err, tt.wantErr)
                return
            }

            if result != tt.expected {
                t.Errorf("Process() = %v, want %v", result, tt.expected)
            }
        })
    }
}
```

**Subtests:**

```go
func TestAuthenticate(t *testing.T) {
    t.Run("valid credentials", func(t *testing.T) {
        user, err := Authenticate("alice@example.com", "password")
        if err != nil {
            t.Fatalf("unexpected error: %v", err)
        }
        if user.Email != "alice@example.com" {
            t.Errorf("got %v, want %v", user.Email, "alice@example.com")
        }
    })

    t.Run("invalid password", func(t *testing.T) {
        _, err := Authenticate("alice@example.com", "wrong")
        if err == nil {
            t.Fatal("expected error, got nil")
        }
    })
}
```

---

## Advanced TDD Techniques

### Mutation Testing (Test Your Tests)

**Concept:** Introduce bugs into code intentionally. If tests still pass, tests are weak.

```python
# Original code
def is_adult(age: int) -> bool:
    return age >= 18

# Test
def test_is_adult():
    assert is_adult(20) is True
    assert is_adult(10) is False

# Mutation: Change >= to >
def is_adult(age: int) -> bool:
    return age > 18  # Mutated!

# Run test
$ pytest tests/test_age.py
PASSED  # Uh oh! Test didn't catch the mutation!

# Test is weak - add boundary test
def test_is_adult_boundary():
    assert is_adult(18) is True  # Now catches the mutation
    assert is_adult(17) is False
```

**Tools:**
- Python: `mutmut`, `cosmic-ray`
- JavaScript: `Stryker`
- Go: `go-mutesting`

### Property-Based Testing

**Concept:** Test properties that should always hold, with generated inputs.

```python
# Traditional TDD
def test_reverse_string():
    assert reverse("abc") == "cba"
    assert reverse("hello") == "olleh"

# Property-based testing
from hypothesis import given
import hypothesis.strategies as st

@given(st.text())
def test_reverse_twice_is_identity(s):
    """Reversing twice should return original string."""
    assert reverse(reverse(s)) == s

@given(st.text())
def test_reverse_length_unchanged(s):
    """Reversing should not change length."""
    assert len(reverse(s)) == len(s)

# Hypothesis generates hundreds of random strings to test properties
```

**Tools:**
- Python: `hypothesis`
- JavaScript: `fast-check`
- Go: `gopter`

### Contract Testing (APIs)

**Concept:** Test API contracts between services.

```python
# Consumer test (frontend)
def test_get_user_api_contract():
    """User API should return expected structure."""
    response = requests.get("http://api/users/123")

    assert response.status_code == 200
    data = response.json()

    # Contract: API must return these fields
    assert "id" in data
    assert "email" in data
    assert "username" in data
    assert isinstance(data["id"], int)
    assert isinstance(data["email"], str)

# Producer test (backend)
def test_get_user_endpoint_contract():
    """User endpoint should fulfill contract."""
    user = User(id=123, email="alice@example.com", username="alice")

    response = client.get("/users/123")

    assert response.status_code == 200
    data = response.json()

    # Verify contract
    assert data == {
        "id": 123,
        "email": "alice@example.com",
        "username": "alice"
    }
```

**Tools:**
- Pact (language-agnostic)
- Spring Cloud Contract (Java)
- Postman Contract Testing

---

**End of Reference Guide**

For core TDD workflow and quick reference, see main SKILL.md file.
