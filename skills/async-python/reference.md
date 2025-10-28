# Async Python Reference

Comprehensive examples, advanced patterns, and detailed troubleshooting for Python async/await development.

---

## Table of Contents

1. [Decision Framework Details](#decision-framework-details)
2. [Advanced asyncio Patterns](#advanced-asyncio-patterns)
3. [Async Generators and Iterators](#async-generators-and-iterators)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Testing Patterns](#testing-patterns)
6. [Performance Optimization](#performance-optimization)
7. [Real-World Examples](#real-world-examples)
8. [Troubleshooting Guide](#troubleshooting-guide)

---

## Decision Framework Details

### Detailed Comparison

| Aspect | asyncio | threading | multiprocessing |
|--------|---------|-----------|-----------------|
| **Best For** | I/O-bound (network, disk) | I/O-bound blocking libs | CPU-bound computation |
| **Concurrency** | Thousands of tasks | Tens of threads | CPU core count |
| **Memory** | Low (single process) | Medium (shared memory) | High (separate processes) |
| **Overhead** | Very low | Low | High (process creation) |
| **GIL Impact** | Irrelevant (single thread) | Limited by GIL | No GIL (separate processes) |
| **Communication** | Direct (shared memory) | Direct (shared memory) | IPC (queues, pipes) |
| **Debugging** | Easier (single thread) | Moderate (race conditions) | Harder (separate processes) |

### When to Choose asyncio

```python
# Network I/O (API calls, websockets, database queries)
async def fetch_multiple_apis():
    """Fetch from 100 APIs concurrently (seconds, not minutes)."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_api(session, url) for url in api_urls]
        return await asyncio.gather(*tasks)

# File I/O (with async libraries)
async def read_multiple_files():
    """Read multiple files concurrently."""
    async with aiofiles.open('file1.txt') as f1:
        async with aiofiles.open('file2.txt') as f2:
            content1 = await f1.read()
            content2 = await f2.read()
    return content1, content2

# Database queries (with async driver)
async def fetch_related_data(user_id: int):
    """Fetch user and related data concurrently."""
    async with asyncpg.connect(dsn) as conn:
        user, orders, profile = await asyncio.gather(
            conn.fetchrow("SELECT * FROM users WHERE id=$1", user_id),
            conn.fetch("SELECT * FROM orders WHERE user_id=$1", user_id),
            conn.fetchrow("SELECT * FROM profiles WHERE user_id=$1", user_id)
        )
    return user, orders, profile
```

### When to Choose threading

```python
import concurrent.futures
import asyncio

# Blocking I/O libraries (no async version available)
async def process_with_blocking_lib():
    """Use threads for libraries without async support."""
    loop = asyncio.get_running_loop()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Run blocking operations in thread pool
        tasks = [
            loop.run_in_executor(executor, requests.get, url)
            for url in urls
        ]
        responses = await asyncio.gather(*tasks)

    return [r.json() for r in responses]

# Mixed workload (some I/O, some CPU)
def mixed_workload_example():
    """Thread pool for mixed I/O and light CPU work."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(fetch_and_process, item)
            for item in items
        ]
        results = [f.result() for f in futures]
    return results
```

### When to Choose multiprocessing

```python
from concurrent.futures import ProcessPoolExecutor
import asyncio

# CPU-bound computation
async def parallel_computation():
    """Run heavy computation across CPU cores."""
    loop = asyncio.get_running_loop()

    with ProcessPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(executor, heavy_compute, chunk)
            for chunk in data_chunks
        ]
        results = await asyncio.gather(*tasks)

    return results

def heavy_compute(data: list[int]) -> int:
    """CPU-intensive calculation (runs in separate process)."""
    # Image processing, ML inference, cryptography, etc.
    return sum(i ** 2 for i in data)

# Data processing pipeline
from multiprocessing import Pool

def process_large_dataset(data: list[dict]) -> list[dict]:
    """Process large dataset in parallel."""
    with Pool() as pool:
        results = pool.map(transform_record, data)
    return results
```

---

## Advanced asyncio Patterns

### Pattern: Semaphore for Rate Limiting

```python
import asyncio

async def fetch_with_rate_limit(urls: list[str], max_concurrent: int = 5):
    """Limit concurrent requests to avoid overwhelming server."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(url: str):
        async with semaphore:  # Acquire semaphore
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()

    tasks = [fetch_one(url) for url in urls]
    return await asyncio.gather(*tasks)
```

### Pattern: as_completed() for Progressive Results

```python
async def process_as_completed(items: list[str]):
    """Process items and handle results as they complete."""
    tasks = [process_item(item) for item in items]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        print(f"Completed: {result}")
        # Can update UI, save to database, etc. as each completes

async def first_successful_result(urls: list[str]):
    """Return first successful result, cancel others."""
    tasks = [fetch_url(url) for url in urls]

    for coro in asyncio.as_completed(tasks):
        try:
            result = await coro
            # Cancel remaining tasks
            for task in tasks:
                task.cancel()
            return result
        except Exception:
            continue

    raise Exception("All requests failed")
```

### Pattern: Lock for Shared State

```python
import asyncio

class SharedCounter:
    """Thread-safe counter for async code."""

    def __init__(self):
        self._value = 0
        self._lock = asyncio.Lock()

    async def increment(self):
        """Safely increment counter."""
        async with self._lock:
            self._value += 1

    async def get_value(self) -> int:
        """Get current value."""
        async with self._lock:
            return self._value
```

### Pattern: Event for Coordination

```python
import asyncio

async def waiter(event: asyncio.Event, name: str):
    """Wait for event to be set."""
    print(f"{name} waiting")
    await event.wait()
    print(f"{name} triggered")

async def coordinator():
    """Coordinate multiple tasks with event."""
    event = asyncio.Event()

    # Start waiters
    waiters = [
        asyncio.create_task(waiter(event, f"Waiter-{i}"))
        for i in range(5)
    ]

    # Do some work
    await asyncio.sleep(2)

    # Trigger all waiters
    event.set()

    # Wait for all to complete
    await asyncio.gather(*waiters)
```

### Pattern: async_timeout for Complex Timeouts

```python
from async_timeout import timeout

async def complex_operation_with_timeout():
    """Use async_timeout for cleaner timeout handling."""
    try:
        async with timeout(10) as cm:
            result1 = await step1()
            result2 = await step2(result1)
            result3 = await step3(result2)
            return result3
    except asyncio.TimeoutError:
        LOG.error(f"Operation timed out after {cm.expired} seconds")
        raise
```

---

## Async Generators and Iterators

### Async Generators

```python
async def fetch_paginated_results(api_url: str):
    """Async generator for paginated API results."""
    page = 1
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(f"{api_url}?page={page}") as resp:
                data = await resp.json()
                if not data['items']:
                    break

                for item in data['items']:
                    yield item

                page += 1

# Usage
async def process_all_results():
    """Process paginated results as they arrive."""
    async for item in fetch_paginated_results("https://api.example.com"):
        await process_item(item)
```

### Async Iterators

```python
class AsyncFileReader:
    """Async iterator for reading large files line by line."""

    def __init__(self, filename: str):
        self.filename = filename
        self.file = None

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.file is None:
            self.file = await aiofiles.open(self.filename, 'r')

        line = await self.file.readline()
        if not line:
            await self.file.close()
            raise StopAsyncIteration

        return line.strip()

# Usage
async def process_large_file():
    """Process large file line by line without loading into memory."""
    async for line in AsyncFileReader("large_file.txt"):
        await process_line(line)
```

### Async Comprehensions

```python
async def fetch_all_user_data(user_ids: list[int]) -> list[dict]:
    """Async list comprehension."""
    return [
        await fetch_user(uid)
        async for uid in async_user_generator(user_ids)
    ]

async def user_data_dict(user_ids: list[int]) -> dict[int, dict]:
    """Async dict comprehension."""
    return {
        uid: await fetch_user(uid)
        async for uid in async_user_generator(user_ids)
    }
```

---

## Error Handling Patterns

### Pattern: Retry with Exponential Backoff

```python
import asyncio
from typing import TypeVar, Callable

T = TypeVar('T')

async def retry_with_backoff(
    coro_func: Callable[..., Awaitable[T]],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> T:
    """Retry async function with exponential backoff."""
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return await coro_func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                LOG.error(f"Failed after {max_retries} attempts")
                raise

            LOG.warning(
                f"Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {delay}s"
            )
            await asyncio.sleep(delay)
            delay *= backoff_factor

# Usage
async def fetch_with_retry(url: str):
    return await retry_with_backoff(fetch_url, url=url, max_retries=5)
```

### Pattern: Partial Success with gather()

```python
async def fetch_all_with_partial_success(urls: list[str]) -> list[dict | None]:
    """Fetch all URLs, return None for failures."""
    tasks = [fetch_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Log failures
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            LOG.error(f"Failed to fetch {urls[i]}: {result}")
            results[i] = None

    return results
```

### Pattern: Circuit Breaker

```python
import asyncio
from datetime import datetime, timedelta

class CircuitBreaker:
    """Circuit breaker pattern for async operations."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, coro_func, *args, **kwargs):
        """Execute function through circuit breaker."""
        if self.state == "open":
            if datetime.now() - self.last_failure_time > timedelta(
                seconds=self.recovery_timeout
            ):
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await coro_func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        """Reset on successful call."""
        self.failure_count = 0
        self.state = "closed"

    def on_failure(self):
        """Increment failure count, open circuit if threshold reached."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            LOG.error("Circuit breaker opened")
```

---

## Testing Patterns

### Testing with pytest-asyncio

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture
async def async_client():
    """Async fixture for HTTP client."""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
async def db_connection():
    """Async fixture for database connection."""
    conn = await asyncpg.connect(dsn="postgresql://...")
    yield conn
    await conn.close()

@pytest.mark.asyncio
async def test_fetch_user(async_client, db_connection):
    """Test async function with fixtures."""
    user = await fetch_user(db_connection, user_id=1)
    assert user['name'] == 'Test User'

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test multiple concurrent operations."""
    results = await asyncio.gather(
        operation1(),
        operation2(),
        operation3()
    )
    assert len(results) == 3

@pytest.mark.asyncio
async def test_with_timeout():
    """Test that operation completes within timeout."""
    result = await asyncio.wait_for(
        slow_operation(),
        timeout=5.0
    )
    assert result is not None

@pytest.mark.asyncio
async def test_timeout_raises():
    """Test that operation times out correctly."""
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(very_slow_operation(), timeout=1.0)
```

### Mocking Async Dependencies

```python
@pytest.mark.asyncio
async def test_with_mocked_api():
    """Test with mocked async API call."""
    mock_response = {"status": "success", "data": "test"}
    mock_fetch = AsyncMock(return_value=mock_response)

    with patch('module.fetch_api', mock_fetch):
        result = await process_api_data()

    assert result["data"] == "test"
    mock_fetch.assert_awaited_once()

@pytest.mark.asyncio
async def test_with_mocked_context_manager():
    """Test with mocked async context manager."""
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = None
    mock_conn.fetch.return_value = [{"id": 1}]

    async def mock_connect(*args, **kwargs):
        return mock_conn

    with patch('asyncpg.connect', mock_connect):
        result = await fetch_from_database()

    assert len(result) == 1
    mock_conn.execute.assert_called()
```

### Testing Cancellation

```python
@pytest.mark.asyncio
async def test_task_cancellation():
    """Test that task handles cancellation properly."""
    task = asyncio.create_task(long_running_task())

    # Let it start
    await asyncio.sleep(0.1)

    # Cancel task
    task.cancel()

    # Verify cancellation
    with pytest.raises(asyncio.CancelledError):
        await task

    # Verify cleanup happened
    assert cleanup_completed()

@pytest.mark.asyncio
async def test_graceful_shutdown():
    """Test graceful shutdown of async tasks."""
    tasks = [
        asyncio.create_task(worker(i))
        for i in range(5)
    ]

    # Let them run
    await asyncio.sleep(1)

    # Cancel all
    for task in tasks:
        task.cancel()

    # Wait for all to finish
    await asyncio.gather(*tasks, return_exceptions=True)

    # Verify all cleaned up
    assert all(task.cancelled() or task.done() for task in tasks)
```

---

## Performance Optimization

### Optimize Connection Pooling

```python
# BAD - creates new session for each request
async def inefficient_fetching(urls: list[str]):
    results = []
    for url in urls:
        async with aiohttp.ClientSession() as session:  # New session each time!
            async with session.get(url) as response:
                results.append(await response.json())
    return results

# GOOD - reuse session for all requests
async def efficient_fetching(urls: list[str]):
    async with aiohttp.ClientSession() as session:  # Single session
        tasks = [fetch_with_session(session, url) for url in urls]
        return await asyncio.gather(*tasks)

async def fetch_with_session(session, url):
    async with session.get(url) as response:
        return await response.json()
```

### Optimize Database Queries

```python
# BAD - sequential queries
async def slow_batch_insert(records: list[dict]):
    async with asyncpg.connect(dsn) as conn:
        for record in records:  # One at a time!
            await conn.execute(
                "INSERT INTO users (name, email) VALUES ($1, $2)",
                record['name'], record['email']
            )

# GOOD - batch insert
async def fast_batch_insert(records: list[dict]):
    async with asyncpg.connect(dsn) as conn:
        await conn.executemany(
            "INSERT INTO users (name, email) VALUES ($1, $2)",
            [(r['name'], r['email']) for r in records]
        )

# GOOD - use connection pool
from asyncpg import create_pool

async def with_connection_pool():
    pool = await create_pool(dsn, min_size=10, max_size=20)

    async with pool.acquire() as conn:
        await conn.fetch("SELECT * FROM users")

    await pool.close()
```

### Optimize Memory Usage

```python
# BAD - load all results into memory
async def memory_intensive(urls: list[str]):
    all_results = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            async with session.get(url) as response:
                all_results.append(await response.json())  # Keeps all in memory
    return all_results

# GOOD - process results as they arrive
async def memory_efficient(urls: list[str]):
    async with aiohttp.ClientSession() as session:
        for url in urls:
            async with session.get(url) as response:
                data = await response.json()
                await process_and_store(data)  # Process immediately
                # data can be garbage collected

# GOOD - use async generator
async def streaming_results(urls: list[str]):
    async with aiohttp.ClientSession() as session:
        for url in urls:
            async with session.get(url) as response:
                yield await response.json()

# Usage
async def process_streaming():
    async for result in streaming_results(urls):
        await process_result(result)  # One at a time
```

---

## Real-World Examples

### Example: Web Scraper

```python
import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def scrape_website(url: str) -> dict:
    """Scrape single website."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            return {
                'url': url,
                'title': soup.title.string if soup.title else None,
                'links': [a['href'] for a in soup.find_all('a', href=True)]
            }

async def scrape_multiple_websites(
    urls: list[str],
    max_concurrent: int = 10
) -> list[dict]:
    """Scrape multiple websites with rate limiting."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def scrape_with_limit(url: str):
        async with semaphore:
            return await scrape_website(url)

    tasks = [scrape_with_limit(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Example: Background Task Manager

```python
import asyncio
from typing import Callable

class BackgroundTaskManager:
    """Manage long-running background tasks."""

    def __init__(self):
        self.tasks: set[asyncio.Task] = set()

    def create_task(
        self,
        coro: Awaitable,
        name: str | None = None
    ) -> asyncio.Task:
        """Create and track background task."""
        task = asyncio.create_task(coro, name=name)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def cancel_all(self):
        """Cancel all background tasks."""
        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def wait_for_all(self):
        """Wait for all background tasks to complete."""
        await asyncio.gather(*self.tasks, return_exceptions=True)

# Usage
async def main():
    manager = BackgroundTaskManager()

    # Start background tasks
    manager.create_task(background_worker(), name="worker-1")
    manager.create_task(background_worker(), name="worker-2")

    # Do main work
    await main_work()

    # Wait for background tasks to finish
    await manager.wait_for_all()
```

### Example: Async API Client

```python
import asyncio
import aiohttp
from typing import Any

class AsyncAPIClient:
    """Async API client with connection pooling and retry."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None

    async def __aenter__(self):
        """Create session on context entry."""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={'User-Agent': 'AsyncAPIClient/1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session on context exit."""
        if self.session:
            await self.session.close()

    async def get(self, endpoint: str, **kwargs) -> dict[str, Any]:
        """GET request with automatic retry."""
        url = f"{self.base_url}/{endpoint}"
        return await self._request_with_retry('GET', url, **kwargs)

    async def post(
        self,
        endpoint: str,
        data: dict,
        **kwargs
    ) -> dict[str, Any]:
        """POST request with automatic retry."""
        url = f"{self.base_url}/{endpoint}"
        return await self._request_with_retry(
            'POST',
            url,
            json=data,
            **kwargs
        )

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int = 3,
        **kwargs
    ) -> dict[str, Any]:
        """Make request with exponential backoff retry."""
        delay = 1.0

        for attempt in range(max_retries):
            try:
                async with self.session.request(method, url, **kwargs) as resp:
                    resp.raise_for_status()
                    return await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    raise

                LOG.warning(
                    f"Request failed (attempt {attempt + 1}): {e}. "
                    f"Retrying in {delay}s"
                )
                await asyncio.sleep(delay)
                delay *= 2

# Usage
async def fetch_api_data():
    async with AsyncAPIClient("https://api.example.com") as client:
        user = await client.get("users/123")
        posts = await client.get("users/123/posts")
        return user, posts
```

---

## Troubleshooting Guide

### Issue: "RuntimeError: Event loop is closed"

**Cause:** Trying to use event loop after `asyncio.run()` completes.

**Solution:**
```python
# BAD
result1 = asyncio.run(fetch1())
result2 = asyncio.run(fetch2())  # ERROR: loop closed

# GOOD
async def main():
    result1 = await fetch1()
    result2 = await fetch2()
    return result1, result2

asyncio.run(main())
```

### Issue: "RuntimeError: This event loop is already running"

**Cause:** Trying to start event loop from within running event loop.

**Solution:**
```python
# BAD
async def bad():
    result = asyncio.run(fetch())  # ERROR: already in loop

# GOOD
async def good():
    result = await fetch()
```

### Issue: Coroutine Never Executed

**Cause:** Missing `await` keyword.

**Solution:**
```python
# BAD
async def bad():
    result = fetch_data()  # Returns coroutine object, doesn't execute!
    print(result)  # <coroutine object...>

# GOOD
async def good():
    result = await fetch_data()  # Actually executes
    print(result)  # Actual data
```

### Issue: Tasks Don't Run Concurrently

**Cause:** Using `await` in loop instead of `gather()`.

**Solution:**
```python
# BAD - runs sequentially
async def sequential():
    results = []
    for url in urls:
        results.append(await fetch(url))  # One at a time
    return results

# GOOD - runs concurrently
async def concurrent():
    tasks = [fetch(url) for url in urls]
    return await asyncio.gather(*tasks)  # All at once
```

### Issue: "Task was destroyed but it is pending"

**Cause:** Task created but never awaited or cancelled.

**Solution:**
```python
# BAD
async def bad():
    task = asyncio.create_task(background_work())
    return "done"  # Task never awaited or cancelled

# GOOD - await task
async def good_await():
    task = asyncio.create_task(background_work())
    result = await task
    return result

# GOOD - fire and forget with tracking
async def good_fire_forget():
    background_tasks = set()
    task = asyncio.create_task(background_work())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    return "done"
```

### Issue: Slow Performance Despite Async

**Cause:** Blocking the event loop with synchronous operations.

**Solution:**
```python
# BAD - blocks event loop
async def bad():
    time.sleep(5)  # Blocks everything!
    data = requests.get(url)  # Blocks everything!
    return data

# GOOD - use async versions
async def good():
    await asyncio.sleep(5)  # Yields to event loop
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# GOOD - run blocking code in executor
async def good_with_blocking():
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, requests.get, url)
    return data.json()
```

---

## Additional Resources

### Async Libraries

**HTTP Clients:**
- `aiohttp` - Async HTTP client/server
- `httpx` - Modern async HTTP client

**Databases:**
- `asyncpg` - PostgreSQL async driver
- `motor` - MongoDB async driver
- `aiomysql` - MySQL async driver
- `aiosqlite` - SQLite async driver

**File I/O:**
- `aiofiles` - Async file operations

**Testing:**
- `pytest-asyncio` - Pytest plugin for async tests
- `async-asgi-testclient` - Test ASGI apps

**Utilities:**
- `aiocache` - Async cache library
- `aioredis` - Redis async client
- `async-timeout` - Timeout context manager

### Further Reading

- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)
- [AsyncIO best practices](https://github.com/python/asyncio/wiki/AsyncIO-Best-Practices)
