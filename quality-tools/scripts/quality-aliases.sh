#!/bin/bash
# Quality tool aliases and functions
# Add this to your .zshrc or .bashrc: source ~/dotfiles/quality-tools/scripts/quality-aliases.sh

# Quick quality check for current project
alias qc='make validate 2>/dev/null || (echo "No Makefile found, running language-specific checks..." && ~/dotfiles/quality-tools/scripts/quick-validate.sh)'

# Initialize quality tools for current project
alias qinit='~/dotfiles/quality-tools/scripts/init-quality-tools.sh'

# Remind agent about quality rules
alias warp-quality='cat ~/.warp-agent-rules'

# Function to enforce quality checks before commits
quality-commit() {
    echo "🔍 Running quality checks before commit..."
    if make validate 2>/dev/null; then
        echo "✅ Quality checks passed!"
        git add -A && git commit "$@"
    else
        echo "❌ Quality checks failed! Fix issues before committing."
        return 1
    fi
}

# Function to show current project's quality status
quality-status() {
    echo "📊 Project Quality Status"
    echo "========================"
    
    # Detect project type
    if [ -f "go.mod" ]; then
        echo "🔷 Go Project Detected"
        echo "Coverage:"
        go test -cover ./... 2>/dev/null | grep coverage || echo "No tests found"
    elif [ -f "package.json" ]; then
        echo "🔷 TypeScript/JavaScript Project Detected"
        npm run test:coverage 2>/dev/null || echo "No coverage script found"
    elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
        echo "🔷 Python Project Detected"
        pytest --cov 2>/dev/null | grep TOTAL || echo "No tests found"
    fi
    
    echo ""
    echo "Available commands:"
    [ -f "Makefile" ] && make help 2>/dev/null | head -20
}

# Function to create a new project with quality tools
quality-new-project() {
    local project_name=$1
    local project_type=$2
    
    if [ -z "$project_name" ]; then
        echo "Usage: quality-new-project <project-name> [go|python|typescript]"
        return 1
    fi
    
    mkdir -p "$project_name"
    cd "$project_name"
    
    case "$project_type" in
        go)
            go mod init "github.com/yourusername/$project_name"
            ;;
        python)
            python3 -m venv .venv
            touch requirements.txt
            ;;
        typescript|ts)
            npm init -y
            ;;
    esac
    
    # Initialize quality tools
    ~/dotfiles/quality-tools/scripts/init-quality-tools.sh
    
    echo "✅ Project '$project_name' created with quality tools!"
    echo "📁 Location: $(pwd)"
}

# Add to shell prompt to show quality status (optional)
quality_prompt() {
    if [ -f "Makefile" ] && grep -q "validate:" Makefile 2>/dev/null; then
        echo "✓"
    elif [ -f ".golangci.yml" ] || [ -f "pyproject.toml" ] || [ -f ".eslintrc.js" ]; then
        echo "○"
    else
        echo "✗"
    fi
}

echo "🚀 Quality tool aliases loaded!"
echo "Commands available:"
echo "  qc              - Run quick quality check"
echo "  qinit           - Initialize quality tools"
echo "  quality-commit  - Commit with quality checks"
echo "  quality-status  - Show project quality status"
echo "  quality-new-project - Create new project with quality tools"
echo "  warp-quality    - Show agent quality rules"
