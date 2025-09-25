# Claude Orchestra Templates

These templates are used by the `/tuning` command to set up new users.

## Files

### settings.template.json
The main Claude configuration file template. Contains:
- Model preference placeholder (`{{USER_MODEL}}`)
- All hook configurations
- Status line configuration

### .credentials.template.json
Template for storing API credentials securely. Includes:
- GitHub token for PR creation
- OpenAI/Anthropic API keys
- Database connection strings
- Cloud service credentials

**Security Note**: The actual `.credentials.json` is gitignored and should never be committed.

### preferences.template.json
User preferences template including:
- Personality mode (vibe)
- Language-specific settings
- Quality tool configurations
- Test coverage requirements

### .mcp.template.json
MCP (Model Context Protocol) server configuration template.
Lists all available MCP servers with their:
- Installation commands
- Required environment variables
- Descriptions

## Usage

Run `/tuning` after cloning the repository to:
1. Set up your personal configuration
2. Install quality tools
3. Configure MCP servers
4. Store credentials securely

## Manual Setup

If you prefer manual setup:

1. Copy `settings.template.json` to `~/.claude/settings.json`
2. Replace `{{USER_MODEL}}` with: opus, sonnet, or haiku
3. Copy other templates as needed and fill in placeholders
4. Create directories:
   ```bash
   mkdir -p ~/.claude/{projects,todos,preferences,quality-tools,preflight,backups}
   ```

## Placeholders

All placeholders use the format `{{PLACEHOLDER_NAME}}` and should be replaced with actual values:

- `{{USER_MODEL}}`: Your preferred Claude model (opus/sonnet/haiku)
- `{{USER_VIBE}}`: Personality mode (solo/concert/duo/mentor)
- `{{PRIMARY_LANGUAGE}}`: Your main programming language
- `{{GITHUB_PERSONAL_ACCESS_TOKEN}}`: Your GitHub PAT
- `{{POSTGRES_CONNECTION_STRING}}`: PostgreSQL connection string
- etc.

## Security

Never commit files containing actual credentials or API keys. The `.gitignore` file is configured to exclude:
- `settings.json` (contains your model preference)
- `.credentials.json` (contains API keys)
- `preferences/` directory (contains personal preferences)
- `.mcp.json` (may contain credentials)