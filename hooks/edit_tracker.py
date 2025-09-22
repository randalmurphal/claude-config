#!/usr/bin/env python3
"""
Edit Tracker Hook
Tracks file edit patterns and relationships to learn which files are commonly edited together.
"""

import json
import sys
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timezone

# Import universal learner
sys.path.insert(0, str(Path(__file__).parent))
from universal_learner import get_learner

class EditTracker:
    """Track file edit patterns and relationships."""

    def __init__(self):
        self.session_file = Path.home() / ".claude" / "edit_session.json"
        self.session_file.parent.mkdir(exist_ok=True)
        self.session = self.load_session()
        self.learner = get_learner()
        self.architecture_cache = {}  # Cache for layer detection
        self.previous_edits = {}  # Track previous versions to detect degradation

    def load_session(self) -> Dict:
        """Load current edit session."""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    session = json.load(f)
                    # Check if session is recent (within 1 hour)
                    if time.time() - session.get("last_edit", 0) < 3600:
                        return session
            except:
                pass

        # Create new session
        return {
            "session_id": f"edit_{int(time.time())}",
            "started": time.time(),
            "last_edit": time.time(),
            "edited_files": [],
            "edit_sequence": [],
            "file_clusters": defaultdict(list)
        }

    def save_session(self):
        """Save current edit session."""
        # Convert defaultdict to regular dict for JSON
        session_data = dict(self.session)
        if "file_clusters" in session_data and isinstance(session_data["file_clusters"], defaultdict):
            session_data["file_clusters"] = dict(session_data["file_clusters"])

        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

    def track_edit(self, file_path: str, operation: str):
        """Track a file edit."""
        current_time = time.time()

        # Update session
        self.session["last_edit"] = current_time

        # Add to edited files list if not already there
        if file_path not in self.session["edited_files"]:
            self.session["edited_files"].append(file_path)

        # Add to edit sequence with timestamp
        self.session["edit_sequence"].append({
            "file": file_path,
            "operation": operation,
            "timestamp": current_time
        })

        # Track file clustering (files edited close in time)
        self.update_file_clusters(file_path, current_time)

        # Learn patterns if we have enough data
        if len(self.session["edited_files"]) >= 2:
            self.learn_file_relationships()

        # Save session
        self.save_session()

    def update_file_clusters(self, file_path: str, timestamp: float):
        """Update file clustering based on temporal proximity."""
        # Look for files edited within last 5 minutes
        recent_window = 300  # 5 minutes

        recent_edits = []
        for edit in self.session["edit_sequence"][-20:]:  # Check last 20 edits
            if timestamp - edit["timestamp"] < recent_window:
                if edit["file"] != file_path:
                    recent_edits.append(edit["file"])

        # Add to cluster if there are recent edits
        if recent_edits:
            cluster_key = tuple(sorted(set([file_path] + recent_edits[:5])))  # Limit to 5 files
            if "file_clusters" not in self.session:
                self.session["file_clusters"] = {}
            if str(cluster_key) not in self.session["file_clusters"]:
                self.session["file_clusters"][str(cluster_key)] = 0
            self.session["file_clusters"][str(cluster_key)] += 1

    def learn_file_relationships(self):
        """Learn file coupling patterns from edit session."""
        # Check for files edited in same session
        edited_files = self.session["edited_files"]

        if len(edited_files) >= 2:
            # Calculate time proximity
            first_edit = self.session["edit_sequence"][0]["timestamp"] if self.session["edit_sequence"] else 0
            last_edit = self.session["last_edit"]
            time_proximity = last_edit - first_edit if first_edit else None

            # Create rich pattern with semantic content
            files_list = edited_files[-10:]  # Last 10 files max

            # Generate human-readable content
            if len(files_list) == 2:
                content = f"{files_list[0]} and {files_list[1]} are frequently edited together"
            else:
                content = f"Files {', '.join(files_list[:3])} and {len(files_list)-3} others form a related code module"

            # Create pattern with relationships
            pattern = {
                "type": "file_coupling",
                "content": content,
                "files": files_list,
                "reason": "edited in same session within {:.0f} seconds".format(time_proximity) if time_proximity else "edited together",
                "edit_sequence": [e["file"] for e in self.session["edit_sequence"][-20:]],
                "frequency": len(self.session["edit_sequence"]),
                "time_proximity": time_proximity,
                "confidence": min(0.9, 0.5 + len(files_list) * 0.1),
                "relationships": self._generate_file_relationships(files_list)
            }

            # Learn the pattern
            self.learner.learn_pattern(pattern)

            # Learn specific file pairs that are frequently edited together
            self.learn_file_pairs()

    def _generate_file_relationships(self, files: List[str]) -> List[tuple]:
        """Generate Neo4j relationships for file couplings."""
        relationships = []
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                relationships.append((
                    file1,
                    "COUPLED_WITH",
                    file2,
                    {"edit_frequency": len(self.session["edit_sequence"])}
                ))

        # Add module relationships if detectable
        for file in files:
            if "test" in file.lower():
                # Find the file it tests
                base_name = file.replace("test_", "").replace("_test.", ".")
                for other_file in files:
                    if base_name in other_file and other_file != file:
                        relationships.append((
                            other_file,
                            "TESTED_BY",
                            file
                        ))

        return relationships

    def learn_file_pairs(self):
        """Learn specific file pairs that are commonly edited together."""
        # Look for file pairs in clusters
        if "file_clusters" in self.session:
            for cluster_str, count in self.session["file_clusters"].items():
                if count >= 2:  # Edited together at least twice
                    try:
                        # Parse cluster string back to list
                        cluster = eval(cluster_str) if cluster_str.startswith("(") else [cluster_str]
                        if len(cluster) >= 2:
                            files = list(cluster)

                            # Create semantic pattern
                            pattern = {
                                "type": "file_coupling",
                                "content": f"Files {files[0]} and {files[1]} are strongly coupled (edited together {count} times)",
                                "files": files,
                                "reason": f"co-edited {count} times in close proximity",
                                "frequency": count,
                                "time_proximity": 60,  # Close proximity since they're clustered
                                "confidence": min(0.95, 0.6 + count * 0.1),
                                "relationships": [(files[0], "STRONGLY_COUPLED", files[1], {"frequency": count})]
                            }

                            self.learner.learn_pattern(pattern)
                    except:
                        pass

    def get_related_files(self, file_path: str) -> List[str]:
        """Get files commonly edited with the given file."""
        # Get relevant memories from learner
        context = {"file": file_path, "type": "file_coupling"}
        memories = self.learner.get_relevant_memories(context, limit=5)

        related_files = set()
        for memory in memories:
            try:
                content = json.loads(memory.get("content", "{}"))
                if content.get("type") == "file_coupling" and content.get("files"):
                    for f in content["files"]:
                        if f != file_path:
                            related_files.add(f)
            except:
                pass

        return list(related_files)[:5]  # Return top 5 related files

    def detect_layer(self, file_path: str) -> str:
        """Detect architectural layer from file path."""
        if file_path in self.architecture_cache:
            return self.architecture_cache[file_path]

        path_parts = Path(file_path).parts
        file_name = Path(file_path).name.lower()

        # Common layer patterns
        layer_patterns = {
            'presentation': ['ui', 'view', 'controller', 'handler', 'route', 'api', 'endpoint'],
            'business': ['service', 'manager', 'processor', 'business', 'logic', 'use_case'],
            'data': ['repository', 'dao', 'model', 'entity', 'database', 'db', 'storage'],
            'infrastructure': ['config', 'util', 'helper', 'common', 'shared'],
            'test': ['test', 'spec', 'tests']
        }

        # Check path and filename
        for layer, patterns in layer_patterns.items():
            for pattern in patterns:
                if pattern in file_name or any(pattern in part.lower() for part in path_parts):
                    self.architecture_cache[file_path] = layer
                    return layer

        # Default to infrastructure
        self.architecture_cache[file_path] = 'infrastructure'
        return 'infrastructure'

    def extract_imports(self, content: str, language: str = 'python') -> List[str]:
        """Extract import statements from code content."""
        imports = []

        if language == 'python':
            # Python imports
            import_patterns = [
                r'^import\s+([\w.]+)',
                r'^from\s+([\w.]+)\s+import'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.extend(matches)

        elif language in ['javascript', 'typescript']:
            # JS/TS imports
            import_patterns = [
                r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",
                r"require\(['\"]([^'\"]+)['\"]\)"
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)

        return imports

    def track_architectural_patterns(self, file_path: str, content: str = None):
        """Track architectural patterns from file edits."""
        layer = self.detect_layer(file_path)

        # Store layer information
        pattern = {
            "type": "architecture_pattern",
            "content": f"{file_path} belongs to {layer} layer",
            "file": file_path,
            "layer": layer,
            "confidence": 0.85,
            "relationships": [(file_path, "BELONGS_TO", layer)]
        }

        self.learner.learn_pattern(pattern)

        # If we have content, extract and track imports
        if content:
            language = 'python' if file_path.endswith('.py') else 'javascript'
            imports = self.extract_imports(content, language)

            if imports:
                # Track import patterns
                import_pattern = {
                    "type": "import_pattern",
                    "content": f"{file_path} imports from {', '.join(imports[:5])}",
                    "file": file_path,
                    "imports": imports,
                    "layer": layer,
                    "confidence": 0.9,
                    "relationships": [(file_path, "IMPORTS_FROM", imp) for imp in imports[:10]]
                }

                self.learner.learn_pattern(import_pattern)

                # Check for layer violations
                self.check_layer_violations(file_path, layer, imports)

    def check_layer_violations(self, file_path: str, source_layer: str, imports: List[str]) -> List[Dict]:
        """Check and track architectural layer violations."""
        violations = []

        # Define allowed dependencies
        layer_hierarchy = {
            'presentation': ['business', 'infrastructure'],
            'business': ['data', 'infrastructure'],
            'data': ['infrastructure'],
            'infrastructure': [],
            'test': ['presentation', 'business', 'data', 'infrastructure']
        }

        allowed_layers = layer_hierarchy.get(source_layer, [])

        for import_path in imports:
            # Try to detect the target layer
            if '.' in import_path:
                target_layer = self.detect_layer(import_path.replace('.', '/') + '.py')
            else:
                target_layer = self.detect_layer(import_path)

            # Check for violation
            if target_layer not in allowed_layers and target_layer != source_layer:
                if target_layer != 'infrastructure':  # Infrastructure is always allowed
                    # Track the violation
                    violation_pattern = {
                        "type": "architecture_violation",
                        "content": f"{source_layer} layer ({file_path}) should not import from {target_layer} layer ({import_path})",
                        "file": file_path,
                        "source_layer": source_layer,
                        "target_layer": target_layer,
                        "import": import_path,
                        "confidence": 0.95,
                        "relationships": [
                            (file_path, "VIOLATES_ARCHITECTURE", import_path),
                            (source_layer, "SHOULD_NOT_IMPORT", target_layer)
                        ]
                    }

                    self.learner.learn_pattern(violation_pattern)
                    violations.append({
                        'source': file_path,
                        'source_layer': source_layer,
                        'target_layer': target_layer,
                        'import': import_path
                    })

        return violations

    def detect_degradation_attempt(self, file_path: str, new_content: str) -> Dict:
        """Detect if new code is a degraded version of previous code."""
        degradation_indicators = {}

        # Get previous version if exists
        if file_path in self.previous_edits:
            old_content = self.previous_edits[file_path]

            # Count complexity indicators
            old_try_count = len(re.findall(r'\btry\s*:', old_content))
            new_try_count = len(re.findall(r'\btry\s*:', new_content))

            old_except_count = len(re.findall(r'\bexcept\s*.*:', old_content))
            new_except_count = len(re.findall(r'\bexcept\s*.*:', new_content))

            # Check for degradation patterns
            if new_try_count > old_try_count:
                degradation_indicators['increased_try_blocks'] = {
                    'old': old_try_count,
                    'new': new_try_count,
                    'message': 'Adding more try blocks instead of fixing root cause'
                }

            if new_except_count > old_except_count:
                degradation_indicators['increased_except_blocks'] = {
                    'old': old_except_count,
                    'new': new_except_count,
                    'message': 'Adding more exception handlers instead of preventing errors'
                }

            # Check for fallback keywords
            fallback_keywords = ['fallback', 'workaround', 'hack', 'temporary', 'TODO', 'FIXME']
            old_fallback_count = sum(1 for kw in fallback_keywords if kw.lower() in old_content.lower())
            new_fallback_count = sum(1 for kw in fallback_keywords if kw.lower() in new_content.lower())

            if new_fallback_count > old_fallback_count:
                degradation_indicators['increased_fallback_keywords'] = {
                    'old': old_fallback_count,
                    'new': new_fallback_count,
                    'message': 'Adding workarounds instead of proper fixes'
                }

            # Check for simplified logic (degradation)
            if 'advanced' in old_content and 'simple' in new_content and 'simple' not in old_content:
                degradation_indicators['logic_simplification'] = {
                    'message': 'Replacing advanced logic with simpler version'
                }

            # If degradation detected, store as pattern
            if degradation_indicators:
                pattern = {
                    'type': 'degradation_attempt',
                    'content': f"Code degradation detected in {file_path}",
                    'file': file_path,
                    'indicators': degradation_indicators,
                    'confidence': 0.9,
                    'relationships': [(file_path, 'DEGRADED_TO', 'simpler_version')]
                }
                self.learner.learn_pattern(pattern)

        # Store current version for future comparison
        self.previous_edits[file_path] = new_content

        return degradation_indicators

def main():
    """Main hook handler."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps({"action": "continue"}))
        return

    # Track edits from Write, Edit, MultiEdit tools
    tool_name = input_data.get("tool_name", "")
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        print(json.dumps({"action": "continue"}))
        return

    event_type = input_data.get("hook_event_name", "")

    # Track on both pre and post events to capture the full edit session
    if event_type not in ["PreToolUse", "PostToolUse"]:
        print(json.dumps({"action": "continue"}))
        return

    # Initialize tracker
    tracker = EditTracker()

    # Extract file path based on tool type
    tool_input = input_data.get("tool_input", {})
    file_path = None

    if tool_name in ["Write", "Edit"]:
        file_path = tool_input.get("file_path")
    elif tool_name == "MultiEdit":
        file_path = tool_input.get("file_path")
        # Could also track all files in multi-edit, but for now just track the main file

    if file_path:
        # Track the edit
        tracker.track_edit(file_path, tool_name)

        # On PreToolUse, suggest related files
        if event_type == "PreToolUse":
            related = tracker.get_related_files(file_path)
            if related:
                suggestion = f"Files commonly edited with {Path(file_path).name}: {', '.join([Path(f).name for f in related[:3]])}"
                print(json.dumps({
                    "action": "continue",
                    "message": suggestion
                }), file=sys.stderr)

        # On PostToolUse, track architectural patterns
        if event_type == "PostToolUse":
            # Get the content to analyze
            content = None
            if tool_name == "Write":
                content = tool_input.get("content")
            elif tool_name == "Edit":
                content = tool_input.get("new_string")
            elif tool_name == "MultiEdit":
                # Combine all edits
                edits = tool_input.get("edits", [])
                if edits:
                    content = "\n".join([e.get("new_string", "") for e in edits])

            # Track architectural patterns from the content
            if content:
                tracker.track_architectural_patterns(file_path, content)

                # Check for degradation attempts
                degradation = tracker.detect_degradation_attempt(file_path, content)
                if degradation:
                    print(json.dumps({
                        "action": "continue",
                        "warning": f"⚠️ CODE DEGRADATION DETECTED in {Path(file_path).name}:\n" +
                                  "\n".join([f"  - {ind['message']}" for ind in degradation.values()])
                    }), file=sys.stderr)

    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()