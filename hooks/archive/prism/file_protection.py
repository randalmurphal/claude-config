#!/usr/bin/env python3
"""
File Protection Hook for Claude Code
Enforces repository boundaries and prevents dangerous file operations
"""

import json
import os
import sys
import subprocess
import re
from pathlib import Path
import fnmatch
from typing import Dict, List, Optional, Tuple

class FileProtectionHook:
    def __init__(self):
        self.config_path = Path.home() / ".claude" / "file-protection-config.json"
        self.config = self.load_config()
        self.git_root = self.get_git_root()
        self.working_dir = Path.cwd()
        
    def load_config(self) -> Dict:
        """Load the file protection configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "global_protection": {
                "never_delete_patterns": [],
                "critical_files": [],
                "protected_directories": []
            },
            "safety_rules": {
                "max_files_per_delete": 5,
                "max_files_per_modify": 20
            }
        }
    
    def get_git_root(self) -> Optional[Path]:
        """Get the root of the current git repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except:
            pass
        return None
    
    def is_path_in_repo(self, path: Path) -> bool:
        """Check if a path is within the current git repository"""
        if not self.git_root:
            return True  # If not in a git repo, allow normal operations
        
        try:
            # Resolve the path to handle relative paths and symlinks
            resolved_path = path.resolve()
            resolved_git = self.git_root.resolve()
            
            # Check if the path is within the git repository
            return resolved_path.is_relative_to(resolved_git)
        except:
            return False
    
    def is_system_path(self, path: Path) -> bool:
        """Check if a path is a critical system path"""
        system_paths = [
            "/etc", "/usr", "/bin", "/sbin", "/boot", "/lib", "/lib64",
            "/proc", "/sys", "/dev", "/root", "/var/log", "/var/lib"
        ]
        
        try:
            resolved = path.resolve()
            path_str = str(resolved)
            
            # Check if it's a system path
            for sys_path in system_paths:
                if path_str.startswith(sys_path):
                    return True
                    
            # Check if it's in user's home but outside normal work areas
            home = Path.home()
            if resolved.is_relative_to(home):
                # Allow paths in common work directories
                safe_home_dirs = [
                    "repos", "projects", "work", "dev", "Documents",
                    "Downloads", "Desktop", ".claude", "src", "code"
                ]
                relative_to_home = resolved.relative_to(home)
                first_part = str(relative_to_home).split('/')[0] if '/' in str(relative_to_home) else str(relative_to_home)
                
                # If it's directly in home or in a dot directory (except .claude)
                if first_part.startswith('.') and first_part != '.claude':
                    return True
                    
        except:
            pass
            
        return False
    
    def matches_protected_pattern(self, path: Path, patterns: List[str]) -> bool:
        """Check if a path matches any of the protected patterns"""
        path_str = str(path)
        
        for pattern in patterns:
            # Handle glob patterns
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Also check if any parent directory matches
            for parent in path.parents:
                if fnmatch.fnmatch(str(parent), pattern):
                    return True
                    
        return False
    
    def check_python_code(self, code: str) -> Tuple[bool, str]:
        """Check Python code for dangerous operations"""
        # Dangerous Python patterns
        dangerous_patterns = [
            # File system operations
            (r'os\.remove\s*\(', "os.remove() - deleting files"),
            (r'os\.unlink\s*\(', "os.unlink() - deleting files"),
            (r'os\.rmdir\s*\(', "os.rmdir() - removing directories"),
            (r'shutil\.rmtree\s*\(', "shutil.rmtree() - recursively deleting directories"),
            (r'pathlib.*\.unlink\s*\(', "Path.unlink() - deleting files"),
            (r'pathlib.*\.rmdir\s*\(', "Path.rmdir() - removing directories"),
            
            # System modification
            (r'os\.system\s*\(', "os.system() - executing system commands"),
            (r'subprocess\.(run|call|Popen)\s*\(', "subprocess - executing system commands"),
            (r'exec\s*\(', "exec() - executing arbitrary code"),
            (r'eval\s*\(', "eval() - evaluating arbitrary code"),
            (r'__import__\s*\(', "__import__() - dynamic imports"),
            (r'compile\s*\(', "compile() - compiling arbitrary code"),
            
            # Dangerous file operations on system paths
            (r'open\s*\(\s*["\']\/(?:etc|usr|bin|sbin|boot|lib|proc|sys|dev)', "opening system files for writing"),
            (r'with\s+open\s*\(\s*["\']\/(?:etc|usr|bin|sbin|boot|lib|proc|sys|dev)', "opening system files"),
        ]
        
        # Check for dangerous patterns
        for pattern, description in dangerous_patterns:
            if re.search(pattern, code):
                # For file operations, check if they're targeting system files or outside repo
                if 'remove' in description or 'delet' in description or 'rmtree' in description:
                    # Try to extract the path being operated on
                    path_patterns = [
                        r'["\']([^"\']+)["\']',  # String literals
                        r'Path\s*\(\s*["\']([^"\']+)["\']',  # Path objects
                    ]
                    
                    for path_pattern in path_patterns:
                        matches = re.findall(path_pattern, code)
                        for match in matches:
                            try:
                                path = Path(match).expanduser()
                                if path.is_absolute():
                                    if self.is_system_path(path):
                                        return False, f"Blocked: Python code attempts to {description} on system path '{path}'"
                                    if self.git_root and not self.is_path_in_repo(path):
                                        return False, f"Blocked: Python code attempts to {description} outside repository '{path}'"
                            except:
                                pass
                    
                    # If we can't determine the path, warn about the operation
                    return False, f"Blocked: Python code contains dangerous operation: {description}. Please verify the target paths are safe."
                
                # For other dangerous operations, block them
                if any(danger in description for danger in ['system()', 'subprocess', 'exec()', 'eval()', '__import__', 'compile()']):
                    return False, f"Blocked: Python code contains potentially dangerous operation: {description}"
        
        return True, "OK"
    
    def check_bash_command(self, command: str) -> Tuple[bool, str]:
        """Check if a bash command is safe to execute"""
        dangerous_commands = [
            "rm -rf /", "rm -fr /", 
            "dd if=/dev/zero of=/",
            "mkfs", "fdisk", "parted",
            "> /dev/sda", "chmod -R 777 /",
            "chown -R", ":(){ :|:& };:",  # Fork bomb
        ]
        
        # Check for obviously dangerous commands
        for dangerous in dangerous_commands:
            if dangerous in command:
                return False, f"Blocked: Command contains dangerous operation '{dangerous}'"
        
        # Check if it's a Python command
        python_patterns = [
            r'^python[0-9]*\s+',
            r'^python[0-9]*\s+-c\s+',
            r'^python[0-9]*\s+-m\s+',
            r'python[0-9]*\s+.*\.py\b',
        ]
        
        for pattern in python_patterns:
            if re.search(pattern, command):
                # Extract Python code
                if '-c' in command:
                    # Inline Python code
                    code_match = re.search(r'-c\s+["\'](.+?)["\']', command)
                    if not code_match:
                        code_match = re.search(r'-c\s+(.+?)(?:\s*;|$)', command)
                    
                    if code_match:
                        python_code = code_match.group(1)
                        allowed, message = self.check_python_code(python_code)
                        if not allowed:
                            return False, message
                
                # Check if running a Python file
                if '.py' in command:
                    # Extract the file path
                    file_match = re.search(r'([^\s]+\.py)', command)
                    if file_match:
                        py_file = file_match.group(1)
                        try:
                            py_path = Path(py_file).expanduser()
                            # Only allow Python files within the repo or in temp
                            if py_path.is_absolute():
                                if self.git_root and not self.is_path_in_repo(py_path):
                                    if not self.should_allow_external_path(py_path):
                                        return False, f"Blocked: Cannot run Python script outside repository '{py_path}'"
                        except:
                            pass
        
        # Parse the command to look for file operations
        if self.git_root:
            # Look for file paths in the command
            # This is a simple heuristic - could be improved
            if any(op in command for op in ["rm ", "mv ", "cp ", ">"]):
                # Try to extract paths from the command
                parts = command.split()
                for i, part in enumerate(parts):
                    if part.startswith('/') or part.startswith('~'):
                        path = Path(part).expanduser()
                        if not self.is_path_in_repo(path):
                            if self.is_system_path(path):
                                return False, f"Blocked: Command targets system path '{path}'"
                            elif not self.should_allow_external_path(path):
                                return False, f"Blocked: Command targets path outside repository '{path}'"
        
        return True, "OK"
    
    def should_allow_external_path(self, path: Path) -> bool:
        """Determine if an external path should be allowed"""
        # Allow reading certain external files
        safe_external_patterns = [
            "*.txt", "*.md", "*.json", "*.yml", "*.yaml",
            "*.csv", "*.log", "*.conf", "*.ini"
        ]
        
        # Allow operations in temp directories
        temp_dirs = ["/tmp", "/var/tmp", Path.home() / "tmp"]
        for temp_dir in temp_dirs:
            try:
                if path.resolve().is_relative_to(Path(temp_dir).resolve()):
                    return True
            except:
                pass
        
        # Allow reading documentation or configuration files
        if path.suffix in ['.md', '.txt', '.json', '.yml', '.yaml', '.conf', '.ini']:
            return True
            
        return False
    
    def check_file_operation(self, tool: str, params: Dict) -> Tuple[bool, str]:
        """Check if a file operation should be allowed"""
        # Extract file path based on tool
        file_path = None
        operation_type = None
        
        if tool in ["Write", "Edit", "MultiEdit"]:
            file_path = params.get("file_path")
            operation_type = "write"
        elif tool == "Read":
            file_path = params.get("file_path")
            operation_type = "read"
        elif tool == "Bash":
            command = params.get("command", "")
            return self.check_bash_command(command)
        else:
            # Unknown tool, allow it
            return True, "OK"
        
        if not file_path:
            return True, "OK"
        
        path = Path(file_path).expanduser()
        
        # For read operations, be more permissive
        if operation_type == "read":
            # Allow reading most files, just warn about sensitive ones
            if self.is_system_path(path):
                # Allow reading common system files like /etc/passwd for legitimate purposes
                sensitive_files = ["/etc/shadow", "/etc/sudoers", "/root/.ssh/id_rsa"]
                if str(path) in sensitive_files:
                    return False, f"Blocked: Cannot read sensitive system file '{path}'"
                # Allow reading other system files
                return True, "OK"
            # Always allow read operations
            return True, "OK"
        
        # For write operations, be more restrictive
        if operation_type == "write":
            # Check if it's a system path
            if self.is_system_path(path):
                return False, f"Blocked: Cannot {operation_type} system file '{path}'"
            
            # Allow operations in temp directories even outside repo
            temp_dirs = ["/tmp", "/var/tmp"]
            for temp_dir in temp_dirs:
                try:
                    if path.resolve().is_relative_to(Path(temp_dir).resolve()):
                        return True, "OK"
                except:
                    pass
            
            # If we're in a git repo, enforce repository boundaries for write operations
            if self.git_root:
                if not self.is_path_in_repo(path):
                    # Check if this is an allowed external operation
                    if self.should_allow_external_path(path):
                        return True, "OK"
                        
                    return False, f"Blocked: Cannot {operation_type} file outside repository. File: '{path}', Repository: '{self.git_root}'"
        
        # Check against protected patterns
        if operation_type == "write":
            protection = self.config.get("global_protection", {})
            
            # Check never delete patterns
            if self.matches_protected_pattern(path, protection.get("never_delete_patterns", [])):
                return False, f"Blocked: File matches protected pattern '{path}'"
            
            # Check critical files
            if path.name in protection.get("critical_files", []):
                # Allow editing critical files within the repo
                if self.git_root and self.is_path_in_repo(path):
                    return True, "OK"
                return False, f"Blocked: Cannot modify critical file '{path.name}' outside repository"
            
            # Check protected directories
            for protected_dir in protection.get("protected_directories", []):
                if protected_dir in str(path):
                    # Allow if it's within the repo (e.g., modifying node_modules within project)
                    if self.git_root and self.is_path_in_repo(path):
                        # Still block certain directories even in repo
                        if protected_dir in [".git", ".svn", ".hg"]:
                            return False, f"Blocked: Cannot modify version control directory '{protected_dir}'"
                    else:
                        return False, f"Blocked: Cannot modify protected directory '{protected_dir}'"
        
        return True, "OK"
    
    def process_hook(self):
        """Main hook processing logic"""
        # Read the hook input
        try:
            hook_input = json.loads(sys.stdin.read())
        except json.JSONDecodeError:
            # If no JSON input, allow the operation
            return
        
        tool = hook_input.get("tool", "")
        params = hook_input.get("params", {})
        
        # Check the operation
        allowed, message = self.check_file_operation(tool, params)
        
        if not allowed:
            # Block the operation
            print(json.dumps({
                "action": "block",
                "message": message,
                "suggestion": "This operation was blocked by the file protection hook. If this is intentional, please confirm the operation or modify the target to be within the repository boundaries."
            }))
            sys.exit(0)
        
        # Allow the operation (no output means proceed)
        sys.exit(0)

def main():
    """Main entry point"""
    try:
        hook = FileProtectionHook()
        hook.process_hook()
    except Exception as e:
        # Log the error but don't block operations on hook failure
        error_log = Path.home() / ".claude" / "hooks" / "protection_errors.log"
        with open(error_log, 'a') as f:
            f.write(f"Protection hook error: {e}\n")
        # Allow operation to proceed on hook error
        sys.exit(0)

if __name__ == "__main__":
    main()