"""Unit tests for cc_orchestrations.workflow.gates.

Tests voting gate logic including weighted voting, consensus detection,
and user escalation.
"""

from cc_orchestrations.workflow.gates import (
    VotingOutcome,
    tally_votes,
    tally_votes_weighted,
)


class TestTallyVotes:
    """Tests for the unweighted tally_votes function."""

    def test_empty_votes(self):
        """Empty votes should return no consensus and need user decision."""
        result = tally_votes('test_gate', [], ['A', 'B'])

        assert result.consensus is False
        assert result.winner is None
        assert result.needs_user_decision is True

    def test_unanimous_consensus(self):
        """All votes the same should reach consensus."""
        votes = [
            {'vote': 'A', 'confidence': 0.9, 'reasoning': 'A is best'},
            {'vote': 'A', 'confidence': 0.8, 'reasoning': 'A is good'},
            {'vote': 'A', 'confidence': 0.7, 'reasoning': 'A works'},
        ]
        result = tally_votes('test_gate', votes, ['A', 'B'])

        assert result.consensus is True
        assert result.winner == 'A'
        assert result.needs_user_decision is False

    def test_two_thirds_consensus(self):
        """2/3 majority should reach consensus with default threshold."""
        votes = [
            {'vote': 'A', 'confidence': 0.9, 'reasoning': 'A is best'},
            {'vote': 'A', 'confidence': 0.8, 'reasoning': 'A is good'},
            {'vote': 'B', 'confidence': 0.7, 'reasoning': 'B is better'},
        ]
        result = tally_votes('test_gate', votes, ['A', 'B'])

        assert result.consensus is True
        assert result.winner == 'A'

    def test_no_consensus(self):
        """Split vote should not reach consensus."""
        votes = [
            {'vote': 'A', 'confidence': 0.9, 'reasoning': 'A is best'},
            {'vote': 'B', 'confidence': 0.8, 'reasoning': 'B is better'},
            {'vote': 'C', 'confidence': 0.7, 'reasoning': 'C is great'},
        ]
        result = tally_votes('test_gate', votes, ['A', 'B', 'C'])

        assert result.consensus is False
        assert result.winner is None
        assert result.needs_user_decision is True

    def test_vote_counts_tracked(self):
        """Vote counts should be tracked correctly."""
        votes = [
            {'vote': 'A', 'reasoning': 'reason1'},
            {'vote': 'A', 'reasoning': 'reason2'},
            {'vote': 'B', 'reasoning': 'reason3'},
        ]
        result = tally_votes('test_gate', votes, ['A', 'B'])

        assert result.vote_counts['A'] == 2
        assert result.vote_counts['B'] == 1

    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        votes = [
            {'vote': 'A', 'reasoning': 'reason1'},
            {'vote': 'A', 'reasoning': 'reason2'},
            {'vote': 'B', 'reasoning': 'reason3'},
            {'vote': 'B', 'reasoning': 'reason4'},
        ]
        # 50% threshold - A has 2/4 = 50%
        result = tally_votes('test_gate', votes, ['A', 'B'], threshold=0.5)
        assert result.consensus is True
        assert result.winner == 'A'

        # 75% threshold - neither has 75%
        result = tally_votes('test_gate', votes, ['A', 'B'], threshold=0.75)
        assert result.consensus is False


class TestTallyVotesWeighted:
    """Tests for the confidence-weighted tally_votes_weighted function."""

    def test_empty_votes(self):
        """Empty votes should return no consensus."""
        result = tally_votes_weighted('test_gate', [], ['A', 'B'])

        assert result.consensus is False
        assert result.winner is None
        assert result.needs_user_decision is True

    def test_high_confidence_wins(self):
        """High confidence vote should outweigh low confidence votes."""
        votes = [
            {'vote': 'A', 'confidence': 0.95, 'reasoning': 'Very confident A'},
            {'vote': 'B', 'confidence': 0.3, 'reasoning': 'Unsure B'},
            {'vote': 'B', 'confidence': 0.3, 'reasoning': 'Unsure B'},
        ]
        # Weights: A=0.95, B=0.6, total=1.55
        # A: 0.95/1.55 = 61% (needs 67% for consensus)
        result = tally_votes_weighted('test_gate', votes, ['A', 'B'])

        # At 61%, A doesn't quite reach 67% threshold
        assert result.consensus is False

    def test_high_confidence_reaches_threshold(self):
        """High confidence vote should reach consensus if above threshold."""
        votes = [
            {'vote': 'A', 'confidence': 0.9, 'reasoning': 'Very confident A'},
            {'vote': 'A', 'confidence': 0.8, 'reasoning': 'Confident A'},
            {'vote': 'B', 'confidence': 0.2, 'reasoning': 'Unsure B'},
        ]
        # Weights: A=1.7, B=0.2, total=1.9
        # A: 1.7/1.9 = 89%
        result = tally_votes_weighted('test_gate', votes, ['A', 'B'])

        assert result.consensus is True
        assert result.winner == 'A'

    def test_low_confidence_needs_more_votes(self):
        """Low confidence votes should need more agreement."""
        votes = [
            {'vote': 'A', 'confidence': 0.4, 'reasoning': 'Maybe A'},
            {'vote': 'A', 'confidence': 0.4, 'reasoning': 'Maybe A'},
            {'vote': 'A', 'confidence': 0.4, 'reasoning': 'Maybe A'},
            {'vote': 'B', 'confidence': 0.4, 'reasoning': 'Maybe B'},
        ]
        # Weights: A=1.2, B=0.4, total=1.6
        # A: 1.2/1.6 = 75% (above threshold)
        result = tally_votes_weighted('test_gate', votes, ['A', 'B'])

        assert result.consensus is True
        assert result.winner == 'A'

    def test_fallback_to_unweighted_no_confidence(self):
        """Should fall back to unweighted if no confidence provided."""
        votes = [
            {'vote': 'A', 'reasoning': 'A is best'},
            {'vote': 'A', 'reasoning': 'A is good'},
            {'vote': 'B', 'reasoning': 'B is ok'},
        ]
        result = tally_votes_weighted('test_gate', votes, ['A', 'B'])

        # Falls back to unweighted: A has 2/3 = 67%
        assert result.consensus is True
        assert result.winner == 'A'

    def test_confidence_clamped_to_range(self):
        """Confidence values outside 0-1 should be clamped."""
        votes = [
            {'vote': 'A', 'confidence': 1.5, 'reasoning': 'Over confident'},
            {'vote': 'B', 'confidence': -0.5, 'reasoning': 'Negative?'},
            {'vote': 'A', 'confidence': 0.8, 'reasoning': 'Normal'},
        ]
        # Clamped: A=1.0+0.8=1.8, B=0.0, total=1.8
        result = tally_votes_weighted('test_gate', votes, ['A', 'B'])

        assert result.consensus is True
        assert result.winner == 'A'

    def test_invalid_confidence_uses_default(self):
        """Invalid confidence values should use default 0.5."""
        votes = [
            {'vote': 'A', 'confidence': 'high', 'reasoning': 'String conf'},
            {'vote': 'A', 'confidence': None, 'reasoning': 'None conf'},
            {'vote': 'A', 'confidence': 0.5, 'reasoning': 'Normal A'},
            {'vote': 'B', 'confidence': 0.5, 'reasoning': 'Normal B'},
        ]
        # A: 0.5 (string->default) + 0.5 (None->default) + 0.5 = 1.5
        # B: 0.5
        # Total: 2.0, A: 1.5/2.0 = 75%
        result = tally_votes_weighted('test_gate', votes, ['A', 'B'])

        assert result.consensus is True
        assert result.winner == 'A'

    def test_weighted_vote_counts_scaled(self):
        """Vote counts should be scaled weights (x10 for precision)."""
        votes = [
            {'vote': 'A', 'confidence': 0.9, 'reasoning': 'A'},
            {'vote': 'B', 'confidence': 0.5, 'reasoning': 'B'},
        ]
        result = tally_votes_weighted('test_gate', votes, ['A', 'B'])

        # vote_counts are int(weight * 10)
        assert result.vote_counts['A'] == 9  # 0.9 * 10
        assert result.vote_counts['B'] == 5  # 0.5 * 10

    def test_user_prompt_includes_weighted_info(self):
        """User prompt for no consensus should include weighted info."""
        votes = [
            {'vote': 'A', 'confidence': 0.5, 'reasoning': 'Maybe A'},
            {'vote': 'B', 'confidence': 0.5, 'reasoning': 'Maybe B'},
        ]
        result = tally_votes_weighted('test_gate', votes, ['A', 'B'])

        assert result.needs_user_decision is True
        assert 'weighted' in result.user_prompt.lower()

    def test_mixed_confidence_presence(self):
        """Some votes with confidence, some without."""
        votes = [
            {'vote': 'A', 'confidence': 0.9, 'reasoning': 'Confident A'},
            {'vote': 'A', 'reasoning': 'No confidence specified'},
            {'vote': 'B', 'confidence': 0.3, 'reasoning': 'Unsure B'},
        ]
        # A: 0.9 + 0.5 (default) = 1.4
        # B: 0.3
        # Total: 1.7, A: 1.4/1.7 = 82%
        result = tally_votes_weighted('test_gate', votes, ['A', 'B'])

        assert result.consensus is True
        assert result.winner == 'A'


class TestVotingOutcome:
    """Tests for VotingOutcome dataclass."""

    def test_outcome_creation(self):
        """Test basic outcome creation."""
        outcome = VotingOutcome(
            gate_name='test',
            consensus=True,
            winner='A',
            vote_counts={'A': 2, 'B': 1},
            votes=[{'vote': 'A'}],
        )

        assert outcome.gate_name == 'test'
        assert outcome.consensus is True
        assert outcome.winner == 'A'

    def test_outcome_to_vote_result(self):
        """Test conversion to VoteResult for state storage."""
        outcome = VotingOutcome(
            gate_name='test',
            consensus=True,
            winner='A',
            vote_counts={'A': 2},
            votes=[{'vote': 'A'}],
        )

        vote_result = outcome.to_vote_result()

        assert vote_result.gate_name == 'test'
        assert vote_result.winner == 'A'
        assert vote_result.consensus is True

    def test_outcome_with_user_decision(self):
        """Test outcome requiring user decision."""
        outcome = VotingOutcome(
            gate_name='test',
            consensus=False,
            winner=None,
            vote_counts={'A': 1, 'B': 1},
            votes=[],
            needs_user_decision=True,
            user_prompt='Please decide',
        )

        assert outcome.needs_user_decision is True
        assert outcome.user_prompt == 'Please decide'

        vote_result = outcome.to_vote_result(user_decision='A')
        assert vote_result.user_decision == 'A'
