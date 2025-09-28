---
name: pr_review
description: Comprehensive PR review against Jira ticket requirements
---

You are conducting a comprehensive PR review by comparing GitLab changes against Jira requirements.

## Command Usage

`/pr_review <ticket>:<branch>`

Examples:
- `/pr_review INT-3877:develop` - Review INT-3877 against develop branch
- `/pr_review INT-3877:release-6.21.0` - Review INT-3877 against release-6.21.0

## Smart Detection

Handle common variations:
- `INT-3877:dev` → `develop`
- `INT-3877:6.21` → `release-6.21.0`
- `INT-3877:main` → `develop` (if that's your default)
- `INT-3877` → Default to `develop`

## Review Process

### 1. Parse Input & Detect Intent
```python
# Parse ticket:branch format
if ":" in input:
    ticket, branch = input.split(":")
    branch = normalize_branch(branch)  # Handle typos/shortcuts
else:
    ticket = input
    branch = "develop"  # Default

# Detect which MCP/tool to use
if gitlab_mcp_available:
    use_tool = "gitlab_mcp"
elif github_mcp_available:
    use_tool = "github_mcp"
else:
    # Ask before falling back to git
    use_tool = "git_commands" if user_confirms() else None
```

### 2. Gather Context (PARALLEL)

#### Check MCP Availability
First, check if GitLab/GitHub MCP is available:
```python
if not gitlab_mcp_available and not github_mcp_available:
    ask_user: "GitLab/GitHub MCP not available. Continue with git commands? (y/n)"
    if user_says_no:
        return "Review cancelled. Please configure GitLab/GitHub MCP."
    else:
        use_git_fallback = True
```

#### If Using Git Fallback
**IMPORTANT: Never checkout branches without permission**

**Step 1: Check current branch**
```bash
current_branch=$(git branch --show-current)
echo "Currently on branch: $current_branch"
```

**Step 2: Get diff WITHOUT checking out**
```bash
# Fetch latest without checkout
git fetch origin

# If already on the ticket branch
if [[ "$current_branch" == *"$ticket"* ]]; then
    git diff origin/[target_branch]...HEAD
else
    # Compare remote branches without checkout
    git diff origin/[target_branch]...origin/[ticket_branch]
fi

# Get file list without checkout
git diff --name-only origin/[target_branch]...origin/[ticket_branch]

# Get commit messages without checkout
git log origin/[target_branch]..origin/[ticket_branch] --oneline

# View specific file without checkout
git show origin/[ticket_branch]:path/to/file.py
```

**Step 3: Only if checkout absolutely needed:**
```
ask_user: "Currently on [$current_branch]. Need to checkout [$ticket_branch] for deeper analysis. OK? (y/n)"
if yes:
    git stash  # Save any local changes
    git checkout [ticket_branch]
    # do analysis
    git checkout $current_branch  # return to original
    git stash pop  # Restore local changes
else:
    # Continue with remote branch analysis only
```

#### Standard MCP Flow
If MCP is available:
- **Jira**: `mcp__jira__get_issue` for ticket details
- **GitLab/GitHub**: Find PR for ticket branch against target branch

### 3. Analyze Requirements vs Implementation
```markdown
From Jira ticket:
- Acceptance criteria
- Story description  
- Technical requirements
- Related tickets

From GitLab PR:
- Files changed
- Diff analysis
- Commit messages
- PR description
```

### 4. Perform Comprehensive Review

Review ALL aspects:

#### Code Quality
- Clean code principles
- DRY violations
- Complexity issues
- Naming conventions
- Dead code

#### Requirements Coverage
- Each Jira requirement → where implemented
- Missing requirements
- Extra features not in ticket

#### Test Coverage
- New code has tests
- Edge cases covered
- Integration tests present
- Matches our 95%/100% standards

#### Security Review
- No hardcoded secrets
- Input validation
- SQL injection risks
- XSS vulnerabilities
- Authentication/authorization

#### Performance Analysis
- Database query efficiency
- N+1 query problems
- Caching opportunities
- Memory usage
- API call optimization

#### Error Handling
- Specific error types
- User-friendly messages
- Proper logging
- Recovery mechanisms

#### Documentation
- Code comments where needed
- API documentation
- README updates
- Configuration docs

### 5. Generate Review Output

Structure your response as:

```markdown
# PR Review: [TICKET] against [BRANCH]

## ✅ Good (What's Working Well)
- Clean implementation of [feature]
- Excellent test coverage for [component]
- Good error handling in [module]
- Performance optimization with [technique]

## ❌ Issues (Must Fix)
- Missing validation in [file:line]
- SQL injection risk in [file:line]
- No tests for error case in [file:line]
- Breaking change not documented in [file:line]

## 💬 Suggestions for Comments (Copy these to GitLab)

### File: src/scan_processor.py, Line 145
```comment
Consider adding validation for null host_uuid here. We've seen cases where 
Tenable returns null values that cause downstream issues.
```

### File: src/api/endpoints.py, Line 78
```comment
This endpoint needs rate limiting. Suggested: 100 requests/minute per user.
```

### File: tests/test_integration.py, Line 234
```comment
Add test case for empty asset list. This edge case caused issues in production before.
```

## 📝 Documentation Updates Applied
- Updated: project_notes/imports/tenable_sc/README.md
  - Added new caching strategy section
  - Updated data flow diagram
- Updated: project_notes/imports/tenable_sc/REVIEW_NOTES.md
  - Added review findings for INT-3877
```

### 6. Update Documentation

Automatically update project_notes:
- Use Task tool to launch doc-maintainer:
  ```
  "Update documentation based on PR review findings:
   - Component: [affected component]
   - Changes: [what changed]
   - Review notes: [findings to add to REVIEW_NOTES.md]"
  ```

## Smart Branch Detection

Common patterns to handle:
```python
branch_mappings = {
    "dev": "develop",
    "main": "develop",
    "master": "develop",
    "6.22": "release-6.22.0",
    "6.21": "release-6.21.0",
    "6.20": "release-6.20.0",
    "release-6.22": "release-6.22.0",
    "v6.22": "release-6.22.0"
}

def normalize_branch(branch):
    # Direct match
    if branch in branch_mappings:
        return branch_mappings[branch]
    
    # Version pattern (6.XX)
    if re.match(r'\d+\.\d+', branch):
        return f"release-{branch}.0"
    
    # Already correct format
    if branch.startswith("release-"):
        return branch
    
    # Default or unknown
    return branch if "/" in branch else "develop"
```

## Error Handling

### MCP Not Available
```python
if not gitlab_mcp and not github_mcp:
    print("⚠️ GitLab/GitHub MCP not configured")
    response = ask_user("Continue with git commands? (y/n)")
    if response == 'n':
        exit("Configure MCP with: npx -y @aashari/mcp-server-gitlab")
```

### Git Fallback Mode Rules
1. **NEVER checkout branches without asking**
2. **Use origin/branch references** to avoid local checkouts
3. **Prefer diff and log commands** that work on remote refs
4. **If checkout needed**, always ask permission first
5. **Return to original branch** after any checkout

### Jira Not Available
If Jira MCP not found:
- Continue with code review only
- Note: "⚠️ Could not verify against Jira requirements"

### GitLab/GitHub PR Not Found
When using MCP but PR not found:
- Check if branch exists locally/remotely
- Suggest: "No PR found. Create with: gh pr create..."

### Branch Typo Detection
- Suggest: "Did you mean 'develop'? (found 'devlop')"
- List available branches if unclear

## Key Principles

1. **Always do FULL review** - Don't skip any aspect
2. **Be specific** - Include file:line references
3. **Actionable feedback** - Provide exact fixes or code snippets
4. **Document everything** - Auto-update project_notes
5. **Format for GitLab** - Make comments ready to copy/paste

## After Review Complete

Always end with:
- Count of issues found (critical/high/medium/low)
- Documentation update confirmation
- Reminder: "Copy comment suggestions to GitLab PR if appropriate"