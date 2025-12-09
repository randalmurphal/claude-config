"""Workflow execution engine.

The engine drives the workflow through phases, managing state transitions,
agent execution, and validation loops.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from cc_orchestrations.core.config import Config, PhaseConfig
from cc_orchestrations.core.git import git_commit
from cc_orchestrations.core.runner import AgentRunner
from cc_orchestrations.core.state import (
    ComponentState,
    ComponentStatus,
    Issue,
    PhaseStatus,
    State,
    StateManager,
)
from cc_orchestrations.core.workspace import Workspace

from .loops import LoopResult, ValidationLoop

LOG = logging.getLogger(__name__)


class PhaseHandler(Protocol):
    """Protocol for phase handlers."""

    def __call__(
        self,
        ctx: 'ExecutionContext',
        phase: PhaseConfig,
    ) -> 'PhaseResult': ...


@dataclass
class PhaseResult:
    """Result of a phase execution."""

    success: bool
    next_phase: str = ''  # Override automatic progression
    skip_to: str = ''  # Skip ahead to this phase
    error: str = ''
    needs_user_input: bool = False
    user_prompt: str = ''
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Context passed to phase handlers."""

    config: Config
    state: State
    state_manager: StateManager
    runner: AgentRunner
    work_dir: Path
    spec_path: Path
    handlers: dict[str, PhaseHandler] = field(default_factory=dict)

    # Runtime data
    components: list[dict[str, Any]] = field(default_factory=list)
    current_component: str = ''
    risk_level: str = 'medium'
    draft_mode: bool = False  # True if running in draft mode (Composer)

    # Workspace for context management (PULL model)
    workspace: Workspace | None = None

    # Callbacks
    on_status_change: Callable[[str, str], None] | None = None
    on_user_prompt: Callable[[str], str] | None = None

    # Commit tracking
    commits: list[str] = field(default_factory=list)  # Commit hashes created

    def commit_phase(
        self, phase: str, component: str | None = None
    ) -> str | None:
        """Create a commit after a phase completes.

        Args:
            phase: Phase name (skeleton, implementation, validation)
            component: Component name if applicable

        Returns:
            Commit hash if created, None if no changes
        """
        commit_hash = git_commit(
            work_dir=self.work_dir,
            phase=phase,
            component=component,
            draft_mode=self.draft_mode,
        )
        if commit_hash:
            self.commits.append(commit_hash)
            LOG.info(f'Committed {phase}: {commit_hash}')
        return commit_hash

    @property
    def mode_config(self) -> Any:
        """Get mode config from config."""
        return self.config.mode_config

    @property
    def dry_run(self) -> bool:
        """Check if running in dry-run mode."""
        return self.config.dry_run

    @property
    def parallelization(self) -> str:
        """Get parallelization strategy from mode config."""
        return (
            self.mode_config.parallelization if self.mode_config else 'by_level'
        )

    def log_status(self, phase: str, status: str) -> None:
        """Log and callback status change."""
        LOG.info(f'[{phase}] {status}')
        if self.on_status_change:
            self.on_status_change(phase, status)

    def ask_user(self, prompt: str) -> str:
        """Ask user for input.

        Raises:
            RuntimeError: If running non-interactively and no callback set
        """
        if self.on_user_prompt:
            return self.on_user_prompt(prompt)
        # Fallback to stdin
        print(prompt)
        try:
            return input('> ').strip()
        except EOFError:
            # Non-interactive mode - can't prompt user
            raise RuntimeError(
                f'User input required but running non-interactively. '
                f'Prompt was: {prompt[:200]}...'
            ) from None

    def get_completed_components(self) -> list[str]:
        """Get list of completed component files."""
        return self.state.get_completed_components()

    def get_component_context(self, component: str) -> dict[str, Any]:
        """Build context for a component operation.

        If workspace is available, includes workspace context for the component.
        Otherwise falls back to state-based context.
        """
        comp_state = self.state.components.get(
            component, ComponentState(file=component)
        )

        base_context = {
            'component': component,
            'purpose': comp_state.purpose,
            'depends_on': comp_state.depends_on,
            'completed_deps': [
                d
                for d in comp_state.depends_on
                if d in self.get_completed_components()
            ],
            'work_dir': str(self.work_dir),
            'spec_path': str(self.spec_path),
        }

        # Add workspace context if available
        if self.workspace and self.workspace.is_initialized:
            # Get component ID from file path (use stem or sanitized name)
            component_id = (
                Path(component).stem.replace('-', '_').replace('.', '_')
            )
            base_context['workspace_context'] = (
                self.workspace.get_component_context(component_id)
            )

        return base_context


class WorkflowEngine:
    """Executes a workflow through its phases."""

    def __init__(
        self,
        config: Config,
        work_dir: Path,
        spec_path: Path,
        handlers: dict[str, PhaseHandler] | None = None,
        draft_mode: bool = False,
    ):
        self.config = config
        self.work_dir = work_dir
        self.spec_path = spec_path
        self.draft_mode = draft_mode  # Composer-only run for spec validation

        # Initialize state
        state_dir = work_dir / config.state_dir
        self.state_manager = StateManager(state_dir)
        self.state_manager.ensure_dirs()

        # Initialize runner with dry_run from config
        self.runner = AgentRunner(config, work_dir, dry_run=config.dry_run)

        # Phase handlers
        self.handlers = handlers or {}

        # Mode config (ensure it's set)
        if config.mode_config is None:
            config.__post_init__()  # This sets mode_config from mode

        # Callbacks
        self.on_status_change: Callable[[str, str], None] | None = None
        self.on_user_prompt: Callable[[str], str] | None = None
        self.on_phase_complete: Callable[[str, PhaseResult], None] | None = None

    def run(self, resume: bool = True) -> bool:
        """Run the workflow from current state.

        Args:
            resume: If True, resume from saved state. If False, start fresh.

        Returns:
            True if workflow completed successfully
        """
        # Load or initialize state
        if resume:
            state = self.state_manager.load()
        else:
            state = State()
            state.spec_path = str(self.spec_path)
            state.work_dir = str(self.work_dir)
            state.mode = self.config.mode.value
            state.dry_run = self.config.dry_run
            self.state_manager.save(state)

        # Build execution context
        ctx = ExecutionContext(
            config=self.config,
            state=state,
            state_manager=self.state_manager,
            runner=self.runner,
            work_dir=self.work_dir,
            spec_path=self.spec_path,
            handlers=self.handlers,
            on_status_change=self.on_status_change,
            on_user_prompt=self.on_user_prompt,
            draft_mode=self.draft_mode,
        )

        # Find starting phase
        current_phase = state.current_phase
        if current_phase == 'complete':
            LOG.info('Workflow already complete')
            return True

        # Get phase list
        phases = self.config.phases
        if not phases:
            LOG.error('No phases defined in config')
            return False

        # Find starting index
        phase_names = [p.name for p in phases]
        try:
            start_idx = phase_names.index(current_phase)
        except ValueError:
            start_idx = 0

        # Execute phases
        for i in range(start_idx, len(phases)):
            phase = phases[i]

            # Check skip condition
            if phase.skip_condition and self._eval_condition(
                phase.skip_condition, ctx
            ):
                LOG.info(f'Skipping phase {phase.name}: {phase.skip_condition}')
                self.state_manager.update_phase(phase.name, PhaseStatus.SKIPPED)
                continue

            # Execute phase
            ctx.log_status(phase.name, 'Starting')
            self.state_manager.update_phase(phase.name, PhaseStatus.IN_PROGRESS)

            try:
                result = self._execute_phase(ctx, phase)
            except Exception as e:
                LOG.error(f'Phase {phase.name} failed with exception: {e}')
                self.state_manager.set_error(str(e))
                return False

            if self.on_phase_complete:
                self.on_phase_complete(phase.name, result)

            if not result.success:
                if result.needs_user_input:
                    # Get user input and retry
                    user_response = ctx.ask_user(result.user_prompt)
                    ctx.state.discoveries.append(
                        f'User decision on {phase.name}: {user_response}'
                    )
                    self.state_manager.save(ctx.state)
                    # For now, don't retry - let user re-run
                    LOG.info(f'User input received: {user_response}')

                LOG.error(f'Phase {phase.name} failed: {result.error}')
                self.state_manager.update_phase(phase.name, PhaseStatus.BLOCKED)
                self.state_manager.set_error(result.error)
                return False

            # Phase succeeded
            self.state_manager.update_phase(phase.name, PhaseStatus.COMPLETE)
            ctx.log_status(phase.name, 'Complete')

            # Handle next phase override
            if result.skip_to:
                try:
                    skip_idx = phase_names.index(result.skip_to)
                    if skip_idx > i:
                        LOG.info(f'Skipping to phase {result.skip_to}')
                        i = skip_idx - 1  # Will be incremented by loop
                except ValueError:
                    LOG.warning(f'Skip target {result.skip_to} not found')

            elif (
                result.next_phase and result.next_phase != phases[i + 1].name
                if i + 1 < len(phases)
                else ''
            ):
                try:
                    _ = phase_names.index(
                        result.next_phase
                    )  # Validate phase exists
                    LOG.info(f'Jumping to phase {result.next_phase}')
                except ValueError:
                    LOG.warning(f'Next phase {result.next_phase} not found')

        # All phases complete
        self.state_manager.mark_complete()
        ctx.log_status('workflow', 'Complete')
        return True

    def _execute_phase(
        self,
        ctx: ExecutionContext,
        phase: PhaseConfig,
    ) -> PhaseResult:
        """Execute a single phase."""
        # Check for custom handler
        if phase.name in self.handlers:
            return self.handlers[phase.name](ctx, phase)

        # Default: run configured agents
        if not phase.agents:
            LOG.warning(f'Phase {phase.name} has no agents configured')
            return PhaseResult(success=True)

        if phase.parallel:
            return self._run_parallel_agents(ctx, phase)
        return self._run_sequential_agents(ctx, phase)

    def _run_parallel_agents(
        self,
        ctx: ExecutionContext,
        phase: PhaseConfig,
    ) -> PhaseResult:
        """Run phase agents in parallel."""
        component = ctx.current_component or 'all'
        context = (
            ctx.get_component_context(component)
            if ctx.current_component
            else {}
        )

        tasks: list[tuple[str, str, dict[str, Any] | None]] = [
            (agent, f'Execute {phase.name} for {component}', context)
            for agent in phase.agents
        ]

        results = ctx.runner.run_parallel(tasks)

        # Check results
        failures = [r for r in results if not r.success]
        if failures:
            errors = '; '.join(f.error for f in failures)
            return PhaseResult(success=False, error=f'Agents failed: {errors}')

        return PhaseResult(success=True)

    def _run_sequential_agents(
        self,
        ctx: ExecutionContext,
        phase: PhaseConfig,
    ) -> PhaseResult:
        """Run phase agents sequentially."""
        component = ctx.current_component or 'all'
        context = (
            ctx.get_component_context(component)
            if ctx.current_component
            else {}
        )

        for agent in phase.agents:
            result = ctx.runner.run(
                agent,
                f'Execute {phase.name} for {component}',
                context=context,
            )

            if not result.success:
                return PhaseResult(
                    success=False, error=f'Agent {agent} failed: {result.error}'
                )

        return PhaseResult(success=True)

    def _eval_condition(self, condition: str, ctx: ExecutionContext) -> bool:
        """Safely evaluate a condition string WITHOUT using eval().

        Supports these patterns:
        - Simple boolean: 'is_new_project'
        - Equality: "risk_level == 'high'"
        - Inequality: "risk_level != 'low'"
        - Membership: "risk_level in ('high', 'critical')"
        - Negated membership: "risk_level not in ('high', 'critical')"

        Returns False for any unparseable condition (fail safe).
        """
        # Build namespace
        namespace = {
            'state': ctx.state,
            'components': ctx.components,
            'risk_level': ctx.risk_level,
            'is_new_project': ctx.state.is_new_project,
            'transitive_deps': getattr(ctx.state, 'transitive_deps', 0),
        }

        try:
            return self._safe_evaluate(condition.strip(), namespace)
        except Exception as e:
            LOG.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    def _safe_evaluate(self, condition: str, namespace: dict[str, Any]) -> bool:
        """Parse and evaluate a condition safely."""
        import re

        # Pattern: field not in ('a', 'b', ...)
        match = re.match(
            r'(\w+)\s+not\s+in\s+\(([^)]+)\)',
            condition,
        )
        if match:
            field, values_str = match.groups()
            values = self._parse_tuple(values_str)
            return namespace.get(field) not in values

        # Pattern: field in ('a', 'b', ...)
        match = re.match(r'(\w+)\s+in\s+\(([^)]+)\)', condition)
        if match:
            field, values_str = match.groups()
            values = self._parse_tuple(values_str)
            return namespace.get(field) in values

        # Pattern: field == 'value' or field == value
        match = re.match(r'(\w+)\s*==\s*(.+)', condition)
        if match:
            field, value_str = match.groups()
            value = self._parse_value(value_str.strip())
            return namespace.get(field) == value

        # Pattern: field != 'value' or field != value
        match = re.match(r'(\w+)\s*!=\s*(.+)', condition)
        if match:
            field, value_str = match.groups()
            value = self._parse_value(value_str.strip())
            return namespace.get(field) != value

        # Pattern: simple field (truthy check)
        if re.match(r'^\w+$', condition):
            return bool(namespace.get(condition))

        LOG.warning(f"Unsupported condition pattern: '{condition}'")
        return False

    def _parse_tuple(self, values_str: str) -> tuple[Any, ...]:
        """Parse comma-separated values from a tuple string."""
        values = []
        for v in values_str.split(','):
            values.append(self._parse_value(v.strip()))
        return tuple(values)

    def _parse_value(self, value_str: str) -> Any:
        """Parse a single value from string."""
        # String literal (single or double quotes)
        if (value_str.startswith("'") and value_str.endswith("'")) or (
            value_str.startswith('"') and value_str.endswith('"')
        ):
            return value_str[1:-1]
        # Boolean
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        # None
        if value_str.lower() == 'none':
            return None
        # Number
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass
        # Return as-is (field reference would need more work)
        return value_str


class ComponentLoop:
    """Handles the per-component execution loop."""

    # Risk levels that trigger Opus for implementation
    HIGH_RISK_LEVELS = ('high', 'critical')

    def __init__(
        self,
        ctx: ExecutionContext,
        validation_config: dict[str, Any] | None = None,
    ):
        self.ctx = ctx
        self.validation_loop = ValidationLoop(
            runner=ctx.runner,
            max_attempts=validation_config.get('max_attempts', 3)
            if validation_config
            else 3,
            reviewers=validation_config.get('reviewers', 2)
            if validation_config
            else 2,
            same_issue_threshold=validation_config.get(
                'same_issue_threshold', 2
            )
            if validation_config
            else 2,
        )

    def _should_use_opus(self, component: str) -> bool:
        """Determine if Opus should be used for this component.

        Uses Opus when:
        - Overall risk level is high/critical (blast radius)
        - Component complexity is 'high'
        - Component touches shared utilities (common/, helpers/, utils/)

        Args:
            component: Component file path

        Returns:
            True if Opus should be used for implementation
        """
        # Check overall risk level (blast radius)
        if self.ctx.risk_level in self.HIGH_RISK_LEVELS:
            return True

        # Check component-specific complexity
        comp_state = self.ctx.state.components.get(
            component, ComponentState(file=component)
        )
        if comp_state.complexity == 'high':
            return True

        # Check for shared utility paths
        shared_patterns = ('common/', 'helpers/', 'utils/', 'shared/', 'lib/')
        if any(pattern in component.lower() for pattern in shared_patterns):
            return True

        return False

    def run_component(self, component: str) -> PhaseResult:
        """Run full component pipeline: skeleton -> implement -> validate.

        Commits are created after each coding phase for reviewable timeline.

        Args:
            component: Component file path

        Returns:
            PhaseResult
        """
        self.ctx.current_component = component
        self.ctx.state_manager.update_component(
            component, status=ComponentStatus.SKELETON
        )

        # Phase 1: Skeleton
        self.ctx.log_status(component, 'Building skeleton')
        skeleton_result = self._run_skeleton(component)
        if not skeleton_result.success:
            return skeleton_result

        # Commit skeleton
        self.ctx.commit_phase('skeleton', component)

        self.ctx.state_manager.update_component(
            component, status=ComponentStatus.IMPLEMENTING
        )

        # Phase 2: Implementation
        self.ctx.log_status(component, 'Implementing')
        impl_result = self._run_implementation(component)
        if not impl_result.success:
            return impl_result

        # Commit implementation
        self.ctx.commit_phase('implementation', component)

        self.ctx.state_manager.update_component(
            component, status=ComponentStatus.VALIDATING
        )

        # Phase 3: Validation loop
        self.ctx.log_status(component, 'Validating')
        validation_result = self._run_validation(component)

        if validation_result.passed:
            # Commit any validation fixes
            self.ctx.commit_phase('validation', component)

            self.ctx.state_manager.update_component(
                component, status=ComponentStatus.COMPLETE
            )
            self.ctx.log_status(component, 'Complete')
            return PhaseResult(success=True)

        if validation_result.escalated:
            # Commit partial progress even on escalation
            self.ctx.commit_phase('validation-blocked', component)

            self.ctx.state_manager.update_component(
                component,
                status=ComponentStatus.BLOCKED,
                error=validation_result.escalation_reason,
            )
            return PhaseResult(
                success=False,
                error=validation_result.escalation_reason,
                needs_user_input=validation_result.voting_outcome.needs_user_decision
                if validation_result.voting_outcome
                else False,
                user_prompt=validation_result.voting_outcome.user_prompt
                if validation_result.voting_outcome
                else '',
            )

        return PhaseResult(success=False, error='Validation failed')

    def _run_skeleton(self, component: str) -> PhaseResult:
        """Build skeleton for component."""
        context = self.ctx.get_component_context(component)
        # Get component ID for workspace context
        component_id = Path(component).stem.replace('-', '_').replace('.', '_')

        # Use Opus for high-risk/high-complexity components
        model_override = 'opus' if self._should_use_opus(component) else None
        if model_override:
            self.ctx.log_status(
                component,
                f'Using {model_override} for skeleton (high risk/complexity)',
            )

        result = self.ctx.runner.run(
            'skeleton_builder',
            f'Create skeleton for {component}',
            context=context,
            component_id=component_id,
            workspace=self.ctx.workspace,
            model_override=model_override,
        )

        if not result.success:
            return PhaseResult(
                success=False, error=f'Skeleton failed: {result.error}'
            )

        if result.status == 'blocked':
            return PhaseResult(
                success=False,
                error=f'Skeleton blocked: {result.get("blockers", [])}',
            )

        return PhaseResult(success=True)

    def _run_implementation(self, component: str) -> PhaseResult:
        """Implement component."""
        context = self.ctx.get_component_context(component)
        # Get component ID for workspace context
        component_id = Path(component).stem.replace('-', '_').replace('.', '_')

        # Use Opus for high-risk/high-complexity components
        model_override = 'opus' if self._should_use_opus(component) else None
        if model_override:
            self.ctx.log_status(
                component,
                f'Using {model_override} for implementation (high risk/complexity)',
            )

        result = self.ctx.runner.run(
            'implementation_executor',
            f'Implement {component}',
            context=context,
            component_id=component_id,
            workspace=self.ctx.workspace,
            model_override=model_override,
        )

        if not result.success:
            return PhaseResult(
                success=False, error=f'Implementation failed: {result.error}'
            )

        if result.status == 'blocked':
            return PhaseResult(
                success=False,
                error=f'Implementation blocked: {result.get("blockers", [])}',
            )

        # Record discoveries
        if result.get('discoveries'):
            for discovery in result.get('discoveries', []):
                self.ctx.state_manager.add_discovery(discovery)

        return PhaseResult(success=True)

    def _run_validation(self, component: str) -> LoopResult:
        """Run validation loop for component."""
        context = self.ctx.get_component_context(component)

        # Determine reviewers based on risk
        risk = self.ctx.risk_level
        num_reviewers = self.ctx.config.get_reviewers_for_risk(risk)

        # Build validator list
        validators = ['validator'] * num_reviewers

        # Add security auditor for public-facing components
        comp_state = self.ctx.state.components.get(
            component, ComponentState(file=component)
        )
        if any(
            kw in comp_state.purpose.lower()
            for kw in ['api', 'endpoint', 'public', 'auth']
        ):
            validators.append('security_auditor')

        def on_issues(issues: list[Issue]) -> None:
            self.ctx.state_manager.update_component(
                component,
                issues=issues,
                previous_issues=self.ctx.state.components.get(
                    component, ComponentState(file=component)
                ).issues,
            )

        return self.validation_loop.run(
            component=component,
            context=context,
            validator_agents=validators,
            on_issues_found=on_issues,
        )
