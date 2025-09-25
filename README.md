# Claude Code Configuration & Hooks

Advanced configuration for Claude Code with PRISM integration, intelligent hooks, and cross-session learning.

## 🎯 Overview

This configuration enhances Claude Code with:
- **PRISM MCP Integration**: Semantic memory with Neo4j graphs and Qdrant vectors
- **Universal Learning**: Cross-session pattern recognition and promotion
- **Smart Hooks**: Event-driven automation for code quality and safety
- **Agent Memory Injection**: Agents receive relevant context from past sessions
- **Semantic Code Understanding**: Extracts what changed, not just metadata
- **User Preference Detection**: Learns from corrections and explicit preferences
- **Orchestration Support**: MCP-based coordination for complex tasks
- **Vibe System**: Personality modes for different work styles

## 🚀 Quick Start

### Prerequisites
- Claude Code installed
- Python 3.13+ with virtualenv at `/opt/envs/py3.13`
- Docker/nerdctl for PRISM services
- Redis, Neo4j, Qdrant running (via nerdctl)

### Installation

```bash
# Clone configuration
git clone [your-repo] ~/.claude

# Start PRISM services
cd ~/repos/claude_mcp/prism_mcp
nerdctl compose up -d

# Verify PRISM HTTP server
curl http://localhost:8090/health

# Ready to use!
claude
```

## 📁 Directory Structure

```
~/.claude/
├── settings.json           # Hook configuration
├── CLAUDE.md              # Global instructions for Claude
├── universal_learner_config.json  # Learning system config
│
├── hooks/                 # Event-driven automation
│   ├── README.md          # Hook documentation
│   ├── prism_http_startup.py     # Auto-starts PRISM server
│   ├── prism_client.py           # PRISM client wrapper
│   ├── prism_http_client.py      # HTTP client implementation
│   ├── universal_learner.py      # Cross-session learning
│   ├── universal_learner_session_end.py  # Pattern promotion
│   ├── unified_context_provider.py       # Context retrieval & agent injection
│   ├── edit_tracker.py                   # Semantic change extraction
│   ├── agent_learner.py                  # Agent discovery capture
│   ├── preference_manager.py             # User preference detection
│   ├── unified_bash_guardian.py          # Command safety
│   ├── unified_code_validator.py         # Code validation
│   ├── orchestration_learner.py          # Agent learning
│   ├── auto_formatter.py                 # Code formatting
│   ├── vibe_tracker.py                   # Personality modes
│   └── [other hooks]
│
├── configs/               # Language-specific configs
│   ├── python/           # ruff, pylint, mypy
│   ├── javascript/       # prettier, eslint
│   └── go/              # golangci
│
├── agents/               # Orchestration agents (optional)
├── commands/            # Custom commands (optional)
└── [auto-generated]     # Runtime directories
```

## 🔧 Active Hook System

### Session Hooks

**SessionStart**:
- `prism_http_startup.py` - Starts PRISM HTTP server
- `vibe_tracker.py` - Sets personality mode
- `chamber_cleanup.py` - Cleans git worktrees
- `orchestration_dashboard.py` - Shows task status

**SessionEnd**:
- `universal_learner_session_end.py` - Promotes patterns, consolidates session learnings

**UserPromptSubmit**:
- `unified_context_provider.py` - Injects relevant memories, detects preferences
- `auto_orchestration_detector.py` - Detects complex tasks
- `orchestration_dashboard.py` - Updates status

**SubagentStop**:
- `agent_learner.py` - Captures agent discoveries and patterns

### Tool Hooks

**PreToolUse**:
- Bash: `unified_bash_guardian.py` - Command safety analysis
- Write/Edit: `unified_code_validator.py` - Pattern validation, preference enforcement
- Write/Edit: `file_protection.py` - Protects critical files
- Write/Edit: `edit_tracker.py` - Extracts semantic changes
- Task: `unified_context_provider.py` - Injects memories into agent prompts
- Task: `assumption_detector.py` - Catches assumptions

**PostToolUse**:
- Read: `post_read_injector.py` - Injects file-specific memories
- Write/Edit: `auto_formatter.py` - Formats code
- Write/Edit: `edit_tracker.py` - Stores semantic memories in PRISM
- Bash: `post_error_injector.py` - Injects error fixes after failures
- Bash: `test_coverage_enforcer.py` - Enforces test coverage
- Task: `orchestration_learner.py` - Learns from agents
- Task: `orchestration_progress.py` - Updates progress
- Bash: `test_coverage_enforcer.py` - Enforces coverage

## 🧠 PRISM Integration

PRISM (Persistent Reasoning & Intelligent Semantic Memory) provides:
- **Semantic Memory Storage**: Rich JSON with changes, entities, relationships
- **Vector Search**: Qdrant database with 2,802+ semantic vectors
- **Graph Relationships**: Neo4j for file coupling and dependencies
- **Memory Tiers**: ANCHORS (critical), LONGTERM (stable), WORKING (session), EPISODIC (recent)
- **Automatic Context Injection**: Relevant memories injected into prompts and agent launches

### What Gets Stored
- **Semantic code changes**: added_error_handling, bug_fix, refactoring
- **File relationships**: TESTS, TESTED_BY, RELATED_TO
- **Agent discoveries**: Patterns, decisions, and fixes from agent outputs
- **User preferences**: Explicit rules and repeated corrections
- **Bug fixes**: Error→solution mappings

### Memory Tier Promotion
Patterns are automatically promoted based on usage:
- WORKING → LONGTERM: 3+ uses or 85%+ confidence (via background task every 5 minutes)
- Bug fixes → LONGTERM: Immediately
- User preferences → ANCHORS: With frustration level 3+ or after 2+ corrections
- Security patterns → Fast-track with 2+ uses
- Client-side deduplication prevents storing duplicates (handled in preference_manager.py)

### Ephemeral File Filtering
Automatically skips: `/tmp/*`, `node_modules/*`, `.git/*`, `venv/*`, `build/*`, `dist/*`

## 🎭 Vibe System

Set your personality mode with `/vibe`:

- **🎸 Solo** (default): Direct, slightly sarcastic, efficient
- **🎭 Concert**: Professional precision for production
- **🎼 Duo**: Collaborative exploration
- **📚 Mentor**: Socratic teaching method

```bash
/vibe              # Show current vibe
/vibe solo         # Set to solo mode
```

## 📊 Universal Learning & Memory System

### How It Works
1. **Extraction**: Hooks extract semantic meaning from your actions
   - `edit_tracker.py`: What changed in code (not just file metadata)
   - `agent_learner.py`: What agents discovered
   - `preference_manager.py`: Your coding preferences

2. **Storage**: Rich memories stored in PRISM
   ```json
   {
     "type": "bug_fix",
     "content": "Fixed race condition in async test",
     "semantic": ["added_error_handling", "async_fix"],
     "entities": ["test_async", "race_condition"],
     "relationships": [["test.py", "TESTS", "async.py"]],
     "confidence": 0.9
   }
   ```

3. **Retrieval**: Context injected automatically
   - On user prompts: Relevant patterns shown
   - On agent launch: Past discoveries injected
   - Weighted by tier: ANCHORS > LONGTERM > WORKING

4. **Promotion**: Patterns promoted by usage
   - 3+ uses → Higher tier
   - Bug fixes → Immediate promotion
   - User corrections → Preference storage

## 🔒 Quality Gates

### Code Validation & Memory Enforcement
- **Blocks ANCHORS violations** - Critical preferences stop execution
- **Deduplicates preferences** - Prevents storing same rule multiple times
- **Auto-promotes after corrections** - 2+ fixes → ANCHORS tier
- Prevents fallback patterns (NO .get() with defaults)
- Blocks linter suppressions
- Enforces error message quality
- Checks cyclomatic complexity
- Validates architecture boundaries

### Auto-Formatting
Language-specific formatters (post-edit):
- Python: ruff → black fallback
- JavaScript: prettier → eslint
- Go: goimports → gofmt

## 🚀 MCP Servers

Available MCP servers (when configured):
- **PRISM MCP**: Semantic reasoning and memory
- **Orchestration MCP**: Redis-based task coordination (YOU orchestrate directly)
- **Filesystem**: File operations
- **Playwright**: Browser automation
- **Postgres**: Database operations (project-specific)

Check status: `/mcp`

## 💡 Tips

1. **Let hooks work**: They automatically learn and improve
2. **Corrections matter**: 2+ corrections auto-promote to critical rules
3. **ANCHORS violations block**: Critical preferences cannot be ignored
4. **Real-time injection**: Memories appear after Read/Error operations
5. **No fallbacks**: Never use .get() with defaults - handle missing data explicitly
6. **Check session summaries**: Review promoted patterns at session end
7. **Trust the validators**: They prevent common issues

## 🚧 Troubleshooting

**PRISM not connecting**:
```bash
# Check HTTP server
curl http://localhost:8090/health

# Restart services
cd ~/repos/claude_mcp/prism_mcp
nerdctl compose restart
```

**Hooks not triggering**:
```bash
# Verify configuration
cat ~/.claude/settings.json | jq '.hooks'

# Check hook permissions
ls -la ~/.claude/hooks/*.py
```

**Pattern promotion issues**:
```bash
# Manual session end trigger
echo '{"hook_event_name":"SessionEnd"}' | python ~/.claude/hooks/universal_learner_session_end.py
```

## 📝 Global Instructions

The `CLAUDE.md` file contains:
- Core coding principles
- Complete implementation requirements
- Communication style (vibe modes)
- Quality standards
- Decision framework

## 🔗 Related Projects

- **PRISM MCP**: `~/repos/claude_mcp/prism_mcp/`
- **Orchestration MCP**: `~/repos/claude_mcp/orchestration_mcp/`

---

*Configuration for developers who want Claude Code to learn and improve across sessions*