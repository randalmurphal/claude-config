#!/usr/bin/env python3
"""
Documentation Prompter Hook
Prompts agents to update CLAUDE.md when significant changes are made
Language and project agnostic
"""

import json
import sys
import os
import re
from pathlib import Path


def find_tool_claude_md(file_path):
    """Find the first CLAUDE.md going up from the file's directory"""
    path = Path(file_path).parent
    
    # Simple: just go up until we find a CLAUDE.md
    while path.parent != path:
        claude_md = path / 'CLAUDE.md'
        if claude_md.exists():
            return claude_md
        path = path.parent
    
    return None


def is_in_tool_directory(file_path):
    """Check if file is in a tool-specific directory (not root)"""
    path = Path(file_path)
    
    # Skip if in root directories
    root_indicators = ['/.git/', '/node_modules/', '/venv/', '/.venv/', 
                      '/build/', '/dist/', '/__pycache__/']
    if any(indicator in str(path) for indicator in root_indicators):
        return False
    
    # Check if there's a CLAUDE.md in the same or immediate parent directory
    # This indicates we're in a tool/module directory
    for parent in [path.parent, path.parent.parent]:
        if (parent / 'CLAUDE.md').exists():
            return True
    
    return False


def analyze_significance(tool, params, file_path):
    """Determine if a change is significant enough to warrant documentation"""
    
    # Skip test files and non-code files
    if any(pattern in file_path.lower() for pattern in ['test', 'spec', '.md', '.txt', '.json', '.yml', '.yaml', '.toml', '__pycache__', '.pyc']):
        return False, None
    
    # Check file extension for code files
    code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.cpp', '.c', '.rs', '.rb', '.php']
    if not any(file_path.endswith(ext) for ext in code_extensions):
        return False, None
    
    significant_changes = []
    
    if tool == "Write":
        content = params.get("content", "")
        
        # Skip trivial files
        if len(content.strip()) < 50:  # Very small files
            return False, None
        
        # Only mark new file as significant if it has substantial content
        has_substance = False
        
        # Check for major components
        if re.search(r'class\s+\w+', content):
            classes = re.findall(r'class\s+(\w+)', content)
            # Filter out test/mock classes
            real_classes = [c for c in classes if not any(skip in c.lower() for skip in ['test', 'mock', 'stub', 'dummy'])]
            if real_classes:
                significant_changes.append(f"New classes: {', '.join(real_classes)}")
                has_substance = True
        
        # Count significant functions
        if re.search(r'def\s+\w+', content):
            functions = re.findall(r'def\s+([a-zA-Z]\w*)', content)
            # Filter out private, test, and trivial functions
            public_functions = [f for f in functions if not f.startswith('_') and not any(skip in f.lower() for skip in ['test', 'setup', 'teardown'])]
            if len(public_functions) >= 3:  # At least 3 public functions
                significant_changes.append(f"New functions: {', '.join(public_functions[:5])}")
                has_substance = True
        
        # API endpoints (various frameworks)
        api_patterns = [
            r'@(app|router|api|blueprint)\.(get|post|put|delete|patch|route)',
            r'@(Get|Post|Put|Delete|Patch|RequestMapping)',  # Java/Spring
            r'router\.(get|post|put|delete|patch)\(',  # Express.js
            r'http\.(HandleFunc|Handle)\(',  # Go
        ]
        for pattern in api_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                significant_changes.append("New API endpoints")
                has_substance = True
                break
        
        # Data models/schemas/migrations
        if re.search(r'(class\s+\w+.*\(.*(?:Model|Schema|Entity|Table|Document|Collection))', content):
            significant_changes.append("New data model/schema")
            has_substance = True
        
        # Database migrations
        if re.search(r'(CREATE|ALTER|DROP)\s+(TABLE|INDEX|VIEW|TRIGGER)', content, re.IGNORECASE):
            significant_changes.append("Database schema changes")
            has_substance = True
        
        # Configuration or settings
        if re.search(r'class\s+\w*(?:Config|Settings|Configuration|Options)\b', content, re.IGNORECASE):
            significant_changes.append("Configuration changes")
            has_substance = True
        
        # New integrations/clients/connections
        integration_patterns = [
            r'(?:redis|mongodb|postgres|mysql|kafka|rabbitmq|aws|azure|gcp).*(?:client|connection|connect)',
            r'class\s+\w*(?:Client|Connection|Adapter|Gateway|Service|Integration)\b',
            r'(?:import|from)\s+(?:boto3|pymongo|redis|psycopg2|kafka|pika|azure)',
        ]
        for pattern in integration_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                significant_changes.append("New integration/service connection")
                has_substance = True
                break
        
        # If new file but no substantial content detected
        if not has_substance:
            # Check if it's a significant file type by name
            significant_file_patterns = ['handler', 'processor', 'service', 'manager', 'controller', 'gateway', 'adapter']
            if any(pattern in file_path.lower() for pattern in significant_file_patterns):
                functions = re.findall(r'def\s+([a-zA-Z]\w*)', content)
                if len(functions) >= 2:  # At least 2 functions
                    significant_changes.append("New component file")
                    has_substance = True
        
        # Only report new file if it has substance
        if has_substance and "New file created" not in str(significant_changes):
            significant_changes.insert(0, "New file created")
            
    elif tool in ["Edit", "MultiEdit"]:
        # For edits, check what's being modified
        if tool == "Edit":
            old_string = params.get("old_string", "")
            new_string = params.get("new_string", "")
            
            # Check size of change
            lines_changed = abs(len(new_string.splitlines()) - len(old_string.splitlines()))
            if lines_changed < 10:
                return False, None  # Minor change
            
            # Check for structural changes
            old_classes = set(re.findall(r'class\s+(\w+)', old_string))
            new_classes = set(re.findall(r'class\s+(\w+)', new_string))
            if new_classes - old_classes:
                significant_changes.append(f"New classes: {', '.join(new_classes - old_classes)}")
            
            old_funcs = set(re.findall(r'def\s+([a-zA-Z]\w*)', old_string))
            new_funcs = set(re.findall(r'def\s+([a-zA-Z]\w*)', new_string))
            public_new_funcs = [f for f in (new_funcs - old_funcs) if not f.startswith('_')]
            if len(public_new_funcs) > 1:
                significant_changes.append(f"New functions: {', '.join(public_new_funcs)}")
                
        else:  # MultiEdit
            edits = params.get("edits", [])
            total_lines_changed = 0
            new_components = []
            
            for edit in edits:
                old = edit.get("old_string", "")
                new = edit.get("new_string", "")
                total_lines_changed += abs(len(new.splitlines()) - len(old.splitlines()))
                
                # Check for new classes/functions
                old_classes = set(re.findall(r'class\s+(\w+)', old))
                new_classes = set(re.findall(r'class\s+(\w+)', new))
                new_components.extend(new_classes - old_classes)
                
            if total_lines_changed < 20:
                return False, None  # Minor changes
                
            if new_components:
                significant_changes.append(f"New components: {', '.join(new_components[:5])}")
            if total_lines_changed > 50:
                significant_changes.append(f"Major refactoring ({total_lines_changed} lines changed)")
    
    # Check for borderline significant patterns
    if not significant_changes and tool == "Write":
        content = params.get("content", "")
        
        # New integration/handler/processor files
        if any(pattern in file_path.lower() for pattern in ['handler', 'processor', 'integration', 'service', 'manager', 'controller']):
            significant_changes.append("New component/service file")
        
        # New utility modules with multiple functions
        functions = re.findall(r'def\s+([a-zA-Z]\w*)', content)
        if len(functions) > 3:
            significant_changes.append(f"New utility module with {len(functions)} functions")
        
        # Database migrations or schema changes
        if 'migration' in file_path.lower() or re.search(r'CREATE TABLE|ALTER TABLE', content, re.IGNORECASE):
            significant_changes.append("Database schema changes")
    
    # Return whether significant and what changed
    if significant_changes:
        return True, significant_changes
    
    return False, None


def create_doc_prompt(file_path, changes, claude_md_path):
    """Create a prompt for updating documentation"""
    
    relative_path = os.path.relpath(file_path, claude_md_path.parent)
    
    prompt = f"""
DOCUMENTATION UPDATE NEEDED

Significant changes were made to: {relative_path}
Changes detected: {', '.join(changes)}

Please review the changes and update {claude_md_path} if needed.

Consider documenting:
1. Purpose of new components/files
2. How they fit into the overall architecture
3. Key functions and their roles
4. Data flow changes
5. Important dependencies or integrations
6. Any patterns or conventions used

If the changes are already documented or don't need documentation, you can skip this update.
Use the Edit tool to update {claude_md_path} with the relevant information.
Keep descriptions concise but complete.
"""
    
    return prompt.strip()


def main():
    # Read input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except:
        print(json.dumps({"action": "continue"}))
        return
    
    # Only process Write, Edit, and MultiEdit tools
    tool = input_data.get("tool", "")
    if tool not in ["Write", "Edit", "MultiEdit"]:
        print(json.dumps({"action": "continue"}))
        return
    
    # Get file path
    params = input_data.get("parameters", {})
    file_path = params.get("file_path", "")
    
    if not file_path:
        print(json.dumps({"action": "continue"}))
        return
    
    # Check if in a tool directory
    if not is_in_tool_directory(file_path):
        print(json.dumps({"action": "continue"}))
        return
    
    # Find the nearest CLAUDE.md
    claude_md = find_tool_claude_md(file_path)
    if not claude_md:
        print(json.dumps({"action": "continue"}))
        return
    
    # Analyze if change is significant
    is_significant, changes = analyze_significance(tool, params, file_path)
    
    if not is_significant:
        print(json.dumps({"action": "continue"}))
        return
    
    # Create documentation prompt
    doc_prompt = create_doc_prompt(file_path, changes, claude_md)
    
    # Modify the original action to include documentation prompt
    # We'll append it to any existing output or return it as a notification
    
    sys.stderr.write(f"📚 Documentation update suggested for {claude_md}\n")
    sys.stderr.write(f"   Changes: {', '.join(changes)}\n")
    
    # Return a notification to prompt for documentation
    print(json.dumps({
        "action": "continue",
        "notification": doc_prompt
    }))


if __name__ == "__main__":
    main()