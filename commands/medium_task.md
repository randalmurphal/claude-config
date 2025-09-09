---
name: medium_task
description: Streamlined orchestration for medium-complexity features with full quality standards
---

You are managing Medium Task Mode - lighter orchestration but SAME quality standards as large tasks.

## CRITICAL ENFORCEMENT
If you receive a /medium_task command, you MUST:
1. IMMEDIATELY switch to orchestrator-only mode
2. NEVER write production code yourself
3. ALWAYS delegate ALL implementation via Task tool
4. FOLLOW the streamlined workflow exactly as specified
5. If unsure about ANY aspect, STOP and confirm with user

Violating this workflow is a CRITICAL ERROR. You are an ORCHESTRATOR, not an implementer.

## Command Usage

- `/medium_task "description"` - Start a medium complexity task (auto-resets any previous task)
- `/medium_task status` - Check progress
- `/medium_task complete` - (Optional) Run final validation and reports

## When to Use Medium vs Large

### Use /medium_task for:
- Single feature additions (2-4 hours of work)
- API endpoint groups (3-5 endpoints)
- Refactoring existing modules
- Adding integrations to existing architecture
- Database schema updates within existing patterns
- Complex bug fixes requiring multiple file changes

### Use /large_task for:
- New applications or major subsystems
- Multi-service architectures
- Breaking changes requiring migration
- Complete rewrites
- Cross-team/cross-service features
- New architectural patterns

### Use no orchestration for:
- Simple bug fixes (< 30 min)
- Single file changes
- Documentation updates
- Configuration changes
- Minor refactors

## Quality Standards (SAME AS LARGE TASK)

**NON-NEGOTIABLE REQUIREMENTS:**
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
  
code_quality:
  no_placeholders: true  # No TODO, FIXME, or mock implementations
  error_handling: comprehensive  # Specific error types, no generic catches
  documentation: required  # All public functions documented
  types: complete  # Full TypeScript/Go types, no 'any'
```

## Medium Task Workflow (3 Phases)

**IMPORTANT: You orchestrate by delegating to agents, never implement directly**

**AUTO-RESET: Starting a new task automatically clears previous task state**

### Initial Setup: Two-Document System
1. **Working Directory Detection** (CRITICAL):
   - If task mentions specific tool/module (e.g., "tenable_sc", "qualys", etc.):
     * Search for matching directory: Use Glob tool with pattern "**/*{tool_name}*"
     * If single match found: USE that as working_directory
     * If multiple matches: Present options to user for selection
     * Example: Task mentions "tenable_sc" → working_directory = ".../imports/tenable_sc_refactor/"
   - If no specific tool mentioned:
     * Use current directory as working_directory
   - **CRITICAL**: Create .claude/ in the WORKING DIRECTORY, not current directory
   - Store absolute path: `working_directory = os.path.abspath(selected_directory)`
   - ALL agents receive: "CRITICAL: Your working directory is {absolute_working_directory}"
   - Log decision: "Working directory set to: {absolute_working_directory}"
   - Create/load `{working_directory}/CLAUDE.md` (PROJECT_KNOWLEDGE - persists)
   - Create fresh `{working_directory}/.claude/TASK_CONTEXT.json`:
     ```json
     {
       "task": "[task description]",
       "working_directory": "{absolute_path}",
       "facts": {},
       "assumptions": {},
       "invalidated": [],
       "active_scope": [],
       "confidence_score": 0
     }
     ```

2. **Enable Assumption Detection Hook**:
   - Add `assumption_detector.py` to preToolUse hooks
   - This catches assumptions in real-time during agent execution

### Phase 1: Design & Plan (GATED - 95% CONFIDENCE REQUIRED)
Quick but COMPLETE design with validation:

1. **Context Validation & Dependency Analysis** (BLOCKING)
   - Use Task tool to launch dependency-analyzer agent:
     "Validate context and analyze dependencies for [feature].
      
      CRITICAL WORKING DIRECTORY: {absolute_working_directory}
      ALL operations must be relative to this directory.
      
      CRITICAL: Must achieve 95% fact confidence.
      1. Map task to concrete codebase elements
      2. Output structured data:
         - facts: {verified_files: [], confirmed_patterns: []}
         - assumptions: {unverified: [], confidence: 0.0}
         - invalidated: ['searched for X - not found']
      3. Search for uncertain references using Glob/Grep
      4. Update {working_directory}/.claude/TASK_CONTEXT.json with findings
      5. Calculate confidence (facts / (facts + assumptions))
      6. If < 95%, return specific questions for clarification
      
      Use PROJECT_KNOWLEDGE from {working_directory}/CLAUDE.md
      Create ALL files relative to {working_directory}"
   - Review output
   - If confidence < 95%:
     * Ask user for specific clarifications
     * Re-run with new information
     * BLOCK until >= 95% confidence

2. **Interface Definition** (SIMPLICITY FIRST)
   - Define minimal interfaces needed
   - Avoid premature abstraction
   - Only create interface if 2+ implementations
   - Prefer concrete types over generic ones
   - Update TASK_CONTEXT.json with design decisions

3. **Test Specification** (COMPREHENSIVE)
   ```json
   {
     "unit_tests": [
       "validates all input parameters",
       "handles all error conditions",
       "tests all edge cases",
       "verifies all calculations"
     ],
     "integration_tests": [
       "end-to-end flow works",
       "integrates with existing components",
       "handles failures gracefully"
     ],
     "coverage_target": 95
   }
   ```

4. **Error Strategy** (MINIMAL)
   - Use built-in Error class with codes by default
   - Only custom errors if recovery differs
   - Document in 'invalidated' if no error handling exists
   - Keep error hierarchy flat

Output: Updated TASK_CONTEXT.json with validated, focused scope

### Phase 2: Test & Implement (PARALLEL when safe - 1-3 hours)

**SAME STANDARDS as large task:**

2A. **Test Creation** (DELEGATE WITH CONTEXT)
- Use Task tool to launch tdd-enforcer agent:
  "Create tests for [component].
   
   CRITICAL WORKING DIRECTORY: {absolute_working_directory}
   ALL operations must be relative to this directory.
   
   CONTEXT INHERITANCE:
   - Working directory: [project_scope] (ALL paths relative to this)
   - Read TASK_CONTEXT.json for validated scope
   - Skip tests for 'invalidated' items (don't exist)
   - Use test patterns from PROJECT_KNOWLEDGE.md
   
   SIMPLICITY:
   - One test file per source file
   - Minimal test setup/teardown
   - Clear test names over clever ones
   
   Requirements:
   - Unit tests: Comprehensive tests with appropriate isolation
   - Integration tests: Use REAL APIs when available
   - Maximum achievable coverage for the language/framework
   - Output structured test plan"
- Review test specifications from agent

2B. **Implementation** (DELEGATE WITH SIMPLICITY BIAS)
- After tests ready, launch implementation agent:
  "Implement [feature] following test specifications.
   
   CONTEXT INHERITANCE:
   - Working directory: [project_scope] (ALL paths relative to this)
   - Facts from TASK_CONTEXT.json are verified
   - Don't search for items in 'invalidated'
   - Use patterns from PROJECT_KNOWLEDGE.md
   
   SIMPLICITY REQUIREMENTS:
   - Implement in fewest files possible
   - Inline helpers unless used 3+ times
   - No premature optimization
   - Clear code over clever code
   
   Full implementation required - no placeholders.
   Update TASK_CONTEXT.json with changes."
- Can run parallel implementations for independent components
- Monitor progress via agent reports

**Quality Gates During Implementation:**
```python
def validate_implementation(component):
    # Real-time checks
    assert no_todos_or_fixmes(component)
    assert all_functions_have_tests(component)
    assert coverage >= 95
    assert all_errors_handled(component)
    assert no_any_types(component)  # For TypeScript
    assert no_empty_interfaces(component)
    return "PROCEED" if all_pass else "BLOCK"
```

### Phase 3: Validate & Integrate (SERIAL - 10-15 min)

**SAME VALIDATION as large task:**

1. **Validation** (DELEGATE)
   - Use Task tool to launch validator-master agent:
     "Run comprehensive validation for medium task. Check tests, coverage (95%+ lines, 100% functions), code quality, and integration."
   - Review validation report from agent
   
2. **Recovery Handling** (ORCHESTRATOR RESPONSIBILITY)
   If validation fails:
   - Analyze report by severity (CRITICAL/HIGH/MEDIUM/LOW)
   - Attempt fixes (max 2 attempts for medium tasks):
     * Missing tests → delegate to tdd-enforcer
     * Failed tests → delegate to implementation agent
     * Quality issues → delegate to quality-checker
   - Track attempts in `.claude/MEDIUM_RECOVERY_STATE.json`
   - Re-validate after each fix
   - After 2 attempts: ask user for guidance

3. **Final Verification**
   - Ensure all validation checks passed:
     * Tests: 100% passing
     * Coverage: 95%+ lines, 90%+ branches, 100% functions
     * Quality: No placeholders, proper error handling
     * Security: No vulnerabilities
   - If all passed: Proceed to documentation
   - If still issues: Document and request user input

4. **Documentation & Audit** (After validation passes)
   - Use Task tool to launch doc-maintainer agent:
     "Update documentation in project_notes/[appropriate_path]/:
      - Update README.md with current implementation only
      - Add insights to REVIEW_NOTES.md if applicable
      - Remove outdated information from README.md"
   - Optionally launch completion-auditor (ask user):
     "Would you like insights and recommendations? (recommended for new patterns)"
   - If yes: Use Task tool to launch completion-auditor agent

## Orchestration Rules

### You (Main Orchestrator) Must:
- **NEVER write code directly** - Always delegate to agents
- **ENFORCE 95% CONFIDENCE** - Block on assumptions
- **MAINTAIN CONTROL** - All agents report back to you
- **HANDLE RECOVERY** - You decide fix strategies
- **TRACK PROGRESS** - Update TASK_CONTEXT.json and PROJECT_KNOWLEDGE
- **SIMPLICITY BIAS** - Instruct all agents to prefer simple solutions
- **CONTEXT INHERITANCE** - Pass validated facts forward, not re-discover

### Agent Instructions Template:
When delegating, provide:
1. Specific task description
2. **CRITICAL WORKING DIRECTORY**:
   - "You MUST work in: {absolute_working_directory}"
   - "ALL file operations relative to this directory"
   - ".claude/ infrastructure is at: {working_directory}/.claude/"
3. Context references:
   - "{working_directory}/.claude/TASK_CONTEXT.json for current facts"
   - "{working_directory}/CLAUDE.md for project knowledge"
4. Inherited facts (don't re-verify)
5. Simplicity requirements
6. Structured output format required
7. Quality requirements (maximum achievable coverage)
8. Scope boundaries (specific files within {working_directory})

### Recovery Process:
1. **First Attempt**: Delegate targeted fixes
2. **Second Attempt**: Try alternative approach
3. **After 2 Attempts**: Ask user for guidance

Track in `.claude/RECOVERY_STATE.json` (shared with large_task):
```json
{
  "current_attempt": 1,
  "max_attempts": 2,
  "issues_found": [],
  "fixes_attempted": [],
  "confidence_impact": "tracks if fixes reduced confidence"
}
```

## Enforcement Mechanisms

### Automatic Blocks
The validator-master will report if:
- Test coverage < 95% lines
- Any function lacks tests (< 100% function coverage)
- TODO/FIXME found in code
- Generic error handling detected
- Missing error types
- Placeholder implementations found

### Progressive Validation
Agents continuously report:
- Coverage metrics
- Test completion status
- Implementation progress
- Quality issues found

## File Structure (Unified with Large Task)

```
{working_directory}/
├── .claude/
│   ├── TASK_CONTEXT.json        # Current task facts (shared with large_task)
│   ├── WORKFLOW_STATE.json      # Progress tracking (shared)
│   ├── TEST_COVERAGE.json       # Real-time coverage
│   ├── RECOVERY_STATE.json      # Recovery tracking (shared)
│   └── VALIDATION_RESULTS.md    # Detailed results
└── CLAUDE.md               # PROJECT_KNOWLEDGE (persists across all tasks)
```

## Key Differences from Large Task

| Aspect | Large Task | Medium Task |
|--------|-----------|-------------|
| **Phases** | 5 detailed phases | 3 streamlined phases |
| **Architecture** | Creates new patterns | Uses existing patterns |
| **Common Code** | Creates /common/ infrastructure | Uses existing only |
| **Documentation** | Separate docs required | Inline docs sufficient |
| **Time** | 4-8+ hours | 1-4 hours |

| **SAME STANDARDS** | Large | Medium |
|-------------------|-------|---------|
| **Test Coverage** | 95%+ | 95%+ |
| **Function Coverage** | 100% | 100% |
| **Error Handling** | Comprehensive | Comprehensive |
| **Code Quality** | No placeholders | No placeholders |
| **Security** | Full validation | Full validation |

## Command Completion

### When invoked with `complete` (OPTIONAL):
**Note: Completion is optional. Starting a new task auto-resets state.**

If you want final validation and reports:
1. Use Task tool to launch validator-master for final validation
2. Review validation report
3. If validation fails:
   - Attempt recovery (max 2 attempts)
   - Delegate fixes to appropriate agents
   - Re-validate after each fix
4. If all validations pass:
   - Use Task tool to launch doc-maintainer agent:
     "Update docs at project_notes/[path]/ using two-document approach"
   - Ask user: "Run completion audit for insights?"
   - If yes: Use Task tool to launch completion-auditor agent
   - Update MEDIUM_TASK_STATUS.json to "completed"
   - Generate summary report with docs location (project_notes/[path]/)
   - Deactivate medium task mode
5. If still failing after 2 attempts:
   - Document remaining issues
   - Ask user whether to:
     * Continue with another attempt
     * Accept current state
     * Escalate to large_task mode

## Example Flow with Context Validation

```bash
User: /medium_task "Add rate limiting to API endpoints"

Orchestrator:
1. Creates TASK_CONTEXT.json with confidence: 0
2. Launches dependency-analyzer for validation
3. Agent returns confidence: 45% (can't find rate limit config)
4. BLOCKS - asks user: "Where should rate limits be configured?"
5. User provides info, re-runs validation
6. Confidence now 96% - proceeds with design
7. Each subsequent agent inherits validated context
8. No agent re-searches for rate limit config