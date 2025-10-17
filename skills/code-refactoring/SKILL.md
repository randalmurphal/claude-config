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

## Real-World Refactoring Example

### Before: 145-line Complex Function

```python
def _accumulate_dvs_to_persistent_staging(self, scan_id: str) -> None:
    """Accumulate DVs to persistent staging for DAA grouping.

    WARNING: 145 lines, 13 branches, 57 statements
    ruff PLR0915: Too many statements
    ruff PLR0912: Too many branches
    """
    # Load DVs from cache
    dvs = self.tenable_cache.get_pending_dv_inserts()

    for dv in dvs:
        # Extract asset relationship (nested dict access)
        asset_id = dv.get('related', {}).get('assets', [])
        asset_id = str(asset_id[0]) if asset_id else None
        if not asset_id:
            self.log.warning(f"DV {dv['_id']} missing asset_id, skipping")
            continue

        # Extract KV relationships (list comprehension + join)
        kv_ids = dv.get('related', {}).get('vulnerabilities', [])
        kv_ids_str = ','.join(str(kv_id) for kv_id in kv_ids) if kv_ids else None

        # Extract solution relationship (nested dict access)
        solution_id = dv.get('related', {}).get('solution')
        solution_id = str(solution_id) if solution_id else None

        # Extract plugin metadata (multiple dict accesses)
        plugin_id = str(dv.get('data', {}).get('pluginID', ''))
        plugin_name = dv.get('data', {}).get('pluginName', '')

        # Extract severity (with default)
        severity = dv.get('data', {}).get('severity', {}).get('id', '0')

        # Extract CVEs (list join)
        cves = dv.get('data', {}).get('cve', [])
        cve_str = ','.join(cves) if cves else None

        # Extract ports/protocol (multiple fields)
        port = dv.get('data', {}).get('port')
        protocol = dv.get('data', {}).get('protocol')

        # Extract IP address (multiple sources)
        ip_address = dv.get('data', {}).get('ip')

        # Extract external flag (boolean conversion)
        is_external = dv.get('data', {}).get('externalAsset', False)

        # Extract subsidiary (list to single value)
        subsidiary_list = dv.get('info', {}).get('owner', {}).get('subsidiary', [])
        subsidiary = subsidiary_list[0] if subsidiary_list else None

        # Extract responsible party
        responsible_party_id = dv.get('info', {}).get('responsiblePartyID')
        responsible_party_id = str(responsible_party_id) if responsible_party_id else None

        # ... 80+ more lines of similar extraction logic ...

        # Finally accumulate to staging
        self.persistent_daa_staging.accumulate_dv(
            plugin_id=plugin_id,
            scan_id=scan_id,
            dv_id=str(dv['_id']),
            asset_id=asset_id,
            kv_ids=kv_ids_str,
            solution_id=solution_id,
            plugin_name=plugin_name,
            severity=severity,
            cve=cve_str,
            port=port,
            protocol=protocol,
            ip_address=ip_address,
            is_external=is_external,
            subsidiary=subsidiary,
            responsible_party_id=responsible_party_id,
            # ... 15+ more parameters ...
        )
```

**Problems**:
- 145 lines long (requires scrolling)
- 13 branches (complex control flow)
- 57 statements (too much happening)
- Mixed concerns: loading, extraction, validation, accumulation
- Deep nesting in extraction logic
- Hard to test (would need to mock entire DV structure)
- Difficult to reuse extraction logic

### After: 23-line Orchestration + Focused Helpers

```python
def _accumulate_dvs_to_persistent_staging(
    self, scan_id: str, flows_updates: dict
) -> None:
    """Accumulate DVs to persistent staging for DAA grouping.

    Clean orchestration showing WHAT happens (not HOW).
    23 lines, 2 branches, 8 statements.
    """
    dvs = self._load_pending_dvs_from_cache()

    for dv in dvs:
        metadata = self._extract_dv_metadata_for_daa(dv, scan_id, flows_updates)
        if metadata:
            self.persistent_daa_staging.accumulate_dv(**metadata)


def _load_pending_dvs_from_cache(self) -> list[dict]:
    """Load pending DV inserts from cache.

    Separate method for clarity and testing.
    """
    return self.tenable_cache.get_pending_dv_inserts()


def _extract_dv_metadata_for_daa(
    self, dv: dict, scan_id: str, flows_updates: dict
) -> dict | None:
    """Extract all metadata needed for DAA staging from DV.

    Single responsibility: coordinate extraction (calls helpers).
    """
    dv_id = str(dv['_id'])

    # Extract relationships (each helper has guard clauses)
    asset_id = self._extract_asset_id_from_dv(dv)
    if not asset_id:
        return None

    kv_ids = self._extract_kv_ids_from_dv(dv)
    solution_id = self._extract_solution_id_from_dv(dv)

    # Extract flows fields (optimization pattern)
    subsidiary, responsible_party_id = self._extract_flows_fields(
        dv, dv_id, flows_updates
    )

    # Extract plugin metadata
    plugin_id, plugin_name = self._extract_plugin_metadata(dv)

    # Extract vulnerability details
    severity = self._extract_severity(dv)
    cve_str = self._extract_cves(dv)
    port, protocol = self._extract_port_protocol(dv)

    # Extract asset context
    ip_address = self._extract_ip_address(dv)
    is_external = self._extract_is_external(dv)

    # Return all metadata as dict (clear parameter mapping)
    return {
        'plugin_id': plugin_id,
        'scan_id': scan_id,
        'dv_id': dv_id,
        'asset_id': asset_id,
        'kv_ids': kv_ids,
        'solution_id': solution_id,
        'plugin_name': plugin_name,
        'severity': severity,
        'cve': cve_str,
        'port': port,
        'protocol': protocol,
        'ip_address': ip_address,
        'is_external': is_external,
        'subsidiary': subsidiary,
        'responsible_party_id': responsible_party_id,
    }


# Focused extraction helpers (each has single responsibility)

def _extract_asset_id_from_dv(self, dv: dict) -> str | None:
    """Extract asset ID from DV relationships."""
    assets = dv.get('related', {}).get('assets', [])
    return str(assets[0]) if assets else None


def _extract_kv_ids_from_dv(self, dv: dict) -> str | None:
    """Extract KV IDs from DV relationships as comma-separated string."""
    kv_ids = dv.get('related', {}).get('vulnerabilities', [])
    return ','.join(str(kv_id) for kv_id in kv_ids) if kv_ids else None


def _extract_solution_id_from_dv(self, dv: dict) -> str | None:
    """Extract solution ID from DV relationships."""
    solution_id = dv.get('related', {}).get('solution')
    return str(solution_id) if solution_id else None


def _extract_flows_fields(
    self, dv: dict, dv_id: str, flows_updates: dict
) -> tuple[str | None, str | None]:
    """Extract subsidiary and responsible party from flows or DV data.

    Performance optimization: use flows_updates dict to avoid MongoDB query.
    """
    if dv_id in flows_updates:
        return (
            flows_updates[dv_id].get('subsidiary'),
            flows_updates[dv_id].get('responsiblePartyID'),
        )

    # Fallback to DV data
    subsidiary_list = dv.get('info', {}).get('owner', {}).get('subsidiary', [])
    subsidiary = subsidiary_list[0] if subsidiary_list else None
    responsible_party_id = dv.get('info', {}).get('responsiblePartyID')

    return subsidiary, str(responsible_party_id) if responsible_party_id else None


def _extract_plugin_metadata(self, dv: dict) -> tuple[str, str]:
    """Extract plugin ID and name from DV data."""
    plugin_id = str(dv.get('data', {}).get('pluginID', ''))
    plugin_name = dv.get('data', {}).get('pluginName', '')
    return plugin_id, plugin_name


def _extract_severity(self, dv: dict) -> str:
    """Extract severity from DV data."""
    return dv.get('data', {}).get('severity', {}).get('id', '0')


def _extract_cves(self, dv: dict) -> str | None:
    """Extract CVEs from DV data as comma-separated string."""
    cves = dv.get('data', {}).get('cve', [])
    return ','.join(cves) if cves else None


def _extract_port_protocol(self, dv: dict) -> tuple[str | None, str | None]:
    """Extract port and protocol from DV data."""
    return (
        dv.get('data', {}).get('port'),
        dv.get('data', {}).get('protocol'),
    )


def _extract_ip_address(self, dv: dict) -> str | None:
    """Extract IP address from DV data."""
    return dv.get('data', {}).get('ip')


def _extract_is_external(self, dv: dict) -> bool:
    """Extract external asset flag from DV data."""
    return dv.get('data', {}).get('externalAsset', False)
```

### Benefits of Refactoring

**Clarity**:
- Main function shows WHAT happens (load, extract, accumulate)
- Helper methods show HOW it happens (implementation details)
- No scrolling required to understand flow

**Testability**:
- Each extraction method can be tested independently
- Mock only what you need (single DV dict, not entire cache)
- Test edge cases in isolation (None values, empty lists, etc.)

**Maintainability**:
- Single responsibility per method (easy to modify)
- Reusable extraction logic (DRY principle)
- Guard clauses eliminate deep nesting

**Performance**:
- No performance penalty (function calls are cheap)
- Optimization patterns still work (_extract_flows_fields)
- Compiler may inline simple helpers

**Metrics**:
- BEFORE: 145 lines, 13 branches, 57 statements
- AFTER: 23 lines (main), 2 branches, 8 statements
- Total lines increased (~200 vs 145), but clarity improved dramatically

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

### Refactoring Workflow

1. **Establish Baseline**:
   ```bash
   # Run tests BEFORE refactoring
   pytest tests/test_module.py -v

   # All tests should pass (green)
   # If not, fix tests first
   ```

2. **Refactor Incrementally**:
   ```python
   # Extract one helper at a time
   # Run tests after each extraction
   # Ensure behavior preserved
   ```

3. **Run Tests After Each Step**:
   ```bash
   # After extracting _extract_asset_id
   pytest tests/test_module.py::test_process_record -v

   # After extracting _extract_kv_ids
   pytest tests/test_module.py::test_process_record -v
   ```

4. **Validate Final Refactoring**:
   ```bash
   # All tests should still pass
   pytest tests/test_module.py -v

   # Run linting to verify complexity reduced
   ruff check module.py
   ```

### Test Updates

**Integration tests** should still pass without changes:
- Validate end-to-end behavior preserved
- Ensure refactoring didn't break business logic

**Unit tests** may need updates:
- New helper methods should have their own tests
- Existing tests may need to mock new helpers
- Add tests for edge cases now easier to test

### Example Test Evolution

```python
# BEFORE refactoring - tests main function
def test_accumulate_dvs():
    """Test DV accumulation with full DV structure."""
    processor = Processor(config, sub_id)

    # Complex DV structure required
    dv = {
        '_id': ObjectId(),
        'related': {
            'assets': [ObjectId()],
            'vulnerabilities': [ObjectId(), ObjectId()],
            'solution': ObjectId(),
        },
        'data': {
            'pluginID': '12345',
            'pluginName': 'Test Plugin',
            # ... 20+ more fields ...
        }
    }

    # Test black box behavior
    processor._accumulate_dvs_to_persistent_staging('scan_1')
    # Assert on side effects only

# AFTER refactoring - tests helpers independently
def test_extract_asset_id_from_dv():
    """Test asset ID extraction from DV."""
    processor = Processor(config, sub_id)

    # Test with valid asset
    dv = {'related': {'assets': [ObjectId('507f1f77bcf86cd799439011')]}}
    assert processor._extract_asset_id_from_dv(dv) == '507f1f77bcf86cd799439011'

    # Test with missing asset
    dv = {'related': {}}
    assert processor._extract_asset_id_from_dv(dv) is None

    # Test with empty assets list
    dv = {'related': {'assets': []}}
    assert processor._extract_asset_id_from_dv(dv) is None

def test_extract_kv_ids_from_dv():
    """Test KV IDs extraction from DV."""
    processor = Processor(config, sub_id)

    # Test with multiple KVs
    dv = {'related': {'vulnerabilities': [ObjectId('1'), ObjectId('2')]}}
    result = processor._extract_kv_ids_from_dv(dv)
    assert '1' in result and '2' in result

    # Test with no KVs
    dv = {'related': {}}
    assert processor._extract_kv_ids_from_dv(dv) is None
```

**Benefits**:
- Focused tests easier to write and understand
- Edge cases easier to test in isolation
- Mock complexity reduced (test single concern)
- Better test coverage (each helper tested independently)

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
