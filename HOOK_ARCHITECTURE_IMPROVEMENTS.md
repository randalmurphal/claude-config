# Hook Architecture Improvements

## Overview
Major improvements to the Universal Learning System hooks to focus on **producing better code quality** through architecture enforcement, bug prevention, and developer preferences.

## New/Updated Hooks

### 1. **unified_context_provider.py** ✨ Enhanced
- **Architecture Context Injection**: Detects layers and enforces boundaries
- **Bug Prevention**: Queries Neo4j for FIXED_BY relationships to prevent recurring bugs
- **Layer Detection**: Identifies presentation/business/data/infrastructure layers
- **Import Validation**: Checks for architecture violations after writes

### 2. **edit_tracker.py** ✨ Enhanced
- **Architectural Pattern Tracking**: Tracks which layer each file belongs to
- **Import Analysis**: Extracts and validates import statements
- **Violation Detection**: Identifies and stores architecture violations
- **File Coupling**: Enhanced with architectural awareness

### 3. **sprint_review_command.py** 🆕 New
- **Command**: `/sprint-review [days]`
- **Git Branch Detection**: Automatically detects main/master/develop branch
- **Pattern Review**: Categorizes patterns by survival rate and usage
- **Bulk Operations**: Promote/demote/archive patterns based on validation

### 4. **auto_formatter.py** ✨ Enhanced
- **Developer Preferences**: Learns individual coding style from actual code
- **Project Requirements**: Respects project standards over personal preferences
- **Smart Application**: Applies preferences only when no conflict with project
- **Learning**: Continuously learns from developer's code patterns

### 5. **universal_learner.py** ✅ Fixed
- **Semantic Storage**: Now stores human-readable content instead of JSON
- **Neo4j Integration**: Properly uses graph relationships
- **Configuration**: External config file at `~/.claude/universal_learner_config.json`
- **Optimized Thresholds**: Similarity threshold 0.3 for better F1-score

## How They Work Together

```
PRE-WRITE Phase:
├── unified_context_provider.py
│   ├── Injects architecture rules (layer, allowed imports)
│   └── Provides bug prevention context (previous fixes)
│
WRITE Phase:
├── Claude writes informed code
│
POST-WRITE Phase:
├── edit_tracker.py
│   ├── Tracks architectural patterns
│   └── Detects violations
├── unified_context_provider.py
│   └── Validates architecture
└── auto_formatter.py
    ├── Applies project standards
    └── Applies developer preferences

SPRINT Review:
└── sprint_review_command.py
    ├── Reviews pattern quality
    └── Promotes validated patterns
```

## Configuration

### universal_learner_config.json
Located at `~/.claude/universal_learner_config.json`:
- Similarity thresholds
- Memory tier thresholds
- Cache TTLs by pattern type
- Validation settings

### Developer Preferences
- Set `CLAUDE_DEVELOPER` environment variable
- System learns from your code automatically
- Preferences applied after project standards

## Key Features

### Architecture Enforcement
- **Layer Hierarchy**: Presentation → Business → Data → Infrastructure
- **Automatic Detection**: Based on file paths and names
- **Violation Warnings**: Non-blocking but informative
- **Pattern Learning**: Stores architectural decisions

### Bug Prevention
- **FIXED_BY Relationships**: Leverages Neo4j graph
- **Context Injection**: Warns before similar bugs
- **Pattern Storage**: Learns from fixes
- **Proactive Prevention**: Applies before writing

### Developer Preferences
- **Automatic Learning**: From actual code, not config
- **Project Priority**: Project standards override preferences
- **Non-Conflicting**: Only applies safe preferences
- **Individual Profiles**: Per-developer settings

## Commands

### Sprint Review
```bash
# Review last 14 days (default)
/sprint-review

# Review specific period
/sprint-review 7
```

## Testing
Comprehensive test suite at `/tmp/test_architecture_improvements.py`:
- All 8 test categories passing ✅
- Full integration testing
- Architecture violation detection
- Developer preference application

## Benefits

1. **Better Code Quality**: Enforces architecture automatically
2. **Bug Prevention**: Learns from past mistakes
3. **Consistency**: Maintains style across team
4. **Non-Intrusive**: Works in background
5. **Continuous Learning**: Improves over time

## Files Modified

### Core Hooks
- `unified_context_provider.py` - Architecture and bug context
- `edit_tracker.py` - Pattern tracking with layers
- `auto_formatter.py` - Developer preferences
- `universal_learner.py` - Semantic storage fixes

### New Files
- `sprint_review_command.py` - Sprint pattern review
- `universal_learner_config.json` - Configuration
- `UNIVERSAL_LEARNER_TUNING.md` - Tuning guide

### Supporting Files
- `unified_bash_guardian.py` - Error pattern learning
- `unified_code_validator.py` - Quality validation
- `services_wrapper.py` - Threshold optimization

## Future Enhancements
- Production validation through git commits
- Pattern decay based on usage
- Team-wide pattern sharing
- A/B testing for thresholds