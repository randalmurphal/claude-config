---
name: sqlite-best-practices
description: SQLite best practices including WAL checkpoint timing for multiprocessing, stateful batch connections for atomicity, and performance configuration. Use when working with SQLite in Python projects requiring concurrent access, multi-table atomicity, or multiprocessing.
location: global
type: pattern-library
tags: [sqlite, performance, multiprocessing, atomicity, wal-mode]
---

# SQLite Best Practices

**Purpose**: Universal SQLite patterns for Python projects requiring performance, atomicity, and multiprocessing support.

**When to Use This Skill**:
- Working with SQLite in Python projects (any domain)
- Using multiprocessing or ProcessPoolExecutor with SQLite
- Need multi-table atomicity without explicit transaction management
- Performance optimization for batch operations
- Concurrent read/write access patterns

**Key Patterns**:
1. **WAL Checkpoint Timing** - Critical for multiprocessing worker visibility
2. **Stateful Batch Connection** - Automatic atomicity + performance optimization
3. **WAL Mode Configuration** - Standard pragma settings for concurrent access

---

## Pattern 1: WAL Checkpoint Timing for Multiprocessing (CRITICAL)

### The Problem

**Multiprocessing workers see stale data from SQLite databases.**

When using Python's `ProcessPoolExecutor` or `multiprocessing.Pool`, workers fork from the main process. SQLite's Write-Ahead Log (WAL) mode means uncommitted writes exist only in the WAL file, not the main database. Forked workers see a snapshot of the database **at fork time**, missing any writes made before the fork but not yet checkpointed.

**Symptom**: Workers query empty tables or missing records that main thread just wrote.

### The Solution

**Force WAL checkpoint BEFORE spawning workers.**

```python
from concurrent.futures import ProcessPoolExecutor
import sqlite3

# Main thread writes data
conn = sqlite3.connect('data.db')
cursor = conn.cursor()
cursor.execute("INSERT INTO records VALUES (1, 'data')")
conn.commit()  # Commits to WAL, NOT main DB yet

# CRITICAL: Force checkpoint before forking workers
cursor.execute("PRAGMA wal_checkpoint(FULL)")
conn.close()

# Now safe to spawn workers
with ProcessPoolExecutor(max_workers=5) as executor:
    results = executor.map(worker_function, task_args)
```

**WHY This Works**:
1. `commit()` writes to WAL file (fast, but workers won't see it)
2. `PRAGMA wal_checkpoint(FULL)` moves WAL contents to main DB file
3. Workers fork AFTER checkpoint, see all committed data

**Checkpoint Modes**:
- `PASSIVE` - Checkpoint if possible, don't block (may fail if readers active)
- `FULL` - Wait for readers, checkpoint everything (recommended)
- `RESTART` - Like FULL, but also deletes WAL file
- `TRUNCATE` - Like RESTART, but truncates WAL to zero bytes

**Recommendation**: Use `FULL` for multiprocessing (ensures workers see data).

### Implementation Pattern

**Using SQLAlchemy**:

```python
from sqlalchemy import create_engine, text

class DataHandler:
    def __init__(self, db_path: str):
        self.engine = create_engine(f'sqlite:///{db_path}')

    def checkpoint_wal(
        self,
        mode: Literal['PASSIVE', 'FULL', 'RESTART', 'TRUNCATE'] = 'FULL'
    ) -> None:
        """Force WAL checkpoint before spawning workers.

        WHY: Ensures workers see all committed writes from main thread.
        ALWAYS call after batch writes, before ProcessPoolExecutor.
        """
        # CRITICAL: Commit any pending transaction first
        with self.engine.begin() as conn:
            conn.commit()  # Ensure WAL has latest data

        # Force checkpoint to move WAL → main DB
        with self.engine.begin() as conn:
            conn.exec_driver_sql(f'PRAGMA wal_checkpoint({mode})')

# Usage
handler = DataHandler('cache.db')

# Write data
with handler.engine.begin() as conn:
    conn.execute(text("INSERT INTO cache VALUES (:id, :data)"),
                 [{'id': i, 'data': f'record_{i}'} for i in range(1000)])

# CRITICAL: Checkpoint before multiprocessing
handler.checkpoint_wal()

# Now safe to spawn workers
with ProcessPoolExecutor(max_workers=10) as executor:
    results = executor.map(worker_func, range(10))
```

**Using sqlite3 directly**:

```python
import sqlite3
from concurrent.futures import ProcessPoolExecutor

def prepare_database_for_workers(db_path: str):
    """Ensure workers will see all data."""
    conn = sqlite3.connect(db_path)

    # Force commit + checkpoint
    conn.commit()
    conn.execute("PRAGMA wal_checkpoint(FULL)")
    conn.close()

# Main thread workflow
conn = sqlite3.connect('work.db')
cursor = conn.cursor()

# Bulk insert
cursor.executemany(
    "INSERT INTO tasks VALUES (?, ?)",
    [(i, f'task_{i}') for i in range(10000)]
)
conn.commit()

# CRITICAL: Checkpoint before workers
cursor.execute("PRAGMA wal_checkpoint(FULL)")
conn.close()

# Workers now see all 10K tasks
with ProcessPoolExecutor(max_workers=5) as executor:
    results = executor.map(process_task, range(5))
```

### Common Gotchas

**Gotcha 1: Checkpoint without commit**

```python
# WRONG - workers won't see uncommitted data
conn.execute("INSERT INTO records ...")
conn.execute("PRAGMA wal_checkpoint(FULL)")  # Checkpoints COMMITTED data only
```

**Fix**: Always commit before checkpoint.

```python
# RIGHT
conn.execute("INSERT INTO records ...")
conn.commit()  # Commit to WAL first
conn.execute("PRAGMA wal_checkpoint(FULL)")  # Then checkpoint WAL → DB
```

**Gotcha 2: Checkpoint in worker instead of main**

```python
# WRONG - workers already forked, too late
def worker(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA wal_checkpoint(FULL)")  # Useless - already forked
```

**Fix**: Checkpoint in main thread BEFORE forking.

```python
# RIGHT - main thread checkpoints before spawning
conn.execute("PRAGMA wal_checkpoint(FULL)")
conn.close()

with ProcessPoolExecutor() as executor:
    executor.map(worker, args)
```

**Gotcha 3: Forgetting checkpoint with concurrent reads**

If main thread writes, then immediately spawns workers to read:

```python
# WRONG - race condition
def main():
    write_to_db()  # Commits to WAL
    with ProcessPoolExecutor() as executor:
        executor.map(read_from_db, args)  # May see stale data
```

**Fix**: Explicit checkpoint between write and fork.

```python
# RIGHT
def main():
    write_to_db()
    checkpoint_wal()  # Force WAL → main DB
    with ProcessPoolExecutor() as executor:
        executor.map(read_from_db, args)  # All workers see latest
```

### Real-World Example

**Tenable SC Refactor - Asset Cascade Matching**

```python
# Source: tenable_sc_refactor/tenable_sc_import.py:647-780

# Phase 1: CASCADE matching writes matched_asset_id to cache
with AssetCascadeMatcher(...) as matcher:
    matcher.run_cascade()  # Writes to cache.sumip_records

# Phase 2: CRITICAL CHECKPOINT before union-find workers
cache.checkpoint_wal()  # Force visibility

# Phase 3: Workers now see all CASCADE results
with ProcessPoolExecutor(max_workers=10) as executor:
    # Workers read matched_asset_id from cache.sumip_records
    groups = asset_union_find.build_groups()
```

**WHY**: Without checkpoint, workers query `sumip_records.matched_asset_id` and see `NULL` for records updated by CASCADE (WAL not visible to forked workers).

---

## Pattern 2: Stateful Batch Connection for Atomicity

### The Problem

**Multi-table operations need atomicity without explicit transaction management.**

When processing data in batches (e.g., 5000 records per commit), you want:
1. **Atomicity**: All writes in a batch succeed or all fail (multi-table)
2. **Performance**: Batch commits (not commit-per-row)
3. **Automatic**: No manual `BEGIN/COMMIT` in business logic

**Naive approach fails atomicity**:

```python
# WRONG - each insert is separate transaction
for record in records:
    conn.execute("INSERT INTO table1 ...")
    conn.execute("INSERT INTO table2 ...")  # May fail, table1 already written
```

**Explicit transactions are verbose**:

```python
# WORKS but verbose + error-prone
conn.execute("BEGIN")
try:
    for record in batch:
        conn.execute("INSERT INTO table1 ...")
        conn.execute("INSERT INTO table2 ...")
    conn.execute("COMMIT")
except:
    conn.execute("ROLLBACK")
    raise
```

### The Solution

**Reuse connection with automatic batch commits.**

Maintain a single connection with open transaction, commit at configurable threshold (e.g., 5000 operations).

```python
class BatchHandler:
    def __init__(self, db_path: str, batch_size: int = 5000):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.batch_size = batch_size
        self._batch_conn_mgr = None  # Context manager
        self._batch_conn = None      # Active connection
        self._ops_since_commit = 0   # Operation counter

    def _get_batch_connection(self):
        """Get or create connection with open transaction.

        WHY: Reuse connection across operations for atomicity.
        Multi-table writes in same transaction automatically atomic.
        """
        if self._batch_conn is None:
            # Create context manager and enter transaction
            self._batch_conn_mgr = self.engine.begin()
            self._batch_conn = self._batch_conn_mgr.__enter__()
        return self._batch_conn

    def _commit_batch_if_needed(self) -> None:
        """Auto-commit when threshold reached.

        WHY: Performance - batch 5000 ops per commit instead of
        commit-per-operation.
        """
        if self._ops_since_commit >= self.batch_size:
            if self._batch_conn_mgr is not None:
                try:
                    # Exit context manager (triggers commit)
                    self._batch_conn_mgr.__exit__(None, None, None)
                finally:
                    self._batch_conn_mgr = None
                    self._batch_conn = None
            self._ops_since_commit = 0

    def insert_record(self, table: str, data: dict):
        """Insert with automatic batching.

        Multi-table inserts in same batch are atomic.
        """
        conn = self._get_batch_connection()
        conn.execute(text(f"INSERT INTO {table} ..."), data)
        self._ops_since_commit += 1
        self._commit_batch_if_needed()

    def commit_batch(self) -> None:
        """Force commit of incomplete batch.

        WHY: Ensure persistence before checkpoint or process exit.
        """
        if self._batch_conn_mgr is not None:
            try:
                self._batch_conn_mgr.__exit__(None, None, None)
            finally:
                self._batch_conn_mgr = None
                self._batch_conn = None
        self._ops_since_commit = 0

    def rollback_batch(self) -> None:
        """Rollback current batch on error.

        WHY: Discard uncommitted ops, maintain atomicity.
        """
        if self._batch_conn_mgr is not None:
            try:
                exc_info = (Exception, Exception('Rollback'), None)
                self._batch_conn_mgr.__exit__(*exc_info)
            finally:
                self._batch_conn_mgr = None
                self._batch_conn = None
        self._ops_since_commit = 0
```

### Usage Example

**Multi-table atomicity automatically guaranteed**:

```python
handler = BatchHandler('cache.db', batch_size=5000)

# Process 10K records
for record in records:  # 10,000 records
    # Both inserts in SAME transaction
    handler.insert_record('table1', {'id': record.id, 'data': record.data})
    handler.insert_record('table2', {'id': record.id, 'meta': record.meta})

    # Auto-commits every 5000 operations
    # Operations 1-5000 in transaction 1
    # Operations 5001-10000 in transaction 2

# Force commit of last batch (10000 % 5000 = 0, but good practice)
handler.commit_batch()
```

**Error handling with rollback**:

```python
handler = BatchHandler('cache.db')

try:
    for record in records:
        handler.insert_record('assets', record.to_dict())

        # Validation error on record 3500
        if not record.is_valid():
            raise ValueError("Invalid record")

except Exception as e:
    # Rollback uncommitted operations (ops 3001-3500)
    handler.rollback_batch()
    raise
```

### Benefits

1. **Automatic Atomicity**: Multi-table writes in same batch atomic (no explicit transactions)
2. **Performance**: Batch commits (5000 ops/commit) vs commit-per-operation
3. **Clean API**: Business logic doesn't manage `BEGIN/COMMIT`
4. **Automatic Cleanup**: Context manager ensures commit/rollback on exit

### Real-World Example

**Tenable SC Refactor - SQLiteHandler**

```python
# Source: tenable_sc_refactor/sqlite_handlers/sqlite_handler.py:1308-1371

class SQLiteHandler:
    def __init__(self, db_path: str, commit_batch_size: int = 5000):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.commit_batch_size = commit_batch_size
        self._batch_conn_mgr = None
        self._batch_conn = None
        self._ops_since_commit = 0

    def execute_write(self, stmt):
        """Execute write with automatic batching."""
        conn = self._get_batch_connection()
        conn.execute(stmt)
        self._ops_since_commit += 1
        self._commit_batch_if_needed()

    def execute_write_many(self, stmt, params_list: list[dict]):
        """Bulk insert with automatic batching."""
        conn = self._get_batch_connection()
        conn.execute(stmt, params_list)
        self._ops_since_commit += len(params_list)
        self._commit_batch_if_needed()

# Usage - multi-table atomicity automatic
handler = SQLiteHandler('cache.db')

# All writes in same batch are atomic
handler.execute_write(insert_asset_stmt)      # Op 1
handler.execute_write(insert_mac_stmt)        # Op 2
handler.execute_write(insert_dns_stmt)        # Op 3
# ... 4997 more operations ...
handler.execute_write(insert_ip_stmt)         # Op 5000 - triggers auto-commit

# Next operation starts new transaction
handler.execute_write(insert_asset_stmt)      # Op 1 of batch 2
```

**Result**: 10K multi-table inserts complete in 2 transactions (5000 ops each), all automatically atomic.

---

## Pattern 3: WAL Mode Configuration

### The Problem

**SQLite defaults to DELETE journal mode, which:**
- Blocks readers during writes (exclusive locking)
- Slower for concurrent access
- No reader/writer concurrency

### The Solution

**Enable WAL mode with performance pragmas.**

WAL (Write-Ahead Logging) enables:
- Concurrent readers + single writer
- Faster writes (append-only WAL file)
- Better crash recovery

```python
import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Enable WAL mode
cursor.execute('PRAGMA journal_mode=WAL')

# Performance pragmas
cursor.execute('PRAGMA synchronous=NORMAL')   # Balance safety/performance
cursor.execute('PRAGMA temp_store=MEMORY')    # Temp tables in RAM
cursor.execute('PRAGMA busy_timeout=30000')   # Wait 30s for locks
cursor.execute('PRAGMA cache_size=-64000')    # 64MB page cache

conn.commit()
```

### Pragma Explanations

| Pragma | Value | WHY | Trade-off |
|--------|-------|-----|-----------|
| `journal_mode` | `WAL` | Concurrent reads, faster writes | Creates `-wal` and `-shm` files |
| `synchronous` | `NORMAL` | Fast writes, safe enough for most apps | Small corruption risk on power loss |
| `temp_store` | `MEMORY` | Faster temp tables/indexes | Uses more RAM |
| `busy_timeout` | `30000` (30s) | Wait for locks instead of failing | May hang if deadlock |
| `cache_size` | `-64000` (64MB) | More cached pages = fewer disk reads | Uses more RAM |

**Synchronous Modes**:
- `OFF` - Fastest, unsafe (corruption on crash)
- `NORMAL` - Fast, safe for most apps (recommended)
- `FULL` - Safest, slower (guarantees no corruption)

### SQLAlchemy Pattern

**Configure pragmas on every connection**:

```python
from sqlalchemy import create_engine, event

engine = create_engine('sqlite:///data.db')

@event.listens_for(engine, 'connect')
def set_sqlite_pragma(dbapi_conn, _connection_record):
    """Configure SQLite on every new connection.

    WHY: Connection pool may create new connections, must configure each.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('PRAGMA synchronous=NORMAL')
    cursor.execute('PRAGMA temp_store=MEMORY')
    cursor.execute('PRAGMA busy_timeout=30000')
    cursor.execute('PRAGMA cache_size=-64000')
    cursor.close()
```

**WHY Event Listener**: SQLAlchemy connection pool creates new connections. Each needs pragma configuration.

### Verification

**Check current settings**:

```python
cursor.execute('PRAGMA journal_mode')
print(cursor.fetchone())  # Should print: ('wal',)

cursor.execute('PRAGMA synchronous')
print(cursor.fetchone())  # Should print: (1,) for NORMAL
```

### Real-World Example

**Tenable SC Refactor - SQLiteHandler Initialization**

```python
# Source: tenable_sc_refactor/sqlite_handlers/sqlite_handler.py:137-148

@event.listens_for(self._engine, 'connect')
def set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('PRAGMA synchronous=NORMAL')
    cursor.execute('PRAGMA temp_store=MEMORY')
    cursor.execute('PRAGMA busy_timeout=30000')
    cursor.execute('PRAGMA group_concat_max_len=10000000')  # Domain-specific
    cursor.close()
```

**Result**: All connections automatically configured for concurrent access and performance.

---

## Common Pitfalls

### Pitfall 1: Connection Pooling with WAL

**Problem**: SQLAlchemy connection pool may not checkpoint automatically.

```python
# WRONG - pool never checkpoints, WAL grows unbounded
engine = create_engine('sqlite:///data.db', pool_size=10)

for i in range(100000):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO records ..."))
# WAL file now 2GB, main DB still small
```

**Fix**: Explicit checkpoint after batch operations.

```python
# RIGHT - periodic checkpoints prevent WAL bloat
engine = create_engine('sqlite:///data.db', pool_size=10)

for batch_num in range(100):
    for i in range(1000):
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO records ..."))

    # Checkpoint every 1000 records
    with engine.begin() as conn:
        conn.exec_driver_sql('PRAGMA wal_checkpoint(PASSIVE)')
```

### Pitfall 2: Forgetting to Close Connections Before Fork

**Problem**: Open connections before fork cause corruption.

```python
# WRONG - connection open during fork
conn = sqlite3.connect('data.db')
conn.execute("INSERT INTO records ...")

with ProcessPoolExecutor() as executor:
    executor.map(worker, args)  # Workers inherit open connection - CORRUPTION
```

**Fix**: Close all connections before forking.

```python
# RIGHT - close before fork
conn = sqlite3.connect('data.db')
conn.execute("INSERT INTO records ...")
conn.commit()
conn.close()  # CRITICAL: Close before fork

with ProcessPoolExecutor() as executor:
    executor.map(worker, args)
```

### Pitfall 3: WAL Mode Per-Connection

**Problem**: PRAGMA journal_mode is persistent, but synchronous is per-connection.

```python
# WRONG - assumes PRAGMA persists across connections
conn1 = sqlite3.connect('data.db')
conn1.execute('PRAGMA synchronous=NORMAL')
conn1.close()

conn2 = sqlite3.connect('data.db')
# conn2 uses default synchronous=FULL (slower)
```

**Fix**: Set pragmas on EVERY connection (use event listener in SQLAlchemy).

```python
# RIGHT - configure every connection
def get_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA synchronous=NORMAL')
    return conn

conn1 = get_connection('data.db')
conn2 = get_connection('data.db')  # Both configured
```

### Pitfall 4: Batch Size Too Large

**Problem**: Large batches consume RAM and delay visibility.

```python
# WRONG - 1M operations in single transaction
handler = BatchHandler('data.db', batch_size=1000000)

for i in range(1000000):
    handler.insert_record('records', {'id': i})  # All in RAM until commit
```

**Fix**: Reasonable batch size (5000-10000 operations).

```python
# RIGHT - 5K operations per transaction
handler = BatchHandler('data.db', batch_size=5000)

for i in range(1000000):
    handler.insert_record('records', {'id': i})
# Auto-commits every 5K records
```

**Guidance**: Batch size 5000-10000 balances performance and resource usage.

---

## Integration Patterns

### Pattern: WAL + Batch + Multiprocessing

**Complete workflow for high-performance SQLite with multiprocessing**:

```python
from concurrent.futures import ProcessPoolExecutor
from sqlalchemy import create_engine, event, text

class DataProcessor:
    def __init__(self, db_path: str, batch_size: int = 5000):
        self.db_path = db_path
        self.batch_size = batch_size
        self.engine = self._create_engine()
        self._batch_conn_mgr = None
        self._batch_conn = None
        self._ops_since_commit = 0

    def _create_engine(self):
        """Create engine with WAL mode enabled."""
        engine = create_engine(f'sqlite:///{self.db_path}')

        @event.listens_for(engine, 'connect')
        def set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA synchronous=NORMAL')
            cursor.execute('PRAGMA busy_timeout=30000')
            cursor.close()

        return engine

    def _get_batch_connection(self):
        """Reuse connection for atomicity."""
        if self._batch_conn is None:
            self._batch_conn_mgr = self.engine.begin()
            self._batch_conn = self._batch_conn_mgr.__enter__()
        return self._batch_conn

    def _commit_batch_if_needed(self):
        """Auto-commit at threshold."""
        if self._ops_since_commit >= self.batch_size:
            if self._batch_conn_mgr is not None:
                self._batch_conn_mgr.__exit__(None, None, None)
                self._batch_conn_mgr = None
                self._batch_conn = None
            self._ops_since_commit = 0

    def insert_record(self, table: str, data: dict):
        """Insert with batching."""
        conn = self._get_batch_connection()
        conn.execute(text(f"INSERT INTO {table} VALUES (:id, :data)"), data)
        self._ops_since_commit += 1
        self._commit_batch_if_needed()

    def commit_batch(self):
        """Force commit."""
        if self._batch_conn_mgr is not None:
            self._batch_conn_mgr.__exit__(None, None, None)
            self._batch_conn_mgr = None
            self._batch_conn = None
        self._ops_since_commit = 0

    def checkpoint_wal(self):
        """Checkpoint before workers."""
        self.commit_batch()  # Commit pending ops
        with self.engine.begin() as conn:
            conn.exec_driver_sql('PRAGMA wal_checkpoint(FULL)')

    def process_data(self, records: list):
        """Main processing with multiprocessing."""
        # Phase 1: Bulk insert with batching
        for record in records:
            self.insert_record('staging', record)
        self.commit_batch()

        # Phase 2: CRITICAL - Checkpoint before workers
        self.checkpoint_wal()

        # Phase 3: Workers process staged data
        with ProcessPoolExecutor(max_workers=10) as executor:
            results = executor.map(self._worker, range(10))

        return list(results)

    @staticmethod
    def _worker(worker_id: int):
        """Worker reads from staging (sees all data after checkpoint)."""
        # Each worker creates own connection
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM staging
            WHERE id % 10 = ?
        """, (worker_id,))

        results = cursor.fetchall()
        conn.close()
        return results

# Usage
processor = DataProcessor('data.db')
records = [{'id': i, 'data': f'record_{i}'} for i in range(100000)]
results = processor.process_data(records)
```

**This pattern combines**:
1. WAL mode configuration (concurrent access)
2. Stateful batch connections (atomicity + performance)
3. WAL checkpoints (multiprocessing visibility)

---

## Performance Characteristics

### Batch Size Impact

| Batch Size | Commits (100K records) | RAM Usage | Visibility Latency |
|------------|------------------------|-----------|-------------------|
| 1 | 100,000 | Low | Immediate |
| 1,000 | 100 | Medium | 1K records |
| 5,000 | 20 | Good | 5K records |
| 10,000 | 10 | High | 10K records |
| 100,000 | 1 | Very High | All records |

**Recommendation**: 5,000-10,000 operations per batch.

### WAL Checkpoint Overhead

| Mode | Duration (1M records) | Blocks Writers? | Blocks Readers? |
|------|----------------------|-----------------|-----------------|
| PASSIVE | <1s | No | No |
| FULL | 2-5s | No | Yes (briefly) |
| RESTART | 2-5s | No | Yes (briefly) |
| TRUNCATE | 2-5s | No | Yes (briefly) |

**Guidance**: Use `FULL` for multiprocessing (ensures consistency), `PASSIVE` for periodic cleanup.

---

## Troubleshooting Guide

### Problem: Workers See Empty Tables

**Symptom**: Main thread inserts records, workers query and get 0 rows.

**Cause**: Forgot WAL checkpoint before fork.

**Fix**:
```python
# Add checkpoint before ProcessPoolExecutor
cache.commit_batch()
cache.checkpoint_wal()  # CRITICAL
with ProcessPoolExecutor() as executor:
    ...
```

### Problem: Database Locked Errors

**Symptom**: `sqlite3.OperationalError: database is locked`

**Cause**: `busy_timeout` too low or connection not closed.

**Fix**:
```python
# Increase busy_timeout
cursor.execute('PRAGMA busy_timeout=30000')  # 30 seconds

# Ensure connections closed
try:
    conn = sqlite3.connect('data.db')
    # ... operations ...
finally:
    conn.close()  # ALWAYS close
```

### Problem: WAL File Growing Large

**Symptom**: `.db-wal` file is GB in size, main DB file small.

**Cause**: No periodic checkpoints.

**Fix**:
```python
# Add periodic PASSIVE checkpoints
for i in range(0, len(records), 10000):
    batch = records[i:i+10000]
    process_batch(batch)

    # Checkpoint every 10K records
    conn.execute('PRAGMA wal_checkpoint(PASSIVE)')
```

### Problem: Slow Concurrent Reads

**Symptom**: Queries slow when writer active.

**Cause**: Not using WAL mode (DELETE journal mode blocks readers).

**Fix**:
```python
# Enable WAL mode
cursor.execute('PRAGMA journal_mode=WAL')
cursor.execute('PRAGMA synchronous=NORMAL')
```

---

## Summary

### Critical Patterns

1. **WAL Checkpoint Before Fork**
   - ALWAYS checkpoint after main thread writes, before ProcessPoolExecutor
   - Use `PRAGMA wal_checkpoint(FULL)` for guaranteed visibility
   - Commit before checkpoint (checkpoint only affects committed data)

2. **Stateful Batch Connection**
   - Reuse connection across operations for multi-table atomicity
   - Auto-commit at threshold (5000-10000 operations)
   - Explicit `commit_batch()` before checkpoint or exit

3. **WAL Mode Configuration**
   - Enable on every connection (use event listener in SQLAlchemy)
   - Set `synchronous=NORMAL` for performance
   - Configure `busy_timeout=30000` for lock contention

### Decision Matrix

| Requirement | Pattern | Implementation |
|-------------|---------|----------------|
| Multiprocessing | WAL checkpoint | `checkpoint_wal()` before `ProcessPoolExecutor` |
| Multi-table atomicity | Stateful batch connection | Reuse connection, auto-commit at threshold |
| Concurrent access | WAL mode | `PRAGMA journal_mode=WAL` on every connection |
| Batch performance | Batched commits | 5000-10000 ops per commit |

### Related Skills

- **python-style** - Type hints, error handling, logging patterns
- **code-refactoring** - When to extract helpers, complexity thresholds
- **async-python** - Alternative to multiprocessing for I/O-bound tasks

---

## Source Implementation

**Reference**: Tenable SC Refactor import (universal patterns extracted from production code)

**Key Files**:
- `sqlite_handlers/sqlite_handler.py` - Stateful batch connection pattern (lines 1308-1430)
- `tenable_sc_import.py` - WAL checkpoint timing for workers (line 769)
- WAL mode configuration via event listener (lines 137-148)

**Verification**: Integration test validates 100% data visibility across 10 parallel workers processing 2.5M records.
