#!/usr/bin/env python3
"""
PRISM HTTP Server Auto-Start Hook
Ensures PRISM HTTP server is running when Claude Code starts.
"""

import subprocess
import time
import requests
import os
import sys
import json
from pathlib import Path

def is_http_server_running(port=8090):
    """Check if PRISM HTTP server is already running."""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            # Check all services are healthy
            return all(data.get("services", {}).values())
    except:
        pass
    return False

def start_http_server():
    """Start the PRISM HTTP server in background."""
    server_script = Path("/home/rmurphy/repos/claude_mcp/prism_mcp/bin/prism-http-server")

    if not server_script.exists():
        print(f"Warning: PRISM HTTP server script not found at {server_script}", file=sys.stderr)
        return False

    try:
        # Start server as background process
        process = subprocess.Popen(
            [str(server_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach from parent process
        )

        # Give it time to start
        time.sleep(5)

        # Check if it started successfully
        if is_http_server_running():
            print("✓ PRISM HTTP server started successfully", file=sys.stderr)
            return True
        else:
            print("Warning: PRISM HTTP server started but not responding", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error starting PRISM HTTP server: {e}", file=sys.stderr)
        return False

def main():
    """Main hook handler for SessionStart event."""
    # Read the hook input
    try:
        input_data = json.loads(sys.stdin.read())
        event_name = input_data.get("hook_event_name")

        # Only run on SessionStart
        if event_name != "SessionStart":
            # Pass through - not our event
            print(json.dumps({"action": "continue"}))
            return

    except:
        # If we can't parse input, just pass through
        print(json.dumps({"action": "continue"}))
        return

    # Check if HTTP server is running
    if is_http_server_running():
        print("✓ PRISM HTTP server already running", file=sys.stderr)
    else:
        print("Starting PRISM HTTP server...", file=sys.stderr)
        if start_http_server():
            print("✓ PRISM HTTP server ready for hooks", file=sys.stderr)
        else:
            print("⚠ PRISM HTTP server could not be started", file=sys.stderr)

    # Always allow session to continue
    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()