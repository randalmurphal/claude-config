# Full SPEC Template (for /conduct)

```markdown
# [Task Name] - Execution Specification

## Problem Statement
[What problem are we solving? What's broken or missing? Be specific about the current pain point or gap.]

## User Impact
[Who is affected and how? What happens when this is fixed? Focus on measurable outcomes.]

## Mission
[The unchanging goal - 1-2 sentences from task description]

## Success Criteria
[Measurable outcomes - these define done]
- [Criterion 1: Testable outcome]
- [Criterion 2: Measurable improvement]
- [Criterion 3: Acceptance condition]

## Requirements (IMMUTABLE)
[Hard requirements that cannot change during execution]

These constraints CANNOT change:
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

## Proposed Approach (EVOLVABLE)
[High-level strategy - can adapt during execution if better approach discovered]

**Components & Dependencies:**
- Component A: [purpose]
- Component B: [purpose]
- Component C: [purpose]

**Dependencies:**
- A depends on: [B, C]
- B depends on: [none]
- C depends on: [none]

**CRITICAL:** Watch for circular dependencies!

## Implementation Phases
### Phase 1: [Name] (Xh estimate)
[Description]

Tasks:
- [task 1]
- [task 2]

### Phase 2: [Name] (Xh estimate)
[Description]

Tasks:
- [task 1]
- [task 2]

## Known Gotchas
[From /spec discoveries and spikes - prevents surprises during implementation]
- [Gotcha 1]
- [Gotcha 2]

## Quality Requirements
[Format: "- Category: Requirement"]

- Tests: 95% coverage minimum (unit + integration)
- Security: [specific security requirements]
- Performance: [specific performance requirements]
- Documentation: [what needs documentation]
- Monitoring: [what needs logging/metrics]

## Testing Strategy
**Test Organization:**
- Unit tests: 1 test file per production file (95% coverage)
- Integration tests: 2-4 per module (85% coverage)
- E2E tests: Critical user workflows

**Coverage Targets:**
- Unit: ≥95%
- Integration: ≥85%
- E2E: Critical paths covered

## Files to Create/Modify
[Exact format required by /conduct parser]

### New Files
- path/to/file.py
  - Purpose: [description]
  - Depends on: [other files]
  - Complexity: [Low|Medium|High]
  - Confidence: [0.0-1.0]

- path/to/another.py
  - Purpose: [description]
  - Depends on: [other files]
  - Complexity: [Low|Medium|High]
  - Confidence: [0.0-1.0]

### Modified Files
- path/to/existing.py
  - Changes: [description of changes]
  - Risk: [Low|Medium|High]

- path/to/another_existing.py
  - Changes: [description of changes]
  - Risk: [Low|Medium|High]
```

## Section Name Requirements

**MUST use these EXACT names (case-sensitive):**
- ✅ "Problem Statement" (not "Problem")
- ✅ "User Impact" (not "Impact" or "User Benefit")
- ✅ "Requirements (IMMUTABLE)" (must include the tag)
- ✅ "Proposed Approach (EVOLVABLE)" (must include the tag)
- ✅ "Files to Create/Modify" (not "Files" or "File Changes")
- ✅ "### New Files" (subsection, must have)
- ✅ "### Modified Files" (subsection, must have)
