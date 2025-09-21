# Claude Code Hooks System

## Overview

The Claude Code hooks system enhances AI interactions through intelligent code validation, context injection, and learning mechanisms. The system uses **unified hooks** that consolidate functionality from multiple sources, providing a streamlined and efficient experience.

## Active Hooks (8 total)

### Core Unified Hooks

#### 1. `unified_bash_guardian.py`
**Triggers:** PreToolUse when tool_name == "Bash"

Consolidates bash safety and learning features:
- Blocks truly dangerous commands (rm -rf /, DROP DATABASE, etc.)
- Warns on risky operations with helpful alternatives
- Learns and suggests command workflows
- Tracks error→fix mappings for future reference
- Retrieves and uses stored patterns from PRISM memory

#### 2. `unified_code_validator.py`
**Triggers:** PreToolUse when tool_name in ["Write", "Edit", "MultiEdit"]

Comprehensive code validation combining:
- Hallucination detection using PRISM semantic analysis
- Security scanning (SQL injection, XSS, hardcoded secrets)
- Code complexity analysis (cyclomatic, cognitive complexity)
- Pattern validation against known good/bad patterns
- Automatic storage of validated patterns for reuse

#### 3. `unified_context_provider.py`
**Triggers:**
- UserPromptSubmit (inject context)
- PostToolUse for Read/Bash (learning)

Smart context management:
- Extracts intent from user messages
- Retrieves relevant memories from ALL PRISM tiers
- Loads project-specific knowledge (DECISION_MEMORY.json, INVARIANTS.md)
- Accumulates patterns from operations
- Provides relevant context to improve responses

#### 4. `orchestration_learner.py`
**Triggers:** PostToolUse when tool_name == "Task"

Agent performance optimization:
- Tracks performance metrics per agent type
- Learns optimal agent sequences
- Identifies chamber patterns and conflicts
- Builds performance profiles
- Suggests better agent choices based on history

### Specialized Hooks

#### 5. `assumption_detector.py`
**Triggers:** PreToolUse when tool_name == "Task"

Validates agent prompts for assumptions:
- Detects uncertainty language ("probably", "should be", "existing")
- Identifies unverified references
- Blocks agent execution if confidence < 95%
- Modifies prompts to require verification first

#### 6. `auto_formatter.py`
**Triggers:** PostToolUse when tool_name in ["Write", "Edit", "MultiEdit"]

Automatic code formatting:
- Detects language from file extension
- Applies appropriate formatter (ruff/black for Python, prettier for JS/TS, etc.)
- Uses project config if available, falls back to global configs
- Non-blocking operation (continues even if formatting fails)

#### 7. `file_protection.py`
**Triggers:** PreToolUse when tool_name in ["Write", "Edit", "MultiEdit"]

Protects sensitive files from modification:
- Configurable protection rules in file-protection-config.json
- Blocks modifications to critical system files
- Warns on sensitive file access

#### 8. `vibe_tracker.py`
**Triggers:** SessionStart

Personality mode management:
- Sets session vibe (solo, concert, duo, mentor)
- Tracks vibe state across sessions
- Adjusts interaction style based on mode

## Support Files

### `prism_client.py`
Unified PRISM MCP client providing:
- Connection to PRISM memory services
- Memory storage/retrieval across tiers (ANCHORS, WORKING, LONGTERM, EPISODIC)
- Semantic analysis (hallucination detection, residue calculation)
- Singleton pattern for efficient resource usage

### `prism_mcp_jsonrpc_client.py`
Low-level JSON-RPC communication with PRISM MCP server.

### `patterns/` Directory
Contains reference patterns for validation:
- `anti_patterns.json` - Code patterns to avoid
- `security_patterns.json` - Security vulnerabilities to detect
- `complexity_patterns.json` - Complexity thresholds
- `embeddings.db` - CodeT5+ embeddings database

## Configuration

### Hook Configuration (`settings.json`)
```json
{
  "hooks": {
    "SessionStart": [
      {"command": "$HOME/.claude/hooks/vibe_tracker.py setVibe solo"}
    ],
    "UserPromptSubmit": [
      {"command": "$HOME/.claude/hooks/unified_context_provider.py"}
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "$HOME/.claude/hooks/unified_bash_guardian.py"
      },
      {
        "matcher": "Write|Edit|MultiEdit",
        "command": "$HOME/.claude/hooks/unified_code_validator.py"
      },
      {
        "matcher": "Task",
        "command": "$HOME/.claude/hooks/assumption_detector.py"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "command": "$HOME/.claude/hooks/auto_formatter.py"
      }
    ]
  }
}
```

### PRISM Configuration (`prism_config.yaml`)
Memory tier configuration and connection settings for PRISM services.

## Architecture

### Memory Tiers
- **ANCHORS**: Immutable project truths
- **WORKING**: Session-specific context (Redis-backed)
- **LONGTERM**: Persistent patterns and knowledge
- **EPISODIC**: Time-based event sequences

### Performance Characteristics
- Non-blocking operations (all hooks use "continue" action)
- Intelligent caching to reduce latency
- Relevance thresholds to filter noise
- CodeT5+ embeddings for semantic analysis (768-dim vectors)

### Safety Features
- Graceful degradation when PRISM unavailable
- Comprehensive error handling
- Audit logging for critical operations
- Confidence thresholds for blocking operations

## Testing

Test individual hooks:
```bash
# Test bash guardian
echo '{"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}' | python unified_bash_guardian.py

# Test code validator
echo '{"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "/tmp/test.py", "content": "eval(user_input)"}}' | python unified_code_validator.py

# Test context provider
echo '{"hook_event_name": "UserPromptSubmit", "user_message": "fix bug in auth"}' | python unified_context_provider.py
```

## Troubleshooting

### Common Issues

1. **Hooks not triggering**: Check settings.json configuration
2. **PRISM connection errors**: Ensure PRISM MCP server is running
3. **Slow performance**: Check prism_bash_debug.log for bottlenecks
4. **False positives**: Adjust confidence thresholds in individual hooks

### Debug Logs
- `prism_bash_debug.log` - Bash guardian activity
- `bash_command_history.json` - Command history tracking
- `operation_history.json` - Operation patterns

## Key Benefits

1. **Unified Architecture**: Consolidated from 14+ hooks to 4 core unified hooks
2. **Intelligent Learning**: Patterns improve with each session
3. **Safety First**: Multiple layers of validation and protection
4. **Context Aware**: Deep integration with project knowledge
5. **Performance Optimized**: Smart caching and relevance filtering

## Version
Last Updated: 2024-09-21
Hook System: v2.0 (Unified Architecture)