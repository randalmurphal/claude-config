---
name: git-workflows
description: Advanced Git workflows including interactive rebase, bisect, worktrees, branch strategies, conflict resolution, cherry-picking, and submodules. Use when doing complex git operations, cleaning up commit history, managing multiple branches, investigating bugs with git bisect, or working on parallel features with worktrees.
allowed-tools:
  - Read
  - Bash
  - Grep
---

# Git Workflows Skill

**Purpose:** Guide advanced Git operations for complex workflows, history management, and parallel development.

**When to use:** Interactive rebase, git bisect debugging, worktree management, conflict resolution, cherry-picking commits, branch cleanup, submodule operations.

**For detailed examples and advanced patterns:** See [reference.md](./reference.md)

---

## Core Principles

1. **Never rewrite published history** - Only rebase/amend local commits
2. **Worktrees for parallel work** - Don't branch spam, use worktrees
3. **Bisect for bug hunting** - Binary search beats guesswork
4. **Clean history aids reviews** - Interactive rebase before pushing
5. **Cherry-pick sparingly** - Prefer merge/rebase for full branches

---

## Git Worktrees (Parallel Development)

**Purpose:** Work on multiple branches simultaneously without switching contexts or stashing.

**Use cases:** Parallel features, emergency hotfix during feature work, code review without stashing, testing across branches.

### Using git-worktree Script

**Script location:** `~/.claude/scripts/git-worktree`

```bash
# Create worktrees for parallel work
git-worktree auth api database

# List worktrees
git-worktree --list

# Cleanup when done
git-worktree --cleanup
```

### Manual Worktree Commands

| Command | Purpose |
|---------|---------|
| `git worktree add <path> <branch>` | Create worktree from existing branch |
| `git worktree add -b <new> <path> <base>` | Create worktree with new branch |
| `git worktree list` | Show all worktrees |
| `git worktree remove <path>` | Remove worktree |
| `git worktree prune` | Clean stale references |

**For detailed workflow examples:** See reference.md

---

## Interactive Rebase (History Cleanup)

**Purpose:** Clean up commit history before pushing/merging.

**CRITICAL:** Only rebase commits NOT pushed to shared branches.

### Rebase Operations

| Action | Purpose |
|--------|---------|
| `pick` | Keep commit as-is |
| `reword` | Change commit message |
| `edit` | Modify commit content |
| `squash` | Merge with previous commit (edit message) |
| `fixup` | Merge with previous commit (keep message) |
| `drop` | Remove commit |

### Quick Commands

```bash
# Rebase last 3 commits
git rebase -i HEAD~3

# Rebase entire feature branch
git rebase -i main

# In editor: pick/squash/fixup/edit/reorder
```

**Example before/after:**
```
Before: WIP commits, typos, test fixes scattered
After: 2-3 clean, logical commits with clear messages
```

**For detailed patterns (squash all, split commits, reorder):** See reference.md

---

## Git Bisect (Bug Hunting)

**Purpose:** Binary search through commit history to find bug introduction point.

### Basic Bisect Workflow

```bash
git bisect start                # Start
git bisect bad                  # Current commit is bad
git bisect good <commit-hash>   # Known good commit

# Test, then mark:
git bisect bad     # or
git bisect good

# Repeat until found
git show           # View culprit commit
git bisect reset   # End session
```

### Automated Bisect

```bash
# Create test script (exit 0 = good, exit 1 = bad)
cat > test.sh <<'EOF'
#!/bin/bash
pytest tests/test_auth.py::test_login
exit $?
EOF
chmod +x test.sh

# Run automated bisect
git bisect start
git bisect bad HEAD
git bisect good v1.2.3
git bisect run ./test.sh
git bisect reset
```

**For detailed examples:** See reference.md

---

## Branch Management

### Branch Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<name>` | `feature/user-auth` |
| Bugfix | `fix/<issue>` | `fix/login-timeout` |
| Hotfix | `hotfix/<issue>` | `hotfix/security-patch` |
| Release | `release/<version>` | `release/v1.2.0` |
| Experiment | `spike/<name>` | `spike/new-framework` |

### Common Operations

```bash
# List branches
git branch                      # Local
git branch -r                   # Remote
git branch --merged main        # Merged branches
git branch --no-merged main     # Unmerged branches

# Delete branches
git branch -d feature/old       # Delete if merged
git branch -D feature/old       # Force delete
git push origin --delete feature/old

# Cleanup
git fetch --prune               # Prune stale remotes
git branch --merged main | grep -v "^\* main" | xargs git branch -d
```

### Branch Strategies Summary

| Strategy | Main Branch | Feature Branches | Best For |
|----------|-------------|-----------------|----------|
| **Trunk-Based** | Always deployable | Short-lived (<2 days) | Fast iteration, CI/CD |
| **Git Flow** | Production-ready | Long-lived, from develop | Release-based projects |
| **GitHub Flow** | Deployable | All from main, PR review | Simple, continuous deployment |

**For detailed strategy workflows:** See reference.md

---

## Conflict Resolution

### Resolution Strategies

| Strategy | Command | When |
|----------|---------|------|
| Keep yours | `git checkout --ours <file>` | Your changes correct |
| Keep theirs | `git checkout --theirs <file>` | Incoming changes correct |
| Manual merge | Edit file, remove markers | Need both |
| Abort | `git merge --abort` or `git rebase --abort` | Start over |

### Conflict Resolution Workflow

```bash
# 1. Merge/rebase triggers conflict
git merge feature/branch
# Or: git rebase main

# 2. View conflicts
git status

# 3. Choose resolution:
git checkout --ours path/file.py      # Keep yours
git checkout --theirs path/file.py    # Keep theirs
# Or manually edit, remove <<<, ===, >>> markers

# 4. Stage resolved files
git add path/file.py

# 5. Continue
git merge --continue
# Or: git rebase --continue
```

### Preventing Conflicts

- Merge main into feature frequently (smaller conflicts)
- Communicate with team on shared files
- Keep branches short-lived
- Use feature flags for incomplete work

**For merge tool setup and advanced patterns:** See reference.md

---

## Cherry-Picking

**Purpose:** Apply specific commits from one branch to another.

**When:** Port bug fix to release branch, selectively apply changes.
**When NOT:** Merging entire branches (use merge/rebase).

```bash
# Single commit
git cherry-pick <commit-hash>

# Multiple commits
git cherry-pick <commit1> <commit2>

# Range
git cherry-pick <start>^..<end>

# Without committing (stage only)
git cherry-pick -n <commit-hash>

# Handle conflicts
git cherry-pick --continue
git cherry-pick --abort
```

**Example use case:**
```bash
# Bug fix in feature branch, needed in release
git log feature/new --oneline
# abc1234 Fix auth timeout

git checkout release/v1.2
git cherry-pick abc1234
git push origin release/v1.2
```

**For detailed conflict handling:** See reference.md

---

## Submodules

**Purpose:** Include other Git repos as subdirectories.

### Common Commands

| Command | Purpose |
|---------|---------|
| `git submodule add <url> <path>` | Add submodule |
| `git submodule init` | Initialize after clone |
| `git submodule update` | Checkout correct commit |
| `git submodule update --remote` | Update to latest |
| `git submodule foreach <cmd>` | Run command in all |

### Quick Workflows

**Add submodule:**
```bash
git submodule add https://github.com/user/lib.git libs/lib
git commit -m "Add lib submodule"
```

**Clone with submodules:**
```bash
git clone --recurse-submodules <repo-url>
# Or: git submodule init && git submodule update
```

**Update submodule:**
```bash
git submodule update --remote libs/lib
git add libs/lib
git commit -m "Update lib submodule"
```

**For removal and advanced patterns:** See reference.md

---

## Advanced Git Log and Diff

### Useful Log Commands

```bash
git log --oneline --graph --all --decorate   # Pretty history
git log --stat                               # With file changes
git log -p                                   # With diff
git log --follow path/to/file.py            # File history
git log --grep="auth"                        # Search messages
git log -S "function_name"                   # Search code changes
git log --author="name@example.com"          # By author
git log branch-A ^branch-B                   # Diff branches
git log --since="2 weeks ago"                # Time range
```

### Useful Diff Commands

```bash
git diff                                     # Working dir vs staging
git diff --staged                            # Staging vs last commit
git diff main..feature/branch                # Between branches
git diff HEAD path/to/file.py               # Specific file
git diff --word-diff                         # Word-level
git diff --stat main..feature/branch        # Summary only
git show <commit-hash>                       # Commit diff
```

---

## Quick Reference: Common Pitfalls

| Problem | Solution |
|---------|----------|
| Committed to wrong branch | `git checkout correct-branch && git cherry-pick <commit>` |
| Undo last commit (keep changes) | `git reset HEAD~1` |
| Undo last commit (discard) | `git reset --hard HEAD~1` |
| Lost commits after reset | `git reflog` then `git cherry-pick <commit>` |
| Detached HEAD | `git switch -c new-branch-name` |
| Accidentally pushed rebase | Communicate with team, coordinate force pull |

---

## Quick Reference: Command Cheat Sheet

### Worktrees
```bash
git-worktree auth api                # Create multiple (script)
git worktree add <path> <branch>     # Create one
git worktree list                    # List all
git worktree remove <path>           # Remove
```

### Interactive Rebase
```bash
git rebase -i HEAD~3                 # Last 3 commits
git rebase -i main                   # Entire branch
# Editor: pick/squash/fixup/edit/reorder
```

### Bisect
```bash
git bisect start
git bisect bad                       # Current
git bisect good <commit>             # Known good
# Test and mark bad/good until found
git bisect reset
```

### Branch Cleanup
```bash
git branch --merged main             # Show merged
git branch -d <branch>               # Delete merged
git branch -D <branch>               # Force delete
git fetch --prune                    # Clean remotes
```

### Conflict Resolution
```bash
git checkout --ours <file>           # Keep yours
git checkout --theirs <file>         # Keep theirs
git merge --abort                    # Abort merge
git rebase --abort                   # Abort rebase
```

### Cherry-Pick
```bash
git cherry-pick <commit>             # Apply commit
git cherry-pick <start>^..<end>      # Range
git cherry-pick --continue           # After conflict
```

### Submodules
```bash
git submodule add <url> <path>       # Add
git submodule update --init          # Initialize
git submodule update --remote        # Update
```

---

## Validation Checklist

**Before interactive rebase:**
- [ ] Only rebasing unpushed commits
- [ ] Backup branch created: `git branch backup`

**Before force push:**
- [ ] Coordinated with team
- [ ] Not pushing to main/protected branch
- [ ] No one else working on branch

**After conflict resolution:**
- [ ] Tests pass
- [ ] Code builds
- [ ] All conflict markers removed: `grep -r "<<<<<<" src/`

**Before deleting branches:**
- [ ] Branch merged or work preserved
- [ ] Verified: `git branch --merged main`

---

**Remember:** Clean Git history aids code review and debugging. These tools help your commit history tell a clear story.

**For comprehensive examples, edge cases, and advanced patterns:** See [reference.md](./reference.md)
