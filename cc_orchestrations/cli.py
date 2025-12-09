"""Unified CLI for cc_orchestrations.

Entry point for all orchestration commands:
- implement: Automated ticket-to-PR pipeline
- conduct: Multi-component implementation orchestration
- pr-review: Automated PR review
"""

import argparse
import sys
from pathlib import Path


def cmd_implement(args: argparse.Namespace) -> int:
    """Run the implement (ticket-to-PR) pipeline."""
    from .implement.cli import main as implement_main

    # Build argv for implement CLI
    argv = [args.ticket]
    if args.force:
        argv.append('--force')
    if args.status:
        argv.append('--status')
    if args.resume:
        argv.append('--resume')
    if hasattr(args, 'verbose') and args.verbose:
        argv.append('--verbose')
    if hasattr(args, 'debug') and args.debug:
        argv.append('--debug')

    return implement_main(argv)


def cmd_conduct(args: argparse.Namespace) -> int:
    """Run the conduct orchestration."""
    from .conduct.cli import main as conduct_main

    # Build argv for conduct CLI
    argv = ['run']  # Default subcommand

    if hasattr(args, 'spec') and args.spec:
        argv.extend(['--spec', args.spec])
    if hasattr(args, 'draft') and args.draft:
        argv.append('--draft')
    if hasattr(args, 'mode') and args.mode:
        argv.extend(['--mode', args.mode])
    if hasattr(args, 'dry_run') and args.dry_run:
        argv.append('--dry-run')
    if hasattr(args, 'fresh') and args.fresh:
        argv.append('--fresh')
    if hasattr(args, 'branch') and args.branch:
        argv.extend(['--branch', args.branch])
    if hasattr(args, 'no_worktree') and args.no_worktree:
        argv.append('--no-worktree')
    if hasattr(args, 'verbose') and args.verbose:
        argv.append('--verbose')
    if hasattr(args, 'debug') and args.debug:
        argv.append('--debug')

    return conduct_main(argv)


def cmd_pr_review(args: argparse.Namespace) -> int:
    """Run a PR review workflow.

    Args:
        args: Parsed arguments with ticket, target_branch, dry_run, branch

    Returns:
        0 on success, 1 on failure
    """
    import os
    import subprocess

    from .core.config import Config
    from .core.paths import get_git_root, get_project_name
    from .core.runner import AgentRunner
    from .core.worktree import WORKTREES_BASE, WorktreeManager
    from .pr_review.config import create_default_config
    from .pr_review.phases import (
        PRReviewContext,
        phase_investigation,
        phase_report,
        phase_synthesis,
        phase_triage,
        phase_validation,
    )

    ticket = args.ticket
    target_branch = (
        getattr(args, 'target_branch', None)
        or getattr(args, 'target', None)
        or 'develop'
    )
    dry_run = getattr(args, 'dry_run', False)
    source_branch = getattr(args, 'branch', None)

    print('=' * 60)
    print(f'PR REVIEW: {ticket}')
    print('=' * 60)
    print()

    # Find git root
    try:
        repo_root = get_git_root()
        project_name = get_project_name()
    except RuntimeError as e:
        print(f'Error: {e}')
        return 1

    print(f'Project: {project_name}')
    print(f'Repository: {repo_root}')
    print(f'Target branch: {target_branch}')

    # Check for project-specific PR review config
    project_agents = []
    project_config_path = (
        repo_root / '.claude' / 'cc_orchestrations' / 'pr_review' / 'config.py'
    )
    if project_config_path.exists():
        print(f'Loading project extensions from: {project_config_path.parent}')
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                'project_pr_review_config',
                project_config_path,
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Look for project-specific agents - prefer M32RIMM_AGENTS, etc.
                for pattern in ['M32RIMM_AGENTS', 'PROJECT_AGENTS']:
                    if hasattr(module, pattern):
                        project_agents = getattr(module, pattern)
                        agent_count = len(project_agents)
                        print(
                            f'  Loaded {agent_count} project agents from {pattern}'
                        )
                        break
                # Fallback: look for any list ending with _AGENTS (not GENERIC)
                if not project_agents:
                    for attr in dir(module):
                        if (
                            attr.endswith('_AGENTS')
                            and attr != 'GENERIC_AGENTS'
                            and isinstance(getattr(module, attr), list)
                        ):
                            project_agents = getattr(module, attr)
                            agent_count = len(project_agents)
                            print(
                                f'  Loaded {agent_count} project agents from {attr}'
                            )
                            break
        except Exception as e:
            print(f'  Warning: Could not load project config: {e}')

    # Find source branch if not specified
    if not source_branch:
        print(f'Finding branch for ticket: {ticket}')
        result = subprocess.run(
            ['git', 'fetch', 'origin', '--prune'],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f'Warning: git fetch failed: {result.stderr}')

        # Find branch matching ticket
        result = subprocess.run(
            ['git', 'branch', '-r'],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        branches = result.stdout.strip().split('\n')
        matching = [
            b.strip().replace('origin/', '')
            for b in branches
            if ticket.lower() in b.lower() and 'pre-styling' not in b.lower()
        ]

        if not matching:
            print(f'Error: No branch found for ticket {ticket}')
            print('Use --branch to specify the source branch')
            return 1

        source_branch = matching[0]
        if len(matching) > 1:
            print(f'Multiple branches found: {matching}')
            print(f'Using: {source_branch}')

    print(f'Source branch: {source_branch}')
    print()

    if dry_run:
        print('[DRY RUN MODE]')
        print()

    # Step 1: Set up worktrees
    print('Setting up worktrees...')
    manager = WorktreeManager(repo_root)
    tool_dir = WORKTREES_BASE / project_name / 'pr-review'

    # Use branch name for PR-specific worktree (cleaned up after)
    # Base worktree is shared and reused across reviews
    pr_worktree_name = source_branch.replace(
        '/', '-'
    )  # Sanitize for directory name

    try:
        # Create base worktree (target branch) - shared, reused
        base_wt = manager.create_worktree(
            name='base',
            base_dir=tool_dir,
            checkout_branch=f'origin/{target_branch}',
        )
        print(f'  Base worktree: {base_wt}')

        # Create PR worktree (source branch) - branch-specific
        pr_wt = manager.create_worktree(
            name=pr_worktree_name,
            base_dir=tool_dir,
            checkout_branch=f'origin/{source_branch}',
        )
        print(f'  PR worktree: {pr_wt}')
        print()

        # Get diff files
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'{target_branch}...HEAD'],
            cwd=pr_wt,
            capture_output=True,
            text=True,
        )
        diff_files = [f for f in result.stdout.strip().split('\n') if f]
        print(f'Changed files: {len(diff_files)}')
        for f in diff_files[:10]:
            print(f'  - {f}')
        if len(diff_files) > 10:
            print(f'  ... and {len(diff_files) - 10} more')
        print()

        # Get Jira context if script exists (check subdirectory first, then root)
        jira_script = (
            repo_root / '.claude' / 'scripts' / 'jira' / 'jira-get-issue'
        )
        if not jira_script.exists():
            jira_script = repo_root / '.claude' / 'scripts' / 'jira-get-issue'
        jira_context = None
        if jira_script.exists():
            print(f'Fetching Jira ticket: {ticket}')
            result = subprocess.run(
                [str(jira_script), ticket],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                jira_context = result.stdout
                # Extract summary line
                for line in jira_context.split('\n'):
                    if line.startswith('# '):
                        print(f'  {line}')
                        break
            else:
                print(f'  Warning: Could not fetch Jira: {result.stderr[:100]}')
            print()

        # Get GitLab MR context if script exists (check subdirectory first, then root)
        gitlab_script = (
            repo_root / '.claude' / 'scripts' / 'gitlab' / 'gitlab-get-mr'
        )
        if not gitlab_script.exists():
            gitlab_script = repo_root / '.claude' / 'scripts' / 'gitlab-get-mr'
        mr_context = None
        if gitlab_script.exists():
            print(f'Fetching GitLab MR for: {ticket}')
            result = subprocess.run(
                [str(gitlab_script), ticket],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                mr_context = result.stdout
                # Extract MR title for display
                for line in mr_context.split('\n'):
                    if line.startswith('# MR'):
                        print(f'  {line}')
                        break
                else:
                    print('  MR found')
            else:
                # Show the actual error
                error_msg = (
                    result.stderr.strip() if result.stderr else 'Unknown error'
                )
                print(f'  No MR found: {error_msg}')
            print()

        if dry_run:
            print('=' * 60)
            print('DRY RUN COMPLETE')
            print('=' * 60)
            print()
            print('Would run phases:')
            print('  1. Triage - Assess risk level')
            print('  2. Investigation - Run reviewers')
            print(
                '  3. Cross-Pollination - Second-round analysis (medium+ risk)'
            )
            print('  4. Validation - Validate findings, council votes')
            print('  5. Synthesis - Consolidate results')
            print('  6. Report - Generate report')
            print()
            print('To run for real:')
            print(f'  python -m cc_orchestrations pr-review {ticket}')
            return 0

        # Create review context
        claude_path = os.path.expanduser('~/.claude/local/claude')

        config = Config(
            name='pr-review',
            dry_run=False,
            claude_path=claude_path,
            default_model='opus',  # PR review uses Opus for thoroughness
        )

        # Skills directory - check project first, then ~/.claude
        project_skills_dir = repo_root / '.claude' / 'skills'
        global_skills_dir = Path.home() / '.claude' / 'skills'
        skills_dir = (
            project_skills_dir
            if project_skills_dir.exists()
            else global_skills_dir
        )

        # Finding classification path (if exists)
        finding_classification = (
            repo_root
            / '.claude'
            / 'cc_orchestrations'
            / 'pr_review'
            / 'finding_classification.md'
        )

        runner = AgentRunner(
            config=config,
            work_dir=pr_wt,
            skills_dir=skills_dir if skills_dir.exists() else None,
            finding_classification_path=(
                finding_classification
                if finding_classification.exists()
                else None
            ),
            dry_run=False,
        )

        # Create config with project-specific agents if available
        review_config = create_default_config()
        if project_agents:
            # Merge project agents with generic agents
            review_config.agents.extend(project_agents)
            agent_count = len(review_config.agents)
            print(f'  {agent_count} agents available (triage will select)')

        ctx = PRReviewContext(
            ticket_id=ticket,
            source_branch=source_branch,
            target_branch=target_branch,
            work_dir=repo_root,
            worktree_path=pr_wt,
            diff_files=diff_files,
            config=review_config,
            runner=runner,
        )

        # Add Jira context
        if jira_context:
            ctx.jira_context = jira_context

        # Phase 1: Triage
        print('Phase 1: Triage')
        result = phase_triage(ctx)
        if not result.success:
            print(f'  Triage failed: {result.error}')
            return 1
        print(f'  Risk level: {ctx.risk_level.value}')
        print()

        # Phase 2: Investigation
        print('Phase 2: Investigation')
        result = phase_investigation(ctx)
        if not result.success:
            print(f'  Investigation failed: {result.error}')
            return 1
        print(f'  Findings: {len(ctx.findings)}')
        print()

        # Phase 3: Validation
        print('Phase 3: Validation')
        result = phase_validation(ctx)
        if not result.success:
            print(f'  Validation failed: {result.error}')
            return 1
        print(f'  Validated findings: {len(ctx.validated_findings)}')
        print()

        # Phase 4: Synthesis
        print('Phase 4: Synthesis')
        result = phase_synthesis(ctx)
        if not result.success:
            print(f'  Synthesis failed: {result.error}')
            return 1
        print()

        # Phase 5: Report
        print('Phase 5: Report')
        result = phase_report(ctx)
        if not result.success:
            print(f'  Report failed: {result.error}')
            return 1
        print(f'  Report: {result.data.get("report_path", "N/A")}')
        print()

        print('=' * 60)
        print('PR REVIEW COMPLETE')
        print('=' * 60)
        return 0

    finally:
        # Cleanup only the branch-specific worktree (keep base for reuse)
        print()
        print('Cleaning up worktrees...')
        manager.cleanup_worktree(project_name, 'pr-review', pr_worktree_name)
        print('Done.')


def cmd_pr_review_batch(args: argparse.Namespace) -> int:
    """Run batch PR review for multiple MRs.

    Args:
        args: Parsed arguments with tickets, target_branch, dry_run, output

    Returns:
        0 on success, 1 on failure
    """
    from .pr_review.batch import main as batch_main

    argv = []
    if hasattr(args, 'tickets') and args.tickets:
        argv.extend(args.tickets)
    if hasattr(args, 'target_branch') and args.target_branch:
        argv.extend(['--target', args.target_branch])
    if hasattr(args, 'dry_run') and args.dry_run:
        argv.append('--dry-run')
    if hasattr(args, 'output') and args.output:
        argv.extend(['--output', str(args.output)])

    return batch_main(argv)


def cmd_extensions(args: argparse.Namespace) -> int:
    """List installed extensions."""
    from .core.extensions import get_installed_extensions

    extensions = get_installed_extensions()

    if not extensions:
        print('No extensions installed.')
        print()
        print('Available extensions:')
        print(
            '  cc_orchestrations_m32rimm - MongoDB/import patterns for m32rimm'
        )
        return 0

    print('Installed extensions:')
    for ext in extensions:
        print(f'  - {ext}')

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='cc-orchestrations',
        description='Claude Code Orchestrations - Multi-agent workflow automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Automated ticket-to-PR
  cc-orchestrations implement INT-1234
  cc-orchestrations implement INT-1234 --force
  cc-orchestrations implement INT-1234 --status

  # Multi-component orchestration
  cc-orchestrations conduct --spec .spec/SPEC.md
  cc-orchestrations conduct --spec my-feature --draft
  cc-orchestrations conduct --spec .spec/SPEC.md --dry-run
  cc-orchestrations conduct --spec .spec/SPEC.md --mode full

  # PR review
  cc-orchestrations pr-review INT-1234
  cc-orchestrations pr-review INT-1234 --target main
  cc-orchestrations pr-review INT-1234 --branch feature/my-branch
  cc-orchestrations pr-review INT-1234 --dry-run

  # Batch PR review
  cc-orchestrations pr-review-batch --target develop
  cc-orchestrations pr-review-batch INT-1234 INT-5678 INT-9012
  cc-orchestrations pr-review-batch --target main --dry-run

  # List installed extensions
  cc-orchestrations extensions
""",
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

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # implement command
    impl_parser = subparsers.add_parser(
        'implement',
        help='Automated ticket-to-PR pipeline',
        description='Fully automated: Jira ticket → Investigation → Spec → Code → PR',
    )
    impl_parser.add_argument(
        'ticket',
        help='Jira ticket ID (e.g., INT-1234)',
    )
    impl_parser.add_argument(
        '--force',
        action='store_true',
        help='Proceed despite assumption threshold',
    )
    impl_parser.add_argument(
        '--status',
        action='store_true',
        help='Show pipeline status',
    )
    impl_parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from saved state',
    )

    # conduct command
    conduct_parser = subparsers.add_parser(
        'conduct',
        help='Multi-component implementation orchestration',
    )
    conduct_parser.add_argument(
        '--spec',
        required=True,
        help='Spec name or path (default: .spec/SPEC.md)',
    )
    conduct_parser.add_argument(
        '--draft',
        action='store_true',
        help='Draft mode: Use Composer for all agents for fast preview',
    )
    conduct_parser.add_argument(
        '--mode',
        choices=['quick', 'standard', 'full'],
        default='standard',
        help='Execution mode: quick (fast), standard (balanced), full (thorough)',
    )
    conduct_parser.add_argument(
        '--dry-run',
        action='store_true',
        dest='dry_run',
        help='Dry run: Validate flow without executing real work',
    )
    conduct_parser.add_argument(
        '--fresh',
        action='store_true',
        help='Start fresh (ignore saved state)',
    )
    conduct_parser.add_argument(
        '--branch',
        help='Branch to base worktree on (default: current branch)',
    )
    conduct_parser.add_argument(
        '--no-worktree',
        action='store_true',
        dest='no_worktree',
        help='UNSAFE: Skip worktree isolation, run in current directory',
    )

    # pr-review command
    pr_parser = subparsers.add_parser(
        'pr-review',
        help='Automated PR review',
    )
    pr_parser.add_argument(
        'ticket',
        help='Jira ticket ID',
    )
    pr_parser.add_argument(
        '--target',
        default='develop',
        dest='target_branch',
        help='Target branch (default: develop)',
    )
    pr_parser.add_argument(
        '--branch',
        help='Source branch (auto-detected if not specified)',
    )
    pr_parser.add_argument(
        '--dry-run',
        action='store_true',
        dest='dry_run',
        help='Dry run: Show what would be reviewed without executing',
    )

    # pr-review-batch command
    pr_batch_parser = subparsers.add_parser(
        'pr-review-batch',
        help='Batch PR review for multiple MRs',
    )
    pr_batch_parser.add_argument(
        'tickets',
        nargs='*',
        help='Ticket IDs to review (if not specified, lists open MRs)',
    )
    pr_batch_parser.add_argument(
        '--target',
        default='develop',
        dest='target_branch',
        help='Target branch (default: develop)',
    )
    pr_batch_parser.add_argument(
        '--dry-run',
        action='store_true',
        dest='dry_run',
        help='Dry run: Show what would be reviewed without executing',
    )
    pr_batch_parser.add_argument(
        '--output',
        type=Path,
        help='Output directory for reports',
    )

    # extensions command
    subparsers.add_parser(
        'extensions',
        help='List installed extensions',
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        'implement': cmd_implement,
        'conduct': cmd_conduct,
        'pr-review': cmd_pr_review,
        'pr-review-batch': cmd_pr_review_batch,
        'extensions': cmd_extensions,
    }

    if args.command in commands:
        return commands[args.command](args)

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
