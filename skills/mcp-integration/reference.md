# MCP Integration Reference

**Complete server setup instructions, detailed troubleshooting, and advanced configurations.**

For quick reference and core concepts, see `SKILL.md`.

---

## Detailed Server Setup

### ObsidianPilot MCP - Complete Setup

**Purpose:** Direct filesystem access to Obsidian vaults with advanced search (100-1000x faster than REST API)

**Features:**
- Full-text search (SQLite FTS5 with boolean operators)
- Frontmatter property search (=, !=, >, <, contains)
- Date-based search (created/modified within X days)
- Regex search with timeout protection
- Tag search (hierarchical tags)
- Instant writes (direct filesystem, no API overhead)

**Installation Steps:**

1. **Install uv package manager:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Add to `~/.claude.json` under mcpServers:**
   ```json
   {
     "mcpServers": {
       "obsidian": {
         "type": "stdio",
         "command": "~/.local/bin/uvx",
         "args": ["obsidianpilot"],
         "env": {
           "OBSIDIAN_VAULT_PATH": "~/obsidian-notes"
         }
       }
     }
   }
   ```

3. **Vault Path Options:**
   - WSL native (`/home/user/vault`) - Fastest
   - Windows filesystem (`/mnt/c/Users/user/vault`) - Accessible from Obsidian GUI

4. **Verify:**
   ```bash
   ~/.local/bin/uvx obsidianpilot
   # Should launch without errors
   ```

**Tools Available:** 15+ tools for notes, search, tags, links
**Token Cost:** ~3k tokens

**Common Issues:**
- **Slow writes on Windows filesystem:** Expected with `/mnt/c/` paths (WSL→Windows overhead), still 100x faster than REST API
- **Vault not found:** Verify `OBSIDIAN_VAULT_PATH` points to correct directory
- **uvx command not found:** Add `~/.local/bin` to PATH: `export PATH="$HOME/.local/bin:$PATH"`

---

### Jira MCP - Complete Setup

**Purpose:** Full-featured Jira integration with JQL search and dev info (commits, PRs)

**Installation Steps:**

1. **Install globally:**
   ```bash
   npm install -g @aashari/mcp-server-atlassian-jira
   ```

2. **Generate Atlassian API token:**
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Copy token immediately (only shown once)

3. **Add via CLI (local scope - works in project subdirs):**
   ```bash
   cd /path/to/project
   claude mcp add jira mcp-atlassian-jira \
     -e ATLASSIAN_SITE_NAME=yourcompany \
     -e ATLASSIAN_USER_EMAIL=you@company.com \
     -e ATLASSIAN_API_TOKEN=your_token
   ```

4. **Verify:**
   ```bash
   claude mcp list
   # Should show: jira: mcp-atlassian-jira - ✓ Connected
   ```

**Tools Available:**
- list_projects - List all Jira projects
- search_issues - Search issues using JQL
- get_issue - Get detailed issue information
- get_dev_info - View commits, PRs, builds linked to issue

**Token Cost:** ~2.5k tokens

**Example JQL Queries:**
```jql
# Open issues assigned to current user
assignee = currentUser() AND status != Done

# High priority bugs
type = Bug AND priority = High

# Issues updated in last 7 days
updated >= -7d
```

**Common Issues:**
- **Tools not available:** Verify server added with local scope (default)
- **Site name format:** Use `yourcompany` not `yourcompany.atlassian.net`
- **Authentication failed:** Regenerate API token, update config
- **Connection timeout:** Check firewall/network access to Atlassian

---

### MongoDB MCP - Complete Setup

**Purpose:** Direct MongoDB access for queries, aggregations, CRUD operations

**Installation Steps:**

1. **Add to project (local scope):**
   ```bash
   cd /path/to/project
   claude mcp add mongodb npx -y mongodb-mcp-server \
     -e MDB_MCP_CONNECTION_STRING="mongodb://user:pass@host:port/db?authSource=admin"
   ```

2. **Connection String Format:**
   ```
   mongodb://[username:password@]host[:port]/[database][?options]
   ```

   **Examples:**
   - Local without auth: `mongodb://localhost:27017/mydb`
   - Local with auth: `mongodb://admin:pass@localhost:27017/mydb?authSource=admin`
   - Remote: `mongodb://user:pass@mongo.example.com:27017/mydb?authSource=admin`

3. **Verify connection:**
   ```bash
   mongosh "mongodb://user:pass@host:port/db?authSource=admin"
   # Should connect successfully
   ```

4. **Test MCP:**
   ```bash
   claude mcp test mongodb
   ```

**Tools Available:**
- `list-databases` - List all databases
- `list-collections` - List collections in database
- `find` - Query documents (supports filters, projection, sort, limit)
- `aggregate` - Run aggregation pipelines
- `count` - Count documents matching filter
- `insert-many` - Insert multiple documents
- `update-many` - Update documents matching filter
- `delete-many` - Delete documents matching filter
- `collection-schema` - Infer collection schema from documents

**Token Cost:** ~3k tokens

**Example Workflows:**

```bash
# Discover database structure
1. mcp__mongodb__list-databases
2. mcp__mongodb__list-collections (database: "mydb")
3. mcp__mongodb__collection-schema (database: "mydb", collection: "users")

# Query with filters
mcp__mongodb__find({
  "database": "mydb",
  "collection": "users",
  "filter": {"status": "active"},
  "limit": 10
})

# Aggregation pipeline
mcp__mongodb__aggregate({
  "database": "mydb",
  "collection": "orders",
  "pipeline": [
    {"$match": {"status": "completed"}},
    {"$group": {"_id": "$customer_id", "total": {"$sum": "$amount"}}},
    {"$sort": {"total": -1}}
  ]
})
```

**Common Issues:**
- **Connection refused:** Verify MongoDB is running (`mongosh` connection test)
- **Authentication failed:** Check username, password, authSource
- **Database not found:** List databases first to verify name
- **No results:** Check database name in connection string matches query

---

### PostgreSQL MCP - Complete Setup

**Purpose:** Query and inspect PostgreSQL databases

**Installation Steps:**

1. **Pull Docker image:**
   ```bash
   docker pull mcp/postgres
   ```

2. **Add to per-project config (`.mcp.json`):**
   ```json
   {
     "mcpServers": {
       "postgres": {
         "command": "docker",
         "args": [
           "run", "--rm", "-i", "--network", "host",
           "mcp/postgres",
           "--connection-string", "postgresql://user:pass@localhost:5432/dbname"
         ]
       }
     }
   }
   ```

3. **Connection String Format:**
   ```
   postgresql://[user[:password]@][host][:port][/dbname][?param1=value1&...]
   ```

4. **Verify connection:**
   ```bash
   psql "postgresql://user:pass@localhost:5432/dbname"
   # Should connect successfully
   ```

**Tools Available:**
- Execute SQL queries (SELECT, INSERT, UPDATE, DELETE)
- Schema inspection (list tables, columns, indexes)
- Read-only mode by default (configurable)

**Token Cost:** ~2.5k tokens

**Security Notes:**
- Default is read-only mode for safety
- Add `--read-write` flag to enable writes
- Store credentials securely (environment variables)

**Common Issues:**
- **Docker not found:** Install Docker or use nerdctl
- **Connection refused:** Check PostgreSQL is running
- **Permission denied:** Verify user has correct privileges
- **Network issues:** Ensure `--network host` in config

---

### SQLite MCP - Complete Setup

**Purpose:** Lightweight database operations and testing

**Installation Steps:**

1. **Install globally:**
   ```bash
   npm install -g @modelcontextprotocol/server-sqlite
   ```

2. **Add to per-project config:**
   ```json
   {
     "mcpServers": {
       "sqlite": {
         "command": "mcp-server-sqlite",
         "args": ["--db-path", "./data"]
       }
     }
   }
   ```

   **Path Options:**
   - `./data` - Directory containing SQLite databases
   - `./data/mydb.db` - Specific database file

3. **Verify:**
   ```bash
   sqlite3 ./data/mydb.db ".tables"
   # Should list tables
   ```

**Tools Available:**
- `read_query` - Execute SELECT queries
- `write_query` - Execute INSERT/UPDATE/DELETE
- `create_table` - Create new tables
- `list_tables` - List all tables
- `describe_table` - Show table schema
- `append_insight` - Store analysis insights

**Token Cost:** ~2.5k tokens

**Example Usage:**
```sql
-- Create table
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);

-- Insert data
INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');

-- Query
SELECT * FROM users WHERE email LIKE '%@example.com';
```

**Common Issues:**
- **Database locked:** Another process has database open
- **Database not found:** Verify `--db-path` points to correct location
- **Permission denied:** Check file permissions on database file

---

### Redis MCP - Complete Setup

**Purpose:** Key operations, cache inspection, pub/sub

**Installation Steps:**

1. **Pull Docker image:**
   ```bash
   docker pull mcp/redis
   ```

2. **Add to per-project config:**
   ```json
   {
     "mcpServers": {
       "redis": {
         "command": "docker",
         "args": [
           "run", "--rm", "-i", "--network", "host",
           "mcp/redis",
           "--url", "redis://localhost:6379"
         ]
       }
     }
   }
   ```

3. **Connection String Format:**
   ```
   redis://[:password@]host[:port][/database]
   ```

   **Examples:**
   - Local without auth: `redis://localhost:6379`
   - Local with auth: `redis://:password@localhost:6379`
   - Specific DB: `redis://localhost:6379/2`

4. **Verify connection:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

**Tools Available:**
- `get` - Get value by key
- `set` - Set key-value pair
- `delete` - Delete key
- `ttl` - Get time to live
- `expire` - Set expiration time
- `keys` - List keys matching pattern
- `publish` - Publish message to channel
- `subscribe` - Subscribe to channel

**Token Cost:** ~2k tokens

**Example Usage:**
```bash
# Set key with expiration
SET user:123 "Alice" EX 3600

# Get key
GET user:123

# List all user keys
KEYS user:*

# Set with TTL check
TTL user:123
```

**Common Issues:**
- **Connection refused:** Redis not running (`redis-cli ping` test)
- **Authentication required:** Add password to connection string
- **Wrong DB:** Specify database number in URL (`/1`, `/2`, etc.)

---

### Neo4j MCP - Complete Setup

**Purpose:** Graph database queries (Cypher, graph traversal)

**Installation Steps:**

1. **Install globally:**
   ```bash
   npm install -g @modelcontextprotocol/server-neo4j
   ```

2. **Add to per-project config:**
   ```json
   {
     "mcpServers": {
       "neo4j": {
         "command": "mcp-server-neo4j",
         "env": {
           "NEO4J_URI": "bolt://localhost:7687",
           "NEO4J_USER": "neo4j",
           "NEO4J_PASSWORD": "password"
         }
       }
     }
   }
   ```

3. **Connection String Format:**
   ```
   bolt://[username:password@]host[:port]
   neo4j://[username:password@]host[:port]
   ```

4. **Verify connection:**
   ```bash
   # Test with cypher-shell
   cypher-shell -a bolt://localhost:7687 -u neo4j -p password "RETURN 1"
   ```

**Tools Available:**
- Execute Cypher queries
- Graph traversal operations
- Node/relationship CRUD
- Path finding algorithms

**Token Cost:** ~3k tokens

**Example Cypher Queries:**
```cypher
// Find all nodes
MATCH (n) RETURN n LIMIT 25

// Create relationship
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
CREATE (a)-[:KNOWS]->(b)

// Find shortest path
MATCH p=shortestPath((a:Person {name: 'Alice'})-[*]-(b:Person {name: 'Bob'}))
RETURN p

// Aggregate relationships
MATCH (p:Person)-[:KNOWS]->(f)
RETURN p.name, COUNT(f) AS friends
ORDER BY friends DESC
```

**Port Conflicts:**
- Default Neo4j: port 7687
- PRISM Neo4j: port 7688
- Use different ports to run multiple instances

**Common Issues:**
- **Connection refused:** Neo4j not running
- **Authentication failed:** Wrong username/password
- **Port already in use:** Another Neo4j instance running (check PRISM)
- **Bolt protocol error:** Verify URI uses `bolt://` not `http://`

---

## Advanced Troubleshooting

### MCP Server Startup Failures

**Symptom:** Server shows "✗ Disconnected" in `claude mcp list`

**Diagnostic Steps:**

1. **Check command exists:**
   ```bash
   which mcp-server-github
   which uvx
   which python3
   ```

2. **Test command manually:**
   ```bash
   # Custom MCP
   python3 -m prism_mcp.interfaces.mcp_server

   # NPM MCP
   npx @modelcontextprotocol/server-github

   # uvx MCP
   ~/.local/bin/uvx obsidianpilot
   ```

3. **Check environment variables:**
   ```bash
   # List all env vars in config
   cat ~/.claude/mcp_config.json | grep -A 5 '"env"'

   # Test if they're set
   echo $GITHUB_TOKEN
   echo $MDB_MCP_CONNECTION_STRING
   ```

4. **Validate JSON syntax:**
   ```bash
   python3 -m json.tool ~/.claude/mcp_config.json
   python3 -m json.tool ~/.config/claude/mcp_config.json
   python3 -m json.tool .mcp.json
   ```

5. **Check Claude Code logs:**
   ```bash
   tail -100 ~/.config/claude/logs/claude-code-*.log | grep -i error
   ```

6. **Restart Claude Code:**
   - Full exit and relaunch (config changes require restart)
   - Don't just reload window

---

### Database Connection Debugging

**MongoDB Connection Issues:**

```bash
# Test connection string
mongosh "mongodb://user:pass@host:port/db?authSource=admin"

# Check if MongoDB is running
ps aux | grep mongod
nc -zv localhost 27017

# Test authentication
mongosh --host localhost --port 27017 -u admin -p password --authenticationDatabase admin

# Check logs
tail -f /var/log/mongodb/mongod.log
```

**PostgreSQL Connection Issues:**

```bash
# Test connection string
psql "postgresql://user:pass@localhost:5432/dbname"

# Check if PostgreSQL is running
ps aux | grep postgres
nc -zv localhost 5432

# List databases
psql -U postgres -l

# Check logs
tail -f /var/log/postgresql/postgresql-*.log
```

**Redis Connection Issues:**

```bash
# Test connection
redis-cli ping
redis-cli -a password ping  # With auth

# Check if Redis is running
ps aux | grep redis
nc -zv localhost 6379

# Test specific DB
redis-cli -n 2 ping

# Check logs
tail -f /var/log/redis/redis-server.log
```

---

### Configuration Scope Issues

**Problem:** "Project MCP servers require approval" when working in subdirectories

**Root Cause:** Server added with `-s project` scope requires approval settings

**Solution 1: Use Local Scope (Recommended)**
```bash
# Remove project-scoped server
claude mcp remove -s project server-name

# Re-add with local scope (default)
claude mcp add server-name command -e KEY=value
```

**Solution 2: Configure Approval**
Add to `.claude/settings.local.json`:
```json
{
  "mcpSettings": {
    "autoApprove": ["server-name"]
  }
}
```

---

### Token Budget Exceeded

**Symptom:** "Too many tools - context budget exceeded"

**Current Usage:**
- Default budget: 25k tokens
- Your usage: ~42.5k tokens (with all MCPs)

**Solution:** Increase budget in `~/.config/claude/settings.json`:
```json
{
  "mcpSettings": {
    "maxToolsTokens": 60000
  }
}
```

**Recommended Values:**
- 25k: Default (8-10 MCP servers)
- 40k: Medium (15-20 servers)
- 60k: Large (20+ servers)

**Alternative:** Remove unused MCPs:
```bash
# List all servers
claude mcp list

# Remove unused ones
claude mcp remove unused-server
```

---

### Performance Issues

**ObsidianPilot Slow Writes:**
- **Expected:** WSL→Windows filesystem overhead (`/mnt/c/` paths)
- **Speed:** Still 100x faster than REST API
- **Optimization:** Use WSL native path (`/home/user/vault`) for max speed

**MongoDB Query Timeouts:**
- **Cause:** Large collections without indexes
- **Solution:** Add indexes to frequently queried fields
- **Check:** Use `collection-schema` tool to infer schema

**GitHub MCP Slow:**
- **Cause:** Rate limiting (5000 requests/hour)
- **Solution:** Cache results, reduce frequency
- **Check:** `gh api rate_limit` to see current usage

---

## MCPs Evaluated and Rejected

**Complete evaluation results for reference when considering new MCPs:**

| MCP | Reason Skipped | Alternative | Token Cost |
|-----|----------------|-------------|------------|
| **Filesystem MCP** | Built-in Read/Write/Edit sufficient | Use Read, Write, Edit, Grep tools | ~3k |
| **Containerd MCP** | nerdctl bash commands work fine | Use `nerdctl` via Bash tool | ~2k |
| **Brave Search MCP** | WebSearch tool redundant | Use built-in WebSearch | ~2.5k |
| **Exa MCP** | WebSearch tool redundant | Use built-in WebSearch | ~2k |
| **Semgrep MCP** | Can run via Bash, Tech Scanner exists | `semgrep --config auto .` | ~3k |
| **Docker MCP** | nerdctl commands simpler | `nerdctl` via Bash | ~2.5k |
| **Kubernetes MCP** | kubectl via Bash sufficient | `kubectl` commands | ~4k |
| **Terraform MCP** | terraform CLI works fine | `terraform` commands | ~3k |
| **AWS MCP** | aws CLI provides same functionality | `aws` commands | ~5k |

**Evaluation Criteria:**
1. **Value over existing tools** - Does it provide structured access that Bash can't?
2. **Frequency of use** - Will it be used regularly or once per month?
3. **Token cost** - Is the context overhead justified?
4. **Maintenance** - Does it require ongoing configuration updates?

**Key Lesson:** Don't add MCPs "just because they exist". Only install if they provide clear value over alternatives.

---

## Complete Command Reference

### MCP Server Management

```bash
# List all configured servers with status
claude mcp list

# List servers in specific scope
claude mcp list -s user
claude mcp list -s local
claude mcp list -s project

# Add server (local scope - default, works in all subdirs)
claude mcp add server-name command -e KEY=value

# Add server (user scope - global)
claude mcp add -s user server-name command -e KEY=value

# Add server (project scope - requires approval)
claude mcp add -s project server-name command -e KEY=value

# Remove server
claude mcp remove server-name
claude mcp remove -s user server-name
claude mcp remove -s project server-name

# Get server configuration details
claude mcp get server-name

# Test server connection
claude mcp test server-name

# Update server configuration
claude mcp update server-name -e NEW_KEY=new_value
```

### Configuration File Management

```bash
# Custom MCPs (your servers) - uses "servers" key
cat ~/.claude/mcp_config.json

# External MCPs (third-party) - uses "mcpServers" key
cat ~/.config/claude/mcp_config.json

# Per-project MCPs (local scope) - stored per-repo
cat ~/.claude.json

# Per-project MCPs (project scope) - checked into git
cat .mcp.json

# Claude Code global settings
cat ~/.config/claude/settings.json

# Project-specific settings
cat .claude/settings.local.json
```

### Server Testing Commands

```bash
# Test custom Python MCP servers
python3 -m prism_mcp.interfaces.mcp_server
python3 -m orchestration_mcp.mcp_server
python3 -m tech_scanner_mcp.mcp_server

# Test NPM MCP servers
npx @modelcontextprotocol/server-github
npx mongodb-mcp-server "mongodb://localhost:27017/mydb"
npx mcp-atlassian-jira

# Test ObsidianPilot
~/.local/bin/uvx obsidianpilot

# Test with specific environment
GITHUB_TOKEN=xxx npx @modelcontextprotocol/server-github
```

### Database Connection Testing

```bash
# MongoDB
mongosh "mongodb://user:pass@host:port/db?authSource=admin"
mongosh --eval "db.adminCommand('ping')"

# PostgreSQL
psql "postgresql://user:pass@localhost:5432/dbname"
psql -U postgres -c "SELECT 1"

# Redis
redis-cli ping
redis-cli -a password ping
redis-cli -h host -p port -a password ping

# Neo4j
cypher-shell -a bolt://localhost:7687 -u neo4j -p password "RETURN 1"

# SQLite
sqlite3 ./data/mydb.db ".tables"
sqlite3 ./data/mydb.db "SELECT 1"
```

### Network Connectivity Testing

```bash
# Test port connectivity
nc -zv localhost 27017  # MongoDB
nc -zv localhost 5432   # PostgreSQL
nc -zv localhost 6379   # Redis
nc -zv localhost 7687   # Neo4j
nc -zv localhost 7688   # PRISM Neo4j

# Check listening ports
netstat -tlnp | grep 27017
ss -tlnp | grep 27017

# Test with telnet
telnet localhost 27017
```

### JSON Validation

```bash
# Validate JSON syntax
python3 -m json.tool ~/.claude/mcp_config.json
python3 -m json.tool ~/.config/claude/mcp_config.json
python3 -m json.tool .mcp.json

# Pretty print with jq
jq . ~/.claude/mcp_config.json
jq '.mcpServers' ~/.config/claude/mcp_config.json

# Check specific server config
jq '.servers.prism' ~/.claude/mcp_config.json
jq '.mcpServers.github' ~/.config/claude/mcp_config.json
```

### Log Analysis

```bash
# View Claude Code logs
tail -f ~/.config/claude/logs/claude-code-*.log

# Filter for MCP errors
tail -100 ~/.config/claude/logs/claude-code-*.log | grep -i "mcp\|error"

# Check for specific server
tail -100 ~/.config/claude/logs/claude-code-*.log | grep -i "prism\|mongodb\|github"

# View database logs
tail -f /var/log/mongodb/mongod.log
tail -f /var/log/postgresql/postgresql-*.log
tail -f /var/log/redis/redis-server.log
tail -f /var/log/neo4j/neo4j.log
```

---

## Server-Specific Advanced Configuration

### PRISM MCP Configuration

**Full configuration example:**
```json
{
  "servers": {
    "prism": {
      "command": "python3",
      "args": ["-m", "prism_mcp.interfaces.mcp_server"],
      "env": {
        "PYTHONPATH": "~/repos/claude_mcp/prism_mcp",
        "NEO4J_URI": "bolt://localhost:7688",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password",
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6334",
        "QDRANT_API_KEY": "",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Environment Variables:**
- `PYTHONPATH`: Path to PRISM MCP source code
- `NEO4J_URI`: Neo4j connection (port 7688 to avoid conflict with default 7687)
- `QDRANT_HOST/PORT`: Vector database for embeddings
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR

---

### Orchestration MCP Configuration

**Full configuration example:**
```json
{
  "servers": {
    "orchestration": {
      "command": "python3",
      "args": ["-m", "orchestration_mcp.mcp_server"],
      "env": {
        "PYTHONPATH": "~/repos/claude_mcp/orchestration_mcp",
        "WORKSPACE_DIR": "~/workspace",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Environment Variables:**
- `PYTHONPATH`: Path to Orchestration MCP source code
- `WORKSPACE_DIR`: Directory for orchestration workspaces
- `LOG_LEVEL`: Logging verbosity

---

### GitHub MCP Configuration

**Full configuration example:**
```json
{
  "mcpServers": {
    "github": {
      "command": "mcp-server-github",
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxx",
        "GITHUB_API_URL": "https://api.github.com",
        "GITHUB_ENTERPRISE_URL": ""
      }
    }
  }
}
```

**Token Permissions Required:**
- `repo` - Full repository access
- `workflow` - Update GitHub Actions workflows
- `read:org` - Read organization data
- `read:user` - Read user profile data

**Rate Limits:**
- Authenticated: 5000 requests/hour
- Unauthenticated: 60 requests/hour
- Check usage: `gh api rate_limit`

---

## Resources

### Official Documentation
- **MCP Protocol:** https://modelcontextprotocol.io/
- **MCP Registry:** https://github.com/modelcontextprotocol/registry
- **MCP Servers:** https://github.com/modelcontextprotocol/servers

### Community Resources
- **Awesome MCP Servers:** https://github.com/wong2/awesome-mcp-servers
- **Docker MCP Catalog:** https://hub.docker.com/mcp

### Your Custom MCPs
- **PRISM:** `~/repos/claude_mcp/prism_mcp/CLAUDE.md`
- **Orchestration:** `~/repos/claude_mcp/orchestration_mcp/CLAUDE.md`
- **Tech Scanner:** `~/repos/claude_mcp/tech_scanner_mcp/`

### Installed MCP Documentation
- **ObsidianPilot:** https://github.com/that0n3guy/ObsidianPilot
- **Jira MCP:** https://github.com/aashari/mcp-server-atlassian-jira
- **MongoDB MCP:** https://www.npmjs.com/package/mongodb-mcp-server
- **GitHub MCP:** https://github.com/modelcontextprotocol/servers/tree/main/src/github
- **Package Registry:** https://github.com/artmann/package-registry-mcp
