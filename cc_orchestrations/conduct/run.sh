#!/bin/bash
# Wrapper to run conduct orchestrator
# Usage: ./run.sh [options] [command]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run the Python module
exec python3 -m conduct "$@"
