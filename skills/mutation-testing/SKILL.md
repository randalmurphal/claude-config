# Mutation Testing for Test Quality Validation

**Skill Metadata**:
- **Name**: Mutation Testing for Test Quality Validation
- **Description**: Validate test suite quality using mutation testing with mutmut or cosmic-ray to detect weak tests, calculate mutation scores, and improve test coverage. Use when validating test effectiveness, achieving high test quality, or detecting tests that pass but don't validate behavior.
- **Allowed Tools**: Read, Bash, Grep
- **Use Cases**: Test quality validation, detecting weak tests, improving test effectiveness, achieving high-quality test suites

---

## Table of Contents
1. [Mutation Testing Concept](#1-mutation-testing-concept)
2. [Tools Comparison](#2-tools-comparison)
3. [mutmut Workflow](#3-mutmut-workflow)
4. [Interpreting Results](#4-interpreting-results)
5. [Common Survived Mutations](#5-common-survived-mutations-weak-tests)
6. [Improving Mutation Score](#6-improving-mutation-score)
7. [CI/CD Integration](#7-cicd-integration)
8. [Performance Optimization](#8-performance-optimization)
9. [Limitations & Caveats](#9-limitations--caveats)
10. [Best Practices](#10-best-practices)
11. [Workflow Example](#11-workflow-example)
12. [Integration with Test Coverage](#12-integration-with-test-coverage)

---

## 1. Mutation Testing Concept

### What is Mutation Testing?

Mutation testing validates test quality by introducing small, deliberate bugs (mutations) into your code and checking if your tests catch them.

**Core Principle**: If you change working code and tests still pass, those tests aren't validating behavior properly.

### Why It Matters

**Problem**: 100% code coverage doesn't guarantee test quality.

```python
# Code with 100% coverage
def calculate_discount(price, is_member):
    if is_member:
        return price * 0.9
    return price

# Weak test (100% coverage, but doesn't validate behavior)
def test_calculate_discount():
    result = calculate_discount(100, True)
    # No assertion - test always passes!
```

This test executes all code (100% coverage) but validates nothing. Mutation testing catches this.

### Mutation Operators

Mutation testing applies these transformations:

| Operator | Example | Description |
|----------|---------|-------------|
| **Arithmetic** | `+` → `-`, `*` → `/` | Change math operators |
| **Comparison** | `==` → `!=`, `>` → `<` | Flip comparisons |
| **Boolean** | `and` → `or`, `True` → `False` | Change logic |
| **Statement deletion** | Remove line | Delete code |
| **Constant modification** | `10` → `11`, `"foo"` → `"XXfooXX"` | Modify values |
| **Return values** | `return x` → `return None` | Change returns |

### Mutation Outcomes

**Killed Mutation** (Good):
- Test fails when code is mutated
- Test correctly validates behavior
- Example: Change `price * 0.9` to `price * 0.8`, test fails because `assert result == 90`

**Survived Mutation** (Bad):
- Test passes even when code is mutated
- Test doesn't validate behavior
- Example: Change `price * 0.9` to `price * 0.8`, test still passes because no assertion

**Mutation Score**: `(Killed mutations / Total mutations) * 100%`

**Target**: 80%+ mutation score indicates high-quality tests

---

## 2. Tools Comparison

### mutmut (Recommended)

**Pros**:
- Simple installation and configuration
- Works almost out-of-the-box
- Faster execution than cosmic-ray
- Good default mutation operators
- Active maintenance

**Cons**:
- Limited customization
- Fewer mutation operators than cosmic-ray
- Single-threaded (no native parallelization)

**Installation**:
```bash
pip install mutmut
```

**Best For**: Most Python projects, getting started with mutation testing, CI/CD integration

### cosmic-ray (Advanced)

**Pros**:
- Highly customizable
- More mutation operators (30+ vs mutmut's 10)
- Distributed execution support
- Detailed reporting

**Cons**:
- Complex configuration
- Slower execution
- Steeper learning curve
- More dependencies

**Installation**:
```bash
pip install cosmic-ray
```

**Best For**: Large projects needing distributed execution, advanced mutation operators, research

### Recommendation

**Start with mutmut**, upgrade to cosmic-ray if you need:
- Custom mutation operators
- Distributed execution across multiple machines
- More granular control over mutation selection

---

## 3. mutmut Workflow

### Basic Usage

```bash
# Run mutation testing on entire project
mutmut run

# See results summary
mutmut results
# Output:
# Survived: 15
# Killed: 85
# Timeout: 2
# Suspicious: 1
# Total: 103
# Mutation score: 82.5%

# Show details of survived mutation #5
mutmut show 5

# Generate HTML report
mutmut html
```

### Targeted Testing

```bash
# Test specific file
mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/asset_processor.py

# Test specific directory
mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/

# Rerun only failed mutations
mutmut run --rerun-all

# Run with custom test command
mutmut run --runner="pytest -x tests/unit/ --tb=short"

# Run specific mutation IDs
mutmut run 5 10 15
```

### Configuration

**pyproject.toml**:
```toml
[tool.mutmut]
paths_to_mutate = "fisio/"
backup = false
runner = "pytest -x --tb=short"
tests_dir = "tests/"
dict_synonyms = "Struct, NamedStruct"
```

**setup.cfg**:
```ini
[mutmut]
paths_to_mutate=fisio/
backup=False
runner=pytest -x --tb=short
tests_dir=tests/
```

**Command-line overrides**:
```bash
# Override config settings
mutmut run --paths-to-mutate=fisio/imports/ --runner="pytest -x"
```

### Workflow Commands

```bash
# 1. Initialize (first run)
mutmut run

# 2. Review results
mutmut results

# 3. Show survived mutations
mutmut show

# 4. Fix tests to kill mutations

# 5. Rerun failed mutations
mutmut run --rerun-all

# 6. Generate report
mutmut html

# 7. Open report in browser
open html/index.html
```

---

## 4. Interpreting Results

### Mutation Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| **Killed** | Test failed (mutation caught) | ✅ GOOD - Test validates behavior |
| **Survived** | Test passed (mutation not caught) | ❌ BAD - Test doesn't validate behavior |
| **Suspicious** | Tests took too long | ⚠️ Possible infinite loop, investigate |
| **Timeout** | Mutation caused timeout | ⚠️ Check for infinite loops |
| **Skipped** | Couldn't apply mutation | ℹ️ Ignore (rare, usually syntax edge cases) |

### Mutation Score Targets

| Score | Quality | Action |
|-------|---------|--------|
| **< 50%** | Weak test suite | Major gaps, prioritize test improvements |
| **50-70%** | Moderate quality | Room for improvement, focus on critical paths |
| **70-80%** | Good quality | Few gaps, polish edge cases |
| **80-90%** | Excellent quality | High confidence, minimal improvements needed |
| **> 90%** | Exceptional | Diminishing returns, focus elsewhere |

**Target**: Aim for **80%+ mutation score** for production code.

### Reading Mutation Details

```bash
mutmut show 5
```

**Output**:
```diff
--- fisio/imports/tenable_sc_refactor/processors/asset_processor.py
+++ [Mutant] fisio/imports/tenable_sc_refactor/processors/asset_processor.py
@@ -123,7 +123,7 @@
     def calculate_match_quality(self, match_level):
-        if match_level >= 7:
+        if match_level > 7:
             return "High"
         return "Low"
```

**Analysis**:
- **Change**: `>=` → `>`
- **Status**: Survived
- **Problem**: No test validates boundary case `match_level == 7`
- **Fix**: Add test `assert calculate_match_quality(7) == "High"`

---

## 5. Common Survived Mutations (Weak Tests)

### Example 1: Missing Assertion

**Code**:
```python
def calculate_total(items):
    return sum(item.price for item in items)
```

**Weak Test** (mutation survives):
```python
def test_calculate_total():
    items = [Item(price=10), Item(price=20)]
    result = calculate_total(items)
    # NO ASSERTION - test always passes
```

**Mutation**: Change `sum(...)` to `0` → Test still passes!

**Fix**:
```python
def test_calculate_total():
    items = [Item(price=10), Item(price=20)]
    result = calculate_total(items)
    assert result == 30  # Kills mutation
```

---

### Example 2: Assertion Too Broad

**Code**:
```python
def get_severity(score):
    if score >= 7.0:
        return "High"
    return "Low"
```

**Weak Test**:
```python
def test_get_severity():
    assert get_severity(8.0) is not None  # Too broad
```

**Mutation**: Change `"High"` to `"Low"` → Test still passes!

**Fix**:
```python
def test_get_severity():
    assert get_severity(8.0) == "High"  # Exact value
    assert get_severity(5.0) == "Low"   # Both branches
    assert get_severity(7.0) == "High"  # Boundary
```

---

### Example 3: Missing Edge Cases

**Code**:
```python
def divide(a, b):
    if b == 0:
        raise ValueError("Division by zero")
    return a / b
```

**Weak Test**:
```python
def test_divide():
    assert divide(10, 2) == 5
```

**Mutations**:
- Change `==` to `!=` in `if b == 0` → Survives (no zero test)
- Change `/` to `*` → Survives (no additional test cases)

**Fix**:
```python
def test_divide():
    # Happy path
    assert divide(10, 2) == 5

    # Edge cases
    assert divide(10, 3) == 3.333...  # Float result
    assert divide(0, 5) == 0          # Zero numerator

    # Error case
    with pytest.raises(ValueError, match="Division by zero"):
        divide(5, 0)
```

---

### Example 4: Testing Implementation, Not Behavior

**Code**:
```python
def process_scan(scan_id):
    cache = {}  # Internal implementation detail
    data = fetch_data(scan_id)
    cache[scan_id] = data
    return data
```

**Weak Test** (tests implementation):
```python
def test_process_scan():
    result = process_scan(123)
    # No assertion - just checking it doesn't crash
```

**Mutation**: Remove `cache[scan_id] = data` → Test still passes!

**Fix** (test behavior):
```python
@mock.patch('module.fetch_data')
def test_process_scan(mock_fetch):
    mock_fetch.return_value = {'scan_id': 123, 'data': 'test'}

    result = process_scan(123)

    # Test behavior: correct data returned
    assert result == {'scan_id': 123, 'data': 'test'}
    # Test behavior: fetch_data called correctly
    mock_fetch.assert_called_once_with(123)
```

---

### Example 5: Incomplete Branch Coverage

**Code**:
```python
def categorize_risk(score):
    if score >= 9.0:
        return "Critical"
    elif score >= 7.0:
        return "High"
    elif score >= 4.0:
        return "Medium"
    else:
        return "Low"
```

**Weak Test**:
```python
def test_categorize_risk():
    assert categorize_risk(9.5) == "Critical"
    assert categorize_risk(2.0) == "Low"
```

**Mutations**:
- Change `>= 7.0` to `> 7.0` → Survives (no boundary test)
- Change `>= 4.0` to `> 4.0` → Survives (no Medium test)

**Fix**:
```python
def test_categorize_risk():
    # All categories
    assert categorize_risk(10.0) == "Critical"
    assert categorize_risk(8.0) == "High"
    assert categorize_risk(5.0) == "Medium"
    assert categorize_risk(2.0) == "Low"

    # Boundaries
    assert categorize_risk(9.0) == "Critical"  # Exactly 9.0
    assert categorize_risk(7.0) == "High"      # Exactly 7.0
    assert categorize_risk(4.0) == "Medium"    # Exactly 4.0
```

---

## 6. Improving Mutation Score

### Strategy 1: Add Missing Assertions

**Process**:
1. Run `mutmut results` to find survived mutations
2. Run `mutmut show <id>` to see mutation details
3. Add specific assertions to kill mutations
4. Rerun `mutmut run <id>` to verify fix

**Example**:
```bash
mutmut show 15
# Output: Mutation changed `return True` to `return False`

# Before (survived)
def test_validate_email():
    result = validate_email("test@example.com")
    # No assertion

# After (killed)
def test_validate_email():
    assert validate_email("test@example.com") is True
    assert validate_email("invalid") is False
```

---

### Strategy 2: Test Edge Cases

**Common Edge Cases**:
- **Boundary values**: 0, -1, max values, min values
- **Empty inputs**: `[]`, `{}`, `""`, `None`
- **Single-item collections**: `[1]`, `{"key": "value"}`
- **Large inputs**: Performance edge cases
- **Special characters**: Unicode, whitespace, escape sequences

**Example**:
```python
def get_first_item(items):
    if not items:
        return None
    return items[0]

# Comprehensive edge case tests
def test_get_first_item():
    # Normal case
    assert get_first_item([1, 2, 3]) == 1

    # Edge cases
    assert get_first_item([]) is None          # Empty
    assert get_first_item([42]) == 42          # Single item
    assert get_first_item([None, 1]) is None   # None as first item
```

---

### Strategy 3: Validate Behavior, Not Implementation

**Anti-pattern** (testing implementation):
```python
def test_cache_internal_state():
    processor = Processor()
    processor.process(data)
    # Testing internal cache state
    assert len(processor._cache) == 1
```

**Better** (testing behavior):
```python
def test_process_returns_correct_result():
    processor = Processor()
    result = processor.process(data)
    # Testing observable behavior
    assert result == expected_output
```

**Key Principle**: Tests should validate what the code does, not how it does it.

---

### Strategy 4: Incremental Improvement

**Workflow**:
1. **Baseline**: Run mutation testing, record score
2. **Prioritize**: Focus on critical modules first (high-value, high-risk)
3. **Iterate**: Fix 5-10 survived mutations per cycle
4. **Track**: Monitor mutation score over time
5. **Review**: Accept some survived mutations (document why)

**Tracking Example**:
```bash
# Week 1: Initial run
mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/asset_processor.py
# Mutation score: 65%

# Week 2: Fix boundary cases
mutmut run --rerun-all
# Mutation score: 72%

# Week 3: Add error case tests
mutmut run --rerun-all
# Mutation score: 81%

# Week 4: Polish edge cases
mutmut run --rerun-all
# Mutation score: 85% ✅ Target reached
```

---

### Strategy 5: Use Parametrized Tests

**Problem**: Testing multiple similar cases leads to code duplication.

**Solution**: Parametrized tests improve coverage with less code.

```python
import pytest

# Before: Multiple similar tests
def test_severity_critical():
    assert get_severity(9.0) == "Critical"

def test_severity_high():
    assert get_severity(7.0) == "High"

def test_severity_medium():
    assert get_severity(4.0) == "Medium"

# After: Parametrized test (kills more mutations)
@pytest.mark.parametrize("score,expected", [
    (10.0, "Critical"),
    (9.0, "Critical"),   # Boundary
    (8.0, "High"),
    (7.0, "High"),       # Boundary
    (5.0, "Medium"),
    (4.0, "Medium"),     # Boundary
    (2.0, "Low"),
    (0.0, "Low"),
])
def test_get_severity(score, expected):
    assert get_severity(score) == expected
```

---

## 7. CI/CD Integration

### GitHub Actions Example

**.github/workflows/mutation-testing.yml**:
```yaml
name: Mutation Testing

# Run on schedule (mutation testing is slow)
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
  workflow_dispatch:     # Manual trigger

jobs:
  mutation-testing:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install mutmut pytest

      - name: Run mutation testing
        run: |
          mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/
          mutmut results
          mutmut junitxml > mutation-results.xml

      - name: Check mutation score
        run: |
          # Custom script to parse results
          python scripts/check_mutation_score.py --threshold 80

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: mutation-results
          path: mutation-results.xml
```

---

### Mutation Score Checker Script

**scripts/check_mutation_score.py**:
```python
#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys

def get_mutation_score():
    """Parse mutmut results to get mutation score."""
    result = subprocess.run(
        ["mutmut", "results"],
        capture_output=True,
        text=True
    )

    # Parse output: "Mutation score: 82.5%"
    match = re.search(r"Mutation score: ([\d.]+)%", result.stdout)
    if match:
        return float(match.group(1))

    return 0.0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=80.0)
    args = parser.parse_args()

    score = get_mutation_score()
    print(f"Mutation score: {score}%")
    print(f"Threshold: {args.threshold}%")

    if score < args.threshold:
        print(f"❌ FAIL: Mutation score {score}% below threshold {args.threshold}%")
        sys.exit(1)

    print(f"✅ PASS: Mutation score {score}% meets threshold {args.threshold}%")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

### Incremental Mutation Testing (Changed Files Only)

**GitHub Actions example**:
```yaml
- name: Run mutation testing on changed files
  run: |
    # Get changed Python files
    CHANGED_FILES=$(git diff --name-only origin/main...HEAD | grep '\.py$' | tr '\n' ' ')

    if [ -z "$CHANGED_FILES" ]; then
      echo "No Python files changed"
      exit 0
    fi

    echo "Running mutation testing on: $CHANGED_FILES"
    mutmut run --paths-to-mutate=$CHANGED_FILES
    mutmut results
```

---

## 8. Performance Optimization

### Problem: Mutation Testing is Slow

**Example**: 1000 mutations × 10s test suite = 10,000s (~3 hours)

### Solution 1: Parallel Execution (Manual)

mutmut doesn't natively support parallelization, but you can use GNU parallel:

```bash
# Install GNU parallel
sudo apt-get install parallel

# Split files into groups
FILES=(fisio/imports/tenable_sc_refactor/processors/*.py)

# Run in parallel (4 workers)
parallel -j4 mutmut run --paths-to-mutate={} ::: "${FILES[@]}"

# Combine results (mutmut stores in .mutmut-cache)
mutmut results
```

---

### Solution 2: Incremental Testing

**Test only changed files**:
```bash
# In CI pipeline
git diff --name-only main...HEAD | grep '\.py$' | xargs mutmut run --paths-to-mutate

# Locally
mutmut run --paths-to-mutate=$(git diff --name-only HEAD~1 | grep '\.py$')
```

---

### Solution 3: Cache Mutations

mutmut caches results in `.mutmut-cache`:
- Rerun only failed mutations: `mutmut run --rerun-all`
- Speeds up subsequent runs (10x faster)

**CI setup**:
```yaml
- name: Cache mutation results
  uses: actions/cache@v3
  with:
    path: .mutmut-cache
    key: mutmut-${{ hashFiles('**/*.py') }}

- name: Run mutation testing
  run: mutmut run --rerun-all  # Only rerun failed mutations
```

---

### Solution 4: Targeted Testing

**Test critical modules only**:
```bash
# High-value modules
mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/asset_processor.py

# Skip low-value modules (e.g., CLI argument parsing)
mutmut run --paths-to-mutate=fisio/ --paths-to-exclude=fisio/common/cmd.py
```

---

### Solution 5: Fast Test Suite

**Optimize test execution**:
```bash
# Use pytest-xdist for parallel test execution
pip install pytest-xdist

# Configure mutmut to use parallel pytest
mutmut run --runner="pytest -n auto -x --tb=short"
```

**Fast test subset**:
```bash
# Run only unit tests (skip slow integration tests)
mutmut run --runner="pytest tests/unit/ -x"
```

---

## 9. Limitations & Caveats

### Limitation 1: Slow Execution

**Problem**: Mutation testing is inherently slow.

**Impact**: 1000 mutations × 10s test suite = ~3 hours

**Mitigation**:
- Run on nightly builds, not every commit
- Use incremental testing (changed files only)
- Parallelize execution
- Optimize test suite performance

---

### Limitation 2: Equivalent Mutations

**Problem**: Some mutations don't change behavior.

**Example**:
```python
# Original
i += 1

# Mutation (logically equivalent)
i = i + 1
```

Both are functionally identical, but mutation testing marks this as "survived".

**Impact**: False positives inflate survived mutation count.

**Mitigation**:
- Manual review of survived mutations
- Accept some survived mutations (document why)
- Focus on mutation score trends, not absolute numbers

---

### Limitation 3: High False Positive Rate

**Problem**: Not all survived mutations indicate weak tests.

**Examples**:
- Equivalent mutations (see above)
- Defensive code never executed in practice
- Logging statements (mutation doesn't affect behavior)

**Example**:
```python
def process_data(data):
    LOG.debug("Processing %d items", len(data))  # Mutation survives
    return [transform(item) for item in data]
```

Mutating the log message doesn't affect behavior, so mutation survives.

**Mitigation**:
- Review survived mutations manually
- Exclude logging/debug code from mutation testing
- Document accepted survived mutations

---

### Limitation 4: Doesn't Replace Code Coverage

**Problem**: Mutation testing complements coverage, doesn't replace it.

**Why**:
- Coverage finds untested code
- Mutation testing finds weak tests
- Both needed for comprehensive quality

**Best Practice**: Require both 95% coverage AND 80% mutation score.

---

### Limitation 5: Limited to Unit Tests

**Problem**: Mutation testing works best on unit tests, not integration tests.

**Why**: Integration tests are slow, making mutation testing impractical.

**Best Practice**: Run mutation testing on unit tests only.

---

## 10. Best Practices

### 1. Start Small

**Anti-pattern**: Run mutation testing on entire codebase immediately.

**Better**: Test one critical module, expand gradually.

```bash
# Week 1: Critical processor
mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/asset_processor.py

# Week 2: Add another processor
mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/

# Week 3: Expand to all processors
mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/
```

---

### 2. Iterate on Improvements

**Process**:
1. Run mutation testing
2. Fix 5-10 survived mutations
3. Rerun to verify fixes
4. Repeat until target score reached

**Don't**: Try to fix all survived mutations at once (overwhelming).

---

### 3. Track Score Over Time

**Use trend analysis**:
```bash
# Track in spreadsheet or dashboard
Date       | Module                | Mutation Score
-----------|----------------------|---------------
2025-10-01 | asset_processor.py   | 65%
2025-10-08 | asset_processor.py   | 72%
2025-10-15 | asset_processor.py   | 81%
2025-10-22 | asset_processor.py   | 85% ✅
```

**Goal**: Gradual improvement, not perfection immediately.

---

### 4. Combine with Coverage

**Quality gate**:
```bash
# Step 1: Check line coverage
pytest --cov=fisio --cov-report=term --cov-fail-under=95

# Step 2: Check mutation score
mutmut run
python scripts/check_mutation_score.py --threshold=80

# Both must pass
```

**Why**: Coverage finds untested code, mutation testing finds weak tests.

---

### 5. Run Off-Peak

**Problem**: Mutation testing is CPU-intensive.

**Solution**: Run during low-load periods.

**Examples**:
- Nightly builds (2 AM)
- Weekends
- Dedicated CI runners
- Developer's lunch break

---

### 6. Review Manually

**Don't**: Blindly try to kill all survived mutations.

**Do**: Review survived mutations, assess if they matter.

**Example**:
```python
# Survived mutation: LOG.debug("Processing") → LOG.debug("XXProcessingXX")
# Assessment: Logging mutation, doesn't affect behavior
# Action: Document as accepted survived mutation
```

---

### 7. Document Exceptions

**Create `.mutmut-exceptions.md`**:
```markdown
# Accepted Survived Mutations

## Mutation #42: Logging statement
- **File**: asset_processor.py:123
- **Mutation**: Changed log message
- **Reason**: Logging doesn't affect behavior
- **Reviewed**: 2025-10-17

## Mutation #55: Defensive code
- **File**: asset_processor.py:234
- **Mutation**: Removed defensive None check
- **Reason**: Never None in practice (validated upstream)
- **Reviewed**: 2025-10-17
```

---

### 8. Set Realistic Targets

**Don't**: Aim for 100% mutation score (diminishing returns).

**Do**: Set 80% target, accept some survived mutations.

**Why**: 90%+ requires disproportionate effort for minimal benefit.

---

### 9. Focus on Critical Code

**Prioritize**:
- Security-sensitive code
- Business logic
- Data processing pipelines
- Error handling

**Deprioritize**:
- CLI argument parsing
- Logging
- Configuration loading
- Simple getters/setters

---

### 10. Automate in CI/CD

**Don't**: Rely on developers to run mutation testing manually.

**Do**: Integrate in CI pipeline (nightly builds).

**Why**: Automated checks prevent regression, ensure consistent quality.

---

## 11. Workflow Example

### End-to-End Mutation Testing Workflow

```bash
# Step 1: Run mutation testing on target module
cd /home/rmurphy/repos/m32rimm/fisio
source /opt/envs/imports/bin/activate

mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/asset_processor.py

# Output:
# - Mutations: 103
# - Killed: 50
# - Survived: 10
# - Timeout: 2
# - Suspicious: 1
# - Skipped: 40
# - Mutation score: 79.4%

# Step 2: View results summary
mutmut results

# Step 3: Review first survived mutation
mutmut show 1

# Output:
# --- asset_processor.py
# +++ [Mutant] asset_processor.py
# @@ -123,7 +123,7 @@
#      def calculate_match_quality(self, match_level):
# -        if match_level >= 7:
# +        if match_level > 7:
#              return "High"
#          return "Low"

# Analysis: No test validates boundary case (match_level == 7)

# Step 4: Fix test to kill mutation
# Edit tests/test_imports/test_tenable_sc_refactor/test_asset_processor.py

# Add test:
def test_calculate_match_quality_boundary():
    processor = AssetProcessor(...)
    assert processor.calculate_match_quality(7) == "High"  # Kills mutation
    assert processor.calculate_match_quality(6) == "Low"

# Step 5: Rerun specific mutation to verify fix
mutmut run 1

# Output: Mutation #1 killed ✅

# Step 6: Review next survived mutation
mutmut show 2

# Step 7: Repeat until mutation score >= 80%

# Step 8: Generate HTML report
mutmut html

# Step 9: Open report in browser
firefox html/index.html

# Step 10: Document accepted survived mutations
echo "## Mutation #42: Logging statement" >> .mutmut-exceptions.md
```

---

### Incremental Improvement Workflow

```bash
# Baseline (Week 1)
mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/asset_processor.py
# Score: 65%

# Iteration 1 (Week 2): Fix boundary cases
mutmut show  # Review all survived mutations
# Fix 5-10 boundary case tests
mutmut run --rerun-all
# Score: 72%

# Iteration 2 (Week 3): Add error case tests
# Add tests for ValueError, TypeError, edge cases
mutmut run --rerun-all
# Score: 81% ✅ Target reached

# Iteration 3 (Week 4): Polish remaining mutations
# Review remaining survived mutations
# Accept some (document in .mutmut-exceptions.md)
# Fix critical gaps
mutmut run --rerun-all
# Score: 85%
```

---

## 12. Integration with Test Coverage

### Combined Quality Gate

**Strategy**: Require BOTH high coverage AND high mutation score.

```bash
#!/bin/bash
# scripts/quality_gate.sh

set -e  # Exit on first failure

echo "Running quality gate checks..."

# Step 1: Check line coverage
echo "Checking line coverage..."
pytest --cov=fisio/imports/tenable_sc_refactor --cov-report=term --cov-fail-under=95
echo "✅ Line coverage >= 95%"

# Step 2: Check mutation score
echo "Running mutation testing..."
mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/

echo "Checking mutation score..."
python scripts/check_mutation_score.py --threshold=80
echo "✅ Mutation score >= 80%"

echo "✅ All quality gates passed!"
```

---

### Coverage vs Mutation Testing

| Metric | What It Measures | Limitation | Best For |
|--------|------------------|------------|----------|
| **Line Coverage** | % of code executed by tests | Doesn't validate behavior | Finding untested code |
| **Branch Coverage** | % of branches executed | Doesn't validate outcomes | Finding untested paths |
| **Mutation Score** | % of mutations killed | Slow, false positives | Validating test quality |

**Complementary Metrics**:
- **Coverage** finds gaps (what's NOT tested)
- **Mutation testing** finds weakness (what's POORLY tested)

---

### Example: High Coverage, Low Mutation Score

```python
# Code
def calculate_discount(price, is_member):
    if is_member:
        return price * 0.9
    return price

# Weak test (100% coverage, 0% mutation score)
def test_calculate_discount():
    calculate_discount(100, True)
    calculate_discount(100, False)
    # No assertions - 100% coverage, but tests validate nothing!
```

**Coverage report**: 100% (both branches executed)
**Mutation score**: 0% (all mutations survive)

**Fix**:
```python
def test_calculate_discount():
    assert calculate_discount(100, True) == 90   # Kills mutations
    assert calculate_discount(100, False) == 100
```

**Coverage report**: 100%
**Mutation score**: 100% ✅

---

### Quality Metrics Dashboard

**Track both metrics over time**:
```
Module: asset_processor.py

Date       | Line Cov | Branch Cov | Mutation Score | Quality
-----------|----------|------------|----------------|--------
2025-10-01 | 95%      | 88%        | 65%            | ⚠️
2025-10-08 | 96%      | 90%        | 72%            | ⚠️
2025-10-15 | 97%      | 92%        | 81%            | ✅
2025-10-22 | 98%      | 94%        | 85%            | ✅
```

**Target**: 95%+ coverage AND 80%+ mutation score.

---

## M32RIMM-Specific Recommendations

### Critical Modules for Mutation Testing

**Priority 1** (High-value, high-risk):
- `fisio/imports/tenable_sc_refactor/processors/asset_processor.py`
- `fisio/imports/tenable_sc_refactor/processors/detected_vuln_processor.py`
- `fisio/imports/tenable_sc_refactor/processors/known_vuln_processor.py`

**Priority 2** (Important logic):
- `fisio/imports/tenable_sc_refactor/processors/solution_processor.py`
- `fisio/imports/tenable_sc_refactor/processors/daa_processor.py`
- `fisio/imports/tenable_sc_refactor/processors/application_processor.py`

**Priority 3** (Supporting logic):
- `fisio/imports/tenable_sc_refactor/cache/tenable_sc_cache.py`
- `fisio/imports/tenable_sc_refactor/api_handler/download_manager.py`

---

### CI/CD Integration for M32RIMM

**Nightly mutation testing**:
```yaml
# .github/workflows/nightly-mutation-testing.yml
name: Nightly Mutation Testing

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  mutation-testing:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m venv /opt/envs/imports
          source /opt/envs/imports/bin/activate
          pip install -r requirements.txt
          pip install mutmut

      - name: Run mutation testing (Priority 1)
        run: |
          source /opt/envs/imports/bin/activate
          cd fisio
          mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/asset_processor.py
          mutmut results

      - name: Check mutation score
        run: |
          source /opt/envs/imports/bin/activate
          python scripts/check_mutation_score.py --threshold 80
```

---

### Target Mutation Scores

| Module | Target Score | Rationale |
|--------|--------------|-----------|
| **Critical processors** (asset, DV, KV) | 85%+ | High-value, high-risk code |
| **Supporting processors** (solution, DAA, app) | 80%+ | Important business logic |
| **Cache/API handlers** | 75%+ | Less critical, more I/O-bound |
| **Utilities** | 70%+ | Simple helper functions |

---

### Workflow for M32RIMM

```bash
# 1. Weekly mutation testing on critical modules
cd /home/rmurphy/repos/m32rimm/fisio
source /opt/envs/imports/bin/activate

mutmut run --paths-to-mutate=fisio/imports/tenable_sc_refactor/processors/asset_processor.py

# 2. Review survived mutations
mutmut show

# 3. Fix weak tests incrementally
# (5-10 mutations per week)

# 4. Track progress
echo "$(date): Mutation score $(mutmut results | grep 'Mutation score')" >> mutation_tracking.log

# 5. Monthly review
# Accept remaining survived mutations (document why)
```

---

## Summary

**Mutation Testing in 5 Steps**:

1. **Run**: `mutmut run --paths-to-mutate=your_module.py`
2. **Review**: `mutmut show` to see survived mutations
3. **Fix**: Add assertions to kill mutations
4. **Verify**: `mutmut run --rerun-all`
5. **Track**: Monitor mutation score over time

**Key Takeaways**:
- **Mutation testing validates test quality**, not code quality
- **Target 80%+ mutation score** for production code
- **Combine with 95%+ code coverage** for comprehensive quality
- **Run in nightly builds** (too slow for every commit)
- **Review survived mutations manually** (some are false positives)
- **Start small, iterate** (critical modules first)

**Tools**:
- **mutmut**: Recommended for most projects (simple, fast)
- **cosmic-ray**: Advanced users needing customization

**Remember**: 100% coverage doesn't mean 100% quality. Mutation testing finds the gap.
