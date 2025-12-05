"""Path resolution utilities for orchestration.

Provides consistent path handling with ~ expansion and no hardcoded user paths.
"""

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


def get_claude_home() -> Path:
    """Get ~/.claude directory.

    Returns:
        Absolute path to ~/.claude
    """
    return expand_path('~/.claude')


def get_specs_dir() -> Path:
    """Get ~/.claude/orchestrations/specs directory.

    Returns:
        Absolute path to specs directory
    """
    return get_claude_home() / 'orchestrations' / 'specs'


def get_spec_path(project: str, spec_name: str) -> Path:
    """Get path to a specific spec directory.

    Args:
        project: Project name (e.g., "claude-config")
        spec_name: Spec name with hash (e.g., "refactor-228fbe82")

    Returns:
        Absolute path to spec directory
    """
    return get_specs_dir() / project / spec_name


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
