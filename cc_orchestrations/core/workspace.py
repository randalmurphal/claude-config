"""Workspace management for orchestration context.

The Workspace provides a PULL-based context model where agents receive minimal
context by default but can read additional files on demand. This replaces the
PUSH model where full spec content was injected into every prompt.

Directory structure:
    .workspace/
        INDEX.md                 # Navigation header (always injected)
        spec/
            OVERVIEW.md          # High-level summary (default injection)
            requirements.md      # Functional requirements
            architecture.md      # Technical approach
            components.md        # Component definitions
            gotchas.md           # Edge cases and pitfalls
            testing.md           # Testing requirements
        components/
            <component-id>.md    # Per-component status and context
        DISCOVERIES.md           # Append-only: findings during work
        DECISIONS.md             # Append-only: architectural decisions
        BLOCKERS.md              # Current blockers (mutable)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .manifest import Manifest

LOG = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class WorkspaceConfig:
    """Configuration for context injection per agent type.

    Controls what workspace content is automatically injected into prompts.
    Agents can always read additional files via the Read tool.
    """

    inject_index: bool = True
    """Always inject INDEX.md navigation header."""

    inject_overview: bool = True
    """Inject spec/OVERVIEW.md summary."""

    inject_component: bool = True
    """Inject current component's context file."""

    additional_sections: list[str] = field(default_factory=list)
    """Additional spec sections to inject (e.g., ['architecture', 'testing'])."""


# Default configurations per agent type
# Agents not listed get WorkspaceConfig() (index + overview + component)
AGENT_WORKSPACE_DEFAULTS: dict[str, WorkspaceConfig] = {
    # Skeleton builder needs architecture to understand patterns
    'skeleton_builder': WorkspaceConfig(
        additional_sections=['architecture'],
    ),
    # Implementation executor just needs component context
    'implementation_executor': WorkspaceConfig(),
    # Validator needs testing requirements and gotchas
    'validator': WorkspaceConfig(
        additional_sections=['testing', 'gotchas'],
    ),
    # Fix executor only needs the issues - minimal context
    'fix_executor': WorkspaceConfig(
        inject_overview=False,
    ),
    # Investigator needs full picture
    'investigator': WorkspaceConfig(
        additional_sections=['architecture', 'requirements'],
    ),
    # Impact analyzer focuses on architecture
    'impact_analyzer': WorkspaceConfig(
        additional_sections=['architecture'],
    ),
    # Spec parser just needs to read files
    'spec_parser': WorkspaceConfig(
        inject_overview=False,
        inject_component=False,
    ),
    # Test runner needs testing section
    'test_runner': WorkspaceConfig(
        additional_sections=['testing'],
    ),
    # Security auditor needs gotchas
    'security_auditor': WorkspaceConfig(
        additional_sections=['gotchas', 'architecture'],
    ),
}


# =============================================================================
# INDEX.md Template
# =============================================================================

INDEX_TEMPLATE = """# Workspace Navigation

Read files with the Read tool when you need more context.

## Spec Sections
| File | Contents |
|------|----------|
| `.workspace/spec/OVERVIEW.md` | High-level summary and goals |
| `.workspace/spec/requirements.md` | Functional requirements |
| `.workspace/spec/architecture.md` | Technical approach and patterns |
| `.workspace/spec/components.md` | Component definitions and dependencies |
| `.workspace/spec/gotchas.md` | Edge cases and pitfalls to avoid |
| `.workspace/spec/testing.md` | Testing requirements and strategy |

## Component Context
- `.workspace/components/<id>.md` - Per-component status, context, blockers

## Shared Knowledge
| File | Purpose | How to Use |
|------|---------|------------|
| `.workspace/DISCOVERIES.md` | Findings during work | Append with Write tool |
| `.workspace/DECISIONS.md` | Architectural decisions | Append with Write tool |
| `.workspace/BLOCKERS.md` | Current blockers | Update as needed |

**Instructions**: Read additional files when you need context. Append discoveries when you learn something important for other agents.
"""


# =============================================================================
# Spec Section Headers
# =============================================================================

# Mapping of section keywords to output filenames
# Used for heuristic parsing of SPEC.md into sections
SECTION_MAPPINGS: list[tuple[list[str], str]] = [
    # Requirements section
    (
        ['requirements', 'functional requirements', 'user requirements'],
        'requirements.md',
    ),
    # Architecture section
    (
        ['architecture', 'technical', 'design', 'approach', 'implementation'],
        'architecture.md',
    ),
    # Components section
    (
        ['components', 'files', 'modules', 'file changes', 'files to create'],
        'components.md',
    ),
    # Testing section
    (['testing', 'tests', 'validation', 'quality'], 'testing.md'),
    # Gotchas section
    (
        ['gotchas', 'edge cases', 'pitfalls', 'known issues', 'caveats'],
        'gotchas.md',
    ),
]


# =============================================================================
# Component Template
# =============================================================================

COMPONENT_TEMPLATE = """# Component: {component_id}

## File
`{file_path}`

## Purpose
{purpose}

## Dependencies
{dependencies}

## Status
{status}

## Context
{context}

## For Next Agent
{for_next_agent}
"""


# =============================================================================
# Workspace Class
# =============================================================================


class Workspace:
    """Manages workspace files within a worktree.

    The workspace provides:
    - Parsed spec sections for selective context injection
    - Per-component context files
    - Append-only shared knowledge files
    - Navigation index for agents to find more context

    Usage:
        workspace = Workspace(worktree_path)
        workspace.initialize(manifest, spec_content)

        # Get context for an agent
        context = workspace.get_context_for_agent('skeleton_builder', 'component_a')

        # Update shared knowledge
        workspace.append_discovery("Found existing pattern in utils.py", "skeleton_builder")
    """

    def __init__(self, worktree_path: Path | str):
        """Initialize workspace manager.

        Args:
            worktree_path: Path to the worktree root
        """
        self.worktree_path = Path(worktree_path)
        self.root = self.worktree_path / '.workspace'
        self.spec_dir = self.root / 'spec'
        self.components_dir = self.root / 'components'

    @property
    def is_initialized(self) -> bool:
        """Check if workspace has been initialized."""
        return (self.root / 'INDEX.md').exists()

    def initialize(
        self,
        manifest: 'Manifest',
        spec_content: str,
        project_context: str = '',
    ) -> None:
        """Initialize workspace from manifest and spec.

        Creates directory structure, parses spec into sections,
        and creates component context files.

        Args:
            manifest: Manifest with component definitions
            spec_content: Full SPEC.md content to parse
            project_context: Optional project context to include in overview
        """
        LOG.info(f'Initializing workspace at {self.root}')

        # Create directory structure
        self.root.mkdir(parents=True, exist_ok=True)
        self.spec_dir.mkdir(exist_ok=True)
        self.components_dir.mkdir(exist_ok=True)

        # Parse spec into sections
        self._parse_spec_into_sections(spec_content, project_context)

        # Create component files from manifest
        self._initialize_component_files(manifest)

        # Create shared knowledge files
        self._initialize_shared_files()

        # Create navigation index
        self._create_index()

        LOG.info(
            f'Workspace initialized with {len(manifest.components)} components'
        )

    def _parse_spec_into_sections(
        self,
        spec_content: str,
        project_context: str = '',
    ) -> None:
        """Parse SPEC.md into separate section files.

        Uses heuristic header matching to split spec into logical sections.
        Unmatched content goes into OVERVIEW.md.
        """
        # Split by markdown headers (## or ###)
        sections = self._split_by_headers(spec_content)

        # Categorize sections
        categorized: dict[str, list[str]] = {
            'overview': [],
            'requirements.md': [],
            'architecture.md': [],
            'components.md': [],
            'testing.md': [],
            'gotchas.md': [],
        }

        for header, content in sections:
            matched = False
            header_lower = header.lower()

            for keywords, filename in SECTION_MAPPINGS:
                if any(kw in header_lower for kw in keywords):
                    categorized[filename].append(f'## {header}\n\n{content}')
                    matched = True
                    break

            if not matched:
                categorized['overview'].append(f'## {header}\n\n{content}')

        # Write section files
        for filename, contents in categorized.items():
            if filename == 'overview':
                # OVERVIEW.md includes project context
                overview_parts = []
                if project_context:
                    overview_parts.append(
                        f'# Project Context\n\n{project_context}'
                    )
                overview_parts.extend(contents)
                self._write_spec_file(
                    'OVERVIEW.md',
                    '\n\n---\n\n'.join(overview_parts)
                    if overview_parts
                    else '# Overview\n\nNo overview content.',
                )
            elif contents:
                self._write_spec_file(filename, '\n\n'.join(contents))
            else:
                # Create empty placeholder
                self._write_spec_file(
                    filename,
                    f'# {filename.replace(".md", "").title()}\n\nNo content for this section.',
                )

    def _split_by_headers(self, content: str) -> list[tuple[str, str]]:
        """Split markdown content by ## headers.

        Returns:
            List of (header_text, section_content) tuples
        """
        # Pattern matches ## or ### headers
        header_pattern = re.compile(r'^(#{2,3})\s+(.+)$', re.MULTILINE)

        sections: list[tuple[str, str]] = []
        matches = list(header_pattern.finditer(content))

        if not matches:
            # No headers found, return entire content as overview
            return [('Overview', content.strip())]

        # Handle content before first header
        if matches[0].start() > 0:
            preamble = content[: matches[0].start()].strip()
            if preamble:
                sections.append(('Overview', preamble))

        # Extract each section
        for i, match in enumerate(matches):
            header_text = match.group(2).strip()

            # Content runs from end of this header to start of next (or EOF)
            content_start = match.end()
            content_end = (
                matches[i + 1].start() if i + 1 < len(matches) else len(content)
            )
            section_content = content[content_start:content_end].strip()

            sections.append((header_text, section_content))

        return sections

    def _write_spec_file(self, filename: str, content: str) -> None:
        """Write a spec section file."""
        file_path = self.spec_dir / filename
        file_path.write_text(content)
        LOG.debug(f'Wrote spec section: {filename}')

    def _initialize_component_files(self, manifest: 'Manifest') -> None:
        """Create component context files from manifest."""
        for component in manifest.components:
            component_file = self.components_dir / f'{component.id}.md'

            # Format dependencies
            deps = (
                ', '.join(component.depends_on)
                if component.depends_on
                else 'None'
            )

            content = COMPONENT_TEMPLATE.format(
                component_id=component.id,
                file_path=component.file,
                purpose=component.purpose or 'Not specified',
                dependencies=deps,
                status='PENDING',
                context=component.notes or 'No additional context.',
                for_next_agent='Begin implementation.',
            )

            component_file.write_text(content)

    def _initialize_shared_files(self) -> None:
        """Create shared knowledge files."""
        timestamp = self._timestamp()

        # DISCOVERIES.md
        discoveries = f"""# Discoveries

Important findings captured during implementation.

---

[{timestamp}] Workspace initialized
"""
        (self.root / 'DISCOVERIES.md').write_text(discoveries)

        # DECISIONS.md
        decisions = f"""# Decisions

Architectural and implementation decisions made during work.

---

[{timestamp}] Workspace initialized
"""
        (self.root / 'DECISIONS.md').write_text(decisions)

        # BLOCKERS.md
        blockers = """# Current Blockers

Issues blocking progress. Update as blockers are resolved.

---

No current blockers.
"""
        (self.root / 'BLOCKERS.md').write_text(blockers)

    def _create_index(self) -> None:
        """Create the INDEX.md navigation file."""
        (self.root / 'INDEX.md').write_text(INDEX_TEMPLATE)

    # =========================================================================
    # Context Retrieval
    # =========================================================================

    def get_context_for_agent(
        self,
        agent_type: str,
        component_id: str | None = None,
        config_override: WorkspaceConfig | None = None,
    ) -> str:
        """Get context string for an agent.

        Returns minimal context based on agent type configuration.
        Agents can read additional files via Read tool.

        Args:
            agent_type: Type of agent (e.g., 'skeleton_builder')
            component_id: Current component ID (optional)
            config_override: Override default config for this agent

        Returns:
            Formatted context string to inject into prompt
        """
        config = config_override or AGENT_WORKSPACE_DEFAULTS.get(
            agent_type, WorkspaceConfig()
        )

        parts: list[str] = []

        # Always inject navigation index
        if config.inject_index:
            index_content = self._read_file('INDEX.md')
            if index_content:
                parts.append(index_content)

        # Inject overview
        if config.inject_overview:
            overview = self._read_file('spec/OVERVIEW.md')
            if overview:
                parts.append(overview)

        # Inject additional sections
        for section in config.additional_sections:
            section_file = f'spec/{section}.md'
            content = self._read_file(section_file)
            if content:
                parts.append(content)

        # Inject component context
        if config.inject_component and component_id:
            component_context = self.get_component_context(component_id)
            if component_context:
                parts.append(component_context)

        return '\n\n---\n\n'.join(parts) if parts else ''

    def get_navigation_header(self) -> str:
        """Get just the INDEX.md navigation header.

        Useful for prompts that only need navigation, not content.
        """
        return self._read_file('INDEX.md') or ''

    def get_component_context(self, component_id: str) -> str:
        """Get context for a specific component.

        Args:
            component_id: Component identifier

        Returns:
            Component context content or empty string
        """
        return self._read_file(f'components/{component_id}.md') or ''

    def get_spec_section(self, section: str) -> str:
        """Get a specific spec section.

        Args:
            section: Section name (e.g., 'requirements', 'architecture')

        Returns:
            Section content or empty string
        """
        # Handle with or without .md extension
        if not section.endswith('.md'):
            section = f'{section}.md'

        return self._read_file(f'spec/{section}') or ''

    def _read_file(self, relative_path: str) -> str | None:
        """Read a workspace file.

        Args:
            relative_path: Path relative to .workspace/

        Returns:
            File content or None if not found
        """
        file_path = self.root / relative_path
        if file_path.exists():
            return file_path.read_text()
        return None

    # =========================================================================
    # Context Updates
    # =========================================================================

    def append_discovery(
        self,
        discovery: str,
        source_agent: str,
    ) -> None:
        """Append a discovery to DISCOVERIES.md.

        Args:
            discovery: The discovery text
            source_agent: Name of agent that made the discovery
        """
        timestamp = self._timestamp()
        entry = f'\n[{timestamp}] ({source_agent}) {discovery}\n'

        discoveries_file = self.root / 'DISCOVERIES.md'
        content = discoveries_file.read_text()
        discoveries_file.write_text(content + entry)

        LOG.debug(f'Discovery added: {discovery[:50]}...')

    def append_decision(
        self,
        decision: str,
        rationale: str,
        source_agent: str = '',
    ) -> None:
        """Append a decision to DECISIONS.md.

        Args:
            decision: The decision made
            rationale: Why this decision was made
            source_agent: Name of agent that made the decision
        """
        timestamp = self._timestamp()
        source = f' ({source_agent})' if source_agent else ''
        entry = f'\n[{timestamp}]{source} **{decision}**\n\n{rationale}\n'

        decisions_file = self.root / 'DECISIONS.md'
        content = decisions_file.read_text()
        decisions_file.write_text(content + entry)

        LOG.debug(f'Decision added: {decision}')

    def update_blocker(
        self,
        blocker: str,
        resolved: bool = False,
    ) -> None:
        """Update BLOCKERS.md with a blocker.

        Args:
            blocker: Description of the blocker
            resolved: If True, marks blocker as resolved
        """
        timestamp = self._timestamp()
        status = 'RESOLVED' if resolved else 'BLOCKING'
        entry = f'\n[{timestamp}] [{status}] {blocker}\n'

        blockers_file = self.root / 'BLOCKERS.md'
        content = blockers_file.read_text()

        # Remove "No current blockers" placeholder if present
        content = content.replace('No current blockers.', '')

        blockers_file.write_text(content + entry)

    def update_component_status(
        self,
        component_id: str,
        status: str,
        for_next_agent: str = '',
        context: str = '',
    ) -> None:
        """Update a component's status and context.

        Args:
            component_id: Component identifier
            status: New status (e.g., 'IMPLEMENTING', 'COMPLETE')
            for_next_agent: Instructions for next agent
            context: Additional context to add
        """
        component_file = self.components_dir / f'{component_id}.md'

        if not component_file.exists():
            LOG.warning(f'Component file not found: {component_id}')
            return

        content = component_file.read_text()

        # Update status
        content = re.sub(
            r'## Status\n.*?(?=\n##|\Z)',
            f'## Status\n{status}\n',
            content,
            flags=re.DOTALL,
        )

        # Update for_next_agent if provided
        if for_next_agent:
            content = re.sub(
                r'## For Next Agent\n.*?(?=\n##|\Z)',
                f'## For Next Agent\n{for_next_agent}\n',
                content,
                flags=re.DOTALL,
            )

        # Append to context if provided
        if context:
            timestamp = self._timestamp()
            context_entry = f'\n\n[{timestamp}] {context}'
            content = re.sub(
                r'(## Context\n.*?)(?=\n## For Next Agent)',
                rf'\1{context_entry}',
                content,
                flags=re.DOTALL,
            )

        component_file.write_text(content)

    # =========================================================================
    # Utilities
    # =========================================================================

    @staticmethod
    def _timestamp() -> str:
        """Generate ISO 8601 timestamp."""
        return datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')

    def list_components(self) -> list[str]:
        """List all component IDs in workspace."""
        if not self.components_dir.exists():
            return []

        return [f.stem for f in self.components_dir.glob('*.md')]

    def get_all_discoveries(self) -> str:
        """Get all discoveries content."""
        return self._read_file('DISCOVERIES.md') or ''

    def get_all_decisions(self) -> str:
        """Get all decisions content."""
        return self._read_file('DECISIONS.md') or ''


# =============================================================================
# Helper Functions
# =============================================================================


def create_workspace(
    worktree_path: Path | str,
    manifest: 'Manifest',
    spec_content: str,
    project_context: str = '',
) -> Workspace:
    """Create and initialize a workspace.

    Convenience function that creates a Workspace and initializes it.

    Args:
        worktree_path: Path to worktree root
        manifest: Manifest with component definitions
        spec_content: Full SPEC.md content
        project_context: Optional project context

    Returns:
        Initialized Workspace
    """
    workspace = Workspace(worktree_path)
    workspace.initialize(manifest, spec_content, project_context)
    return workspace
