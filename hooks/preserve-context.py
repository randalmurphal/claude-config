#!/usr/bin/env python3
"""
Universal Context Preservation Hook for Claude Code Compacting
Intelligently preserves important context across any project type/language
"""

import json
import sys
import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import os
import fnmatch

# Universal patterns that work across all languages
REQUIREMENT_PATTERNS = [
    r"(?i)\b(MUST|NEVER|ALWAYS|IMPORTANT|CRITICAL|REQUIRED|TODO|FIXME|HACK|WARNING|NOTE)\b[:\s]+([^\n]+)",
    r"(?i)\b(don't|do not|avoid|ensure|make sure|be sure|remember)\b[:\s]+([^\n]+)",
    r"(?i)^[-*]\s*(requirement|constraint|rule|policy)[:\s]+([^\n]+)",
]

# Config files that are universally important
UNIVERSAL_CONFIGS = [
    "Dockerfile", "docker-compose.yml", ".dockerignore",
    "Makefile", ".env", ".env.example", ".env.local",
    ".gitignore", ".github/workflows/*",
    "README.md", "CONTRIBUTING.md", "LICENSE",
]

# Language-specific important files
LANGUAGE_PATTERNS = {
    "python": ["requirements*.txt", "setup.py", "pyproject.toml", "*.py", "__init__.py", "main.py"],
    "javascript": ["package*.json", "*.config.js", "index.js", "app.js", "*.jsx", "*.tsx"],
    "typescript": ["tsconfig*.json", "*.ts", "*.tsx", "*.d.ts"],
    "go": ["go.mod", "go.sum", "main.go", "*.go"],
    "rust": ["Cargo.toml", "Cargo.lock", "main.rs", "lib.rs", "*.rs"],
    "java": ["pom.xml", "build.gradle", "*.java", "Main.java"],
    "ruby": ["Gemfile", "Gemfile.lock", "*.rb", "Rakefile"],
    "php": ["composer.json", "composer.lock", "*.php"],
    "c": ["Makefile", "CMakeLists.txt", "*.c", "*.h"],
    "cpp": ["Makefile", "CMakeLists.txt", "*.cpp", "*.hpp", "*.cc", "*.h"],
}

# Test file patterns
TEST_PATTERNS = [
    r"test[s]?[_\-\.]", r"spec[s]?[_\-\.]", r"[_\-\.]test[s]?\.", r"[_\-\.]spec[s]?\.",
    r"__tests__", r"tests?/", r"spec/", r"test_", r"_test\.", r"\.test\.", r"\.spec\."
]

class ContextPreserver:
    def __init__(self, transcript_path: str):
        self.transcript_path = transcript_path
        self.transcript = []
        self.file_access_count = defaultdict(int)
        self.file_modifications = defaultdict(list)
        self.errors_encountered = []
        self.test_failures = []
        self.unresolved_issues = []
        self.requirements = []
        self.todos = []
        self.key_discoveries = []
        self.project_type = None
        self.current_focus = []
        self.failed_attempts = []  # Track what didn't work
        self.working_solutions = []  # Track what DID work
        self.current_objective = ""  # What we're trying to accomplish
        self.key_decisions = []  # Architectural decisions made
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from preferences file if it exists"""
        config_path = os.path.expanduser("~/.claude/compact-preferences.json")
        default_config = {
            "always_preserve": [],
            "keyword_boost": ["TODO", "FIXME", "HACK"],
            "file_pattern_boost": [],
            "error_keywords": ["FAILED", "Error", "AssertionError"],
            "max_context_lines": 100,
            "max_files_to_preserve": 20,
            "max_requirements": 15,
            "max_issues": 10
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except (json.JSONDecodeError, IOError):
                pass  # Use defaults if config is invalid
        
        return default_config
        
    def load_transcript(self):
        """Load and parse the transcript file"""
        try:
            with open(self.transcript_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            self.transcript.append(entry)
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            sys.stderr.write(f"Transcript file not found: {self.transcript_path}\n")
            sys.exit(1)
    
    def detect_project_type(self) -> str:
        """Auto-detect the primary language/framework of the project"""
        file_extensions = Counter()
        frameworks = set()
        
        for entry in self.transcript:
            # Check tool uses for file paths
            if entry.get("type") == "tool_use":
                tool_name = entry.get("name", "")
                if tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
                    file_path = entry.get("input", {}).get("file_path", "")
                    if file_path:
                        ext = Path(file_path).suffix.lower()
                        if ext:
                            file_extensions[ext] += 1
                        
                        # Check for framework indicators
                        if "package.json" in file_path:
                            frameworks.add("node")
                        elif "requirements.txt" in file_path or "setup.py" in file_path:
                            frameworks.add("python")
                        elif "go.mod" in file_path:
                            frameworks.add("go")
                        elif "Cargo.toml" in file_path:
                            frameworks.add("rust")
        
        # Determine primary language
        if file_extensions:
            most_common = file_extensions.most_common(1)[0][0]
            lang_map = {
                ".py": "python", ".js": "javascript", ".ts": "typescript",
                ".go": "go", ".rs": "rust", ".java": "java", ".rb": "ruby",
                ".php": "php", ".c": "c", ".cpp": "cpp", ".cc": "cpp"
            }
            self.project_type = lang_map.get(most_common, "unknown")
        
        return self.project_type or "unknown"
    
    def analyze_file_access(self):
        """Track file access patterns and modifications"""
        recent_entries = self.transcript[-50:] if len(self.transcript) > 50 else self.transcript
        
        for i, entry in enumerate(self.transcript):
            # Handle both formats: direct tool_use and nested in message.content
            tools_to_process = []
            
            # Format 1: Direct tool_use (mock transcripts)
            if entry.get("type") == "tool_use":
                tools_to_process.append((entry.get("name", ""), entry.get("input", {})))
            
            # Format 2: Nested in message.content (actual Claude transcripts)
            elif entry.get("type") in ["assistant", "user"] and "message" in entry:
                message = entry.get("message", {})
                content = message.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            tools_to_process.append((item.get("name", ""), item.get("input", {})))
            
            # Process all found tools
            for tool_name, tool_input in tools_to_process:
                
                # Track file access
                if tool_name in ["Read", "Write", "Edit", "MultiEdit", "NotebookEdit"]:
                    file_path = tool_input.get("file_path") or tool_input.get("notebook_path", "")
                    if file_path:
                        self.file_access_count[file_path] += 1
                        
                        # Track modifications with context
                        if tool_name in ["Write", "Edit", "MultiEdit"]:
                            # Look for preceding user message to understand why
                            context = self._find_preceding_user_message(i)
                            self.file_modifications[file_path].append({
                                "type": tool_name,
                                "context": context[:100] if context else "No context"
                            })
                        
                        # Track recent focus
                        if entry in recent_entries:
                            if file_path not in self.current_focus:
                                self.current_focus.append(file_path)
    
    def extract_requirements(self):
        """Extract important requirements and instructions from user messages"""
        for entry in self.transcript:
            content = ""
            
            # Format 1: Direct human_text (mock)
            if entry.get("type") == "human_text":
                content = entry.get("content", "")
            
            # Format 2: User message in actual transcript
            elif entry.get("type") == "user" and "message" in entry:
                message = entry.get("message", {})
                msg_content = message.get("content", [])
                if isinstance(msg_content, list):
                    for item in msg_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            content += item.get("text", "") + "\n"
                elif isinstance(msg_content, str):
                    content = msg_content
            
            if content:
                
                # Check for requirement patterns
                for pattern in REQUIREMENT_PATTERNS:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    for match in matches:
                        if isinstance(match, tuple):
                            requirement = " ".join(match).strip()
                        else:
                            requirement = match.strip()
                        
                        # Check for boosted keywords from config
                        is_boosted = any(keyword in requirement.upper() for keyword in self.config.get('keyword_boost', []))
                        
                        if len(requirement) > 10:  # Filter out trivial matches
                            if is_boosted:
                                # Boosted requirements go to the front
                                self.requirements.insert(0, requirement[:200])
                            else:
                                self.requirements.append(requirement[:200])  # Limit length
    
    def analyze_errors_and_tests(self):
        """Find test failures, errors, and unresolved issues"""
        for i, entry in enumerate(self.transcript):
            content = ""
            
            # Format 1: Direct tool_result (mock)
            if entry.get("type") == "tool_result":
                content = entry.get("content", "")
            
            # Format 2: Tool result in actual transcript
            elif entry.get("type") == "user" and "message" in entry:
                message = entry.get("message", {})
                msg_content = message.get("content", [])
                if isinstance(msg_content, list):
                    for item in msg_content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            result_content = item.get("content", "")
                            if isinstance(result_content, dict):
                                content += json.dumps(result_content) + "\n"
                            else:
                                content += str(result_content) + "\n"
            
            if content:
                if isinstance(content, dict):
                    content = json.dumps(content)
                elif not isinstance(content, str):
                    content = str(content)
                
                # Check for test failures (include config error keywords)
                test_failure_patterns = [
                    r"FAIL[ED]?[:\s]+(.*?)(?:\n|$)",
                    r"(\d+)\s+failed?,\s+\d+\s+passed",
                    r"AssertionError[:\s]+(.*?)(?:\n|$)",
                    r"Test.*failed",
                    r"✗\s+(.*?)(?:\n|$)",  # Common test failure marker
                    r"Error[:\s]+.*test.*",
                ]
                
                # Add custom error keywords from config
                for keyword in self.config.get('error_keywords', []):
                    test_failure_patterns.append(rf"{re.escape(keyword)}[:\s]+(.*?)(?:\n|$)")
                
                for pattern in test_failure_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Check if this was addressed in subsequent entries
                        if not self._was_issue_addressed(i, "test", matches[0] if isinstance(matches[0], str) else matches[0][0]):
                            self.test_failures.extend(matches[:3])  # Limit to avoid spam
                
                # Check for other errors
                error_patterns = [
                    r"(?:Error|ERROR)[:\s]+(.*?)(?:\n|$)",
                    r"(?:Exception|EXCEPTION)[:\s]+(.*?)(?:\n|$)",
                    r"Failed to\s+(.*?)(?:\n|$)",
                    r"Could not\s+(.*?)(?:\n|$)",
                    r"Unable to\s+(.*?)(?:\n|$)",
                ]
                
                for pattern in error_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # Check if this was a test-related error (already captured)
                        is_test = any(test_pat in content.lower() for test_pat in ["test", "spec", "jest", "pytest", "mocha"])
                        if not is_test and not self._was_issue_addressed(i, "error", matches[0]):
                            self.errors_encountered.extend(matches[:2])
                
                # Check for TODO/FIXME items that weren't completed
                todo_patterns = [
                    r"(?:TODO|FIXME)[:\s]+(.*?)(?:\n|$)",
                    r"(?:HACK|XXX)[:\s]+(.*?)(?:\n|$)",
                ]
                
                for pattern in todo_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        self.todos.extend(matches[:3])
    
    def analyze_todos(self):
        """Extract todo items and their completion status"""
        incomplete_todos = []
        
        for entry in self.transcript:
            # Format 1: Direct tool_use (mock)
            if entry.get("type") == "tool_use" and entry.get("name") == "TodoWrite":
                todos = entry.get("input", {}).get("todos", [])
                for todo in todos:
                    if todo.get("status") != "completed":
                        incomplete_todos.append(todo.get("content", "Unknown task"))
            
            # Format 2: Nested in message.content (actual transcript)
            elif entry.get("type") in ["assistant"] and "message" in entry:
                message = entry.get("message", {})
                content = message.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_use" and item.get("name") == "TodoWrite":
                            todos = item.get("input", {}).get("todos", [])
                            for todo in todos:
                                if todo.get("status") != "completed":
                                    incomplete_todos.append(todo.get("content", "Unknown task"))
        
        # Add to unresolved issues
        self.unresolved_issues.extend(incomplete_todos[:5])  # Limit to top 5
    
    def _was_issue_addressed(self, issue_index: int, issue_type: str, issue_content: str) -> bool:
        """Check if an error/test failure was addressed in subsequent entries"""
        # Look at next 10 entries for resolution
        for entry in self.transcript[issue_index + 1:issue_index + 11]:
            if entry.get("type") == "tool_use":
                tool_name = entry.get("name", "")
                if tool_name in ["Edit", "Write", "MultiEdit"]:
                    # Check if the edit might have addressed the issue
                    tool_input = str(entry.get("input", {}))
                    if any(keyword in tool_input.lower() for keyword in ["fix", "resolve", "correct", "address"]):
                        return True
            
            if entry.get("type") == "tool_result":
                result = str(entry.get("content", ""))
                # Check for success indicators
                if issue_type == "test" and any(word in result.lower() for word in ["pass", "success", "✓", "ok"]):
                    return True
                if issue_type == "error" and "success" in result.lower():
                    return True
        
        return False
    
    def _find_preceding_user_message(self, index: int) -> str:
        """Find the most recent user message before the given index"""
        for i in range(index - 1, max(0, index - 10), -1):
            if self.transcript[i].get("type") == "human_text":
                return self.transcript[i].get("content", "")[:200]
        return ""
    
    def identify_key_discoveries(self):
        """Identify important discoveries and code patterns found"""
        for i, entry in enumerate(self.transcript):
            if entry.get("type") == "tool_use":
                tool_name = entry.get("name", "")
                
                # Track search results that led to edits
                if tool_name in ["Grep", "Glob"]:
                    # Check if next actions were edits
                    if i + 1 < len(self.transcript):
                        next_entry = self.transcript[i + 1]
                        if next_entry.get("type") == "tool_use" and next_entry.get("name") in ["Edit", "Read", "MultiEdit"]:
                            pattern = entry.get("input", {}).get("pattern", "")
                            if pattern:
                                self.key_discoveries.append(f"Found pattern '{pattern}' (led to edits)")
    
    def track_working_solutions(self):
        """Track commands and approaches that worked successfully"""
        for i in range(len(self.transcript) - 1):
            entry = self.transcript[i]
            next_entry = self.transcript[i + 1] if i + 1 < len(self.transcript) else None
            
            if next_entry:
                # Pattern: Command that succeeded
                if self._is_bash_command(entry):
                    cmd = self._get_command(entry)
                    if cmd and not self._contains_error(next_entry):
                        # Check if it's a meaningful success (not just ls, pwd, etc.)
                        if any(important in cmd.lower() for important in ['test', 'build', 'run', 'start', 'install', 'migrate', 'deploy']):
                            success = f"Command '{cmd[:80]}' succeeded"
                            if success not in self.working_solutions and 'failed' not in next_entry.get('content', '').lower():
                                self.working_solutions.append(success)
    
    def extract_current_objective(self):
        """Try to identify what the user is trying to accomplish"""
        objective_patterns = [
            r"(?i)(?:i'm |we're |let's |need to |want to |trying to |please |help me |can you )(.*?)(?:\.|$)",
            r"(?i)(?:the goal is |objective is |task is |working on )(.*?)(?:\.|$)",
            r"(?i)(?:implement|create|build|fix|debug|solve|add|update|refactor) (.*?)(?:\.|$)"
        ]
        
        # Look through recent user messages for objective
        for entry in reversed(self.transcript[-20:]):  # Check last 20 entries
            if entry.get("type") in ["human_text", "user"]:
                content = self._get_content_text(entry)
                for pattern in objective_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        objective = matches[0] if isinstance(matches[0], str) else matches[0][0]
                        if len(objective) > 20:  # Filter out trivial matches
                            self.current_objective = objective[:200]
                            return
    
    def track_key_decisions(self):
        """Track architectural and design decisions made"""
        decision_patterns = [
            r"(?i)(?:decided to |going to use |let's use |we'll use |switch to |using )(.*?)(?:instead of|because|for|$)",
            r"(?i)(?:don't use |avoid |never use |not using )(.*?)(?:because|since|as|$)",
            r"(?i)(?:chose |selected |picked |went with )(.*?)(?:over|instead|because|$)"
        ]
        
        for entry in self.transcript:
            if entry.get("type") in ["human_text", "user", "assistant"]:
                content = self._get_content_text(entry)
                for pattern in decision_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        decision = match if isinstance(match, str) else match[0]
                        if len(decision) > 15 and len(decision) < 150:
                            if decision not in self.key_decisions:
                                self.key_decisions.append(decision)
    
    def track_failed_attempts(self):
        """Track approaches that were tried but didn't work"""
        for i in range(len(self.transcript) - 2):
            entry = self.transcript[i]
            next_entry = self.transcript[i + 1] if i + 1 < len(self.transcript) else None
            next_next = self.transcript[i + 2] if i + 2 < len(self.transcript) else None
            
            # Pattern 1: Edit followed by error followed by different edit
            if self._is_edit_tool(entry) and next_entry and self._contains_error(next_entry):
                file_path = self._get_file_path(entry)
                error_msg = self._extract_error_message(next_entry)
                if file_path and error_msg:
                    # Check if we tried a different approach after
                    if next_next and self._is_edit_tool(next_next):
                        attempt = f"Failed edit to {file_path}: {error_msg[:100]}"
                        if attempt not in self.failed_attempts:
                            self.failed_attempts.append(attempt)
            
            # Pattern 2: Command that failed followed by different command
            if self._is_bash_command(entry) and next_entry and self._contains_error(next_entry):
                cmd = self._get_command(entry)
                error = self._extract_error_message(next_entry)
                if cmd and error and next_next and self._is_bash_command(next_next):
                    next_cmd = self._get_command(next_next)
                    if next_cmd != cmd:  # Different command tried
                        attempt = f"Failed command '{cmd[:50]}': {error[:100]}"
                        if attempt not in self.failed_attempts:
                            self.failed_attempts.append(attempt)
    
    def _is_edit_tool(self, entry):
        """Check if entry is an edit tool use"""
        if entry.get("type") == "tool_use" and entry.get("name") in ["Edit", "Write", "MultiEdit"]:
            return True
        # Check nested format
        if entry.get("type") in ["assistant"] and "message" in entry:
            content = entry.get("message", {}).get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        if item.get("name") in ["Edit", "Write", "MultiEdit"]:
                            return True
        return False
    
    def _is_bash_command(self, entry):
        """Check if entry is a bash command"""
        if entry.get("type") == "tool_use" and entry.get("name") == "Bash":
            return True
        # Check nested format
        if entry.get("type") in ["assistant"] and "message" in entry:
            content = entry.get("message", {}).get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        if item.get("name") == "Bash":
                            return True
        return False
    
    def _get_file_path(self, entry):
        """Extract file path from tool use"""
        # Direct format
        if entry.get("type") == "tool_use":
            return entry.get("input", {}).get("file_path", "")
        # Nested format
        if "message" in entry:
            content = entry.get("message", {}).get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        return item.get("input", {}).get("file_path", "")
        return ""
    
    def _get_command(self, entry):
        """Extract command from bash tool use"""
        # Direct format
        if entry.get("type") == "tool_use":
            return entry.get("input", {}).get("command", "")
        # Nested format
        if "message" in entry:
            content = entry.get("message", {}).get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        return item.get("input", {}).get("command", "")
        return ""
    
    def _contains_error(self, entry):
        """Check if entry contains an error"""
        # Check tool results
        if entry.get("type") in ["tool_result", "user"]:
            content = self._get_content_text(entry)
            error_indicators = ["error", "failed", "exception", "traceback", "syntaxerror", 
                              "typeerror", "nameerror", "attributeerror", "does not exist",
                              "command not found", "no such file", "permission denied"]
            if any(indicator in content.lower() for indicator in error_indicators):
                return True
        return False
    
    def _extract_error_message(self, entry):
        """Extract error message from entry"""
        content = self._get_content_text(entry)
        # Try to extract the most relevant part of the error
        lines = content.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ["error", "failed", "exception"]):
                return line.strip()
        return content[:200] if content else ""
    
    def _get_content_text(self, entry):
        """Extract text content from various entry formats"""
        # Direct content
        if "content" in entry:
            content = entry["content"]
            if isinstance(content, str):
                return content
            elif isinstance(content, dict):
                return json.dumps(content)
        
        # Nested in message
        if "message" in entry:
            msg_content = entry["message"].get("content", [])
            if isinstance(msg_content, str):
                return msg_content
            elif isinstance(msg_content, list):
                texts = []
                for item in msg_content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            texts.append(item.get("text", ""))
                        elif item.get("type") == "tool_result":
                            result = item.get("content", "")
                            if isinstance(result, str):
                                texts.append(result)
                            else:
                                texts.append(json.dumps(result))
                return "\n".join(texts)
        return ""
    
    def build_preserved_context(self) -> str:
        """Build the final preserved context string"""
        lines = ["=== PRESERVED CONTEXT FROM PREVIOUS WORK ===\n"]
        
        # Add current objective if identified
        if self.current_objective:
            lines.append("📍 CURRENT OBJECTIVE:")
            lines.append(self.current_objective)
            lines.append("")
        
        # Add requirements if any
        if self.requirements:
            lines.append("KEY REQUIREMENTS AND CONSTRAINTS:")
            max_reqs = self.config.get('max_requirements', 15)
            for req in list(dict.fromkeys(self.requirements))[:max_reqs]:  # Dedupe while preserving order
                lines.append(f"• {req}")
            lines.append("")
        
        # Add key decisions made
        if self.key_decisions:
            lines.append("🏗️ KEY DECISIONS MADE:")
            for decision in self.key_decisions[:8]:  # Limit to 8
                lines.append(f"• {decision}")
            lines.append("")
        
        # Add working solutions
        if self.working_solutions:
            lines.append("✅ CONFIRMED WORKING APPROACHES:")
            for solution in self.working_solutions[:10]:  # Limit to 10
                lines.append(f"• {solution}")
            lines.append("")
        
        # Add failed attempts
        if self.failed_attempts:
            lines.append("❌ APPROACHES THAT DIDN'T WORK (Don't retry these):")
            for attempt in self.failed_attempts[:10]:  # Limit to 10 most relevant
                lines.append(f"• {attempt}")
            lines.append("")
        
        # Add unresolved issues (PRIORITY)
        if self.test_failures or self.errors_encountered or self.unresolved_issues:
            lines.append("⚠️ UNRESOLVED ISSUES REQUIRING ATTENTION:")
            
            if self.test_failures:
                lines.append("\nFailed Tests:")
                for failure in list(set(str(f) for f in self.test_failures))[:5]:
                    lines.append(f"• {failure[:150]}")
            
            if self.errors_encountered:
                lines.append("\nErrors Not Addressed:")
                for error in list(set(str(e) for e in self.errors_encountered))[:5]:
                    lines.append(f"• {error[:150]}")
            
            if self.unresolved_issues:
                lines.append("\nIncomplete Tasks:")
                for issue in self.unresolved_issues[:5]:
                    lines.append(f"• {issue}")
            
            lines.append("")
        
        # Add important files
        important_files = self._get_important_files()
        if important_files:
            lines.append("IMPORTANT FILES (by access frequency and recency):")
            max_files = self.config.get('max_files_to_preserve', 20)
            for file_path, reason in important_files[:max_files]:
                lines.append(f"• {file_path} - {reason}")
            lines.append("")
        
        # Add current focus
        if self.current_focus:
            lines.append("RECENT FOCUS AREAS:")
            for file_path in self.current_focus[:10]:
                lines.append(f"• {file_path}")
            lines.append("")
        
        # Add key discoveries
        if self.key_discoveries:
            lines.append("KEY DISCOVERIES:")
            for discovery in list(set(self.key_discoveries))[:8]:
                lines.append(f"• {discovery}")
            lines.append("")
        
        # Add todos if any
        if self.todos:
            lines.append("TODOS/FIXMES IN CODE:")
            for todo in list(set(str(t) for t in self.todos))[:5]:
                lines.append(f"• {todo[:150]}")
            lines.append("")
        
        # Add project type
        if self.project_type and self.project_type != "unknown":
            lines.append(f"PROJECT TYPE: {self.project_type}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_important_files(self) -> List[Tuple[str, str]]:
        """Get list of important files with reasons"""
        important = []
        
        for file_path, count in self.file_access_count.items():
            importance_score = count
            reason_parts = []
            
            # High access count
            if count >= 3:
                importance_score += count * 2
                reason_parts.append(f"accessed {count}x")
            
            # Recently modified
            if file_path in self.file_modifications:
                importance_score += len(self.file_modifications[file_path]) * 3
                reason_parts.append(f"modified {len(self.file_modifications[file_path])}x")
            
            # Is a config file or in always_preserve list
            if any(pattern in file_path for pattern in self.config.get('always_preserve', [])):
                importance_score += 10
                reason_parts.append("always preserve")
            elif any(pattern in file_path.lower() for pattern in ["config", "settings", ".env", "package.json", "requirements"]):
                importance_score += 5
                reason_parts.append("config")
            
            # Check file pattern boost from config
            for pattern in self.config.get('file_pattern_boost', []):
                if fnmatch.fnmatch(file_path, pattern):
                    importance_score += 7
                    reason_parts.append("boosted")
                    break
            
            # Is a test file
            if any(re.search(pattern, file_path, re.IGNORECASE) for pattern in TEST_PATTERNS):
                importance_score += 3
                reason_parts.append("tests")
            
            # Current focus
            if file_path in self.current_focus:
                importance_score += 10
                reason_parts.append("recent")
            
            if importance_score > 2:  # Threshold for importance
                reason = ", ".join(reason_parts) if reason_parts else f"score: {importance_score}"
                important.append((file_path, reason))
        
        # Sort by importance score (approximated by reason length + position)
        important.sort(key=lambda x: len(x[1]), reverse=True)
        return important
    
    def run(self):
        """Main execution flow"""
        self.load_transcript()
        self.detect_project_type()
        self.analyze_file_access()
        self.extract_requirements()
        self.analyze_errors_and_tests()
        self.analyze_todos()
        self.identify_key_discoveries()
        self.track_failed_attempts()  # Track what didn't work
        self.track_working_solutions()  # Track what DID work
        self.extract_current_objective()  # What are we trying to do?
        self.track_key_decisions()  # Important decisions made
        
        preserved_context = self.build_preserved_context()
        
        # Return as JSON for Claude
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreCompact",
                "additionalContext": preserved_context
            }
        }
        
        print(json.dumps(output))
        return 0

def main():
    """Main entry point for the hook"""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        transcript_path = input_data.get("transcript_path", "")
        
        if not transcript_path:
            sys.stderr.write("Error: No transcript path provided\n")
            sys.exit(1)
        
        # Expand ~ to home directory
        transcript_path = os.path.expanduser(transcript_path)
        
        # Run the context preserver
        preserver = ContextPreserver(transcript_path)
        return preserver.run()
        
    except Exception as e:
        sys.stderr.write(f"Error in preserve-context hook: {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())