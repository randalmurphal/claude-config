---
name: pr_review
description: Comprehensive PR review against Jira ticket requirements
---

**⚠️  REVIEW MODE DIRECTIVES (Active Regardless of Output Style):**

You are a **critical code reviewer**, not a cheerleader. Even if using a different output style:
- **Assume code is flawed** until proven otherwise
- **Security first** - flag vulnerabilities immediately (injection, auth bypass, secrets)
- **Context-aware** - internal APIs get different scrutiny than public endpoints
- **No sugar-coating** - be direct about problems
- **Evidence required** - every finding needs file:line reference + proof
- **Provide fixes** - specific code changes, not just complaints
- **Acknowledge good code** - call out solid patterns when found
- **No assumptions** - if uncertain, flag for verification, don't claim it's an issue
- **Investigate thoroughly** - minor issues deserve full understanding

**Output format:** Group by severity (🔴 Critical, 🟡 High, 🔵 Medium, 🟢 Low, 🟣 Needs Verification)

---

You are conducting a comprehensive multi-round PR review using parallel specialized agents analyzing code in isolated git worktrees.

## Command Usage

`/pr_review <ticket>:<target_branch>`

Examples:
- `/pr_review INT-3877:develop`
- `/pr_review INT-3877:release-6.21.0`
- `/pr_review INT-3877` (defaults to develop)

## Review Architecture

**Multi-round verification approach with supervision:**

1. **Phase 1:** Load skills & prepare
2. **Phase 2:** Parse input & setup worktrees
3. **Phase 3:** Context gathering (Jira ticket, MR comments, git analysis, comment thread analysis)
4. **Phase 4:** Specialized domain reviews (4 parallel agents)
   - All outputs tagged with [AGENT: name] for traceability

5. **Phase 5:** Supervisory quality check (general-investigator)
   - Verify agents stayed in their lanes (no role drift)
   - Check completeness (all files covered, evidence present)
   - Detect contradictions between agents
   - Flag weak evidence or vague claims

6. **Phase 6:** Requirements & ripple effect analysis (3-4 parallel agents)
   - All outputs tagged for traceability

7. **Phase 7:** Verification round (N parallel agents)
   - Prove/disprove critical findings
   - Pass original agent reasoning for context
   - Each verifier gets full context of what original agent saw

8. **Phase 8:** Meta-verification (verify the verifiers)
   - Double-check FALSE_POSITIVE claims
   - Prevent overzealous verifiers from removing real issues
   - Restore findings if verifier was wrong

9. **Phase 9:** Second investigation pass (2-3 investigators with fresh perspective)
   - Different focus areas (edge cases, data flow, observability)

10. **Phase 10:** Deep investigation (unlimited time on "needs investigation")
    - Items flagged as suspicious get thorough analysis
    - Read related files, check git history, trace call chains

11. **Phase 11:** Contradiction resolution (tie-breaker investigators)
    - Resolve conflicting findings from different agents
    - Provide definitive verdict with evidence

12. **Phase 12:** Synthesis
    - Cross-validate, remove false positives, generate report

13. **Phase 13:** Cleanup worktrees

**Why multi-round with supervision?**
- Supervisor catches role drift before it propagates
- Verification round catches false positives
- Meta-verification catches overzealous verifiers
- Deep investigation ensures nothing suspicious is left unexamined
- Contradiction resolution prevents conflicting findings reaching user
- LLM tagging enables traceability and accountability
- Different agents/angles = no stone unturned

---

## Phase 1: Load Skills & Prepare

**MANDATORY FIRST STEP:**

```python
# Load agent-prompting skill BEFORE spawning any agents
Skill(command="agent-prompting")

# Review "Critical Inline Standards by Agent Type" section
# You MUST include inline standards in ALL agent prompts
```

**Why:** Sub-agents don't automatically know project standards (try/except rules, logging patterns, type hints, etc). Inline standards in prompts guarantee they're followed.

---

## Phase 2: Parse Input & Setup

**⚠️ CRITICAL: NEVER WORK IN MAIN REPO**

**Rules for main repo usage:**
- ✅ **ALLOWED:** Read files from current branch (if on develop, can read develop code for reference)
- ✅ **ALLOWED:** Run `git fetch origin -q` to update remote refs
- ✅ **ALLOWED:** Run `git branch -r` to list remote branches
- ✅ **ALLOWED:** Run git-worktree script to create worktrees
- ❌ **FORBIDDEN:** Create any branches in main repo
- ❌ **FORBIDDEN:** Checkout any branches in main repo
- ❌ **FORBIDDEN:** Make any commits in main repo
- ❌ **FORBIDDEN:** Modify any files in main repo
- ❌ **FORBIDDEN:** Run any git commands that change state (checkout, commit, merge, rebase, etc.)

**ALL review work happens in worktrees at `/tmp/pr-review-{ticket}/wt-pr`**

### 2.1 Parse Input & Normalize Branch

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

### 2.2 Find Source Branch

```bash
# Fetch latest
git fetch origin -q

# Find all branches matching ticket
all_branches=$(git branch -r | grep "origin/$ticket" | grep -v "pre-styling")

if [ -z "$all_branches" ]; then
    echo "❌ No branch found for $ticket"
    git branch -r | grep "$ticket" || echo "No similar branches"
    exit 1
fi

# Count branches
branch_count=$(echo "$all_branches" | wc -l)

if [ $branch_count -eq 1 ]; then
    # Single branch - use it
    source_branch=$(echo "$all_branches" | head -1 | sed 's|.*origin/||')
else
    # Multiple branches - agent decides which to use
    # Get metadata for each branch
    echo "⚠️  Multiple branches found for $ticket:"
    echo ""

    for branch in $all_branches; do
        branch_name=$(echo "$branch" | sed 's|.*origin/||')
        last_commit=$(git log -1 --format="%ci | %s" "$branch")
        echo "  $branch_name"
        echo "    Last commit: $last_commit"
        echo ""
    done

    # AGENT DECISION POINT
    # YOU (the agent) need to decide which branch to use based on:
    # - Branch names (avoid ones with "test", "experimental", "spike" unless that's the only option)
    # - Most recent commit date (more recent = likely the active branch)
    # - Commit messages (production-ready work vs experimental)
    #
    # Pick the branch that seems like the main/production branch for this ticket.
    # If unclear, pick the most recently updated one.
    #
    # Set source_branch variable to your choice (without origin/ prefix)

    # Default behavior if agent doesn't override: most recent
    source_branch=$(echo "$all_branches" | \
        xargs -I {} bash -c 'echo "$(git log -1 --format=%ct {}) {}"' | \
        sort -rn | \
        head -1 | \
        cut -d' ' -f2 | \
        sed 's|origin/||')
fi
```

### 2.3 Setup Worktrees

```bash
# Create worktrees in /tmp/pr-review-$ticket
~/.claude/scripts/git-worktree --base /tmp/pr-review-$ticket --main $target_branch base pr

# Checkout PR branch in pr worktree (detached HEAD - no branch creation)
# DO NOT create a review branch - detached HEAD is perfect for read-only review
cd /tmp/pr-review-$ticket/wt-pr && git checkout origin/$source_branch
```

---

## Phase 3: Context Gathering (Parallel)

**Single message with multiple tool calls:**

```python
# 1. Jira ticket (requirements) - using jira-get-issue script
result = Bash(command=f"~/.claude/scripts/jira-get-issue {ticket}")
if result.returncode == 0:
    ticket_content = result.stdout
else:
    ticket_content = None  # Not available or ticket not found

# 2. GitLab MR comments (existing feedback) - using gitlab-mr-comments script
result = Bash(command=f"~/.claude/scripts/gitlab-mr-comments {ticket}")
if result.returncode == 0:
    mr_comments = result.stdout
else:
    mr_comments = None  # Not available or MR not found

# 3. Git analysis (all in /tmp/pr-review-$ticket/wt-pr)
git log origin/$target_branch..origin/$source_branch --oneline
git diff --name-status origin/$target_branch...origin/$source_branch
git diff --stat origin/$target_branch...origin/$source_branch
full_diff = git diff origin/$target_branch...origin/$source_branch  # Full diff - used for scoping

# 4. Categorize changed files
code_files = [f for f in changed_files if f.endswith('.py') and not f.startswith('test_')]
test_files = [f for f in changed_files if 'test_' in f or f.startswith('tests/')]
config_files = [f for f in changed_files if f.endswith(('.json', '.yaml', '.yml', '.toml', '.ini', '.env'))]
migration_files = [f for f in changed_files if 'migration' in f.lower() or 'schema' in f.lower() or f.endswith('.sql')]
```

### 3.1 Detect Review Context

**Determine what kind of code this is (affects security scrutiny):**

```python
# Read changed files to understand context
context_analysis = {
    "has_external_api": False,      # Public REST/GraphQL endpoints
    "has_internal_api": False,       # Backend-only service calls
    "has_auth_changes": False,       # Authentication/authorization
    "has_db_changes": False,         # Database schema/queries
    "has_cache_changes": False,      # Redis/memcache operations
    "has_payment_logic": False,      # Financial transactions
    "has_pii_handling": False,       # Personal identifiable info
    "db_type": None,                 # "mongodb", "postgres", "mysql", None
}

# Quick grep to detect context
# External API: @app.route, @api.route, FastAPI endpoints
# Internal API: internal service calls, RPC
# Auth: login, authenticate, verify_token, permissions
# DB: pymongo, sqlalchemy, psycopg2, mysql.connector
# Cache: redis, memcache
# Payment: stripe, payment, transaction, billing
# PII: email, ssn, phone, address in user models
```

**This context determines review depth:**
- External API → High security scrutiny (injection, auth, rate limiting)
- Internal API → Medium security (still check, but less paranoid)
- Payment logic → Extra validation, decimal precision, idempotency
- PII handling → Data exposure, logging, encryption checks
- DB changes → Schema compatibility, migration safety

### 3.2 Analyze MR Comment Threads

**If MR comments exist, analyze threads to understand what's been addressed:**

```python
if mr_comments:
    Task(general-investigator, f"""
You are the MR COMMENT THREAD ANALYZER.

Parse ALL MR comment threads (including replies) to categorize what's been addressed, dismissed, or outstanding.

MR COMMENT THREADS:
{mr_comments}

GIT DIFF (what changed since comments):
{full_diff}

YOUR JOB: For EACH top-level comment thread, determine its status.

CATEGORIES:

1. **ADDRESSED** - Code was changed to fix the concern
   - Check git diff for evidence of fix
   - Note file:line where fix was applied

2. **DISMISSED_WITH_REASONING** - Author explained why not fixing
   - Extract the reasoning (important: later review agents should know this)
   - Note if reasoning is sound or questionable

3. **OUTSTANDING** - No response or unresolved discussion
   - Flag for review agents to check

4. **PLANNED_FOLLOWUP** - Acknowledged but out of scope for this PR
   - Extract what's planned and why it's separate
   - Should be verified that it's actually tracked (ticket mentioned?)

5. **RESOLVED_BY_DISCUSSION** - Concern was clarified/misunderstanding
   - No code change needed, but misunderstanding resolved

For EACH comment thread, analyze:
- Original comment + all replies
- Check if code changed at mentioned file:line
- Extract reasoning from author responses
- Determine final status

RETURN JSON:
{{{{
  "addressed": [
    {{{{
      "original_comment": "Comment text",
      "author": "@username",
      "file": "path/to/file.py",
      "line": 123,
      "evidence_of_fix": "Code at line 123 now validates input (see diff +125-130)",
      "fix_quality": "complete | partial | overcorrected"
    }}}}
  ],
  "dismissed_with_reasoning": [
    {{{{
      "original_comment": "Comment text",
      "author": "@username",
      "file": "path/to/file.py",
      "line": 123,
      "reasoning": "Author's explanation why not fixing",
      "reasoning_quality": "sound | questionable | insufficient",
      "flag_for_review": true/false  // If reasoning is questionable
    }}}}
  ],
  "outstanding": [
    {{{{
      "original_comment": "Comment text",
      "author": "@username",
      "file": "path/to/file.py",
      "line": 123,
      "severity": "critical | high | medium | low",
      "days_since_comment": 3
    }}}}
  ],
  "planned_followup": [
    {{{{
      "original_comment": "Comment text",
      "author": "@username",
      "what_planned": "What will be done in follow-up",
      "tracked_in": "TICKET-123 | mentioned but not tracked | not mentioned",
      "verify_needed": true/false  // Should review agents verify it's actually tracked?
    }}}}
  ],
  "resolved_by_discussion": [
    {{{{
      "original_comment": "Comment text",
      "author": "@username",
      "resolution": "How misunderstanding was resolved"
    }}}}
  ]
}}}}

CRITICAL: Read entire comment threads (original + all replies). Don't just look at top-level comments.

BUDGET DIRECTIVE: Use full token budget if needed. Don't skip analysis.
""", max_tokens=None)

    # Parse result
    mr_comment_analysis = result

    # Pass this to all review agents so they:
    # - Don't re-flag addressed issues
    # - Question dismissed items if reasoning is questionable
    # - Prioritize outstanding items
    # - Verify planned follow-ups are actually tracked
```

**Why this matters:**
- Avoids re-flagging issues already addressed
- Surfaces questionable dismissals for re-review
- Ensures outstanding comments aren't ignored
- Verifies follow-up work is actually tracked (not just promised)

---

## Phase 4: Round 1 - Specialized Review (Parallel)

**CRITICAL: All agent prompts MUST include these directives:**

```
WORKTREE PATH: /tmp/pr-review-{ticket}/wt-pr

⚠️ CRITICAL: ALL file operations MUST use the worktree path above.
- NEVER read files from /home/rmurphy/repos/m32rimm (main repo)
- ALWAYS use /tmp/pr-review-{ticket}/wt-pr for ALL file reads
- ALL Grep/Glob operations MUST specify path parameter with worktree path
- Sub-agents: You are in a git worktree - never touch the main repo

SCOPING RULES (MANDATORY):

You are reviewing PR changes for ticket: {ticket}

Ticket context:
{ticket_content}

**CRITICAL:** You MUST analyze ALL sections of the ticket data provided:
- If a section exists in the ticket data, it is MANDATORY to review it
- DO NOT skip sections because they're "not your focus" - review EVERYTHING
- If ticket data is missing, that's noted below - proceed with code-only review

The ticket includes multiple sections that provide critical context:
- **Description** - Overall requirements and goals
- **Acceptance Criteria** - What must be true when done
- **Developer Checklist** - Technical implementation details (data structures, API changes, migrations)
- **Test Plan** - What should be tested and how
- **Comments** - ALL discussion threads, clarifications, decisions made during development
- **Related Ticket Details (FULL)** - Frontend/Backend pairs, clones, dependencies with COMPLETE ticket data (description, checklists, test plans, comments)

**If ticket says "check Developer Checklist" or references any section - YOU MUST check it.**

Review agents MUST:
1. Check Developer Checklist against actual code (does code match planned data structures, API changes, etc.?)
2. Verify Test Plan is covered by actual tests
3. Read ALL Comments for context on decisions, dismissed concerns, or out-of-scope items
4. Review Related Tickets THOROUGHLY - you get FULL ticket data (not previews) for:
   - FE/BE pairs - Check if backend changes match what frontend expects (or vice versa)
   - Clones/splits - Understand what was done in parent ticket vs this one
   - Blocking tickets - Ensure dependencies are satisfied
   - Each related ticket includes its own Description, Developer Checklist, Test Plan, Comments

ONLY report issues that meet ONE of these criteria:
1. **Introduced/Modified in this PR** - Code that appears in the git diff (added/modified lines)
2. **Related to ticket requirements** - Pre-existing code that's related to what the ticket is trying to accomplish
3. **Breaking changes** - Pre-existing code that will BREAK due to this PR's changes

DO NOT report:
- Pre-existing issues unrelated to the ticket scope
- Pre-existing issues not modified by this PR
- General code quality issues in unchanged code (unless they block the ticket's goals)

How to determine if something is "introduced/modified":
- Check the git diff: {full_diff}
- Look for +/- lines at the specific file:line you're flagging
- If the line wasn't touched (no + or -), it's pre-existing

Pre-existing issues ARE relevant if:
- They're in the same function/class being modified and impact the changes
- They're called by new code and will cause failures
- They're similar patterns to what's being added (consistency concern)
- They directly relate to ticket requirements

When in doubt: Include the finding but mark it as "pre-existing, related to {specific ticket requirement}"

---

MR COMMENT ANALYSIS:
{mr_comment_analysis}

**MANDATORY:** If MR comments exist in the data above, you MUST use them:

USE THIS DATA TO:
1. **Don't re-flag addressed issues** - If comment analysis shows something was addressed, verify the fix quality instead of re-reporting
2. **Question dismissals** - If comment was dismissed with "questionable" reasoning, flag it in your review with context
3. **Prioritize outstanding** - If comment is outstanding (no response), check if it's still valid and escalate if critical
4. **Verify follow-ups** - If planned follow-up mentioned, verify it's actually tracked (ticket exists, linked, etc.)

DO NOT:
- Ignore outstanding comments (must be checked)
- Accept questionable dismissals without review
- Re-report issues already confirmed as addressed (unless fix is incomplete)
```

**Load all templates and populate with worktree paths:**

```python
worktree = f"/tmp/pr-review-{ticket}/wt-pr"

# Read templates
code_tmpl = read('~/.claude/templates/pr-review-code-analysis.md')
sec_tmpl = read('~/.claude/templates/pr-review-security.md')
perf_tmpl = read('~/.claude/templates/pr-review-performance.md')
test_tmpl = read('~/.claude/templates/pr-review-tests.md')
```

**Launch ALL agents in ONE message (4 parallel):**

```python
# ALWAYS run these 4
Task(general-investigator, code_tmpl.format(
    worktree_path=worktree,
    changed_files='\n'.join(code_files + test_files),
    mr_comments=mr_comments or "No existing comments",
    mr_comment_analysis=mr_comment_analysis if mr_comments else "No comment analysis",
    ticket_content=ticket_content or "No ticket available",  # NEW: Ticket scope
    full_diff=full_diff  # NEW: Git diff to distinguish new vs existing
), max_tokens=None)

Task(security-auditor, sec_tmpl.format(
    worktree_path=worktree,
    changed_files='\n'.join(code_files + test_files),
    context=context_analysis,  # Tells agent what kind of code this is
    mr_comment_analysis=mr_comment_analysis if mr_comments else "No comment analysis",
    ticket_content=ticket_content or "No ticket available",  # NEW: Ticket scope
    full_diff=full_diff  # NEW: Git diff to distinguish new vs existing
), max_tokens=None)

Task(performance-optimizer, perf_tmpl.format(
    worktree_path=worktree,
    changed_files='\n'.join(code_files + test_files),
    db_type=context_analysis['db_type'],
    mr_comment_analysis=mr_comment_analysis if mr_comments else "No comment analysis",
    ticket_content=ticket_content or "No ticket available",  # NEW: Ticket scope
    full_diff=full_diff  # NEW: Git diff to distinguish new vs existing
), max_tokens=None)

Task(general-investigator, test_tmpl.format(
    worktree_path=worktree,
    code_files='\n'.join(code_files),
    test_files='\n'.join(test_files),
    mr_comment_analysis=mr_comment_analysis if mr_comments else "No comment analysis",
    ticket_content=ticket_content or "No ticket available",  # NEW: Ticket scope
    full_diff=full_diff  # NEW: Git diff to distinguish new vs existing
), max_tokens=None)
```

**Agent outputs:**
- Each returns JSON with findings categorized by severity
- Include file:line, issue description, evidence, fix suggestion
- Flag uncertain findings as "needs_verification"

**Tag all agent outputs:**

```python
# After each agent completes, tag output with agent name
code_analysis_output = f"[AGENT: code-analysis]\n{code_analysis_response}"
security_output = f"[AGENT: security-auditor]\n{security_response}"
performance_output = f"[AGENT: performance-optimizer]\n{performance_response}"
test_output = f"[AGENT: test-implementer]\n{test_response}"
```

---

## Phase 5: Supervisory Quality Check

**After Round 1 completes, verify quality before proceeding:**

```python
Task(general-investigator, f"""
You are the REVIEW SUPERVISOR. Check Round 1 outputs for quality issues.

ROUND 1 OUTPUTS (with LLM tags):
[AGENT: code-analysis]
{code_analysis_output}

[AGENT: security-auditor]
{security_output}

[AGENT: performance-optimizer]
{performance_output}

[AGENT: test-implementer]
{test_output}


YOUR JOB - Quality Control:

1. **Role Drift Detection**
   - Did code-analysis stay in its lane? (logic/correctness only)
   - Did security focus on security? (not performance)
   - Did any agent do another agent's job?

2. **Completeness Check**
   - Did each agent analyze ALL changed files: {'\n'.join(code_files + test_files)}?
   - Are findings backed by evidence (file:line + code snippet)?
   - Any JSON format violations?

3. **Contradiction Detection**
   - Do any findings contradict each other?
   - Example: Agent A says "SQL injection" + Agent B says "Parameterized query" at same location

4. **Missing Coverage**
   - Changed files not analyzed by ANY agent?
   - Critical areas skipped?

5. **Evidence Quality**
   - Vague claims? ("might be wrong")
   - Specific claims? ("Line 45: user_id in f-string")

RETURN JSON:
{{
  "drift_detected": {{}},
  "completeness_gaps": [],
  "contradictions": [],
  "missing_coverage": [],
  "weak_evidence": [],
  "recommendation": "PROCEED | RERUN_AGENT | ESCALATE",
  "rerun_instructions": ""
}}

If recommendation is RERUN_AGENT, provide specific instructions for what needs re-analysis.
""", max_tokens=None)
```

**Handle supervisor recommendations:**

```python
# If supervisor flags issues, act on them
if supervisor_result.recommendation == "RERUN_AGENT":
    # Re-run specific agents with clarified instructions
    # Include supervisor feedback in re-run prompt
    pass
elif supervisor_result.recommendation == "ESCALATE":
    # Flag for human review before continuing
    pass
# else: PROCEED to Round 2
```

---

## Phase 6: Round 2 - Requirements & Ripple Effects (Parallel)

**After Round 1 completes, launch Round 2:**

```python
req_tmpl = read('~/.claude/templates/pr-review-requirements.md')
ripple_breaking_tmpl = read('~/.claude/templates/pr-review-ripple-breaking.md')
ripple_integration_tmpl = read('~/.claude/templates/pr-review-ripple-integration.md')
ripple_db_tmpl = read('~/.claude/templates/pr-review-ripple-db.md')

# Launch in parallel (single message, 4 Tasks)

# 1. Requirements verification (ALWAYS runs)
# If ticket exists: verify code matches all ticket sections
# If no ticket: do code-only quality review
Task(general-investigator, req_tmpl.format(
    worktree_path=worktree,
    ticket_content=ticket_content if ticket_content else "NO TICKET DATA - Perform code-only quality review",
    changed_files='\n'.join(code_files + test_files),
    full_diff=full_diff
), max_tokens=None)

# NOTE: req_tmpl MUST instruct agent to:
# - If ticket data exists: Check ALL ticket sections (Description, Acceptance Criteria, Developer Checklist, Test Plan, Comments, Related Tickets)
# - If no ticket: Review code quality, test coverage, documentation
# - NEVER skip analysis because "no ticket" - code review is still mandatory

# 2. Ripple effect analysis - breaking changes
Task(general-investigator, ripple_breaking_tmpl.format(
    worktree_path=worktree,
    changed_files='\n'.join(code_files)
), max_tokens=None)

# 3. Ripple effect analysis - integration points
Task(general-investigator, ripple_integration_tmpl.format(
    worktree_path=worktree,
    changed_files='\n'.join(code_files)
), max_tokens=None)

# 4. DB field usage compatibility (only if DB changes)
if migration_files or context_analysis['has_db_changes']:
    Task(general-investigator, ripple_db_tmpl.format(
        worktree_path=worktree,
        changed_files='\n'.join(code_files + migration_files)
    ), max_tokens=None)
```

**Tag Round 2 outputs:**

```python
# After Round 2 agents complete, tag outputs
requirements_output = f"[AGENT: requirements-verifier]\n{requirements_response}" if ticket_content else ""
ripple_breaking_output = f"[AGENT: ripple-breaking-changes]\n{ripple_breaking_response}"
ripple_integration_output = f"[AGENT: ripple-integration-points]\n{ripple_integration_response}"
ripple_db_output = f"[AGENT: ripple-db-compatibility]\n{ripple_db_response}" if db_changes else ""
```

---

## Phase 7: Round 3 - Verification Round (Parallel)

**Prove or disprove critical/high findings to eliminate false positives:**

```python
# Collect all CRITICAL + HIGH findings from Round 1 & 2
critical_findings = [f for f in all_findings if f.severity in ["critical", "high"]]

verify_tmpl = read('~/.claude/templates/pr-review-verification.md')

# Spawn verifier for EACH critical/high finding (all in parallel, one message)
# Include original agent reasoning for context
for finding in critical_findings:
    Task(general-investigator, verify_tmpl.format(
        worktree_path=worktree,
        finding=finding,
        original_agent_reasoning=finding.agent_metadata,  # NEW: Pass original reasoning
        original_agent_name=finding.agent_name,           # NEW: Which agent found this
        changed_files='\n'.join(code_files + test_files)
    ), max_tokens=None)
```

**Verifier outputs:**
```json
{
  "verdict": "CONFIRMED" | "FALSE_POSITIVE" | "UNCERTAIN",
  "evidence": "Code snippet/trace/test showing proof",
  "explanation": "Why this is/isn't a real issue",
  "severity_adjustment": "critical|high|medium|low|none"  // May downgrade
}
```

**After verification:**
- Remove FALSE_POSITIVE findings
- Downgrade severity if verifier recommends
- Keep UNCERTAIN for human review
- Upgrade CONFIRMED with additional evidence

**Tag verification outputs:**

```python
# Tag each verification result
verification_outputs = []
for idx, verification in enumerate(verifier_responses):
    tagged_output = f"[AGENT: verifier-{idx}]\n{verification}"
    verification_outputs.append(tagged_output)
```

---

## Phase 8: Meta-Verification (Verify the Verifiers)

**For each FALSE_POSITIVE verdict, double-check the verifier's claim:**

```python
false_positives = [v for v in verifier_outputs if v.verdict == "FALSE_POSITIVE"]

# Launch meta-verifiers in parallel (one message)
for verification in false_positives:
    Task(general-investigator, f"""
A verifier claimed FALSE POSITIVE. Independently verify this claim.

Original finding:
{verification.original_finding}

Original agent: {verification.original_agent}
Original reasoning: {verification.original_reasoning}

Verifier's claim:
{verification.verifier_reasoning}
Verifier's verdict: FALSE_POSITIVE

YOUR JOB: Verify the verifier's claim.
- Did verifier actually read the code at the specified location?
- Is verifier's reasoning sound?
- Did verifier miss something the original agent saw?
- Is there any validity to the original finding?

WORKTREE PATH: {worktree}

Read the actual code and make independent assessment.

RETURN:
{{{{
  "verdict": "AGREE | DISAGREE | UNCERTAIN",
  "evidence": "Why you agree/disagree with verifier",
  "code_snippet": "Actual code at the location",
  "final_recommendation": "REMOVE_FINDING | RESTORE_FINDING | NEEDS_HUMAN"
}}}}

Be thorough. False positives waste reviewer time, but removing real issues is dangerous.
""", max_tokens=None)
```

**Process meta-verification results:**

```python
# After meta-verifiers complete:
# - If DISAGREE: Restore the original finding (verifier was wrong)
# - If AGREE: Keep finding removed (verifier was right)
# - If UNCERTAIN: Flag for human review (can't determine definitively)
```

---

## Phase 9: Round 4 - Second Investigation Pass (Parallel)

**Fresh perspective to catch what Round 1 missed:**

```python
# Launch 2-3 investigators with different angles

# Investigator 1: Focus on edge cases and error handling
Task(general-investigator, f"""
Review {changed_files} for edge cases and error handling gaps.

WORKTREE PATH: {worktree_path}

Previous rounds focused on security, performance, tests. You focus on:
- Edge cases: empty lists, None, 0, negative numbers, unicode, large inputs
- Error handling: what happens when external service fails?
- Recovery: can system recover from partial failures?
- Logging: are errors logged with enough context?

Success criteria:
- All changed files analyzed for edge cases
- Findings include file:line + code snippet + impact
- Missing error handling identified with specific scenarios

CRITICAL STANDARDS (inline):
- Start narrow, expand if needed (progressive disclosure)
- Use Grep (cheap) before Read (focused)
- Don't read >5 files without reporting findings first
- Include file:line references in all findings
- Check for improper try/except (wrapping safe operations)
- Check logging uses logging.getLogger(__name__)

Expected output format:
{{{{
  "status": "COMPLETE",
  "agent_type": "edge-case-investigator",
  "files_analyzed": ["file1.py", "file2.py"],
  "findings": [
    {{{{
      "category": "edge_case" | "error_handling" | "recovery" | "logging",
      "severity": "critical" | "high" | "medium" | "low",
      "file": "path/to/file.py",
      "line": 123,
      "issue": "Specific description",
      "evidence": "Code snippet showing issue",
      "impact": "What breaks / fails",
      "fix": "How to resolve"
    }}}}
  ]
}}}}

Return valid JSON only - no prose, no markdown.
""", max_tokens=None)

# Investigator 2: Focus on data flow and state management
Task(general-investigator, f"""
Review {changed_files} for data flow issues and state management.

WORKTREE PATH: {worktree_path}

Previous rounds may have missed:
- State mutations: unexpected side effects?
- Data transformations: data loss or corruption possible?
- Race conditions: concurrent access issues?
- Idempotency: safe to retry operations?

Success criteria:
- All changed files analyzed for data flow and state issues
- Findings include file:line + code snippet + reproduction scenario
- Race conditions identified with specific concurrent access patterns

CRITICAL STANDARDS (inline):
- Start narrow, expand if needed (progressive disclosure)
- Use Grep (cheap) before Read (focused)
- Don't read >5 files without reporting findings first
- Include file:line references in all findings
- Trace data transformations step-by-step
- Identify shared state mutations

Expected output format:
{{{{
  "status": "COMPLETE",
  "agent_type": "data-flow-investigator",
  "files_analyzed": ["file1.py", "file2.py"],
  "findings": [
    {{{{
      "category": "state_mutation" | "data_transformation" | "race_condition" | "idempotency",
      "severity": "critical" | "high" | "medium" | "low",
      "file": "path/to/file.py",
      "line": 123,
      "issue": "Specific description",
      "evidence": "Code snippet showing issue",
      "impact": "What breaks / data loss scenario",
      "fix": "How to resolve"
    }}}}
  ]
}}}}

Return valid JSON only - no prose, no markdown.
""", max_tokens=None)

# Investigator 3: Focus on observability and debugging
Task(general-investigator, f"""
Review {changed_files} for observability and debugging issues.

WORKTREE PATH: {worktree_path}

Check:
- Logging: enough context to debug production issues?
- Metrics: can we measure performance in prod?
- Error messages: helpful or cryptic?
- Debugging: easy to reproduce issues locally?

Success criteria:
- All changed files analyzed for observability issues
- Findings include file:line + what's missing + why it matters
- Logging gaps identified with specific debug scenarios

CRITICAL STANDARDS (inline):
- Start narrow, expand if needed (progressive disclosure)
- Use Grep (cheap) before Read (focused)
- Don't read >5 files without reporting findings first
- Include file:line references in all findings
- Check logging uses logging.getLogger(__name__)
- Check error messages are actionable (not cryptic)

Expected output format:
{{{{
  "status": "COMPLETE",
  "agent_type": "observability-investigator",
  "files_analyzed": ["file1.py", "file2.py"],
  "findings": [
    {{{{
      "category": "logging" | "metrics" | "error_messages" | "debugging",
      "severity": "critical" | "high" | "medium" | "low",
      "file": "path/to/file.py",
      "line": 123,
      "issue": "Specific description",
      "evidence": "Code snippet showing gap",
      "impact": "What's hard to debug / monitor",
      "fix": "How to improve observability"
    }}}}
  ]
}}}}

Return valid JSON only - no prose, no markdown.
""", max_tokens=None)
```

**Why second pass?**
- Different focus areas than specialized agents
- Fresh eyes catch what familiarity blinds
- Research shows multi-pass reduces missed issues by 40%

**Tag Round 4 outputs:**

```python
# Tag second-pass investigation outputs
edge_case_output = f"[AGENT: investigator-edge-cases]\n{edge_case_response}"
data_flow_output = f"[AGENT: investigator-data-flow]\n{data_flow_response}"
observability_output = f"[AGENT: investigator-observability]\n{observability_response}"
```

---

## Phase 10: Deep Investigation (Needs Investigation Items)

**Items flagged as "needs_investigation" get unlimited investigation time:**

```python
needs_investigation = [f for f in all_findings if f.category == "needs_investigation"]

# Launch deep investigators in parallel (one message, multiple Tasks)
for item in needs_investigation:
    Task(general-investigator, f"""
Something suspicious found that needs deeper investigation:

Finding: {item.description}
Location: {item.file}:{item.line}
Original agent: {item.agent_name}
Original reasoning: {item.reasoning}

YOUR JOB: Unlimited time to investigate thoroughly.

Investigation steps:
1. Read ALL related files (not just changed files)
2. Trace through entire call chain (upstream and downstream)
3. Check git history (when was this added? why? by whom?)
4. Check for related patterns elsewhere in codebase
5. Test scenarios mentally (can you construct reproduction case?)
6. Consider architectural implications

WORKTREE PATH: {worktree}

Take as long as needed. Return when you have DEFINITIVE answer.

RETURN:
{{{{
  "verdict": "CONFIRMED_ISSUE | FALSE_ALARM | ARCHITECTURAL_CONCERN | NEEDS_DISCUSSION",
  "evidence": "Full investigation results with file:line references",
  "investigation_path": "What you checked and why",
  "recommendation": "What should be done (specific action)",
  "confidence": 0.95  // How certain are you (0-1)
}}}}

If still uncertain after deep dive, verdict should be NEEDS_DISCUSSION with human.
""", max_tokens=None)
```

---

## Phase 11: Contradiction Resolution

**Before synthesis, resolve any contradictions between agents:**

```python
# Find contradictions: Same file:line with conflicting claims
contradictions = find_contradictions(all_findings)

if contradictions:
    # Launch tie-breaker investigators in parallel
    for contradiction in contradictions:
        Task(general-investigator, f"""
CONTRADICTION DETECTED - You are the tie-breaker.

Location: {contradiction.file}:{contradiction.line}

Finding A (from {contradiction.agent_a}):
{contradiction.finding_a}
Reasoning: {contradiction.reasoning_a}
Confidence: {contradiction.confidence_a}

Finding B (from {contradiction.agent_b}):
{contradiction.finding_b}
Reasoning: {contradiction.reasoning_b}
Confidence: {contradiction.confidence_b}

YOUR JOB: Determine which agent is correct (or if both are wrong/partially correct).

Steps:
1. Read the code independently at {contradiction.file}:{contradiction.line}
2. Trace execution paths that each agent might have considered
3. Consider what each agent might have missed
4. Provide DEFINITIVE answer with proof

WORKTREE PATH: {worktree}

RETURN:
{{{{
  "correct_agent": "agent_a | agent_b | both_wrong | both_partially_correct",
  "resolution": "Detailed explanation of what's actually happening",
  "evidence": "Code snippet showing proof",
  "final_verdict": {{{{
    "issue": "What the actual issue is (if any)",
    "severity": "critical|high|medium|low|none",
    "confidence": 0.98
  }}}}
}}}}

Your evidence must include actual code snippet from the worktree.
""", max_tokens=None)
```

**Apply contradiction resolutions:**

```python
# After tie-breakers complete:
# - Remove findings from incorrect agent(s)
# - Update finding with tie-breaker's verdict
# - If both_partially_correct: Merge insights into single finding
```

---

## Phase 11.5: Final Reasonableness Filter

**Last sanity check before returning to user - filter out garbage:**

```python
# After all verification, contradiction resolution, and deep investigation
# One final filter to remove findings that aren't worth the user's time

Task(general-investigator, f"""
You are the FINAL REASONABLENESS FILTER.

Your job: Remove findings that waste the user's time.

**LOAD SKILLS FIRST:**
- pr-review-common-patterns (has DO NOT FLAG list)
- pr-review-standards (has severity thresholds)

ALL FINDINGS (post-verification):
{json.dumps(all_findings, indent=2)}

YOUR JOB: Aggressively remove findings that are:

**1. Personal Preferences** (ALWAYS remove):
- Variable naming style ("data" vs "result")
- Comment style ("TODO" vs "FIXME")
- Import ordering
- Formatting/whitespace preferences
- Single vs double quotes

**2. Style Nitpicks** (ALWAYS remove):
- Line length <5 chars over limit
- Missing docstrings on private functions
- "Not descriptive enough" variable names
- Obvious "magic numbers" (port 443, HTTP 200)
- "Could be more Pythonic"

**3. Theoretical Issues** (ALWAYS remove):
- "Could be problematic" without reproduction
- "Might cause issues if..." without demonstrating the "if"
- "Should validate this" without proving unvalidated input reaches danger
- "Consider refactoring" without concrete benefit
- "This looks wrong" without evidence

**4. Not Project Standards** (remove if not enforced):
- Missing type hints (if project doesn't require them)
- Line length violations (if project allows longer lines)
- Naming conventions (if no project standard)

**KEEP findings that are:**

**1. WILL Break Production:**
- Crashes with reproduction scenario
- `TypeError`, `AttributeError`, `KeyError` with inputs
- Division by zero with empty list proof
- Data corruption with scenario

**2. Security Vulnerabilities:**
- SQL injection with exploit proof
- Auth bypass with demonstration
- Hardcoded secrets (actual secrets, not placeholders)
- PII in logs (actual PII fields)

**3. Breaking Changes:**
- API contract changes with list of affected callers
- Function signature changes with caller analysis
- Behavior changes that break consumers

**4. Significant Performance Issues:**
- >10x regression with calculation
- N+1 queries with quantified impact (1000 users = 1000 queries)
- O(n) → O(n²) with calculation
- Removed caching with 100x+ impact

**THE TEST:**
For EACH finding, ask: "Would I stop a teammate in code review to mention this?"
- If NO → REMOVE IT
- If YES → KEEP IT

**ANOTHER TEST:**
"Can I write a failing test case for this?"
- If NO → REMOVE IT (it's theoretical)
- If YES → KEEP IT (it's provable)

**BE AGGRESSIVE:**
- When in doubt, REMOVE the finding
- Better to miss a nitpick than waste user's time
- If finding doesn't have STRONG evidence → REMOVE

RETURN JSON:
{{
  "kept_findings": [
    {{
      "finding_id": "original_id",
      "reason": "Will crash with empty list (reproduction: line 45 with [])"
    }}
  ],
  "removed_findings": [
    {{
      "finding_id": "original_id",
      "reason": "Personal preference - variable naming style",
      "category": "personal_preference" | "nitpick" | "theoretical" | "not_project_standard" | "no_strong_evidence"
    }}
  ],
  "removal_stats": {{
    "personal_preferences": 5,
    "style_nitpicks": 3,
    "theoretical_issues": 2,
    "no_strong_evidence": 4,
    "not_project_standard": 1
  }},
  "final_finding_count": 12,
  "summary": "Removed 15 low-value findings (personal preferences, nitpicks, theoretical issues). Kept 12 high-impact findings (3 critical, 5 high, 4 medium)."
}}

REMEMBER: User is tired of false positives and nitpicks. Only keep findings worth their time.
""", max_tokens=None)

# Apply reasonableness filter
all_findings = [f for f in all_findings if f.id in reasonableness_result.kept_findings]

# Log what was removed for transparency
LOG.info(f"Reasonableness filter removed {len(reasonableness_result.removed_findings)} findings")
LOG.info(f"Removal breakdown: {reasonableness_result.removal_stats}")
```

**Why this phase matters:**
- Agents still flag preferences/nitpicks despite verification
- Last line of defense against wasting user's time
- Dramatically reduces false positives and subjective opinions
- Focus user attention on real, impactful issues

---

## Phase 12: Synthesis & Final Report

### 12.1 Filter Irrelevant Findings (Ticket Scope Check)

**Before cross-validation, filter findings against ticket scope:**

```python
# Launch scope validator to check each finding's relevance
Task(general-investigator, f"""
You are the RELEVANCE FILTER. Check all findings against ticket scope.

TICKET: {ticket}
TICKET REQUIREMENTS:
{ticket_content}

GIT DIFF (what changed in this PR):
{full_diff}

ALL FINDINGS FROM PREVIOUS ROUNDS:
{json.dumps(all_findings, indent=2)}

YOUR JOB: Filter out findings that are NOT relevant to this PR.

KEEP findings that:
1. Are on lines that appear in the git diff (+/- lines)
2. Are in functions/classes modified by this PR (even if specific line not in diff)
3. Relate to ticket requirements (even if pre-existing)
4. Will BREAK due to this PR's changes
5. Are similar patterns to what's being added (consistency)

REMOVE findings that:
1. Are pre-existing issues in unmodified code
2. Are unrelated to ticket requirements
3. Are general code quality issues in unchanged code
4. Are in files touched by PR but unrelated to the changes

For EACH finding:
1. Check the file:line in the git diff
2. Check if it relates to ticket requirements
3. Determine if it's relevant

RETURN JSON:
{{
  "kept_findings": [
    {{
      "finding_id": "original_id",
      "reason": "Modified in PR at line X" | "Relates to ticket req: Y" | "Called by new code at Z"
    }}
  ],
  "removed_findings": [
    {{
      "finding_id": "original_id",
      "reason": "Pre-existing, unrelated to ticket" | "Unchanged code, no ticket relation"
    }}
  ]
}}

Be conservative: When in doubt, KEEP the finding (false positive better than false negative).
""", max_tokens=None)

# Apply scope filter
all_findings = [f for f in all_findings if f.id in scope_filter_result.kept_findings]
```

### 12.2 Cross-Validate All Findings

```python
# Consolidate findings from all rounds
all_findings = (
    round1_findings +        # 5-6 specialized agents
    round2_findings +        # 3-4 requirements/ripple agents
    round3_findings +        # N verification agents (adjusted severities)
    round4_findings +        # 2-3 second-pass investigators
    deep_investigation_findings +  # Deep dives on needs_investigation items
    contradiction_resolutions      # Tie-breaker verdicts
)

# 1. Remove false positives (marked by verifiers and confirmed by meta-verification)
verified_findings = [f for f in all_findings if f.verdict != "FALSE_POSITIVE"]

# 1a. Restore findings if meta-verifier disagreed with verifier
for meta_result in meta_verification_results:
    if meta_result.final_recommendation == "RESTORE_FINDING":
        verified_findings.append(meta_result.original_finding)

# 2. Verify file:line references exist in worktree
cd /tmp/pr-review-{ticket}/wt-pr
for finding in verified_findings:
    # Check file exists and line is valid
    if ! [ -f {finding.file} ]; then
        # Invalid reference, remove
        continue
    fi
    line_count=$(wc -l < {finding.file})
    if [ {finding.line} -gt $line_count ]; then
        # Invalid line number, remove
        continue
    fi
done

# 3. Remove duplicates (same file:line, same issue type)
deduped_findings = remove_duplicates(verified_findings)

# 4. Flag contradictions for manual review
contradictions = find_contradictions(deduped_findings)
# Example: Agent A says "SQL injection at line 45", Agent B says "Parameterized query at line 45"
```

### 12.3 Add PEP 8 Style Check

**You do this (agents don't):**

```python
# Check import grouping
# Standard library → blank line → third-party → blank line → local

# Check line length (80 char max)

# Check naming conventions
# snake_case for functions/variables
# PascalCase for classes
# UPPER_CASE for constants

# Add findings to "medium" severity if violations found
```

### 12.4 Categorize by Severity

```python
# Sort findings into buckets
critical = [f for f in deduped_findings if f.severity == "critical"]
high = [f for f in deduped_findings if f.severity == "high"]
medium = [f for f in deduped_findings if f.severity == "medium"]
low = [f for f in deduped_findings if f.severity == "low"]
needs_verification = [f for f in deduped_findings if f.verdict == "UNCERTAIN"]

# Severity guidelines:
# 🔴 Critical: Security vulns, data corruption, crashes, breaking changes
# 🟡 High: Performance regressions, missing tests, logic bugs with impact
# 🔵 Medium: Code quality issues, optimization opportunities, style violations
# 🟢 Low: Nitpicks, suggestions, minor improvements
# 🟣 Needs Verification: Uncertain findings requiring human judgment
```

### 12.5 Generate Final Report

```markdown
# PR Review: {ticket} - {jira_title}

**Branch:** origin/{source_branch} → origin/{target_branch}
**Commits:** {count} | **Files:** {count} ({code_count} code, {test_count} test, {other_count} other)
**Lines:** +{added} -{removed}

## Review Summary

**Issues Found:** Critical: {X} | High: {Y} | Medium: {Z} | Low: {W}
**Needs Verification:** {V} (human judgment required)
**Recommendation:** {APPROVE | REQUEST CHANGES | NEEDS DISCUSSION}

**Context:** {internal_api|external_api|payment_logic|pii_handling|etc}
- This affects security scrutiny and validation depth

---

## 🔴 Critical Issues (Must Fix Before Merge)

{If none: "✅ No critical issues found"}

1. **{Category}** ({file.py:line})
   - **Problem:** {what's wrong - specific description}
   - **Evidence:** {code snippet or trace showing issue}
   - **Impact:** {what breaks / security risk / data loss}
   - **Fix:** {exact code change or approach}
   - **Verified:** ✅ Confirmed by verification round

---

## 🟡 High Priority (Should Fix)

{If none: "✅ No high priority issues"}

1. **{Category}** ({file.py:line})
   - **Problem:** {what's wrong}
   - **Evidence:** {proof}
   - **Impact:** {performance/reliability/breaking change}
   - **Fix:** {how to fix}

---

## 🔵 Medium Priority (Consider)

{If none: "✅ No medium priority issues"}

1. **{Category}** ({file.py:line})
   - **Problem:** {what could be better}
   - **Suggestion:** {improvement idea}
   - **Benefit:** {why this matters}

---

## 🟢 Low Priority (Optional)

{If none: "✅ No low priority suggestions"}

1. **{Category}** ({file.py:line})
   - **Suggestion:** {minor improvement}

---

## 🟣 Needs Human Verification

{If none: "✅ All findings verified by agents"}

1. **{Category}** ({file.py:line})
   - **Concern:** {what might be wrong}
   - **Uncertainty:** {why agent couldn't confirm}
   - **Verification Needed:** {what human should check}

---

## ✅ What's Good

{Specific positive findings - don't skip this section}

- **Strong test coverage:** file.py has 98% coverage with edge cases tested
- **Good error handling:** Proper try/except for DB connections only, not safe ops
- **Clean separation:** Auth logic properly separated from business logic
- **Performance conscious:** Batch operations used, no N+1 queries

---

## 📊 Ticket Coverage Analysis

### Requirements (from Description/Acceptance Criteria)

**Requirement 1:** {description from ticket}
- ✅ Implemented in: file.py:line-range
- ✅ Tested in: test_file.py:line-range

**Requirement 2:** {description}
- ⚠️ Partially implemented - missing {specific gap}
- ❌ No tests for this requirement

### Developer Checklist Coverage

**Checklist Item 1:** Create new collection "activitiesEmail"
- ✅ Implemented: models/activity_email.py:15-45
- ✅ Matches spec: Schema matches documented structure

**Checklist Item 2:** Update nodemailer endpoint to accept "activity_meta"
- ⚠️ Partial: Endpoint updated but validation incomplete
- Location: api/nodemailer.py:123

[If no Developer Checklist in ticket data: State "No Developer Checklist in ticket"]

### Test Plan Coverage

**Test Case 1:** {from Test Plan}
- ✅ Covered: test_notifications.py:67-89

**Test Case 2:** {from Test Plan}
- ❌ Missing: No test found for this scenario

[If no Test Plan or says "TODO": State "Test Plan not provided or marked TODO - assessed test coverage from code review"]

### Ticket Comments Context

**Relevant decisions from comments:**
- Milind Joshi (2024-12-18): Email content retention set to 5 years (implemented: retention_policy.py:34)
- Kelly Peyton (2024-12-17): Archive message added for old content (implemented: activity_service.py:156)

[If no relevant comments: State "No relevant context from ticket comments"]

### Related Tickets Impact

**PLAT-53 (Frontend pair):**
- Status: In Progress
- Impact: BE provides "activitiesEmail" collection, FE consumes for display
- Coordination needed: Ensure FE team aware of schema changes

[If no related tickets: State "No related tickets"]

---

## 🧪 Test Coverage

**Well Covered:**
- file.py:45-67 `calculate_total()` - 100% coverage, all edge cases tested
- file.py:89-102 `validate_input()` - Happy path + 5 error scenarios

**Missing Coverage:**
- file.py:120-135 `process_refund()` - No tests (RISK: Financial logic untested)
- file.py:145 `_helper_function()` - No tests for edge case: empty list

**Test Issues:**
- test_file.py:34 - Test doesn't actually test claimed behavior (asserts on wrong variable)
- test_file.py:67 - Integration test uses mock (should use real DB)

---

## 🔒 Security Analysis

**Context:** {Internal API / External API / Payment Logic / etc}

{For internal APIs:}
✅ Input validation present
✅ No hardcoded secrets
⚠️ {concerns with file:line}

{For external APIs - more detailed:}
✅ Rate limiting implemented
✅ Input sanitization for SQL injection
✅ CSRF protection present
✅ No sensitive data in logs
⚠️ {concerns with file:line}

---

## 💾 Database Changes

**Schema Changes:**
- Added column: `users.tax_rate` (DECIMAL(5,4), default 0.0)
- Modified column: `orders.status` (VARCHAR(20) → VARCHAR(50))
- Removed column: `products.legacy_id` ⚠️ **Breaking change**

**Compatibility:**
✅ All existing code updated to handle new `tax_rate` field
⚠️ `reports.py:145` still references removed `legacy_id` - will break

**Migration Safety:**
✅ Migration has rollback path
✅ Default values prevent NULL issues
⚠️ No migration for data transformation (old status values incompatible)

---

## ⚡ Performance

**Analyzed:**
- ✅ No N+1 query problems
- ✅ Batch operations used where appropriate
- ✅ Caching strategy unchanged (no regressions)

**Concerns:**
- file.py:89 - Linear scan of list inside loop (O(n²)) - 10k items = 100M operations
  - **Fix:** Use set for O(1) lookup or dict for mapping

**Opportunities:**
- file.py:123 - Could cache result of expensive calculation (called 1000x per request)

---

## 🔄 Ripple Effects & Breaking Changes

**Breaking Changes:**
1. **`calculate_total()` signature changed** (billing.py:45)
   - Added required parameter: `tax_rate`
   - **Affects:**
     - ✅ invoices.py:123 - UPDATED to pass tax_rate
     - ✅ reports.py:67 - UPDATED to pass tax_rate
     - ❌ legacy_import.py:89 - NOT UPDATED (will crash)

**Integration Impacts:**
- API endpoint `/api/billing/calculate` now requires `tax_rate` param
  - ⚠️ Breaking change for API consumers (needs version bump or backward compat)

**Side Effects:**
- Logging volume increased by 3x (new DEBUG logs in hot path)
  - Consider: Log level adjustment for production

---

## 📝 Code Quality

**PEP 8 Compliance:**
✅ Import grouping correct
✅ Line length within 80 chars
✅ Naming conventions followed

**Code Quality Issues:**
- file.py:145 - Function has cyclomatic complexity 15 (threshold: 10)
  - **Fix:** Extract validation logic, error handling to separate functions

**Documentation:**
✅ Docstrings present for public functions
⚠️ file.py:67 - Complex logic but no WHY comment

---

## 🎯 MR Comment Status

### ✅ Addressed Comments ({count})

**Comment 1** (by @reviewer, 2 days ago): "Missing validation for negative amounts"
- ✅ Fixed at: file.py:78
- Fix quality: Complete
- Evidence: Added `if amount < 0: raise ValueError()`

**Comment 2** (by @reviewer, 1 day ago): "Should we batch these DB calls?"
- ✅ Fixed at: file.py:123-145
- Fix quality: Complete
- Evidence: Replaced loop with bulk_insert()

### ⚠️ Dismissed With Reasoning ({count})

**Comment 3** (by @security, 3 hours ago): "Potential SQL injection?"
- 🟢 Reasoning: "Uses parameterized query - see line 45"
- Quality: Sound
- Verified: ✅ Confirmed parameterized query used

**Comment 4** (by @reviewer, 1 day ago): "Should handle edge case X?"
- 🟡 Reasoning: "Rare edge case, will handle in follow-up INT-4567"
- Quality: Questionable - Follow-up ticket not found in Jira
- Verified: ❌ INT-4567 doesn't exist - **needs follow-up**

### 🔴 Outstanding Comments (No Response) ({count})

**Comment 5** (by @lead, 2 days ago): "This breaks backward compatibility"
- Severity: CRITICAL
- Days outstanding: 2
- **REQUIRES RESPONSE** - Breaking change concern unaddressed

### 📋 Planned Follow-ups ({count})

**Comment 6** (by @reviewer): "Refactor this for better performance"
- Planned: "Will optimize in INT-4568"
- Tracked in: INT-4568 (verified in Jira)
- Status: ✅ Properly tracked

**Comment 7** (by @reviewer): "Add more test coverage"
- Planned: "Will add in next sprint"
- Tracked in: ❌ Not tracked - **needs ticket**

### 💬 Resolved by Discussion ({count})

**Comment 8** (by @reviewer): "Why use X instead of Y?"
- Resolution: Clarified that Y doesn't support feature Z needed here
- No code change needed

---

## 🎬 Final Recommendation

**Status:** {APPROVE ✅ | REQUEST CHANGES ❌ | NEEDS DISCUSSION 💬}

{For REQUEST CHANGES:}
**Must fix before merge:**
1. Critical issue #1 - {specific fix needed}
2. Critical issue #2 - {specific fix needed}
3. High priority #1 - {specific fix needed}

**Must address:**
- Outstanding MR comments (critical/high priority)
- Questionable dismissals need re-evaluation
- Untracked follow-ups need tickets created

**Should fix (optional for this PR, but create follow-up tickets):**
- Medium issue #1
- Medium issue #2

{For APPROVE:}
**Quality assessment:**
- Code is well-tested (95%+ coverage)
- Security considerations appropriate for {context}
- No breaking changes or properly documented
- Performance characteristics acceptable
- Requirements fully implemented

**Minor improvements for follow-up:**
- {Optional improvements as separate tickets}

{For NEEDS DISCUSSION:}
**Questions for team:**
1. {Architectural decision needed}
2. {Trade-off requiring team input}
3. {Breaking change - how to handle?}

---

## 📊 Review Statistics

**Agent Rounds:**
- Phase 4 (Specialized): 4 agents, {X} findings
- Phase 5 (Supervisor): Quality check passed/failed, {Y} issues flagged
- Phase 6 (Requirements/Ripple): 4 agents, {Z} findings
- Phase 7 (Verification): {N} verifiers, {W} false positives removed
- Phase 8 (Meta-Verification): {M} verifier claims checked, {P} findings restored
- Phase 9 (Second Pass): 3 agents, {Q} additional findings
- Phase 10 (Deep Investigation): {R} deep dives completed
- Phase 11 (Contradiction Resolution): {S} contradictions resolved

**Verification Results:**
- Total findings (all rounds): {total}
- Verified real issues: {verified}
- False positives removed: {false_positives}
- False positives restored (meta-verification caught bad verifier): {restored}
- Contradictions resolved: {contradictions}
- Deep investigations completed: {deep_dives}
- Needs human review: {uncertain}
- Verification accuracy: {verified / total * 100}%
- Meta-verification accuracy: {(false_positives - restored) / false_positives * 100}%

**Coverage:**
- Files reviewed: {count}
- Functions analyzed: {count}
- Integration points checked: {count}
- Database fields validated: {count}

---
```

---

## Phase 13: Cleanup

```bash
# Always cleanup worktrees when done
~/.claude/scripts/git-worktree --cleanup

# Worktrees removed:
# - /tmp/pr-review-{ticket}/wt-base
# - /tmp/pr-review-{ticket}/wt-pr

# IMPORTANT: Verify no branches were created in main repo
# After cleanup, run: git branch | grep review-
# Should return nothing - if it shows branches, you created branches incorrectly
# The correct approach: detached HEAD in worktree (no branch creation)
```

---

## Error Handling

### Branch Not Found

```bash
if ! git branch -r | grep -q "origin/$ticket"; then
    echo "❌ No branch found for ticket: $ticket"
    echo ""
    echo "Similar branches:"
    git branch -r | grep -i "${ticket%%-*}" | head -5 || echo "  (none found)"
    exit 1
fi
```

### Multiple Branches

When multiple branches exist for a ticket, the agent makes an intelligent decision based on:

**Decision criteria (in priority order):**

1. **Branch name patterns** - Avoid branches with:
   - "test" (unless it's like "latest-feature")
   - "experimental"
   - "spike"
   - Other obvious non-production indicators
   - But use context - don't filter blindly

2. **Most recent commit** - More recent = likely the active branch

3. **Commit messages** - Look for production-ready work vs WIP/experimental

**Default behavior:** If agent can't decide or all branches seem equal, pick the most recently updated one.

**Implementation:** See section 2.2 - the bash script displays all branches with metadata, then agent decides which `source_branch` to use before proceeding to worktree setup.

### No Commits Between Branches

```bash
if ! git log origin/$target..origin/$source --oneline | grep -q .; then
    echo "❌ No commits between branches (already merged?)"
    echo "Target: $target_branch"
    echo "Source: $source_branch"
    exit 1
fi
```

### Scripts Not Available or Credentials Missing

```python
# Gracefully handle missing scripts or credentials
jira_result = Bash(command=f"~/.claude/scripts/jira-get-issue {ticket}")
if jira_result.returncode == 4:
    echo("⚠️  Jira credentials not configured - skipping ticket requirements check")
    ticket_content = None
elif jira_result.returncode == 0:
    ticket_content = jira_result.stdout
else:
    ticket_content = None  # Ticket not found

gitlab_result = Bash(command=f"~/.claude/scripts/gitlab-mr-comments {ticket}")
if gitlab_result.returncode == 4:
    echo("⚠️  GitLab credentials not configured - skipping MR comment check")
    mr_comments = None
elif gitlab_result.returncode == 0:
    mr_comments = gitlab_result.stdout
else:
    mr_comments = None  # MR not found
```

---

## Key Principles

### 1. Multi-Round Architecture

**Never single-pass review.** Research shows:
- Single pass: 60% false positive rate
- With verification: 4% false positive rate (15x improvement)
- Second investigation pass: Catches 40% more real issues

### 2. Context-Aware Scrutiny

**Not all code needs same paranoia:**
- External API → High security scrutiny (injection, auth, rate limits)
- Internal API → Medium security (validate inputs, but less paranoid)
- Payment logic → Extra validation (decimal precision, idempotency, rollback)
- PII handling → Data exposure checks (logging, encryption, access control)
- Pure utility functions → Focus on correctness, edge cases

### 3. No Assumptions Allowed

**Rule:** If agent can't prove it, flag as NEEDS_VERIFICATION, not ISSUE.

**Bad:** "This could be a SQL injection" (without proof)
**Good:** "Potential SQL injection - need to verify if input is sanitized upstream" (flagged for human review)

### 4. Evidence Required

**Every finding must have:**
- File:line reference (verified to exist)
- Code snippet or trace (proof)
- Impact explanation (why it matters)
- Fix suggestion (actionable)

**No theoretical concerns without evidence.**

### 5. Fresh Perspectives

**Why multiple rounds with different agents?**
- Specialized agents (Round 1) focus on domain expertise
- Requirements agents (Round 2) focus on "did we build what was asked?"
- Verifiers (Round 3) focus on "is this claim actually true?"
- Second-pass investigators (Round 4) focus on "what did we miss?"

Different angles = comprehensive coverage.

### 6. DB Schema Compatibility

**Critical for DB changes:**
1. Detect schema changes (migrations, model changes, DDL)
2. Find ALL code using affected fields (not just changed files)
3. Check type compatibility (INT → VARCHAR breaks integer math)
4. Check for missing field handling (new fields, removed fields, defaults)
5. Verify migration path (can we roll back? data transformation needed?)

### 7. Ripple Effect Analysis

**Never review in isolation:**
- Find all callers of changed functions (across entire codebase)
- Check integration points (APIs, message queues, caches, DB)
- Verify backward compatibility (breaking changes documented?)
- Check side effects (logging, metrics, monitoring)

---

## Validation Checklist

**Before sending report to user:**

- [ ] agent-prompting skill loaded before spawning agents
- [ ] All agent prompts include critical inline standards
- [ ] All agent prompts include BUDGET DIRECTIVE (never stop short)
- [ ] All agent prompts include SCOPING RULES (ticket relevance filter)
- [ ] All agents receive ticket_content and full_diff for scoping
- [ ] No token limits on agents (max_tokens=None or omitted)
- [ ] LLM tagging implemented for all agent outputs ([AGENT: name] format)
- [ ] Phase 3.2 complete (MR comment thread analysis if comments exist)
- [ ] Phase 4 complete (4 specialized agents)
- [ ] Phase 5 complete (supervisory quality check)
- [ ] Phase 6 complete (3-4 requirements/ripple agents)
- [ ] Phase 7 complete (N verification agents with original agent reasoning)
- [ ] Phase 8 complete (meta-verification of FALSE_POSITIVE claims)
- [ ] Phase 9 complete (2-3 second-pass investigators)
- [ ] Phase 10 complete (deep investigations of needs_investigation items)
- [ ] Phase 11 complete (contradiction resolution)
- [ ] Phase 12.1 complete (scope filter removes irrelevant findings)
- [ ] All file:line references verified in worktree
- [ ] False positives removed (verification round results)
- [ ] Duplicates removed (same file:line:issue)
- [ ] Contradictions flagged for manual review
- [ ] Findings categorized by severity (critical/high/medium/low/needs_verification)
- [ ] PEP 8 violations checked and added
- [ ] Context-aware security applied (internal vs external)
- [ ] DB schema compatibility verified (or confirmed no DB changes)
- [ ] Requirements coverage checked (or confirmed no ticket data available)
- [ ] MR comments addressed (or confirmed no MR comments available)
- [ ] Clear recommendation provided (APPROVE/REQUEST CHANGES/NEEDS DISCUSSION)
- [ ] Positive findings included ("What's Good" section)
- [ ] Worktrees cleaned up
- [ ] Review statistics included (rounds, verification accuracy)

---

## Anti-Patterns to Avoid

❌ **Single-pass review** - No verification, assumptions slip through
❌ **Same security scrutiny for all code** - Wastes time on internal utils
❌ **No evidence for findings** - "This looks wrong" without proof
❌ **Only reviewing changed files** - Misses breaking changes in callers
❌ **Skipping second investigation** - Leaves stones unturned
❌ **No false positive removal** - User gets flooded with noise
❌ **Generic templates** - Agents don't know project standards
❌ **No LLM tagging** - Can't trace which agent produced which output
❌ **Trusting verifiers blindly** - Meta-verification catches bad verifier claims
❌ **Ignoring contradictions** - Different agents with conflicting findings must be resolved
❌ **Skipping deep investigation** - Items flagged as "needs investigation" deserve thorough analysis

---

## Success Metrics

**10/10 PR review has:**
- ✅ Zero false positives reach user (verification round filters them)
- ✅ No missed critical issues (multi-round coverage)
- ✅ Context-appropriate scrutiny (internal vs external)
- ✅ Clear, actionable findings (file:line + evidence + fix)
- ✅ Requirements verified (Jira ticket mapped to code)
- ✅ Breaking changes caught (ripple effect analysis)
- ✅ DB compatibility verified (schema change impact)
- ✅ Fast execution (parallel agents, not sequential)
- ✅ High confidence recommendation (APPROVE/REJECT/DISCUSS)

**Expected review time:**
- Simple PR (5-10 files): 3-5 minutes (parallel execution)
- Medium PR (20-40 files): 8-12 minutes
- Complex PR (50+ files): 15-25 minutes

**Parallelization saves 80% time vs sequential.**
