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

from cc_orchestrations.core.config import Config, PhaseConfig
from cc_orchestrations.core.manifest import ComponentDef, Manifest
from cc_orchestrations.core.state import (
    ComponentState,
    ComponentStatus,
)
from cc_orchestrations.core.workspace import Workspace
from cc_orchestrations.workflow import (
    ComponentLoop,
    ExecutionContext,
    PhaseResult,
    ValidationLoop,
    WorkflowEngine,
    run_voting_gate,
)

from .config import CONDUCT_CONFIG

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

    # Run spec parser with explicit JSON schema
    # Pass absolute path so agent can read the file
    spec_abs_path = ctx.spec_path.resolve()
    result = ctx.runner.run(
        'spec_parser',
        f"""Read and parse the specification file at: {spec_abs_path}

Look for sections like:
- "Files to Create/Modify"
- "Components" table
- "Implementation Phases" with file references

Return JSON in this EXACT format:
{{
    "components": [
        {{
            "file": "path/to/file.py",
            "purpose": "what this file does",
            "depends_on": ["path/to/other.py"],
            "complexity": "low|medium|high"
        }}
    ]
}}

The "components" array must contain at least one item.
Extract file paths from the spec - look for code blocks, tables, and headers.
""",
        context={'spec_path': str(spec_abs_path)},
    )

    if not result.success:
        LOG.error(f'Spec parser failed: {result.error}')
        raw = result.raw_output[:500] if result.raw_output else 'None'
        LOG.error(f'Raw output: {raw}')
        return PhaseResult(
            success=False, error=f'Spec parsing failed: {result.error}'
        )

    if result.status == 'error':
        return PhaseResult(
            success=False, error=result.get('error', 'Unknown parse error')
        )

    # Try to extract components from various possible keys
    components = (
        result.get('components', [])
        or result.get('files', [])
        or result.get('modified_files', [])
        or result.get('items', [])
    )

    # Log what we got for debugging
    data_keys = list(result.data.keys()) if result.data else 'None'
    LOG.debug(f'Spec parser data keys: {data_keys}')
    raw_preview = result.raw_output[:300] if result.raw_output else 'None'
    LOG.debug(f'Spec parser raw output preview: {raw_preview}')

    if not components:
        keys = list(result.data.keys()) if result.data else 'None'
        return PhaseResult(
            success=False,
            error=f'No components found in spec. Parser returned keys: {keys}',
        )

    # Topological sort (simple - assumes deps are already in order)
    # In production, would do proper topo sort with cycle detection
    ctx.components = components

    # Extract file paths - handle different key names from spec parser
    def get_file_path(comp: dict) -> str:
        return comp.get('file') or comp.get('path') or comp.get('name', 'unknown')

    ctx.state.component_order = [get_file_path(c) for c in components]

    # Initialize component states
    for comp in components:
        file_path = get_file_path(comp)
        ctx.state.components[file_path] = ComponentState(
            file=file_path,
            depends_on=comp.get('depends_on', []),
            purpose=comp.get('purpose', ''),
            complexity=comp.get('complexity', 'medium'),
        )

    ctx.state_manager.save(ctx.state)
    ctx.log_status('parse_spec', f'Found {len(components)} components')

    # Initialize workspace if enabled (PULL model for context)
    if ctx.config.use_workspace:
        ctx.log_status('parse_spec', 'Initializing workspace')

        # Build Manifest from parsed components
        manifest = Manifest(
            name=ctx.spec_path.stem,
            project=ctx.work_dir.name,
            work_dir=str(ctx.work_dir),
            spec_dir=str(ctx.spec_path.parent),
            components=[
                ComponentDef(
                    id=Path(get_file_path(c)).stem.replace('-', '_').replace('.', '_'),
                    file=get_file_path(c),
                    purpose=c.get('purpose', ''),
                    depends_on=c.get('depends_on', []),
                    complexity=c.get('complexity', 'medium'),
                )
                for c in components
            ],
        )

        # Read spec content for parsing into sections
        spec_content = ctx.spec_path.read_text()

        # Initialize workspace
        ctx.workspace = Workspace(ctx.work_dir)
        ctx.workspace.initialize(manifest, spec_content)

        ctx.log_status('parse_spec', 'Workspace initialized')

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
            f'High impact ({transitive_deps} deps) - triggering vote (using thinking model)',
        )

        # High-impact architectural decisions benefit from thinking model
        from cc_orchestrations.core.config import DEFAULT_COUNCIL_MODELS
        voter_models = DEFAULT_COUNCIL_MODELS[:3]  # thinking + opus + gpt-5.1-high

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
            voter_models=voter_models,
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
                    error=f'{component} has incomplete deps: {incomplete_deps}',
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
    """Production readiness gate - voting for high+ risk.

    Uses opus-thinking for the lead voter to ensure deep reasoning
    on the ship/don't-ship decision.
    """
    # Only for high/critical risk
    if ctx.risk_level not in ('high', 'critical'):
        ctx.log_status(
            'production_gate', 'Skipping - risk level below threshold'
        )
        return PhaseResult(success=True)

    ctx.log_status('production_gate', 'Running production readiness vote (using thinking model)')

    # Critical decision: use thinking model for lead voter, diverse council for others
    # This ensures deep reasoning on the most important gate
    from cc_orchestrations.core.config import DEFAULT_COUNCIL_MODELS
    voter_models = DEFAULT_COUNCIL_MODELS[:3]  # thinking + opus + gpt-5.1-high

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
        voter_models=voter_models,
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

    fail_count = len(failures)
    return PhaseResult(
        success=False,
        error=f'Failed to fix tests after {max_attempts} attempts. {fail_count} remaining',
    )


# =============================================================================
# PHASE HANDLERS REGISTRY
# =============================================================================

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
    draft_mode: bool = False,
) -> WorkflowEngine:
    """Create a conduct workflow engine.

    Args:
        work_dir: Working directory for the project
        spec_path: Path to SPEC.md (defaults to work_dir/.spec/SPEC.md)
        config_override: Override default config. If provided, uses this config
                        and adds phases/voting_gates from CONDUCT_CONFIG if missing.
        draft_mode: If True, running in Composer-only mode for spec validation.
                   Forces all models to 'composer-1'. Commits will be prefixed [DRAFT].

    Returns:
        Configured WorkflowEngine
    """
    from .config import create_default_config

    if spec_path is None:
        spec_path = work_dir / '.spec' / 'SPEC.md'

    # Create a fresh config - never mutate the CONDUCT_CONFIG singleton
    if config_override is not None:
        # Use the provided config, but ensure phases/voting_gates/agents are present
        config = config_override
        # Add phases from default if not present
        if not config.phases:
            config.phases = CONDUCT_CONFIG.phases.copy()
        if not config.voting_gates:
            config.voting_gates = CONDUCT_CONFIG.voting_gates.copy()
        # CRITICAL: Merge agents from CONDUCT_CONFIG (needed for model overrides)
        # Only add agents that don't already exist in config
        for agent_name, agent_config in CONDUCT_CONFIG.agents.items():
            if agent_name not in config.agents:
                # Copy agent config to avoid mutating CONDUCT_CONFIG
                from dataclasses import replace
                config.agents[agent_name] = replace(agent_config)
    else:
        # Create fresh default config
        config = create_default_config()

    # DRAFT MODE: Force all agent models to composer-1 for cheap validation
    # Use force_model which overrides even explicit model_override in phases
    if draft_mode:
        LOG.info('Draft mode: forcing all agent models to composer-1')
        config.force_model = 'composer-1'

    return WorkflowEngine(
        config=config,
        work_dir=work_dir,
        spec_path=spec_path,
        handlers=CONDUCT_HANDLERS,
        draft_mode=draft_mode,
    )
