"""Voting gates - multi-agent consensus for critical decisions.

When the orchestrator hits a gate, it spawns multiple agents in parallel,
collects their votes, and either proceeds with consensus or escalates to user.
"""

import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any

from cc_orchestrations.core.config import VotingGateConfig
from cc_orchestrations.core.runner import AgentRunner
from cc_orchestrations.core.schemas import get_schema
from cc_orchestrations.core.state import VoteResult


LOG = logging.getLogger(__name__)


@dataclass
class VotingOutcome:
    """Outcome of a voting gate."""

    gate_name: str
    consensus: bool
    winner: str | None
    vote_counts: dict[str, int]
    votes: list[dict[str, Any]]
    needs_user_decision: bool = False
    user_prompt: str = ''

    def to_vote_result(self, user_decision: str = '') -> VoteResult:
        """Convert to VoteResult for state storage."""
        return VoteResult(
            gate_name=self.gate_name,
            votes=self.votes,
            winner=self.winner or '',
            consensus=self.consensus,
            user_decision=user_decision,
        )


class VotingGate:
    """A voting gate that requires consensus."""

    def __init__(
        self,
        config: VotingGateConfig,
        runner: AgentRunner,
    ):
        self.config = config
        self.runner = runner

    def run(
        self,
        context: dict[str, Any],
        voter_prompt: str | None = None,
    ) -> VotingOutcome:
        """Run the voting gate.

        Args:
            context: Context variables for the vote
            voter_prompt: Override prompt for voters

        Returns:
            VotingOutcome with consensus result or user escalation
        """
        prompt = voter_prompt or self._build_prompt(context)

        # Validate schema exists for voters
        schema_name = self.config.schema
        if schema_name:
            try:
                _ = get_schema(schema_name)  # Validate schema exists
            except ValueError:
                LOG.warning(
                    f'Schema {schema_name} not found for gate {self.config.name}'
                )

        # Run voters in parallel
        LOG.info(
            f'Running voting gate: {self.config.name} with {self.config.num_voters} voters'
        )

        tasks = [
            (
                self.config.voter_agent,
                f'{prompt}\n\nYou are voter {i + 1} of {self.config.num_voters}.',
                {'voter_id': f'voter_{i + 1}', **context},
            )
            for i in range(self.config.num_voters)
        ]

        results = self.runner.run_parallel(tasks)

        # Collect votes
        votes = []
        for result in results:
            if result.success and 'vote' in result.data:
                votes.append(result.data)
            else:
                LOG.warning(f'Voter failed or no vote: {result.error}')

        if not votes:
            LOG.error('No valid votes collected')
            return VotingOutcome(
                gate_name=self.config.name,
                consensus=False,
                winner=None,
                vote_counts={},
                votes=[],
                needs_user_decision=True,
                user_prompt='Voting failed - no valid votes received. Please decide manually.',
            )

        # Tally votes
        return tally_votes(
            gate_name=self.config.name,
            votes=votes,
            options=self.config.options,
            threshold=self.config.consensus_threshold,
        )


    def _build_prompt(self, context: dict[str, Any]) -> str:
        """Build the voting prompt from template and context."""
        if self.config.prompt_template:
            # Format template with context
            try:
                return self.config.prompt_template.format(**context)
            except KeyError as e:
                LOG.warning(f'Missing context key in prompt template: {e}')

        # Build generic prompt
        options_str = '\n'.join(f'- {opt}' for opt in self.config.options)
        return f"""
You are voting on: {self.config.name}

Context:
{context}

Options:
{options_str}

Evaluate the situation and cast your vote. Provide reasoning for your choice.
"""


def tally_votes(
    gate_name: str,
    votes: list[dict[str, Any]],
    options: list[str],
    threshold: float = 0.67,
) -> VotingOutcome:
    """Tally votes and determine consensus.

    Args:
        gate_name: Name of the voting gate
        votes: List of vote dictionaries with 'vote' key
        options: Valid options
        threshold: Fraction needed for consensus (default 2/3)

    Returns:
        VotingOutcome with consensus result
    """
    if not votes:
        return VotingOutcome(
            gate_name=gate_name,
            consensus=False,
            winner=None,
            vote_counts={},
            votes=[],
            needs_user_decision=True,
            user_prompt='No votes received.',
        )

    # Count votes
    vote_values = [v.get('vote', '') for v in votes]
    counts = Counter(vote_values)

    # Check for consensus
    total = len(votes)
    threshold_count = int(total * threshold)

    winner = None
    for option, count in counts.most_common():
        if count >= threshold_count:
            winner = option
            break

    if winner:
        LOG.info(
            f'Voting gate {gate_name}: Consensus on {winner} ({counts[winner]}/{total})'
        )
        return VotingOutcome(
            gate_name=gate_name,
            consensus=True,
            winner=winner,
            vote_counts=dict(counts),
            votes=votes,
        )
    # No consensus - need user decision
    vote_summary = '\n'.join(
        f'- {opt}: {count} vote(s)' for opt, count in counts.most_common()
    )
    reasoning_summary = '\n\n'.join(
        f'Voter {i + 1} ({v.get("vote", "N/A")}): {v.get("reasoning", "No reasoning provided")}'
        for i, v in enumerate(votes)
    )

    user_prompt = f"""
No consensus reached on {gate_name} (needed {threshold_count}/{total} votes).

Vote counts:
{vote_summary}

Voter reasoning:
{reasoning_summary}

Please choose one of: {', '.join(options)}
"""
    LOG.info(f'Voting gate {gate_name}: No consensus, escalating to user')
    return VotingOutcome(
        gate_name=gate_name,
        consensus=False,
        winner=None,
        vote_counts=dict(counts),
        votes=votes,
        needs_user_decision=True,
        user_prompt=user_prompt,
    )


def run_voting_gate(
    runner: AgentRunner,
    gate_name: str,
    num_voters: int,
    prompt: str,
    options: list[str],
    schema: str = '',
    threshold: float = 0.67,
    voter_agent: str = 'investigator',
) -> VotingOutcome:
    """Convenience function to run a one-off voting gate.

    Args:
        runner: AgentRunner instance
        gate_name: Name for this gate
        num_voters: Number of voters
        prompt: Prompt for voters
        options: Valid vote options
        schema: Schema name for structured output
        threshold: Consensus threshold
        voter_agent: Agent type to use for voting

    Returns:
        VotingOutcome
    """
    config = VotingGateConfig(
        name=gate_name,
        trigger_condition='True',
        num_voters=num_voters,
        consensus_threshold=threshold,
        voter_agent=voter_agent,
        schema=schema,
        options=options,
    )

    gate = VotingGate(config, runner)
    return gate.run({}, voter_prompt=prompt)
