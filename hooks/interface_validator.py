#!/usr/bin/env python3
"""Interface Validation Hook - Validates interface compatibility on file changes.

This hook checks for breaking changes in interfaces and ensures compatibility
between modules during development.
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# Color codes for terminal output
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def extract_interfaces(file_content: str, file_type: str) -> Dict[str, Dict]:
    """Extract interface definitions from file content."""
    interfaces = {}

    if file_type in ['.ts', '.tsx', '.js', '.jsx']:
        # Extract TypeScript/JavaScript interfaces
        # Find interface definitions
        interface_pattern = r'(?:export\s+)?interface\s+(\w+)\s*\{([^}]*)\}'
        for match in re.finditer(interface_pattern, file_content, re.MULTILINE | re.DOTALL):
            interface_name = match.group(1)
            interface_body = match.group(2)
            fields = {}

            # Extract fields
            field_pattern = r'(\w+)\s*(?:\?)?:\s*([^;,\n]+)'
            for field_match in re.finditer(field_pattern, interface_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                fields[field_name] = field_type

            interfaces[interface_name] = {
                'fields': fields,
                'type': 'interface'
            }

        # Find type definitions
        type_pattern = r'(?:export\s+)?type\s+(\w+)\s*=\s*\{([^}]*)\}'
        for match in re.finditer(type_pattern, file_content, re.MULTILINE | re.DOTALL):
            type_name = match.group(1)
            type_body = match.group(2)
            fields = {}

            # Extract fields
            field_pattern = r'(\w+)\s*(?:\?)?:\s*([^;,\n]+)'
            for field_match in re.finditer(field_pattern, type_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                fields[field_name] = field_type

            interfaces[type_name] = {
                'fields': fields,
                'type': 'type'
            }

    elif file_type == '.py':
        # Extract Python class definitions (dataclasses, TypedDict, etc.)
        # Find dataclass definitions
        dataclass_pattern = r'@dataclass(?:\(.*?\))?\s*class\s+(\w+)(?:\([^)]*\))?:\s*\n((?:[ \t]+[^\n]+\n)*)'
        for match in re.finditer(dataclass_pattern, file_content, re.MULTILINE):
            class_name = match.group(1)
            class_body = match.group(2) if match.group(2) else ""
            fields = {}

            # Extract fields
            field_pattern = r'^\s+(\w+)\s*:\s*([^\n=]+)(?:\s*=\s*[^\n]+)?'
            for field_match in re.finditer(field_pattern, class_body, re.MULTILINE):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                fields[field_name] = field_type

            if fields:  # Only add if we found fields
                interfaces[class_name] = {
                    'fields': fields,
                    'type': 'dataclass'
                }

        # Find TypedDict definitions
        typeddict_pattern = r'class\s+(\w+)\(TypedDict\):\s*\n((?:[ \t]+[^\n]+\n)*)'
        for match in re.finditer(typeddict_pattern, file_content, re.MULTILINE):
            class_name = match.group(1)
            class_body = match.group(2) if match.group(2) else ""
            fields = {}

            # Extract fields
            field_pattern = r'^\s+(\w+)\s*:\s*([^\n]+)'
            for field_match in re.finditer(field_pattern, class_body, re.MULTILINE):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                fields[field_name] = field_type

            if fields:  # Only add if we found fields
                interfaces[class_name] = {
                    'fields': fields,
                    'type': 'TypedDict'
                }

    elif file_type == '.go':
        # Extract Go struct definitions
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{([^}]*)\}'
        for match in re.finditer(struct_pattern, file_content, re.MULTILINE | re.DOTALL):
            struct_name = match.group(1)
            struct_body = match.group(2)
            fields = {}

            # Extract fields
            field_pattern = r'(\w+)\s+([^\s\n]+)(?:\s+`[^`]*`)?'
            for field_match in re.finditer(field_pattern, struct_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                fields[field_name] = field_type

            interfaces[struct_name] = {
                'fields': fields,
                'type': 'struct'
            }

    return interfaces

def find_consumers(file_path: str, interface_name: str) -> List[str]:
    """Find files that import and use the given interface."""
    consumers = []
    file_dir = os.path.dirname(file_path)
    project_root = find_project_root(file_path)

    # Common patterns to search for
    search_patterns = [
        f"import.*{interface_name}",  # Import statements
        f":\\s*{interface_name}",      # Type annotations
        f"<{interface_name}>",         # Generic type usage
        f"extends\\s+{interface_name}", # Inheritance
        f"implements\\s+{interface_name}", # Implementation
    ]

    # Search in the same directory and common consumer directories
    search_dirs = [
        file_dir,
        os.path.join(project_root, "src"),
        os.path.join(project_root, "lib"),
        os.path.join(project_root, "components"),
        os.path.join(project_root, "services"),
    ]

    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue

        for root, _, files in os.walk(search_dir):
            # Skip node_modules and other build directories
            if any(skip in root for skip in ['node_modules', '.git', 'dist', 'build', '__pycache__']):
                continue

            for file in files:
                if not file.endswith(('.ts', '.tsx', '.js', '.jsx', '.py', '.go')):
                    continue

                full_path = os.path.join(root, file)
                if full_path == file_path:  # Skip the file itself
                    continue

                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in search_patterns:
                            if re.search(pattern, content):
                                consumers.append(full_path)
                                break
                except Exception:
                    continue

    return list(set(consumers))  # Remove duplicates

def check_compatibility(old_interface: Dict, new_interface: Dict) -> Tuple[bool, List[str]]:
    """Check if the new interface is compatible with the old one."""
    issues = []
    old_fields = old_interface.get('fields', {})
    new_fields = new_interface.get('fields', {})

    # Check for removed fields (breaking change)
    for field_name, field_type in old_fields.items():
        if field_name not in new_fields:
            issues.append(f"Field '{field_name}' was removed (breaking change)")

    # Check for type changes (potential breaking change)
    for field_name, old_type in old_fields.items():
        if field_name in new_fields:
            new_type = new_fields[field_name]
            if old_type != new_type:
                # Check if it's a compatible change (e.g., string | null to string)
                if not is_compatible_type_change(old_type, new_type):
                    issues.append(f"Field '{field_name}' type changed from '{old_type}' to '{new_type}' (breaking change)")

    # Check for required fields added (potential breaking change for implementations)
    for field_name, field_type in new_fields.items():
        if field_name not in old_fields:
            # Check if it's optional
            if '?' not in field_type and 'Optional' not in field_type and '| None' not in field_type:
                issues.append(f"Required field '{field_name}' added (may break implementations)")

    is_compatible = len(issues) == 0
    return is_compatible, issues

def is_compatible_type_change(old_type: str, new_type: str) -> bool:
    """Check if a type change is compatible."""
    # Normalize types
    old_normalized = old_type.replace(' ', '').lower()
    new_normalized = new_type.replace(' ', '').lower()

    # Same type is always compatible
    if old_normalized == new_normalized:
        return True

    # Widening is generally safe
    safe_widenings = [
        ('string', 'string|null'),
        ('number', 'number|null'),
        ('boolean', 'boolean|null'),
        ('string', 'string|undefined'),
        ('number', 'number|undefined'),
        ('boolean', 'boolean|undefined'),
    ]

    for old, new in safe_widenings:
        if old in old_normalized and new in new_normalized:
            return True

    return False

def find_project_root(file_path: str) -> str:
    """Find the project root directory."""
    current = Path(file_path).parent
    while current != current.parent:
        # Check for common project root indicators
        if any((current / indicator).exists() for indicator in [
            'package.json', 'setup.py', 'go.mod', '.git', 'requirements.txt'
        ]):
            return str(current)
        current = current.parent
    return str(Path(file_path).parent)

def get_file_type(file_path: str) -> str:
    """Get the file extension."""
    return Path(file_path).suffix

def load_previous_interfaces(cache_path: str) -> Dict:
    """Load previously cached interfaces."""
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_interfaces(cache_path: str, interfaces: Dict):
    """Save interfaces to cache."""
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(interfaces, f, indent=2)

def validate_interface_changes(file_path: str, content: str) -> Tuple[bool, List[str]]:
    """Main validation function."""
    file_type = get_file_type(file_path)

    # Skip non-interface files
    if file_type not in ['.ts', '.tsx', '.js', '.jsx', '.py', '.go']:
        return True, []

    # Extract interfaces from new content
    new_interfaces = extract_interfaces(content, file_type)

    if not new_interfaces:
        return True, []  # No interfaces to validate

    # Load cached interfaces
    project_root = find_project_root(file_path)
    cache_path = os.path.join(project_root, '.claude', 'interface_cache.json')
    previous_interfaces = load_previous_interfaces(cache_path)

    file_key = os.path.relpath(file_path, project_root)
    old_interfaces = previous_interfaces.get(file_key, {})

    all_issues = []

    for interface_name, new_interface in new_interfaces.items():
        if interface_name in old_interfaces:
            # Check compatibility
            is_compatible, issues = check_compatibility(
                old_interfaces[interface_name],
                new_interface
            )

            if not is_compatible:
                # Find consumers
                consumers = find_consumers(file_path, interface_name)

                if consumers:
                    all_issues.append(f"\n{RED}{BOLD}Breaking change in {interface_name}:{RESET}")
                    for issue in issues:
                        all_issues.append(f"  {YELLOW}• {issue}{RESET}")
                    all_issues.append(f"  {BLUE}Affected files:{RESET}")
                    for consumer in consumers[:5]:  # Limit to first 5
                        rel_path = os.path.relpath(consumer, project_root)
                        all_issues.append(f"    - {rel_path}")
                    if len(consumers) > 5:
                        all_issues.append(f"    ... and {len(consumers) - 5} more")

    # Update cache with new interfaces
    previous_interfaces[file_key] = new_interfaces
    save_interfaces(cache_path, previous_interfaces)

    if all_issues:
        return False, all_issues
    return True, []

def main():
    """Main entry point for the hook."""
    # This hook is typically called by Claude with file path and content
    if len(sys.argv) < 3:
        print(f"{YELLOW}Usage: interface_validator.py <file_path> <content_or_file>{RESET}")
        sys.exit(0)

    file_path = sys.argv[1]
    content_source = sys.argv[2]

    # Read content (can be from file or stdin)
    if os.path.exists(content_source):
        with open(content_source, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = content_source

    # Validate
    is_valid, issues = validate_interface_changes(file_path, content)

    if not is_valid:
        print(f"\n{RED}{BOLD}⚠️  Interface Compatibility Issues Detected{RESET}")
        for issue in issues:
            print(issue)
        print(f"\n{YELLOW}Suggestions:{RESET}")
        print(f"  1. Make the changes backward compatible")
        print(f"  2. Update all consumers to handle the new interface")
        print(f"  3. Version the interface (e.g., UserV2) for gradual migration")
        sys.exit(1)
    else:
        print(f"{GREEN}✓ Interface changes are compatible{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()