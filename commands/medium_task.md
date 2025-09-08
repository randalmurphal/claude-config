---
name: medium_task
description: Streamlined orchestration for medium-complexity features with full quality standards
---

You are managing Medium Task Mode - lighter orchestration but SAME quality standards as large tasks.

## Command Usage

- `/medium_task "description"` - Start a medium complexity task
- `/medium_task status` - Check progress
- `/medium_task complete` - Finish and validate

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

### Phase 1: Design & Plan (SERIAL - 10-15 min)
Quick but COMPLETE design:

1. **Dependency Analysis** (DELEGATE)
   - Use Task tool to launch dependency-analyzer agent:
     "Analyze dependencies for [feature description]. Map affected components and integration points."
   - Review analysis results
   - Document in MEDIUM_TASK_PLAN.md

2. **Interface Definition** (MUST BE COMPLETE)
   ```typescript
   // All interfaces fully defined, no placeholders
   interface RateLimiter {
     checkLimit(userId: string, endpoint: string): Promise<RateLimitResult>
     resetLimit(userId: string): Promise<void>
     getStatus(userId: string): Promise<RateLimitStatus>
   }
   ```

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

4. **Error Strategy** (COMPLETE)
   - Define all error types needed
   - Plan error handling for each component
   - Specify error messages and codes

Output: `.claude/MEDIUM_TASK_PLAN.md` with FULL specifications

### Phase 2: Test & Implement (PARALLEL when safe - 1-3 hours)

**SAME STANDARDS as large task:**

2A. **Test Creation** (DELEGATE)
- Use Task tool to launch tdd-enforcer agent:
  "Create comprehensive tests for [component]. Requirements:
   - Unit tests: One test class per function, mock all dependencies
   - Integration tests: Use REAL APIs when available
   - Follow existing patterns in fisio/tests/
   - 95% line coverage, 100% function coverage
   - Test every possible case"
- Tests MUST be written first (TDD enforced)
- Review test specifications from agent

2B. **Implementation** (DELEGATE) 
- After tests are ready, launch implementation agent:
  "Implement [feature] following test specifications. Full implementation required - no placeholders, comprehensive error handling."
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
- **MAINTAIN CONTROL** - All agents report back to you
- **HANDLE RECOVERY** - You decide fix strategies
- **TRACK PROGRESS** - Update MEDIUM_TASK_STATUS.json

### Agent Instructions Template:
When delegating, provide:
1. Specific task description
2. Quality requirements (coverage, standards)
3. Scope boundaries (which files/components)
4. Expected deliverables

### Recovery Process:
1. **First Attempt**: Delegate targeted fixes
2. **Second Attempt**: Try alternative approach
3. **After 2 Attempts**: Ask user for guidance

Track in `.claude/MEDIUM_RECOVERY_STATE.json`:
```json
{
  "current_attempt": 1,
  "max_attempts": 2,
  "issues_found": [],
  "fixes_attempted": []
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

## File Structure (Lightweight)

```
.claude/
├── MEDIUM_TASK_PLAN.md      # Full specifications
├── MEDIUM_TASK_STATUS.json  # Progress tracking
├── TEST_COVERAGE.json       # Real-time coverage
└── VALIDATION_RESULTS.md    # Detailed results
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

### When invoked with `complete`:
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

## Example Flow

```bash
User: /medium_task "Add rate limiting to API endpoints"