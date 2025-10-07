# MCP Server Setup Instructions

## Understanding MCP Scopes

Claude Code has three scope levels for MCP servers. **Use local scope for project-specific servers** - it works seamlessly across all subdirectories in the git repo.

### Scope Comparison

| Scope | Command | Config Location | Works In | Use Case |
|-------|---------|----------------|----------|----------|
| **local** (default) | `claude mcp add` | `~/.claude.json` | All subdirs in git repo | ✅ **Best for project-specific servers** |
| project | `claude mcp add -s project` | `.mcp.json` | Requires approval settings | Team-sharable, checked into git |
| user | `claude mcp add -s user` | `~/.claude.json` | All projects everywhere | Global tools |

### Quick Reference

**Add project-specific MCP server (recommended):**
```bash
cd /path/to/your/repo
claude mcp add server-name command-or-url -e KEY=value
# Uses local scope by default - works in all subdirectories!
```

**List servers:**
```bash
claude mcp list
```

**Remove server:**
```bash
claude mcp remove server-name       # Removes from local scope
claude mcp remove -s user server-name   # Removes from user scope
```

### Troubleshooting Scope Issues

**Problem:** MCP server works in git root but not subdirectories
- **Cause:** Server added with `-s project` scope, requires `enableAllProjectMcpServers: true`
- **Fix:** Remove and re-add with local scope (default):
  ```bash
  claude mcp remove -s project server-name
  claude mcp add server-name command -e KEY=value
  ```

**Problem:** Server shows in .mcp.json but doesn't load
- **Cause:** Project scope requires approval in `.claude/settings.local.json`
- **Fix:** Use local scope instead (stores in `~/.claude.json` per-project)

---

## ObsidianPilot MCP Server

**Why ObsidianPilot?** 100-1000x faster than REST API-based MCP servers with full search capabilities including frontmatter, tags, dates, and regex.

### Prerequisites

- Python 3.10+
- Obsidian vault on local filesystem

### Installation

1. **Install `uv` (Python package manager):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   This installs to `~/.local/bin/uv` and `~/.local/bin/uvx`

2. **Configure Claude Code:**

   Add to `~/.claude.json` under `mcpServers`:

   ```json
   "obsidian": {
     "type": "stdio",
     "command": "/home/rmurphy/.local/bin/uvx",
     "args": ["obsidianpilot"],
     "env": {
       "OBSIDIAN_VAULT_PATH": "/path/to/your/obsidian/vault"
     }
   }
   ```

   **Important:**
   - Command must be lowercase `obsidianpilot` (not `ObsidianPilot`)
   - Use full path to `uvx` (not just `uvx`)
   - Vault path can be WSL or Windows (`/mnt/c/...`)

3. **Restart Claude Code**

   ObsidianPilot will build a SQLite index on first run (10-30 seconds for medium vaults).

### Vault Path Configuration

**WSL Native (Fastest):**
```json
"OBSIDIAN_VAULT_PATH": "/home/username/obsidian-notes"
```
- ✅ Maximum speed (instant writes)
- ❌ Obsidian accesses via `\\wsl$\Ubuntu\...`

**Windows Filesystem (Recommended for Obsidian GUI):**
```json
"OBSIDIAN_VAULT_PATH": "/mnt/c/Users/username/Documents/obsidian-notes"
```
- ✅ Easy Obsidian access from Windows
- ✅ Still much faster than REST API
- ⚠️ Slower than WSL native (but acceptable)

### Features

**Search Capabilities:**
- Full-text search with SQLite FTS5 (boolean operators: AND, OR, NOT)
- Frontmatter property search with operators (=, !=, >, <, contains)
- Date-based search (created/modified, within/exactly X days)
- Regex search with timeout protection
- Tag search (hierarchical tags supported)
- Path filtering

**Performance:**
- File/directory creation: Instant (direct filesystem)
- Searches: <0.5 seconds on large vaults
- No Obsidian plugin required
- Works with Obsidian closed or open

### Available Tools

- `mcp__obsidian__list_notes_tool` - List notes in vault
- `mcp__obsidian__create_note_tool` - Create notes
- `mcp__obsidian__read_note_tool` - Read note content
- `mcp__obsidian__update_note_tool` - Update notes
- `mcp__obsidian__delete_note_tool` - Delete notes
- `mcp__obsidian__search_notes` - Full-text search
- `mcp__obsidian__search_by_property` - Frontmatter search
- `mcp__obsidian__search_by_date` - Date-based search
- `mcp__obsidian__search_by_regex` - Regex search
- Many more tag management, link management tools

### Troubleshooting

**Tools not available after restart:**
- Verify `uvx` is at correct path: `which uvx` or `ls ~/.local/bin/uvx`
- Check config has lowercase `obsidianpilot` in args
- Verify vault path exists: `ls /path/to/vault`

**Slow writes on Windows filesystem:**
- This is expected with `/mnt/c/` paths (WSL→Windows overhead)
- Still much faster than REST API approach
- For maximum speed, use WSL native path

**Index not building:**
- Check vault path is correct
- Ensure vault has `.md` files
- Check Claude Code logs for errors

### Comparison with Other MCP Servers

**cyanheads/obsidian-mcp-server (Previous):**
- ❌ Slow writes (~1 second files, minutes directories)
- ✅ Good search via REST API
- ❌ Requires Obsidian running + REST API plugin

**StevenStavrakis/obsidian-mcp:**
- ✅ Fast writes (direct filesystem)
- ❌ Limited search (no frontmatter/tag/date filtering)

**ObsidianPilot (Current):**
- ✅ Fast writes (direct filesystem)
- ✅ Excellent search (all features + SQLite FTS5)
- ✅ No plugin required
- ✅ 100-1000x faster

### Integration with Slash Commands

ObsidianPilot powers these commands:
- `/notes-start [topic]` - Load context with fast queries
- `/notes-update [topic]` - Capture findings with instant writes
- `/consolidate [topic]` - Clean up notes efficiently

See `~/.claude/commands/` for full documentation.

### Repository

GitHub: https://github.com/that0n3guy/ObsidianPilot

### Notes

- ObsidianPilot reads/writes markdown files directly
- Works alongside Obsidian (no conflicts)
- Changes made by ObsidianPilot appear in Obsidian immediately
- Changes made in Obsidian are visible to ObsidianPilot
- SQLite index maintained in memory for fast searches

---

## Atlassian Jira MCP Server

**Package:** `@aashari/mcp-server-atlassian-jira` - Full-featured Jira integration with project listing, issue search (JQL), and dev info (commits, PRs).

### Prerequisites

- Node.js 18+
- Atlassian API token (create at: https://id.atlassian.com/manage-profile/security/api-tokens)
- Jira Cloud instance (e.g., `yourcompany.atlassian.net`)

### Installation

1. **Install package globally:**
   ```bash
   npm install -g @aashari/mcp-server-atlassian-jira
   ```

2. **Get credentials:**
   - Site name: Your Atlassian subdomain (e.g., `fortressinfosec` from `fortressinfosec.atlassian.net`)
   - User email: Your Atlassian account email
   - API token: Generate at https://id.atlassian.com/manage-profile/security/api-tokens

3. **Add to Claude Code (local scope - works in project subdirs):**
   ```bash
   cd /path/to/your/project
   claude mcp add jira mcp-atlassian-jira \
     -e ATLASSIAN_SITE_NAME=yourcompany \
     -e ATLASSIAN_USER_EMAIL=you@company.com \
     -e ATLASSIAN_API_TOKEN=your_api_token_here
   ```

4. **Verify installation:**
   ```bash
   claude mcp list
   # Should show: jira: mcp-atlassian-jira - ✓ Connected
   ```

### Available Tools

- `mcp__jira__ls-projects` - List all Jira projects
- `mcp__jira__get-project` - Get project details
- `mcp__jira__ls-issues` - List issues in project
- `mcp__jira__search-issues` - Search using JQL
- `mcp__jira__get-issue` - Get issue details
- `mcp__jira__get-dev-info` - View commits, PRs for issue

### Usage Examples

**List projects:**
```
Show me all my Jira projects
```

**Search issues:**
```
Find all open issues assigned to me in project ABC
```

**Get issue details:**
```
Get details for INT-3930
```

### Troubleshooting

**Server not connecting:**
- Verify API token is valid (test at https://yourcompany.atlassian.net)
- Check site name doesn't include `.atlassian.net` (just `yourcompany`)
- Ensure email matches Atlassian account

**JQL search not working:**
- Use Jira's JQL syntax (e.g., `project = ABC AND status = Open`)
- Test JQL in Jira's search interface first

**Tools not showing in subdirectories:**
- Check server was added with local scope (default), not project scope
- Run `claude mcp get jira` to verify configuration
- See "Understanding MCP Scopes" section above

### Repository

GitHub: https://github.com/aashari/mcp-server-atlassian-jira

---

## MongoDB MCP Server

**Package:** `mongodb-mcp-server` - Direct MongoDB access for queries, aggregations, and CRUD operations.

### Prerequisites

- MongoDB instance (local or remote)
- Connection string with auth credentials

### Installation

1. **Package is auto-installed via npx** (no global install needed)

2. **Get connection string:**
   ```
   mongodb://username:password@host:port/database?authSource=admin
   ```

3. **Add to Claude Code (local scope):**
   ```bash
   cd /path/to/your/project
   claude mcp add mongodb npx -y mongodb-mcp-server \
     "mongodb://username:password@host:port/database?authSource=admin"
   ```

   Or with environment variable:
   ```bash
   claude mcp add mongodb npx -y mongodb-mcp-server \
     -e MDB_MCP_CONNECTION_STRING="mongodb://username:password@host:port/database?authSource=admin"
   ```

4. **Verify connection:**
   ```bash
   claude mcp list
   # Should show: mongodb: npx -y mongodb-mcp-server - ✓ Connected
   ```

### Available Tools

- `mcp__mongodb__list-databases` - List all databases
- `mcp__mongodb__list-collections` - List collections in database
- `mcp__mongodb__find` - Query documents
- `mcp__mongodb__aggregate` - Run aggregation pipelines
- `mcp__mongodb__insert-many` - Insert documents
- `mcp__mongodb__update-many` - Update documents
- `mcp__mongodb__delete-many` - Delete documents
- `mcp__mongodb__count` - Count documents
- `mcp__mongodb__collection-schema` - Infer collection schema

### Usage Examples

**Query documents:**
```
Find all users in the rthree database where subscription_id = $SUB1
```

**Aggregation:**
```
Count vulnerabilities by severity in the detectedVulnerabilities collection
```

**Schema inspection:**
```
Show me the schema for the assets collection
```

### Troubleshooting

**Connection failed:**
- Verify MongoDB is running: `mongosh "your-connection-string"`
- Check network access (firewall, security groups)
- Ensure auth credentials are correct

**Database not found:**
- List databases first: `mcp__mongodb__list-databases`
- Check database name in connection string

**Slow queries:**
- Large result sets are limited by `responseBytesLimit` (default 1MB)
- Use `filter` and `limit` parameters for targeted queries
- Consider using aggregation for complex operations

### Repository

npm: https://www.npmjs.com/package/mongodb-mcp-server
