# Component: validator.py

## Purpose
Python validation of manifests against schemas and logic rules. Catches errors before execution with specific, actionable messages.

## Location
`~/.claude/orchestrations/spec/validator.py`

## Dependencies
- `manifest.py` (for Manifest dataclass)

## Interface

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class ValidationError:
    """A specific validation error."""
    field: str  # e.g., "components[2].depends_on"
    error: str  # What's wrong
    suggestion: str = ""  # How to fix

@dataclass
class ValidationResult:
    """Result of manifest validation."""
    valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError] = field(default_factory=list)

class ManifestValidator:
    """Validates manifests against schemas and logic rules."""

    def validate(self, manifest: Manifest) -> ValidationResult:
        """Run all validations."""

    def _validate_required_fields(self, manifest: Manifest) -> list[ValidationError]:
        """Check required fields are present."""

    def _validate_component_structure(self, manifest: Manifest) -> list[ValidationError]:
        """Check each component has required fields."""

    def _validate_dependencies(self, manifest: Manifest) -> list[ValidationError]:
        """Check dependency graph is valid:
        - All dependencies exist
        - No circular dependencies
        """

    def _validate_consistency(self, manifest: Manifest) -> list[ValidationError]:
        """Check internal consistency:
        - Risk level matches complexity
        - Reviewer count matches risk
        - Execution config makes sense
        """

    def _detect_cycles(self, components: list[ComponentDef]) -> list[list[str]]:
        """Detect circular dependencies, return list of cycles."""
```

## Validation Rules

### Required Fields
- `name`, `project`, `work_dir` must be non-empty
- `components` must have at least one entry
- Each component must have `id`, `file`, `depends_on`

### Dependency Validation
- All `depends_on` entries must reference existing component IDs
- No circular dependencies (A->B->C->A)
- Detect and report all cycles, not just first one

### Consistency Checks
- `risk_level: high` + `reviewers: 2` = warning
- `complexity > 8` + `risk_level: low` = warning
- `require_tests: true` + no `validation_command` = warning

## Error Format Examples

```
ValidationError(
    field="components[2].depends_on",
    error="Dependency 'nonexistent' not found in components",
    suggestion="Add 'nonexistent' to components or remove from depends_on"
)

ValidationError(
    field="components",
    error="Circular dependency: auth -> database -> auth",
    suggestion="Remove one direction of the dependency"
)

ValidationError(
    field="execution.reviewers",
    error="High risk but only 2 reviewers configured",
    suggestion="Set reviewers to 4+ for high-risk specs"
)
```

## Implementation Notes

- Return ALL errors, not just first one
- Separate errors (blocking) from warnings (advisory)
- Use field paths like `components[2].depends_on` for specificity
- Cycle detection: use DFS with recursion stack
