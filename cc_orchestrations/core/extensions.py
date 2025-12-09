"""Extension discovery and management.

Extensions allow project-specific customizations:
- Custom prompts for investigation, spec generation, etc.
- Custom validators (e.g., MongoDB patterns, import framework)
- Custom patterns and context

Extensions are separate pip-installable packages that follow the naming convention:
    cc_orchestrations_<name>

Example:
    cc_orchestrations_m32rimm - MongoDB/import patterns for m32rimm project
"""

import importlib
import logging
from pathlib import Path
from typing import Any

LOG = logging.getLogger(__name__)

# Known extensions and their detection patterns
KNOWN_EXTENSIONS = {
    'm32rimm': {
        'package': 'cc_orchestrations_m32rimm',
        'detect_patterns': [
            lambda p: (p / 'fisio').is_dir(),
            lambda p: 'rimm' in p.name.lower(),
            lambda p: (p / 'fortress_api').is_dir(),
        ],
    },
}


def get_installed_extensions() -> list[str]:
    """Discover all installed extension packages.

    Returns:
        List of installed extension names (e.g., ['m32rimm'])
    """
    extensions = []

    for name, config in KNOWN_EXTENSIONS.items():
        try:
            importlib.import_module(config['package'])
            extensions.append(name)
            LOG.debug(f'Extension found: {name}')
        except ImportError:
            pass

    return extensions


def detect_project_extensions(work_dir: Path) -> list[str]:
    """Detect which extensions apply to the given project.

    Uses heuristics to determine which installed extensions
    are relevant for the current project.

    Args:
        work_dir: Project working directory

    Returns:
        List of applicable extension names
    """
    installed = get_installed_extensions()
    applicable = []

    for name in installed:
        config = KNOWN_EXTENSIONS.get(name, {})
        patterns = config.get('detect_patterns', [])

        for pattern in patterns:
            try:
                if pattern(work_dir):
                    applicable.append(name)
                    LOG.info(f'Extension {name} detected for {work_dir}')
                    break
            except Exception:
                pass

    return applicable


def load_extension(name: str) -> Any:
    """Load an extension module.

    Args:
        name: Extension name (e.g., 'm32rimm')

    Returns:
        Extension module or None if not found

    Raises:
        ImportError: If extension is not installed
    """
    config = KNOWN_EXTENSIONS.get(name)
    if not config:
        raise ImportError(f'Unknown extension: {name}')

    return importlib.import_module(config['package'])


def get_extension_prompts(name: str) -> dict[str, str]:
    """Get prompts from an extension.

    Args:
        name: Extension name

    Returns:
        Dictionary of prompt name -> prompt template
    """
    try:
        ext = load_extension(name)
        if hasattr(ext, 'PROMPTS'):
            return ext.PROMPTS
        if hasattr(ext, 'prompts'):
            return ext.prompts.PROMPTS
    except ImportError:
        pass

    return {}


def get_extension_validators(name: str) -> list[str]:
    """Get validator types from an extension.

    Args:
        name: Extension name

    Returns:
        List of validator type names
    """
    try:
        ext = load_extension(name)
        if hasattr(ext, 'VALIDATORS'):
            return ext.VALIDATORS
        if hasattr(ext, 'validators'):
            return list(ext.validators.VALIDATOR_TYPES.keys())
    except ImportError:
        pass

    return []


def get_extension_context(name: str) -> str:
    """Get additional context from an extension.

    This is project-specific knowledge that should be included
    in prompts (e.g., MongoDB patterns, common gotchas).

    Args:
        name: Extension name

    Returns:
        Context string to include in prompts
    """
    try:
        ext = load_extension(name)
        if hasattr(ext, 'CONTEXT'):
            return ext.CONTEXT
        if hasattr(ext, 'get_context'):
            return ext.get_context()
    except ImportError:
        pass

    return ''


def merge_prompts(
    base_prompts: dict[str, str],
    extensions: list[str],
) -> dict[str, str]:
    """Merge base prompts with extension prompts.

    Extension prompts can:
    - Override base prompts (same key)
    - Add new prompts (new key)

    Args:
        base_prompts: Base prompt templates
        extensions: List of extension names to merge

    Returns:
        Merged prompts dictionary
    """
    merged = base_prompts.copy()

    for ext_name in extensions:
        ext_prompts = get_extension_prompts(ext_name)
        merged.update(ext_prompts)

    return merged


def get_extension_pr_review_prompt(name: str, agent_name: str) -> str:
    """Get a PR review agent prompt from an extension.

    Args:
        name: Extension name (e.g., 'm32rimm')
        agent_name: Agent name (e.g., 'mongo-ops-reviewer')

    Returns:
        Prompt content or empty string if not found
    """
    try:
        ext = load_extension(name)
        # Try pr_review module first
        if hasattr(ext, 'pr_review'):
            pr_review = ext.pr_review
            if hasattr(pr_review, 'get_prompt'):
                return pr_review.get_prompt(agent_name)
            if hasattr(pr_review, 'load_prompt'):
                try:
                    return pr_review.load_prompt(agent_name)
                except FileNotFoundError:
                    pass
    except ImportError:
        pass

    return ''


def get_extension_pr_review_config(name: str) -> Any:
    """Get PR review configuration from an extension.

    Args:
        name: Extension name

    Returns:
        PRReviewConfig or None if not found
    """
    try:
        ext = load_extension(name)
        if hasattr(ext, 'pr_review'):
            pr_review = ext.pr_review
            if hasattr(pr_review, 'm32rimm_config'):
                return pr_review.m32rimm_config
            if hasattr(pr_review, 'create_m32rimm_config'):
                return pr_review.create_m32rimm_config()
    except ImportError:
        pass

    return None


def has_extension_prompt(name: str, prompt_name: str) -> bool:
    """Check if an extension has a specific prompt.

    Args:
        name: Extension name
        prompt_name: Prompt name to check

    Returns:
        True if prompt exists
    """
    try:
        ext = load_extension(name)
        if hasattr(ext, 'pr_review'):
            pr_review = ext.pr_review
            if hasattr(pr_review, 'has_prompt'):
                return pr_review.has_prompt(prompt_name)
    except ImportError:
        pass

    return False
