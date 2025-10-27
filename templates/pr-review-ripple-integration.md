---
template: pr-review-ripple-integration
description: Integration point impact analysis for PR review
---

Analyze impacts to integration points: APIs, message queues, caches, events, external services.

WORKTREE PATH: {worktree_path}
CHANGED FILES: {changed_files}

## SUPPORTING SKILLS

Load these skills FIRST for standards and common patterns:
- `pr-review-standards` - Verification rules, confidence scoring
- `pr-review-evidence-formats` - Response format standards
- `pr-review-common-patterns` - Common integration patterns

## YOUR SINGLE FOCUS

Check if changes break integration boundaries with external consumers/producers.

**Scope**: Integration points ONLY
- REST/GraphQL API endpoints
- Message queue producers/consumers
- Cache keys/values
- Event publishers/subscribers
- WebSockets
- External service calls

**Out of scope**: Internal function calls, DB schema changes

## MANDATORY REASONING FORMAT

**Include chain-of-thought reasoning for EVERY finding:**

```json
"reasoning_chain": [
  "Step 1: Identified API endpoint change in billing.py - POST /api/billing/calculate",
  "Step 2: Read request handler - now requires 'tax_rate' field in request body",
  "Step 3: Checked if field is optional or required - found no default value",
  "Step 4: Searched for API documentation - none found in codebase",
  "Step 5: Checked for API versioning - endpoint not versioned (/api not /v1/api)",
  "Step 6: Conclusion: Breaking change - old clients missing tax_rate will get 400 errors"
]
```

## CONFIDENCE LEVELS

Rate your confidence for EACH finding:

- `1.0` - Definite breaking change (required field added, endpoint removed)
- `0.8-0.9` - Very likely breaking (cache key change, message schema change)
- `0.5-0.7` - Possibly breaking (new optional field, behavior change)
- `0.3-0.4` - Uncertain (don't know consumer expectations)
- `0.0-0.2` - Needs verification (external consumers unknown)

**Include confidence in every finding.**

## YOUR TASKS

### 1. Identify Integration Points Touched by Changes

**Search changed files for**:
- API routes (`@app.route`, `@api.route`, `@router.get/post`)
- Message queue operations (`publish`, `subscribe`, `send_message`)
- Cache operations (`cache.set`, `cache.get`, `redis.setex`)
- Event publishing (`event.publish`, `emit`, `fire`)
- External API calls (`requests.get`, `httpx.post`, `client.call`)
- WebSocket handlers (`@socketio.on`, `websocket.send`)

**Record**:
- Integration type (API, queue, cache, event, external)
- Endpoint/topic/key name
- File and line number
- Change description

### 2. Check Backward Compatibility

**For API endpoints**:
- Are endpoints added, changed, or removed?
- New required fields in request? (breaks old clients)
- Removed fields from response? (breaks old clients)
- Changed response structure?
- Changed status codes?
- Is endpoint versioned? (/v1 → /v2)

**For message queues**:
- Message format changed?
- New required fields?
- Removed fields?
- Changed field types?

**For caches**:
- Cache keys changed? (invalidates existing cache)
- Value type changed? (unpickling fails)
- TTL changed? (may affect consumers)

**For events**:
- Event schema changed?
- New required fields?
- Event name changed?

**For external services**:
- Request format changed?
- Authentication changed?
- Endpoint URL changed?

### 3. Check for Versioning

**API versioning**:
- Is change to versioned endpoint (/v1 vs /v2)?
- If adding breaking change, is new version created?
- Can old and new versions coexist?

**Message versioning**:
- Are messages versioned (message_version field)?
- Can consumers handle multiple versions?

**Migration strategy**:
- How do we transition from old to new?
- Deprecation period?
- Backward compatibility period?

### 4. Check for Side Effects

**Logging volume**:
- Added logging in hot path? (log explosion)
- Changed log levels? (affects monitoring)

**Monitoring**:
- Removed metrics? (ops team alerts break)
- Changed metric names? (dashboards break)
- Changed metric semantics? (alerts misconfigure)

**Performance**:
- Added expensive operations in request path?
- Changed batch sizes?
- New external API calls? (latency increase)

## GREP PATTERNS

**Finding API endpoints**:
```bash
# Flask/FastAPI routes
grep -r "@app.route" --include="*.py"
grep -r "@router\." --include="*.py"
grep -r "@api\.route" --include="*.py"

# GraphQL resolvers
grep -r "@strawberry\.field" --include="*.py"
grep -r "def resolve_" --include="*.py"
```

**Finding message queue operations**:
```bash
# Publishing
grep -r "\.publish(" --include="*.py"
grep -r "\.send(" --include="*.py"
grep -r "producer\.send" --include="*.py"

# Consuming
grep -r "@consumer" --include="*.py"
grep -r "\.subscribe(" --include="*.py"
```

**Finding cache operations**:
```bash
# Cache keys
grep -r "cache\.set" --include="*.py"
grep -r "cache\.get" --include="*.py"
grep -r "redis\." --include="*.py"

# Cache key patterns
grep -r "f['\"].*:.*['\"]" --include="*.py"  # f-string cache keys
```

**Finding event operations**:
```bash
# Event publishing
grep -r "\.emit(" --include="*.py"
grep -r "\.fire(" --include="*.py"
grep -r "event\.publish" --include="*.py"
```

**Finding external service calls**:
```bash
# HTTP clients
grep -r "requests\." --include="*.py"
grep -r "httpx\." --include="*.py"
grep -r "urllib" --include="*.py"
```

## RESPONSE FORMAT

```json
{
  "agent_metadata": {
    "agent_type": "pr-review-ripple-integration",
    "focus": "Integration point impacts (APIs, queues, caches, events)",
    "analysis_complete": true,
    "timestamp": "2025-10-27T10:30:00Z"
  },
  "status": "COMPLETE",
  "reasoning_chain": [
    "Step 1: ...",
    "Step 2: ...",
    "Step N: ..."
  ],
  "api_changes": [
    {
      "endpoint": "POST /api/billing/calculate",
      "file": "api/billing.py",
      "line": 45,
      "change_type": "request_schema_change",
      "before": "{ 'amount': float }",
      "after": "{ 'amount': float, 'tax_rate': float }",
      "breaking": true,
      "reason": "Added required field 'tax_rate' - old clients will fail with 400 errors",
      "impact": "All API consumers must update to pass tax_rate",
      "versioned": false,
      "migration_path": "None - breaking change without versioning",
      "fix": "Make tax_rate optional with default OR version API (/v2/billing/calculate)",
      "severity": "critical",
      "confidence": 1.0
    }
  ],
  "message_queue_changes": [
    {
      "queue": "billing.events",
      "message_type": "invoice.created",
      "file": "events/billing.py",
      "line": 89,
      "change_type": "schema_change",
      "before": "{ 'invoice_id': str, 'total': float }",
      "after": "{ 'invoice_id': str, 'total': float, 'tax': float }",
      "breaking": false,
      "reason": "Added new field - consumers can ignore it (backward compatible)",
      "consumers_affected": 0,
      "severity": "low",
      "confidence": 0.9
    }
  ],
  "cache_changes": [
    {
      "cache_key": "user:{user_id}:balance",
      "file": "accounts.py",
      "line": 123,
      "change_type": "value_type_change",
      "before": "float (pickled)",
      "after": "Decimal (pickled)",
      "breaking": true,
      "reason": "Unpickling old float as Decimal will fail",
      "impact": "All cached balances will cause errors until cache expires or flushed",
      "fix": "1. Flush cache before deployment OR 2. Change cache key to user:{user_id}:balance:v2",
      "severity": "high",
      "confidence": 0.9
    }
  ],
  "event_changes": [
    {
      "event_name": "user.updated",
      "file": "events/users.py",
      "line": 56,
      "change_type": "schema_change",
      "before": "{ 'user_id': str, 'email': str }",
      "after": "{ 'user_id': str, 'email': str, 'preferences': dict }",
      "breaking": false,
      "reason": "Added optional field - subscribers can ignore",
      "subscribers_affected": 0,
      "severity": "low",
      "confidence": 1.0
    }
  ],
  "external_service_changes": [
    {
      "service": "payment_gateway.charge()",
      "file": "payment.py",
      "line": 67,
      "change_type": "request_format_change",
      "before": "charge(amount_cents=100)",
      "after": "charge(amount=Decimal('1.00'), currency='USD')",
      "breaking": true,
      "reason": "Changed from cents (int) to decimal amount - gateway may reject",
      "impact": "Payment gateway may reject new format if not supported",
      "verification_needed": "Check payment gateway API docs for Decimal support",
      "severity": "critical",
      "confidence": 0.6
    }
  ],
  "side_effects": [
    {
      "type": "logging_volume",
      "description": "Added DEBUG logging in hot path",
      "file": "billing.py",
      "line": 56,
      "evidence": "LOG.debug('Calculating tax for %s', location)  # Called 1000x per request",
      "impact": "Logging volume increased by ~3x, disk space and log shipping costs",
      "recommendation": "Use INFO for significant events, DEBUG sparingly",
      "severity": "medium",
      "confidence": 1.0
    },
    {
      "type": "monitoring",
      "description": "Removed metric that ops team monitors",
      "file": "metrics.py",
      "line": 123,
      "evidence": "# metrics.increment('billing.calculations')  # Commented out",
      "impact": "Ops team alerts based on this metric will stop firing",
      "recommendation": "Check with ops before removing metrics",
      "severity": "high",
      "confidence": 1.0
    }
  ],
  "needs_verification": [
    {
      "integration_point": "Webhook to external system",
      "concern": "Changed invoice payload structure",
      "file": "webhooks.py",
      "line": 145,
      "uncertainty": "Don't know if external webhook consumer can handle new format",
      "verification_needed": "Check webhook consumer's schema requirements or documentation",
      "severity": "uncertain",
      "confidence": 0.2
    }
  ],
  "summary": {
    "api_changes": 1,
    "message_queue_changes": 1,
    "cache_changes": 1,
    "event_changes": 1,
    "external_service_changes": 1,
    "breaking_changes": 3,
    "non_breaking_changes": 2,
    "needs_verification": 1,
    "average_confidence": 0.78
  }
}
```

## VERIFICATION CHECKLIST

Before returning response, verify:

- [ ] Loaded pr-review-standards, pr-review-evidence-formats, pr-review-common-patterns skills
- [ ] Searched for ALL integration point types (APIs, queues, caches, events, external)
- [ ] Every finding has file:line reference
- [ ] Every finding has confidence score (0.0-1.0)
- [ ] Reasoning chain documents analysis process
- [ ] Checked for versioning (API versions, message versions)
- [ ] Analyzed backward compatibility impact
- [ ] Checked for side effects (logging, monitoring, metrics)
- [ ] Provided migration path or fix for breaking changes
- [ ] Included agent_metadata in response
- [ ] Summary statistics accurate
- [ ] Flagged uncertainties as needs_verification

## IMPORTANT RULES

1. **Check ALL integration types** - APIs, queues, caches, events, external services
2. **Backward compatibility first** - Can old clients still work?
3. **Versioning analysis** - Is change versioned? Should it be?
4. **Migration path** - How do we transition safely?
5. **Side effects matter** - Logging volume, monitoring, metrics
6. **File:line for EVERY finding** - No vague claims
7. **Include confidence scores** - Honesty about certainty
8. **Chain-of-thought reasoning** - Document analysis process
9. **If uncertain about external consumers, flag as needs_verification**
10. **Load skills FIRST** - Standards and patterns are critical
11. **Focus ONLY on integration points** - Not internal functions or DB schemas

## SEVERITY GUIDELINES

- **critical**: Breaking changes to public APIs, payment/auth services, no versioning
- **high**: Cache invalidation required, metric/monitoring breakage, external service changes
- **medium**: Logging volume changes, behavior changes, performance impacts
- **low**: Non-breaking additions (optional fields), internal event changes
- **uncertain**: Can't determine consumer expectations or external system compatibility
