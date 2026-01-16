#!/bin/bash

# Claude Code statusLine - clean metrics display

input=$(cat)

# Colors
C_RESET=$(printf '\033[0m')
C_DIM=$(printf '\033[38;5;245m')       # Gray for text
C_CHARCOAL=$(printf '\033[38;5;238m')  # Charcoal for * separators
C_DARK_GREEN=$(printf '\033[38;5;22m') # Hacker terminal green for separators
C_MAGENTA=$(printf '\033[38;5;201m')   # Workspace
C_BLUE=$(printf '\033[38;5;67m')       # Context (low) - medium dark blue
C_YELLOW=$(printf '\033[38;5;226m')    # Context (mid)
C_RED=$(printf '\033[38;5;203m')       # Context (high)

# Extract data
MODEL=$(echo "$input" | jq -r '.model.display_name // "?"')
CWD=$(echo "$input" | jq -r '.workspace.current_dir // "."')
VERSION=$(echo "$input" | jq -r '.version // "?"')

# Git info and smart directory display
GIT_BRANCH=""
if git -C "$CWD" rev-parse --git-dir > /dev/null 2>&1; then
    GIT_BRANCH=$(git -C "$CWD" branch 2>/dev/null | grep '^*' | colrm 1 2)
    GIT_ROOT=$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null)
    # Show path relative to git root
    CURRENT_DIR="${CWD#$GIT_ROOT}"
    CURRENT_DIR="${CURRENT_DIR#/}"  # Remove leading slash
    [ -z "$CURRENT_DIR" ] && CURRENT_DIR=$(basename "$GIT_ROOT")  # At root, show repo name
else
    # Not in git: show relative to home with ~
    CURRENT_DIR="${CWD/#$HOME/\~}"
fi

# Cost
COST_USD=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
COST_FMT=$(printf "%.4f" "$COST_USD")
LINES_ADDED=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
LINES_REMOVED=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')

# Context
CTX_SIZE=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')
TOTAL_IN=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
TOTAL_OUT=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
CTX_USED=$((TOTAL_IN + TOTAL_OUT))
[ "$CTX_SIZE" -gt 0 ] && CTX_PERCENT=$((CTX_USED * 100 / CTX_SIZE)) || CTX_PERCENT=0

# Format tokens
format_k() {
    local n=$1
    if [ "$n" -ge 1000 ]; then
        echo "$(echo "scale=1; $n / 1000" | bc)k"
    else
        echo "$n"
    fi
}
TOTAL_IN_FMT=$(format_k "$TOTAL_IN")
TOTAL_OUT_FMT=$(format_k "$TOTAL_OUT")

# Context color based on usage
if [ "$CTX_PERCENT" -lt 50 ]; then
    CTX_COLOR="$C_BLUE"
elif [ "$CTX_PERCENT" -lt 80 ]; then
    CTX_COLOR="$C_YELLOW"
else
    CTX_COLOR="$C_RED"
fi

# Separators
SEP="${C_DARK_GREEN}◇${C_RESET}"
STAR="${C_DIM}*${C_RESET}"

# Build sections (all gray, charcoal * separators)
S="${C_CHARCOAL}*${C_DIM}"  # charcoal star then back to gray
SEC_WORKSPACE="${C_DIM}${CURRENT_DIR}${C_RESET}"
SEC_CONTEXT="${C_DIM}▤ ${CTX_PERCENT}%${C_RESET}"
SEC_META="${C_DIM}${MODEL} ${S} v${VERSION}${C_RESET}"
SEC_COST="${C_DIM}+${LINES_ADDED}/-${LINES_REMOVED} ${S} \$${COST_FMT}${C_RESET}"

# Build git section (only if branch exists)
if [ -n "$GIT_BRANCH" ]; then
    SEC_GIT="${C_DIM}${GIT_BRANCH}${C_RESET}"
    printf "%s" "${C_DARK_GREEN}«${C_RESET} ${SEC_WORKSPACE} ${SEP} ${SEC_GIT} ${SEP} ${SEC_CONTEXT} ${SEP} ${SEC_META} ${SEP} ${SEC_COST} ${C_DARK_GREEN}»${C_RESET}"
else
    printf "%s" "${C_DARK_GREEN}«${C_RESET} ${SEC_WORKSPACE} ${SEP} ${SEC_CONTEXT} ${SEP} ${SEC_META} ${SEP} ${SEC_COST} ${C_DARK_GREEN}»${C_RESET}"
fi
