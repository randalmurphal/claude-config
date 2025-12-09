"""Self-contained prompts for orchestration workflows.

All prompts are defined here as templates that can be filled with context.
This makes the system portable and independent of external prompt files.

Extensions can add or override prompts by providing a PROMPTS dictionary.
"""

from .conduct import (
    IMPLEMENTATION_PROMPT,
    SKELETON_BUILDER_PROMPT,
    VALIDATION_PROMPT,
)
from .implement import (
    FINDING_FIXER_PROMPT,
    INVESTIGATION_PROMPT,
    PR_REVIEW_PROMPT,
    SPEC_GENERATION_PROMPT,
)

# All base prompts
PROMPTS = {
    # Implement (ticket-to-PR)
    'investigation': INVESTIGATION_PROMPT,
    'spec_generation': SPEC_GENERATION_PROMPT,
    'pr_review': PR_REVIEW_PROMPT,
    'finding_fixer': FINDING_FIXER_PROMPT,
    # Conduct
    'skeleton_builder': SKELETON_BUILDER_PROMPT,
    'implementation': IMPLEMENTATION_PROMPT,
    'validation': VALIDATION_PROMPT,
}

__all__ = [
    'FINDING_FIXER_PROMPT',
    'IMPLEMENTATION_PROMPT',
    'INVESTIGATION_PROMPT',
    'PR_REVIEW_PROMPT',
    'PROMPTS',
    'SKELETON_BUILDER_PROMPT',
    'SPEC_GENERATION_PROMPT',
    'VALIDATION_PROMPT',
]
