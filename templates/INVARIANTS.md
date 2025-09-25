# Project Invariants

These rules must NEVER be violated. Each invariant includes WHY it exists and the consequences of violation.

## Security Invariants

### 1. Authentication Before Data Access
**Rule**: All data access must be preceded by authentication check
**WHY**: Security audit requirement from [incident/date]
**Consequence**: Unauthorized data exposure, compliance violation
**Example**:
```python
# ALWAYS
if not user.is_authenticated:
    raise AuthenticationError()
data = fetch_user_data(user.id)

# NEVER
data = fetch_user_data(request.user_id)  # No auth check
```

### 2. Input Validation Before Logging
**Rule**: Never log raw user input without validation
**WHY**: PII/sensitive data can leak into logs (GDPR violation risk)
**Consequence**: €20M fine, data breach notification required
**Example**:
```python
# ALWAYS
validated_input = sanitize_for_logging(user_input)
logger.info(f"Processing request: {validated_input}")

# NEVER
logger.info(f"User input: {user_input}")  # May contain passwords
```

## Performance Invariants

### 3. Database Connections in Context Managers
**Rule**: All database connections must use context managers
**WHY**: Connection leak caused 3-day outage in [date]
**Consequence**: Connection pool exhaustion, service downtime
**Example**:
```python
# ALWAYS
with get_db_connection() as conn:
    result = conn.execute(query)

# NEVER
conn = get_db_connection()
result = conn.execute(query)  # May not close on exception
```

### 4. API Calls With Timeout
**Rule**: Every external API call must have explicit timeout
**WHY**: Partner API hang brought down entire service [date]
**Consequence**: Thread starvation, cascading failures
**Example**:
```python
# ALWAYS
response = requests.get(url, timeout=30)

# NEVER
response = requests.get(url)  # Can hang forever
```

## Business Logic Invariants

### 5. [Your Domain-Specific Rule]
**Rule**: [Specific rule for your domain]
**WHY**: [Business reason or incident]
**Consequence**: [What happens if violated]
**Example**: [Show correct vs incorrect]

## Testing Invariants

### 6. Integration Tests Use Real Execution
**Rule**: Integration tests must use subprocess.run(), not mocked calls
**WHY**: Mocked tests missed critical integration bugs
**Consequence**: False confidence, production failures
**Example**:
```python
# ALWAYS
result = subprocess.run(['python', 'main.py'], capture_output=True)

# NEVER
with mock.patch('main.process'):  # Doesn't test real integration
```

---

## How to Add New Invariants

When you discover a new invariant (usually from an incident):

1. Add it to the appropriate section
2. Include the date/incident that revealed the need
3. Explain consequences clearly
4. Provide correct/incorrect examples
5. Update DECISION_MEMORY.json with the discovery

Remember: Invariants are discovered through pain. Document that pain to prevent repetition.