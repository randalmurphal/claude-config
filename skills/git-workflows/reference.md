# Git Workflows Reference

Detailed examples, edge cases, and advanced patterns for Git workflows.

**Related:** [SKILL.md](./SKILL.md) for quick reference and core patterns.

---

## Table of Contents

- [Git Worktrees: Detailed Workflows](#git-worktrees-detailed-workflows)
- [Interactive Rebase: Advanced Patterns](#interactive-rebase-advanced-patterns)
- [Git Bisect: Complex Scenarios](#git-bisect-complex-scenarios)
- [Branch Strategies: Detailed Workflows](#branch-strategies-detailed-workflows)
- [Conflict Resolution: Advanced Techniques](#conflict-resolution-advanced-techniques)
- [Cherry-Picking: Edge Cases](#cherry-picking-edge-cases)
- [Submodules: Advanced Operations](#submodules-advanced-operations)
- [Git Hooks and Automation](#git-hooks-and-automation)

---

## Git Worktrees: Detailed Workflows

### Worktree Structure Deep Dive

**Why the `.worktrees` pattern?**
```
Bad (in main repo):
  ~/projects/myapp/
  ~/projects/myapp-auth/         # Looks like separate project
  ~/projects/myapp-api/          # Confusing structure

Good (separate worktrees dir):
  ~/projects/myapp/              # Main repo
  ~/projects/.worktrees/myapp/
    ├── wt-auth/
    ├── wt-api/
    └── wt-hotfix/
```

**Benefits:**
- Clear separation from main repo
- Easy to find all worktrees
- Clean `ls ~/projects` output
- Predictable structure for scripts

### Complete Parallel Development Example

**Scenario:** Adding authentication, updating API, and fixing database migration simultaneously.

```bash
# 1. Setup
cd ~/projects/myapp
git checkout main
git pull

# 2. Create worktrees
git-worktree auth api db-fix

# 3. Terminal 1: Auth work
cd ~/projects/.worktrees/myapp/wt-auth
git status  # On wt-auth branch
# Implement authentication
git add src/auth/
git commit -m "Add JWT authentication"
git push -u origin wt-auth

# 4. Terminal 2: API work (parallel)
cd ~/projects/.worktrees/myapp/wt-api
# Update API endpoints
git add src/api/
git commit -m "Add auth middleware to API"
git push -u origin wt-api

# 5. Terminal 3: DB fix (parallel)
cd ~/projects/.worktrees/myapp/wt-db-fix
# Fix migration
git add migrations/
git commit -m "Fix user table migration"
git push -u origin wt-db-fix

# 6. Create pull requests (all 3 in parallel)
cd ~/projects/.worktrees/myapp/wt-auth
gh pr create --title "Add JWT authentication" --body "..."

cd ~/projects/.worktrees/myapp/wt-api
gh pr create --title "Add auth middleware" --body "..."

cd ~/projects/.worktrees/myapp/wt-db-fix
gh pr create --title "Fix user migration" --body "..."

# 7. After PRs merged, cleanup
cd ~/projects/myapp
git checkout main
git pull
git-worktree --cleanup
```

### Emergency Hotfix During Feature Work

**Scenario:** Working on feature, production bug reported.

```bash
# Currently working on feature
cd ~/projects/myapp
git status  # Modified files, uncommitted work

# Create hotfix worktree (no stashing needed!)
git-worktree hotfix

# Terminal 2: Fix production bug
cd ~/projects/.worktrees/myapp/wt-hotfix
git log --oneline -5  # Find good commit
git checkout v1.2.3  # Start from production tag
git checkout -b hotfix/security-fix
# Make fix
git commit -m "Fix security vulnerability"
git push -u origin hotfix/security-fix
gh pr create --base release/v1.2 --title "Security hotfix" --body "..."

# Terminal 1: Continue feature work (uninterrupted)
cd ~/projects/myapp
# Your work still there, no stashing needed
git status  # Same modified files
```

### Worktree vs Branch Switching

| Scenario | Worktree | Branch Switching |
|----------|----------|-----------------|
| Parallel features | Multiple terminals, no context switch | Stash → switch → unstash (context loss) |
| Emergency fix | New worktree, main work untouched | Stash → branch → fix → back (disruptive) |
| Code review | Worktree for review branch | Stash → checkout review → back |
| Build time | Work continues in main while building in worktree | Wait for build in one place |

---

## Interactive Rebase: Advanced Patterns

### Pattern 1: Squash All Commits Into One

**Before:**
```
* e4f5a6b WIP: more tests
* d3c4b5a Fix linting errors
* c2b3a4b Add tests
* b1a2c3d Fix typo in docstring
* a0b1c2d Add user authentication feature
```

**Interactive rebase:**
```bash
git rebase -i main

# Editor opens with:
pick a0b1c2d Add user authentication feature
pick b1a2c3d Fix typo in docstring
pick c2b3a4b Add tests
pick d3c4b5a Fix linting errors
pick e4f5a6b WIP: more tests

# Change to:
pick a0b1c2d Add user authentication feature
squash b1a2c3d Fix typo in docstring
squash c2b3a4b Add tests
squash d3c4b5a Fix linting errors
squash e4f5a6b WIP: more tests

# Save and exit
# New editor opens for commit message:
# Add user authentication feature
#
# - JWT token generation and validation
# - Login endpoint with rate limiting
# - User session management
# - Comprehensive test coverage
```

**After:**
```
* f6g7h8i Add user authentication feature
* [main] Previous work
```

### Pattern 2: Split Large Commit

**Scenario:** Commit contains unrelated changes (auth + logging).

**Before:**
```
* abc1234 Add auth and update logging
  - src/auth/service.py (new)
  - src/auth/models.py (new)
  - src/logging/config.py (modified)
  - src/logging/formatters.py (modified)
```

**Split process:**
```bash
git rebase -i HEAD~1

# In editor:
edit abc1234 Add auth and update logging

# Terminal shows:
# Stopped at abc1234... Add auth and update logging
# You can amend the commit now...

# Reset to before this commit (unstages everything)
git reset HEAD^

# Now stage and commit separately
git add src/auth/
git commit -m "Add JWT authentication service

- JWT token generation and validation
- User authentication models
- Integration with FastAPI"

git add src/logging/
git commit -m "Improve logging configuration

- Add structured JSON logging
- Custom formatters for different environments
- Better error message formatting"

# Continue rebase
git rebase --continue
```

**After:**
```
* def5678 Improve logging configuration
* abc1234 Add JWT authentication service
* [previous commits]
```

### Pattern 3: Reorder Commits for Logical Story

**Before (messy order):**
```
* e4f5a6b Add API endpoint
* d3c4b5a Add tests for service
* c2b3a4b Add service implementation
* b1a2c3d Add data models
* a0b1c2d Add database migration
```

**Reorder for logical flow:**
```bash
git rebase -i HEAD~5

# In editor, reorder lines:
pick a0b1c2d Add database migration
pick b1a2c3d Add data models
pick c2b3a4b Add service implementation
pick d3c4b5a Add tests for service
pick e4f5a6b Add API endpoint
```

**After (logical progression):**
```
* e4f5a6b Add API endpoint
* d3c4b5a Add tests for service
* c2b3a4b Add service implementation
* b1a2c3d Add data models
* a0b1c2d Add database migration
```

**Result:** Reviewer sees: DB → Models → Service → Tests → API (natural progression)

### Pattern 4: Fixup Workflow (Quick Fixes)

**Scenario:** Committed feature, then noticed typo in that commit.

```bash
# Original commit
git commit -m "Add user authentication"

# Later: find typo in that commit
# Fix typo
git add src/auth/service.py
git commit --fixup abc1234  # Creates "fixup! Add user authentication"

# More work
git commit -m "Add API endpoint"

# Before pushing, auto-squash fixups
git rebase -i --autosquash main

# Editor opens with fixup already placed:
pick abc1234 Add user authentication
fixup def5678 fixup! Add user authentication
pick ghi9012 Add API endpoint
```

**Pro tip:** Configure git to always autosquash:
```bash
git config --global rebase.autosquash true
```

### Pattern 5: Edit Old Commit

**Scenario:** Need to add forgotten file to commit from 3 commits ago.

```bash
git rebase -i HEAD~3

# In editor:
edit abc1234 Add authentication (the one to modify)
pick def5678 Add tests
pick ghi9012 Add API endpoint

# Terminal pauses at abc1234
# Add the forgotten file
git add forgotten_file.py
git commit --amend --no-edit  # Amends without changing message

# Continue rebase
git rebase --continue
```

---

## Git Bisect: Complex Scenarios

### Scenario 1: Performance Regression

**Problem:** API endpoint slow, was fast 2 weeks ago.

**Setup test script:**
```bash
cat > test_performance.sh <<'EOF'
#!/bin/bash

# Start server in background
python -m uvicorn app.main:app --port 8000 &
SERVER_PID=$!
sleep 2  # Let server start

# Test endpoint performance
RESPONSE_TIME=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8000/api/users)

# Kill server
kill $SERVER_PID

# Check if response time acceptable (< 0.5s)
if (( $(echo "$RESPONSE_TIME < 0.5" | bc -l) )); then
    exit 0  # Good
else
    exit 1  # Bad
fi
EOF
chmod +x test_performance.sh
```

**Run bisect:**
```bash
git bisect start
git bisect bad HEAD
git bisect good v1.2.0  # Known fast version
git bisect run ./test_performance.sh

# Output:
# abc1234 is the first bad commit
# commit abc1234
# Author: Developer <dev@example.com>
# Date:   Mon Jan 15 14:22:10 2024
#
#     Add N+1 query to user endpoint
```

### Scenario 2: Flaky Test

**Problem:** Test sometimes passes, sometimes fails.

**Strategy:** Run test multiple times, bisect only if consistently fails.

```bash
cat > test_flaky.sh <<'EOF'
#!/bin/bash

# Run test 10 times
for i in {1..10}; do
    pytest tests/test_integration.py::test_user_creation -v
    if [ $? -ne 0 ]; then
        echo "Failed on run $i"
        exit 1
    fi
done

echo "Passed all 10 runs"
exit 0
EOF
chmod +x test_flaky.sh

git bisect start
git bisect bad HEAD
git bisect good <known-good-commit>
git bisect run ./test_flaky.sh
```

### Scenario 3: Build Failure

**Problem:** Build fails, but many commits don't build (skip those).

```bash
git bisect start
git bisect bad HEAD
git bisect good v1.0.0

# Git checks out commit
make build

# If build fails for unrelated reason (missing dependency, etc.)
git bisect skip

# If build succeeds but feature broken
git bisect bad

# If build succeeds and feature works
git bisect good

# Repeat until culprit found
```

### Scenario 4: Using Git Bisect with Docker

**Problem:** Need specific environment to reproduce bug.

```bash
cat > test_in_docker.sh <<'EOF'
#!/bin/bash

# Build Docker image with current commit
docker build -t myapp:bisect .

# Run tests in container
docker run --rm myapp:bisect pytest tests/test_critical.py

# Capture exit code
EXIT_CODE=$?

# Cleanup
docker rmi myapp:bisect

exit $EXIT_CODE
EOF
chmod +x test_in_docker.sh

git bisect start
git bisect bad HEAD
git bisect good <commit-hash>
git bisect run ./test_in_docker.sh
```

---

## Branch Strategies: Detailed Workflows

### Trunk-Based Development (Detailed)

**Philosophy:** Small, frequent merges to main. Main always deployable.

**Branch lifetime:** Hours to 2 days maximum.

**Example workflow:**
```bash
# Day 1: Start feature
git checkout main
git pull
git checkout -b feature/add-caching

# Make small change
# Implement Redis caching for user queries
git add src/cache/
git commit -m "Add Redis caching for user queries"
git push -u origin feature/add-caching

# Create PR immediately (even if not done)
gh pr create --title "WIP: Add caching" --draft

# Continue work
# Add cache invalidation
git commit -m "Add cache invalidation on user update"
git push

# Ready for review
gh pr ready
gh pr create --title "Add Redis caching with invalidation"

# Merge same day or next day
# Total branch lifetime: < 1 day
```

**Feature flags for incomplete work:**
```python
# Merge incomplete feature behind flag
if feature_flags.is_enabled("redis_caching", user_id):
    return get_from_cache(user_id)
else:
    return get_from_database(user_id)
```

### Git Flow (Detailed)

**Branch structure:**
- `main` - Production code (tagged with versions)
- `develop` - Integration branch (all features merge here)
- `feature/*` - Feature branches (from develop)
- `release/*` - Release preparation (from develop)
- `hotfix/*` - Production fixes (from main)

**Complete release cycle:**

```bash
# 1. Start feature (Developer A)
git checkout develop
git pull
git checkout -b feature/new-auth
# Work on feature
git push -u origin feature/new-auth
# PR to develop
gh pr create --base develop --title "Add new auth"

# 2. Start another feature (Developer B)
git checkout develop
git checkout -b feature/api-v2
# Work on feature
git push -u origin feature/api-v2
# PR to develop
gh pr create --base develop --title "Add API v2"

# 3. Features merged to develop
git checkout develop
git merge feature/new-auth
git merge feature/api-v2

# 4. Start release (Release Manager)
git checkout develop
git pull
git checkout -b release/v1.3.0

# 5. Release preparation
# - Update version numbers
# - Final testing
# - Bug fixes (commit to release branch)
git commit -m "Bump version to 1.3.0"

# 6. Merge release to main and develop
git checkout main
git merge release/v1.3.0
git tag -a v1.3.0 -m "Release version 1.3.0"
git push origin main --tags

git checkout develop
git merge release/v1.3.0
git push origin develop

# 7. Delete release branch
git branch -d release/v1.3.0
git push origin --delete release/v1.3.0

# 8. Hotfix if production issue found
git checkout main
git checkout -b hotfix/security-fix
# Fix issue
git commit -m "Fix security vulnerability"

# Merge to both main and develop
git checkout main
git merge hotfix/security-fix
git tag -a v1.3.1 -m "Hotfix: security vulnerability"
git push origin main --tags

git checkout develop
git merge hotfix/security-fix
git push origin develop
```

### GitHub Flow (Detailed)

**Simplest strategy:** Everything branches from and merges to main.

```bash
# 1. Start work
git checkout main
git pull
git checkout -b feature/new-feature

# 2. Make changes
git add .
git commit -m "Add feature"
git push -u origin feature/new-feature

# 3. Create PR
gh pr create --title "Add new feature" --body "Description..."

# 4. Code review, CI checks
# Make changes based on review
git add .
git commit -m "Address review comments"
git push

# 5. Merge when approved
gh pr merge

# 6. Deploy from main
# CI/CD automatically deploys main branch

# 7. Cleanup
git checkout main
git pull
git branch -d feature/new-feature
```

---

## Conflict Resolution: Advanced Techniques

### Using Merge Tools

**Configure merge tool (one-time setup):**
```bash
# Option 1: VS Code
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait --merge $REMOTE $LOCAL $BASE $MERGED'

# Option 2: vimdiff (built-in)
git config --global merge.tool vimdiff

# Option 3: meld (GUI)
git config --global merge.tool meld
```

**Use merge tool during conflict:**
```bash
git merge feature/branch
# CONFLICT in src/auth/service.py

# Launch merge tool
git mergetool

# Tool shows 3-way comparison:
# LOCAL (your changes) | BASE (common ancestor) | REMOTE (incoming)
# Resolve conflicts visually

# After resolving
git add src/auth/service.py
git merge --continue
```

### Resolving Conflicts in Multiple Files

**Scenario:** Merge causes conflicts in 10 files.

**Strategy 1: Resolve by file type**
```bash
git merge feature/big-refactor
# CONFLICT: 10 files

# View conflicts
git status

# Resolve config files first (often keep theirs)
git checkout --theirs config/*.yaml
git add config/*.yaml

# Resolve code files manually
# Edit src/*.py files

# Resolve tests (often keep yours)
git checkout --ours tests/*.py
git add tests/*.py

git merge --continue
```

**Strategy 2: Resolve by decision**
```bash
# All conflicts: keep yours
git checkout --ours .

# All conflicts: keep theirs
git checkout --theirs .

# Specific files: custom resolution
git checkout --ours important_file.py
git checkout --theirs config.yaml
# Manually edit mixed_file.py

git add .
git merge --continue
```

### Conflict in Rebase

**Different from merge:** Each commit can have conflicts.

```bash
git rebase main
# CONFLICT in commit 1/5

# Resolve conflict
# Edit file, remove markers
git add file.py
git rebase --continue

# CONFLICT in commit 2/5
# Resolve again
git add file.py
git rebase --continue

# Repeat for each conflict
```

**If too many conflicts:**
```bash
# Abort rebase
git rebase --abort

# Try merge instead
git merge main
# Single conflict resolution

# Or rebase with strategy
git rebase main -X theirs  # Prefer incoming changes
git rebase main -X ours    # Prefer your changes
```

---

## Cherry-Picking: Edge Cases

### Cherry-Pick with Conflicts

```bash
git cherry-pick abc1234
# CONFLICT in src/service.py

# View conflict
cat src/service.py
# <<<<<<< HEAD
# Your version
# =======
# Cherry-picked version
# >>>>>>> abc1234

# Resolve conflict
# Edit file, remove markers
git add src/service.py
git cherry-pick --continue
```

### Cherry-Pick Multiple Related Commits

```bash
# Commits that depend on each other
git log feature/branch --oneline
# abc1234 Fix auth bug
# def5678 Add auth helper (required by abc1234)

# Cherry-pick both in order
git cherry-pick def5678 abc1234

# Or use range
git cherry-pick def5678^..abc1234
```

### Cherry-Pick Without Committing (Preview)

```bash
# Preview changes before committing
git cherry-pick -n abc1234

# Files staged but not committed
git status
git diff --staged

# Modify if needed
git reset src/unwanted_file.py

# Commit when ready
git commit
```

---

## Submodules: Advanced Operations

### Update Specific Submodule

```bash
# Update one submodule to specific commit
cd libs/library
git fetch
git checkout v2.3.0
cd ../..
git add libs/library
git commit -m "Update library to v2.3.0"
```

### Submodule Initialization After Clone

```bash
# Someone added submodule, you pull main
git pull

# Your working directory missing submodule content
ls libs/library  # Empty directory

# Initialize and update
git submodule init
git submodule update

# Or combined
git submodule update --init

# Recursive (submodules within submodules)
git submodule update --init --recursive
```

### Remove Submodule

```bash
# 1. Deinitialize
git submodule deinit libs/library

# 2. Remove from git
git rm libs/library

# 3. Remove submodule directory from .git
rm -rf .git/modules/libs/library

# 4. Commit
git commit -m "Remove library submodule"
```

### Convert Submodule to Regular Directory

```bash
# 1. Remove submodule
git submodule deinit libs/library
git rm libs/library
rm -rf .git/modules/libs/library

# 2. Clone repo content into directory
git clone https://github.com/user/library.git libs/library

# 3. Remove git metadata
rm -rf libs/library/.git

# 4. Add as regular files
git add libs/library/
git commit -m "Convert library from submodule to vendored code"
```

---

## Git Hooks and Automation

### Pre-commit Hook (Run Tests Before Commit)

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running tests before commit..."
pytest tests/

if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "Tests passed. Proceeding with commit."
exit 0
```

### Pre-push Hook (Run Linting Before Push)

```bash
# .git/hooks/pre-push
#!/bin/bash

echo "Running linting before push..."
ruff check .

if [ $? -ne 0 ]; then
    echo "Linting failed. Push aborted."
    exit 1
fi

exit 0
```

### Commit Message Validation

```bash
# .git/hooks/commit-msg
#!/bin/bash

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Enforce format: "type: description"
if ! echo "$COMMIT_MSG" | grep -qE "^(feat|fix|docs|refactor|test|chore): .+"; then
    echo "Invalid commit message format."
    echo "Must be: type: description"
    echo "Types: feat, fix, docs, refactor, test, chore"
    exit 1
fi

exit 0
```

---

**For quick reference and core patterns:** See [SKILL.md](./SKILL.md)
