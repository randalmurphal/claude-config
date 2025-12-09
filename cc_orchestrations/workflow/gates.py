"""Voting gates - multi-agent consensus for critical decisions.

When the orchestrator hits a gate, it spawns multiple agents in parallel,
collects their votes, and either proceeds with consensus or escalates to user.
"""

import logging
from collections import Counter, defaultdict
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
        base_prompt = voter_prompt or self._build_prompt(context)

        # Always add JSON output instructions to ensure structured response
        prompt = base_prompt + self._get_json_instructions()

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
        # Use model from voter_models if configured (supports thinking models for critical decisions)
        LOG.info(
            f'Running voting gate: {self.config.name} with {self.config.num_voters} voters'
        )
        if self.config.voter_models:
            LOG.info(
                f'  Using models: {self.config.voter_models[: self.config.num_voters]}'
            )

        tasks = []
        for i in range(self.config.num_voters):
            model = (
                self.config.get_model_for_voter(i)
                if self.config.voter_models
                else None
            )
            task = {
                'name': self.config.voter_agent,
                'prompt': f'{prompt}\n\nYou are voter {i + 1} of {self.config.num_voters}.',
                'context': {'voter_id': f'voter_{i + 1}', **context},
            }
            if model:
                task['model'] = model
            tasks.append(task)

        results = self.runner.run_parallel(tasks)

        # Collect votes
        votes = []
        for result in results:
            if (
                result.success
                and isinstance(result.data, dict)
                and 'vote' in result.data
            ):
                votes.append(result.data)
            else:
                LOG.warning(
                    f'Voter failed or invalid vote format: {result.error or type(result.data).__name__}'
                )

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

        # Tally votes with confidence weighting
        return tally_votes_weighted(
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

    def _get_json_instructions(self) -> str:
        """Get JSON output instructions for voters."""
        options_list = ', '.join(f'"{opt}"' for opt in self.config.options)
        return f"""

## CRITICAL: JSON Output Required

You MUST respond with a JSON object containing these fields:
- "vote": One of [{options_list}]
- "confidence": A number between 0.0 and 1.0
- "reasoning": A string explaining your vote

Example format:
{{
    "vote": "{self.config.options[0]}",
    "confidence": 0.85,
    "reasoning": "Your explanation here..."
}}

Output ONLY the JSON object, no other text before or after."""


def tally_votes_weighted(
    gate_name: str,
    votes: list[dict[str, Any]],
    options: list[str],
    threshold: float = 0.67,
) -> VotingOutcome:
    """Tally votes with confidence weighting.

    Weight = confidence value (0.0-1.0), defaults to 0.5 if missing.
    Winner needs weighted_score / total_weight >= threshold.

    Falls back to unweighted tally_votes() if all confidences are missing.

    Args:
        gate_name: Name of the voting gate
        votes: List of vote dictionaries with 'vote' and optional 'confidence' keys
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

    weighted_counts: dict[str, float] = defaultdict(float)
    total_weight = 0.0
    has_confidence = False

    for vote in votes:
        if not isinstance(vote, dict):
            continue
        vote_value = vote.get('vote', '')
        confidence = vote.get('confidence')

        if confidence is not None:
            has_confidence = True
            # Clamp confidence to valid range
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = 0.5
        else:
            confidence = 0.5  # Default to neutral

        weighted_counts[vote_value] += confidence
        total_weight += confidence

    # If no confidences were provided, fall back to unweighted voting
    if not has_confidence:
        LOG.debug('No confidence scores in votes, using unweighted tally')
        return tally_votes(gate_name, votes, options, threshold)

    if total_weight == 0:
        return tally_votes(gate_name, votes, options, threshold)

    # Find winner based on weighted threshold
    winner = None
    for option, weight in sorted(weighted_counts.items(), key=lambda x: -x[1]):
        if option and weight / total_weight >= threshold:
            winner = option
            break

    # Convert to integer counts for compatibility (multiply by 10 for precision)
    vote_counts = {k: int(v * 10) for k, v in weighted_counts.items() if k}

    if winner:
        LOG.info(
            f'Voting gate {gate_name}: Weighted consensus on {winner} '
            f'({weighted_counts[winner]:.2f}/{total_weight:.2f})'
        )
        return VotingOutcome(
            gate_name=gate_name,
            consensus=True,
            winner=winner,
            vote_counts=vote_counts,
            votes=votes,
        )

    # No consensus - need user decision
    vote_summary = '\n'.join(
        f'- {opt}: {weight:.2f} weighted score'
        for opt, weight in sorted(weighted_counts.items(), key=lambda x: -x[1])
        if opt
    )
    reasoning_summary = '\n\n'.join(
        f'Voter {i + 1} ({v.get("vote", "N/A")}, confidence: {v.get("confidence", "N/A")}): '
        f'{v.get("reasoning", "No reasoning provided")}'
        for i, v in enumerate(votes)
        if isinstance(v, dict)
    )

    user_prompt = f"""
No consensus reached on {gate_name} (needed {threshold:.0%} weighted).

Weighted vote scores:
{vote_summary}

Total weight: {total_weight:.2f}

Voter reasoning:
{reasoning_summary}

Please choose one of: {', '.join(options)}
"""
    LOG.info(
        f'Voting gate {gate_name}: No weighted consensus, escalating to user'
    )
    return VotingOutcome(
        gate_name=gate_name,
        consensus=False,
        winner=None,
        vote_counts=vote_counts,
        votes=votes,
        needs_user_decision=True,
        user_prompt=user_prompt,
    )


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

    # Count votes (filter out any non-dict entries defensively)
    vote_values = [v.get('vote', '') for v in votes if isinstance(v, dict)]
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
        if isinstance(v, dict)
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
    voter_models: list[str] | None = None,
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
        voter_models: Optional list of models for each voter (e.g., for using
                     opus-thinking on critical decisions). If provided, cycles
                     through models for each voter.

    Returns:
        VotingOutcome
    """
    config = VotingGateConfig(
        name=gate_name,
        trigger_condition='True',
        num_voters=num_voters,
        consensus_threshold=threshold,
        voter_agent=voter_agent,
        voter_models=voter_models or [],
        schema=schema,
        options=options,
    )

    gate = VotingGate(config, runner)
    return gate.run({}, voter_prompt=prompt)
