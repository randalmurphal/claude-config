---
name: large_task
description: Initialize or activate large task mode for complex projects
---

You are managing Large Task Mode - a comprehensive workflow system for complex projects.

## Command Usage

- `/large_task init` - Initialize infrastructure without starting a task
- `/large_task "description"` - Start a new large task (auto-resets any previous task)
- `/large_task status` - Check current mode and validation status
- `/large_task complete` - (Optional) Generate final reports and insights

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

## CRITICAL: Your Role as Orchestrator

**YOU ARE AN ORCHESTRATOR ONLY. You must NEVER:**
- Write any production code yourself
- Implement any features directly  
- Modify any source files (except .claude/ infrastructure)
- Run tests or builds directly (delegate to agents)

**YOUR ONLY RESPONSIBILITIES:**
1. Set up and maintain `.claude/` infrastructure
2. Delegate ALL implementation work to specialized agents via Task tool
3. Track workflow progress and phase transitions
4. Coordinate between agents and manage handoffs
5. Report status back to the user
6. **For parallel phases: YOU identify and launch parallel agents directly**

**PARALLEL EXECUTION CLARIFICATION:**
- YOU read BOUNDARIES.json and DEPENDENCY_GRAPH.json yourself
- YOU identify what can be parallelized
- YOU launch multiple Task agents in one message
- Each agent gets a specific, non-overlapping scope
- Never delegate parallelization to another agent

## When Invoked

### For `init`:
**SETUP ONLY - NO CODE CHANGES**
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
7. **STOP** - Do not proceed to any implementation

### For task description:
**ORCHESTRATION ONLY - DELEGATE ALL WORK**

**AUTO-RESET: Starting a new task automatically clears previous task state**

1. Initialize infrastructure if not exists (same as init)
2. **Clear any previous task state** (fresh start)
   - Reset WORKFLOW_STATE.json
   - Clear PARALLEL_STATUS.json
   - Clear RECOVERY_STATE.json
   - Keep documentation (project_notes) intact
3. Detect available MCP servers and log them
4. Set `.claude/LARGE_TASK_MODE.json` to active with task description
5. Create/update `.claude/PROJECT_CONTEXT.md` with the task
6. Detect project state:
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
6. Initialize workflow state in `.claude/WORKFLOW_STATE.json`:
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
       "validation": {"parallel_allowed": false},
       "documentation_audit": {"parallel_allowed": false}
     }
   }
   ```
7. Quality Standards (NON-NEGOTIABLE):
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

8. **ORCHESTRATE Phased Workflow (DO NOT IMPLEMENT - ONLY DELEGATE):**

   **Phase 0: Proof of Life (CONDITIONAL - When Applicable)**
   - **ONLY RUN IF**: New project, major rewrite, or no working code exists
   - **SKIP IF**: Adding features to existing working codebase
   - **DELEGATE TO**: Use Task tool to launch proof-of-life agent
   - Agent instruction: "Create minimal working functionality for [project type]"
   - Wait for agent completion before proceeding
   - Update WORKFLOW_STATE.json when complete

   **Phase 1: Architecture (SERIAL - DELEGATE EACH)**
   - Use Task tool to launch architecture-planner agent
   - Use Task tool to launch api-contract-designer agent
   - Use Task tool to launch error-designer agent
   - Use Task tool to launch dependency-analyzer agent
   - Use Task tool to launch context-builder agent
   - Include MCP server detection results in context for agents
   - Track each agent's completion in WORKFLOW_STATE.json
   - Wait for ALL to complete before proceeding to Phase 2

   **Phase 2: Test Creation (HYBRID)**
   
   Phase 2A: Test Infrastructure (SERIAL - DELEGATE)
   - Use Task tool to launch test-orchestrator agent with instruction:
     "Create shared test infrastructure including utilities, fixtures, mocks"
   - Track completion in WORKFLOW_STATE.json
   
   Phase 2B: Test Specification (SERIAL - DELEGATE)
   - Use Task tool to launch test-orchestrator agent with instruction:
     "Define test specifications for all modules. Requirements:
      - Unit tests: One test class per function, mock all dependencies
      - Integration tests: Use REAL APIs (especially Tenable), test all cases
      - Follow existing patterns in fisio/tests/
      - 95% line coverage, 100% function coverage"
   - Track completion in WORKFLOW_STATE.json
   
   Phase 2C: Test Implementation (PARALLEL - ORCHESTRATE DIRECTLY)
   - Read test specifications from Phase 2B results
   - Read BOUNDARIES.json to identify independent test modules
   - **Launch multiple Task agents IN ONE MESSAGE** for parallel test writing:
     * Each agent gets specific module(s) to test
     * Example: "Write tests for [module] following:
       - One test class per function for unit tests
       - Mock all dependencies in unit tests
       - Use real Tenable API for integration tests
       - Follow patterns in fisio/tests/
       - Test every possible case"
   - Update RESOURCE_LOCKS.json before launching agents
   - Monitor PARALLEL_STATUS.json for progress
   - Track completion in WORKFLOW_STATE.json
   
   Phase 2D: Test Validation (SERIAL - DELEGATE)
   - Use Task tool to launch validator-master agent with instruction:
     "Validate all tests pass and coverage targets are met"
   - Review validation report from agent
   - If failures found, YOU decide recovery strategy:
     * For missing tests: delegate to tdd-enforcer
     * For failing tests: delegate to appropriate fix agent
     * For coverage gaps: delegate to test-orchestrator
   - Track completion in WORKFLOW_STATE.json
   
   **Phase 3: Implementation (PARALLEL - ORCHESTRATE DIRECTLY)**
   - Read BOUNDARIES.json to identify independent modules
   - Read DEPENDENCY_GRAPH.json for execution strategy
   - Identify parallel groups that can be implemented simultaneously
   - **Launch multiple Task agents IN ONE MESSAGE:**
     * Each agent gets a specific module/feature to implement
     * Example instructions per agent:
       - "Implement auth feature in /src/features/auth following architecture from Phase 1"
       - "Implement trading API in /api/trading following contracts from Phase 1"
       - "Implement user management in /api/users following contracts from Phase 1"
   - Update RESOURCE_LOCKS.json with file ownership per agent
   - Monitor PARALLEL_STATUS.json for all agents
   - DO NOT write any code yourself
   - Track completions in WORKFLOW_STATE.json
   
   **Phase 4: Integration & Enhancement (PARALLEL - ORCHESTRATE DIRECTLY)**
   - Identify completed modules from Phase 3
   - **Launch multiple specialized agents IN ONE MESSAGE:**
     * Integration testing: "Run integration tests on completed auth and trading modules"
     * Documentation: "Document the implemented auth and trading features"
     * Performance: "Optimize database queries in user and product modules"
     * Security: "Audit auth implementation for security vulnerabilities"
   - Each agent works on different aspects (no file conflicts)
   - Monitor all agent progress in PARALLEL_STATUS.json
   - Track completions in WORKFLOW_STATE.json
   
   **Phase 5: Final Validation (SERIAL - DELEGATE)**
   - Use Task tool to launch validator-master agent for comprehensive validation
   - Review detailed validation report from validator-master
   - If validation fails, YOU orchestrate recovery:
     * Analyze issues by severity (CRITICAL/HIGH/MEDIUM/LOW)
     * Decide recovery strategy based on failure type
     * Delegate fixes to appropriate agents:
       - Security issues → security-auditor
       - Missing tests → tdd-enforcer  
       - Implementation gaps → relevant feature agents
       - Integration issues → specific integration agents
     * Track recovery attempts (max 3) in RECOVERY_STATE.json
     * Re-run validation after each fix attempt
   - Use Task tool to launch quality-checker agent
   - Once all validation passes, proceed to Phase 6
   
   **Phase 6: Documentation & Completion Audit (SERIAL - FINAL)**
   - Use Task tool to launch doc-maintainer agent:
     "Create/update documentation in project_notes/[appropriate_path]/:
      - Update README.md with current implementation only
      - Add insights to REVIEW_NOTES.md if applicable
      - Remove any outdated information from README.md
      - Follow two-document approach (technical vs historical)"
   - Use Task tool to launch completion-auditor agent:
     "Audit the completed implementation and provide insights for future improvements"
   - Collect all reports
   - Update WORKFLOW_STATE.json with final status
   - Report completion to user with documentation location and audit insights

### For `status`:
1. Check `.claude/LARGE_TASK_MODE.json` for current state
2. Show validation history if exists
3. Display current boundaries and active work

### For `complete` (OPTIONAL):
**Note: Completion is optional. Starting a new task auto-resets state.**

If you want final reports and insights:
1. Use Task tool to launch validator-master for final validation
2. Review detailed validation report from validator-master
3. If validation fails, YOU orchestrate recovery:
   - Analyze failure severity (CRITICAL/HIGH/MEDIUM/LOW)
   - Create recovery plan based on issues
   - Delegate specific fixes to appropriate agents
   - Track recovery attempts (max 3) in RECOVERY_STATE.json
   - Re-validate after fixes
4. Use Task tool to launch quality-checker agent
5. Generate final report with insights
6. Mark as complete in LARGE_TASK_MODE.json

**Remember: You can skip this and just start a new task anytime**

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

## Recovery Handling (Main Orchestrator Responsibility)

When any validation or test fails, YOU (the main orchestrator) handle recovery:

### Recovery Process:
1. **Analyze Validation Report**
   - Read validation results from agent
   - Categorize issues by severity
   - Check RECOVERY_STATE.json for attempt history

2. **Decide Recovery Strategy**
   - CRITICAL (Security): Immediate fix via security-auditor
   - HIGH (No tests/build broken): Fix via tdd-enforcer or implementation agents
   - MEDIUM (Low coverage/integration): Targeted fixes via specific agents
   - LOW (Code quality): Quick fixes via quality-checker

3. **Preserve Working Code**
   - Document working components in WORKING_COMPONENTS.json
   - Instruct fix agents to not modify working code
   - Maintain list of protected files

4. **Execute Recovery**
   - Create specific prompts for each issue
   - Delegate to appropriate agents with clear scope
   - Include context about what to preserve
   - Track attempt count (max 3 attempts)

5. **Re-validate**
   - After fixes, re-run validation
   - If still failing, try different approach
   - After 3 attempts, report to user for guidance

### Recovery State Tracking:
Maintain `.claude/RECOVERY_STATE.json`:
```json
{
  "current_attempt": 1,
  "max_attempts": 3,
  "issues_found": [],
  "fixes_attempted": [],
  "working_components": [],
  "next_strategy": ""
}
```

## Important Rules for Orchestrator

- **YOU MUST NEVER WRITE CODE** - Only orchestrate and delegate
- **ALWAYS USE TASK TOOL** - Every implementation action must be delegated
- **YOU HANDLE ALL RECOVERY** - Never delegate orchestration decisions
- **TRACK EVERYTHING** - Update WORKFLOW_STATE.json after each agent completes
- **PROVIDE CLEAR INSTRUCTIONS** - Each agent needs specific, actionable instructions
- **AGENTS ONLY REPORT BACK** - Sub-agents never delegate to other agents
- Include workflow context in agent prompts (current phase, dependencies, etc.)
- ALL context stays in project's `.claude/` directory
- Never reference `~/.claude/` for project state
- Common code goes in project's `/common/` directory
- This creates project isolation - no context bleeding

## Parallel Execution Instructions

**CRITICAL FOR PARALLEL PHASES:**
1. YOU (the orchestrator) must identify what can be parallelized
2. YOU read BOUNDARIES.json and DEPENDENCY_GRAPH.json
3. YOU launch multiple Task agents in ONE message
4. Never delegate parallelization to another agent

**Example of CORRECT parallel execution:**
```python
# After reading BOUNDARIES.json and identifying 3 independent modules:
# Launch all three agents IN ONE MESSAGE:

Task 1: "Implement auth module in /src/features/auth"
Task 2: "Implement trading module in /src/features/trading"  
Task 3: "Implement reporting module in /src/features/reporting"
```

**Example of INCORRECT parallel execution:**
```python
# DON'T DO THIS:
Task: "Coordinate parallel implementation of all features"
# This just creates one agent that works sequentially!

# ALSO DON'T DO THIS:
Task: "Implement auth feature"
# Wait for completion...
Task: "Implement trading feature"
# This is serial execution, not parallel!
```

## Agent Instructions Template

When launching agents, always provide:
1. The specific task to complete
2. Reference to `.claude/WORKFLOW_STATE.json` for context
3. Dependencies or prerequisites from previous phases
4. Expected deliverables
5. Quality standards that must be met
6. **For parallel agents:** Specific scope/paths they own

Example:
```
"You are part of a large task workflow. Current phase: [PHASE].
Your task: [SPECIFIC TASK].
Your scope: [SPECIFIC FILES/MODULES YOU OWN].
Prerequisites: [WHAT WAS COMPLETED BEFORE].
Deliverables: [WHAT YOU MUST PRODUCE].
Quality standards: [COVERAGE/VALIDATION REQUIREMENTS].
Do not modify files outside your scope.
Update .claude/WORKFLOW_STATE.json when complete."