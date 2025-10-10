#!/usr/bin/env bash
# Auto-format hook for Claude Code
# Triggers on Write|Edit|MultiEdit|NotebookEdit|Update
# Runs appropriate formatter based on file extension

set -euo pipefail

# Parse JSON input from stdin
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty')

# Exit if no file path found
[[ -z "$file_path" ]] && exit 0

# Get file extension
ext="${file_path##*.}"

case "$ext" in
  py)
    # Python: ruff format
    ruff format --config ~/.claude/configs/python/ruff.toml "$file_path" 2>&1
    exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
      echo "Ruff formatting failed for $file_path"
      exit 2  # Block on failure
    fi
    ;;

  js|jsx|ts|tsx)
    # JavaScript/TypeScript: prettier
    prettier --config ~/.claude/configs/javascript/prettier.json --write "$file_path" 2>&1
    exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
      echo "Prettier formatting failed for $file_path"
      exit 2
    fi
    ;;

  go)
    # Go: gofmt (built-in, always available)
    gofmt -w "$file_path" 2>&1
    exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
      echo "gofmt formatting failed for $file_path"
      exit 2
    fi
    ;;

  *)
    # No formatter for this extension, silently succeed
    exit 0
    ;;
esac

exit 0
