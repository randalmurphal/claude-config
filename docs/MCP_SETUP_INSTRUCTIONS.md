# MCP Server Setup Instructions

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
