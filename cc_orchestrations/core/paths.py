"""Path resolution utilities for orchestration.

Provides consistent path handling with ~ expansion and git root detection.
Specs live in the project's .claude/specs/ directory.
"""

import subprocess
from pathlib import Path


def expand_path(path: str | Path) -> Path:
    """Expand ~ and resolve to absolute path.

    Args:
        path: Path string or Path object, may contain ~

    Returns:
        Absolute resolved Path
    """
    p = Path(path) if isinstance(path, str) else path
    return p.expanduser().resolve()


def get_git_root(from_path: Path | None = None) -> Path:
    """Find git repository root from given path or cwd.

    Args:
        from_path: Starting path to search from (defaults to cwd)

    Returns:
        Absolute path to git root

    Raises:
        RuntimeError: If not in a git repository
    """
    cwd = str(from_path) if from_path else None
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f'Not in a git repository: {e.stderr.strip()}'
        ) from e


def get_claude_home() -> Path:
    """Get ~/.claude directory.

    Returns:
        Absolute path to ~/.claude
    """
    return expand_path('~/.claude')


def get_specs_dir(from_path: Path | None = None) -> Path:
    """Get <git_root>/.claude/specs directory for current project.

    Args:
        from_path: Starting path to find git root (defaults to cwd)

    Returns:
        Absolute path to project's specs directory
    """
    git_root = get_git_root(from_path)
    return git_root / '.claude' / 'specs'


def get_spec_path(spec_name: str, from_path: Path | None = None) -> Path:
    """Get path to a specific spec directory.

    Args:
        spec_name: Spec name with hash (e.g., "refactor-228fbe82")
        from_path: Starting path to find git root (defaults to cwd)

    Returns:
        Absolute path to spec directory
    """
    return get_specs_dir(from_path) / spec_name


def get_project_name(from_path: Path | None = None) -> str:
    """Get project name from git root directory name.

    Args:
        from_path: Starting path to find git root (defaults to cwd)

    Returns:
        Name of the git repository directory
    """
    return get_git_root(from_path).name


def relative_to_home(path: Path) -> str:
    """Convert absolute path to ~/... string for display/storage.

    Args:
        path: Absolute path

    Returns:
        Path string with ~ prefix if under home, otherwise original path
    """
    home = Path.home()
    try:
        relative = path.relative_to(home)
        return f'~/{relative}'
    except ValueError:
        # Path is not under home directory
        return str(path)


def relative_to_git_root(path: Path, from_path: Path | None = None) -> str:
    """Convert absolute path to path relative to git root.

    Args:
        path: Absolute path
        from_path: Starting path to find git root (defaults to cwd)

    Returns:
        Path string relative to git root, or original if not in repo
    """
    try:
        git_root = get_git_root(from_path)
        return str(path.relative_to(git_root))
    except (RuntimeError, ValueError):
        return str(path)
