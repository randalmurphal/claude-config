# Component: manifest.py

## Purpose
Manifest dataclass that represents the execution configuration for a spec. This is what drives workflow execution - the machine-readable version of the spec.

## Location
`~/.claude/orchestrations/core/manifest.py`

## Dependencies
- `paths.py` (for path resolution)

## Interface

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class ComponentDef:
    """Definition of a component in the manifest."""
    id: str
    file: str
    depends_on: list[str] = field(default_factory=list)
    complexity: str = "medium"  # low, medium, high
    purpose: str = ""
    context_file: str = ""
    notes: str = ""

@dataclass
class ExecutionConfig:
    """Execution configuration."""
    mode: str = "standard"  # quick, standard, full
    parallel_components: bool = False
    reviewers: int = 2
    require_tests: bool = True
    voting_gates: list[str] = field(default_factory=list)

@dataclass
class QualityConfig:
    """Quality requirements."""
    coverage_target: int = 80
    lint_required: bool = True
    security_scan: bool = False

@dataclass
class Manifest:
    """Complete manifest for a spec."""
    name: str
    project: str
    work_dir: str
    spec_dir: str
    created: str = ""

    complexity: int = 5  # 1-10
    risk_level: str = "medium"

    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    components: list[ComponentDef] = field(default_factory=list)
    quality: QualityConfig = field(default_factory=QualityConfig)
    gotchas: list[str] = field(default_factory=list)
    validation_command: str = ""

    def to_dict(self) -> dict[str, Any]: ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Manifest": ...

    @classmethod
    def load(cls, spec_dir: Path) -> "Manifest": ...

    def save(self, spec_dir: Path | None = None) -> None: ...

    def get_component(self, id: str) -> ComponentDef: ...

    def get_dependency_order(self) -> list[str]:
        """Return component IDs in topological order."""

    def resolve_work_dir(self) -> Path:
        """Resolve work_dir with ~ expansion."""
```

## Implementation Notes

- Follow existing pattern from `config.py` (to_dict/from_dict)
- `get_dependency_order()` does topological sort
- `load()` reads `manifest.json` from spec_dir
- `save()` writes `manifest.json` to spec_dir (or self.spec_dir)
- All paths stored as strings, resolved on access

## Gotchas

- Component IDs must be unique
- Dependencies reference IDs, not file paths
- `work_dir` and `spec_dir` use `~` notation, resolve at runtime
