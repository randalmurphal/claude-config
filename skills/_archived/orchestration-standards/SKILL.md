---
name: orchestration-standards
description: Risk-based quality scaling, review configuration, voting gates, and failure handling for multi-agent workflows. Load for /conduct, /spec, /pr_review, or any orchestrated work requiring scaled validation.
---

# Orchestration Standards

## Risk Assessment

Assess BEFORE choosing review depth:

| Factor | Low (1) | Medium (2) | High (3) |
|--------|---------|------------|----------|
| **Files** | 1-3 | 4-10 | 10+ |
| **API exposure** | Internal only | Service-to-service | Public/external |
| **Data ops** | Read-only | Create/update | Delete/financial |
| **Auth/security** | None | Uses existing | Implements new |
| **Breaking changes** | None | Backward compat | Breaking |

**Risk Score** = Sum of factors (5-15)

---

## Review Configuration

| Risk Score | Per-Task | Full Validation | Voting |
|------------|----------|-----------------|--------|
| 5-7 (Low) | 1 reviewer | 2 reviewers | Skip |
| 8-10 (Medium) | 2 reviewers | 4 reviewers | On failures |
| 11-13 (High) | 2 + verification | 6 reviewers | All gates |
| 14-15 (Critical) | Full suite | 6 + synthesis | All + human |

### Reviewer Focus Assignment

| Reviewer | Focus |
|----------|-------|
| code-reviewer-1 | Logic, complexity, error handling |
| code-reviewer-2 | Edge cases, coupling, types |
| code-reviewer-3 | Docs, naming, maintainability |
| security-auditor | Injection, auth, data exposure |
| performance-optimizer | N+1, algorithms, caching |

---

## Voting Gates

### When to Vote

| Gate | Trigger | Threshold |
|------|---------|-----------|
| Architecture | Multiple valid approaches | 2/3 or escalate |
| Fix Strategy | Same issue after 2 attempts | 2/3 or escalate |
| Production Readiness | High-risk validation passes | 2/3 or escalate |

### Skip Voting When

- Single obvious approach
- Low-risk changes
- Making progress (different issues each attempt)

### Consensus Handling

- 2/3+ agree → Proceed
- Split → Present options to user, never proceed without decision

---

## Failure Handling

### Pattern Detection

| Pattern | Meaning | Action |
|---------|---------|--------|
| Same issue | Approach wrong | Vote or escalate |
| Different issues | Making progress | Continue |
| Cascading issues | Fix broke things | Step back |

### Escalation Triggers

- 3 attempts with same issue pattern
- No voting consensus
- Scope larger than expected
- Security concern with no clear fix

### Escalation Format

```
BLOCKED: [What]

Issue: [Specific problem]
Attempts: [What was tried]
Pattern: [Same/different/cascading]
Options: [A, B, C with trade-offs]
Recommendation: [Your suggestion]
Need: [Specific decision required]
```

---

## Review Output Format

```json
{
  "status": "COMPLETE",
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "file": "path/to/file.py",
      "line": 123,
      "issue": "Description",
      "evidence": "Proof",
      "fix": "Resolution"
    }
  ],
  "summary": "2-3 sentences"
}
```

---

**For model selection:** See CLAUDE.md
**For agent prompting:** Load `agent-prompting` skill
**For tools:** See CLAUDE.md Scripts section
