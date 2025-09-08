# Parallel Execution Guide for Large Task Mode

## Overview
This guide ensures TRUE parallel execution when Claude claims to work in parallel, preventing the common issue of saying "parallel" but executing serially.

## Workflow Phases

### Serial Phases (NO Parallelization)
These phases MUST complete sequentially:

1. **Architecture Phase**
   - architecture-planner → api-contract-designer → error-designer
   - Creates `/common/` infrastructure that all other work depends on
   - BLOCKS: Everything else

2. **Test Definition Phase**  
   - tdd-enforcer creates comprehensive test suite
   - Tests MUST exist before implementation
   - BLOCKS: Implementation phase

3. **Final Validation Phase**
   - validator-master runs comprehensive checks
   - Must run after all work complete
   - BLOCKS: Deployment

### Parallel Phases
These phases allow concurrent execution:

1. **Implementation Phase**
   - Independent features can run in parallel
   - Different API endpoints can run in parallel
   - Frontend components can run in parallel
   - REQUIREMENT: No overlapping file modifications

2. **Integration & Enhancement Phase**
   - Security audits
   - Performance testing
   - Documentation updates
   - Code quality reviews

## How to Ensure TRUE Parallel Execution

### ❌ WRONG - Serial Disguised as Parallel
```
"I'll work on these features in parallel:"
[Uses Task tool for Feature A]
"Now working on Feature B..."
[Uses Task tool for Feature B]
```

### ✅ CORRECT - Actual Parallel
```
"Launching parallel implementation for independent features:"

[Task tool 1: Feature A implementation]
[Task tool 2: Feature B implementation]  
[Task tool 3: Feature C implementation]

(All Task invocations in SINGLE response)
```

## Parallel Execution Rules

### 1. Resource Locking
- Each parallel task gets EXCLUSIVE paths
- No two agents modify same file
- Common files are READ-ONLY during parallel work

### 2. Dependency Management
```json
{
  "feature-trading": {
    "dependencies": ["/common/types", "/common/utils"],
    "can_modify": ["/src/features/trading/"],
    "cannot_modify": ["/common/", "/src/features/analysis/"]
  }
}
```

### 3. Conflict Prevention
- Check BOUNDARIES.json for `parallel_safe` flag
- Verify no path overlaps
- Ensure dependencies are complete

## Common Parallel Patterns

### Pattern 1: Feature-Based Parallelization
```
Phase: Implementation
Independent features identified:
- Trading: /src/features/trading/, /api/trading/
- Analysis: /src/features/analysis/, /api/analysis/
- Reporting: /src/features/reporting/, /api/reporting/

[Task 1: Implement Trading]
[Task 2: Implement Analysis]
[Task 3: Implement Reporting]
```

### Pattern 2: Layer-Based Parallelization
```
Phase: Implementation
Independent layers identified:
- Frontend Components
- Backend APIs
- Database Models

[Task 1: Build UI Components]
[Task 2: Implement API Endpoints]
[Task 3: Create Database Layer]
```

### Pattern 3: Test-Implementation Parallelization
```
Phase: Implementation
Parallel work:
- Implement Feature A
- Write integration tests for completed Feature B
- Update documentation for Feature C

[Task 1: Feature A Implementation]
[Task 2: Feature B Integration Tests]
[Task 3: Feature C Documentation]
```

## Synchronization Points

Points where ALL parallel work must complete:

1. **After Architecture** → All agents wait for common code
2. **After Test Definition** → Implementation can begin
3. **Before Integration Testing** → All components ready
4. **Before Final Validation** → All work complete
5. **Before Deployment** → All checks passed

## Monitoring Parallel Execution

### PARALLEL_STATUS.json
```json
{
  "execution_id": "exec-123",
  "phase": "implementation",
  "started": "2024-01-10T10:00:00Z",
  "tasks": [
    {
      "id": "task-1",
      "name": "Trading Feature",
      "agent": "general-purpose",
      "status": "in_progress",
      "paths": ["/src/features/trading/"],
      "started": "2024-01-10T10:00:00Z"
    },
    {
      "id": "task-2", 
      "name": "Analysis Feature",
      "agent": "general-purpose",
      "status": "completed",
      "paths": ["/src/features/analysis/"],
      "started": "2024-01-10T10:00:00Z",
      "completed": "2024-01-10T10:15:00Z"
    }
  ]
}
```

### RESOURCE_LOCKS.json
```json
{
  "locks": [
    {
      "agent_id": "task-123",
      "locked_paths": ["/src/features/trading/"],
      "lock_time": "2024-01-10T10:00:00Z"
    }
  ]
}
```

## Troubleshooting

### Issue: "Parallel" but runs serially
**Solution**: Use parallel-task-dispatcher agent which enforces multiple Task tools in single response

### Issue: Resource conflicts
**Solution**: Check BOUNDARIES.json, ensure no overlapping paths

### Issue: Dependency violations  
**Solution**: Ensure all dependencies complete before parallel phase

### Issue: Parallel work in serial phase
**Solution**: Check WORKFLOW_STATE.json for current phase

## Validation

The `parallel_execution_validator.py` will:
1. Detect when parallel execution is claimed
2. Verify multiple Task tools are used
3. Check for resource conflicts
4. Enforce proper locking
5. Block if in serial phase

## Best Practices

1. **Always check phase** before claiming parallel execution
2. **Use parallel-task-dispatcher** for coordinated parallel work
3. **Lock resources** before modification
4. **Monitor PARALLEL_STATUS.json** for progress
5. **Clear locks** after completion
6. **Synchronize** at defined points

## Example Workflow

```bash
# User request
"Build authentication and trading features"

# Claude's response (CORRECT)
"Analyzing for parallel execution...

Current phase: Implementation (parallel allowed)
No resource conflicts detected.

Launching parallel implementation:

[Task Tool 1: Authentication Feature]
- Agent: general-purpose
- Scope: /src/features/auth/, /api/auth/
- Dependencies: /common/types

[Task Tool 2: Trading Feature]  
- Agent: general-purpose
- Scope: /src/features/trading/, /api/trading/
- Dependencies: /common/types

Both tasks launched in parallel. Tracking in PARALLEL_STATUS.json"
```

This ensures actual parallel execution instead of serial with parallel claims.