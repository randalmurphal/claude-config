---
name: performance-profiling
description: Python performance profiling with cProfile, line_profiler, memory_profiler, and py-spy. Covers profiling workflows, interpreting results, finding bottlenecks, memory leak detection, and optimization strategies. Use when code is slow, debugging performance issues, optimizing for production, or investigating memory usage.
allowed-tools: [Read, Bash, Grep]
---

# Performance Profiling

## Core Principles

- **Measure first, optimize second** - Never optimize without profiling. Intuition is wrong 80% of the time
- **Profile in production-like conditions** - Dev performance doesn't predict production
- **Focus on the 80/20** - 20% of code causes 80% of slowness
- **One bottleneck at a time** - Fix biggest, re-profile, repeat
- **Don't micro-optimize** - Shaving 1ms off rarely-called function doesn't matter

### When to Profile

**Profile when:**
- Measurably slow (timeouts, SLA violations)
- Adding feature to critical path
- Memory growth over time
- Production performance degrades

**Don't profile:**
- "Code doesn't look fast" (measure first)
- Premature optimization
- Already-fast code

## Tools Comparison

| Tool | Best For | Overhead | Production Safe | Installation |
|------|----------|----------|-----------------|--------------|
| cProfile | Function-level CPU | Low (2-5%) | Yes (brief) | Built-in |
| line_profiler | Line-level CPU | High (10-50x) | No | pip install |
| memory_profiler | Line-level memory | Very high (100x+) | No | pip install |
| py-spy | Production sampling | Very low (<1%) | Yes | pip install |
| tracemalloc | Memory tracking | Medium (5-10%) | Yes (brief) | Built-in |

## cProfile - Function-Level

### Usage

**Profile script:**
```bash
python -m cProfile -s cumtime script.py
python -m cProfile -o output.prof script.py
```

**Profile function:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
result = my_function()
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Interpreting Output

```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     1000    0.150    0.000    2.450    0.002 module.py:10(process_data)
     5000    1.200    0.000    1.800    0.000 module.py:25(expensive_calc)
```

**Columns:**
- **ncalls:** Times called
- **tottime:** Time in function (excluding subcalls)
- **cumtime:** Time in function (including subcalls)
- **percall:** Time per call

**Look for:**
- High cumtime: Biggest total impact
- High tottime: Expensive work
- High ncalls + low percall: Cache/batch opportunity
- Low ncalls + high percall: Algorithmic issue

### Sort Options

```python
stats.sort_stats('cumulative')  # Total impact (start here)
stats.sort_stats('tottime')     # Function-only time
stats.sort_stats('ncalls')      # Call frequency
```

**Workflow:**
1. Sort by cumulative - highest impact
2. Sort by tottime - find hot spots
3. Optimize intersection

### Visualization

```bash
pip install snakeviz
python -m cProfile -o profile.prof script.py
snakeviz profile.prof  # Opens browser
```

## line_profiler - Line-Level

### Usage

```python
# script.py
@profile  # No import needed
def slow_function():
    result = 0
    for i in range(10000):
        result += expensive_calc(i)  # Which line is slow?
    return result
```

```bash
kernprof -l -v script.py
```

### Interpreting Output

```
Line #  Hits    Time      Per Hit   % Time  Line Contents
    11     1      5.0      5.0      0.0    result = 0
    12  10000  15234.0    1.5      2.5    for i in range(10000):
    13  10000 580123.0   58.0     95.0        result += expensive_calc(i)
```

**Columns:**
- **Hits:** Times executed
- **Time:** Total time (microseconds)
- **% Time:** Percentage of function time

**Look for:**
- High % Time: Optimize first
- High Hits + low Time: Batch?
- Low Hits + high Time: Algorithm issue

### Best Practices

```python
# Profile selectively (overhead too high for everything)
@profile
def suspected_bottleneck():
    pass  # Only profile this

def helper():
    pass  # Don't profile unless needed
```

## memory_profiler - Memory Usage

### Usage

```python
from memory_profiler import profile

@profile
def load_data():
    data = []
    for i in range(1000000):
        data.append({'id': i})  # How much memory?
    return data
```

```bash
python -m memory_profiler script.py
```

### Interpreting Output

```
Line #  Mem usage  Increment  Occurrences   Line Contents
     5   50.5 MiB   50.5 MiB           1   @profile
     6   50.5 MiB    0.0 MiB           1       data = []
     7  150.8 MiB  100.3 MiB           1       for i in range(1000000):
     8  150.8 MiB    0.0 MiB     1000000           data.append(...)
```

**Look for:**
- Large Increment: Big allocations
- Memory not released: Potential leak
- Unexpected growth

## tracemalloc - Memory Tracking

### Usage

```python
import tracemalloc

tracemalloc.start()

# Code to profile
data = load_large_dataset()

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f} MB")
print(f"Peak: {peak / 1024 / 1024:.2f} MB")

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)

tracemalloc.stop()
```

### Finding Leaks

```python
tracemalloc.start()

snapshot1 = tracemalloc.take_snapshot()

# Run suspected code
for i in range(1000):
    potentially_leaky()

snapshot2 = tracemalloc.take_snapshot()

# Compare
top_stats = snapshot2.compare_to(snapshot1, 'lineno')
for stat in top_stats[:10]:
    print(stat)
```

## py-spy - Production Profiling

### Usage

```bash
# Profile running process
sudo py-spy top --pid 12345

# Record for 60 seconds
sudo py-spy record -o profile.svg --pid 12345 --duration 60

# Profile from start
py-spy record -o profile.svg -- python script.py
```

### Advantages

- Low overhead (<1%)
- No code modification
- Attach to running processes
- Flame graphs

**Use for:**
- Production profiling
- Live performance issues
- Long-running processes
- Code you can't modify

### Flame Graph Reading

- **Width:** Time spent (wider = more time)
- **Height:** Stack depth
- **Flat top:** Function doing work itself
- **Deep stacks:** Many nested calls

## Optimization Strategies

### Common Bottlenecks

**1. Unnecessary computations:**
```python
# Before
for item in items:
    if item > compute_threshold():  # Every iteration
        process(item)

# After
threshold = compute_threshold()  # Once
for item in items:
    if item > threshold:
        process(item)
```

**2. N+1 queries:**
```python
# Before
for user_id in user_ids:
    orders = db.query(f"SELECT * FROM orders WHERE user_id = {user_id}")

# After
orders = db.query(f"SELECT * FROM orders WHERE user_id IN ({user_ids})")
```

**3. Large data in memory:**
```python
# Before: All in memory
data = [json.loads(line) for line in f]
return [process(item) for item in data]

# After: Stream
for line in f:
    yield process(json.loads(line))
```

**4. Inefficient algorithms:**
```python
# Before: O(n²)
for i, item1 in enumerate(items):
    for item2 in items[i+1:]:
        if item1 == item2:
            duplicates.append(item1)

# After: O(n)
seen = set()
duplicates = set()
for item in items:
    if item in seen:
        duplicates.add(item)
    seen.add(item)
```

**5. No caching:**
```python
# Before
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# After
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

### Workflow

1. **Profile:** `python -m cProfile -s cumtime script.py`
2. **Drill down:** Line profile the slow function
3. **Optimize:** Fix algorithmic issues, add caching, batch operations
4. **Re-profile:** Verify improvement
5. **Repeat:** Next bottleneck

## Quick Reference

### Decision Tree

```
Is code slow?
├─ Yes → cProfile
│  ├─ Find slow function
│  ├─ line_profiler on function
│  ├─ Find slow line
│  └─ Optimize
└─ No → Don't optimize

Memory growing?
├─ Yes → tracemalloc
│  ├─ Find allocation source
│  ├─ Compare snapshots
│  └─ Fix leak
└─ No → Monitor

Production issue?
├─ Yes → py-spy (no code changes)
└─ No → cProfile/line_profiler
```

### Commands

```bash
# cProfile
python -m cProfile -s cumtime script.py
snakeviz profile.prof

# line_profiler
kernprof -l -v script.py

# memory_profiler
python -m memory_profiler script.py

# py-spy
sudo py-spy top --pid <PID>
sudo py-spy record -o profile.svg --pid <PID> --duration 60
```

### Optimization Checklist

**Before:**
- [ ] Profile to confirm bottleneck
- [ ] Measure baseline
- [ ] Identify hot path

**Optimize:**
- [ ] Reduce time complexity (O(n²) → O(n))
- [ ] Add caching
- [ ] Use appropriate data structures
- [ ] Batch operations
- [ ] Use generators vs lists
- [ ] Stream large files

**After:**
- [ ] Re-profile
- [ ] Verify improvement
- [ ] Check no regressions

### Metrics to Track

**CPU:**
- Total execution time
- Time per function (cumtime)
- Call count (ncalls)

**Memory:**
- Current usage
- Peak usage
- Growth over time

**Production:**
- Response time (p50, p95, p99)
- Throughput (req/sec)
- Error rate

### Anti-Patterns

**Don't:**
- Optimize without profiling
- Micro-optimize fast code
- Profile only in dev
- Use high-overhead profilers in production
- Fix one bottleneck and stop
- Skip re-profiling after changes

**Do:**
- Profile first
- Focus on biggest bottlenecks
- Profile in production-like conditions
- Use low-overhead tools (py-spy) for production
- Re-profile after optimization
- Measure actual improvement
