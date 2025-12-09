# Finding Classification for m32rimm Implementation

**Load this for ALL validation agents during /conduct.** This encodes m32rimm-specific patterns.

---

## Core Philosophy

### The Threshold
**Can you write a failing test for this? If NO, don't flag it.**

### Crash Philosophy
This codebase EXPECTS crashes on bad state:
- Missing required Mongo fields → crash (data integrity issue)
- Missing subscription config → crash (deployment issue)
- Invalid input to internal functions → crash (caller's bug)

**Goal: Crash EARLY and LOUD at the SOURCE, not silently fail later.**

---

## ALWAYS Flag (Real Issues)

| Pattern | Severity | Why |
|---------|----------|-----|
| `mark_for_aggregation()` without prior `flush()` | **CRITICAL** | Data loss - aggregates empty buffer |
| `businessObjects` query missing `info.owner.subID` | **CRITICAL** | Cross-tenant data exposure |
| Missing `retry_run()` on mongo ops in production code | HIGH | Network blips crash the import |
| Mongo call inside a loop | HIGH | Scales badly regardless of collection size |
| DBOpsHelper without `flush()` before return | HIGH | Data in buffer never persists |
| `insert_data_importer()` without matching `complete_data_importer()` | HIGH | Audit trail broken, stuck "Running" status |
| Breaking change to shared utility without checking callers | HIGH+ | Check blast radius |
| Race condition possible in production | HIGH | "Rare" still happens at scale |
| Error raised late instead of at source | MEDIUM+ | Should crash at detection point |

---

## NEVER Flag (Known False Positives)

| Pattern | Why It's Not An Issue |
|---------|----------------------|
| KeyError not caught on REQUIRED field | Intentional crash - we want failure on missing data |
| Subscription config field not validated | Intentional crash - missing config should fail loudly |
| Missing retry_run in test code | Only matters in production paths |
| Missing retry_run inside DBOpsHelper | DBOpsHelper handles retry internally |
| subID filter applied by caller or decorator | Don't flag if filtering happens upstream |
| flush() called in finally block or context manager | Don't double-flag |
| Theoretical issue that CAN'T happen in written code | Need proof it CAN happen |
| Performance on small, rarely-queried collection | Unless in a loop pattern |
| "Could add validation" without crash scenario | If it won't break, don't flag |
| N+1 query on small fixed dataset | Flag only for unbounded or large N |
| Race condition impossible in single-threaded context | Check actual execution model |

---

## Context-Dependent (Investigate First)

| Pattern | FLAG if... | DON'T FLAG if... |
|---------|------------|------------------|
| Missing try/except | External API, network op, DB write | Internal function, required field access |
| No type hints | New code, public API | Legacy code not being modified |
| Performance concern | High-frequency path, large collection, loop | One-time op, small fixed dataset |
| Missing logging | Error path, important state change | Happy path, internal helper |
| No error handling | Critical path, user-facing | Internal utility, crash-is-ok context |

---

## Severity Guidelines

### CRITICAL
**WILL break production** (with proof)
- Must include: Reproduction scenario OR exploit proof
- Examples: Data loss, data leak, crash with specific inputs
- NOT "critical": "Could crash", "Might leak", "Should validate"

### HIGH
**WILL cause user-visible problems** (with proof)
- Must include: Quantified impact OR affected caller list
- Examples: N+1 with 1000 queries, import fails silently, broken audit trail
- NOT "high": "Poor performance", "Breaking change" without callers listed

### MEDIUM
**Should fix, increases bug risk**
- Must include: Specific scenario where issue manifests
- Examples: Missing error handling in critical path, uncovered edge case
- NOT "medium": "Could be better", "Consider refactoring"

### LOW
**Nice to have**
- Optimization with minor benefit
- Code clarity improvements

### DON'T ASSIGN SEVERITY (don't flag)
- Personal preferences (naming, comments)
- Theoretical without proof
- Style (ruff handles this)

---

## m32rimm-Specific Pattern Checklist

### MongoDB Operations
- [ ] `retry_run()` wrapping all mongo ops (reads AND writes)
- [ ] `subID` filter on ALL businessObjects queries
- [ ] DBOpsHelper `flush()` before aggregation or return
- [ ] No mongo calls inside loops

### Import Framework
- [ ] `insert_data_importer()` / `complete_data_importer()` paired
- [ ] `flush()` before `mark_for_aggregation()`
- [ ] Proper exception handling in complete_data_importer

### Business Objects
- [ ] Correct relationship type (related.* vs relatedV2)
- [ ] r3 frontend schema alignment if fields changed
- [ ] BO structure matches expected schema

### General
- [ ] Logging with `logging.getLogger(__name__)`
- [ ] try/except ONLY for network/DB/external API
- [ ] Type hints on new code
- [ ] 80 char line limit

---

## Real-World Plausibility Check

Before flagging, ask:
1. **How would a user trigger this?** If no realistic scenario, downgrade.
2. **What's the actual data pattern?** Check configs/examples for typical usage.
3. **What's the frequency?** Every request = serious. Once a year = probably low.
4. **Who controls the inputs?** User = higher risk. Admin = lower risk.

| Theoretical Issue | Practical Reality | Verdict |
|-------------------|-------------------|---------|
| "Empty list causes error" | List always populated by upstream | FALSE_POSITIVE |
| "N+1 in loop" | Loop processes 3 config items | DOWNGRADE to LOW |
| "Missing retry on read" | Critical import path, 100k records | CONFIRMED HIGH |
| "Race condition possible" | Single-threaded, queue-controlled | FALSE_POSITIVE |

---

## Validation Verdicts

| Verdict | When to Use |
|---------|-------------|
| **CONFIRMED** | Issue is real, evidence holds |
| **CONFIRMED_UPGRADED** | Real AND more severe than claimed |
| **CONFIRMED_DOWNGRADED** | Real but less severe |
| **FALSE_POSITIVE** | Issue doesn't exist (with proof) |
| **UNCERTAIN** | Can't determine, needs human |

**Expected false positive rate: 30-50%.** If everything confirms, validators aren't challenging enough.
