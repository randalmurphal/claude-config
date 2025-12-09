"""m32rimm-specific PR review configuration.

DESIGN: Self-contained extension with all prompts embedded.
All prompts are loaded from this package's prompts/ directory.

Structure:
- Agent definitions with prompts loaded at import time
- Finding classifier: m32rimm-specific classification rules
- No external dependencies on .claude/agents/ directories
"""

from pathlib import Path
from typing import Any

# Import base classes from base framework
from cc_orchestrations.pr_review.config import (
    PRReviewAgent,
    PRReviewConfig,
)

from .finding_classification import M32RIMMFindingClassifier
from .prompts import get_prompt


# Base directory for this extension
PR_REVIEW_DIR = Path(__file__).parent


# =============================================================================
# PROMPT LOADING
# =============================================================================


def _load_agent_prompt(name: str) -> str:
    """Load prompt from extension's prompts directory.

    Args:
        name: Agent name (e.g., 'mongo-ops-reviewer')

    Returns:
        Prompt content or empty string if not found
    """
    return get_prompt(name)


# =============================================================================
# AGENT CONFIGURATION
#
# All prompts are loaded from this extension's prompts/ directory.
# The 'trigger' field is IGNORED - intelligent triage decides agent relevance.
# =============================================================================


# Placeholder trigger - triage phase decides relevance, not file patterns
def _triage_decides(ctx: dict[str, Any]) -> bool:
    """Placeholder - actual selection done by intelligent triage."""
    return True


# Required agents (always run for m32rimm)
M32RIMM_REQUIRED_AGENTS = [
    PRReviewAgent(
        name='test-plan-validator',
        trigger=_triage_decides,
        prompt_template=_load_agent_prompt('test-plan-validator'),
        model='opus',
        required=True,
        description='Validates Jira Test Plan exists and aligns with integration tests',
    ),
]

# Domain-specific agents (triage decides if relevant)
M32RIMM_DOMAIN_AGENTS = [
    PRReviewAgent(
        name='mongo-ops-reviewer',
        trigger=_triage_decides,
        prompt_template=_load_agent_prompt('mongo-ops-reviewer'),
        model='opus',
        required=False,
        description='MongoDB patterns: retry_run, subID filtering, DBOpsHelper.flush()',
    ),
    PRReviewAgent(
        name='import-framework-reviewer',
        trigger=_triage_decides,
        prompt_template=_load_agent_prompt('import-framework-reviewer'),
        model='opus',
        required=False,
        description='Import framework: data_importer pairing, parallel processing, import tracking',
    ),
    PRReviewAgent(
        name='api-security-reviewer',
        trigger=_triage_decides,
        prompt_template=_load_agent_prompt('api-security-reviewer'),
        model='opus',
        required=False,
        description='API security: JWT token handling, subID from token, auth decorators',
    ),
    PRReviewAgent(
        name='bo-structure-reviewer',
        trigger=_triage_decides,
        prompt_template=_load_agent_prompt('bo-structure-reviewer'),
        model='opus',
        required=False,
        description='Business object structure: required fields, types, related/relatedV2',
    ),
    PRReviewAgent(
        name='schema-alignment-reviewer',
        trigger=_triage_decides,
        prompt_template=_load_agent_prompt('schema-alignment-reviewer'),
        model='opus',
        required=False,
        description='Schema alignment: BO field changes, r3 frontend compatibility',
    ),
    PRReviewAgent(
        name='performance-reviewer',
        trigger=_triage_decides,
        prompt_template=_load_agent_prompt('performance-reviewer'),
        model='opus',
        required=False,
        description='Performance: N+1 queries, aggregation efficiency, batch processing',
    ),
    # NOTE: architecture-reviewer is in GENERIC_AGENTS, not duplicated here
]

# Combined list for export
M32RIMM_AGENTS = M32RIMM_REQUIRED_AGENTS + M32RIMM_DOMAIN_AGENTS


# =============================================================================
# VALIDATION AGENTS
#
# These are used in the validation phase (Phase 3)
# =============================================================================

M32RIMM_VALIDATORS = [
    'finding-validator',
    'adversarial-reviewer',
    'severity-auditor',
    'critical-reinvestigator',
]

# Second-round agents (Phase 2.5)
M32RIMM_SECOND_ROUND_AGENTS = [
    'blind-spot-hunter',
    'interaction-investigator',
    'conclusion-validator',
]

# Report synthesizer
M32RIMM_REPORT_AGENT = 'pr-report-synthesizer'


# =============================================================================
# PROMPT ACCESS FUNCTIONS
# =============================================================================


def get_validator_prompt(name: str) -> str:
    """Get prompt for a validation agent.

    Args:
        name: Validator name

    Returns:
        Prompt content
    """
    return get_prompt(name)


def get_second_round_prompt(name: str) -> str:
    """Get prompt for a second-round agent.

    Args:
        name: Agent name

    Returns:
        Prompt content
    """
    return get_prompt(name)


def get_report_synthesizer_prompt() -> str:
    """Get prompt for the report synthesizer.

    Returns:
        Prompt content
    """
    return get_prompt(M32RIMM_REPORT_AGENT)


# =============================================================================
# CONFIGURATION FACTORY
# =============================================================================


def create_m32rimm_config() -> PRReviewConfig:
    """Create m32rimm-specific PR review configuration.

    Merges m32rimm agents with generic agents from the base framework.
    Finding classification uses m32rimm-specific rules.

    Returns:
        PRReviewConfig configured for m32rimm
    """
    from cc_orchestrations.pr_review.config import create_default_config

    # Start with generic config (includes generic agents)
    config = create_default_config()

    # Add m32rimm-specific agents
    config.agents.extend(M32RIMM_AGENTS)

    # Override finding classification with m32rimm rules
    config.finding_classification = M32RIMMFindingClassifier()

    # Update metadata
    config.name = 'pr_review_m32rimm'
    config.version = '2.0.0-m32rimm'

    return config


# Singleton for convenience
m32rimm_config = create_m32rimm_config()
