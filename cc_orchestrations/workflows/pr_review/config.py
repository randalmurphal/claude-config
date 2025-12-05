"""Configuration for PR review workflow.

Defines agent types, risk levels, and extension points for project-specific reviews.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from cc_orchestrations.core.config import AgentConfig


class RiskLevel(str, Enum):
    """PR risk levels determining validation depth."""

    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


@dataclass
class PRReviewAgent:
    """Configuration for a PR review agent.

    Attributes:
        name: Agent identifier
        trigger: Function to determine if agent should run (receives diff context)
        prompt_template: Prompt template name or inline prompt
        model: Model to use (sonnet, opus, haiku)
        required: Whether agent must run (True) or is conditional (False)
        description: Human-readable description
    """

    name: str
    trigger: Callable[[dict[str, Any]], bool]
    prompt_template: str
    model: str = 'opus'
    required: bool = False
    description: str = ''

    def should_run(self, context: dict[str, Any]) -> bool:
        """Check if agent should run based on trigger condition."""
        return self.required or self.trigger(context)

    def to_agent_config(self) -> AgentConfig:
        """Convert to AgentConfig for runner."""
        return AgentConfig(
            name=self.name,
            model=self.model,
            schema='validator',  # All PR reviewers use validator schema
            allowed_tools=['Read', 'Grep', 'Glob', 'Bash'],
            disallowed_tools=['Write', 'Edit'],
            prompt_template=self.prompt_template,
            description=self.description,
        )


@dataclass
class PRReviewPhaseConfig:
    """Configuration for a review phase."""

    name: str
    agents: list[PRReviewAgent]
    parallel: bool = True
    description: str = ''


@dataclass
class FindingClassification:
    """Classification criteria for review findings.

    Extension point for projects to define severity rules, false positive patterns,
    and finding categorization logic.
    """

    severity_rules: dict[str, list[str]] = field(default_factory=dict)
    false_positive_patterns: list[str] = field(default_factory=list)
    auto_fix_patterns: list[str] = field(default_factory=list)

    def classify_finding(self, finding: dict[str, Any]) -> dict[str, Any]:
        """Classify a finding (severity, category, fix recommendation).

        Projects can override this method to apply custom classification logic.

        Args:
            finding: Raw finding from reviewer

        Returns:
            Classified finding with severity, category, and metadata
        """
        # Default implementation - projects override for custom logic
        return finding


@dataclass
class PRReviewConfig:
    """Complete PR review workflow configuration.

    Attributes:
        name: Workflow name
        agents: All available agents (generic + project-specific)
        phases: Review phases (triage, investigation, validation, synthesis, report)
        risk_config: Agent sets and validation depth per risk level
        finding_classification: Classification rules for findings
        voting_threshold: Consensus threshold for validation voting (default 2/3)
        report_template: Path to report template
        extension_hooks: Hooks for project-specific customization
    """

    name: str = 'pr_review'
    version: str = '1.0.0'
    agents: list[PRReviewAgent] = field(default_factory=list)
    phases: list[PRReviewPhaseConfig] = field(default_factory=list)

    # Risk-based agent selection
    risk_config: dict[RiskLevel, dict[str, Any]] = field(
        default_factory=lambda: {
            RiskLevel.LOW: {
                'required_agents': True,  # Only required agents
                'conditional_agents': False,  # Skip conditional agents
                'validation_depth': 'basic',  # finding-validator only
                'second_round': False,
            },
            RiskLevel.MEDIUM: {
                'required_agents': True,
                'conditional_agents': True,  # Run relevant conditional agents
                'validation_depth': 'standard',  # + adversarial + severity-auditor
                'second_round': True,  # Cross-pollination phase
            },
            RiskLevel.HIGH: {
                'required_agents': True,
                'conditional_agents': True,
                'validation_depth': 'thorough',  # + reinvestigator + council
                'second_round': True,
            },
        }
    )

    # Finding classification
    finding_classification: FindingClassification = field(
        default_factory=FindingClassification
    )

    # Validation
    voting_threshold: float = 0.67  # 2/3 consensus
    max_validation_rounds: int = 3

    # Report
    report_template: str = 'pr_review_report.md'

    # Extension points
    extension_hooks: dict[str, Callable] = field(default_factory=dict)

    def get_agents_for_risk(
        self, risk_level: RiskLevel, context: dict[str, Any]
    ) -> list[PRReviewAgent]:
        """Get agents to run based on risk level and diff context.

        Args:
            risk_level: Risk level of PR
            context: Diff context (files, changes, etc.)

        Returns:
            List of agents to run
        """
        risk_cfg = self.risk_config[risk_level]
        agents_to_run: list[PRReviewAgent] = []

        for agent in self.agents:
            if (
                agent.required
                and risk_cfg['required_agents']
                or (
                    not agent.required
                    and risk_cfg['conditional_agents']
                    and agent.should_run(context)
                )
            ):
                agents_to_run.append(agent)

        return agents_to_run

    def get_validators_for_risk(self, risk_level: RiskLevel) -> list[str]:
        """Get validator agent names for risk level.

        Args:
            risk_level: Risk level of PR

        Returns:
            List of validator agent names
        """
        depth = self.risk_config[risk_level]['validation_depth']

        validators = ['finding-validator']

        if depth in ('standard', 'thorough'):
            validators.extend(['adversarial-reviewer', 'severity-auditor'])

        if depth == 'thorough':
            validators.extend(['critical-reinvestigator', 'council-reviewer'])

        return validators

    def should_run_second_round(self, risk_level: RiskLevel) -> bool:
        """Check if second investigation round needed.

        Args:
            risk_level: Risk level of PR

        Returns:
            True if second round (cross-pollination) should run
        """
        return self.risk_config[risk_level]['second_round']


# =============================================================================
# GENERIC AGENTS (always available, projects extend)
# =============================================================================


def _always_trigger(context: dict[str, Any]) -> bool:
    """Trigger function for required agents."""
    return True


def _has_files_matching(pattern: str) -> Callable[[dict[str, Any]], bool]:
    """Create trigger that checks for files matching pattern.

    Args:
        pattern: Pattern to match (e.g., 'test', '.py', 'api/')

    Returns:
        Trigger function
    """

    def trigger(context: dict[str, Any]) -> bool:
        diff_files = context.get('diff_files', [])
        return any(pattern in f for f in diff_files)

    return trigger


def _has_file_count_over(threshold: int) -> Callable[[dict[str, Any]], bool]:
    """Create trigger that checks if file count exceeds threshold.

    Args:
        threshold: Minimum file count

    Returns:
        Trigger function
    """

    def trigger(context: dict[str, Any]) -> bool:
        diff_files = context.get('diff_files', [])
        return len(diff_files) >= threshold

    return trigger


GENERIC_AGENTS = [
    PRReviewAgent(
        name='requirements-reviewer',
        trigger=_always_trigger,
        prompt_template="""Review if all ticket requirements are implemented.

Ticket: {ticket_id}
Requirements:
{requirements}

Diff files:
{diff_files}

Check:
1. Each requirement has corresponding implementation
2. Implementation matches requirement intent
3. No requirements are missing or partially done

Report issues if requirements are incomplete or implementation doesn't match.""",
        model='opus',
        required=True,
        description='Verify all ticket requirements are implemented',
    ),
    PRReviewAgent(
        name='side-effects-reviewer',
        trigger=_always_trigger,
        prompt_template="""Review for unintended side effects on existing code.

Files modified:
{diff_files}

Check for:
1. Changes breaking existing functionality
2. Unintended behavior changes
3. Missing updates to dependent code
4. Breaking changes without migration path

Focus on blast radius - what else might this affect?""",
        model='opus',
        required=True,
        description='Identify unintended effects on existing code',
    ),
    PRReviewAgent(
        name='test-coverage-reviewer',
        trigger=_always_trigger,
        prompt_template="""Review test coverage and quality.

Files modified:
{diff_files}

Test files:
{test_files}

Check:
1. New/modified code has corresponding tests
2. Tests actually validate the behavior
3. Edge cases are covered
4. Tests will catch regressions

Report missing or inadequate test coverage.""",
        model='opus',
        required=True,
        description='Verify tests exist and are adequate',
    ),
    PRReviewAgent(
        name='architecture-reviewer',
        trigger=_has_file_count_over(10),
        prompt_template="""Review architectural impact of changes.

Files modified: {file_count}
{diff_files}

Check:
1. Changes follow existing architecture patterns
2. No architectural violations introduced
3. Appropriate abstraction level
4. Proper separation of concerns

Report architectural issues or inconsistencies.""",
        model='opus',
        required=False,
        description='Review architectural consistency (10+ files)',
    ),
]


def create_default_config() -> PRReviewConfig:
    """Create default PR review configuration.

    Projects can extend this by:
    1. Adding project-specific agents to the agents list
    2. Overriding finding_classification for custom rules
    3. Adding extension_hooks for custom phases
    4. Adjusting risk_config thresholds

    Returns:
        Default PRReviewConfig
    """
    return PRReviewConfig(
        agents=GENERIC_AGENTS.copy(),
        phases=[
            PRReviewPhaseConfig(
                name='triage',
                agents=[],  # No agents, just setup
                parallel=False,
                description='Setup worktree, gather context, assess risk',
            ),
            PRReviewPhaseConfig(
                name='investigation',
                agents=GENERIC_AGENTS,  # All agents run in parallel
                parallel=True,
                description='Run reviewers in parallel to find issues',
            ),
            PRReviewPhaseConfig(
                name='validation',
                agents=[],  # Validators, not review agents
                parallel=True,
                description='Validate findings, filter false positives',
            ),
            PRReviewPhaseConfig(
                name='synthesis',
                agents=[],  # Single consolidation step
                parallel=False,
                description='Consolidate findings, classify threads',
            ),
            PRReviewPhaseConfig(
                name='report',
                agents=[],  # Single report generation
                parallel=False,
                description='Generate final report and cleanup',
            ),
        ],
    )
