#!/usr/bin/env python3
"""
Pre-flight Validation Hook for Claude Code
Ensures proper virtual environments and installs quality tools
"""

import os
import sys
import json
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class PreflightValidator:
    def __init__(self, working_directory: str):
        self.working_directory = Path(working_directory)
        self.project_hash = hashlib.md5(str(self.working_directory).encode()).hexdigest()
        
        # User directories
        self.claude_home = Path.home() / '.claude'
        self.prefs_dir = self.claude_home / 'preferences'
        self.project_prefs_file = self.prefs_dir / 'projects' / f'{self.project_hash}.json'
        self.cache_dir = self.claude_home / 'preflight'
        self.cache_file = self.cache_dir / f'{self.project_hash}.json'
        self.quality_tools_dir = self.claude_home / 'quality-tools'
        
        # Create directories
        self.prefs_dir.mkdir(parents=True, exist_ok=True)
        (self.prefs_dir / 'projects').mkdir(exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.quality_tools_dir.mkdir(parents=True, exist_ok=True)
        
        self.preferences = self.load_preferences()
        self.validation_cache = self.load_cache()
        
    def load_preferences(self) -> dict:
        """Load project preferences"""
        if self.project_prefs_file.exists():
            try:
                with open(self.project_prefs_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_preferences(self):
        """Save project preferences"""
        self.project_prefs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.project_prefs_file, 'w') as f:
            json.dump(self.preferences, f, indent=2)
    
    def load_cache(self) -> dict:
        """Load validation cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    # Check if cache is still valid (< 7 days old)
                    import time
                    if time.time() - cache.get('timestamp', 0) < 604800:
                        return cache
            except:
                pass
        return {}
    
    def save_cache(self):
        """Save validation cache"""
        import time
        self.validation_cache['timestamp'] = time.time()
        with open(self.cache_file, 'w') as f:
            json.dump(self.validation_cache, f, indent=2)
    
    def detect_languages(self) -> List[str]:
        """Detect programming languages in the project"""
        languages = []
        
        # Python detection
        if any(self.working_directory.glob(pattern) for pattern in [
            'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 
            'environment.yml', '*.py'
        ]):
            languages.append('python')
        
        # JavaScript/TypeScript detection
        if any(self.working_directory.glob(pattern) for pattern in [
            'package.json', 'yarn.lock', 'pnpm-lock.yaml', '*.js', '*.jsx', '*.ts', '*.tsx'
        ]):
            languages.append('javascript')
        
        # Go detection
        if any(self.working_directory.glob(pattern) for pattern in [
            'go.mod', 'go.sum', '*.go'
        ]):
            languages.append('go')
        
        # Ruby detection
        if any(self.working_directory.glob(pattern) for pattern in [
            'Gemfile', '*.rb'
        ]):
            languages.append('ruby')
        
        # Rust detection
        if any(self.working_directory.glob(pattern) for pattern in [
            'Cargo.toml', '*.rs'
        ]):
            languages.append('rust')
        
        return languages
    
    def validate_python_environment(self) -> Tuple[bool, str, Dict]:
        """Validate Python virtual environment"""
        print("🐍 Checking Python environment...")
        
        # Check if we already have venv configured
        if 'python' in self.preferences:
            venv_path = Path(self.preferences['python'].get('venv_path', ''))
            if venv_path.exists() and (venv_path / 'bin' / 'python').exists():
                print(f"✅ Using configured virtual environment: {venv_path}")
                return True, "", self.preferences['python']
        
        # Check if we're already in a virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            venv_path = sys.prefix
            print(f"✅ Already in virtual environment: {venv_path}")
            python_config = {
                'venv_path': venv_path,
                'venv_type': 'venv',
                'python_binary': os.path.join(venv_path, 'bin', 'python'),
                'pip_binary': os.path.join(venv_path, 'bin', 'pip'),
                'activation_command': f"source {venv_path}/bin/activate"
            }
            self.preferences['python'] = python_config
            self.save_preferences()
            return True, "", python_config
        
        # Check for common venv directories
        for venv_dir in ['venv', '.venv', 'env', '.env']:
            venv_path = self.working_directory / venv_dir
            if venv_path.exists() and (venv_path / 'bin' / 'python').exists():
                print(f"✅ Found virtual environment: {venv_path}")
                python_config = {
                    'venv_path': str(venv_path),
                    'venv_type': 'venv',
                    'python_binary': str(venv_path / 'bin' / 'python'),
                    'pip_binary': str(venv_path / 'bin' / 'pip'),
                    'activation_command': f"source {venv_path}/bin/activate"
                }
                self.preferences['python'] = python_config
                self.save_preferences()
                return True, "", python_config
        
        # Check for Poetry
        if (self.working_directory / 'poetry.lock').exists():
            try:
                result = subprocess.run(['poetry', 'env', 'info', '--path'], 
                                      capture_output=True, text=True, cwd=self.working_directory)
                if result.returncode == 0:
                    venv_path = result.stdout.strip()
                    print(f"✅ Found Poetry environment: {venv_path}")
                    python_config = {
                        'venv_path': venv_path,
                        'venv_type': 'poetry',
                        'python_binary': 'poetry run python',
                        'pip_binary': 'poetry add',
                        'activation_command': 'poetry shell'
                    }
                    self.preferences['python'] = python_config
                    self.save_preferences()
                    return True, "", python_config
            except FileNotFoundError:
                pass
        
        # Check for Pipenv
        if (self.working_directory / 'Pipfile').exists():
            try:
                result = subprocess.run(['pipenv', '--venv'], 
                                      capture_output=True, text=True, cwd=self.working_directory)
                if result.returncode == 0:
                    venv_path = result.stdout.strip()
                    print(f"✅ Found Pipenv environment: {venv_path}")
                    python_config = {
                        'venv_path': venv_path,
                        'venv_type': 'pipenv',
                        'python_binary': 'pipenv run python',
                        'pip_binary': 'pipenv install',
                        'activation_command': 'pipenv shell'
                    }
                    self.preferences['python'] = python_config
                    self.save_preferences()
                    return True, "", python_config
            except FileNotFoundError:
                pass
        
        # No virtual environment found
        error_msg = """
❌ Python Virtual Environment Required

No virtual environment detected for this Python project.
Virtual environments are REQUIRED to avoid polluting your system Python.

Please create and activate a virtual environment:

Option 1 - Standard venv (Recommended):
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\\Scripts\\activate

Option 2 - Poetry:
    poetry install
    poetry shell

Option 3 - Pipenv:
    pipenv install
    pipenv shell

Option 4 - Conda:
    conda create -n myproject python=3.9
    conda activate myproject

After creating the environment, run this command again.
Your environment choice will be saved for future sessions.
"""
        return False, error_msg, {}
    
    def install_python_tools(self, python_config: Dict) -> bool:
        """Install Python quality tools in the virtual environment
        
        Tool hierarchy:
        - Formatting: ruff (primary), black (fallback only)
        - Complexity: radon (cyclomatic), cognitive_complexity (understandability)
        - Dead code: vulture
        - Type checking: mypy
        """
        print("📦 Installing Python quality tools...")
        
        # Note: ruff is the primary formatter, black is fallback only
        tools = ['radon', 'flake8-cognitive-complexity', 'vulture', 'ruff', 'black', 'mypy']
        pip_cmd = python_config.get('pip_binary', 'pip')
        
        # Handle different venv types
        if python_config.get('venv_type') == 'poetry':
            # Poetry uses 'add' for dependencies
            for tool in tools:
                try:
                    subprocess.run(['poetry', 'add', '--dev', tool], 
                                 capture_output=True, timeout=30, cwd=self.working_directory)
                except:
                    print(f"  ⚠️  Failed to install {tool}, continuing...")
        elif python_config.get('venv_type') == 'pipenv':
            # Pipenv uses 'install' for dependencies
            for tool in tools:
                try:
                    subprocess.run(['pipenv', 'install', '--dev', tool], 
                                 capture_output=True, timeout=30, cwd=self.working_directory)
                except:
                    print(f"  ⚠️  Failed to install {tool}, continuing...")
        else:
            # Standard pip install
            try:
                cmd = [pip_cmd, 'install'] + tools
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    print(f"  ✅ Installed: {', '.join(tools)}")
                    return True
                else:
                    print(f"  ⚠️  Some tools failed to install, continuing with available tools")
            except:
                print(f"  ⚠️  Failed to install tools, will use fallback patterns")
        
        return False
    
    def install_javascript_tools(self) -> bool:
        """Install JavaScript quality tools"""
        print("📦 Checking JavaScript tools...")
        
        # Check if package.json exists
        if not (self.working_directory / 'package.json').exists():
            print("  ℹ️  No package.json found, skipping JS tool installation")
            return False
        
        # Check package manager
        if (self.working_directory / 'yarn.lock').exists():
            pkg_manager = 'yarn'
        elif (self.working_directory / 'pnpm-lock.yaml').exists():
            pkg_manager = 'pnpm'
        else:
            pkg_manager = 'npm'
        
        # Check if tools already installed
        try:
            with open(self.working_directory / 'package.json', 'r') as f:
                package_json = json.load(f)
                dev_deps = package_json.get('devDependencies', {})
                deps = package_json.get('dependencies', {})
                all_deps = {**deps, **dev_deps}
                
                if 'eslint' in all_deps:
                    print("  ✅ ESLint already installed")
                    return True
        except:
            pass
        
        # Try to install as dev dependencies
        print(f"  📦 Installing ESLint with {pkg_manager}...")
        try:
            if pkg_manager == 'yarn':
                cmd = ['yarn', 'add', '--dev', 'eslint', 'prettier']
            elif pkg_manager == 'pnpm':
                cmd = ['pnpm', 'add', '-D', 'eslint', 'prettier']
            else:
                cmd = ['npm', 'install', '--save-dev', 'eslint', 'prettier']
            
            result = subprocess.run(cmd, capture_output=True, timeout=60, cwd=self.working_directory)
            if result.returncode == 0:
                print(f"  ✅ Installed JavaScript tools")
                return True
        except:
            print(f"  ⚠️  Failed to install JS tools, will use fallback patterns")
        
        return False
    
    def install_go_tools(self) -> bool:
        """Install Go quality tools"""
        print("📦 Installing Go tools...")
        
        tools = [
            'github.com/fzipp/gocyclo/cmd/gocyclo@latest',
            'github.com/golangci/golangci-lint/cmd/golangci-lint@latest',
            'honnef.co/go/tools/cmd/staticcheck@latest'
        ]
        
        for tool in tools:
            try:
                result = subprocess.run(['go', 'install', tool], 
                                      capture_output=True, timeout=30)
                if result.returncode == 0:
                    tool_name = tool.split('/')[-1].split('@')[0]
                    print(f"  ✅ Installed {tool_name}")
            except:
                print(f"  ⚠️  Failed to install {tool}, continuing...")
        
        return True
    
    def validate_and_setup(self) -> Tuple[bool, str]:
        """Main validation and setup function"""
        print(f"\n🚀 Pre-flight Validation for {self.working_directory}\n")
        
        # Detect languages
        languages = self.detect_languages()
        if not languages:
            print("⚠️  No recognized programming languages detected")
            return True, ""
        
        print(f"🔍 Detected languages: {', '.join(languages)}")
        
        errors = []
        
        # Validate Python environment if Python detected
        if 'python' in languages:
            success, error_msg, python_config = self.validate_python_environment()
            if not success:
                return False, error_msg
            
            # Try to install Python tools
            if python_config:
                self.install_python_tools(python_config)
        
        # Install JavaScript tools if needed
        if 'javascript' in languages:
            self.install_javascript_tools()
        
        # Install Go tools if needed
        if 'go' in languages:
            self.install_go_tools()
        
        # Save successful validation to cache
        self.validation_cache['languages'] = languages
        self.validation_cache['validated'] = True
        self.save_cache()
        
        print("\n✅ Pre-flight validation complete!\n")
        return True, ""

def validate_project(working_directory: str) -> Tuple[bool, str]:
    """Entry point for pre-flight validation"""
    validator = PreflightValidator(working_directory)
    return validator.validate_and_setup()

if __name__ == "__main__":
    # Can be run standalone for testing
    import sys
    if len(sys.argv) > 1:
        working_dir = sys.argv[1]
    else:
        working_dir = os.getcwd()
    
    success, error = validate_project(working_dir)
    if not success:
        print(error)
        sys.exit(1)
    sys.exit(0)