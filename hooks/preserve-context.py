#!/usr/bin/env python3
"""
Simplified Context Preservation Hook for Claude Code
Tracks only what's NOT preserved in normal Claude compact:
- Failed attempts (what didn't work)
- Working solutions (what DID work)  
- Key architectural decisions
- Unresolved issues
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Set
import os

class SimplifiedContextPreserver:
    def __init__(self, transcript_path: str):
        self.transcript_path = transcript_path
        self.transcript = []
        self.failed_attempts = []  # What didn't work
        self.working_solutions = []  # What DID work
        self.key_decisions = []  # Architectural choices made
        self.unresolved_issues = []  # Problems not yet fixed
        self.current_objective = ""  # Current goal being worked on
        
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
    
    def analyze_unique_context(self):
        """Extract context that Claude's compact doesn't preserve"""
        
        # Track failed attempts (errors that were encountered)
        self.track_failed_attempts()
        
        # Track working solutions
        self.track_working_solutions()
        
        # Track key decisions
        self.track_key_decisions()
        
        # Track unresolved issues
        self.track_unresolved_issues()
        
        # Extract current objective
        self.extract_current_objective()
    
    def track_failed_attempts(self):
        """Track what approaches failed"""
        for i, entry in enumerate(self.transcript):
            if entry.get("type") == "tool_result":
                content = str(entry.get("content", ""))
                
                # Look for error patterns
                error_patterns = [
                    r"(?i)error[:\s]",
                    r"(?i)failed[:\s]",
                    r"(?i)exception[:\s]",
                    r"(?i)traceback",
                    r"(?i)assertion.*failed",
                    r"(?i)cannot\s+",
                    r"(?i)unable\s+to",
                    r"(?i)permission\s+denied",
                    r"(?i)not\s+found",
                    r"(?i)invalid\s+",
                ]
                
                for pattern in error_patterns:
                    if re.search(pattern, content):
                        # Get the preceding action that failed
                        if i > 0 and self.transcript[i-1].get("type") == "tool_use":
                            tool_name = self.transcript[i-1].get("name", "")
                            tool_input = self.transcript[i-1].get("input", {})
                            
                            # Extract key information about what failed
                            failure_info = {
                                "tool": tool_name,
                                "error": content[:200],  # First 200 chars of error
                                "context": self._get_failure_context(tool_input, tool_name)
                            }
                            
                            # Avoid duplicates
                            if failure_info not in self.failed_attempts:
                                self.failed_attempts.append(failure_info)
                        break
    
    def track_working_solutions(self):
        """Track successful approaches after failures"""
        had_error = False
        error_context = ""
        
        for i, entry in enumerate(self.transcript):
            if entry.get("type") == "tool_result":
                content = str(entry.get("content", ""))
                
                # Check if this is an error
                if any(pattern in content.lower() for pattern in ["error", "failed", "exception"]):
                    had_error = True
                    error_context = content[:100]
                
                # Check if this is a success after an error
                elif had_error and "success" in content.lower() or "completed" in content.lower():
                    if i > 0 and self.transcript[i-1].get("type") == "tool_use":
                        tool_name = self.transcript[i-1].get("name", "")
                        tool_input = self.transcript[i-1].get("input", {})
                        
                        solution_info = {
                            "fixed_error": error_context,
                            "solution": f"Used {tool_name} with {self._get_solution_summary(tool_input, tool_name)}"
                        }
                        
                        if solution_info not in self.working_solutions:
                            self.working_solutions.append(solution_info)
                    
                    had_error = False
                    error_context = ""
    
    def track_key_decisions(self):
        """Track architectural and design decisions"""
        for entry in self.transcript:
            if entry.get("type") == "text":
                content = entry.get("content", "")
                
                # Look for decision patterns
                decision_patterns = [
                    r"(?i)decided\s+to\s+([^.]+)",
                    r"(?i)going\s+with\s+([^.]+)",
                    r"(?i)choosing\s+([^.]+)",
                    r"(?i)will\s+use\s+([^.]+)",
                    r"(?i)approach[:]\s*([^.]+)",
                    r"(?i)solution[:]\s*([^.]+)",
                    r"(?i)architecture[:]\s*([^.]+)",
                ]
                
                for pattern in decision_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if len(match) > 20:  # Substantial decision
                            decision = match.strip()[:150]  # Limit length
                            if decision not in self.key_decisions:
                                self.key_decisions.append(decision)
    
    def track_unresolved_issues(self):
        """Track issues that weren't resolved"""
        issues_mentioned = []
        issues_fixed = []
        
        for entry in self.transcript:
            if entry.get("type") == "text":
                content = entry.get("content", "")
                
                # Look for issue mentions
                issue_patterns = [
                    r"(?i)issue[:]\s*([^.]+)",
                    r"(?i)problem[:]\s*([^.]+)",
                    r"(?i)bug[:]\s*([^.]+)",
                    r"(?i)todo[:]\s*([^.]+)",
                    r"(?i)fixme[:]\s*([^.]+)",
                    r"(?i)needs?\s+(?:to\s+)?(?:be\s+)?([^.]+)",
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
                    issue_text = issue.strip()[:150]
                    if issue_text not in self.unresolved_issues:
                        self.unresolved_issues.append(issue_text)
    
    def extract_current_objective(self):
        """Extract what we're currently trying to accomplish"""
        # Look at recent user messages
        for entry in reversed(self.transcript[-10:]):
            if entry.get("type") == "text" and entry.get("role") == "user":
                self.current_objective = entry.get("content", "")[:200]
                break
    
    def _get_failure_context(self, tool_input: dict, tool_name: str) -> str:
        """Extract relevant context from failed tool use"""
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            return tool_input.get("file_path", "unknown file")
        elif tool_name == "Bash":
            return tool_input.get("command", "unknown command")[:100]
        elif tool_name == "Read":
            return tool_input.get("file_path", "unknown file")
        return "unknown context"
    
    def _get_solution_summary(self, tool_input: dict, tool_name: str) -> str:
        """Summarize successful solution"""
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            return f"modified {tool_input.get('file_path', 'file')}"
        elif tool_name == "Bash":
            return f"command: {tool_input.get('command', '')[:50]}"
        return "approach"
    
    def generate_context(self) -> str:
        """Generate the unique context summary"""
        context_parts = []
        
        # Current objective
        if self.current_objective:
            context_parts.append(f"CURRENT OBJECTIVE:\n{self.current_objective}\n")
        
        # Failed attempts (limit to 5 most recent)
        if self.failed_attempts:
            context_parts.append("FAILED ATTEMPTS (avoid these):")
            for attempt in self.failed_attempts[-5:]:
                context_parts.append(f"- {attempt['tool']} on {attempt['context']}: {attempt['error'][:100]}")
            context_parts.append("")
        
        # Working solutions (limit to 5)
        if self.working_solutions:
            context_parts.append("WORKING SOLUTIONS (these worked):")
            for solution in self.working_solutions[-5:]:
                context_parts.append(f"- Fixed: {solution['fixed_error'][:50]} → {solution['solution']}")
            context_parts.append("")
        
        # Key decisions (limit to 5)
        if self.key_decisions:
            context_parts.append("KEY DECISIONS MADE:")
            for decision in self.key_decisions[-5:]:
                context_parts.append(f"- {decision}")
            context_parts.append("")
        
        # Unresolved issues (limit to 5)
        if self.unresolved_issues:
            context_parts.append("UNRESOLVED ISSUES:")
            for issue in self.unresolved_issues[-5:]:
                context_parts.append(f"- {issue}")
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
        preserver = SimplifiedContextPreserver(transcript_path)
        preserver.load_transcript()
        preserver.analyze_unique_context()
        
        # Generate context
        context = preserver.generate_context()
        
        if context:
            # Output the unique context
            print(json.dumps({
                "action": "append",
                "content": f"\n--- UNIQUE CONTEXT (not in normal compact) ---\n{context}\n---\n"
            }))
        else:
            print(json.dumps({"action": "continue"}))
            
    except Exception as e:
        # Log error but don't block
        sys.stderr.write(f"Context preservation error: {e}\n")
        print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()