---
name: pr_review
description: Comprehensive PR review against Jira ticket requirements
---

You are conducting a comprehensive PR review using parallel specialized agents analyzing code in isolated git worktrees.

## Command Usage

`/pr_review <ticket>:<target_branch>`

Examples:
- `/pr_review INT-3877:develop`
- `/pr_review INT-3877:release-6.21.0`
- `/pr_review INT-3877` (defaults to develop)

## Review Process

### 1. Parse Input & Normalize Branch

```python
# Parse
if ":" in input:
    ticket, target_branch = input.split(":")
else:
    ticket = input
    target_branch = "develop"

# Normalize target branch
branch_mappings = {
    "dev": "develop",
    "main": "develop",
    "master": "develop",
    "6.22": "release-6.22.0",
    "6.21": "release-6.21.0",
    "release-6.22": "release-6.22.0",
}
target_branch = branch_mappings.get(target_branch, target_branch)
```

### 2. Setup Worktrees

```bash
# Fetch latest
git fetch origin -q

# Find source branch
source_branch=$(git branch -r | grep "origin/$ticket" | grep -v "pre-styling" | head -1 | sed 's|origin/||')

# Create worktrees in /tmp/pr-review-$ticket
~/.claude/scripts/git-worktree --base /tmp/pr-review-$ticket --main $target_branch base pr

# Checkout PR branch in pr worktree
cd /tmp/pr-review-$ticket/wt-pr && git checkout origin/$source_branch -b review-$ticket
```

### 3. Gather Context (Parallel)

Single message with multiple tool calls:

```python
# Jira ticket
mcp__jira__jira_get_issue(ticket)

# Git analysis (all in /tmp/pr-review-$ticket)
git log origin/$target_branch..origin/$source_branch --oneline
git diff --name-status origin/$target_branch...origin/$source_branch
git diff --stat origin/$target_branch...origin/$source_branch
```

### 4. Launch 4 Review Agents (Single Message, Parallel)

Extract file lists from diff:
```python
code_files = [f for f in changed_files if f.endswith('.py') and not f.startswith('test_')]
test_files = [f for f in changed_files if 'test_' in f or f.startswith('tests/')]
```

Load templates and populate:
```python
# Read templates
code_tmpl = read('~/.claude/templates/pr-review-code-analysis.md')
sec_tmpl = read('~/.claude/templates/pr-review-security.md')
perf_tmpl = read('~/.claude/templates/pr-review-performance.md')
test_tmpl = read('~/.claude/templates/pr-review-tests.md')

# Populate with worktree path and files
worktree = f"/tmp/pr-review-{ticket}/wt-pr"
```

Launch ALL 4 agents in ONE message:
```python
Task(investigator, code_tmpl.format(worktree_path=worktree, changed_files='\n'.join(code_files + test_files)))
Task(security-auditor, sec_tmpl.format(worktree_path=worktree, changed_files='\n'.join(code_files + test_files)))
Task(performance-optimizer, perf_tmpl.format(worktree_path=worktree, changed_files='\n'.join(code_files + test_files)))
Task(test-implementer, test_tmpl.format(worktree_path=worktree, code_files='\n'.join(code_files), test_files='\n'.join(test_files)))
```

### 5. Validate & Synthesize Agent Reports

After all 4 agents complete:

1. **Cross-validate findings**:
   - Check file:line references exist in worktree
   - Remove duplicate findings from multiple agents
   - Flag contradictions for manual review

2. **Categorize by severity**:
   - 🔴 Critical: Security vulns, data corruption, crashes
   - 🟡 High: Breaking changes, performance regressions, missing tests
   - 🟢 Medium: Logic bugs, edge cases, optimization opportunities

3. **Add PEP 8 check** (you do this, agents don't):
   - Import grouping (stdlib → third-party → local with blank lines)
   - Line length (80 char max)

### 6. Generate Final Report

```markdown
# PR Review: {ticket} - {title}

**Branch:** origin/{source_branch} → origin/{target_branch}
**Commits:** {count} | **Files:** {count} | **Lines:** +{added} -{removed}

## 🔴 Critical Issues (Must Fix Before Merge)

1. **{Category}** (file.py:line)
   - **Problem**: {what's wrong}
   - **Impact**: {what breaks/security risk/data loss}
   - **Fix**: {exact fix or code suggestion}

## 🟡 High Priority (Should Fix)

1. **{Category}** (file.py:line)
   - **Problem**: {what's wrong}
   - **Impact**: {performance/reliability/breaking change}
   - **Fix**: {how to fix}

## 🟢 Medium Priority (Consider)

1. **{Category}** (file.py:line)
   - **Problem**: {what could be better}
   - **Suggestion**: {improvement idea}

## ✅ What's Good

- {Specific positive findings}
- {Well-tested areas}
- {Good practices used}

## 📊 Test Coverage

**Covered:** file.py:line-range - {what's tested}
**Missing:** file.py:line-range - {what's not tested, risk}
**Issues:** test_file.py:line - {incorrect/incomplete test}

## 🔒 Security

- ✅ No hardcoded secrets
- ✅ Input validation present
- ⚠️ {concerns with file:line}

## ⚡ Performance

- ✅ No regressions
- ⚠️ {concerns with estimates}

## Summary

**Issues:** Critical: {X} | High: {Y} | Medium: {Z}
**Recommendation:** {APPROVE | REQUEST CHANGES | NEEDS DISCUSSION}

**Action Items:**
1. {Must fix item}
2. {Must fix item}
```

### 7. Cleanup Worktrees

```bash
~/.claude/scripts/git-worktree --cleanup
```

## Error Handling

**Branch not found:**
```bash
if ! git branch -r | grep -q "origin/$ticket"; then
    echo "❌ No branch found for $ticket"
    git branch -r | grep "$ticket" || echo "No similar branches"
    exit 1
fi
```

**Multiple branches:**
Use most recent, prefer non-pre-styling branches.

**No commits:**
```bash
if ! git log origin/$target..origin/$source --oneline | grep -q .; then
    echo "❌ No commits between branches (already merged?)"
    exit 1
fi
```

## Key Rules

1. **Parallel agents**: ALL 4 in ONE message
2. **Worktree isolation**: Never touch current branch
3. **Evidence required**: Every finding needs file:line
4. **Validation layer**: Cross-check agent findings before reporting
5. **Actionable only**: Real issues, not theoretical
6. **Cleanup**: Always remove worktrees when done

## Validation Checklist

Before sending report to user:
- [ ] All 4 agents completed
- [ ] File:line references verified in worktree
- [ ] Duplicates removed
- [ ] Findings categorized by severity
- [ ] PEP 8 violations checked
- [ ] Clear recommendation provided
- [ ] Worktrees cleaned up
