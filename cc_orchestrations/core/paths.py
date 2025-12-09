"""Path resolution utilities for orchestration.

Provides consistent path handling with ~ expansion and git root detection.

Data storage:
- Default data dir: ~/.cc_orchestrations/
- Can be overridden with CC_ORCHESTRATIONS_HOME environment variable
- Specs: <data_dir>/specs/<project>/<spec-name>/
- Tickets: <data_dir>/tickets/<project>/<ticket-id>/
"""

import os
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


def get_data_home() -> Path:
    """Get the orchestration data directory.

    Uses CC_ORCHESTRATIONS_HOME env var if set, otherwise ~/.cc_orchestrations/

    Returns:
        Absolute path to data directory
    """
    env_home = os.environ.get('CC_ORCHESTRATIONS_HOME')
    if env_home:
        return expand_path(env_home)
    return expand_path('~/.cc_orchestrations')


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


def get_specs_dir(
    project_name: str | None = None,
    from_path: Path | None = None,
) -> Path:
    """Get specs directory for a project.

    Args:
        project_name: Project name (defaults to git root directory name)
        from_path: Starting path to find git root (defaults to cwd)

    Returns:
        Absolute path to project's specs directory
    """
    if project_name is None:
        project_name = get_project_name(from_path)
    return get_data_home() / 'specs' / project_name


def get_spec_path(
    spec_name: str,
    project_name: str | None = None,
    from_path: Path | None = None,
) -> Path:
    """Get path to a specific spec directory.

    Args:
        spec_name: Spec name with hash (e.g., "refactor-228fbe82")
        project_name: Project name (defaults to git root directory name)
        from_path: Starting path to find git root (defaults to cwd)

    Returns:
        Absolute path to spec directory
    """
    return get_specs_dir(project_name, from_path) / spec_name


def get_tickets_dir(
    project_name: str | None = None,
    from_path: Path | None = None,
) -> Path:
    """Get tickets directory for a project.

    Args:
        project_name: Project name (defaults to git root directory name)
        from_path: Starting path to find git root (defaults to cwd)

    Returns:
        Absolute path to project's tickets directory
    """
    if project_name is None:
        project_name = get_project_name(from_path)
    return get_data_home() / 'tickets' / project_name


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
