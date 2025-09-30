# MCP Servers Reference

**Maintained**: 2025-09-30
**Purpose**: Track useful MCP servers for Claude Code, organized by priority and use case

---

## Current Setup

### Custom MCPs (Active - Configured in `~/.claude/mcp_config.json`)

1. **PRISM MCP** (33 tools) - Memory & Learning System
   - Memory operations, ADR storage, pattern detection
   - Duplication detection, preference learning, context warming
   - **Status**: ✅ ACTIVE

2. **Orchestration MCP** (18 tools) - Workflow Management
   - Multi-agent coordination, checkpoints, worktrees
   - Task decomposition, complexity analysis
   - **Status**: ✅ ACTIVE

3. **Tech Scanner MCP** (1 tool) - Security Analysis
   - Vulnerability scanning for technology stacks
   - **Status**: ✅ ACTIVE

**Total Custom**: 52 tools (~16k tokens, 8% of context)

---

## External MCPs

### Installed (Active)

#### 1. GitHub MCP (51 tools) - CRITICAL
**Value**: 🔥🔥🔥
**Purpose**: Repository operations, PR automation, CI/CD monitoring

**Capabilities**:
- Repository: browse, search, get files, commits (12 tools)
- Issues: create, update, comment, assign, labels (10 tools)
- Pull Requests: create, update, review, merge (8 tools)
- Actions: workflows, runs, jobs, artifacts, logs (14 tools)
- Security: code scanning, Dependabot alerts (4 tools)
- Context: user, teams, discussions, gists (8 tools)

**Installation**:
```bash
npm install -g @modelcontextprotocol/server-github
```

**Configuration** (`~/.config/claude/mcp_config.json`):
```json
"github": {
  "command": "mcp-server-github",
  "env": {
    "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxx"
  }
}
```

**Token Impact**: ~15k tokens
**Status**: ✅ INSTALLED (2025-09-30)

---

#### 2. Package Registry MCP (5 tools) - HIGH VALUE
**Value**: 🔥🔥
**Purpose**: Instant package intelligence across ecosystems

**Capabilities**:
- search_npm_packages - Search npm registry
- search_pypi_packages - Search Python Package Index
- search_cargo_packages - Search Rust crates
- search_nuget_packages - Search .NET packages
- get_package_details - Get detailed package info (versions, vulnerabilities, dependencies)

**Installation**:
```bash
npm install -g @artmann/package-registry-mcp
```

**Configuration**:
```json
"package-registry": {
  "command": "package-registry-mcp"
}
```

**Token Impact**: ~1.5k tokens
**Status**: ✅ INSTALLED (2025-09-30)

---

### Considered But Not Installing

#### Filesystem MCP - SKIPPED
**Why Skipped**: Built-in Read/Write/Edit tools sufficient
- Already have file operations via Read, Write, Edit
- Already have search via Grep tool
- Already have bash for advanced operations
- Unclear value vs existing tooling
- Would cost ~3k tokens

**Verdict**: Not worth the tokens for marginal benefit

---

#### Containerd MCP - REFERENCE ONLY
**Status**: 📚 DOCUMENTED FOR REFERENCE (not installing)

**Why Not Installing**:
- nerdctl bash commands work fine
- Simple operations (start, stop, logs, ps)
- ~5k tokens for infrequent use not justified
- Text output from nerdctl is easy to parse

**When it WOULD be useful**:
- Complex container orchestration
- Managing dozens of containers programmatically
- Parsing complex container configs frequently

**Our use case**: Few stable containers (PRISM databases), nerdctl is sufficient

**Installation** (for reference if needed later):
```bash
# Requires Rust
git clone https://github.com/jokemanfire/mcp-containerd
cd mcp-containerd
cargo build --release
```

**Configuration** (if ever needed):
```json
"containerd": {
  "command": "/path/to/mcp-containerd/target/release/mcp-containerd",
  "args": ["-t", "http"]
}
```

**Default Socket**: `unix:///run/containerd/containerd.sock`
**GitHub**: https://github.com/jokemanfire/mcp-containerd

---

### Other MCPs Evaluated and Rejected

#### Brave Search MCP - REDUNDANT
**Why Skipped**: Already have WebSearch tool built-in
- WebSearch already provides real-time web research
- No clear benefit over existing tool
- Would cost ~1k tokens for duplicate functionality

#### Exa MCP - MARKETING HYPE
**Why Skipped**: WebSearch already works fine
- "AI-optimized search" sounds like marketing
- No evidence of better quality than WebSearch
- Would cost ~1.5k tokens for unproven benefit

#### Semgrep MCP - REDUNDANT
**Why Skipped**: Can run via Bash, Tech Scanner already exists
- Can run `semgrep --config auto .` via Bash tool anytime
- Tech Scanner MCP already provides vulnerability scanning
- Convenience wrapper not worth ~2k tokens

---

## Tier 3: Per-Project Databases (Configure as Needed)

**Strategy**: Use project-specific `.mcp.json` files, not global configuration

### PostgreSQL MCP
**Purpose**: Query and inspect PostgreSQL databases

**Installation**:
```bash
# Docker Hub: mcp/postgres
docker pull mcp/postgres
```

**Per-Project Config** (`.mcp.json` in project root):
```json
{
  "mcpServers": {
    "postgres": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--network", "host",
        "mcp/postgres",
        "--connection-string", "postgresql://user:pass@localhost:5432/dbname"
      ]
    }
  }
}
```

**Capabilities**:
- Execute queries
- Schema inspection
- Read-only by default (safe)

**Token Impact**: ~2.5k tokens (per project)
**Status**: 🔧 CONFIGURE PER PROJECT

---

### MongoDB MCP
**Purpose**: Collection operations and aggregation queries

**Installation**:
```bash
npm install -g @mongodb-js/mongodb-mcp-server
# OR
docker pull mongodb/mongodb-mcp-server
```

**Per-Project Config**:
```json
{
  "mcpServers": {
    "mongodb": {
      "command": "mongodb-mcp-server",
      "env": {
        "MONGODB_URI": "mongodb://localhost:27017/mydb"
      }
    }
  }
}
```

**Capabilities**:
- Collection CRUD
- Aggregation pipelines
- Index management

**Token Impact**: ~3k tokens
**Status**: 🔧 CONFIGURE PER PROJECT

**Docs**: https://www.mongodb.com/docs/mcp-server/

---

### Redis MCP
**Purpose**: Key operations, cache inspection, pub/sub

**Installation**:
```bash
docker pull mcp/redis
```

**Per-Project Config**:
```json
{
  "mcpServers": {
    "redis": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--network", "host",
        "mcp/redis",
        "--url", "redis://localhost:6379"
      ]
    }
  }
}
```

**Capabilities**:
- Key operations (get, set, delete)
- Cache inspection
- Pub/sub operations
- TTL management

**Token Impact**: ~2k tokens
**Status**: 🔧 CONFIGURE PER PROJECT

---

### MySQL MCP
**Purpose**: Query execution and schema operations

**Installation**:
```bash
# Via Docker database server
docker pull mcp/mysql
```

**Per-Project Config**:
```json
{
  "mcpServers": {
    "mysql": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--network", "host",
        "mcp/mysql",
        "--connection-string", "mysql://user:pass@localhost:3306/dbname"
      ]
    }
  }
}
```

**Capabilities**:
- SQL query execution
- Schema inspection
- Table operations

**Token Impact**: ~2.5k tokens
**Status**: 🔧 CONFIGURE PER PROJECT

---

### Neo4j MCP
**Purpose**: Graph database queries (already using for PRISM!)

**Installation**:
```bash
npm install -g @modelcontextprotocol/server-neo4j
```

**Per-Project Config**:
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

**Capabilities**:
- Cypher query execution
- Graph traversal
- Node/relationship operations

**Token Impact**: ~3k tokens
**Status**: 🔧 CONFIGURE PER PROJECT

**Note**: You already use Neo4j for PRISM (port 7688)

---

### SQLite MCP
**Purpose**: Lightweight database operations and testing

**Installation**:
```bash
npm install -g @modelcontextprotocol/server-sqlite
```

**Per-Project Config**:
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

**Capabilities**:
- read_query
- write_query
- create_table, list_tables, describe_table
- append_insight (AI annotations)

**Token Impact**: ~2.5k tokens
**Status**: 🔧 CONFIGURE PER PROJECT

---

## Tier 4: Conditional (Only If You Use These Services)

### Cloud Services

#### AWS Bedrock MCP
**Purpose**: Query Amazon Bedrock Knowledge Bases
**Condition**: If using AWS Bedrock for AI workloads

#### Azure MCP
**Purpose**: Azure Storage, Cosmos DB, Azure CLI
**Condition**: If using Azure cloud services

#### Google Cloud Run MCP
**Purpose**: Deploy and manage Cloud Run services
**Condition**: If deploying to GCP

#### Cloudflare MCP
**Purpose**: Edge config, Workers, DNS management
**Condition**: If using Cloudflare services

---

### Productivity Tools

#### Notion MCP
**Purpose**: Query workspace, pages, databases
**Condition**: If using Notion for documentation

#### Linear MCP
**Purpose**: Issue tracking and project management
**Condition**: If using Linear for project management

#### Jira MCP (Atlassian)
**Purpose**: Work items, sprints, boards
**Condition**: If using Jira for issue tracking

#### Slack MCP
**Purpose**: Team communication, channel operations
**Condition**: If using Slack for team collaboration

---

### Monitoring & Observability

#### Sentry MCP
**Purpose**: Error tracking, performance monitoring
**Condition**: If using Sentry for application monitoring

---

## Token Budget Summary

### Current Setup (Custom MCPs Only)
- Custom MCPs: 52 tools = ~16k tokens (8% of context)
- Built-in tools: ~32 tools = ~10k tokens (5% of context)
- **Total**: 84 tools = ~26k tokens (13% of context)
- **Remaining**: 174k tokens (87%)

### With External MCPs (Current - Installed)
- Custom MCPs: 52 tools = ~16k tokens
- Built-in tools: ~32 tools = ~10k tokens
- GitHub MCP: 51 tools = ~15k tokens
- Package Registry: 5 tools = ~1.5k tokens
- **Total**: 140 tools = **~42.5k tokens (21% of context)**
- **Remaining**: 157.5k tokens (79%)

### Per-Project Database MCPs
- Each database MCP adds: ~2-3k tokens per project
- Only loaded when working on that specific project
- Does NOT affect global token budget
- Configure via `.mcp.json` in project root

---

## Installation Status

### ✅ Completed (2025-09-30)
1. **GitHub MCP** (51 tools, ~15k tokens) - Repository operations
2. **Package Registry MCP** (5 tools, ~1.5k tokens) - Package intelligence

**Total Impact**: 56 tools, ~16.5k tokens

### 📚 Documented for Reference (Not Installing)
- **Containerd MCP** - nerdctl bash commands sufficient
- **Filesystem MCP** - Built-in Read/Write/Edit sufficient
- **Brave Search MCP** - WebSearch tool redundant
- **Exa MCP** - WebSearch tool redundant
- **Semgrep MCP** - Bash + Tech Scanner redundant

### 🔧 Per-Project (Configure as Needed)
- Database MCPs (PostgreSQL, MongoDB, Redis, MySQL, Neo4j, SQLite)
- Configure via `.mcp.json` in project root
- Only loaded when working on specific projects

---

## Configuration Strategy

### Global MCPs
**Location**: `~/.config/claude/mcp_config.json`
**Purpose**: Tools useful across all projects
**Examples**: GitHub, Package Registry, Filesystem, Containerd, Search

### Per-Project MCPs
**Location**: `<project_root>/.mcp.json`
**Purpose**: Project-specific tools (especially databases)
**Examples**: PostgreSQL, MongoDB, Redis, MySQL, Neo4j (project-specific)

### Custom MCPs
**Location**: `~/.claude/mcp_config.json` (git-tracked)
**Purpose**: Your custom-built MCP servers
**Examples**: PRISM, Orchestration, Tech Scanner

**Note**: Two different config files exist:
- `~/.claude/mcp_config.json` - Custom MCPs (uses "servers" key)
- `~/.config/claude/mcp_config.json` - External MCPs (uses "mcpServers" key)

---

## How to Add New MCP Servers

### Global External MCP
1. Install via npm/cargo/docker
2. Add to `~/.config/claude/mcp_config.json`
3. Restart Claude Code

### Per-Project MCP
1. Create `.mcp.json` in project root
2. Configure server with project-specific credentials
3. MCP loads automatically when working in that project

### Custom MCP
1. Develop server in `~/repos/claude_mcp/<name>_mcp/`
2. Add to `~/.claude/mcp_config.json`
3. Commit to git for version control
4. Push to personal claude-config repo

---

## Maintenance Notes

### When to Update This File
- Found new useful MCP server
- Installed/removed MCP server
- Changed configuration strategy
- Discovered new use case for existing MCP

### Version Control
- This file is tracked in ~/.claude git repo
- Commit changes after updates
- Push to origin: `github.com:randalmurphal/claude-config.git`

### Token Budget Monitoring
- Current limit: 25k tokens (Claude Code default)
- Recommended: Increase to 60k for full Tier 1+2 setup
- Update in `~/.config/claude/settings.json`:
  ```json
  {
    "mcpSettings": {
      "maxToolsTokens": 60000
    }
  }
  ```

---

## Quick Reference

### Check Active MCPs
```bash
# List configured servers
cat ~/.claude/mcp_config.json
cat ~/.config/claude/mcp_config.json

# Check project-specific
cat .mcp.json  # in project root
```

### Test MCP Installation
```bash
# Test custom MCP
python3 -m prism_mcp.interfaces.mcp_server
python3 -m orchestration_mcp.mcp_server

# Test containerd MCP
/path/to/mcp-containerd -t http

# Test npm-installed MCP
npx @modelcontextprotocol/server-github
```

### Common Issues
- **MCP not loading**: Restart Claude Code after config changes
- **Too many tools**: Check token budget (increase maxToolsTokens)
- **Database connection fails**: Use per-project config with correct credentials
- **Containerd socket error**: Verify socket path (usually `/run/containerd/containerd.sock`)

---

## Resources

### Official Documentation
- MCP Registry: https://github.com/modelcontextprotocol/registry
- MCP Servers: https://github.com/modelcontextprotocol/servers
- MCP Protocol: https://modelcontextprotocol.io/

### Community Lists
- Awesome MCP Servers: https://github.com/wong2/awesome-mcp-servers
- Docker MCP Catalog: https://hub.docker.com/mcp

### Your Custom MCPs
- PRISM: `/home/randy/repos/claude_mcp/prism_mcp/CLAUDE.md`
- Orchestration: `/home/randy/repos/claude_mcp/orchestration_mcp/CLAUDE.md`
- Tech Scanner: `/home/randy/repos/claude_mcp/tech_scanner_mcp/`

---

## Summary

**Status**: Complete and production-ready ✅

**Current Configuration** (as of 2025-09-30):
- **Custom MCPs**: 52 tools (PRISM, Orchestration, Tech Scanner)
- **External MCPs**: 56 tools (GitHub, Package Registry) - ✅ INSTALLED
- **Built-in Tools**: ~32 tools (Read, Write, Edit, Grep, Bash, etc.)
- **Total**: 140 tools using ~42.5k tokens (21% of context)

**Token Budget**:
- Tools: ~42.5k tokens (21%)
- Available for work: 157.5k tokens (79%)
- Well within limits, no performance concerns

**What Was Installed**:
- ✅ GitHub MCP - Repository operations, PRs, CI/CD monitoring
- ✅ Package Registry MCP - npm/PyPI/Cargo/NuGet package intelligence

**What Was Skipped** (and why):
- ❌ Containerd MCP - nerdctl bash commands work fine
- ❌ Filesystem MCP - Built-in Read/Write/Edit tools sufficient
- ❌ Brave Search, Exa, Semgrep MCPs - Redundant with existing tools

**Performance Outlook**:
- GitHub MCP: Structured API access > bash `gh` command parsing
- Package Registry MCP: Instant package data > web scraping
- ~157k tokens available for actual code and conversation
- No negative performance impact expected

**Ready for Production**: YES 🚀

---

**Last Updated**: 2025-09-30
**Next Review**: When discovering new useful MCPs or changing infrastructure