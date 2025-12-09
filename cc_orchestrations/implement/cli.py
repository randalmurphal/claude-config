"""CLI for implement command."""

import argparse
import json
import logging
import sys
from pathlib import Path

from cc_orchestrations.core.paths import get_git_root

from .pipeline import ImplementPipeline


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


def print_status(status: dict) -> None:
    """Pretty print pipeline status."""
    status_icons = {
        'not_started': '⬜',
        'fetching_ticket': '📥',
        'investigating': '🔍',
        'creating_spec': '📝',
        'draft_validation': '🧪',
        'full_orchestration': '🏗️',
        'creating_mr': '📤',
        'pr_review': '👀',
        'addressing_findings': '🔧',
        'complete': '✅',
        'failed': '❌',
        'blocked': '🚫',
    }

    icon = status_icons.get(status['status'], '❓')

    print(f'\n{icon} Ticket: {status["ticket"]}')
    print(f'   Status: {status["status"]}')

    if status.get('branch'):
        print(f'   Branch: {status["branch"]}')
    if status.get('mr_iid'):
        print(f'   MR: !{status["mr_iid"]}')
    if status.get('worktree'):
        print(f'   Worktree: {status["worktree"]}')
    if status.get('spec'):
        print(f'   Spec: {status["spec"]}')
    if status.get('started'):
        print(f'   Started: {status["started"]}')
    if status.get('completed'):
        print(f'   Completed: {status["completed"]}')
    if status.get('error'):
        print(f'   Error: {status["error"]}')

    print(f'   Draft attempts: {status.get("draft_attempts", 0)}')
    print(f'   Review fix attempts: {status.get("review_fix_attempts", 0)}')

    if status.get('remaining_findings', 0) > 0:
        print(f'   ⚠️  Remaining findings: {status["remaining_findings"]}')

    print()


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='implement',
        description='Automated ticket-to-PR pipeline',
    )

    parser.add_argument(
        'ticket',
        help='Jira ticket ID (e.g., INT-1234)',
    )

    parser.add_argument(
        '-d',
        '--work-dir',
        default='.',
        help='Working directory (default: current)',
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
        '--force',
        action='store_true',
        help='Proceed despite assumption threshold',
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show pipeline status',
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from saved state',
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON (with --status)',
    )

    args = parser.parse_args(argv)
    setup_logging(verbose=args.verbose, debug=args.debug)

    work_dir = Path(args.work_dir).resolve()

    try:
        get_git_root(work_dir)
    except RuntimeError as e:
        print(f'❌ {e}')
        return 1

    pipeline = ImplementPipeline(
        ticket_id=args.ticket,
        work_dir=work_dir,
        force=args.force,
    )

    if args.status:
        status = pipeline.get_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print_status(status)
        return 0

    print(f'🎫 Starting implement pipeline for {args.ticket}')
    if args.force:
        print('   --force: Will proceed despite assumption threshold')
    print()

    success = pipeline.run(resume=args.resume)

    if success:
        status = pipeline.get_status()
        print('\n✅ Pipeline complete!')
        if status.get('mr_iid'):
            print(f'   MR: !{status["mr_iid"]}')
        if status.get('branch'):
            print(f'   Branch: {status["branch"]}')
        if status.get('remaining_findings', 0) > 0:
            print(
                f'   ⚠️  {status["remaining_findings"]} findings need manual review'
            )
        return 0

    print('\n❌ Pipeline failed')
    print_status(pipeline.get_status())
    return 1


if __name__ == '__main__':
    sys.exit(main())
