---
name: Code Refactoring Patterns
description: When and how to refactor complex functions including complexity thresholds (50+ statements, 12+ branches), extraction patterns, guard clauses, and testing strategies. Use when ruff/pylint complexity warnings appear or code becomes hard to maintain.
allowed-tools: Read, Grep, Bash
---

# Code Refactoring Patterns

## When to Refactor (Triggers)

Refactor when you observe these warning signs:

1. **Complexity Warnings from Linters**:
   - `ruff PLR0915`: Function has too many statements (>50)
   - `ruff PLR0912`: Function has too many branches (>12)
   - `ruff C901`: McCabe complexity too high (>10)

2. **Code Smells**:
   - Multiple distinct responsibilities mixed together
   - Deep nesting (>3 levels) makes logic hard to follow
   - Duplicate code patterns (DRY violations)
   - Code is hard to test (tight coupling, hidden dependencies)
   - Function exceeds ~100 lines or requires scrolling to understand

3. **Development Pain Points**:
   - Adding new features requires touching many parts of same function
   - Debugging requires mental juggling of multiple concerns
   - Writing tests requires mocking too many things
   - Code reviews generate confusion or "what does this do?" questions

## When NOT to Refactor

Don't refactor in these situations:

1. **Code is Already Clear**:
   - Function is straightforward and easy to understand
   - Refactoring would not improve clarity
   - Current structure matches mental model perfectly

2. **No Real Benefit**:
   - Refactoring just to hit arbitrary metrics
   - Making code more "clever" without improving readability
   - Creating abstractions that obscure rather than clarify

3. **Wrong Timing**:
   - During time-sensitive bug fixes (refactor separately later)
   - When tests don't exist (write tests first, then refactor)
   - Making changes without understanding the code's purpose

4. **Over-Engineering**:
   - Creating patterns for problems that don't exist
   - Abstracting before you have 2+ use cases
   - Trading simplicity for theoretical flexibility

**Remember**: Refactor to improve clarity and maintainability, not to satisfy arbitrary rules.

## How to Refactor (Patterns)

### 1. Extract Method Pattern

Pull out focused helper functions with single responsibilities:

```python
# BEFORE - mixed responsibilities
def process_data(data):
    # Validate
    if not data:
        return None
    if not isinstance(data, dict):
        return None

    # Extract fields
    field1 = data.get('field1')
    field2 = data.get('field2')

    # Transform
    result = {
        'transformed_field1': field1.upper() if field1 else None,
        'transformed_field2': int(field2) if field2 else 0,
    }

    return result

# AFTER - single responsibility per function
def process_data(data):
    """Orchestrate data processing."""
    if not _is_valid_data(data):
        return None

    fields = _extract_fields(data)
    return _transform_fields(fields)

def _is_valid_data(data) -> bool:
    """Validate data structure."""
    return bool(data) and isinstance(data, dict)

def _extract_fields(data: dict) -> dict:
    """Extract required fields from data."""
    return {
        'field1': data.get('field1'),
        'field2': data.get('field2'),
    }

def _transform_fields(fields: dict) -> dict:
    """Transform fields to output format."""
    return {
        'transformed_field1': fields['field1'].upper() if fields['field1'] else None,
        'transformed_field2': int(fields['field2']) if fields['field2'] else 0,
    }
```

### 2. Guard Clause Pattern

Replace nested conditionals with early returns:

```python
# BEFORE - deep nesting
def process_record(record):
    if record:
        if record.get('type') == 'valid':
            if record.get('status') == 'active':
                # ... 50 lines of processing ...
                return result
            else:
                return None
        else:
            return None
    else:
        return None

# AFTER - guard clauses
def process_record(record):
    # Early returns reduce nesting
    if not record:
        return None
    if record.get('type') != 'valid':
        return None
    if record.get('status') != 'active':
        return None

    # Main logic at top level (easy to read)
    # ... 50 lines of processing ...
    return result
```

### 3. Extract Variable Pattern

Name complex expressions for clarity:

```python
# BEFORE - complex expression
if (user.get('status') == 'active' and
    user.get('permissions', {}).get('admin', False) and
    not user.get('suspended', False)):
    grant_access()

# AFTER - named expression
is_active_user = user.get('status') == 'active'
has_admin_permissions = user.get('permissions', {}).get('admin', False)
is_not_suspended = not user.get('suspended', False)

if is_active_user and has_admin_permissions and is_not_suspended:
    grant_access()
```

### 4. Extract Metadata Pattern

Pull out complex data extraction logic:

```python
# BEFORE - extraction mixed with business logic
def create_record(data):
    # Extract relationships (15 lines)
    asset_id = data.get('related', {}).get('assets', [])
    asset_id = str(asset_id[0]) if asset_id else None

    kv_ids = data.get('related', {}).get('vulnerabilities', [])
    kv_ids_str = ','.join(str(kv_id) for kv_id in kv_ids) if kv_ids else None

    solution_id = data.get('related', {}).get('solution')
    solution_id = str(solution_id) if solution_id else None

    # Business logic (20 lines)
    if not asset_id:
        return None
    # ... more logic ...

# AFTER - extraction separated
def create_record(data):
    """Orchestrate record creation."""
    metadata = _extract_record_metadata(data)
    if not metadata:
        return None

    return _build_record(metadata)

def _extract_record_metadata(data: dict) -> dict | None:
    """Extract all metadata needed for record creation."""
    asset_id = _extract_asset_id(data)
    if not asset_id:
        return None

    return {
        'asset_id': asset_id,
        'kv_ids': _extract_kv_ids(data),
        'solution_id': _extract_solution_id(data),
    }

def _extract_asset_id(data: dict) -> str | None:
    """Extract asset ID from relationships."""
    assets = data.get('related', {}).get('assets', [])
    return str(assets[0]) if assets else None

def _extract_kv_ids(data: dict) -> str | None:
    """Extract KV IDs from relationships."""
    kv_ids = data.get('related', {}).get('vulnerabilities', [])
    return ','.join(str(kv_id) for kv_id in kv_ids) if kv_ids else None

def _extract_solution_id(data: dict) -> str | None:
    """Extract solution ID from relationships."""
    solution_id = data.get('related', {}).get('solution')
    return str(solution_id) if solution_id else None
```

## Real-World Examples

For detailed real-world refactoring examples with complete before/after code, see [reference.md](reference.md).

**Quick summary**:
- 145-line function reduced to 23-line orchestration + focused helpers
- Metrics: 13 branches -> 2 branches, 57 statements -> 8 statements
- Benefits: Improved clarity, testability, maintainability with no performance penalty

## Complexity Thresholds

### Ruff Complexity Rules

When these warnings appear, consider refactoring:

1. **PLR0915: Too many statements (>50)**
   ```
   Function has too many statements (57/50)
   ```
   - **Fix**: Extract methods to reduce statement count
   - **Goal**: Main function should orchestrate, not implement

2. **PLR0912: Too many branches (>12)**
   ```
   Function has too many branches (13/12)
   ```
   - **Fix**: Extract conditional logic into helpers
   - **Goal**: Reduce if/elif/else complexity

3. **C901: McCabe complexity too high (>10)**
   ```
   Function is too complex (15/10)
   ```
   - **Fix**: Break into smaller functions with single paths
   - **Goal**: Linear flow with minimal branching

### What These Metrics Mean

- **Statements**: Lines of executable code (not comments/blank lines)
- **Branches**: if/elif/else/for/while control flow points
- **McCabe Complexity**: Number of independent paths through code

**High metrics indicate**:
- Function doing too much (multiple responsibilities)
- Deep nesting (control flow hard to follow)
- Testing difficulty (too many paths to cover)

## Testing During Refactoring

**Critical workflow**:
1. Run tests BEFORE refactoring (establish baseline)
2. Refactor incrementally (one extraction at a time)
3. Run tests after each step (validate behavior preserved)
4. Verify linting passes (complexity reduced)

**Test updates**:
- Integration tests should pass without changes (behavior preserved)
- Unit tests may need updates (new helpers need tests)
- Test extraction helpers independently (easier mocking, focused tests)

**For detailed testing workflow and examples**, see [reference.md](reference.md#testing-during-refactoring).

## Common Refactoring Patterns Checklist

Before refactoring, ask yourself:

- [ ] Does this function have >50 statements?
- [ ] Does this function have >12 branches?
- [ ] Is the function hard to understand without scrolling?
- [ ] Are there multiple distinct responsibilities?
- [ ] Is nesting depth >3 levels?
- [ ] Would extraction improve clarity?

During refactoring:

- [ ] Tests pass before refactoring (baseline)
- [ ] Extract methods one at a time (incremental)
- [ ] Run tests after each extraction (validation)
- [ ] Use guard clauses to reduce nesting
- [ ] Give helpers descriptive names (intention-revealing)
- [ ] Each helper has single responsibility
- [ ] Main function is orchestration only

After refactoring:

- [ ] All tests still pass (behavior preserved)
- [ ] Linting passes (ruff/pylint clean)
- [ ] Code is more readable than before
- [ ] Complexity metrics improved
- [ ] No performance regression
- [ ] New helpers have tests (if complex)

## Anti-Patterns to Avoid

**Don't**:
- Refactor to hit arbitrary metrics (refactor for clarity)
- Extract single-use helpers that obscure flow
- Create abstractions before you need them (YAGNI)
- Refactor without tests (write tests first)
- Change behavior during refactoring (preserve semantics)
- Create deep helper hierarchies (keep it flat)

**Do**:
- Refactor when complexity impacts understanding
- Extract reusable logic (DRY principle)
- Use guard clauses to eliminate nesting
- Keep main function as clear orchestration
- Preserve behavior (tests should still pass)
- Add tests for new helpers (if non-trivial)

## Summary

**When to refactor**: Complexity warnings, code smells, development pain
**When NOT to refactor**: Code is clear, no benefit, wrong timing
**How to refactor**: Extract methods, guard clauses, extract variables
**Testing**: Run before, during, and after - preserve behavior
**Goal**: Improve clarity and maintainability, not satisfy arbitrary metrics

**The Golden Rule**: If refactoring makes code harder to understand, you're doing it wrong. The goal is clarity, not complexity metrics.
