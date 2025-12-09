"""Pytest configuration and shared fixtures.

Test Tiers:
- unit: Fast tests with no external dependencies
- integration: Tests that use dry-run mode with haiku
- e2e: Full workflow tests (expensive)
- live_cli: Tests that invoke real CLIs (opt-in with --live-cli)

Usage:
    pytest                     # All tests except live_cli
    pytest -m unit             # Unit tests only
    pytest -m integration      # Integration tests only
    pytest -m e2e              # E2E tests only
    pytest -m "not slow"       # Skip slow tests
    pytest --live-cli          # Include live CLI tests (claude + cursor-agent)
"""

import os
import tempfile
from pathlib import Path

import pytest


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        '--live-cli',
        action='store_true',
        default=False,
        help='Run live CLI tests (invokes real claude and cursor-agent CLIs)',
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        'markers', 'unit: Unit tests (fast, no dependencies)'
    )
    config.addinivalue_line(
        'markers', 'integration: Integration tests (dry-run mode)'
    )
    config.addinivalue_line('markers', 'e2e: End-to-end tests (full workflow)')
    config.addinivalue_line('markers', 'slow: Slow running tests')
    config.addinivalue_line(
        'markers',
        'live_cli: Live CLI tests (opt-in, invokes real claude/cursor-agent)',
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on file location and handle --live-cli flag."""
    run_live_cli = config.getoption('--live-cli')

    for item in items:
        # Auto-mark based on filename
        if 'test_core_' in item.nodeid or 'test_prompts' in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif 'test_integration' in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif 'test_e2e' in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        elif 'test_live_cli' in item.nodeid:
            item.add_marker(pytest.mark.live_cli)

        # Skip live_cli tests unless --live-cli flag is provided
        if 'live_cli' in [m.name for m in item.iter_markers()]:
            if not run_live_cli:
                item.add_marker(
                    pytest.mark.skip(
                        reason='Live CLI tests require --live-cli flag'
                    )
                )


@pytest.fixture(scope='session')
def claude_available():
    """Check if Claude CLI is available."""
    claude_path = os.path.expanduser('~/.claude/local/claude')
    return os.path.exists(claude_path)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_spec_content():
    """Standard mock spec content for tests."""
    return """# Test Feature

## Summary
A test feature for unit testing.

## Components

### src/main.py
- Purpose: Main entry point
- Depends on: None
- Complexity: low

### tests/test_main.py
- Purpose: Tests
- Depends on: src/main.py
- Complexity: low

## Quality Requirements
- Tests pass
- Type hints

## Success Criteria
- Feature works
"""


@pytest.fixture
def mock_project(temp_dir, mock_spec_content):
    """Create a mock project structure."""
    # Create spec
    spec_dir = temp_dir / '.spec'
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / 'SPEC.md').write_text(mock_spec_content)

    # Create project structure
    (temp_dir / 'src').mkdir(exist_ok=True)
    (temp_dir / 'tests').mkdir(exist_ok=True)
    (temp_dir / 'src' / '__init__.py').touch()
    (temp_dir / 'tests' / '__init__.py').touch()

    return temp_dir


@pytest.fixture
def dry_run_config():
    """Create config with dry-run enabled."""
    from cc_orchestrations.core.config import Config

    claude_path = os.path.expanduser('~/.claude/local/claude')
    return Config(
        name='test',
        dry_run=True,
        claude_path=claude_path,
        default_model='haiku',
    )


@pytest.fixture
def live_test_config():
    """Create config with live_test enabled.

    live_test mode:
    - Uses real CLIs (claude + cursor-agent)
    - Claude agents -> haiku (cheap)
    - Cursor agents -> composer-1 (cheap)
    - No mock JSON wrapper - real execution
    """
    from cc_orchestrations.core.config import Config

    claude_path = os.path.expanduser('~/.claude/local/claude')
    return Config(
        name='live-test',
        dry_run=False,  # Real execution
        live_test=True,  # Use cheap models
        claude_path=claude_path,
        default_model='sonnet',  # Will be overridden by live_test
    )


@pytest.fixture(scope='session')
def cursor_available():
    """Check if cursor-agent CLI is available."""
    cursor_path = os.path.expanduser('~/.local/bin/cursor-agent')
    return os.path.exists(cursor_path)
