"""Prompt loading utilities for PR review workflow.

Prompts are stored in separate .txt files for maintainability.
This module provides clean loading with variable substitution.
"""

from pathlib import Path
from typing import Any

# Prompts directory
PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str, **kwargs: Any) -> str:
    """Load a prompt from file with optional variable substitution.

    Args:
        name: Prompt name (without .txt extension)
        **kwargs: Variables to substitute in the prompt

    Returns:
        Formatted prompt string

    Example:
        prompt = load_prompt('triage', ticket_id='INT-1234', diff_files=['a.py', 'b.py'])
    """
    prompt_file = PROMPTS_DIR / f'{name}.txt'

    if not prompt_file.exists():
        raise FileNotFoundError(f'Prompt not found: {prompt_file}')

    content = prompt_file.read_text()

    # Substitute variables if provided
    # Uses safe substitution - missing keys are left as-is
    if kwargs:
        for key, value in kwargs.items():
            # Handle lists and other types
            if isinstance(value, (list, tuple)):
                value = '\n'.join(f'- {item}' for item in value)
            elif not isinstance(value, str):
                value = str(value)
            content = content.replace(f'{{{key}}}', value)

    return content


def build_prompt(*parts: str, separator: str = '\n\n') -> str:
    """Build a prompt from multiple parts.

    Use this for combining static prompts with dynamic context.

    Args:
        *parts: Prompt parts to combine
        separator: Separator between parts (default: double newline)

    Returns:
        Combined prompt string

    Example:
        prompt = build_prompt(
            load_prompt('triage'),
            '## Changed Files',
            '\\n'.join(diff_files),
            '## Available Reviewers',
            reviewer_list
        )
    """
    return separator.join(p.strip() for p in parts if p.strip())


# Common prompt parts for reuse
WORKTREE_INSTRUCTIONS = """
## Worktree Access

You have access to TWO worktrees for investigation:

- **PR Worktree (code WITH changes):** `{pr_worktree}`
- **Base Worktree (code BEFORE changes):** `{base_worktree}`

**IMPORTANT:** Use the FULL PATH with the worktree prefix when reading files or grepping.

Examples:
- Read changed file: `Read({pr_worktree}/path/to/file.py)`
- Grep for usages: `Grep(pattern="function_name", path="{pr_worktree}")`
- Compare before/after: Read from both worktrees
"""

JSON_OUTPUT_INSTRUCTIONS = """
## Output Format

Return your response as valid JSON with this structure:
```json
{
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "issue": "Brief description",
      "file": "path/to/file.py",
      "line": 123,
      "details": "Detailed explanation",
      "recommendation": "How to fix"
    }
  ],
  "summary": "Brief summary of your review",
  "no_issues_reason": "If no issues, explain why code looks good"
}
```

If no issues found: `{"issues": [], "summary": "...", "no_issues_reason": "..."}`
Return ONLY valid JSON, no prose.
"""


# Prompt name constants
class PromptNames:
    """Prompt file names for type-safe loading."""

    TRIAGE = 'triage'
    FINDING_VALIDATOR = 'finding_validator'
    REQUIREMENTS_REVIEWER = 'requirements_reviewer'
    SIDE_EFFECTS_REVIEWER = 'side_effects_reviewer'
    TEST_COVERAGE_REVIEWER = 'test_coverage_reviewer'
    ARCHITECTURE_REVIEWER = 'architecture_reviewer'
    COUNCIL_REVIEWER = 'council_reviewer'
    BLIND_SPOT_HUNTER = 'blind_spot_hunter'
    CONCLUSION_VALIDATOR = 'conclusion_validator'
    INTERACTION_INVESTIGATOR = 'interaction_investigator'
    MR_THREAD_CLASSIFIER = 'mr_thread_classifier'
    PHASE3_SYNTHESIS = 'phase3_synthesis'  # Cross-pollination analysis
