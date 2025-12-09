"""Agent runner - invokes claude CLI with structured output.

This is the core mechanism: we call claude -p with --json-schema to force
structured output, then parse the JSON to make control flow decisions.

Key insight from Claude Code docs:
- CLAUDE.md is auto-discovered from working directory
- Skills are NOT available via Skill tool in print mode
- Skills must be injected via --append-system-prompt
- Tools must be explicitly specified via --tools or --allowed-tools

Retry behavior:
- Retryable errors: timeouts, rate limits, transient failures
- Non-retryable: auth failures, schema errors, logic errors
- Exponential backoff with jitter
"""

import json
import logging
import random
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .config import (
    AgentConfig,
    CLIBackend,
    Config,
    get_backend_for_model,
    get_timeout_for_model,
)
from .context import ContextManager, ContextUpdate
from .schemas import get_schema
from .trajectory import AgentTrajectory, TrajectoryLogger
from .workspace import Workspace

LOG = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Classification of errors for retry decisions."""

    RETRYABLE = 'retryable'  # Timeout, rate limit, transient
    NON_RETRYABLE = 'non_retryable'  # Auth, schema, logic errors
    UNKNOWN = 'unknown'  # Treat as retryable with caution


def classify_error(error: str, returncode: int | None = None) -> ErrorType:
    """Classify an error to determine retry behavior.

    Args:
        error: The error message
        returncode: The process return code if available

    Returns:
        ErrorType classification
    """
    error_lower = error.lower()

    # Non-retryable patterns (don't waste time retrying these)
    non_retryable_patterns = [
        'authentication',
        'unauthorized',
        'forbidden',
        '403',
        '401',
        'invalid api key',
        'api key',
        'invalid token',
        'permission denied',
        'schema validation',
        'invalid schema',
        'json decode error',
        'malformed',
        'syntax error',
    ]

    for pattern in non_retryable_patterns:
        if pattern in error_lower:
            return ErrorType.NON_RETRYABLE

    # Retryable patterns
    retryable_patterns = [
        'timeout',
        'timed out',
        'rate limit',
        'too many requests',
        '429',
        '500',
        '502',
        '503',
        '504',
        'service unavailable',
        'connection reset',
        'connection refused',
        'connection error',
        'network',
        'temporary',
        'transient',
        'overloaded',
        'capacity',
    ]

    for pattern in retryable_patterns:
        if pattern in error_lower:
            return ErrorType.RETRYABLE

    # Exit codes that suggest retryable vs non-retryable
    if returncode is not None:
        # Signal-based exits (killed, timeout)
        if returncode < 0 or returncode > 128:
            return ErrorType.RETRYABLE

    return ErrorType.UNKNOWN


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0
    jitter: float = 0.1  # Random factor to prevent thundering herd

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt with exponential backoff and jitter."""
        delay = min(
            self.initial_delay * (self.exponential_base**attempt),
            self.max_delay,
        )
        # Add jitter
        jitter_range = delay * self.jitter
        delay += random.uniform(-jitter_range, jitter_range)
        return max(0.1, delay)  # Never less than 100ms


# Default retry config
DEFAULT_RETRY_CONFIG = RetryConfig()

# Dry-run prompt wrapper that asks for test data
DRY_RUN_WRAPPER = """🧪 DRY RUN TEST - OUTPUT ONLY JSON 🧪

INSTRUCTIONS: This is an automated dry-run test of the orchestration infrastructure.
You MUST respond with ONLY valid JSON. No explanations, no conversation, no markdown.

Your ONLY output should be a JSON object simulating a successful response for this task.

TASK TO SIMULATE:
---
{original_prompt}
---

RULES:
1. Output ONLY valid JSON (no prose, no explanation)
2. Include realistic test data (not empty arrays)
3. Prefix any strings with "[DRY-RUN]" so data is clearly fake
4. If the prompt mentions a schema, follow it

EXAMPLE OUTPUT (no other text before or after):
{{"status": "success", "data": "[DRY-RUN] mock response", "items": [{{"name": "[DRY-RUN] test item"}}]}}

YOUR JSON RESPONSE:"""


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
    retry_attempts: int = 0  # Number of retries before success/final failure
    error_type: ErrorType | None = None  # Classification if failed

    @property
    def status(self) -> str:
        """Get status from data, with fallback."""
        return self.data.get('status', 'error' if self.error else 'unknown')

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from data dict."""
        return self.data.get(key, default)


class AgentRunner:
    """Runs agents via claude CLI or cursor-agent CLI.

    Backend selection:
    - Claude models (opus, sonnet, haiku) ALWAYS use Claude Code CLI
    - Non-Anthropic models (gpt-5.1, gemini-3-pro, grok, composer-1) use cursor-agent
    """

    # Default cursor-agent path
    DEFAULT_CURSOR_PATH = str(Path.home() / '.local' / 'bin' / 'cursor-agent')

    def __init__(
        self,
        config: Config,
        work_dir: Path,
        skills_dir: Path | None = None,
        finding_classification_path: Path | None = None,
        dry_run: bool | None = None,
        live_test: bool | None = None,
        context_manager: ContextManager | None = None,
        cursor_path: str | None = None,
        enable_trajectory: bool = False,
    ):
        self.config = config
        self.work_dir = work_dir
        self.claude_path = config.claude_path
        self.cursor_path = cursor_path or self.DEFAULT_CURSOR_PATH
        # Use explicit dry_run if provided, otherwise fall back to config
        self.dry_run = dry_run if dry_run is not None else config.dry_run
        # live_test: use real CLIs with cheap models (Claude→haiku, Cursor→composer-1)
        self.live_test = (
            live_test if live_test is not None else config.live_test
        )

        # Context management
        self.context_manager = context_manager

        # Skill and classification injection
        self.skills_dir = skills_dir
        self.finding_classification_path = finding_classification_path
        self._skill_cache: dict[str, str] = {}
        self._finding_classification: str | None = None

        # Check cursor-agent availability
        self._cursor_available: bool | None = None

        # Trajectory logging for debugging
        self.trajectory_logger: TrajectoryLogger | None = (
            TrajectoryLogger(work_dir) if enable_trajectory else None
        )

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

    def is_cursor_available(self) -> bool:
        """Check if cursor-agent CLI is available."""
        if self._cursor_available is not None:
            return self._cursor_available

        try:
            result = subprocess.run(
                [self.cursor_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self._cursor_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._cursor_available = False

        if not self._cursor_available:
            LOG.warning(
                f'cursor-agent not available at {self.cursor_path}. '
                'Non-Anthropic models will fall back to Claude.'
            )

        return self._cursor_available

    def _validate_cursor_model(self, model: str) -> str:
        """Validate that a model name is valid for cursor-agent.

        Args:
            model: Model name (should be actual cursor-agent model name)

        Returns:
            The model name (unchanged - no translation needed)

        Note:
            Use actual cursor-agent model names (composer-1, gpt-5.1, etc.)
            not aliases. See CURSOR_MODELS in config.py for valid names.
        """
        return model  # Pass through - cursor-agent will validate

    def _build_cursor_command(
        self,
        prompt: str,
        model: str,
        dry_run: bool = False,
    ) -> list[str]:
        """Build cursor-agent CLI command.

        Note: cursor-agent has limited options compared to Claude Code.
        No tool restrictions, no schema enforcement, no system prompt injection.
        Use it for simple tasks where diverse model opinion matters.

        Args:
            prompt: The prompt to send
            model: Actual cursor-agent model name (e.g., 'composer-1', 'gpt-5.1')
            dry_run: If True, wrap prompt for mock JSON responses
        """
        cursor_model = self._validate_cursor_model(model)

        cmd = [
            self.cursor_path,
            '-p',  # Print mode (non-interactive)
            '--output-format',
            'json',
            '--model',
            cursor_model,
            '--workspace',
            str(self.work_dir),
            '--force',  # Auto-approve command permissions
            '--approve-mcps',  # Auto-approve MCP servers
        ]

        # The prompt - wrap in dry-run wrapper if needed
        final_prompt = (
            DRY_RUN_WRAPPER.format(original_prompt=prompt)
            if dry_run
            else prompt
        )
        cmd.append(final_prompt)

        return cmd

    def _parse_cursor_output(self, stdout: str) -> dict[str, Any] | None:
        """Parse cursor-agent JSON output.

        cursor-agent output format:
        {
            "type": "result",
            "subtype": "success",
            "is_error": false,
            "result": "```json\\n{...}\\n```",  # May be wrapped in markdown
            ...
        }
        """
        try:
            output = json.loads(stdout)

            if output.get('is_error'):
                return None

            result_content = output.get('result', '')

            # Result may be wrapped in markdown code block
            if isinstance(result_content, str):
                # Try to extract JSON from markdown
                extracted = self._extract_json(result_content)
                if extracted:
                    return extracted

                # Try direct parse
                try:
                    return json.loads(result_content)
                except json.JSONDecodeError:
                    return {'raw': result_content}

            return result_content if isinstance(result_content, dict) else None

        except json.JSONDecodeError:
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
            '--dangerously-skip-permissions',  # Auto-approve for orchestration
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
        live_test: bool | None = None,
        component_id: str | None = None,
        show_progress: bool = True,
        retry_config: RetryConfig | None = None,
        workspace: Workspace | None = None,
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
                     When True: all models→haiku, wraps prompt for mock JSON
            live_test: Override live_test setting (uses instance setting if None)
                       When True: Claude→haiku, Cursor→composer-1, real execution
            component_id: Component identifier for context injection
            show_progress: Show progress spinner (default True)
            retry_config: Retry configuration (default: 3 attempts with backoff)
            workspace: Workspace for PULL-model context (optional)
                       When provided, injects minimal context with navigation

        Returns:
            AgentResult with structured data
        """
        from .progress import SingleAgentProgress

        # Use default retry config if not provided
        retry_cfg = retry_config or DEFAULT_RETRY_CONFIG

        # Determine test modes
        is_dry_run = dry_run if dry_run is not None else self.dry_run
        is_live_test = live_test if live_test is not None else self.live_test

        try:
            agent_config = self.config.get_agent(agent_name)
        except ValueError:
            # Create minimal config for unknown agents
            agent_config = AgentConfig(name=agent_name)

        # Format prompt with context
        full_prompt = self._format_prompt(
            agent_config, prompt, context, component_id, workspace
        )

        # Determine which model and backend to use
        # Priority: force_model > dry_run > live_test > explicit override > agent config
        intended_model = model_override or agent_config.model
        backend = get_backend_for_model(intended_model)

        # Apply test mode model overrides
        if self.config.force_model:
            # force_model overrides EVERYTHING - used for draft mode
            model_used = self.config.force_model
            backend = get_backend_for_model(model_used)
        elif is_dry_run:
            # dry_run: force haiku for all (cheapest, wraps prompt for mock JSON)
            model_used = 'haiku'
            backend = CLIBackend.CLAUDE  # Don't use cursor in dry_run
        elif is_live_test:
            # live_test: use cheap models but route to correct backend
            if backend == CLIBackend.CURSOR:
                model_used = 'composer-1'  # Cheap cursor model
            else:
                model_used = 'haiku'  # Cheap Claude model
        else:
            model_used = intended_model

        # Fall back to Claude if cursor not available
        if backend == CLIBackend.CURSOR and not self.is_cursor_available():
            LOG.warning(
                f'cursor-agent not available, falling back to Claude for '
                f'{agent_name} (model: {model_used})'
            )
            backend = CLIBackend.CLAUDE
            # Also fall back model to sonnet for capability match (or haiku in live_test)
            model_used = 'haiku' if is_live_test else 'sonnet'

        # Build command based on backend
        # Note: is_dry_run controls prompt wrapping for mock JSON responses
        # live_test uses real prompts but cheap models
        if backend == CLIBackend.CURSOR:
            cmd = self._build_cursor_command(
                full_prompt,
                model_used,
                dry_run=is_dry_run,  # Only wrap for mock responses in dry_run
            )
        else:
            cmd = self._build_command(
                agent_config,
                full_prompt,
                model_override=model_used,
                skills_to_inject=skills,
                inject_finding_classification=inject_finding_classification,
                scope_context=scope_context,
                dry_run=is_dry_run,  # Only wrap for mock responses in dry_run
            )

        dry_run_tag = ' [DRY-RUN]' if is_dry_run else ''
        live_test_tag = (
            ' [LIVE-TEST]' if is_live_test and not is_dry_run else ''
        )
        backend_tag = (
            f' [{backend.value}]' if backend == CLIBackend.CURSOR else ''
        )
        LOG.info(
            f'Running agent: {agent_name}{dry_run_tag}{live_test_tag}{backend_tag} '
            f'(model: {model_used})'
        )
        LOG.debug(f'Command: {" ".join(cmd[:10])}...')

        # Start progress display
        progress = None
        if show_progress:
            progress = SingleAgentProgress(agent_name, model_used or '')
            progress.start()

        # Retry loop
        last_result: AgentResult | None = None
        total_duration = 0.0
        attempt = 0

        while attempt < retry_cfg.max_attempts:
            start_time = time.time()

            try:
                # Use timeout from: explicit > agent config > model-based default
                effective_timeout = timeout or (
                    agent_config._timeout
                    if agent_config._timeout is not None
                    else get_timeout_for_model(model_used or 'sonnet')
                )
                result = self._execute_command(
                    cmd,
                    agent_name,
                    model_used or '',
                    effective_timeout,
                    component_id,
                    backend=backend,
                )

                attempt_duration = time.time() - start_time
                total_duration += attempt_duration
                result.duration = total_duration
                result.retry_attempts = attempt

                if result.success:
                    # Success - stop retrying
                    last_result = result
                    break

                # Failed - classify error and decide retry
                error_type = classify_error(result.error)
                result.error_type = error_type

                if error_type == ErrorType.NON_RETRYABLE:
                    LOG.warning(
                        f'Agent {agent_name} failed with non-retryable error: '
                        f'{result.error}'
                    )
                    last_result = result
                    break

                # Retryable error
                last_result = result
                attempt += 1

                if attempt < retry_cfg.max_attempts:
                    delay = retry_cfg.get_delay(attempt)
                    LOG.info(
                        f'Agent {agent_name} failed (attempt {attempt}/'
                        f'{retry_cfg.max_attempts}), retrying in {delay:.1f}s: '
                        f'{result.error}'
                    )
                    time.sleep(delay)
                else:
                    LOG.error(
                        f'Agent {agent_name} failed after {attempt} attempts: '
                        f'{result.error}'
                    )

            except Exception as e:
                attempt_duration = time.time() - start_time
                total_duration += attempt_duration

                error_type = classify_error(str(e))
                last_result = AgentResult(
                    success=False,
                    error=str(e),
                    duration=total_duration,
                    agent_name=agent_name,
                    model=model_used or '',
                    retry_attempts=attempt,
                    error_type=error_type,
                )

                if error_type == ErrorType.NON_RETRYABLE:
                    LOG.error(f'Agent {agent_name} non-retryable error: {e}')
                    break

                attempt += 1
                if attempt < retry_cfg.max_attempts:
                    delay = retry_cfg.get_delay(attempt)
                    LOG.info(
                        f'Agent {agent_name} error (attempt {attempt}/'
                        f'{retry_cfg.max_attempts}), retrying in {delay:.1f}s: {e}'
                    )
                    time.sleep(delay)
                else:
                    LOG.error(
                        f'Agent {agent_name} failed after {attempt} attempts: {e}'
                    )

        # Stop progress display
        if progress and last_result:
            if last_result.success:
                findings = len(last_result.data.get('issues', []))
                summary = f'{findings} findings' if findings else 'done'
            else:
                summary = 'failed'
            progress.stop(last_result.success, summary)

        # Log trajectory for debugging
        final_result = last_result or AgentResult(
            success=False,
            error='No result produced',
            agent_name=agent_name,
            model=model_used or '',
        )

        if self.trajectory_logger:
            trajectory = AgentTrajectory(
                agent_name=agent_name,
                prompt_hash=TrajectoryLogger.hash_prompt(full_prompt),
                model=model_used or '',
                input_context_keys=list((context or {}).keys()),
                prompt_preview=full_prompt[:500] if full_prompt else '',
                duration_ms=int(final_result.duration * 1000),
                retry_attempts=final_result.retry_attempts,
                success=final_result.success,
                output_preview=final_result.raw_output[:500]
                if final_result.raw_output
                else '',
                structured_keys=list(final_result.data.keys())
                if final_result.data
                else [],
                error=final_result.error or '',
                status=final_result.status,
            )
            self.trajectory_logger.log(trajectory)

        return final_result

    def _execute_command(
        self,
        cmd: list[str],
        agent_name: str,
        model_used: str,
        timeout: int,
        component_id: str | None = None,
        backend: CLIBackend = CLIBackend.CLAUDE,
    ) -> AgentResult:
        """Execute a single command attempt.

        This is the inner execution that can be retried.
        Handles both Claude CLI and cursor-agent output formats.
        """
        result = subprocess.run(
            cmd,
            check=False,
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            return AgentResult(
                success=False,
                error=result.stderr or f'Exit code {result.returncode}',
                raw_output=result.stdout,
                agent_name=agent_name,
                model=model_used,
            )

        # Parse JSON output based on backend
        try:
            if backend == CLIBackend.CURSOR:
                # cursor-agent has different output format
                data = self._parse_cursor_output(result.stdout)
                if data is None:
                    return AgentResult(
                        success=False,
                        error='Failed to parse cursor-agent output',
                        raw_output=result.stdout,
                        agent_name=agent_name,
                        model=model_used,
                    )
            else:
                # Claude CLI output parsing
                output = json.loads(result.stdout)

                # Claude CLI with --json-schema puts structured output in 'structured_output'
                if isinstance(output, dict) and 'structured_output' in output:
                    data = output['structured_output']
                # Fallback: Claude CLI json output has a 'result' field
                elif isinstance(output, dict) and 'result' in output:
                    result_content = output['result']
                    if isinstance(result_content, str):
                        try:
                            data = json.loads(result_content)
                        except json.JSONDecodeError:
                            extracted = self._extract_json(result_content)
                            data = (
                                extracted
                                if extracted
                                else {'raw': result_content}
                            )
                    else:
                        data = result_content
                else:
                    data = output

            agent_result = AgentResult(
                success=True,
                data=data,
                raw_output=result.stdout,
                agent_name=agent_name,
                model=model_used,
            )

            # Update context after successful execution
            self._update_context_from_result(agent_result, component_id)
            return agent_result

        except json.JSONDecodeError as e:
            LOG.warning(f'Failed to parse JSON from {agent_name}: {e}')
            data = self._extract_json(result.stdout)
            if data:
                agent_result = AgentResult(
                    success=True,
                    data=data,
                    raw_output=result.stdout,
                    agent_name=agent_name,
                    model=model_used,
                )
                self._update_context_from_result(agent_result, component_id)
                return agent_result

            return AgentResult(
                success=False,
                error=f'Failed to parse output: {e}',
                raw_output=result.stdout,
                agent_name=agent_name,
                model=model_used,
            )

    def run_prompt(
        self,
        prompt: str,
        model: str = 'opus',
        timeout: int | None = None,
        dry_run: bool | None = None,
    ) -> AgentResult:
        """Run a raw prompt without agent configuration.

        This is a simplified interface for running prompts that don't need
        agent-specific configuration. Useful for self-contained prompts.

        Args:
            prompt: The full prompt to run
            model: Model to use (default: opus)
            timeout: Timeout in seconds
            dry_run: Override dry_run setting

        Returns:
            AgentResult with structured data
        """
        return self.run(
            agent_name='prompt',  # Dummy name
            prompt=prompt,
            model_override=model,
            timeout=timeout,
            dry_run=dry_run,
            show_progress=True,
        )

    def run_parallel(
        self,
        tasks: list[tuple[str, str, dict[str, Any] | None]]
        | list[dict[str, Any]],
        max_workers: int | None = None,
        show_progress: bool = True,
    ) -> list[AgentResult]:
        """Run multiple agents in parallel.

        Args:
            tasks: List of (agent_name, prompt, context) tuples OR
                   List of dicts with keys: name, prompt, context, model, skills
            max_workers: Maximum parallel workers (None = all at once)
            show_progress: Show progress spinner (default True)

        Returns:
            List of AgentResults in same order as tasks
        """
        # Default to running all tasks in parallel
        if max_workers is None:
            max_workers = len(tasks)
        from .progress import create_progress_tracker

        results: list[AgentResult | None] = [None] * len(tasks)

        # Get agent names for progress tracking
        agent_names = [
            task['name'] if isinstance(task, dict) else task[0]
            for task in tasks
        ]

        # Create progress tracker
        tracker = (
            create_progress_tracker(agent_names) if show_progress else None
        )

        def run_task_with_progress(task: tuple | dict, idx: int) -> AgentResult:
            """Run a single task with progress tracking."""
            agent_name = task['name'] if isinstance(task, dict) else task[0]

            if tracker:
                tracker.start_agent(agent_name)

            try:
                if isinstance(task, dict):
                    result = self.run(
                        agent_name=task['name'],
                        prompt=task['prompt'],
                        context=task.get('context'),
                        model_override=task.get('model'),
                        skills=task.get('skills'),
                        show_progress=False,  # Parallel has its own tracker
                    )
                else:
                    # Legacy tuple format
                    agent_name, prompt, context = task
                    result = self.run(
                        agent_name, prompt, context, show_progress=False
                    )

                if tracker:
                    # Summarize result
                    if result.success:
                        findings = len(result.data.get('issues', []))
                        summary = (
                            f'{findings} findings' if findings else 'no issues'
                        )
                    else:
                        summary = 'failed'
                    tracker.complete_agent(agent_name, result.success, summary)

                return result

            except Exception as e:
                if tracker:
                    tracker.complete_agent(agent_name, False, str(e)[:30])
                raise

        # Start progress display
        if tracker:
            tracker.start_display()

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx = {
                    executor.submit(run_task_with_progress, task, idx): idx
                    for idx, task in enumerate(tasks)
                }

                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        results[idx] = future.result()
                    except Exception as e:
                        LOG.error(f'Parallel task {idx} failed: {e}')
                        task = tasks[idx]
                        agent_name = (
                            task['name'] if isinstance(task, dict) else task[0]
                        )
                        results[idx] = AgentResult(
                            success=False,
                            error=str(e),
                            agent_name=agent_name,
                        )
        finally:
            # Stop progress display
            if tracker:
                tracker.stop_display()

        return [r for r in results if r is not None]

    def _format_prompt(
        self,
        agent_config: AgentConfig,
        prompt: str,
        context: dict[str, Any] | None,
        component_id: str | None = None,
        workspace: Workspace | None = None,
    ) -> str:
        """Format prompt with template, context, and persistent context.

        If workspace is provided (PULL model), injects minimal context with
        navigation instructions. Otherwise falls back to legacy context_manager.
        """
        parts = []

        # 1. Workspace context (PULL model) or legacy persistent context
        if workspace and workspace.is_initialized:
            # Use workspace for minimal, agent-specific context injection
            workspace_ctx = workspace.get_context_for_agent(
                agent_config.name,
                component_id,
            )
            if workspace_ctx:
                parts.append(workspace_ctx)
        elif self.context_manager:
            # Legacy: full context injection
            persistent_ctx = self.context_manager.get_context_for_prompt(
                component_id
            )
            if persistent_ctx:
                parts.append(
                    f'## Context from Previous Work\n\n{persistent_ctx}'
                )

        # 2. Template (existing)
        if agent_config.prompt_template:
            template = self._load_template(agent_config.prompt_template)
            if template:
                parts.append(template)

        # 3. Task-specific prompt
        parts.append(prompt)

        # 4. Runtime context (existing) - skip workspace_context since it's injected above
        if context:
            # Filter out workspace_context from runtime context to avoid duplication
            filtered_context = {
                k: v for k, v in context.items() if k != 'workspace_context'
            }
            if filtered_context:
                context_str = '\n'.join(
                    f'{k}: {v}' for k, v in filtered_context.items()
                )
                parts.append(f'## Runtime Context\n\n{context_str}')

        # 5. Context update instructions
        # For workspace: agents write directly to files, so add workspace instructions
        # For legacy: include context update instructions
        if workspace and workspace.is_initialized:
            parts.append(self._get_workspace_update_instructions())
        elif self.context_manager:
            parts.append(self._get_context_update_instructions())

        return '\n\n---\n\n'.join(parts)

    def _get_workspace_update_instructions(self) -> str:
        """Instructions for agent to update workspace files."""
        return """## Workspace Updates

When you discover something important or make decisions, update the workspace:

- **Discoveries**: Append to `.workspace/DISCOVERIES.md` with the Write tool
- **Decisions**: Append to `.workspace/DECISIONS.md` with rationale
- **Blockers**: Update `.workspace/BLOCKERS.md` if blocked
- **Component status**: Update `.workspace/components/<id>.md` with progress

These updates are visible to other agents working on this task."""

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

    def _get_context_update_instructions(self) -> str:
        """Instructions for agent to provide context updates."""
        return """## Context Updates Required

Before completing, provide updates for future agents:
- What did you accomplish? (summary)
- What did you learn? (discoveries)
- What's blocking progress? (blockers)
- Any architectural decisions? (decisions)
- What should the next agent know? (for_next_agent)

Include these in your JSON response."""

    def _update_context_from_result(
        self,
        result: AgentResult,
        component_id: str | None = None,
    ) -> None:
        """Update context files from agent result."""
        if not self.context_manager:
            return

        update = ContextUpdate(
            summary=result.get('summary', ''),
            discoveries=result.get('discoveries', []),
            blockers=result.get('blockers', []),
            decisions=result.get('decisions', []),
            for_next_agent=result.get('for_next_agent', ''),
        )

        if any(
            [
                update.summary,
                update.discoveries,
                update.blockers,
                update.decisions,
                update.for_next_agent,
            ]
        ):
            self.context_manager.update_from_result(update, component_id)

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """Try to extract JSON from text that might have other content."""
        # First, try to find JSON in code blocks (most reliable)
        code_block_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
        ]
        for pattern in code_block_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        # Try to find a complete JSON object with nested braces
        # Find all potential starting positions and try each
        for start_idx in range(len(text)):
            if text[start_idx] != '{':
                continue

            brace_count = 0
            for i, char in enumerate(text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = text[start_idx : i + 1]
                        try:
                            parsed = json.loads(json_str)
                            # Only return if it looks like a valid response
                            if isinstance(parsed, dict):
                                return parsed
                        except json.JSONDecodeError:
                            pass
                        break  # Try next { if this one failed

        return None
