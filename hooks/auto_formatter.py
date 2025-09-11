#!/usr/bin/env python3
"""
Universal auto-formatter hook for Claude
Automatically formats code after Write/Edit/MultiEdit operations
Supports multiple languages with appropriate formatters
"""

import json
import sys
import subprocess
import os
import re
from pathlib import Path
from typing import Tuple, Optional, Dict, List


class LanguageFormatter:
    """Base class for language-specific formatters"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.home_dir = Path.home()
        self.claude_config_dir = self.home_dir / '.claude' / 'configs'
    
    def format(self) -> Tuple[bool, str]:
        """Format the file. Returns (success, message)"""
        raise NotImplementedError


class PythonFormatter(LanguageFormatter):
    """Python formatter using ruff (preferred) or black (fallback)"""
    
    def detect_quote_style(self) -> str:
        """Detect the predominant quote style in the file"""
        if not os.path.exists(self.file_path):
            return 'single'  # Default for new files
        
        try:
            with open(self.file_path, 'r') as f:
                content = f.read()
            
            # Remove docstrings and triple-quoted strings
            content_no_docstrings = re.sub(r'"""[\s\S]*?"""', '', content)
            content_no_docstrings = re.sub(r"'''[\s\S]*?'''", '', content_no_docstrings)
            
            single_quotes = len(re.findall(r"'[^']*'", content_no_docstrings))
            double_quotes = len(re.findall(r'"[^"]*"', content_no_docstrings))
            
            # If file has more double quotes, use double
            if double_quotes > single_quotes * 1.2:  # 20% threshold
                return 'double'
            else:
                return 'single'
        except:
            return 'single'  # Default on error
    
    def find_config(self, tool: str) -> Optional[str]:
        """Find configuration file for the tool"""
        # Check project directory first
        current = Path.cwd()
        while current != current.parent:
            # Check for tool-specific configs
            if tool == 'ruff':
                configs = ['ruff.toml', 'pyproject.toml', '.ruff.toml']
            elif tool == 'black':
                configs = ['pyproject.toml', '.black']
            elif tool == 'pylint':
                configs = ['pylintrc.toml', '.pylintrc', 'pyproject.toml']
            elif tool == 'mypy':
                configs = ['mypy.ini', 'setup.cfg', 'pyproject.toml']
            else:
                configs = []
            
            for config_name in configs:
                config_path = current / config_name
                if config_path.exists():
                    return str(config_path)
            
            current = current.parent
        
        # Fall back to global Claude configs
        if tool == 'ruff':
            global_config = self.claude_config_dir / 'python' / 'ruff.toml'
        elif tool == 'black':
            global_config = self.claude_config_dir / 'python' / 'black.toml'
        elif tool == 'pylint':
            global_config = self.claude_config_dir / 'python' / 'pylintrc.toml'
        elif tool == 'mypy':
            global_config = self.claude_config_dir / 'python' / 'mypy.ini'
        else:
            return None
        
        if global_config.exists():
            return str(global_config)
        
        return None
    
    def format_with_ruff(self) -> Tuple[bool, str]:
        """Try to format with ruff"""
        try:
            subprocess.run(['ruff', '--version'], 
                          capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "Ruff not available"
        
        config_path = self.find_config('ruff')
        quote_style = self.detect_quote_style()
        
        cmd = ['ruff', 'format']
        
        if config_path:
            cmd.extend(['--config', config_path])
        
        # Override quote style based on file detection
        cmd.extend(['--quote-style', quote_style])
        cmd.append(self.file_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, f"Formatted with ruff (quote style: {quote_style})"
            else:
                return False, f"Ruff error: {result.stderr}"
        except Exception as e:
            return False, f"Error running ruff: {str(e)}"
    
    def format_with_black(self) -> Tuple[bool, str]:
        """Try to format with black as fallback"""
        try:
            subprocess.run(['black', '--version'], 
                          capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "Black not available"
        
        config_path = self.find_config('black')
        
        cmd = ['black', '--line-length', '80']
        
        if config_path:
            cmd.extend(['--config', config_path])
        
        cmd.append(self.file_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Formatted with black"
            else:
                return False, f"Black error: {result.stderr}"
        except Exception as e:
            return False, f"Error running black: {str(e)}"
    
    def format(self) -> Tuple[bool, str]:
        """Format Python file with ruff or black"""
        # Try ruff first
        success, message = self.format_with_ruff()
        if success:
            return success, message
        
        # Fall back to black
        success, message = self.format_with_black()
        if success:
            return success, message
        
        return False, "No Python formatter available (tried ruff, black)"


class JavaScriptFormatter(LanguageFormatter):
    """JavaScript/TypeScript formatter using prettier or eslint"""
    
    def find_config(self, tool: str) -> Optional[str]:
        """Find configuration file for the tool"""
        current = Path.cwd()
        while current != current.parent:
            if tool == 'prettier':
                configs = ['.prettierrc', '.prettierrc.json', '.prettierrc.js', 
                          'prettier.config.js', 'package.json']
            elif tool == 'eslint':
                configs = ['.eslintrc', '.eslintrc.json', '.eslintrc.js', 
                          'eslint.config.js', 'package.json']
            else:
                configs = []
            
            for config_name in configs:
                config_path = current / config_name
                if config_path.exists():
                    return str(config_path)
            
            current = current.parent
        
        # Fall back to global Claude configs
        if tool == 'prettier':
            global_config = self.claude_config_dir / 'javascript' / 'prettier.json'
            if global_config.exists():
                return str(global_config)
        
        return None
    
    def format_with_prettier(self) -> Tuple[bool, str]:
        """Try to format with prettier"""
        try:
            subprocess.run(['prettier', '--version'], 
                          capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "Prettier not available"
        
        config_path = self.find_config('prettier')
        
        cmd = ['prettier', '--write']
        
        if config_path:
            cmd.extend(['--config', config_path])
        
        cmd.append(self.file_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Formatted with prettier"
            else:
                return False, f"Prettier error: {result.stderr}"
        except Exception as e:
            return False, f"Error running prettier: {str(e)}"
    
    def format_with_eslint(self) -> Tuple[bool, str]:
        """Try to format with eslint --fix"""
        try:
            # Try npx eslint first (local install)
            subprocess.run(['npx', 'eslint', '--version'], 
                          capture_output=True, check=True)
            eslint_cmd = ['npx', 'eslint']
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try global eslint
                subprocess.run(['eslint', '--version'], 
                              capture_output=True, check=True)
                eslint_cmd = ['eslint']
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False, "ESLint not available"
        
        cmd = eslint_cmd + ['--fix', self.file_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Formatted with eslint --fix"
            else:
                # ESLint returns non-zero even after fixing, check if file was modified
                return True, "Formatted with eslint --fix (with warnings)"
        except Exception as e:
            return False, f"Error running eslint: {str(e)}"
    
    def format(self) -> Tuple[bool, str]:
        """Format JavaScript/TypeScript file"""
        # Try prettier first
        success, message = self.format_with_prettier()
        if success:
            return success, message
        
        # Fall back to eslint --fix
        success, message = self.format_with_eslint()
        if success:
            return success, message
        
        return False, "No JS/TS formatter available (tried prettier, eslint)"


class GoFormatter(LanguageFormatter):
    """Go formatter using gofmt or goimports"""
    
    def format_with_gofmt(self) -> Tuple[bool, str]:
        """Format with gofmt"""
        try:
            subprocess.run(['gofmt', '-h'], 
                          capture_output=True, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            return False, "gofmt not available"
        
        cmd = ['gofmt', '-w', self.file_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Formatted with gofmt"
            else:
                return False, f"gofmt error: {result.stderr}"
        except Exception as e:
            return False, f"Error running gofmt: {str(e)}"
    
    def format_with_goimports(self) -> Tuple[bool, str]:
        """Format with goimports"""
        try:
            subprocess.run(['goimports', '-h'], 
                          capture_output=True, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            return False, "goimports not available"
        
        cmd = ['goimports', '-w', self.file_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Formatted with goimports"
            else:
                return False, f"goimports error: {result.stderr}"
        except Exception as e:
            return False, f"Error running goimports: {str(e)}"
    
    def format(self) -> Tuple[bool, str]:
        """Format Go file"""
        # Try goimports first (it includes gofmt)
        success, message = self.format_with_goimports()
        if success:
            return success, message
        
        # Fall back to gofmt
        success, message = self.format_with_gofmt()
        if success:
            return success, message
        
        return False, "No Go formatter available (tried goimports, gofmt)"


class RustFormatter(LanguageFormatter):
    """Rust formatter using rustfmt"""
    
    def format(self) -> Tuple[bool, str]:
        """Format Rust file with rustfmt"""
        try:
            subprocess.run(['rustfmt', '--version'], 
                          capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "rustfmt not available"
        
        cmd = ['rustfmt', self.file_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Formatted with rustfmt"
            else:
                return False, f"rustfmt error: {result.stderr}"
        except Exception as e:
            return False, f"Error running rustfmt: {str(e)}"


class YAMLFormatter(LanguageFormatter):
    """YAML formatter using prettier"""
    
    def format(self) -> Tuple[bool, str]:
        """Format YAML file with prettier"""
        try:
            subprocess.run(['prettier', '--version'], 
                          capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "Prettier not available for YAML"
        
        # Use global prettier config if available
        config_path = self.claude_config_dir / 'javascript' / 'prettier.json'
        
        cmd = ['prettier', '--write']
        
        if config_path.exists():
            cmd.extend(['--config', str(config_path)])
        
        cmd.append(self.file_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Formatted YAML with prettier"
            else:
                return False, f"Prettier error: {result.stderr}"
        except Exception as e:
            return False, f"Error running prettier: {str(e)}"


def get_formatter_for_file(file_path: str) -> Optional[LanguageFormatter]:
    """Get the appropriate formatter based on file extension"""
    ext = Path(file_path).suffix.lower()
    
    # Python
    if ext in ['.py', '.pyw']:
        return PythonFormatter(file_path)
    
    # JavaScript/TypeScript
    elif ext in ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs']:
        return JavaScriptFormatter(file_path)
    
    # Go
    elif ext == '.go':
        return GoFormatter(file_path)
    
    # Rust
    elif ext == '.rs':
        return RustFormatter(file_path)
    
    # YAML/JSON (use prettier)
    elif ext in ['.yaml', '.yml', '.json']:
        return YAMLFormatter(file_path)
    
    # C/C++ could be added with clang-format
    # Other languages can be added as needed
    
    return None


def main():
    """Main entry point for the auto-formatter hook"""
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
    
    # Get formatter for the file type
    formatter = get_formatter_for_file(file_path)
    
    if not formatter:
        # No formatter for this file type
        print(json.dumps({"action": "continue"}))
        return
    
    # Run formatting
    success, message = formatter.format()
    
    # Log result to stderr (won't interfere with stdout JSON)
    if success:
        sys.stderr.write(f"✅ Auto-format: {file_path} - {message}\n")
    else:
        # Don't log failures for unavailable formatters (too noisy)
        if "not available" not in message.lower():
            sys.stderr.write(f"⚠️ Auto-format failed: {file_path} - {message}\n")
    
    # Always continue (non-blocking)
    print(json.dumps({"action": "continue"}))


if __name__ == "__main__":
    main()