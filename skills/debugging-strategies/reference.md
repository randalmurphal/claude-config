# Debugging Strategies - Detailed Reference

This file contains detailed examples, advanced patterns, and comprehensive troubleshooting guides that supplement the core SKILL.md.

---

## Table of Contents

1. [Advanced Root-Cause Tracing Examples](#advanced-root-cause-tracing-examples)
2. [Complex Reproduction Scenarios](#complex-reproduction-scenarios)
3. [Advanced pdb Techniques](#advanced-pdb-techniques)
4. [Production Debugging Patterns](#production-debugging-patterns)
5. [Performance Debugging](#performance-debugging)
6. [Distributed System Debugging](#distributed-system-debugging)
7. [Debugging by Bug Type](#debugging-by-bug-type)
8. [Debugging Tools Comparison](#debugging-tools-comparison)

---

## Advanced Root-Cause Tracing Examples

### Multi-Layer Trace: Database to API to UI

**Scenario:** User reports "Can't save profile" error in UI.

**Error in UI:**
```javascript
// React component shows: "Failed to save profile"
const saveProfile = async (data) => {
  const response = await fetch('/api/profile', {
    method: 'POST',
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to save profile');
}
```

**Trace to API:**
```python
# API endpoint returns 500
@app.post('/api/profile')
async def update_profile(data: dict):
    user = await db.update_user(data['user_id'], data)
    return user  # Returns None, causing error
```

**Trace to database layer:**
```python
# Database layer has silent failure
async def update_user(user_id: str, data: dict):
    try:
        await collection.update_one(
            {'_id': user_id},
            {'$set': data}
        )
        return await collection.find_one({'_id': user_id})
    except Exception:
        return None  # ROOT CAUSE: Swallows exception
```

**Root cause:** Exception handling returns None instead of propagating error. User ID format changed from string to ObjectId, causing query to fail silently.

**Fix at source:**
```python
from bson import ObjectId

async def update_user(user_id: str, data: dict):
    # Don't catch exceptions - let them propagate
    oid = ObjectId(user_id)  # Explicit conversion with clear error
    result = await collection.update_one(
        {'_id': oid},
        {'$set': data}
    )
    if result.modified_count == 0:
        raise ValueError(f"User {user_id} not found")
    return await collection.find_one({'_id': oid})
```

### Tracing Through Async Code

**Challenge:** Async code has complex call chains that are hard to trace.

**Technique: Add correlation IDs**
```python
import contextvars
import uuid

# Context variable tracks request across async calls
request_id = contextvars.ContextVar('request_id', default=None)

async def handle_request(data):
    # Set correlation ID at entry point
    rid = str(uuid.uuid4())
    request_id.set(rid)
    LOG.info(f"[{rid}] Request started")

    try:
        result = await process_data(data)
        LOG.info(f"[{rid}] Request completed")
        return result
    except Exception as e:
        LOG.error(f"[{rid}] Request failed: {e}")
        raise

async def process_data(data):
    rid = request_id.get()
    LOG.debug(f"[{rid}] process_data called")
    # Now all logs share correlation ID
    result = await database_call(data)
    return result
```

---

## Complex Reproduction Scenarios

### Reproducing Race Conditions

**Scenario:** Bug only happens when two users perform action simultaneously.

```python
import threading
import time

def test_race_condition_reproduction():
    """Reproduce race condition with parallel execution."""
    errors = []

    def update_balance(user_id, amount):
        try:
            # Simulate reading balance
            balance = db.get_balance(user_id)
            time.sleep(0.01)  # Simulate processing delay
            # Simulate writing balance
            db.set_balance(user_id, balance + amount)
        except Exception as e:
            errors.append(str(e))

    # Two threads update same user simultaneously
    user_id = "test_user_123"
    db.set_balance(user_id, 100)

    t1 = threading.Thread(target=update_balance, args=(user_id, 50))
    t2 = threading.Thread(target=update_balance, args=(user_id, 50))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    final_balance = db.get_balance(user_id)
    # Expected: 200 (100 + 50 + 50)
    # Actual: 150 (race condition - one update lost)
    assert final_balance == 200, f"Race condition! Balance: {final_balance}"
```

### Reproducing Timing-Dependent Bugs

**Scenario:** Bug only happens when operations occur in specific time window.

```python
import time
from unittest.mock import patch

def test_timing_dependent_bug():
    """Reproduce bug that depends on system time."""

    # Mock time to control timing
    with patch('time.time') as mock_time:
        # Set time to just before token expires
        token_expires = 1700000000
        mock_time.return_value = token_expires - 1  # 1 second before expiry

        token = create_token(user_id="test", expires=token_expires)

        # Advance time past expiry
        mock_time.return_value = token_expires + 1

        # Now validation should fail
        with pytest.raises(TokenExpiredError):
            validate_token(token)
```

### Reproducing Memory-Related Bugs

**Scenario:** Bug only appears after processing large datasets.

```python
import psutil
import gc

def test_memory_leak_reproduction():
    """Reproduce memory leak with large dataset."""

    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Process increasing amounts of data
    for iteration in range(10):
        data = generate_large_dataset(size=1000000 * (iteration + 1))
        process_data(data)

        gc.collect()  # Force garbage collection
        current_memory = process.memory_info().rss / 1024 / 1024

        memory_growth = current_memory - initial_memory
        LOG.info(f"Iteration {iteration}: Memory growth: {memory_growth:.2f} MB")

        if memory_growth > 500:  # 500MB threshold
            raise MemoryError(f"Memory leak detected: {memory_growth:.2f} MB growth")
```

---

## Advanced pdb Techniques

### Conditional Breakpoints

```python
# Break only when specific condition is true
def process_users(users):
    for user in users:
        # Break only for problematic user
        if user.id == "problem_user_123":
            breakpoint()
        process_user(user)
```

### Post-Mortem Debugging

```python
# Debug after crash
import pdb

try:
    buggy_function()
except Exception:
    pdb.post_mortem()  # Debug at point of exception
```

### Remote Debugging

```python
# Debug running process remotely
import pdb
import socket

class RemotePdb(pdb.Pdb):
    """Remote debugger accessible over network."""

    def __init__(self, host='127.0.0.1', port=4444):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind((host, port))
        self.listen_socket.listen(1)
        (client_socket, _) = self.listen_socket.accept()
        handle = client_socket.makefile('rw')
        pdb.Pdb.__init__(self, stdin=handle, stdout=handle)

# In code:
RemotePdb().set_trace()

# Connect from another terminal:
# telnet localhost 4444
```

### Custom pdb Commands

```python
import pdb

class CustomPdb(pdb.Pdb):
    """pdb with custom commands."""

    def do_context(self, arg):
        """Show all local variables with types."""
        frame = self.curframe
        for name, value in frame.f_locals.items():
            print(f"{name}: {type(value).__name__} = {repr(value)[:100]}")

    def do_sql(self, arg):
        """Execute SQL query from debugger."""
        import sqlite3
        conn = sqlite3.connect('app.db')
        cursor = conn.execute(arg)
        print(cursor.fetchall())

# Use custom debugger:
CustomPdb().set_trace()
```

---

## Production Debugging Patterns

### Safe Production Debugging

**Problem:** Can't use interactive debugger in production.

**Solution: Logging-based debugging**
```python
import logging
from functools import wraps

def production_debug(logger):
    """Decorator for production debugging."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"PROD_DEBUG: {func.__name__} called")
            logger.debug(f"PROD_DEBUG: args={args}, kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)
                logger.debug(f"PROD_DEBUG: {func.__name__} returned {type(result)}")
                return result
            except Exception as e:
                logger.error(f"PROD_DEBUG: {func.__name__} raised {type(e).__name__}: {e}")
                logger.debug(f"PROD_DEBUG: locals={locals()}")
                raise

        return wrapper
    return decorator

# Usage:
@production_debug(LOG)
def critical_function(user_id, data):
    # Function implementation
    pass
```

### Feature Flags for Debugging

```python
import os

DEBUG_USERS = os.getenv('DEBUG_USERS', '').split(',')

def process_request(user_id, data):
    # Enable verbose logging for specific users
    debug_enabled = user_id in DEBUG_USERS

    if debug_enabled:
        LOG.setLevel(logging.DEBUG)
        LOG.debug(f"DEBUG MODE for user {user_id}")
        LOG.debug(f"Request data: {data}")

    try:
        result = handle_request(data)

        if debug_enabled:
            LOG.debug(f"Result: {result}")

        return result
    finally:
        if debug_enabled:
            LOG.setLevel(logging.INFO)  # Reset log level
```

### Sampling-Based Debugging

```python
import random

def process_item(item):
    # Only log details for 1% of requests
    should_debug = random.random() < 0.01

    if should_debug:
        LOG.debug(f"SAMPLE_DEBUG: Processing item {item['id']}")
        LOG.debug(f"SAMPLE_DEBUG: Full item: {item}")

    result = expensive_operation(item)

    if should_debug:
        LOG.debug(f"SAMPLE_DEBUG: Result: {result}")

    return result
```

---

## Performance Debugging

### Profiling with cProfile

```python
import cProfile
import pstats

def profile_function():
    """Profile function performance."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Run code to profile
    result = slow_function()

    profiler.disable()

    # Print stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 slowest functions

    return result
```

### Line-by-Line Profiling

```bash
# Install line_profiler
pip install line-profiler
```

```python
from line_profiler import LineProfiler

def profile_line_by_line():
    """Profile line-by-line execution time."""
    profiler = LineProfiler()
    profiler.add_function(slow_function)
    profiler.enable()

    slow_function()

    profiler.disable()
    profiler.print_stats()

# Or use decorator:
@profile  # Requires kernprof runner
def slow_function():
    # Function implementation
    pass

# Run with: kernprof -l -v script.py
```

### Finding Bottlenecks

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(label):
    """Context manager to time code blocks."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        LOG.info(f"{label}: {elapsed:.4f}s")

def slow_operation():
    with timer("Database query"):
        users = db.query_users()

    with timer("Data processing"):
        results = [process(u) for u in users]

    with timer("API calls"):
        for result in results:
            api.send(result)

    # Output shows which section is slow:
    # Database query: 0.0234s
    # Data processing: 2.3456s  ← Bottleneck!
    # API calls: 0.1234s
```

---

## Distributed System Debugging

### Distributed Tracing

```python
import uuid
from typing import Optional

class TraceContext:
    """Distributed tracing context."""

    def __init__(self, trace_id: Optional[str] = None, span_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())
        self.parent_span_id = span_id

    def new_span(self) -> 'TraceContext':
        """Create child span."""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4())
        )

# Service A:
def handle_request(data):
    trace = TraceContext()
    LOG.info(f"[trace:{trace.trace_id}] [span:{trace.span_id}] Request received")

    # Call Service B with trace context
    response = requests.post(
        'http://service-b/api',
        json=data,
        headers={
            'X-Trace-Id': trace.trace_id,
            'X-Span-Id': trace.span_id
        }
    )

# Service B:
def handle_api_request(request):
    # Extract trace context
    trace = TraceContext(
        trace_id=request.headers.get('X-Trace-Id'),
        span_id=request.headers.get('X-Span-Id')
    )
    child_trace = trace.new_span()

    LOG.info(f"[trace:{child_trace.trace_id}] [span:{child_trace.span_id}] Processing")
    # Now both services log with same trace_id - can correlate logs
```

### Debugging Message Queues

```python
def debug_message_queue():
    """Add debugging to message queue consumers."""

    def consume_message(message):
        message_id = message.get('id', 'unknown')

        LOG.info(f"MSG_DEBUG: Received message {message_id}")
        LOG.debug(f"MSG_DEBUG: Full message: {message}")

        try:
            result = process_message(message)
            LOG.info(f"MSG_DEBUG: Message {message_id} processed successfully")
            return result
        except Exception as e:
            LOG.error(f"MSG_DEBUG: Message {message_id} failed: {e}")
            LOG.debug(f"MSG_DEBUG: Message content: {message}")
            # Dead letter queue
            send_to_dlq(message, error=str(e))
            raise
```

---

## Debugging by Bug Type

### Debugging Concurrency Bugs

**Add synchronization debugging:**
```python
import threading
import logging

# Thread-safe logger
LOG = logging.getLogger(__name__)

def debug_concurrent_access(resource_name):
    """Decorator to debug concurrent access."""
    def decorator(func):
        lock = threading.Lock()

        def wrapper(*args, **kwargs):
            thread_id = threading.current_thread().ident
            LOG.debug(f"Thread {thread_id} waiting for {resource_name}")

            with lock:
                LOG.debug(f"Thread {thread_id} acquired {resource_name}")
                try:
                    return func(*args, **kwargs)
                finally:
                    LOG.debug(f"Thread {thread_id} released {resource_name}")

        return wrapper
    return decorator

@debug_concurrent_access("user_balance")
def update_balance(user_id, amount):
    # Critical section
    balance = get_balance(user_id)
    set_balance(user_id, balance + amount)
```

### Debugging State Machines

**Add state transition logging:**
```python
class StateMachine:
    def __init__(self):
        self.state = "INIT"
        self._transitions = []

    def transition(self, new_state):
        """Transition with debugging."""
        old_state = self.state
        LOG.info(f"STATE: {old_state} → {new_state}")

        # Record transition history
        self._transitions.append({
            'from': old_state,
            'to': new_state,
            'timestamp': time.time()
        })

        self.state = new_state

        # Debug unexpected transitions
        if len(self._transitions) > 100:
            LOG.warning(f"STATE: Many transitions: {len(self._transitions)}")
            LOG.debug(f"STATE: Recent transitions: {self._transitions[-10:]}")

    def debug_state_history(self):
        """Print state transition history."""
        for t in self._transitions:
            print(f"{t['from']} → {t['to']} at {t['timestamp']}")
```

### Debugging Resource Leaks

```python
import weakref
from typing import List

class ResourceTracker:
    """Track resource allocation/deallocation."""

    def __init__(self):
        self._resources: List[weakref.ref] = []

    def track(self, resource, name):
        """Track resource."""
        ref = weakref.ref(resource, lambda r: LOG.info(f"Resource {name} deallocated"))
        self._resources.append(ref)
        LOG.debug(f"Resource {name} allocated (total: {len(self._resources)})")

    def check_leaks(self):
        """Check for leaked resources."""
        alive = [r for r in self._resources if r() is not None]
        if alive:
            LOG.warning(f"Potential leak: {len(alive)} resources still alive")
            return len(alive)
        return 0

# Usage:
tracker = ResourceTracker()

def process_file(filename):
    f = open(filename)
    tracker.track(f, f"file:{filename}")
    # If f.close() is missed, tracker will report leak
    data = f.read()
    f.close()
    return data
```

---

## Debugging Tools Comparison

### Python Debugging Tools

| Tool | Best For | Speed | Learning Curve | Production-Safe |
|------|----------|-------|----------------|-----------------|
| **print()** | Quick checks | ⚡ Instant | None | ✅ Yes |
| **logging** | Permanent tracing | ⚡ Fast | Low | ✅ Yes |
| **pdb** | Interactive debugging | 🔄 Interactive | Medium | ⚠️ Rarely |
| **debugpy (VS Code)** | Visual debugging | 🔄 Interactive | Low | ❌ No |
| **cProfile** | Performance profiling | 🐌 Slow | Medium | ⚠️ Sampling only |
| **tracemalloc** | Memory debugging | 🐌 Slow | Medium | ⚠️ Overhead |
| **strace** | System call tracing | 🐌 Very slow | High | ⚠️ Linux only |

### When to Use Each Tool

**print() / LOG.debug():**
- Quick verification of values
- Permanent trace points
- Production debugging

**pdb:**
- Understanding complex state
- Exploring unfamiliar code
- Interactive investigation

**profiler (cProfile):**
- Finding performance bottlenecks
- Optimizing slow code
- Understanding time complexity

**Memory profiler:**
- Finding memory leaks
- Optimizing memory usage
- Understanding allocation patterns

**strace (Linux):**
- Debugging system interactions
- File access issues
- Network call debugging

---

## Advanced Debugging Checklist

**Before starting:**
- [ ] Can you reproduce the bug consistently?
- [ ] Do you have a minimal reproduction case?
- [ ] Have you checked logs for related errors?
- [ ] Is there a test that demonstrates the bug?

**During debugging:**
- [ ] Are you tracing backward to root cause?
- [ ] Have you verified assumptions with evidence?
- [ ] Are you isolating the problem (binary search)?
- [ ] Have you checked for similar issues in codebase?

**Before claiming fixed:**
- [ ] Does the fix address root cause (not symptom)?
- [ ] Do tests pass (including new test for this bug)?
- [ ] Have you verified the fix manually?
- [ ] Could this fix break anything else?
- [ ] Is there logging to prevent recurrence?

---

## Debugging War Stories (Learning from Real Bugs)

### The Heisenbug

**Bug:** Test passes when run alone, fails when run with other tests.

**Root cause:** Test modified global state (environment variable) without cleanup, affecting subsequent tests.

**Lesson:** Always clean up test state. Use fixtures, setup/teardown, or pytest's autouse fixtures.

### The Production-Only Bug

**Bug:** Works in dev, staging, but fails in production.

**Root cause:** Production had different timezone setting (UTC vs local time). Code used `datetime.now()` instead of `datetime.utcnow()`.

**Lesson:** Environment parity matters. Use UTC in all environments. Test with production-like configuration.

### The Race Condition

**Bug:** Balance occasionally wrong after concurrent updates.

**Root cause:** Read-modify-write without locking. Two threads read same balance, both add to it, one update lost.

**Lesson:** Critical sections need synchronization. Use database transactions or explicit locks.

---

**For core debugging workflow and quick reference, see SKILL.md**
