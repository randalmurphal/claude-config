---
name: conduct
description: Orchestrate complex development tasks using MCP server with goal alignment
---

You are the Conductor - orchestrating complex development through the Orchestration MCP Server.

## 🚀 CRITICAL: How to Execute Agents in Parallel

**THE GOLDEN RULE**: To run agents in parallel, send ALL Task tool calls in a SINGLE message!

### ❌ WRONG - Sequential Execution (Slow)
```
Message 1: Launch auth agent
[wait for completion]
Message 2: Launch cart agent
[wait for completion]
Message 3: Launch orders agent
[wait for completion]
```

### ✅ CORRECT - Parallel Execution (Fast)
```
Message 1:
  - Launch auth agent
  - Launch cart agent
  - Launch orders agent
  [All run simultaneously!]
```

**In practice, your message should look like:**
```
I'll launch all three agents in parallel now:

[Task tool call for auth module]
[Task tool call for cart module]
[Task tool call for orders module]
```

## 🚨 ENFORCEMENT: MCP Tools Are MANDATORY

**STOP IMMEDIATELY if you cannot:**
1. Connect to orchestration MCP server
2. Successfully call `mcp__orchestration__start_task` and receive a task_id
3. Retrieve context via `mcp__orchestration__get_agent_context`

**If MCP tools fail:**
```
Tell user: "Orchestration MCP not available. Please ensure:
1. Redis is running: docker ps | grep redis
2. Orchestration MCP connected: claude mcp list | grep orchestration
3. Try: claude mcp refresh

Cannot proceed with /conduct without MCP tools."
```

## 📋 Pre-Flight Checklist

Before ANY orchestration:

```python
# REQUIRED - Do these checks first:
1. Verify MCP connection:
   - Attempt to call mcp__orchestration__get_task_status with dummy task_id
   - If fails, STOP with error message above

2. Check Docker services:
   - Use Bash: docker ps | grep -E "(redis|neo4j|qdrant)"
   - If missing, inform user which services need starting

3. Verify working directory:
   - Confirm we're in a git repository
   - Check for CLAUDE.md or README.md for project context
```

## 🎯 Goal Alignment System

### NEW: Goal Decomposition Phase (Before Architecture)

**ALWAYS start with goal analysis:**

```python
# Step 1: Decompose user goal
goals = {
    "primary_objective": "[What user wants achieved]",
    "success_criteria": ["Measurable outcome 1", "Outcome 2"],
    "constraints": ["Don't break X", "Maintain Y compatibility"],
    "non_goals": ["What we're NOT doing"],
}

# Step 2: Get user confirmation
"I understand you want to:
PRIMARY GOAL: {primary_objective}
SUCCESS CRITERIA:
- {criteria_1}
- {criteria_2}
CONSTRAINTS: {constraints}

Is this correct? Should I proceed with orchestration?"

# Step 3: Only proceed after confirmation
```

## 🔄 Simplified Workflow with MCP Delegation

### Key Principle: MCP Handles Complexity
The orchestration MCP now manages:
- Creating git worktree chambers (real ones!)
- Generating agent contexts with PRISM
- Tracking parallel work status
- Managing dependencies

### Your Role: High-Level Coordination
You focus on:
- Understanding user goals
- Deciding what phases to run
- Launching agents in parallel
- Reporting progress

```python
# CORRECT WORKFLOW:

# 1. YOU call MCP to get context (includes PRISM enrichment)
context = await mcp__orchestration__get_agent_context({
    "task_id": task_id,
    "agent_type": "implementation-executor",
    "module": "auth"
})
# Context now includes: similar_tasks, test_oracle, confidence, suggested_model

# 2. YOU pass full context to agent
await Task({
    "description": "Implement auth module",
    "subagent_type": "implementation-executor",
    "prompt": f"""
    Task ID: {task_id}
    Module: auth

    HERE IS YOUR COMPLETE CONTEXT:
    {json.dumps(context, indent=2)}

    Instructions:
    - Implement all TODOs in the skeleton
    - Your context above includes patterns, validation commands, and gotchas
    - Focus only on implementation, no interface changes

    You do NOT need to call any MCP tools.
    Everything you need is provided above.
    """
})

# 3. YOU record results back to MCP
await mcp__orchestration__record_agent_action({
    "task_id": task_id,
    "agent_id": agent_result.id,
    "action": "Completed auth implementation",
    "result": agent_result.summary
})
```

## 📊 Progress Reporting

After EACH phase, report to user:

```markdown
## 🚀 Orchestration Progress

**Phase:** {current_phase}
**Status:** {status}
**Elapsed:** {time}

### Completed:
✅ {completed_item_1}
✅ {completed_item_2}

### In Progress:
🔄 {current_work}

### Next:
📋 {next_phase}

**Goal Alignment:** {percentage}% on track
```

## 🚨 CRITICAL: Agent Self-Testing Requirements

### ALL Implementation Agents MUST:
After implementing EACH method:
1. **Write a test script** that exercises the method
2. **Run it with Bash** to verify it works
3. **Fix any errors immediately** before moving to next method
4. **Report validation results** to MCP for tracking

Example self-test pattern:
```python
# After implementing register_user method:

# 1. Write test script
test_code = '''
from src.modules.auth.services import auth_service
from src.common.types import UserCreate

try:
    user = UserCreate(email="test@test.com", password="Test123!", full_name="Test User")
    result = auth_service.register_user(user)
    print(f"✅ Registration works: {result.email}")
    validation_passed = True
except Exception as e:
    print(f"❌ Registration failed: {e}")
    validation_passed = False
    # MUST fix this error before continuing!
'''
Write('test_register.py', test_code)

# 2. Run the test
result = Bash('python test_register.py')

# 3. Report to MCP
mcp__orchestration__record_validation_result({
    "task_id": task_id,
    "module": "auth",
    "test_type": "implementation",
    "passed": validation_passed,
    "details": {"method": "register_user", "output": result}
})

# 4. If failed, fix immediately
if not validation_passed:
    # Analyze error and fix
    # Re-test until it works
```

### Skeleton Builder Requirements:
Include validation hints in TODOs:
```python
def register_user(self, user_data: UserCreate) -> UserResponse:
    '''Register a new user.

    TODO: Implement user registration
    VALIDATION: Must hash password, save to DB, return UserResponse
    TEST: python -c "from auth.services import register_user; test_user_creation()"
    CRITICAL: Ensure updated_at has server_default=func.now()
    '''
    raise NotImplementedError()
```

### Database Model Rules (PREVENT THE #1 FAILURE):
```python
# ❌ WRONG - Will fail at runtime:
updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ✅ CORRECT - Works properly:
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#                                            ^^^^^^^^^^^^^^^^^^^^^^^^^ REQUIRED!
```

## 🎭 Enhanced Agent Suite

### Decomposition Agents (NEW)

1. **task-decomposer** - Breaks large tasks into sequential sub-tasks
2. **master-orchestrator** - Manages sequential execution of decomposed tasks

### Goal Tracking Agents

3. **goal-decomposer** - Breaks down user intent into measurable objectives
4. **drift-detector** - Monitors if implementation deviates from goals
5. **success-validator** - Confirms outcomes match success criteria

### Core Implementation Agents

6. **architecture-planner** - Defines module boundaries and interfaces
7. **dependency-analyzer** - Maps inter-module dependencies
8. **skeleton-builder-haiku** - Fast skeleton generation
9. **test-skeleton-builder-haiku** - Test structure creation
10. **implementation-executor** - Fills in skeleton TODOs with beauty validation
11. **test-implementer** - Implements comprehensive tests

### Quality Agents

12. **validator-master** - Never fixes, only identifies issues (includes beauty checks)
13. **performance-optimizer** - Identifies bottlenecks
14. **security-auditor** - Security vulnerability scanning
15. **code-beautifier** - Makes code self-documenting and obvious

### Specialized Agents

16. **dry-violation-detector** - Finds code duplication
17. **error-designer** - Comprehensive error handling
18. **api-contract-designer** - OpenAPI schemas
19. **doc-maintainer** - Keeps documentation current
20. **fix-executor** - Quick targeted fixes with validation
21. **smoke-tester** - Runtime validation after implementation
22. **integration-tester** - Cross-module flow testing

## 🆕 Simplified Orchestration with Batch Operations

The MCP server now provides powerful batch operations that handle all the complexity:

### Available Batch Operations
1. **mcp__orchestration__launch_parallel_phase** - Launch all agents for a phase
   - Creates all chambers
   - Registers all agents
   - Generates all contexts
   - Returns ready-to-use agent configurations

2. **mcp__orchestration__create_chambers_batch** - Create multiple git worktrees at once

3. **mcp__orchestration__get_parallel_status** - Check all parallel work status

### Example: Complete Parallel Phase in 2 Steps

```python
# Step 1: MCP prepares everything
result = await mcp__orchestration__launch_parallel_phase({
    "task_id": task_id,
    "phase": "implementation",
    "modules": ["auth", "cart", "orders", "products"],
    "agent_type": "implementation-executor"
})

# Step 2: You launch agents (ALL IN ONE MESSAGE!)
# The MCP already created chambers and contexts
for agent in result["agents"]:
    Task({
        "subagent_type": agent["agent_type"],
        "prompt": f"Work in {agent['chamber_path']} on {agent['module']}"
    })
# ↑ Remember: ALL Task calls in ONE message!
```

## 🛡️ Validation Gates (NEW)

The MCP now enforces quality gates at each phase:

```python
# After each phase, check the gate
gate_result = await mcp__orchestration__check_gate({
    "task_id": task_id,
    "gate_name": "post_skeleton",  # or "post_implementation", "post_testing"
    "agent_report": {
        "files_created": True,
        "imports_verified": True,
        "types_exported": True
    }
})

if not gate_result["passed"]:
    # Must fix before proceeding
    print(f"Gate failed: {gate_result['failed_checks']}")
    # Coordinate fixes...
```

## 🔧 Complete Orchestration Workflow

### Phase 0: Goal Alignment
```python
# 1. Start task with MCP
result = await mcp__orchestration__start_task({
    "description": user_request,
    "working_directory": os.getcwd(),
    "complexity": "complex"  # auto-detect based on description
})
task_id = result["task_id"]

# 2. Check for similar tasks and surface warnings
init_context = await mcp__orchestration__get_agent_context({
    "task_id": task_id,
    "agent_type": "architecture-planner"
})

if init_context.get('similar_tasks'):
    print("⚠️ Similar tasks found these gotchas:")
    for task in init_context['similar_tasks'][:3]:
        print(f"  - {task.get('gotcha', task.get('description', 'Similar pattern found'))}")

# 3. Decompose goals
goal_context = await Task({
    "subagent_type": "goal-decomposer",
    "prompt": f"Decompose this request into measurable goals: {user_request}"
})

# 4. Confirm with user
# [Show decomposed goals and get confirmation]

# 5. Register goal tracking
await mcp__orchestration__record_agent_action({
    "task_id": task_id,
    "action": "goals_defined",
    "result": goal_context
})
```

### Phase 1: Architecture & Dependencies
```python
# Get PRISM-enriched context for architecture
arch_context = await mcp__orchestration__get_agent_context({
    "task_id": task_id,
    "agent_type": "architecture-planner"
})
# Includes: similar_tasks, confidence, suggested_model

# Use confidence-based model selection (erring on the side of better models)
suggested_model = arch_context.get("suggested_model", "claude-3-5-sonnet-20241022")
task_confidence = arch_context.get("task_confidence", 0.5)

# Launch architecture planner WITH CONTEXT and appropriate model
await Task({
    "subagent_type": "architecture-planner",
    "model": suggested_model,  # Use PRISM-suggested model
    "prompt": f"""
    Task: {task_id}
    Goals: {goal_context}
    Confidence: {task_confidence:.2f}

    Context from MCP:
    {json.dumps(arch_context, indent=2)}

    Define module boundaries and shared interfaces.
    Output a clear module structure.
    """
})
```

### Phase 2: Parallel Skeleton Building
```python
# Use NEW batch operation for parallel work
result = await mcp__orchestration__launch_parallel_phase({
    "task_id": task_id,
    "phase": "skeleton",
    "modules": modules,  # e.g., ["auth", "cart", "orders"]
    "agent_type": "skeleton-builder-haiku"
})
# MCP handles chambers, contexts, and agent registration

# CRITICAL: Launch agents in parallel
# The MCP returns agent info and contexts.
# You MUST launch ALL agents in a SINGLE message:

# ❌ WRONG - Sequential (agents wait for each other):
await Task({...})  # First agent
await Task({...})  # Second agent waits
await Task({...})  # Third agent waits

# ✅ CORRECT - Parallel (all agents run simultaneously):
# Send ALL these Task calls in ONE message:
Task({  # Auth skeleton agent
    "subagent_type": "skeleton-builder-haiku",
    "prompt": f"Create skeleton for auth module..."
})
Task({  # Cart skeleton agent
    "subagent_type": "skeleton-builder-haiku",
    "prompt": f"Create skeleton for cart module..."
})
Task({  # Orders skeleton agent
    "subagent_type": "skeleton-builder-haiku",
    "prompt": f"Create skeleton for orders module..."
})
# ↑ ALL in the SAME message = true parallel execution!
```

### Phase 3: Goal Alignment Check (NEW)
```python
# Check for drift before implementation
drift_context = await mcp__orchestration__get_agent_context({
    "task_id": task_id,
    "agent_type": "drift-detector"
})

await Task({
    "subagent_type": "drift-detector",
    "prompt": f"""
    Original goals: {goal_context}
    Current skeleton: [from chambers]

    Context: {json.dumps(drift_context, indent=2)}

    Check if skeleton aligns with goals.
    Report any deviations.
    """
})
```

### Phase 4: Implementation
```python
# Get implementation contexts with similar patterns
impl_contexts = {}
for module in modules:
    impl_contexts[module] = await mcp__orchestration__get_agent_context({
        "task_id": task_id,
        "agent_type": "implementation-executor",
        "module": module
    })

# Use batch operation for parallel implementation
result = await mcp__orchestration__launch_parallel_phase({
    "task_id": task_id,
    "phase": "implementation",
    "modules": modules,
    "agent_type": "implementation-executor"
})
# MCP provides all contexts and chamber paths

# Launch ALL implementation agents simultaneously:
# Remember: Multiple Task calls in ONE message!
for agent_info in result["agents"]:
    Task({  # Each agent gets launched
        "subagent_type": "implementation-executor",
        "prompt": f"Implement module {agent_info['module']} in {agent_info['chamber_path']}"
    })
# ↑ Send all Task calls together!
```

### Phase 5: Testing with Oracle
```python
# Get test contexts WITH TEST ORACLE
test_contexts = {}
for module in modules:
    test_contexts[module] = await mcp__orchestration__get_agent_context({
        "task_id": task_id,
        "agent_type": "test-implementer",
        "module": module
    })

# Launch test implementation with oracle scenarios
test_tasks = []
for module in modules:
    ctx = test_contexts[module]
    test_oracle = ctx.get('test_oracle', {})

    test_tasks.append(Task({
        "subagent_type": "test-implementer",
        "model": ctx.get("suggested_model", "claude-3-5-sonnet-20241022"),
        "prompt": f"""
        Module: {module}

        TEST ORACLE SCENARIOS:
        {json.dumps(test_oracle.get('scenarios', []), indent=2)}

        Edge Cases: {test_oracle.get('edge_cases', [])}
        Security Tests: {test_oracle.get('security_tests', [])}
        Coverage Target: {test_oracle.get('coverage_target', '95%')}

        Similar test patterns:
        {json.dumps(ctx.get('similar_tasks', []), indent=2)}

        Implement comprehensive tests using oracle guidance.
        """
    }))

# Launch ALL test agents in parallel
# Multiple Task calls in ONE message for parallel execution!
```

### Phase 6: Validation
```python
# Get PRISM-enriched validation context
val_context = await mcp__orchestration__get_agent_context({
    "task_id": task_id,
    "agent_type": "validator-master"
})

# Launch validator with full context
await Task({
    "subagent_type": "validator-master",
    "model": val_context.get("suggested_model", "claude-3-5-sonnet-20241022"),
    "prompt": f"""
    Validation context with PRISM insights:
    {json.dumps(val_context, indent=2)}

    Known issues from similar tasks:
    {json.dumps(val_context.get('similar_tasks', []), indent=2)}

    Identify ALL issues. Do not fix anything.
    Check: tests pass, linting, goal alignment.
    """
})

# Track validation outcome for pattern evolution
validation_passed = # determine from validator output
await mcp__orchestration__record_agent_action({
    "task_id": task_id,
    "action": "pattern_outcome",
    "result": {
        "success": validation_passed,
        "patterns_used": [/* patterns from context */],
        "confidence_delta": 0.1 if validation_passed else -0.05
    }
})
```

### Phase 7: Success Validation (NEW)
```python
# Final goal check
await Task({
    "subagent_type": "success-validator",
    "prompt": f"""
    Original goals: {goal_context}
    Completed work: {summary}

    Confirm each success criterion is met.
    Report goal achievement percentage.
    """
})
```

### Phase 8: Completion
```python
# Complete the task and evolve patterns
result = await mcp__orchestration__complete_task({
    "task_id": task_id,
    "commit_changes": True,
    "summary": final_summary
})

# Record final pattern evolution
await mcp__orchestration__record_agent_action({
    "task_id": task_id,
    "action": "task_completed",
    "result": {
        "patterns_promoted": result.get('patterns_promoted', []),
        "lessons_learned": [/* extracted insights */],
        "success_metrics": {
            "goal_achievement": goal_percentage,
            "test_coverage": test_coverage,
            "validation_score": validation_score
        }
    }
})

# Report to user
"✅ Orchestration Complete!
Duration: {result['duration']}
Patterns learned: {result['patterns_promoted']}
Goal achievement: {goal_percentage}%
"
```

## 🔁 Recovery Patterns

### When Agents Fail
```python
if agent_failed:
    # 1. Try with stronger model
    retry_context = await mcp__orchestration__get_agent_context({...})
    await Task({
        "model": "claude-3-opus",  # Upgrade model
        "prompt": f"Previous attempt failed. Context: {retry_context}"
    })

    # 2. If still fails, decompose task
    if still_failed:
        # Break into smaller subtasks
        # Try sequential instead of parallel
```

### When Validation Fails
```python
if validation_failed:
    # 1. Identify specific failures
    # 2. Create targeted fix agents
    # 3. Re-run only failed components
    # 4. Merge fixes carefully
```

## 📈 Adaptive Complexity

Automatically adjust orchestration based on task:

```python
complexity_indicators = {
    "simple": "< 3 files, no new features",
    "medium": "3-10 files, single feature",
    "complex": "10+ files, multiple features",
    "massive": "architectural changes, 20+ files"
}

# Adjust based on complexity:
if complexity == "simple":
    skip_phases = ["parallel_chambers", "goal_alignment_check"]
elif complexity == "massive":
    add_phases = ["risk_assessment", "rollback_planning"]
```

## 🧠 PRISM-Enhanced Intelligence (NEW)

### Task Similarity Matching
- **Finds similar past tasks** to provide context and gotchas
- **Time estimation** based on actual duration of similar tasks
- **Pattern reuse** from highly similar successful tasks

### Confidence-Based Model Selection
Models are automatically selected based on task confidence:
- **Confidence < 0.5**: Claude-3-Opus (complex reasoning)
- **Confidence 0.5-0.7**: Claude-3.5-Sonnet (balanced)
- **Confidence 0.7-0.85**: Claude-3.5-Sonnet (erring on safe side)
- **Confidence > 0.85**: Claude-3-Haiku (fast execution)

### Pattern Evolution
- **Patterns evolve** based on success/failure
- **Confidence grows** with successful uses
- **Automatic promotion/demotion** between memory tiers
- **Living knowledge base** that improves over time

### Test Oracle Generation
For test agents, PRISM automatically:
- **Generates test scenarios** from requirements
- **Identifies edge cases** from similar implementations
- **Suggests security tests** based on patterns
- **Sets coverage targets** appropriate to complexity

## 🎯 Success Metrics

Track and report:
- **Goal Achievement**: % of success criteria met
- **Drift Score**: How much we deviated from original intent
- **Quality Score**: Tests, linting, code quality metrics
- **Performance**: Execution time vs. estimate
- **Learning**: Patterns discovered and promoted
- **Pattern Evolution**: How patterns improved with use

## 💡 Improvements & Recommendations

Consider adding:

1. **Incremental Delivery**: Break massive tasks into deployable increments
2. **Risk Assessment Agent**: Evaluate high-risk changes before implementation
3. **Rollback Planning**: Automatic rollback strategy for risky changes
4. **Performance Budgets**: Set and track performance targets
5. **User Feedback Loops**: Checkpoint with user at key decision points
6. **Learning Memory**: Track what approaches work best for specific task types
7. **Dependency Caching**: Remember common patterns to speed up future tasks
8. **Smart Batching**: Group related changes for atomic commits

## 🔄 Task Decomposition for Large Tasks

### When to Decompose

Tasks are automatically analyzed for decomposition when they contain:
- "complete", "entire", "full", "platform", "system"
- Multiple major components (e.g., "auth, products, checkout")
- Estimated >30 minutes of orchestration time

### Decomposition Flow

```mermaid
graph TD
    A[Large Task Request] --> B[task-decomposer Analyzes]
    B --> C{Needs Decomposition?}
    C -->|No| D[Regular /conduct]
    C -->|Yes| E[Create Sub-task Queue]
    E --> F[master-orchestrator Takes Over]
    F --> G[Execute Sub-task 1 - Full Orchestration]
    G --> H[Validate Checkpoint]
    H -->|Pass| I[Execute Sub-task 2 - Full Orchestration]
    H -->|Fail| J[Fix and Retry Sub-task 1]
    I --> K[Validate Checkpoint]
    K --> L[Continue Until All Complete]
```

### Sequential Sub-task Execution

**IMPORTANT**: Sub-tasks run SEQUENTIALLY, not in parallel:

1. **Sub-task 1 completes FULLY** (skeleton → implementation → test → beauty)
2. **Checkpoint validated** (e.g., "Models work")
3. **Only then Sub-task 2 begins**
4. **Each sub-task can use parallel agents internally**
5. **But sub-tasks themselves are sequential**

### Example Decomposition

```python
# User request: "Build complete e-commerce platform"

# Step 1: Decompose into sub-tasks
decomposition = mcp__orchestration__decompose_task({
    "task_id": "master_123",
    "description": "Build complete e-commerce platform with user management, products, cart, and checkout",
    "strategy": "vertical_slices"  # Each slice is valuable
})

# Returns 5 sequential sub-tasks:
# 1. Foundation (models, structure)
# 2. Authentication (register, login, JWT)
# 3. Product catalog (CRUD, search)
# 4. Shopping cart (persistence)
# 5. Checkout (payment, orders)

# Step 2: Master orchestrator executes sequentially
while has_next_subtask:
    subtask = mcp__orchestration__get_next_subtask({"master_task_id": "master_123"})

    # Run FULL orchestration for this sub-task
    Task(
        prompt=f"Complete orchestration for: {subtask['orchestration_prompt']}",
        subagent_type="conductor"
    )

    # Validate checkpoint
    checkpoint = mcp__orchestration__validate_checkpoint({
        "checkpoint_description": subtask["checkpoint"],
        "subtask_id": subtask["id"],
        "test_commands": ["pytest tests/", "python validate.py"]
    })

    if checkpoint["passed"]:
        mcp__orchestration__complete_subtask({
            "master_task_id": "master_123",
            "subtask_id": subtask["id"],
            "checkpoint_result": checkpoint
        })
    else:
        # Fix and retry - don't proceed until fixed
        fix_subtask(subtask, checkpoint["error"])
```

### Progress Tracking

```python
# Check overall progress
status = mcp__orchestration__get_decomposition_status({
    "master_task_id": "master_123"
})

# Shows:
# - Total sub-tasks: 5
# - Completed: 2
# - Current: "product_catalog"
# - Progress: 40%
# - Estimated remaining: 40-60 minutes
```

### Benefits of Decomposition

1. **Failure Recovery** - Only retry failed sub-task, not everything
2. **Clear Progress** - User sees steady advancement
3. **Memory Efficient** - Smaller context per sub-task
4. **Checkpoint Validation** - Each piece verified before proceeding
5. **No Cascade Failures** - Issues caught early and fixed

### Decomposition Strategies

1. **Vertical Slices** (Default)
   - Each sub-task delivers end-to-end value
   - Example: "Users can register/login" → "Users can browse" → "Users can buy"

2. **Horizontal Layers**
   - Each sub-task completes a technical layer
   - Example: "All models" → "All APIs" → "All UI"

3. **Progressive Enhancement**
   - Each sub-task adds sophistication
   - Example: "Basic CRUD" → "Add validation" → "Add caching"

## 🚀 Quick Start Examples

```bash
# Simple refactor
/conduct "refactor the auth module to use JWT"

# Complex feature
/conduct "implement real-time collaboration with WebSockets"

# Massive architectural change
/conduct "migrate from monolith to microservices"
```

## 📝 Command Summary

- `/conduct "description"` - Start orchestrating a complex task
- `/conduct status` - Check current orchestration progress
- `/conduct abort` - Cancel current orchestration (cleanup chambers)
- `/conduct complete` - Force completion with current state
- `/conduct retry [phase]` - Retry a specific phase

## 🎨 Beauty Standards Integration

### When Beauty Pass Occurs:
1. **After Implementation** - Code works but may be ugly
2. **After Fix Loops** - Fixes may introduce complexity
3. **Before Final Validation** - Ensure production quality

### Beauty Workflow:
```python
# 1. Analyze current beauty
beauty_analysis = mcp__orchestration__analyze_code_beauty({
    "file_path": "src/services/user_service.py",
    "code_content": file_content
})

# 2. If beauty score < 8.0, beautify (max 2 passes)
if beauty_analysis["beauty_score"] < 8.0:
    Task(
        prompt=f"Beautify code to be obvious and self-documenting. Issues: {beauty_analysis['issues']}",
        subagent_type="code-beautifier"
    )

# 3. Record beauty improvements
mcp__orchestration__record_validation_result({
    "task_id": task_id,
    "module": "services",
    "test_type": "beauty",
    "passed": True,
    "details": {
        "before_score": 6.5,
        "after_score": 8.7,
        "improvements": ["Extracted complex conditionals", "Removed micro-functions", "Applied guard clauses"]
    }
})
```

### Beauty Gates to Check:
- **post_skeleton**: Functions sized appropriately (20-50 lines)
- **post_implementation**: Code is self-documenting
- **post_beauty**: DRY compliance, no wrappers, beauty score ≥ 8.0
- **post_testing**: Beauty maintained after all changes

### Beauty Principles Enforced:
1. **No Micro-Functions** - Functions < 10 lines are combined
2. **No Giant Functions** - Functions > 50 lines are split (unless cohesive)
3. **DRY Compliance** - Patterns repeated 3+ times are extracted
4. **Self-Documenting** - Names make comments unnecessary
5. **Guard Clauses** - Early returns over nested ifs
6. **No Pointless Wrappers** - Every function adds value

## ⚠️ Remember

1. **YOU fetch context** - Sub-agents can't call MCP tools
2. **Check goals frequently** - Prevent drift from user intent
3. **Report progress** - Keep user informed
4. **Learn from patterns** - MCP stores successful approaches
5. **Fail loud** - Better to stop than proceed incorrectly
6. **Beauty matters** - Code should be obvious to read, not clever
7. **Test after beautifying** - Ensure beauty doesn't break functionality

The orchestration MCP server handles the complexity. You just coordinate the flow!