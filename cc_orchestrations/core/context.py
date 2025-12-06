"""Context management for spec execution.

Manages context files that persist information between agent calls.
Agents read context before executing and write updates after completing work.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .paths import expand_path

if TYPE_CHECKING:
    from .manifest import Manifest


@dataclass
class ContextUpdate:
    """Update to apply to context files."""

    summary: str = ''  # What was accomplished
    discoveries: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    for_next_agent: str = ''  # Specific instructions for next agent


class ContextManager:
    """Manages context files for a spec."""

    def __init__(self, spec_dir: Path | str):
        """Initialize context manager.

        Args:
            spec_dir: Path to spec directory (supports ~ expansion)
        """
        self.spec_dir = expand_path(spec_dir)
        self.context_file = self.spec_dir / 'CONTEXT.md'
        self.decisions_file = self.spec_dir / 'DECISIONS.md'
        self.components_dir = self.spec_dir / 'components'

    def get_global_context(self) -> str:
        """Read global CONTEXT.md content.

        Returns:
            Content of CONTEXT.md, or empty string if file doesn't exist
        """
        if not self.context_file.exists():
            return ''
        return self.context_file.read_text()

    def get_component_context(self, component_id: str) -> str:
        """Read component-specific context.

        Args:
            component_id: Component identifier

        Returns:
            Content of component context file, or empty string if doesn't exist
        """
        component_file = self.components_dir / f'{component_id}.md'
        if not component_file.exists():
            return ''
        return component_file.read_text()

    def get_context_for_prompt(self, component_id: str | None = None) -> str:
        """Build full context section for agent prompt.

        Includes:
        - Global context (CONTEXT.md)
        - Relevant decisions (DECISIONS.md)
        - Component-specific context if component_id provided

        Args:
            component_id: Optional component identifier

        Returns:
            Formatted context string for inclusion in agent prompt
        """
        sections = []

        # Global context
        global_context = self.get_global_context()
        if global_context:
            sections.append('# Global Context\n\n' + global_context)

        # Decisions
        if self.decisions_file.exists():
            decisions = self.decisions_file.read_text()
            if decisions:
                sections.append('# Decisions\n\n' + decisions)

        # Component-specific context
        if component_id:
            component_context = self.get_component_context(component_id)
            if component_context:
                sections.append(
                    f'# Component Context: {component_id}\n\n'
                    + component_context
                )

        if not sections:
            return ''

        return '\n\n---\n\n'.join(sections)

    def update_from_result(
        self,
        update: ContextUpdate,
        component_id: str | None = None,
    ) -> None:
        """Update context files from agent result.

        - Appends discoveries to CONTEXT.md
        - Appends decisions to DECISIONS.md
        - Updates component context if component_id provided

        Args:
            update: Context update with discoveries, decisions, blockers
            component_id: Optional component identifier
        """
        timestamp = self._timestamp()

        # Update global context with discoveries and blockers
        if update.discoveries or update.blockers or update.summary:
            self._append_global_context(update, timestamp)

        # Update decisions
        if update.decisions:
            self._append_decisions(update.decisions, timestamp)

        # Update component context
        if component_id:
            self._update_component_context(component_id, update, timestamp)

    def update_component_status(
        self,
        component_id: str,
        status: str,
        summary: str = '',
    ) -> None:
        """Update component context with new status.

        Args:
            component_id: Component identifier
            status: New status (e.g., "IMPLEMENTING", "COMPLETE")
            summary: Optional summary of status change
        """
        timestamp = self._timestamp()
        component_file = self.components_dir / f'{component_id}.md'

        # Ensure components directory exists
        self.components_dir.mkdir(parents=True, exist_ok=True)

        if component_file.exists():
            # Update existing file - replace status section
            content = component_file.read_text()
            lines = content.split('\n')

            # Find and replace status line
            new_lines = []
            for line in lines:
                if line.startswith('## Status'):
                    new_lines.append(line)
                    # Skip old status value
                    continue
                if line.strip() and not line.startswith('#'):
                    # First non-header line after Status section
                    new_lines.append(status)
                    new_lines.append('')
                    if summary:
                        new_lines.append(
                            f"## What's Been Done\n- [{timestamp}] {summary}"
                        )
                    new_lines.append(line)
                    break
                new_lines.append(line)

            # Add remaining lines
            idx = len(new_lines)
            new_lines.extend(lines[idx:])

            component_file.write_text('\n'.join(new_lines))
        else:
            # Create new component context
            content = f"""# Component: {component_id}

## Status
{status}

## Purpose
[To be populated from manifest]

## What's Been Done
- [{timestamp}] {summary or 'Component initialized'}

## Discoveries
[None yet]

## For Next Agent
[No specific instructions]
"""
            component_file.write_text(content)

    def initialize(self, manifest: 'Manifest') -> None:
        """Initialize context files for a new spec execution.

        Creates:
        - CONTEXT.md with initial state
        - DECISIONS.md (empty)
        - components/ directory
        - Component context files for each component in manifest

        Args:
            manifest: Manifest with component definitions
        """
        # Create spec directory if needed
        self.spec_dir.mkdir(parents=True, exist_ok=True)

        # Initialize CONTEXT.md
        timestamp = self._timestamp()
        total_components = len(manifest.components)
        context_content = f"""# Execution Context

## Current State
Status: IN_PROGRESS
Components: 0/{total_components} complete
Last updated: {timestamp}

## Critical Discoveries
[None yet]

## Blockers
[None]

## For Next Agent
Begin with first component in dependency order.
"""
        self.context_file.write_text(context_content)

        # Initialize DECISIONS.md
        decisions_content = f"""# Decisions

All architectural and implementation decisions made during execution.

---

[{timestamp}] Execution initialized
"""
        self.decisions_file.write_text(decisions_content)

        # Create components directory
        self.components_dir.mkdir(parents=True, exist_ok=True)

        # Initialize component contexts
        for component in manifest.components:
            component_file = self.components_dir / f'{component.id}.md'
            component_content = f"""# Component: {component.id}

## Status
PENDING

## Purpose
{component.purpose or '[No purpose specified]'}

## File
{component.file}

## Dependencies
{', '.join(component.depends_on) if component.depends_on else 'None'}

## What's Been Done
[Nothing yet]

## Discoveries
[None yet]

## For Next Agent
{component.notes or '[No specific instructions]'}
"""
            component_file.write_text(component_content)

    def _append_global_context(
        self, update: ContextUpdate, timestamp: str
    ) -> None:
        """Append discoveries and blockers to CONTEXT.md."""
        if not self.context_file.exists():
            # Initialize if missing
            self.context_file.write_text(
                """# Execution Context

## Current State
Status: IN_PROGRESS
Last updated: {timestamp}

## Critical Discoveries
[None yet]

## Blockers
[None]

## For Next Agent
[No instructions]
"""
            )

        content = self.context_file.read_text()
        lines = content.split('\n')

        # Process sections in REVERSE order to avoid index shifting issues
        # 1. Update "For Next Agent" first (at end of file)
        for_next_idx = None
        for i, line in enumerate(lines):
            if line.startswith('## For Next Agent'):
                for_next_idx = i
                break

        if update.for_next_agent and for_next_idx is not None:
            # Replace content after header until next section or EOF
            new_lines = lines[: for_next_idx + 1]
            new_lines.append(update.for_next_agent)

            # Find next section (shouldn't be any after this, but handle it)
            next_section_idx = for_next_idx + 1
            while next_section_idx < len(lines):
                if lines[next_section_idx].startswith('##'):
                    new_lines.extend(lines[next_section_idx:])
                    break
                next_section_idx += 1

            lines = new_lines

        # 2. Insert blockers (before "For Next Agent")
        blockers_idx = None
        for i, line in enumerate(lines):
            if line.startswith('## Blockers'):
                blockers_idx = i
                break

        if update.blockers and blockers_idx is not None:
            insert_idx = blockers_idx + 1
            # Skip to end of section (stop at next ## or EOF)
            while insert_idx < len(lines) and not lines[insert_idx].startswith(
                '##'
            ):
                insert_idx += 1

            # Back up past trailing empty lines
            while (
                insert_idx > blockers_idx + 1
                and lines[insert_idx - 1].strip() == ''
            ):
                insert_idx -= 1

            # Insert new blockers
            for blocker in update.blockers:
                lines.insert(insert_idx, f'- [{timestamp}] {blocker}')
                insert_idx += 1

        # 3. Insert discoveries (before "Blockers")
        discoveries_idx = None
        for i, line in enumerate(lines):
            if line.startswith('## Critical Discoveries'):
                discoveries_idx = i
                break

        if update.discoveries and discoveries_idx is not None:
            insert_idx = discoveries_idx + 1
            # Skip to end of section (stop at next ## or EOF)
            while insert_idx < len(lines) and not lines[insert_idx].startswith(
                '##'
            ):
                insert_idx += 1

            # Back up past trailing empty lines
            while (
                insert_idx > discoveries_idx + 1
                and lines[insert_idx - 1].strip() == ''
            ):
                insert_idx -= 1

            for discovery in update.discoveries:
                lines.insert(insert_idx, f'- [{timestamp}] {discovery}')
                insert_idx += 1

        # Update timestamp in "Current State"
        for i, line in enumerate(lines):
            if line.startswith('Last updated:'):
                lines[i] = f'Last updated: {timestamp}'
                break

        self.context_file.write_text('\n'.join(lines))

    def _append_decisions(self, decisions: list[str], timestamp: str) -> None:
        """Append decisions to DECISIONS.md."""
        if not self.decisions_file.exists():
            self.decisions_file.write_text('# Decisions\n\n')

        content = self.decisions_file.read_text()

        # Append decisions
        decision_entries = [
            f'\n[{timestamp}] {decision}' for decision in decisions
        ]
        content += '\n'.join(decision_entries) + '\n'

        self.decisions_file.write_text(content)

    def _update_component_context(
        self,
        component_id: str,
        update: ContextUpdate,
        timestamp: str,
    ) -> None:
        """Update component-specific context file."""
        component_file = self.components_dir / f'{component_id}.md'

        if not component_file.exists():
            # Create minimal component context
            component_file.write_text(
                f"""# Component: {component_id}

## Status
IN_PROGRESS

## What's Been Done
[Nothing yet]

## Discoveries
[None yet]

## For Next Agent
[No instructions]
"""
            )

        content = component_file.read_text()
        lines = content.split('\n')

        # Process sections in REVERSE order to avoid index shifting
        # 1. Update "For Next Agent" first (at end)
        for_next_idx = None
        for i, line in enumerate(lines):
            if line.startswith('## For Next Agent'):
                for_next_idx = i
                break

        if update.for_next_agent and for_next_idx is not None:
            new_lines = lines[: for_next_idx + 1]
            new_lines.append(update.for_next_agent)

            # Find next section (shouldn't be any)
            next_section_idx = for_next_idx + 1
            while next_section_idx < len(lines):
                if lines[next_section_idx].startswith('##'):
                    new_lines.extend(lines[next_section_idx:])
                    break
                next_section_idx += 1

            lines = new_lines

        # 2. Add discoveries to Discoveries section (before "For Next Agent")
        discoveries_idx = None
        for i, line in enumerate(lines):
            if line.startswith('## Discoveries'):
                discoveries_idx = i
                break

        if update.discoveries and discoveries_idx is not None:
            insert_idx = discoveries_idx + 1
            # Skip to end of section (stop at next ## or EOF)
            while insert_idx < len(lines) and not lines[insert_idx].startswith(
                '##'
            ):
                insert_idx += 1

            # Back up past trailing empty lines
            while (
                insert_idx > discoveries_idx + 1
                and lines[insert_idx - 1].strip() == ''
            ):
                insert_idx -= 1

            for discovery in update.discoveries:
                lines.insert(insert_idx, f'- [{timestamp}] {discovery}')
                insert_idx += 1

        # 3. Add summary to "What's Been Done" (before "Discoveries")
        done_idx = None
        for i, line in enumerate(lines):
            if line.startswith("## What's Been Done"):
                done_idx = i
                break

        if update.summary and done_idx is not None:
            insert_idx = done_idx + 1
            # Skip to end of section (stop at next ## or EOF)
            while insert_idx < len(lines) and not lines[insert_idx].startswith(
                '##'
            ):
                insert_idx += 1

            # Back up past trailing empty lines
            while (
                insert_idx > done_idx + 1
                and lines[insert_idx - 1].strip() == ''
            ):
                insert_idx -= 1

            lines.insert(insert_idx, f'- [{timestamp}] {update.summary}')

        component_file.write_text('\n'.join(lines))

    @staticmethod
    def _timestamp() -> str:
        """Generate ISO 8601 timestamp with UTC timezone.

        Returns:
            Timestamp string in format: 2025-12-05T10:00:00Z
        """
        return datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
