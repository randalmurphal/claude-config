"""Main implement pipeline - automated ticket-to-PR.

Orchestrates the full flow:
1. Fetch & validate ticket
2. Investigation (Opus)
3. Auto-spec generation
4. Draft validation
5. Full orchestration
6. Create MR
7. PR review
8. Address findings (Opus)
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from cc_orchestrations.core import (
    Config,
    ExecutionMode,
    get_git_root,
    get_project_name,
)
from cc_orchestrations.core.extensions import (
    detect_project_extensions,
    get_extension_context,
    merge_prompts,
)
from cc_orchestrations.core.paths import get_data_home, get_tickets_dir
from cc_orchestrations.core.runner import AgentRunner
from cc_orchestrations.prompts import PROMPTS

from .assumptions import Assumption, AssumptionLevel, AssumptionTracker

LOG = logging.getLogger(__name__)


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    NOT_STARTED = 'not_started'
    FETCHING_TICKET = 'fetching_ticket'
    INVESTIGATING = 'investigating'
    CREATING_SPEC = 'creating_spec'
    DRAFT_VALIDATION = 'draft_validation'
    FULL_ORCHESTRATION = 'full_orchestration'
    CREATING_MR = 'creating_mr'
    PR_REVIEW = 'pr_review'
    ADDRESSING_FINDINGS = 'addressing_findings'
    COMPLETE = 'complete'
    FAILED = 'failed'
    BLOCKED = 'blocked'


@dataclass
class PipelineState:
    """Persistent state for pipeline execution."""

    ticket_id: str = ''
    project: str = ''
    status: PipelineStatus = PipelineStatus.NOT_STARTED
    branch_name: str = ''
    worktree_path: str = ''
    spec_path: str = ''
    mr_iid: str = ''

    # Tracking
    started_at: str = ''
    completed_at: str = ''
    error: str = ''

    # Results
    assumptions_file: str = ''
    pr_review_findings: list[dict] = field(default_factory=list)
    remaining_findings: int = 0

    # Attempt tracking
    draft_attempts: int = 0
    review_fix_attempts: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'ticket_id': self.ticket_id,
            'project': self.project,
            'status': self.status.value,
            'branch_name': self.branch_name,
            'worktree_path': self.worktree_path,
            'spec_path': self.spec_path,
            'mr_iid': self.mr_iid,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error': self.error,
            'assumptions_file': self.assumptions_file,
            'pr_review_findings': self.pr_review_findings,
            'remaining_findings': self.remaining_findings,
            'draft_attempts': self.draft_attempts,
            'review_fix_attempts': self.review_fix_attempts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PipelineState':
        """Create from dictionary."""
        state = cls()
        state.ticket_id = data.get('ticket_id', '')
        state.project = data.get('project', '')
        state.status = PipelineStatus(data.get('status', 'not_started'))
        state.branch_name = data.get('branch_name', '')
        state.worktree_path = data.get('worktree_path', '')
        state.spec_path = data.get('spec_path', '')
        state.mr_iid = data.get('mr_iid', '')
        state.started_at = data.get('started_at', '')
        state.completed_at = data.get('completed_at', '')
        state.error = data.get('error', '')
        state.assumptions_file = data.get('assumptions_file', '')
        state.pr_review_findings = data.get('pr_review_findings', [])
        state.remaining_findings = data.get('remaining_findings', 0)
        state.draft_attempts = data.get('draft_attempts', 0)
        state.review_fix_attempts = data.get('review_fix_attempts', 0)
        return state


class ImplementPipeline:
    """Orchestrates the full ticket-to-PR pipeline."""

    MAX_DRAFT_ATTEMPTS = 3
    MAX_REVIEW_FIX_ATTEMPTS = 3

    def __init__(
        self,
        ticket_id: str,
        work_dir: Path,
        force: bool = False,
        config: Config | None = None,
        jira_script: Path | None = None,
        gitlab_script_dir: Path | None = None,
    ):
        self.ticket_id = ticket_id
        self.work_dir = work_dir.resolve()
        self.force = force
        self.config = config or self._default_config()

        # Process ID for unique branch naming
        self.proc_id = os.getpid()

        # Determine project
        self.project = get_project_name(work_dir)
        self.git_root = get_git_root(work_dir)

        # Detect applicable extensions
        self.extensions = detect_project_extensions(work_dir)
        LOG.info(f'Extensions detected: {self.extensions}')

        # Build prompts (merge base + extensions)
        self.prompts = merge_prompts(PROMPTS, self.extensions)

        # State management
        self.state_dir = get_tickets_dir(self.project) / ticket_id
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / 'STATE.json'

        # Load or create state
        self.state = self._load_state()

        # Assumption tracker
        self.assumptions = AssumptionTracker()
        if self.state.assumptions_file:
            assumptions_path = Path(self.state.assumptions_file)
            if assumptions_path.exists():
                self.assumptions = AssumptionTracker.load(assumptions_path)

        # Runner for agent invocation
        self.runner = AgentRunner(self.config, work_dir)

        # Scripts (can be overridden)
        self.jira_script = jira_script or self._find_jira_script()
        self.gitlab_script_dir = (
            gitlab_script_dir or self._find_gitlab_scripts()
        )

    def _default_config(self) -> Config:
        """Create default config."""
        return Config(
            name='implement',
            mode=ExecutionMode.STANDARD,
            default_model='opus',
        )

    def _find_jira_script(self) -> Path | None:
        """Find jira-get-issue script."""
        # Check project first
        project_script = (
            self.git_root / '.claude' / 'scripts' / 'jira' / 'jira-get-issue'
        )
        if project_script.exists():
            return project_script

        # Check home
        home_script = (
            Path.home() / '.claude' / 'scripts' / 'jira' / 'jira-get-issue'
        )
        if home_script.exists():
            return home_script

        return None

    def _find_gitlab_scripts(self) -> Path | None:
        """Find gitlab scripts directory."""
        project_dir = self.git_root / '.claude' / 'scripts' / 'gitlab'
        if project_dir.exists():
            return project_dir

        home_dir = Path.home() / '.claude' / 'scripts' / 'gitlab'
        if home_dir.exists():
            return home_dir

        return None

    def _load_state(self) -> PipelineState:
        """Load state from file or create new."""
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text())
            return PipelineState.from_dict(data)

        state = PipelineState()
        state.ticket_id = self.ticket_id
        state.project = self.project
        return state

    def _save_state(self) -> None:
        """Save current state."""
        self.state_file.write_text(json.dumps(self.state.to_dict(), indent=2))

    def _update_status(self, status: PipelineStatus, error: str = '') -> None:
        """Update pipeline status."""
        self.state.status = status
        if error:
            self.state.error = error
        self._save_state()
        LOG.info(
            f'Pipeline status: {status.value}'
            + (f' - {error}' if error else '')
        )

    def _get_project_context(self) -> str:
        """Build project context for prompts."""
        context_parts = []

        # Read AGENTS.md if exists
        agents_md = self.git_root / 'AGENTS.md'
        if agents_md.exists():
            context_parts.append(
                f'## Project Documentation (AGENTS.md)\n\n{agents_md.read_text()[:5000]}'
            )

        # Add extension context
        for ext in self.extensions:
            ext_context = get_extension_context(ext)
            if ext_context:
                context_parts.append(
                    f'## Extension Context ({ext})\n\n{ext_context}'
                )

        return (
            '\n\n'.join(context_parts)
            if context_parts
            else 'No project context available.'
        )

    def _jira_comment(self, message: str) -> bool:
        """Post comment to Jira ticket."""
        if not self.jira_script:
            LOG.warning('Jira script not found, cannot post comment')
            return False

        comment_script = self.jira_script.parent / 'jira-comment-ticket'
        if not comment_script.exists():
            LOG.warning(f'Jira comment script not found: {comment_script}')
            return False

        try:
            subprocess.run(
                [str(comment_script), self.ticket_id, message],
                cwd=self.git_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            LOG.error(f'Failed to post Jira comment: {e.stderr}')
            return False

    def _fail_with_comment(self, reason: str) -> None:
        """Fail pipeline and post reason to Jira."""
        self._update_status(PipelineStatus.FAILED, reason)

        comment = f"""h2. (x) Automated Implementation Failed

{reason}

*Pipeline ID:* {self.proc_id}
*Status:* Failed

Please update the ticket with more details or resolve the blocker."""

        self._jira_comment(comment)

    def run(self, resume: bool = False) -> bool:
        """Run the full pipeline.

        Args:
            resume: If True, resume from saved state.

        Returns:
            True if pipeline completed successfully
        """
        import datetime

        # Handle failed/blocked states - reset to retry from beginning
        if self.state.status in [PipelineStatus.FAILED, PipelineStatus.BLOCKED]:
            LOG.info(
                f'Resetting from {self.state.status.value} to retry pipeline'
            )
            self.state.status = PipelineStatus.NOT_STARTED
            self.state.error = ''
            self._save_state()

        if not resume or self.state.status == PipelineStatus.NOT_STARTED:
            self.state.started_at = datetime.datetime.now(
                tz=datetime.UTC
            ).isoformat()
            self._save_state()

        try:
            # Phase 1: Fetch and validate ticket
            if self.state.status in [
                PipelineStatus.NOT_STARTED,
                PipelineStatus.FETCHING_TICKET,
            ]:
                if not self._phase_fetch_ticket():
                    return False

            # Phase 2: Investigation
            if self.state.status == PipelineStatus.INVESTIGATING:
                if not self._phase_investigate():
                    return False

            # Phase 3: Create spec
            if self.state.status == PipelineStatus.CREATING_SPEC:
                if not self._phase_create_spec():
                    return False

            # Phase 4: Draft validation
            if self.state.status == PipelineStatus.DRAFT_VALIDATION:
                if not self._phase_draft_validation():
                    return False

            # Phase 5: Full orchestration
            if self.state.status == PipelineStatus.FULL_ORCHESTRATION:
                if not self._phase_full_orchestration():
                    return False

            # Phase 6: Create MR
            if self.state.status == PipelineStatus.CREATING_MR:
                if not self._phase_create_mr():
                    return False

            # Phase 7: PR Review
            if self.state.status == PipelineStatus.PR_REVIEW:
                if not self._phase_pr_review():
                    return False

            # Phase 8: Address findings
            if self.state.status == PipelineStatus.ADDRESSING_FINDINGS:
                if not self._phase_address_findings():
                    return False

            # Complete
            self.state.completed_at = datetime.datetime.now(
                tz=datetime.UTC
            ).isoformat()
            self._update_status(PipelineStatus.COMPLETE)

            self._post_completion_comment()
            return True

        except KeyboardInterrupt:
            LOG.info('Pipeline interrupted. State saved.')
            self._save_state()
            return False
        except Exception as e:
            LOG.exception(f'Pipeline failed: {e}')
            self._fail_with_comment(f'Unexpected error: {e}')
            return False

    def _phase_fetch_ticket(self) -> bool:
        """Phase 1: Fetch and validate ticket from Jira."""
        self._update_status(PipelineStatus.FETCHING_TICKET)

        if not self.jira_script or not self.jira_script.exists():
            self._fail_with_comment(
                'Jira script not found. Cannot fetch ticket.'
            )
            return False

        try:
            result = subprocess.run(
                [str(self.jira_script), self.ticket_id],
                cwd=self.git_root,
                capture_output=True,
                text=True,
                check=True,
            )
            ticket_data = result.stdout
        except subprocess.CalledProcessError as e:
            self._fail_with_comment(f'Failed to fetch ticket: {e.stderr}')
            return False

        # Save ticket data
        ticket_file = self.state_dir / 'TICKET.md'
        ticket_file.write_text(ticket_data)

        # Basic validation
        if 'No description' in ticket_data or len(ticket_data.strip()) < 100:
            self._fail_with_comment(
                'Cannot proceed: Ticket has insufficient description. '
                'Please add details with acceptance criteria.'
            )
            return False

        self._update_status(PipelineStatus.INVESTIGATING)
        return True

    def _phase_investigate(self) -> bool:
        """Phase 2: Investigate codebase and interpret ticket."""
        ticket_file = self.state_dir / 'TICKET.md'
        ticket_content = ticket_file.read_text() if ticket_file.exists() else ''

        # Build prompt from template
        prompt = self.prompts['investigation'].format(
            ticket_id=self.ticket_id,
            ticket_content=ticket_content,
            project_name=self.project,
            work_dir=str(self.work_dir),
            project_context=self._get_project_context(),
        )

        result = self.runner.run_prompt(prompt, model='opus')

        if not result.success:
            self._fail_with_comment(f'Investigation failed: {result.error}')
            return False

        # Parse assumptions
        for assumption_data in result.get('assumptions', []):
            assumption = Assumption(
                topic=assumption_data.get('topic', ''),
                options=assumption_data.get('options', []),
                chosen=assumption_data.get('chosen', ''),
                rationale=assumption_data.get('rationale', ''),
                level=AssumptionLevel(assumption_data.get('level', 'minor')),
                risk_if_wrong=assumption_data.get('risk_if_wrong', ''),
            )
            self.assumptions.add(assumption)

        # Save assumptions
        assumptions_file = self.state_dir / 'ASSUMPTIONS.json'
        self.assumptions.save(assumptions_file)
        self.state.assumptions_file = str(assumptions_file)

        # Check for blockers (unless --force)
        blockers = result.get('blockers', [])
        if blockers and not self.force:
            self._fail_with_comment(
                'Cannot proceed due to blockers:\n'
                + '\n'.join(f'- {b}' for b in blockers)
            )
            return False
        elif blockers:
            LOG.warning(f'Bypassing {len(blockers)} blockers due to --force')
            for b in blockers:
                LOG.warning(f'  - {b}')

        # Check assumption threshold (unless --force)
        if not self.force and self.assumptions.is_over_threshold():
            reason = self.assumptions.get_stop_reason()
            assumptions_md = self.assumptions.to_jira_comment()

            self._fail_with_comment(
                f'{reason}\n\n'
                f'Assumptions:\n{assumptions_md}\n\n'
                f'Add more details or re-run with --force.'
            )
            return False

        # Check if investigation says not to proceed
        if not result.get('proceed', True):
            self._fail_with_comment(
                'Investigation determined this cannot be implemented automatically. '
                f'Reason: {result.get("understanding", "Unknown")}'
            )
            return False

        # Save investigation results
        investigation_file = self.state_dir / 'INVESTIGATION.json'
        investigation_file.write_text(json.dumps(result.data, indent=2))

        self._update_status(PipelineStatus.CREATING_SPEC)
        return True

    def _phase_create_spec(self) -> bool:
        """Phase 3: Create spec from investigation."""
        investigation_file = self.state_dir / 'INVESTIGATION.json'
        investigation = {}
        if investigation_file.exists():
            investigation = json.loads(investigation_file.read_text())

        ticket_file = self.state_dir / 'TICKET.md'
        ticket_content = ticket_file.read_text() if ticket_file.exists() else ''

        # Create spec directory
        spec_name = f'{self.ticket_id}-{self.proc_id}'
        spec_dir = get_data_home() / 'specs' / self.project / spec_name
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / 'brainstorm').mkdir(exist_ok=True)
        (spec_dir / 'components').mkdir(exist_ok=True)

        self.state.spec_path = str(spec_dir)
        self._save_state()

        # Build prompt
        prompt = self.prompts['spec_generation'].format(
            ticket_id=self.ticket_id,
            ticket_content=ticket_content,
            investigation_json=json.dumps(investigation, indent=2),
            assumptions_json=self.assumptions.to_markdown(),
            project_name=self.project,
        )

        result = self.runner.run_prompt(prompt, model='opus')

        if not result.success:
            self._fail_with_comment(f'Spec generation failed: {result.error}')
            return False

        # Write spec files
        spec_file = spec_dir / 'SPEC.md'
        manifest_file = spec_dir / 'manifest.json'

        if result.get('spec_content'):
            spec_file.write_text(result.get('spec_content'))
        else:
            self._fail_with_comment('Spec generation did not produce SPEC.md')
            return False

        if result.get('manifest'):
            manifest_file.write_text(
                json.dumps(result.get('manifest'), indent=2)
            )

        self._update_status(PipelineStatus.DRAFT_VALIDATION)
        return True

    def _phase_draft_validation(self) -> bool:
        """Phase 4: Draft implementation to discover spec gaps.

        Uses cursor-agent (composer-1) if available, falls back to haiku.
        Does a quick draft implementation attempt to expose anything the spec
        missed, then UPDATES THE SPEC with those discoveries before full
        orchestration.
        """
        spec_path = Path(self.state.spec_path) / 'SPEC.md'

        if not spec_path.exists():
            self._fail_with_comment(f'SPEC.md not found at {spec_path}')
            return False

        # Read spec content
        spec_content = spec_path.read_text()

        # Run draft implementation with cheap model (composer-1 or haiku)
        runner = AgentRunner(
            config=self.config,
            work_dir=self.git_root,
        )

        use_cursor = runner.is_cursor_available()
        model = 'composer-1' if use_cursor else 'haiku'

        LOG.info(
            f'Draft implementation using {model} (cursor available: {use_cursor})'
        )

        result = runner.run(
            agent_name='draft_implementer',
            prompt=f"""Do a quick draft implementation pass on this spec.

As you mentally work through implementing each component, note anything
the spec missed or got wrong:
- Missing edge cases or error handling
- Unclear interfaces between components
- Dependencies that weren't documented
- Implementation details that need to be specified
- Gotchas you discovered

Return JSON with spec updates:
{{
    "discoveries": [
        "Thing 1 the spec missed",
        "Thing 2 that needs clarification"
    ],
    "spec_additions": {{
        "gotchas": ["New gotcha to add"],
        "dependencies": ["Newly discovered dependency"],
        "clarifications": ["Clarification for unclear part"]
    }},
    "components_viable": true/false,
    "summary": "Brief summary of draft findings"
}}

=== SPEC ===
{spec_content}
=== END SPEC ===
""",
            model_override=model,
            show_progress=True,
        )

        if not result.success:
            LOG.warning(f'Draft implementation failed: {result.error}')
            # Continue anyway - full orchestration will handle it
            self._update_status(PipelineStatus.FULL_ORCHESTRATION)
            return True

        # Extract discoveries
        discoveries = result.get('discoveries', [])
        spec_additions = result.get('spec_additions', {})
        viable = result.get('components_viable', True)
        summary = result.get('summary', '')

        LOG.info(f'Draft found {len(discoveries)} discoveries')

        if discoveries:
            LOG.info(f'Draft discoveries: {discoveries}')

        # Update the spec with discoveries if any
        if discoveries or spec_additions:
            self._update_spec_with_discoveries(
                spec_path, discoveries, spec_additions
            )

        if not viable:
            LOG.warning(
                f'Draft indicates components may not be viable: {summary}'
            )
            # Still proceed - let full orchestration handle it

        LOG.info('Draft complete - proceeding to full orchestration')
        self._update_status(PipelineStatus.FULL_ORCHESTRATION)
        return True

    def _update_spec_with_discoveries(
        self,
        spec_path: Path,
        discoveries: list[str],
        additions: dict,
    ) -> None:
        """Append draft discoveries to the spec."""
        if not discoveries and not additions:
            return

        LOG.info(f'Updating spec with {len(discoveries)} discoveries')

        # Read current spec
        spec_content = spec_path.read_text()

        # Build additions section
        additions_text = '\n\n---\n\n## Draft Implementation Discoveries\n\n'
        additions_text += (
            '*Added automatically from draft implementation pass*\n\n'
        )

        if discoveries:
            additions_text += '### Discoveries\n\n'
            for d in discoveries:
                additions_text += f'- {d}\n'

        if additions.get('gotchas'):
            additions_text += '\n### Additional Gotchas\n\n'
            for g in additions['gotchas']:
                additions_text += f'- {g}\n'

        if additions.get('dependencies'):
            additions_text += '\n### Additional Dependencies\n\n'
            for dep in additions['dependencies']:
                additions_text += f'- {dep}\n'

        if additions.get('clarifications'):
            additions_text += '\n### Clarifications Needed\n\n'
            for c in additions['clarifications']:
                additions_text += f'- {c}\n'

        # Append to spec
        spec_path.write_text(spec_content + additions_text)
        LOG.info('Spec updated with draft discoveries')

    def _phase_full_orchestration(self) -> bool:
        """Phase 5: Run full orchestration with quality models."""
        from cc_orchestrations.conduct import create_conduct_workflow

        worktree_path = Path(self.state.worktree_path)
        spec_path = worktree_path / '.spec' / 'SPEC.md'

        # Reset draft commits
        try:
            # Get draft commit count
            result = subprocess.run(
                ['git', 'log', '--oneline', '--grep=\\[DRAFT\\]'],
                cwd=worktree_path,
                capture_output=True,
                text=True,
            )
            draft_count = (
                len(result.stdout.strip().split('\n'))
                if result.stdout.strip()
                else 0
            )

            if draft_count > 0:
                subprocess.run(
                    ['git', 'reset', '--hard', f'HEAD~{draft_count}'],
                    cwd=worktree_path,
                    capture_output=True,
                    check=True,
                )
                LOG.info(f'Reset {draft_count} draft commits')
        except subprocess.CalledProcessError as e:
            LOG.warning(f'Failed to reset draft commits: {e}')

        # Run full conduct
        config = self.config
        config.mode = ExecutionMode.STANDARD
        config.default_model = 'sonnet'  # Use Sonnet for implementation

        # Use Opus for validation
        if 'validator' in config.agents:
            config.agents['validator'].model = 'opus'

        engine = create_conduct_workflow(
            work_dir=worktree_path,
            spec_path=spec_path,
            config_override=config,
            draft_mode=False,
        )

        success = engine.run(resume=False)

        if not success:
            self._fail_with_comment(
                'Full orchestration failed. Manual intervention needed.'
            )
            return False

        self._update_status(PipelineStatus.CREATING_MR)
        return True

    def _phase_create_mr(self) -> bool:
        """Phase 6: Create GitLab merge request."""
        import re

        worktree_path = Path(self.state.worktree_path)

        # Push branch
        try:
            subprocess.run(
                ['git', 'push', '-u', 'origin', self.state.branch_name],
                cwd=worktree_path,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            LOG.warning(f'Push failed, may already exist: {e.stderr}')

        # Build MR description
        spec_file = Path(self.state.spec_path) / 'SPEC.md'
        spec_content = spec_file.read_text() if spec_file.exists() else ''

        assumptions_md = self.assumptions.to_markdown()

        description = f"""## {self.ticket_id}: Automated Implementation

### Assumptions Made
{assumptions_md}

### Spec Summary
{spec_content[:2000]}...

---
*This MR was automatically generated by the implement pipeline.*
*Pipeline ID: {self.proc_id}*
"""

        # Create MR using script
        if not self.gitlab_script_dir:
            LOG.warning('GitLab scripts not found, skipping MR creation')
            self._update_status(PipelineStatus.PR_REVIEW)
            return True

        script = self.gitlab_script_dir / 'gitlab-create-mr'
        if not script.exists():
            LOG.error(f'GitLab script not found: {script}')
            # Continue without MR - can be created manually
            self._update_status(PipelineStatus.PR_REVIEW)
            return True

        try:
            result = subprocess.run(
                [
                    str(script),
                    self.state.branch_name,
                    'develop',  # TODO: Make configurable
                    f'{self.ticket_id}: Automated implementation',
                    description,
                ],
                cwd=self.git_root,
                capture_output=True,
                text=True,
                check=True,
            )
            # Parse MR IID from output
            # Expected format: "Created MR !123" or similar
            match = re.search(r'!(\d+)', result.stdout)
            if match:
                self.state.mr_iid = match.group(1)
                self._save_state()
        except subprocess.CalledProcessError as e:
            LOG.error(f'Failed to create MR: {e.stderr}')

        # Post assumptions to Jira ticket
        self._jira_comment(
            f'h2. (i) Automated Implementation Started\n\n'
            f'MR created: !{self.state.mr_iid}\n'
            f'Branch: {self.state.branch_name}\n\n'
            f'{self.assumptions.to_jira_comment()}'
        )

        self._update_status(PipelineStatus.PR_REVIEW)
        return True

    def _phase_pr_review(self) -> bool:
        """Phase 7: Run automated PR review."""
        # Run PR review using the pr_reviewer agent
        result = self.runner.run_prompt(
            f"""Review the merge request for ticket {self.ticket_id}.

Branch: {self.state.branch_name}
MR: !{self.state.mr_iid}

Review against:
1. Ticket requirements (JIRA)
2. Code quality standards
3. Security concerns
4. Test coverage

Output structured findings as JSON:
{{
    "findings": [
        {{
            "severity": "critical|high|medium|low",
            "category": "security|quality|requirements|tests",
            "file": "path/to/file.py",
            "line": 42,
            "issue": "description",
            "suggestion": "how to fix"
        }}
    ],
    "summary": "overall assessment"
}}
""",
            model='opus',
        )

        if result.success:
            self.state.pr_review_findings = result.get('findings', [])
            self._save_state()

        self._update_status(PipelineStatus.ADDRESSING_FINDINGS)
        return True

    def _phase_address_findings(self) -> bool:
        """Phase 8: Address PR review findings with Opus."""
        if not self.state.pr_review_findings:
            LOG.info('No PR review findings to address')
            return True

        self.state.review_fix_attempts += 1
        self._save_state()

        if self.state.review_fix_attempts > self.MAX_REVIEW_FIX_ATTEMPTS:
            self.state.remaining_findings = len(self.state.pr_review_findings)
            LOG.warning(
                f'{self.state.remaining_findings} findings remain after '
                f'{self.MAX_REVIEW_FIX_ATTEMPTS} fix attempts'
            )
            return True  # Continue to completion, note remaining issues

        worktree_path = Path(self.state.worktree_path)

        # Have Opus address each finding
        result = self.runner.run_prompt(
            f"""Address these PR review findings:

{json.dumps(self.state.pr_review_findings, indent=2)}

For each finding:
1. Understand the issue
2. Make the necessary code changes
3. Verify the fix doesn't break anything

Work in: {worktree_path}

After fixing, commit with message: "[conduct] review-fix: address PR findings"

Output:
{{
    "fixed": ["list of fixed finding indices"],
    "unfixed": ["list of findings that couldn't be fixed"],
    "new_issues": ["any new issues discovered"]
}}
""",
            model='opus',
        )

        if result.success:
            unfixed = result.get('unfixed', [])
            new_issues = result.get('new_issues', [])

            if unfixed or new_issues:
                # Update findings for next iteration
                remaining = []
                for idx in unfixed:
                    if idx < len(self.state.pr_review_findings):
                        remaining.append(self.state.pr_review_findings[idx])
                remaining.extend(new_issues)

                self.state.pr_review_findings = remaining
                self._save_state()

                if remaining:
                    return self._phase_address_findings()  # Retry

            # Push fixes
            try:
                subprocess.run(
                    ['git', 'push'],
                    cwd=worktree_path,
                    capture_output=True,
                    check=True,
                )
            except subprocess.CalledProcessError:
                pass  # Non-fatal

        self.state.remaining_findings = len(self.state.pr_review_findings)
        return True

    def _post_completion_comment(self) -> None:
        """Post completion comment to Jira."""
        remaining_note = ''
        if self.state.remaining_findings > 0:
            remaining_note = (
                f'\n\n(!) {self.state.remaining_findings} findings '
                f'could not be automatically addressed.'
            )

        comment = f"""h2. (/) Automated Implementation Complete

*MR:* !{self.state.mr_iid}
*Branch:* {self.state.branch_name}
*Pipeline ID:* {self.proc_id}

Please review the MR.
{remaining_note}

{self.assumptions.to_jira_comment()}
"""
        self._jira_comment(comment)

    def get_status(self) -> dict:
        """Get current pipeline status."""
        return {
            'ticket': self.ticket_id,
            'status': self.state.status.value,
            'branch': self.state.branch_name,
            'mr_iid': self.state.mr_iid,
            'worktree': self.state.worktree_path,
            'spec': self.state.spec_path,
            'started': self.state.started_at,
            'completed': self.state.completed_at,
            'error': self.state.error,
            'draft_attempts': self.state.draft_attempts,
            'review_fix_attempts': self.state.review_fix_attempts,
            'remaining_findings': self.state.remaining_findings,
        }
