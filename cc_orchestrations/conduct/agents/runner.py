"""Agent runner - invokes claude CLI with structured output.

This is the core mechanism: we call claude -p with --json-schema to force
structured output, then parse the JSON to make control flow decisions.

Key insight from Claude Code docs:
- CLAUDE.md is auto-discovered from working directory
- Skills are NOT available via Skill tool in print mode
- Skills must be injected via --append-system-prompt
- Tools must be explicitly specified via --tools or --allowed-tools
"""

import json
import logging
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cc_orchestrations.conduct.core.config import AgentConfig, Config
from cc_orchestrations.conduct.core.schemas import get_schema

LOG = logging.getLogger(__name__)

# Dry-run prompt wrapper that asks for test data
DRY_RUN_WRAPPER = """🧪 DRY RUN MODE - RETURN TEST DATA 🧪

This is a dry-run test. Return REALISTIC TEST DATA that simulates a successful response.

IMPORTANT: You MUST return populated data, NOT empty arrays. Generate fake but realistic data.

For this task, return a response as if you completed it successfully with test data:
---
{original_prompt}
---

Example of GOOD dry-run response (with data):
{{"status": "success", "components": [{{"file": "[DRY-RUN] test/example.py", "depends_on": []}}]}}

Example of BAD dry-run response (empty):
{{"status": "success", "components": []}}

Return JSON matching the schema with AT LEAST ONE item in any array fields."""


@dataclass
class AgentResult:
    """Result from an agent invocation."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    raw_output: str = ''
    error: str = ''
    duration: float = 0.0
    agent_name: str = ''
    model: str = ''

    @property
    def status(self) -> str:
        """Get status from data, with fallback."""
        return self.data.get('status', 'error' if self.error else 'unknown')

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from data dict."""
        return self.data.get(key, default)


class AgentRunner:
    """Runs agents via claude CLI."""

    def __init__(
        self,
        config: Config,
        work_dir: Path,
        skills_dir: Path | None = None,
        finding_classification_path: Path | None = None,
        dry_run: bool | None = None,
    ):
        self.config = config
        self.work_dir = work_dir
        self.claude_path = config.claude_path
        # Use explicit dry_run if provided, otherwise fall back to config
        self.dry_run = dry_run if dry_run is not None else config.dry_run

        # Skill and classification injection
        self.skills_dir = skills_dir
        self.finding_classification_path = finding_classification_path
        self._skill_cache: dict[str, str] = {}
        self._finding_classification: str | None = None

    def load_skill(self, skill_name: str) -> str | None:
        """Load a skill file for injection via --append-system-prompt."""
        if skill_name in self._skill_cache:
            return self._skill_cache[skill_name]

        if not self.skills_dir:
            return None

        # Try various paths
        paths_to_try = [
            self.skills_dir / skill_name / 'SKILL.md',
            self.skills_dir / f'{skill_name}.md',
            self.skills_dir / skill_name,
        ]

        for path in paths_to_try:
            if path.exists():
                content = path.read_text()
                self._skill_cache[skill_name] = content
                return content

        LOG.warning(f'Skill not found: {skill_name}')
        return None

    def load_finding_classification(self) -> str | None:
        """Load finding classification for validators."""
        if self._finding_classification:
            return self._finding_classification

        if (
            self.finding_classification_path
            and self.finding_classification_path.exists()
        ):
            self._finding_classification = (
                self.finding_classification_path.read_text()
            )
            return self._finding_classification

        return None

    def _build_command(
        self,
        agent_config: AgentConfig,
        prompt: str,
        model_override: str | None = None,
        add_dirs: list[str] | None = None,
        skills_to_inject: list[str] | None = None,
        inject_finding_classification: bool = False,
        scope_context: str | None = None,
        dry_run: bool = False,
    ) -> list[str]:
        """Build the claude CLI command."""
        cmd = [
            self.claude_path,
            '-p',
            '--output-format',
            'json',
        ]

        # Model selection - use haiku for dry-run to save cost
        if dry_run:
            model = 'haiku'
        else:
            model = (
                model_override
                or agent_config.model
                or self.config.default_model
            )
        cmd.extend(['--model', model])

        # JSON schema for structured output
        if agent_config.schema:
            try:
                schema = get_schema(agent_config.schema)
                cmd.extend(['--json-schema', schema.to_json_string()])
            except ValueError as e:
                LOG.warning(f'Schema not found: {e}')

        # Tool restrictions
        # Use = syntax to avoid argument parsing issues with variadic flags
        # In dry-run mode, don't restrict tools - the prompt tells Claude not to use them
        if not dry_run:
            if agent_config.allowed_tools:
                cmd.append(
                    f'--allowed-tools={",".join(agent_config.allowed_tools)}'
                )
            if agent_config.disallowed_tools:
                cmd.append(
                    f'--disallowed-tools={",".join(agent_config.disallowed_tools)}'
                )

        # Permission mode
        if self.config.permission_mode != 'default':
            cmd.extend(['--permission-mode', self.config.permission_mode])

        # Additional directories (skip in dry-run)
        if add_dirs and not dry_run:
            for d in add_dirs:
                cmd.extend(['--add-dir', d])

        # Build system prompt injection
        # Skills are NOT available via Skill tool in print mode - must inject
        system_additions = []

        # Inject skills (skip in dry-run to save tokens)
        if skills_to_inject and not dry_run:
            for skill_name in skills_to_inject:
                skill_content = self.load_skill(skill_name)
                if skill_content:
                    system_additions.append(
                        f'# Skill: {skill_name}\n\n{skill_content}'
                    )

        # Inject finding classification for validators (skip in dry-run)
        if inject_finding_classification and not dry_run:
            classification = self.load_finding_classification()
            if classification:
                system_additions.append(
                    f'# Finding Classification\n\n{classification}'
                )

        # Inject scope discipline (skip in dry-run)
        if scope_context and not dry_run:
            system_additions.append(f"""# Scope Discipline

{scope_context}

CRITICAL RULES:
- Only work within the defined scope
- Do NOT refactor unrelated code
- Do NOT add "improvements" not in spec
- Flag out-of-scope issues to DISCOVERIES.md but don't fix them
- Pre-existing issues in untouched files are OUT OF SCOPE
""")

        # Add system prompt via --append-system-prompt
        if system_additions:
            combined = '\n\n---\n\n'.join(system_additions)
            cmd.extend(['--append-system-prompt', combined])

        # The prompt - wrap in dry-run wrapper if needed
        final_prompt = (
            DRY_RUN_WRAPPER.format(original_prompt=prompt)
            if dry_run
            else prompt
        )
        cmd.append(final_prompt)

        return cmd

    def run(
        self,
        agent_name: str,
        prompt: str,
        context: dict[str, Any] | None = None,
        model_override: str | None = None,
        timeout: int | None = None,
        skills: list[str] | None = None,
        inject_finding_classification: bool = False,
        scope_context: str | None = None,
        dry_run: bool | None = None,
    ) -> AgentResult:
        """Run a single agent and return structured result.

        Args:
            agent_name: Name of agent to run
            prompt: The main prompt
            context: Additional context dict
            model_override: Override model from config
            timeout: Override timeout from config
            skills: Skills to inject via --append-system-prompt
            inject_finding_classification: Include finding classification
            scope_context: Scope boundaries to inject
            dry_run: Override dry_run setting (uses instance setting if None)

        Returns:
            AgentResult with structured data
        """
        # Determine dry-run mode
        is_dry_run = dry_run if dry_run is not None else self.dry_run

        try:
            agent_config = self.config.get_agent(agent_name)
        except ValueError:
            # Create minimal config for unknown agents
            agent_config = AgentConfig(name=agent_name)

        # Format prompt with context
        full_prompt = self._format_prompt(agent_config, prompt, context)

        # Build command
        cmd = self._build_command(
            agent_config,
            full_prompt,
            model_override=model_override,
            skills_to_inject=skills,
            inject_finding_classification=inject_finding_classification,
            scope_context=scope_context,
            dry_run=is_dry_run,
        )

        dry_run_tag = ' [DRY-RUN]' if is_dry_run else ''
        model_used = (
            'haiku' if is_dry_run else (model_override or agent_config.model)
        )
        LOG.info(
            f'Running agent: {agent_name}{dry_run_tag} (model: {model_used})'
        )
        LOG.debug(f'Command: {" ".join(cmd[:10])}...')

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                check=False,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=timeout or agent_config.timeout,
            )

            duration = time.time() - start_time

            if result.returncode != 0:
                LOG.error(f'Agent {agent_name} failed: {result.stderr}')
                return AgentResult(
                    success=False,
                    error=result.stderr or f'Exit code {result.returncode}',
                    raw_output=result.stdout,
                    duration=duration,
                    agent_name=agent_name,
                    model=model_used,
                )

            # Parse JSON output
            try:
                # The output format is JSON with a specific structure
                output = json.loads(result.stdout)

                # Claude CLI with --json-schema puts structured output in 'structured_output'
                if isinstance(output, dict) and 'structured_output' in output:
                    data = output['structured_output']
                # Fallback: Claude CLI json output has a 'result' field with the actual content
                elif isinstance(output, dict) and 'result' in output:
                    # The result might be a string that needs parsing
                    result_content = output['result']
                    if isinstance(result_content, str):
                        try:
                            data = json.loads(result_content)
                        except json.JSONDecodeError:
                            # Not JSON, use as-is
                            data = {'raw': result_content}
                    else:
                        data = result_content
                else:
                    data = output

                return AgentResult(
                    success=True,
                    data=data,
                    raw_output=result.stdout,
                    duration=duration,
                    agent_name=agent_name,
                    model=model_used,
                )

            except json.JSONDecodeError as e:
                LOG.warning(f'Failed to parse JSON from {agent_name}: {e}')
                # Try to extract JSON from the output
                data = self._extract_json(result.stdout)
                if data:
                    return AgentResult(
                        success=True,
                        data=data,
                        raw_output=result.stdout,
                        duration=duration,
                        agent_name=agent_name,
                        model=model_used,
                    )
                return AgentResult(
                    success=False,
                    error=f'Failed to parse output: {e}',
                    raw_output=result.stdout,
                    duration=duration,
                    agent_name=agent_name,
                    model=model_used,
                )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            LOG.error(
                f'Agent {agent_name} timed out after {timeout or agent_config.timeout}s'
            )
            return AgentResult(
                success=False,
                error=f'Timeout after {timeout or agent_config.timeout} seconds',
                duration=duration,
                agent_name=agent_name,
                model=model_used,
            )

        except Exception as e:
            duration = time.time() - start_time
            LOG.error(f'Agent {agent_name} error: {e}')
            return AgentResult(
                success=False,
                error=str(e),
                duration=duration,
                agent_name=agent_name,
                model=model_used,
            )

    def run_parallel(
        self,
        tasks: list[tuple[str, str, dict[str, Any] | None]],
        max_workers: int = 4,
    ) -> list[AgentResult]:
        """Run multiple agents in parallel.

        Args:
            tasks: List of (agent_name, prompt, context) tuples
            max_workers: Maximum parallel workers

        Returns:
            List of AgentResults in same order as tasks
        """
        results: list[AgentResult | None] = [None] * len(tasks)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(self.run, agent_name, prompt, context): idx
                for idx, (agent_name, prompt, context) in enumerate(tasks)
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    LOG.error(f'Parallel task {idx} failed: {e}')
                    results[idx] = AgentResult(
                        success=False,
                        error=str(e),
                        agent_name=tasks[idx][0],
                    )

        return [r for r in results if r is not None]

    def _format_prompt(
        self,
        agent_config: AgentConfig,
        prompt: str,
        context: dict[str, Any] | None,
    ) -> str:
        """Format prompt with template and context."""
        # Start with template if available
        if agent_config.prompt_template:
            template = self._load_template(agent_config.prompt_template)
            if template:
                prompt = f'{template}\n\n{prompt}'

        # Add context
        if context:
            context_str = '\n'.join(f'{k}: {v}' for k, v in context.items())
            prompt = f'{prompt}\n\nContext:\n{context_str}'

        return prompt

    def _load_template(self, template_name: str) -> str | None:
        """Load a prompt template from file."""
        if not self.config.prompts_dir:
            return None

        template_path = Path(self.config.prompts_dir) / f'{template_name}.txt'
        if template_path.exists():
            return template_path.read_text()

        # Try without extension
        template_path = Path(self.config.prompts_dir) / template_name
        if template_path.exists():
            return template_path.read_text()

        return None

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """Try to extract JSON from text that might have other content."""
        # Try to find JSON object in the text
        import re

        # Look for JSON object pattern
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Try to find JSON in code blocks
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return None
