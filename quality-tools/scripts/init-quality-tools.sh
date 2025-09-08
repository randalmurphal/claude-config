#!/bin/bash
# Master initialization script for quality tools
# Automatically detects project type and applies appropriate configurations

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
QUALITY_TOOLS_DIR="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Detect project type
detect_project_type() {
    local project_type=""
    
    # Check for Go project
    if [ -f "go.mod" ] || [ -f "go.sum" ] || ls *.go 2>/dev/null | grep -q .; then
        project_type="go"
    fi
    
    # Check for Python project
    if [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ] || ls *.py 2>/dev/null | grep -q .; then
        if [ -n "$project_type" ]; then
            project_type="${project_type},python"
        else
            project_type="python"
        fi
    fi
    
    # Check for TypeScript/JavaScript project
    if [ -f "package.json" ] || [ -f "tsconfig.json" ]; then
        if [ -n "$project_type" ]; then
            project_type="${project_type},typescript"
        else
            project_type="typescript"
        fi
    fi
    
    echo "$project_type"
}

# Initialize Go project
init_go_project() {
    print_info "Initializing Go project quality tools..."
    
    # Copy golangci-lint config
    if [ ! -f ".golangci.yml" ]; then
        cp "$QUALITY_TOOLS_DIR/go/.golangci.yml" .
        print_success "Copied .golangci.yml"
    else
        print_warning ".golangci.yml already exists, skipping"
    fi
    
    # Copy Makefile
    if [ ! -f "Makefile" ]; then
        cp "$QUALITY_TOOLS_DIR/universal/makefiles/Makefile.go" Makefile
        print_success "Copied Makefile for Go"
    else
        print_warning "Makefile already exists, copying as Makefile.go.example"
        cp "$QUALITY_TOOLS_DIR/universal/makefiles/Makefile.go" Makefile.go.example
    fi
    
    # Copy benchmark template
    if [ ! -d "benchmark" ]; then
        mkdir -p benchmark
        cp "$QUALITY_TOOLS_DIR/go/benchmark_template.go" benchmark/
        print_success "Copied benchmark template"
    fi
    
    # Install tools
    print_info "Installing Go development tools..."
    make -f Makefile install-tools || true
    
    print_success "Go project initialized!"
}

# Initialize Python project
init_python_project() {
    print_info "Initializing Python project quality tools..."
    
    # Copy pyproject.toml
    if [ ! -f "pyproject.toml" ]; then
        cp "$QUALITY_TOOLS_DIR/python/pyproject.toml" .
        print_success "Copied pyproject.toml"
    else
        print_warning "pyproject.toml already exists, merging configurations..."
        # TODO: Implement config merging
    fi
    
    # Copy pyrightconfig.json
    if [ ! -f "pyrightconfig.json" ]; then
        cp "$QUALITY_TOOLS_DIR/python/pyrightconfig.json" .
        print_success "Copied pyrightconfig.json"
    fi
    
    # Copy pytest.ini if not using pyproject.toml for pytest config
    if [ ! -f "pytest.ini" ] && ! grep -q "\[tool.pytest\]" pyproject.toml 2>/dev/null; then
        cp "$QUALITY_TOOLS_DIR/python/pytest.ini" .
        print_success "Copied pytest.ini"
    fi
    
    # Copy Makefile
    if [ ! -f "Makefile" ]; then
        cp "$QUALITY_TOOLS_DIR/universal/makefiles/Makefile.python" Makefile
        print_success "Copied Makefile for Python"
    else
        print_warning "Makefile already exists, copying as Makefile.python.example"
        cp "$QUALITY_TOOLS_DIR/universal/makefiles/Makefile.python" Makefile.python.example
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv .venv
        print_success "Virtual environment created at .venv"
        print_info "Activate it with: source .venv/bin/activate"
    fi
    
    print_success "Python project initialized!"
}

# Initialize TypeScript project
init_typescript_project() {
    print_info "Initializing TypeScript/React project quality tools..."
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        print_warning "No package.json found. Initializing npm project..."
        npm init -y
    fi
    
    # Copy ESLint config
    if [ ! -f ".eslintrc.js" ] && [ ! -f ".eslintrc.json" ]; then
        cp "$QUALITY_TOOLS_DIR/typescript/.eslintrc.js" .
        print_success "Copied .eslintrc.js"
    else
        print_warning "ESLint config already exists, skipping"
    fi
    
    # Copy Prettier config
    if [ ! -f ".prettierrc" ] && [ ! -f ".prettierrc.json" ]; then
        cp "$QUALITY_TOOLS_DIR/typescript/.prettierrc" .
        print_success "Copied .prettierrc"
    fi
    
    # Copy TypeScript config
    if [ ! -f "tsconfig.json" ]; then
        cp "$QUALITY_TOOLS_DIR/typescript/tsconfig.json" .
        print_success "Copied tsconfig.json"
    else
        print_warning "tsconfig.json already exists, copying as tsconfig.strict.json"
        cp "$QUALITY_TOOLS_DIR/typescript/tsconfig.json" tsconfig.strict.json
    fi
    
    # Copy Jest config
    if [ ! -f "jest.config.js" ]; then
        cp "$QUALITY_TOOLS_DIR/typescript/jest.config.js" .
        print_success "Copied jest.config.js"
    fi
    
    # Copy Makefile
    if [ ! -f "Makefile" ]; then
        cp "$QUALITY_TOOLS_DIR/universal/makefiles/Makefile.typescript" Makefile
        print_success "Copied Makefile for TypeScript"
    else
        print_warning "Makefile already exists, copying as Makefile.typescript.example"
        cp "$QUALITY_TOOLS_DIR/universal/makefiles/Makefile.typescript" Makefile.typescript.example
    fi
    
    # Update package.json scripts
    print_info "Updating package.json scripts..."
    node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    
    pkg.scripts = pkg.scripts || {};
    pkg.scripts.lint = pkg.scripts.lint || 'eslint . --ext .ts,.tsx,.js,.jsx --max-warnings 0';
    pkg.scripts['lint:fix'] = pkg.scripts['lint:fix'] || 'eslint . --ext .ts,.tsx,.js,.jsx --fix';
    pkg.scripts.format = pkg.scripts.format || 'prettier --write \"src/**/*.{ts,tsx,js,jsx,json,css,md}\"';
    pkg.scripts['format:check'] = pkg.scripts['format:check'] || 'prettier --check \"src/**/*.{ts,tsx,js,jsx,json,css,md}\"';
    pkg.scripts.typecheck = pkg.scripts.typecheck || 'tsc --noEmit';
    pkg.scripts['test:coverage'] = pkg.scripts['test:coverage'] || 'jest --coverage';
    pkg.scripts['test:watch'] = pkg.scripts['test:watch'] || 'jest --watch';
    pkg.scripts['test:ci'] = pkg.scripts['test:ci'] || 'jest --ci --coverage --maxWorkers=2';
    pkg.scripts.validate = pkg.scripts.validate || 'npm run typecheck && npm run lint && npm run test:coverage';
    
    fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
    console.log('✅ Updated package.json scripts');
    "
    
    print_success "TypeScript project initialized!"
}

# Main execution
main() {
    echo -e "${BLUE}🚀 Quality Tools Initializer${NC}"
    echo "================================"
    
    # Detect project type
    project_types=$(detect_project_type)
    
    if [ -z "$project_types" ]; then
        print_warning "Could not detect project type automatically."
        echo "Please select project type:"
        echo "1) Go"
        echo "2) Python"
        echo "3) TypeScript/React"
        echo "4) All"
        read -p "Enter choice (1-4): " choice
        
        case $choice in
            1) project_types="go" ;;
            2) project_types="python" ;;
            3) project_types="typescript" ;;
            4) project_types="go,python,typescript" ;;
            *) print_error "Invalid choice"; exit 1 ;;
        esac
    else
        print_success "Detected project type(s): $project_types"
    fi
    
    # Initialize based on detected types
    IFS=',' read -ra TYPES <<< "$project_types"
    for type in "${TYPES[@]}"; do
        case $type in
            go) init_go_project ;;
            python) init_python_project ;;
            typescript) init_typescript_project ;;
        esac
    done
    
    echo ""
    print_success "🎉 Quality tools initialization complete!"
    echo ""
    echo "Next steps:"
    echo "1. Review and customize the configuration files"
    echo "2. Run 'make help' to see available commands"
    echo "3. Run 'make validate' to run all quality checks"
}

# Run main function
main "$@"
