#!/bin/bash

# Claude Code statusLine script matching custom zsh prompt style
# Format: (venv) [user:host]:(git-branch):curr_dir
# Your actual prompt: (py3.13)[randy:Nexus]::~$
# Colors: venv=orange(214), user=green, host=blue, git=dark_gray(8), dir=magenta

# Read JSON input from stdin
input=$(cat)

# Extract current working directory from JSON
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // "."')

# Function to get git branch
get_git_branch() {
    if [ -d "$cwd/.git" ]; then
        cd "$cwd" 2>/dev/null || return
        git branch 2>/dev/null | grep '^*' | cut -c3- 2>/dev/null
    fi
}

# Define colors using printf format (more reliable than echo -e)
# These match your zsh colors exactly
COLOR_ORANGE=$(printf '\033[38;5;214m')  # venv - matches zsh %F{214}
COLOR_GREEN=$(printf '\033[32m')          # user - matches zsh %F{green}
COLOR_BLUE=$(printf '\033[34m')           # host - matches zsh %F{blue}
COLOR_DARK_GRAY=$(printf '\033[38;5;8m')  # git - matches zsh %F{8}
COLOR_MAGENTA=$(printf '\033[35m')        # dir - matches zsh %F{magenta}
COLOR_RESET=$(printf '\033[0m')           # reset

# Get components
username=$(whoami)
hostname_short=$(hostname)
git_branch=$(get_git_branch)
current_dir=$(basename "$cwd")

# Special case for home directory
if [ "$cwd" = "$HOME" ]; then
    current_dir="~"
fi

# Build status line with colors
status_line=""

# Add virtualenv if present (orange)
if [[ -n "$VIRTUAL_ENV" ]]; then
    venv_name=$(basename "$VIRTUAL_ENV")
    status_line="${COLOR_ORANGE}(${venv_name})${COLOR_RESET} "
fi

# Add [user:host] with green user and blue host
status_line="${status_line}[${COLOR_GREEN}${username}${COLOR_RESET}:${COLOR_BLUE}${hostname_short}${COLOR_RESET}]"

# Add git branch (dark gray) or extra colon
if [[ -n "$git_branch" ]]; then
    status_line="${status_line}:${COLOR_DARK_GRAY}${git_branch}${COLOR_RESET}"
else
    status_line="${status_line}:"
fi

# Add current directory (magenta)
status_line="${status_line}:${COLOR_MAGENTA}${current_dir}${COLOR_RESET}"

# Output without trailing newline
printf "%s" "$status_line"