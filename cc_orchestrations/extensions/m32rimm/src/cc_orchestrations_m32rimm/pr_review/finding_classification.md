# Finding Classification Guide

**Load this ref for ALL PR review agents.** This encodes m32rimm-specific patterns.

---

## ❌ DON'T FLAG - We Don't Care About These

**These are NOT findings. Do not waste time reporting them.**

| Category | Examples | Why We Don't Care |
|----------|----------|-------------------|
| **Style/Formatting** | Line length, spacing, naming conventions | `ruff` handles this - not a PR review concern |
| **Linting issues** | Unused imports, missing docstrings | `ruff` handles this - not a PR review concern |
| **Type hints missing** | No type hints on legacy code | Only flag if new PUBLIC API |
| **Comments could be better** | "Add docstring", "comment this" | Unless it's genuinely confusing |
| **Logging could be added** | "Add logging here" | Unless error path is completely dark |
| **Could be more DRY** | "Extract to helper function" | Unless egregious copy-paste |
| **Generic "best practice"** | "Consider using X pattern" | Only flag if it causes bugs |
| **Theoretical concerns** | "Could be exploited if..." | Need PROOF it can happen |
| **Pre-existing issues** | Problems in code not modified by PR | Out of scope - file a separate ticket |

**The test**: Would this crash production or corrupt data? If NO, probably don't flag it.

---

## ✅ ALWAYS Flag (Real Issues)

| Pattern | Severity | Why |
|---------|----------|-----|
| Mongo call inside a loop | HIGH+ | Scales badly regardless of collection size |
| Race condition possible in production | HIGH | "Rare" still happens at scale |
| Error raised late instead of at source | MEDIUM+ | Should RuntimeError at detection point |
| Missing `retry_run()` on mongo ops | HIGH | Network blips crash the process |
| Missing `subID` filter on businessObjects | CRITICAL | Cross-tenant data exposure |
| `flush()` missing before aggregation | CRITICAL | Data loss - aggregates stale data |
| Breaking change to shared utility | HIGH+ | Check blast radius for actual severity |

---

## 🚫 NEVER Flag (Known False Positives)

| Pattern | Why It's Not An Issue |
|---------|----------------------|
| KeyError not caught on REQUIRED field | Intentional crash - we want failure on missing required data |
| Subscription config field not validated | Intentional crash - missing config should fail loudly |
| Already addressed in MR discussion threads | Don't re-flag resolved issues |
| Theoretical issue that CAN'T happen in the written code | Need proof it CAN happen |
| Performance on small, rarely-queried collection | Unless it's a scalability pattern (loop calls) |
| "Could add validation" without crash scenario | If it won't actually break, don't flag |

---

## ⚖️ Context-Dependent (Investigate First)

| Pattern | FLAG if... | DON'T FLAG if... |
|---------|------------|------------------|
| Missing try/except | External API, network op, DB write | Internal function, required field access |
| No type hints | New code, public API | Legacy code not being modified |
| Performance concern | High-frequency path, large collection, loop pattern | One-time op, small fixed dataset |
| Missing logging | Error path, important state change | Happy path, internal helper |

---

## 🔥 The Crash Philosophy

This codebase EXPECTS certain things to crash:
- Missing required Mongo fields → crash (data integrity issue)
- Missing subscription config → crash (deployment issue)
- Invalid input to internal functions → crash (caller's bug)

**Goal: Crash EARLY and LOUD at the SOURCE, not silently fail later.**

- **FLAG:** Error happens but isn't surfaced, or surfaces in wrong place
- **DON'T FLAG:** Intentional crash on bad input/state

---

## 🎯 Severity Guidelines

### CRITICAL
- **WILL** cause data loss, data corruption, or security breach
- Must include: Specific scenario showing data loss/breach
- Examples: Missing subID filter, flush missing before aggregation

### HIGH
- **WILL** cause production crash or user-visible breakage
- Must include: Specific crash scenario or API break
- Examples: Missing retry_run, N+1 query in high-frequency path

### MEDIUM
- **COULD** cause issues under certain conditions
- Must include: The specific conditions
- Examples: Error path without logging, missing edge case handling

### LOW
- Code quality improvement that doesn't affect production
- Should NOT be reported unless specifically requested

---

## 🔍 Validation: Be Practical

**Validators must assess WITH CONTEXT.** The goal is accuracy, not rejection quotas.

For EVERY finding, ask:
1. **Is it in scope?** Is the issue in code modified by this PR?
2. **Is it real in THIS scenario?** Consider how this code actually gets used
3. **What's the practical impact?** Blocker, worth noting, or noise?
4. **Is it already handled?** Check caller, decorator, context manager
5. **What should happen?** Fix now, note for later, or dismiss?

**Categorize by practical impact:**

| Category | Meaning | Action |
|----------|---------|--------|
| **BLOCKER** | Will cause production issues | Must fix before merge |
| **SHOULD_FIX** | Real issue, reasonable to fix | Fix if easy, else document |
| **NOTE** | Worth awareness, not blocking | Include in report as observation |
| **DISMISS** | Not a real issue in this context | Remove from report |

Validation verdicts:
- `CONFIRMED` - Issue is real, severity is correct
- `CONFIRMED_UPGRADED` - Issue is real but MORE severe than reported
- `CONFIRMED_DOWNGRADED` - Issue is real but LESS severe (becomes NOTE)
- `FALSE_POSITIVE` - Not an issue IN THIS CONTEXT (explain why)
- `NEEDS_INVESTIGATION` - Can't determine, need more context

---

## 📋 m32rimm Auto-Check List

These patterns MUST be verified in every relevant PR:

- [ ] `flush()` called before `mark_for_aggregation()`
- [ ] `subID` filter on ALL `businessObjects` queries
- [ ] `insert_data_importer()` paired with `complete_data_importer()`
- [ ] `retry_run()` wraps ALL mongo operations (reads AND writes)
- [ ] Correct relationship type: `related.*` for imports, `relatedV2` for API
- [ ] Test Plan exists in Jira (if testing needed)
- [ ] Integration tests updated for changed functionality
