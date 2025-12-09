"""Configuration factory for conduct workflow.

Provides extensible configuration for the conduct orchestration workflow.
Projects can extend this by:
1. Adding project-specific agents to the agents dict
2. Overriding validation settings
3. Adjusting risk thresholds
4. Adding custom phases
"""

from pathlib import Path

from cc_orchestrations.core.config import (
    Config,
    PhaseConfig,
    RiskConfig,
    ValidationConfig,
    VotingGateConfig,
)
from cc_orchestrations.core.registry import REGISTRY

# =============================================================================
# PHASE DEFINITIONS
# =============================================================================

DEFAULT_PHASES = [
    PhaseConfig(
        name='parse_spec',
        description='Parse SPEC.md and extract components',
        agents=['spec_parser'],
    ),
    PhaseConfig(
        name='impact_analysis',
        description='Analyze blast radius of changes',
        agents=['impact_analyzer'],
        skip_condition='is_new_project',
    ),
    PhaseConfig(
        name='component_loop',
        description='Build each component: skeleton -> implement -> validate',
        agents=[],  # Handled by custom handler
    ),
    PhaseConfig(
        name='integration_validation',
        description='Run integration tests',
        agents=['test_runner'],
    ),
    PhaseConfig(
        name='final_validation',
        description='Final validation scaled by risk',
        agents=[],  # Handled by custom handler
    ),
    PhaseConfig(
        name='production_gate',
        description='Production readiness vote',
        agents=[],  # Handled by custom handler
        skip_condition="risk_level not in ('high', 'critical')",
    ),
    PhaseConfig(
        name='completion',
        description='Finalize and report',
        agents=[],
    ),
]


# =============================================================================
# VOTING GATE DEFINITIONS
# =============================================================================

DEFAULT_VOTING_GATES = {
    'impact_strategy': VotingGateConfig(
        name='impact_strategy',
        trigger_condition='transitive_deps > 10',
        num_voters=3,
        voter_agent='investigator',
        schema='impact_vote',
        options=[
            'BACKWARD_COMPATIBLE',
            'COORDINATED_ROLLOUT',
            'INCREMENTAL_MIGRATION',
            'REDESIGN_NEEDED',
        ],
    ),
    'fix_strategy': VotingGateConfig(
        name='fix_strategy',
        trigger_condition='same_issue_count >= 2',
        num_voters=3,
        voter_agent='investigator',
        schema='fix_strategy_vote',
        options=['FIX_IN_PLACE', 'REFACTOR', 'ESCALATE'],
    ),
    'production_ready': VotingGateConfig(
        name='production_ready',
        trigger_condition="risk_level in ('high', 'critical')",
        num_voters=3,
        voter_agent='investigator',
        schema='production_ready_vote',
        options=['READY', 'NEEDS_WORK', 'RISKY'],
    ),
    # Additional gates from original /conduct learnings
    'test_adequacy': VotingGateConfig(
        name='test_adequacy',
        trigger_condition='tests_pass and coverage >= 95',
        num_voters=3,
        voter_agent='code_reviewer',
        schema='test_adequacy_vote',
        options=['ADEQUATE', 'NEEDS_MORE', 'WEAK'],
    ),
    'doc_quality': VotingGateConfig(
        name='doc_quality',
        trigger_condition='has_documentation',
        num_voters=3,
        voter_agent='documentation_reviewer',
        schema='doc_quality_vote',
        options=['READY', 'GAPS', 'INACCURATE'],
    ),
}


# =============================================================================
# DEFAULT CONFIGURATIONS
# =============================================================================

DEFAULT_VALIDATION = ValidationConfig(
    max_fix_attempts=3,
    reviewers_per_validation=2,
    same_issue_threshold=2,
)

DEFAULT_RISK = RiskConfig(
    impact_vote_threshold=10,
    reviewers_by_risk={
        'low': 2,
        'medium': 4,
        'high': 6,
        'critical': 6,
    },
)


# =============================================================================
# CONFIG FACTORY
# =============================================================================


def create_default_config(
    prompts_dir: Path | None = None,
    claude_path: str = 'claude',
    state_dir: str = '.spec',
    default_model: str = 'sonnet',
) -> Config:
    """Create default conduct workflow configuration.

    Projects can extend this by:
    1. Calling this function to get the base config
    2. Adding project-specific agents: config.agents.update({...})
    3. Adjusting validation: config.validation = ValidationConfig(...)
    4. Adjusting risk thresholds: config.risk = RiskConfig(...)

    Args:
        prompts_dir: Directory containing prompt templates (default: auto-detect)
        claude_path: Path to claude CLI (default: 'claude')
        state_dir: Directory for state files (default: '.spec')
        default_model: Default model for agents (default: 'sonnet')

    Returns:
        Default Config for conduct workflow

    Example:
        # Basic usage
        config = create_default_config()

        # Extended for specific project
        config = create_default_config()
        config.agents['my_custom_validator'] = AgentConfig(...)
        config.validation.max_fix_attempts = 5
    """
    if prompts_dir is None:
        prompts_dir = Path(__file__).parent.parent / 'prompts'

    return Config(
        name='conduct',
        version='1.0.0',
        description='Full orchestration workflow for complex features',
        agents=REGISTRY.to_configs(),
        phases=DEFAULT_PHASES.copy(),
        voting_gates=DEFAULT_VOTING_GATES.copy(),
        validation=DEFAULT_VALIDATION,
        risk=DEFAULT_RISK,
        prompts_dir=str(prompts_dir),
        state_dir=state_dir,
        claude_path=claude_path,
        default_model=default_model,
    )


# Legacy compatibility - module-level config
CONDUCT_CONFIG = create_default_config()
