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

1. **Phase 1:** Specialized domain reviews (4 parallel agents)
   - All outputs tagged with [AGENT: name] for traceability

2. **Phase 1.5:** Supervisory quality check (general-investigator)
   - Verify agents stayed in their lanes (no role drift)
   - Check completeness (all files covered, evidence present)
   - Detect contradictions between agents
   - Flag weak evidence or vague claims

3. **Phase 2:** Requirements & ripple effect analysis (3-4 parallel agents)
   - All outputs tagged for traceability

4. **Phase 3:** Verification round (N parallel agents)
   - Prove/disprove critical findings
   - Pass original agent reasoning for context
   - Each verifier gets full context of what original agent saw

5. **Phase 3.5:** Meta-verification (verify the verifiers)
   - Double-check FALSE_POSITIVE claims
   - Prevent overzealous verifiers from removing real issues
   - Restore findings if verifier was wrong

6. **Phase 4:** Second investigation pass (2-3 investigators with fresh perspective)
   - Different focus areas (edge cases, data flow, observability)

7. **Phase 4.5:** Deep investigation (unlimited time on "needs investigation")
   - Items flagged as suspicious get thorough analysis
   - Read related files, check git history, trace call chains

8. **Phase 5:** Contradiction resolution (tie-breaker investigators)
   - Resolve conflicting findings from different agents
   - Provide definitive verdict with evidence

9. **Phase 6:** Synthesis
   - Cross-validate, remove false positives, generate report

**Why multi-round with supervision?**
- Supervisor catches role drift before it propagates
- Verification round catches false positives
- Meta-verification catches overzealous verifiers
- Deep investigation ensures nothing suspicious is left unexamined
- Contradiction resolution prevents conflicting findings reaching user
- LLM tagging enables traceability and accountability
- Different agents/angles = no stone unturned

---

## Phase 0: Load Skills & Prepare

**MANDATORY FIRST STEP:**

```python
# Load agent-prompting skill BEFORE spawning any agents
Skill(command="agent-prompting")

# Review "Critical Inline Standards by Agent Type" section
# You MUST include inline standards in ALL agent prompts
```

**Why:** Sub-agents don't automatically know project standards (try/except rules, logging patterns, type hints, etc). Inline standards in prompts guarantee they're followed.

---

## Phase 1: Parse Input & Setup

### 1.1 Parse Input & Normalize Branch

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

### 1.2 Setup Worktrees

```bash
# Fetch latest
git fetch origin -q

# Find source branch
source_branch=$(git branch -r | grep "origin/$ticket" | grep -v "pre-styling" | head -1 | sed 's|origin/||')

# Validate branch exists
if [ -z "$source_branch" ]; then
    echo "❌ No branch found for $ticket"
    git branch -r | grep "$ticket" || echo "No similar branches"
    exit 1
fi

# Create worktrees in /tmp/pr-review-$ticket
~/.claude/scripts/git-worktree --base /tmp/pr-review-$ticket --main $target_branch base pr

# Checkout PR branch in pr worktree
cd /tmp/pr-review-$ticket/wt-pr && git checkout origin/$source_branch -b review-$ticket
```

---

## Phase 2: Context Gathering (Parallel)

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
git diff origin/$target_branch...origin/$source_branch  # Full diff

# 4. Categorize changed files
code_files = [f for f in changed_files if f.endswith('.py') and not f.startswith('test_')]
test_files = [f for f in changed_files if 'test_' in f or f.startswith('tests/')]
config_files = [f for f in changed_files if f.endswith(('.json', '.yaml', '.yml', '.toml', '.ini', '.env'))]
migration_files = [f for f in changed_files if 'migration' in f.lower() or 'schema' in f.lower() or f.endswith('.sql')]
```

### 2.1 Detect Review Context

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

---

## Phase 3: Round 1 - Specialized Review (Parallel)

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
    mr_comments=mr_comments or "No existing comments"
))

Task(security-auditor, sec_tmpl.format(
    worktree_path=worktree,
    changed_files='\n'.join(code_files + test_files),
    context=context_analysis  # Tells agent what kind of code this is
))

Task(performance-optimizer, perf_tmpl.format(
    worktree_path=worktree,
    changed_files='\n'.join(code_files + test_files),
    db_type=context_analysis['db_type']
))

Task(general-investigator, test_tmpl.format(
    worktree_path=worktree,
    code_files='\n'.join(code_files),
    test_files='\n'.join(test_files)
))
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

## Phase 1.5: Supervisory Quality Check

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

## Phase 4: Round 2 - Requirements & Ripple Effects (Parallel)

**After Round 1 completes, launch Round 2:**

```python
req_tmpl = read('~/.claude/templates/pr-review-requirements.md')
ripple_breaking_tmpl = read('~/.claude/templates/pr-review-ripple-breaking.md')
ripple_integration_tmpl = read('~/.claude/templates/pr-review-ripple-integration.md')
ripple_db_tmpl = read('~/.claude/templates/pr-review-ripple-db.md')

# Launch in parallel (single message, 3-4 Tasks)

# 1. Requirements verification (only if ticket fetched)
if ticket_content:
    Task(general-investigator, req_tmpl.format(
        worktree_path=worktree,
        ticket_content=ticket_content,
        changed_files='\n'.join(code_files + test_files)
    ))

# 2. Ripple effect analysis - breaking changes
Task(general-investigator, ripple_breaking_tmpl.format(
    worktree_path=worktree,
    changed_files='\n'.join(code_files)
))

# 3. Ripple effect analysis - integration points
Task(general-investigator, ripple_integration_tmpl.format(
    worktree_path=worktree,
    changed_files='\n'.join(code_files)
))

# 4. DB field usage compatibility (only if DB changes)
if migration_files or context_analysis['has_db_changes']:
    Task(general-investigator, ripple_db_tmpl.format(
        worktree_path=worktree,
        changed_files='\n'.join(code_files + migration_files)
    ))
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

## Phase 5: Round 3 - Verification Round (Parallel)

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
    ))
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

## Phase 3.5: Meta-Verification (Verify the Verifiers)

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

## Phase 6: Round 4 - Second Investigation Pass (Parallel)

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
""", max_tokens=100000)

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
""", max_tokens=100000)

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
""", max_tokens=100000)
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

## Phase 4.5: Deep Investigation (Needs Investigation Items)

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

## Phase 6.5: Contradiction Resolution

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

## Phase 7: Synthesis & Final Report

### 7.1 Cross-Validate All Findings

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

### 7.2 Add PEP 8 Style Check

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

### 7.3 Categorize by Severity

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

### 7.4 Generate Final Report

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

## 📊 Requirements Coverage

{If Jira ticket available}

**Requirement 1:** {description from ticket}
- ✅ Implemented in: file.py:line-range
- ✅ Tested in: test_file.py:line-range

**Requirement 2:** {description}
- ⚠️ Partially implemented - missing {specific gap}
- ❌ No tests for this requirement

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

{If DB changes present}

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

## 🎯 Addressed MR Comments

{If GitLab comments available}

**Comment 1** (by @reviewer, 2 days ago): "Missing validation for negative amounts"
- ✅ Resolved: Added validation at file.py:78

**Comment 2** (by @reviewer, 1 day ago): "Should we batch these DB calls?"
- ✅ Resolved: Batching added at file.py:123-145

**Comment 3** (by @security, 3 hours ago): "Potential SQL injection?"
- ✅ Addressed: False positive - parameterized query used (verified)

---

## 🎬 Final Recommendation

**Status:** {APPROVE ✅ | REQUEST CHANGES ❌ | NEEDS DISCUSSION 💬}

{For REQUEST CHANGES:}
**Must fix before merge:**
1. Critical issue #1 - {specific fix needed}
2. Critical issue #2 - {specific fix needed}
3. High priority #1 - {specific fix needed}

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
- Phase 1 (Specialized): 4 agents, {X} findings
- Phase 1.5 (Supervisor): Quality check passed/failed, {Y} issues flagged
- Phase 2 (Requirements/Ripple): 4 agents, {Z} findings
- Phase 3 (Verification): {N} verifiers, {W} false positives removed
- Phase 3.5 (Meta-Verification): {M} verifier claims checked, {P} findings restored
- Phase 4 (Second Pass): 3 agents, {Q} additional findings
- Phase 4.5 (Deep Investigation): {R} deep dives completed
- Phase 5 (Contradiction Resolution): {S} contradictions resolved

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

## Phase 8: Cleanup

```bash
# Always cleanup worktrees when done
~/.claude/scripts/git-worktree --cleanup

# Worktrees removed:
# - /tmp/pr-review-{ticket}/wt-base
# - /tmp/pr-review-{ticket}/wt-pr
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

```bash
# Use most recent, prefer non-pre-styling branches
branches=$(git branch -r | grep "origin/$ticket" | grep -v "pre-styling")
if [ $(echo "$branches" | wc -l) -gt 1 ]; then
    echo "⚠️  Multiple branches found for $ticket:"
    echo "$branches"
    echo ""
    echo "Using most recent: $source_branch"
fi
```

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
- [ ] LLM tagging implemented for all agent outputs ([AGENT: name] format)
- [ ] Phase 1 complete (4 specialized agents)
- [ ] Phase 1.5 complete (supervisory quality check)
- [ ] Phase 2 complete (3-4 requirements/ripple agents)
- [ ] Phase 3 complete (N verification agents with original agent reasoning)
- [ ] Phase 3.5 complete (meta-verification of FALSE_POSITIVE claims)
- [ ] Phase 4 complete (2-3 second-pass investigators)
- [ ] Phase 4.5 complete (deep investigations of needs_investigation items)
- [ ] Phase 5 complete (contradiction resolution)
- [ ] All file:line references verified in worktree
- [ ] False positives removed (verification round results)
- [ ] Duplicates removed (same file:line:issue)
- [ ] Contradictions flagged for manual review
- [ ] Findings categorized by severity (critical/high/medium/low/needs_verification)
- [ ] PEP 8 violations checked and added
- [ ] Context-aware security applied (internal vs external)
- [ ] DB schema compatibility verified (if applicable)
- [ ] Requirements coverage checked (if Jira available)
- [ ] MR comments addressed (if GitLab available)
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
