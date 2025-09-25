#!/usr/bin/env python3
"""
Post-Read Memory Injector Hook
==============================
Injects relevant memories immediately after reading a file.
Only injects highly relevant context to avoid noise.
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from prism_client import get_prism_client

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

RELEVANCE_THRESHOLD = 0.7  # High threshold to avoid noise


class PostReadInjector:
    """Inject relevant memories after file reads."""

    def __init__(self):
        self.client = get_prism_client()

    def get_file_specific_memories(self, file_path: str) -> List[Dict]:
        """Get memories specifically about this file."""
        if not self.client or not self.client.is_available():
            return []

        try:
            filename = Path(file_path).name
            directory = Path(file_path).parent.name
            extension = Path(file_path).suffix

            # Build targeted queries
            queries = [
                f"file:{filename}",  # Exact file
                f"bug_fix {filename}",  # Previous bugs in this file
                f"gotcha {filename}",  # Known issues
                f"pattern {filename}"  # Patterns specific to this file
            ]

            all_memories = []

            # Search ANCHORS first (critical knowledge)
            for query in queries:
                results = self.client.search_memory(
                    query=query,
                    tiers=["ANCHORS"],
                    limit=2
                )
                for result in results:
                    if result.get('score', 0) > RELEVANCE_THRESHOLD:
                        result['source_tier'] = 'ANCHORS'
                        all_memories.append(result)

            # Add LONGTERM if needed
            if len(all_memories) < 3:
                for query in queries[:2]:  # Just file and bug_fix queries
                    results = self.client.search_memory(
                        query=query,
                        tiers=["LONGTERM"],
                        limit=1
                    )
                    for result in results:
                        if result.get('score', 0) > RELEVANCE_THRESHOLD:
                            result['source_tier'] = 'LONGTERM'
                            all_memories.append(result)

            return all_memories[:5]  # Max 5 memories

        except Exception as e:
            logger.error(f"Failed to get file memories: {e}")
            return []

    def format_injection(self, file_path: str, memories: List[Dict]) -> str:
        """Format memories for injection."""
        if not memories:
            return ""

        sections = [f"\n## 📚 Known Context for {Path(file_path).name}\n"]

        # Group by tier
        critical_memories = [m for m in memories if m.get('source_tier') == 'ANCHORS']
        pattern_memories = [m for m in memories if m.get('source_tier') == 'LONGTERM']

        if critical_memories:
            sections.append("### 🔴 Critical Information:")
            for mem in critical_memories:
                content = mem.get('content', '')
                if len(content) > 200:
                    content = content[:200] + "..."
                sections.append(f"• {content}")

        if pattern_memories:
            sections.append("\n### 💡 Relevant Patterns:")
            for mem in pattern_memories:
                content = mem.get('content', '')
                if len(content) > 150:
                    content = content[:150] + "..."
                sections.append(f"• {content}")

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

    # Only process Read tool
    if tool_name != "Read":
        print(json.dumps({"action": "continue"}))
        return

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        print(json.dumps({"action": "continue"}))
        return

    # Get and inject memories
    injector = PostReadInjector()
    memories = injector.get_file_specific_memories(file_path)

    if memories:
        formatted = injector.format_injection(file_path, memories)
        if formatted:
            print(json.dumps({
                "action": "assistant_message",
                "assistant_message": formatted
            }), file=sys.stderr)

    # Always continue
    print(json.dumps({"action": "continue"}))


if __name__ == "__main__":
    main()