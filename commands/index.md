# /index - Interactive Codebase Interrogation

## Overview
Intelligent codebase interrogation that extracts knowledge through conversation with you, the domain expert. Generates comprehensive CLAUDE.md documentation that's 100% correct and 100% complete.

**This is NOT automated indexing.** This is a collaborative conversation where I extract the knowledge that only exists in your head.

## Command
```
/index <directory>
```

## What This Does

### Phase 1: Preliminary Investigation (I do this)
1. Scan directory structure and file organization
2. Quick AST analysis to understand what the code does
3. Look for existing docs (README, architecture docs)
4. Form initial hypothesis about the system
5. Ask you basic orientation questions:
   - What does this codebase do?
   - What are the main components?
   - What are the critical constraints?
   - Any known gotchas I should be aware of?

### Phase 2: Generate Starter CLAUDE.md (I do this)
Create initial documentation with what I learned:
- System purpose
- High-level architecture
- Key components identified
- Critical constraints you mentioned
- Known gotchas flagged

### Phase 3: Deep Interrogation (Background)
Kick off aggressive investigation system:
- Reads code files in detail
- Extracts all config values
- Finds all comments (TODO, IMPORTANT, WHY)
- Detects patterns (retry logic, cleanup, validation)
- Maps execution flows
- Identifies knowledge gaps

**I'll tell you how to monitor progress and when it's done.**

### Phase 4: Synthesis & Presentation (After you tell me it's done)
I review the interrogation results and:
1. Show you everything I found (findings summary)
2. Present the big picture understanding
3. Map out execution flows and data transformations
4. Identify what I'm confident about vs uncertain
5. Highlight potential inconsistencies or assumptions

### Phase 5: Conversational Q&A (The Important Part)
I ask you hyper-specific questions like:
```
Line 46 of tenable_asset_os_ports_services_import.py says:
"Need to restrict this tool and main import from creating concurrent"

Questions:
1. What is "main import"? Another script? Another module?
2. What SPECIFICALLY breaks if you run both concurrently?
   - Race condition on shared resource?
   - Database connection exhaustion?
   - API rate limit violation?
3. Why isn't this enforced in code (mutex/lock)?
```

**NOT like this:**
```
Can you confirm this understanding of concurrency?
```

### Phase 6: Iterative Refinement (Until Perfect)
- You answer my questions
- I spot inconsistencies or bad assumptions
- I ask follow-ups to probe deeper
- I update CLAUDE.md with verified knowledge
- I show you the updated understanding
- We iterate until you say "yes, that's 100% correct and complete"

## Success Criteria

**100% Correct:**
- Zero factual errors in CLAUDE.md
- All technical details verified by you
- All assumptions validated
- All edge cases documented

**100% Complete:**
- All critical business logic explained
- All tuning decisions rationalized (why 4 workers? why batch size 500?)
- All gotchas and constraints documented
- All failure modes and recovery strategies explained
- Any agent could read CLAUDE.md and refactor with confidence

## Expected Output

### CLAUDE.md Contents
```markdown
# [System Name]

## Purpose
[What this system does and why]

## Architecture
[High-level components and how they interact]

## Critical Constraints
[Things that MUST NOT be violated]

### Concurrency Restriction (Line 46)
**WHY:** [Root cause - shared DB connection pool]
**WHAT BREAKS:** [Deadlock if both run simultaneously]
**ENFORCEMENT:** [Manual - documented in runbook]

## Configuration

### Worker Count: 4
**WHY:** API rate limit is 1000 req/min, each worker makes ~250 req/min
**WHAT BREAKS IF INCREASED:** API returns 429, entire import fails
**WHAT BREAKS IF DECREASED:** Import takes >2 hours, misses processing window

### Batch Size: 500
**WHY:** Memory limit - each item uses ~2KB, 500 = 1MB per batch
**WHAT BREAKS IF INCREASED:** OOM on machines with <8GB RAM
**WHAT BREAKS IF DECREASED:** Too many API calls, hits rate limit

## Execution Flow
[Detailed flow with entry points, data transformations, outputs]

## Error Handling
[What errors can occur, how they're handled, retry strategy]

## Cleanup & Shutdown
[What gets cleaned up, what happens if cleanup fails]

## Gotchas
[Known edge cases, operational issues, monitoring alerts]

## Testing
[How to test, what to verify, known test gaps]
```

## Usage

```bash
# Start interrogation
/index /home/rmurphy/repos/m32rimm/fisio/fisio/imports/tenable_sc

# I'll ask preliminary questions
# I'll generate starter CLAUDE.md
# I'll kick off deep interrogation

# Monitor progress:
tail -f /tmp/interrogation_[session_id].log
# (I'll tell you the exact command)

# When you see: "✅ Interrogation complete"
# Tell me: "it's done"

# Then we have the conversation
# I ask questions, you answer
# We refine CLAUDE.md together
# We iterate until perfect
```

## What Makes This Different

**Traditional indexing:**
- Extracts structure (WHAT the code does)
- Automated, no human input
- Fast but shallow

**This approach:**
- Extracts knowledge (WHY decisions were made)
- Collaborative conversation
- Slower but deep and verified

**The goal:** An agent reading CLAUDE.md should know everything you know about this codebase.

## Conversation Examples

### Bad Question (Old Approach)
```
What concurrency model does this use?
```

### Good Question (New Approach)
```
I found 4 API workers (constants.py) and a comment at line 46:
"Need to restrict this tool and main import from creating concurrent"

You mentioned this is a Tenable SC import. Questions:

1. Is "main import" referring to another import script
   (like the QualysGuard import)?

2. What resource can't be shared between imports?
   - The shared MongoDB connection pool (max 10 connections)?
   - API credentials that have rate limits?
   - File locks on temp directory?

3. Why 4 workers specifically? I calculated:
   - API rate limit: 1000 req/min
   - Batch size: 500 items
   - Processing time: ~2 sec/batch
   - 4 workers × 250 req/min = 1000 req/min
   Is this the constraint, or something else?
```

## Tips for Best Results

**Be specific in your answers:**
- ❌ "It'll break if you change it"
- ✅ "The API returns 429 rate limit, entire import fails, no retry logic"

**Explain the WHY:**
- ❌ "We use 4 workers"
- ✅ "4 workers because API has 1000 req/min limit, tested that 5 workers triggers 429"

**Document gotchas:**
- ❌ "Be careful with signals"
- ✅ "SIGTERM during DB write leaves partial data, must check import_status table on restart"

**Validate my assumptions:**
- I'll form hypotheses from code
- Tell me if I'm wrong
- Explain what I'm missing

## Limitations

- Requires your time (30min - 2hr depending on complexity)
- Requires you to know the codebase deeply
- Can't extract knowledge that doesn't exist anywhere (lost tribal knowledge)
- Works best on codebases you've worked on extensively

## Output Location

- `<directory>/CLAUDE.md` - Main documentation
- `<directory>/.interrogation/` - Session data, findings, questions
- `<directory>/.interrogation/round_N.json` - Results from each round

## Integration with PRISM

After CLAUDE.md is finalized:
- Verified knowledge stored in PRISM ANCHORS tier (permanent)
- Scoped to exact project/file/line
- Available for future agents working on this codebase
- Can generate flow diagrams from stored knowledge

## The Ultimate Test

After interrogation, I should be able to:
1. Generate complete architecture documentation with diagrams
2. Explain every business logic decision
3. Document every edge case and failure mode
4. Refactor the code confidently without breaking constraints

**If I can't, we iterate more.**
