"""Configuration for orchestration workflows.

All configurable aspects: models, prompts, thresholds, agent definitions.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


LOG = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """Execution mode controlling validation depth and parallelization."""

    QUICK = 'quick'  # Aggressive parallel, end-only validation
    STANDARD = 'standard'  # Level-based parallel, intermediate validation
    FULL = 'full'  # Conservative sequential, full validation at each step


@dataclass
class ModeConfig:
    """Configuration specific to an execution mode."""

    name: str
    parallelization: str  # "aggressive", "by_level", "conservative"
    validate_after_skeleton: bool
    validate_after_implementation: (
        str  # "none", "lint_only", "quick_review", "full_review"
    )
    validate_after_level: bool  # For STANDARD mode
    fix_all_severities: bool  # True = fix even minor issues
    backtrack_allowed: bool
    skeleton_gate: bool  # Full mode only - review gate after all skeletons
    production_gate: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'parallelization': self.parallelization,
            'validate_after_skeleton': self.validate_after_skeleton,
            'validate_after_implementation': self.validate_after_implementation,
            'validate_after_level': self.validate_after_level,
            'fix_all_severities': self.fix_all_severities,
            'backtrack_allowed': self.backtrack_allowed,
            'skeleton_gate': self.skeleton_gate,
            'production_gate': self.production_gate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ModeConfig':
        return cls(
            name=data.get('name', 'standard'),
            parallelization=data.get('parallelization', 'by_level'),
            validate_after_skeleton=data.get('validate_after_skeleton', True),
            validate_after_implementation=data.get(
                'validate_after_implementation', 'quick_review'
            ),
            validate_after_level=data.get('validate_after_level', True),
            fix_all_severities=data.get('fix_all_severities', False),
            backtrack_allowed=data.get('backtrack_allowed', False),
            skeleton_gate=data.get('skeleton_gate', False),
            production_gate=data.get('production_gate', False),
        )


# Pre-defined mode configurations
MODE_CONFIGS: dict[ExecutionMode, ModeConfig] = {
    ExecutionMode.QUICK: ModeConfig(
        name='quick',
        parallelization='aggressive',
        validate_after_skeleton=False,
        validate_after_implementation='lint_only',
        validate_after_level=False,
        fix_all_severities=False,  # Only critical/high
        backtrack_allowed=False,
        skeleton_gate=False,
        production_gate=False,
    ),
    ExecutionMode.STANDARD: ModeConfig(
        name='standard',
        parallelization='by_level',
        validate_after_skeleton=True,  # Quick structure review
        validate_after_implementation='quick_review',
        validate_after_level=True,
        fix_all_severities=False,  # Critical/high/medium
        backtrack_allowed=False,  # Limited backtrack on critical only
        skeleton_gate=False,
        production_gate=False,
    ),
    ExecutionMode.FULL: ModeConfig(
        name='full',
        parallelization='conservative',
        validate_after_skeleton=True,  # Full review
        validate_after_implementation='full_review',
        validate_after_level=False,  # N/A - sequential
        fix_all_severities=True,  # ALL issues including minor
        backtrack_allowed=True,
        skeleton_gate=True,  # Vote after all skeletons
        production_gate=True,  # Vote before shipping
    ),
}


@dataclass
class AgentConfig:
    """Configuration for an agent type."""

    name: str
    model: str = 'sonnet'
    schema: str = ''  # Schema name from schemas.py
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    prompt_template: str = ''
    timeout: int = 300  # seconds
    description: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'model': self.model,
            'schema': self.schema,
            'allowed_tools': self.allowed_tools,
            'disallowed_tools': self.disallowed_tools,
            'prompt_template': self.prompt_template,
            'timeout': self.timeout,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'AgentConfig':
        return cls(
            name=data['name'],
            model=data.get('model', 'sonnet'),
            schema=data.get('schema', ''),
            allowed_tools=data.get('allowed_tools', []),
            disallowed_tools=data.get('disallowed_tools', []),
            prompt_template=data.get('prompt_template', ''),
            timeout=data.get('timeout', 300),
            description=data.get('description', ''),
        )


@dataclass
class VotingGateConfig:
    """Configuration for a voting gate."""

    name: str
    trigger_condition: str  # Python expression evaluated against state
    num_voters: int = 3
    consensus_threshold: float = 0.67  # 2/3 default
    voter_agent: str = 'investigator'
    schema: str = ''
    prompt_template: str = ''
    options: list[str] = field(default_factory=list)
    description: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'trigger_condition': self.trigger_condition,
            'num_voters': self.num_voters,
            'consensus_threshold': self.consensus_threshold,
            'voter_agent': self.voter_agent,
            'schema': self.schema,
            'prompt_template': self.prompt_template,
            'options': self.options,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'VotingGateConfig':
        return cls(
            name=data['name'],
            trigger_condition=data.get('trigger_condition', 'False'),
            num_voters=data.get('num_voters', 3),
            consensus_threshold=data.get('consensus_threshold', 0.67),
            voter_agent=data.get('voter_agent', 'investigator'),
            schema=data.get('schema', ''),
            prompt_template=data.get('prompt_template', ''),
            options=data.get('options', []),
            description=data.get('description', ''),
        )


@dataclass
class PhaseConfig:
    """Configuration for a workflow phase."""

    name: str
    description: str = ''
    agents: list[str] = field(default_factory=list)  # Agent names to use
    parallel: bool = False  # Run agents in parallel
    voting_gate: str = ''  # Voting gate to trigger after phase
    max_attempts: int = 3
    skip_condition: str = ''  # Python expression; if true, skip phase
    next_phase: str = ''  # Override automatic progression
    on_failure: str = 'escalate'  # escalate, retry, skip, vote

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'agents': self.agents,
            'parallel': self.parallel,
            'voting_gate': self.voting_gate,
            'max_attempts': self.max_attempts,
            'skip_condition': self.skip_condition,
            'next_phase': self.next_phase,
            'on_failure': self.on_failure,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'PhaseConfig':
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            agents=data.get('agents', []),
            parallel=data.get('parallel', False),
            voting_gate=data.get('voting_gate', ''),
            max_attempts=data.get('max_attempts', 3),
            skip_condition=data.get('skip_condition', ''),
            next_phase=data.get('next_phase', ''),
            on_failure=data.get('on_failure', 'escalate'),
        )


@dataclass
class ValidationConfig:
    """Configuration for validation loops."""

    max_fix_attempts: int = 3
    reviewers_per_validation: int = 2
    require_all_pass: bool = True
    escalate_on_same_issue: bool = True
    same_issue_threshold: int = 2  # Attempts before voting

    def to_dict(self) -> dict[str, Any]:
        return {
            'max_fix_attempts': self.max_fix_attempts,
            'reviewers_per_validation': self.reviewers_per_validation,
            'require_all_pass': self.require_all_pass,
            'escalate_on_same_issue': self.escalate_on_same_issue,
            'same_issue_threshold': self.same_issue_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ValidationConfig':
        return cls(
            max_fix_attempts=data.get('max_fix_attempts', 3),
            reviewers_per_validation=data.get('reviewers_per_validation', 2),
            require_all_pass=data.get('require_all_pass', True),
            escalate_on_same_issue=data.get('escalate_on_same_issue', True),
            same_issue_threshold=data.get('same_issue_threshold', 2),
        )


@dataclass
class RiskConfig:
    """Configuration for risk-based scaling."""

    # Thresholds for risk levels
    low_threshold: int = 3  # files changed
    medium_threshold: int = 10
    high_threshold: int = 25

    # Transitive dependency thresholds
    impact_vote_threshold: int = 10

    # Reviewers per risk level
    reviewers_by_risk: dict[str, int] = field(
        default_factory=lambda: {
            'low': 2,
            'medium': 4,
            'high': 6,
            'critical': 6,
        }
    )

    # Model selection by risk (for validation)
    validator_model_by_risk: dict[str, str] = field(
        default_factory=lambda: {
            'low': 'sonnet',
            'medium': 'sonnet',
            'high': 'opus',
            'critical': 'opus',
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            'low_threshold': self.low_threshold,
            'medium_threshold': self.medium_threshold,
            'high_threshold': self.high_threshold,
            'impact_vote_threshold': self.impact_vote_threshold,
            'reviewers_by_risk': self.reviewers_by_risk,
            'validator_model_by_risk': self.validator_model_by_risk,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'RiskConfig':
        return cls(
            low_threshold=data.get('low_threshold', 3),
            medium_threshold=data.get('medium_threshold', 10),
            high_threshold=data.get('high_threshold', 25),
            impact_vote_threshold=data.get('impact_vote_threshold', 10),
            reviewers_by_risk=data.get(
                'reviewers_by_risk',
                {'low': 2, 'medium': 4, 'high': 6, 'critical': 6},
            ),
            validator_model_by_risk=data.get(
                'validator_model_by_risk',
                {
                    'low': 'sonnet',
                    'medium': 'sonnet',
                    'high': 'opus',
                    'critical': 'opus',
                },
            ),
        )


@dataclass
class Config:
    """Complete workflow configuration."""

    # Workflow identity
    name: str = 'conduct'
    version: str = '1.0.0'
    description: str = ''

    # Execution mode
    mode: ExecutionMode = ExecutionMode.STANDARD
    mode_config: ModeConfig | None = None  # Auto-set from mode if not provided
    dry_run: bool = (
        False  # When True, agents return test data without doing work
    )

    # Agents
    agents: dict[str, AgentConfig] = field(default_factory=dict)

    # Phases
    phases: list[PhaseConfig] = field(default_factory=list)

    # Voting gates
    voting_gates: dict[str, VotingGateConfig] = field(default_factory=dict)

    # Validation
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    # Risk scaling
    risk: RiskConfig = field(default_factory=RiskConfig)

    # Paths
    prompts_dir: str = ''
    state_dir: str = '.spec'

    # Claude CLI options
    claude_path: str = 'claude'
    default_model: str = 'sonnet'
    permission_mode: str = 'default'

    def __post_init__(self) -> None:
        """Set mode_config from mode if not provided."""
        if self.mode_config is None:
            self.mode_config = MODE_CONFIGS.get(
                self.mode, MODE_CONFIGS[ExecutionMode.STANDARD]
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'mode': self.mode.value,
            'mode_config': self.mode_config.to_dict()
            if self.mode_config
            else None,
            'dry_run': self.dry_run,
            'agents': {k: v.to_dict() for k, v in self.agents.items()},
            'phases': [p.to_dict() for p in self.phases],
            'voting_gates': {
                k: v.to_dict() for k, v in self.voting_gates.items()
            },
            'validation': self.validation.to_dict(),
            'risk': self.risk.to_dict(),
            'prompts_dir': self.prompts_dir,
            'state_dir': self.state_dir,
            'claude_path': self.claude_path,
            'default_model': self.default_model,
            'permission_mode': self.permission_mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Config':
        mode_str = data.get('mode', 'standard')
        try:
            mode = ExecutionMode(mode_str)
        except ValueError:
            LOG.warning(f"Unknown mode '{mode_str}', defaulting to standard")
            mode = ExecutionMode.STANDARD

        mode_config_data = data.get('mode_config')
        mode_config = (
            ModeConfig.from_dict(mode_config_data) if mode_config_data else None
        )

        return cls(
            name=data.get('name', 'conduct'),
            version=data.get('version', '1.0.0'),
            description=data.get('description', ''),
            mode=mode,
            mode_config=mode_config,
            dry_run=data.get('dry_run', False),
            agents={
                k: AgentConfig.from_dict(v)
                for k, v in data.get('agents', {}).items()
            },
            phases=[PhaseConfig.from_dict(p) for p in data.get('phases', [])],
            voting_gates={
                k: VotingGateConfig.from_dict(v)
                for k, v in data.get('voting_gates', {}).items()
            },
            validation=ValidationConfig.from_dict(data.get('validation', {})),
            risk=RiskConfig.from_dict(data.get('risk', {})),
            prompts_dir=data.get('prompts_dir', ''),
            state_dir=data.get('state_dir', '.spec'),
            claude_path=data.get('claude_path', 'claude'),
            default_model=data.get('default_model', 'sonnet'),
            permission_mode=data.get('permission_mode', 'default'),
        )

    def get_agent(self, name: str) -> AgentConfig:
        """Get agent config by name."""
        if name not in self.agents:
            raise ValueError(
                f'Unknown agent: {name}. Available: {list(self.agents.keys())}'
            )
        return self.agents[name]

    def get_voting_gate(self, name: str) -> VotingGateConfig:
        """Get voting gate config by name."""
        if name not in self.voting_gates:
            raise ValueError(f'Unknown voting gate: {name}')
        return self.voting_gates[name]

    def get_phase(self, name: str) -> PhaseConfig:
        """Get phase config by name."""
        for phase in self.phases:
            if phase.name == name:
                return phase
        raise ValueError(f'Unknown phase: {name}')

    def get_reviewers_for_risk(self, risk_level: str) -> int:
        """Get number of reviewers for a risk level."""
        return self.risk.reviewers_by_risk.get(risk_level, 2)


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file or return defaults."""
    if config_path and config_path.exists():
        try:
            data = json.loads(config_path.read_text())
            return Config.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            LOG.warning(f'Failed to load config from {config_path}: {e}')

    # Return default config
    return Config()


def save_config(config: Config, config_path: Path) -> None:
    """Save configuration to file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config.to_dict(), indent=2))
