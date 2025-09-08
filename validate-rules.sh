#!/bin/bash

# Claude Code Rule Validator - PostToolUse Hook
# Enforces: No fake data, no partial implementations, prefer refactoring over duplication

set -euo pipefail

# Read hook input from stdin
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')

# Only validate code modifications
if [[ ! "$tool_name" =~ ^(Write|Edit|MultiEdit)$ ]]; then
    exit 0
fi

# Extract file path and content based on tool type
if [[ "$tool_name" == "MultiEdit" ]]; then
    # For MultiEdit, we need to check each edit
    file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.filePath')
    # Get the final content after all edits (from tool_response)
    if echo "$input" | jq -e '.tool_response.success' >/dev/null 2>&1; then
        # Read the actual file to check final state
        if [[ -f "$file_path" ]]; then
            content=$(cat "$file_path")
        else
            exit 0
        fi
    else
        exit 0
    fi
else
    # For Write/Edit
    file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.filePath')
    content=$(echo "$input" | jq -r '.tool_input.content // .tool_input.new_string // ""')
fi

# Skip if no content to validate
if [[ -z "$content" ]]; then
    exit 0
fi

violations=()

# ============================================
# CHECK 1: Fake Data and Placeholder Patterns
# ============================================

# Common fake data patterns (case insensitive)
fake_patterns=(
    'TODO|FIXME|XXX|HACK'
    'placeholder|dummy|fake|mock_|stub_'
    'test_?data|sample_?data|example_?data'
    'foo|bar|baz|qux|quux'  # Unless in actual variable names
    'example\.com|test\.com|fake\.com|dummy\.com'
    'john_?doe|jane_?doe|test_?user'
    '123456|password123|admin123|test123'
    'lorem ipsum|dolor sit amet'
)

for pattern in "${fake_patterns[@]}"; do
    if echo "$content" | grep -qiE "$pattern"; then
        # Check if it's in a comment or string (might be legitimate documentation)
        if echo "$content" | grep -iE "$pattern" | grep -qvE '^\s*(#|//|\*|")'; then
            match=$(echo "$content" | grep -iE "$pattern" | head -1 | sed 's/^[[:space:]]*//')
            violations+=("❌ Contains fake/placeholder data: '${match:0:60}...'")
            break
        fi
    fi
done

# ============================================
# CHECK 2: Partial Implementations
# ============================================

# Language-specific partial implementation patterns
extension="${file_path##*.}"

case "$extension" in
    py)
        # Python partial implementations
        if echo "$content" | grep -qE '^\s*(pass)\s*(#.*)?$'; then
            violations+=("❌ Contains unimplemented code (pass statement)")
        fi
        if echo "$content" | grep -qE 'raise NotImplementedError'; then
            violations+=("❌ Contains NotImplementedError (partial implementation)")
        fi
        if echo "$content" | grep -qE '^\s*\.\.\.\s*(#.*)?$'; then
            violations+=("❌ Contains ellipsis as placeholder")
        fi
        # Check for functions that just return None or hardcoded values
        if echo "$content" | grep -qE 'def .+\(.*\):\s*(#.*)?\s*return (None|True|False|\[\]|\{\}|""|'"'"''"'"')$'; then
            violations+=("❌ Function returns hardcoded empty/placeholder value")
        fi
        ;;
        
    js|ts|jsx|tsx)
        # JavaScript/TypeScript partial implementations
        if echo "$content" | grep -qE 'throw new Error\(.*(not implemented|todo|implement me)'; then
            violations+=("❌ Contains 'not implemented' error (partial implementation)")
        fi
        if echo "$content" | grep -qE '^\s*\/\/ implement me|\/\/ todo: implement'; then
            violations+=("❌ Contains implementation TODO comment")
        fi
        if echo "$content" | grep -qE 'return (null|undefined|""|'"'"''"'"'|\[\]|\{\});\s*(\/\/.*)?$'; then
            if echo "$content" | grep -B2 'return' | grep -qE 'TODO|implement|placeholder'; then
                violations+=("❌ Function returns placeholder value with TODO")
            fi
        fi
        ;;
        
    java)
        # Java partial implementations
        if echo "$content" | grep -qE 'throw new UnsupportedOperationException'; then
            violations+=("❌ Contains UnsupportedOperationException (partial implementation)")
        fi
        if echo "$content" | grep -qE 'return null;\s*//\s*(TODO|FIXME|implement)'; then
            violations+=("❌ Returns null with TODO (partial implementation)")
        fi
        ;;
        
    go)
        # Go partial implementations
        if echo "$content" | grep -qE 'panic\(.*(not implemented|todo|unimplemented)'; then
            violations+=("❌ Contains 'not implemented' panic (partial implementation)")
        fi
        ;;
        
    *)
        # Generic checks for other languages
        if echo "$content" | grep -qiE 'not.?implemented|to.?be.?implemented|coming.?soon'; then
            violations+=("❌ Contains 'not implemented' marker")
        fi
        ;;
esac

# Check for empty function bodies (multi-language)
if echo "$content" | grep -qE '(function|def|func|fn|method|proc)\s+\w+\s*\([^)]*\)\s*\{?\s*\}?$'; then
    violations+=("⚠️ Contains empty function definition")
fi

# ============================================
# CHECK 3: Code Duplication
# ============================================

# Only check for duplication when creating new files
if [[ "$tool_name" == "Write" ]]; then
    dir=$(dirname "$file_path")
    filename=$(basename "$file_path")
    base_name="${filename%.*}"
    extension="${filename##*.}"
    
    # Check if we're creating a numbered/versioned file (code_v2.py, code2.py, code_new.py)
    if echo "$base_name" | grep -qE '(_v[0-9]+|[0-9]+|_new|_copy|_backup|_old|_temp)$'; then
        # Strip the version suffix to find the original
        original_base=$(echo "$base_name" | sed -E 's/(_v[0-9]+|[0-9]+|_new|_copy|_backup|_old|_temp)$//')
        
        # Look for the original file
        if ls "$dir" 2>/dev/null | grep -qE "^${original_base}\.${extension}$"; then
            violations+=("❌ Creating versioned duplicate of '$original_base.$extension' - refactor the existing file instead")
        fi
    fi
    
    # Check for very similar filenames (edit distance)
    if [[ -d "$dir" ]]; then
        for existing_file in "$dir"/*."$extension"; do
            [[ ! -f "$existing_file" ]] && continue
            existing_base=$(basename "$existing_file" ".$extension")
            
            # Skip if it's the same file
            [[ "$existing_base" == "$base_name" ]] && continue
            
            # Check for common duplication patterns
            if echo "$base_name" | grep -qiE "(utils?|helpers?|common|shared|lib|core|base)"; then
                if echo "$existing_base" | grep -qiE "(utils?|helpers?|common|shared|lib|core|base)"; then
                    violations+=("⚠️ Creating '$filename' when '$existing_base.$extension' exists - consider refactoring shared utilities")
                    break
                fi
            fi
        done
    fi
    
    # Check for duplicate class/function definitions across files
    if [[ "$extension" =~ ^(py|js|ts|java|go)$ ]]; then
        # Extract main class/function names from content
        if [[ "$extension" == "py" ]]; then
            new_definitions=$(echo "$content" | grep -E '^(class|def) ' | sed -E 's/(class|def) ([a-zA-Z_][a-zA-Z0-9_]*).*/\2/' | head -5)
        elif [[ "$extension" =~ ^(js|ts)$ ]]; then
            new_definitions=$(echo "$content" | grep -E '^(class|function|const [a-zA-Z_][a-zA-Z0-9_]* =)' | sed -E 's/(class|function|const) ([a-zA-Z_][a-zA-Z0-9_]*).*/\2/' | head -5)
        fi
        
        if [[ -n "$new_definitions" ]] && [[ -d "$dir" ]]; then
            for def in $new_definitions; do
                # Search for this definition in other files
                for other_file in "$dir"/*."$extension"; do
                    [[ ! -f "$other_file" ]] && continue
                    [[ "$other_file" == "$file_path" ]] && continue
                    
                    if grep -qE "(class|def|function|const) $def" "$other_file" 2>/dev/null; then
                        violations+=("❌ Definition '$def' already exists in '$(basename "$other_file")' - refactor instead of duplicating")
                        break 2
                    fi
                done
            done
        fi
    fi
fi

# ============================================
# CHECK 4: Common Anti-patterns
# ============================================

# Check for console.log/print statements in production code
if [[ ! "$file_path" =~ (test|spec|debug) ]]; then
    if echo "$content" | grep -qE '^\s*console\.(log|debug|info)'; then
        violations+=("⚠️ Contains console.log in non-test file - use proper logging")
    fi
    if [[ "$extension" == "py" ]] && echo "$content" | grep -qE '^\s*print\('; then
        if ! echo "$content" | grep -qE '^\s*#.*print\('; then
            violations+=("⚠️ Contains print() in non-test file - use proper logging")
        fi
    fi
fi

# Check for hardcoded secrets/credentials patterns
if echo "$content" | grep -qE '(api[_-]?key|secret|password|token|credential)\s*=\s*["\'"'"'][^"\'"'"']+["\'"'"']'; then
    if ! echo "$content" | grep -qE '(getenv|environ|process\.env|config\.)'; then
        violations+=("🚨 Possible hardcoded credential - use environment variables")
    fi
fi

# ============================================
# OUTPUT RESULTS
# ============================================

if [[ ${#violations[@]} -gt 0 ]]; then
    # Format violations as JSON
    reason="Code violates your CLAUDE.md rules:\n"
    for violation in "${violations[@]}"; do
        reason="${reason}${violation}\n"
    done
    reason="${reason}\nFix these issues or explain why they're necessary."
    
    # Use jq to create proper JSON
    jq -n --arg reason "$reason" '{
        "decision": "block",
        "reason": $reason
    }'
    exit 0
fi

# Success - optionally provide positive feedback
if [[ "$extension" =~ ^(py|js|ts|java|go)$ ]]; then
    # Count some positive patterns
    has_error_handling=false
    has_tests=false
    
    if echo "$content" | grep -qE '(try|catch|except|rescue|recover)'; then
        has_error_handling=true
    fi
    
    if [[ "$file_path" =~ (test|spec) ]] || echo "$content" | grep -qE '(describe|test|it)\(|def test_|@Test'; then
        has_tests=true
    fi
    
    if [[ "$has_error_handling" == "true" ]] || [[ "$has_tests" == "true" ]]; then
        feedback="✅ Good practices detected:"
        [[ "$has_error_handling" == "true" ]] && feedback="$feedback error-handling"
        [[ "$has_tests" == "true" ]] && feedback="$feedback testing"
        echo "$feedback"
    fi
fi

exit 0