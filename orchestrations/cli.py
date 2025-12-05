"""Unified orchestration CLI.

Provides a single entry point for all workflow types and spec management.
Replaces workflow-specific CLIs with a unified interface.
"""

import argparse
import logging
import sys
from pathlib import Path

from .core import Manifest, expand_path, get_specs_dir
from .core.state import StateManager
from .spec.validator import ManifestValidator


LOG = logging.getLogger(__name__)


def cmd_run(args: argparse.Namespace) -> int:
    """Run a spec.

    Args:
        args: Parsed command-line arguments with 'spec' and 'fresh' fields.

    Returns:
        0 on success, 1 on failure.
    """
    spec_path = resolve_spec_path(args.spec)

    if not spec_path.exists():
        print(f'Error: Spec not found: {args.spec}')
        print(f'Expected path: {spec_path}')
        return 1

    # Check for manifest.json
    manifest_path = spec_path / 'manifest.json'
    if not manifest_path.exists():
        print(f'Error: No manifest.json found in {spec_path}')
        print('Run the /spec command to generate a manifest first.')
        return 1

    try:
        manifest = Manifest.load(spec_path)
    except (FileNotFoundError, ValueError) as e:
        print(f'Error loading manifest: {e}')
        return 1

    # TODO: Once workflow refactor is complete, dynamically select workflow type
    # For now, print a helpful message about using the old conduct CLI
    print(f'Spec: {manifest.name}')
    print(f'Project: {manifest.project}')
    print(f'Work dir: {manifest.work_dir}')
    print(f'Components: {len(manifest.components)}')
    print()
    print('Note: Workflow execution is not yet implemented in the unified CLI.')
    print('Use the legacy conduct CLI for now:')
    print('  cd ~/.claude/orchestrations/conduct')
    print(f'  python -m conduct --spec {spec_path / "SPEC.md"}')
    print()
    print(
        "Once the refactor is complete, you'll be able to run specs directly with:"
    )
    print(f'  python -m orchestrations run --spec {args.spec}')

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all specs or specs for a specific project.

    Args:
        args: Parsed command-line arguments with optional 'project' field.

    Returns:
        0 on success, 1 on failure.
    """
    specs_dir = get_specs_dir()

    if not specs_dir.exists():
        print(f'Specs directory not found: {specs_dir}')
        print('Create it with: mkdir -p ~/.claude/orchestrations/specs')
        return 1

    # Determine which projects to list
    if args.project:
        project_dirs = [specs_dir / args.project]
        if not project_dirs[0].exists():
            print(f'Project not found: {args.project}')
            return 1
    else:
        # List all projects
        project_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]

    if not project_dirs:
        print('No projects found in specs directory.')
        print(f'Specs directory: {specs_dir}')
        return 0

    # List specs for each project
    for project_dir in sorted(project_dirs):
        spec_dirs = [d for d in project_dir.iterdir() if d.is_dir()]

        if not spec_dirs:
            continue

        print(f'\n{project_dir.name}/')

        for spec_dir in sorted(spec_dirs):
            status = get_spec_status(spec_dir)
            print(f'  {spec_dir.name:60} [{status}]')

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show detailed status of a spec.

    Args:
        args: Parsed command-line arguments with 'spec' field.

    Returns:
        0 on success, 1 on failure.
    """
    spec_path = resolve_spec_path(args.spec)

    if not spec_path.exists():
        print(f'Error: Spec not found: {args.spec}')
        print(f'Expected path: {spec_path}')
        return 1

    # Load manifest
    try:
        manifest = Manifest.load(spec_path)
    except (FileNotFoundError, ValueError) as e:
        print(f'Error loading manifest: {e}')
        return 1

    # Display manifest info
    print(f'Spec: {args.spec}')
    print(f'Name: {manifest.name}')
    print(f'Project: {manifest.project}')
    print(f'Work dir: {manifest.work_dir}')
    print(f'Components: {len(manifest.components)}')
    print(f'Complexity: {manifest.complexity}/10')
    print(f'Risk: {manifest.risk_level}')
    print(f'Mode: {manifest.execution.mode}')
    print(f'Reviewers: {manifest.execution.reviewers}')
    print(f'Tests required: {manifest.execution.require_tests}')

    # Check for execution state
    state_file = spec_path / 'STATE.json'
    if state_file.exists():
        try:
            state_mgr = StateManager(spec_path)
            state = state_mgr.load()

            print('\n--- Execution State ---')
            print(f'Phase: {state.current_phase}')
            print(f'Status: {state.phase_status.value}')

            if state.components:
                completed = sum(
                    1
                    for c in state.components.values()
                    if c.status.value == 'complete'
                )
                total = len(state.components)
                print(f'Progress: {completed}/{total} components complete')

                if state.current_component:
                    print(f'Current: {state.current_component}')

            if state.discoveries:
                print(f'\nDiscoveries: {len(state.discoveries)}')
                for i, discovery in enumerate(state.discoveries[-3:], 1):
                    print(f'  {i}. {discovery[:80]}...')

            if state.error:
                print(f'\nError: {state.error}')

        except Exception as e:
            print(f'\nWarning: Could not load execution state: {e}')
    else:
        print('\n(No execution state - spec has not been run)')

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a spec manifest without executing.

    Args:
        args: Parsed command-line arguments with 'spec' field.

    Returns:
        0 if valid, 1 if invalid or errors found.
    """
    spec_path = resolve_spec_path(args.spec)

    if not spec_path.exists():
        print(f'Error: Spec not found: {args.spec}')
        print(f'Expected path: {spec_path}')
        return 1

    # Load manifest
    try:
        manifest = Manifest.load(spec_path)
    except (FileNotFoundError, ValueError) as e:
        print(f'Error loading manifest: {e}')
        return 1

    # Validate
    validator = ManifestValidator()
    result = validator.validate(manifest)

    if result.valid:
        print('✓ Manifest is valid')

        if result.warnings:
            print(f'\nWarnings ({len(result.warnings)}):')
            for warning in result.warnings:
                print(f'  {warning.field}: {warning.error}')
                if warning.suggestion:
                    print(f'    → {warning.suggestion}')

        return 0
    print(f'✗ Validation failed ({len(result.errors)} errors)\n')

    for error in result.errors:
        print(f'  {error.field}:')
        print(f'    Error: {error.error}')
        if error.suggestion:
            print(f'    Fix: {error.suggestion}')
        print()

    return 1


def cmd_new(args: argparse.Namespace) -> int:
    """Create a new spec directory structure.

    Args:
        args: Parsed command-line arguments with 'project' and 'name' fields.

    Returns:
        0 on success, 1 on failure.
    """
    import secrets

    # Generate unique hash suffix
    hash_suffix = secrets.token_hex(4)
    spec_name = f'{args.name}-{hash_suffix}'
    spec_path = get_specs_dir() / args.project / spec_name

    # Create directory structure
    try:
        spec_path.mkdir(parents=True, exist_ok=False)
        (spec_path / 'brainstorm').mkdir()
        (spec_path / 'components').mkdir()

        # Create placeholder files
        (spec_path / 'SPEC.md').write_text(
            f"""# {args.name}

## Context

[Describe the problem or feature this spec addresses]

## Approach

[Outline the solution approach]

## Components

[List components to create/modify]

## Success Criteria

[Define what success looks like]
"""
        )

        (spec_path / 'brainstorm' / 'README.md').write_text(
            """# Brainstorm

This directory contains working documents and notes from the /spec investigation phase.

These files are used to generate the formal manifest.json.
"""
        )

        print(f'✓ Created spec: {args.project}/{spec_name}')
        print(f'  Path: {spec_path}')
        print()
        print('Next steps:')
        print('  1. Edit SPEC.md with your requirements')
        print('  2. Run /spec to formalize into manifest.json')
        print(
            f'  3. Run: python -m orchestrations run --spec {args.project}/{spec_name}'
        )

        return 0

    except FileExistsError:
        print(f'Error: Spec directory already exists: {spec_path}')
        return 1
    except OSError as e:
        print(f'Error creating spec directory: {e}')
        return 1


def resolve_spec_path(spec_ref: str) -> Path:
    """Resolve a spec reference to an absolute path.

    Accepts either:
    - project/name format: "claude-config/orchestration-refactor-228fbe82"
    - Absolute path: "/home/user/.claude/orchestrations/specs/..."
    - Home-relative path: "~/.claude/orchestrations/specs/..."

    Args:
        spec_ref: Spec reference string.

    Returns:
        Absolute Path to the spec directory.
    """
    # If it contains / but doesn't start with / or ~, assume project/name format
    if '/' in spec_ref and not spec_ref.startswith(('/', '~')):
        return get_specs_dir() / spec_ref

    # Otherwise treat as a path
    return expand_path(spec_ref)


def get_spec_status(spec_dir: Path) -> str:
    """Get the status of a spec.

    Args:
        spec_dir: Path to the spec directory.

    Returns:
        Status string: "not_started", "in_progress", "complete", "error", or "no_manifest".
    """
    # Check for manifest
    manifest_path = spec_dir / 'manifest.json'
    if not manifest_path.exists():
        return 'no_manifest'

    # Check for state
    state_file = spec_dir / 'STATE.json'
    if not state_file.exists():
        return 'not_started'

    # Load state and check status
    try:
        state_mgr = StateManager(spec_dir)
        state = state_mgr.load()

        if state.error:
            return 'error'

        if state.completed_at:
            return 'complete'

        if state.current_phase != 'init':
            return 'in_progress'

        return 'not_started'

    except Exception:
        return 'error'


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description='Unified orchestration CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a spec
  python -m orchestrations run --spec claude-config/my-spec-abc123

  # List all specs
  python -m orchestrations list

  # List specs for a project
  python -m orchestrations list --project claude-config

  # Show spec status
  python -m orchestrations status --spec claude-config/my-spec-abc123

  # Validate a manifest
  python -m orchestrations validate --spec claude-config/my-spec-abc123

  # Create new spec directory
  python -m orchestrations new --project my-project --name feature-name
""",
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # run command
    run_parser = subparsers.add_parser(
        'run', help='Run a spec', description='Execute a spec workflow'
    )
    run_parser.add_argument(
        '--spec',
        required=True,
        help='Spec path (project/name or absolute path)',
    )
    run_parser.add_argument(
        '--fresh',
        action='store_true',
        help='Start fresh (ignore existing state)',
    )

    # list command
    list_parser = subparsers.add_parser(
        'list',
        help='List specs',
        description='List all specs or specs for a specific project',
    )
    list_parser.add_argument(
        '--project',
        help='Filter by project name',
    )

    # status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show spec status',
        description='Display detailed status of a spec',
    )
    status_parser.add_argument(
        '--spec',
        required=True,
        help='Spec path (project/name or absolute path)',
    )

    # validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate spec',
        description='Validate a spec manifest without executing',
    )
    validate_parser.add_argument(
        '--spec',
        required=True,
        help='Spec path (project/name or absolute path)',
    )

    # new command
    new_parser = subparsers.add_parser(
        'new',
        help='Create new spec',
        description='Create a new spec directory structure',
    )
    new_parser.add_argument(
        '--project',
        required=True,
        help='Project name',
    )
    new_parser.add_argument(
        '--name',
        required=True,
        help='Spec name (hash will be appended)',
    )

    # Parse arguments
    args = parser.parse_args()

    # Dispatch to command handler
    commands = {
        'run': cmd_run,
        'list': cmd_list,
        'status': cmd_status,
        'validate': cmd_validate,
        'new': cmd_new,
    }

    if args.command in commands:
        return commands[args.command](args)

    # No command specified
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
