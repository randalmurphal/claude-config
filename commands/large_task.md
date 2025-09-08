---
name: large_task
description: Initialize or activate large task mode for complex projects
---

You are managing Large Task Mode - a comprehensive workflow system for complex projects.

## Command Usage

- `/large_task init` - Initialize infrastructure without starting a task
- `/large_task "description"` - Start a new large task with description
- `/large_task status` - Check current mode and validation status
- `/large_task complete` - Complete and deactivate mode

## MCP Server Auto-Detection

When starting a task, automatically detect and suggest relevant MCP servers:

```python
def detect_mcp_servers(project_path):
    available_mcp = []
    
    # Check package.json for Node dependencies
    if os.path.exists("package.json"):
        with open("package.json") as f:
            pkg = json.load(f)
            deps = pkg.get("dependencies", {}) | pkg.get("devDependencies", {})
            
            if "mongodb" in deps or "mongoose" in deps:
                available_mcp.append("mongodb")
            if "pg" in deps or "postgres" in deps:
                available_mcp.append("postgres")
            if "@playwright/test" in deps:
                available_mcp.append("playwright")
    
    # Check Python requirements
    if os.path.exists("requirements.txt"):
        with open("requirements.txt") as f:
            reqs = f.read()
            if "pymongo" in reqs:
                available_mcp.append("mongodb")
            if "psycopg2" in reqs or "sqlalchemy" in reqs:
                available_mcp.append("postgres")
    
    # Check for API documentation
    if os.path.exists("openapi.yaml") or os.path.exists("swagger.json"):
        available_mcp.append("apidog")
    
    # Check .mcp.json for project-specific servers
    if os.path.exists(".mcp.json"):
        with open(".mcp.json") as f:
            mcp_config = json.load(f)
            available_mcp.extend(mcp_config.get("mcpServers", {}).keys())
    
    return available_mcp
```

## When Invoked

### For `init`:
1. Check if you're in a project directory (has .git or is a clear project folder)
2. Create `.claude/` directory structure in current project
3. Copy validator templates from `~/.claude/templates/` to `.claude/validators/`:
   - base_validator.py
   - pre_tool_validator.py
   - code_quality_validator.py
   - error_handling_validator.py
   - api_contract_validator.py
   - documentation_validator.py
   - security_validator.py
   - prompt_analyzer.py
   - session_start_hook.py
4. Create initial configuration files:
   - `.claude/LARGE_TASK_MODE.json` with status "ready"
   - `.claude/BOUNDARIES.json` with initial structure
   - `.claude/PROJECT_CONTEXT.md` with project overview
5. Set up project-local hooks in `.claude/settings.local.json`
6. Inform user that project is ready for automatic workflow activation

### For task description:
1. Initialize infrastructure if not exists (same as init)
2. Detect available MCP servers and log them
3. Set `.claude/LARGE_TASK_MODE.json` to active with task description
3. Create/update `.claude/PROJECT_CONTEXT.md` with the task
4. Detect project state:
   ```python
   # Determine if Proof of Life needed
   project_state = detect_project_state()
   if project_state == "new_project":
       start_phase = "proof_of_life"
   elif project_state == "broken_project":
       start_phase = "proof_of_life"  
   elif project_state == "working_project":
       start_phase = "architecture"  # Skip proof of life
   ```
5. Initialize workflow state in `.claude/WORKFLOW_STATE.json`:
   ```json
   {
     "current_phase": "architecture",
     "current_subphase": null,
     "completed_phases": [],
     "completed_subphases": [],
     "active_parallel_tasks": [],
     "synchronization_points": [],
     "phase_details": {
       "proof_of_life": {"parallel_allowed": false},
       "architecture": {"parallel_allowed": false},
       "test_2a_infrastructure": {"parallel_allowed": false},
       "test_2b_specification": {"parallel_allowed": false},
       "test_2c_implementation": {"parallel_allowed": true},
       "test_2d_validation": {"parallel_allowed": false},
       "implementation": {"parallel_allowed": true},
       "integration": {"parallel_allowed": true},
       "validation": {"parallel_allowed": false}
     }
   }
   ```
5. Quality Standards (NON-NEGOTIABLE):
   ```yaml
   test_coverage:
     lines: 95%         # Must cover 95% of code lines
     branches: 90%      # Must test 90% of conditionals  
     functions: 100%    # EVERY function must be tested
     statements: 95%    # Nearly all statements covered
   
   critical_coverage:
     error_handling: 100%   # ALL error paths must be tested
     edge_cases: 100%       # ALL edge cases must be covered
     security_code: 100%    # ALL auth/security code tested
     validations: 100%      # ALL input validation tested
   
   quality_validation:
     tool: ~/.claude/quality-tools/scripts/quick-validate.sh
     frequency: After each phase
     blocking: Failures prevent phase completion
   ```

6. Execute Phased Workflow:

   **Phase 0: Proof of Life (CONDITIONAL - When Applicable)**
   - **ONLY RUN IF**: New project, major rewrite, or no working code exists
   - **SKIP IF**: Adding features to existing working codebase
   - When run: Create minimal working functionality
   - Adapt to project type (script, service, processor, etc.)
   - Must produce real, verifiable output
   - Creates foundation all other work extends

   **Phase 1: Architecture (SERIAL)**
   - Run architecture-planner to define `/common/` structure
   - Run api-contract-designer for API contracts
   - Run error-designer for error hierarchy
   - Run dependency-analyzer to map real dependencies
   - Run context-builder to initialize critical context tracking
   - Check available MCP servers and include in context
   - Wait for ALL to complete before proceeding

   **Phase 2: Test Creation (HYBRID)**
   
   Phase 2A: Test Infrastructure (SERIAL)
   - Run test-orchestrator to create shared test utilities
   - Define test fixtures, mocks, and factories
   - Establish test patterns and configuration
   
   Phase 2B: Test Specification (SERIAL)
   - Run test-orchestrator to define what to test
   - Create detailed test specifications per module
   - Set coverage targets and requirements
   
   Phase 2C: Test Implementation (PARALLEL)
   - Run parallel-task-dispatcher for test writing
   - Multiple agents implement tests from specs
   - Each agent uses shared test infrastructure
   
   Phase 2D: Test Validation (SERIAL)
   - Validate all tests pass
   - Verify coverage targets met
   - Ensure pattern consistency
   
   **Phase 3: Implementation (PARALLEL)**
   - Run parallel-task-dispatcher to:
     - Analyze BOUNDARIES.json for independent modules
     - Launch parallel agents for non-conflicting work
     - Track execution in PARALLEL_STATUS.json
   
   **Phase 4: Integration & Enhancement (PARALLEL)**
   - Run parallel validation and enhancement:
     - Integration testing on completed modules
     - Documentation updates
     - Performance optimization
   
   **Phase 5: Final Validation (SERIAL)**
   - Run validator-master for comprehensive validation
   - Run quality-checker with ~/.claude/quality-tools
   - Generate final reports

### For `status`:
1. Check `.claude/LARGE_TASK_MODE.json` for current state
2. Show validation history if exists
3. Display current boundaries and active work

### For `complete`:
1. Run validator-master for final validation
2. Run quality-checker using ~/.claude/quality-tools
3. If passed: deactivate mode, generate report
4. If failed: show failures, ask user to continue or force complete

## Project Structure Created

```
.claude/
├── validators/              # Project-specific validators
├── hooks/                  # Project-specific hooks
├── protocols/              # Work protocols
├── context/                # Progressive context tracking
│   ├── CRITICAL_CONTEXT.json    # Current task critical decisions
│   ├── PERSISTENT_GOTCHAS.json  # Cross-task gotchas
│   └── archive/                 # Historical contexts
├── LARGE_TASK_MODE.json    # Mode state
├── WORKFLOW_STATE.json     # Current workflow phase & progress
├── PROJECT_CONTEXT.md      # Human-readable progress
├── BOUNDARIES.json         # Work zones with parallel safety flags
├── DEPENDENCY_GRAPH.json  # Real dependency analysis
├── ACTIVE_WORK.json       # Current activity
├── PARALLEL_STATUS.json   # Parallel execution tracking
├── RESOURCE_LOCKS.json    # File-level lock tracking
├── COMMON_REGISTRY.json   # Common code tracking
└── VALIDATION_HISTORY.json # Validation log
```

## Important

- ALL context stays in project's `.claude/` directory
- Never reference `~/.claude/` for project state
- Common code goes in project's `/common/` directory
- This creates project isolation - no context bleeding