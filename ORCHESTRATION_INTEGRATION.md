# Orchestration Integration Guide

## Overview
This guide shows how the dependency analyzer and context builder integrate with the orchestration workflow.

## Component Interaction Flow

### Phase 1: Architecture (SERIAL)
```
architecture-planner → api-contract-designer → error-designer
                ↓
        dependency-analyzer (NEW)
                ↓
    Analyzes real dependencies & creates execution strategy
                ↓
        context-builder (NEW)
                ↓
    Initializes critical context tracking
```

### How Components Work Together

#### 1. Dependency Analyzer Output → Parallel Task Dispatcher

The dependency-analyzer creates `.claude/DEPENDENCY_GRAPH.json`:
```json
{
  "execution_strategy": {
    "parallel_groups": [
      {"group": 1, "components": ["UserService", "AuthService"]},
      {"group": 2, "components": ["OrderService"], "depends_on": [1]}
    ]
  }
}
```

Parallel-task-dispatcher reads this to make informed decisions:
```python
# Instead of guessing what can run in parallel
deps = load_dependency_graph()
for group in deps.execution_strategy.parallel_groups:
    if group.depends_on_complete():
        launch_parallel_tasks(group.components)
```

#### 2. Context Builder → All Agents

Context-builder maintains `.claude/context/CRITICAL_CONTEXT.json`:
```json
{
  "critical_decisions": [
    {
      "decision": "Using Redis for session storage",
      "impacts": ["All services need Redis client"],
      "phase": "architecture"
    }
  ],
  "gotchas": [
    {
      "issue": "Jest mocks break WebSocket tests",
      "workaround": "Use real timers for WebSocket"
    }
  ]
}
```

Every agent checks context before starting:
```python
# Any agent starting work
context = context_builder.get_relevant_context()
# Sees: "All services need Redis client"
# Knows to include Redis setup in implementation
```

## Workflow Improvements

### Before (Without New Components)
- **Problem**: Agent discovers OrderService needs PaymentService during implementation
- **Result**: Rework, delays, potential conflicts

### After (With Dependency Analyzer)
- **Solution**: Dependency found in Phase 1, execution order adjusted
- **Result**: No surprises, optimal parallelization

### Before (Without Context Builder)
- **Problem**: Agent 3 repeats same mistake Agent 1 made
- **Result**: Time wasted, frustration

### After (With Context Builder)  
- **Solution**: Gotcha recorded, Agent 3 sees warning
- **Result**: Mistake avoided, time saved

## Updated Test Coverage Standards

All tasks now require:
```yaml
test_coverage:
  lines: 95%         # Up from 80%
  branches: 90%      # Up from 75%
  functions: 100%    # EVERY function tested
  statements: 95%    # Up from 80%

mandatory_100_percent:
  - Error handling paths
  - Security/auth code
  - Input validation
  - Edge cases
```

## Practical Example

### Task: "Build authentication system"

**Phase 1: Architecture**
1. architecture-planner creates auth design
2. dependency-analyzer discovers:
   - AuthService → UserService → Database
   - Hidden: AuthService → RedisCache
   - Can parallel: AuthUI and AuthAPI
3. context-builder records:
   - Decision: "JWT with refresh tokens"
   - Gotcha: "Bcrypt 72 char limit"

**Phase 2: Tests (Using dependency info)**
- Group 1: UserService tests (no dependencies)
- Group 2: AuthService tests (after Group 1)
- Parallel: AuthUI and AuthAPI tests

**Phase 3: Implementation (Using context)**
- All agents see: "JWT with refresh tokens decision"
- Auth implementer sees: "Bcrypt 72 char warning"
- Parallel execution follows dependency graph

**Result**: 
- 40% faster due to optimal parallelization
- Zero dependency conflicts
- No repeated mistakes

## Key Benefits

1. **Dependency Analyzer**
   - Prevents integration failures
   - Enables true parallelization
   - Catches circular dependencies early
   - Maps hidden dependencies

2. **Context Builder**
   - Preserves critical decisions
   - Prevents repeated mistakes
   - No context clutter
   - Auto-cleans stale info

3. **Higher Test Coverage**
   - 95% line coverage (was 80%)
   - 100% function coverage
   - ALL error paths tested
   - Better quality assurance

## Usage Commands

### Large Tasks (Full orchestration)
```bash
/large_task "Build complete trading platform"
# Uses all phases, dependency analysis, context tracking
```

### Medium Tasks (Streamlined)
```bash
/medium_task "Add OAuth authentication"  
# 3 phases, same quality standards, uses existing architecture
```

### Simple Tasks (No orchestration)
```bash
# Just ask directly for simple changes
"Fix the typo in the login button"
```

## Success Metrics

The new system succeeds when:
- Parallel tasks actually run in parallel (not serial)
- No "surprise" dependencies discovered late
- Critical decisions are never lost
- Gotchas don't happen twice
- 95%+ test coverage achieved
- Zero circular dependencies
- Context stays under 2KB per task