#!/usr/bin/env python3
"""
Preference Manager - Central User Preference System
====================================================
Manages user preferences, corrections, and coding standards across all hooks.
Stores preferences in PRISM memory with appropriate tiers based on importance.
"""

import json
import sys
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Import PRISM client and universal learner
sys.path.insert(0, str(Path(__file__).parent))
from prism_client import get_prism_client
from universal_learner import get_learner


class PreferenceManager:
    """Central manager for user preferences across hooks."""

    def __init__(self):
        self.prism = get_prism_client()
        self.learner = get_learner()
        self.preference_cache = {}  # Cache by file extension
        self.global_preferences = []  # Apply to all files
        self.correction_history = defaultdict(list)  # Track corrections
        self.session_id = f"pref_{int(time.time())}"
        self.warm_cache()

    def warm_cache(self):
        """Load user preferences from PRISM at startup."""
        if not self.prism:
            return

        try:
            # Query for all user preferences
            results = self.prism.search_memory(
                query="user_preference forbidden_pattern coding_standard",
                tiers=["ANCHORS", "LONGTERM"],
                limit=50
            )

            for result in results:
                self.parse_and_cache_preference(result)

        except Exception as e:
            print(f"Failed to warm preference cache: {e}", file=sys.stderr)

    def parse_and_cache_preference(self, prism_result: Dict):
        """Parse PRISM result and add to cache."""
        try:
            metadata = prism_result.get('metadata', {})
            applies_to = metadata.get('applies_to', ['*'])

            pref = {
                'rule': prism_result.get('content', ''),
                'pattern': metadata.get('pattern'),
                'type': metadata.get('type', 'preference'),
                'confidence': prism_result.get('score', 0.5),
                'correction_count': metadata.get('correction_count', 0),
                'frustration_level': metadata.get('frustration_level', 0),
                'tier': metadata.get('tier', 'WORKING')
            }

            # Cache by file type
            for file_pattern in applies_to:
                if file_pattern == '*':
                    self.global_preferences.append(pref)
                else:
                    if file_pattern not in self.preference_cache:
                        self.preference_cache[file_pattern] = []
                    self.preference_cache[file_pattern].append(pref)

        except Exception as e:
            print(f"Failed to parse preference: {e}", file=sys.stderr)

    def detect_preference_in_message(self, message: str) -> Optional[Dict]:
        """Detect preference statements in user messages."""
        message_lower = message.lower()

        # Preference detection patterns with extraction
        patterns = [
            # Strong preferences
            (r'\balways\s+use\s+([^\s,]+)(?:\s+instead\s+of\s+([^\s,]+))?', 'always_use', 0.95),
            (r'\bnever\s+(?:use|write|add)\s+([^\s,]+)', 'never_use', 0.98),
            (r'\bdon\'t\s+(?:use|write|add)\s+([^\s,]+)', 'forbidden', 0.9),
            (r'\bstop\s+(?:using|adding|writing)\s+([^\s,]+)', 'stop_using', 0.95),
            (r'\bprefer\s+([^\s,]+)\s+(?:over|instead\s+of)\s+([^\s,]+)', 'preference', 0.85),

            # Corrections (with frustration)
            (r'i\s+(?:said|told\s+you).*?don\'t\s+([^\s,]+)', 'frustrated_correction', 0.95),
            (r'why\s+do\s+you\s+keep\s+([^\s,]+)', 'frustrated_pattern', 0.9),
            (r'stop\s+([^\s,]+)ing.*?i\s+(?:said|told)', 'frustrated_command', 0.95),

            # Style preferences
            (r'use\s+(single|double)\s+quotes', 'quote_style', 0.9),
            (r'(?:no|don\'t\s+use)\s+(docstrings|comments|type\s+hints)', 'no_documentation', 0.85),
            (r'(?:always|use)\s+(\d+)\s+spaces', 'indentation', 0.8),
        ]

        for pattern, pref_type, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                groups = match.groups()

                # Build preference object
                preference = {
                    'type': pref_type,
                    'confidence': confidence,
                    'detected_in': message[:100],
                    'timestamp': time.time()
                }

                # Extract specific values
                if pref_type == 'always_use':
                    preference['prefer'] = groups[0]
                    if len(groups) > 1 and groups[1]:
                        preference['avoid'] = groups[1]
                elif pref_type in ['never_use', 'forbidden', 'stop_using']:
                    preference['avoid'] = groups[0]
                    preference['frustration_level'] = 0.5 if 'stop' in pref_type else 0.3
                elif pref_type == 'preference':
                    preference['prefer'] = groups[0]
                    preference['avoid'] = groups[1] if len(groups) > 1 else None
                elif pref_type.startswith('frustrated'):
                    preference['frustration_level'] = 0.8
                    preference['pattern'] = groups[0] if groups else None
                elif pref_type == 'quote_style':
                    preference['style'] = groups[0]
                elif pref_type == 'no_documentation':
                    preference['avoid'] = groups[0]
                elif pref_type == 'indentation':
                    preference['spaces'] = int(groups[0])

                return preference

        return None

    def detect_correction(self, file_path: str, old_content: str, new_content: str,
                         edit_history: List[Dict]) -> Optional[Dict]:
        """Detect if an edit is correcting a Claude mistake."""

        # Check if same file was edited recently
        recent_edits_same_file = [
            e for e in edit_history
            if e.get('file') == file_path
            and time.time() - e.get('timestamp', 0) < 600  # Within 10 minutes
        ]

        if len(recent_edits_same_file) >= 2:
            # Multiple edits to same file = likely correction

            # Try to extract what changed
            pattern_changed = self.extract_change_pattern(old_content, new_content)

            # Update correction history
            self.correction_history[pattern_changed].append({
                'file': file_path,
                'timestamp': time.time(),
                'old': old_content[:100],
                'new': new_content[:100]
            })

            correction_count = len(self.correction_history[pattern_changed])

            return {
                'type': 'user_correction',
                'pattern': pattern_changed,
                'confidence': min(0.95, 0.7 + correction_count * 0.1),
                'frustration_level': min(1.0, correction_count * 0.3),
                'correction_count': correction_count,
                'should_store': correction_count >= 2  # Store after 2 corrections
            }

        return None

    def extract_change_pattern(self, old_content: str, new_content: str) -> str:
        """Extract semantic pattern from what changed."""
        # Simple pattern extraction - can be enhanced

        # Check for common patterns
        if 'f"' in old_content and 'format(' in new_content:
            return "f_string_to_format"
        elif 'f\'' in old_content and 'format(' in new_content:
            return "f_string_to_format"
        elif '"""' in old_content and '"""' not in new_content:
            return "removed_docstring"
        elif 'except:' in old_content and 'except ' in new_content:
            return "bare_except_to_specific"
        elif 'print(' in old_content and 'logger.' in new_content:
            return "print_to_logger"
        elif '\t' in old_content and '    ' in new_content:
            return "tabs_to_spaces"
        elif '"' in old_content and "'" in new_content:
            return "double_to_single_quotes"

        # Generic change
        return f"change_{hash((old_content[:50], new_content[:50])) % 10000}"

    def check_for_duplicate(self, preference: Dict) -> Optional[Dict]:
        """Check if this preference already exists in PRISM."""
        if not self.prism:
            return None

        try:
            # Search for exact or very similar preferences
            search_query = preference.get('pattern', '') or preference.get('avoid', '') or preference.get('prefer', '')
            if not search_query:
                return None

            # Search in all tiers for duplicates
            results = self.prism.search_memory(
                query=search_query,
                limit=5
            )

            for result in results:
                # Check for exact content match
                if result.get('content') == self.build_rule_description(preference):
                    # Found duplicate - update its metadata
                    metadata = result.get('metadata', {})
                    metadata['correction_count'] = metadata.get('correction_count', 0) + 1
                    metadata['last_seen'] = time.time()
                    metadata['frustration_level'] = max(
                        metadata.get('frustration_level', 0),
                        preference.get('frustration_level', 0)
                    )
                    return result
            return None
        except Exception as e:
            print(f"Error checking for duplicates: {e}", file=sys.stderr)
            return None

    def store_preference(self, preference: Dict) -> bool:
        """Store preference in PRISM with deduplication and appropriate tier."""
        if not self.prism:
            return False

        try:
            # Check for duplicates first
            duplicate = self.check_for_duplicate(preference)
            if duplicate:
                # Update existing preference instead of creating new
                metadata = duplicate.get('metadata', {})
                if 'correction_count' not in metadata:
                    metadata['correction_count'] = 1
                correction_count = metadata['correction_count']

                # Auto-promote if corrected multiple times
                if correction_count >= 2:
                    # Move to ANCHORS immediately
                    print(f"Auto-promoting preference to ANCHORS (corrected {correction_count} times)", file=sys.stderr)
                    # Store updated version in ANCHORS
                    preference['correction_count'] = correction_count
                    preference['frustration_level'] = min(1.0, correction_count * 0.3)  # Calculate, don't default
                    tier = 'ANCHORS'
                else:
                    return True  # Duplicate handled, no new storage needed
            else:
                # Determine tier for new preference
                tier = self.determine_tier(preference)

            # Build detection pattern if not present
            if not preference.get('pattern'):
                preference['pattern'] = self.build_detection_pattern(preference)

            # Determine what files this applies to
            applies_to = preference.get('applies_to', ['*'])

            # Build rule description
            rule = self.build_rule_description(preference)

            # Store in PRISM
            result = self.prism.store_memory(
                content=rule,
                tier=tier,
                metadata={
                    'type': 'user_preference',
                    'subtype': preference.get('type', 'preference'),
                    'pattern': preference.get('pattern'),
                    'applies_to': applies_to,
                    'correction_count': preference.get('correction_count', 0),
                    'frustration_level': preference.get('frustration_level', 0),
                    'confidence': preference.get('confidence', 0.7),
                    'prefer': preference.get('prefer'),
                    'avoid': preference.get('avoid'),
                    'detected_at': preference.get('timestamp', time.time()),
                    'session_id': self.session_id
                }
            )

            # Add to cache immediately
            self.parse_and_cache_preference({
                'content': rule,
                'score': preference.get('confidence', 0.7),
                'metadata': {
                    'type': 'user_preference',
                    'pattern': preference.get('pattern'),
                    'applies_to': applies_to,
                    'correction_count': preference.get('correction_count', 0),
                    'frustration_level': preference.get('frustration_level', 0),
                    'tier': tier
                }
            })

            # Learn pattern for graph relationships
            if self.learner:
                pattern_data = {
                    'type': 'user_preference',
                    'content': rule,
                    'confidence': preference.get('confidence', 0.7),
                    'relationships': self.build_relationships(preference)
                }
                self.learner.learn_pattern(pattern_data)

            return True

        except Exception as e:
            print(f"Failed to store preference: {e}", file=sys.stderr)
            return False

    def determine_tier(self, preference: Dict) -> str:
        """Determine PRISM tier based on preference importance - NO FALLBACKS."""
        # REQUIRE these fields to exist
        if 'correction_count' not in preference:
            preference['correction_count'] = 0  # New preference, first time seen

        if 'frustration_level' not in preference:
            # Calculate frustration from corrections
            preference['frustration_level'] = min(1.0, preference['correction_count'] * 0.3)

        if 'confidence' not in preference:
            # High confidence for explicit user statements
            preference['confidence'] = 0.9 if preference.get('type') in ['never_use', 'always_use'] else 0.7

        frustration = preference['frustration_level']
        confidence = preference['confidence']
        correction_count = preference['correction_count']

        # Critical preferences go to ANCHORS immediately
        # 2+ corrections or high frustration -> ANCHORS
        if frustration >= 0.5 or correction_count >= 2:
            return 'ANCHORS'
        # Explicit rules with good confidence go to LONGTERM
        elif confidence >= 0.8 or correction_count >= 1:
            return 'LONGTERM'
        # New preferences go to WORKING
        else:
            return 'WORKING'

    def build_detection_pattern(self, preference: Dict) -> Optional[str]:
        """Build regex pattern for detecting preference violations."""
        pref_type = preference.get('type', '')

        if pref_type == 'f_string_to_format':
            return r'f["\'].*\{.*\}["\']'
        elif pref_type == 'removed_docstring':
            return r'"""[\s\S]*?"""'
        elif pref_type == 'bare_except_to_specific':
            return r'except\s*:'
        elif pref_type == 'print_to_logger':
            return r'print\s*\('
        elif preference.get('avoid'):
            # Build pattern from avoided term
            avoided = preference['avoid']
            return rf'\b{re.escape(avoided)}\b'

        return None

    def build_rule_description(self, preference: Dict) -> str:
        """Build human-readable rule description."""
        pref_type = preference.get('type', '')

        if preference.get('prefer') and preference.get('avoid'):
            return f"Always use {preference['prefer']} instead of {preference['avoid']}"
        elif preference.get('avoid'):
            return f"Never use {preference['avoid']}"
        elif preference.get('prefer'):
            return f"Always use {preference['prefer']}"
        elif pref_type == 'f_string_to_format':
            return "Use .format() instead of f-strings"
        elif pref_type == 'removed_docstring':
            return "Don't add docstrings"
        elif pref_type == 'bare_except_to_specific':
            return "Never use bare except, always specify exception type"
        elif pref_type == 'print_to_logger':
            return "Use logger instead of print statements"
        else:
            return f"User preference: {pref_type}"

    def build_relationships(self, preference: Dict) -> List[Tuple]:
        """Build graph relationships for preference."""
        relationships = []

        if preference.get('prefer') and preference.get('avoid'):
            relationships.append((
                preference['prefer'],
                'PREFERRED_OVER',
                preference['avoid']
            ))

        if preference.get('file_path'):
            relationships.append((
                Path(preference['file_path']).name,
                'HAS_PREFERENCE',
                preference.get('type', 'unknown')
            ))

        return relationships

    def get_preferences_for_file(self, file_path: str) -> List[Dict]:
        """Get all preferences applicable to a file."""
        file_ext = Path(file_path).suffix
        file_name = Path(file_path).name

        applicable = []

        # Add global preferences
        applicable.extend(self.global_preferences)

        # Add extension-specific preferences
        if file_ext in self.preference_cache:
            applicable.extend(self.preference_cache[file_ext])

        # Add wildcard patterns that match
        for pattern, prefs in self.preference_cache.items():
            if '*' in pattern and self.matches_pattern(file_path, pattern):
                applicable.extend(prefs)

        # Sort by importance (frustration level, correction count)
        applicable.sort(key=lambda p: (
            p.get('frustration_level', 0),
            p.get('correction_count', 0),
            p.get('confidence', 0)
        ), reverse=True)

        return applicable

    def matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches a pattern."""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern)

    def check_violations(self, content: str, file_path: str) -> List[Dict]:
        """Check content for preference violations."""
        violations = []
        preferences = self.get_preferences_for_file(file_path)

        for pref in preferences:
            if pref.get('pattern'):
                if re.search(pref['pattern'], content, re.MULTILINE | re.DOTALL):
                    violations.append({
                        'rule': pref['rule'],
                        'pattern': pref['pattern'],
                        'severity': 'HIGH' if pref.get('frustration_level', 0) > 0.5 else 'MEDIUM',
                        'correction_count': pref.get('correction_count', 0),
                        'message': self.build_violation_message(pref)
                    })

        return violations

    def build_violation_message(self, preference: Dict) -> str:
        """Build helpful violation message."""
        base = f"Violates preference: {preference['rule']}"

        correction_count = preference.get('correction_count', 0)
        if correction_count > 0:
            base += f" (corrected {correction_count} times before)"

        frustration = preference.get('frustration_level', 0)
        if frustration > 0.7:
            base = "❌ " + base + " - User is frustrated with this"
        elif frustration > 0.5:
            base = "⚠️ " + base

        return base


# Singleton instance
_preference_manager = None

def get_preference_manager() -> PreferenceManager:
    """Get or create preference manager instance."""
    global _preference_manager
    if _preference_manager is None:
        _preference_manager = PreferenceManager()
    return _preference_manager