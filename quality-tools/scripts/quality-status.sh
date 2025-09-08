#!/bin/bash
# Show current project's quality status
# Part of the integrated .claude quality tools

echo "📊 Project Quality Status"
echo "========================"

# Detect project type
if [ -f "go.mod" ]; then
    echo "🔷 Go Project Detected"
    echo ""
    echo "Running quality checks..."
    ~/.claude/quality-tools/go/validate.sh
elif [ -f "package.json" ]; then
    echo "🔷 TypeScript/JavaScript Project Detected"
    echo ""
    echo "Running quality checks..."
    ~/.claude/quality-tools/typescript/validate.sh
elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    echo "🔷 Python Project Detected"
    echo ""
    echo "Running quality checks..."
    ~/.claude/quality-tools/python/validate.sh
else
    echo "⚠️ Unknown project type"
    echo ""
    echo "No go.mod, package.json, or Python config found"
    echo "Running universal checks..."
    ~/.claude/quality-tools/scripts/quick-validate.sh
fi

echo ""
echo "Available quality commands:"
echo "  qc       - Quick quality check"
echo "  qinit    - Initialize quality tools for project"
echo "  qstatus  - Show this status (you are here)"
echo ""
echo "Quality tools location: ~/.claude/quality-tools/"