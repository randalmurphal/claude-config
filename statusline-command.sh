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

# Context (pre-calculated percentage from Claude Code)
CTX_PERCENT=$(echo "$input" | jq -r '.context_window.used_percentage // 0 | floor')

# Rate limits (Pro/Max only; absent before first API response of session)
RAW_5HR=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
RAW_7D=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
if [ -n "$RAW_5HR" ]; then
    RATE_5HR=$(printf "%.0f%%" "$RAW_5HR")
else
    RATE_5HR="-"
fi
if [ -n "$RAW_7D" ]; then
    RATE_7D=$(printf "%.0f%%" "$RAW_7D")
else
    RATE_7D="-"
fi

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

# Build sections
SEC_WORKSPACE="${C_DIM}${CURRENT_DIR}${C_RESET}"
SEC_MODEL="${C_DIM}${MODEL}${C_RESET}"
SEC_VERSION="${C_DIM}v${VERSION}${C_RESET}"
SEC_CONTEXT="${C_DIM}▤ ${CTX_PERCENT}%${C_RESET}"
SEC_5HR="${C_DIM}5h ${RATE_5HR}${C_RESET}"
SEC_7D="${C_DIM}7d ${RATE_7D}${C_RESET}"
SEC_COST="${C_DIM}\$${COST_FMT}${C_RESET}"

# Build output (with or without git)
if [ -n "$GIT_BRANCH" ]; then
    SEC_GIT="${C_DIM}${GIT_BRANCH}${C_RESET}"
    printf "%s" "${C_DARK_GREEN}«${C_RESET} ${SEC_WORKSPACE} ${SEP} ${SEC_GIT} ${SEP} ${SEC_MODEL} ${SEP} ${SEC_VERSION} ${SEP} ${SEC_CONTEXT} ${SEP} ${SEC_5HR} ${SEP} ${SEC_7D} ${SEP} ${SEC_COST} ${C_DARK_GREEN}»${C_RESET}"
else
    printf "%s" "${C_DARK_GREEN}«${C_RESET} ${SEC_WORKSPACE} ${SEP} ${SEC_MODEL} ${SEP} ${SEC_VERSION} ${SEP} ${SEC_CONTEXT} ${SEP} ${SEC_5HR} ${SEP} ${SEC_7D} ${SEP} ${SEC_COST} ${C_DARK_GREEN}»${C_RESET}"
fi
