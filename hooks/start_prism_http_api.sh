#!/usr/bin/env bash
# Startup hook to ensure PRISM HTTP API is running
# Checks port 8090 and starts the server if needed

PRISM_PORT=8090
LOG_FILE="$HOME/.claude/logs/prism_http_startup.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Check if port is already in use
if ss -tlnp 2>/dev/null | grep -q ":${PRISM_PORT} "; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] PRISM HTTP API already running on port ${PRISM_PORT}" >> "$LOG_FILE"
    exit 0
fi

# Start the HTTP API in the background
# Since prism_mcp is an installed Python module, we can run it from anywhere
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting PRISM HTTP API..." >> "$LOG_FILE"
nohup python3 -m prism_mcp.interfaces.http_api >> "$LOG_FILE" 2>&1 &
PRISM_PID=$!

# Wait for server to start (model loading takes ~3-5 seconds)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for server to initialize..." >> "$LOG_FILE"
for i in {1..10}; do
    sleep 1
    if ss -tlnp 2>/dev/null | grep -q ":${PRISM_PORT} "; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] PRISM HTTP API started successfully (PID: $PRISM_PID)" >> "$LOG_FILE"
        exit 0
    fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: PRISM HTTP API failed to start after 10 seconds" >> "$LOG_FILE"
exit 1