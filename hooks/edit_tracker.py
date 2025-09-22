#!/usr/bin/env python3
"""
Edit Tracker Hook - Semantic Memory Builder
============================================
Tracks file edits and extracts semantic patterns for PRISM storage.
Stores rich relationships and actual code changes, not just metadata.
"""

import json
import sys
import time
import re
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timezone

# Import universal learner, PRISM client, and preference manager
sys.path.insert(0, str(Path(__file__).parent))
from universal_learner import get_learner
from prism_client import get_prism_client
from preference_manager import get_preference_manager

# Ephemeral patterns to skip
EPHEMERAL_PATTERNS = [
    r'^/tmp/',
    r'^/var/',
    r'\.pyc$',
    r'__pycache__',
    r'^\.git/',
    r'node_modules/',
    r'venv/',
    r'\.venv/',
    r'build/',
    r'dist/',
    r'\.egg-info/',
    r'\.pytest_cache/',
    r'\.coverage',
    r'\.tox/'
]

class SemanticEditTracker:
    """Track file edits and extract semantic patterns."""

    def __init__(self):
        self.learner = get_learner()
        self.client = get_prism_client()
        self.preference_manager = get_preference_manager()
        self.session_id = f"edit_{int(time.time())}"
        self.recent_edits = []  # In-memory tracking for current session
        self.file_content_cache = {}  # Cache file contents for diffing

    def should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped from tracking."""
        if not file_path:
            return True

        for pattern in EPHEMERAL_PATTERNS:
            if re.search(pattern, file_path):
                return True
        return False

    def detect_architectural_layer(self, file_path: str) -> str:
        """Detect architectural layer from file path."""
        path_lower = file_path.lower()

        # Test files
        if '/test' in path_lower or 'test_' in Path(file_path).name:
            return 'test'
        # API/Routes
        elif any(x in path_lower for x in ['/api/', '/routes/', '/handlers/', '/controllers/']):
            return 'presentation'
        # Services/Business logic
        elif any(x in path_lower for x in ['/services/', '/business/', '/logic/', '/processors/']):
            return 'business'
        # Data layer
        elif any(x in path_lower for x in ['/models/', '/repositories/', '/dao/', '/database/']):
            return 'data'
        # Infrastructure
        elif any(x in path_lower for x in ['/utils/', '/helpers/', '/config/', '/hooks/']):
            return 'infrastructure'
        else:
            return 'application'

    def extract_semantic_changes(self, file_path: str, operation: str, tool_input: Dict) -> Dict:
        """Extract semantic meaning from the edit operation."""
        semantic_data = {
            "type": "code_change",
            "operation": operation,
            "file": file_path,
            "layer": self.detect_architectural_layer(file_path),
            "semantic_changes": [],
            "entities": [],
            "relationships": [],
            "confidence": 0.7
        }

        # Extract based on operation type
        if operation == "Write":
            content = tool_input.get("content", "")
            semantic_data["semantic_changes"] = self.analyze_new_code(content, file_path)
            semantic_data["entities"] = self.extract_code_entities(content)

        elif operation == "Edit":
            old_str = tool_input.get("old_string", "")
            new_str = tool_input.get("new_string", "")
            semantic_data["semantic_changes"] = self.analyze_edit(old_str, new_str)
            semantic_data["entities"] = self.extract_code_entities(new_str)

            # Detect specific fix patterns
            if "error" in old_str.lower() or "exception" in old_str.lower():
                semantic_data["type"] = "bug_fix"
                semantic_data["confidence"] = 0.9
            elif "TODO" in old_str or "FIXME" in old_str:
                semantic_data["type"] = "todo_resolution"
                semantic_data["confidence"] = 0.85

        elif operation == "MultiEdit":
            edits = tool_input.get("edits", [])
            all_changes = []
            for edit in edits[:5]:  # Analyze first 5 edits
                changes = self.analyze_edit(
                    edit.get("old_string", ""),
                    edit.get("new_string", "")
                )
                all_changes.extend(changes)
            semantic_data["semantic_changes"] = list(set(all_changes))  # Unique changes
            semantic_data["type"] = "refactoring" if len(edits) > 3 else "modification"

        return semantic_data

    def analyze_new_code(self, content: str, file_path: str) -> List[str]:
        """Analyze newly written code for semantic patterns."""
        patterns = []

        # Check file type
        file_ext = Path(file_path).suffix

        if file_ext in ['.py', '.js', '.ts']:
            # Function/class definitions
            if re.search(r'(def |class |function |const \w+ = )', content):
                if 'test_' in content or '@test' in content:
                    patterns.append("test_implementation")
                else:
                    patterns.append("new_implementation")

            # Import statements
            if re.search(r'(import |from .* import|require\()', content):
                patterns.append("dependency_setup")

            # Error handling
            if re.search(r'(try:|except |catch\(|\.catch\()', content):
                patterns.append("error_handling")

            # Async patterns
            if re.search(r'(async |await |Promise|asyncio)', content):
                patterns.append("async_implementation")

        return patterns

    def analyze_edit(self, old_content: str, new_content: str) -> List[str]:
        """Analyze the semantic difference between old and new content."""
        changes = []

        # Check for error handling additions
        if 'try' not in old_content and 'try' in new_content:
            changes.append("added_error_handling")

        # Check for import additions
        old_imports = re.findall(r'(?:import |from )[\w.]+', old_content)
        new_imports = re.findall(r'(?:import |from )[\w.]+', new_content)
        if len(new_imports) > len(old_imports):
            changes.append("added_dependencies")

        # Check for function signature changes
        if '(' in old_content and '(' in new_content:
            old_params = re.findall(r'\(([^)]*)\)', old_content)
            new_params = re.findall(r'\(([^)]*)\)', new_content)
            if old_params != new_params:
                changes.append("signature_modification")

        # Check for test additions
        if 'assert' not in old_content and 'assert' in new_content:
            changes.append("added_assertions")

        # Check for comment/documentation
        if ('"""' in new_content or "'''" in new_content or '//' in new_content) and \
           ('"""' not in old_content and "'''" not in old_content and '//' not in old_content):
            changes.append("added_documentation")

        # Performance optimizations
        if any(x in new_content for x in ['cache', 'memo', 'optimize', 'batch']):
            changes.append("performance_optimization")

        return changes if changes else ["code_modification"]

    def extract_code_entities(self, content: str) -> List[str]:
        """Extract meaningful entities from code content."""
        entities = []

        # Function names
        functions = re.findall(r'(?:def|function|const) (\w+)', content)
        entities.extend(functions[:5])

        # Class names
        classes = re.findall(r'class (\w+)', content)
        entities.extend(classes[:3])

        # Import modules
        imports = re.findall(r'(?:import|from) ([\w]+)', content)
        entities.extend(imports[:5])

        # Test names
        tests = re.findall(r'test_(\w+)', content)
        entities.extend([f"test_{t}" for t in tests[:3]])

        return list(set(entities))  # Unique entities

    def detect_file_relationships(self, file_path: str) -> List[Tuple[str, str, str]]:
        """Detect relationships between files based on recent edits."""
        relationships = []

        # Check recent edits for co-editing patterns
        recent_files = [e['file'] for e in self.recent_edits[-10:] if e['file'] != file_path]

        for recent_file in set(recent_files):
            # Determine relationship type
            if 'test' in recent_file and 'test' not in file_path:
                relationships.append((file_path, "TESTED_BY", recent_file))
            elif 'test' in file_path and 'test' not in recent_file:
                relationships.append((file_path, "TESTS", recent_file))
            else:
                relationships.append((file_path, "RELATED_TO", recent_file))

        return relationships[:5]  # Limit to 5 relationships

    def store_semantic_memory(self, semantic_data: Dict):
        """Store rich semantic memory in PRISM."""
        if not self.client:
            return

        try:
            # Build comprehensive memory content
            content = {
                "type": semantic_data["type"],
                "content": f"{semantic_data['operation']} on {Path(semantic_data['file']).name}: {', '.join(semantic_data['semantic_changes'][:3])}",
                "semantic": semantic_data["semantic_changes"],
                "entities": semantic_data["entities"],
                "relationships": semantic_data.get("relationships", []),
                "context": {
                    "file": semantic_data["file"],
                    "layer": semantic_data["layer"],
                    "operation": semantic_data["operation"],
                    "session_id": self.session_id,
                    "timestamp": time.time()
                },
                "confidence": semantic_data["confidence"]
            }

            # Determine tier based on importance
            tier = "WORKING"  # Default
            if semantic_data["type"] in ["bug_fix", "security_fix"]:
                tier = "LONGTERM"  # Important fixes
            elif semantic_data["confidence"] >= 0.85:
                tier = "LONGTERM"  # High confidence patterns

            # Store in PRISM
            self.client.store_memory(
                content=json.dumps(content),
                tier=tier,
                metadata={
                    "importance": "high" if tier == "LONGTERM" else "medium",
                    "tags": [semantic_data["type"], semantic_data["layer"], semantic_data["operation"]],
                    "file_path": semantic_data["file"]
                }
            )

            # Store relationships in universal learner
            if semantic_data.get("relationships"):
                for rel in semantic_data["relationships"]:
                    relationship_pattern = {
                        "type": "file_relationship",
                        "content": f"{rel[0]} {rel[1]} {rel[2]}",
                        "source": rel[0],
                        "relation": rel[1],
                        "target": rel[2],
                        "confidence": 0.8
                    }
                    self.learner.learn_pattern(relationship_pattern)

        except Exception as e:
            print(f"Failed to store semantic memory: {e}", file=sys.stderr)

    def track_edit(self, file_path: str, operation: str, tool_input: Dict):
        """Main entry point to track an edit operation."""
        # Skip ephemeral files
        if self.should_skip_file(file_path):
            return

        # Extract semantic information
        semantic_data = self.extract_semantic_changes(file_path, operation, tool_input)

        # Add file relationships
        semantic_data["relationships"] = self.detect_file_relationships(file_path)

        # Check if this edit is a correction (user fixing Claude's output)
        if operation == "Edit":
            old_str = tool_input.get("old_string", "")
            new_str = tool_input.get("new_string", "")
            correction = self.preference_manager.detect_correction(
                file_path, old_str, new_str, self.recent_edits
            )

            if correction and correction.get('should_store'):
                # This is a repeated correction - store as preference
                preference = {
                    'type': 'user_correction',
                    'pattern': correction['pattern'],
                    'confidence': correction['confidence'],
                    'frustration_level': correction['frustration_level'],
                    'correction_count': correction['correction_count'],
                    'applies_to': [Path(file_path).suffix] if Path(file_path).suffix else ['*'],
                    'detected_in': f"Edit to {Path(file_path).name}"
                }

                # Store the preference
                stored = self.preference_manager.store_preference(preference)
                if stored:
                    semantic_data["preference_learned"] = True
                    semantic_data["type"] = "correction_pattern"

        # Track in recent edits
        self.recent_edits.append({
            "file": file_path,
            "operation": operation,
            "timestamp": time.time(),
            "semantic": semantic_data["semantic_changes"],
            "old_content": tool_input.get("old_string", "")[:100] if operation == "Edit" else "",
            "new_content": tool_input.get("new_string", "")[:100] if operation == "Edit" else ""
        })

        # Keep only last 50 edits in memory
        if len(self.recent_edits) > 50:
            self.recent_edits = self.recent_edits[-50:]

        # Store in PRISM
        self.store_semantic_memory(semantic_data)

        # Learn file coupling patterns
        self.learn_file_patterns()

    def learn_file_patterns(self):
        """Learn patterns from recent editing session."""
        if len(self.recent_edits) < 3:
            return

        # Group files edited in close proximity (within 5 minutes)
        time_window = 300  # 5 minutes
        current_time = time.time()

        file_groups = defaultdict(list)
        for edit in self.recent_edits[-20:]:
            if current_time - edit["timestamp"] < time_window:
                # Group by semantic changes
                for change in edit["semantic"]:
                    file_groups[change].append(edit["file"])

        # Store significant patterns
        for change_type, files in file_groups.items():
            if len(set(files)) >= 2:  # At least 2 different files
                pattern = {
                    "type": "edit_pattern",
                    "content": f"When making {change_type}, these files are often modified together: {', '.join(set(files)[:5])}",
                    "change_type": change_type,
                    "files": list(set(files))[:5],
                    "confidence": min(0.9, 0.5 + len(set(files)) * 0.1)
                }
                self.learner.learn_pattern(pattern)

def main():
    """Main hook handler."""
    try:
        input_data = json.loads(sys.stdin.read())
        event_name = input_data.get("hook_event_name", "")
        tool_name = input_data.get("tool_name", "")

        # Only process edit operations
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            tracker = SemanticEditTracker()

            tool_input = input_data.get("tool_input", {})
            file_path = tool_input.get("file_path", "")

            if file_path:
                tracker.track_edit(file_path, tool_name, tool_input)

    except Exception as e:
        print(f"Error in edit_tracker: {e}", file=sys.stderr)

    # Always allow operation to continue
    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()