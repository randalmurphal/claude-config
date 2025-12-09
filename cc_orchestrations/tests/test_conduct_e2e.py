#!/usr/bin/env python3
"""End-to-end dry-run test for conduct workflow (LIVE TEST).

This test exercises the FULL workflow through all phases with REAL API calls:
1. Parse spec
2. Impact analysis (skipped for new project)
3. Component loop (skeleton -> implement -> validate per component)
4. Integration validation
5. Final validation
6. Production gate (skipped for non-high risk)
7. Completion

All agents run in dry-run mode (haiku with mock data), but REAL API calls are made.

This test is marked as live_cli and will be SKIPPED unless --live-cli is passed.

Usage:
    python -m pytest cc_orchestrations/tests/test_conduct_e2e.py -v --live-cli
    python cc_orchestrations/tests/test_conduct_e2e.py
    python cc_orchestrations/tests/test_conduct_e2e.py -v
"""

import argparse
import logging
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import pytest

from cc_orchestrations.conduct import (
    create_conduct_workflow,
    create_default_config,
)
from cc_orchestrations.core.state import PhaseStatus

# Mark all tests in this module as live_cli (requires --live-cli flag to run)
pytestmark = [pytest.mark.live_cli, pytest.mark.slow]

LOG = logging.getLogger(__name__)


MOCK_SPEC = """# Feature: User Preferences API

## Summary
Add a new API endpoint for managing user preferences with persistence.

## Components

### fisio/fisio/api/preferences.py
- Purpose: API endpoint handlers for user preferences CRUD
- Depends on: None
- Complexity: medium

### fisio/fisio/models/preferences.py
- Purpose: Data models for preferences
- Depends on: None
- Complexity: low

### fisio/tests/test_preferences.py
- Purpose: Unit tests for preferences API
- Depends on: fisio/fisio/api/preferences.py, fisio/fisio/models/preferences.py
- Complexity: medium

## Quality Requirements
- All tests must pass
- Type hints on all functions
- Logging for all API calls
- Error handling for invalid input

## Success Criteria
- GET /preferences returns user preferences
- PUT /preferences updates preferences
- Validation for preference values
- Audit logging for changes
"""


def create_mock_project(work_dir: Path) -> Path:
    """Create a minimal mock project structure."""
    # Create spec
    spec_dir = work_dir / '.spec'
    spec_dir.mkdir(parents=True, exist_ok=True)

    spec_path = spec_dir / 'SPEC.md'
    spec_path.write_text(MOCK_SPEC)

    # Create minimal project structure
    (work_dir / 'fisio' / 'fisio' / 'api').mkdir(parents=True, exist_ok=True)
    (work_dir / 'fisio' / 'fisio' / 'models').mkdir(parents=True, exist_ok=True)
    (work_dir / 'fisio' / 'tests').mkdir(parents=True, exist_ok=True)

    # Create empty __init__.py files
    for path in [
        'fisio/__init__.py',
        'fisio/fisio/__init__.py',
        'fisio/fisio/api/__init__.py',
        'fisio/fisio/models/__init__.py',
        'fisio/tests/__init__.py',
    ]:
        (work_dir / path).touch()

    return spec_path


def test_e2e_dry_run(verbose: bool = False) -> None:
    """Run full workflow in dry-run mode.

    Validates the workflow completes successfully in dry-run mode.
    """
    print('\n' + '=' * 60)
    print('E2E Dry-Run Test: Conduct Workflow')
    print('=' * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        spec_path = create_mock_project(work_dir)

        print(f'\n📁 Work directory: {work_dir}')
        print(f'📋 Spec path: {spec_path}')

        # Create config with dry-run enabled
        config = create_default_config()
        config.dry_run = True

        # Mark as new project to skip impact analysis
        print('\n⚙️  Configuration:')
        print('   Mode: standard')
        print(f'   Dry-run: {config.dry_run}')
        print(f'   Phases: {len(config.phases)}')

        # Create workflow engine
        engine = create_conduct_workflow(
            work_dir=work_dir,
            spec_path=spec_path,
            config_override=config,
        )

        # Set up status callbacks
        phase_results = []

        def on_status_change(phase: str, status: str) -> None:
            phase_results.append((phase, status))
            if verbose:
                print(f'   [{phase}] {status}')

        def on_user_prompt(prompt: str) -> str:
            # Auto-respond in dry-run mode
            print(f'   [USER PROMPT] {prompt[:50]}...')
            return 'proceed'

        engine.on_status_change = on_status_change
        engine.on_user_prompt = on_user_prompt

        print('\n🚀 Starting workflow execution...\n')

        # Run workflow
        try:
            success = engine.run(resume=False)
        except Exception as e:
            print(f'\n❌ Workflow failed with exception: {e}')
            if verbose:
                import traceback

                traceback.print_exc()
            raise AssertionError(f'Workflow failed with exception: {e}') from e

        # Check results
        print('\n' + '-' * 40)
        print('Phase Execution Summary:')
        print('-' * 40)

        # Group by phase
        phases_seen = {}
        for phase, status in phase_results:
            if phase not in phases_seen:
                phases_seen[phase] = []
            phases_seen[phase].append(status)

        for phase, statuses in phases_seen.items():
            final_status = statuses[-1]
            emoji = (
                '✅'
                if 'Complete' in final_status
                else '⏭️'
                if 'Skip' in final_status
                else '❓'
            )
            print(f'  {emoji} {phase}: {final_status}')

        # Check state
        state = engine.state_manager.load()
        print('\n📊 Final State:')
        print(f'   Current phase: {state.current_phase}')
        print(f'   Phase status: {state.phase_status.value}')
        print(f'   Components: {len(state.components)}')
        print(f'   Discoveries: {len(state.discoveries)}')

        if state.error:
            print(f'   ⚠️  Error: {state.error}')

        # Result
        print('\n' + '=' * 60)
        if success:
            print('✅ E2E TEST PASSED - Workflow completed successfully')
        else:
            print('❌ E2E TEST FAILED - Workflow did not complete')
        print('=' * 60)

        assert success, 'Workflow should complete successfully in dry-run mode'


def test_e2e_with_resume(verbose: bool = False) -> None:
    """Test workflow resume capability.

    Creates a workflow, runs it partway, then verifies resume preserves state.
    """
    print('\n' + '=' * 60)
    print('E2E Dry-Run Test: Workflow Resume')
    print('=' * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        spec_path = create_mock_project(work_dir)

        # Create config
        config = create_default_config()
        config.dry_run = True

        # First run - will complete parse_spec phase
        engine1 = create_conduct_workflow(
            work_dir=work_dir,
            spec_path=spec_path,
            config_override=config,
        )

        print('\n🔄 First run: Starting workflow...')

        # Manually set state to simulate partial completion
        state = engine1.state_manager.load()
        state.current_phase = 'parse_spec'
        state.phase_status = PhaseStatus.COMPLETE
        state.is_new_project = True  # Skip impact analysis
        engine1.state_manager.save(state)

        # Update to next phase
        engine1.state_manager.update_phase(
            'impact_analysis', PhaseStatus.SKIPPED
        )
        engine1.state_manager.update_phase(
            'component_loop', PhaseStatus.IN_PROGRESS
        )

        print('   Simulated partial completion at component_loop phase')

        # Second run - resume
        engine2 = create_conduct_workflow(
            work_dir=work_dir,
            spec_path=spec_path,
            config_override=config,
        )

        print('\n🔄 Second run: Resuming workflow...')

        # Check state is preserved
        resumed_state = engine2.state_manager.load()
        print(f'   Resumed at phase: {resumed_state.current_phase}')

        phase_preserved = resumed_state.current_phase == 'component_loop'

        print('\n' + '=' * 60)
        if phase_preserved:
            print('✅ E2E RESUME TEST PASSED - State correctly preserved')
        else:
            print('❌ E2E RESUME TEST FAILED - State not preserved correctly')
        print('=' * 60)

        assert phase_preserved, 'Workflow state should be preserved on resume'


def _run_test(
    name: str, test_func: Callable[[bool], None], verbose: bool
) -> tuple[str, bool]:
    """Run a test function and catch assertions."""
    try:
        test_func(verbose)
        return (name, True)
    except AssertionError as e:
        print(f'\n❌ {name} failed: {e}')
        return (name, False)
    except Exception as e:
        print(f'\n❌ {name} error: {e}')
        return (name, False)


def main() -> int:
    """Run E2E tests."""
    parser = argparse.ArgumentParser(description='Conduct E2E Dry-Run Tests')
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Verbose output'
    )
    parser.add_argument(
        '--skip-full', action='store_true', help='Skip full workflow test'
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=level)

    results = []

    # Resume test (faster, always run)
    results.append(_run_test('Resume Test', test_e2e_with_resume, args.verbose))

    # Full workflow test (slower, can be skipped)
    if not args.skip_full:
        results.append(
            _run_test('Full Workflow', test_e2e_dry_run, args.verbose)
        )
    else:
        print('\n⏭️  Skipping full workflow test (--skip-full)')

    # Summary
    print('\n' + '=' * 60)
    print('E2E TEST SUMMARY')
    print('=' * 60)

    passed = 0
    for name, success in results:
        status = '✓ PASS' if success else '✗ FAIL'
        print(f'  {status}: {name}')
        if success:
            passed += 1

    print()
    print(f'  {passed}/{len(results)} tests passed')
    print()

    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
