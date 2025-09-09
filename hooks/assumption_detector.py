#!/usr/bin/env python3
"""
Assumption Detection Hook for Claude Code
Monitors agent output for assumptions and unverified references
"""

import re
import json
import sys

def detect_assumptions(text):
    """Detect assumption patterns in agent output"""
    
    assumptions = []
    
    # Vague language patterns indicating uncertainty
    uncertainty_patterns = [
        r'\b(probably|likely|should be|typically|usually|generally|might be|could be|seems like)\b',
        r'\b(I assume|assuming|presuming|suppose|expect)\b',
        r'\b(something like|similar to|based on common patterns)\b',
    ]
    
    # Unverified references (things mentioned without verification)
    unverified_patterns = [
        r'the\s+\w+\s+(module|package|library|component)',
        r'existing\s+\w+\s+(service|component|module|handler|class|function)',
        r'uses?\s+\w+\s+(database|cache|queue|storage)',  # Any tech without verification
        r'follows?\s+the\s+\w+\s+pattern',
        r'standard\s+\w+\s+implementation',
        r'the\s+project\'s\s+\w+',  # "the project's X" without verification
    ]
    
    # Generic path references without verification
    generic_paths = [
        r'\.\.\/[^\/\s]+',  # Relative paths without verification
        r'\/(?:src|lib|app|pkg|Sources|internal|cmd|bin)\/\w+',  # Common source directories
        r'\/(?:api|services|controllers|handlers|routes)\/\w+',  # Common API paths
        r'\/(?:test|tests|spec|specs|__tests__)\/\w+',  # Test directories
    ]
    
    # Check for uncertainty language
    for pattern in uncertainty_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            assumptions.append({
                "type": "uncertainty",
                "pattern": pattern,
                "matches": matches,
                "severity": "medium"
            })
    
    # Check for unverified references
    for pattern in unverified_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            assumptions.append({
                "type": "unverified_reference",
                "pattern": pattern,
                "matches": matches,
                "severity": "high"
            })
    
    # Check for generic paths
    for pattern in generic_paths:
        matches = re.findall(pattern, text)
        if matches:
            assumptions.append({
                "type": "generic_path",
                "pattern": pattern,
                "matches": matches,
                "severity": "high"
            })
    
    # Check for missing file:line references
    code_mentions = re.findall(r'(class|function|method|component)\s+(\w+)', text, re.IGNORECASE)
    for mention_type, mention_name in code_mentions:
        # Check if there's a file:line reference nearby
        context = text[max(0, text.find(mention_name)-100):text.find(mention_name)+100]
        if not re.search(r'\w+\.\w+:\d+', context):
            assumptions.append({
                "type": "missing_location",
                "reference": f"{mention_type} {mention_name}",
                "severity": "medium"
            })
    
    return assumptions

def calculate_confidence(text, assumptions):
    """Calculate confidence score based on facts vs assumptions"""
    
    # Count verified facts (things with concrete references)
    facts = []
    
    # File:line references are facts
    file_refs = re.findall(r'([\/\w]+\.\w+):(\d+)', text)
    facts.extend(file_refs)
    
    # Concrete paths that exist are facts
    concrete_paths = re.findall(r'\/[\w\/]+\.\w+', text)
    facts.extend(concrete_paths)
    
    # Specific version numbers, configs are facts
    configs = re.findall(r'(version|config|setting):\s*[\w\.\-]+', text)
    facts.extend(configs)
    
    # Calculate ratio
    total_claims = len(facts) + len(assumptions)
    if total_claims == 0:
        return 100  # No claims made
    
    confidence = (len(facts) / total_claims) * 100
    return round(confidence, 1)

def main():
    # Read input from stdin
    input_data = json.loads(sys.stdin.read())
    
    # Only process Task tool calls
    if input_data.get("tool") != "Task":
        print(json.dumps({"action": "continue"}))
        return
    
    # Get the prompt being sent to the agent
    prompt = input_data.get("parameters", {}).get("prompt", "")
    
    # Detect assumptions in the prompt
    assumptions = detect_assumptions(prompt)
    
    if assumptions:
        # Calculate confidence
        confidence = calculate_confidence(prompt, assumptions)
        
        # Build warning message
        warning_parts = []
        
        # Group by severity
        high_severity = [a for a in assumptions if a["severity"] == "high"]
        medium_severity = [a for a in assumptions if a["severity"] == "medium"]
        
        if high_severity:
            warning_parts.append("⚠️ HIGH RISK ASSUMPTIONS DETECTED:")
            for assumption in high_severity[:3]:  # Show top 3
                warning_parts.append(f"  - {assumption['type']}: {assumption.get('matches', [assumption.get('reference', '')])[:2]}")
        
        if medium_severity:
            warning_parts.append("⚠️ MEDIUM RISK ASSUMPTIONS:")
            for assumption in medium_severity[:2]:  # Show top 2
                warning_parts.append(f"  - {assumption['type']}: {assumption.get('matches', [assumption.get('reference', '')])[:2]}")
        
        warning_parts.append(f"\n📊 Confidence Score: {confidence}%")
        
        if confidence < 95:
            warning_parts.append("\n🛑 BLOCKING: Confidence below 95% threshold")
            warning_parts.append("Agent should:")
            warning_parts.append("1. Search for concrete file locations")
            warning_parts.append("2. Verify mentioned components exist")
            warning_parts.append("3. Replace generic paths with specific ones")
            warning_parts.append("4. Return findings for user clarification if needed")
            
            # Modify the prompt to include assumption awareness
            modified_prompt = f"""⚠️ ASSUMPTION WARNING ⚠️
Your prompt contains assumptions that need verification first.

{chr(10).join(warning_parts)}

MODIFIED INSTRUCTIONS:
Before proceeding with the main task:
1. Use Glob/Grep to verify all mentioned components exist
2. Find concrete file:line locations for any generic references
3. Confirm or invalidate each assumption
4. Update TASK_CONTEXT.json with findings
5. If confidence remains <95%, return specific questions for user

Original task:
{prompt}"""
            
            print(json.dumps({
                "action": "modify",
                "parameters": {
                    "prompt": modified_prompt
                }
            }))
        else:
            # Just add a reminder to be specific
            modified_prompt = f"""{prompt}

📝 REMINDER: Output structured data with concrete file:line references.
Separate facts from assumptions. Track what doesn't exist in 'invalidated'."""
            
            print(json.dumps({
                "action": "modify", 
                "parameters": {
                    "prompt": modified_prompt
                }
            }))
    else:
        # No assumptions detected, continue
        print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()