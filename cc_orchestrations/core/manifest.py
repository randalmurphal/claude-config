"""Manifest dataclass for spec execution configuration.

The manifest is the machine-readable version of a spec that drives workflow
execution. It defines components, dependencies, execution settings, and quality
requirements.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import expand_path


LOG = logging.getLogger(__name__)


@dataclass
class ComponentDef:
    """Definition of a component in the manifest."""

    id: str
    file: str
    depends_on: list[str] = field(default_factory=list)
    complexity: str = 'medium'  # low, medium, high
    purpose: str = ''
    context_file: str = ''
    notes: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'file': self.file,
            'depends_on': self.depends_on,
            'complexity': self.complexity,
            'purpose': self.purpose,
            'context_file': self.context_file,
            'notes': self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ComponentDef':
        return cls(
            id=data['id'],
            file=data['file'],
            depends_on=data.get('depends_on', []),
            complexity=data.get('complexity', 'medium'),
            purpose=data.get('purpose', ''),
            context_file=data.get('context_file', ''),
            notes=data.get('notes', ''),
        )


@dataclass
class ExecutionConfig:
    """Execution configuration."""

    mode: str = 'standard'  # quick, standard, full
    parallel_components: bool = False
    reviewers: int = 2
    require_tests: bool = True
    voting_gates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'mode': self.mode,
            'parallel_components': self.parallel_components,
            'reviewers': self.reviewers,
            'require_tests': self.require_tests,
            'voting_gates': self.voting_gates,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ExecutionConfig':
        return cls(
            mode=data.get('mode', 'standard'),
            parallel_components=data.get('parallel_components', False),
            reviewers=data.get('reviewers', 2),
            require_tests=data.get('require_tests', True),
            voting_gates=data.get('voting_gates', []),
        )


@dataclass
class QualityConfig:
    """Quality requirements."""

    coverage_target: int = 80
    lint_required: bool = True
    security_scan: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            'coverage_target': self.coverage_target,
            'lint_required': self.lint_required,
            'security_scan': self.security_scan,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'QualityConfig':
        return cls(
            coverage_target=data.get('coverage_target', 80),
            lint_required=data.get('lint_required', True),
            security_scan=data.get('security_scan', False),
        )


@dataclass
class Manifest:
    """Complete manifest for a spec."""

    name: str
    project: str
    work_dir: str
    spec_dir: str
    created: str = ''

    complexity: int = 5  # 1-10
    risk_level: str = 'medium'

    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    components: list[ComponentDef] = field(default_factory=list)
    quality: QualityConfig = field(default_factory=QualityConfig)
    gotchas: list[str] = field(default_factory=list)
    validation_command: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'project': self.project,
            'work_dir': self.work_dir,
            'spec_dir': self.spec_dir,
            'created': self.created,
            'complexity': self.complexity,
            'risk_level': self.risk_level,
            'execution': self.execution.to_dict(),
            'components': [c.to_dict() for c in self.components],
            'quality': self.quality.to_dict(),
            'gotchas': self.gotchas,
            'validation_command': self.validation_command,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Manifest':
        return cls(
            name=data['name'],
            project=data['project'],
            work_dir=data['work_dir'],
            spec_dir=data['spec_dir'],
            created=data.get('created', ''),
            complexity=data.get('complexity', 5),
            risk_level=data.get('risk_level', 'medium'),
            execution=ExecutionConfig.from_dict(data.get('execution', {})),
            components=[
                ComponentDef.from_dict(c) for c in data.get('components', [])
            ],
            quality=QualityConfig.from_dict(data.get('quality', {})),
            gotchas=data.get('gotchas', []),
            validation_command=data.get('validation_command', ''),
        )

    @classmethod
    def load(cls, spec_dir: Path) -> 'Manifest':
        """Load manifest from manifest.json in spec_dir."""
        manifest_path = spec_dir / 'manifest.json'
        if not manifest_path.exists():
            raise FileNotFoundError(
                f'Manifest not found: {manifest_path}. '
                'Run /spec to generate a manifest for this spec.'
            )

        try:
            data = json.loads(manifest_path.read_text())
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(
                f'Invalid JSON in manifest {manifest_path}: {e}'
            ) from e
        except KeyError as e:
            raise ValueError(
                f'Missing required field in manifest {manifest_path}: {e}'
            ) from e

    def save(self, spec_dir: Path | None = None) -> None:
        """Save manifest to manifest.json in spec_dir.

        Args:
            spec_dir: Directory to save to. If None, uses self.spec_dir.
        """
        if spec_dir is None:
            spec_dir = expand_path(self.spec_dir)
        else:
            spec_dir = expand_path(spec_dir)

        spec_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = spec_dir / 'manifest.json'

        manifest_path.write_text(json.dumps(self.to_dict(), indent=2))
        LOG.info(f'Manifest saved to {manifest_path}')

    def get_component(self, id: str) -> ComponentDef:
        """Get component by ID.

        Args:
            id: Component ID to find.

        Returns:
            ComponentDef matching the ID.

        Raises:
            ValueError: If component ID not found.
        """
        for component in self.components:
            if component.id == id:
                return component
        raise ValueError(
            f"Component '{id}' not found. "
            f'Available: {[c.id for c in self.components]}'
        )

    def get_dependency_order(self) -> list[str]:
        """Return component IDs in topological order.

        Components with no dependencies come first, followed by components
        that depend on them, etc. Detects cycles and raises an error.

        Returns:
            List of component IDs in execution order.

        Raises:
            ValueError: If a dependency cycle is detected or if a component
                references a non-existent dependency.
        """
        # Build dependency graph
        all_ids = {c.id for c in self.components}

        # Validate all dependencies exist
        for component in self.components:
            for dep_id in component.depends_on:
                if dep_id not in all_ids:
                    raise ValueError(
                        f"Component '{component.id}' depends on unknown "
                        f"component '{dep_id}'"
                    )

        # Calculate in-degrees (number of dependencies each node has)
        in_degree: dict[str, int] = {}
        for component in self.components:
            in_degree[component.id] = len(component.depends_on)

        # Kahn's algorithm for topological sort
        queue: list[str] = []
        result: list[str] = []

        # Start with nodes that have no dependencies
        for comp_id, degree in in_degree.items():
            if degree == 0:
                queue.append(comp_id)

        while queue:
            # Sort queue for deterministic ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # For each node that depends on current, decrement its in-degree
            for component in self.components:
                if current in component.depends_on:
                    in_degree[component.id] -= 1
                    if in_degree[component.id] == 0:
                        queue.append(component.id)

        # Check for cycles
        if len(result) != len(self.components):
            # Find components that weren't processed (part of cycle)
            unprocessed = all_ids - set(result)
            raise ValueError(
                f'Dependency cycle detected involving components: '
                f'{sorted(unprocessed)}'
            )

        return result

    def resolve_work_dir(self) -> Path:
        """Resolve work_dir with ~ expansion.

        Returns:
            Absolute Path to the working directory.
        """
        return expand_path(self.work_dir)
