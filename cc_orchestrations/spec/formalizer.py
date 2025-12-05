"""Spec formalizer - converts brainstorm artifacts into validated manifest.

This is the bridge between the interactive /spec phase and the execution phase.
Takes free-form brainstorm documents and produces a structured, validated
manifest.json that drives workflow execution.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from cc_orchestrations.core.context import ContextManager
from cc_orchestrations.core.manifest import Manifest
from cc_orchestrations.core.runner import AgentRunner

from .validator import ManifestValidator, ValidationError


LOG = logging.getLogger(__name__)


@dataclass
class FormalizationResult:
    """Result of formalization attempt."""

    success: bool
    manifest: Manifest | None = None
    validation_errors: list[ValidationError] = field(default_factory=list)
    draft: dict | None = None  # Raw draft if validation failed
    error: str = ''


class SpecFormalizer:
    """Formalizes brainstorm artifacts into validated manifest."""

    def __init__(
        self,
        runner: AgentRunner,
        validator: ManifestValidator,
    ):
        """Initialize formalizer.

        Args:
            runner: AgentRunner for invoking formalization agent
            validator: ManifestValidator for validating output
        """
        self.runner = runner
        self.validator = validator

    def formalize(
        self,
        spec_dir: Path,
        max_attempts: int = 3,
    ) -> FormalizationResult:
        """Formalize brainstorm into manifest.

        Process:
        1. Read brainstorm artifacts
        2. Run formalization agent
        3. Validate result
        4. If invalid, show errors and retry
        5. Return validated manifest or errors

        Args:
            spec_dir: Path to spec directory containing brainstorm/
            max_attempts: Maximum validation attempts

        Returns:
            FormalizationResult with manifest or errors
        """
        # Read brainstorm artifacts
        try:
            brainstorm = self._read_brainstorm(spec_dir)
        except FileNotFoundError as e:
            return FormalizationResult(
                success=False,
                error=f'Missing brainstorm file: {e}',
            )
        except Exception as e:
            return FormalizationResult(
                success=False,
                error=f'Failed to read brainstorm: {e}',
            )

        previous_errors = None
        draft = None

        # Validation loop
        for attempt in range(1, max_attempts + 1):
            LOG.info(f'Formalization attempt {attempt}/{max_attempts}')

            # Build prompt with previous errors if retrying
            prompt = self._build_formalization_prompt(
                brainstorm, previous_errors
            )

            # Run formalization agent
            draft = self._run_formalization_agent(prompt)
            if not draft:
                return FormalizationResult(
                    success=False,
                    error='Agent failed to produce output',
                )

            # Convert to Manifest
            try:
                manifest = Manifest.from_dict(draft)
            except Exception as e:
                LOG.warning(f'Failed to convert to Manifest: {e}')
                previous_errors = [
                    ValidationError(
                        field='root',
                        error=str(e),
                        suggestion='Check JSON structure matches schema',
                    )
                ]
                continue

            # Validate
            result = self.validator.validate(manifest)

            if result.valid:
                # Success! Write manifest and initialize component contexts
                self._write_manifest(manifest, spec_dir)
                self._initialize_component_contexts(manifest, spec_dir)

                LOG.info(f'Formalization successful on attempt {attempt}')
                return FormalizationResult(success=True, manifest=manifest)

            # Validation failed - prepare for retry
            previous_errors = result.errors
            LOG.warning(
                f'Attempt {attempt} failed: {len(result.errors)} errors'
            )
            for error in result.errors[:3]:  # Show first 3
                LOG.warning(f'  - {error.field}: {error.error}')

        # All attempts exhausted
        return FormalizationResult(
            success=False,
            validation_errors=previous_errors or [],
            draft=draft,
            error=f'Validation failed after {max_attempts} attempts',
        )

    def _read_brainstorm(self, spec_dir: Path) -> dict[str, str]:
        """Read all brainstorm artifacts.

        Args:
            spec_dir: Path to spec directory

        Returns:
            Dictionary with brainstorm content keyed by document type

        Raises:
            FileNotFoundError: If required brainstorm files are missing
        """
        brainstorm_dir = spec_dir / 'brainstorm'

        if not brainstorm_dir.exists():
            raise FileNotFoundError(
                f'Brainstorm directory not found: {brainstorm_dir}'
            )

        result = {}

        # Required files
        mission_file = brainstorm_dir / 'MISSION.md'
        investigation_file = brainstorm_dir / 'INVESTIGATION.md'
        decisions_file = brainstorm_dir / 'DECISIONS.md'

        if not mission_file.exists():
            raise FileNotFoundError(f'Missing {mission_file}')
        result['mission'] = mission_file.read_text()

        if not investigation_file.exists():
            raise FileNotFoundError(f'Missing {investigation_file}')
        result['investigation'] = investigation_file.read_text()

        if not decisions_file.exists():
            raise FileNotFoundError(f'Missing {decisions_file}')
        result['decisions'] = decisions_file.read_text()

        # Optional files
        concerns_file = brainstorm_dir / 'CONCERNS.md'
        if concerns_file.exists():
            result['concerns'] = concerns_file.read_text()

        return result

    def _build_formalization_prompt(
        self,
        brainstorm: dict[str, str],
        previous_errors: list[ValidationError] | None = None,
    ) -> str:
        """Build prompt for formalization agent.

        Args:
            brainstorm: Dictionary of brainstorm artifacts
            previous_errors: Validation errors from previous attempt

        Returns:
            Formatted prompt for agent
        """
        prompt_parts = [
            '# Formalization Task',
            '',
            'Convert the following brainstorm artifacts into a structured manifest.',
            '',
            '## Brainstorm Artifacts',
            '',
            '### Mission',
            brainstorm['mission'],
            '',
            '### Investigation Findings',
            brainstorm['investigation'],
            '',
            '### Architectural Decisions',
            brainstorm['decisions'],
        ]

        if 'concerns' in brainstorm:
            prompt_parts.extend(
                [
                    '',
                    '### Concerns',
                    brainstorm['concerns'],
                ]
            )

        prompt_parts.extend(
            [
                '',
                '## Requirements',
                '',
                '1. Extract all components mentioned in the artifacts',
                '2. Determine dependencies from the investigation',
                '3. Set complexity (1-10) based on findings',
                '4. Set risk_level (low, medium, high) based on dependencies and scope',
                '5. Choose appropriate execution mode (quick, standard, full)',
                '6. Include all gotchas discovered during investigation',
                '7. Set appropriate quality requirements',
                '',
                '## Output Format',
                '',
                'Return a JSON object with this structure:',
                '```json',
                '{',
                '  "name": "spec-name",',
                '  "project": "project-name",',
                '  "work_dir": "~/path/to/work/dir",',
                '  "spec_dir": "~/path/to/spec/dir",',
                '  "created": "ISO-8601 timestamp",',
                '  "complexity": 1-10,',
                '  "risk_level": "low|medium|high",',
                '  "execution": {',
                '    "mode": "quick|standard|full",',
                '    "parallel_components": true/false,',
                '    "reviewers": 2-8,',
                '    "require_tests": true/false,',
                '    "voting_gates": []',
                '  },',
                '  "components": [',
                '    {',
                '      "id": "component-id",',
                '      "file": "path/to/file.py",',
                '      "depends_on": ["other-id"],',
                '      "complexity": "low|medium|high",',
                '      "purpose": "What this component does",',
                '      "context_file": "",',
                '      "notes": "Additional context"',
                '    }',
                '  ],',
                '  "quality": {',
                '    "coverage_target": 80,',
                '    "lint_required": true,',
                '    "security_scan": false',
                '  },',
                '  "gotchas": ["discovered gotchas..."],',
                '  "validation_command": "pytest tests/"',
                '}',
                '```',
            ]
        )

        # Add previous validation errors if retrying
        if previous_errors:
            prompt_parts.extend(
                [
                    '',
                    '## Previous Validation Errors',
                    '',
                    'Fix these specific issues in your output:',
                    '',
                ]
            )
            for error in previous_errors:
                suggestion = (
                    f' ({error.suggestion})' if error.suggestion else ''
                )
                prompt_parts.append(
                    f'- **{error.field}**: {error.error}{suggestion}'
                )

        return '\n'.join(prompt_parts)

    def _run_formalization_agent(
        self,
        prompt: str,
    ) -> dict | None:
        """Run agent to produce manifest JSON.

        Args:
            prompt: Formatted prompt for agent

        Returns:
            Parsed JSON dict, or None if agent failed
        """
        result = self.runner.run(
            agent_name='formalization-agent',
            prompt=prompt,
            timeout=300,  # 5 minutes
        )

        if not result.success:
            LOG.error(f'Formalization agent failed: {result.error}')
            return None

        # Try to get JSON from structured output
        if result.data:
            return result.data

        # Try to parse raw output
        try:
            return json.loads(result.raw_output)
        except json.JSONDecodeError:
            LOG.error('Failed to parse agent output as JSON')
            return None

    def _write_manifest(
        self,
        manifest: Manifest,
        spec_dir: Path,
    ) -> None:
        """Write validated manifest to spec_dir.

        Args:
            manifest: Validated Manifest object
            spec_dir: Directory to write manifest.json
        """
        manifest.save(spec_dir)
        LOG.info(f'Manifest written to {spec_dir / "manifest.json"}')

    def _initialize_component_contexts(
        self,
        manifest: Manifest,
        spec_dir: Path,
    ) -> None:
        """Create initial component context files.

        Creates components/<component_id>.md for each component with
        initial structure.

        Args:
            manifest: Manifest with component definitions
            spec_dir: Directory containing spec
        """
        context_manager = ContextManager(spec_dir)
        context_manager.initialize(manifest)
        LOG.info(f'Initialized {len(manifest.components)} component contexts')
