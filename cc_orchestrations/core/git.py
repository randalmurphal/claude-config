"""Git utilities for orchestration workflows.

Provides commit functionality to create a reviewable timeline of changes.
Each coding phase should commit its changes for later analysis.
"""

import logging
import subprocess
from pathlib import Path

LOG = logging.getLogger(__name__)


def git_has_changes(work_dir: Path) -> bool:
    """Check if there are uncommitted changes.

    Args:
        work_dir: Working directory (must be in a git repo)

    Returns:
        True if there are staged or unstaged changes
    """
    try:
        # Check for any changes (staged or unstaged)
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        LOG.warning(f'git status failed: {e}')
        return False


def git_stage_all(work_dir: Path) -> bool:
    """Stage all changes for commit.

    Args:
        work_dir: Working directory

    Returns:
        True if successful
    """
    try:
        subprocess.run(
            ['git', 'add', '-A'],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        LOG.error(f'git add failed: {e.stderr}')
        return False


def git_commit(
    work_dir: Path,
    phase: str,
    component: str | None = None,
    message: str | None = None,
    draft_mode: bool = False,
) -> str | None:
    """Create a commit for a phase completion.

    Commit message format:
    [conduct] <phase>: <component or message>

    If draft_mode, adds [DRAFT] prefix.

    Args:
        work_dir: Working directory
        phase: Phase name (skeleton, implementation, validation, etc.)
        component: Component file/name if applicable
        message: Override message (instead of component)
        draft_mode: If True, prefix with [DRAFT]

    Returns:
        Commit hash if successful, None if failed or nothing to commit
    """
    if not git_has_changes(work_dir):
        LOG.debug(f'No changes to commit for {phase}')
        return None

    # Build commit message
    prefix = '[DRAFT] ' if draft_mode else ''
    subject = component or message or phase
    commit_msg = f'{prefix}[conduct] {phase}: {subject}'

    # Stage all changes
    if not git_stage_all(work_dir):
        return None

    # Commit
    try:
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        LOG.info(f'Committed: {commit_msg}')

        # Get commit hash
        hash_result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return hash_result.stdout.strip()

    except subprocess.CalledProcessError as e:
        LOG.error(f'git commit failed: {e.stderr}')
        return None


def git_log_since(
    work_dir: Path,
    since_commit: str | None = None,
    format_str: str = '%h %s',
) -> list[str]:
    """Get commit log since a specific commit.

    Args:
        work_dir: Working directory
        since_commit: Starting commit (exclusive). If None, gets recent commits.
        format_str: Git log format string

    Returns:
        List of formatted commit strings
    """
    try:
        cmd = ['git', 'log', f'--format={format_str}']
        if since_commit:
            cmd.append(f'{since_commit}..HEAD')
        else:
            cmd.extend(['-n', '50'])  # Last 50 commits if no starting point

        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return [line for line in result.stdout.strip().split('\n') if line]

    except subprocess.CalledProcessError as e:
        LOG.warning(f'git log failed: {e}')
        return []


def git_show_commit(work_dir: Path, commit_hash: str) -> dict[str, str]:
    """Get details of a specific commit.

    Args:
        work_dir: Working directory
        commit_hash: Commit hash to show

    Returns:
        Dict with 'message', 'files', 'diff' keys
    """
    result = {'message': '', 'files': '', 'diff': ''}

    try:
        # Get commit message
        msg_result = subprocess.run(
            ['git', 'log', '-1', '--format=%B', commit_hash],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        result['message'] = msg_result.stdout.strip()

        # Get files changed
        files_result = subprocess.run(
            ['git', 'show', '--name-status', '--format=', commit_hash],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        result['files'] = files_result.stdout.strip()

        # Get diff (limited to avoid huge output)
        diff_result = subprocess.run(
            ['git', 'show', '--stat', commit_hash],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        result['diff'] = diff_result.stdout.strip()

    except subprocess.CalledProcessError as e:
        LOG.warning(f'git show failed for {commit_hash}: {e}')

    return result


def get_conduct_commits(work_dir: Path) -> list[dict[str, str]]:
    """Get all [conduct] commits in the current branch.

    Returns commits with their phase and component info parsed.

    Args:
        work_dir: Working directory

    Returns:
        List of dicts with 'hash', 'phase', 'component', 'draft', 'message'
    """
    import re

    commits = []
    log_lines = git_log_since(work_dir, format_str='%h|%s')

    # Pattern: [DRAFT] [conduct] phase: component
    pattern = re.compile(
        r'^(?P<draft>\[DRAFT\] )?\[conduct\] (?P<phase>\w+): (?P<component>.+)$'
    )

    for line in log_lines:
        if '|' not in line:
            continue
        hash_part, subject = line.split('|', 1)

        match = pattern.match(subject)
        if match:
            commits.append(
                {
                    'hash': hash_part,
                    'phase': match.group('phase'),
                    'component': match.group('component'),
                    'draft': bool(match.group('draft')),
                    'message': subject,
                }
            )

    return commits
