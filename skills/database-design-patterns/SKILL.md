---
name: database-design-patterns
description: Database schema design including normalization, denormalization, indexes, migrations, foreign keys, constraints, and query optimization. Covers PostgreSQL, MySQL, and general SQL patterns. Use when designing database schemas, optimizing queries, setting up migrations, or debugging performance issues.
allowed-tools: [Read, Bash, Grep]
---

# Database Design Patterns

## Core Principles

- **Start normalized, denormalize strategically** - Normalize to 3NF first, then denormalize based on measured performance needs
- **Indexes are not free** - Every index speeds reads but slows writes
- **Constraints enforce integrity** - Use database constraints over application logic
- **Migrations are one-way** - Design migrations to be reversible, but assume rollbacks are rare
- **Query patterns drive design** - Optimize schema for 80% of queries, not edge cases

### Database Selection

| Database | Best For | Avoid For |
|----------|----------|-----------|
| PostgreSQL | Complex queries, JSONB, full-text search | Simple key-value, extreme write throughput |
| MySQL | High concurrency reads, replication | Complex JSON queries, advanced functions |
| SQLite | Embedded apps, development | High concurrency, large datasets (>100GB) |

## Normalization

### Normal Forms

**1NF:** Atomic values, unique rows, no repeating groups
**2NF:** 1NF + no partial dependencies
**3NF:** 2NF + no transitive dependencies

**Stop at 3NF when:**
- Query performance suffers (measured)
- Join complexity unmaintainable
- Read-heavy (>95% reads)

### Example

**Before (unnormalized):**
```sql
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_name VARCHAR(100),
    product_names TEXT,  -- "Widget,Gadget"
    product_prices TEXT  -- "10.00,25.00"
);
```

**After (3NF):**
```sql
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
```

## Denormalization

### When to Denormalize

**Valid:** Measured performance issues, read:write >100:1, frequent aggregations
**Invalid:** "Joins are slow" without measurement, avoiding SQL

### Patterns

**Computed columns:**
```sql
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    total_price DECIMAL(10,2) NOT NULL,  -- Denormalized sum
    item_count INT NOT NULL
);
```

**Materialized views (PostgreSQL):**
```sql
CREATE MATERIALIZED VIEW monthly_sales AS
SELECT DATE_TRUNC('month', order_date) AS month,
       COUNT(*) AS order_count
FROM orders GROUP BY 1;

REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_sales;
```

**Redundant FK data:**
```sql
CREATE TABLE orders (
    customer_name VARCHAR(100) NOT NULL  -- Redundant from customers
);
```

### Tradeoffs

| Pattern | Read Speed | Write Speed | Consistency Risk |
|---------|------------|-------------|------------------|
| Computed columns | Fast | Slower | Low (triggers) |
| Materialized views | Very fast | No impact | Medium (stale) |
| Redundant FK | Fast | Slower | High (sync) |

## Indexes

### Types

**B-Tree (default):** Equality, ranges, sorting
```sql
CREATE INDEX idx_orders_customer ON orders(customer_id);
```

**GIN:** Full-text, JSONB, arrays
```sql
CREATE INDEX idx_users_metadata ON users USING GIN (metadata jsonb_path_ops);
```

**Partial:** Index subset
```sql
CREATE INDEX idx_active_users ON users(last_login) WHERE status = 'active';
```

**Composite:** Multi-column (order matters)
```sql
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
-- Supports: WHERE customer_id = X
-- Supports: WHERE customer_id = X AND order_date > Y
-- NOT: WHERE order_date > Y (only second column)
```

### Selection Strategy

**Always index:**
- Foreign keys (not automatic!)
- WHERE clause columns
- JOIN conditions

**Avoid indexing:**
- Low cardinality (boolean, 2-3 values)
- Small tables (<1000 rows)
- Never-queried columns

### Maintenance

**Check usage (PostgreSQL):**
```sql
SELECT indexname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
ORDER BY idx_scan;
-- Zero scans = unused
```

## Constraints

### Types

**NOT NULL, UNIQUE:**
```sql
CREATE TABLE users (
    email VARCHAR(100) UNIQUE NOT NULL
);
```

**CHECK:**
```sql
CREATE TABLE products (
    price DECIMAL(10,2) CHECK (price >= 0),
    status VARCHAR(20) CHECK (status IN ('active', 'discontinued'))
);
```

**FOREIGN KEY:**
```sql
CREATE TABLE orders (
    customer_id INT REFERENCES customers(customer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
```

### Cascade Options

| Option | DELETE Behavior | Use Case |
|--------|----------------|----------|
| CASCADE | Delete children | Order items with order |
| RESTRICT | Prevent | Products in use |
| SET NULL | Set NULL | Optional relationships |
| NO ACTION | Error | Default, safest |

### Best Practices

**Use database constraints:**
```sql
-- GOOD
CREATE TABLE users (
    email VARCHAR(100) UNIQUE NOT NULL CHECK (email LIKE '%@%')
);

-- BAD: Only app validates
CREATE TABLE users (
    email VARCHAR(100)
);
```

**Name constraints:**
```sql
CONSTRAINT chk_price_positive CHECK (price > 0),
CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
```

## Migrations

### Principles

- Be reversible
- Be idempotent
- Minimize downtime
- Preserve data

### Safe Patterns

**Add column:**
```sql
ALTER TABLE users ADD COLUMN last_login TIMESTAMP DEFAULT NULL;
CREATE INDEX CONCURRENTLY idx_users_last_login ON users(last_login);
```

**Add NOT NULL (multi-step):**
```sql
-- Step 1: Add nullable with default
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';
-- Step 2: Backfill
UPDATE users SET status = 'active' WHERE status IS NULL;
-- Step 3: Add constraint
ALTER TABLE users ALTER COLUMN status SET NOT NULL;
```

**Rename column (multi-step):**
```sql
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN email_address VARCHAR(100);
-- Step 2: Backfill
UPDATE users SET email_address = email;
-- Step 3: Deploy code reading both
-- Step 4: Deploy code writing both
-- Step 5: Deploy code using new only
-- Step 6: Drop old
ALTER TABLE users DROP COLUMN email;
```

### Zero-Downtime Checklist

- [ ] Add columns with defaults (not NULL)
- [ ] Create indexes CONCURRENTLY
- [ ] Backfill in batches
- [ ] Deploy code before schema changes (removals)
- [ ] Test rollback

## Query Optimization

### EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE
SELECT o.order_id, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date > '2024-01-01';

-- Look for:
-- Seq Scan (bad for large tables)
-- Index Scan (good)
-- High cost estimates
```

### Patterns

**Filter before join:**
```sql
-- GOOD
SELECT o.order_id, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date > '2024-01-01' AND c.status = 'active';

-- BAD: OR prevents optimization
WHERE o.order_date > '2024-01-01' OR c.status = 'active';
```

**Avoid N+1:**
```sql
-- BAD: N+1 queries
SELECT * FROM customers;
-- Then for each: SELECT * FROM orders WHERE customer_id = ?;

-- GOOD: Single query
SELECT c.*, o.*
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id;
```

### Anti-Patterns

**SELECT *:**
```sql
-- BAD
SELECT * FROM users WHERE user_id = 123;
-- GOOD
SELECT user_id, name, email FROM users WHERE user_id = 123;
```

**OR in WHERE:**
```sql
-- BAD
WHERE category = 'books' OR category = 'electronics';
-- GOOD
WHERE category IN ('books', 'electronics');
```

**Functions on indexed columns:**
```sql
-- BAD: Prevents index
WHERE LOWER(email) = 'user@example.com';
-- GOOD: Functional index
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
```

**Implicit conversion:**
```sql
-- BAD: customer_id is INT
WHERE customer_id = '123';
-- GOOD
WHERE customer_id = 123;
```

## Quick Reference

### Common Schemas

```sql
-- User auth
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit trail
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    action VARCHAR(10),
    changed_by INT REFERENCES users(user_id),
    old_values JSONB,
    new_values JSONB
);

-- Soft deletes
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    deleted_at TIMESTAMP DEFAULT NULL
);
CREATE INDEX idx_products_active ON products(product_id)
WHERE deleted_at IS NULL;

-- Many-to-many
CREATE TABLE users_roles (
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    role_id INT REFERENCES roles(role_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);
```

### Performance Checklist

- [ ] Foreign keys indexed
- [ ] WHERE columns indexed
- [ ] No SELECT *
- [ ] No OR in WHERE (use IN)
- [ ] No functions on indexed columns
- [ ] Correct data types
- [ ] EXPLAIN shows index scans
- [ ] Queries return <1000 rows
- [ ] Connection pooling configured

### PostgreSQL Advantages

- JSONB with indexing
- Full-text search
- Array types with GIN
- Window functions
- CTEs and recursive queries
- LISTEN/NOTIFY

### MySQL Advantages

- Better replication
- Simpler for CRUD
- Wider hosting support
- Read-heavy workloads
