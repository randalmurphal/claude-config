# Code Refactoring Reference Guide

**Companion to SKILL.md** - Detailed real-world examples, comprehensive testing strategies, and deep-dive pattern demonstrations.

## Table of Contents

1. [Real-World Refactoring Example](#real-world-refactoring-example)
2. [Testing During Refactoring](#testing-during-refactoring)

---

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

---

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

---

## Pattern Deep Dives

### Extract Method Pattern - Extended

The extract method pattern is most effective when you:

1. **Identify cohesive blocks** - Look for sections that do one thing
2. **Name by intent** - Use verbs that describe what, not how
3. **Keep parameters focused** - Pass only what's needed
4. **Return clearly** - Single return type per function

**Signs you need extract method**:
- Comments explaining what a block does (the function name should explain it)
- Nested loops or conditionals making logic hard to follow
- Duplicate code patterns across functions
- Testing requires setting up unrelated state

### Guard Clause Pattern - Extended

Guard clauses move validation to the top of functions, reducing cognitive load:

```python
# BEFORE - nested validation
def process_payment(user, amount, method):
    if user:
        if user.is_active:
            if amount > 0:
                if method in ['card', 'bank']:
                    # 50 lines of payment logic
                    return success
                else:
                    return error("Invalid method")
            else:
                return error("Invalid amount")
        else:
            return error("User inactive")
    else:
        return error("No user")

# AFTER - guard clauses
def process_payment(user, amount, method):
    # Validate preconditions early
    if not user:
        return error("No user")
    if not user.is_active:
        return error("User inactive")
    if amount <= 0:
        return error("Invalid amount")
    if method not in ['card', 'bank']:
        return error("Invalid method")

    # Happy path at top level (easy to read)
    # 50 lines of payment logic
    return success
```

**Benefits**:
- Happy path is at the top level (no nesting)
- Preconditions are explicit and ordered
- Easy to add new validations
- Testing edge cases is straightforward

### Extract Variable Pattern - Extended

Extract variable pattern is about naming intentions:

```python
# BEFORE - implicit logic
if (order['status'] == 'pending' and
    order['created_at'] < datetime.now() - timedelta(hours=24) and
    order['payment']['method'] == 'invoice' and
    order['customer']['tier'] == 'enterprise'):
    send_reminder()

# AFTER - explicit intentions
is_pending = order['status'] == 'pending'
is_old_enough = order['created_at'] < datetime.now() - timedelta(hours=24)
is_invoice_payment = order['payment']['method'] == 'invoice'
is_enterprise = order['customer']['tier'] == 'enterprise'

should_send_reminder = (
    is_pending and
    is_old_enough and
    is_invoice_payment and
    is_enterprise
)

if should_send_reminder:
    send_reminder()
```

**When to use**:
- Complex boolean expressions
- Nested dictionary access
- Calculations used multiple times
- Unclear business logic

---

## Summary

**Real-world refactoring** often means:
- Increasing total line count for clarity
- Creating many small helper functions
- Trading brevity for understandability
- Making testing easier, not harder

**Testing during refactoring** is non-negotiable:
- Establish baseline before starting
- Validate after each extraction
- Update tests to match new structure
- Ensure behavior preservation throughout

**Reference this guide** when:
- Facing complex refactoring decisions
- Need examples of complete refactoring workflows
- Writing tests for refactored code
- Teaching refactoring patterns to others
