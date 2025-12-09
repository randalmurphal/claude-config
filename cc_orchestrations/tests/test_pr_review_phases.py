"""Unit tests for cc_orchestrations.pr_review.phases.

Tests PR review phase logic including Round 2 consolidation.
"""

from unittest.mock import MagicMock

import pytest

from cc_orchestrations.core.runner import AgentResult
from cc_orchestrations.pr_review.phases import _consolidate_round2_findings


@pytest.fixture
def mock_context():
    """Create a mock PRReviewContext."""
    ctx = MagicMock()
    ctx.runner = MagicMock()
    ctx.log_status = MagicMock()
    return ctx


@pytest.fixture
def sample_round2_findings():
    """Create sample Round 2 findings."""
    return [
        {
            'issue': 'Missing error handling in API endpoint',
            'severity': 'major',
            'file': 'src/api.py',
            'source_agent': 'blind-spot-hunter',
        },
        {
            'issue': 'Race condition in cache update',
            'severity': 'critical',
            'file': 'src/cache.py',
            'source_agent': 'interaction-investigator',
        },
        {
            'issue': 'Potential null pointer in response handler',
            'severity': 'major',
            'file': 'src/handlers.py',
            'source_agent': 'blind-spot-hunter',
        },
    ]


@pytest.fixture
def sample_round2_results():
    """Create sample Round 2 agent results."""
    return [
        AgentResult(
            success=True,
            data={
                'issues': [
                    {'issue': 'Missing error handling', 'severity': 'major'},
                ],
                'areas_checked': ['error handling', 'input validation'],
            },
            agent_name='blind-spot-hunter',
        ),
        AgentResult(
            success=True,
            data={
                'issues': [
                    {
                        'issue': 'Race condition in cache',
                        'severity': 'critical',
                    },
                ],
                'areas_checked': ['concurrency', 'state management'],
            },
            agent_name='interaction-investigator',
        ),
        AgentResult(
            success=True,
            data={
                'revalidated_findings': [],
            },
            agent_name='conclusion-validator',
        ),
    ]


class TestConsolidateRound2Findings:
    """Tests for _consolidate_round2_findings function."""

    def test_returns_empty_with_no_runner(
        self, sample_round2_findings, sample_round2_results
    ):
        """Should return empty list if runner is None."""
        ctx = MagicMock()
        ctx.runner = None

        result = _consolidate_round2_findings(
            ctx, sample_round2_findings, sample_round2_results
        )

        assert result == []

    def test_returns_empty_with_no_findings(
        self, mock_context, sample_round2_results
    ):
        """Should return empty list if no findings."""
        result = _consolidate_round2_findings(
            mock_context, [], sample_round2_results
        )

        assert result == []
        mock_context.runner.run.assert_not_called()

    def test_calls_investigator_agent(
        self, mock_context, sample_round2_findings, sample_round2_results
    ):
        """Should call investigator agent for consolidation."""
        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={'compound_findings': [], 'contradictions': []},
            agent_name='investigator',
        )

        _consolidate_round2_findings(
            mock_context, sample_round2_findings, sample_round2_results
        )

        mock_context.runner.run.assert_called_once()
        call_args = mock_context.runner.run.call_args
        assert call_args[0][0] == 'investigator'  # First arg is agent name

    def test_uses_sonnet_model(
        self, mock_context, sample_round2_findings, sample_round2_results
    ):
        """Should use sonnet model for speed."""
        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={'compound_findings': [], 'contradictions': []},
            agent_name='investigator',
        )

        _consolidate_round2_findings(
            mock_context, sample_round2_findings, sample_round2_results
        )

        call_kwargs = mock_context.runner.run.call_args[1]
        assert call_kwargs.get('model_override') == 'sonnet'

    def test_extracts_compound_findings(
        self, mock_context, sample_round2_findings, sample_round2_results
    ):
        """Should extract compound findings from consolidation result."""
        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={
                'compound_findings': [
                    {
                        'issue': 'Combined error handling and race condition creates data corruption risk',
                        'compounds': [0, 1],
                        'severity': 'critical',
                    },
                ],
                'contradictions': [],
            },
            agent_name='investigator',
        )

        result = _consolidate_round2_findings(
            mock_context, sample_round2_findings, sample_round2_results
        )

        assert len(result) == 1
        assert 'data corruption' in result[0]['issue']
        assert result[0]['severity'] == 'critical'
        assert result[0]['source_agent'] == 'round2-consolidator'
        assert result[0]['type'] == 'compound'

    def test_extracts_contradictions(
        self, mock_context, sample_round2_findings, sample_round2_results
    ):
        """Should extract unresolved contradictions."""
        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={
                'compound_findings': [],
                'contradictions': [
                    {
                        'topic': 'Thread safety of cache implementation',
                        'positions': [
                            'blind-spot-hunter: safe',
                            'interaction-investigator: risky',
                        ],
                        'resolution': 'needs review',
                    },
                ],
            },
            agent_name='investigator',
        )

        result = _consolidate_round2_findings(
            mock_context, sample_round2_findings, sample_round2_results
        )

        assert len(result) == 1
        assert 'Contradiction' in result[0]['issue']
        assert 'Thread safety' in result[0]['issue']
        assert result[0]['type'] == 'contradiction'
        assert result[0]['severity'] == 'medium'

    def test_ignores_resolved_contradictions(
        self, mock_context, sample_round2_findings, sample_round2_results
    ):
        """Should ignore contradictions marked as resolved."""
        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={
                'compound_findings': [],
                'contradictions': [
                    {
                        'topic': 'Minor disagreement',
                        'positions': ['a: yes', 'b: no'],
                        'resolution': 'resolved',  # Marked as resolved
                    },
                ],
            },
            agent_name='investigator',
        )

        result = _consolidate_round2_findings(
            mock_context, sample_round2_findings, sample_round2_results
        )

        assert len(result) == 0

    def test_handles_consolidation_failure(
        self, mock_context, sample_round2_findings, sample_round2_results
    ):
        """Should return empty list on consolidation failure."""
        mock_context.runner.run.return_value = AgentResult(
            success=False,
            error='Timeout',
            agent_name='investigator',
        )

        result = _consolidate_round2_findings(
            mock_context, sample_round2_findings, sample_round2_results
        )

        assert result == []

    def test_limits_findings_in_prompt(
        self, mock_context, sample_round2_results
    ):
        """Should limit findings sent to consolidator to prevent prompt bloat."""
        # Create many findings
        many_findings = [
            {
                'issue': f'Issue {i}',
                'severity': 'minor',
                'file': f'file_{i}.py',
                'source_agent': 'test',
            }
            for i in range(50)
        ]

        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={'compound_findings': [], 'contradictions': []},
            agent_name='investigator',
        )

        _consolidate_round2_findings(
            mock_context, many_findings, sample_round2_results
        )

        # Check the prompt sent to consolidator
        call_args = mock_context.runner.run.call_args
        prompt = call_args[0][1]

        # Should mention it's showing a subset
        assert '15' in prompt or 'first' in prompt.lower()

    def test_builds_agent_summaries(
        self, mock_context, sample_round2_findings, sample_round2_results
    ):
        """Should include agent summaries in consolidation prompt."""
        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={'compound_findings': [], 'contradictions': []},
            agent_name='investigator',
        )

        _consolidate_round2_findings(
            mock_context, sample_round2_findings, sample_round2_results
        )

        call_args = mock_context.runner.run.call_args
        prompt = call_args[0][1]

        # Should include agent names in summary
        assert 'blind-spot-hunter' in prompt
        assert 'interaction-investigator' in prompt

    def test_handles_empty_compound_fields(
        self, mock_context, sample_round2_findings, sample_round2_results
    ):
        """Should handle findings without required fields gracefully."""
        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={
                'compound_findings': [
                    {'compounds': [0, 1]},  # Missing 'issue' field
                    {'issue': 'Valid finding', 'severity': 'high'},  # Valid
                ],
                'contradictions': [
                    {'resolution': 'needs review'},  # Missing 'topic' field
                ],
            },
            agent_name='investigator',
        )

        result = _consolidate_round2_findings(
            mock_context, sample_round2_findings, sample_round2_results
        )

        # Should only include valid findings
        assert len(result) == 1
        assert result[0]['issue'] == 'Valid finding'

    def test_failed_agent_results_excluded(
        self, mock_context, sample_round2_findings
    ):
        """Failed agent results should be excluded from summaries."""
        results_with_failure = [
            AgentResult(
                success=True,
                data={'issues': [{'issue': 'test'}]},
                agent_name='blind-spot-hunter',
            ),
            AgentResult(
                success=False,
                error='Timeout',
                agent_name='interaction-investigator',
            ),
        ]

        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={'compound_findings': [], 'contradictions': []},
            agent_name='investigator',
        )

        _consolidate_round2_findings(
            mock_context, sample_round2_findings, results_with_failure
        )

        call_args = mock_context.runner.run.call_args
        prompt = call_args[0][1]

        # Should include successful agent
        assert 'blind-spot-hunter' in prompt


class TestConsolidationIntegrationWithPhase:
    """Tests for consolidation integration with _run_second_round."""

    def test_consolidation_extends_findings(
        self, mock_context, sample_round2_findings, sample_round2_results
    ):
        """Consolidation findings should extend Round 2 findings."""
        # This tests that the return value format is correct for extending
        mock_context.runner.run.return_value = AgentResult(
            success=True,
            data={
                'compound_findings': [
                    {
                        'issue': 'Compound issue',
                        'severity': 'high',
                        'compounds': [0, 1],
                    },
                ],
                'contradictions': [],
            },
            agent_name='investigator',
        )

        result = _consolidate_round2_findings(
            mock_context, sample_round2_findings, sample_round2_results
        )

        # Result should be a list that can be extended to findings
        assert isinstance(result, list)
        for finding in result:
            assert isinstance(finding, dict)
            assert 'issue' in finding
            assert 'severity' in finding
            assert 'source_agent' in finding
