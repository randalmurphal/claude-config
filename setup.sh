#!/bin/bash
# Claude Environment Setup Script
# This script sets up a complete Claude environment on a new machine

set -e  # Exit on error

echo "🚀 Claude Environment Setup"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for required tools
check_requirement() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        return 1
    fi
}

echo ""
echo "📋 Checking requirements..."
echo ""

MISSING_DEPS=0

# Check Node.js
if ! check_requirement node; then
    echo "  Please install Node.js: https://nodejs.org/"
    MISSING_DEPS=1
fi

# Check npm
if ! check_requirement npm; then
    echo "  Please install npm (comes with Node.js)"
    MISSING_DEPS=1
fi

# Check git
if ! check_requirement git; then
    echo "  Please install git: https://git-scm.com/"
    MISSING_DEPS=1
fi

# Check Claude CLI
if ! check_requirement claude; then
    echo -e "${YELLOW}⚠${NC} Claude CLI not installed. Installing..."
    npm install -g @anthropic/claude-cli
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Claude CLI installed successfully"
    else
        echo -e "${RED}✗${NC} Failed to install Claude CLI"
        MISSING_DEPS=1
    fi
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${RED}Please install missing dependencies and run this script again.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All requirements satisfied!${NC}"
echo ""

# Create environment file if it doesn't exist
ENV_FILE="$HOME/.claude-env"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Creating environment template at $ENV_FILE"
    cat > "$ENV_FILE" << 'EOF'
# Claude MCP Server Environment Variables
# Source this file in your shell: source ~/.claude-env

# === Version Control ===
# GitHub - Get token at: https://github.com/settings/tokens
# Scopes needed: repo, read:org
export GITHUB_TOKEN=""

# GitLab - Get token at: https://gitlab.com/-/profile/personal_access_tokens  
# Scopes needed: api, read_repository
export GITLAB_PERSONAL_ACCESS_TOKEN=""

# === API Services (All have FREE tiers) ===
# AlphaVantage - Get FREE key at: https://www.alphavantage.co/support/#api-key
# Just need email, instant activation - 25 requests/day free
export ALPHAVANTAGE_API_KEY=""

# Apidog - Get FREE at: https://apidog.com
# Sign up for free account, find token in settings
export APIDOG_API_TOKEN=""

# Tinybird - Get FREE at: https://www.tinybird.co
# Sign up for free tier (10GB storage, 1000 requests/day)
export TINYBIRD_TOKEN=""

# === Database ===
# PostgreSQL - Your local password (only if using PostgreSQL)
export POSTGRES_PASSWORD=""

# === Quality Tools Aliases ===
# Quick quality check
alias qc='~/.claude/quality-tools/scripts/quick-validate.sh'

# Initialize quality tools for current project
alias qinit='~/.claude/quality-tools/scripts/init-quality-tools.sh'

# Check quality status
alias qstatus='~/.claude/quality-tools/scripts/quality-status.sh'

# Quality-enforced commit
quality-commit() {
    echo "🔍 Running quality checks before commit..."
    if ~/.claude/quality-tools/scripts/quick-validate.sh; then
        echo "✅ Quality checks passed!"
        git add -A && git commit "$@"
    else
        echo "❌ Quality checks failed! Fix issues before committing."
        return 1
    fi
}
EOF
    echo -e "${GREEN}✓${NC} Environment template created"
    echo ""
    echo -e "${YELLOW}⚠${NC} Please edit $ENV_FILE and add your API keys"
else
    echo -e "${GREEN}✓${NC} Environment file already exists at $ENV_FILE"
fi

# Check if .claude directory exists
if [ -d "$HOME/.claude" ]; then
    echo ""
    echo -e "${YELLOW}⚠${NC} .claude directory already exists"
    read -p "Do you want to backup existing .claude? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP_NAME=".claude-backup-$(date +%Y%m%d-%H%M%S)"
        mv "$HOME/.claude" "$HOME/$BACKUP_NAME"
        echo -e "${GREEN}✓${NC} Backed up to ~/$BACKUP_NAME"
    fi
fi

# Setup shell integration
SHELL_RC=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    # Check if already sourced
    if ! grep -q "source ~/.claude-env" "$SHELL_RC" 2>/dev/null; then
        echo ""
        read -p "Add Claude environment to $SHELL_RC? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "" >> "$SHELL_RC"
            echo "# Claude Environment" >> "$SHELL_RC"
            echo "[ -f ~/.claude-env ] && source ~/.claude-env" >> "$SHELL_RC"
            echo -e "${GREEN}✓${NC} Added to $SHELL_RC"
        fi
    else
        echo -e "${GREEN}✓${NC} Claude environment already in $SHELL_RC"
    fi
fi

# Configure MCP servers (if Claude CLI is available)
if command -v claude &> /dev/null; then
    echo ""
    echo "🔧 Configuring MCP Servers..."
    echo ""
    
    # Add user-level MCP servers
    echo "Adding user-level MCP servers..."
    
    # GitHub
    claude mcp add github --scope user \
        --env GITHUB_TOKEN=\${GITHUB_TOKEN} \
        -- npx -y @modelcontextprotocol/server-github 2>/dev/null || true
    
    # GitLab
    claude mcp add gitlab --scope user \
        --env GITLAB_PERSONAL_ACCESS_TOKEN=\${GITLAB_PERSONAL_ACCESS_TOKEN} \
        --env GITLAB_API_URL="https://gitlab.com/api/v4" \
        -- npx -y @modelcontextprotocol/server-gitlab 2>/dev/null || true
    
    # Filesystem
    claude mcp add filesystem --scope user \
        -- npx -y @modelcontextprotocol/server-filesystem \
        --allowed-directories \$HOME/repos 2>/dev/null || true
    
    # Playwright
    claude mcp add playwright --scope user \
        -- npx -y @microsoft/playwright-mcp 2>/dev/null || true
    
    # Apidog
    claude mcp add apidog --scope user \
        --env APIDOG_API_TOKEN=\${APIDOG_API_TOKEN} \
        -- npx -y @apidog/mcp-server 2>/dev/null || true
    
    # Tinybird
    claude mcp add tinybird --scope user \
        --env TINYBIRD_TOKEN=\${TINYBIRD_TOKEN} \
        --env TINYBIRD_URL="https://mcp.tinybird.co" \
        -- npx -y @modelcontextprotocol/server-tinybird 2>/dev/null || true
    
    echo -e "${GREEN}✓${NC} MCP servers configured"
fi

# Make quality scripts executable
if [ -d "$HOME/.claude/quality-tools/scripts" ]; then
    chmod +x $HOME/.claude/quality-tools/scripts/*.sh
    chmod +x $HOME/.claude/quality-tools/*/validate.sh 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Quality scripts made executable"
fi

echo ""
echo "✨ Setup Summary"
echo "================"
echo ""
echo -e "${GREEN}✓${NC} Claude environment prepared"
echo -e "${GREEN}✓${NC} Quality tools integrated in ~/.claude"
echo -e "${GREEN}✓${NC} MCP servers configured"
echo ""
echo "📋 Next Steps:"
echo "1. Edit ~/.claude-env and add your API keys"
echo "2. Run: source ~/.claude-env"
echo "3. Test with: claude mcp list"
echo "4. Try: qc (quality check) in any project"
echo ""
echo "🔑 Get your FREE API keys at:"
echo "   GitHub: https://github.com/settings/tokens"
echo "   GitLab: https://gitlab.com/-/profile/personal_access_tokens"
echo "   AlphaVantage: https://www.alphavantage.co/support/#api-key"
echo "   Apidog: https://apidog.com"
echo "   Tinybird: https://www.tinybird.co"
echo ""
echo "📦 To migrate to another machine:"
echo "   tar -czf claude-backup.tar.gz ~/.claude ~/.claude-env"
echo "   # Copy to new machine, extract, and run this setup.sh"
echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"