#!/usr/bin/env python3
"""Session start hook to reload Large Task Mode context"""

import json
import sys
from pathlib import Path

def load_large_task_context():
    """Load context if Large Task Mode is active"""
    mode_file = Path('.claude/LARGE_TASK_MODE.json')
    
    if not mode_file.exists():
        return None
    
    try:
        mode_data = json.loads(mode_file.read_text())
    except json.JSONDecodeError:
        return None
    
    if mode_data.get('status') not in ['active', 'ready']:
        return None
    
    # Build context to reload
    context_parts = []
    
    # Add mode status
    context_parts.append(f"[LARGE TASK MODE] Status: {mode_data.get('status')}")
    if mode_data.get('status') == 'active':
        context_parts.append(f"Task: {mode_data.get('original_prompt', 'No description')}")
    
    # Load project context
    if Path('.claude/PROJECT_CONTEXT.md').exists():
        context_parts.append("\n" + Path('.claude/PROJECT_CONTEXT.md').read_text())
    
    # Load boundaries
    if Path('.claude/BOUNDARIES.json').exists():
        boundaries = json.loads(Path('.claude/BOUNDARIES.json').read_text())
        if boundaries:
            context_parts.append("\nWork boundaries are defined. Common code must go in /common/")
    
    # Load active work
    if Path('.claude/ACTIVE_WORK.json').exists():
        active = json.loads(Path('.claude/ACTIVE_WORK.json').read_text())
        if active:
            context_parts.append(f"\nActive work in progress: {list(active.keys())}")
    
    # Check for recent validation failures
    if Path('.claude/VALIDATION_REPORT.json').exists():
        try:
            report = json.loads(Path('.claude/VALIDATION_REPORT.json').read_text())
            if report.get('status') == 'failed':
                context_parts.append("\n⚠️ Previous validation failed. Run validator-master to check status.")
        except json.JSONDecodeError:
            # Invalid report, skip
            report = {}
    
    return "\n".join(context_parts)

def handle_session_start():
    """Main function for session start hook"""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    # Load Large Task context if active
    context = load_large_task_context()
    
    if context:
        # Return context to be added to session
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context + "\n\nContinue with Large Task workflow. Check PROJECT_CONTEXT.md for details."
            }
        }
        json.dump(output, sys.stdout)
    
    sys.exit(0)

if __name__ == "__main__":
    handle_session_start()