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

## Recommended External MCPs

### Tier 1: Essential (Global - High Priority)

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
**Status**: ⏳ PENDING INSTALL

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
**Status**: ⏳ PENDING INSTALL

---

#### 3. Filesystem MCP (~10 tools) - SECURITY & SEARCH
**Value**: 🔥🔥
**Purpose**: Sandboxed file operations with advanced search and metadata

**Capabilities**:
- File Operations: read_file, write_file, edit_file (with pattern matching)
- Directory Management: create_directory, list_directory, move_file
- Search & Metadata: search_files, get_file_info (size, permissions, timestamps)
- Security: Sandboxed operations, read-only mounts, directory restrictions
- Advanced Editing: Diff previews, pattern matching

**Why Useful** (vs built-in Read/Write/Edit):
- Security sandboxing (restrict to specific directories)
- Advanced search across files (better than grep for complex queries)
- Metadata inspection (file sizes, permissions, timestamps)
- Pattern matching in edits
- Batch operations

**Installation**:
```bash
npm install -g @modelcontextprotocol/server-filesystem
```

**Configuration** (with allowed directories):
```json
"filesystem": {
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-filesystem",
    "/home/randy/repos",
    "/tmp"
  ]
}
```

**Token Impact**: ~3k tokens
**Status**: ⏳ PENDING INSTALL

---

#### 4. Containerd MCP (~15 tools) - INFRASTRUCTURE
**Value**: 🔥🔥
**Purpose**: Container operations via containerd (works with nerdctl infrastructure)

**Capabilities**:
- Container Management: list, create, stop, delete containers
- Pod Operations: create, stop, delete pods
- Image Management: list, pull, manage container images
- Execution: Execute commands inside running containers
- Version & Status: Check containerd version and status

**Why This Instead of Docker MCP**:
- Works with containerd socket (what nerdctl uses)
- Native integration with existing nerdctl infrastructure
- No Docker daemon required

**Installation**:
```bash
# Requires Rust
git clone https://github.com/jokemanfire/mcp-containerd
cd mcp-containerd
cargo build --release
```

**Configuration**:
```json
"containerd": {
  "command": "/path/to/mcp-containerd/target/release/mcp-containerd",
  "args": ["-t", "http"]
}
```

**Default Socket**: `unix:///run/containerd/containerd.sock`
**Token Impact**: ~5k tokens
**Status**: ⏳ PENDING INSTALL

**GitHub**: https://github.com/jokemanfire/mcp-containerd

---

### Tier 2: High Value (Global - Recommended)

#### 5. Brave Search MCP - RESEARCH
**Value**: 🔥
**Purpose**: Real-time web research for AI agents

**Capabilities**:
- Real-time web search
- Up-to-date information beyond training data
- Research technical questions with current answers

**Installation**:
```bash
npm install -g @modelcontextprotocol/server-brave-search
```

**Configuration**:
```json
"brave-search": {
  "command": "mcp-server-brave-search",
  "env": {
    "BRAVE_API_KEY": "your-brave-api-key"
  }
}
```

**Token Impact**: ~1k tokens
**Status**: ⏳ PENDING INSTALL

---

#### 6. Exa MCP - AI-OPTIMIZED SEARCH
**Value**: 🔥
**Purpose**: Search engine built specifically for AI agents

**Capabilities**:
- AI-optimized search results
- Better context extraction than generic search
- Technical query optimization

**Installation**:
```bash
npm install -g @agentic/exa
```

**Configuration**:
```json
"exa": {
  "command": "npx",
  "args": ["-y", "@agentic/exa"],
  "env": {
    "EXA_API_KEY": "your-exa-api-key"
  }
}
```

**Token Impact**: ~1.5k tokens
**Status**: ⏳ PENDING INSTALL

---

#### 7. Semgrep MCP - SECURITY ANALYSIS
**Value**: 🔥
**Purpose**: Static analysis and vulnerability detection

**Capabilities**:
- Static code analysis
- Security vulnerability detection
- Pattern-based code scanning
- Complements Tech Scanner MCP

**Installation**:
```bash
npm install -g @modelcontextprotocol/server-semgrep
```

**Configuration**:
```json
"semgrep": {
  "command": "mcp-server-semgrep"
}
```

**Token Impact**: ~2k tokens
**Status**: ⏳ PENDING INSTALL

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
- Remaining: 184k tokens (92%)

### With Tier 1 (Essential Global MCPs)
- Custom MCPs: 52 tools = ~16k tokens
- GitHub: 51 tools = ~15k tokens
- Package Registry: 5 tools = ~1.5k tokens
- Filesystem: 10 tools = ~3k tokens
- Containerd: 15 tools = ~5k tokens
- **Total Tier 1**: 133 tools = **~40.5k tokens (20% of context)**
- **Remaining**: 159.5k tokens (80%)

### With Tier 1 + Tier 2 (Recommended Setup)
- Tier 1: ~40.5k tokens
- Brave Search: ~1k tokens
- Exa: ~1.5k tokens
- Semgrep: ~2k tokens
- **Total**: 145 tools = **~45k tokens (22.5% of context)**
- **Remaining**: 155k tokens (77.5%)

### Per-Project Database MCPs
- Each database MCP adds: ~2-3k tokens per project
- Only loaded when working on that specific project
- Does NOT affect global token budget

---

## Installation Priority

### Phase 1: Core Infrastructure (Do First)
1. **Containerd MCP** - Replace nerdctl bash commands
2. **GitHub MCP** - Essential for repository work
3. **Package Registry MCP** - Instant dependency intelligence

**Impact**: 71 tools, ~21.5k tokens

### Phase 2: Enhanced Capabilities (Do Next)
4. **Filesystem MCP** - Sandboxed file ops with search
5. **Brave Search MCP** - Real-time research

**Impact**: +11 tools, +4k tokens

### Phase 3: Code Quality (Optional)
6. **Semgrep MCP** - Security analysis
7. **Exa MCP** - AI-optimized search

**Impact**: +TBD tools, +3.5k tokens

### Phase 4: Per-Project (As Needed)
- Database MCPs configured per project via `.mcp.json`
- Only installed/loaded when working on specific projects

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

**Last Updated**: 2025-09-30
**Next Review**: When discovering new useful MCPs or changing infrastructure