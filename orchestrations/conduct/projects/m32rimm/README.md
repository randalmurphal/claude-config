# m32rimm Conduct Configuration

Optimized conduct orchestration for the m32rimm monorepo, applying patterns from the pr_review_m32rimm system.

## Usage

```bash
# From m32rimm repo root
python -m conduct run --config ~/.claude/orchestrations/conduct/projects/m32rimm/config.json
```

## What's Different

### Domain-Specific Validators

| Validator | Trigger | Focus |
|-----------|---------|-------|
| `general_validator` | Always | Logging, try/except, type hints |
| `mongo_validator` | Uses db., pymongo, DBOpsHelper | retry_run, subID, flush |
| `import_validator` | imports/ or data_importer | Import tracking, aggregation |

### Finding Classification

Based on pr_review_m32rimm patterns:

**ALWAYS FLAG:**
- `mark_for_aggregation()` without `flush()` → CRITICAL
- Missing `subID` on businessObjects → CRITICAL
- Missing `retry_run()` on mongo ops → HIGH
- Mongo call inside loop → HIGH

**NEVER FLAG:**
- KeyError on required field (crash is intentional)
- Missing retry_run in test code
- Theoretical issues without proof

### Finding Validation

The `finding_validator` (Opus) challenges ALL findings:
- Expects 30-50% false positive rate
- Checks real-world plausibility
- Applies m32rimm crash philosophy
- Can upgrade/downgrade severity

### Crash Philosophy

From m32rimm patterns:
- Missing required data → crash
- Missing config → crash
- Invalid internal input → crash

**Goal: Crash EARLY and LOUD at the SOURCE.**

## Files

```
projects/m32rimm/
├── config.json              # Workflow configuration
├── finding_classification.md # What to flag/not flag
├── README.md                # This file
└── prompts/
    ├── implement_m32rimm.txt   # m32rimm-specific implementation
    ├── fix_m32rimm.txt         # m32rimm-specific fixes
    ├── validate_mongo.txt      # MongoDB operations
    ├── validate_imports.txt    # Import framework
    ├── validate_general.txt    # General code quality
    └── finding_validator.txt   # Challenge all findings
```

## Validation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPONENT IMPLEMENTED                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 1: Domain Validators (Parallel)          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  general_   │  │   mongo_    │  │  import_    │         │
│  │  validator  │  │  validator  │  │  validator  │         │
│  │  (always)   │  │ (if mongo)  │  │(if imports) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                    Aggregate all findings
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 2: Finding Validator (Opus)              │
│                                                             │
│  For EACH finding:                                          │
│  • Read full context (50+ lines)                           │
│  • Trace execution path                                     │
│  • Check real-world plausibility                           │
│  • Apply m32rimm crash philosophy                          │
│                                                             │
│  Verdicts:                                                  │
│  • CONFIRMED / CONFIRMED_UPGRADED / CONFIRMED_DOWNGRADED   │
│  • FALSE_POSITIVE (with proof)                             │
│  • UNCERTAIN (needs human)                                  │
│                                                             │
│  Expected: 30-50% false positive rate                       │
└─────────────────────────────────────────────────────────────┘
                              │
                  Only CONFIRMED issues remain
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 3: Fix Loop (if issues)                  │
│                                                             │
│  • Fix using m32rimm patterns                              │
│  • Re-validate after fix                                    │
│  • Max 3 attempts before voting gate                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PASS / FAIL   │
                    └─────────────────┘
```

## Key Patterns Applied

From pr_review_m32rimm:

1. **Evidence Required** - "Can you write a failing test?"
2. **Real-World Plausibility** - Theoretical issues get downgraded
3. **Crash Philosophy** - Missing required data should crash
4. **Multi-Stage Validation** - Validators challenge each other
5. **Domain Expertise** - Specific patterns for Mongo, imports
