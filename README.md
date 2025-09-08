# Claude Orchestration Configuration

My personal Claude orchestration system with integrated quality tools, agents, and commands.

## 🚀 Quick Setup on New Machine

```bash
# Clone this repository
git clone https://github.com/randalmurphal/claude-config.git ~/.claude

# Run the setup script
~/.claude/setup.sh

# Configure your API keys
vim ~/.claude-env
# Add your tokens for GitHub, GitLab, AlphaVantage, etc.

# Source the environment
source ~/.claude-env

# Test the setup
claude mcp list
```

## 📁 Structure

```
.claude/
├── agents/                 # Specialized agents for tasks
│   ├── proof-of-life.md   # Creates minimal working functionality
│   ├── reality-checker.md # Validates actual functionality
│   ├── quality-checker.md # Runs quality validations
│   └── ...
├── commands/              # Orchestration commands
│   ├── large_task.md     # Full orchestration for complex tasks
│   └── medium_task.md    # Streamlined for 1-4 hour tasks
├── quality-tools/        # Integrated quality validation
│   ├── python/          # Python linting, formatting, testing
│   ├── go/              # Go validation tools
│   ├── typescript/      # TS/JS validation
│   └── scripts/         # Universal quality scripts
├── templates/           # Project templates
├── validators/          # Validation scripts
└── setup.sh            # One-command setup script
```

## 🛠️ Available Commands

After setup, you have access to:

- `/large_task` - Full orchestration for complex projects
- `/medium_task` - Streamlined workflow for smaller tasks
- `qc` - Quick quality check
- `qstatus` - Show project quality status
- `quality-commit` - Git commit with quality validation

## 🔧 MCP Servers

Configured at user level (available in all projects):
- GitHub - Code management
- GitLab - Alternative code management
- Filesystem - Safe file operations
- Playwright - Browser automation
- Apidog - API documentation
- Tinybird - Analytics

## 📋 Quality Standards

- **Test Coverage**: 95% lines, 100% functions
- **Linting**: Zero errors allowed
- **Formatting**: Enforced via ruff/prettier/gofmt
- **Type Safety**: Full type checking

## 🔄 Keeping in Sync

```bash
cd ~/.claude
git pull origin main
```

## 📝 Notes

- All API keys are stored in `~/.claude-env` (not in git)
- Project-specific MCP servers go in project's `.mcp.json`
- Quality tools run automatically during orchestration phases

---

*Private configuration for @randalmurphal*