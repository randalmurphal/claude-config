"""Unit tests for cc_orchestrations.workflow.engine.

Tests WorkflowEngine, ExecutionContext, PhaseResult, and condition evaluation.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cc_orchestrations.core.config import Config, ExecutionMode, PhaseConfig
from cc_orchestrations.core.state import PhaseStatus, State, StateManager
from cc_orchestrations.workflow.engine import (
    ExecutionContext,
    PhaseResult,
    WorkflowEngine,
)


@pytest.fixture
def temp_work_dir(tmp_path: Path) -> Path:
    """Create a temporary work directory."""
    work = tmp_path / 'work'
    work.mkdir()
    return work


@pytest.fixture
def temp_spec_path(tmp_path: Path) -> Path:
    """Create a temporary spec file."""
    spec = tmp_path / 'SPEC.md'
    spec.write_text('# Test Spec\n\nTest content.')
    return spec


@pytest.fixture
def basic_config() -> Config:
    """Create a basic configuration."""
    return Config(
        dry_run=True,
        mode=ExecutionMode.QUICK,
        phases=[
            PhaseConfig(name='phase1', agents=['agent1']),
            PhaseConfig(name='phase2', agents=['agent2']),
            PhaseConfig(name='phase3', agents=['agent3']),
        ],
    )


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_success_result(self):
        """Test successful phase result."""
        result = PhaseResult(success=True)

        assert result.success is True
        assert result.error == ''
        assert result.needs_user_input is False

    def test_failure_result(self):
        """Test failed phase result."""
        result = PhaseResult(
            success=False,
            error='Something went wrong',
        )

        assert result.success is False
        assert result.error == 'Something went wrong'

    def test_user_input_result(self):
        """Test result requiring user input."""
        result = PhaseResult(
            success=False,
            needs_user_input=True,
            user_prompt='Choose A or B?',
        )

        assert result.needs_user_input is True
        assert result.user_prompt == 'Choose A or B?'

    def test_skip_to_result(self):
        """Test result with skip_to."""
        result = PhaseResult(
            success=True,
            skip_to='phase5',
        )

        assert result.skip_to == 'phase5'

    def test_data_field(self):
        """Test result with additional data."""
        result = PhaseResult(
            success=True,
            data={'files_created': 5, 'issues_found': 0},
        )

        assert result.data['files_created'] == 5
        assert result.data['issues_found'] == 0


class TestExecutionContext:
    """Tests for ExecutionContext."""

    @pytest.fixture
    def context(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
        basic_config: Config,
    ) -> ExecutionContext:
        """Create an execution context for testing."""
        state_dir = temp_work_dir / '.state'
        state_manager = StateManager(state_dir)
        state_manager.ensure_dirs()

        runner = MagicMock()

        return ExecutionContext(
            config=basic_config,
            state=State(),
            state_manager=state_manager,
            runner=runner,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
        )

    def test_basic_properties(self, context: ExecutionContext):
        """Test basic context properties."""
        assert context.dry_run is True
        assert context.work_dir.exists()
        assert context.spec_path.exists()

    def test_mode_config(self, context: ExecutionContext):
        """Test mode_config property."""
        mode_config = context.mode_config
        # Quick mode should have mode_config set
        assert mode_config is not None

    def test_log_status(self, context: ExecutionContext):
        """Test log_status method."""
        callback = MagicMock()
        context.on_status_change = callback

        context.log_status('phase1', 'Starting')

        callback.assert_called_once_with('phase1', 'Starting')

    def test_log_status_no_callback(self, context: ExecutionContext):
        """Test log_status without callback."""
        # Should not raise
        context.log_status('phase1', 'Starting')

    def test_get_completed_components(self, context: ExecutionContext):
        """Test get_completed_components method."""
        context.state.components['comp_a'] = MagicMock()
        context.state.components['comp_a'].status = 'complete'

        completed = context.get_completed_components()

        # Depends on state implementation
        assert isinstance(completed, list)

    def test_get_component_context(self, context: ExecutionContext):
        """Test get_component_context method."""
        ctx = context.get_component_context('my_component.py')

        assert 'component' in ctx
        assert ctx['component'] == 'my_component.py'
        assert 'work_dir' in ctx


class TestWorkflowEngine:
    """Tests for WorkflowEngine."""

    @pytest.fixture
    def engine(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
        basic_config: Config,
    ) -> WorkflowEngine:
        """Create a workflow engine for testing."""
        return WorkflowEngine(
            config=basic_config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
        )

    def test_engine_creation(self, engine: WorkflowEngine):
        """Test basic engine creation."""
        assert engine.config.dry_run is True
        assert engine.work_dir.exists()
        assert engine.draft_mode is False

    def test_engine_draft_mode(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
        basic_config: Config,
    ):
        """Test engine in draft mode."""
        engine = WorkflowEngine(
            config=basic_config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
            draft_mode=True,
        )

        assert engine.draft_mode is True

    def test_run_with_no_phases(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
    ):
        """Test run with no phases configured."""
        config = Config(
            dry_run=True,
            mode=ExecutionMode.QUICK,
            phases=[],  # No phases
        )

        engine = WorkflowEngine(
            config=config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
        )

        result = engine.run(resume=False)

        assert result is False

    def test_run_already_complete(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
        basic_config: Config,
    ):
        """Test run when workflow is already complete."""
        engine = WorkflowEngine(
            config=basic_config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
        )

        # Set state to complete
        state = State()
        state.current_phase = 'complete'
        engine.state_manager.save(state)

        result = engine.run(resume=True)

        assert result is True


class TestConditionEvaluation:
    """Tests for condition evaluation in WorkflowEngine."""

    @pytest.fixture
    def engine(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
        basic_config: Config,
    ) -> WorkflowEngine:
        """Create engine for testing."""
        return WorkflowEngine(
            config=basic_config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
        )

    @pytest.fixture
    def context(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
        basic_config: Config,
    ) -> ExecutionContext:
        """Create context for testing."""
        state_dir = temp_work_dir / '.state'
        state_manager = StateManager(state_dir)
        state_manager.ensure_dirs()

        return ExecutionContext(
            config=basic_config,
            state=State(),
            state_manager=state_manager,
            runner=MagicMock(),
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
            risk_level='medium',
        )

    def test_eval_simple_truthy(
        self, engine: WorkflowEngine, context: ExecutionContext
    ):
        """Test simple truthy condition."""
        context.state.is_new_project = True

        result = engine._eval_condition('is_new_project', context)

        assert result is True

    def test_eval_simple_falsy(
        self, engine: WorkflowEngine, context: ExecutionContext
    ):
        """Test simple falsy condition."""
        context.state.is_new_project = False

        result = engine._eval_condition('is_new_project', context)

        assert result is False

    def test_eval_equality(
        self, engine: WorkflowEngine, context: ExecutionContext
    ):
        """Test equality condition."""
        context.risk_level = 'high'

        result = engine._eval_condition("risk_level == 'high'", context)

        assert result is True

    def test_eval_inequality(
        self, engine: WorkflowEngine, context: ExecutionContext
    ):
        """Test inequality condition."""
        context.risk_level = 'low'

        result = engine._eval_condition("risk_level != 'high'", context)

        assert result is True

    def test_eval_in_tuple(
        self, engine: WorkflowEngine, context: ExecutionContext
    ):
        """Test 'in' tuple condition."""
        context.risk_level = 'high'

        result = engine._eval_condition(
            "risk_level in ('high', 'critical')", context
        )

        assert result is True

    def test_eval_not_in_tuple(
        self, engine: WorkflowEngine, context: ExecutionContext
    ):
        """Test 'not in' tuple condition."""
        context.risk_level = 'low'

        result = engine._eval_condition(
            "risk_level not in ('high', 'critical')", context
        )

        assert result is True

    def test_eval_invalid_condition(
        self, engine: WorkflowEngine, context: ExecutionContext
    ):
        """Test that invalid conditions return False."""
        result = engine._eval_condition('invalid >> syntax', context)

        assert result is False

    def test_eval_boolean_value(
        self, engine: WorkflowEngine, context: ExecutionContext
    ):
        """Test parsing boolean values."""
        # Create a condition that would parse True
        result = engine._parse_value('True')
        assert result is True

        result = engine._parse_value('false')
        assert result is False

    def test_eval_numeric_value(
        self, engine: WorkflowEngine, context: ExecutionContext
    ):
        """Test parsing numeric values."""
        result = engine._parse_value('42')
        assert result == 42

        result = engine._parse_value('3.14')
        assert result == 3.14


class TestPhaseExecution:
    """Tests for phase execution logic."""

    @pytest.fixture
    def engine_with_handler(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
    ) -> WorkflowEngine:
        """Create engine with custom handler."""
        config = Config(
            dry_run=True,
            mode=ExecutionMode.QUICK,
            phases=[
                PhaseConfig(name='custom_phase', agents=[]),
            ],
        )

        def custom_handler(ctx, phase):
            return PhaseResult(success=True, data={'handled': True})

        engine = WorkflowEngine(
            config=config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
            handlers={'custom_phase': custom_handler},
        )

        return engine

    def test_custom_handler_called(self, engine_with_handler: WorkflowEngine):
        """Test that custom handlers are invoked."""
        result = engine_with_handler.run(resume=False)

        assert result is True


class TestPhaseSkipping:
    """Tests for phase skip conditions."""

    def test_phase_with_skip_condition(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
    ):
        """Test phase is skipped when condition is true."""
        config = Config(
            dry_run=True,
            mode=ExecutionMode.QUICK,
            phases=[
                PhaseConfig(
                    name='phase1',
                    agents=[],
                    skip_condition='is_new_project',
                ),
                PhaseConfig(name='phase2', agents=[]),
            ],
        )

        engine = WorkflowEngine(
            config=config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
        )

        # Start fresh
        state = State()
        state.is_new_project = True
        engine.state_manager.save(state)

        result = engine.run(resume=True)

        # Workflow should succeed
        assert result is True

        # Verify we reached phase2 (meaning phase1 was skipped)
        state = engine.state_manager.load()
        # Phase2 should be the last phase we processed
        assert state.current_phase == 'phase2'
        # Workflow should be marked complete
        assert state.phase_status == PhaseStatus.COMPLETE


class TestCallbacks:
    """Tests for workflow callbacks."""

    def test_on_phase_complete_callback(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
    ):
        """Test on_phase_complete callback is called."""
        config = Config(
            dry_run=True,
            mode=ExecutionMode.QUICK,
            phases=[
                PhaseConfig(name='phase1', agents=[]),
            ],
        )

        engine = WorkflowEngine(
            config=config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
        )

        callback = MagicMock()
        engine.on_phase_complete = callback

        engine.run(resume=False)

        callback.assert_called_once()
        phase_name, phase_result = callback.call_args[0]
        assert phase_name == 'phase1'
        assert isinstance(phase_result, PhaseResult)

    def test_on_status_change_callback(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
    ):
        """Test on_status_change callback is called."""
        config = Config(
            dry_run=True,
            mode=ExecutionMode.QUICK,
            phases=[
                PhaseConfig(name='phase1', agents=[]),
            ],
        )

        engine = WorkflowEngine(
            config=config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
        )

        callback = MagicMock()
        engine.on_status_change = callback

        engine.run(resume=False)

        # Should be called for Starting and Complete
        assert callback.call_count >= 2


class TestParseValue:
    """Tests for _parse_value helper."""

    @pytest.fixture
    def engine(
        self,
        temp_work_dir: Path,
        temp_spec_path: Path,
        basic_config: Config,
    ) -> WorkflowEngine:
        """Create engine for testing."""
        return WorkflowEngine(
            config=basic_config,
            work_dir=temp_work_dir,
            spec_path=temp_spec_path,
        )

    def test_parse_single_quoted_string(self, engine: WorkflowEngine):
        """Test parsing single-quoted strings."""
        result = engine._parse_value("'hello'")
        assert result == 'hello'

    def test_parse_double_quoted_string(self, engine: WorkflowEngine):
        """Test parsing double-quoted strings."""
        result = engine._parse_value('"world"')
        assert result == 'world'

    def test_parse_true(self, engine: WorkflowEngine):
        """Test parsing True."""
        assert engine._parse_value('True') is True
        assert engine._parse_value('true') is True

    def test_parse_false(self, engine: WorkflowEngine):
        """Test parsing False."""
        assert engine._parse_value('False') is False
        assert engine._parse_value('false') is False

    def test_parse_none(self, engine: WorkflowEngine):
        """Test parsing None."""
        assert engine._parse_value('None') is None
        assert engine._parse_value('none') is None

    def test_parse_integer(self, engine: WorkflowEngine):
        """Test parsing integers."""
        assert engine._parse_value('42') == 42
        assert engine._parse_value('-5') == -5

    def test_parse_float(self, engine: WorkflowEngine):
        """Test parsing floats."""
        assert engine._parse_value('3.14') == 3.14
        assert engine._parse_value('-2.5') == -2.5

    def test_parse_unrecognized(self, engine: WorkflowEngine):
        """Test parsing unrecognized values."""
        result = engine._parse_value('something_else')
        assert result == 'something_else'
