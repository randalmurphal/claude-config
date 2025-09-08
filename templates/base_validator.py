#!/usr/bin/env python3
"""Base validator for Large Task Mode - checks if mode is active before running"""

import json
import sys
import os
from pathlib import Path

def is_large_task_mode():
    """Check if Large Task Mode is active for current project"""
    mode_file = Path('.claude/LARGE_TASK_MODE.json')
    
    if not mode_file.exists():
        return False
    
    try:
        mode_data = json.loads(mode_file.read_text())
        
        # Verify this is the correct project
        if 'project_path' in mode_data:
            if mode_data['project_path'] != os.getcwd():
                return False
        
        return mode_data.get('status') in ['active', 'ready']
    except (json.JSONDecodeError, KeyError):
        return False

def load_boundaries():
    """Load work boundaries for current project"""
    boundaries_file = Path('.claude/BOUNDARIES.json')
    
    if not boundaries_file.exists():
        return {}
    
    try:
        return json.loads(boundaries_file.read_text())
    except json.JSONDecodeError:
        return {}

def load_project_context():
    """Load project context"""
    context_file = Path('.claude/PROJECT_CONTEXT.md')
    
    if not context_file.exists():
        return ""
    
    return context_file.read_text()

def update_validation_log(entry):
    """Add entry to validation log"""
    log_file = Path('.claude/VALIDATION_HISTORY.json')
    
    if log_file.exists():
        try:
            history = json.loads(log_file.read_text())
        except json.JSONDecodeError:
            history = []
    else:
        history = []
    
    history.append(entry)
    log_file.write_text(json.dumps(history, indent=2))

if __name__ == "__main__":
    # Exit silently if not in Large Task Mode
    if not is_large_task_mode():
        sys.exit(0)
    
    # Template file - actual validators will implement logic here
    sys.exit(0)