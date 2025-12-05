# Component: paths.py

## Purpose
Path resolution utilities that handle `~` expansion, relative path resolution, and ensure no hardcoded user paths leak into the codebase.

## Location
`~/.claude/orchestrations/core/paths.py`

## Dependencies
None (foundation component)

## Interface

```python
from pathlib import Path

def expand_path(path: str | Path) -> Path:
    """Expand ~ and resolve to absolute path."""

def get_claude_home() -> Path:
    """Get ~/.claude directory."""

def get_specs_dir() -> Path:
    """Get ~/.claude/orchestrations/specs directory."""

def get_spec_path(project: str, spec_name: str) -> Path:
    """Get path to a specific spec directory."""

def relative_to_home(path: Path) -> str:
    """Convert absolute path to ~/... string for display/storage."""
```

## Implementation Notes

- Use `Path.expanduser()` for ~ expansion
- Use `Path.resolve()` for absolute paths
- `relative_to_home` should return `~/...` string for paths under home
- All functions should handle both str and Path inputs

## Tests Needed

- `expand_path("~/.claude")` returns absolute path
- `expand_path("./relative")` resolves relative to cwd
- `relative_to_home("/home/user/.claude/foo")` returns `"~/.claude/foo"`
- Works on different platforms (use Path, not string manipulation)
