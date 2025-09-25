#!/usr/bin/env python3
"""
Enhanced Read Injector Hook
===========================
Injects semantic code analysis context when files are read.
Provides AI-powered understanding of code purpose, patterns, and similar implementations.

Key Features:
- Shows what code DOES (not just syntax)
- Identifies patterns and anti-patterns
- Finds similar implementations in PRISM memory
- Suggests improvements based on past fixes
- NO FALLBACKS - requires all services running
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import semantic analyzer and PRISM client
sys.path.append(str(Path(__file__).parent))
from semantic_code_analyzer import get_semantic_analyzer
from prism_client import get_prism_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedReadInjector:
    """Injects semantic analysis context on file reads."""

    def __init__(self):
        """Initialize with REQUIRED services - NO FALLBACKS."""
        self.analyzer = get_semantic_analyzer()  # Will raise if unavailable
        self.prism_client = get_prism_client()   # Will raise if unavailable

    def inject_semantic_context(self, file_path: str, content: str) -> str:
        """
        Generate semantic analysis context for file content.
        NO FALLBACKS - all analysis must succeed or we fail loudly.
        """
        context_parts = []

        # 1. Summarize what the code does
        try:
            summary = self.analyzer.summarize_code(content)
            if summary:
                context_parts.append(f"📝 **Code Summary**: {summary}")
        except Exception as e:
            logger.error(f"Code summarization failed: {e}")
            # Don't hide failures - show them
            context_parts.append(f"⚠️ Code analysis unavailable: {str(e)}")

        # 2. Detect patterns and anti-patterns
        try:
            patterns = self.analyzer.detect_code_patterns(content)

            # Show design patterns found
            design_patterns = patterns.get("design_patterns", [])
            if design_patterns:
                context_parts.append("\n✅ **Design Patterns**:")
                for pattern in design_patterns[:3]:  # Top 3
                    context_parts.append(f"  - {pattern}")

            # Warn about anti-patterns
            anti_patterns = patterns.get("anti_patterns", [])
            if anti_patterns:
                context_parts.append("\n⚠️ **Anti-patterns Detected**:")
                for pattern in anti_patterns[:3]:  # Top 3
                    context_parts.append(f"  - {pattern}")
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            context_parts.append(f"⚠️ Pattern analysis unavailable: {str(e)}")

        # 3. Find similar implementations in memory
        try:
            # Search for similar code in PRISM memory
            similar = self.prism_client.search_memory(
                query=summary if summary else content[:500],
                tiers=["LONGTERM", "ANCHORS"],
                limit=3
            )

            if similar:
                context_parts.append("\n🔍 **Similar Implementations**:")
                for item in similar:
                    # Extract relevant info from memory
                    content_data = item.get("content", {})
                    if isinstance(content_data, str):
                        try:
                            content_data = json.loads(content_data)
                        except:
                            continue

                    # Show what we found
                    description = content_data.get("description", "")
                    if description:
                        context_parts.append(f"  - {description}")

                        # If there were issues fixed, mention them
                        if "fix" in description.lower() or "issue" in description.lower():
                            context_parts.append(f"    💡 Previously fixed issue here")
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            # Don't hide the failure
            context_parts.append(f"⚠️ Memory search unavailable: {str(e)}")

        # 4. Analyze code complexity
        try:
            # Get function-level analysis
            analysis = self.analyzer.analyze_code_logic(content)
            logic_info = analysis.get("logic", {})

            # Report complexity concerns
            if logic_info.get("complexity_score", 0) > 10:
                context_parts.append(f"\n⚡ **Complexity Warning**: Score {logic_info['complexity_score']}/20")
                context_parts.append("   Consider breaking into smaller functions")

            # Check for security issues
            security = analysis.get("security", {})
            if security.get("vulnerabilities"):
                context_parts.append("\n🔒 **Security Concerns**:")
                for vuln in security["vulnerabilities"][:3]:
                    context_parts.append(f"  - {vuln}")
        except Exception as e:
            logger.error(f"Logic analysis failed: {e}")
            context_parts.append(f"⚠️ Logic analysis unavailable: {str(e)}")

        # 5. Check for known issues with this file
        try:
            # Search for past issues with this specific file
            file_issues = self.prism_client.search_memory(
                query=f"issue problem bug {Path(file_path).name}",
                tiers=["WORKING", "EPISODIC"],
                limit=2
            )

            if file_issues:
                context_parts.append("\n📋 **Known Issues with This File**:")
                for issue in file_issues:
                    content_data = issue.get("content", {})
                    if isinstance(content_data, str):
                        try:
                            content_data = json.loads(content_data)
                        except:
                            continue

                    desc = content_data.get("description", "")
                    if desc:
                        context_parts.append(f"  - {desc}")
        except Exception as e:
            logger.error(f"Issue search failed: {e}")

        # Combine all context
        if context_parts:
            full_context = "\n".join(context_parts)
            return f"\n{'='*60}\n🧠 SEMANTIC ANALYSIS CONTEXT\n{'='*60}\n{full_context}\n{'='*60}\n"

        return ""


def main():
    """Main hook entry point - PostToolUse for Read operations."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON input")
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    event_type = input_data.get("hook_event_name", "")

    # Only process PostToolUse for Read
    if tool_name != "Read" or event_type != "PostToolUse":
        sys.exit(0)

    # Get file path and content from result
    tool_result = input_data.get("tool_result", {})
    if not tool_result:
        sys.exit(0)

    # Extract file path from input
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Skip non-code files
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.h'}
    if not any(file_path.endswith(ext) for ext in code_extensions):
        sys.exit(0)

    # Get file content from result
    content = tool_result.get("content", "")
    if not content:
        sys.exit(0)

    # Initialize injector
    try:
        injector = EnhancedReadInjector()
    except Exception as e:
        # Service unavailable - fail loudly
        logger.error(f"Cannot initialize enhanced read injector: {e}")
        print(json.dumps({
            "user_message": {
                "text": f"⚠️ Enhanced code analysis unavailable: {str(e)}\\nEnsure PRISM HTTP server (port 8090) and Redis (port 6379) are running."
            }
        }))
        sys.exit(0)

    # Generate semantic context
    try:
        semantic_context = injector.inject_semantic_context(file_path, content)

        if semantic_context:
            # Inject context as user message
            print(json.dumps({
                "user_message": {
                    "text": semantic_context
                }
            }))
    except Exception as e:
        logger.error(f"Failed to generate semantic context: {e}")
        # Don't block the Read, but notify about the failure
        print(json.dumps({
            "user_message": {
                "text": f"⚠️ Semantic analysis failed: {str(e)}"
            }
        }))


if __name__ == "__main__":
    main()