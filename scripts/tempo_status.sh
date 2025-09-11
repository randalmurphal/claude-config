#!/bin/bash
# Musical tempo status line for Claude
# Shows tempo based on recent git activity

get_tempo_bpm() {
    # Check git activity in last 5 minutes
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo ""
        return
    fi
    
    # Count recent commits/changes
    recent_commits=$(git log --since="5 minutes ago" --oneline 2>/dev/null | wc -l)
    staged_files=$(git diff --cached --name-only 2>/dev/null | wc -l)
    modified_files=$(git diff --name-only 2>/dev/null | wc -l)
    
    # Calculate activity score
    activity=$((recent_commits * 3 + staged_files * 2 + modified_files))
    
    # Determine BPM based on activity
    if [ $activity -eq 0 ]; then
        echo "♪ 60"   # Very slow
    elif [ $activity -le 3 ]; then
        echo "♪ 90"   # Walking pace
    elif [ $activity -le 8 ]; then
        echo "♪ 120"  # Moderate pace
    elif [ $activity -le 15 ]; then
        echo "♪ 140"  # Fast
    else
        echo "♪ 180"  # Very fast
    fi
}

get_vibe() {
    # Check for current vibe from a simple current_vibe file
    # The /vibe command will update this file
    vibe_file="$HOME/.claude/current_vibe.txt"
    
    if [ -f "$vibe_file" ]; then
        vibe=$(cat "$vibe_file")
    else
        vibe="solo"  # Default
    fi
    
    # Return icon based on vibe
    case "$vibe" in
        solo)
            echo "🎸"
            ;;
        concert)
            echo "🎭"
            ;;
        duo)
            echo "🎼"
            ;;
        mentor)
            echo "📚"
            ;;
        *)
            echo "🎸"  # Default to solo
            ;;
    esac
}

# Read input
input=$(cat)

# Extract workspace info
venv_info=""
if [[ -n "$VIRTUAL_ENV" ]]; then
    venv_info="\\033[38;5;214m($(basename "$VIRTUAL_ENV"))\\033[0m "
fi

git_branch=""
if git rev-parse --git-dir >/dev/null 2>&1; then
    git_branch="$(git branch 2>/dev/null | grep '^*' | cut -d' ' -f2-)"
fi

cwd="$(echo "$input" | jq -r '.workspace.current_dir')"
cwd_base="$(basename "$cwd")"

# Get tempo BPM and vibe
tempo=$(get_tempo_bpm)
vibe=$(get_vibe)

# Build status line with vibe and tempo
if [ -n "$vibe" ]; then
    vibe_display="${vibe} "
else
    vibe_display=""
fi

if [ -n "$tempo" ]; then
    tempo_display="\\033[36m${tempo}\\033[0m "
else
    tempo_display=""
fi

# Output formatted status line with proper escaping
# Use echo -e to interpret escape sequences, then printf to avoid newline
echo -en "${vibe_display}${tempo_display}${venv_info}[\\033[32m$(whoami)\\033[0m:\\033[34m$(hostname -s)\\033[0m]:\\033[90m${git_branch}\\033[0m:\\033[35m${cwd_base}\\033[0m"