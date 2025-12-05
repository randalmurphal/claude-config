# Component: formalizer.py

## Purpose
Translates brainstorm artifacts into a validated manifest. This is the bridge between the interactive `/spec` phase and the execution phase.

## Location
`~/.claude/orchestrations/spec/formalizer.py`

## Dependencies
- `manifest.py` (Manifest dataclass)
- `validator.py` (ManifestValidator)
- `runner.py` (AgentRunner for formalization agent)
- `paths.py` (path resolution)

## Interface

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FormalizationResult:
    """Result of formalization attempt."""
    success: bool
    manifest: Manifest | None = None
    validation_errors: list[ValidationError] = field(default_factory=list)
    draft: dict | None = None  # Raw draft if validation failed
    error: str = ""

class SpecFormalizer:
    """Formalizes brainstorm artifacts into validated manifest."""

    def __init__(
        self,
        runner: AgentRunner,
        validator: ManifestValidator,
    ):
        self.runner = runner
        self.validator = validator

    def formalize(
        self,
        spec_dir: Path,
        max_attempts: int = 3,
    ) -> FormalizationResult:
        """Formalize brainstorm into manifest.

        1. Read brainstorm artifacts
        2. Run formalization agent
        3. Validate result
        4. If invalid, show errors and retry
        5. Return validated manifest or errors
        """

    def _read_brainstorm(self, spec_dir: Path) -> dict[str, str]:
        """Read all brainstorm artifacts."""
        brainstorm_dir = spec_dir / "brainstorm"
        return {
            "mission": (brainstorm_dir / "MISSION.md").read_text(),
            "investigation": (brainstorm_dir / "INVESTIGATION.md").read_text(),
            "decisions": (brainstorm_dir / "DECISIONS.md").read_text(),
            "concerns": (brainstorm_dir / "CONCERNS.md").read_text() if exists,
        }

    def _build_formalization_prompt(
        self,
        brainstorm: dict[str, str],
        previous_errors: list[ValidationError] | None = None,
    ) -> str:
        """Build prompt for formalization agent."""

    def _run_formalization_agent(
        self,
        prompt: str,
    ) -> dict | None:
        """Run agent to produce manifest JSON."""

    def _write_manifest(
        self,
        manifest: Manifest,
        spec_dir: Path,
    ) -> None:
        """Write validated manifest to spec_dir."""

    def _initialize_component_contexts(
        self,
        manifest: Manifest,
        spec_dir: Path,
    ) -> None:
        """Create initial component context files."""
```

## Formalization Agent Prompt

```markdown
# Formalization Task

Convert the following brainstorm artifacts into a structured manifest.

## Brainstorm Artifacts

### Mission
{mission}

### Investigation Findings
{investigation}

### Architectural Decisions
{decisions}

## Output Format

Return a JSON object matching this schema:
{manifest_schema}

## Requirements

1. Extract all components mentioned in the artifacts
2. Determine dependencies from the investigation
3. Set complexity (1-10) based on findings
4. Set risk_level based on dependencies and scope
5. Choose appropriate execution mode
6. Include all gotchas discovered

## Previous Validation Errors (if any)
{previous_errors}

Fix these specific issues in your output.
```

## Validation Loop

```python
def formalize(self, spec_dir: Path, max_attempts: int = 3) -> FormalizationResult:
    brainstorm = self._read_brainstorm(spec_dir)
    previous_errors = None

    for attempt in range(1, max_attempts + 1):
        prompt = self._build_formalization_prompt(brainstorm, previous_errors)

        draft = self._run_formalization_agent(prompt)
        if not draft:
            return FormalizationResult(success=False, error="Agent failed")

        # Convert to Manifest
        try:
            manifest = Manifest.from_dict(draft)
        except Exception as e:
            previous_errors = [ValidationError("root", str(e))]
            continue

        # Validate
        result = self.validator.validate(manifest)

        if result.valid:
            self._write_manifest(manifest, spec_dir)
            self._initialize_component_contexts(manifest, spec_dir)
            return FormalizationResult(success=True, manifest=manifest)

        previous_errors = result.errors
        LOG.warning(f"Attempt {attempt} failed: {len(result.errors)} errors")

    return FormalizationResult(
        success=False,
        validation_errors=previous_errors,
        draft=draft,
    )
```

## Error Handling

When validation fails:
1. Show specific errors to user
2. Offer to retry with fixes
3. Allow manual manifest editing
4. Provide draft for inspection
