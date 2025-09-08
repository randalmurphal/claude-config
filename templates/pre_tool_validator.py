#!/usr/bin/env python3
"""Validates tool usage before execution in Large Task Mode"""

import json
import sys
from pathlib import Path

# Import base validator functions
sys.path.insert(0, str(Path(__file__).parent))
from base_validator import is_large_task_mode, load_boundaries

def main():
    # Exit silently if not in Large Task Mode
    if not is_large_task_mode():
        sys.exit(0)
    
    # Read hook input
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    tool_name = input_data.get('tool_name')
    tool_input = input_data.get('tool_input', {})
    
    # Validate based on tool type
    if tool_name in ['Write', 'Edit', 'MultiEdit']:
        file_path = tool_input.get('file_path', '')
        
        # Check if creating common code outside /common/
        if any(pattern in file_path.lower() for pattern in ['util', 'helper', 'common', 'shared', 'type', 'interface']):
            if not file_path.startswith('/common/') and not file_path.startswith('./common/'):
                # Check if architecture has been defined
                if not Path('.claude/ARCHITECTURE.md').exists():
                    output = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": "Architecture must be defined first. Run architecture-planner agent."
                        }
                    }
                    json.dump(output, sys.stdout)
                    sys.exit(0)
                else:
                    output = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": "Common code must be in /common/ directory only. This prevents duplication."
                        }
                    }
                    json.dump(output, sys.stdout)
                    sys.exit(0)
        
        # Check work boundaries
        boundaries = load_boundaries()
        if boundaries:
            # Check if file is in a locked zone
            for zone_name, zone_data in boundaries.items():
                if zone_data.get('locked'):
                    for path in zone_data.get('paths', []):
                        if file_path.startswith(path):
                            # Check if this agent is allowed
                            session_id = input_data.get('session_id', '')
                            if zone_data.get('owner') != session_id and zone_data.get('owner') != 'unassigned':
                                output = {
                                    "hookSpecificOutput": {
                                        "hookEventName": "PreToolUse",
                                        "permissionDecision": "deny",
                                        "permissionDecisionReason": f"This path is locked to {zone_data.get('owner')}. Cannot modify."
                                    }
                                }
                                json.dump(output, sys.stdout)
                                sys.exit(0)
    
    elif tool_name == 'Task':
        # Track subagent work
        subagent = tool_input.get('subagent_type', '')
        prompt = tool_input.get('prompt', '')
        
        # Register subagent work
        active_work_file = Path('.claude/ACTIVE_WORK.json')
        if active_work_file.exists():
            try:
                work_data = json.loads(active_work_file.read_text())
            except json.JSONDecodeError:
                work_data = {}
        else:
            work_data = {}
        
        work_data[subagent] = {
            "prompt": prompt,
            "timestamp": input_data.get('session_id'),
            "status": "working"
        }
        
        active_work_file.parent.mkdir(exist_ok=True)
        active_work_file.write_text(json.dumps(work_data, indent=2))
    
    # Allow by default
    sys.exit(0)

if __name__ == "__main__":
    main()