# Symphony - Advanced Orchestration System for Claude Code

A sophisticated orchestration system that implements skeleton-first development with merge-purge-continue patterns, architectural deviation tracking, and intelligent parallel execution.

## 🎯 Overview

Symphony transforms Claude Code into a powerful development conductor, managing complex multi-file projects through:
- **Merge-Purge-Continue Pattern**: No interruptions, progressive refinement
- **Deviation Tracking**: Handles architectural discoveries without stopping work
- **Smart Parallel Execution**: Workers in isolated "chambers" with git worktrees
- **Living Mission Context**: Requirements evolve as understanding improves

## 🚀 Key Features

### 1. **Skeleton-First Architecture with Deviation Handling**
- Builds complete structure before implementation
- Workers mark deviations when skeleton doesn't match reality
- Three implementation cycles: Implement → Merge/Purge → Refine
- Preserves good code even when architecture changes
- No work interruption - complete then resolve

### 2. **Intelligent Context Management**
- Context importance scoring: MUST READ / SHOULD KNOW / REFERENCE
- Living mission context that evolves with discoveries
- Business logic extraction before architecture
- Progressive context refinement between phases
- Each phase outputs what the next needs

### 3. **Smart Validation & Recovery**
- Phase-specific recovery agents for targeted fixes
- Intelligent failure classification (design_flaw, typo, etc.)
- Auto-detects project validation tools (Python/JS/Go)
- Test impact analysis for selective test execution
- Complexity metrics using language-specific tools (radon/gocyclo/eslint)

## 📁 System Structure

```
{project}/.symphony/           # Orchestration infrastructure (not .claude)
├── tools/
│   └── orchestration.py       # Main orchestration tool
├── chambers/                  # Worker chambers (git worktrees)
│   ├── auth-impl/
│   │   └── .chamber/         # Chamber-specific context
│   └── db-impl/
├── MISSION_CONTEXT.json      # Evolving understanding
├── DEVIATIONS.json           # Architectural mismatches
├── BUSINESS_LOGIC.json       # Extracted rules
└── ARCHITECTURAL_DECISIONS.json # Merge/purge decisions

~/.claude/                    # User configuration (separate)
├── tools/                     # Orchestration tools and utilities
│   ├── preflight_validator.py # Enforces virtual environments and installs quality tools
│   └── [other tools]          # Various utility scripts
│
├── agents/                    # Specialized sub-agents
│   ├── skeleton-builder.md    # Creates implementation structure (Sonnet)
│   ├── skeleton-builder-haiku.md # Fast skeleton creation (Haiku) ✨
│   ├── skeleton-beautifier.md # Makes skeletons beautiful (Default) ✨ NEW
│   ├── skeleton-reviewer.md   # Reviews with issue categorization (Default)
│   ├── test-skeleton-builder.md # Creates test structure (Sonnet)
│   ├── test-skeleton-builder-haiku.md # Fast test skeleton (Haiku) ✨
│   ├── implementation-executor.md # Implements code (Default)
│   ├── code-beautifier.md     # Beautifies implementation (Default) ✨ NEW
│   ├── test-implementer.md    # Implements tests (Default)
│   ├── validator-quick-haiku.md # Fast validation checks (Haiku) ✨
│   ├── test-runner-haiku.md   # Execute tests and report (Haiku) ✨
│   ├── consolidation-analyzer.md # Post-merge integration
│   ├── merge-coordinator.md   # Merges code AND context
│   ├── context-builder.md     # Phase transition manager
│   └── [other agents]         # Various specialized agents
│
├── commands/                  # Musical-themed commands
│   ├── prelude.md            # Build task specifications through conversation
│   ├── conduct.md            # Main orchestration command
│   ├── coda.md               # Generate handoff summaries
│   └── vibe.md               # Set personality mode (solo/concert/duo/mentor)
│
├── hooks/                   # Event-driven automation
│   ├── auto_formatter.py    # Universal code formatter for multiple languages
│   ├── assumption_detector.py # Catches assumptions in real-time
│   ├── code_quality_gate.py # Unified quality enforcement with complexity analysis
│   └── [other hooks]        # Various automation hooks

├── configs/                 # Language-specific formatter configs
│   ├── python/             # ruff, pylint, mypy configs
│   ├── javascript/         # prettier config
│   └── go/                 # golangci config
│
└── [auto-generated]        # Directories Claude creates (gitignored)
    ├── projects/           # Project-specific data
    ├── todos/              # Agent task tracking
    ├── shell-snapshots/    # Shell state snapshots
    └── downloads/          # Downloaded files
```

## 🎭 The Symphony Pattern

### Main Command: `/conduct`

The Symphony orchestration follows a **7-phase workflow** with optional beautification phases:

```
1. Business Logic Extraction → Extract rules before architecture
2. Architecture & Validation → 95% confidence required, document WHY
3. Implementation Skeleton → Create structure with interfaces
   2.5. Skeleton Beautification → Optional DRY and clarity improvements
4. Test Skeleton → Define test structure (no implementation)
5. Implementation (3 Cycles):
   Cycle 1: Initial Implementation (2 hours)
   - Workers implement in chambers
   - Mark deviations when skeleton doesn't match
   - Document architectural discoveries
   
   Cycle 2: Merge, Purge & Resolution (1 hour)
   - Orchestrator reviews deviations
   - Makes architectural decisions
   - Merge agent applies decisions
   - Preserves good code, purges incompatible
   
   Cycle 3: Refinement (1 hour)
   - Redistribute clean code
   - Continue from consistent state
   
   4.5. Code Beautification → Optional DRY and complexity reduction
   
6. Test Implementation → Write tests against real code
7. Validation & Documentation → Comprehensive checks and doc updates
```

### Key Principles

- **No Interruptions**: Workers complete tasks despite discoveries
- **Deviation Tracking**: Mark architectural mismatches, continue working
- **Merge-Purge-Continue**: Progressive refinement without restarts
- **Living Mission**: Requirements evolve as understanding improves
- **Context Importance**: MUST READ / SHOULD KNOW / REFERENCE levels
- **Git Safety**: Merge to working branch only, never auto-push
- **Preserve Good Code**: Keep working patterns even when architecture changes
- **Clear Decisions**: Orchestrator makes calls, agents execute

## 🔄 Deviation Handling

When workers discover architectural mismatches:

### Severity Levels

**🟢 Minor**: Implementation detail differs
- Action: Implement better way, mark deviation
- Example: Sync in skeleton, async is better

**🟡 Major**: Architectural pattern change
- Action: Create stub, document, continue elsewhere
- Example: REST expected but GraphQL needed

**🔴 Fundamental**: Entire approach invalid
- Action: Interface stubs only, extensive docs
- Example: Auth system completely different

### Recording Deviations

```bash
python .symphony/tools/orchestration.py record-deviation \
  --agent "auth-impl" --module "auth" \
  --severity major \
  --expected "REST API" \
  --discovered "GraphQL required"
```

## 🧠 Intelligent Systems

### 1. **Module Cache & Gotchas** (`MODULE_CACHE.json` & `GOTCHAS.md`)
```json
{
  "confirmed_patterns": {
    "validation": {"pattern": "Always use Zod", "confidence": 0.95}
  },
  "anti_patterns": {
    "never_use": ["console.log in production", "var declarations"]
  }
}
```

### 2. **Pre-flight Validation** (Environment enforcement)
- Enforces virtual environment for Python projects (MANDATORY)
- Installs quality tools in appropriate environments:
  - Python: radon, vulture, ruff in project venv
  - JavaScript: eslint, prettier as dev dependencies
  - Go: gocyclo, golangci-lint via go install
- Caches validation in `~/.claude/preflight/{project_hash}.json`
- Saves project preferences including venv paths
- STOPS orchestration if environment setup fails

### 3. **Unified Quality Gate** (`code_quality_gate.py`)
- Single hook combining all critical quality checks:
  - Blocks anti-patterns (nested ternaries, double negation, linter suppression)
  - Ensures helpful error messages with actionable advice
  - Runs language-specific complexity analysis:
    * Python: radon for cyclomatic complexity
    * JavaScript: ESLint complexity rules
    * Go: gocyclo for metrics
  - Enforces limits: blocks complexity >15, warns >10
  - Falls back to pattern analysis when tools unavailable
  - Caches results for performance

### 4. **Context Flow System**
All agents receive essential context:
- **CLAUDE.md**: Coding standards and principles
- **INVARIANTS.md**: Unbreakable rules with WHY
- **DECISION_MEMORY.json**: All decisions with reasoning
- **GOTCHAS.md**: Project-specific patterns

WHO adds WHY comments:
- **Architects**: Design decisions
- **Implementers**: Discoveries and workarounds
- **Beautifiers**: Only if changes obscure reasoning

### 5. **Semantic Skeleton Diff**
- Only modifies files that need changes
- Preserves working code during refinements
- 10x faster than full rebuilds
- Maintains compilation validity

## 📊 Quality Standards

```yaml
test_philosophy:
  primary_validation: Integration test passes = code is validated
  secondary_metrics: Unit tests provide coverage numbers

test_coverage:
  lines: 95%          # Must achieve
  functions: 100%     # Every function tested
  branches: 90%       # Most conditionals covered

test_structure:
  mandatory_directories:
    unit_tests: tests/unit_tests/  # ALL unit tests here (NO EXCEPTIONS)
    integration_tests: tests/integration_tests/  # ALL integration tests here (NO EXCEPTIONS)
    violations: NO tests allowed outside these directories
  
  naming_requirements:
    unit_tests: test_[exact_source_filename].py  # EXACT 1:1 name match
    integration_tests: test_{workflow}_integration.py  # Workflow-level, not component
  
  separation_rules:
    mixed_files: FORBIDDEN - No file can contain both unit and integration tests
    directory_mixing: FORBIDDEN - Tests only in designated directories
    subdirectories: FORBIDDEN - No nested folders in test directories
  
  integration_test: 
    count: ONE comprehensive test class (1-2 files max)
    role: PRIMARY VALIDATION - passes = code validated
    scenarios: DATA configurations, not separate functions
    execution: Run process MINIMUM times, test MAXIMUM scenarios
    connections: REAL Server/DB/API (NO MOCKS)
    sequential_runs: Only for UPDATE/RE-CREATION/STATE TRANSITIONS/INCOMPATIBLE FLAGS
  
  unit_tests: 
    count: EXACTLY ONE file per source file (strict 1:1 mapping)
    role: SECONDARY - coverage metrics only
    coverage: 100% function coverage required
    mocking: Mock ALL dependencies
  
  e2e_tests: OPTIONAL - only if UI/API exists
```

## 🚀 Getting Started

### Installation

```bash
# Clone this configuration
git clone [your-repo] ~/.claude

# Set up any required environment variables
export ANTHROPIC_API_KEY="your-key"

# Ready to use!
claude
```

### Basic Usage

```bash
# Set your personality vibe
/vibe              # Show available vibes
/vibe solo         # 🎸 Quick and direct (default)
/vibe concert      # 🎭 Professional precision
/vibe duo          # 🎼 Collaborative
/vibe mentor       # 📚 Socratic teaching

# Musical command symphony
/prelude           # Build task specification through conversation
/conduct           # Execute the orchestrated task
/coda              # Generate handoff summary

# For simple tasks (< 30 minutes)
# Just use Claude directly without orchestration
```

## 🔧 Key Orchestration Commands

### Symphony Tools

```bash
# Setup chambers for parallel work
python .symphony/tools/orchestration.py setup-chambers \
  --workers '[{"id": "auth-impl", "module": "auth", "scope": "src/auth/**"}]'

# Record architectural deviation
python .symphony/tools/orchestration.py record-deviation \
  --agent "auth-impl" --severity major \
  --expected "REST" --discovered "GraphQL"

# Get all deviations for review
python .symphony/tools/orchestration.py get-deviations

# Format architectural decisions
python .symphony/tools/orchestration.py format-decisions

# Merge chambers to working branch
python .symphony/tools/orchestration.py merge-chambers

# Clean up after task
python .symphony/tools/orchestration.py cleanup-task
```

## 🔧 Advanced Features

### Model Strategy (Optimized for Speed)
- **Haiku 4**: DEFAULT for skeletons, validation checks, test execution (3-5x faster)
- **Sonnet 4**: Complex implementation, escalation from Haiku
- **Default Model**: Reviews, security audits, complex reasoning
- **Smart Escalation**: Haiku → Sonnet → Default based on complexity

### Parallel Execution
The conductor identifies parallelizable work and launches multiple agents simultaneously:
- Implementation agents work on different modules
- Test writers create tests in parallel
- All coordinated through the conductor

### Progressive Validation & Recovery
**Two-Phase Validation**:
1. **Quick Phase (Haiku)**: Syntax, imports, tests, linting
2. **Deep Phase (Default)**: Security, architecture, performance

**Smart Recovery**:
- Distinguish ARCHITECTURE_FLAW vs MODEL_LIMITATION
- Route to appropriate fix (Phase 1 vs model escalation)
- Fast feedback loop with Haiku validation
- Maximum 3 recovery attempts before user escalation

## ⚡ Performance Improvements (v2.0)

### Speed Optimizations
- **30-40% faster** overall task completion
- **Haiku-First Strategy**: Default to Haiku for skeletons (3-5x faster)
- **Progressive Validation**: Catch 80% of issues in 20% of time
- **Smart Model Selection**: Right model for right task
- **Parallel Execution**: Multiple validation checks simultaneously

### Key Improvements
- **Issue Categorization**: ARCHITECTURE_FLAW vs MODEL_LIMITATION vs QUALITY_ISSUE
- **Model Escalation**: Haiku → Sonnet → Opus only when needed
- **Two-Phase Validation**: Quick checks (Haiku) then deep analysis (Default)
- **Strict Test Structure**: Enforced directories and 1:1 mapping
- **Integration-First Testing**: Integration = validation, Unit = metrics

## 🎯 When to Use This System

**Perfect for:**
- Projects touching 3+ files
- Tasks requiring comprehensive testing
- Features needing parallel development
- Complex refactoring with dependencies

**Not needed for:**
- Simple bug fixes
- Single file changes
- Documentation updates
- Minor configuration changes

## 🔮 System Evolution

This orchestration system learns and improves:
- Each task updates pattern confidence
- Failed approaches are remembered
- Successful patterns are reinforced
- Project-specific knowledge accumulates

## 🎵 Musical Theme & Personality System

### Vibe Modes
Claude adapts its personality while maintaining brutal honesty:

- **🎸 Solo** (default): Quick, direct, slightly sarcastic. "That's overengineered. Just use grep."
- **🎭 Concert**: Professional precision for production. "Critical: This exposes user data."
- **🎼 Duo**: Collaborative exploration. "Building on your idea, what if..."
- **📚 Mentor**: Socratic teaching method. "What do you think happens when...?"


### Auto-Formatting
Automatic code formatting after edits:
- Python: ruff → black fallback
- JavaScript/TypeScript: prettier → eslint
- Go: goimports → gofmt
- Configs in `~/.claude/configs/`

## 💡 Tips for Success

1. **Trust the Gates**: Let validation gates catch issues early
2. **Embrace Learning**: The system improves with use
3. **Delegate Everything**: The conductor never implements directly
4. **Maintain Skeletons**: Treat skeleton contracts as sacred
5. **Review Gotchas**: Periodically update `GOTCHAS.md` with new rules
6. **Pick Your Vibe**: Use `/vibe mentor` for learning, `/vibe concert` for production

## 🚧 Troubleshooting

**Environment Issues**: Run `/conduct` and choose option B to fix in new session
**Rule Conflicts**: Check `GOTCHAS.md` and update outdated rules
**Validation Failures**: Review gate feedback, often just needs refinement

---

*Built for developers who want Claude Code to work like a well-conducted orchestra* 🎼