#!/bin/bash

# Claude Code statusLine script matching zsh prompt style
# Format: (venv) [user:host]:(git-branch):curr_dir

# Read JSON input from stdin
input=$(cat)

# Extract current working directory from JSON
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd')

# Function to get git branch (skip optional locks)
get_git_branch() {
    if [ -d "$cwd/.git" ]; then
        cd "$cwd" 2>/dev/null || return
        git branch 2>/dev/null | grep '^*' | cut -c3- 2>/dev/null
    fi
}

# Function to get virtualenv info
get_virtualenv_info() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        printf "\033[38;5;214m($(basename "$VIRTUAL_ENV"))\033[0m"
    fi
}

# Get components
venv_info=$(get_virtualenv_info)
username=$(whoami)
hostname=$(hostname -s)
git_branch=$(get_git_branch)
current_dir=$(basename "$cwd")

# Build the status line with colors matching your zsh prompt
# Format: (venv) [user:host]:(git-branch):curr_dir
status_line=""

# Add virtualenv if present
if [[ -n "$venv_info" ]]; then
    status_line="${venv_info} "
fi

# Add [user:host] with green user and blue host
status_line="${status_line}[\033[32m${username}\033[0m:\033[34m${hostname}\033[0m]"

# Add git branch if present (gray color)
if [[ -n "$git_branch" ]]; then
    status_line="${status_line}:\033[90m${git_branch}\033[0m"
fi

# Add current directory (magenta color)
status_line="${status_line}:\033[35m${current_dir}\033[0m"

# Output the final status line
printf "%s" "$status_line"