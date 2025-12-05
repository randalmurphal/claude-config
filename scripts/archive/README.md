# Claude Scripts

Lightweight bash scripts that replace heavy MCP tools. Each script is ~100 lines vs. 80,000 tokens of MCP functions.

## Philosophy

**Use scripts instead of MCP when:**
- You need 1-2 operations from an 80+ function MCP
- The operation is simple (API GET request)
- You want full control over output format
- Token budget matters

**Use MCP when:**
- You need many operations from the service
- Complex workflows with state management
- Auto-generated bindings are valuable

## Available Scripts

### Git Scripts

#### git-worktree

Smart git worktree manager for parallel development.

**Usage:**
```bash
git-worktree auth api database     # Create 3 worktrees
git-worktree --list                # List all worktrees
git-worktree --cleanup             # Remove all worktrees
```

**What it does:**
- Auto-detects repo, creates organized worktree structure
- Supports multiple modules in parallel
- Manages cleanup with --cleanup flag

**Status:** ✅ Production-ready

---

### GitLab Scripts

All GitLab scripts require credentials in `~/.claude/scripts/.gitlab-credentials` (see Credential Management below).

#### gitlab-mr-comments

Fetch merge request discussions/comments for a ticket.

**Usage:** `gitlab-mr-comments INT-3877`

**Output:** Formatted markdown with all MR comments, resolved/unresolved status

**Status:** ✅ Tested with INT-3997

---

#### gitlab-list-mrs

List merge requests with filters (state, author, assignee, labels).

**Usage:**
```bash
gitlab-list-mrs --state opened
gitlab-list-mrs --author rmurphy --state opened
gitlab-list-mrs --assignee alice --labels bug,urgent
```

**Output:** Formatted markdown list with MR details

**Status:** ✅ Production-ready

---

#### gitlab-create-mr

Create a new merge request.

**Usage:**
```bash
gitlab-create-mr INT-3877-auth develop "INT-3877: Add rate limiting" "Description here"
```

**Output:** MR URL and IID

**Status:** ✅ Production-ready

---

#### gitlab-comment-mr

Add a comment to a merge request.

**Usage:** `gitlab-comment-mr 1234 "LGTM, approved"`

**Output:** Comment ID and confirmation

**Status:** ✅ Production-ready

---

#### gitlab-update-mr

Update merge request metadata (title, description, assignee, labels).

**Usage:**
```bash
gitlab-update-mr 1234 --title "Updated title" --labels "bug,urgent"
gitlab-update-mr 1234 --assignee jdoe --description "New description"
```

**Output:** Updated MR details

**Status:** ✅ Production-ready

---

#### gitlab-inline-comment

Add inline comment to specific code line in a merge request.

**Usage:**
```bash
gitlab-inline-comment INT-3877 src/auth.py 45 "Missing validation here"
gitlab-inline-comment 1234 src/auth.py 45 "Missing validation here"  # Can use MR IID directly
```

**Output:** Discussion ID and confirmation on success

**What it does:**
- Accepts ticket ID or MR IID as first argument
- Auto-resolves ticket to MR if ticket provided
- Uses GitLab position API for inline comments
- Adds comment to specific line in specific file

**Status:** ✅ Production-ready

---

### Jira Scripts

All Jira scripts require credentials in `~/.claude/scripts/.jira-credentials` (see Credential Management below).

#### jira-get-issue

Fetch comprehensive Jira issue details including ALL custom fields, comments, and related tickets.

**Usage:**
```bash
jira-get-issue INT-4013              # Fetch with related tickets
jira-get-issue INT-4013 --no-related # Skip related ticket fetch
```

**Output:** Complete ticket context in markdown format including:
- Description, Acceptance Criteria
- **Developer Checklist** (customfield_11848) - technical implementation details, data structures, API changes
- **Test Plan** (customfield_11003) - testing strategy and test cases
- **Dev Complete Checklist**, **Implementation Checklist** (if present)
- **ALL Comments** - full pagination, no limits, with author and date
- **Related Ticket Details (FULL)** - fetches COMPLETE data for FE/BE pairs, clones, blocking tickets
  - Each related ticket includes: Description, Developer Checklist, Test Plan, Comments
  - No recursion (only fetches related tickets of main ticket)
  - Perfect for FE/BE coordination

**Output size:** ~80 lines (basic ticket) to ~1100 lines (ticket with Developer Checklist, Test Plan, Comments, and 5 related tickets)

**Example:** `jira-get-issue PLAT-54` returns:
- PLAT-54 full data (343 lines)
- PLAT-53 (FE pair) full data with Developer Checklist, Test Plan, Comments
- 4 other related tickets with full data
- Total: ~1100 lines of comprehensive context

**Status:** ✅ Production-ready, tested with INT-4013, AIM-418, PLAT-54

---

#### jira-list-tickets

List Jira tickets with filters (project, status, assignee, type, custom JQL).

**Usage:**
```bash
jira-list-tickets --project INT
jira-list-tickets --status "In Progress" --assignee "user@example.com"
jira-list-tickets --jql "project = INT AND status = Done"
```

**Output:** Formatted markdown list with ticket details

**Status:** ✅ Production-ready

---

#### jira-list-sprint

Show current sprint issues for a board.

**Usage:**
```bash
jira-list-sprint        # Use default board from credentials
jira-list-sprint 123    # Use specific board ID
```

**Output:** Sprint details with issue status summary

**Status:** ✅ Production-ready

---

#### jira-create-ticket

Create a new Jira ticket.

**Usage:**
```bash
jira-create-ticket INT Task "Add rate limiting" "Description here"
```

**Output:** Created ticket key and URL

**Status:** ✅ Production-ready

---

#### jira-comment-ticket

Add a comment to a Jira ticket.

**Usage:** `jira-comment-ticket INT-3877 "Work completed and tested"`

**Output:** Comment ID and confirmation

**Status:** ✅ Production-ready

---

#### jira-update-ticket

Update Jira ticket fields (description, assignee, status, priority, labels).

**Usage:**
```bash
jira-update-ticket INT-3877 --description "Updated" --priority High
jira-update-ticket INT-3877 --status "In Progress" --assignee "user@example.com"
```

**Output:** Updated ticket details

**Status:** ✅ Production-ready

---

#### jira-log-work

Log time spent on a Jira ticket.

**Usage:**
```bash
jira-log-work INT-3877 "2h 30m" "Implemented rate limiting logic"
jira-log-work INT-3877 "1d 4h"
```

**Time format:** `2h`, `1d 4h`, `30m`, `1w 2d 3h 30m` (w=weeks, d=days, h=hours, m=minutes)

**Output:** Worklog ID and confirmation

**Status:** ✅ Production-ready

---

#### jira-link-tickets

Link two Jira tickets with a relationship.

**Usage:**
```bash
jira-link-tickets INT-3877 "Blocks" INT-3878
jira-link-tickets INT-3877 "Relates to" INT-3900
```

**Link types:** Blocks, Relates to, Duplicates, Clones, Causes (case-sensitive)

**Output:** Link confirmation

**Status:** ✅ Production-ready

---

## Credential Management

Scripts that need API access use gitignored credential files in this directory.

### GitLab Credentials

**File:** `~/.claude/scripts/.gitlab-credentials`

**Create from example:**
```bash
cp ~/.claude/scripts/.gitlab-credentials.example ~/.claude/scripts/.gitlab-credentials
# Edit with your credentials
```

**Required variables:**
- `GITLAB_PERSONAL_ACCESS_TOKEN` - Your GitLab personal access token (scope: api)
- `GITLAB_API_URL` - API endpoint (default: `https://gitlab.com/api/v4`)
- `GITLAB_PROJECT_ID` - Your project ID (found on project page)

**Get your token:**
1. Go to: https://gitlab.com/-/profile/personal_access_tokens
2. Create token with `api` scope
3. Copy the token (starts with `glpat-`)

**Find project ID:**
- On your project's GitLab page
- Look under the project name (e.g., "Project ID: 29007973")

**Self-hosted GitLab:**
- Change `GITLAB_API_URL` to your instance (e.g., `https://gitlab.yourcompany.com/api/v4`)

---

### Jira Credentials

**File:** `~/.claude/scripts/.jira-credentials`

**Create from example:**
```bash
cp ~/.claude/scripts/.jira-credentials.example ~/.claude/scripts/.jira-credentials
# Edit with your credentials
```

**Required variables:**
- `ATLASSIAN_API_TOKEN` - Your Atlassian API token
- `ATLASSIAN_SITE_NAME` - Your Jira site name (e.g., "fortressinfosec")
- `ATLASSIAN_USER_EMAIL` - Your email address

**Optional variables:**
- `JIRA_DEFAULT_BOARD_ID` - Default board ID for sprint queries

**Get your API token:**
1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Copy the token (starts with `ATATT`)

**Find your site name:**
- Your Jira URL format: `https://YOUR-SITE-NAME.atlassian.net`

**Find board ID (optional):**
- Visit your board in Jira
- Check URL: `https://your-site.atlassian.net/jira/software/projects/INT/boards/123`
- Board ID is the number at the end (123 in this example)

### Security

**Credentials are gitignored:**
- `~/.claude/.gitignore` has pattern: `scripts/*-credentials`
- Never commit credential files
- Each script validates credentials exist before running
- Clear error messages guide credential setup

**Error handling:**
- Exit code 4 = credentials missing
- Script stops and shows setup instructions
- No partial execution without credentials

---

## Token Savings

| Tool | Functions | Tokens | Scripts Implemented | Script Tokens | Savings |
|------|-----------|--------|---------------------|---------------|---------|
| **GitLab MCP** | 82 | 80,000 | 5 scripts | ~1,000 | **98.75%** |
| **Jira MCP** | ~30 | ~40,000 | 7 scripts | ~1,750 | **95.6%** |
| **Combined** | 112 | **120,000** | **12 scripts** | **~2,750** | **97.7%** |

**Real Results - /pr_review Workflow:**

**Before:**
- GitLab MCP: 80,000 tokens (loaded 82 functions, used 1)
- Jira MCP: 40,000 tokens (loaded ~30 functions, used 1)
- **Total: 120,000 tokens** (60% of 200k budget)
- Available for code analysis: 80,000 tokens (40%)

**After:**
- gitlab-mr-comments: 200 tokens
- jira-get-issue: 250 tokens
- **Total: 450 tokens** (0.2% of 200k budget)
- Available for code analysis: 199,550 tokens (99.8%)

**Impact:**
- **119,550 tokens saved per /pr_review conversation** (99.6% reduction)
- **149% increase** in available budget for code analysis
- All 12 scripts tested and working
- Same credentials as MCPs (no new setup required)
- Now have full CRUD operations for both GitLab and Jira without token bloat

---

## Creating New Scripts

### Template

```bash
#!/usr/bin/env bash
set -euo pipefail

# script-name - Brief description
#
# Usage: script-name <args>
# Example: script-name foo bar
#
# Exit codes: 0 = success, 1 = arg error, 2 = not found, 3 = API error, 4 = credentials missing

# Get script directory for credentials
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREDS_FILE="${SCRIPT_DIR}/.service-credentials"

# Function to show credential setup instructions
show_credential_instructions() {
    cat >&2 <<'EOF'
❌ Credentials not found or incomplete.

STOP: This script requires API credentials to be configured.

Please create the file: ~/.claude/scripts/.service-credentials

With the following content:

    SERVICE_API_TOKEN="your-token-here"
    SERVICE_API_URL="https://api.service.com"

How to get these values:
[Instructions here]

EOF
    exit 4
}

# Validate credentials
if [ ! -f "$CREDS_FILE" ]; then
    echo "❌ Credentials file not found: $CREDS_FILE" >&2
    show_credential_instructions
fi

source "$CREDS_FILE"

if [ -z "${SERVICE_API_TOKEN:-}" ]; then
    echo "❌ SERVICE_API_TOKEN not set in $CREDS_FILE" >&2
    show_credential_instructions
fi

# Script logic here
```

### Best Practices

1. **Exit codes:**
   - 0 = success
   - 1 = usage/argument error
   - 2 = resource not found
   - 3 = API/network error
   - 4 = credentials missing

2. **Error messages:**
   - Send errors to stderr: `echo "Error" >&2`
   - Include context: what failed, why, what to do
   - Use emojis for clarity: ❌ ⚠️ ✅

3. **Output format:**
   - Structured (easy to parse)
   - Human-readable (can read in terminal)
   - Use markdown for formatting

4. **Credentials:**
   - Always validate before API calls
   - Show clear setup instructions
   - Never hardcode tokens

5. **Git check:**
   - After creating, verify it's tracked: `git status`
   - Verify credentials ignored: `git check-ignore -v scripts/.service-credentials`

---

## Testing

**Test happy path:**
```bash
./script-name valid-input
echo $?  # Should be 0
```

**Test error cases:**
```bash
./script-name  # Missing argument - exit 1
./script-name nonexistent  # Not found - exit 2
mv .service-credentials .backup && ./script-name valid-input  # Missing creds - exit 4
```

**Test in /pr_review workflow:**
- Use script in command
- Verify output format works with agents
- Check performance (should be <2 seconds)

---

## Adding to .gitignore

Already configured in `~/.claude/.gitignore`:

```gitignore
# Script credentials (scripts/.gitlab-credentials, scripts/.jira-credentials, etc)
scripts/*-credentials
scripts/.gitlab-credentials
scripts/.jira-credentials
scripts/.aws-credentials
```

Pattern `scripts/*-credentials` catches all credential files.

---

## Maintenance

**When to update:**
- API changes (rarely for stable APIs like GitLab/Jira)
- New fields needed in output
- Performance optimization

**When to replace with MCP:**
- Using >5 operations from same service
- Complex state management needed
- Auto-generated bindings save significant time

**When to add new script:**
- Heavy MCP tool used for 1-2 operations
- Token budget becoming constrained
- Custom output format needed
