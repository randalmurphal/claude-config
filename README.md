# Claude Conductor - Advanced Orchestration System

A sophisticated orchestration system for Claude Code that implements skeleton-first development with intelligent validation gates and learning capabilities.

## 🎯 Overview

This is a complete orchestration system that transforms Claude Code into a powerful development conductor, capable of managing complex multi-file projects with parallel execution, intelligent refinement, and quality gates.

## 🚀 Key Features

### 1. **Skeleton-First Architecture**
- Builds complete structure before implementation
- Specialized agents for each phase (not generic tasks)
- Enables true parallel development with git worktrees
- Post-merge consolidation fixes integration issues
- Guaranteed workspace cleanup after parallel work

### 2. **Intelligent Context Management**
- Phase-scoped contexts with smart handoffs
- Context inheritance rules (MUST_INHERIT, CAN_INHERIT, MUST_PURGE)
- Parallel workers get isolated LOCAL_CONTEXT.json
- Merge-coordinator aggregates all discoveries
- FAILURE_MEMORY.json tracks and classifies failures

### 3. **Smart Validation & Recovery**
- Phase-specific recovery agents for targeted fixes
- Intelligent failure classification (design_flaw, typo, etc.)
- Auto-detects project validation tools (Python/JS/Go)
- Test impact analysis for selective test execution
- Complexity metrics using language-specific tools (radon/gocyclo/eslint)

## 📁 System Structure

```
~/.claude/
├── agents/                    # Specialized sub-agents
│   ├── skeleton-builder.md    # Creates implementation structure (Sonnet)
│   ├── skeleton-builder-haiku.md # Fast skeleton creation (Haiku) ✨
│   ├── skeleton-reviewer.md   # Reviews with issue categorization (Opus)
│   ├── skeleton-refiner.md    # Surgical updates to skeletons (Sonnet)
│   ├── test-skeleton-builder.md # Creates test structure (Sonnet)
│   ├── test-skeleton-builder-haiku.md # Fast test skeleton (Haiku) ✨
│   ├── implementation-executor.md # Implements code (Default)
│   ├── test-implementer.md    # Implements tests (Default)
│   ├── validator-quick-haiku.md # Fast validation checks (Haiku) ✨
│   ├── test-runner-haiku.md   # Execute tests and report (Haiku) ✨
│   ├── preflight-validator-haiku.md # Fast environment checks (Haiku) ✨
│   ├── consolidation-analyzer.md # Post-merge integration
│   ├── merge-coordinator.md   # Merges code AND context
│   ├── context-builder.md     # Phase transition manager
│   └── [other agents]         # Various specialized agents
│
├── commands/                  # Orchestration commands
│   └── conduct.md            # Main orchestration command (/conduct)
│
├── quality-tools/            # Language-specific quality validation
│   ├── python/              # Python linting, formatting, testing
│   ├── go/                 # Go validation tools
│   ├── typescript/          # TS/JS validation
│   └── scripts/            # Universal quality scripts
│
├── hooks/                   # Event-driven automation
│   └── assumption_detector.py # Catches assumptions in real-time
│
└── [auto-generated]        # Directories Claude creates (gitignored)
    ├── projects/           # Project-specific data
    ├── todos/              # Agent task tracking
    ├── shell-snapshots/    # Shell state snapshots
    └── downloads/          # Downloaded files
```

## 🎭 The Conductor Pattern

### Main Command: `/conduct`

The conductor orchestration follows this sophisticated workflow:

```
1. Pre-flight Validation → preflight-validator-haiku (FAST cached checks)
2. Architecture & Context → Validate 95% confidence before proceeding
3. Implementation Skeleton → skeleton-builder-haiku (DEFAULT) or sonnet if complex
   └── GATE 1: skeleton-reviewer categorizes issues:
       - ARCHITECTURE_FLAW → back to Phase 1
       - MODEL_LIMITATION → escalate to better model
       - QUALITY_ISSUE → skeleton-refiner
4. Test Skeleton → test-skeleton-builder-haiku (DEFAULT) or sonnet if complex
   └── GATE 2: Validate structure and coverage planning
5. Parallel Implementation:
   a. Setup workspaces with context distribution
   b. implementation-executor agents implement code
   c. test-implementer agents implement tests (Integration-First)
   d. merge-coordinator merges code AND context
   e. consolidation-analyzer fixes integration issues
   f. Guaranteed workspace cleanup
6. Progressive Validation (TWO-PHASE):
   a. Quick validation with Haiku agents (syntax, tests, lint)
   b. If passes → Comprehensive validation with Opus
7. Documentation → Update CLAUDE.md and GOTCHAS.md
```

### Key Principles

- **Orchestrator Never Implements**: Main agent only delegates
- **95% Confidence Gate**: Never proceed on assumptions
- **Phase-Scoped Context**: Each phase has isolated context with handoffs
- **Specialized Agents**: Each phase uses purpose-built agents
- **Intelligent Failure Memory**: Learn from mistakes, avoid repetition
- **Post-Merge Consolidation**: Fix integration issues after parallel work
- **Guaranteed Cleanup**: Workspaces always removed after use

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

### 2. **Pre-flight Validation** (User-specific caching)
- Checks environment readiness before starting
- Caches results in `~/.claude/preflight/{project_hash}.json`
- Avoids git conflicts with user-specific storage
- Offers recovery options if environment isn't ready

### 3. **Semantic Skeleton Diff**
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
# For complex tasks (30+ minutes)
/conduct "Build a complete authentication system with JWT"

# Check status
/conduct status

# For simple tasks (< 30 minutes)
# Just use Claude directly without orchestration
```

## 🔧 Advanced Features

### Model Strategy (Optimized for Speed)
- **Haiku 4**: DEFAULT for skeletons, validation checks, test execution (3-5x faster)
- **Sonnet 4**: Complex implementation, escalation from Haiku
- **Opus 4**: Reviews, security audits, complex reasoning
- **Smart Escalation**: Haiku → Sonnet → Opus based on complexity

### Parallel Execution
The conductor identifies parallelizable work and launches multiple agents simultaneously:
- Implementation agents work on different modules
- Test writers create tests in parallel
- All coordinated through the conductor

### Progressive Validation & Recovery
**Two-Phase Validation**:
1. **Quick Phase (Haiku)**: Syntax, imports, tests, linting
2. **Deep Phase (Opus)**: Security, architecture, performance

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
- **Two-Phase Validation**: Quick checks (Haiku) then deep analysis (Opus)
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

## 💡 Tips for Success

1. **Trust the Gates**: Let validation gates catch issues early
2. **Embrace Learning**: The system improves with use
3. **Delegate Everything**: The conductor never implements directly
4. **Maintain Skeletons**: Treat skeleton contracts as sacred
5. **Review Gotchas**: Periodically update `GOTCHAS.md` with new rules

## 🚧 Troubleshooting

**Environment Issues**: Run `/conduct` and choose option B to fix in new session
**Rule Conflicts**: Check `GOTCHAS.md` and update outdated rules
**Validation Failures**: Review gate feedback, often just needs refinement

---

*Built for developers who want Claude Code to work like a well-conducted orchestra* 🎼