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

### Phase 1: Design & Plan (SERIAL - 10-15 min)
Quick but COMPLETE design:

1. **Dependency Analysis**
   - Run dependency analyzer
   - Map affected components
   - Identify integration points

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

2A. **Test Creation (Can be parallel per component)**
- Tests MUST be written first (TDD enforced)
- 95% line coverage minimum
- 100% function coverage required
- ALL error paths tested
- ALL edge cases covered

2B. **Implementation**
- Full implementation, no placeholders
- Comprehensive error handling
- Complete documentation
- No technical debt

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

1. **Test Execution**
   ```bash
   # Must pass 100% of tests
   npm test -- --coverage
   # Coverage must meet requirements:
   # - Lines: 95%+
   # - Branches: 90%+
   # - Functions: 100%
   ```

2. **Quality Validation**
   - No console.logs in production code
   - No commented-out code
   - No debugging artifacts
   - All types properly defined

3. **Integration Verification**
   - Integrates with existing components
   - No regressions in existing tests
   - Performance acceptable
   - Security checks pass

4. **Final Checks**
   ```python
   def final_validation():
       checks = {
           "tests_pass": all_tests_passing(),
           "coverage_met": coverage_meets_requirements(),
           "no_placeholders": scan_for_todos() == 0,
           "errors_handled": all_errors_have_handlers(),
           "documented": all_public_functions_documented(),
           "secure": security_scan_passes()
       }
       
       if not all(checks.values()):
           return "BLOCKED - Fix issues before completing"
       return "PASSED - Ready for production"
   ```

## Enforcement Mechanisms

### Automatic Blocks
The system will BLOCK progress if:
- Test coverage < 95% lines
- Any function lacks tests (< 100% function coverage)
- TODO/FIXME found in code
- Generic error handling detected
- Missing error types
- Placeholder implementations found

### Progressive Validation
During Phase 2, continuously check:
- Coverage trending toward 95%+
- All new functions have tests
- Error handling is specific
- No accumulating technical debt

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

## Example Flow

```bash
User: /medium_task "Add rate limiting to API endpoints"