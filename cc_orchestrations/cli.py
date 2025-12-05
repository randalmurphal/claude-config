"""Unified orchestration CLI.

Provides a single entry point for all workflow types and spec management.
Specs are stored per-project in <git_root>/.claude/specs/<name>-<hash>/.
"""

import argparse
import logging
import sys
from pathlib import Path

from .core import Manifest, expand_path, get_specs_dir, get_project_name, get_git_root
from .core.state import StateManager
from .spec.validator import ManifestValidator


LOG = logging.getLogger(__name__)


def cmd_run(args: argparse.Namespace) -> int:
    """Run a spec.

    Args:
        args: Parsed command-line arguments with 'spec', 'fresh', and 'dry_run' fields.

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

    dry_run = getattr(args, 'dry_run', False)

    if dry_run:
        return _run_dry_run(manifest, spec_path)

    # Full execution
    return _run_workflow(manifest, spec_path, fresh=args.fresh)


def _run_dry_run(manifest: Manifest, spec_path: Path) -> int:
    """Execute a dry-run showing execution plan and testing infrastructure.

    Args:
        manifest: Loaded manifest
        spec_path: Path to spec directory

    Returns:
        0 on success, 1 on failure
    """
    print('=' * 60)
    print('DRY RUN - Execution Plan')
    print('=' * 60)
    print()

    # Basic info
    print(f'Spec: {manifest.name}')
    print(f'Project: {manifest.project}')
    print(f'Work dir: {manifest.work_dir}')
    print(f'Spec dir: {spec_path}')
    print()

    # Execution settings
    print('Execution Settings:')
    print(f'  Mode: {manifest.execution.mode}')
    print(f'  Parallel: {manifest.execution.parallel_components}')
    print(f'  Reviewers: {manifest.execution.reviewers}')
    print(f'  Tests required: {manifest.execution.require_tests}')
    print(f'  Complexity: {manifest.complexity}/10')
    print(f'  Risk: {manifest.risk_level}')
    print()

    # Components in dependency order
    print('Components (execution order):')
    try:
        order = manifest.get_dependency_order()
        for i, comp_id in enumerate(order, 1):
            comp = manifest.get_component(comp_id)
            deps = f' (deps: {", ".join(comp.depends_on)})' if comp.depends_on else ''
            print(f'  {i}. {comp_id}: {comp.file}{deps}')
            if comp.purpose:
                print(f'      Purpose: {comp.purpose}')
    except ValueError as e:
        print(f'  Error: {e}')
        return 1
    print()

    # Gotchas
    if manifest.gotchas:
        print('Gotchas to watch for:')
        for gotcha in manifest.gotchas:
            print(f'  - {gotcha}')
        print()

    # Quality requirements
    print('Quality Requirements:')
    print(f'  Coverage target: {manifest.quality.coverage_target}%')
    print(f'  Lint required: {manifest.quality.lint_required}')
    print(f'  Security scan: {manifest.quality.security_scan}')
    if manifest.validation_command:
        print(f'  Validation: {manifest.validation_command}')
    print()

    # Test runner infrastructure
    print('Testing runner infrastructure...')
    try:
        from .core.runner import AgentRunner
        from .core.config import Config, AgentConfig

        # Create minimal config for testing
        import os
        claude_path = os.path.expanduser('~/.claude/local/claude')
        config = Config(
            name='dry-run-test',
            dry_run=True,
            claude_path=claude_path,
        )

        runner = AgentRunner(
            config=config,
            work_dir=manifest.resolve_work_dir(),
            dry_run=True,
        )

        # Test with a simple prompt
        print('  Running test agent (haiku, dry-run mode)...')
        result = runner.run(
            agent_name='test-agent',
            prompt='Return a JSON object with status="ok" and message="dry-run test successful"',
            dry_run=True,
        )

        if result.success:
            print(f'  ✓ Runner test passed ({result.duration:.1f}s)')
            print(f'    Response: {result.data}')
        else:
            print(f'  ✗ Runner test failed: {result.error}')
            return 1

    except Exception as e:
        print(f'  ✗ Runner infrastructure error: {e}')
        return 1

    print()
    print('=' * 60)
    print('DRY RUN COMPLETE - Ready to execute')
    print('=' * 60)
    print()
    print(f'To run for real: python -m cc_orchestrations run --spec {manifest.name}')

    return 0


def _run_workflow(manifest: Manifest, spec_path: Path, fresh: bool = False) -> int:
    """Execute the actual workflow.

    Args:
        manifest: Loaded manifest
        spec_path: Path to spec directory
        fresh: Start fresh, ignoring existing state

    Returns:
        0 on success, 1 on failure
    """
    print(f'Spec: {manifest.name}')
    print(f'Project: {manifest.project}')
    print(f'Work dir: {manifest.work_dir}')
    print(f'Components: {len(manifest.components)}')
    print()

    # TODO: Wire up to WorkflowEngine once Config/Manifest alignment is done
    print('Note: Full workflow execution not yet implemented.')
    print('Use --dry-run to test the infrastructure.')
    print()
    print('For now, the workflow can be run via the conduct CLI:')
    print(f'  cd {spec_path}')
    print('  # Run /conduct from Claude Code')

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all specs in the current project.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        specs_dir = get_specs_dir()
        project_name = get_project_name()
    except RuntimeError as e:
        print(f'Error: {e}')
        print('Run this command from within a git repository.')
        return 1

    if not specs_dir.exists():
        print(f'No specs directory found for project: {project_name}')
        print(f'Create a spec with: python -m cc_orchestrations new --name my-feature')
        return 0

    spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]

    if not spec_dirs:
        print(f'No specs found in {project_name}')
        print(f'Specs directory: {specs_dir}')
        return 0

    print(f'\nSpecs in {project_name}:\n')

    for spec_dir in sorted(spec_dirs):
        status = get_spec_status(spec_dir)
        print(f'  {spec_dir.name:50} [{status}]')

    print()
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
        args: Parsed command-line arguments with 'name' field.

    Returns:
        0 on success, 1 on failure.
    """
    import secrets

    try:
        specs_dir = get_specs_dir()
        project_name = get_project_name()
    except RuntimeError as e:
        print(f'Error: {e}')
        print('Run this command from within a git repository.')
        return 1

    # Generate unique hash suffix
    hash_suffix = secrets.token_hex(4)
    spec_name = f'{args.name}-{hash_suffix}'
    spec_path = specs_dir / spec_name

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

        print(f'✓ Created spec: {spec_name}')
        print(f'  Project: {project_name}')
        print(f'  Path: {spec_path}')
        print()
        print('Next steps:')
        print('  1. Edit SPEC.md with your requirements')
        print('  2. Run /spec to formalize into manifest.json')
        print(f'  3. Run: python -m cc_orchestrations run --spec {spec_name}')

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
    - Spec name: "my-feature-abc123" (looks in current project)
    - Absolute path: "/home/user/project/.claude/specs/..."
    - Home-relative path: "~/.claude/specs/..."

    Args:
        spec_ref: Spec reference string.

    Returns:
        Absolute Path to the spec directory.
    """
    # If it starts with / or ~, treat as a path
    if spec_ref.startswith(('/', '~')):
        return expand_path(spec_ref)

    # Otherwise, look in current project's specs dir
    return get_specs_dir() / spec_ref


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
  # List specs in current project
  python -m cc_orchestrations list

  # Create new spec
  python -m cc_orchestrations new --name feature-name

  # Show spec status
  python -m cc_orchestrations status --spec my-feature-abc123

  # Validate a manifest
  python -m cc_orchestrations validate --spec my-feature-abc123

  # Run a spec
  python -m cc_orchestrations run --spec my-feature-abc123
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
        help='Spec name or absolute path',
    )
    run_parser.add_argument(
        '--fresh',
        action='store_true',
        help='Start fresh (ignore existing state)',
    )
    run_parser.add_argument(
        '--dry-run',
        action='store_true',
        dest='dry_run',
        help='Show execution plan and test infrastructure without running',
    )

    # list command
    subparsers.add_parser(
        'list',
        help='List specs',
        description='List all specs in current project',
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
        help='Spec name or absolute path',
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
        help='Spec name or absolute path',
    )

    # new command
    new_parser = subparsers.add_parser(
        'new',
        help='Create new spec',
        description='Create a new spec directory structure',
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
