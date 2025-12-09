"""Unit tests for cc_orchestrations.core.config.

These tests verify config creation, serialization, and mode handling
without any API calls.
"""

from cc_orchestrations.core.config import (
    AgentConfig,
    Config,
    ExecutionMode,
    PhaseConfig,
    RiskConfig,
    ValidationConfig,
    VotingGateConfig,
    get_timeout_for_model,
)


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_mode_values(self):
        """Verify all expected modes exist."""
        assert ExecutionMode.QUICK.value == 'quick'
        assert ExecutionMode.STANDARD.value == 'standard'
        assert ExecutionMode.FULL.value == 'full'

    def test_mode_from_string(self):
        """Test creating mode from string."""
        assert ExecutionMode('quick') == ExecutionMode.QUICK
        assert ExecutionMode('standard') == ExecutionMode.STANDARD
        assert ExecutionMode('full') == ExecutionMode.FULL


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_config(self):
        """Test config with defaults."""
        config = Config(name='test')
        assert config.name == 'test'
        assert config.dry_run is False
        assert config.default_model == 'sonnet'
        assert config.mode == ExecutionMode.STANDARD

    def test_config_with_dry_run(self):
        """Test dry_run flag."""
        config = Config(name='test', dry_run=True)
        assert config.dry_run is True

    def test_config_serialization(self):
        """Test config round-trip serialization."""
        original = Config(
            name='test-serialize',
            mode=ExecutionMode.FULL,
            dry_run=True,
            default_model='opus',
            state_dir='.custom-state',
        )

        data = original.to_dict()
        assert data['name'] == 'test-serialize'
        assert data['mode'] == 'full'
        assert data['dry_run'] is True
        assert data['default_model'] == 'opus'
        assert data['state_dir'] == '.custom-state'

        restored = Config.from_dict(data)
        assert restored.name == original.name
        assert restored.mode == original.mode
        assert restored.dry_run == original.dry_run
        assert restored.default_model == original.default_model
        assert restored.state_dir == original.state_dir

    def test_config_with_phases(self):
        """Test config with phase definitions."""
        phases = [
            PhaseConfig(name='phase1', description='First phase'),
            PhaseConfig(
                name='phase2', description='Second phase', agents=['agent1']
            ),
        ]
        config = Config(name='test', phases=phases)
        assert len(config.phases) == 2
        assert config.phases[0].name == 'phase1'
        assert config.phases[1].agents == ['agent1']

    def test_config_with_agents(self):
        """Test config with agent definitions."""
        agents = {
            'validator': AgentConfig(
                name='validator',
                model='opus',
                allowed_tools=['Read', 'Grep'],
            ),
        }
        config = Config(name='test', agents=agents)
        assert 'validator' in config.agents
        assert config.agents['validator'].model == 'opus'


class TestPhaseConfig:
    """Tests for PhaseConfig."""

    def test_phase_defaults(self):
        """Test phase with defaults."""
        phase = PhaseConfig(name='test-phase')
        assert phase.name == 'test-phase'
        assert phase.description == ''
        assert phase.agents == []
        assert phase.skip_condition == ''  # Empty string default
        assert phase.max_attempts == 3

    def test_phase_serialization(self):
        """Test phase round-trip."""
        original = PhaseConfig(
            name='validate',
            description='Run validation',
            agents=['validator', 'security_auditor'],
            skip_condition='is_test_only',
            max_attempts=5,
        )

        data = original.to_dict()
        restored = PhaseConfig.from_dict(data)

        assert restored.name == original.name
        assert restored.agents == original.agents
        assert restored.skip_condition == original.skip_condition
        assert restored.max_attempts == original.max_attempts


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_agent_defaults(self):
        """Test agent with defaults."""
        agent = AgentConfig(name='test-agent')
        assert agent.name == 'test-agent'
        assert agent.model == 'sonnet'
        assert agent.allowed_tools == []

    def test_agent_with_tools(self):
        """Test agent with allowed tools."""
        agent = AgentConfig(
            name='investigator',
            model='opus',
            allowed_tools=['Read', 'Grep', 'Glob', 'Bash'],
        )
        assert agent.model == 'opus'
        assert 'Bash' in agent.allowed_tools


class TestValidationConfig:
    """Tests for ValidationConfig."""

    def test_validation_defaults(self):
        """Test validation config defaults."""
        config = ValidationConfig()
        assert config.max_fix_attempts >= 1
        assert config.reviewers_per_validation >= 1
        assert config.same_issue_threshold >= 1

    def test_validation_custom(self):
        """Test custom validation config."""
        config = ValidationConfig(
            max_fix_attempts=5,
            reviewers_per_validation=3,
            same_issue_threshold=2,
        )
        assert config.max_fix_attempts == 5


class TestRiskConfig:
    """Tests for RiskConfig."""

    def test_risk_defaults(self):
        """Test risk config defaults."""
        config = RiskConfig()
        assert isinstance(config.reviewers_by_risk, dict)
        assert 'low' in config.reviewers_by_risk
        assert 'medium' in config.reviewers_by_risk
        assert 'high' in config.reviewers_by_risk

    def test_reviewers_scale_with_risk(self):
        """Test that higher risk means more reviewers."""
        config = RiskConfig()
        assert (
            config.reviewers_by_risk['low']
            <= config.reviewers_by_risk['medium']
        )
        assert (
            config.reviewers_by_risk['medium']
            <= config.reviewers_by_risk['high']
        )


class TestVotingGateConfig:
    """Tests for VotingGateConfig."""

    def test_voting_gate(self):
        """Test voting gate configuration."""
        gate = VotingGateConfig(
            name='test-gate',
            trigger_condition='risk_level == "high"',
            num_voters=3,
            options=['approve', 'reject', 'abstain'],
            voter_agent='investigator',
        )
        assert gate.num_voters == 3
        assert len(gate.options) == 3
        assert gate.consensus_threshold == 0.67  # Default is 2/3

    def test_voting_gate_with_threshold(self):
        """Test voting gate with custom threshold."""
        gate = VotingGateConfig(
            name='strict-gate',
            trigger_condition='always',
            num_voters=5,
            options=['yes', 'no'],
            voter_agent='validator',
            consensus_threshold=0.8,
        )
        assert gate.consensus_threshold == 0.8


class TestModelTimeouts:
    """Tests for model timeout configuration."""

    def test_opus_timeout(self):
        """Opus gets longest timeout."""
        timeout = get_timeout_for_model('opus')
        assert timeout >= 300

    def test_sonnet_timeout(self):
        """Sonnet gets medium timeout (8 minutes)."""
        timeout = get_timeout_for_model('sonnet')
        assert timeout == 480

    def test_haiku_timeout(self):
        """Haiku gets shortest timeout (3 minutes)."""
        timeout = get_timeout_for_model('haiku')
        assert timeout == 180

    def test_partial_match(self):
        """Test partial model name matching."""
        timeout = get_timeout_for_model('claude-3-opus-latest')
        assert timeout >= 300

    def test_unknown_model_default(self):
        """Unknown models get default timeout."""
        timeout = get_timeout_for_model('unknown-model-xyz')
        assert timeout > 0  # Should get some default
