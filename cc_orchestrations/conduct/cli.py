"""Command-line interface for the conduct orchestrator.

CRITICAL: Conduct orchestrations MUST run in git worktrees to protect
the working branch from background agent operations.
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

from cc_orchestrations.core.config import (
    ExecutionMode,
    load_config,
    save_config,
)
from cc_orchestrations.core.paths import get_git_root, get_project_name
from cc_orchestrations.core.state import StateManager
from cc_orchestrations.core.worktree import (
    WORKTREES_BASE,
    WorktreeManager,
    is_in_worktree,
)

from .config import CONDUCT_CONFIG
from .workflow import create_conduct_workflow


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
        'Starting': '\u25b6\ufe0f',
        'Complete': '\u2705',
        'Failed': '\u274c',
        'Skipping': '\u23ed\ufe0f',
    }
    icon = icons.get(status.split()[0], '\ud83d\udccd')
    print(f'{icon} [{phase}] {status}')


def prompt_user(prompt: str) -> str:
    """Prompt user for input."""
    print('\n' + '=' * 60)
    print(prompt)
    print('=' * 60)
    return input('\nYour choice: ').strip()


def get_current_branch(repo_path: Path) -> str:
    """Get the current branch name."""
    result = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def extract_spec_name(spec_path: Path) -> str:
    """Extract a clean name from spec path for worktree naming."""
    # Handle paths like .spec/SPEC.md or .claude/specs/feature-abc123/SPEC.md
    if spec_path.name == 'SPEC.md':
        parent = spec_path.parent
        if parent.name == '.spec':
            # Legacy: .spec/SPEC.md - use 'default'
            return 'default'
        else:
            # New: .claude/specs/feature-abc123/SPEC.md
            return parent.name
    return spec_path.stem or 'conduct'


def ensure_worktree(
    work_dir: Path,
    spec_path: Path,
    target_branch: str | None = None,
) -> tuple[Path, bool]:
    """Ensure we're running in a worktree, creating one if needed.

    Creates a NEW branch for the worktree (conduct-<spec>-<timestamp>) based on
    the target branch. This avoids git's restriction on checking out a branch
    that's already checked out elsewhere.

    Args:
        work_dir: Requested working directory
        spec_path: Path to SPEC.md
        target_branch: Branch to base worktree on (default: current branch)

    Returns:
        Tuple of (worktree_path, was_created)
        - worktree_path: Path to use for execution
        - was_created: True if a new worktree was created
    """
    import time

    # Already in a worktree? Good to go.
    if is_in_worktree(work_dir):
        print('\u2713 Already in worktree')
        return work_dir, False

    # Not in a worktree - need to create one
    print('\u26a0\ufe0f  Conduct requires worktree isolation for safety')

    try:
        repo_root = get_git_root(work_dir)
        project_name = get_project_name(work_dir)
    except RuntimeError as e:
        raise RuntimeError(f'Cannot create worktree: {e}') from e

    # Determine base branch
    if target_branch is None:
        target_branch = get_current_branch(repo_root)

    # Create unique worktree name and branch name
    spec_name = extract_spec_name(spec_path)
    timestamp = int(time.time())
    worktree_name = f'{spec_name}-{timestamp}'
    worktree_branch = f'conduct/{spec_name}-{timestamp}'

    print(f'   Creating worktree: {worktree_name}')
    print(f'   New branch: {worktree_branch}')
    print(f'   Based on: {target_branch}')

    manager = WorktreeManager(repo_root)
    tool_dir = WORKTREES_BASE / project_name / 'conduct'

    # Create worktree with a NEW branch (not checkout existing)
    # This avoids "branch already checked out" errors
    worktree_path = manager.create_worktree(
        name=worktree_name,
        base_dir=tool_dir,
        base_branch=target_branch,  # Creates new branch from this
        checkout_branch=None,  # None = create new branch
    )

    print(f'   Path: {worktree_path}')
    print()

    return worktree_path, True


def cmd_run(args: argparse.Namespace) -> int:
    """Run the orchestration workflow.

    WORKTREE ENFORCEMENT: All conduct operations run in isolated git worktrees
    to prevent background agents from modifying your working branch.
    """
    work_dir = Path(args.work_dir).resolve()
    spec_path = (
        Path(args.spec).resolve()
        if args.spec
        else work_dir / '.spec' / 'SPEC.md'
    )

    # Check spec exists (unless dry-run, which can work without)
    if not spec_path.exists() and not args.dry_run:
        print(f'\u274c SPEC.md not found at {spec_path}')
        print('Run /spec first to create the specification.')
        return 1

    # Parse mode
    try:
        mode = ExecutionMode(args.mode)
    except ValueError:
        print(f'\u274c Invalid mode: {args.mode}')
        print(f'   Valid modes: {", ".join(m.value for m in ExecutionMode)}')
        return 1

    mode_emoji = {
        'quick': '\u26a1',
        'standard': '\ud83c\udfb5',
        'full': '\ud83c\udfbc',
    }
    dry_run_tag = ' [DRY RUN]' if args.dry_run else ''
    draft_mode = getattr(args, 'draft', False)
    draft_tag = ' [DRAFT - Composer]' if draft_mode else ''

    emoji = mode_emoji.get(mode.value, '\ud83c\udfb5')
    print(f'{emoji} Starting conduct orchestration{dry_run_tag}{draft_tag}')
    print(f'   Mode: {mode.value.upper()}')
    if draft_mode:
        print(
            '   \ud83d\udcdd Draft mode: All agents using Composer for fast preview'
        )
    print()

    # WORKTREE ENFORCEMENT: Ensure we're in an isolated worktree
    skip_worktree = getattr(args, 'no_worktree', False)
    worktree_created = False

    if skip_worktree:
        print(
            '\u26a0\ufe0f  --no-worktree: Running in current directory (UNSAFE)'
        )
        print('   Background agents may modify your working branch!')
        print()
    else:
        try:
            target_branch = getattr(args, 'branch', None)
            work_dir, worktree_created = ensure_worktree(
                work_dir, spec_path, target_branch
            )
            # Update spec_path if we created a worktree (spec is in worktree now)
            if worktree_created:
                # Recalculate spec path relative to new worktree
                if args.spec:
                    # User provided explicit spec path - make it relative to worktree
                    rel_spec = spec_path.relative_to(
                        get_git_root(spec_path.parent)
                    )
                    spec_path = work_dir / rel_spec
                else:
                    spec_path = work_dir / '.spec' / 'SPEC.md'
        except RuntimeError as e:
            print(f'\u274c Worktree setup failed: {e}')
            print('   Use --no-worktree to bypass (not recommended)')
            return 1

    print(f'   Work dir: {work_dir}')
    print(f'   Spec: {spec_path}')
    if worktree_created:
        print('   \ud83c\udf33 Running in isolated worktree')
    if args.dry_run:
        print('   \u26a0\ufe0f  Dry run - agents will return test data only')
    print()

    # Load config
    config = CONDUCT_CONFIG
    if args.config:
        config = load_config(Path(args.config))

    # Apply mode and dry-run settings
    config.mode = mode
    config.dry_run = args.dry_run

    # DRAFT MODE: Override all agent models to use Composer
    # This runs the actual implementation with a fast/cheap model to validate
    # the spec instructions before committing to a full run
    if draft_mode:
        for agent_name, agent_config in config.agents.items():
            original_model = agent_config.model
            agent_config.model = 'composer-1'
            logging.getLogger(__name__).debug(
                f'Draft mode: {agent_name} model {original_model} -> composer-1'
            )
        # Also override default model
        config.default_model = 'composer-1'
        # Use quick mode for draft (aggressive parallelization)
        config.mode = ExecutionMode.QUICK

    # Create workflow
    engine = create_conduct_workflow(
        work_dir=work_dir,
        spec_path=spec_path,
        config_override=config,
        draft_mode=draft_mode,
    )

    # Set callbacks
    engine.on_status_change = print_status
    engine.on_user_prompt = prompt_user

    # Run
    try:
        success = engine.run(resume=not args.fresh)
    except KeyboardInterrupt:
        print('\n\u26a0\ufe0f Interrupted. State saved - run again to resume.')
        return 130

    if success:
        if args.dry_run:
            print('\n\u2705 Dry run complete! Flow validated successfully.')
        else:
            print('\n\u2705 Orchestration complete!')
        return 0
    print('\n\u274c Orchestration failed. Check state for details.')
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show current workflow status."""
    work_dir = Path(args.work_dir).resolve()
    state_dir = work_dir / '.spec'

    manager = StateManager(state_dir)
    state = manager.load()

    print(f'\ud83d\udcca Workflow Status: {state.workflow_name}')
    print(f'   Phase: {state.current_phase} ({state.phase_status.value})')
    print(f'   Risk: {state.risk_level}')
    print(f'   Started: {state.started_at or "N/A"}')
    print()

    # Component status
    print('Components:')
    for file, comp in state.components.items():
        status_icon = {
            'not_started': '\u2b1c',
            'skeleton': '\ud83d\udd28',
            'implementing': '\u2699\ufe0f',
            'validating': '\ud83d\udd0d',
            'fixing': '\ud83d\udd27',
            'complete': '\u2705',
            'blocked': '\u274c',
        }.get(comp.status.value, '\u2753')

        print(f'   {status_icon} {file}: {comp.status.value}')
        if comp.error:
            print(f'      Error: {comp.error}')

    # Discoveries
    if state.discoveries:
        print('\nDiscoveries:')
        for d in state.discoveries[-5:]:  # Last 5
            print(f'   \u2022 {d}')

    # Error
    if state.error:
        print(f'\n\u274c Error: {state.error}')

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
        print('\u2705 State reset.')
    else:
        print('No state file found.')

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Show or save default configuration."""
    if args.output:
        save_config(CONDUCT_CONFIG, Path(args.output))
        print(f'\u2705 Config saved to {args.output}')
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
        help='Execution mode: quick (minimal), standard, full (thorough)',
    )
    run_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run through flow without executing real work - agents return test data',
    )
    run_parser.add_argument(
        '--draft',
        action='store_true',
        help='Draft mode: Use Composer for ALL agents for fast preview. '
        'Actually implements the spec to validate instructions before full run.',
    )
    run_parser.add_argument(
        '--fresh',
        action='store_true',
        help='Start fresh (ignore saved state)',
    )
    run_parser.add_argument(
        '-b',
        '--branch',
        help='Branch to base worktree on (default: current branch)',
    )
    run_parser.add_argument(
        '--no-worktree',
        action='store_true',
        dest='no_worktree',
        help='UNSAFE: Skip worktree isolation, run in current directory',
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
    resume_parser.add_argument(
        '-m',
        '--mode',
        choices=['quick', 'standard', 'full'],
        default='standard',
        help='Execution mode',
    )
    resume_parser.add_argument(
        '-b',
        '--branch',
        help='Branch to base worktree on (default: current branch)',
    )
    resume_parser.add_argument(
        '--no-worktree',
        action='store_true',
        dest='no_worktree',
        help='UNSAFE: Skip worktree isolation',
    )
    resume_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode',
    )
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
        args.draft = False
        args.fresh = False
        args.branch = None
        args.no_worktree = False
        args.func = cmd_run

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
