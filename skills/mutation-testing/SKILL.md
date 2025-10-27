---
name: mutation-testing
description: Validate test suite quality using mutation testing with mutmut or cosmic-ray to detect weak tests, calculate mutation scores, and improve test coverage. Use when validating test effectiveness, achieving high test quality, or detecting tests that pass but don't validate behavior.
allowed-tools:
  - Read
  - Bash
  - Grep
---

# Mutation Testing for Test Quality Validation

## Table of Contents
1. [Mutation Testing Concept](#1-mutation-testing-concept)
2. [Tools Comparison](#2-tools-comparison)
3. [mutmut Workflow](#3-mutmut-workflow)
4. [Interpreting Results](#4-interpreting-results)
5. [Limitations & Caveats](#5-limitations--caveats)
6. [Best Practices](#6-best-practices)

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
mutmut run --paths-to-mutate=src/processors/asset_processor.py

# Test specific directory
mutmut run --paths-to-mutate=src/processors/

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
paths_to_mutate = "src/"
backup = false
runner = "pytest -x --tb=short"
tests_dir = "tests/"
dict_synonyms = "Struct, NamedStruct"
```

**setup.cfg**:
```ini
[mutmut]
paths_to_mutate=src/
backup=False
runner=pytest -x --tb=short
tests_dir=tests/
```

### Quick Workflow Commands

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
--- src/processors/asset_processor.py
+++ [Mutant] src/processors/asset_processor.py
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

### Common Weak Test Patterns

**1. Missing Assertion**:
```python
# Weak: No assertion
def test_function():
    result = function()
    # Test passes without validating result

# Strong: Specific assertion
def test_function():
    result = function()
    assert result == expected_value
```

**2. Assertion Too Broad**:
```python
# Weak: Too generic
assert result is not None

# Strong: Exact value
assert result == "Expected Value"
```

**3. Missing Boundary Cases**:
```python
# Weak: Only normal case
def test_threshold():
    assert get_severity(8.0) == "High"

# Strong: Normal + boundaries
def test_threshold():
    assert get_severity(8.0) == "High"
    assert get_severity(7.0) == "High"  # Boundary
    assert get_severity(6.9) == "Low"   # Just below
```

---

## 5. Limitations & Caveats

### Limitation 1: Slow Execution

**Problem**: Mutation testing is inherently slow.

**Impact**: 1000 mutations × 10s test suite = ~3 hours

**Mitigation**:
- Run on nightly builds, not every commit
- Use incremental testing (changed files only)
- Parallelize execution manually (GNU parallel)
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

**Mitigation**:
- Manual review of survived mutations
- Accept some survived mutations (document why)
- Focus on mutation score trends, not absolute numbers

---

### Limitation 3: High False Positive Rate

**Problem**: Not all survived mutations indicate weak tests.

**Examples**:
- Equivalent mutations
- Defensive code never executed in practice
- Logging statements (mutation doesn't affect behavior)

**Example**:
```python
def process_data(data):
    LOG.debug("Processing %d items", len(data))  # Mutation survives
    return [transform(item) for item in data]
```

Mutating the log message doesn't affect behavior.

**Mitigation**:
- Review survived mutations manually
- Exclude logging/debug code from mutation testing
- Document accepted survived mutations

---

### Limitation 4: Doesn't Replace Code Coverage

**Best Practice**: Require both 95% coverage AND 80% mutation score.

**Why**:
- Coverage finds untested code
- Mutation testing finds weak tests
- Both needed for comprehensive quality

---

### Limitation 5: Limited to Unit Tests

**Problem**: Mutation testing works best on unit tests, not integration tests.

**Why**: Integration tests are slow, making mutation testing impractical.

**Best Practice**: Run mutation testing on unit tests only.

---

## 6. Best Practices

### Start Small & Iterate
- **Don't** run on entire codebase immediately
- **Do** test one critical module, expand gradually
- Fix 5-10 survived mutations per cycle
- Track score over time (aim for gradual improvement)

### Combine with Coverage
- Require **both** 95%+ coverage AND 80%+ mutation score
- Coverage finds untested code, mutation testing finds weak tests

### Run Strategically
- Run in nightly builds (too slow for every commit)
- Focus on critical code: security, business logic, data processing
- Deprioritize: CLI parsing, logging, configuration, getters/setters

### Review Intelligently
- Review survived mutations manually (not all indicate weak tests)
- Accept some mutations (logging, equivalent mutations)
- Document exceptions in `.mutmut-exceptions.md`
- Set realistic 80% target (90%+ has diminishing returns)

### Automate
- Integrate in CI pipeline (nightly builds)
- Use custom scripts to enforce mutation score thresholds
- Cache results (`.mutmut-cache`) for faster reruns

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

---

**For comprehensive examples and advanced strategies:** See reference.md
