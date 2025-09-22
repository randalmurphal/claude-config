# Claude Code Hooks

Custom hooks that enhance Claude Code's development workflow with architecture enforcement, fallback prevention, and intelligent learning.

## 🚀 Major Features

### Architecture Enforcement
- Automatic layer detection (presentation/business/data/infrastructure)
- Import validation to prevent boundary violations
- Bug prevention using Neo4j FIXED_BY relationships

### NO FALLBACK Prevention
- **BLOCKS** fallback logic and degraded error handling
- Forces proper solutions or clear failures
- Detects and prevents workarounds

### Universal Learning System
- Semantic content storage with proper embeddings
- Sprint review for pattern validation
- Developer preference learning and application

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

### no_fallback_enforcer.py
**Purpose**: Prevents fallback logic and degraded error handling.

**Features**:
- Stores forbidden patterns in ANCHORS tier
- Detects silent fallbacks, feature detection, error masking
- Provides specific fix suggestions
- Blocks workarounds and temporary fixes

### sprint_review_command.py
**Purpose**: Reviews and validates patterns from development sprints.

**Command**: `/sprint-review [days]`

**Features**:
- Auto-detects main git branch
- Categorizes patterns by survival rate
- Bulk promote/demote/archive operations

### universal_learner.py
**Purpose**: Core learning system with semantic storage.

**Features**:
- Proper semantic content storage
- Neo4j relationship management
- Multi-tier memory system (ANCHORS, LONGTERM, EPISODIC, WORKING)

### unified_context_provider.py
**Purpose**: Provides architecture and bug prevention context.

**Features**:
- Architecture layer detection
- Bug prevention via FIXED_BY relationships
- Import validation
- Context injection before writes

### edit_tracker.py
**Purpose**: Tracks edit patterns and detects degradation.

**Features**:
- File coupling detection
- Architecture pattern tracking
- Degradation detection across edits
- Violation tracking

### unified_code_validator.py
**Purpose**: Comprehensive code validation with fallback prevention.

**Features**:
- Fallback pattern blocking (highest priority)
- Security scanning
- Complexity analysis
- Hallucination detection

### auto_formatter.py
**Purpose**: Applies formatting with developer preferences.

**Features**:
- Learns from developer's actual code
- Applies preferences after project standards
- Supports Python, JavaScript, TypeScript, Go, Rust

## Integration

These hooks can be integrated into your workflow by:

1. **Manual execution**: Run hooks before committing changes
2. **Git hooks**: Add to pre-commit hooks for automatic validation
3. **CI/CD**: Include in continuous integration pipelines
4. **Editor integration**: Configure your editor to run on save

## Configuration

Hooks store their cache and configuration in:
- `.claude/interface_cache.json` - Interface definitions cache
- `.claude/hook_config.json` - Hook-specific configuration (if needed)
- `.claude/universal_learner_config.json` - Learning system configuration
- `.claude/edit_session.json` - Edit tracking session data
- `.claude/project_knowledge.json` - Accumulated project knowledge
- `.claude/FORBIDDEN_PATTERNS.md` - Documentation of blocked patterns
- `.claude/SYSTEM_IMPROVEMENTS_2025.md` - System enhancement documentation

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