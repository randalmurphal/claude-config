---
name: MCP Integration
description: Set up and use MCP (Model Context Protocol) servers to extend Claude Code capabilities including PRISM semantic memory, filesystem access, and database integration. Use when setting up MCP servers, debugging MCP connections, or understanding MCP tool usage.
allowed-tools:
  - Read
  - Bash
---

# MCP Integration Skill

## What is MCP?

**Model Context Protocol (MCP)** is a standardized protocol that extends Claude Code with additional capabilities through specialized servers. Each MCP server provides tools that Claude can invoke to interact with external systems, databases, APIs, and services.

**Benefits:**
- Extends Claude beyond built-in tools (Read, Write, Edit, Grep, Bash)
- Standardized interface for diverse integrations
- Lightweight and composable (mix and match servers)
- Context-efficient (tools described once, invoked many times)

**Trade-offs:**
- Each server consumes context tokens (typically 1.5-3k per server)
- More tools = more context overhead
- Some operations possible via Bash but MCP provides structure

---

## Configuration Architecture

### Three Configuration Locations

| Config File | Purpose | Key Name | Use Case |
|-------------|---------|----------|----------|
| `~/.claude/mcp_config.json` | Custom-built MCPs | `servers` | Your own MCP servers (PRISM, Orchestration) |
| `~/.config/claude/mcp_config.json` | External MCPs | `mcpServers` | Third-party NPM/Docker MCPs (GitHub, databases) |
| `<project>/.mcp.json` | Per-project MCPs | `mcpServers` | Project-specific tools (MongoDB, Redis for this project) |

**Key Insight:** Two different key names exist (`servers` vs `mcpServers`) for historical reasons. Custom MCPs use `servers`, everything else uses `mcpServers`.

### Configuration Scopes

Claude Code has three scope levels (use **local scope** for project-specific servers):

| Scope | Command | Storage | Visibility | Best For |
|-------|---------|---------|-----------|----------|
| **local** (default) | `claude mcp add` | `~/.claude.json` | All subdirs in git repo | Project-specific servers (MongoDB for this repo) |
| project | `claude mcp add -s project` | `.mcp.json` | Requires approval settings | Team-shared, checked into git |
| user | `claude mcp add -s user` | `~/.claude.json` | All projects everywhere | Global tools (GitHub, Package Registry) |

**Recommendation:** Use **local scope** for project databases, **user scope** for global tools like GitHub.

---

## Current MCP Setup

### Custom MCPs (Active)
**Location:** `~/.claude/mcp_config.json`

1. **PRISM MCP** (33 tools, ~10k tokens)
   - Semantic memory system with Neo4j + Qdrant backends
   - Memory operations, ADR storage, pattern detection
   - Duplication detection, preference learning, context warming
   - **Use when:** Storing/retrieving past decisions, patterns, learnings

2. **Orchestration MCP** (18 tools, ~6k tokens)
   - Multi-agent coordination, checkpoints, worktrees
   - Task decomposition, complexity analysis
   - **Use when:** Managing complex multi-step workflows

3. **Tech Scanner MCP** (1 tool, ~500 tokens)
   - Security analysis for technology stacks
   - **Use when:** Scanning dependencies for vulnerabilities

**Total Custom:** 52 tools, ~16k tokens (8% of context)

### External MCPs (Installed)
**Location:** `~/.config/claude/mcp_config.json`

1. **GitHub MCP** (51 tools, ~15k tokens)
   - Repository operations, PR automation, CI/CD monitoring
   - Issues, pull requests, workflows, security scanning
   - **Use when:** Automating GitHub operations beyond `gh` CLI

2. **Package Registry MCP** (5 tools, ~1.5k tokens)
   - Search npm, PyPI, Cargo, NuGet packages
   - Get package details, versions, vulnerabilities
   - **Use when:** Researching packages before installation

**Total External:** 56 tools, ~16.5k tokens (8% of context)

### Built-in Tools (~32 tools, ~10k tokens)
- Read, Write, Edit, MultiEdit, Grep, Glob, Bash, Task, WebSearch, etc.
- Always available, no configuration needed

**Grand Total:** 140 tools using ~42.5k tokens (21% of context budget)

---

## Available MCP Servers

### Productivity & Documentation

#### ObsidianPilot MCP
**Purpose:** Direct filesystem access to Obsidian vaults with advanced search (100-1000x faster than REST API)

**Features:**
- Full-text search (SQLite FTS5 with boolean operators)
- Frontmatter property search (=, !=, >, <, contains)
- Date-based search (created/modified within X days)
- Regex search with timeout protection
- Tag search (hierarchical tags)
- Instant writes (direct filesystem, no API overhead)

**Installation:**
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to ~/.claude.json under mcpServers
{
  "obsidian": {
    "type": "stdio",
    "command": "/home/rmurphy/.local/bin/uvx",
    "args": ["obsidianpilot"],
    "env": {
      "OBSIDIAN_VAULT_PATH": "/home/rmurphy/obsidian-notes"
    }
  }
}
```

**Vault Path Options:**
- WSL native (`/home/user/vault`) - Fastest
- Windows filesystem (`/mnt/c/Users/user/vault`) - Accessible from Obsidian GUI

**Tools:** 15+ tools for notes, search, tags, links
**Token Cost:** ~3k tokens

#### Jira MCP
**Purpose:** Full-featured Jira integration with JQL search and dev info (commits, PRs)

**Installation:**
```bash
npm install -g @aashari/mcp-server-atlassian-jira

# Add via CLI (local scope - works in project subdirs)
cd /path/to/project
claude mcp add jira mcp-atlassian-jira \
  -e ATLASSIAN_SITE_NAME=yourcompany \
  -e ATLASSIAN_USER_EMAIL=you@company.com \
  -e ATLASSIAN_API_TOKEN=your_token
```

**Tools:** List projects, search issues (JQL), get issue details, view dev info
**Token Cost:** ~2.5k tokens

### Databases (Configure Per-Project)

#### MongoDB MCP
**Purpose:** Direct MongoDB access for queries, aggregations, CRUD operations

**Installation:**
```bash
cd /path/to/project
claude mcp add mongodb npx -y mongodb-mcp-server \
  -e MDB_MCP_CONNECTION_STRING="mongodb://user:pass@host:port/db?authSource=admin"
```

**Tools:**
- list-databases, list-collections
- find, aggregate, count
- insert-many, update-many, delete-many
- collection-schema (infer schema)

**Token Cost:** ~3k tokens

#### PostgreSQL MCP
**Purpose:** Query and inspect PostgreSQL databases

**Installation:**
```bash
# Via Docker
docker pull mcp/postgres

# Per-project config (.mcp.json)
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

**Tools:** Execute queries, schema inspection, read-only by default
**Token Cost:** ~2.5k tokens

#### SQLite MCP
**Purpose:** Lightweight database operations and testing

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-sqlite

# Per-project config
{
  "mcpServers": {
    "sqlite": {
      "command": "mcp-server-sqlite",
      "args": ["--db-path", "./data"]
    }
  }
}
```

**Tools:** read_query, write_query, create_table, list_tables, describe_table, append_insight
**Token Cost:** ~2.5k tokens

#### Redis MCP
**Purpose:** Key operations, cache inspection, pub/sub

**Installation:**
```bash
docker pull mcp/redis

# Per-project config
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

**Tools:** get, set, delete, TTL management, pub/sub
**Token Cost:** ~2k tokens

#### Neo4j MCP
**Purpose:** Graph database queries (Cypher, graph traversal)

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-neo4j

# Per-project config
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

**Tools:** Cypher queries, graph traversal, node/relationship operations
**Token Cost:** ~3k tokens

**Note:** You already use Neo4j for PRISM (port 7688)

### MCPs Evaluated and Rejected

**Why Not Install:**

| MCP | Reason Skipped | Alternative |
|-----|----------------|-------------|
| Filesystem MCP | Built-in Read/Write/Edit sufficient | Use Read, Write, Edit, Grep |
| Containerd MCP | nerdctl bash commands work fine | Use `nerdctl` via Bash tool |
| Brave Search MCP | WebSearch tool redundant | Use built-in WebSearch |
| Exa MCP | WebSearch tool redundant | Use built-in WebSearch |
| Semgrep MCP | Can run via Bash, Tech Scanner exists | `semgrep --config auto .` |

**Key Lesson:** Don't add MCPs just because they exist. Evaluate if they provide value over existing tools.

---

## Setup and Configuration

### Installing Global External MCPs

**Via npm:**
```bash
npm install -g @modelcontextprotocol/server-github
```

**Add to user scope:**
```bash
claude mcp add -s user github mcp-server-github \
  -e GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
```

**Verify:**
```bash
claude mcp list
# Should show: github: mcp-server-github - ✓ Connected
```

### Installing Per-Project MCPs

**Use local scope (default - works in all subdirectories):**
```bash
cd /path/to/your/repo
claude mcp add mongodb npx -y mongodb-mcp-server \
  -e MDB_MCP_CONNECTION_STRING="mongodb://localhost:27017/rthree?authSource=admin"
```

**Verify in subdirectory:**
```bash
cd /path/to/your/repo/some/deep/subdirectory
claude mcp list
# Should still show mongodb server
```

### Custom MCP Development

**Location:** `~/repos/claude_mcp/<name>_mcp/`

**Add to `~/.claude/mcp_config.json`:**
```json
{
  "servers": {
    "prism": {
      "command": "python3",
      "args": ["-m", "prism_mcp.interfaces.mcp_server"],
      "env": {
        "PYTHONPATH": "/home/rmurphy/repos/claude_mcp/prism_mcp",
        "NEO4J_URI": "bolt://localhost:7688",
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6334"
      }
    }
  }
}
```

**Restart Claude Code after config changes.**

### Environment Variables and Paths

**Python virtualenv requirements:**
- Custom Python MCPs need `PYTHONPATH` or virtualenv activation
- Use absolute paths for `command` (e.g., `/opt/envs/imports/bin/python3`)
- Or use system python with `-m module.path` args

**Common environment variables:**
- Database MCPs: Connection strings (URI, host, port, auth)
- API MCPs: API tokens/keys (GITHUB_TOKEN, ATLASSIAN_API_TOKEN)
- Path MCPs: Directory paths (OBSIDIAN_VAULT_PATH)

**Security note:** Credentials stored in plaintext in config files. Protect with filesystem permissions.

---

## Using MCP Tools

### When to Use MCP vs Built-in Tools

**Use MCP when:**
- Structured API access needed (GitHub issues > parsing `gh` output)
- Complex queries (MongoDB aggregations > bash mongosh parsing)
- Frequent operations (PRISM memory > manual file management)
- Safety/validation required (Database MCPs prevent SQL injection)

**Use built-in Bash when:**
- Simple one-off commands
- Tools already available via CLI
- No structured parsing needed
- MCP overhead not justified

**Example comparison:**

| Task | Via Bash | Via MCP | Winner |
|------|----------|---------|--------|
| Create GitHub PR | `gh pr create` | `mcp__github__create_pull_request` | MCP (structured, safer) |
| List files | `ls -la` | Filesystem MCP | Bash (simpler) |
| Query MongoDB | `mongosh --eval "..."` | `mcp__mongodb__find` | MCP (structured results) |
| Search packages | `npm search foo` | `mcp__package_registry__search_npm_packages` | MCP (detailed info) |

### Integration Patterns

**Pattern 1: Database Queries**
```
Query the MongoDB rthree database for all assets where info.owner.subID = $SUB1
```
Claude will use `mcp__mongodb__find` tool automatically.

**Pattern 2: Multi-step Workflows**
```
1. Search Jira for open INT tickets assigned to me
2. For each ticket, get dev info (commits, PRs)
3. Summarize work in progress
```
Claude will chain multiple MCP tools (Jira search → Jira dev info → text summary).

**Pattern 3: Memory + Code**
```
Before implementing this feature, check PRISM for similar patterns we've used
```
Claude will query PRISM MCP, retrieve past decisions, apply patterns to current work.

**Pattern 4: Package Research**
```
Find Python packages for PDF parsing, check versions and vulnerabilities
```
Claude will use Package Registry MCP to search PyPI and get security info.

### Best Practices

**Do:**
- Use specific tool names when you know what you want
- Let Claude choose tools for complex workflows
- Check PRISM before major decisions (if PRISM MCP active)
- Use project-scoped databases (MongoDB, Redis) for per-project work

**Don't:**
- Install MCPs "just in case" (context overhead adds up)
- Use MCP when Bash is simpler
- Store production secrets in MCP config (use env vars or secrets manager)
- Mix scopes unnecessarily (use local for projects, user for globals)

---

## Troubleshooting

### Server Not Starting

**Symptoms:**
- MCP tools not available after restart
- `claude mcp list` shows "✗ Disconnected"

**Fixes:**

1. **Verify command path:**
   ```bash
   which mcp-server-github  # Should return path
   which uvx  # For ObsidianPilot
   ```

2. **Check config syntax:**
   ```bash
   # Validate JSON
   cat ~/.claude/mcp_config.json | python3 -m json.tool
   cat ~/.config/claude/mcp_config.json | python3 -m json.tool
   ```

3. **Test server manually:**
   ```bash
   # Custom MCP
   python3 -m prism_mcp.interfaces.mcp_server

   # NPM MCP
   npx @modelcontextprotocol/server-github

   # Check for errors
   ```

4. **Check environment variables:**
   ```bash
   # MongoDB
   echo $MDB_MCP_CONNECTION_STRING

   # Verify connection string works
   mongosh "mongodb://localhost:27017/rthree?authSource=admin"
   ```

5. **Restart Claude Code:**
   - Config changes require full restart
   - Exit and relaunch, don't just reload

### Connection Issues

**MongoDB/PostgreSQL/Redis connection failed:**

1. **Verify service is running:**
   ```bash
   # MongoDB
   mongosh "mongodb://localhost:27017/rthree?authSource=admin"

   # PostgreSQL
   psql "postgresql://user:pass@localhost:5432/dbname"

   # Redis
   redis-cli ping
   ```

2. **Check network access:**
   ```bash
   # Test port connectivity
   nc -zv localhost 27017  # MongoDB
   nc -zv localhost 5432   # PostgreSQL
   nc -zv localhost 6379   # Redis
   ```

3. **Verify credentials:**
   - Double-check username, password, database name
   - Test credentials outside of MCP first

4. **Check Docker network:**
   ```bash
   # If using Docker MCP servers
   docker network ls
   # Ensure --network host in config
   ```

**GitHub MCP not connecting:**

1. **Verify token:**
   ```bash
   # Test token via gh CLI
   gh auth status
   ```

2. **Check token permissions:**
   - Go to https://github.com/settings/tokens
   - Ensure token has repo, workflow, read:org scopes

3. **Regenerate if expired:**
   - GitHub tokens can expire
   - Generate new token, update config

### Configuration Errors

**"Project MCP servers require approval" (working in subdirectories):**

**Cause:** Server added with `-s project` scope, requires approval settings

**Fix:** Remove and re-add with local scope:
```bash
claude mcp remove -s project server-name
claude mcp add server-name command -e KEY=value  # Uses local by default
```

**"Server shows in .mcp.json but doesn't load":**

**Cause:** Project scope requires approval in `.claude/settings.local.json`

**Fix:** Use local scope instead (stores in `~/.claude.json` per-project):
```bash
claude mcp remove -s project mongodb
claude mcp add mongodb npx -y mongodb-mcp-server -e MDB_MCP_CONNECTION_STRING="..."
```

**"Too many tools - context budget exceeded":**

**Cause:** MCP servers consume context tokens

**Fix:** Increase token budget in `~/.config/claude/settings.json`:
```json
{
  "mcpSettings": {
    "maxToolsTokens": 60000
  }
}
```

**Default:** 25k tokens (supports ~8-10 MCP servers)
**Recommended:** 60k tokens (supports 20+ servers comfortably)

### Log Locations

**Claude Code logs:**
```bash
# Check for MCP startup errors
~/.config/claude/logs/

# Recent log file (varies by date)
tail -f ~/.config/claude/logs/claude-code-2025-10-17.log
```

**Custom MCP logs:**
- PRISM MCP: Check stdout/stderr where launched
- Add logging to your MCP server code

**NPM MCP logs:**
- Usually printed to Claude Code logs
- Run manually to see direct output: `npx server-name`

### Common Issues

**ObsidianPilot slow writes on Windows filesystem:**
- Expected with `/mnt/c/` paths (WSL→Windows overhead)
- Still 100x faster than REST API approach
- For max speed, use WSL native path

**MongoDB query returns no results:**
- Check database name in connection string
- List databases first: `mcp__mongodb__list-databases`
- Verify collection exists: `mcp__mongodb__list-collections`

**Jira tools not available:**
- Verify server added with local scope (default)
- Check site name doesn't include `.atlassian.net`
- Run `claude mcp get jira` to verify config

**GitHub MCP tools not showing:**
- Restart Claude Code after adding server
- Check token has correct permissions
- Verify global install: `which mcp-server-github`

---

## Token Budget Management

### Current Usage
- **Custom MCPs:** 52 tools = ~16k tokens (8%)
- **External MCPs:** 56 tools = ~16.5k tokens (8%)
- **Built-in tools:** ~32 tools = ~10k tokens (5%)
- **Total:** 140 tools = ~42.5k tokens (21% of 200k context)

### Planning New MCPs

**Before adding an MCP, ask:**
1. What value does this provide over existing tools?
2. Can I accomplish this with Bash?
3. How often will I use this?
4. What's the token cost? (check MCP documentation)

**Token budget guidelines:**
- Small MCPs (1-5 tools): ~1-2k tokens
- Medium MCPs (5-15 tools): ~2-5k tokens
- Large MCPs (15-50 tools): ~5-15k tokens

**Calculate headroom:**
- Default budget: 200k tokens
- ~50k for tools (25% overhead OK)
- ~150k for actual work
- Current: 42.5k used, ~107.5k headroom

### Optimizing Token Usage

**Strategies:**
1. **Per-project MCPs** - Only load MongoDB/Redis when working on that project
2. **Remove unused MCPs** - Uninstall MCPs you added but never use
3. **Increase budget** - Raise `maxToolsTokens` to 60k if needed
4. **Selective installation** - Don't install "nice to have" MCPs

---

## Integration with Workflows

### PRISM Memory Integration

**When to query PRISM:**
- Before making architectural decisions
- When encountering similar problems
- To retrieve past patterns/conventions
- To check if issue already solved

**How Claude uses it:**
```
You: "How should I structure error handling in this module?"
Claude: [Queries PRISM for past error handling patterns]
Claude: "Based on past decisions, we use centralized exception classes..."
```

### Orchestration MCP Integration

**When orchestration activates:**
- Complex multi-step tasks
- Parallel work coordination
- Checkpoint/resume workflows
- Git worktree management

**How it works:**
```
You: "Refactor this 5000-line module into separate components"
Claude: [Uses orchestration MCP to decompose, checkpoint, coordinate]
```

### Database MCP Patterns

**MongoDB example workflow:**
```
1. List databases to find correct DB
2. List collections to find target collection
3. Infer schema to understand structure
4. Query documents with filters
5. Aggregate for complex analysis
```

**Why MCP > Bash:**
- Structured JSON responses (no parsing)
- Type safety (prevents injection)
- Aggregation pipelines (complex queries)
- Schema inference (understand data)

---

## Quick Reference Commands

### Managing MCPs

```bash
# List all configured servers
claude mcp list

# Add server (local scope - recommended for projects)
claude mcp add server-name command -e KEY=value

# Add server (user scope - global tools)
claude mcp add -s user server-name command -e KEY=value

# Remove server
claude mcp remove server-name
claude mcp remove -s user server-name

# Get server details
claude mcp get server-name

# Test server connection
claude mcp test server-name
```

### Configuration Files

```bash
# Custom MCPs (your servers)
cat ~/.claude/mcp_config.json

# External MCPs (third-party)
cat ~/.config/claude/mcp_config.json

# Per-project MCPs
cat .mcp.json  # in project root

# Claude Code settings
cat ~/.config/claude/settings.json
```

### Testing MCP Servers

```bash
# Test custom MCP
python3 -m prism_mcp.interfaces.mcp_server
python3 -m orchestration_mcp.mcp_server

# Test NPM MCP
npx @modelcontextprotocol/server-github
npx mongodb-mcp-server "mongodb://localhost:27017/rthree"

# Test ObsidianPilot
/home/rmurphy/.local/bin/uvx obsidianpilot
```

### Debugging

```bash
# Validate JSON config
python3 -m json.tool ~/.claude/mcp_config.json
python3 -m json.tool ~/.config/claude/mcp_config.json

# Check service connectivity
nc -zv localhost 27017  # MongoDB
nc -zv localhost 6379   # Redis
nc -zv localhost 5432   # PostgreSQL

# Test database connection
mongosh "mongodb://localhost:27017/rthree?authSource=admin"
redis-cli ping
psql "postgresql://user:pass@localhost:5432/dbname"

# Check logs
tail -f ~/.config/claude/logs/claude-code-*.log
```

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
- **PRISM:** `/home/randy/repos/claude_mcp/prism_mcp/CLAUDE.md`
- **Orchestration:** `/home/randy/repos/claude_mcp/orchestration_mcp/CLAUDE.md`
- **Tech Scanner:** `/home/randy/repos/claude_mcp/tech_scanner_mcp/`

### Installed MCP Documentation
- **ObsidianPilot:** https://github.com/that0n3guy/ObsidianPilot
- **Jira MCP:** https://github.com/aashari/mcp-server-atlassian-jira
- **MongoDB MCP:** https://www.npmjs.com/package/mongodb-mcp-server
- **GitHub MCP:** https://github.com/modelcontextprotocol/servers/tree/main/src/github
- **Package Registry:** https://github.com/artmann/package-registry-mcp

---

## Summary

**MCP extends Claude Code with specialized tools for databases, APIs, and services.**

**Key Principles:**
1. **Evaluate before installing** - Token overhead adds up
2. **Use local scope for projects** - Works in all subdirectories
3. **Use user scope for globals** - GitHub, Package Registry
4. **Test manually first** - Verify tools work before configuring MCP
5. **Monitor token budget** - Current: 42.5k/200k (21%), healthy headroom

**Current Setup (Production-Ready):**
- Custom MCPs: PRISM, Orchestration, Tech Scanner (52 tools)
- External MCPs: GitHub, Package Registry (56 tools)
- Built-in tools: Read, Write, Edit, Grep, Bash, etc. (32 tools)
- **Total:** 140 tools, ~42.5k tokens (21% of context)

**When to Use This Skill:**
- Setting up new MCP servers
- Debugging MCP connection issues
- Understanding which MCP to use for a task
- Troubleshooting configuration problems
- Planning token budget for new MCPs

**For operational issues, check logs and test manually. For architecture decisions, consult PRISM first.**
