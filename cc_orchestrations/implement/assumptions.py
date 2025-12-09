"""Assumption tracking and threshold logic.

Tracks assumptions made during ticket interpretation and enforces thresholds
to prevent proceeding with too much uncertainty.

Thresholds:
- CRITICAL: Max 2 (core functionality, what the feature does)
- MODERATE: Max 4 (implementation approach, patterns)
- MINOR: Unlimited (naming, file locations)
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

LOG = logging.getLogger(__name__)


class AssumptionLevel(str, Enum):
    """Severity level of an assumption."""

    CRITICAL = 'critical'  # Core functionality - what does the feature do?
    MODERATE = 'moderate'  # Implementation approach - how to build it?
    MINOR = 'minor'  # Details - naming, locations, style


@dataclass
class Assumption:
    """A single assumption made during interpretation."""

    topic: str  # What's ambiguous
    options: list[str]  # Possible interpretations
    chosen: str  # What we chose
    rationale: str  # Why we chose it
    level: AssumptionLevel  # Severity
    risk_if_wrong: str  # What happens if this was wrong

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'topic': self.topic,
            'options': self.options,
            'chosen': self.chosen,
            'rationale': self.rationale,
            'level': self.level.value,
            'risk_if_wrong': self.risk_if_wrong,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Assumption':
        """Create from dictionary."""
        return cls(
            topic=data['topic'],
            options=data['options'],
            chosen=data['chosen'],
            rationale=data['rationale'],
            level=AssumptionLevel(data['level']),
            risk_if_wrong=data['risk_if_wrong'],
        )

    def to_markdown(self) -> str:
        """Format as markdown for comments."""
        level_emoji = {
            AssumptionLevel.CRITICAL: '🔴',
            AssumptionLevel.MODERATE: '🟡',
            AssumptionLevel.MINOR: '🟢',
        }
        emoji = level_emoji.get(self.level, '⚪')

        options_str = ', '.join(self.options) if self.options else 'N/A'
        return f"""### {emoji} {self.topic} ({self.level.value})
**Options considered:** {options_str}
**Chose:** {self.chosen}
**Rationale:** {self.rationale}
**Risk if wrong:** {self.risk_if_wrong}
"""


# Default thresholds
DEFAULT_THRESHOLDS = {
    AssumptionLevel.CRITICAL: 2,
    AssumptionLevel.MODERATE: 4,
    AssumptionLevel.MINOR: float('inf'),  # Unlimited
}


@dataclass
class AssumptionTracker:
    """Tracks assumptions and enforces thresholds."""

    assumptions: list[Assumption] = field(default_factory=list)
    thresholds: dict[AssumptionLevel, int | float] = field(
        default_factory=lambda: DEFAULT_THRESHOLDS.copy()
    )

    def add(self, assumption: Assumption) -> None:
        """Add an assumption."""
        self.assumptions.append(assumption)
        LOG.info(
            f'Assumption added [{assumption.level.value}]: {assumption.topic}'
        )

    def count_by_level(self, level: AssumptionLevel) -> int:
        """Count assumptions at a specific level."""
        return len([a for a in self.assumptions if a.level == level])

    def is_over_threshold(self) -> bool:
        """Check if any level exceeds its threshold."""
        for level in [AssumptionLevel.CRITICAL, AssumptionLevel.MODERATE]:
            count = self.count_by_level(level)
            threshold = self.thresholds.get(level, float('inf'))
            if count > threshold:
                return True
        return False

    def get_threshold_violations(
        self,
    ) -> list[tuple[AssumptionLevel, int, int]]:
        """Get list of (level, count, threshold) for violated thresholds."""
        violations = []
        for level in [AssumptionLevel.CRITICAL, AssumptionLevel.MODERATE]:
            count = self.count_by_level(level)
            threshold = self.thresholds.get(level, float('inf'))
            if count > threshold:
                violations.append((level, count, int(threshold)))
        return violations

    def get_stop_reason(self) -> str:
        """Get human-readable reason for stopping."""
        violations = self.get_threshold_violations()
        if not violations:
            return ''

        parts = []
        for level, count, threshold in violations:
            parts.append(f'{count} {level.value} assumptions (max {threshold})')

        return f'Too many assumptions needed: {", ".join(parts)}'

    def to_markdown(self, include_header: bool = True) -> str:
        """Format all assumptions as markdown."""
        if not self.assumptions:
            return 'No assumptions made.'

        lines = []
        if include_header:
            lines.append('# Assumptions Made During Implementation\n')
            lines.append(
                'The following assumptions were made due to ambiguity '
                'in the ticket. Please verify these are correct.\n'
            )

        # Group by level
        for level in [
            AssumptionLevel.CRITICAL,
            AssumptionLevel.MODERATE,
            AssumptionLevel.MINOR,
        ]:
            level_assumptions = [
                a for a in self.assumptions if a.level == level
            ]
            if level_assumptions:
                lines.append(f'## {level.value.title()} Assumptions\n')
                for assumption in level_assumptions:
                    lines.append(assumption.to_markdown())

        return '\n'.join(lines)

    def to_jira_comment(self) -> str:
        """Format for Jira comment (uses Jira wiki markup)."""
        if not self.assumptions:
            return 'No assumptions made.'

        lines = ['h2. Assumptions Made During Automated Implementation\n']
        lines.append(
            'The following assumptions were made. Please verify these are correct.\n'
        )

        for level in [
            AssumptionLevel.CRITICAL,
            AssumptionLevel.MODERATE,
            AssumptionLevel.MINOR,
        ]:
            level_assumptions = [
                a for a in self.assumptions if a.level == level
            ]
            if level_assumptions:
                emoji = {'critical': '(!)', 'moderate': '(!)', 'minor': '(i)'}
                lines.append(
                    f'\nh3. {emoji.get(level.value, "")} {level.value.title()} Assumptions\n'
                )
                for a in level_assumptions:
                    lines.append(f'*{a.topic}*')
                    lines.append(f'* Options: {", ".join(a.options)}')
                    lines.append(f'* Chose: {a.chosen}')
                    lines.append(f'* Rationale: {a.rationale}')
                    lines.append(f'* Risk if wrong: {a.risk_if_wrong}')
                    lines.append('')

        return '\n'.join(lines)

    def save(self, path: Path) -> None:
        """Save to JSON file."""
        data = {
            'assumptions': [a.to_dict() for a in self.assumptions],
            'thresholds': {k.value: v for k, v in self.thresholds.items()},
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> 'AssumptionTracker':
        """Load from JSON file."""
        if not path.exists():
            return cls()

        data = json.loads(path.read_text())
        tracker = cls()
        tracker.assumptions = [
            Assumption.from_dict(a) for a in data.get('assumptions', [])
        ]
        if 'thresholds' in data:
            tracker.thresholds = {
                AssumptionLevel(k): v for k, v in data['thresholds'].items()
            }
        return tracker
