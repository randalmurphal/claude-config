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
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from cc_orchestrations.core.agents import AgentLoader
from cc_orchestrations.core.extensions import (
    detect_project_extensions,
    get_extension_pr_review_prompt,
    has_extension_prompt,
)
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
from .prompts import (
    JSON_OUTPUT_INSTRUCTIONS,
    WORKTREE_INSTRUCTIONS,
    build_prompt,
    load_prompt,
)

LOG = logging.getLogger(__name__)

# Agent loader - loads prompts from .claude/agents/*.md files (fallback)
# Primary source is now extension prompts
_agent_loader: AgentLoader | None = None

# Detected extensions for the current session
_detected_extensions: list[str] | None = None


def _get_agent_loader(project_dir: Path | None = None) -> AgentLoader:
    """Get or create the agent loader.

    Args:
        project_dir: Project root directory

    Returns:
        AgentLoader instance
    """
    global _agent_loader
    if _agent_loader is None:
        _agent_loader = AgentLoader(project_dir=project_dir)
    return _agent_loader


def _get_extensions(project_dir: Path | None = None) -> list[str]:
    """Get detected extensions for the current project.

    Args:
        project_dir: Project root directory

    Returns:
        List of extension names
    """
    global _detected_extensions
    if _detected_extensions is None and project_dir:
        _detected_extensions = detect_project_extensions(project_dir)
        LOG.info(f'Detected extensions: {_detected_extensions}')
    return _detected_extensions or []


def _load_agent_prompt(
    agent_name: str, project_dir: Path | None = None, **kwargs: Any
) -> str:
    """Load an agent's prompt, preferring extension prompts over .claude/agents/.

    Load order:
    1. Extension prompts (e.g., cc_orchestrations_m32rimm.pr_review.prompts)
    2. Fallback to .claude/agents/<agent_name>.md in project directory

    Args:
        agent_name: Agent name (e.g., 'finding-validator', 'conclusion-validator')
        project_dir: Project root directory
        **kwargs: Format parameters to substitute in the prompt

    Returns:
        Formatted prompt string, or empty if agent not found
    """
    template = ''

    # Try extension prompts first
    extensions = _get_extensions(project_dir)
    for ext_name in extensions:
        if has_extension_prompt(ext_name, agent_name):
            template = get_extension_pr_review_prompt(ext_name, agent_name)
            if template:
                LOG.debug(
                    f'Loaded prompt for {agent_name} from extension {ext_name}'
                )
                break

    # Fallback to AgentLoader (.claude/agents/*.md)
    if not template:
        global _agent_loader
        if project_dir and (
            _agent_loader is None or _agent_loader.project_agents_dir is None
        ):
            _agent_loader = AgentLoader(project_dir=project_dir)
        loader = _get_agent_loader(project_dir)
        agent = loader.get(agent_name)

        if agent:
            template = agent.prompt
            LOG.debug(f'Loaded prompt for {agent_name} from AgentLoader')
        else:
            LOG.warning(f'Agent not found: {agent_name}')
            return ''

    # Format with provided kwargs, leaving missing placeholders as-is
    if kwargs and template:
        try:
            return template.format(**kwargs)
        except KeyError:
            # Some placeholders not provided - use safe formatting
            for key, value in kwargs.items():
                template = template.replace('{' + key + '}', str(value))

    return template


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
    severity_upgraded: list[dict[str, Any]] = field(default_factory=list)

    # MR threads
    mr_threads: dict[str, Any] = field(default_factory=dict)
    mr_discussions_raw: str = ''  # Raw discussions from GitLab

    # Discoveries
    discoveries: list[str] = field(default_factory=list)

    # Agents selected during triage
    agents_to_run: list[Any] = field(default_factory=list)

    # Review stats
    review_stats: dict[str, Any] = field(default_factory=dict)

    # Optional Jira context for requirements validation (raw text from Jira script)
    jira_context: str | None = None

    def log_status(self, phase: str, message: str) -> None:
        """Log phase status with timestamp."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        LOG.info(f'[{timestamp}] [{phase}] {message}')
        print(f'[{timestamp}] [{phase}] {message}')

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

    # Step 3: Assess risk AND select reviewers - SINGLE INVESTIGATION
    ctx.log_status(
        'triage',
        'Assessing blast radius and selecting reviewers (investigating code)',
    )

    # Determine worktree paths
    pr_worktree = (
        str(ctx.worktree_path) if ctx.worktree_path else str(ctx.work_dir)
    )
    base_worktree = (
        str(ctx.worktree_path).replace('/pr/', '/base/')
        if ctx.worktree_path
        else str(ctx.work_dir)
    )

    # Get all available agent names and descriptions for selection
    available_agents = [
        {'name': a.name, 'description': a.description, 'required': a.required}
        for a in ctx.config.agents
    ]

    # Build triage prompt from file + dynamic context
    triage_prompt = build_prompt(
        # Worktree instructions
        WORKTREE_INSTRUCTIONS.format(
            pr_worktree=pr_worktree,
            base_worktree=base_worktree,
        ),
        # Changed files
        f'## Changed Files ({len(ctx.diff_files)})',
        '\n'.join(f'- {f}' for f in ctx.diff_files),
        # Available reviewers
        '## Available Reviewers',
        '\n'.join(
            f'- **{a["name"]}**: {a["description"]} (required: {a["required"]})'
            for a in available_agents
        ),
        # Core triage instructions from file
        load_prompt('triage'),
    )

    if not ctx.runner:
        return PhaseResult(success=False, error='No runner configured')

    risk_result = ctx.runner.run(
        'investigator',
        triage_prompt,
        context={
            'diff_files': ctx.diff_files,
            'diff_summary': ctx.diff_summary,
            'file_count': len(ctx.diff_files),
            'work_dir': pr_worktree,
        },
        model_override='opus',  # Use Opus for risk + agent selection
    )

    # Initialize for fallback
    selected_agent_names: set[str] = set()

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

        # Extract agent selection from same result
        agent_names = risk_result.get('agents_to_run', [])
        if isinstance(agent_names, list):
            selected_agent_names = set(agent_names)
            agent_reasoning = risk_result.get('agent_selection_reasoning', '')
            if agent_reasoning:
                ctx.add_discovery(f'Agent selection: {agent_reasoning}')

    ctx.log_status('triage', f'Risk level: {ctx.risk_level.value}')

    # Step 4: Build agent list from investigation results
    # (agent selection was already done in Step 3 blast radius investigation)
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

    # Step 2: Run agents in parallel with proper model and skills
    # Determine worktree paths for all agents
    pr_worktree = (
        str(ctx.worktree_path) if ctx.worktree_path else str(ctx.work_dir)
    )
    base_worktree = (
        pr_worktree.replace('/pr/', '/base/')
        if '/pr/' in pr_worktree
        else pr_worktree
    )

    # Use shared instructions from prompts module
    worktree_instructions = WORKTREE_INSTRUCTIONS.format(
        pr_worktree=pr_worktree,
        base_worktree=base_worktree,
    )
    json_output_instructions = JSON_OUTPUT_INSTRUCTIONS

    tasks = []
    for agent in agents_to_run:
        # Format prompt with context using safe substitution
        # (agent prompts contain JSON examples with {} that aren't placeholders)
        prompt = agent.prompt_template
        substitutions = {
            '{ticket_id}': ctx.ticket_id,
            '{requirements}': ctx.requirements,
            '{diff_files}': '\n'.join(ctx.diff_files),
            '{test_files}': '\n'.join(ctx.test_files),
            '{file_count}': str(len(ctx.diff_files)),
        }
        for placeholder, value in substitutions.items():
            prompt = prompt.replace(placeholder, value)

        # Prepend worktree instructions, append JSON output instructions
        prompt = worktree_instructions + prompt + json_output_instructions

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

    # Log actual count after building tasks
    ctx.log_status(
        'investigation',
        f'Running {len(tasks)} first-round agents: {", ".join(t["name"] for t in tasks)}',
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

    # Track stats
    ctx.review_stats['first_round_findings'] = len(findings)
    ctx.review_stats['agents_run'] = len(agents_to_run)

    # Step 4: Second round (cross-pollination) - always run if there are findings
    if findings:
        ctx.log_status(
            'investigation',
            f'Running second round (cross-pollination) - {len(findings)} findings to analyze',
        )

        # Synthesize what we found
        synthesis = _synthesize_findings_for_second_round(ctx, findings)

        # Run second-round agents based on synthesis
        second_round_findings = _run_second_round(ctx, synthesis, findings)

        ctx.findings.extend(second_round_findings)
        ctx.review_stats['second_round_findings'] = len(second_round_findings)
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
  "needs_investigation": ["specific area to look deeper"],
  "high_severity_to_revalidate": [0, 3]
}}
```
Return ONLY valid JSON. Include at least empty arrays for all keys.
Include indices of CRITICAL/HIGH findings that should be re-evaluated with full context.
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
    ctx: PRReviewContext,
    synthesis: dict[str, Any],
    first_round_findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run second-round investigators in PARALLEL.

    Always runs all three if there are findings:
    - Blind spot hunter (coverage gaps)
    - Interaction investigator (compounding issues)
    - Conclusion validator (high-severity re-evaluation)

    Args:
        ctx: PR review context
        synthesis: Synthesis from first round
        first_round_findings: All findings from first round

    Returns:
        Additional findings
    """
    if not ctx.runner or not first_round_findings:
        return []

    gaps = synthesis.get('gaps', [])
    interactions = synthesis.get('interactions', [])
    high_severity_indices = synthesis.get('high_severity_to_revalidate', [])

    # Log what we got from synthesis
    ctx.log_status(
        'investigation',
        f'Synthesis: {len(synthesis.get("patterns", []))} patterns, '
        f'{len(gaps)} gaps, {len(interactions)} interactions',
    )

    # Get high-severity findings for conclusion-validator
    high_severity_findings = [
        f
        for i, f in enumerate(first_round_findings)
        if i in high_severity_indices
        or f.get('severity', '').lower() in ('critical', 'high')
    ]

    # Worktree paths for all second-round agents
    pr_worktree = (
        str(ctx.worktree_path) if ctx.worktree_path else str(ctx.work_dir)
    )
    base_worktree = (
        pr_worktree.replace('/pr/', '/base/')
        if '/pr/' in pr_worktree
        else pr_worktree
    )

    # Use shared instructions from prompts module
    worktree_header = WORKTREE_INSTRUCTIONS.format(
        pr_worktree=pr_worktree,
        base_worktree=base_worktree,
    )

    # Build tasks for parallel execution - always run all three
    tasks = []

    # 1. Blind spot hunter
    blind_spot_prompt = worktree_header + _load_agent_prompt(
        'blind-spot-hunter', project_dir=ctx.work_dir
    )

    # Build findings summary outside f-string to avoid {{ escaping issues
    findings_summary = [
        {
            'severity': f.get('severity'),
            'issue': f.get('issue'),
            'file': f.get('file'),
        }
        for f in first_round_findings[:20]
    ]
    blind_spot_prompt += f"""

## First-Round Findings Summary

{json.dumps(findings_summary, indent=2)}

## Gaps Identified by Synthesis

{json.dumps(gaps, indent=2) if gaps else 'No specific gaps identified - look for what reviewers missed'}

## Changed Files

{chr(10).join(ctx.diff_files)}
"""
    tasks.append(
        {
            'name': 'blind-spot-hunter',
            'prompt': blind_spot_prompt,
            'context': {
                'gaps': gaps,
                'findings': first_round_findings,
                'diff_files': ctx.diff_files,
                'work_dir': str(ctx.worktree_path),
            },
            'model': 'opus',
        }
    )

    # 2. Interaction investigator
    interaction_prompt = worktree_header + _load_agent_prompt(
        'interaction-investigator', project_dir=ctx.work_dir
    )
    interaction_prompt += f"""

## All First-Round Findings

{json.dumps(first_round_findings[:20], indent=2)}

## Potential Interactions Identified

{json.dumps(interactions, indent=2) if interactions else 'No specific interactions identified - look for compounding issues'}

## Changed Files

{chr(10).join(ctx.diff_files)}
"""
    tasks.append(
        {
            'name': 'interaction-investigator',
            'prompt': interaction_prompt,
            'context': {
                'interactions': interactions,
                'findings': first_round_findings,
                'diff_files': ctx.diff_files,
            },
            'model': 'opus',
        }
    )

    # 3. Conclusion validator
    conclusion_prompt = worktree_header + _load_agent_prompt(
        'conclusion-validator', project_dir=ctx.work_dir
    )
    conclusion_prompt += f"""

## Findings to Re-evaluate

{json.dumps(first_round_findings, indent=2)}

## High-Severity Findings (prioritize these)

{json.dumps(high_severity_findings, indent=2) if high_severity_findings else 'No high-severity findings identified'}

## Changed Files

{chr(10).join(ctx.diff_files)}

## MR Discussion Summary

{ctx.mr_discussions_raw or 'No MR discussions available'}
"""
    tasks.append(
        {
            'name': 'conclusion-validator',
            'prompt': conclusion_prompt,
            'context': {
                'findings': first_round_findings,
                'high_severity_findings': high_severity_findings,
                'diff_files': ctx.diff_files,
                'work_dir': str(ctx.worktree_path),
            },
            'model': 'opus',
        }
    )

    ctx.log_status(
        'investigation', f'Running {len(tasks)} second-round agents in parallel'
    )

    # Run all in parallel
    results = ctx.runner.run_parallel(tasks)

    # Collect findings from results
    findings: list[dict[str, Any]] = []

    for result in results:
        if not result.success:
            ctx.log_status(
                'investigation',
                f'  {result.agent_name}: failed - {result.error[:50] if result.error else "unknown"}',
            )
            continue

        # Handle blind-spot-hunter and interaction-investigator findings
        if result.agent_name in (
            'blind-spot-hunter',
            'interaction-investigator',
        ):
            agent_findings = result.data.get(
                'issues', result.data.get('findings', [])
            )
            ctx.log_status(
                'investigation',
                f'  {result.agent_name}: {len(agent_findings)} findings',
            )
            for issue in agent_findings:
                if isinstance(issue, dict):
                    issue['source_agent'] = result.agent_name
                    findings.append(issue)

        # Handle conclusion-validator (modifies existing findings)
        elif result.agent_name == 'conclusion-validator':
            revalidations = result.data.get(
                'revalidated_findings', result.data.get('reevaluations', [])
            )
            ctx.log_status(
                'investigation',
                f'  conclusion-validator: {len(revalidations)} re-evaluations',
            )
            for revalidation in revalidations:
                finding_id = revalidation.get('finding_id', -1)
                verdict = revalidation.get(
                    'verdict', revalidation.get('new_assessment', 'CONFIRMED')
                ).upper()
                new_severity = revalidation.get('new_severity', '')

                if 0 <= finding_id < len(first_round_findings):
                    original = first_round_findings[finding_id]
                    if verdict == 'FALSE_POSITIVE':
                        original['conclusion_validator_verdict'] = (
                            'FALSE_POSITIVE'
                        )
                        original['conclusion_validator_reason'] = (
                            revalidation.get('reasoning', '')
                        )
                    elif (
                        verdict in ('DOWNGRADE', 'DOWNGRADED') and new_severity
                    ):
                        original['severity'] = new_severity
                        original['severity_downgraded'] = True
                        original['downgrade_reason'] = revalidation.get(
                            'reasoning', ''
                        )
                    elif verdict in ('UPGRADE', 'UPGRADED') and new_severity:
                        original['original_severity'] = original.get('severity')
                        original['severity'] = new_severity
                        original['severity_upgraded'] = True

    # Run mini-consolidation to catch cross-agent interactions
    if findings and ctx.runner:
        ctx.log_status('investigation', 'Running Round 2 consolidation')
        consolidation_findings = _consolidate_round2_findings(
            ctx, findings, results
        )
        if consolidation_findings:
            ctx.log_status(
                'investigation',
                f'Consolidation found {len(consolidation_findings)} compound/contradictory findings',
            )
            findings.extend(consolidation_findings)

    return findings


def _consolidate_round2_findings(
    ctx: PRReviewContext,
    round2_findings: list[dict[str, Any]],
    round2_results: list,  # list[AgentResult] but avoiding import
) -> list[dict[str, Any]]:
    """Quick consolidation pass over Round 2 findings.

    Looks for:
    - Contradictions between Round 2 agents
    - Findings that compound when combined
    - Gaps both blind-spot-hunter AND interaction-investigator missed

    Args:
        ctx: PR review context
        round2_findings: Findings from Round 2 agents
        round2_results: Raw results from Round 2 agents

    Returns:
        Additional findings from consolidation
    """
    if not ctx.runner or not round2_findings:
        return []

    # Build summary of what each agent found
    agent_summaries = {}
    for result in round2_results:
        if result.success:
            agent_summaries[result.agent_name] = {
                'findings_count': len(
                    result.data.get('issues', result.data.get('findings', []))
                ),
                'areas_checked': result.data.get('areas_checked', []),
                'key_concerns': [
                    f.get('issue', '')[:100]
                    for f in result.data.get(
                        'issues', result.data.get('findings', [])
                    )[:3]
                ],
            }

    # Limit findings summary to prevent prompt bloat
    findings_summary = [
        {
            'id': i,
            'severity': f.get('severity', 'unknown'),
            'issue': f.get('issue', '')[:150],
            'file': f.get('file', ''),
            'source': f.get('source_agent', 'unknown'),
        }
        for i, f in enumerate(round2_findings[:15])
    ]

    prompt = f"""Quick consolidation of Round 2 PR review findings.

## Round 2 Agent Summaries

{json.dumps(agent_summaries, indent=2)}

## Round 2 Findings ({len(round2_findings)} total, showing first 15)

{json.dumps(findings_summary, indent=2)}

## Task

Look for:
1. **Contradictions**: Do any agents disagree? (e.g., one says safe, another says risky)
2. **Compound issues**: Do findings combine to create a larger problem?
3. **Gaps**: Did all agents miss something obvious given the file changes?

Return JSON:
{{
    "compound_findings": [
        {{"issue": "Combined effect of X and Y creates Z problem", "compounds": [0, 3], "severity": "high"}}
    ],
    "contradictions": [
        {{"topic": "error handling in foo.py", "positions": ["agent_a: safe", "agent_b: risky"], "resolution": "needs review"}}
    ]
}}

Return empty arrays if nothing found. Be BRIEF - this is a quick sanity check, not a full review.
"""

    result = ctx.runner.run(
        'investigator',
        prompt,
        context={'round2_findings': round2_findings[:15]},
        model_override='sonnet',  # Fast model for quick consolidation
    )

    if not result.success:
        LOG.warning(f'Round 2 consolidation failed: {result.error}')
        return []

    # Extract compound findings as new issues
    new_findings: list[dict[str, Any]] = []

    compounds = result.data.get('compound_findings', [])
    for c in compounds:
        if c.get('issue'):
            new_findings.append(
                {
                    'issue': c.get('issue', ''),
                    'severity': c.get('severity', 'medium'),
                    'source_agent': 'round2-consolidator',
                    'compounds': c.get('compounds', []),
                    'type': 'compound',
                }
            )

    contradictions = result.data.get('contradictions', [])
    for c in contradictions:
        if c.get('topic') and c.get('resolution', '').lower() != 'resolved':
            new_findings.append(
                {
                    'issue': f'Contradiction: {c.get("topic")} - {c.get("resolution", "needs review")}',
                    'severity': 'medium',
                    'source_agent': 'round2-consolidator',
                    'type': 'contradiction',
                    'positions': c.get('positions', []),
                }
            )

    return new_findings


# =============================================================================
# PHASE 3: VALIDATION
# =============================================================================


def phase_validation(ctx: PRReviewContext) -> PhaseResult:
    """Validate findings and filter false positives.

    Steps:
    1. Get validators for risk level
    2. Run SKEPTICAL validators in parallel on all findings
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

    # Filter out findings already marked as false positive by conclusion validator
    findings_to_validate = [
        f
        for f in ctx.findings
        if f.get('conclusion_validator_verdict') != 'FALSE_POSITIVE'
    ]
    pre_filtered = len(ctx.findings) - len(findings_to_validate)
    if pre_filtered:
        ctx.log_status(
            'validation',
            f'Pre-filtered {pre_filtered} findings from conclusion validator',
        )

    # Step 1: Get validators for risk level
    validator_names = ctx.config.get_validators_for_risk(ctx.risk_level)
    ctx.log_status('validation', f'Running {len(validator_names)} validators')

    # Worktree paths for validators
    pr_worktree = (
        str(ctx.worktree_path) if ctx.worktree_path else str(ctx.work_dir)
    )
    base_worktree = (
        pr_worktree.replace('/pr/', '/base/')
        if '/pr/' in pr_worktree
        else pr_worktree
    )

    # Use shared instructions from prompts module
    worktree_header = WORKTREE_INSTRUCTIONS.format(
        pr_worktree=pr_worktree,
        base_worktree=base_worktree,
    )

    # Step 2: Run validators - use finding-validator agent prompt
    findings_summary = json.dumps(findings_to_validate, indent=2)

    tasks = []
    for validator in validator_names:
        # Load the agent-specific prompt (finding-validator, adversarial-reviewer, etc.)
        base_prompt = _load_agent_prompt(validator, project_dir=ctx.work_dir)
        if not base_prompt:
            # Fallback for unknown validators
            base_prompt = f'You are {validator}. Validate findings thoroughly.'

        # Add worktree header
        base_prompt = worktree_header + base_prompt

        # Append the findings to validate
        prompt = (
            base_prompt
            + f"""

## Findings to Validate ({len(findings_to_validate)} total)

{findings_summary}

## Changed Files

{chr(10).join(ctx.diff_files)}
"""
        )

        tasks.append(
            (
                validator,
                prompt,
                {
                    'findings': findings_to_validate,
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

    for idx, finding in enumerate(findings_to_validate):
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
                        original_severity = finding.get('severity')
                        finding['severity'] = v.get(
                            'recommended_severity', finding.get('severity')
                        )
                        finding['severity_upgraded'] = True
                        finding['original_severity'] = original_severity
                        ctx.severity_upgraded.append(finding)
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

    # Update stats
    ctx.review_stats['validated'] = len(validated_findings)
    ctx.review_stats['false_positives'] = len(false_positives)
    ctx.review_stats['disputed'] = len(disputed)

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

    # Load council reviewer agent prompt
    base_prompt = _load_agent_prompt(
        'council-reviewer', project_dir=ctx.work_dir
    )
    prompt = (
        base_prompt
        + f"""

## Finding to Vote On

{json.dumps(finding, indent=2)}

## Validator Opinions

{validations_summary}
"""
        if base_prompt
        else f"""Vote on disputed finding.

Finding:
{json.dumps(finding, indent=2)}

Validator opinions:
{validations_summary}

Vote:
- REAL_ISSUE: This is a legitimate issue that should be fixed
- FALSE_POSITIVE: This is not a real issue (with proof)
- NEEDS_MORE_INFO: Cannot determine without more investigation

Cast your vote with reasoning. Be SKEPTICAL - if unsure, lean FALSE_POSITIVE.
"""
    )

    # Disputed findings are critical decisions - use thinking model for lead voter
    from cc_orchestrations.core.config import DEFAULT_COUNCIL_MODELS

    voter_models = DEFAULT_COUNCIL_MODELS[:3]  # thinking + opus + gpt-5.1-high

    outcome = run_voting_gate(
        runner=ctx.runner,
        gate_name='council_finding_dispute',
        num_voters=3,
        prompt=prompt,
        options=['REAL_ISSUE', 'FALSE_POSITIVE', 'NEEDS_MORE_INFO'],
        schema='',
        voter_agent='investigator',
        voter_models=voter_models,
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
    if ctx.mr_discussions_raw and ctx.runner:
        ctx.log_status('synthesis', 'Classifying MR threads')

        # MR thread classification is a utility task, not a dedicated agent
        prompt = f"""Classify MR discussion threads by status.

## MR Discussions

{ctx.mr_discussions_raw}

## Classification

For each discussion thread, determine:
- **ADDRESSED**: Issue was fixed in code
- **DISMISSED**: Agreed it's not an issue
- **OUTSTANDING**: Not yet resolved
- **PLANNED_FOLLOWUP**: Will address in separate ticket

Return JSON:
```json
{{
  "thread_classifications": [
    {{
      "thread_id": "...",
      "topic": "Brief topic",
      "status": "ADDRESSED|DISMISSED|OUTSTANDING|PLANNED_FOLLOWUP",
      "evidence": "How you determined this"
    }}
  ],
  "summary": {{
    "addressed": 0,
    "dismissed": 0,
    "outstanding": 0,
    "planned_followup": 0
  }},
  "blocking_threads": ["thread_ids that should block merge"]
}}
```
"""

        result = ctx.runner.run(
            'investigator',
            prompt,
            context={
                'mr_discussions': ctx.mr_discussions_raw,
                'diff_files': ctx.diff_files,
            },
        )

        if result.success and 'thread_classifications' in result.data:
            ctx.mr_threads = result.data
            summary = result.data.get('summary', {})
            ctx.log_status(
                'synthesis',
                f'MR threads: {summary.get("addressed", 0)} addressed, '
                f'{summary.get("outstanding", 0)} outstanding, '
                f'{summary.get("dismissed", 0)} dismissed',
            )
    else:
        ctx.log_status('synthesis', 'No MR discussions to classify')

    # Step 3: Group by severity
    by_severity: dict[str, list[dict[str, Any]]] = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': [],
    }

    for finding in deduplicated:
        severity = finding.get('severity', 'medium').lower()
        if severity in by_severity:
            by_severity[severity].append(finding)
        else:
            by_severity['medium'].append(finding)

    ctx.log_status(
        'synthesis',
        f'Grouped: {len(by_severity["critical"])} critical, '
        f'{len(by_severity["high"])} high, '
        f'{len(by_severity["medium"])} medium, '
        f'{len(by_severity["low"])} low',
    )

    # Store deduplicated findings back
    ctx.validated_findings = deduplicated

    return PhaseResult(
        success=True,
        data={
            'consolidated_findings': deduplicated,
            'by_severity': by_severity,
            'mr_threads': ctx.mr_threads,
        },
    )


# =============================================================================
# PHASE 5: REPORT
# =============================================================================


def phase_report(ctx: PRReviewContext) -> PhaseResult:
    """Generate final report using pr-report-synthesizer agent.

    Steps:
    1. Gather all findings and context
    2. Run pr-report-synthesizer agent to create verified report
    3. Write report to file
    4. Cleanup worktree

    Args:
        ctx: PR review context

    Returns:
        PhaseResult with report path
    """
    ctx.log_status('report', 'Starting report phase')

    if not ctx.runner:
        # Fallback to code-generated report
        ctx.log_status('report', 'No runner - using fallback report generation')
        report_content = _generate_report_fallback(ctx)
    else:
        # Use pr-report-synthesizer agent for intelligent report
        ctx.log_status('report', 'Running pr-report-synthesizer agent')

        # Prepare comprehensive context for the agent
        _prepare_report_context(ctx)

        # Load agent prompt
        agent_prompt = _load_agent_prompt(
            'pr-report-synthesizer', project_dir=ctx.work_dir
        )

        if not agent_prompt:
            ctx.log_status('report', 'Agent not found - using fallback')
            report_content = _generate_report_fallback(ctx)
        else:
            # Worktree paths for report synthesizer
            pr_worktree = (
                str(ctx.worktree_path)
                if ctx.worktree_path
                else str(ctx.work_dir)
            )
            base_worktree = (
                pr_worktree.replace('/pr/', '/base/')
                if '/pr/' in pr_worktree
                else pr_worktree
            )

            prompt = (
                f"""
---
## WORKTREE ACCESS - VERIFY ALL FINDINGS

- **PR Worktree (code WITH changes):** `{pr_worktree}`
- **Base Worktree (code BEFORE changes):** `{base_worktree}`

You MUST verify critical/high findings by reading the actual code. Check that file paths and line numbers are correct before including in the report.

---
"""
                + agent_prompt
                + f"""

## Review Data

### Ticket
{ctx.ticket_id}

### Changed Files ({len(ctx.diff_files)})
{chr(10).join(f'- {f}' for f in ctx.diff_files)}

### All Validated Findings ({len(ctx.validated_findings)})
{json.dumps(ctx.validated_findings, indent=2)}

### False Positives Filtered ({len(ctx.false_positives)})
{json.dumps(ctx.false_positives[:10], indent=2) if ctx.false_positives else '[]'}

### Severity Upgrades
{json.dumps(ctx.severity_upgraded, indent=2) if ctx.severity_upgraded else '[]'}

### MR Thread Status
{json.dumps(ctx.mr_threads, indent=2) if ctx.mr_threads else 'No MR threads analyzed'}

### Review Statistics
{json.dumps(ctx.review_stats, indent=2)}

### Discoveries
{chr(10).join(f'- {d}' for d in ctx.discoveries) if ctx.discoveries else 'None'}

### Jira Context
{getattr(ctx, 'jira_context', 'Not available')}

---

Now create the final PR review report. Verify critical/high findings by reading the actual code files. The report should be comprehensive but focused on actionable items.
"""
            )

            result = ctx.runner.run(
                'pr-report-synthesizer',
                prompt,
                context={
                    'findings': ctx.validated_findings,
                    'diff_files': ctx.diff_files,
                    'work_dir': str(ctx.worktree_path or ctx.work_dir),
                },
                model_override='opus',
            )

            if result.success:
                # Extract report content from agent result
                report_content = _extract_report_content(result)
                if report_content:
                    ctx.log_status(
                        'report', 'Agent generated report successfully'
                    )
                else:
                    ctx.log_status(
                        'report', 'Agent returned empty report - using fallback'
                    )
                    report_content = _generate_report_fallback(ctx)
            else:
                ctx.log_status(
                    'report',
                    f'Agent failed: {result.error[:100] if result.error else "unknown"} - using fallback',
                )
                report_content = _generate_report_fallback(ctx)

    # Write report
    report_path = ctx.work_dir / f'pr_review_{ctx.ticket_id}.md'
    report_path.write_text(report_content)

    ctx.log_status('report', f'Report written to {report_path}')

    # Note: Worktree cleanup is handled by CLI after phases complete

    return PhaseResult(
        success=True,
        data={
            'report_path': str(report_path),
            'report_content': report_content,
        },
    )


def _extract_report_content(result: Any) -> str:
    """Extract clean markdown report from agent result.

    The agent output can come in various formats:
    - Direct markdown in result.data['raw']
    - JSON with 'result' field containing the markdown
    - Markdown wrapped in ```markdown``` blocks
    - Raw JSON string with escaped newlines

    Args:
        result: AgentResult from the report synthesizer

    Returns:
        Clean markdown string with proper newlines
    """
    content = ''

    # Try to get content from parsed data first
    if result.data:
        if isinstance(result.data, dict):
            # Check common keys where content might be
            for key in ['raw', 'result', 'report', 'content', 'markdown']:
                if key in result.data and isinstance(result.data[key], str):
                    content = result.data[key]
                    break
        elif isinstance(result.data, str):
            content = result.data

    # Fall back to raw_output if no content from data
    if not content and result.raw_output:
        # Try to parse as JSON and extract content
        try:
            parsed = json.loads(result.raw_output)
            if isinstance(parsed, dict):
                for key in ['result', 'raw', 'report', 'content']:
                    if key in parsed and isinstance(parsed[key], str):
                        content = parsed[key]
                        break
        except (json.JSONDecodeError, TypeError):
            # Not JSON, use raw output directly
            content = result.raw_output

    if not content:
        return ''

    # Fix escaped newlines (common when content passes through JSON)
    content = content.replace('\\n', '\n')
    content = content.replace('\\t', '\t')
    content = content.replace('\\"', '"')

    # Extract markdown from code blocks if wrapped
    if '```markdown' in content:
        match = re.search(r'```markdown\s*\n(.*?)```', content, re.DOTALL)
        if match:
            content = match.group(1)
    elif '```md' in content:
        match = re.search(r'```md\s*\n(.*?)```', content, re.DOTALL)
        if match:
            content = match.group(1)

    # Find the actual report start if there's preamble text
    if '# PR Review' in content:
        idx = content.find('# PR Review')
        if idx > 0:
            content = content[idx:]

    # Clean up any remaining artifacts
    content = content.strip()

    return content


def _prepare_report_context(ctx: PRReviewContext) -> dict[str, Any]:
    """Prepare comprehensive context for report synthesizer."""
    return {
        'ticket_id': ctx.ticket_id,
        'diff_files': ctx.diff_files,
        'validated_findings': ctx.validated_findings,
        'false_positives': ctx.false_positives,
        'severity_upgraded': ctx.severity_upgraded,
        'mr_threads': ctx.mr_threads,
        'review_stats': ctx.review_stats,
        'discoveries': ctx.discoveries,
        'risk_level': ctx.risk_level.value if ctx.risk_level else 'unknown',
    }


def _generate_report_fallback(ctx: PRReviewContext) -> str:
    """Fallback report generation when agent is unavailable.

    Args:
        ctx: PR review context

    Returns:
        Report markdown content
    """
    # Group findings by severity
    by_severity: dict[str, list[dict[str, Any]]] = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': [],
    }

    for finding in ctx.validated_findings:
        severity = finding.get('severity', 'medium').lower()
        if severity in by_severity:
            by_severity[severity].append(finding)

    # Determine recommendation
    if by_severity['critical']:
        recommendation = (
            '**:x: BLOCK** - Critical issues must be resolved before merge.'
        )
    elif by_severity['high']:
        recommendation = '**:warning: REQUEST CHANGES** - High-priority issues should be addressed.'
    elif by_severity['medium']:
        recommendation = '**:speech_balloon: NEEDS DISCUSSION** - Review medium findings before approval.'
    else:
        recommendation = (
            '**:white_check_mark: APPROVE** - No blocking issues found.'
        )

    # Build report
    lines = [
        f'# PR Review: {ctx.ticket_id}',
        '',
        '## Summary',
        '',
        '| Metric | Value |',
        '|--------|-------|',
        f'| **Risk Level** | {ctx.risk_level.value.upper()} |',
        f'| **Files Changed** | {len(ctx.diff_files)} |',
        f'| **Critical** | {len(by_severity["critical"])} |',
        f'| **High** | {len(by_severity["high"])} |',
        f'| **Medium** | {len(by_severity["medium"])} |',
        f'| **Low** | {len(by_severity["low"])} |',
        f'| **False Positives Filtered** | {len(ctx.false_positives)} |',
        '',
        '## Recommendation',
        '',
        recommendation,
        '',
        '---',
        '',
    ]

    # Severity upgraded findings (prominently displayed)
    if ctx.severity_upgraded:
        lines.extend(
            [
                '## Findings Upgraded During Validation',
                '',
                'These findings were initially lower severity but upgraded after validation:',
                '',
            ]
        )
        for finding in ctx.severity_upgraded:
            lines.extend(
                [
                    f'- **{finding.get("issue", "Unknown")}** ({finding.get("original_severity", "?")} -> {finding.get("severity", "?")})',
                    f'  - File: `{finding.get("file", "N/A")}`',
                    '',
                ]
            )
        lines.append('---')
        lines.append('')

    # Critical findings (detailed)
    if by_severity['critical']:
        lines.extend(['## Critical Findings', ''])
        for idx, finding in enumerate(by_severity['critical'], 1):
            lines.extend(_format_finding(idx, finding, detailed=True))

    # High findings (detailed)
    if by_severity['high']:
        lines.extend(['## High Priority Findings', ''])
        for idx, finding in enumerate(by_severity['high'], 1):
            lines.extend(_format_finding(idx, finding, detailed=True))

    # Medium findings (semi-detailed)
    if by_severity['medium']:
        lines.extend(['## Medium Priority Findings', ''])
        for idx, finding in enumerate(by_severity['medium'], 1):
            lines.extend(_format_finding(idx, finding, detailed=False))

    # Low findings (collapsed)
    if by_severity['low']:
        lines.extend(
            [
                '## Low Priority Findings',
                '',
                '<details>',
                '<summary>Click to expand ({} items)</summary>'.format(
                    len(by_severity['low'])
                ),
                '',
            ]
        )
        for idx, finding in enumerate(by_severity['low'], 1):
            lines.append(
                f'{idx}. `{finding.get("file", "N/A")}`: {finding.get("issue", "Unknown")}'
            )
        lines.extend(['', '</details>', ''])

    # MR Thread Status
    if ctx.mr_threads and 'thread_classifications' in ctx.mr_threads:
        lines.extend(['---', '', '## MR Thread Status', ''])
        lines.append('| Thread | Status | Notes |')
        lines.append('|--------|--------|-------|')
        for thread in ctx.mr_threads['thread_classifications']:
            lines.append(
                f'| {thread.get("topic", "?")} | '
                f'{thread.get("status", "?")} | '
                f'{thread.get("evidence", "")[:50]}... |'
            )
        lines.append('')

        # Blocking threads warning
        blocking = ctx.mr_threads.get('blocking_threads', [])
        if blocking:
            lines.extend(
                [
                    '**Blocking Threads:**',
                    '',
                ]
            )
            for thread_id in blocking:
                lines.append(f'- {thread_id}')
            lines.append('')

    # Review Statistics
    lines.extend(['---', '', '## Review Statistics', ''])
    lines.append('| Phase | Count |')
    lines.append('|-------|-------|')
    lines.append(f'| Agents Run | {ctx.review_stats.get("agents_run", "?")} |')
    lines.append(
        f'| First Round Findings | {ctx.review_stats.get("first_round_findings", "?")} |'
    )
    if 'second_round_findings' in ctx.review_stats:
        lines.append(
            f'| Second Round Findings | {ctx.review_stats.get("second_round_findings", 0)} |'
        )
    lines.append(f'| Validated | {ctx.review_stats.get("validated", "?")} |')
    lines.append(
        f'| False Positives | {ctx.review_stats.get("false_positives", "?")} |'
    )
    if ctx.review_stats.get('disputed'):
        lines.append(
            f'| Disputed (Council) | {ctx.review_stats.get("disputed", 0)} |'
        )
    lines.append('')

    # False Positives (for calibration)
    if ctx.false_positives:
        lines.extend(
            [
                '## False Positives Filtered',
                '',
                '<details>',
                f'<summary>Click to expand ({len(ctx.false_positives)} items) - for review calibration</summary>',
                '',
            ]
        )
        for fp in ctx.false_positives[:10]:  # Limit to 10
            lines.append(
                f'- `{fp.get("file", "?")}`: {fp.get("issue", "?")} (from {fp.get("source_agent", "?")})'
            )
        if len(ctx.false_positives) > 10:
            lines.append(f'- ... and {len(ctx.false_positives) - 10} more')
        lines.extend(['', '</details>', ''])

    # Discoveries
    if ctx.discoveries:
        lines.extend(['## Discoveries', ''])
        for discovery in ctx.discoveries:
            lines.append(f'- {discovery}')
        lines.append('')

    # Files reviewed
    lines.extend(
        [
            '---',
            '',
            '## Files Reviewed',
            '',
        ]
    )
    for f in ctx.diff_files[:20]:  # Limit to 20
        lines.append(f'- `{f}`')
    if len(ctx.diff_files) > 20:
        lines.append(f'- ... and {len(ctx.diff_files) - 20} more')
    lines.append('')

    # Footer
    lines.extend(
        [
            '---',
            '',
            f'Generated by PR Review Workflow v{ctx.config.version}',
        ]
    )

    return '\n'.join(lines)


def _format_finding(
    idx: int, finding: dict[str, Any], detailed: bool
) -> list[str]:
    """Format a single finding for the report.

    Args:
        idx: Finding index
        finding: Finding dict
        detailed: Whether to include full details

    Returns:
        List of markdown lines
    """
    lines = [
        f'### {idx}. {finding.get("issue", "Unknown issue")}',
        '',
        f'**File**: `{finding.get("file", "N/A")}`',
    ]

    if finding.get('line'):
        lines.append(f'**Line**: {finding.get("line")}')

    lines.append('')

    if detailed:
        if finding.get('details'):
            lines.extend(
                [
                    '**Details**:',
                    finding.get('details', ''),
                    '',
                ]
            )

        if finding.get('recommendation'):
            lines.extend(
                [
                    '**Fix**:',
                    finding.get('recommendation', finding.get('fix', 'N/A')),
                    '',
                ]
            )

        # Validation info
        if finding.get('severity_upgraded'):
            lines.append(
                f'*Severity upgraded from {finding.get("original_severity", "?")}*'
            )
        if finding.get('severity_downgraded'):
            lines.append('*Severity downgraded*')

    lines.extend(
        [
            f'**Source**: {finding.get("source_agent", "unknown")}',
            '',
        ]
    )

    return lines


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
