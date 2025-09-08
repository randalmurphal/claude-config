# 🚀 Universal Quality Tools for Go, Python, and TypeScript

A comprehensive collection of quality tooling configurations and scripts for Go, Python, and TypeScript/React projects. Optimized for production-ready code with special emphasis on financial/trading applications.

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Features](#features)
- [Language Support](#language-support)
  - [Go](#go)
  - [Python](#python)
  - [TypeScript/React](#typescriptreact)
- [Installation](#installation)
- [Usage](#usage)
- [Financial/Trading Features](#financialtrading-features)
- [Customization](#customization)

## 🎯 Quick Start

```bash
# Navigate to your project directory
cd ~/your-project

# Run the initialization script
~/dotfiles/quality-tools/scripts/init-quality-tools.sh

# Run all quality checks
make validate
```

## ✨ Features

### Universal Features (All Languages)
- 🔍 **Comprehensive Linting** - Catch bugs before they happen
- 🧪 **Testing with Coverage** - Minimum 80% coverage enforcement
- 📊 **Type Safety** - Strict type checking for all languages
- 🔒 **Security Scanning** - Detect vulnerabilities early
- 🎨 **Auto-formatting** - Consistent code style
- 📦 **Makefiles** - Simple commands for all operations
- 🏃 **CI/CD Ready** - GitHub Actions templates included

### Language-Specific Highlights

#### Go
- **golangci-lint** with 50+ linters enabled
- **staticcheck** for advanced analysis
- **Race condition detection** (critical for concurrent trading systems)
- **Benchmark templates** for performance testing
- **Decimal precision** checks for financial calculations

#### Python
- **Ruff** for fast linting and formatting (replaces Black, isort, flake8, etc.)
- **Pyright** for modern type checking (alternative to mypy)
- **Hypothesis** for property-based testing
- **pytest** with coverage reporting
- **Security scanning** with bandit and safety

#### TypeScript/React
- **ESLint** with strict TypeScript rules
- **Prettier** for consistent formatting
- **Jest** with React Testing Library
- **Bundle size analysis** tools
- **Accessibility** (a11y) checking
- **React Native** support included

## 📁 Directory Structure

```
~/dotfiles/quality-tools/
├── go/                          # Go-specific configurations
│   ├── .golangci.yml           # Comprehensive linter config
│   ├── go-coverage.sh          # Coverage enforcement script
│   ├── go-race.sh              # Race detection script
│   └── benchmark_template.go   # Benchmark examples
├── python/                      # Python-specific configurations
│   ├── pyproject.toml         # Ruff, Pyright, pytest config
│   ├── pyrightconfig.json     # Pyright type checking
│   └── pytest.ini             # pytest configuration
├── typescript/                  # TypeScript/React configurations
│   ├── .eslintrc.js           # ESLint with strict rules
│   ├── .prettierrc            # Prettier formatting
│   ├── tsconfig.json          # Strict TypeScript config
│   ├── jest.config.js         # Jest testing config
│   └── package.template.json  # Package.json template
├── universal/                   # Cross-language tools
│   ├── makefiles/             # Makefile templates
│   │   ├── Makefile.go
│   │   ├── Makefile.python
│   │   └── Makefile.typescript
│   └── pre-commit/            # Git hooks (coming soon)
├── scripts/                     # Initialization scripts
│   └── init-quality-tools.sh  # Master initialization script
└── README.md                   # This file
```

## 🛠️ Installation

### Prerequisites

#### Go Projects
```bash
# Install Go (if not already installed)
# Then install tools:
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go install honnef.co/go/tools/cmd/staticcheck@latest
```

#### Python Projects
```bash
# Ensure Python 3.10+ is installed
pip install ruff pyright mypy pytest pytest-cov hypothesis
```

#### TypeScript Projects
```bash
# Ensure Node.js 18+ is installed
npm install -g typescript eslint prettier
```

## 📖 Usage

### Initialize a New Project

```bash
# The script auto-detects project type
~/dotfiles/quality-tools/scripts/init-quality-tools.sh

# Or specify type manually
~/dotfiles/quality-tools/scripts/init-quality-tools.sh --type=go
```

### Common Make Commands

All project types support these commands:

```bash
make help        # Show all available commands
make validate    # Run all quality checks
make test        # Run tests
make coverage    # Run tests with coverage
make lint        # Run linters
make format      # Format code
make security    # Run security scans
make clean       # Clean build artifacts
```

### Go-Specific Commands

```bash
make race        # Run race detector
make benchmark   # Run benchmarks
make mod         # Tidy go modules
```

### Python-Specific Commands

```bash
make typecheck   # Run Pyright type checking
make venv        # Create virtual environment
make complexity  # Check code complexity
```

### TypeScript-Specific Commands

```bash
make typecheck       # Run TypeScript compiler
make analyze-bundle  # Analyze bundle size
make lighthouse      # Run Lighthouse audit
make storybook      # Start Storybook
```

## 💰 Financial/Trading Features

Special configurations for financial applications:

### Decimal Precision
- Enforced use of decimal types instead of floats
- Linter rules to catch precision loss
- Test templates for edge cases

### Concurrency Safety
- Race condition detection for Go
- Strict async/await rules for TypeScript
- Thread safety checks

### Time Zone Handling
- UTC enforcement where appropriate
- Timezone-aware datetime checks
- Market hours validation helpers

### Security
- Input validation for monetary values
- SQL injection prevention
- API key handling best practices

## 🎨 Customization

### Adjusting Linter Rules

#### Go
Edit `.golangci.yml` to enable/disable specific linters:
```yaml
linters:
  enable:
    - your-linter
  disable:
    - unwanted-linter
```

#### Python
Edit `pyproject.toml`:
```toml
[tool.ruff]
select = ["E", "F", "YOUR_RULES"]
ignore = ["RULES_TO_IGNORE"]
```

#### TypeScript
Edit `.eslintrc.js`:
```javascript
rules: {
  'your-rule': 'error',
  'rule-to-disable': 'off'
}
```

### Coverage Thresholds

Change minimum coverage in Makefiles:
```makefile
MIN_COVERAGE := 90  # Increase to 90%
```

## 🔧 Troubleshooting

### Common Issues

**Issue**: "command not found" errors
**Solution**: Install the required tools for your language (see Installation section)

**Issue**: Linter is too strict
**Solution**: Adjust rules in the respective config file or add ignore comments

**Issue**: Tests fail due to coverage
**Solution**: Write more tests or adjust MIN_COVERAGE in Makefile

## 🚀 Best Practices

1. **Run `make validate` before every commit**
2. **Set up pre-commit hooks** (coming soon)
3. **Keep coverage above 80%** for production code
4. **Use property-based testing** for financial calculations
5. **Always run race detection** for concurrent Go code
6. **Type everything** - no `any` in TypeScript, full type hints in Python

## 📝 License

These configurations are provided as-is for personal and commercial use.

## 🤝 Contributing

Feel free to customize these configurations for your specific needs. If you have improvements that would benefit others, consider sharing them!

---

Made with ❤️ for writing production-ready code
