#!/opt/envs/py3.13/bin/python
"""
No Fallback Enforcer
====================
Stores and enforces patterns to prevent Claude from writing fallback logic
or degraded error handling. Forces proper solutions or clear failures.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))
from universal_learner import get_learner


class NoFallbackEnforcer:
    """Enforce no-fallback patterns and prevent degraded solutions."""

    def __init__(self):
        self.learner = get_learner()
        self.initialize_no_fallback_patterns()

    def initialize_no_fallback_patterns(self):
        """Store critical NO_FALLBACK patterns in ANCHORS tier."""

        patterns = [
            {
                "type": "forbidden_pattern",
                "subtype": "silent_fallback",
                "content": "NEVER write try/except that silently falls back to simpler logic",
                "examples": {
                    "bad": [
                        "try:\n    advanced_method()\nexcept:\n    simple_method()",
                        "try:\n    result = complex_operation()\nexcept:\n    result = None",
                        "except Exception:\n    pass  # Silent failure"
                    ],
                    "good": [
                        "# Fix the actual implementation\nadvanced_method()  # Make this work properly",
                        "# Explicit error\nif not prereq:\n    raise ValueError('Missing prerequisite')",
                        "# Clear failure\nexcept SpecificError as e:\n    raise RuntimeError(f'Operation failed: {e}')"
                    ]
                },
                "confidence": 1.0,
                "tier": "ANCHORS"
            },
            {
                "type": "forbidden_pattern",
                "subtype": "feature_detection_fallback",
                "content": "NEVER check if features are available and fall back to worse alternatives",
                "examples": {
                    "bad": [
                        "if has_advanced_lib:\n    use_advanced()\nelse:\n    use_basic()",
                        "try:\n    import advanced_module\nexcept ImportError:\n    use_fallback = True",
                        "if not feature_available():\n    return simplified_version()"
                    ],
                    "good": [
                        "# Require the dependency\nimport advanced_module  # Add to requirements if missing",
                        "# Fail clearly\nif not feature:\n    raise NotImplementedError('Feature X required')",
                        "# Fix the environment\nassert has_requirement, 'Install X first'"
                    ]
                },
                "confidence": 1.0,
                "tier": "ANCHORS"
            },
            {
                "type": "forbidden_pattern",
                "subtype": "error_masking",
                "content": "NEVER hide errors by returning None, empty, or default values",
                "examples": {
                    "bad": [
                        "except:\n    return None",
                        "except:\n    return []",
                        "except:\n    return {}",
                        "except:\n    return ''",
                        "except:\n    return default_value"
                    ],
                    "good": [
                        "# Let errors bubble up\n# Don't catch what you can't handle",
                        "# Specific handling\nexcept FileNotFoundError:\n    raise FileNotFoundError(f'Config file {path} not found')",
                        "# Re-raise with context\nexcept Exception as e:\n    raise RuntimeError(f'Failed to process: {e}') from e"
                    ]
                },
                "confidence": 1.0,
                "tier": "ANCHORS"
            },
            {
                "type": "forbidden_pattern",
                "subtype": "degraded_retry",
                "content": "NEVER retry with simpler logic on failure",
                "examples": {
                    "bad": [
                        "for method in [advanced, intermediate, basic]:\n    try:\n        return method()\n    except:\n        continue",
                        "if not try_optimal():\n    return try_suboptimal()",
                        "retries = [(complex_way, {}), (simple_way, {})]"
                    ],
                    "good": [
                        "# Fix the root cause\nresult = advanced()  # Make this reliable",
                        "# Single approach\nreturn optimal_solution()  # Fix if broken",
                        "# Clear retry logic\nfor attempt in range(3):\n    result = same_method()  # Same method, not degraded"
                    ]
                },
                "confidence": 1.0,
                "tier": "ANCHORS"
            },
            {
                "type": "forbidden_pattern",
                "subtype": "workaround_instead_of_fix",
                "content": "NEVER add workarounds when encountering bugs - FIX the root cause",
                "examples": {
                    "bad": [
                        "# Workaround for bug in X\nif version < 2.0:\n    use_hack()",
                        "# TODO: Remove when fixed\ntry:\n    buggy_function()\nexcept:\n    workaround()",
                        "# Temporary fix\nif has_bug:\n    apply_patch()"
                    ],
                    "good": [
                        "# Fix the actual bug in the code",
                        "# Update to fixed version",
                        "# Report and wait for proper fix\nraise NotImplementedError('Waiting for upstream fix #123')"
                    ]
                },
                "confidence": 1.0,
                "tier": "ANCHORS"
            },
            {
                "type": "coding_standard",
                "subtype": "error_handling_philosophy",
                "content": "FAIL FAST AND CLEARLY - Never degrade functionality silently",
                "rules": [
                    "If the proper solution doesn't work, FIX IT",
                    "If you can't fix it, FAIL with a clear error",
                    "If dependencies are missing, REQUIRE them",
                    "If the environment is wrong, DOCUMENT what's needed",
                    "NEVER silently fall back to worse solutions"
                ],
                "confidence": 1.0,
                "tier": "ANCHORS"
            }
        ]

        # Store each pattern
        for pattern in patterns:
            # Check if pattern already exists
            existing = self.learner.search_patterns(
                f"forbidden_pattern {pattern['subtype']}",
                mode='exact',
                limit=1
            )

            if not existing:
                self.learner.learn_pattern(pattern)
                print(f"Stored NO_FALLBACK pattern: {pattern['subtype']}")

    def check_for_fallback_patterns(self, code: str) -> List[Dict]:
        """Check code for fallback anti-patterns."""
        violations = []

        # Patterns to detect - simplified for reliability
        fallback_patterns = [
            # Silent fallbacks
            (r"except\s*:", "Bare except clause"),
            (r"except.*?:\s*pass", "Silent exception with pass"),
            (r"except.*?:\s*return\s+(None|''|\[\]|\{\}|False|0)", "Error masking with default return"),

            # Fallback logic in exception handlers
            (r"except.*?:.*?(simple|basic|fallback)", "Exception with fallback keyword"),
            (r"except.*?:.*?result\s*=", "Result assignment in exception"),

            # Feature detection fallbacks
            (r"if\s+has_", "Has-check pattern"),
            (r"try:\s*import", "Try-import pattern"),

            # Degraded functionality
            (r"(advanced|complex|optimal).*?except.*?(simple|basic|fallback)", "Degraded exception handling"),
            (r"for\s+\w+\s+in\s+\[.*?\]:.*?try:", "Multiple method attempts"),

            # Workarounds
            (r"#\s*(FIXME|TODO|HACK|Workaround|TEMP)", "Workaround comment"),
            (r"workaround", "Workaround keyword"),
        ]

        import re
        for pattern, description in fallback_patterns:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE | re.DOTALL):
                violations.append({
                    "type": "fallback_detected",
                    "pattern": pattern,
                    "description": description,
                    "severity": "HIGH"
                })

        return violations

    def suggest_proper_solution(self, violation: Dict) -> str:
        """Suggest proper solution instead of fallback."""
        suggestions = {
            "Silent exception fallback": "Remove try/except or raise specific error with context",
            "Error masking with default return": "Let error propagate or raise with explanation",
            "Feature availability fallback": "Require the feature as dependency",
            "Import fallback": "Add to requirements.txt/setup.py",
            "Degraded exception handling": "Fix the advanced method to work reliably",
            "Multiple method attempts": "Use single robust implementation",
            "Workaround comment": "Fix the root cause instead of working around it",
            "Version-based workaround": "Update to fixed version or fix the issue"
        }

        return suggestions.get(violation['description'], "Fix root cause, don't add fallback")


def main():
    """Initialize NO_FALLBACK patterns when script runs."""
    enforcer = NoFallbackEnforcer()
    print("NO_FALLBACK patterns initialized in ANCHORS tier")

    # Show stored patterns
    patterns = enforcer.learner.search_patterns(
        "forbidden_pattern",
        mode='semantic',
        limit=10
    )

    print(f"\nStored {len(patterns)} NO_FALLBACK patterns")
    for p in patterns:
        if p.get('subtype'):
            print(f"  - {p['subtype']}: {p.get('content', '')[:60]}...")


if __name__ == "__main__":
    main()