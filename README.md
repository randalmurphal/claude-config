# Claude Code Configuration & Hooks

Advanced configuration for Claude Code with PRISM integration, intelligent hooks, and cross-session learning.

## 🎯 Overview

This configuration enhances Claude Code with:
- **PRISM MCP Integration**: Semantic reasoning, memory persistence, and hallucination detection
- **Universal Learning**: Cross-session pattern recognition and promotion
- **Smart Hooks**: Event-driven automation for code quality and safety
- **Orchestration Support**: Tools for complex multi-agent workflows
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
│   ├── unified_context_provider.py       # Context retrieval
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
- `universal_learner_session_end.py` - Promotes learned patterns

**UserPromptSubmit**:
- `unified_context_provider.py` - Provides relevant context
- `auto_orchestration_detector.py` - Detects complex tasks
- `orchestration_dashboard.py` - Updates status

### Tool Hooks

**PreToolUse**:
- Bash: `unified_bash_guardian.py` - Command safety analysis
- Write/Edit: `unified_code_validator.py` - Pattern validation
- Write/Edit: `file_protection.py` - Protects critical files
- Task: `assumption_detector.py` - Catches assumptions

**PostToolUse**:
- Write/Edit: `auto_formatter.py` - Formats code
- Write/Edit: `edit_tracker.py` - Tracks file relationships
- Task: `orchestration_learner.py` - Learns from agents
- Task: `orchestration_progress.py` - Updates progress
- Read/Bash: `unified_context_provider.py` - Updates context
- Bash: `test_coverage_enforcer.py` - Enforces coverage

## 🧠 PRISM Integration

PRISM (Persistent Reasoning & Intelligent Semantic Memory) provides:
- **Semantic Analysis**: Mathematical reasoning with confidence zones
- **Memory Tiers**: ANCHORS, LONGTERM, EPISODIC, WORKING
- **Hallucination Detection**: Risk assessment and mitigation
- **Pattern Learning**: Cross-session knowledge accumulation

### Memory Tier Promotion
Patterns are automatically promoted based on usage:
- WORKING → EPISODIC: 1 use
- EPISODIC → LONGTERM: 3 uses
- LONGTERM → ANCHORS: 5 uses
- Security/critical patterns: Fast-track with 2 uses

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

## 📊 Universal Learning

The universal learner:
- Extracts semantic content from technical patterns
- Stores in PRISM with proper metadata
- Creates Neo4j relationships (file coupling, error fixes)
- Promotes patterns based on usage and confidence
- Cleans up stale patterns after 7 days

Configuration in `universal_learner_config.json`:
- Memory tier thresholds
- Promotion rules
- Cleanup settings
- Graph relationships

## 🔒 Quality Gates

### Code Validation
- Prevents fallback patterns
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
- **Orchestration MCP**: Multi-agent coordination
- **Filesystem**: File operations
- **Playwright**: Browser automation
- **Postgres**: Database operations (project-specific)

Check status: `/mcp`

## 💡 Tips

1. **Let hooks work**: They automatically learn and improve
2. **Check session summaries**: Review promoted patterns at session end
3. **Use appropriate vibes**: Solo for coding, concert for production
4. **Trust the validators**: They prevent common issues
5. **Review learned patterns**: Check PRISM memory periodically

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