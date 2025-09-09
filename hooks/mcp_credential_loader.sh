#!/bin/bash
# MCP Credential Loader - Reads credentials from .credentials.json
# This script loads credentials and exports them as environment variables for MCP servers

# Find the .credentials.json file (using ~ for home directory)
CREDS_FILE="$HOME/.claude/.credentials.json"

# Check if credentials file exists
if [ ! -f "$CREDS_FILE" ]; then
    echo "Error: Credentials file not found at $CREDS_FILE" >&2
    exit 1
fi

# Parse the server type from command line argument
SERVER_TYPE="$1"

case "$SERVER_TYPE" in
    gitlab)
        # Extract GitLab credentials
        export GITLAB_PERSONAL_ACCESS_TOKEN=$(python3 -c "import json; data = json.load(open('$CREDS_FILE')); print(data.get('mcp', {}).get('gitlab', {}).get('token', ''))")
        export GITLAB_API_URL=$(python3 -c "import json; data = json.load(open('$CREDS_FILE')); print(data.get('mcp', {}).get('gitlab', {}).get('api_url', ''))")
        
        if [ -z "$GITLAB_PERSONAL_ACCESS_TOKEN" ]; then
            echo "Error: GitLab token not found in credentials file" >&2
            exit 1
        fi
        
        # Run GitLab MCP server
        exec npx -y gitlab-mcp@latest
        ;;
        
    jira)
        # Extract Jira credentials
        export JIRA_INSTANCE_URL=$(python3 -c "import json; data = json.load(open('$CREDS_FILE')); print(data.get('mcp', {}).get('jira', {}).get('instance_url', ''))")
        export JIRA_USER_EMAIL=$(python3 -c "import json; data = json.load(open('$CREDS_FILE')); print(data.get('mcp', {}).get('jira', {}).get('user_email', ''))")
        export JIRA_API_KEY=$(python3 -c "import json; data = json.load(open('$CREDS_FILE')); print(data.get('mcp', {}).get('jira', {}).get('api_key', ''))")
        
        if [ -z "$JIRA_API_KEY" ]; then
            echo "Error: Jira API key not found in credentials file" >&2
            exit 1
        fi
        
        # Run Jira MCP server
        exec npx -y jira-mcp@latest
        ;;
        
    mongodb)
        # Extract MongoDB credentials
        export MDB_MCP_CONNECTION_STRING=$(python3 -c "import json; data = json.load(open('$CREDS_FILE')); print(data.get('mcp', {}).get('mongodb', {}).get('connection_string', ''))")
        
        if [ -z "$MDB_MCP_CONNECTION_STRING" ]; then
            echo "Error: MongoDB connection string not found in credentials file" >&2
            exit 1
        fi
        
        # Run MongoDB MCP server
        exec npx -y mongodb-mcp-server
        ;;
        
    *)
        echo "Error: Unknown server type: $SERVER_TYPE" >&2
        echo "Usage: $0 {gitlab|jira|mongodb}" >&2
        exit 1
        ;;
esac