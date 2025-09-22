# Claude Code Hooks

Event-driven automation hooks that enhance Claude Code with intelligent learning, validation, and safety features.

## 🎯 Overview

These hooks integrate with Claude Code to provide:
- **PRISM Integration**: Semantic reasoning and persistent memory
- **Universal Learning**: Cross-session pattern recognition
- **Quality Gates**: Code validation and formatting
- **Safety Checks**: Command and code safety analysis
- **Pattern Tracking**: File relationships and workflow learning

## 🔧 Active Hooks by Event

### SessionStart
- **prism_http_startup.py**: Starts PRISM HTTP server at localhost:8090
- **vibe_tracker.py**: Sets personality mode (solo/concert/duo/mentor)
- **chamber_cleanup.py**: Cleans up git worktrees from orchestration
- **orchestration_dashboard.py**: Displays task status

### SessionEnd
- **universal_learner_session_end.py**: Promotes patterns based on usage, saves session summary

### UserPromptSubmit
- **unified_context_provider.py**: Retrieves relevant context from PRISM memory
- **auto_orchestration_detector.py**: Detects complex tasks needing orchestration
- **orchestration_dashboard.py**: Updates task progress

### PreToolUse
- **unified_bash_guardian.py** (Bash): Analyzes command safety, learns error fixes
- **unified_code_validator.py** (Write/Edit): Validates patterns, prevents fallbacks
- **file_protection.py** (Write/Edit): Protects critical files
- **edit_tracker.py** (Write/Edit): Tracks file edit patterns
- **assumption_detector.py** (Task): Catches unstated assumptions

### PostToolUse
- **auto_formatter.py** (Write/Edit): Auto-formats code with language-specific tools
- **edit_tracker.py** (Write/Edit): Records file relationships
- **orchestration_learner.py** (Task): Learns from agent outcomes
- **orchestration_progress.py** (Task): Updates orchestration status
- **unified_context_provider.py** (Read/Bash): Updates context after operations
- **test_coverage_enforcer.py** (Bash): Enforces test coverage requirements

## 📚 Core Hooks

### PRISM Integration Hooks

#### prism_http_startup.py
- **Trigger**: SessionStart
- **Purpose**: Auto-starts PRISM HTTP server
- **Features**: Health checks, detached process, graceful startup

#### prism_client.py / prism_http_client.py
- **Type**: Library (not a hook)
- **Purpose**: HTTP client for PRISM communication
- **Used by**: Most other hooks for memory and analysis

### Learning System

#### universal_learner.py
- **Type**: Library
- **Purpose**: Core learning system with semantic extraction
- **Features**:
  - Extracts human-readable content from patterns
  - Stores in PRISM memory tiers
  - Creates Neo4j relationships
  - Multi-mode search (semantic, graph, hybrid)

#### universal_learner_session_end.py
- **Trigger**: SessionEnd
- **Purpose**: Consolidates and promotes patterns
- **Features**:
  - Promotes patterns used 3+ times
  - Fast-tracks security patterns (2+ uses)
  - Saves session summaries
  - Cleans up stale patterns (7+ days)

### Validation & Safety

#### unified_code_validator.py
- **Trigger**: PreToolUse (Write/Edit)
- **Purpose**: Prevents bad patterns and fallbacks
- **Blocks**:
  - Linter suppressions (noqa, eslint-disable)
  - Silent fallbacks and error masking
  - Nested ternaries and double negation
  - Poor error messages

#### unified_bash_guardian.py
- **Trigger**: PreToolUse (Bash)
- **Purpose**: Command safety and learning
- **Features**:
  - Detects dangerous commands
  - Learns error fixes
  - Provides recovery suggestions
  - Stores workflow patterns

### Context & Learning

#### unified_context_provider.py
- **Trigger**: UserPromptSubmit, PostToolUse (Read/Bash)
- **Purpose**: Intelligent context retrieval
- **Features**:
  - Searches PRISM for relevant patterns
  - Provides error fixes
  - Suggests related files
  - Updates operation history

#### orchestration_learner.py
- **Trigger**: PostToolUse (Task)
- **Purpose**: Learns from orchestration agents
- **Features**:
  - Tracks agent performance
  - Promotes successful patterns
  - Stores workflow patterns
  - Updates confidence scores

### Code Quality

#### auto_formatter.py
- **Trigger**: PostToolUse (Write/Edit)
- **Purpose**: Auto-formats code
- **Language Support**:
  - Python: ruff → black fallback
  - JavaScript/TypeScript: prettier → eslint
  - Go: goimports → gofmt
- **Features**:
  - Detects project configs
  - Preserves quote styles
  - Learns developer preferences

#### test_coverage_enforcer.py
- **Trigger**: PostToolUse (Bash)
- **Purpose**: Enforces test coverage
- **Requirements**:
  - 95% line coverage
  - 100% function coverage
- **Features**:
  - Parses pytest/jest output
  - Learns coverage patterns
  - Blocks on low coverage

### File Tracking

#### edit_tracker.py
- **Trigger**: Pre/PostToolUse (Write/Edit)
- **Purpose**: Tracks file relationships
- **Features**:
  - Detects file coupling
  - Identifies architecture layers
  - Records edit sequences
  - Creates Neo4j relationships

#### file_protection.py
- **Trigger**: PreToolUse (Write/Edit)
- **Purpose**: Protects critical files
- **Protected**:
  - Package files (package.json, pyproject.toml)
  - Configs (.env, settings.json)
  - CI/CD files
- **Features**: Requires confirmation for critical changes

## 🔧 Configuration

### Hook Registration (settings.json)
```json
{
  "hooks": {
    "SessionEnd": [{"hooks": [{"type": "command", "command": "$HOME/.claude/hooks/universal_learner_session_end.py"}]}],
    "SessionStart": [{"hooks": [{"type": "command", "command": "$HOME/.claude/hooks/prism_http_startup.py"}]}],
    // ... other hooks
  }
}
```

### Universal Learner Config (universal_learner_config.json)
- Memory tier thresholds
- Promotion rules (usage counts)
- Cleanup settings
- Graph relationships
- Redis TTL by pattern type

### PRISM Config (prism_config.yaml)
- HTTP server settings
- Service endpoints
- Memory tier configurations

## 🧠 Memory Tiers

Patterns are stored in PRISM memory tiers:

1. **WORKING**: Active session patterns (0+ uses)
2. **EPISODIC**: Recent patterns (1+ uses, 30-day retention)
3. **LONGTERM**: Established patterns (3+ uses, 1-year retention)
4. **ANCHORS**: Critical patterns (5+ uses, permanent)

Security and critical patterns get fast-track promotion.

## 📊 Pattern Types

Common pattern types learned:
- `command_error`: Error → fix mappings
- `command_workflow`: Command sequences
- `file_coupling`: Frequently co-edited files
- `test_coverage`: Coverage insights
- `validation_error`: Code quality issues
- `best_practice`: Coding standards
- `security`: Security patterns
- `architecture`: Design decisions
- `orchestration_workflow`: Agent workflows
- `session_summary`: Session insights

## 🚀 Usage

Hooks run automatically based on events. To check their status:

```bash
# View hook configuration
cat ~/.claude/settings.json | jq '.hooks'

# Test PRISM connectivity
curl http://localhost:8090/health

# Manually trigger session end
echo '{"hook_event_name":"SessionEnd"}' | python ~/.claude/hooks/universal_learner_session_end.py

# Check learned patterns
python -c "from universal_learner import get_learner; l=get_learner(); print(len(l.pattern_cache['patterns']))"
```

## 🔍 Debugging

Enable debug output by setting environment variables:
```bash
export HOOK_DEBUG=1
export PRISM_DEBUG=1
```

Check hook logs in stderr output during Claude sessions.

## 💡 Tips

1. **Let hooks learn**: They improve with usage
2. **Review promotions**: Check session end summaries
3. **Trust validators**: They prevent common issues
4. **Check patterns**: Periodically review learned patterns
5. **Configure tiers**: Adjust promotion thresholds as needed

---

*Intelligent hooks that make Claude Code learn and improve across sessions*