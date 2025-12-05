"""Conduct workflow definition.

This defines the full orchestration workflow matching the original /conduct command:
1. Parse spec
2. Impact analysis (with voting if high impact)
3. Component loop: skeleton -> implement -> validate -> fix
4. Integration validation
5. Final validation (scaled by risk)
6. Production readiness gate
"""

import json
import logging
from pathlib import Path

from orchestrations.core import (
    REGISTRY,
    ComponentState,
    ComponentStatus,
    Config,
    PhaseConfig,
    RiskConfig,
    ValidationConfig,
    VotingGateConfig,
)
from orchestrations.workflow import (
    ComponentLoop,
    ExecutionContext,
    PhaseResult,
    ValidationLoop,
    WorkflowEngine,
    run_voting_gate,
)


LOG = logging.getLogger(__name__)


# =============================================================================
# PHASE HANDLERS
# =============================================================================


def phase_parse_spec(ctx: ExecutionContext, phase: PhaseConfig) -> PhaseResult:
    """Parse SPEC.md and extract components with dependencies."""
    ctx.log_status('parse_spec', 'Reading SPEC.md')

    # Check spec exists
    if not ctx.spec_path.exists():
        return PhaseResult(
            success=False,
            error=f'SPEC.md not found at {ctx.spec_path}. Run /spec first.',
        )

    # Run spec parser
    result = ctx.runner.run(
        'spec_parser',
        f"""Parse the specification file and extract:
1. All components/files to create or modify
2. Dependencies between components ("Depends on:" field)
3. Quality requirements
4. Success criteria

Spec file: {ctx.spec_path}

Return structured JSON with components in dependency order.
""",
        context={'spec_path': str(ctx.spec_path)},
    )

    if not result.success:
        return PhaseResult(
            success=False, error=f'Spec parsing failed: {result.error}'
        )

    if result.status == 'error':
        return PhaseResult(
            success=False, error=result.get('error', 'Unknown parse error')
        )

    # Store components
    components = result.get('components', [])
    if not components:
        return PhaseResult(success=False, error='No components found in spec')

    # Topological sort (simple - assumes deps are already in order)
    # In production, would do proper topo sort with cycle detection
    ctx.components = components
    ctx.state.component_order = [c['file'] for c in components]

    # Initialize component states
    for comp in components:
        ctx.state.components[comp['file']] = ComponentState(
            file=comp['file'],
            depends_on=comp.get('depends_on', []),
            purpose=comp.get('purpose', ''),
            complexity=comp.get('complexity', 'medium'),
        )

    ctx.state_manager.save(ctx.state)
    ctx.log_status('parse_spec', f'Found {len(components)} components')

    return PhaseResult(success=True, data={'components': components})


def phase_impact_analysis(
    ctx: ExecutionContext, phase: PhaseConfig
) -> PhaseResult:
    """Analyze blast radius of changes."""
    # Skip for new projects
    if ctx.state.is_new_project:
        ctx.log_status('impact_analysis', 'Skipping - new project')
        return PhaseResult(success=True, skip_to='component_loop')

    ctx.log_status('impact_analysis', 'Analyzing change impact')

    files_to_modify = [c['file'] for c in ctx.components]

    result = ctx.runner.run(
        'impact_analyzer',
        f"""Analyze the blast radius of modifying these files:
{files_to_modify}

For each file:
1. Find all files that import/depend on it (direct dependents)
2. Find transitive dependents (up to 3 levels)
3. Identify critical dependencies (many importers = high risk)

Return structured analysis with counts and recommendations.
""",
        context={
            'files': files_to_modify,
            'work_dir': str(ctx.work_dir),
        },
        model_override='opus',  # Use Opus for judgment
    )

    if not result.success:
        LOG.warning(f'Impact analysis failed: {result.error}')
        # Non-fatal - continue with medium risk assumption
        ctx.risk_level = 'medium'
        return PhaseResult(success=True)

    # Store results
    transitive_deps = result.get('transitive_dependents', 0)
    ctx.risk_level = result.get('risk_level', 'medium')
    ctx.state.risk_level = ctx.risk_level

    # Record discoveries
    if result.get('recommendations'):
        for rec in result.get('recommendations', []):
            ctx.state_manager.add_discovery(f'Impact: {rec}')

    # Check if voting needed
    impact_threshold = ctx.config.risk.impact_vote_threshold
    if transitive_deps > impact_threshold:
        ctx.log_status(
            'impact_analysis',
            f'High impact ({transitive_deps} deps) - triggering vote',
        )

        outcome = run_voting_gate(
            runner=ctx.runner,
            gate_name='impact_strategy',
            num_voters=3,
            prompt=f"""
Analyze the risk and vote on mitigation strategy.

Files to modify: {len(files_to_modify)}
Transitive dependents: {transitive_deps}
Risk level: {ctx.risk_level}

Critical dependencies:
{result.get('critical_dependencies', [])}

Strategies:
- BACKWARD_COMPATIBLE: Maintain full backward compatibility
- COORDINATED_ROLLOUT: Breaking changes with coordinated deployment
- INCREMENTAL_MIGRATION: Phase migration over multiple releases
- REDESIGN_NEEDED: Impact too high, needs architectural redesign

Vote for the best strategy given the risk profile.
""",
            options=[
                'BACKWARD_COMPATIBLE',
                'COORDINATED_ROLLOUT',
                'INCREMENTAL_MIGRATION',
                'REDESIGN_NEEDED',
            ],
            schema='impact_vote',
        )

        ctx.state_manager.add_vote_result(outcome.to_vote_result())

        if outcome.needs_user_decision:
            return PhaseResult(
                success=False,
                needs_user_input=True,
                user_prompt=outcome.user_prompt,
            )

        ctx.state_manager.add_discovery(f'Impact strategy: {outcome.winner}')

    ctx.state_manager.save(ctx.state)
    return PhaseResult(success=True)


def phase_component_loop(
    ctx: ExecutionContext, phase: PhaseConfig
) -> PhaseResult:
    """Execute each component: skeleton -> implement -> validate."""
    component_loop = ComponentLoop(
        ctx,
        validation_config={
            'max_attempts': ctx.config.validation.max_fix_attempts,
            'reviewers': ctx.config.validation.reviewers_per_validation,
            'same_issue_threshold': ctx.config.validation.same_issue_threshold,
        },
    )

    # Process components in dependency order
    for component in ctx.state.component_order:
        comp_state = ctx.state.components.get(component)

        # Skip if already complete
        if comp_state and comp_state.status == ComponentStatus.COMPLETE:
            ctx.log_status(component, 'Already complete, skipping')
            continue

        # Check dependencies are complete
        if comp_state:
            incomplete_deps = [
                d
                for d in comp_state.depends_on
                if ctx.state.components.get(d, ComponentState(file=d)).status
                != ComponentStatus.COMPLETE
            ]
            if incomplete_deps:
                return PhaseResult(
                    success=False,
                    error=f'Component {component} has incomplete dependencies: {incomplete_deps}',
                )

        # Run component
        result = component_loop.run_component(component)

        if not result.success:
            return result

    return PhaseResult(success=True)


def phase_integration_validation(
    ctx: ExecutionContext, phase: PhaseConfig
) -> PhaseResult:
    """Run integration validation across all components."""
    ctx.log_status('integration', 'Running integration tests')

    # Run test suite
    result = ctx.runner.run(
        'test_runner',
        """Run the full test suite and report results.

Run all tests, report:
- Total tests run
- Tests passed/failed
- Coverage if available
- Any failures with details
""",
        context={'work_dir': str(ctx.work_dir)},
    )

    if not result.success:
        return PhaseResult(
            success=False, error=f'Test run failed: {result.error}'
        )

    if result.status == 'fail':
        # Tests failed - enter fix loop
        failures = result.get('failures', [])
        ctx.log_status(
            'integration', f'{len(failures)} test failures - entering fix loop'
        )

        fix_loop_result = _run_test_fix_loop(ctx, failures)
        if not fix_loop_result.success:
            return fix_loop_result

    return PhaseResult(success=True)


def phase_final_validation(
    ctx: ExecutionContext, phase: PhaseConfig
) -> PhaseResult:
    """Run final validation scaled by risk."""
    ctx.log_status(
        'final_validation', f'Running final validation (risk: {ctx.risk_level})'
    )

    # Get reviewer count based on risk
    num_reviewers = ctx.config.get_reviewers_for_risk(ctx.risk_level)

    # Build validator list
    validators = ['validator'] * (
        num_reviewers - 2
    )  # Reserve slots for specialized
    validators.extend(['security_auditor', 'performance_reviewer'])

    # Run validation loop
    validation_loop = ValidationLoop(
        runner=ctx.runner,
        max_attempts=ctx.config.validation.max_fix_attempts,
        reviewers=num_reviewers,
    )

    all_files = list(ctx.state.components.keys())
    result = validation_loop.run(
        component='all_components',
        context={
            'files': all_files,
            'work_dir': str(ctx.work_dir),
            'scope': 'full_codebase',
        },
        validator_agents=validators,
    )

    if result.escalated:
        return PhaseResult(
            success=False,
            error=result.escalation_reason,
            needs_user_input=result.voting_outcome.needs_user_decision
            if result.voting_outcome
            else False,
            user_prompt=result.voting_outcome.user_prompt
            if result.voting_outcome
            else '',
        )

    return PhaseResult(success=True)


def phase_production_gate(
    ctx: ExecutionContext, phase: PhaseConfig
) -> PhaseResult:
    """Production readiness gate - voting for high+ risk."""
    # Only for high/critical risk
    if ctx.risk_level not in ('high', 'critical'):
        ctx.log_status(
            'production_gate', 'Skipping - risk level below threshold'
        )
        return PhaseResult(success=True)

    ctx.log_status('production_gate', 'Running production readiness vote')

    outcome = run_voting_gate(
        runner=ctx.runner,
        gate_name='production_ready',
        num_voters=3,
        prompt=f"""
Evaluate production readiness of the implementation.

Components implemented: {len(ctx.state.components)}
Risk level: {ctx.risk_level}
Validation status: All components passed validation

Review:
1. Are all requirements met?
2. Are there any blocking issues?
3. Is the code production-quality?

Vote:
- READY: Ship it
- NEEDS_WORK: Specific improvements needed
- RISKY: Concerns about production deployment
""",
        options=['READY', 'NEEDS_WORK', 'RISKY'],
        schema='production_ready_vote',
        voter_agent='investigator',
    )

    ctx.state_manager.add_vote_result(outcome.to_vote_result())

    if outcome.needs_user_decision:
        return PhaseResult(
            success=False,
            needs_user_input=True,
            user_prompt=outcome.user_prompt,
        )

    if outcome.winner != 'READY':
        concerns = []
        for vote in outcome.votes:
            concerns.extend(vote.get('concerns', []))

        return PhaseResult(
            success=False,
            error=f'Production gate failed: {outcome.winner}. Concerns: {concerns}',
        )

    return PhaseResult(success=True)


def phase_completion(ctx: ExecutionContext, phase: PhaseConfig) -> PhaseResult:
    """Finalize workflow - commit, archive, report."""
    ctx.log_status('completion', 'Finalizing')

    # Summary
    completed = len(
        [
            c
            for c in ctx.state.components.values()
            if c.status == ComponentStatus.COMPLETE
        ]
    )
    total = len(ctx.state.components)

    ctx.log_status('completion', f'Completed {completed}/{total} components')

    # Archive spec files (would move to .spec/archive/)
    # For now, just log

    return PhaseResult(
        success=True,
        data={
            'components_completed': completed,
            'components_total': total,
            'discoveries': ctx.state.discoveries,
            'votes': [v.to_dict() for v in ctx.state.voting_results],
        },
    )


def _run_test_fix_loop(
    ctx: ExecutionContext, failures: list[dict]
) -> PhaseResult:
    """Fix loop for test failures."""
    max_attempts = ctx.config.validation.max_fix_attempts

    for attempt in range(1, max_attempts + 1):
        ctx.log_status('integration', f'Fix attempt {attempt}/{max_attempts}')

        # Run fix executor
        result = ctx.runner.run(
            'fix_executor',
            f"""Fix the following test failures:

{json.dumps(failures, indent=2)}

Analyze each failure, fix the underlying issue, and ensure tests pass.
""",
            context={'failures': failures},
        )

        if not result.success:
            LOG.error(f'Fix executor failed: {result.error}')
            continue

        # Re-run tests
        test_result = ctx.runner.run(
            'test_runner',
            'Re-run all tests after fixes',
            context={'work_dir': str(ctx.work_dir)},
        )

        if test_result.status == 'pass':
            return PhaseResult(success=True)

        failures = test_result.get('failures', [])

    return PhaseResult(
        success=False,
        error=f'Failed to fix tests after {max_attempts} attempts. Remaining failures: {len(failures)}',
    )


# =============================================================================
# WORKFLOW CONFIGURATION
# =============================================================================

CONDUCT_CONFIG = Config(
    name='conduct',
    version='1.0.0',
    description='Full orchestration workflow for complex features',
    # Agents - use registry defaults
    agents=REGISTRY.to_configs(),
    # Phases
    phases=[
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
    ],
    # Voting gates
    voting_gates={
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
    },
    # Validation
    validation=ValidationConfig(
        max_fix_attempts=3,
        reviewers_per_validation=2,
        same_issue_threshold=2,
    ),
    # Risk scaling
    risk=RiskConfig(
        impact_vote_threshold=10,
        reviewers_by_risk={
            'low': 2,
            'medium': 4,
            'high': 6,
            'critical': 6,
        },
    ),
    # Paths - auto-detect relative to this module
    prompts_dir=str(Path(__file__).parent.parent / 'prompts'),
    state_dir='.spec',
    claude_path='claude',  # Assumes claude is in PATH; override in project config if needed
    default_model='sonnet',
)

# Phase handlers
CONDUCT_HANDLERS = {
    'parse_spec': phase_parse_spec,
    'impact_analysis': phase_impact_analysis,
    'component_loop': phase_component_loop,
    'integration_validation': phase_integration_validation,
    'final_validation': phase_final_validation,
    'production_gate': phase_production_gate,
    'completion': phase_completion,
}


def create_conduct_workflow(
    work_dir: Path,
    spec_path: Path | None = None,
    config_override: Config | None = None,
) -> WorkflowEngine:
    """Create a conduct workflow engine.

    Args:
        work_dir: Working directory for the project
        spec_path: Path to SPEC.md (defaults to work_dir/.spec/SPEC.md)
        config_override: Override default config

    Returns:
        Configured WorkflowEngine
    """
    if spec_path is None:
        spec_path = work_dir / '.spec' / 'SPEC.md'

    config = config_override or CONDUCT_CONFIG

    return WorkflowEngine(
        config=config,
        work_dir=work_dir,
        spec_path=spec_path,
        handlers=CONDUCT_HANDLERS,
    )

