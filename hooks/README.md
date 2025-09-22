# Claude Code Hooks

Custom hooks that enhance Claude Code's development workflow.

## Available Hooks

### interface_validator.py
**Purpose**: Validates interface compatibility to catch breaking changes early.

**Features**:
- Detects removed fields (breaking changes)
- Identifies type changes that break compatibility
- Finds consumer files that would be affected
- Caches interface definitions for comparison
- Supports TypeScript, JavaScript, Python, and Go

**How it works**:
1. Extracts interface/type/class definitions from files
2. Compares with cached versions to detect changes
3. Identifies breaking changes (removed fields, incompatible type changes)
4. Searches for consumer files that import the interface
5. Reports issues with affected files and suggestions

**Supported patterns**:
- TypeScript: `interface`, `type`
- Python: `@dataclass`, `TypedDict`
- Go: `struct`

**Usage**:
```bash
python interface_validator.py <file_path> <content>
```

**Example output**:
```
⚠️  Interface Compatibility Issues Detected

Breaking change in UserDTO:
  • Field 'email' was removed (breaking change)
  • Field 'id' type changed from 'number' to 'string' (breaking change)
  Affected files:
    - src/services/auth.ts
    - src/components/UserProfile.tsx
    - tests/user.test.ts

Suggestions:
  1. Make the changes backward compatible
  2. Update all consumers to handle the new interface
  3. Version the interface (e.g., UserV2) for gradual migration
```

## Integration with Claude Code

These hooks can be integrated into your workflow by:

1. **Manual execution**: Run hooks before committing changes
2. **Git hooks**: Add to pre-commit hooks for automatic validation
3. **CI/CD**: Include in continuous integration pipelines
4. **Editor integration**: Configure your editor to run on save

## Configuration

Hooks store their cache and configuration in:
- `.claude/interface_cache.json` - Interface definitions cache
- `.claude/hook_config.json` - Hook-specific configuration (if needed)

## Adding New Hooks

To add a new hook:

1. Create a Python script in this directory
2. Follow the pattern of existing hooks:
   - Accept file path and content as arguments
   - Return 0 for success, 1 for validation failure
   - Print colored output for clarity
3. Document the hook in this README

## Color Codes

Hooks use ANSI color codes for terminal output:
- 🔴 RED: Errors and breaking changes
- 🟡 YELLOW: Warnings and suggestions
- 🟢 GREEN: Success messages
- 🔵 BLUE: Information and file paths