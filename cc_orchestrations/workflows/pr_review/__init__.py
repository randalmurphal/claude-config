"""Generic PR review workflow with risk-scaled validation.

This workflow provides a foundation for PR reviews that can be extended by projects.
Based on the m32rimm PR review pattern, generalized for reuse.
"""

from .config import (
    GENERIC_AGENTS,
    PRReviewAgent,
    PRReviewConfig,
    RiskLevel,
    create_default_config,
)
from .phases import (
    PRReviewContext,
    create_pr_review_workflow,
    phase_investigation,
    phase_report,
    phase_synthesis,
    phase_triage,
    phase_validation,
)

__all__ = [
    'PRReviewAgent',
    'PRReviewConfig',
    'RiskLevel',
    'GENERIC_AGENTS',
    'create_default_config',
    'PRReviewContext',
    'phase_triage',
    'phase_investigation',
    'phase_validation',
    'phase_synthesis',
    'phase_report',
    'create_pr_review_workflow',
]
