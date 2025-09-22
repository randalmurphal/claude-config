# FORBIDDEN PATTERNS - NO FALLBACK POLICY

## ❌ ABSOLUTELY FORBIDDEN

These patterns will be **BLOCKED** by the validation system. You MUST NOT write:

### 1. Silent Fallbacks
```python
# ❌ FORBIDDEN
try:
    advanced_method()
except:
    simple_method()  # Silent fallback

# ✅ CORRECT
advanced_method()  # Fix it if it's broken
```

### 2. Feature Detection Fallbacks
```python
# ❌ FORBIDDEN
if has_advanced_lib:
    use_advanced()
else:
    use_basic()  # Degraded functionality

# ✅ CORRECT
import advanced_lib  # Require it in requirements.txt
use_advanced()
```

### 3. Error Masking
```python
# ❌ FORBIDDEN
try:
    result = complex_operation()
except:
    return None  # Hiding errors

# ✅ CORRECT
result = complex_operation()  # Let errors bubble up
# OR
try:
    result = complex_operation()
except SpecificError as e:
    raise RuntimeError(f"Operation failed: {e}") from e
```

### 4. Degraded Retries
```python
# ❌ FORBIDDEN
for method in [advanced, intermediate, basic]:
    try:
        return method()
    except:
        continue  # Trying progressively worse methods

# ✅ CORRECT
return advanced()  # Make it reliable
```

### 5. Workarounds Instead of Fixes
```python
# ❌ FORBIDDEN
# Workaround for bug in function X
if version < 2.0:
    use_hack()

# ✅ CORRECT
# Fix the bug or update to fixed version
use_proper_function()
```

## 🚫 NEVER DO THIS

1. **Don't check if features are available** - Require them
2. **Don't catch exceptions to use simpler logic** - Fix the root cause
3. **Don't return None/empty on errors** - Raise clear errors
4. **Don't add workarounds** - Fix the actual problem
5. **Don't degrade functionality** - Make it work properly

## ✅ ALWAYS DO THIS INSTEAD

### When Something Doesn't Work:
1. **FIX THE ROOT CAUSE** - Don't avoid it
2. **RAISE CLEAR ERRORS** - Explain what's wrong
3. **REQUIRE DEPENDENCIES** - Don't check availability
4. **DOCUMENT REQUIREMENTS** - Be explicit about needs
5. **FAIL FAST AND CLEARLY** - Never silently degrade

### Error Handling Philosophy:
```python
# ✅ GOOD: Specific error handling
try:
    data = load_config()
except FileNotFoundError:
    raise FileNotFoundError(f"Config file required at {path}")

# ✅ GOOD: Let unexpected errors bubble
data = process_data()  # Don't catch what you can't handle

# ✅ GOOD: Re-raise with context
try:
    result = risky_operation()
except Exception as e:
    raise RuntimeError(f"Failed to complete operation: {e}") from e
```

## 🛡️ ENFORCEMENT

### Automatic Detection
The system will:
1. **BLOCK** writes containing fallback patterns
2. **WARN** about degradation attempts
3. **TRACK** workaround patterns
4. **PREVENT** silent error handling

### Pattern Learning
- Forbidden patterns stored in **ANCHORS** tier (permanent)
- Violations tracked and prevented in future
- Degradation attempts detected across edits

## 📋 EXAMPLES OF BLOCKED PATTERNS

### Example 1: Import Fallback
```python
# ❌ WILL BE BLOCKED
try:
    import advanced_module
    use_advanced = True
except ImportError:
    use_advanced = False
    import basic_module

if use_advanced:
    processor = advanced_module.Processor()
else:
    processor = basic_module.SimpleProcessor()
```

**FIX**: Add `advanced_module` to requirements and remove fallback

### Example 2: API Degradation
```python
# ❌ WILL BE BLOCKED
try:
    result = api_v2.get_detailed_data()
except:
    # Fall back to older API
    result = api_v1.get_basic_data()
```

**FIX**: Fix the v2 API connection or raise clear error

### Example 3: Silent Failure
```python
# ❌ WILL BE BLOCKED
def get_user(user_id):
    try:
        return database.fetch_user(user_id)
    except:
        return {}  # Return empty dict on error
```

**FIX**: Let the error propagate or handle specific cases

## 🎯 GOAL

**WRITE ROBUST CODE THAT WORKS PROPERLY**

Not code that:
- Silently degrades
- Hides errors
- Uses workarounds
- Falls back to worse solutions

## 📝 REMEMBER

> "If it doesn't work properly, FIX IT. Don't hide it, work around it, or fall back to something worse."

This policy is **ENFORCED AUTOMATICALLY** by the validation system. Violations will be **BLOCKED**.