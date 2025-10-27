# Mutation Testing Reference Guide

**Companion to SKILL.md** - Detailed workflows, comprehensive examples, and advanced strategies.

## Table of Contents
1. [Common Survived Mutations](#1-common-survived-mutations-weak-tests)
2. [Improving Mutation Score](#2-improving-mutation-score)
3. [CI/CD Integration](#3-cicd-integration)
4. [Performance Optimization](#4-performance-optimization)
5. [Workflow Examples](#5-workflow-examples)
6. [Integration with Test Coverage](#6-integration-with-test-coverage)
7. [Project-Specific Recommendations](#7-project-specific-recommendations)

---

## 1. Common Survived Mutations (Weak Tests)

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

## 2. Improving Mutation Score

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
mutmut run --paths-to-mutate=src/processors/asset_processor.py
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

## 3. CI/CD Integration

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
          mutmut run --paths-to-mutate=src/processors/
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

## 4. Performance Optimization

### Problem: Mutation Testing is Slow

**Example**: 1000 mutations × 10s test suite = 10,000s (~3 hours)

### Solution 1: Parallel Execution (Manual)

mutmut doesn't natively support parallelization, but you can use GNU parallel:

```bash
# Install GNU parallel
sudo apt-get install parallel

# Split files into groups
FILES=(src/processors/*.py)

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
mutmut run --paths-to-mutate=src/processors/asset_processor.py

# Skip low-value modules (e.g., CLI argument parsing)
mutmut run --paths-to-mutate=src/ --paths-to-exclude=src/common/cmd.py
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

## 5. Workflow Examples

### End-to-End Mutation Testing Workflow

```bash
# Step 1: Run mutation testing on target module
cd /path/to/project
source venv/bin/activate

mutmut run --paths-to-mutate=src/processors/asset_processor.py

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
# Edit tests/test_asset_processor.py

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
mutmut run --paths-to-mutate=src/processors/asset_processor.py
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

## 6. Integration with Test Coverage

### Combined Quality Gate

**Strategy**: Require BOTH high coverage AND high mutation score.

```bash
#!/bin/bash
# scripts/quality_gate.sh

set -e  # Exit on first failure

echo "Running quality gate checks..."

# Step 1: Check line coverage
echo "Checking line coverage..."
pytest --cov=src --cov-report=term --cov-fail-under=95
echo "✅ Line coverage >= 95%"

# Step 2: Check mutation score
echo "Running mutation testing..."
mutmut run --paths-to-mutate=src/processors/

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

## 7. Project-Specific Recommendations

### Example Project Structure

**Critical Modules for Mutation Testing** (adjust for your project):

**Priority 1** (High-value, high-risk):
- Core business logic processors
- Data transformation modules
- Security-sensitive components

**Priority 2** (Important logic):
- Supporting business logic
- Data validation modules
- API handlers

**Priority 3** (Supporting logic):
- Caching layers
- Download managers
- Utility functions

---

### CI/CD Integration Example

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
          python3 -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
          pip install mutmut

      - name: Run mutation testing (Priority 1)
        run: |
          source venv/bin/activate
          mutmut run --paths-to-mutate=src/processors/asset_processor.py
          mutmut results

      - name: Check mutation score
        run: |
          source venv/bin/activate
          python scripts/check_mutation_score.py --threshold 80
```

---

### Target Mutation Scores

| Module Type | Target Score | Rationale |
|-------------|--------------|-----------|
| **Critical processors/logic** | 85%+ | High-value, high-risk code |
| **Supporting processors/logic** | 80%+ | Important business logic |
| **Cache/API handlers** | 75%+ | Less critical, more I/O-bound |
| **Utilities** | 70%+ | Simple helper functions |

---

### Workflow Template

```bash
# 1. Weekly mutation testing on critical modules
cd /path/to/project
source venv/bin/activate

mutmut run --paths-to-mutate=src/processors/asset_processor.py

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

**For quick reference and core concepts, see SKILL.md**

This reference provides:
- Detailed examples of common mutation survival patterns
- Comprehensive strategies for improving mutation scores
- Complete CI/CD integration templates
- Performance optimization techniques
- End-to-end workflow examples
- Coverage integration strategies
- Project-specific customization templates

**Remember**: Mutation testing validates test quality, not code quality. Use it to find weak tests that pass but don't validate behavior.
