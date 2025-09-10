# Project Gotchas & Hard-Learned Rules

This file documents project-specific rules, gotchas, and patterns that MUST be followed.
Each entry should be SPECIFIC and ACTIONABLE.

## Format Rules
- Each entry starts with date and brief title
- Must be specific enough to be enforced
- No vague patterns or "maybe" rules
- Maximum 20 rules (delete old ones if exceeded)

---

## [YYYY-MM-DD] - Example: Test File Location
**Rule**: Tests must go in `tests/` directory, NOT `__tests__/`
**Why**: Project uses Jest config that only looks in tests/
**Violations will cause**: Tests not found, 0% coverage reported

## [YYYY-MM-DD] - Example: Middleware Order  
**Rule**: Rate limiter middleware MUST come before auth middleware
**Why**: Auth middleware throws on invalid tokens, bypassing rate limit
**Violations will cause**: DDoS vulnerability on auth endpoints

## [YYYY-MM-DD] - Example: Database Mocking
**Rule**: NEVER mock PostgreSQL in integration tests - use real test database
**Why**: Mock behavior differs from real Postgres (especially transactions)
**Violations will cause**: Tests pass but production fails

## [YYYY-MM-DD] - Example: Error Format
**Rule**: API errors must have `.code` property (not custom error classes)
**Why**: Frontend error handler expects `error.code` for translations
**Violations will cause**: Generic error messages shown to users

---

## Anti-Patterns (NEVER DO)
- Creating interfaces with only 1 implementation
- Creating src/common/ directory with fewer than 3 consumers
- Using custom error class hierarchies instead of Error with .code
- Mocking file system or databases in integration tests

## Project-Specific Conventions
- Import order: external → internal → relative → types
- File naming: kebab-case for files, PascalCase for components
- Test naming: `*.test.ts` for unit, `*.integration.ts` for integration
- API responses: Always wrap in `{ data: ..., meta: ... }` structure