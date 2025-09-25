#!/usr/bin/env python3
"""
Post-Error Memory Injector Hook
================================
Injects relevant fix patterns after Bash commands that produce errors.
Searches for similar errors and their solutions in memory.
"""

import json
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from prism_client import get_prism_client

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class PostErrorInjector:
    """Inject relevant fixes after errors."""

    def __init__(self):
        self.client = get_prism_client()

    def detect_error_type(self, output: str) -> Optional[Dict]:
        """Detect the type of error from command output."""
        output_lower = output.lower()

        # Common error patterns
        error_patterns = [
            (r'modulenotfounderror.*no module named [\'"](\w+)[\'"]', 'missing_module', 1),
            (r'importerror.*cannot import name [\'"](\w+)[\'"]', 'import_error', 1),
            (r'syntaxerror.*invalid syntax', 'syntax_error', None),
            (r'nameerror.*name [\'"](\w+)[\'"] is not defined', 'undefined_name', 1),
            (r'typeerror.*(\w+)\(\) takes', 'type_error', 1),
            (r'attributeerror.*has no attribute [\'"](\w+)[\'"]', 'attribute_error', 1),
            (r'filenotfounderror.*no such file or directory.*[\'"]([^\'\"]+)[\'"]', 'file_not_found', 1),
            (r'permission denied', 'permission_error', None),
            (r'failed.*test.*(\w+)', 'test_failure', 1),
            (r'assertion.*failed', 'assertion_failure', None),
            (r'connection refused', 'connection_error', None),
            (r'timeout', 'timeout_error', None),
        ]

        for pattern, error_type, group_idx in error_patterns:
            match = re.search(pattern, output_lower)
            if match:
                context = match.group(group_idx) if group_idx and len(match.groups()) >= group_idx else None
                return {
                    'type': error_type,
                    'context': context,
                    'full_match': match.group(0)
                }

        # Generic error detection
        if any(term in output_lower for term in ['error', 'failed', 'exception', 'traceback']):
            return {
                'type': 'generic_error',
                'context': None,
                'full_match': output[:100]
            }

        return None

    def search_error_fixes(self, error_info: Dict) -> List[Dict]:
        """Search for fixes to similar errors."""
        if not self.client or not self.client.is_available():
            return []

        try:
            error_type = error_info['type']
            context = error_info.get('context', '')

            # Build search queries based on error type
            queries = [
                f"fix {error_type}",
                f"error {error_type} solution"
            ]

            if context:
                queries.insert(0, f"fix {error_type} {context}")

            all_fixes = []

            # Search ANCHORS and LONGTERM for fixes
            for query in queries:
                # ANCHORS first (critical fixes)
                results = self.client.search_memory(
                    query=query,
                    tiers=["ANCHORS"],
                    limit=2
                )
                for result in results:
                    if result.get('score', 0) > 0.6:  # Lower threshold for error fixes
                        result['source_tier'] = 'ANCHORS'
                        all_fixes.append(result)

                # LONGTERM if needed
                if len(all_fixes) < 3:
                    results = self.client.search_memory(
                        query=query,
                        tiers=["LONGTERM"],
                        limit=2
                    )
                    for result in results:
                        if result.get('score', 0) > 0.5:
                            result['source_tier'] = 'LONGTERM'
                            all_fixes.append(result)

            return all_fixes[:5]  # Max 5 fixes

        except Exception as e:
            logger.error(f"Failed to search error fixes: {e}")
            return []

    def format_fix_suggestions(self, error_info: Dict, fixes: List[Dict]) -> str:
        """Format fix suggestions for injection."""
        if not fixes:
            return ""

        sections = [f"\n## 🔧 Error Detected: {error_info['type'].replace('_', ' ').title()}\n"]

        if error_info.get('context'):
            sections.append(f"**Context**: {error_info['context']}")

        # Group by tier
        critical_fixes = [f for f in fixes if f.get('source_tier') == 'ANCHORS']
        pattern_fixes = [f for f in fixes if f.get('source_tier') == 'LONGTERM']

        if critical_fixes:
            sections.append("\n### 🔴 Known Fixes (High Priority):")
            for fix in critical_fixes:
                content = fix.get('content', '')
                if len(content) > 200:
                    content = content[:200] + "..."
                sections.append(f"• {content}")

        if pattern_fixes:
            sections.append("\n### 💡 Possible Solutions:")
            for fix in pattern_fixes:
                content = fix.get('content', '')
                if len(content) > 150:
                    content = content[:150] + "..."
                sections.append(f"• {content}")

        # Add generic advice based on error type
        if error_info['type'] == 'missing_module':
            sections.append(f"\n💡 Try: `pip install {error_info.get('context', 'missing_package')}`")
        elif error_info['type'] == 'permission_error':
            sections.append("\n💡 Try: Check file permissions or use sudo if appropriate")
        elif error_info['type'] == 'connection_error':
            sections.append("\n💡 Try: Check if the service is running and accessible")

        return "\n".join(sections)


def main():
    """Main hook execution."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"action": "continue"}))
        return

    # Only process PostToolUse events
    event_type = input_data.get("hook_event_name", "")
    if event_type != "PostToolUse":
        print(json.dumps({"action": "continue"}))
        return

    tool_name = input_data.get("tool_name", "")

    # Only process Bash tool
    if tool_name != "Bash":
        print(json.dumps({"action": "continue"}))
        return

    tool_output = input_data.get("tool_output", {})
    output = tool_output.get("output", "")

    if not output:
        print(json.dumps({"action": "continue"}))
        return

    # Detect if there's an error
    injector = PostErrorInjector()
    error_info = injector.detect_error_type(output)

    if error_info:
        # Search for fixes
        fixes = injector.search_error_fixes(error_info)

        if fixes:
            formatted = injector.format_fix_suggestions(error_info, fixes)
            if formatted:
                print(json.dumps({
                    "action": "assistant_message",
                    "assistant_message": formatted
                }), file=sys.stderr)

    # Always continue
    print(json.dumps({"action": "continue"}))


if __name__ == "__main__":
    main()