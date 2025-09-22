#!/opt/envs/py3.13/bin/python
"""
Unified Bash Guardian Hook
=========================
Consolidates bash validation, learning, and safety features from:
- prism_bash_learner.py
- knowledge_validation.py
- knowledge_immune_system.py

Key Features:
- Blocks truly dangerous commands (rm -rf /, DROP DATABASE, etc.)
- Learns and suggests command workflows
- Tracks error-to-fix mappings
- RETRIEVES and USES stored patterns (fixes current gap)
- Works for both orchestration agents and solo development
- Provides visible value through helpful suggestions
- Universal learning integration for command patterns
"""

import json
import sys
import time
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import re

# Import PRISM client and universal learner
sys.path.append(str(Path(__file__).parent))
from prism_client import get_prism_client
from universal_learner import get_learner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
COMMAND_HISTORY_FILE = Path.home() / ".claude" / "bash_command_history.json"
ERROR_FIX_MAPPING_FILE = Path.home() / ".claude" / "error_fix_mappings.json"
MAX_HISTORY_SIZE = 100
WORKFLOW_CONFIDENCE_THRESHOLD = 0.7
PATTERN_RELEVANCE_THRESHOLD = 0.6

class UnifiedBashGuardian:
    """Unified bash command guardian with learning and safety features."""

    def __init__(self):
        self.client = get_prism_client()
        self.history = self.load_command_history()
        self.error_fix_mappings = self.load_error_fix_mappings()

    def load_command_history(self) -> List[Dict]:
        """Load recent command history from file."""
        try:
            if COMMAND_HISTORY_FILE.exists():
                with open(COMMAND_HISTORY_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load command history: {e}")
        return []

    def save_command_history(self):
        """Save command history to file."""
        try:
            COMMAND_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            trimmed_history = self.history[-MAX_HISTORY_SIZE:]
            with open(COMMAND_HISTORY_FILE, 'w') as f:
                json.dump(trimmed_history, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save command history: {e}")

    def load_error_fix_mappings(self) -> Dict[str, List[str]]:
        """Load known error-to-fix mappings."""
        try:
            if ERROR_FIX_MAPPING_FILE.exists():
                with open(ERROR_FIX_MAPPING_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert to defaultdict to handle missing keys
                    return defaultdict(list, data)
        except Exception as e:
            logger.debug(f"Failed to load error-fix mappings: {e}")
        return defaultdict(list)

    def save_error_fix_mappings(self):
        """Save error-fix mappings to file."""
        try:
            ERROR_FIX_MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(ERROR_FIX_MAPPING_FILE, 'w') as f:
                json.dump(dict(self.error_fix_mappings), f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save error-fix mappings: {e}")

    def analyze_command_danger(self, command: str, pwd: str) -> Tuple[str, str, str]:
        """
        Analyze command for potential dangers.
        Returns: (action, severity, reason)
        Actions: BLOCK, WARN, SUGGEST, ALLOW
        """
        command_lower = command.lower().strip()

        # BLOCK level - Critical dangers (never allow these)
        critical_patterns = [
            ('rm -rf /', 'BLOCK', 'CRITICAL', '🚨 Attempting to delete root filesystem - CATASTROPHIC'),
            ('rm -rf /*', 'BLOCK', 'CRITICAL', '🚨 Attempting to delete all root directories'),
            ('rm -rf ~$', 'BLOCK', 'CRITICAL', '🚨 Attempting to delete entire home directory'),
            ('rm -rf ~ ', 'BLOCK', 'CRITICAL', '🚨 Attempting to delete entire home directory'),
            ('rm -rf $HOME$', 'BLOCK', 'CRITICAL', '🚨 Attempting to delete home directory'),
            ('rm -rf $HOME ', 'BLOCK', 'CRITICAL', '🚨 Attempting to delete home directory'),
            ('dd if=/dev/zero of=/dev/', 'BLOCK', 'CRITICAL', '💀 Attempting to zero out device - DATA LOSS'),
            ('mkfs.', 'BLOCK', 'CRITICAL', '💀 Creating filesystem will DESTROY ALL DATA'),
            ('format c:', 'BLOCK', 'CRITICAL', '💀 Attempting to format drive'),
            ('DROP DATABASE', 'BLOCK', 'CRITICAL', '🗑️ Dropping database - PERMANENT DATA LOSS'),
            ('DROP TABLE', 'BLOCK', 'HIGH', '⚠️ Dropping table - data will be lost'),
            (':(){ :|:& };:', 'BLOCK', 'CRITICAL', '💣 Fork bomb detected - will crash system'),
            ('mv / /dev/null', 'BLOCK', 'CRITICAL', '💀 Attempting to move root to null device'),
            ('chmod -R 000 /', 'BLOCK', 'CRITICAL', '🔒 Removing all permissions from root'),
        ]

        for pattern, action, severity, reason in critical_patterns:
            if pattern in command_lower:
                return action, severity, reason

        # WARN level - Dangerous but sometimes necessary
        warning_patterns = [
            ('rm -rf', 'WARN', 'HIGH', '⚠️ Recursive forced delete - double-check target'),
            ('sudo rm', 'WARN', 'HIGH', '⚠️ Elevated delete permissions - verify target'),
            ('curl | bash', 'WARN', 'HIGH', '🔍 Executing remote script without inspection'),
            ('wget | sh', 'WARN', 'HIGH', '🔍 Executing remote script without inspection'),
            ('chmod 777', 'WARN', 'HIGH', '🔓 Setting dangerous permissions (world-writable)'),
            ('chmod -R', 'WARN', 'MEDIUM', '🔑 Changing permissions recursively'),
            ('chown -R', 'WARN', 'MEDIUM', '👤 Changing ownership recursively'),
            ('git push --force', 'WARN', 'MEDIUM', '⚠️ Force pushing - may overwrite remote'),
            ('git reset --hard', 'WARN', 'MEDIUM', '⚠️ Hard reset - uncommitted changes will be lost'),
            ('docker system prune -a', 'WARN', 'MEDIUM', '🐳 Will remove ALL unused Docker resources'),
            ('npm install -g', 'WARN', 'LOW', '📦 Global npm install - affects system'),
            ('pip install --user', 'WARN', 'LOW', '🐍 User-level Python package install'),
        ]

        for pattern, action, severity, reason in warning_patterns:
            if pattern in command_lower:
                return action, severity, reason

        # Check for patterns that might need suggestions
        if 'git clone' in command_lower:
            return 'SUGGEST', 'INFO', '💡 After cloning, you might want to: cd into the directory'
        elif 'npm init' in command_lower:
            return 'SUGGEST', 'INFO', '💡 Next steps: npm install dependencies'
        elif 'python -m venv' in command_lower or 'virtualenv' in command_lower:
            return 'SUGGEST', 'INFO', '💡 Don\'t forget to activate the virtual environment'

        return 'ALLOW', 'SAFE', 'Command appears safe'

    def retrieve_relevant_workflows(self, command: str) -> List[Dict]:
        """
        RETRIEVE stored workflows relevant to current command.
        This fixes the current gap where patterns are stored but not used.
        """
        if not self.client:
            return []

        relevant_workflows = []
        try:
            # Search for similar command patterns in LONGTERM memory
            # (using LONGTERM since EPISODIC had issues)
            search_query = command.split()[0] if command else ""

            results = self.client.search_memory(
                query=search_query,
                tier='LONGTERM',
                limit=5
            )

            for result in results:
                try:
                    content = json.loads(result.get('content', '{}'))
                    if content.get('type') == 'command_sequence':
                        # Check if this workflow is relevant
                        commands = content.get('commands', [])
                        if any(search_query in cmd for cmd in commands):
                            relevant_workflows.append({
                                'commands': commands,
                                'success_rate': content.get('success_rate', 0),
                                'score': result.get('score', 0)
                            })
                except:
                    continue

            # Sort by relevance score
            relevant_workflows.sort(key=lambda x: x['score'], reverse=True)

        except Exception as e:
            logger.debug(f"Failed to retrieve workflows: {e}")

        return relevant_workflows[:3]  # Return top 3 most relevant

    def suggest_next_commands(self, command: str, workflows: List[Dict]) -> Optional[str]:
        """Generate suggestions based on retrieved workflows."""
        if not workflows:
            return None

        suggestions = []
        for workflow in workflows:
            commands = workflow['commands']
            success_rate = workflow.get('success_rate', 0)

            # Find where current command appears in workflow
            for i, cmd in enumerate(commands[:-1]):
                if command.split()[0] in cmd:
                    next_cmd = commands[i + 1]
                    if success_rate > 0.8:
                        suggestions.append(f"• {next_cmd} (worked {int(success_rate*100)}% of the time)")

        if suggestions:
            return "💡 **Based on past workflows, common next steps:**\n" + "\n".join(suggestions[:3])
        return None

    def learn_error_fix_pattern(self, error_output: str, fix_command: str):
        """Learn which commands fix which errors."""
        if not error_output or not fix_command:
            return

        # Extract key error phrases
        error_patterns = []
        error_type = "unknown"
        if 'command not found' in error_output:
            error_patterns.append('command_not_found')
            error_type = "missing_command"
        if 'permission denied' in error_output.lower():
            error_patterns.append('permission_denied')
            error_type = "permission_error"
        if 'no such file or directory' in error_output.lower():
            error_patterns.append('file_not_found')
            error_type = "missing_file"
        if 'connection refused' in error_output.lower():
            error_patterns.append('connection_refused')
            error_type = "network_error"

        # Create rich semantic pattern
        from universal_learner import get_learner
        learner = get_learner()

        pattern = {
            "type": "command_error",
            "content": f"Error: '{error_output[:100]}...' can be fixed with command: '{fix_command}'",
            "error": error_output,
            "fix": fix_command,
            "error_type": error_type,
            "error_patterns": error_patterns,
            "confidence": 0.8,
            "relationships": [
                (error_output[:100], "FIXED_BY", fix_command)
            ]
        }

        learner.learn_pattern(pattern)

        # Store the fix for each error pattern
        for pattern in error_patterns:
            if fix_command not in self.error_fix_mappings[pattern]:
                self.error_fix_mappings[pattern].append(fix_command)
                # Keep only last 5 fixes per error type
                self.error_fix_mappings[pattern] = self.error_fix_mappings[pattern][-5:]

        self.save_error_fix_mappings()

        # Also store in PRISM for long-term learning
        if self.client and error_patterns:
            try:
                fix_data = {
                    'type': 'error_fix_mapping',
                    'error_patterns': error_patterns,
                    'fix_command': fix_command,
                    'timestamp': time.time()
                }

                self.client.store_memory(
                    content=json.dumps(fix_data),
                    tier='LONGTERM',
                    metadata={
                        'importance': 'medium',
                        'tags': ['error_fix', 'bash', 'learning']
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to store error-fix pattern: {e}")

    def suggest_error_fixes(self, error_output: str) -> Optional[str]:
        """Suggest fixes based on error patterns."""
        if not error_output:
            return None

        suggestions = []
        error_lower = error_output.lower()

        # Check known error patterns
        if 'command not found' in error_lower:
            fixes = self.error_fix_mappings.get('command_not_found', [])
            if fixes:
                suggestions.append("🔧 **Command not found fixes that worked before:**")
                suggestions.extend([f"  • {fix}" for fix in fixes[-3:]])

        if 'permission denied' in error_lower:
            fixes = self.error_fix_mappings.get('permission_denied', [])
            suggestions.append("🔐 **Permission denied - try:**")
            suggestions.append("  • Add 'sudo' to run with elevated permissions")
            suggestions.append("  • Check file ownership with 'ls -la'")
            if fixes:
                suggestions.extend([f"  • {fix}" for fix in fixes[-2:]])

        if suggestions:
            return "\n".join(suggestions)
        return None

    def store_workflow_pattern(self, command_data: Dict):
        """Store successful command workflows for future retrieval."""
        # Import learner here to avoid circular imports
        from universal_learner import get_learner
        learner = get_learner()

        # Store individual command if it succeeded
        if command_data.get('exit_code') == 0:
            pattern = {
                "type": "command_workflow",
                "content": f"Command '{command_data['command']}' succeeded in {command_data.get('pwd', 'unknown')}",
                "command": command_data['command'],
                "pwd": command_data.get('pwd', os.getcwd()),
                "duration": command_data.get('duration', 0),
                "confidence": 0.7
            }
            learner.learn_pattern(pattern)

        # Create workflow from recent history if we have multiple commands
        if len(self.history) >= 2:
            recent_commands = [h['command'] for h in self.history[-3:]]
            success_rate = sum(1 for h in self.history[-3:] if h.get('exit_code') == 0) / min(3, len(self.history))

            if success_rate > 0.5:  # Only store successful workflows
                workflow_pattern = {
                    'type': 'command_workflow',
                    'content': f"Workflow sequence: {' -> '.join(recent_commands)}",
                    'sequence': recent_commands,
                    'pwd': command_data.get('pwd', os.getcwd()),
                    'success_rate': success_rate,
                    'confidence': min(0.9, 0.5 + success_rate * 0.4),
                    'relationships': [
                        (recent_commands[i], "FOLLOWED_BY", recent_commands[i+1])
                        for i in range(len(recent_commands)-1)
                    ]
                }

                try:
                    learner.learn_pattern(workflow_pattern)
                    logger.debug(f"Stored workflow pattern: {recent_commands[0][:30]}...")
                except Exception as e:
                    logger.debug(f"Failed to store workflow: {e}")

    def process_pre_execution(self, input_data: Dict) -> Dict:
        """Process pre-execution hook for bash commands."""
        tool_input = input_data.get("tool_input", {})
        command = tool_input.get("command", "")
        pwd = os.getcwd()

        if not command:
            return {"intervention": None}

        # Analyze command danger level
        action, severity, reason = self.analyze_command_danger(command, pwd)

        # Prepare intervention response
        intervention = None

        if action == "BLOCK":
            # Block truly dangerous commands
            intervention = {
                "type": "block_execution",
                "severity": severity,
                "message": f"# ⛔ BLOCKED: Command Too Dangerous\n\n{reason}\n\n**Command:** `{command}`\n\n**Alternative:** Please use a safer approach or be more specific with your target."
            }

            # Store as dangerous pattern
            if self.client:
                try:
                    danger_data = {
                        'type': 'blocked_dangerous_command',
                        'command': command,
                        'severity': severity,
                        'reason': reason,
                        'timestamp': time.time()
                    }
                    self.client.store_memory(
                        content=json.dumps(danger_data),
                        tier='ANCHORS',  # Immutable dangerous patterns
                        metadata={
                            'importance': 'critical',
                            'tags': ['danger', 'blocked', severity.lower()]
                        }
                    )
                except:
                    pass

        elif action == "WARN":
            # Warn but allow execution
            # Also retrieve relevant workflows to help
            workflows = self.retrieve_relevant_workflows(command)
            workflow_suggestions = self.suggest_next_commands(command, workflows)

            warning_message = f"# ⚠️ WARNING: Potentially Dangerous Command\n\n{reason}\n\n**Command:** `{command}`"

            if workflow_suggestions:
                warning_message += f"\n\n{workflow_suggestions}"

            warning_message += "\n\n**Proceeding with caution...**"

            intervention = {
                "type": "warning",
                "severity": severity,
                "message": warning_message
            }

        elif action == "SUGGEST":
            # Provide helpful suggestions
            workflows = self.retrieve_relevant_workflows(command)
            workflow_suggestions = self.suggest_next_commands(command, workflows)

            if workflow_suggestions or reason != 'Command appears safe':
                suggestion_message = f"# 💡 Suggestion\n\n{reason}"

                if workflow_suggestions:
                    suggestion_message += f"\n\n{workflow_suggestions}"

                intervention = {
                    "type": "suggestion",
                    "severity": "INFO",
                    "message": suggestion_message
                }

        # Return intervention if any
        if intervention:
            return {"intervention": intervention}

        return {"intervention": None}

    def process_post_execution(self, input_data: Dict) -> Dict:
        """Process post-execution hook for learning."""
        tool_input = input_data.get("tool_input", {})
        tool_response = input_data.get("tool_response", {})

        command = tool_input.get("command", "")
        output = tool_response.get("output", "")
        exit_code = tool_response.get("exit_code", 0)

        if not command:
            return {"intervention": None}

        # Track command in history
        command_data = {
            'command': command,
            'pwd': os.getcwd(),
            'exit_code': exit_code,
            'success': exit_code == 0,
            'timestamp': time.time(),
            'output_preview': output[:200] if output else ""
        }

        self.history.append(command_data)
        self.save_command_history()

        # Learn using universal learner
        learner = get_learner()

        # Calculate execution duration if possible
        duration = None
        if len(self.history) > 1 and self.history[-2].get('timestamp'):
            duration = command_data['timestamp'] - self.history[-2]['timestamp']

        # Get recent context (last few commands for context)
        context = {
            'pwd': os.getcwd(),
            'recent_commands': [h['command'] for h in self.history[-3:]]
        }

        # Learn the command pattern
        learner.learn_command_pattern(
            command=command,
            exit_code=exit_code,
            error=output if exit_code != 0 else None,
            duration=duration,
            context=context
        )

        # Learn from execution
        if exit_code == 0:
            # Successful command - store workflow pattern
            self.store_workflow_pattern(command_data)

            # Check if this fixed a previous error
            if len(self.history) >= 2:
                prev = self.history[-2]
                if prev.get('exit_code', 0) != 0 and prev.get('output_preview'):
                    # This command fixed an error
                    self.learn_error_fix_pattern(prev['output_preview'], command)

        else:
            # Command failed - suggest fixes if available
            error_fixes = self.suggest_error_fixes(output)

            if error_fixes:
                return {
                    "intervention": {
                        "type": "suggestion",
                        "severity": "INFO",
                        "message": f"# 🔧 Error Fix Suggestions\n\n{error_fixes}"
                    }
                }

        return {"intervention": None}

def main():
    """Main hook execution."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON input")
        sys.exit(1)

    # Only process Bash tool events
    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    event_type = input_data.get("hook_event_name", "")

    # Initialize guardian
    guardian = UnifiedBashGuardian()

    # Process based on event type
    result = {"intervention": None}

    if event_type == "PreToolUse":
        result = guardian.process_pre_execution(input_data)
    elif event_type == "PostToolUse":
        result = guardian.process_post_execution(input_data)

    # Output result
    print(json.dumps(result))

if __name__ == "__main__":
    main()