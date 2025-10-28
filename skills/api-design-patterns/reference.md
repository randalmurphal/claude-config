# API Design Patterns - Reference Guide

Detailed examples, OpenAPI specifications, implementation guides, and language-specific patterns for REST API design.

**Core skill:** See SKILL.md for quick reference and core patterns.

---

## Table of Contents

1. [Complete Status Code Reference](#complete-status-code-reference)
2. [Versioning Examples](#versioning-examples)
3. [Pagination Implementation Details](#pagination-implementation-details)
4. [Error Response Examples by Status Code](#error-response-examples-by-status-code)
5. [Authentication Implementation](#authentication-implementation)
6. [Complete OpenAPI Examples](#complete-openapi-examples)
7. [Language-Specific Patterns](#language-specific-patterns)
8. [Security Best Practices](#security-best-practices)
9. [Performance Optimization](#performance-optimization)

---

## Complete Status Code Reference

### 1xx Informational

| Code | Meaning | Use Case |
|------|---------|----------|
| 100 Continue | Client should continue | Large file uploads |
| 101 Switching Protocols | Switching to WebSocket | WebSocket upgrade |

### 2xx Success

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 OK | Request successful | GET, PUT, PATCH with response body |
| 201 Created | Resource created | POST success, include Location header |
| 202 Accepted | Accepted for processing | Async operations, queued jobs |
| 204 No Content | Success, no response body | DELETE, PUT/PATCH with no return |
| 206 Partial Content | Partial resource returned | Range requests, pagination |

### 3xx Redirection

| Code | Meaning | Use Case |
|------|---------|----------|
| 301 Moved Permanently | Resource permanently moved | API endpoint deprecated |
| 302 Found | Temporary redirect | Temporary maintenance redirect |
| 303 See Other | Redirect to another resource | POST → GET redirect |
| 304 Not Modified | Cached version still valid | Conditional GET with ETag |
| 307 Temporary Redirect | Temporary, preserve method | Temporary endpoint change |
| 308 Permanent Redirect | Permanent, preserve method | Permanent endpoint change |

### 4xx Client Errors

| Code | Meaning | Use Case |
|------|---------|----------|
| 400 Bad Request | Malformed request | Invalid JSON, missing required fields |
| 401 Unauthorized | Authentication required | Missing/invalid token |
| 403 Forbidden | Access denied | Valid auth but insufficient permissions |
| 404 Not Found | Resource not found | Invalid ID, deleted resource |
| 405 Method Not Allowed | HTTP method not supported | POST to read-only endpoint |
| 406 Not Acceptable | Can't satisfy Accept header | Unsupported content type |
| 408 Request Timeout | Request took too long | Client timeout |
| 409 Conflict | Resource conflict | Duplicate resource, version conflict |
| 410 Gone | Resource permanently deleted | Intentionally deleted resource |
| 412 Precondition Failed | Conditional request failed | ETag mismatch |
| 413 Payload Too Large | Request body too large | File upload exceeds limit |
| 415 Unsupported Media Type | Content-Type not supported | Wrong content type |
| 422 Unprocessable Entity | Semantic validation failed | Valid JSON but business rule violation |
| 423 Locked | Resource is locked | Resource being modified |
| 429 Too Many Requests | Rate limit exceeded | Client exceeded quota |

### 5xx Server Errors

| Code | Meaning | Use Case |
|------|---------|----------|
| 500 Internal Server Error | Generic server error | Uncaught exception |
| 501 Not Implemented | Feature not implemented | Endpoint exists but not implemented |
| 502 Bad Gateway | Upstream service failed | External API error |
| 503 Service Unavailable | Temporarily unavailable | Maintenance, overloaded |
| 504 Gateway Timeout | Upstream timeout | External API timeout |
| 507 Insufficient Storage | Storage limit reached | Disk full, quota exceeded |

---

## Versioning Examples

### URL Path Versioning (Recommended)

```http
# Simple version in path
GET /v1/users
GET /v2/users

# Version with API prefix
GET /api/v1/users
GET /api/v2/users

# Subdomain versioning
GET https://v1.api.example.com/users
GET https://v2.api.example.com/users
```

### Header Versioning

```http
# Custom header
GET /users
API-Version: 1

# Accept header (vendor media type)
GET /users
Accept: application/vnd.myapi.v1+json

# Accept header (content negotiation)
GET /users
Accept: application/json; version=1
```

### Version Deprecation Headers

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 31 Dec 2025 23:59:59 GMT
Link: <https://api.example.com/v2/users>; rel="alternate"
Warning: 299 - "API v1 is deprecated and will be removed on 2025-12-31"

{
  "data": [...],
  "_links": {
    "self": {"href": "/v1/users"},
    "current": {"href": "/v2/users"}
  }
}
```

### Migration Guide Response

```http
GET /v1/users
HTTP/1.1 200 OK
X-API-Deprecated: true
X-API-Sunset-Date: 2025-12-31
X-API-Migration-Guide: https://docs.example.com/migration/v1-to-v2

{
  "data": [...],
  "migration": {
    "current_version": "v1",
    "latest_version": "v2",
    "sunset_date": "2025-12-31",
    "migration_guide": "https://docs.example.com/migration/v1-to-v2"
  }
}
```

---

## Pagination Implementation Details

### Offset Pagination (Complete Example)

**Request:**
```http
GET /users?limit=20&offset=40&sort=-created_at
```

**Response:**
```json
{
  "data": [
    {"id": 41, "name": "User 41"},
    {"id": 42, "name": "User 42"}
  ],
  "pagination": {
    "limit": 20,
    "offset": 40,
    "total": 1000,
    "page": 3,
    "pages": 50
  },
  "links": {
    "first": "/users?limit=20&offset=0&sort=-created_at",
    "prev": "/users?limit=20&offset=20&sort=-created_at",
    "self": "/users?limit=20&offset=40&sort=-created_at",
    "next": "/users?limit=20&offset=60&sort=-created_at",
    "last": "/users?limit=20&offset=980&sort=-created_at"
  }
}
```

**SQL Implementation:**
```sql
SELECT * FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 40;

-- Count total (for pagination metadata)
SELECT COUNT(*) FROM users;
```

**Problems:**
- Large offset = slow query (skips many rows)
- COUNT(*) query expensive on large tables
- Inconsistent results if data changes between pages

### Cursor Pagination (Complete Example)

**First Request:**
```http
GET /users?limit=20&sort=-created_at
```

**Response:**
```json
{
  "data": [
    {"id": 123, "name": "User 123", "created_at": "2024-01-15T10:30:00Z"},
    {"id": 124, "name": "User 124", "created_at": "2024-01-15T10:25:00Z"}
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6MTI0LCJjcmVhdGVkX2F0IjoiMjAyNC0wMS0xNVQxMDoyNTowMFoifQ==",
    "prev_cursor": null,
    "has_more": true
  },
  "links": {
    "next": "/users?limit=20&cursor=eyJpZCI6MTI0LCJjcmVhdGVkX2F0IjoiMjAyNC0wMS0xNVQxMDoyNTowMFoifQ=="
  }
}
```

**Next Page Request:**
```http
GET /users?limit=20&cursor=eyJpZCI6MTI0LCJjcmVhdGVkX2F0IjoiMjAyNC0wMS0xNVQxMDoyNTowMFoifQ==
```

**Cursor Encoding/Decoding:**
```javascript
// Encode cursor (base64 JSON)
const cursor = {
  id: 124,
  created_at: "2024-01-15T10:25:00Z"
};
const encoded = Buffer.from(JSON.stringify(cursor)).toString('base64');
// eyJpZCI6MTI0LCJjcmVhdGVkX2F0IjoiMjAyNC0wMS0xNVQxMDoyNTowMFoifQ==

// Decode cursor
const decoded = JSON.parse(Buffer.from(encoded, 'base64').toString());
// {id: 124, created_at: "2024-01-15T10:25:00Z"}
```

**SQL Implementation:**
```sql
-- Decode cursor: {id: 124, created_at: "2024-01-15T10:25:00Z"}
SELECT * FROM users
WHERE (created_at, id) < ('2024-01-15T10:25:00Z', 124)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

**Benefits:**
- Fast regardless of position in dataset
- Consistent results (no duplicates/skips)
- Works with real-time data
- No expensive COUNT(*) query

### Keyset Pagination (High Performance)

**Request:**
```http
GET /users?limit=20&after_id=123&after_created_at=2024-01-15T10:30:00Z
```

**Response:**
```json
{
  "data": [
    {"id": 124, "name": "User 124", "created_at": "2024-01-15T10:25:00Z"}
  ],
  "pagination": {
    "limit": 20,
    "after_id": 144,
    "after_created_at": "2024-01-14T18:00:00Z",
    "has_more": true
  },
  "links": {
    "next": "/users?limit=20&after_id=144&after_created_at=2024-01-14T18:00:00Z"
  }
}
```

**SQL Implementation:**
```sql
-- Forward pagination
SELECT * FROM users
WHERE (created_at, id) < ('2024-01-15T10:30:00Z', 123)
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Backward pagination (complex)
SELECT * FROM (
  SELECT * FROM users
  WHERE (created_at, id) > ('2024-01-15T10:30:00Z', 123)
  ORDER BY created_at ASC, id ASC
  LIMIT 20
) AS reversed
ORDER BY created_at DESC, id DESC;
```

**Index Required:**
```sql
CREATE INDEX idx_users_created_at_id ON users(created_at DESC, id DESC);
```

### Pagination Comparison

| Aspect | Offset | Cursor | Keyset |
|--------|--------|--------|--------|
| **Performance (large offset)** | Slow (O(n)) | Fast (O(1)) | Fast (O(1)) |
| **Consistency** | Inconsistent | Consistent | Consistent |
| **Jump to page** | Yes | No | No |
| **Bidirectional** | Yes | Yes (complex) | Yes (complex) |
| **Total count** | Easy | Hard/expensive | Hard/expensive |
| **Implementation** | Simple | Medium | Medium |
| **Transparency** | Transparent | Opaque | Transparent |

---

## Error Response Examples by Status Code

### 400 Bad Request (Validation Errors)

```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 400,
  "detail": "Request body contains 2 validation errors",
  "instance": "/api/v1/users",
  "errors": [
    {
      "field": "email",
      "message": "Email address is invalid",
      "code": "INVALID_EMAIL",
      "value": "not-an-email"
    },
    {
      "field": "password",
      "message": "Password must be at least 8 characters",
      "code": "PASSWORD_TOO_SHORT",
      "constraint": {"min_length": 8}
    }
  ],
  "trace_id": "abc123-def456-ghi789"
}
```

### 401 Unauthorized (Missing/Invalid Token)

```json
{
  "type": "https://api.example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Authentication token is missing or invalid",
  "instance": "/api/v1/users/123",
  "error_code": "INVALID_TOKEN",
  "trace_id": "abc123-def456-ghi789"
}
```

### 403 Forbidden (Insufficient Permissions)

```json
{
  "type": "https://api.example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "You do not have permission to delete users",
  "instance": "/api/v1/users/123",
  "required_permission": "users.delete",
  "user_permissions": ["users.read", "users.write"],
  "trace_id": "abc123-def456-ghi789"
}
```

### 404 Not Found

```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "User with ID 123 does not exist",
  "instance": "/api/v1/users/123",
  "resource_type": "User",
  "resource_id": "123",
  "trace_id": "abc123-def456-ghi789"
}
```

### 409 Conflict (Duplicate Resource)

```json
{
  "type": "https://api.example.com/errors/conflict",
  "title": "Resource Conflict",
  "status": 409,
  "detail": "A user with this email address already exists",
  "instance": "/api/v1/users",
  "conflict_field": "email",
  "conflict_value": "user@example.com",
  "existing_resource_id": "456",
  "trace_id": "abc123-def456-ghi789"
}
```

### 422 Unprocessable Entity (Business Rule Violation)

```json
{
  "type": "https://api.example.com/errors/business-rule-violation",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "Cannot delete user with active orders",
  "instance": "/api/v1/users/123",
  "rule": "ACTIVE_ORDERS_EXIST",
  "rule_description": "Users with active orders cannot be deleted",
  "suggested_action": "Cancel or complete all orders before deleting user",
  "active_order_count": 3,
  "trace_id": "abc123-def456-ghi789"
}
```

### 429 Too Many Requests (Rate Limit)

```json
{
  "type": "https://api.example.com/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "You have exceeded the rate limit of 100 requests per hour",
  "instance": "/api/v1/users",
  "rate_limit": {
    "limit": 100,
    "period": "hour",
    "remaining": 0,
    "reset_at": "2024-01-15T11:00:00Z"
  },
  "retry_after": 1800,
  "trace_id": "abc123-def456-ghi789"
}
```

### 500 Internal Server Error

```json
{
  "type": "https://api.example.com/errors/internal-server-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Please contact support if the problem persists",
  "instance": "/api/v1/users",
  "trace_id": "abc123-def456-ghi789",
  "support_email": "support@example.com",
  "support_url": "https://support.example.com/contact"
}
```

### 503 Service Unavailable (Maintenance)

```json
{
  "type": "https://api.example.com/errors/service-unavailable",
  "title": "Service Unavailable",
  "status": 503,
  "detail": "The API is temporarily unavailable due to scheduled maintenance",
  "instance": "/api/v1/users",
  "maintenance_window": {
    "start": "2024-01-15T02:00:00Z",
    "end": "2024-01-15T04:00:00Z"
  },
  "retry_after": 3600,
  "trace_id": "abc123-def456-ghi789"
}
```

---

## Authentication Implementation

### JWT Implementation (Complete)

**Token Generation (Server):**
```javascript
const jwt = require('jsonwebtoken');

// Generate access token
function generateAccessToken(user) {
  return jwt.sign(
    {
      sub: user.id,
      email: user.email,
      role: user.role,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + (60 * 60) // 1 hour
    },
    process.env.JWT_SECRET,
    { algorithm: 'HS256' }
  );
}

// Generate refresh token
function generateRefreshToken(user) {
  return jwt.sign(
    {
      sub: user.id,
      type: 'refresh',
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + (30 * 24 * 60 * 60) // 30 days
    },
    process.env.JWT_REFRESH_SECRET,
    { algorithm: 'HS256' }
  );
}
```

**Authentication Endpoints:**
```javascript
// Login endpoint
POST /auth/token
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secret"
}

// Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def50200...",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "role": "admin"
  }
}

// Refresh token endpoint
POST /auth/refresh
Authorization: Bearer <refresh_token>

// Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}

// Logout (blacklist token)
POST /auth/logout
Authorization: Bearer <access_token>

// Response
{
  "message": "Successfully logged out"
}
```

**Token Verification Middleware:**
```javascript
function verifyToken(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      type: "https://api.example.com/errors/unauthorized",
      title: "Unauthorized",
      status: 401,
      detail: "Authentication token is missing"
    });
  }

  const token = authHeader.substring(7);

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({
      type: "https://api.example.com/errors/unauthorized",
      title: "Unauthorized",
      status: 401,
      detail: "Authentication token is invalid or expired"
    });
  }
}
```

### OAuth 2.0 Authorization Code Flow (Complete)

**Step 1: Authorization Request**
```http
GET /oauth/authorize?
  response_type=code&
  client_id=CLIENT_ID&
  redirect_uri=https://app.example.com/callback&
  scope=read:users+write:orders&
  state=RANDOM_STATE_STRING
```

**Step 2: User Grants Permission (HTML Form)**
```html
<!-- Authorization page shown to user -->
<form method="POST" action="/oauth/authorize">
  <h2>App Name wants to access your account</h2>
  <p>Permissions requested:</p>
  <ul>
    <li>Read your user profile</li>
    <li>Create and update orders</li>
  </ul>
  <button name="decision" value="approve">Approve</button>
  <button name="decision" value="deny">Deny</button>
</form>
```

**Step 3: Redirect with Authorization Code**
```http
HTTP/1.1 302 Found
Location: https://app.example.com/callback?code=AUTH_CODE_12345&state=RANDOM_STATE_STRING
```

**Step 4: Exchange Code for Token**
```http
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTH_CODE_12345&
redirect_uri=https://app.example.com/callback&
client_id=CLIENT_ID&
client_secret=CLIENT_SECRET
```

**Step 5: Token Response**
```json
{
  "access_token": "ya29.a0AfH6SMBx...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "1//0gKxQvEU...",
  "scope": "read:users write:orders"
}
```

**Using Access Token:**
```http
GET /api/v1/users
Authorization: Bearer ya29.a0AfH6SMBx...
```

### API Key Management

**Generate API Key:**
```http
POST /api-keys
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "name": "Production Server",
  "description": "Main production API key",
  "scopes": ["read:users", "write:orders"],
  "expires_at": "2025-12-31T23:59:59Z"
}

Response:
{
  "id": "key_abc123",
  "key": "sk_live_51H2xPqF3AbC123...",  // Only shown once!
  "name": "Production Server",
  "description": "Main production API key",
  "scopes": ["read:users", "write:orders"],
  "created_at": "2024-01-15T10:00:00Z",
  "expires_at": "2025-12-31T23:59:59Z",
  "last_used_at": null
}
```

**List API Keys:**
```http
GET /api-keys
Authorization: Bearer <user_token>

Response:
{
  "data": [
    {
      "id": "key_abc123",
      "name": "Production Server",
      "scopes": ["read:users", "write:orders"],
      "created_at": "2024-01-15T10:00:00Z",
      "last_used_at": "2024-01-15T15:30:00Z",
      "expires_at": "2025-12-31T23:59:59Z"
    }
  ]
}
```

**Revoke API Key:**
```http
DELETE /api-keys/{id}
Authorization: Bearer <user_token>

Response:
{
  "message": "API key successfully revoked"
}
```

**Using API Key:**
```http
GET /api/v1/users
X-API-Key: sk_live_51H2xPqF3AbC123...
```

---

## Complete OpenAPI Examples

### Full User Management API Spec

```yaml
openapi: 3.0.3
info:
  title: User Management API
  version: 1.0.0
  description: |
    Complete user management API with authentication, pagination, and filtering.

    ## Authentication
    This API uses JWT Bearer tokens. Obtain a token via the `/auth/token` endpoint.

    ## Rate Limiting
    - Free tier: 100 requests/hour
    - Premium tier: 1000 requests/hour

  contact:
    name: API Support
    email: api@example.com
    url: https://support.example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging.example.com/v1
    description: Staging
  - url: http://localhost:3000/v1
    description: Development

tags:
  - name: Authentication
    description: Authentication and token management
  - name: Users
    description: User management operations
  - name: Orders
    description: Order management operations

paths:
  /auth/token:
    post:
      tags:
        - Authentication
      summary: Obtain access token
      description: Exchange credentials for JWT access and refresh tokens
      operationId: login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - username
                - password
              properties:
                username:
                  type: string
                  format: email
                  example: user@example.com
                password:
                  type: string
                  format: password
                  minLength: 8
                  example: secretPassword123
      responses:
        '200':
          description: Successfully authenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
        '401':
          description: Invalid credentials
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/Error'
              examples:
                invalid_credentials:
                  value:
                    type: "https://api.example.com/errors/invalid-credentials"
                    title: "Invalid Credentials"
                    status: 401
                    detail: "Username or password is incorrect"

  /users:
    get:
      tags:
        - Users
      summary: List users
      description: Get a paginated list of users with optional filtering and sorting
      operationId: listUsers
      security:
        - BearerAuth: []
      parameters:
        - name: limit
          in: query
          description: Number of users to return
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: cursor
          in: query
          description: Pagination cursor
          schema:
            type: string
        - name: status
          in: query
          description: Filter by user status
          schema:
            type: string
            enum: [active, inactive, suspended]
        - name: role
          in: query
          description: Filter by user role
          schema:
            type: string
            enum: [admin, user, moderator]
        - name: sort
          in: query
          description: Sort field (prefix with - for descending)
          schema:
            type: string
            enum: [created_at, -created_at, name, -name]
            default: -created_at
      responses:
        '200':
          description: Successful response
          headers:
            RateLimit-Limit:
              schema:
                type: integer
              description: Request limit per hour
            RateLimit-Remaining:
              schema:
                type: integer
              description: Remaining requests in current window
            RateLimit-Reset:
              schema:
                type: integer
              description: Unix timestamp when rate limit resets
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    $ref: '#/components/schemas/CursorPagination'
        '401':
          $ref: '#/components/responses/UnauthorizedError'
        '429':
          $ref: '#/components/responses/RateLimitError'

    post:
      tags:
        - Users
      summary: Create user
      description: Create a new user account
      operationId: createUser
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: User created successfully
          headers:
            Location:
              schema:
                type: string
              description: URL of the created user
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/ValidationError'
        '401':
          $ref: '#/components/responses/UnauthorizedError'
        '409':
          description: User already exists
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/Error'

  /users/{id}:
    parameters:
      - name: id
        in: path
        required: true
        description: User ID
        schema:
          type: integer
          minimum: 1

    get:
      tags:
        - Users
      summary: Get user by ID
      description: Retrieve a single user by their ID
      operationId: getUser
      security:
        - BearerAuth: []
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          $ref: '#/components/responses/NotFoundError'

    patch:
      tags:
        - Users
      summary: Update user
      description: Partially update a user
      operationId: updateUser
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateUserRequest'
      responses:
        '200':
          description: User updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/ValidationError'
        '404':
          $ref: '#/components/responses/NotFoundError'

    delete:
      tags:
        - Users
      summary: Delete user
      description: Permanently delete a user
      operationId: deleteUser
      security:
        - BearerAuth: []
      responses:
        '204':
          description: User deleted successfully
        '404':
          $ref: '#/components/responses/NotFoundError'
        '422':
          description: Cannot delete user
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT access token obtained from /auth/token endpoint

  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
          example: 123
        email:
          type: string
          format: email
          example: user@example.com
        name:
          type: string
          example: John Doe
        role:
          type: string
          enum: [admin, user, moderator]
          example: user
        status:
          type: string
          enum: [active, inactive, suspended]
          example: active
        created_at:
          type: string
          format: date-time
          example: "2024-01-15T10:00:00Z"
        updated_at:
          type: string
          format: date-time
          example: "2024-01-15T10:00:00Z"

    CreateUserRequest:
      type: object
      required:
        - email
        - name
        - password
      properties:
        email:
          type: string
          format: email
          example: user@example.com
        name:
          type: string
          minLength: 1
          maxLength: 100
          example: John Doe
        password:
          type: string
          format: password
          minLength: 8
          example: secretPassword123
        role:
          type: string
          enum: [admin, user, moderator]
          default: user

    UpdateUserRequest:
      type: object
      properties:
        email:
          type: string
          format: email
        name:
          type: string
          minLength: 1
          maxLength: 100
        status:
          type: string
          enum: [active, inactive, suspended]

    TokenResponse:
      type: object
      properties:
        access_token:
          type: string
          example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        token_type:
          type: string
          example: Bearer
        expires_in:
          type: integer
          description: Token expiration in seconds
          example: 3600
        refresh_token:
          type: string
          example: def50200...

    CursorPagination:
      type: object
      properties:
        next_cursor:
          type: string
          nullable: true
          example: eyJpZCI6MTIzfQ==
        prev_cursor:
          type: string
          nullable: true
          example: eyJpZCI6MTAzfQ==
        has_more:
          type: boolean
          example: true

    Error:
      type: object
      required:
        - type
        - title
        - status
      properties:
        type:
          type: string
          format: uri
          example: "https://api.example.com/errors/validation-failed"
        title:
          type: string
          example: "Validation Failed"
        status:
          type: integer
          example: 400
        detail:
          type: string
          example: "One or more fields failed validation"
        instance:
          type: string
          example: "/api/v1/users"
        errors:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string
              code:
                type: string
        trace_id:
          type: string
          example: "abc123-def456-ghi789"

  responses:
    ValidationError:
      description: Validation error
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            validation_failed:
              value:
                type: "https://api.example.com/errors/validation-failed"
                title: "Validation Failed"
                status: 400
                detail: "Request body contains validation errors"
                errors:
                  - field: "email"
                    message: "Email is required"
                    code: "REQUIRED_FIELD"

    UnauthorizedError:
      description: Unauthorized
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            missing_token:
              value:
                type: "https://api.example.com/errors/unauthorized"
                title: "Unauthorized"
                status: 401
                detail: "Authentication token is missing or invalid"

    NotFoundError:
      description: Resource not found
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            user_not_found:
              value:
                type: "https://api.example.com/errors/not-found"
                title: "Not Found"
                status: 404
                detail: "User with ID 123 does not exist"

    RateLimitError:
      description: Rate limit exceeded
      headers:
        RateLimit-Limit:
          schema:
            type: integer
        RateLimit-Remaining:
          schema:
            type: integer
        RateLimit-Reset:
          schema:
            type: integer
        Retry-After:
          schema:
            type: integer
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            rate_limit_exceeded:
              value:
                type: "https://api.example.com/errors/rate-limit-exceeded"
                title: "Rate Limit Exceeded"
                status: 429
                detail: "You have exceeded the rate limit"
                retry_after: 3600

security:
  - BearerAuth: []
```

---

## Language-Specific Patterns

### Python (FastAPI)

```python
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import jwt

app = FastAPI(title="User API", version="1.0.0")
security = HTTPBearer()

# Models
class User(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    password: str

# Authentication
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Endpoints
@app.get("/v1/users", response_model=List[User])
async def list_users(
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = None,
    status: Optional[str] = Query(None, regex="^(active|inactive|suspended)$"),
    current_user: dict = Depends(verify_token)
):
    # Implementation
    pass

@app.post("/v1/users", response_model=User, status_code=201)
async def create_user(
    user: CreateUserRequest,
    current_user: dict = Depends(verify_token)
):
    # Implementation
    pass
```

### Node.js (Express)

```javascript
const express = require('express');
const jwt = require('jsonwebtoken');
const { body, query, validationResult } = require('express-validator');

const app = express();
app.use(express.json());

// Middleware
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({
      type: 'https://api.example.com/errors/unauthorized',
      title: 'Unauthorized',
      status: 401,
      detail: 'Authentication token is missing'
    });
  }

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(401).json({
        type: 'https://api.example.com/errors/unauthorized',
        title: 'Unauthorized',
        status: 401,
        detail: 'Authentication token is invalid'
      });
    }
    req.user = user;
    next();
  });
}

// Endpoints
app.get('/v1/users',
  authenticateToken,
  [
    query('limit').optional().isInt({ min: 1, max: 100 }),
    query('status').optional().isIn(['active', 'inactive', 'suspended'])
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        type: 'https://api.example.com/errors/validation-failed',
        title: 'Validation Failed',
        status: 400,
        errors: errors.array()
      });
    }

    // Implementation
  }
);

app.post('/v1/users',
  authenticateToken,
  [
    body('email').isEmail(),
    body('name').notEmpty().isLength({ max: 100 }),
    body('password').isLength({ min: 8 })
  ],
  async (req, res) => {
    // Implementation
  }
);
```

---

## Security Best Practices

### HTTPS Only

```
Always use HTTPS in production. Never send credentials over HTTP.
```

### CORS Configuration

```javascript
// Restrictive CORS (recommended)
app.use(cors({
  origin: ['https://app.example.com', 'https://admin.example.com'],
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  maxAge: 86400
}));
```

### Security Headers

```javascript
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  res.setHeader('Content-Security-Policy', "default-src 'self'");
  next();
});
```

### Input Validation

```javascript
// Always validate and sanitize input
const schema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().min(8).required(),
  name: Joi.string().max(100).required()
});

const { error, value } = schema.validate(req.body);
if (error) {
  return res.status(400).json({
    type: 'https://api.example.com/errors/validation-failed',
    title: 'Validation Failed',
    status: 400,
    errors: error.details
  });
}
```

### Password Hashing

```javascript
const bcrypt = require('bcrypt');

// Hash password
const saltRounds = 10;
const hashedPassword = await bcrypt.hash(password, saltRounds);

// Verify password
const isValid = await bcrypt.compare(password, hashedPassword);
```

### SQL Injection Prevention

```javascript
// BAD - vulnerable to SQL injection
const query = `SELECT * FROM users WHERE email = '${email}'`;

// GOOD - parameterized query
const query = 'SELECT * FROM users WHERE email = ?';
const results = await db.query(query, [email]);
```

---

## Performance Optimization

### Caching with ETag

```http
# First request
GET /users/123
HTTP/1.1 200 OK
ETag: "686897696a7c876b7e"
Cache-Control: max-age=3600

# Subsequent request
GET /users/123
If-None-Match: "686897696a7c876b7e"

# Response if not modified
HTTP/1.1 304 Not Modified
ETag: "686897696a7c876b7e"
```

### Compression

```javascript
const compression = require('compression');
app.use(compression());
```

### Field Selection

```http
# Request specific fields only
GET /users?fields=id,name,email

Response:
{
  "data": [
    {"id": 1, "name": "John", "email": "john@example.com"}
  ]
}
```

### Batch Operations

```http
POST /users/batch
[
  {"op": "create", "data": {"email": "user1@example.com", "name": "User 1"}},
  {"op": "update", "id": 123, "data": {"name": "Updated Name"}},
  {"op": "delete", "id": 456}
]

Response:
{
  "results": [
    {"op": "create", "status": "success", "id": 789},
    {"op": "update", "status": "success", "id": 123},
    {"op": "delete", "status": "success", "id": 456}
  ]
}
```

---

**End of Reference Guide**

For core patterns and quick reference, see SKILL.md
