# ~/.claude Overview - Claude Code Configuration System

**Purpose**: Intelligent development environment with cross-session learning, orchestration patterns, and AI-optimized documentation.

**Version**: 2025-10-17
**Primary User**: Developer using Claude Code CLI
**AI Agent Target**: Sonnet 4.5 (general-builder, orchestrator, specialized agents)

---

## What This Directory Contains

### 1. Work Contract & Global Instructions
- `CLAUDE.md` - Core principles, quality gates, decision framework (105 lines)
- `README.md` - Installation, hook system, PRISM integration (270 lines)
- `ORCHESTRATION_GUIDE.md` - Command comparison and decision tree (291 lines)
- `llms.txt` - This index for AI agents (documentation map)

### 2. Core Documentation (docs/)
**AI Documentation Standards**:
- How to write concise, scannable docs for AI agents
- Structure over prose, location over explanation
- Hierarchical CLAUDE.md best practices

**Testing Standards**:
- 1:1 file mapping (one test per production file)
- 95%+ coverage for unit tests
- Test organization patterns

**MCP Integration**:
- Model Context Protocol setup and servers
- PRISM semantic memory integration
- Obsidian vault configuration

### 3. Orchestration System

**Three Commands for Different Complexities**:

| Command | When to Use | Prerequisites | Token Budget |
|---------|-------------|---------------|--------------|
| `/solo` | Simple, straightforward tasks | None | 10-20k |
| `/spec` | Need investigation & planning | None | 15-30k |
| `/conduct` | Complex multi-component work | SPEC.md from /spec | 50k+ |

**Command Flow**:
```
User Task
    │
    ├─ Straightforward? ──→ /solo ──→ Done
    │
    ├─ Need planning? ──→ /spec ──→ Creates SPEC.md ──→ /conduct ──→ Done
    │
    └─ Have SPEC.md? ──→ /conduct ──→ Done
```

**Commands** (commands/):
- User-facing workflows with clear scope
- Reference templates for detailed formats
- Integrate with agent definitions

**Orchestration Patterns** (orchestration/):
- SPEC_INSTRUCTIONS.md - Discovery phase (spike testing, investigation)
- CONDUCT_INSTRUCTIONS.md - Execution phase (dependency-aware implementation)
- ORCHESTRATOR_PATTERN.md - General orchestration principles

### 4. Agent Definitions (agents/)

**Implementation Agents**:
- skeleton-builder - Create file skeletons with interfaces
- implementation-executor - Implement full working code
- test-implementer - Write comprehensive tests
- test-skeleton-builder - Create test file skeletons

**Validation Agents**:
- code-reviewer - Code quality and patterns (spawned 2-3x per phase)
- code-beautifier - Clean up code style
- security-auditor - Security vulnerability analysis
- performance-optimizer - Performance analysis

**Utility Agents**:
- fix-executor - Fix validation and test failures
- general-builder - Simple feature implementation (1-3 files)
- general-investigator - Codebase investigation
- spike-tester - Validate approaches in /tmp
- architecture-planner - High-level design

**Specialized Agents**:
- dependency-analyzer - Dependency analysis
- consolidation-analyzer - Find duplication
- merge-coordinator - Coordinate worktree merges

### 5. Templates (templates/)

**Spec Templates**:
- spec-minimal.md - For /solo (BUILD spec)
- spec-full.md - For /conduct (SPEC.md with 10 required sections)

**Response Templates**:
- agent-responses.md - Structured agent output formats (NO prose)
- operational.md - Algorithms (fix-validate loops, dependency resolution)

**Review Templates**:
- pr-review-code-analysis.md
- pr-review-security.md
- pr-review-tests.md
- pr-review-performance.md

**Pattern Templates**:
- INVARIANTS.md - Project invariants documentation
- GOTCHAS_TEMPLATE.md - Gotcha documentation pattern

### 6. Hook System (hooks/)

**Event-Driven Automation**:

**Session Hooks**:
- SessionStart: prism_http_startup.py, vibe_tracker.py
- SessionEnd: universal_learner_session_end.py (pattern promotion)
- UserPromptSubmit: unified_context_provider.py (memory injection)

**Tool Hooks**:
- PreToolUse (Bash): unified_bash_guardian.py (command safety)
- PreToolUse (Write/Edit): unified_code_validator.py (pattern enforcement)
- PreToolUse (Task): unified_context_provider.py (agent memory injection)
- PostToolUse (Write/Edit): edit_tracker.py (semantic change extraction)
- PostToolUse (Task): agent_learner.py (capture agent discoveries)

**Learning System**:
- edit_tracker.py - Extract semantic meaning from code changes
- agent_learner.py - Capture agent discoveries and patterns
- preference_manager.py - Detect and enforce user preferences
- universal_learner_session_end.py - Promote patterns across tiers

### 7. Language Configurations (configs/)

**Python**: ruff.toml, pylint.toml, mypy.ini
**JavaScript/TypeScript**: .prettierrc, .eslintrc.json
**Go**: .golangci.yml

Project configs take priority, these are fallbacks.

---

## How It All Fits Together

### Workflow Example: Simple Task (/solo)

1. **User**: `/solo add rate limiting to API endpoint`
2. **Main Agent**:
   - Reads task, determines scope
   - Creates `.spec/BUILD_rate-limit.md` (minimal spec)
   - Spawns implementation-executor
   - Spawns test-implementer
3. **Validation Loop**:
   - Runs linting
   - Spawns 6 reviewers in parallel
   - Spawns fix-executor if issues found
   - Repeats until clean (max 3 attempts)
4. **Testing Loop**:
   - Runs pytest with coverage
   - Spawns fix-executor if failures
   - Repeats until 95%+ coverage
5. **Documentation**: Validates all .md files
6. **Complete**: Working, tested, validated code

**Hooks in Action**:
- UserPromptSubmit: Injects relevant memories about rate limiting from past work
- PreToolUse (Task): Injects context into agent prompts
- PostToolUse (Write/Edit): Extracts semantic changes (added_rate_limiting)
- PostToolUse (Task): Captures agent discoveries (recommended using Redis)
- SessionEnd: Promotes rate limiting pattern if used 3+ times

### Workflow Example: Complex Feature (/spec + /conduct)

1. **User**: `/spec add real-time event processing with gRPC`
2. **Spec Phase** (spec.md + SPEC_INSTRUCTIONS.md):
   - Initial assessment (3-5 questions)
   - Auto-investigation (read existing code)
   - Challenge mode (find ≥3 concerns)
   - Spike testing in /tmp (validate gRPC, DB, UI approaches)
   - Create SPEC.md with 10 required sections
   - Create component phase specs (SPEC_1_*.md, SPEC_2_*.md, etc.)
3. **User**: `/conduct`
4. **Conduct Phase** (conduct.md + CONDUCT_INSTRUCTIONS.md):
   - Parse SPEC.md → extract components and dependencies
   - Build dependency graph → topological sort
   - For each component in order:
     - Skeleton → Implementation → Validate → Test → Document → Checkpoint
   - Integration testing after all components
   - Documentation validation
5. **Complete**: Multi-component system, fully tested and validated

**Hooks in Action**:
- Spike testing stores findings in PRISM (semantic memory)
- Each component discovery enhances future component specs
- Agent learnings captured and promoted across sessions
- User preferences enforced (e.g., "never use .get() with defaults")

---

## Key Architectural Decisions

### 1. Three-Tier Command Structure

**Why**: Different task complexities need different approaches.
- /solo: Fast iteration for straightforward work (no orchestration overhead)
- /spec: Proper investigation prevents costly rework
- /conduct: Dependency-aware execution for complex systems

**Trade-off**: More commands to learn, but clearer scope and better outcomes.

### 2. Agent-Based Delegation

**Why**: Token efficiency + specialization.
- Main agent orchestrates, doesn't implement
- Sub-agents focus on single responsibility
- Parallel agent execution (6 reviewers in single message)

**Trade-off**: More coordination overhead, but better quality and context management.

### 3. Spike Testing Philosophy (/spec)

**Why**: Validate everything before committing to approach.
- Test in /tmp before production code
- Document exact commands that work
- Capture gotchas with recovery steps

**Trade-off**: More upfront time, but prevents failed implementations.

### 4. Per-Component Validation (/conduct)

**Why**: Catch issues early, build on working foundations.
- Each component fully validated before next starts
- Next components see working APIs from previous phases
- Token usage per agent stays reasonable

**Trade-off**: Sequential validation slower than all-at-once, but prevents cascading failures.

### 5. PRISM Semantic Memory Integration

**Why**: Cross-session learning without manual documentation.
- Hooks extract semantic meaning automatically
- Patterns promoted by usage (3+ uses → LONGTERM tier)
- Context injected into prompts and agent launches
- User preferences enforced (2+ corrections → ANCHORS tier)

**Trade-off**: Requires PRISM infrastructure (Redis, Neo4j, Qdrant), but provides genuine learning.

### 6. AI-Optimized Documentation

**Why**: AI agents need maps, not tutorials.
- Concise over comprehensive (agents can read code)
- Structure over prose (tables/bullets over paragraphs)
- Location over explanation (file:line references)
- Hierarchical CLAUDE.md (avoid duplication across levels)

**Trade-off**: Less "readable" for humans, but 10x more useful for AI agents.

---

## Directory Purposes

| Directory | Purpose | Primary Users | Line Count Target |
|-----------|---------|---------------|-------------------|
| docs/ | Core standards and setup | Developers, agents | 200-800 per file |
| commands/ | User-facing workflows | Developers | 300-600 per file |
| orchestration/ | Agent execution patterns | Main orchestrator | 200-800 per file |
| agents/ | Specialized agent definitions | Main orchestrator | 100-300 per file |
| templates/ | Reusable formats | Commands, agents | 50-300 per file |
| hooks/ | Event-driven automation | System (automatic) | 100-500 per file |
| configs/ | Language tool configs | Tools (automatic) | N/A |

---

## Common Navigation Paths

### For Developers (Using Claude Code)

**Starting a task**:
1. Check ORCHESTRATION_GUIDE.md decision tree
2. Choose /solo, /spec, or /conduct
3. Run command, let orchestration handle it

**Understanding what happened**:
1. Check `.spec/PROGRESS.md` in working directory
2. Review `.spec/BUILD_*.md` or `.spec/SPEC.md` for context
3. Check agent definitions if curious about sub-agent behavior

**Customizing behavior**:
1. Edit CLAUDE.md in project root (project-specific rules)
2. Edit ~/.claude/CLAUDE.md for global overrides
3. Edit language configs in ~/.claude/configs/

### For AI Agents (Reading This)

**Orchestrating a task**:
1. Read command file (solo.md, spec.md, or conduct.md)
2. Read orchestration instructions (SPEC_INSTRUCTIONS.md or CONDUCT_INSTRUCTIONS.md)
3. Reference agent definitions when spawning sub-agents
4. Use templates for spec and response formats

**Finding implementation details**:
1. Check operational.md for algorithms (fix-validate loops, dependency resolution)
2. Check agent-responses.md for structured output formats
3. Check TESTING_STANDARDS.md for coverage requirements

**Delegating to sub-agents**:
1. Read agent definition (e.g., agents/implementation-executor.md)
2. Craft prompt with spec reference and context
3. Include response template for structured output
4. Wait for agent completion, parse response

---

## Quality Standards Summary

**Testing**: 95%+ coverage for unit tests, 1:1 file mapping
**Linting**: Zero errors (ruff/eslint/golangci), no suppressions without justification
**Documentation**: Accurate, up-to-date, AI-scannable
**Validation**: 6 reviewers (security, performance, code quality 3x, style, docs)
**Git Commits**: After each major step, descriptive messages, Claude co-author
**Error Handling**: Fail loud, never catch and ignore

---

## PRISM Memory System

**What It Does**:
- Stores semantic code changes (added_error_handling, bug_fix, refactoring)
- Captures agent discoveries (patterns, decisions, gotchas)
- Detects user preferences (repeated corrections)
- Injects relevant context into prompts and agent launches
- Promotes patterns across tiers (WORKING → LONGTERM → ANCHORS)

**Memory Tiers**:
- ANCHORS: Critical rules (violations block execution)
- LONGTERM: Stable patterns (3+ uses or 85%+ confidence)
- WORKING: Session-specific (cleared between sessions)
- EPISODIC: Recent events (time-based decay)

**Promotion Logic**:
- 3+ uses → Higher tier
- Bug fixes → Immediate LONGTERM
- 2+ user corrections → ANCHORS
- Background task every 5 minutes checks promotion criteria

**Integration Points**:
- UserPromptSubmit hook: Injects relevant memories
- PreToolUse (Task) hook: Injects context into agent prompts
- PostToolUse (Write/Edit) hook: Extracts semantic changes
- PostToolUse (Task) hook: Captures agent discoveries
- SessionEnd hook: Promotes patterns across tiers

---

## When to Use What

### Commands

**Use /solo when**:
- Single component or few related files
- Clear, straightforward implementation
- Standard patterns apply
- Fast iteration desired

**Use /spec when**:
- Need to explore problem space
- Architecture requires thought
- Multiple approaches possible
- High complexity/uncertainty

**Use /conduct when**:
- Have SPEC.md from /spec
- Multiple interconnected components
- Dependencies need management
- Variant exploration beneficial

### Agents

**Use implementation-executor**: Full implementation from skeleton
**Use test-implementer**: Write tests for working code
**Use fix-executor**: Fix validation or test failures
**Use general-builder**: Simple 1-3 file features with validation
**Use spike-tester**: Validate approach in /tmp before production
**Use code-reviewer**: Quality validation (spawn 2-3x per validation)

### Documentation Patterns

**Use CLAUDE.md**: Project-specific patterns and rules
**Use QUICKREF.md**: Deep-dive examples and code snippets
**Use OVERVIEW.md**: System architecture and navigation
**Use BUSINESS_RULES.md**: Authoritative business logic catalog
**Use llms.txt**: Documentation index for AI agents

---

## Troubleshooting

**Orchestration feels stuck**:
1. Check `.spec/PROGRESS.md` for current phase
2. Review agent response for status
3. Check for ESCALATE or BLOCKED messages

**Agent not following patterns**:
1. Check agent definition (agents/*.md)
2. Verify response template was included in prompt
3. Check if ANCHORS preference is blocking

**PRISM not injecting context**:
1. Verify PRISM HTTP server running: `curl http://localhost:8090/health`
2. Check hooks enabled: `cat ~/.claude/settings.json | jq '.hooks'`
3. Restart services: `cd ~/repos/claude_mcp/prism_mcp && nerdctl compose restart`

**Hooks not triggering**:
1. Check permissions: `ls -la ~/.claude/hooks/*.py`
2. Verify hook configuration in settings.json
3. Check debug output in ~/.claude/debug/

**Pattern not promoting**:
1. Check usage count (needs 3+ uses)
2. Verify confidence level (needs 85%+)
3. Manual session end: `echo '{"hook_event_name":"SessionEnd"}' | python ~/.claude/hooks/universal_learner_session_end.py`

---

## Related Projects

- **PRISM MCP**: `~/repos/claude_mcp/prism_mcp/` - Semantic memory system
- **Orchestration MCP**: `~/repos/claude_mcp/orchestration_mcp/` - Redis-based task coordination (deprecated - YOU orchestrate directly now)

---

## Remember

**For humans**: Let the orchestration system handle complexity. Your job is to specify WHAT, not HOW.

**For AI agents**: Follow command instructions, delegate to specialized agents, validate at quality gates, document learnings. This system learns across sessions - your discoveries benefit future work.

**The philosophy**: Concise, structured, validated, and continuously improving through automated learning.
