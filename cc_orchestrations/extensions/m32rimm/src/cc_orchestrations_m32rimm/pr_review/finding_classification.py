"""m32rimm-specific finding classification rules.

Implements the finding classification guide to identify real issues,
false positives, and context-dependent patterns.

NOTE: This module imports FindingClassification from the base cc_orchestrations
package to ensure type compatibility with PRReviewConfig.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Import base class from main package for type compatibility
from cc_orchestrations.pr_review.config import FindingClassification


class Severity(str, Enum):
    """Finding severity levels."""

    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class Classification(str, Enum):
    """Finding classification outcomes."""

    ALWAYS_FLAG = 'always_flag'  # Real issue
    FALSE_POSITIVE = 'false_positive'  # Not an issue
    CONTEXT_DEPENDENT = 'context_dependent'  # Needs investigation


@dataclass
class FindingPattern:
    """Pattern for matching findings.

    Attributes:
        pattern: Regex pattern to match finding text
        classification: Classification outcome
        severity: Severity level (if ALWAYS_FLAG)
        reason: Why this classification
    """

    pattern: str
    classification: Classification
    severity: Severity | None = None
    reason: str = ''


# =============================================================================
# ALWAYS FLAG (Real Issues)
# =============================================================================

ALWAYS_FLAG_PATTERNS = [
    FindingPattern(
        pattern=r'mongo.*call.*inside.*loop',
        classification=Classification.ALWAYS_FLAG,
        severity=Severity.HIGH,
        reason='Mongo calls in loops scale badly regardless of collection size',
    ),
    FindingPattern(
        pattern=r'race.*condition',
        classification=Classification.ALWAYS_FLAG,
        severity=Severity.HIGH,
        reason='Race conditions happen at scale even if rare',
    ),
    FindingPattern(
        pattern=r'error.*raised.*late|error.*detection.*point',
        classification=Classification.ALWAYS_FLAG,
        severity=Severity.MEDIUM,
        reason='Should raise RuntimeError at detection point',
    ),
    FindingPattern(
        pattern=r'missing.*retry_run|without.*retry_run|no.*retry_run',
        classification=Classification.ALWAYS_FLAG,
        severity=Severity.HIGH,
        reason='Network blips crash the process without retry_run',
    ),
    FindingPattern(
        pattern=r'missing.*subID.*filter|no.*subID|subID.*not.*filtered',
        classification=Classification.ALWAYS_FLAG,
        severity=Severity.CRITICAL,
        reason='Cross-tenant data exposure - CRITICAL security issue',
    ),
    FindingPattern(
        pattern=r'flush.*missing|no.*flush.*before.*aggregation|missing.*flush.*before',
        classification=Classification.ALWAYS_FLAG,
        severity=Severity.CRITICAL,
        reason='Data loss - aggregates stale data without flush',
    ),
    FindingPattern(
        pattern=r'breaking.*change.*shared.*utility|shared.*utility.*breaking',
        classification=Classification.ALWAYS_FLAG,
        severity=Severity.HIGH,
        reason='Breaking changes to shared code - check blast radius',
    ),
]


# =============================================================================
# NEVER FLAG (Known False Positives)
# =============================================================================

FALSE_POSITIVE_PATTERNS = [
    FindingPattern(
        pattern=r'KeyError.*not.*caught.*required.*field|required.*field.*KeyError',
        classification=Classification.FALSE_POSITIVE,
        reason='Intentional crash - we want failure on missing required data',
    ),
    FindingPattern(
        pattern=r'subscription.*config.*not.*validated|missing.*validation.*config',
        classification=Classification.FALSE_POSITIVE,
        reason='Intentional crash - missing config should fail loudly',
    ),
    FindingPattern(
        pattern=r'already.*addressed.*MR|resolved.*in.*discussion|MR.*thread.*resolved',
        classification=Classification.FALSE_POSITIVE,
        reason='Already addressed in MR discussion threads',
    ),
    FindingPattern(
        pattern=r'theoretical.*issue.*can.*t.*happen|cannot.*happen.*in.*code',
        classification=Classification.FALSE_POSITIVE,
        reason='Theoretical issue without proof it can happen',
    ),
    FindingPattern(
        pattern=r'performance.*small.*collection|small.*rarely.*queried',
        classification=Classification.FALSE_POSITIVE,
        reason='Performance on small, rarely-queried collection is not an issue',
    ),
    FindingPattern(
        pattern=r'could.*add.*validation.*without.*crash',
        classification=Classification.FALSE_POSITIVE,
        reason="If it won't actually break, don't flag",
    ),
]


# =============================================================================
# CONTEXT-DEPENDENT (Investigate First)
# =============================================================================

CONTEXT_DEPENDENT_PATTERNS = [
    FindingPattern(
        pattern=r'missing.*try.*except|no.*error.*handling|except.*missing',
        classification=Classification.CONTEXT_DEPENDENT,
        reason="FLAG if external API/network/DB write, DON'T FLAG if internal function",
    ),
    FindingPattern(
        pattern=r'no.*type.*hints|missing.*type.*hints|type.*hints.*missing',
        classification=Classification.CONTEXT_DEPENDENT,
        reason="FLAG if new code or public API, DON'T FLAG if legacy code",
    ),
    FindingPattern(
        pattern=r'performance.*concern|performance.*issue|slow.*query',
        classification=Classification.CONTEXT_DEPENDENT,
        reason="FLAG if high-frequency path/large collection/loop, DON'T FLAG if one-time op",
    ),
    FindingPattern(
        pattern=r'missing.*logging|no.*logging|logging.*missing',
        classification=Classification.CONTEXT_DEPENDENT,
        reason="FLAG if error path or important state change, DON'T FLAG if happy path",
    ),
]


# =============================================================================
# CLASSIFICATION FUNCTIONS
# =============================================================================


def is_always_flag(
    finding: dict[str, Any],
) -> tuple[bool, FindingPattern | None]:
    """Check if finding matches ALWAYS FLAG patterns.

    Args:
        finding: Finding dict with 'issue' key

    Returns:
        Tuple of (is_match, pattern) where pattern is None if no match
    """
    issue_text = finding.get('issue', '').lower()

    for pattern in ALWAYS_FLAG_PATTERNS:
        if re.search(pattern.pattern, issue_text, re.IGNORECASE):
            return True, pattern

    return False, None


def is_false_positive(
    finding: dict[str, Any],
) -> tuple[bool, FindingPattern | None]:
    """Check if finding matches FALSE POSITIVE patterns.

    Args:
        finding: Finding dict with 'issue' key

    Returns:
        Tuple of (is_match, pattern) where pattern is None if no match
    """
    issue_text = finding.get('issue', '').lower()

    for pattern in FALSE_POSITIVE_PATTERNS:
        if re.search(pattern.pattern, issue_text, re.IGNORECASE):
            return True, pattern

    return False, None


def is_context_dependent(
    finding: dict[str, Any],
) -> tuple[bool, FindingPattern | None]:
    """Check if finding matches CONTEXT-DEPENDENT patterns.

    Args:
        finding: Finding dict with 'issue' key

    Returns:
        Tuple of (is_match, pattern) where pattern is None if no match
    """
    issue_text = finding.get('issue', '').lower()

    for pattern in CONTEXT_DEPENDENT_PATTERNS:
        if re.search(pattern.pattern, issue_text, re.IGNORECASE):
            return True, pattern

    return False, None


def classify_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Classify a finding using m32rimm-specific rules.

    Args:
        finding: Raw finding from reviewer

    Returns:
        Classified finding with classification, severity adjustments, and reasoning
    """
    # Check ALWAYS FLAG first
    is_real, pattern = is_always_flag(finding)
    if is_real and pattern:
        finding['classification'] = Classification.ALWAYS_FLAG.value
        finding['classification_reason'] = pattern.reason

        # Apply severity if specified
        if pattern.severity:
            old_severity = finding.get('severity', 'unknown')
            finding['severity'] = pattern.severity.value
            if old_severity != pattern.severity.value:
                finding['severity_upgraded'] = True
                finding['severity_upgrade_reason'] = (
                    f'Pattern match: {pattern.reason}'
                )

        return finding

    # Check FALSE POSITIVE
    is_false, pattern = is_false_positive(finding)
    if is_false and pattern:
        finding['classification'] = Classification.FALSE_POSITIVE.value
        finding['classification_reason'] = pattern.reason
        finding['false_positive'] = True
        return finding

    # Check CONTEXT-DEPENDENT
    is_context, pattern = is_context_dependent(finding)
    if is_context and pattern:
        finding['classification'] = Classification.CONTEXT_DEPENDENT.value
        finding['classification_reason'] = pattern.reason
        finding['needs_investigation'] = True
        return finding

    # No pattern match - default to context-dependent
    finding['classification'] = Classification.CONTEXT_DEPENDENT.value
    finding['classification_reason'] = 'No pattern match - needs manual review'
    finding['needs_investigation'] = True

    return finding


# =============================================================================
# M32RIMM FINDING CLASSIFIER
# =============================================================================


class M32RIMMFindingClassifier(FindingClassification):
    """m32rimm-specific finding classifier.

    Implements FindingClassification interface with m32rimm patterns.
    """

    def __init__(self) -> None:
        """Initialize classifier with m32rimm patterns."""
        super().__init__()

        # Populate severity rules
        self.severity_rules = {
            'critical': [
                'missing subID filter',
                'flush missing before aggregation',
                'cross-tenant data exposure',
            ],
            'high': [
                'mongo call inside loop',
                'race condition',
                'missing retry_run',
                'breaking change shared utility',
            ],
            'medium': [
                'error raised late',
                'missing error handling on external API',
            ],
            'low': [
                'missing logging',
                'no type hints on new code',
            ],
        }

        # Populate false positive patterns
        self.false_positive_patterns = [
            'KeyError on required field',
            'subscription config not validated',
            'already addressed in MR',
            'theoretical issue',
            'performance on small collection',
        ]

    def classify_finding(self, finding: dict[str, Any]) -> dict[str, Any]:
        """Classify a finding using m32rimm rules.

        Args:
            finding: Raw finding from reviewer

        Returns:
            Classified finding with severity, category, and metadata
        """
        return classify_finding(finding)
