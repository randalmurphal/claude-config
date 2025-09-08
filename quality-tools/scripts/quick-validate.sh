#!/bin/bash
# Quick validation script for projects without Makefiles

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Running Quick Validation${NC}"
echo "=============================="

# Detect and validate based on project type
validated=false

# Go project
if [ -f "go.mod" ]; then
    echo -e "${BLUE}Go project detected${NC}"
    
    # Lint
    if command -v golangci-lint &> /dev/null; then
        echo "Running golangci-lint..."
        golangci-lint run --timeout=5m ./...
    else
        echo "Running go vet..."
        go vet ./...
    fi
    
    # Test with coverage
    echo "Running tests with coverage..."
    go test -race -cover ./...
    
    validated=true
fi

# Python project
if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ] || [ -f "setup.py" ]; then
    echo -e "${BLUE}Python project detected${NC}"
    
    # Format check
    if command -v ruff &> /dev/null; then
        echo "Running Ruff..."
        ruff check .
        ruff format --check .
    elif command -v flake8 &> /dev/null; then
        echo "Running flake8..."
        flake8 .
    fi
    
    # Type check
    if command -v pyright &> /dev/null; then
        echo "Running Pyright..."
        pyright
    elif command -v mypy &> /dev/null; then
        echo "Running mypy..."
        mypy --strict .
    fi
    
    # Tests
    if command -v pytest &> /dev/null; then
        echo "Running pytest with coverage..."
        pytest --cov --cov-fail-under=80
    elif [ -f "manage.py" ]; then
        echo "Running Django tests..."
        python manage.py test
    else
        echo "Running unittest discover..."
        python -m unittest discover
    fi
    
    validated=true
fi

# TypeScript/JavaScript project
if [ -f "package.json" ]; then
    echo -e "${BLUE}TypeScript/JavaScript project detected${NC}"
    
    # Check if npm scripts exist
    if grep -q '"lint"' package.json; then
        echo "Running npm lint..."
        npm run lint
    elif command -v eslint &> /dev/null; then
        echo "Running ESLint..."
        eslint . --ext .ts,.tsx,.js,.jsx
    fi
    
    if grep -q '"typecheck"' package.json; then
        echo "Running type check..."
        npm run typecheck
    elif [ -f "tsconfig.json" ] && command -v tsc &> /dev/null; then
        echo "Running TypeScript compiler..."
        tsc --noEmit
    fi
    
    if grep -q '"test"' package.json; then
        echo "Running tests..."
        npm test
    fi
    
    validated=true
fi

# Rust project
if [ -f "Cargo.toml" ]; then
    echo -e "${BLUE}Rust project detected${NC}"
    
    echo "Running cargo check..."
    cargo check
    
    echo "Running cargo clippy..."
    cargo clippy -- -D warnings
    
    echo "Running cargo test..."
    cargo test
    
    validated=true
fi

# Ruby project
if [ -f "Gemfile" ]; then
    echo -e "${BLUE}Ruby project detected${NC}"
    
    if command -v rubocop &> /dev/null; then
        echo "Running RuboCop..."
        rubocop
    fi
    
    if [ -f "Rakefile" ] && grep -q "spec" Rakefile; then
        echo "Running rake spec..."
        bundle exec rake spec
    elif command -v rspec &> /dev/null; then
        echo "Running RSpec..."
        rspec
    fi
    
    validated=true
fi

# C/C++ project
if [ -f "Makefile" ] || [ -f "CMakeLists.txt" ]; then
    if ls *.c *.cpp *.h *.hpp 2>/dev/null | grep -q .; then
        echo -e "${BLUE}C/C++ project detected${NC}"
        
        if command -v cppcheck &> /dev/null; then
            echo "Running cppcheck..."
            cppcheck --enable=all --error-exitcode=1 .
        fi
        
        if [ -f "Makefile" ]; then
            echo "Running make test (if available)..."
            make test 2>/dev/null || true
        fi
        
        validated=true
    fi
fi

# Summary
echo ""
if [ "$validated" = true ]; then
    echo -e "${GREEN}✅ Validation complete!${NC}"
else
    echo -e "${YELLOW}⚠️  No recognized project type found${NC}"
    echo "Supported types: Go, Python, TypeScript/JavaScript, Rust, Ruby, C/C++"
    echo ""
    echo "To add quality tools to this project, run:"
    echo "  ~/dotfiles/quality-tools/scripts/init-quality-tools.sh"
    exit 1
fi
