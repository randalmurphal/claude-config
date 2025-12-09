"""m32rimm-specific PR review configuration.

All prompts are self-contained in this package's prompts/ directory.
"""

from .config import (
    M32RIMM_AGENTS,
    M32RIMM_REPORT_AGENT,
    M32RIMM_SECOND_ROUND_AGENTS,
    M32RIMM_VALIDATORS,
    create_m32rimm_config,
    get_report_synthesizer_prompt,
    get_second_round_prompt,
    get_validator_prompt,
    m32rimm_config,
)
from .prompts import get_prompt, has_prompt, list_prompts, load_prompt

__all__ = [
    'M32RIMM_AGENTS',
    'M32RIMM_REPORT_AGENT',
    'M32RIMM_SECOND_ROUND_AGENTS',
    'M32RIMM_VALIDATORS',
    'create_m32rimm_config',
    'get_prompt',
    'get_report_synthesizer_prompt',
    'get_second_round_prompt',
    'get_validator_prompt',
    'has_prompt',
    'list_prompts',
    'load_prompt',
    'm32rimm_config',
]
