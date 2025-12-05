"""Validation and fix loops - the core enforcement mechanism.

These loops are the key to external enforcement: the script won't proceed
until the validation passes or escalates.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from cc_orchestrations.core.runner import AgentResult, AgentRunner
from cc_orchestrations.core.state import Issue

from .gates import VotingOutcome, run_voting_gate


LOG = logging.getLogger(__name__)


@dataclass
class LoopResult:
    """Result of a validation/fix loop."""

    passed: bool
    attempts: int
    issues_found: list[Issue] = field(default_factory=list)
    issues_fixed: list[str] = field(default_factory=list)
    voting_outcome: VotingOutcome | None = None
    escalated: bool = False
    escalation_reason: str = ''
    error: str = ''


def issues_are_same(prev: list[Issue], curr: list[Issue]) -> bool:
    """Check if issues are substantially the same (same issue repeating)."""
    if not prev or not curr:
        return False

    # Compare by issue text (ignoring line numbers which might shift)
    prev_texts = {i.issue.lower().strip() for i in prev}
    curr_texts = {i.issue.lower().strip() for i in curr}

    # If >50% of current issues were in previous, consider them "same"
    if not curr_texts:
        return False

    overlap = len(prev_texts & curr_texts)
    return overlap / len(curr_texts) > 0.5


class ValidationLoop:
    """Runs validation with multiple reviewers until pass or escalation."""

    def __init__(
        self,
        runner: AgentRunner,
        max_attempts: int = 3,
        reviewers: int = 2,
        same_issue_threshold: int = 2,
    ):
        self.runner = runner
        self.max_attempts = max_attempts
        self.reviewers = reviewers
        self.same_issue_threshold = same_issue_threshold

    def run(
        self,
        component: str,
        context: dict[str, Any],
        validator_agents: list[str] | None = None,
        on_issues_found: Callable[[list[Issue]], None] | None = None,
    ) -> LoopResult:
        """Run validation loop.

        Args:
            component: Component being validated
            context: Context for validators
            validator_agents: List of validator agent names (defaults to ['validator'])
            on_issues_found: Callback when issues found (for state updates)

        Returns:
            LoopResult indicating pass/fail/escalate
        """
        if not validator_agents:
            validator_agents = ['validator'] * self.reviewers

        all_issues: list[Issue] = []
        previous_issues: list[Issue] = []
        same_issue_count = 0

        for attempt in range(1, self.max_attempts + 1):
            LOG.info(
                f'Validation attempt {attempt}/{self.max_attempts} for {component}'
            )

            # Run validators in parallel
            tasks = [
                (
                    agent,
                    f'Validate {component}',
                    {**context, 'focus': f'reviewer_{i}'},
                )
                for i, agent in enumerate(validator_agents)
            ]
            results = self.runner.run_parallel(tasks)

            # Collect issues from all validators
            current_issues: list[Issue] = []
            for result in results:
                if result.success and 'issues' in result.data:
                    for issue_data in result.data['issues']:
                        current_issues.append(Issue.from_dict(issue_data))

            # Deduplicate issues
            seen = set()
            deduped: list[Issue] = []
            for issue in current_issues:
                key = (issue.file, issue.issue.lower().strip())
                if key not in seen:
                    seen.add(key)
                    deduped.append(issue)
            current_issues = deduped

            if on_issues_found:
                on_issues_found(current_issues)

            # Check if passed
            critical_issues = [
                i for i in current_issues if i.severity == 'critical'
            ]
            major_issues = [i for i in current_issues if i.severity == 'major']

            if not critical_issues and not major_issues:
                LOG.info(f'Validation passed for {component}')
                return LoopResult(
                    passed=True,
                    attempts=attempt,
                    issues_found=current_issues,  # May have minor issues
                )

            # Check for same issue pattern
            if issues_are_same(previous_issues, current_issues):
                same_issue_count += 1
                LOG.warning(
                    f'Same issues found ({same_issue_count}/{self.same_issue_threshold})'
                )

                if same_issue_count >= self.same_issue_threshold:
                    # Trigger voting
                    LOG.info('Same issue threshold reached, triggering vote')
                    outcome = self._vote_on_fix_strategy(
                        component, current_issues, attempt
                    )

                    if outcome.needs_user_decision:
                        return LoopResult(
                            passed=False,
                            attempts=attempt,
                            issues_found=current_issues,
                            voting_outcome=outcome,
                            escalated=True,
                            escalation_reason='Same issue repeated, voting inconclusive',
                        )

                    # Apply voted strategy
                    if outcome.winner == 'ESCALATE':
                        return LoopResult(
                            passed=False,
                            attempts=attempt,
                            issues_found=current_issues,
                            voting_outcome=outcome,
                            escalated=True,
                            escalation_reason='Voters chose to escalate',
                        )

                    # Reset counter if voters chose to try again with new strategy
                    same_issue_count = 0
            else:
                same_issue_count = 0  # Reset if issues changed

            previous_issues = current_issues
            all_issues.extend(current_issues)

            # If not last attempt, run fix loop
            if attempt < self.max_attempts:
                fix_result = self._run_fix(component, current_issues, context)
                if not fix_result.success:
                    LOG.error(f'Fix failed: {fix_result.error}')
                    # Continue to next validation attempt anyway

        # Max attempts reached
        return LoopResult(
            passed=False,
            attempts=self.max_attempts,
            issues_found=previous_issues,
            escalated=True,
            escalation_reason=f'Max attempts ({self.max_attempts}) reached with unresolved issues',
        )

    def _run_fix(
        self,
        component: str,
        issues: list[Issue],
        context: dict[str, Any],
    ) -> AgentResult:
        """Run fix executor for issues."""
        issues_json = [i.to_dict() for i in issues]
        prompt = f"""Fix the following issues in {component}:

Issues:
{issues_json}

Fix all critical and major issues. Run linting after fixes.
"""
        return self.runner.run(
            'fix_executor',
            prompt,
            context={**context, 'issues': issues_json},
        )

    def _vote_on_fix_strategy(
        self,
        component: str,
        issues: list[Issue],
        attempt: int,
    ) -> VotingOutcome:
        """Vote on fix strategy when same issue repeats."""
        issues_summary = '\n'.join(
            f'- [{i.severity}] {i.issue}' for i in issues[:5]
        )

        prompt = f"""
The following issues have persisted after {attempt} fix attempts:

Component: {component}

Issues:
{issues_summary}

Vote on the best strategy:
- FIX_IN_PLACE: Try a different approach to fix in place
- REFACTOR: Needs architectural refactor to fix properly
- ESCALATE: Requires human decision or spec change

Consider the root cause and whether the issue is fixable with current approach.
"""
        return run_voting_gate(
            runner=self.runner,
            gate_name='fix_strategy',
            num_voters=3,
            prompt=prompt,
            options=['FIX_IN_PLACE', 'REFACTOR', 'ESCALATE'],
            schema='fix_strategy_vote',
            voter_agent='investigator',
        )


class FixLoop:
    """Runs fix attempts until issues resolved or max attempts."""

    def __init__(
        self,
        runner: AgentRunner,
        max_attempts: int = 3,
    ):
        self.runner = runner
        self.max_attempts = max_attempts

    def run(
        self,
        component: str,
        issues: list[Issue],
        context: dict[str, Any],
        validate_after: bool = True,
    ) -> LoopResult:
        """Run fix loop.

        Args:
            component: Component to fix
            issues: Issues to fix
            context: Context for fix executor
            validate_after: Whether to validate after each fix

        Returns:
            LoopResult
        """
        remaining_issues = issues.copy()
        fixed_issues: list[str] = []

        for attempt in range(1, self.max_attempts + 1):
            if not remaining_issues:
                return LoopResult(
                    passed=True,
                    attempts=attempt,
                    issues_fixed=fixed_issues,
                )

            LOG.info(
                f'Fix attempt {attempt}/{self.max_attempts} for {component}'
            )

            # Run fix executor
            result = self.runner.run(
                'fix_executor',
                f'Fix issues in {component}',
                context={
                    **context,
                    'issues': [i.to_dict() for i in remaining_issues],
                },
            )

            if not result.success:
                LOG.error(f'Fix executor failed: {result.error}')
                continue

            # Track what was fixed
            if result.get('fixed_issues'):
                fixed_issues.extend(result.get('fixed_issues', []))

            # Check remaining
            if result.get('remaining_issues'):
                remaining_issues = [
                    Issue(severity='major', issue=i)
                    for i in result.get('remaining_issues', [])
                ]
            else:
                # If no remaining issues reported, assume fixed
                remaining_issues = []

            if result.status == 'fixed':
                return LoopResult(
                    passed=True,
                    attempts=attempt,
                    issues_fixed=fixed_issues,
                )

            if result.status == 'blocked':
                return LoopResult(
                    passed=False,
                    attempts=attempt,
                    issues_found=remaining_issues,
                    issues_fixed=fixed_issues,
                    escalated=True,
                    escalation_reason=f'Fix blocked: {result.get("blockers", [])}',
                )

        return LoopResult(
            passed=False,
            attempts=self.max_attempts,
            issues_found=remaining_issues,
            issues_fixed=fixed_issues,
            escalated=True,
            escalation_reason=f'Max fix attempts ({self.max_attempts}) reached',
        )
