#!/usr/bin/env bash
# Pre-commit validation hook for Claude Code orchestrations
# Runs formatters and linters on staged files before commit

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔍 Running pre-commit validation...${NC}"

# Get list of staged files
staged_files=$(git diff --cached --name-only --diff-filter=ACM)

if [[ -z "$staged_files" ]]; then
    echo -e "${YELLOW}No staged files to validate${NC}"
    exit 0
fi

# Track overall success
overall_status=0

# Group files by language
python_files=()
js_files=()
go_files=()

while IFS= read -r file; do
    if [[ ! -f "$file" ]]; then
        continue  # Skip deleted files
    fi

    ext="${file##*.}"
    case "$ext" in
        py)
            python_files+=("$file")
            ;;
        js|jsx|ts|tsx)
            js_files+=("$file")
            ;;
        go)
            go_files+=("$file")
            ;;
    esac
done <<< "$staged_files"

# Python validation
if [[ ${#python_files[@]} -gt 0 ]]; then
    echo -e "\n${GREEN}📝 Python files (${#python_files[@]} files)${NC}"

    # Step 1: Auto-format with ruff
    echo "  • Formatting with ruff..."
    if ruff format --config ~/.claude/configs/python/ruff.toml "${python_files[@]}" 2>&1; then
        echo -e "    ${GREEN}✓${NC} Formatting complete"
        # Re-stage formatted files
        git add "${python_files[@]}"
    else
        echo -e "    ${RED}✗${NC} Formatting failed"
        overall_status=1
    fi

    # Step 2: Lint with ruff check
    echo "  • Linting with ruff check..."
    if ruff check --config ~/.claude/configs/python/ruff.toml "${python_files[@]}" 2>&1; then
        echo -e "    ${GREEN}✓${NC} Linting passed"
    else
        echo -e "    ${RED}✗${NC} Linting failed - fix errors above"
        overall_status=1
    fi

    # Step 3: Type check with pyright
    echo "  • Type checking with pyright..."
    if pyright "${python_files[@]}" 2>&1 | grep -v "0 errors, 0 warnings" > /dev/null; then
        # Has errors/warnings
        pyright "${python_files[@]}" 2>&1
        echo -e "    ${RED}✗${NC} Type checking failed - fix errors above"
        overall_status=1
    else
        echo -e "    ${GREEN}✓${NC} Type checking passed"
    fi
fi

# JavaScript/TypeScript validation
if [[ ${#js_files[@]} -gt 0 ]]; then
    echo -e "\n${GREEN}📝 JavaScript/TypeScript files (${#js_files[@]} files)${NC}"

    # Step 1: Auto-format with prettier
    echo "  • Formatting with prettier..."
    if prettier --config ~/.claude/configs/javascript/prettier.json --write "${js_files[@]}" 2>&1; then
        echo -e "    ${GREEN}✓${NC} Formatting complete"
        # Re-stage formatted files
        git add "${js_files[@]}"
    else
        echo -e "    ${RED}✗${NC} Formatting failed"
        overall_status=1
    fi

    # Step 2: Lint with eslint
    echo "  • Linting with eslint..."
    if command -v eslint &> /dev/null; then
        if eslint --config ~/.claude/configs/javascript/.eslintrc.json "${js_files[@]}" 2>&1; then
            echo -e "    ${GREEN}✓${NC} Linting passed"
        else
            echo -e "    ${RED}✗${NC} Linting failed - fix errors above"
            overall_status=1
        fi
    else
        echo -e "    ${YELLOW}⚠${NC} eslint not found, skipping"
    fi

    # Step 3: Type check with tsc (if TypeScript)
    ts_files=()
    for file in "${js_files[@]}"; do
        if [[ "$file" == *.ts || "$file" == *.tsx ]]; then
            ts_files+=("$file")
        fi
    done

    if [[ ${#ts_files[@]} -gt 0 ]]; then
        echo "  • Type checking with tsc..."
        if command -v tsc &> /dev/null; then
            if tsc --noEmit "${ts_files[@]}" 2>&1; then
                echo -e "    ${GREEN}✓${NC} Type checking passed"
            else
                echo -e "    ${RED}✗${NC} Type checking failed - fix errors above"
                overall_status=1
            fi
        else
            echo -e "    ${YELLOW}⚠${NC} tsc not found, skipping"
        fi
    fi
fi

# Go validation
if [[ ${#go_files[@]} -gt 0 ]]; then
    echo -e "\n${GREEN}📝 Go files (${#go_files[@]} files)${NC}"

    # Step 1: Auto-format with gofmt
    echo "  • Formatting with gofmt..."
    if gofmt -w "${go_files[@]}" 2>&1; then
        echo -e "    ${GREEN}✓${NC} Formatting complete"
        # Re-stage formatted files
        git add "${go_files[@]}"
    else
        echo -e "    ${RED}✗${NC} Formatting failed"
        overall_status=1
    fi

    # Step 2: Lint with golangci-lint
    echo "  • Linting with golangci-lint..."
    if command -v golangci-lint &> /dev/null; then
        if golangci-lint run "${go_files[@]}" 2>&1; then
            echo -e "    ${GREEN}✓${NC} Linting passed"
        else
            echo -e "    ${RED}✗${NC} Linting failed - fix errors above"
            overall_status=1
        fi
    else
        echo -e "    ${YELLOW}⚠${NC} golangci-lint not found, skipping"
    fi
fi

# Final result
echo ""
if [[ $overall_status -eq 0 ]]; then
    echo -e "${GREEN}✅ All pre-commit checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Pre-commit validation failed. Fix errors above and try again.${NC}"
    exit 1
fi
