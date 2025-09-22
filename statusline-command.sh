#!/bin/bash

# Claude Code statusLine script matching custom zsh prompt style
# Format: (venv)[user:host]:(git-branch):curr_dir
# Matches your zsh PROMPT='$(virtualenv_info)[%F{green}%n%f:%F{blue}$(hostname)%f]:%F{8}$(git_branch)%f:%F{magenta}%1~%f$ '
# Colors: venv=orange(214), user=green, host=blue, git=dark_gray(8), dir=magenta

# Read JSON input from stdin
input=$(cat)

# Extract current working directory from JSON
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // "."')

# Function to get git branch (matching your zsh git_branch function)
get_git_branch() {
    if [ -d "$cwd/.git" ] || git -C "$cwd" rev-parse --git-dir > /dev/null 2>&1; then
        git -C "$cwd" branch 2>/dev/null | grep '^*' | colrm 1 2
    fi
}

# Define colors using printf format - matching your zsh exactly
COLOR_ORANGE=$(printf '\033[38;5;214m')  # venv - matches zsh %F{214}
COLOR_GREEN=$(printf '\033[32m')          # user - matches zsh %F{green}
COLOR_BLUE=$(printf '\033[34m')           # host - matches zsh %F{blue}
COLOR_DARK_GRAY=$(printf '\033[38;5;8m')  # git - matches zsh %F{8}
COLOR_MAGENTA=$(printf '\033[35m')        # dir - matches zsh %F{magenta}
COLOR_RESET=$(printf '\033[0m')           # reset

# Get components
username=$(whoami)
hostname_short=$(hostname -s)
git_branch=$(get_git_branch)
current_dir=$(basename "$cwd")

# Special case for home directory (matches zsh %1~)
if [ "$cwd" = "$HOME" ]; then
    current_dir="~"
fi

# Build status line with colors - exact format from your zsh
status_line=""

# Add virtualenv if present (orange) - matches $(virtualenv_info)
if [[ -n "$VIRTUAL_ENV" ]]; then
    venv_name=$(basename "$VIRTUAL_ENV")
    status_line="${COLOR_ORANGE}(${venv_name})${COLOR_RESET}"
fi

# Add [user:host] with green user and blue host
status_line="${status_line}[${COLOR_GREEN}${username}${COLOR_RESET}:${COLOR_BLUE}${hostname_short}${COLOR_RESET}]"

# Add git branch (dark gray) if present
if [[ -n "$git_branch" ]]; then
    status_line="${status_line}:${COLOR_DARK_GRAY}${git_branch}${COLOR_RESET}"
else
    status_line="${status_line}:"
fi

# Add current directory (magenta)
status_line="${status_line}:${COLOR_MAGENTA}${current_dir}${COLOR_RESET}"

# Output without trailing newline (no $ at end since this isn't a shell prompt)
printf "%s" "$status_line"