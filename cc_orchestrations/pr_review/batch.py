"""Batch PR review - review multiple MRs in one run.

Usage:
    # Review all open MRs targeting develop
    cc-orchestrations pr-review-batch --target develop

    # Review specific tickets
    cc-orchestrations pr-review-batch INT-1234 INT-5678 INT-9012

    # Dry run to see what would be reviewed
    cc-orchestrations pr-review-batch --target develop --dry-run
"""

import argparse
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class BatchReviewResult:
    """Result of a single PR review in batch."""

    ticket_id: str
    success: bool
    risk_level: str = 'unknown'
    findings_count: int = 0
    validated_count: int = 0
    report_path: Path | None = None
    error: str | None = None
    duration_seconds: float = 0.0


@dataclass
class BatchReviewSummary:
    """Summary of batch PR review run."""

    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    target_branch: str = 'develop'
    results: list[BatchReviewResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.success)

    @property
    def total_findings(self) -> int:
        return sum(r.findings_count for r in self.results)

    def to_markdown(self) -> str:
        """Generate markdown summary report."""
        lines = [
            '# Batch PR Review Summary',
            '',
            f'**Target:** {self.target_branch}',
            f'**Started:** {self.started_at.isoformat()}',
            (
                f'**Completed:** {self.completed_at.isoformat()}'
                if self.completed_at
                else '**Completed:** In progress'
            ),
            '',
            '## Results',
            '',
            '| Ticket | Status | Risk | Findings | Report |',
            '|--------|--------|------|----------|--------|',
        ]

        for r in self.results:
            status = 'Pass' if r.success else 'Fail'
            report = f'[View]({r.report_path})' if r.report_path else 'N/A'
            lines.append(
                f'| {r.ticket_id} | {status} | {r.risk_level} | '
                f'{r.validated_count}/{r.findings_count} | {report} |'
            )

        lines.extend(
            [
                '',
                '## Summary',
                '',
                f'- **Total PRs:** {self.total}',
                f'- **Passed:** {self.passed}',
                f'- **Failed:** {self.failed}',
                f'- **Total Findings:** {self.total_findings}',
            ]
        )

        return '\n'.join(lines)


def get_open_mrs(target_branch: str, repo_root: Path) -> list[str]:
    """Get list of open MRs targeting the given branch.

    Uses gitlab-list-mrs script if available.

    Args:
        target_branch: Target branch to filter MRs
        repo_root: Git repository root path

    Returns:
        List of ticket IDs for open MRs

    Raises:
        RuntimeError: If gitlab script not found or fails
    """
    gitlab_script = (
        repo_root / '.claude' / 'scripts' / 'gitlab' / 'gitlab-list-mrs'
    )
    if not gitlab_script.exists():
        gitlab_script = repo_root / '.claude' / 'scripts' / 'gitlab-list-mrs'

    if not gitlab_script.exists():
        raise RuntimeError(
            'gitlab-list-mrs script not found. '
            'Provide ticket IDs explicitly or install the script.'
        )

    result = subprocess.run(
        [str(gitlab_script), '--target', target_branch, '--state', 'opened'],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f'Failed to list MRs: {result.stderr}')

    tickets = [
        line.strip()
        for line in result.stdout.strip().split('\n')
        if line.strip()
    ]
    return tickets


def run_single_review(
    ticket_id: str, target_branch: str, dry_run: bool = False
) -> BatchReviewResult:
    """Run PR review for a single ticket.

    Args:
        ticket_id: Ticket ID to review
        target_branch: Target branch for diff
        dry_run: If True, run in dry-run mode

    Returns:
        BatchReviewResult with review outcome
    """
    start = time.time()

    try:
        from ..cli import cmd_pr_review

        args = argparse.Namespace(
            ticket=ticket_id,
            target_branch=target_branch,
            branch=None,
            dry_run=dry_run,
        )

        exit_code = cmd_pr_review(args)

        duration = time.time() - start

        if exit_code == 0:
            return BatchReviewResult(
                ticket_id=ticket_id,
                success=True,
                duration_seconds=duration,
            )
        else:
            return BatchReviewResult(
                ticket_id=ticket_id,
                success=False,
                error=f'Exit code {exit_code}',
                duration_seconds=duration,
            )

    except Exception as e:
        return BatchReviewResult(
            ticket_id=ticket_id,
            success=False,
            error=str(e),
            duration_seconds=time.time() - start,
        )


def run_batch_review(
    tickets: list[str],
    target_branch: str = 'develop',
    dry_run: bool = False,
    output_dir: Path | None = None,
) -> BatchReviewSummary:
    """Run PR review for multiple tickets.

    Args:
        tickets: List of ticket IDs to review
        target_branch: Target branch for diff
        dry_run: If True, run in dry-run mode
        output_dir: Directory to write summary report (optional)

    Returns:
        BatchReviewSummary with aggregate results
    """
    summary = BatchReviewSummary(
        started_at=datetime.now(),
        target_branch=target_branch,
    )

    print('=' * 60)
    print(f'BATCH PR REVIEW: {len(tickets)} tickets')
    print('=' * 60)
    print(f'Target: {target_branch}')
    print(f'Tickets: {", ".join(tickets)}')
    print()

    for i, ticket in enumerate(tickets, 1):
        print(f'\n[{i}/{len(tickets)}] Reviewing {ticket}...')
        print('-' * 40)

        result = run_single_review(ticket, target_branch, dry_run)
        summary.results.append(result)

        if result.success:
            print(f'Pass {ticket} - Review complete')
        else:
            print(f'Fail {ticket} - Failed: {result.error}')

    summary.completed_at = datetime.now()

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = (
            output_dir
            / f'batch-review-{summary.started_at.strftime("%Y%m%d-%H%M%S")}.md'
        )
        report_path.write_text(summary.to_markdown())
        print(f'\nSummary report: {report_path}')

    print()
    print('=' * 60)
    print('BATCH REVIEW COMPLETE')
    print('=' * 60)
    print(f'Total: {summary.total}')
    print(f'Passed: {summary.passed}')
    print(f'Failed: {summary.failed}')
    print(f'Total findings: {summary.total_findings}')

    return summary


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for batch PR review.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 on success, 1 on failure)
    """
    from ..core.paths import get_git_root

    parser = argparse.ArgumentParser(
        prog='cc-orchestrations pr-review-batch',
        description='Run PR review for multiple MRs',
    )

    parser.add_argument(
        'tickets',
        nargs='*',
        help='Ticket IDs to review (if not specified, lists open MRs)',
    )
    parser.add_argument(
        '--target',
        default='develop',
        dest='target_branch',
        help='Target branch (default: develop)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        dest='dry_run',
        help='Dry run mode',
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output directory for reports',
    )

    args = parser.parse_args(argv)

    try:
        repo_root = get_git_root()
    except RuntimeError as e:
        print(f'Error: {e}')
        return 1

    if args.tickets:
        tickets = args.tickets
    else:
        print(f'Finding open MRs targeting {args.target_branch}...')
        try:
            tickets = get_open_mrs(args.target_branch, repo_root)
        except RuntimeError as e:
            print(f'Error: {e}')
            return 1

        if not tickets:
            print('No open MRs found.')
            return 0

        print(f'Found {len(tickets)} open MRs')

    summary = run_batch_review(
        tickets=tickets,
        target_branch=args.target_branch,
        dry_run=args.dry_run,
        output_dir=args.output or (repo_root / '.claude' / 'review-reports'),
    )

    return 0 if summary.failed == 0 else 1


if __name__ == '__main__':
    import sys

    sys.exit(main())
