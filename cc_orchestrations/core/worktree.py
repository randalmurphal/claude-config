"""Git worktree management for orchestrations.

Worktrees are stored in ~/.claude/git_worktrees/<project>/<tool>/<worktree_name>/
and are automatically cleaned up after orchestration completes.
"""

import logging
import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .paths import expand_path, get_claude_home

LOG = logging.getLogger(__name__)

# Base directory for all worktrees
WORKTREES_BASE = get_claude_home() / 'git_worktrees'


@dataclass
class WorktreeInfo:
    """Information about a worktree."""

    path: Path
    branch: str
    commit: str
    is_bare: bool = False
    is_detached: bool = False


@dataclass
class WorktreeContext:
    """Context for worktree operations in an orchestration."""

    project: str
    tool: str  # e.g., 'pr-review', 'conduct'
    source_repo: Path
    base_branch: str = 'main'
    _worktrees: list[Path] | None = None

    @property
    def base_dir(self) -> Path:
        """Get the base directory for this orchestration's worktrees."""
        return WORKTREES_BASE / self.project / self.tool

    def __post_init__(self) -> None:
        """Initialize worktree tracking."""
        self._worktrees = []


class WorktreeManager:
    """Manages git worktrees for orchestrations."""

    def __init__(self, source_repo: Path | str):
        """Initialize with source repository path.

        Args:
            source_repo: Path to the source git repository
        """
        self.source_repo = expand_path(source_repo)
        self._validate_git_repo()

    def _validate_git_repo(self) -> None:
        """Validate that source_repo is a git repository."""
        if not (self.source_repo / '.git').exists():
            # Could be a worktree itself
            git_file = self.source_repo / '.git'
            if git_file.is_file():
                # It's a worktree, find the main repo
                content = git_file.read_text().strip()
                if content.startswith('gitdir:'):
                    return  # Valid worktree
            raise ValueError(f'Not a git repository: {self.source_repo}')

    def _run_git(
        self,
        args: list[str],
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command.

        Args:
            args: Git command arguments (without 'git')
            cwd: Working directory (defaults to source_repo)
            check: Raise on non-zero exit

        Returns:
            Completed process result
        """
        cmd = ['git'] + args
        return subprocess.run(
            cmd,
            cwd=cwd or self.source_repo,
            capture_output=True,
            text=True,
            check=check,
        )

    def get_project_name(self) -> str:
        """Get the project name from the repository."""
        return self.source_repo.name

    def list_worktrees(self) -> list[WorktreeInfo]:
        """List all worktrees for this repository.

        Returns:
            List of WorktreeInfo objects
        """
        result = self._run_git(['worktree', 'list', '--porcelain'])
        worktrees = []
        current: dict[str, str] = {}

        for line in result.stdout.splitlines():
            if not line:
                if current:
                    worktrees.append(
                        WorktreeInfo(
                            path=Path(current['worktree']),
                            branch=current.get('branch', '').replace(
                                'refs/heads/', ''
                            ),
                            commit=current.get('HEAD', ''),
                            is_bare=current.get('bare') == 'bare',
                            is_detached='detached' in current,
                        )
                    )
                    current = {}
            elif line.startswith('worktree '):
                current['worktree'] = line[9:]
            elif line.startswith('HEAD '):
                current['HEAD'] = line[5:]
            elif line.startswith('branch '):
                current['branch'] = line[7:]
            elif line == 'bare':
                current['bare'] = 'bare'
            elif line == 'detached':
                current['detached'] = 'detached'

        # Don't forget last entry
        if current:
            worktrees.append(
                WorktreeInfo(
                    path=Path(current['worktree']),
                    branch=current.get('branch', '').replace('refs/heads/', ''),
                    commit=current.get('HEAD', ''),
                    is_bare=current.get('bare') == 'bare',
                    is_detached='detached' in current,
                )
            )

        return worktrees

    def create_worktree(
        self,
        name: str,
        base_dir: Path,
        base_branch: str = 'main',
        checkout_branch: str | None = None,
    ) -> Path:
        """Create a new worktree.

        Args:
            name: Name for the worktree directory
            base_dir: Base directory to create worktree in
            base_branch: Branch to base new worktree on
            checkout_branch: Existing branch to checkout (instead of creating new)

        Returns:
            Path to the created worktree
        """
        worktree_path = base_dir / name
        base_dir.mkdir(parents=True, exist_ok=True)

        # Check if worktree already exists
        existing = self.list_worktrees()
        for wt in existing:
            if wt.path == worktree_path:
                LOG.info(f'Worktree already exists: {worktree_path}')
                return worktree_path

        try:
            if checkout_branch:
                # Checkout existing branch
                LOG.info(f'Creating worktree for branch: {checkout_branch}')
                result = self._run_git(
                    ['worktree', 'add', str(worktree_path), checkout_branch],
                    check=False,
                )
                if result.returncode != 0:
                    LOG.error(f'Worktree creation failed: {result.stderr}')
                    raise RuntimeError(
                        f'Failed to create worktree: {result.stderr}'
                    )
            else:
                # Create new branch from base
                branch_name = f'wt-{name}'
                LOG.info(f'Creating worktree with new branch: {branch_name}')
                result = self._run_git(
                    [
                        'worktree',
                        'add',
                        '-b',
                        branch_name,
                        str(worktree_path),
                        base_branch,
                    ],
                    check=False,
                )
                if result.returncode != 0:
                    LOG.error(f'Worktree creation failed: {result.stderr}')
                    raise RuntimeError(
                        f'Failed to create worktree: {result.stderr}'
                    )

            # Verify worktree was actually created
            if not worktree_path.exists():
                raise RuntimeError(
                    f'Worktree path does not exist after creation: {worktree_path}'
                )

        except subprocess.CalledProcessError as e:
            LOG.error(f'Git worktree command failed: {e.stderr}')
            raise RuntimeError(f'Failed to create worktree: {e.stderr}') from e

        return worktree_path

    def remove_worktree(self, path: Path, force: bool = False) -> None:
        """Remove a worktree.

        Args:
            path: Path to the worktree to remove
            force: Force removal even if dirty
        """
        args = ['worktree', 'remove', str(path)]
        if force:
            args.append('--force')

        try:
            self._run_git(args)
            LOG.info(f'Removed worktree: {path}')
        except subprocess.CalledProcessError as e:
            LOG.warning(f'Failed to remove worktree {path}: {e.stderr}')
            if force:
                # Last resort: manual cleanup
                if path.exists():
                    shutil.rmtree(path)
                    self._run_git(['worktree', 'prune'])
                    LOG.info(f'Force-removed worktree: {path}')

    def cleanup_worktree(
        self, project: str, tool: str, name: str, force: bool = True
    ) -> None:
        """Clean up a specific worktree by name.

        Args:
            project: Project name
            tool: Tool name (e.g., 'pr-review')
            name: Worktree name to remove
            force: Force removal even if dirty
        """
        worktree_path = WORKTREES_BASE / project / tool / name

        if not worktree_path.exists():
            LOG.info(f'Worktree does not exist: {worktree_path}')
            return

        self.remove_worktree(worktree_path, force=force)
        self._run_git(['worktree', 'prune'], check=False)

    def cleanup_tool_worktrees(self, project: str, tool: str) -> None:
        """Clean up all worktrees for a specific tool.

        Args:
            project: Project name
            tool: Tool name (e.g., 'pr-review')
        """
        tool_dir = WORKTREES_BASE / project / tool

        if not tool_dir.exists():
            LOG.info(f'No worktrees to clean up for {project}/{tool}')
            return

        # Get all worktrees and find ones in our tool directory
        worktrees = self.list_worktrees()
        for wt in worktrees:
            if str(wt.path).startswith(str(tool_dir)):
                self.remove_worktree(wt.path, force=True)

        # Remove the tool directory if empty
        if tool_dir.exists():
            try:
                shutil.rmtree(tool_dir)
                LOG.info(f'Removed tool directory: {tool_dir}')
            except OSError as e:
                LOG.warning(f'Could not remove tool directory: {e}')

        # Prune stale worktree references
        self._run_git(['worktree', 'prune'], check=False)

    def cleanup_all_worktrees(self, project: str) -> None:
        """Clean up all worktrees for a project.

        Args:
            project: Project name
        """
        project_dir = WORKTREES_BASE / project

        if not project_dir.exists():
            LOG.info(f'No worktrees to clean up for {project}')
            return

        # Remove all worktrees under this project
        worktrees = self.list_worktrees()
        for wt in worktrees:
            if str(wt.path).startswith(str(project_dir)):
                self.remove_worktree(wt.path, force=True)

        # Remove the project directory
        if project_dir.exists():
            try:
                shutil.rmtree(project_dir)
                LOG.info(f'Removed project directory: {project_dir}')
            except OSError as e:
                LOG.warning(f'Could not remove project directory: {e}')

        self._run_git(['worktree', 'prune'], check=False)


@contextmanager
def worktree_context(
    source_repo: Path | str,
    tool: str,
    worktree_names: list[str],
    base_branch: str = 'main',
    checkout_branches: dict[str, str] | None = None,
) -> Iterator[dict[str, Path]]:
    """Context manager for worktree operations with automatic cleanup.

    Args:
        source_repo: Path to source git repository
        tool: Tool name (e.g., 'pr-review', 'conduct')
        worktree_names: Names of worktrees to create
        base_branch: Branch to base new worktrees on
        checkout_branches: Map of worktree name -> existing branch to checkout

    Yields:
        Dict mapping worktree name to path

    Example:
        with worktree_context(
            '/path/to/repo',
            'pr-review',
            ['base', 'pr'],
            checkout_branches={'pr': 'feature-branch'}
        ) as worktrees:
            base_path = worktrees['base']
            pr_path = worktrees['pr']
            # Do work...
        # Worktrees are automatically cleaned up
    """
    manager = WorktreeManager(source_repo)
    project = manager.get_project_name()
    base_dir = WORKTREES_BASE / project / tool
    checkout_branches = checkout_branches or {}

    created_worktrees: dict[str, Path] = {}

    try:
        for name in worktree_names:
            checkout = checkout_branches.get(name)
            path = manager.create_worktree(
                name=name,
                base_dir=base_dir,
                base_branch=base_branch,
                checkout_branch=checkout,
            )
            created_worktrees[name] = path

        yield created_worktrees

    finally:
        # Cleanup all worktrees for this tool
        LOG.info(f'Cleaning up worktrees for {project}/{tool}')
        manager.cleanup_tool_worktrees(project, tool)


def ensure_worktrees_gitignore() -> None:
    """Ensure git_worktrees directory is in .gitignore."""
    gitignore_path = get_claude_home() / '.gitignore'

    # Create or update .gitignore
    entry = 'git_worktrees/'
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if entry not in content:
            with gitignore_path.open('a') as f:
                f.write(f'\n# Worktrees for orchestrations\n{entry}\n')
            LOG.info(f'Added {entry} to .gitignore')
    else:
        gitignore_path.write_text(f'# Worktrees for orchestrations\n{entry}\n')
        LOG.info(f'Created .gitignore with {entry}')


# Ensure gitignore is set up on module import
ensure_worktrees_gitignore()
