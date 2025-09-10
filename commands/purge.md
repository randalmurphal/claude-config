---
name: purge
description: Intelligent context management with 3-tier compression
---

# Context Purge - Smart Memory Management

Intelligently manages context to keep important information while removing clutter.

## Usage

- `/purge` - Automatic compression based on current usage
- `/purge status` - Show context usage statistics  
- `/purge clean` - Remove only obvious junk (safe)
- `/purge moderate` - 50% threshold compression
- `/purge aggressive` - 75% threshold compression

## Three-Tier System

### Tier 1: Always Remove (Even at 10% usage)
Obvious junk that adds no value:
- Shell prompts (`user@hostname:~$`)
- Success messages (`File created successfully`)
- Empty lines and separators (`======`)
- Directory listings (`ls` output)
- Package install output
- Progress indicators (`Loading...`)
- Duplicate consecutive messages

### Tier 2: Moderate (50-75% usage)
Remove non-essential context:
- Completed todo items
- Old search results (keep matches only)
- Unchanged file contents
- Passing test output (keep failures)
- Duplicate error messages
- Summarize completed phases to one line

### Tier 3: Aggressive (75%+ usage)
Keep only critical information:

**KEEP FULL**:
- Current task description
- Active errors with context
- ALL skeleton contracts/interfaces
- Applicable GOTCHAS
- Current file being edited

**SUMMARIZE TO BULLETS**:
- Each completed phase → 2-3 bullets
- Architecture decisions → Key choices only
- Test results → Coverage % and failures

**DROP COMPLETELY**:
- All file contents except current
- All search history
- All command output
- Historical discussions
- Implementation details (keep signatures only)

## When Invoked

When you run `/purge`:

1. **Calculate current usage**
   ```python
   usage = current_tokens / max_tokens
   ```

2. **Apply appropriate tier**
   - < 50%: Tier 1 only (remove junk)
   - 50-75%: Tier 1 + 2 (moderate)
   - 75%+: All tiers (aggressive)

3. **Report results**
   ```
   Context: 67% → 45% (removed 22k tokens)
   Applied: Moderate compression
   Kept: All code, errors, current work
   Dropped: Old searches, success messages
   Summarized: Phase 1-2 to bullets
   ```

## Integration with /conduct

The conductor automatically invokes purge at phase transitions:

- **Phase 1 → 2**: Clean if > 40%
- **Phase 2 → 3**: Clean if > 50%  
- **Phase 3 → 4**: Moderate if > 60%
- **Phase 4 → 5**: Aggressive if > 75%

## Patterns to Remove

### Always Remove (Regex)
```python
patterns = [
    r"^\w+@[\w-]+.*\$\s*$",  # Shell prompts
    r"^File .* successfully.*$",  # Success messages
    r"^\s*$",  # Empty lines
    r"^={10,}$|^-{10,}$",  # Separators
    r"^added \d+ packages.*$",  # npm/pip output
    r"^Loading\.\.\.|^Downloading\.\.\.$",  # Progress
    r"^Checking.*\.\.\.$",  # Status messages
]
```

### Smart Compression Rules
- Keep error context (5 lines before/after)
- Keep interface definitions completely
- Summarize discussions to decisions only
- Drop implementation, keep signatures

## Protection Rules

NEVER remove or compress:
- Current task description
- Unresolved errors
- Skeleton contracts
- GOTCHAS.md content
- MODULE_CACHE.json references
- Active work in progress

## Example Compression

**Before (82% full):**
```
Phase 1: Architecture complete with 15 decisions...
[500 lines of analysis]
Phase 2: Skeleton built with validation...
[300 lines of skeleton]
Phase 3: Implementation in progress...
[Current work]
```

**After moderate purge (45% full):**
```
Phase 1: ✓ Architecture (15 decisions → kept in ARCHITECTURE.md)
Phase 2: ✓ Skeleton validated
Phase 3: Implementation in progress...
[Current work - unchanged]
```

## Manual Override

You can force specific compression:
```
/purge aggressive
```
Even if usage is only 30%, this applies tier 3 rules.

## Important Notes

- This does NOT affect Claude's auto-compact
- Run proactively to avoid hitting auto-compact
- Conductor runs this automatically at phase transitions
- All compressions are logged for debugging