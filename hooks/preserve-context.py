#!/usr/bin/env python3
"""
Enhanced Context Preservation Hook for Claude Code
Captures critical context that may not be fully preserved in normal compact:
- Current working directory and project structure
- Active files being worked on
- Failed attempts and error patterns
- Working solutions and successful approaches
- Key architectural decisions
- Unresolved issues and TODOs
- Dependencies and imports discovered
- Test results and coverage metrics
- Commands and scripts used
- Configuration changes made
"""

import json
import sys
import re
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class EnhancedContextPreserver:
    def __init__(self, transcript_path: str):
        self.transcript_path = transcript_path
        self.transcript = []
        
        # Core context tracking
        self.failed_attempts = []  # What didn't work
        self.working_solutions = []  # What DID work
        self.key_decisions = []  # Architectural choices made
        self.unresolved_issues = []  # Problems not yet fixed
        self.current_objective = ""  # Current goal being worked on
        
        # Enhanced context tracking
        self.active_files = set()  # Files being modified
        self.commands_used = []  # Important commands run
        self.test_results = []  # Test outcomes
        self.dependencies = set()  # Dependencies/imports found
        self.config_changes = []  # Configuration modifications
        self.working_directory = ""  # Current working directory
        self.error_patterns = defaultdict(int)  # Common error types
        self.file_operations = []  # Recent file operations
        self.important_paths = set()  # Key directories/files mentioned
        self.api_endpoints = set()  # APIs or services mentioned
        self.database_operations = []  # DB queries/operations
        self.performance_notes = []  # Performance considerations
        self.security_notes = []  # Security considerations
        
    def load_transcript(self):
        """Load the transcript file"""
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
            return  # No transcript yet
    
    def analyze_comprehensive_context(self):
        """Extract comprehensive context from transcript"""
        
        # Original tracking
        self.track_failed_attempts()
        self.track_working_solutions()
        self.track_key_decisions()
        self.track_unresolved_issues()
        self.extract_current_objective()
        
        # Enhanced tracking
        self.track_active_files()
        self.track_commands()
        self.track_test_results()
        self.track_dependencies()
        self.track_config_changes()
        self.track_working_directory()
        self.track_error_patterns()
        self.track_file_operations()
        self.track_important_paths()
        self.track_api_endpoints()
        self.track_database_operations()
        self.track_performance_and_security()
    
    def track_failed_attempts(self):
        """Track what approaches failed with more detail"""
        for i, entry in enumerate(self.transcript):
            if entry.get("type") == "tool_result":
                content = str(entry.get("content", ""))
                
                # Extended error patterns
                error_patterns = [
                    (r"(?i)error[:\s]", "error"),
                    (r"(?i)failed[:\s]", "failure"),
                    (r"(?i)exception[:\s]", "exception"),
                    (r"(?i)traceback", "traceback"),
                    (r"(?i)assertion.*failed", "assertion"),
                    (r"(?i)cannot\s+", "cannot"),
                    (r"(?i)unable\s+to", "unable"),
                    (r"(?i)permission\s+denied", "permission"),
                    (r"(?i)not\s+found", "not_found"),
                    (r"(?i)invalid\s+", "invalid"),
                    (r"(?i)timeout", "timeout"),
                    (r"(?i)connection\s+refused", "connection"),
                    (r"(?i)module.*not.*found", "import_error"),
                    (r"(?i)syntax\s+error", "syntax_error"),
                    (r"(?i)type\s+error", "type_error"),
                ]
                
                for pattern, error_type in error_patterns:
                    if re.search(pattern, content):
                        self.error_patterns[error_type] += 1
                        
                        # Get the preceding action that failed
                        if i > 0 and self.transcript[i-1].get("type") == "tool_use":
                            tool_name = self.transcript[i-1].get("name", "")
                            tool_input = self.transcript[i-1].get("input", {})
                            
                            # Extract detailed failure information
                            failure_info = {
                                "tool": tool_name,
                                "error_type": error_type,
                                "error": self._extract_error_message(content),
                                "context": self._get_failure_context(tool_input, tool_name),
                                "timestamp": entry.get("timestamp", "")
                            }
                            
                            # Avoid duplicates based on context
                            if not any(f["context"] == failure_info["context"] for f in self.failed_attempts):
                                self.failed_attempts.append(failure_info)
                        break
    
    def track_working_solutions(self):
        """Track successful approaches after failures with more context"""
        had_error = False
        error_context = ""
        error_type = ""
        
        for i, entry in enumerate(self.transcript):
            if entry.get("type") == "tool_result":
                content = str(entry.get("content", ""))
                
                # Check if this is an error
                if any(pattern in content.lower() for pattern in ["error", "failed", "exception"]):
                    had_error = True
                    error_context = self._extract_error_message(content)
                    # Identify error type
                    for pattern in ["syntax", "type", "import", "permission", "not found"]:
                        if pattern in content.lower():
                            error_type = pattern
                            break
                
                # Check if this is a success after an error
                elif had_error and any(word in content.lower() for word in ["success", "completed", "passed", "fixed", "works"]):
                    if i > 0 and self.transcript[i-1].get("type") == "tool_use":
                        tool_name = self.transcript[i-1].get("name", "")
                        tool_input = self.transcript[i-1].get("input", {})
                        
                        solution_info = {
                            "fixed_error": error_context,
                            "error_type": error_type,
                            "solution": f"Used {tool_name} with {self._get_solution_summary(tool_input, tool_name)}",
                            "details": self._extract_solution_details(tool_input, tool_name)
                        }
                        
                        if solution_info not in self.working_solutions:
                            self.working_solutions.append(solution_info)
                    
                    had_error = False
                    error_context = ""
                    error_type = ""
    
    def track_active_files(self):
        """Track files being actively worked on"""
        for entry in self.transcript:
            if entry.get("type") == "tool_use":
                tool_name = entry.get("name", "")
                tool_input = entry.get("input", {})
                
                if tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
                    file_path = tool_input.get("file_path", "")
                    if file_path:
                        self.active_files.add(file_path)
                        # Track directory too
                        dir_path = os.path.dirname(file_path)
                        if dir_path:
                            self.important_paths.add(dir_path)
    
    def track_commands(self):
        """Track important commands executed"""
        for entry in self.transcript:
            if entry.get("type") == "tool_use" and entry.get("name") == "Bash":
                command = entry.get("input", {}).get("command", "")
                if command:
                    # Filter out trivial commands
                    if not any(trivial in command for trivial in ["ls", "pwd", "cd", "echo", "cat"]):
                        # Extract command type
                        cmd_info = {
                            "command": command[:200],
                            "type": self._classify_command(command)
                        }
                        if cmd_info not in self.commands_used:
                            self.commands_used.append(cmd_info)
    
    def track_test_results(self):
        """Track test execution results"""
        for i, entry in enumerate(self.transcript):
            if entry.get("type") == "tool_result":
                content = str(entry.get("content", ""))
                
                # Look for test patterns
                test_patterns = [
                    (r"(\d+)\s+passed", "passed"),
                    (r"(\d+)\s+failed", "failed"),
                    (r"(\d+)\s+skipped", "skipped"),
                    (r"coverage[:\s]+(\d+)%", "coverage"),
                    (r"(\d+)\s+errors?", "errors"),
                    (r"All tests passed", "all_passed"),
                ]
                
                for pattern, test_type in test_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        # Get the command that ran the test
                        test_command = ""
                        if i > 0 and self.transcript[i-1].get("type") == "tool_use":
                            if self.transcript[i-1].get("name") == "Bash":
                                test_command = self.transcript[i-1].get("input", {}).get("command", "")
                        
                        test_info = {
                            "type": test_type,
                            "value": match.group(1) if match.groups() else "true",
                            "command": test_command[:100] if test_command else ""
                        }
                        
                        if test_info not in self.test_results:
                            self.test_results.append(test_info)
    
    def track_dependencies(self):
        """Track imports and dependencies discovered"""
        for entry in self.transcript:
            if entry.get("type") in ["tool_use", "tool_result", "text"]:
                content = str(entry.get("content", "") if entry.get("type") == "text" else 
                          entry.get("input", {}) if entry.get("type") == "tool_use" else 
                          entry.get("content", ""))
                
                # Look for import patterns
                import_patterns = [
                    r"import\s+(\w+)",
                    r"from\s+(\w+)",
                    r"require\(['\"]([^'\"]+)",
                    r"include\s+['\"]([^'\"]+)",
                    r"using\s+(\w+)",
                ]
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if match and not match.startswith("."):
                            self.dependencies.add(match)
    
    def track_config_changes(self):
        """Track configuration file modifications"""
        for entry in self.transcript:
            if entry.get("type") == "tool_use":
                tool_name = entry.get("name", "")
                tool_input = entry.get("input", {})
                
                if tool_name in ["Write", "Edit", "MultiEdit"]:
                    file_path = tool_input.get("file_path", "")
                    if file_path and any(config in file_path for config in 
                                        [".json", ".yaml", ".yml", ".toml", ".ini", ".env", 
                                         "config", "settings", "setup"]):
                        config_info = {
                            "file": file_path,
                            "operation": tool_name,
                            "summary": self._extract_config_change(tool_input)
                        }
                        if config_info not in self.config_changes:
                            self.config_changes.append(config_info)
    
    def track_working_directory(self):
        """Track the current working directory"""
        for entry in reversed(self.transcript):
            if entry.get("type") == "tool_result":
                content = str(entry.get("content", ""))
                # Look for pwd output or directory indicators
                if "/home/" in content or "/Users/" in content or "C:\\" in content:
                    # Extract path
                    path_match = re.search(r"(/[^\s]+|[A-Z]:\\[^\s]+)", content)
                    if path_match:
                        potential_wd = path_match.group(1)
                        if os.path.exists(potential_wd) and os.path.isdir(potential_wd):
                            self.working_directory = potential_wd
                            break
    
    def track_error_patterns(self):
        """Already tracked in track_failed_attempts"""
        pass
    
    def track_file_operations(self):
        """Track recent file operations for context"""
        for entry in self.transcript[-20:]:  # Last 20 operations
            if entry.get("type") == "tool_use":
                tool_name = entry.get("name", "")
                tool_input = entry.get("input", {})
                
                if tool_name in ["Read", "Write", "Edit", "MultiEdit", "Glob", "Grep"]:
                    op_info = {
                        "operation": tool_name,
                        "target": tool_input.get("file_path", tool_input.get("path", tool_input.get("pattern", "")))
                    }
                    if op_info["target"]:
                        self.file_operations.append(op_info)
    
    def track_important_paths(self):
        """Track important directories and files mentioned"""
        for entry in self.transcript:
            if entry.get("type") in ["text", "tool_result"]:
                content = str(entry.get("content", ""))
                
                # Look for path patterns
                path_patterns = [
                    r"(/[a-zA-Z0-9_\-/]+\.[a-zA-Z]+)",  # Unix paths with extensions
                    r"([a-zA-Z0-9_\-/]+/[a-zA-Z0-9_\-]+/)",  # Directory paths
                    r"(src/[a-zA-Z0-9_\-/]+)",  # Source paths
                    r"(tests?/[a-zA-Z0-9_\-/]+)",  # Test paths
                ]
                
                for pattern in path_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if len(match) > 5:  # Skip trivial paths
                            self.important_paths.add(match)
    
    def track_api_endpoints(self):
        """Track API endpoints and services mentioned"""
        for entry in self.transcript:
            content = str(entry.get("content", "") if entry.get("type") in ["text", "tool_result"] else "")
            
            # Look for API patterns
            api_patterns = [
                r"(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)",
                r"endpoint[:\s]+([/\w\-{}]+)",
                r"api[/:]([/\w\-{}]+)",
                r"route\(['\"]([/\w\-{}]+)",
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    endpoint = match[1] if isinstance(match, tuple) else match
                    if endpoint and len(endpoint) > 3:
                        self.api_endpoints.add(endpoint)
    
    def track_database_operations(self):
        """Track database queries and operations"""
        for entry in self.transcript:
            content = str(entry.get("content", "") if entry.get("type") in ["text", "tool_result"] else 
                        entry.get("input", {}) if entry.get("type") == "tool_use" else "")
            
            # Look for DB patterns
            db_patterns = [
                r"(SELECT|INSERT|UPDATE|DELETE|CREATE TABLE).*?(?:FROM|INTO|SET|WHERE)",
                r"db\.\w+\.\w+\([^)]*\)",  # MongoDB style
                r"(find|create|update|delete)(?:One|Many|All)?\([^)]*\)",  # ORM style
            ]
            
            for pattern in db_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    db_op = match if isinstance(match, str) else match[0]
                    if db_op:
                        self.database_operations.append(db_op[:100])
    
    def track_performance_and_security(self):
        """Track performance and security considerations mentioned"""
        for entry in self.transcript:
            if entry.get("type") == "text":
                content = entry.get("content", "")
                
                # Performance patterns
                perf_patterns = [
                    r"(?i)(performance|optimization|slow|fast|cache|memory|cpu)[:]\s*([^.]+)",
                    r"(?i)(O\(\w+\))",  # Big O notation
                    r"(?i)(\d+ms|\d+s)\s+(latency|response|timeout)",
                ]
                
                for pattern in perf_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        note = match[1] if isinstance(match, tuple) and len(match) > 1 else str(match)
                        if len(note) > 10:
                            self.performance_notes.append(note[:100])
                
                # Security patterns
                sec_patterns = [
                    r"(?i)(security|vulnerability|auth|permission|sanitize|validate)[:]\s*([^.]+)",
                    r"(?i)(CVE-\d{4}-\d+)",
                    r"(?i)(XSS|CSRF|SQL.injection|injection)",
                ]
                
                for pattern in sec_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        note = match[1] if isinstance(match, tuple) and len(match) > 1 else str(match)
                        if len(note) > 10:
                            self.security_notes.append(note[:100])
    
    def track_key_decisions(self):
        """Track architectural and design decisions with more context"""
        for entry in self.transcript:
            if entry.get("type") == "text":
                content = entry.get("content", "")
                
                # Extended decision patterns
                decision_patterns = [
                    r"(?i)decided\s+to\s+([^.]+)",
                    r"(?i)going\s+with\s+([^.]+)",
                    r"(?i)choosing\s+([^.]+)",
                    r"(?i)will\s+use\s+([^.]+)",
                    r"(?i)approach[:]\s*([^.]+)",
                    r"(?i)solution[:]\s*([^.]+)",
                    r"(?i)architecture[:]\s*([^.]+)",
                    r"(?i)strategy[:]\s*([^.]+)",
                    r"(?i)pattern[:]\s*([^.]+)",
                    r"(?i)instead\s+of\s+([^,]+),\s*([^.]+)",
                ]
                
                for pattern in decision_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        decision = match if isinstance(match, str) else " instead of ".join(match)
                        if len(decision) > 20:  # Substantial decision
                            decision_text = decision.strip()[:200]
                            if decision_text not in self.key_decisions:
                                self.key_decisions.append(decision_text)
    
    def track_unresolved_issues(self):
        """Track issues that weren't resolved with more detail"""
        issues_mentioned = []
        issues_fixed = []
        
        for entry in self.transcript:
            if entry.get("type") in ["text", "tool_result"]:
                content = str(entry.get("content", ""))
                
                # Extended issue patterns
                issue_patterns = [
                    r"(?i)issue[:]\s*([^.]+)",
                    r"(?i)problem[:]\s*([^.]+)",
                    r"(?i)bug[:]\s*([^.]+)",
                    r"(?i)todo[:]\s*([^.]+)",
                    r"(?i)fixme[:]\s*([^.]+)",
                    r"(?i)hack[:]\s*([^.]+)",
                    r"(?i)warning[:]\s*([^.]+)",
                    r"(?i)needs?\s+(?:to\s+)?(?:be\s+)?([^.]+)",
                    r"(?i)broken[:]\s*([^.]+)",
                    r"(?i)failing[:]\s*([^.]+)",
                ]
                
                for pattern in issue_patterns:
                    matches = re.findall(pattern, content)
                    issues_mentioned.extend(matches)
                
                # Look for fixes
                fix_patterns = [
                    r"(?i)fixed\s+([^.]+)",
                    r"(?i)resolved\s+([^.]+)",
                    r"(?i)addressed\s+([^.]+)",
                    r"(?i)completed\s+([^.]+)",
                    r"(?i)solved\s+([^.]+)",
                    r"(?i)corrected\s+([^.]+)",
                ]
                
                for pattern in fix_patterns:
                    matches = re.findall(pattern, content)
                    issues_fixed.extend(matches)
        
        # Find unresolved issues
        for issue in issues_mentioned:
            if len(issue) > 20:  # Substantial issue
                # Check if it was fixed
                was_fixed = any(fix in issue or issue in fix for fix in issues_fixed)
                if not was_fixed:
                    issue_text = issue.strip()[:200]
                    if issue_text not in self.unresolved_issues:
                        self.unresolved_issues.append(issue_text)
    
    def extract_current_objective(self):
        """Extract what we're currently trying to accomplish"""
        # Look at recent user messages
        for entry in reversed(self.transcript[-10:]):
            if entry.get("type") == "text" and entry.get("role") == "user":
                self.current_objective = entry.get("content", "")[:300]
                break
    
    def _extract_error_message(self, content: str) -> str:
        """Extract the core error message from content"""
        # Try to find the actual error message
        patterns = [
            r"Error:\s*(.+?)(?:\n|$)",
            r"Exception:\s*(.+?)(?:\n|$)",
            r"Failed:\s*(.+?)(?:\n|$)",
            r"(\w+Error:\s*.+?)(?:\n|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)[:150]
        
        # Fallback to first line with error
        lines = content.split('\n')
        for line in lines:
            if 'error' in line.lower():
                return line[:150]
        
        return content[:150]
    
    def _get_failure_context(self, tool_input: dict, tool_name: str) -> str:
        """Extract relevant context from failed tool use"""
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            return tool_input.get("file_path", "unknown file")
        elif tool_name == "Bash":
            cmd = tool_input.get("command", "unknown command")
            # Extract the main command
            if " " in cmd:
                return cmd.split()[0] + "..." + cmd[-50:]
            return cmd[:100]
        elif tool_name == "Read":
            return tool_input.get("file_path", "unknown file")
        elif tool_name == "Grep":
            return f"pattern: {tool_input.get('pattern', '')[:50]}"
        elif tool_name == "Task":
            return f"agent: {tool_input.get('subagent_type', 'unknown')}"
        return "unknown context"
    
    def _get_solution_summary(self, tool_input: dict, tool_name: str) -> str:
        """Summarize successful solution"""
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            return f"modified {tool_input.get('file_path', 'file')}"
        elif tool_name == "Bash":
            return f"command: {tool_input.get('command', '')[:50]}"
        elif tool_name == "Task":
            return f"delegated to {tool_input.get('subagent_type', 'agent')}"
        return "approach"
    
    def _extract_solution_details(self, tool_input: dict, tool_name: str) -> str:
        """Extract detailed solution information"""
        if tool_name == "Edit":
            old = tool_input.get("old_string", "")[:50]
            new = tool_input.get("new_string", "")[:50]
            return f"Changed '{old}' to '{new}'"
        elif tool_name == "Write":
            return f"Created/updated with {len(tool_input.get('content', ''))} chars"
        elif tool_name == "Bash":
            return tool_input.get("command", "")[:100]
        return ""
    
    def _classify_command(self, command: str) -> str:
        """Classify the type of command"""
        cmd_lower = command.lower()
        if any(test in cmd_lower for test in ["pytest", "test", "jest", "mocha"]):
            return "test"
        elif any(git in cmd_lower for git in ["git ", "gh "]):
            return "git"
        elif any(pkg in cmd_lower for pkg in ["npm", "pip", "yarn", "cargo"]):
            return "package"
        elif any(build in cmd_lower for build in ["make", "build", "compile"]):
            return "build"
        elif any(lint in cmd_lower for lint in ["lint", "format", "black", "prettier"]):
            return "lint"
        return "other"
    
    def _extract_config_change(self, tool_input: dict) -> str:
        """Extract what configuration was changed"""
        if "old_string" in tool_input and "new_string" in tool_input:
            return f"Modified configuration value"
        elif "content" in tool_input:
            return f"Updated configuration"
        return "Configuration change"
    
    def generate_context(self) -> str:
        """Generate comprehensive context summary"""
        context_parts = []
        
        # Working directory and current objective
        if self.working_directory:
            context_parts.append(f"WORKING DIRECTORY: {self.working_directory}\n")
        
        if self.current_objective:
            context_parts.append(f"CURRENT OBJECTIVE:\n{self.current_objective}\n")
        
        # Active files (most important for context)
        if self.active_files:
            context_parts.append("ACTIVE FILES BEING MODIFIED:")
            for file in list(self.active_files)[-10:]:  # Last 10 files
                context_parts.append(f"- {file}")
            context_parts.append("")
        
        # Recent file operations
        if self.file_operations:
            context_parts.append("RECENT FILE OPERATIONS:")
            for op in self.file_operations[-5:]:
                context_parts.append(f"- {op['operation']} on {op['target']}")
            context_parts.append("")
        
        # Failed attempts with error types
        if self.failed_attempts:
            context_parts.append("FAILED ATTEMPTS (avoid these):")
            # Group by error type
            by_type = defaultdict(list)
            for attempt in self.failed_attempts:
                by_type[attempt['error_type']].append(attempt)
            
            for error_type, attempts in list(by_type.items())[-5:]:
                context_parts.append(f"  {error_type.upper()} errors:")
                for attempt in attempts[-2:]:  # Show 2 per type
                    context_parts.append(f"    - {attempt['tool']} on {attempt['context']}: {attempt['error'][:80]}")
            context_parts.append("")
        
        # Working solutions
        if self.working_solutions:
            context_parts.append("WORKING SOLUTIONS (these worked):")
            for solution in self.working_solutions[-5:]:
                context_parts.append(f"- Fixed {solution['error_type'] or 'error'}: {solution['solution']}")
                if solution['details']:
                    context_parts.append(f"  Details: {solution['details']}")
            context_parts.append("")
        
        # Commands used
        if self.commands_used:
            context_parts.append("KEY COMMANDS USED:")
            # Group by type
            by_type = defaultdict(list)
            for cmd in self.commands_used:
                by_type[cmd['type']].append(cmd['command'])
            
            for cmd_type, commands in by_type.items():
                if commands:
                    context_parts.append(f"  {cmd_type}:")
                    for cmd in commands[-2:]:
                        context_parts.append(f"    - {cmd}")
            context_parts.append("")
        
        # Test results
        if self.test_results:
            context_parts.append("TEST RESULTS:")
            for result in self.test_results[-5:]:
                if result['type'] == 'coverage':
                    context_parts.append(f"- Coverage: {result['value']}%")
                elif result['type'] == 'all_passed':
                    context_parts.append(f"- All tests passed")
                else:
                    context_parts.append(f"- {result['value']} tests {result['type']}")
                if result['command']:
                    context_parts.append(f"  Command: {result['command']}")
            context_parts.append("")
        
        # Dependencies discovered
        if self.dependencies:
            context_parts.append("DEPENDENCIES/IMPORTS FOUND:")
            for dep in list(self.dependencies)[-10:]:
                context_parts.append(f"- {dep}")
            context_parts.append("")
        
        # Configuration changes
        if self.config_changes:
            context_parts.append("CONFIGURATION CHANGES:")
            for config in self.config_changes[-5:]:
                context_parts.append(f"- {config['operation']} on {config['file']}: {config['summary']}")
            context_parts.append("")
        
        # Key decisions
        if self.key_decisions:
            context_parts.append("KEY DECISIONS MADE:")
            for decision in self.key_decisions[-5:]:
                context_parts.append(f"- {decision}")
            context_parts.append("")
        
        # API endpoints
        if self.api_endpoints:
            context_parts.append("API ENDPOINTS:")
            for endpoint in list(self.api_endpoints)[-5:]:
                context_parts.append(f"- {endpoint}")
            context_parts.append("")
        
        # Database operations
        if self.database_operations:
            context_parts.append("DATABASE OPERATIONS:")
            for op in self.database_operations[-3:]:
                context_parts.append(f"- {op}")
            context_parts.append("")
        
        # Performance notes
        if self.performance_notes:
            context_parts.append("PERFORMANCE CONSIDERATIONS:")
            for note in self.performance_notes[-3:]:
                context_parts.append(f"- {note}")
            context_parts.append("")
        
        # Security notes
        if self.security_notes:
            context_parts.append("SECURITY CONSIDERATIONS:")
            for note in self.security_notes[-3:]:
                context_parts.append(f"- {note}")
            context_parts.append("")
        
        # Important paths
        if self.important_paths:
            relevant_paths = [p for p in self.important_paths if not any(skip in p for skip in ["node_modules", ".git", "__pycache__"])]
            if relevant_paths:
                context_parts.append("KEY PATHS/DIRECTORIES:")
                for path in list(relevant_paths)[-8:]:
                    context_parts.append(f"- {path}")
                context_parts.append("")
        
        # Unresolved issues
        if self.unresolved_issues:
            context_parts.append("UNRESOLVED ISSUES/TODOS:")
            for issue in self.unresolved_issues[-5:]:
                context_parts.append(f"- {issue}")
            context_parts.append("")
        
        # Error pattern summary
        if self.error_patterns:
            context_parts.append("ERROR PATTERN SUMMARY:")
            for error_type, count in sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                context_parts.append(f"- {error_type}: {count} occurrences")
            context_parts.append("")
        
        return "\n".join(context_parts)

def main():
    # Get transcript path from stdin
    try:
        input_data = json.loads(sys.stdin.read())
        transcript_path = input_data.get("transcript_path")
        
        if not transcript_path:
            # No transcript path provided
            print(json.dumps({"action": "continue"}))
            return
        
        # Create preserver and analyze
        preserver = EnhancedContextPreserver(transcript_path)
        preserver.load_transcript()
        preserver.analyze_comprehensive_context()
        
        # Generate context
        context = preserver.generate_context()
        
        if context:
            # Output the comprehensive context
            print(json.dumps({
                "action": "append",
                "content": f"\n--- ENHANCED CONTEXT (critical information for continuity) ---\n{context}\n--- END CONTEXT ---\n"
            }))
        else:
            print(json.dumps({"action": "continue"}))
            
    except Exception as e:
        # Log error but don't block
        sys.stderr.write(f"Context preservation error: {e}\n")
        print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()