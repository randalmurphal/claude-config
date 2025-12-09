"""Unit tests for cc_orchestrations.workflow.loops.

Tests ValidationLoop, FixLoop, failure history, checkpointing,
and end-state validation.
"""

from unittest.mock import MagicMock

import pytest

from cc_orchestrations.core.runner import AgentResult
from cc_orchestrations.core.state import Issue, StateManager
from cc_orchestrations.workflow.loops import (
    FixLoop,
    LoopResult,
    ValidationLoop,
    issues_are_same,
)


@pytest.fixture
def mock_runner():
    """Create a mock AgentRunner."""
    runner = MagicMock()
    runner.run.return_value = AgentResult(
        success=True,
        data={'issues': [], 'status': 'pass'},
        agent_name='validator',
    )
    runner.run_parallel.return_value = [
        AgentResult(success=True, data={'issues': []}, agent_name='validator1'),
        AgentResult(success=True, data={'issues': []}, agent_name='validator2'),
    ]
    return runner


@pytest.fixture
def mock_state_manager(tmp_path):
    """Create a mock StateManager."""
    state_manager = MagicMock(spec=StateManager)
    state_manager.create_checkpoint = MagicMock()
    return state_manager


@pytest.fixture
def sample_issues():
    """Create sample issues for testing."""
    return [
        Issue(
            severity='critical',
            issue='Missing error handling',
            file='src/foo.py',
            line=10,
        ),
        Issue(
            severity='major',
            issue='Unused variable',
            file='src/bar.py',
            line=20,
        ),
    ]


class TestIssuesAreSame:
    """Tests for the issues_are_same helper function."""

    def test_same_issues_detected(self):
        """Identical issues should be detected as same."""
        prev = [Issue(severity='major', issue='Bug in foo')]
        curr = [Issue(severity='major', issue='Bug in foo')]

        assert issues_are_same(prev, curr) is True

    def test_different_issues_detected(self):
        """Different issues should not be same."""
        prev = [Issue(severity='major', issue='Bug in foo')]
        curr = [Issue(severity='major', issue='Bug in bar')]

        assert issues_are_same(prev, curr) is False

    def test_empty_lists(self):
        """Empty lists should not match (nothing to compare)."""
        assert issues_are_same([], []) is False

    def test_partial_overlap(self):
        """More than 50% overlap should be considered same."""
        prev = [
            Issue(severity='major', issue='Bug A'),
            Issue(severity='major', issue='Bug B'),
        ]
        curr = [
            Issue(severity='major', issue='Bug A'),  # Same
            Issue(severity='major', issue='Bug C'),  # Different
        ]
        # 1/2 = 50%, threshold is >50%, so not same
        assert issues_are_same(prev, curr) is False

    def test_high_overlap(self):
        """High overlap should be same."""
        prev = [
            Issue(severity='major', issue='Bug A'),
            Issue(severity='major', issue='Bug B'),
            Issue(severity='major', issue='Bug C'),
        ]
        curr = [
            Issue(severity='major', issue='Bug A'),
            Issue(severity='major', issue='Bug B'),
        ]
        # 2/2 = 100% overlap
        assert issues_are_same(prev, curr) is True


class TestLoopResult:
    """Tests for LoopResult dataclass."""

    def test_passed_result(self):
        """Test successful loop result."""
        result = LoopResult(passed=True, attempts=1)

        assert result.passed is True
        assert result.attempts == 1
        assert result.issues_found == []
        assert result.escalated is False

    def test_failed_with_issues(self):
        """Test failed result with issues."""
        issues = [Issue(severity='major', issue='Problem')]
        result = LoopResult(
            passed=False,
            attempts=3,
            issues_found=issues,
        )

        assert result.passed is False
        assert result.attempts == 3
        assert len(result.issues_found) == 1

    def test_escalated_result(self):
        """Test escalated result."""
        result = LoopResult(
            passed=False,
            attempts=3,
            escalated=True,
            escalation_reason='Max attempts reached',
        )

        assert result.escalated is True
        assert result.escalation_reason == 'Max attempts reached'

    def test_error_result(self):
        """Test result with error."""
        result = LoopResult(
            passed=False,
            attempts=1,
            error='Validation failed to run',
        )

        assert result.error == 'Validation failed to run'


class TestValidationLoopInit:
    """Tests for ValidationLoop initialization."""

    def test_basic_init(self, mock_runner):
        """Test basic initialization."""
        loop = ValidationLoop(mock_runner)

        assert loop.runner == mock_runner
        assert loop.max_attempts == 3
        assert loop.reviewers == 2
        assert loop.state_manager is None

    def test_init_with_state_manager(self, mock_runner, mock_state_manager):
        """Test initialization with state manager."""
        loop = ValidationLoop(mock_runner, state_manager=mock_state_manager)

        assert loop.state_manager == mock_state_manager

    def test_custom_config(self, mock_runner):
        """Test initialization with custom config."""
        loop = ValidationLoop(
            mock_runner,
            max_attempts=5,
            reviewers=3,
            same_issue_threshold=3,
        )

        assert loop.max_attempts == 5
        assert loop.reviewers == 3
        assert loop.same_issue_threshold == 3


class TestValidationLoopCheckpointing:
    """Tests for ValidationLoop checkpointing functionality."""

    def test_checkpoint_created_before_validation(
        self, mock_runner, mock_state_manager
    ):
        """Checkpoint should be created before each validation attempt."""
        loop = ValidationLoop(mock_runner, state_manager=mock_state_manager)

        # Mock validator returns no issues (pass on first attempt)
        mock_runner.run_parallel.return_value = [
            AgentResult(
                success=True, data={'issues': []}, agent_name='validator'
            ),
        ]

        loop.run('test_component', {})

        # Should create checkpoint for attempt 1
        mock_state_manager.create_checkpoint.assert_called()
        calls = mock_state_manager.create_checkpoint.call_args_list
        assert any('validation_attempt_1' in str(c) for c in calls)

    def test_checkpoint_after_fix_attempt(
        self, mock_runner, mock_state_manager, sample_issues
    ):
        """Checkpoint should be created after each fix attempt."""
        loop = ValidationLoop(
            mock_runner, max_attempts=2, state_manager=mock_state_manager
        )

        # First validation finds issues
        mock_runner.run_parallel.side_effect = [
            [
                AgentResult(
                    success=True,
                    data={'issues': [i.to_dict() for i in sample_issues]},
                    agent_name='validator',
                )
            ],
            [
                AgentResult(
                    success=True, data={'issues': []}, agent_name='validator'
                )
            ],  # Pass after fix
        ]
        mock_runner.run.return_value = AgentResult(
            success=True, data={}, agent_name='fix_executor'
        )

        loop.run('test_component', {})

        # Should have checkpoints for validation and fix
        calls = mock_state_manager.create_checkpoint.call_args_list
        checkpoint_names = [str(c) for c in calls]
        assert any('validation_attempt' in name for name in checkpoint_names)
        assert any('fix_attempt' in name for name in checkpoint_names)

    def test_no_checkpoint_without_state_manager(self, mock_runner):
        """No checkpointing when state_manager is None."""
        loop = ValidationLoop(mock_runner, state_manager=None)

        mock_runner.run_parallel.return_value = [
            AgentResult(
                success=True, data={'issues': []}, agent_name='validator'
            ),
        ]

        # Should not raise
        result = loop.run('test_component', {})
        assert result.passed is True


class TestValidationLoopFailureHistory:
    """Tests for ValidationLoop failure history in fix prompts."""

    def test_first_attempt_no_history(self, mock_runner, sample_issues):
        """First fix attempt should have no history in prompt."""
        loop = ValidationLoop(mock_runner, max_attempts=2)

        # Capture the prompt sent to fix_executor
        prompts_captured = []

        def capture_prompt(agent_name, prompt, **kwargs):
            if agent_name == 'fix_executor':
                prompts_captured.append(prompt)
            return AgentResult(success=True, data={}, agent_name=agent_name)

        mock_runner.run.side_effect = capture_prompt
        mock_runner.run_parallel.side_effect = [
            [
                AgentResult(
                    success=True,
                    data={'issues': [i.to_dict() for i in sample_issues]},
                    agent_name='validator',
                )
            ],
            [
                AgentResult(
                    success=True, data={'issues': []}, agent_name='validator'
                )
            ],
        ]

        loop.run('test_component', {})

        # First fix prompt should not have "Previous Attempts" section
        assert len(prompts_captured) == 1
        assert 'Previous Attempts' not in prompts_captured[0]

    def test_second_attempt_has_history(self, mock_runner, sample_issues):
        """Second fix attempt should include history from first."""
        loop = ValidationLoop(mock_runner, max_attempts=3)

        prompts_captured = []

        def capture_prompt(agent_name, prompt, **kwargs):
            if agent_name == 'fix_executor':
                prompts_captured.append(prompt)
            return AgentResult(success=True, data={}, agent_name=agent_name)

        mock_runner.run.side_effect = capture_prompt

        # Issues persist through two validation rounds
        mock_runner.run_parallel.side_effect = [
            [
                AgentResult(
                    success=True,
                    data={'issues': [i.to_dict() for i in sample_issues]},
                    agent_name='validator',
                )
            ],
            [
                AgentResult(
                    success=True,
                    data={'issues': [i.to_dict() for i in sample_issues]},
                    agent_name='validator',
                )
            ],
            [
                AgentResult(
                    success=True, data={'issues': []}, agent_name='validator'
                )
            ],
        ]

        loop.run('test_component', {})

        # Second fix prompt should have "Previous Attempts" section
        assert len(prompts_captured) == 2
        assert (
            'Previous Attempts' not in prompts_captured[0]
        )  # First has no history
        assert 'Previous Attempts' in prompts_captured[1]  # Second has history
        assert 'Attempt 1' in prompts_captured[1]

    def test_history_includes_outcome(self, mock_runner, sample_issues):
        """History should include outcome of previous attempts."""
        loop = ValidationLoop(mock_runner, max_attempts=3)

        prompts_captured = []

        def capture_prompt(agent_name, prompt, **kwargs):
            if agent_name == 'fix_executor':
                prompts_captured.append(prompt)
            return AgentResult(success=True, data={}, agent_name=agent_name)

        mock_runner.run.side_effect = capture_prompt

        mock_runner.run_parallel.side_effect = [
            [
                AgentResult(
                    success=True,
                    data={'issues': [i.to_dict() for i in sample_issues]},
                    agent_name='validator',
                )
            ],
            [
                AgentResult(
                    success=True,
                    data={'issues': [i.to_dict() for i in sample_issues]},
                    agent_name='validator',
                )
            ],
            [
                AgentResult(
                    success=True, data={'issues': []}, agent_name='validator'
                )
            ],
        ]

        loop.run('test_component', {})

        # Check that history includes meaningful info
        second_prompt = prompts_captured[1]
        assert 'issues remaining' in second_prompt.lower()
        assert 'What to try differently' in second_prompt


class TestValidationLoopEndStateValidation:
    """Tests for ValidationLoop.run_end_state_validation method."""

    def test_empty_components_passes(self, mock_runner):
        """Empty component list should pass immediately."""
        loop = ValidationLoop(mock_runner)

        result = loop.run_end_state_validation([], {})

        assert result.passed is True
        assert result.attempts == 1
        mock_runner.run.assert_not_called()

    def test_integration_check_called(self, mock_runner):
        """End-state validation should check component integration."""
        loop = ValidationLoop(mock_runner)
        mock_runner.run.return_value = AgentResult(
            success=True,
            data={
                'integration_passed': True,
                'issues': [],
                'recommendation': 'PROCEED',
            },
            agent_name='validator',
        )

        result = loop.run_end_state_validation(
            components=['src/foo.py', 'src/bar.py'],
            context={'work_dir': '/test'},
            spec_summary='Add user auth',
        )

        assert result.passed is True
        mock_runner.run.assert_called_once()

        # Check prompt includes components
        call_args = mock_runner.run.call_args
        prompt = call_args[0][1]  # Second positional arg is prompt
        assert 'src/foo.py' in prompt
        assert 'src/bar.py' in prompt
        assert 'Add user auth' in prompt

    def test_integration_issues_returned(self, mock_runner):
        """Integration issues should be returned in result."""
        loop = ValidationLoop(mock_runner)
        mock_runner.run.return_value = AgentResult(
            success=True,
            data={
                'integration_passed': False,
                'issues': [
                    {
                        'type': 'circular_import',
                        'components': ['src/foo.py', 'src/bar.py'],
                        'issue': 'Circular import detected',
                        'severity': 'critical',
                    }
                ],
                'recommendation': 'FIX_REQUIRED',
            },
            agent_name='validator',
        )

        result = loop.run_end_state_validation(
            components=['src/foo.py', 'src/bar.py'],
            context={},
        )

        assert result.passed is False
        assert len(result.issues_found) == 1
        assert 'Circular import' in result.issues_found[0].issue

    def test_manual_check_escalates(self, mock_runner):
        """MANUAL_CHECK recommendation should escalate."""
        loop = ValidationLoop(mock_runner)
        mock_runner.run.return_value = AgentResult(
            success=True,
            data={
                'integration_passed': False,
                'issues': [],
                'recommendation': 'MANUAL_CHECK',
            },
            agent_name='validator',
        )

        result = loop.run_end_state_validation(['src/foo.py'], {})

        assert result.passed is False
        assert result.escalated is True
        assert 'manual review' in result.escalation_reason.lower()

    def test_uses_opus_model(self, mock_runner):
        """End-state validation should use opus model."""
        loop = ValidationLoop(mock_runner)
        mock_runner.run.return_value = AgentResult(
            success=True,
            data={
                'integration_passed': True,
                'issues': [],
                'recommendation': 'PROCEED',
            },
            agent_name='validator',
        )

        loop.run_end_state_validation(['src/foo.py'], {})

        call_kwargs = mock_runner.run.call_args[1]
        assert call_kwargs.get('model_override') == 'opus'

    def test_checkpoint_created_with_state_manager(
        self, mock_runner, mock_state_manager
    ):
        """Checkpoint should be created after end-state validation."""
        loop = ValidationLoop(mock_runner, state_manager=mock_state_manager)
        mock_runner.run.return_value = AgentResult(
            success=True,
            data={
                'integration_passed': True,
                'issues': [],
                'recommendation': 'PROCEED',
            },
            agent_name='validator',
        )

        loop.run_end_state_validation(['src/foo.py'], {})

        mock_state_manager.create_checkpoint.assert_called_with(
            'end_state_validation'
        )

    def test_validation_failure_returns_error(self, mock_runner):
        """Validation failure should return error in result."""
        loop = ValidationLoop(mock_runner)
        mock_runner.run.return_value = AgentResult(
            success=False,
            error='Timeout',
            agent_name='validator',
        )

        result = loop.run_end_state_validation(['src/foo.py'], {})

        assert result.passed is False
        assert 'Timeout' in result.error


class TestFixLoop:
    """Tests for FixLoop class."""

    def test_basic_fix(self, mock_runner, sample_issues):
        """Test basic fix loop execution."""
        loop = FixLoop(mock_runner)

        mock_runner.run.return_value = AgentResult(
            success=True,
            data={'status': 'fixed'},
            agent_name='fix_executor',
        )

        loop.run('test_component', sample_issues, {}, validate_after=False)

        # Without validation, should complete after one fix
        assert mock_runner.run.called

    def test_max_attempts_respected(self, mock_runner, sample_issues):
        """Max attempts should be respected."""
        loop = FixLoop(mock_runner, max_attempts=2)

        # Always return issues (never fix)
        mock_runner.run.return_value = AgentResult(
            success=True,
            data={'issues': [i.to_dict() for i in sample_issues]},
            agent_name='fix_executor',
        )

        result = loop.run(
            'test_component', sample_issues, {}, validate_after=False
        )

        # Should stop after max_attempts
        assert result.attempts <= 2
