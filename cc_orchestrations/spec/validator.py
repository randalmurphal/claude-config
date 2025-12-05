"""Manifest validation with specific, actionable error messages.

Validates manifests against schemas and logic rules, catching errors before
execution. Returns ALL errors, not just the first one.
"""

from dataclasses import dataclass, field

from cc_orchestrations.core.manifest import ComponentDef, Manifest


@dataclass
class ValidationError:
    """A specific validation error."""

    field: str  # e.g., "components[2].depends_on"
    error: str  # What's wrong
    suggestion: str = ''  # How to fix


@dataclass
class ValidationResult:
    """Result of manifest validation."""

    valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError] = field(default_factory=list)


class ManifestValidator:
    """Validates manifests against schemas and logic rules."""

    def validate(self, manifest: Manifest) -> ValidationResult:
        """Run all validations.

        Returns:
            ValidationResult with all errors and warnings found.
        """
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # Run all validation checks
        errors.extend(self._validate_required_fields(manifest))
        errors.extend(self._validate_component_structure(manifest))
        errors.extend(self._validate_dependencies(manifest))
        warnings.extend(self._validate_consistency(manifest))

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def _validate_required_fields(
        self, manifest: Manifest
    ) -> list[ValidationError]:
        """Check required fields are present and non-empty.

        Args:
            manifest: Manifest to validate.

        Returns:
            List of ValidationError for missing or empty required fields.
        """
        errors: list[ValidationError] = []

        # Check top-level required fields
        if not manifest.name or not manifest.name.strip():
            errors.append(
                ValidationError(
                    field='name',
                    error='Manifest name is required',
                    suggestion='Add a descriptive name for this manifest',
                )
            )

        if not manifest.project or not manifest.project.strip():
            errors.append(
                ValidationError(
                    field='project',
                    error='Project name is required',
                    suggestion='Add the project name this manifest belongs to',
                )
            )

        if not manifest.work_dir or not manifest.work_dir.strip():
            errors.append(
                ValidationError(
                    field='work_dir',
                    error='Working directory is required',
                    suggestion='Add the work_dir path for execution context',
                )
            )

        # Check components list exists and has at least one entry
        if not manifest.components:
            errors.append(
                ValidationError(
                    field='components',
                    error='Components list is empty',
                    suggestion='Add at least one component to the manifest',
                )
            )

        return errors

    def _validate_component_structure(
        self, manifest: Manifest
    ) -> list[ValidationError]:
        """Check each component has required fields.

        Args:
            manifest: Manifest to validate.

        Returns:
            List of ValidationError for components with missing required fields.
        """
        errors: list[ValidationError] = []

        for idx, component in enumerate(manifest.components):
            # Check id
            if not component.id or not component.id.strip():
                errors.append(
                    ValidationError(
                        field=f'components[{idx}].id',
                        error='Component ID is required',
                        suggestion='Add a unique identifier for this component',
                    )
                )

            # Check file
            if not component.file or not component.file.strip():
                errors.append(
                    ValidationError(
                        field=f'components[{idx}].file',
                        error='Component file path is required',
                        suggestion=f"Add file path for component '{component.id}'",
                    )
                )

            # Check depends_on exists (can be empty list, but must be present)
            if component.depends_on is None:
                errors.append(
                    ValidationError(
                        field=f'components[{idx}].depends_on',
                        error='depends_on field is required (can be empty list)',
                        suggestion=f"Set depends_on for component '{component.id}' "
                        f'to [] if no dependencies',
                    )
                )

        return errors

    def _validate_dependencies(
        self, manifest: Manifest
    ) -> list[ValidationError]:
        """Check dependency graph is valid.

        Validates:
        - All dependencies exist
        - No circular dependencies

        Args:
            manifest: Manifest to validate.

        Returns:
            List of ValidationError for invalid dependencies and cycles.
        """
        errors: list[ValidationError] = []

        # Build set of all component IDs
        all_ids = {c.id for c in manifest.components if c.id}

        # Check all dependencies exist
        for idx, component in enumerate(manifest.components):
            if not component.depends_on:
                continue

            for dep_id in component.depends_on:
                if dep_id not in all_ids:
                    errors.append(
                        ValidationError(
                            field=f'components[{idx}].depends_on',
                            error=f"Dependency '{dep_id}' not found in components",
                            suggestion=f"Add component '{dep_id}' to components "
                            f"or remove from {component.id}'s depends_on",
                        )
                    )

        # Check for circular dependencies
        cycles = self._detect_cycles(manifest.components)
        for cycle in cycles:
            cycle_str = ' -> '.join([*cycle, cycle[0]])
            errors.append(
                ValidationError(
                    field='components',
                    error=f'Circular dependency: {cycle_str}',
                    suggestion='Remove one direction of the dependency to break cycle',
                )
            )

        return errors

    def _validate_consistency(
        self, manifest: Manifest
    ) -> list[ValidationError]:
        """Check internal consistency rules.

        Checks:
        - Risk level matches complexity
        - Reviewer count matches risk
        - Test requirements make sense

        Args:
            manifest: Manifest to validate.

        Returns:
            List of ValidationError (warnings) for consistency issues.
        """
        warnings: list[ValidationError] = []

        # Check risk level vs reviewer count
        if manifest.risk_level == 'high' and manifest.execution.reviewers < 4:
            warnings.append(
                ValidationError(
                    field='execution.reviewers',
                    error=f'High risk but only {manifest.execution.reviewers} '
                    f'reviewers configured',
                    suggestion='Set reviewers to 4+ for high-risk specs',
                )
            )

        # Check complexity vs risk level
        if manifest.complexity > 8 and manifest.risk_level == 'low':
            warnings.append(
                ValidationError(
                    field='risk_level',
                    error=f'Complexity is {manifest.complexity} but risk_level '
                    f"is 'low'",
                    suggestion="Consider increasing risk_level to 'medium' or 'high' "
                    'for complex specs',
                )
            )

        # Check test requirements vs validation command
        if manifest.execution.require_tests and not manifest.validation_command:
            warnings.append(
                ValidationError(
                    field='validation_command',
                    error='Tests required but no validation_command specified',
                    suggestion='Add validation_command to run tests, or set '
                    'require_tests to false',
                )
            )

        return warnings

    def _detect_cycles(self, components: list[ComponentDef]) -> list[list[str]]:
        """Detect circular dependencies using DFS.

        Args:
            components: List of components to check for cycles.

        Returns:
            List of cycles, where each cycle is a list of component IDs.
        """
        cycles: list[list[str]] = []

        # Build adjacency list (forward graph: who depends on whom)
        graph: dict[str, list[str]] = {}
        for component in components:
            if component.id:
                graph[component.id] = component.depends_on or []

        # Track visited nodes and recursion stack
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            """DFS helper to detect cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Check all dependencies
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found a cycle - extract it from path
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:]
                    cycles.append(cycle)

            # Backtrack
            path.pop()
            rec_stack.remove(node)

        # Run DFS from each unvisited node
        for component_id in graph:
            if component_id not in visited:
                dfs(component_id)

        return cycles
