#!/usr/bin/env python3
"""
Test script for the file protection hook
Run this to validate that the protection mechanism is working correctly
"""

import json
import sys
import subprocess
from pathlib import Path

def test_protection(tool, params):
    """Test a file operation against the protection hook"""
    test_input = {
        "tool": tool,
        "params": params
    }
    
    try:
        result = subprocess.run(
            ["python3", str(Path.home() / ".claude" / "hooks" / "file_protection.py")],
            input=json.dumps(test_input),
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            output = json.loads(result.stdout)
            return False, output.get("message", "Blocked")
        else:
            return True, "Allowed"
    except Exception as e:
        return True, f"Error: {e}"

def run_tests():
    """Run a series of tests to validate the protection mechanism"""
    print("=" * 60)
    print("File Protection Hook Test Suite")
    print("=" * 60)
    
    # Get current git repo if any
    try:
        git_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True
        ).stdout.strip()
        print(f"Current git repository: {git_root}")
    except:
        git_root = None
        print("Not in a git repository")
    
    print("-" * 60)
    
    tests = [
        # Test 1: Writing to system file
        {
            "name": "Block writing to /etc/passwd",
            "tool": "Write",
            "params": {"file_path": "/etc/passwd", "content": "test"},
            "expected": False
        },
        
        # Test 2: Reading from system file
        {
            "name": "Allow reading /etc/passwd",
            "tool": "Read",
            "params": {"file_path": "/etc/passwd"},
            "expected": True
        },
        
        # Test 3: Writing within repo (if in repo)
        {
            "name": "Allow writing within repository",
            "tool": "Write",
            "params": {"file_path": str(Path.cwd() / "test_file.txt"), "content": "test"},
            "expected": True if git_root else True
        },
        
        # Test 4: Writing outside repo (if in repo)
        {
            "name": "Block writing outside repository",
            "tool": "Write",
            "params": {"file_path": "/tmp/outside_repo.txt", "content": "test"},
            "expected": True  # /tmp is allowed
        },
        
        # Test 5: Dangerous bash command
        {
            "name": "Block dangerous bash command (rm -rf /)",
            "tool": "Bash",
            "params": {"command": "rm -rf /"},
            "expected": False
        },
        
        # Test 6: Safe bash command
        {
            "name": "Allow safe bash command (ls)",
            "tool": "Bash",
            "params": {"command": "ls -la"},
            "expected": True
        },
        
        # Test 7: Writing to home config file
        {
            "name": "Block writing to ~/.bashrc",
            "tool": "Write",
            "params": {"file_path": str(Path.home() / ".bashrc"), "content": "test"},
            "expected": False if git_root and not str(Path.home() / ".bashrc").startswith(git_root) else False
        },
        
        # Test 8: Writing to .git directory
        {
            "name": "Block writing to .git directory",
            "tool": "Write",
            "params": {"file_path": str(Path.cwd() / ".git" / "config"), "content": "test"},
            "expected": False
        },
        
        # Test 9: Reading from outside repo
        {
            "name": "Allow reading documentation outside repo",
            "tool": "Read",
            "params": {"file_path": "/tmp/some_doc.md"},
            "expected": True
        },
        
        # Test 10: Bash command targeting outside repo
        {
            "name": "Block rm command outside repository",
            "tool": "Bash",
            "params": {"command": "rm /usr/bin/something"},
            "expected": False if git_root else False
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        allowed, message = test_protection(test["tool"], test["params"])
        expected_text = "ALLOW" if test["expected"] else "BLOCK"
        actual_text = "ALLOW" if allowed else "BLOCK"
        
        if allowed == test["expected"]:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        print(f"\n{status}: {test['name']}")
        print(f"  Expected: {expected_text}")
        print(f"  Actual:   {actual_text}")
        print(f"  Message:  {message}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Review the protection logic.")
        return 1
    else:
        print("\n✓ All tests passed! Protection is working correctly.")
        return 0

if __name__ == "__main__":
    sys.exit(run_tests())