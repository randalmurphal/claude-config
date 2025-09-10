# Claude Conductor - Advanced Orchestration System

A sophisticated orchestration system for Claude Code that implements skeleton-first development with intelligent validation gates and learning capabilities.

## 🎯 Overview

This is a complete orchestration system that transforms Claude Code into a powerful development conductor, capable of managing complex multi-file projects with parallel execution, intelligent refinement, and quality gates.

## 🚀 Key Features

### 1. **Skeleton-First Architecture**
- Builds complete structure before implementation
- Validates architecture early to prevent integration issues  
- Enables true parallel development with git worktrees
- Surgical refinement instead of full rebuilds
- Safe application of parallel work to working directory

### 2. **Intelligent Context Management**
- MODULE_CACHE.json for instant re-analysis of unchanged files
- GOTCHAS.md for project-specific rules and hard-learned lessons
- Three-tier /purge command prevents context overflow
- Phase-aware compression keeps critical information
- AGENT_METRICS.json tracks performance and detects degradation

### 3. **Smart Validation & Quality Gates**
- Auto-detects project validation tools (Python/JS/Go)
- Distinguishes between "needs refinement" vs "failed implementation"
- Project-aware validation with tool detection
- Test impact analysis for selective test execution
- Complexity metrics using language-specific tools (radon/gocyclo/eslint)

## 📁 System Structure

```
~/.claude/
├── agents/                    # Specialized sub-agents
│   ├── skeleton-builder.md    # Creates implementation structure (Sonnet)
│   ├── skeleton-refiner.md    # Surgical updates to skeletons (Sonnet)
│   ├── skeleton-reviewer.md   # Validates and optimizes (Opus)
│   ├── pattern-learner.md     # Tracks and updates patterns
│   ├── preflight-validator.md # Environment readiness checks
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
1. Pre-flight Validation → Check environment readiness (cached)
2. Architecture & Context → Validate 95% confidence before proceeding
3. Implementation Skeleton → Build structure with parallel agents (Sonnet)
   └── GATE 1: Review & refine with semantic diff
4. Test Skeleton → Create test structure (max 10-15 files)
   └── GATE 2: Validate test organization
5. Parallel Implementation → Multiple agents work against contracts
6. Validation & Recovery → Comprehensive quality checks
7. Documentation & Learning → Update patterns for future tasks
```

### Key Principles

- **Orchestrator Never Implements**: Main agent only delegates
- **95% Confidence Gate**: Never proceed on assumptions
- **Context Inheritance**: Each phase builds on previous discoveries
- **Simplicity Bias**: Prefer single-file solutions, avoid premature abstraction
- **Pattern Learning**: System gets smarter with each task

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
test_coverage:
  lines: 95%          # Must achieve
  functions: 100%     # Every function tested
  branches: 90%       # Most conditionals covered

test_structure:
  unit_tests: One per implementation file
  integration_tests: 5-10 files maximum  
  e2e_tests: 1-2 files maximum
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

### Model Strategy
- **Sonnet**: Used for fast skeleton generation
- **Opus**: Used for validation and complex reasoning
- **Dynamic**: Agents use `--model sonnet` when specified

### Parallel Execution
The conductor identifies parallelizable work and launches multiple agents simultaneously:
- Implementation agents work on different modules
- Test writers create tests in parallel
- All coordinated through the conductor

### Recovery Handling
When validation fails:
1. Analyzes issues by severity
2. Delegates targeted fixes to appropriate agents
3. Maximum 3 recovery attempts
4. Escalates to user if needed

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