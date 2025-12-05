"""Command-line interface for the conduct orchestrator."""

import argparse
import json
import logging
import sys
from pathlib import Path

from .core.config import ExecutionMode, load_config, save_config
from .core.state import StateManager
from .workflows.conduct import create_conduct_workflow, CONDUCT_CONFIG


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Configure logging."""
    level = (
        logging.DEBUG
        if debug
        else (logging.INFO if verbose else logging.WARNING)
    )

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',
    )


def print_status(phase: str, status: str) -> None:
    """Print status update."""
    icons = {
        'Starting': '▶️',
        'Complete': '✅',
        'Failed': '❌',
        'Skipping': '⏭️',
    }
    icon = icons.get(status.split()[0], '📍')
    print(f'{icon} [{phase}] {status}')


def prompt_user(prompt: str) -> str:
    """Prompt user for input."""
    print('\n' + '=' * 60)
    print(prompt)
    print('=' * 60)
    return input('\nYour choice: ').strip()


def cmd_run(args: argparse.Namespace) -> int:
    """Run the orchestration workflow."""
    work_dir = Path(args.work_dir).resolve()
    spec_path = (
        Path(args.spec).resolve()
        if args.spec
        else work_dir / '.spec' / 'SPEC.md'
    )

    # Check spec exists (unless dry-run, which can work without)
    if not spec_path.exists() and not args.dry_run:
        print(f'❌ SPEC.md not found at {spec_path}')
        print('Run /spec first to create the specification.')
        return 1

    # Parse mode
    try:
        mode = ExecutionMode(args.mode)
    except ValueError:
        print(f'❌ Invalid mode: {args.mode}')
        print(f'   Valid modes: {", ".join(m.value for m in ExecutionMode)}')
        return 1

    mode_emoji = {'quick': '⚡', 'standard': '🎵', 'full': '🎼'}
    dry_run_tag = ' [DRY RUN]' if args.dry_run else ''

    print(
        f'{mode_emoji.get(mode.value, "🎵")} Starting conduct orchestration{dry_run_tag}'
    )
    print(f'   Mode: {mode.value.upper()}')
    print(f'   Work dir: {work_dir}')
    print(f'   Spec: {spec_path}')
    if args.dry_run:
        print('   ⚠️  Dry run - agents will return test data only')
    print()

    # Load config
    config = CONDUCT_CONFIG
    if args.config:
        config = load_config(Path(args.config))

    # Apply mode and dry-run settings
    config.mode = mode
    config.dry_run = args.dry_run

    # Create workflow
    engine = create_conduct_workflow(
        work_dir=work_dir,
        spec_path=spec_path,
        config_override=config,
    )

    # Set callbacks
    engine.on_status_change = print_status
    engine.on_user_prompt = prompt_user

    # Run
    try:
        success = engine.run(resume=not args.fresh)
    except KeyboardInterrupt:
        print('\n⚠️ Interrupted. State saved - run again to resume.')
        return 130

    if success:
        if args.dry_run:
            print('\n✅ Dry run complete! Flow validated successfully.')
        else:
            print('\n✅ Orchestration complete!')
        return 0
    else:
        print('\n❌ Orchestration failed. Check state for details.')
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show current workflow status."""
    work_dir = Path(args.work_dir).resolve()
    state_dir = work_dir / '.spec'

    manager = StateManager(state_dir)
    state = manager.load()

    print(f'📊 Workflow Status: {state.workflow_name}')
    print(f'   Phase: {state.current_phase} ({state.phase_status.value})')
    print(f'   Risk: {state.risk_level}')
    print(f'   Started: {state.started_at or "N/A"}')
    print()

    # Component status
    print('Components:')
    for file, comp in state.components.items():
        status_icon = {
            'not_started': '⬜',
            'skeleton': '🔨',
            'implementing': '⚙️',
            'validating': '🔍',
            'fixing': '🔧',
            'complete': '✅',
            'blocked': '❌',
        }.get(comp.status.value, '❓')

        print(f'   {status_icon} {file}: {comp.status.value}')
        if comp.error:
            print(f'      Error: {comp.error}')

    # Discoveries
    if state.discoveries:
        print('\nDiscoveries:')
        for d in state.discoveries[-5:]:  # Last 5
            print(f'   • {d}')

    # Error
    if state.error:
        print(f'\n❌ Error: {state.error}')

    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume workflow from saved state."""
    args.fresh = False
    return cmd_run(args)


def cmd_reset(args: argparse.Namespace) -> int:
    """Reset workflow state."""
    work_dir = Path(args.work_dir).resolve()
    state_file = work_dir / '.spec' / 'STATE.json'

    if state_file.exists():
        if not args.force:
            confirm = (
                input(f'Reset state at {state_file}? [y/N]: ').strip().lower()
            )
            if confirm != 'y':
                print('Cancelled.')
                return 0

        state_file.unlink()
        print('✅ State reset.')
    else:
        print('No state file found.')

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Show or save default configuration."""
    if args.output:
        save_config(CONDUCT_CONFIG, Path(args.output))
        print(f'✅ Config saved to {args.output}')
    else:
        print(json.dumps(CONDUCT_CONFIG.to_dict(), indent=2))

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='conduct',
        description='Orchestrated execution for complex features',
    )

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Verbose output',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debug output',
    )
    parser.add_argument(
        '-d',
        '--work-dir',
        default='.',
        help='Working directory (default: current)',
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # run
    run_parser = subparsers.add_parser('run', help='Run orchestration')
    run_parser.add_argument(
        '-s',
        '--spec',
        help='Path to SPEC.md (default: .spec/SPEC.md)',
    )
    run_parser.add_argument(
        '-c',
        '--config',
        help='Path to config file',
    )
    run_parser.add_argument(
        '-m',
        '--mode',
        choices=['quick', 'standard', 'full'],
        default='standard',
        help='Execution mode: quick (fast, minimal validation), standard (balanced), full (thorough)',
    )
    run_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run through flow without executing real work - agents return test data',
    )
    run_parser.add_argument(
        '--fresh',
        action='store_true',
        help='Start fresh (ignore saved state)',
    )
    run_parser.set_defaults(func=cmd_run)

    # status
    status_parser = subparsers.add_parser('status', help='Show status')
    status_parser.set_defaults(func=cmd_status)

    # resume
    resume_parser = subparsers.add_parser(
        'resume', help='Resume from saved state'
    )
    resume_parser.add_argument('-s', '--spec', help='Path to SPEC.md')
    resume_parser.add_argument('-c', '--config', help='Path to config file')
    resume_parser.set_defaults(func=cmd_resume)

    # reset
    reset_parser = subparsers.add_parser('reset', help='Reset workflow state')
    reset_parser.add_argument(
        '-f', '--force', action='store_true', help='Skip confirmation'
    )
    reset_parser.set_defaults(func=cmd_reset)

    # config
    config_parser = subparsers.add_parser(
        'config', help='Show/save configuration'
    )
    config_parser.add_argument('-o', '--output', help='Save config to file')
    config_parser.set_defaults(func=cmd_config)

    args = parser.parse_args(argv)

    setup_logging(verbose=args.verbose, debug=args.debug)

    if not args.command:
        # Default to run
        args.command = 'run'
        args.spec = None
        args.config = None
        args.mode = 'standard'
        args.dry_run = False
        args.fresh = False
        args.func = cmd_run

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
