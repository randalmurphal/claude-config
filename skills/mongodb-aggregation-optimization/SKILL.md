---
name: MongoDB Aggregation Pipeline Optimization
description: General MongoDB aggregation pipeline optimization techniques including early filtering, index usage, array operators vs $unwind, $lookup optimization, and performance debugging. Use when writing aggregation queries for ANY MongoDB project, debugging slow pipelines, or analyzing query performance. For M32RIMM-specific patterns, use mongodb-m32rimm-patterns skill.
allowed-tools: [Read, Grep, Bash]
---

# MongoDB Aggregation Pipeline Optimization

General optimization patterns for MongoDB aggregation pipelines. Applicable to ANY MongoDB project, regardless of domain or schema.

**Project-Specific Skills**:
- For M32RIMM/FISIO patterns, see `mongodb-m32rimm-patterns` skill (subscription isolation, businessObjects queries, DV/Asset aggregations)

---

## 1. Pipeline Stage Ordering (MOST CRITICAL)

**Early filtering rule**: Place `$match` as early as possible to reduce data volume.

**Optimal stage order**:
```
$match → $project → $addFields → $lookup → $unwind → $group → $sort → $limit
```

**Why this matters**: MongoDB processes pipeline stages sequentially. Filtering 1M docs to 10K BEFORE $lookup saves 990K unnecessary joins.

### Performance Impact

| Optimization | Speedup | Example |
|--------------|---------|---------|
| Early $match | 10-100x | Filter by tenant/status first |
| Project before lookup | 5-20x | Reduce field count before join |
| Covered queries | 5-10x | Return data from index only |
| Array operators vs $unwind | 5-10x | Filter arrays without unwinding |
| Indexed $lookup | 10-50x | Join on indexed fields |

### Stage Ordering Examples

```javascript
// BAD - filters AFTER expensive operations
db.orders.aggregate([
    {$lookup: {from: 'customers', ...}},  // Joins ALL docs
    {$unwind: '$items'},
    {$match: {status: 'pending'}}         // Filters last
])

// GOOD - filters early, reduces data before expensive ops
db.orders.aggregate([
    {$match: {status: 'pending'}},        // Filter first
    {$project: {_id: 1, items: 1}},       // Reduce fields
    {$lookup: {from: 'customers', ...}}   // Join smaller set
])
```

### MongoDB's Automatic Optimization

MongoDB can move `$match` before `$project` when safe:
```javascript
// Written as:
[
    {$project: {_id: 1, status: 1, amount: 1}},
    {$match: {status: 'pending', amount: {$gt: 100}}}
]

// MongoDB optimizes to:
[
    {$match: {status: 'pending', amount: {$gt: 100}}},
    {$project: {_id: 1, status: 1, amount: 1}}
]
```

**BUT**: Don't rely on this. Write explicit early $match for clarity.

---

## 2. Index Usage & Covered Queries

### Check Index Usage

```javascript
// Explain aggregation execution
db.collection.explain('executionStats').aggregate([
    {$match: {status: 'active', category: 'electronics'}},
    {$project: {_id: 1, name: 1}}
])

// Key fields to check:
// - totalDocsExamined (should be close to nReturned)
// - executionTimeMillis (lower is better)
// - winningPlan.stage (IXSCAN = good, COLLSCAN = bad)
```

### Covered Queries

**Definition**: Query returns all data from index (no document fetch).

**Requirements**:
1. All queried fields are in the index
2. All returned fields are in the index
3. Query doesn't exclude `_id` unless `{_id: 0}` in projection

**Example**:
```javascript
// Index
db.products.createIndex({
    category: 1,
    status: 1,
    updated_at: -1
})

// Covered query - returns only indexed fields
db.products.aggregate([
    {$match: {
        category: 'electronics',
        status: 'active'
    }},
    {$project: {
        _id: 1,
        category: 1,
        status: 1,
        updated_at: 1
    }},
    {$sort: {updated_at: -1}}
])
```

**Performance**: 5-10x faster than document scans.

### Index Strategy Best Practices

1. **Filter fields first**: Most selective filters at start of compound index
2. **Sort fields last**: Include sort fields at end of compound index
3. **Include projection fields**: Add projected fields for covered queries
4. **Avoid index bloat**: Don't index every field (diminishing returns)

```javascript
// Good compound index design
db.orders.createIndex({
    tenant_id: 1,        // Filter: highest selectivity
    status: 1,           // Filter: medium selectivity
    created_at: -1       // Sort field last
})

// Query uses index efficiently
db.orders.aggregate([
    {$match: {
        tenant_id: 'abc123',
        status: 'pending'
    }},
    {$sort: {created_at: -1}}
])
```

---

## 3. Array Operators vs $unwind/$group Anti-Pattern

**AVOID**: `$unwind → $group` for array transformations (blocking stage, slow).

**USE**: Array operators (`$filter`, `$map`, `$reduce`, `$arrayElemAt`, `$size`).

### Anti-Pattern Example

```javascript
// BAD - unwind explodes documents, then regroups
db.products.aggregate([
    {$match: {category: 'electronics'}},
    {$unwind: '$tags'},
    {$match: {'tags': 'sale'}},
    {$group: {
        _id: '$_id',
        sale_tags: {$push: '$tags'}
    }}
])
```

### Optimized Example

```javascript
// GOOD - filter array in place
db.products.aggregate([
    {$match: {category: 'electronics'}},
    {$project: {
        _id: 1,
        sale_tags: {
            $filter: {
                input: '$tags',
                cond: {$eq: ['$$this', 'sale']}
            }
        }
    }}
])
```

### Array Operator Patterns

```javascript
// Filter array elements
{$filter: {
    input: '$items',
    cond: {$eq: ['$$this.status', 'active']}
}}

// Transform array elements
{$map: {
    input: '$products',
    in: {id: '$$this._id', price: '$$this.price'}
}}

// Get first/last element
{$arrayElemAt: ['$items', 0]}   // First
{$arrayElemAt: ['$items', -1]}  // Last

// Array size
{$size: '$items'}

// Check if array has elements
{$gt: [{$size: '$items'}, 0]}

// Reduce (aggregate array into single value)
{$reduce: {
    input: '$items',
    initialValue: 0,
    in: {$add: ['$$value', '$$this.price']}
}}
```

**Performance**: 5-10x faster for large arrays (1000+ elements).

---

## 4. $lookup Optimization

**Index foreign collection**: Ensure lookup field has index.

**Limit lookup results**: Use pipeline in $lookup to filter early.

**Avoid multiple lookups**: Denormalize if data rarely changes.

### Basic Lookup Pattern

```javascript
{$lookup: {
    from: 'customers',
    localField: 'customer_id',
    foreignField: '_id',
    as: 'customer'
}}
```

### Optimized Lookup with Pipeline

```javascript
{$lookup: {
    from: 'customers',
    let: {customer_id: '$customer_id'},
    pipeline: [
        // Filter early in lookup
        {$match: {
            $expr: {$eq: ['$_id', '$$customer_id']},
            status: 'active'
        }},
        // Project only needed fields
        {$project: {
            _id: 1,
            name: 1,
            email: 1
        }}
    ],
    as: 'customer'
}}
```

### Index Requirements

```javascript
// MUST have index on lookup field
db.customers.createIndex({'_id': 1})  // Usually exists
db.customers.createIndex({
    '_id': 1,
    'status': 1
})

// Check index usage
db.collection.explain('executionStats').aggregate([...])
```

### Multiple Lookup Optimization

```javascript
// BAD - sequential lookups
db.orders.aggregate([
    {$lookup: {from: 'customers', ...}},
    {$lookup: {from: 'products', ...}},
    {$lookup: {from: 'shipping', ...}}
])

// BETTER - combine lookups where possible
db.orders.aggregate([
    {$lookup: {
        from: 'customers',
        let: {customer_id: '$customer_id'},
        pipeline: [
            {$match: {$expr: {$eq: ['$_id', '$$customer_id']}}},
            // Nested lookup within first lookup (if needed)
            {$lookup: {from: 'addresses', ...}}
        ],
        as: 'customer'
    }},
    {$lookup: {from: 'products', ...}}
])

// BEST - denormalize if data rarely changes
// Store customer name/email in orders collection
```

**Performance**: 10-50x faster with indexed lookup field.

---

## 5. $group Optimization

**Group before sort**: Reduce data volume before sorting.

**Use $first/$last**: Instead of $push when only need one value.

**Limit accumulator size**: Use $slice on large arrays.

### Efficient Grouping Pattern

```javascript
// BAD - accumulates large arrays
db.orders.aggregate([
    {$match: {status: 'completed'}},
    {$group: {
        _id: '$customer_id',
        orders: {$push: '$$ROOT'}  // Entire documents
    }},
    {$sort: {count: -1}}
])

// GOOD - accumulate only needed data
db.orders.aggregate([
    {$match: {status: 'completed'}},
    {$group: {
        _id: '$customer_id',
        count: {$sum: 1},
        first_order_id: {$first: '$_id'},
        last_order_date: {$max: '$created_at'}
    }},
    {$sort: {count: -1}}
])
```

### Memory Considerations

MongoDB has 100MB memory limit for blocking stages ($group, $sort):
```javascript
// Enable disk usage for large aggregations
db.collection.aggregate(
    pipeline,
    {allowDiskUse: true}
)
```

### Nested Grouping Pattern

```javascript
// Group twice - first by subcategory, then by category
db.products.aggregate([
    {$match: {status: 'active'}},
    {$group: {  // First group: category + subcategory
        _id: {
            category: '$category',
            subcategory: '$subcategory'
        },
        count: {$sum: 1},
        avg_price: {$avg: '$price'}
    }},
    {$group: {  // Second group: category only
        _id: '$_id.category',
        subcategories: {
            $push: {
                name: '$_id.subcategory',
                count: '$count',
                avg_price: '$avg_price'
            }
        },
        total: {$sum: '$count'}
    }}
], {allowDiskUse: true})
```

---

## 6. Materialized Views with $merge/$out

**Use case**: Heavy aggregations run frequently (dashboards, reports).

### $merge vs $out

| Feature | $merge | $out |
|---------|--------|------|
| Behavior | Upserts into target | Replaces entire collection |
| Preserves other data | Yes | No |
| Update strategy | Configurable | N/A |
| Use when | Incremental updates | Full refresh |

### $merge Pattern

```javascript
// Materialize daily sales summary
db.orders.aggregate([
    {$match: {
        status: 'completed',
        created_at: {$gte: ISODate('2025-01-01')}
    }},
    {$group: {
        _id: {
            year: {$year: '$created_at'},
            month: {$month: '$created_at'},
            day: {$dayOfMonth: '$created_at'}
        },
        total_sales: {$sum: '$amount'},
        order_count: {$sum: 1},
        last_updated: {$max: '$updated_at'}
    }},
    {$merge: {
        into: 'dailySales',
        on: '_id',
        whenMatched: 'replace',
        whenNotMatched: 'insert'
    }}
])
```

### $out Pattern

```javascript
// Full refresh of aggregated data
db.products.aggregate([
    {$match: {status: 'active'}},
    {$group: {
        _id: '$category',
        count: {$sum: 1},
        avg_price: {$avg: '$price'}
    }},
    {$out: 'productsByCategory'}  // Replaces collection
])
```

### Scheduling Strategy

```python
# Run during low-load periods
def refresh_materialized_views(db):
    """Refresh materialized views for dashboard metrics."""
    pipeline = [...]
    db.orders.aggregate(
        pipeline + [{$merge: {into: 'dailySales', ...}}],
        allowDiskUse=True
    )
```

---

## 7. Slot-Based Execution Engine (MongoDB 5.0+)

**Automatic performance improvement** for certain stage combinations.

**Benefits**: Better CPU/memory utilization, faster execution.

**No code changes needed** - optimize pipelines to leverage this.

**Works best with**:
- Sequential $match stages
- $project followed by $match
- Simple $group operations
- Covered queries

**Check if enabled**:
```javascript
db.adminCommand({getParameter: 1, internalQuerySlotBasedExecutionEngine: 1})
```

---

## 8. Debugging Slow Pipelines

### Step 1: Explain Query

```javascript
db.collection.explain('executionStats').aggregate([...])
```

**Key metrics**:
- `totalDocsExamined` - should be close to `nReturned`
- `executionTimeMillis` - total execution time
- `totalKeysExamined` - index usage
- `stage` - IXSCAN (good) vs COLLSCAN (bad)

### Step 2: Check Index Usage

```javascript
// Look for COLLSCAN (collection scan)
explain_result.stages[0].COLLSCAN  // BAD
explain_result.stages[0].IXSCAN    // GOOD
```

**If COLLSCAN found**: Create index on filtered fields.

### Step 3: Profile Slow Queries

```javascript
// Enable profiling for slow queries
db.setProfilingLevel(1, {slowms: 100})

// Check profiler output
db.system.profile.find().sort({ts: -1}).limit(10).pretty()

// Disable when done
db.setProfilingLevel(0)
```

### Step 4: Iterative Testing

```python
# Test pipeline stages incrementally
pipeline = [
    {$match: {...}},  # Test this first
]
result = db.collection.aggregate(pipeline)
print(f"Stage 1: {len(list(result))} docs")

pipeline.append({$project: {...}})  # Add next stage
result = db.collection.aggregate(pipeline)
print(f"Stage 2: {len(list(result))} docs")

# Continue until bottleneck found
```

### Step 5: MongoDB Compass Visual Explain

Use MongoDB Compass for visual pipeline analysis:
1. Copy pipeline to Compass
2. Click "Explain" tab
3. View stage-by-stage execution plan
4. Identify bottlenecks (COLLSCAN, large doc transfers)

---

## 9. Common Patterns & Examples

### Pattern 1: Count by Category

```javascript
db.products.aggregate([
    {$match: {status: 'active'}},
    {$group: {
        _id: '$category',
        count: {$sum: 1},
        avg_price: {$avg: '$price'}
    }},
    {$sort: {count: -1}}
])
```

### Pattern 2: Top N Results

```javascript
// Top 10 customers by order count
db.orders.aggregate([
    {$match: {status: 'completed'}},
    {$group: {
        _id: '$customer_id',
        order_count: {$sum: 1},
        total_spent: {$sum: '$amount'}
    }},
    {$sort: {order_count: -1}},
    {$limit: 10}
])
```

### Pattern 3: Time-Based Aggregation

```javascript
// Orders per week for last 90 days
const ninety_days_ago = new Date();
ninety_days_ago.setDate(ninety_days_ago.getDate() - 90);

db.orders.aggregate([
    {$match: {
        created_at: {$gte: ninety_days_ago}
    }},
    {$group: {
        _id: {
            year: {$year: '$created_at'},
            week: {$week: '$created_at'}
        },
        count: {$sum: 1},
        total: {$sum: '$amount'}
    }},
    {$sort: {'_id.year': 1, '_id.week': 1}}
])
```

### Pattern 4: Join and Aggregate

```javascript
// Order totals with customer info
db.orders.aggregate([
    {$match: {status: 'completed'}},
    {$lookup: {
        from: 'customers',
        let: {customer_id: '$customer_id'},
        pipeline: [
            {$match: {$expr: {$eq: ['$_id', '$$customer_id']}}},
            {$project: {_id: 1, name: 1, email: 1}}
        ],
        as: 'customer'
    }},
    {$project: {
        _id: 1,
        amount: 1,
        customer: {$arrayElemAt: ['$customer', 0]}
    }}
])
```

### Pattern 5: Conditional Aggregation

```javascript
// Count orders by status category
db.orders.aggregate([
    {$group: {
        _id: null,
        pending: {$sum: {$cond: [{$eq: ['$status', 'pending']}, 1, 0]}},
        completed: {$sum: {$cond: [{$eq: ['$status', 'completed']}, 1, 0]}},
        cancelled: {$sum: {$cond: [{$eq: ['$status', 'cancelled']}, 1, 0]}}
    }}
])
```

---

## 10. Anti-Patterns to Avoid

**DON'T**:
- $match after $lookup (filter before lookup)
- $unwind → $group for array transformations (use array operators)
- Querying without indexes (collection scans are slow)
- Multiple sequential $lookup stages (denormalize or combine)
- Bare $group without $match (groups entire collection)
- $sort before $limit without index (sorts everything)
- Projecting all fields before $lookup (transfer unnecessary data)
- Ignoring allowDiskUse for large aggregations (100MB memory limit)

**DO**:
- Filter early (smallest dataset possible)
- Use indexed fields in $match
- Project only needed fields
- Use array operators for array manipulation
- Combine lookups when possible
- Enable allowDiskUse for large aggregations
- Check explain() output before deploying
- Create compound indexes for common query patterns

---

## Performance Benchmarks (Generic Patterns)

| Optimization | Before | After | Speedup |
|--------------|--------|-------|---------|
| Early $match (1M → 10K docs) | 45s | 0.5s | 90x |
| Covered query (indexed fields only) | 2.3s | 0.2s | 11x |
| Array $filter vs $unwind/$group | 8.1s | 0.9s | 9x |
| Indexed $lookup | 120s | 2.4s | 50x |
| Project before $lookup | 15s | 1.8s | 8x |

**Note**: Actual performance depends on collection size, hardware, and data distribution.

---

## Quick Reference Card

```javascript
// 1. Filter early (most selective filters first)
{$match: {tenant_id: 'abc', status: 'active'}}

// 2. Project before expensive operations
{$project: {_id: 1, needed_field: 1}}

// 3. Use array operators (not $unwind/$group)
{$filter: {input: '$items', cond: {...}}}

// 4. Optimize lookups with pipeline
{$lookup: {
    from: 'collection',
    let: {...},
    pipeline: [
        {$match: {$expr: {...}, status: 'active'}}
    ],
    as: 'result'
}}

// 5. Check performance
db.collection.explain('executionStats').aggregate([...])

// 6. Enable disk usage for large aggregations
db.collection.aggregate(pipeline, {allowDiskUse: true})

// 7. Use covered queries when possible
// Only project indexed fields

// 8. Group before sort (reduce data volume)
{$group: {...}}, {$sort: {...}}
```

---

## MongoDB Version Considerations

### MongoDB 4.4+
- $accumulator and $function for custom aggregations
- $merge stage for incremental updates
- Union with $unionWith

### MongoDB 5.0+
- Slot-based execution engine (automatic optimization)
- Time series collections optimizations
- $setWindowFields for window functions

### MongoDB 6.0+
- Encrypted aggregation pipelines
- Improved $lookup performance
- Better memory management

**Check version**: `db.version()`

---

## Remember

**General Priorities**:
1. **Filter early** - Smallest dataset possible before expensive operations
2. **Use indexes** - Query time from minutes to milliseconds
3. **Test with explain()** - Validate index usage before deploying
4. **Profile slow queries** - Find bottlenecks in production

**When in doubt**:
- Start with explain() to check index usage
- Test on production-sized data
- Profile slow queries to find bottlenecks
- Use MongoDB Compass for visual pipeline analysis

---

## See Also

- **MongoDB Documentation**: [Aggregation Pipeline Optimization](https://docs.mongodb.com/manual/core/aggregation-pipeline-optimization/)
- **Project-Specific Skills**:
  - `mongodb-m32rimm-patterns`: M32RIMM/FISIO-specific aggregation patterns (subscription isolation, businessObjects, DV/Asset queries)
- **Related Topics**:
  - Index design best practices
  - Query performance tuning
  - Schema design for aggregation efficiency
