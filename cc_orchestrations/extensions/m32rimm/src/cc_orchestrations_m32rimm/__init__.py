"""m32rimm extension for cc_orchestrations.

Provides:
- MongoDB-specific validation patterns
- Import framework patterns
- Business object structure validation
- Project-specific context for prompts
- Conduct orchestration config
- PR review config
"""

from .prompts import PROMPTS
from .validators import VALIDATOR_TYPES, VALIDATORS
from .patterns import CONTEXT, get_context

# Import orchestration configs
from . import conduct
from . import pr_review

__version__ = '0.1.0'


def register():
    """Register this extension with cc_orchestrations."""
    return {
        'name': 'm32rimm',
        'version': __version__,
        'prompts': PROMPTS,
        'validators': VALIDATORS,
        'context': CONTEXT,
        'conduct': conduct,
        'pr_review': pr_review,
    }


__all__ = [
    'CONTEXT',
    'PROMPTS',
    'VALIDATOR_TYPES',
    'VALIDATORS',
    'conduct',
    'get_context',
    'pr_review',
    'register',
]
