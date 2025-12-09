"""m32rimm PR review prompt loading.

All prompts are self-contained within this extension package.
No external dependencies on .claude/agents/ directories.
"""

from pathlib import Path
from typing import Any

# Prompts directory is the same directory as this file
PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str, **kwargs: Any) -> str:
    """Load a prompt from the extension's prompts directory.

    Args:
        name: Prompt name (without .txt extension). Supports both
              dash-style (mongo-ops-reviewer) and underscore-style (mongo_ops_reviewer)
        **kwargs: Variables to substitute in the prompt

    Returns:
        Formatted prompt string

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    # Normalize name: convert dashes to underscores for file lookup
    file_name = name.replace('-', '_')
    prompt_file = PROMPTS_DIR / f'{file_name}.txt'

    if not prompt_file.exists():
        raise FileNotFoundError(f'Prompt not found: {prompt_file}')

    content = prompt_file.read_text()

    # Substitute variables if provided
    if kwargs:
        for key, value in kwargs.items():
            if isinstance(value, (list, tuple)):
                value = '\n'.join(f'- {item}' for item in value)
            elif not isinstance(value, str):
                value = str(value)
            content = content.replace(f'{{{key}}}', value)

    return content


def get_prompt(name: str, **kwargs: Any) -> str:
    """Get a prompt, returning empty string if not found.

    Convenience wrapper around load_prompt that doesn't raise.

    Args:
        name: Prompt name
        **kwargs: Variables to substitute

    Returns:
        Prompt string or empty if not found
    """
    try:
        return load_prompt(name, **kwargs)
    except FileNotFoundError:
        return ''


def list_prompts() -> list[str]:
    """List all available prompt names.

    Returns:
        List of prompt names (without .txt extension)
    """
    return [f.stem for f in PROMPTS_DIR.glob('*.txt')]


def has_prompt(name: str) -> bool:
    """Check if a prompt exists.

    Args:
        name: Prompt name (dash or underscore style)

    Returns:
        True if prompt exists
    """
    file_name = name.replace('-', '_')
    return (PROMPTS_DIR / f'{file_name}.txt').exists()


# Build PROMPTS dict for extension registration
# This maps prompt names to their content for the extension system
def _build_prompts_dict() -> dict[str, str]:
    """Build prompts dictionary for extension registration."""
    prompts = {}
    for prompt_file in PROMPTS_DIR.glob('*.txt'):
        # Use dash-style names for consistency with agent names
        name = prompt_file.stem.replace('_', '-')
        prompts[name] = prompt_file.read_text()
    return prompts


PROMPTS = _build_prompts_dict()

__all__ = [
    'PROMPTS',
    'PROMPTS_DIR',
    'get_prompt',
    'has_prompt',
    'list_prompts',
    'load_prompt',
]
