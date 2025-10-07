#!/bin/bash
#
# GitLab API Helper Functions
# Reads credentials from ~/.claude/.credentials.json
# Auto-detects project from git remote
#

set -eo pipefail

# Color output helpers
_red() { echo -e "\033[0;31m$*\033[0m" >&2; }
_green() { echo -e "\033[0;32m$*\033[0m" >&2; }
_yellow() { echo -e "\033[0;33m$*\033[0m" >&2; }

# Load credentials from ~/.claude/.credentials.json
_load_gitlab_credentials() {
    local creds_file="$HOME/.claude/.credentials.json"

    if [[ ! -f "$creds_file" ]]; then
        _red "ERROR: Credentials file not found: $creds_file"
        return 1
    fi

    # Extract GitLab token and API URL
    GITLAB_TOKEN=$(jq -r '.mcp.gitlab.token // empty' "$creds_file")
    GITLAB_API_URL=$(jq -r '.mcp.gitlab.api_url // empty' "$creds_file")

    if [[ -z "$GITLAB_TOKEN" ]]; then
        _red "ERROR: GitLab token not found in $creds_file"
        _yellow "Add to .mcp.gitlab.token in credentials file"
        return 1
    fi

    if [[ -z "$GITLAB_API_URL" ]]; then
        GITLAB_API_URL="https://gitlab.com/api/v4"
        _yellow "Using default API URL: $GITLAB_API_URL"
    fi

    export GITLAB_TOKEN GITLAB_API_URL
}

# Get project ID from git remote
_get_project_id() {
    local remote_url
    remote_url=$(git remote get-url origin 2>/dev/null || echo "")

    if [[ -z "$remote_url" ]]; then
        _red "ERROR: Not in a git repository or no origin remote"
        return 1
    fi

    # Extract namespace/project from various URL formats
    # git@gitlab.com:fortressinfosec/m32rimm.git
    # https://gitlab.com/fortressinfosec/m32rimm.git
    local project_path
    project_path=$(echo "$remote_url" | sed -E 's|.*[:/]([^/]+/[^/]+)(\.git)?$|\1|' | sed 's/\.git$//')

    if [[ -z "$project_path" ]]; then
        _red "ERROR: Could not extract project path from: $remote_url"
        return 1
    fi

    # URL-encode the project path (replace / with %2F)
    local encoded_path="${project_path//\//%2F}"

    # Query GitLab API for project ID
    local response
    response=$(curl -s --fail --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "$GITLAB_API_URL/projects/$encoded_path" 2>&1)

    if [[ $? -ne 0 ]]; then
        _red "ERROR: Failed to get project ID for: $project_path"
        _yellow "Response: $response"
        return 1
    fi

    GITLAB_PROJECT_ID=$(echo "$response" | jq -r '.id // empty')

    if [[ -z "$GITLAB_PROJECT_ID" ]]; then
        _red "ERROR: Could not extract project ID from API response"
        return 1
    fi

    export GITLAB_PROJECT_ID
    _green "✓ Found project: $project_path (ID: $GITLAB_PROJECT_ID)"
}

# Initialize GitLab helpers (call this first)
gitlab_init() {
    _load_gitlab_credentials || return 1
    _get_project_id || return 1
}

# Get MR by source/target branch
gitlab_get_mr_by_branch() {
    local source_branch=$1
    local target_branch=${2:-develop}

    if [[ -z "$GITLAB_PROJECT_ID" ]]; then
        _red "ERROR: Run gitlab_init first"
        return 1
    fi

    curl -s --fail --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "$GITLAB_API_URL/projects/$GITLAB_PROJECT_ID/merge_requests?\
source_branch=$source_branch&target_branch=$target_branch&state=opened"
}

# Get MR details by IID
gitlab_get_mr_details() {
    local mr_iid=$1

    if [[ -z "$GITLAB_PROJECT_ID" ]]; then
        _red "ERROR: Run gitlab_init first"
        return 1
    fi

    curl -s --fail --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "$GITLAB_API_URL/projects/$GITLAB_PROJECT_ID/merge_requests/$mr_iid"
}

# Get MR changes (diff)
gitlab_get_mr_changes() {
    local mr_iid=$1

    if [[ -z "$GITLAB_PROJECT_ID" ]]; then
        _red "ERROR: Run gitlab_init first"
        return 1
    fi

    curl -s --fail --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "$GITLAB_API_URL/projects/$GITLAB_PROJECT_ID/merge_requests/$mr_iid/changes"
}

# Get MR commits
gitlab_get_mr_commits() {
    local mr_iid=$1

    if [[ -z "$GITLAB_PROJECT_ID" ]]; then
        _red "ERROR: Run gitlab_init first"
        return 1
    fi

    curl -s --fail --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "$GITLAB_API_URL/projects/$GITLAB_PROJECT_ID/merge_requests/$mr_iid/commits"
}

# Get file contents from specific branch
gitlab_get_file() {
    local file_path=$1
    local branch=${2:-develop}

    if [[ -z "$GITLAB_PROJECT_ID" ]]; then
        _red "ERROR: Run gitlab_init first"
        return 1
    fi

    # URL-encode file path
    local encoded_path="${file_path//\//%2F}"

    curl -s --fail --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "$GITLAB_API_URL/projects/$GITLAB_PROJECT_ID/repository/files/$encoded_path/raw?ref=$branch"
}

# Find MR for ticket (searches by branch name containing ticket)
gitlab_find_mr_for_ticket() {
    local ticket=$1
    local target_branch=${2:-develop}

    if [[ -z "$GITLAB_PROJECT_ID" ]]; then
        _red "ERROR: Run gitlab_init first"
        return 1
    fi

    # Search for open MRs targeting the branch
    local mrs
    mrs=$(curl -s --fail --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "$GITLAB_API_URL/projects/$GITLAB_PROJECT_ID/merge_requests?\
target_branch=$target_branch&state=opened")

    # Filter for MRs where source_branch contains ticket
    # Clean control characters except newline/tab before processing with jq
    echo "$mrs" | tr -d '\000-\010\013-\037' | jq --arg ticket "$ticket" \
        '[.[] | select(.source_branch | contains($ticket))] | .[0] // null'
}

# Print available functions
gitlab_help() {
    cat <<'EOF'
GitLab Helper Functions
=======================

Setup:
  gitlab_init                              Initialize credentials and project

MR Operations:
  gitlab_get_mr_by_branch <source> [target]    Get MR by branch names
  gitlab_find_mr_for_ticket <ticket> [target]  Find MR containing ticket in branch name
  gitlab_get_mr_details <mr_iid>               Get MR details by IID
  gitlab_get_mr_changes <mr_iid>               Get MR diff/changes
  gitlab_get_mr_commits <mr_iid>               Get MR commits

File Operations:
  gitlab_get_file <path> [branch]              Get file contents from branch

Examples:
  gitlab_init
  gitlab_find_mr_for_ticket INT-3930 develop
  gitlab_get_mr_details 123
  gitlab_get_mr_changes 123 | jq '.changes[0].diff'

Environment:
  GITLAB_TOKEN         - Auto-loaded from ~/.claude/.credentials.json
  GITLAB_API_URL       - Auto-loaded (default: https://gitlab.com/api/v4)
  GITLAB_PROJECT_ID    - Auto-detected from git remote
EOF
}

# Auto-initialize if sourced (but allow errors to be handled)
if [[ "${BASH_SOURCE[0]:-}" != "${0}" ]]; then
    # Script is being sourced
    gitlab_init 2>/dev/null || true
fi
