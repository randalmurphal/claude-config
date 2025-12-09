"""Unit tests for prompt loading and management.

Tests embedded prompts are accessible and properly formatted.
"""

import pytest

from cc_orchestrations.pr_review.prompts import (
    WORKTREE_INSTRUCTIONS,
    load_prompt,
)
from cc_orchestrations.prompts import PROMPTS


class TestEmbeddedPrompts:
    """Tests for embedded prompt templates."""

    def test_prompts_dict_exists(self):
        """PROMPTS dict should exist and have content."""
        assert PROMPTS is not None
        assert isinstance(PROMPTS, dict)
        assert len(PROMPTS) > 0

    def test_implementation_prompts_exist(self):
        """Implementation-related prompts should exist."""
        # Check for prompts that actually exist in the module
        expected = ['implementation', 'investigation', 'pr_review']
        for name in expected:
            assert name in PROMPTS, f'Missing prompt: {name}'
            assert len(PROMPTS[name]) > 50, f'Prompt {name} too short'

    def test_prompts_have_content(self):
        """All prompts should have meaningful content."""
        for name, content in PROMPTS.items():
            assert isinstance(content, str), f'Prompt {name} is not a string'
            assert len(content) > 20, f'Prompt {name} too short'


class TestPRReviewPrompts:
    """Tests for PR review prompts."""

    def test_load_triage_prompt(self):
        """Test loading triage prompt."""
        content = load_prompt('triage')
        assert content is not None
        assert len(content) > 100

    def test_load_finding_validator_prompt(self):
        """Test loading finding validator prompt."""
        content = load_prompt('finding_validator')
        assert content is not None
        assert len(content) > 100

    def test_load_nonexistent_prompt_raises(self):
        """Loading nonexistent prompt should raise error."""
        with pytest.raises(FileNotFoundError):
            load_prompt('nonexistent_prompt_xyz')

    def test_worktree_instructions_exist(self):
        """Worktree instructions constant should exist."""
        assert WORKTREE_INSTRUCTIONS is not None
        assert isinstance(WORKTREE_INSTRUCTIONS, str)
        assert len(WORKTREE_INSTRUCTIONS) > 10


class TestPromptFormats:
    """Tests for prompt format consistency."""

    def test_prompts_are_strings(self):
        """All prompts should be strings."""
        for name, content in PROMPTS.items():
            assert isinstance(content, str), f'Prompt {name} is not a string'

    def test_prompts_not_empty(self):
        """No prompt should be empty."""
        for name, content in PROMPTS.items():
            assert content.strip(), f'Prompt {name} is empty'

    def test_prompts_have_reasonable_length(self):
        """Prompts should have reasonable content."""
        for name, content in PROMPTS.items():
            # At least 20 chars (some minimal instruction)
            assert len(content) >= 20, (
                f'Prompt {name} too short: {len(content)} chars'
            )
            # Not absurdly long (token efficiency)
            assert len(content) < 50000, (
                f'Prompt {name} too long: {len(content)} chars'
            )


class TestPRReviewPromptFiles:
    """Test that PR review prompt files are loadable."""

    def test_all_pr_review_prompts_load(self):
        """All expected PR review prompts should load."""
        expected_prompts = [
            'triage',
            'finding_validator',
            'requirements_reviewer',
            'architecture_reviewer',
            'council_reviewer',
            'blind_spot_hunter',
        ]

        for prompt_name in expected_prompts:
            content = load_prompt(prompt_name)
            assert content, f'Prompt {prompt_name} loaded empty'
            assert len(content) > 50, f'Prompt {prompt_name} too short'
