#!/usr/bin/env python3
"""End-to-end test for PR review workflow with mock phases.

This exercises the FULL workflow flow with haiku agents in dry-run mode:
- Phase transitions
- Context passing between phases
- Checkpointing at each phase
- Finding aggregation
- Report generation

Usage:
    python -m pytest cc_orchestrations/tests/test_pr_review_e2e.py -v
    python cc_orchestrations/tests/test_pr_review_e2e.py
    python cc_orchestrations/tests/test_pr_review_e2e.py --verbose
"""

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path

from cc_orchestrations.core.config import Config
from cc_orchestrations.core.runner import AgentRunner
from cc_orchestrations.core.state import PhaseStatus, StateManager

LOG = logging.getLogger(__name__)


class MockPRReviewRunner:
    """Runs a mock PR review workflow for testing."""

    def __init__(
        self,
        work_dir: Path,
        dry_run: bool = True,
        verbose: bool = False,
    ):
        self.work_dir = work_dir
        self.dry_run = dry_run
        self.verbose = verbose

        # Setup
        self.state_dir = work_dir / '.pr-review-test'
        self.state_manager = StateManager(self.state_dir)

        # Create config
        claude_path = os.path.expanduser('~/.claude/local/claude')
        self.config = Config(
            name='test-pr-review-e2e',
            dry_run=dry_run,
            claude_path=claude_path,
            default_model='haiku',
        )

        # Create runner
        self.runner = AgentRunner(
            config=self.config,
            work_dir=work_dir,
            dry_run=dry_run,
        )

        # Mock context
        self.ticket_id = 'TEST-999'
        self.diff_files = [
            'src/api/endpoints.py',
            'src/services/processor.py',
            'tests/test_processor.py',
        ]

        # Results collected
        self.findings: list[dict] = []
        self.validated_findings: list[dict] = []
        self.risk_level = 'medium'

    def run(self) -> bool:
        """Run the full mock workflow."""
        print('=' * 60)
        print('Mock PR Review E2E Test')
        print('=' * 60)
        print()
        print(f'Ticket: {self.ticket_id}')
        print(f'Files: {len(self.diff_files)}')
        print(f'Dry-run: {self.dry_run}')
        print()

        try:
            # Phase 1: Triage
            if not self._phase_triage():
                return False

            # Phase 2: Investigation
            if not self._phase_investigation():
                return False

            # Phase 3: Validation
            if not self._phase_validation():
                return False

            # Phase 4: Synthesis
            if not self._phase_synthesis():
                return False

            # Phase 5: Report
            if not self._phase_report():
                return False

            print()
            print('=' * 60)
            print('✓ E2E TEST PASSED')
            print('=' * 60)
            return True

        except Exception as e:
            print(f'✗ E2E test failed: {e}')
            import traceback

            traceback.print_exc()
            return False

    def _phase_triage(self) -> bool:
        """Phase 1: Triage - assess risk level."""
        print('Phase 1: Triage')
        # Initialize state if not loaded
        self.state_manager.load()
        self.state_manager.state.current_phase = 'triage'
        self.state_manager.state.phase_status = PhaseStatus.IN_PROGRESS
        self.state_manager.save()

        # Run triage agent
        prompt = f"""Assess risk level for PR {self.ticket_id}.
Changed files: {', '.join(self.diff_files)}

Return JSON with: risk_level (low/medium/high), reasoning, agents_to_run (array)"""

        result = self.runner.run(
            agent_name='triage',
            prompt=prompt,
            dry_run=self.dry_run,
            show_progress=self.verbose,
        )

        if result.success:
            self.risk_level = result.data.get('risk_level', 'medium')
            print(f'  ✓ Risk level: {self.risk_level}')

            # Checkpoint
            self.state_manager.checkpoint_phase('triage', 'complete')
            return True
        else:
            print(f'  ✗ Triage failed: {result.error}')
            return False

    def _phase_investigation(self) -> bool:
        """Phase 2: Investigation - run reviewers."""
        print('Phase 2: Investigation')
        self.state_manager.state.current_phase = 'investigation'
        self.state_manager.state.phase_status = PhaseStatus.IN_PROGRESS
        self.state_manager.save()

        # Run multiple mock reviewers
        reviewers = ['requirements-reviewer', 'side-effects-reviewer']

        for reviewer in reviewers:
            prompt = f"""Review PR {self.ticket_id} for {reviewer.replace('-', ' ')}.
Files: {', '.join(self.diff_files)}

Return JSON with: issues (array of {{severity, file, issue, recommendation}}), summary"""

            result = self.runner.run(
                agent_name=reviewer,
                prompt=prompt,
                dry_run=self.dry_run,
                show_progress=self.verbose,
            )

            if result.success:
                issues = result.data.get('issues', [])
                self.findings.extend(issues)
                print(f'  ✓ {reviewer}: {len(issues)} findings')
            else:
                print(f'  ✗ {reviewer} failed: {result.error}')
                return False

        # Checkpoint
        self.state_manager.checkpoint_phase('investigation', 'complete')
        print(f'  Total findings: {len(self.findings)}')
        return True

    def _phase_validation(self) -> bool:
        """Phase 3: Validation - validate findings."""
        print('Phase 3: Validation')
        self.state_manager.state.current_phase = 'validation'
        self.state_manager.state.phase_status = PhaseStatus.IN_PROGRESS
        self.state_manager.save()

        # Run validator
        prompt = f"""Validate findings for PR {self.ticket_id}.
Findings: {self.findings[:3]}  # Just first 3 for testing

Return JSON with: validated_findings (array with verdict: confirmed/false_positive), summary"""

        result = self.runner.run(
            agent_name='finding-validator',
            prompt=prompt,
            dry_run=self.dry_run,
            show_progress=self.verbose,
        )

        if result.success:
            validated = result.data.get('validated_findings', [])
            self.validated_findings = [
                f for f in validated if f.get('verdict') == 'confirmed'
            ]
            print(f'  ✓ Validated: {len(self.validated_findings)} confirmed')

            # Checkpoint
            self.state_manager.checkpoint_phase('validation', 'complete')
            return True
        else:
            print(f'  ✗ Validation failed: {result.error}')
            return False

    def _phase_synthesis(self) -> bool:
        """Phase 4: Synthesis - consolidate findings."""
        print('Phase 4: Synthesis')
        self.state_manager.state.current_phase = 'synthesis'
        self.state_manager.state.phase_status = PhaseStatus.IN_PROGRESS
        self.state_manager.save()

        # Run synthesis
        prompt = f"""Synthesize review findings for PR {self.ticket_id}.
Risk level: {self.risk_level}
Total findings: {len(self.findings)}
Validated: {len(self.validated_findings)}

Return JSON with: final_findings (array), recommendation (approve/request_changes/needs_discussion), summary"""

        result = self.runner.run(
            agent_name='synthesizer',
            prompt=prompt,
            dry_run=self.dry_run,
            show_progress=self.verbose,
        )

        if result.success:
            recommendation = result.data.get(
                'recommendation', 'needs_discussion'
            )
            print(f'  ✓ Recommendation: {recommendation}')

            # Checkpoint
            self.state_manager.checkpoint_phase('synthesis', 'complete')
            return True
        else:
            print(f'  ✗ Synthesis failed: {result.error}')
            return False

    def _phase_report(self) -> bool:
        """Phase 5: Report - generate final report."""
        print('Phase 5: Report')
        self.state_manager.state.current_phase = 'report'
        self.state_manager.state.phase_status = PhaseStatus.IN_PROGRESS
        self.state_manager.save()

        # Generate report
        report_path = self.state_dir / 'REVIEW_REPORT.md'
        report_content = f"""# PR Review Report: {self.ticket_id}

## Summary
- Risk Level: {self.risk_level}
- Total Findings: {len(self.findings)}
- Validated Findings: {len(self.validated_findings)}

## Findings

{self._format_findings()}

## Checkpoints
{self._list_checkpoints()}

---
*Generated by dry-run test*
"""
        report_path.write_text(report_content)
        print(f'  ✓ Report: {report_path}')

        # Mark complete
        self.state_manager.state.phase_status = PhaseStatus.COMPLETE
        self.state_manager.save()
        self.state_manager.checkpoint_phase('report', 'complete')

        return True

    def _format_findings(self) -> str:
        """Format findings for report."""
        if not self.findings:
            return '*No findings*'

        lines = []
        for i, f in enumerate(self.findings[:5], 1):
            severity = f.get('severity', 'unknown')
            issue = f.get('issue', 'No description')
            lines.append(f'{i}. [{severity.upper()}] {issue}')

        if len(self.findings) > 5:
            lines.append(f'... and {len(self.findings) - 5} more')

        return '\n'.join(lines)

    def _list_checkpoints(self) -> str:
        """List checkpoints for report."""
        checkpoints = self.state_manager.list_checkpoints()
        if not checkpoints:
            return '*No checkpoints*'
        return '\n'.join(f'- {cp}' for cp in checkpoints)


def main() -> int:
    """Run E2E test."""
    parser = argparse.ArgumentParser(description='PR Review E2E Test')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=level)

    with tempfile.TemporaryDirectory() as tmpdir:
        runner = MockPRReviewRunner(
            work_dir=Path(tmpdir),
            dry_run=True,
            verbose=args.verbose,
        )
        success = runner.run()

        # Show checkpoints
        print()
        print('Checkpoints created:')
        for cp in runner.state_manager.list_checkpoints():
            print(f'  - {cp}')

        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
