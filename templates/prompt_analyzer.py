#!/usr/bin/env python3
"""Analyzes user prompts to detect complex tasks that need Large Task Mode"""

import json
import sys
from pathlib import Path
from datetime import datetime

def analyze_task_complexity(prompt):
    """Determine if task needs large task workflow"""
    
    # First check if this is a research/discussion task (should NOT trigger)
    research_indicators = [
        'explain', 'what is', 'how does', 'why does', 'tell me about',
        'research', 'investigate', 'analyze', 'review', 'understand',
        'documentation', 'help me understand', 'can you explain',
        'what are', 'describe', 'summary', 'summarize', 'list'
    ]
    
    prompt_lower = prompt.lower()
    
    # Don't trigger for research/discussion
    for indicator in research_indicators:
        if indicator in prompt_lower and not any(code_word in prompt_lower for code_word in ['implement', 'build', 'create', 'code', 'develop']):
            return False
    
    # Check for explicit coding indicators
    complexity_indicators = {
        'high': [
            'implement', 'create', 'build', 'develop', 'code',
            'refactor', 'migrate', 'integrate', 'system', 'feature',
            'setup', 'configure', 'write'
        ],
        'multi_component': [
            'and', 'with', 'plus', 'also', 'multiple', 'several',
            'components', 'modules', 'services', 'both', 'various'
        ],
        'requires_architecture': [
            'api', 'database', 'authentication', 'authorization',
            'frontend', 'backend', 'full-stack', 'microservice',
            'oauth', 'payment', 'integration', 'workflow'
        ]
    }
    
    score = 0
    
    # Check for high complexity keywords
    for word in complexity_indicators['high']:
        if word in prompt_lower:
            score += 2
    
    # Check for multi-component indicators
    for word in complexity_indicators['multi_component']:
        if word in prompt_lower:
            score += 1
    
    # Check for architecture requirements
    for word in complexity_indicators['requires_architecture']:
        if word in prompt_lower:
            score += 3
    
    # Check for explicit multiple requirements
    if any(separator in prompt for separator in ['\n-', '\n*', '\n1.', '1)', '- [ ]']):
        score += 5  # Likely a list of requirements
    
    # Check for multiple sentences indicating complex request
    if prompt.count('.') > 2:
        score += 2
    
    return score >= 5  # Threshold for automatic activation

def main():
    # Read input from hook
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    prompt = input_data.get('prompt', '')
    
    # Check if large task infrastructure exists
    if not Path('.claude/BOUNDARIES.json').exists():
        # Infrastructure not set up yet
        sys.exit(0)
    
    # Check current mode
    mode_file = Path('.claude/LARGE_TASK_MODE.json')
    if mode_file.exists():
        try:
            mode = json.loads(mode_file.read_text())
            if mode.get('status') == 'active':
                # Already in large task mode
                sys.exit(0)
        except json.JSONDecodeError:
            # Invalid JSON, continue without mode
            mode = {}
    
    # Analyze if this task needs large task workflow
    if analyze_task_complexity(prompt):
        # Activate workflow automatically
        activation_context = f"""[LARGE TASK WORKFLOW AUTO-ACTIVATED]

Complex task detected requiring structured approach:
- Architecture planning for common code
- Test-driven development enforcement
- Continuous validation
- Automatic recovery on failures

Starting with architecture-planner agent to define /common/ structure..."""
        
        # Update mode file
        mode_data = {
            "status": "active",
            "auto_triggered": True,
            "original_prompt": prompt,
            "task_id": f"auto_{abs(hash(prompt)) % 10000}",
            "activated_at": datetime.now().isoformat(),
            "project_path": str(Path.cwd())
        }
        mode_file.parent.mkdir(exist_ok=True)
        mode_file.write_text(json.dumps(mode_data, indent=2))
        
        # Return context to trigger workflow
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": activation_context
            }
        }
        json.dump(output, sys.stdout)
    
    sys.exit(0)

if __name__ == "__main__":
    main()