"""Phase handlers for PR review workflow.

Each phase performs a specific part of the review process:
- Triage: Setup, context gathering, risk assessment
- Investigation: Run reviewers in parallel
- Validation: Validate findings, filter false positives
- Synthesis: Consolidate findings, classify MR threads
- Report: Generate final report and cleanup
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cc_orchestrations.core.runner import AgentRunner
from cc_orchestrations.workflow import (
    PhaseResult,
    VotingOutcome,
    run_voting_gate,
)

from .config import (
    PRReviewConfig,
    RiskLevel,
    create_default_config,
)

LOG = logging.getLogger(__name__)


@dataclass
class PRReviewContext:
    """Context for PR review workflow execution.

    Tracks state across all phases.
    """

    # Inputs
    ticket_id: str
    source_branch: str
    target_branch: str
    work_dir: Path
    worktree_path: Path | None = None

    # Configuration
    config: PRReviewConfig = field(default_factory=create_default_config)
    runner: AgentRunner | None = None

    # State
    risk_level: RiskLevel = RiskLevel.MEDIUM
    diff_files: list[str] = field(default_factory=list)
    diff_summary: str = ''
    requirements: str = ''
    test_files: list[str] = field(default_factory=list)

    # Findings
    findings: list[dict[str, Any]] = field(default_factory=list)
    validated_findings: list[dict[str, Any]] = field(default_factory=list)
    false_positives: list[dict[str, Any]] = field(default_factory=list)

    # MR threads
    mr_threads: dict[str, str] = field(
        default_factory=dict
    )  # thread_id -> status

    # Discoveries
    discoveries: list[str] = field(default_factory=list)

    # Agents selected during triage
    agents_to_run: list[Any] = field(default_factory=list)

    def log_status(self, phase: str, message: str) -> None:
        """Log phase status."""
        LOG.info(f'[{phase}] {message}')
        print(f'[{phase}] {message}')

    def add_discovery(self, discovery: str) -> None:
        """Add a discovery (gotcha, unexpected behavior, etc.)."""
        self.discoveries.append(discovery)
        LOG.info(f'Discovery: {discovery}')


# =============================================================================
# PHASE 1: TRIAGE
# =============================================================================


def phase_triage(ctx: PRReviewContext) -> PhaseResult:
    """Setup worktree, gather context, assess risk.

    Steps:
    1. Create worktree for PR review
    2. Gather diff, requirements, test files
    3. Assess risk level based on blast radius
    4. Determine which agents to run

    Args:
        ctx: PR review context

    Returns:
        PhaseResult with success status and risk assessment
    """
    ctx.log_status('triage', 'Starting triage phase')

    # Step 1: Setup worktree
    ctx.log_status('triage', f'Setting up worktree for {ctx.source_branch}')

    # In real implementation, would use git-worktree script
    # For now, assume worktree is already set up or skip
    if not ctx.worktree_path:
        ctx.worktree_path = ctx.work_dir / '.pr-review-worktree'
        ctx.log_status('triage', f'Using worktree at {ctx.worktree_path}')

    # Step 2: Use pre-computed context or gather if missing
    ctx.log_status('triage', 'Gathering diff and context')

    # diff_files is typically pre-computed by CLI - use it if available
    if ctx.diff_files:
        ctx.log_status(
            'triage', f'Using {len(ctx.diff_files)} pre-computed changed files'
        )
        # Extract test files from diff
        ctx.test_files = [f for f in ctx.diff_files if 'test' in f.lower()]
        ctx.diff_summary = f'{len(ctx.diff_files)} files changed'
    elif ctx.runner:
        # Fallback: run agent to gather context (slower, may fail in print mode)
        result = ctx.runner.run(
            'investigator',
            f"""Gather PR context for review.

Ticket: {ctx.ticket_id}
Source: {ctx.source_branch}
Target: {ctx.target_branch}
Work dir: {ctx.worktree_path}

Tasks:
1. Get git diff --name-only between branches (list all changed files)
2. Get diff stats (insertions, deletions, files changed)
3. Find test files related to changes
4. Extract requirements from ticket (if available)

Return structured data:
- diff_files: List of changed file paths
- diff_summary: Brief summary of changes
- test_files: List of test files
- requirements: Requirements from ticket (or "N/A")
""",
            context={
                'ticket_id': ctx.ticket_id,
                'source_branch': ctx.source_branch,
                'target_branch': ctx.target_branch,
                'work_dir': str(ctx.worktree_path),
            },
        )

        if not result.success:
            return PhaseResult(
                success=False,
                error=f'Context gathering failed: {result.error}',
            )

        # Store context from agent
        ctx.diff_files = result.get('diff_files', [])
        ctx.diff_summary = result.get('diff_summary', '')
        ctx.test_files = result.get('test_files', [])
        ctx.requirements = result.get('requirements', 'N/A')
    else:
        return PhaseResult(
            success=False,
            error='No diff_files provided and no runner to gather context',
        )

    ctx.log_status('triage', f'Found {len(ctx.diff_files)} changed files')

    # Step 3: Assess risk
    ctx.log_status('triage', 'Assessing blast radius')

    risk_result = ctx.runner.run(
        'investigator',
        f"""Assess blast radius and risk level for PR.

Changed files ({len(ctx.diff_files)}):
{ctx.diff_files}

Diff summary:
{ctx.diff_summary}

Consider:
1. Blast radius: How many files/modules depend on changed code?
2. Data operations: Are there writes, deletes, migrations?
3. Complexity: Is logic complex or straightforward?
4. Test coverage: Are tests comprehensive?
5. Shared code: Are common utilities or frameworks modified?

Return risk assessment:
- risk_level: low, medium, or high
- reasoning: Why this risk level?
- critical_dependencies: List of critical dependencies (if any)
- recommendations: Any mitigation recommendations

Key question: If this PR has a bug, how bad is it and how many things break?
""",
        context={
            'diff_files': ctx.diff_files,
            'diff_summary': ctx.diff_summary,
            'file_count': len(ctx.diff_files),
        },
    )

    if not risk_result.success:
        ctx.log_status('triage', 'Risk assessment failed, defaulting to MEDIUM')
        ctx.risk_level = RiskLevel.MEDIUM
    else:
        risk_str = risk_result.get('risk_level', 'medium').lower()
        try:
            ctx.risk_level = RiskLevel(risk_str)
        except ValueError:
            ctx.log_status(
                'triage', f'Unknown risk level {risk_str}, defaulting to MEDIUM'
            )
            ctx.risk_level = RiskLevel.MEDIUM

        # Store reasoning as discovery
        reasoning = risk_result.get('reasoning', '')
        if reasoning:
            ctx.add_discovery(f'Risk assessment: {reasoning}')

    ctx.log_status('triage', f'Risk level: {ctx.risk_level.value}')

    # Step 4: Determine agents to run using intelligent analysis
    ctx.log_status('triage', 'Analyzing code to determine relevant reviewers')

    # Get all available agent names and descriptions
    available_agents = [
        {'name': a.name, 'description': a.description, 'required': a.required}
        for a in ctx.config.agents
    ]

    # Use agent to analyze which reviewers are relevant
    agent_selection_result = ctx.runner.run(
        'investigator',
        f"""Analyze this PR and determine which specialized reviewers are needed.

**Ticket:** {ctx.ticket_id}
**Files changed ({len(ctx.diff_files)}):**
{chr(10).join(f'- {f}' for f in ctx.diff_files)}

**Risk level:** {ctx.risk_level.value}

**Available reviewers:**
{chr(10).join(f'- {a["name"]}: {a["description"]} (required: {a["required"]})' for a in available_agents)}

**Your task:**
1. Look at the actual code in the changed files
2. Determine which reviewers are relevant based on what the code DOES, not just filenames
3. Required reviewers always run
4. For conditional reviewers, decide if they're relevant

Consider:
- Does the code have MongoDB/database operations? → mongo-ops-reviewer
- Does it modify business objects or schemas? → schema-alignment-reviewer, bo-structure-reviewer
- Does it have import/data processing logic? → import-framework-reviewer
- Does it have API endpoints? → api-security-reviewer
- Does it have performance-sensitive operations (loops, queries, bulk ops)? → performance-reviewer
- Does it have complex architecture changes? → architecture-reviewer

Return JSON:
{{
  "agents_to_run": ["agent-name-1", "agent-name-2", ...],
  "reasoning": "Brief explanation of why each agent was selected"
}}
""",
        model_override='opus',
    )

    # Parse agent selection
    selected_agent_names = set()
    if agent_selection_result.success:
        selected_names = agent_selection_result.data.get('agents_to_run', [])
        if isinstance(selected_names, list):
            selected_agent_names = set(selected_names)
            reasoning = agent_selection_result.data.get('reasoning', '')
            if reasoning:
                ctx.add_discovery(f'Agent selection reasoning: {reasoning}')

    # Always include required agents, plus intelligently selected ones
    agents_to_run = []
    for agent in ctx.config.agents:
        if agent.required or agent.name in selected_agent_names:
            agents_to_run.append(agent)

    # Store for later phases
    ctx.agents_to_run = agents_to_run

    ctx.log_status('triage', f'Will run {len(agents_to_run)} review agents:')
    for agent in agents_to_run:
        ctx.log_status('triage', f'  - {agent.name}')

    return PhaseResult(
        success=True,
        data={
            'risk_level': ctx.risk_level.value,
            'diff_files': ctx.diff_files,
            'agents_to_run': [a.name for a in agents_to_run],
        },
    )


# =============================================================================
# PHASE 2: INVESTIGATION
# =============================================================================


def phase_investigation(ctx: PRReviewContext) -> PhaseResult:
    """Run review agents in parallel to identify issues.

    Steps:
    1. Get agents for risk level
    2. Run agents in parallel
    3. Collect findings
    4. (Optional) Run second round if medium+ risk

    Args:
        ctx: PR review context

    Returns:
        PhaseResult with findings
    """
    ctx.log_status('investigation', 'Starting investigation phase')

    if not ctx.runner:
        return PhaseResult(success=False, error='No agent runner configured')

    # Step 1: Get agents selected during triage (or fall back to config-based selection)
    agents_to_run = getattr(ctx, 'agents_to_run', None)
    if not agents_to_run:
        # Fallback if triage didn't set agents
        agents_to_run = ctx.config.get_agents_for_risk(
            ctx.risk_level,
            {
                'diff_files': ctx.diff_files,
                'file_count': len(ctx.diff_files),
            },
        )

    if not agents_to_run:
        ctx.log_status('investigation', 'No agents to run')
        return PhaseResult(success=True, data={'findings': []})

    ctx.log_status(
        'investigation', f'Running {len(agents_to_run)} agents in parallel'
    )

    # Step 2: Run agents in parallel with proper model and skills
    # JSON output instructions to append to all prompts
    json_output_instructions = """

---
**IMPORTANT: Output Format**

You MUST return your response as valid JSON with this structure:
```json
{
  "issues": [
    {
      "severity": "critical|major|minor",
      "issue": "Brief description of the issue",
      "file": "path/to/file.py",
      "line": 123,
      "details": "Detailed explanation",
      "recommendation": "How to fix it"
    }
  ],
  "summary": "Brief summary of your review",
  "no_issues_reason": "If no issues found, explain why the code looks good"
}
```

If you find NO issues, return: `{"issues": [], "summary": "...", "no_issues_reason": "..."}`
Do NOT return plain text. Return ONLY valid JSON.
"""

    tasks = []
    for agent in agents_to_run:
        # Format prompt with context
        prompt = agent.prompt_template.format(
            ticket_id=ctx.ticket_id,
            requirements=ctx.requirements,
            diff_files='\n'.join(ctx.diff_files),
            test_files='\n'.join(ctx.test_files),
            file_count=len(ctx.diff_files),
        )

        # Append JSON output instructions
        prompt = prompt + json_output_instructions

        # Extract skill names from LOAD: directives in prompt
        skills = []
        for line in prompt.split('\n'):
            if line.strip().startswith('LOAD:'):
                skill_ref = line.strip()[5:].strip()
                # Handle "skill (section: ...)" format
                skill_name = skill_ref.split('(')[0].strip()
                if skill_name:
                    skills.append(skill_name)

        # Get model from agent config (default to opus for PR review)
        model = getattr(agent, 'model', 'opus') or 'opus'

        ctx.log_status(
            'investigation', f'  Agent: {agent.name} (model: {model})'
        )

        tasks.append(
            {
                'name': agent.name,
                'prompt': prompt,
                'context': {
                    'work_dir': str(ctx.worktree_path),
                    'diff_files': ctx.diff_files,
                },
                'model': model,
                'skills': skills if skills else None,
            }
        )

    results = ctx.runner.run_parallel(tasks)

    # Step 3: Collect findings
    findings: list[dict[str, Any]] = []

    for result in results:
        if not result.success:
            ctx.log_status(
                'investigation',
                f'  Agent {result.agent_name} failed: {result.error[:100] if result.error else "unknown"}',
            )
            continue

        # Try multiple keys that agents might use for findings
        agent_findings = []
        for key in ['issues', 'findings', 'problems', 'concerns', 'results']:
            if key in result.data and isinstance(result.data[key], list):
                agent_findings = result.data[key]
                break

        # If no standard key found, check if data itself is a list
        if not agent_findings and isinstance(result.data, list):
            agent_findings = result.data

        if agent_findings:
            ctx.log_status(
                'investigation',
                f'  Agent {result.agent_name}: {len(agent_findings)} findings',
            )
            for finding in agent_findings:
                if isinstance(finding, dict):
                    finding['source_agent'] = result.agent_name
                    findings.append(finding)
                elif isinstance(finding, str):
                    # Convert string findings to dict
                    findings.append(
                        {
                            'issue': finding,
                            'source_agent': result.agent_name,
                            'severity': 'medium',
                        }
                    )
        else:
            ctx.log_status(
                'investigation',
                f'  Agent {result.agent_name}: 0 findings (keys: {list(result.data.keys()) if isinstance(result.data, dict) else "N/A"})',
            )

    ctx.findings.extend(findings)
    ctx.log_status(
        'investigation', f'Found {len(findings)} findings from first round'
    )

    # Step 4: Second round (cross-pollination) for medium+ risk
    if ctx.config.should_run_second_round(ctx.risk_level):
        ctx.log_status(
            'investigation', 'Running second round (cross-pollination)'
        )

        # Synthesize what we found
        synthesis = _synthesize_findings_for_second_round(ctx, findings)

        # Run second-round agents based on synthesis
        second_round_findings = _run_second_round(ctx, synthesis)

        ctx.findings.extend(second_round_findings)
        ctx.log_status(
            'investigation',
            f'Found {len(second_round_findings)} additional findings from second round',
        )

    return PhaseResult(
        success=True,
        data={
            'findings_count': len(ctx.findings),
            'findings': ctx.findings,
        },
    )


def _synthesize_findings_for_second_round(
    ctx: PRReviewContext, findings: list[dict[str, Any]]
) -> dict[str, Any]:
    """Synthesize first-round findings to guide second round.

    Args:
        ctx: PR review context
        findings: Findings from first round

    Returns:
        Synthesis with patterns, gaps, interactions
    """
    if not ctx.runner:
        return {}

    findings_summary = '\n'.join(
        f'- [{f.get("severity", "unknown")}] {f.get("issue", "N/A")} (from {f.get("source_agent", "unknown")})'
        for f in findings[:20]  # Limit to first 20 for summary
    )

    result = ctx.runner.run(
        'investigator',
        f"""Synthesize first-round findings to identify gaps and interactions.

First-round findings ({len(findings)} total):
{findings_summary}

Files reviewed:
{chr(10).join(f'- {f}' for f in ctx.diff_files)}

Analysis:
1. What patterns emerged across findings?
2. What areas did NO agent examine?
3. Do any findings interact or compound?
4. Are there blind spots in the review?

**IMPORTANT: Return JSON with this structure:**
```json
{{
  "patterns": ["pattern1", "pattern2"],
  "gaps": ["area not examined 1", "area not examined 2"],
  "interactions": ["finding X compounds with finding Y"],
  "needs_investigation": ["specific area to look deeper"]
}}
```
Return ONLY valid JSON. Include at least empty arrays for all keys.
""",
        context={
            'findings': findings,
            'diff_files': ctx.diff_files,
        },
    )

    if not result.success:
        LOG.warning(f'Synthesis failed: {result.error}')
        return {}

    return result.data


def _run_second_round(
    ctx: PRReviewContext, synthesis: dict[str, Any]
) -> list[dict[str, Any]]:
    """Run second-round investigators based on synthesis.

    Args:
        ctx: PR review context
        synthesis: Synthesis from first round

    Returns:
        Additional findings
    """
    if not ctx.runner:
        return []

    gaps = synthesis.get('gaps', [])
    interactions = synthesis.get('interactions', [])

    # Log what we got from synthesis
    ctx.log_status(
        'investigation',
        f'Synthesis returned: patterns={len(synthesis.get("patterns", []))}, '
        f'gaps={len(gaps)}, interactions={len(interactions)}',
    )

    if not gaps and not interactions:
        ctx.log_status(
            'investigation', 'No gaps or interactions, skipping second round'
        )
        return []

    # Run targeted investigators
    findings: list[dict[str, Any]] = []

    # Blind spot hunter
    if gaps:
        ctx.log_status('investigation', f'Investigating {len(gaps)} gaps')
        result = ctx.runner.run(
            'investigator',
            f"""Investigate areas not covered in first review round.

Gaps identified:
{gaps}

Files:
{ctx.diff_files}

Examine these areas and report any issues found.
""",
            context={
                'gaps': gaps,
                'diff_files': ctx.diff_files,
                'work_dir': str(ctx.worktree_path),
            },
        )

        if result.success and 'issues' in result.data:
            for issue in result.data['issues']:
                issue['source_agent'] = 'blind-spot-hunter'
                findings.append(issue)

    # Interaction investigator
    if interactions:
        ctx.log_status(
            'investigation', f'Investigating {len(interactions)} interactions'
        )
        result = ctx.runner.run(
            'investigator',
            f"""Investigate findings that might interact or compound.

Interactions identified:
{interactions}

Determine if these findings compound each other or create additional risks.
""",
            context={
                'interactions': interactions,
                'diff_files': ctx.diff_files,
            },
        )

        if result.success and 'issues' in result.data:
            for issue in result.data['issues']:
                issue['source_agent'] = 'interaction-investigator'
                findings.append(issue)

    return findings


# =============================================================================
# PHASE 3: VALIDATION
# =============================================================================


def phase_validation(ctx: PRReviewContext) -> PhaseResult:
    """Validate findings and filter false positives.

    Steps:
    1. Get validators for risk level
    2. Run validators in parallel on all findings
    3. Collect validation results (CONFIRMED/FALSE_POSITIVE/UPGRADED/DOWNGRADED)
    4. Run council vote for disputes (if needed)

    Args:
        ctx: PR review context

    Returns:
        PhaseResult with validated findings
    """
    ctx.log_status('validation', 'Starting validation phase')

    if not ctx.findings:
        ctx.log_status('validation', 'No findings to validate')
        return PhaseResult(success=True, data={'validated_findings': []})

    if not ctx.runner:
        return PhaseResult(success=False, error='No agent runner configured')

    # Step 1: Get validators for risk level
    validator_names = ctx.config.get_validators_for_risk(ctx.risk_level)
    ctx.log_status('validation', f'Running {len(validator_names)} validators')

    # Step 2: Run validators in parallel
    findings_summary = json.dumps(ctx.findings, indent=2)

    tasks = []
    for validator in validator_names:
        prompt = f"""Validate the following findings from PR review.

Findings to validate ({len(ctx.findings)} total):
{findings_summary}

For each finding:
1. Verify it's a real issue (not false positive)
2. Confirm severity is appropriate
3. Check if it's in scope (in diff, not pre-existing)
4. Provide reasoning

Return validation results:
- finding_id: Index or identifier
- verdict: CONFIRMED / FALSE_POSITIVE / UPGRADE / DOWNGRADE
- reasoning: Why this verdict
- recommended_severity: If upgrade/downgrade
"""

        tasks.append(
            (
                validator,
                prompt,
                {
                    'findings': ctx.findings,
                    'work_dir': str(ctx.worktree_path),
                },
            )
        )

    results = ctx.runner.run_parallel(tasks)

    # Step 3: Collect validation results
    validation_results: dict[int, list[dict[str, Any]]] = {}

    for result in results:
        if result.success and 'validations' in result.data:
            for validation in result.data['validations']:
                finding_id = validation.get('finding_id', -1)
                if finding_id not in validation_results:
                    validation_results[finding_id] = []
                validation_results[finding_id].append(validation)

    # Step 4: Consolidate verdicts
    validated_findings: list[dict[str, Any]] = []
    false_positives: list[dict[str, Any]] = []
    disputed: list[tuple[int, dict[str, Any]]] = []

    for idx, finding in enumerate(ctx.findings):
        validations = validation_results.get(idx, [])

        if not validations:
            # No validation results, keep as-is
            validated_findings.append(finding)
            continue

        # Tally verdicts
        verdicts = [v.get('verdict', 'CONFIRMED') for v in validations]
        verdict_counts = {v: verdicts.count(v) for v in set(verdicts)}

        # Check for consensus (2/3 threshold)
        consensus_needed = max(
            2, int(len(verdicts) * ctx.config.voting_threshold)
        )
        consensus_verdict = None

        for verdict, count in verdict_counts.items():
            if count >= consensus_needed:
                consensus_verdict = verdict
                break

        if consensus_verdict == 'FALSE_POSITIVE':
            false_positives.append(finding)
        elif consensus_verdict in ('CONFIRMED', 'UPGRADE', 'DOWNGRADE'):
            # Apply severity changes if needed
            if consensus_verdict == 'UPGRADE':
                # Find recommended severity
                for v in validations:
                    if v.get('verdict') == 'UPGRADE':
                        finding['severity'] = v.get(
                            'recommended_severity', finding.get('severity')
                        )
                        finding['severity_upgraded'] = True
                        break

            elif consensus_verdict == 'DOWNGRADE':
                for v in validations:
                    if v.get('verdict') == 'DOWNGRADE':
                        finding['severity'] = v.get(
                            'recommended_severity', finding.get('severity')
                        )
                        finding['severity_downgraded'] = True
                        break

            validated_findings.append(finding)
        else:
            # No consensus - disputed
            disputed.append((idx, finding))

    ctx.log_status(
        'validation',
        f'Validated: {len(validated_findings)}, False positives: {len(false_positives)}, Disputed: {len(disputed)}',
    )

    # Step 5: Council vote for disputed (high risk only)
    if disputed and ctx.risk_level == RiskLevel.HIGH:
        ctx.log_status(
            'validation',
            f'Running council vote for {len(disputed)} disputed findings',
        )

        for idx, finding in disputed:
            outcome = _run_council_vote(
                ctx, finding, validation_results.get(idx, [])
            )

            if outcome and outcome.winner == 'REAL_ISSUE':
                validated_findings.append(finding)
            elif outcome and outcome.winner == 'FALSE_POSITIVE':
                false_positives.append(finding)
            else:
                # Needs user decision or NEEDS_MORE_INFO
                ctx.log_status('validation', f'Finding {idx} escalated to user')
                # For now, keep as validated
                validated_findings.append(finding)

    ctx.validated_findings = validated_findings
    ctx.false_positives = false_positives

    return PhaseResult(
        success=True,
        data={
            'validated_findings': len(validated_findings),
            'false_positives': len(false_positives),
            'disputed': len(disputed),
        },
    )


def _run_council_vote(
    ctx: PRReviewContext,
    finding: dict[str, Any],
    validations: list[dict[str, Any]],
) -> VotingOutcome | None:
    """Run council vote for disputed finding.

    Args:
        ctx: PR review context
        finding: The disputed finding
        validations: Validation results from validators

    Returns:
        VotingOutcome or None if voting fails
    """
    if not ctx.runner:
        return None

    validations_summary = '\n'.join(
        f'- {v.get("verdict")}: {v.get("reasoning", "N/A")}'
        for v in validations
    )

    outcome = run_voting_gate(
        runner=ctx.runner,
        gate_name='council_finding_dispute',
        num_voters=3,
        prompt=f"""Vote on disputed finding.

Finding:
{json.dumps(finding, indent=2)}

Validator opinions:
{validations_summary}

Vote:
- REAL_ISSUE: This is a legitimate issue
- FALSE_POSITIVE: This is not a real issue
- NEEDS_MORE_INFO: Cannot determine without more investigation

Cast your vote with reasoning.
""",
        options=['REAL_ISSUE', 'FALSE_POSITIVE', 'NEEDS_MORE_INFO'],
        schema='',
        voter_agent='investigator',
    )

    return outcome


# =============================================================================
# PHASE 4: SYNTHESIS
# =============================================================================


def phase_synthesis(ctx: PRReviewContext) -> PhaseResult:
    """Consolidate findings and classify MR threads.

    Steps:
    1. Deduplicate and group findings
    2. Classify MR threads (ADDRESSED/DISMISSED/OUTSTANDING/PLANNED_FOLLOWUP)
    3. Identify severity upgrades and flag prominently

    Args:
        ctx: PR review context

    Returns:
        PhaseResult with consolidated findings
    """
    ctx.log_status('synthesis', 'Starting synthesis phase')

    if not ctx.validated_findings:
        ctx.log_status('synthesis', 'No findings to synthesize')
        return PhaseResult(success=True, data={'consolidated_findings': []})

    # Step 1: Deduplicate and group
    ctx.log_status(
        'synthesis', f'Deduplicating {len(ctx.validated_findings)} findings'
    )

    # Simple deduplication by issue text
    seen = set()
    deduplicated: list[dict[str, Any]] = []

    for finding in ctx.validated_findings:
        issue_key = (
            finding.get('file', ''),
            finding.get('issue', '').lower().strip(),
        )

        if issue_key not in seen:
            seen.add(issue_key)
            deduplicated.append(finding)

    ctx.log_status(
        'synthesis', f'Deduplicated to {len(deduplicated)} unique findings'
    )

    # Step 2: Classify MR threads
    # In real implementation, would query GitLab API for MR discussions
    # For now, skip this step
    ctx.log_status('synthesis', 'MR thread classification (placeholder)')

    # Step 3: Group by severity
    by_severity: dict[str, list[dict[str, Any]]] = {
        'critical': [],
        'major': [],
        'minor': [],
    }

    for finding in deduplicated:
        severity = finding.get('severity', 'minor').lower()
        if severity in by_severity:
            by_severity[severity].append(finding)

    ctx.log_status(
        'synthesis',
        f'Grouped: {len(by_severity["critical"])} critical, {len(by_severity["major"])} major, {len(by_severity["minor"])} minor',
    )

    return PhaseResult(
        success=True,
        data={
            'consolidated_findings': deduplicated,
            'by_severity': by_severity,
        },
    )


# =============================================================================
# PHASE 5: REPORT
# =============================================================================


def phase_report(ctx: PRReviewContext) -> PhaseResult:
    """Generate final report and cleanup.

    Steps:
    1. Generate report from template
    2. Write report to file
    3. Cleanup worktree

    Args:
        ctx: PR review context

    Returns:
        PhaseResult with report path
    """
    ctx.log_status('report', 'Starting report phase')

    # Step 1: Generate report
    report_content = _generate_report(ctx)

    # Step 2: Write report
    report_path = ctx.work_dir / f'pr_review_{ctx.ticket_id}.md'
    report_path.write_text(report_content)

    ctx.log_status('report', f'Report written to {report_path}')

    # Step 3: Cleanup worktree
    # In real implementation, would cleanup worktree
    ctx.log_status('report', 'Cleanup (placeholder)')

    return PhaseResult(
        success=True,
        data={
            'report_path': str(report_path),
        },
    )


def _generate_report(ctx: PRReviewContext) -> str:
    """Generate report content.

    Args:
        ctx: PR review context

    Returns:
        Report markdown content
    """
    # Group findings by severity
    by_severity: dict[str, list[dict[str, Any]]] = {
        'critical': [],
        'major': [],
        'minor': [],
    }

    for finding in ctx.validated_findings:
        severity = finding.get('severity', 'minor').lower()
        if severity in by_severity:
            by_severity[severity].append(finding)

    # Build report
    lines = [
        f'# PR Review Report: {ctx.ticket_id}',
        '',
        '## Summary',
        '',
        f'- **Risk Level**: {ctx.risk_level.value}',
        f'- **Files Changed**: {len(ctx.diff_files)}',
        f'- **Critical Findings**: {len(by_severity["critical"])}',
        f'- **Major Findings**: {len(by_severity["major"])}',
        f'- **Minor Findings**: {len(by_severity["minor"])}',
        f'- **False Positives Filtered**: {len(ctx.false_positives)}',
        '',
        '## Recommendation',
        '',
    ]

    # Recommendation based on findings
    if by_severity['critical']:
        lines.append(
            '**❌ BLOCK** - Critical issues must be resolved before merge.'
        )
    elif by_severity['major']:
        lines.append('**⚠️  CAUTION** - Major issues should be addressed.')
    else:
        lines.append('**✅ APPROVE** - No blocking issues found.')

    lines.extend(['', '---', ''])

    # Critical findings
    if by_severity['critical']:
        lines.extend(['## Critical Findings', ''])
        for idx, finding in enumerate(by_severity['critical'], 1):
            lines.extend(
                [
                    f'### {idx}. {finding.get("issue", "Unknown issue")}',
                    '',
                    f'**File**: `{finding.get("file", "N/A")}`',
                    f'**Line**: {finding.get("line", "N/A")}',
                    '',
                    f'**Issue**: {finding.get("issue", "N/A")}',
                    '',
                    f'**Fix**: {finding.get("fix", "N/A")}',
                    '',
                    f'**Source**: {finding.get("source_agent", "unknown")}',
                    '',
                ]
            )

    # Major findings
    if by_severity['major']:
        lines.extend(['## Major Findings', ''])
        for idx, finding in enumerate(by_severity['major'], 1):
            lines.extend(
                [
                    f'### {idx}. {finding.get("issue", "Unknown issue")}',
                    '',
                    f'**File**: `{finding.get("file", "N/A")}`',
                    f'**Line**: {finding.get("line", "N/A")}',
                    '',
                    f'**Issue**: {finding.get("issue", "N/A")}',
                    '',
                    f'**Fix**: {finding.get("fix", "N/A")}',
                    '',
                    f'**Source**: {finding.get("source_agent", "unknown")}',
                    '',
                ]
            )

    # Minor findings (collapsed)
    if by_severity['minor']:
        lines.extend(
            [
                '## Minor Findings',
                '',
                '<details>',
                '<summary>Click to expand</summary>',
                '',
            ]
        )
        for idx, finding in enumerate(by_severity['minor'], 1):
            lines.extend(
                [
                    f'### {idx}. {finding.get("issue", "Unknown issue")}',
                    '',
                    f'**File**: `{finding.get("file", "N/A")}`',
                    '',
                ]
            )
        lines.extend(['</details>', ''])

    # Discoveries
    if ctx.discoveries:
        lines.extend(['## Discoveries', ''])
        for discovery in ctx.discoveries:
            lines.append(f'- {discovery}')
        lines.append('')

    # False positives
    if ctx.false_positives:
        lines.extend(
            [
                '## False Positives Filtered',
                '',
                f'Filtered {len(ctx.false_positives)} false positives during validation.',
                '',
            ]
        )

    lines.extend(
        [
            '---',
            '',
            f'Generated by PR Review Workflow v{ctx.config.version}',
        ]
    )

    return '\n'.join(lines)


# =============================================================================
# WORKFLOW FACTORY
# =============================================================================


def create_pr_review_workflow(
    ticket_id: str,
    source_branch: str,
    target_branch: str,
    work_dir: Path,
    config: PRReviewConfig | None = None,
    runner: AgentRunner | None = None,
) -> tuple[PRReviewContext, dict[str, Any]]:
    """Create PR review workflow context and phase handlers.

    Args:
        ticket_id: Ticket/issue identifier
        source_branch: Source branch being reviewed
        target_branch: Target branch (e.g., develop, main)
        work_dir: Working directory for review
        config: Custom PR review config (defaults to generic)
        runner: Agent runner instance

    Returns:
        Tuple of (context, phase_handlers)
    """
    if config is None:
        config = create_default_config()

    ctx = PRReviewContext(
        ticket_id=ticket_id,
        source_branch=source_branch,
        target_branch=target_branch,
        work_dir=work_dir,
        config=config,
        runner=runner,
    )

    phase_handlers = {
        'triage': lambda: phase_triage(ctx),
        'investigation': lambda: phase_investigation(ctx),
        'validation': lambda: phase_validation(ctx),
        'synthesis': lambda: phase_synthesis(ctx),
        'report': lambda: phase_report(ctx),
    }

    return ctx, phase_handlers
