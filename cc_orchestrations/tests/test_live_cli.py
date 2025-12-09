"""Live CLI integration tests.

These tests actually invoke the claude and cursor-agent CLIs to verify
the full integration works end-to-end with real (but cheap) models.

Run with: pytest tests/test_live_cli.py -v --live-cli
Skip with: pytest -m "not live_cli"

Model selection in live_test mode:
- Claude CLI agents -> haiku (fast, cheap)
- cursor-agent agents -> composer-1 (fast, cheap)
"""

import os
import tempfile
from pathlib import Path

import pytest

# Mark all tests in this module as live_cli tests (opt-in)
pytestmark = [pytest.mark.live_cli]


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        'markers',
        'live_cli: marks tests that invoke real CLI tools (opt-in with --live-cli)',
    )


@pytest.fixture
def work_dir():
    """Create temporary work directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def live_config():
    """Create test config with live_test enabled."""
    from cc_orchestrations.core.config import Config

    claude_path = os.path.expanduser('~/.claude/local/claude')
    return Config(
        name='live-test',
        dry_run=False,  # NOT dry_run - we want real execution
        live_test=True,  # Use cheap models but real execution
        claude_path=claude_path,
        default_model='sonnet',  # Will be overridden to haiku by live_test
    )


@pytest.fixture
def live_runner(live_config, work_dir):
    """Create AgentRunner for live CLI tests."""
    from cc_orchestrations.core.runner import AgentRunner

    return AgentRunner(
        config=live_config,
        work_dir=work_dir,
        live_test=True,
    )


class TestClaudeCLI:
    """Tests that exercise the Claude Code CLI with haiku."""

    def test_simple_prompt_returns_json(self, live_runner):
        """Test Claude CLI can return JSON response."""
        result = live_runner.run(
            agent_name='claude-test',
            prompt="""Return a JSON object with these fields:
- status: "ok"
- message: "Claude CLI working"
- model: the model you're using

Return ONLY the JSON, no other text.""",
            show_progress=True,
        )

        assert result.success, f'Claude CLI failed: {result.error}'
        assert result.duration > 0
        # Should have some data (either parsed JSON or raw output)
        assert result.data or result.raw_output
        print(f'\nClaude response: {result.data or result.raw_output[:200]}')

    def test_claude_uses_haiku_in_live_test(self, live_runner):
        """Verify live_test mode forces haiku model."""
        result = live_runner.run(
            agent_name='model-check',
            prompt='Return JSON: {"model": "the model answering this"}',
            model_override='opus',  # Try to use opus - should be overridden
            show_progress=True,
        )

        assert result.success, f'Failed: {result.error}'
        # The runner should have used haiku despite opus override
        assert result.model == 'haiku', f'Expected haiku, got {result.model}'

    def test_claude_handles_code_task(self, live_runner, work_dir):
        """Test Claude can do a simple code-related task."""
        # Create a test file
        test_file = work_dir / 'example.py'
        test_file.write_text('def add(a, b):\n    return a + b\n')

        result = live_runner.run(
            agent_name='code-reader',
            prompt=f"""Read the file at {test_file} and return JSON:
{{
    "file_exists": true/false,
    "function_name": "name of function found",
    "line_count": number of lines
}}

Return ONLY JSON.""",
            show_progress=True,
        )

        assert result.success, f'Failed: {result.error}'
        print(f'\nCode task response: {result.data or result.raw_output[:200]}')


class TestCursorAgentCLI:
    """Tests that exercise the cursor-agent CLI with composer-1."""

    @pytest.fixture
    def cursor_available(self, live_runner):
        """Check if cursor-agent is available."""
        if not live_runner.is_cursor_available():
            pytest.skip('cursor-agent not available')
        return True

    def test_cursor_simple_prompt(self, live_runner, cursor_available):
        """Test cursor-agent CLI can return response."""
        result = live_runner.run(
            agent_name='cursor-test',
            prompt="""Return a JSON object:
{"status": "ok", "message": "cursor-agent working", "backend": "cursor"}

Return ONLY JSON.""",
            model_override='composer-1',  # Force cursor backend
            show_progress=True,
        )

        assert result.success, f'cursor-agent failed: {result.error}'
        assert result.duration > 0
        print(f'\nCursor response: {result.data or result.raw_output[:200]}')

    def test_cursor_uses_composer1_in_live_test(
        self, live_runner, cursor_available
    ):
        """Verify live_test mode uses composer-1 for cursor backend."""
        result = live_runner.run(
            agent_name='cursor-model-check',
            prompt='Return JSON: {"status": "ok"}',
            model_override='gpt-5.1',  # Cursor model - should become composer-1
            show_progress=True,
        )

        assert result.success, f'Failed: {result.error}'
        # Should use composer-1 (cheap cursor model) in live_test
        assert result.model == 'composer-1', (
            f'Expected composer-1, got {result.model}'
        )

    def test_cursor_diverse_opinion(self, live_runner, cursor_available):
        """Test cursor-agent for getting diverse model opinion."""
        result = live_runner.run(
            agent_name='opinion-test',
            prompt="""Analyze this code pattern and return JSON:
```python
data = []
for item in items:
    if item.valid:
        data.append(item.value)
```

Return: {"opinion": "your brief analysis", "suggestion": "any improvement"}""",
            model_override='composer-1',
            show_progress=True,
        )

        assert result.success, f'Failed: {result.error}'
        print(f'\nDiverse opinion: {result.data or result.raw_output[:300]}')


class TestBackendRouting:
    """Tests for correct backend selection in live_test mode."""

    def test_claude_models_route_to_claude(self, live_runner):
        """Claude models (opus, sonnet, haiku) should use Claude CLI."""
        from cc_orchestrations.core.config import (
            CLIBackend,
            get_backend_for_model,
        )

        for model in ['opus', 'sonnet', 'haiku']:
            backend = get_backend_for_model(model)
            assert backend == CLIBackend.CLAUDE, f'{model} should use Claude'

    def test_cursor_models_route_to_cursor(self, live_runner):
        """Cursor models should use cursor-agent CLI."""
        from cc_orchestrations.core.config import (
            CLIBackend,
            get_backend_for_model,
        )

        for model in ['composer-1', 'gpt-5.1', 'gemini-3-pro', 'grok']:
            backend = get_backend_for_model(model)
            assert backend == CLIBackend.CURSOR, f'{model} should use cursor'

    def test_live_test_overrides_to_cheap_models(self, live_runner):
        """live_test mode should use haiku/composer-1 regardless of config."""
        # This is tested by running agents and checking result.model
        # The actual model used should be haiku (Claude) or composer-1 (cursor)
        pass  # Covered by other tests


class TestParallelExecution:
    """Tests for parallel agent execution with both backends."""

    @pytest.fixture
    def cursor_available(self, live_runner):
        """Check if cursor-agent is available."""
        if not live_runner.is_cursor_available():
            pytest.skip('cursor-agent not available')
        return True

    def test_parallel_claude_agents(self, live_runner):
        """Test multiple Claude agents run in parallel."""
        tasks = [
            {
                'name': f'parallel-claude-{i}',
                'prompt': f'Return JSON: {{"task": {i}, "status": "complete"}}',
                'model': 'haiku',
            }
            for i in range(3)
        ]

        results = live_runner.run_parallel(tasks, max_workers=3)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.success, f'Task {i} failed: {result.error}'

    def test_mixed_backend_parallel(self, live_runner, cursor_available):
        """Test Claude and cursor agents running in parallel."""
        tasks = [
            # Claude agent
            {
                'name': 'parallel-claude',
                'prompt': 'Return JSON: {"backend": "claude", "status": "ok"}',
                'model': 'haiku',
            },
            # Cursor agent
            {
                'name': 'parallel-cursor',
                'prompt': 'Return JSON: {"backend": "cursor", "status": "ok"}',
                'model': 'composer-1',
            },
        ]

        results = live_runner.run_parallel(tasks, max_workers=2)

        assert len(results) == 2
        for result in results:
            assert result.success, f'{result.agent_name} failed: {result.error}'

        print(f'\nClaude result: {results[0].data}')
        print(f'Cursor result: {results[1].data}')


class TestErrorHandling:
    """Tests for error handling with real CLIs."""

    def test_invalid_json_handling(self, live_runner):
        """Test graceful handling of non-JSON responses."""
        result = live_runner.run(
            agent_name='invalid-json-test',
            prompt='Just say hello, do not return JSON.',
            show_progress=True,
        )

        # Should still succeed, just with raw_output instead of parsed data
        # The runner tries to extract JSON but falls back gracefully
        assert result.raw_output or result.data

    def test_timeout_handling(self, live_runner):
        """Test timeout is respected."""
        result = live_runner.run(
            agent_name='timeout-test',
            prompt='Return JSON: {"status": "ok"}',
            timeout=60,  # Short but reasonable timeout
            show_progress=True,
        )

        # Should complete well within timeout
        assert result.duration < 60
