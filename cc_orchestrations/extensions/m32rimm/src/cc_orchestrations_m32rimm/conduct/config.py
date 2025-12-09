"""
m32rimm-specific conduct orchestration configuration.

Extension for the /conduct command with domain-specific validators and patterns.

This file provides m32rimm-specific customizations that are merged with
the base conduct config at runtime by the orchestration CLI.
"""

import os
from pathlib import Path

# Base directory for this extension
CONDUCT_DIR = Path(__file__).parent


# =============================================================================
# M32RIMM-SPECIFIC AGENTS
# =============================================================================

M32RIMM_AGENTS = {
    'mongo_validator': {
        'name': 'mongo_validator',
        'model': 'opus',
        'schema': 'validator',
        'allowed_tools': ['Read', 'Glob', 'Grep'],
        'disallowed_tools': ['Write', 'Edit', 'Bash'],
        'prompt_template': 'validate_mongo',
        'timeout': 600,
        'description': 'MongoDB operations validator - flush, subID, retry_run',
    },
    'import_validator': {
        'name': 'import_validator',
        'model': 'sonnet',
        'schema': 'validator',
        'allowed_tools': ['Read', 'Glob', 'Grep'],
        'disallowed_tools': ['Write', 'Edit', 'Bash'],
        'prompt_template': 'validate_imports',
        'timeout': 300,
        'description': 'Import framework validator - tracking, flush, BO structure',
    },
    'general_validator': {
        'name': 'general_validator',
        'model': 'opus',
        'schema': 'validator',
        'allowed_tools': ['Read', 'Glob', 'Grep'],
        'disallowed_tools': ['Write', 'Edit', 'Bash'],
        'prompt_template': 'validate_general',
        'timeout': 1200,
        'description': 'General code quality - logging, try/except, type hints',
    },
    'finding_validator': {
        'name': 'finding_validator',
        'model': 'opus',
        'schema': 'validator',
        'allowed_tools': ['Read', 'Glob', 'Grep'],
        'disallowed_tools': ['Write', 'Edit', 'Bash'],
        'prompt_template': 'finding_validator',
        'timeout': 600,
        'description': 'Challenges ALL findings - expects 30-50% false positives',
    },
}


# =============================================================================
# VALIDATOR SELECTION (m32rimm-specific conditional validators)
# =============================================================================

VALIDATOR_SELECTION = {
    'always': ['general_validator'],
    'conditional': [
        {
            'validator': 'mongo_validator',
            'trigger': 'any file uses: db., pymongo, DBOpsHelper, retry_run, businessObjects',
        },
        {
            'validator': 'import_validator',
            'trigger': 'any file in: imports/, or uses: data_importer, insert_data_importer',
        },
    ],
}


# =============================================================================
# M32RIMM CONFIG
# =============================================================================

CONFIG = {
    'name': 'conduct-m32rimm',
    'version': '1.0.0',
    'description': 'm32rimm-optimized conduct orchestration with domain-specific validation',
    # Additional agents to merge with base config
    'agents': M32RIMM_AGENTS,
    # Validator selection rules
    'validator_selection': VALIDATOR_SELECTION,
    # Validation settings
    'validation': {
        'max_fix_attempts': 3,
        'reviewers_per_validation': 3,
        'same_issue_threshold': 2,
    },
    # Risk-based scaling (m32rimm is a large monorepo, needs more reviewers)
    'risk': {
        'impact_vote_threshold': 10,
        'reviewers_by_risk': {
            'low': 2,
            'medium': 3,
            'high': 4,
            'critical': 5,
        },
    },
    # Paths
    'prompts_dir': str(CONDUCT_DIR / 'prompts'),
    'finding_classification': str(CONDUCT_DIR / 'finding_classification.md'),
    'state_dir': '.spec',
    'claude_path': os.path.expanduser('~/.claude/local/claude'),
    'default_model': 'sonnet',
    'permission_mode': 'default',
}


def get_config():
    """Return the m32rimm conduct configuration dictionary.

    This is merged with the base conduct config by the orchestration CLI
    when running from the m32rimm project.
    """
    return CONFIG


def create_m32rimm_config():
    """Create m32rimm-specific conduct configuration.

    This function is called by the orchestration CLI when it detects
    a project-specific extension exists.

    Returns:
        dict: m32rimm configuration to merge with base config
    """
    return CONFIG
