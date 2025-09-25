#!/usr/bin/env python3
"""
Edit State Reconstructor Hook
=============================
Reconstructs full file content from Edit/MultiEdit operations for complete analysis.
Uses Redis caching to maintain file states during editing sessions.

Key Features:
- Caches file content on Read/Write operations
- Reconstructs full files from edit fragments
- Enables complete semantic analysis on edits
- NO FALLBACKS - requires Redis and PRISM
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import semantic analyzer
sys.path.append(str(Path(__file__).parent))
from semantic_code_analyzer import get_semantic_analyzer
from prism_client import get_prism_client
from preference_manager import get_preference_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EditStateReconstructor:
    """Reconstructs full file states from edit operations."""

    def __init__(self):
        """Initialize with REQUIRED services."""
        self.analyzer = get_semantic_analyzer()  # Will raise if Redis/PRISM unavailable
        self.prism_client = get_prism_client()
        self.preference_manager = get_preference_manager()

    def handle_read(self, file_path: str, content: str) -> None:
        """Cache file content when read."""
        self.analyzer.cache_file_content(file_path, content)
        logger.debug(f"Cached content for {file_path} on Read")

    def handle_write(self, file_path: str, content: str) -> None:
        """Cache file content when written."""
        self.analyzer.cache_file_content(file_path, content)
        logger.debug(f"Cached content for {file_path} on Write")

    def handle_edit(self, file_path: str, old_string: str, new_string: str) -> Dict[str, Any]:
        """
        Reconstruct file with edit and analyze.

        Args:
            file_path: File being edited
            old_string: String to replace
            new_string: Replacement string

        Returns:
            Analysis results for the full reconstructed file
        """
        try:
            # Reconstruct and analyze
            new_content, analysis = self.analyzer.reconstruct_with_edit(
                file_path, old_string, new_string
            )

            # Extract expected behavior from context
            expected_behavior = self._extract_expected_behavior(file_path, new_content)

            # Analyze code logic if we have expected behavior
            if expected_behavior:
                logic_analysis = self.analyzer.analyze_code_logic(
                    new_content,
                    expected_behavior,
                    cache_key=f"{file_path}:logic"
                )
                analysis["logic"] = logic_analysis

            # Check user preferences
            preference_violations = self.preference_manager.check_violations(new_content, file_path)
            if preference_violations:
                analysis["preference_violations"] = preference_violations

            return {
                "success": True,
                "file_path": file_path,
                "analysis": analysis,
                "issues_found": self._has_critical_issues(analysis)
            }

        except Exception as e:
            logger.error(f"Failed to reconstruct/analyze edit: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def handle_multi_edit(self, file_path: str, edits: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Handle multiple edits to same file.

        Args:
            file_path: File being edited
            edits: List of edit operations

        Returns:
            Analysis results for the final reconstructed file
        """
        # Get current content
        content = self.analyzer.get_cached_file(file_path)
        if not content:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                self.analyzer.cache_file_content(file_path, content)
            except Exception as e:
                logger.error(f"Cannot read {file_path} for multi-edit: {e}")
                return {"success": False, "error": str(e)}

        # Apply all edits sequentially
        for edit in edits:
            old_string = edit.get("old_string", "")
            new_string = edit.get("new_string", "")

            if old_string in content:
                content = content.replace(old_string, new_string)
            else:
                logger.warning(f"String not found in multi-edit: {old_string[:50]}...")

        # Cache final content
        self.analyzer.cache_file_content(file_path, content)

        # Analyze final result
        try:
            analysis = {
                "patterns": self.analyzer.detect_code_patterns(content),
                "summary": self.analyzer.summarize_code(content)
            }

            # Extract expected behavior
            expected_behavior = self._extract_expected_behavior(file_path, content)
            if expected_behavior:
                logic_analysis = self.analyzer.analyze_code_logic(
                    content,
                    expected_behavior,
                    cache_key=f"{file_path}:logic"
                )
                analysis["logic"] = logic_analysis

            # Check preferences
            preference_violations = self.preference_manager.check_violations(content, file_path)
            if preference_violations:
                analysis["preference_violations"] = preference_violations

            return {
                "success": True,
                "file_path": file_path,
                "analysis": analysis,
                "issues_found": self._has_critical_issues(analysis)
            }

        except Exception as e:
            logger.error(f"Failed to analyze multi-edit result: {e}")
            return {"success": False, "error": str(e)}

    def _extract_expected_behavior(self, file_path: str, content: str) -> Optional[str]:
        """
        Extract expected behavior from various sources.

        Sources:
        1. Recent user messages about this file
        2. Function/class docstrings
        3. Comments describing intent
        4. PRISM memory about this file
        """
        expected_parts = []

        # Try to get from PRISM memory
        if self.prism_client:
            try:
                results = self.prism_client.search_memory(
                    f"file:{file_path} expected behavior intent requirements",
                    tier="WORKING",
                    limit=1
                )
                if results:
                    for result in results:
                        if 'content' in result:
                            expected_parts.append(result['content'])
            except Exception as e:
                logger.debug(f"Could not retrieve expected behavior from PRISM: {e}")

        # Extract from docstrings (simple approach)
        import re
        docstring_pattern = r'"""(.*?)"""'
        docstrings = re.findall(docstring_pattern, content, re.DOTALL)
        for docstring in docstrings[:3]:  # First 3 docstrings
            if len(docstring) > 20:  # Meaningful docstrings only
                expected_parts.append(docstring.strip())

        # Extract from comments about purpose
        purpose_patterns = [
            r'# Purpose: (.*)',
            r'# This function (.*)',
            r'# Expected: (.*)',
            r'// Purpose: (.*)',
            r'// This function (.*)'
        ]
        for pattern in purpose_patterns:
            matches = re.findall(pattern, content)
            expected_parts.extend(matches[:2])  # First 2 matches

        if expected_parts:
            return " ".join(expected_parts)[:500]  # Limit length

        return None

    def _has_critical_issues(self, analysis: Dict[str, Any]) -> bool:
        """Check if analysis found critical issues."""
        # Check for security anti-patterns
        if "patterns" in analysis:
            anti_patterns = analysis["patterns"].get("anti_patterns", [])
            # Check for critical security issues
            critical_patterns = ["SQL injection", "Command injection", "Hardcoded"]
            for pattern in anti_patterns:
                if any(critical in pattern for critical in critical_patterns):
                    return True

        # Check for logical issues
        if "logic" in analysis:
            if analysis["logic"].get("has_issues"):
                issues = analysis["logic"].get("logical_issues", [])
                # Check severity of logical issues
                for issue in issues:
                    if "invert" in issue.lower() or "missing auth" in issue.lower():
                        return True

        # Check for critical preference violations
        if "preference_violations" in analysis:
            for violation in analysis["preference_violations"]:
                if violation.get("tier") == "ANCHORS":
                    return True
                if violation.get("correction_count", 0) >= 2:
                    return True

        return False

    def clear_cache(self, file_path: str) -> bool:
        """Clear cache for specific file."""
        return self.analyzer.clear_file_cache(file_path)


def main():
    """Main hook entry point."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON input")
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    event_type = input_data.get("hook_event_name", "")

    # Only process file operations
    if tool_name not in ["Read", "Write", "Edit", "MultiEdit"]:
        sys.exit(0)

    # Initialize reconstructor
    try:
        reconstructor = EditStateReconstructor()
    except Exception as e:
        logger.error(f"Cannot initialize reconstructor: {e}")
        # Output error for visibility
        print(json.dumps({
            "intervention": {
                "type": "warning",
                "severity": "HIGH",
                "message": f"⚠️ Edit reconstructor unavailable: {e}\nSemantic analysis disabled!"
            }
        }))
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Skip non-code files
    if not file_path.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs')):
        sys.exit(0)

    # Handle based on tool and event
    if event_type == "PostToolUse":
        if tool_name == "Read":
            # Cache file content after read
            result = input_data.get("tool_result", {})
            content = result if isinstance(result, str) else ""
            if content:
                reconstructor.handle_read(file_path, content)

        elif tool_name == "Write":
            # Cache file content after write
            content = tool_input.get("content", "")
            if content:
                reconstructor.handle_write(file_path, content)

    elif event_type == "PreToolUse":
        if tool_name == "Edit":
            # Reconstruct and analyze edit
            old_string = tool_input.get("old_string", "")
            new_string = tool_input.get("new_string", "")

            if old_string and new_string:
                result = reconstructor.handle_edit(file_path, old_string, new_string)

                if result.get("issues_found"):
                    # Format issues for intervention
                    issues_text = []
                    analysis = result.get("analysis", {})

                    # Add logical issues
                    if "logic" in analysis and analysis["logic"].get("has_issues"):
                        issues_text.append("## 🧠 Logical Issues:")
                        for issue in analysis["logic"].get("logical_issues", []):
                            issues_text.append(f"- {issue}")

                    # Add anti-patterns
                    if "patterns" in analysis:
                        anti_patterns = analysis["patterns"].get("anti_patterns", [])
                        if anti_patterns:
                            issues_text.append("\n## ⚠️ Anti-patterns Detected:")
                            for pattern in anti_patterns:
                                issues_text.append(f"- {pattern}")

                    # Add preference violations
                    if "preference_violations" in analysis:
                        issues_text.append("\n## 📝 Preference Violations:")
                        for violation in analysis["preference_violations"]:
                            issues_text.append(f"- {violation.get('message', 'Unknown violation')}")

                    if issues_text:
                        print(json.dumps({
                            "intervention": {
                                "type": "block_execution",
                                "severity": "HIGH",
                                "message": f"❌ Edit will introduce issues in {file_path}:\n\n" +
                                         "\n".join(issues_text) +
                                         "\n\n**Fix all issues before proceeding!**"
                            }
                        }))
                        sys.exit(0)

        elif tool_name == "MultiEdit":
            # Reconstruct and analyze multi-edit
            edits = tool_input.get("edits", [])

            if edits:
                result = reconstructor.handle_multi_edit(file_path, edits)

                if result.get("issues_found"):
                    # Format issues for intervention
                    issues_text = []
                    analysis = result.get("analysis", {})

                    # Add logical issues
                    if "logic" in analysis and analysis["logic"].get("has_issues"):
                        issues_text.append("## 🧠 Logical Issues:")
                        for issue in analysis["logic"].get("logical_issues", []):
                            issues_text.append(f"- {issue}")

                    # Add anti-patterns
                    if "patterns" in analysis:
                        anti_patterns = analysis["patterns"].get("anti_patterns", [])
                        if anti_patterns:
                            issues_text.append("\n## ⚠️ Anti-patterns Detected:")
                            for pattern in anti_patterns:
                                issues_text.append(f"- {pattern}")

                    # Add preference violations
                    if "preference_violations" in analysis:
                        issues_text.append("\n## 📝 Preference Violations:")
                        for violation in analysis["preference_violations"]:
                            issues_text.append(f"- {violation.get('message', 'Unknown violation')}")

                    if issues_text:
                        print(json.dumps({
                            "intervention": {
                                "type": "block_execution",
                                "severity": "HIGH",
                                "message": f"❌ Multi-edit will introduce issues in {file_path}:\n\n" +
                                         "\n".join(issues_text) +
                                         "\n\n**Fix all issues before proceeding!**"
                            }
                        }))
                        sys.exit(0)

    # No intervention needed
    sys.exit(0)


if __name__ == "__main__":
    main()