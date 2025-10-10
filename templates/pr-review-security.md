---
template: pr-review-security
description: Security audit task for PR review agents
---

Security audit of PR changes in worktree.

WORKTREE PATH: {worktree_path}

CHANGED FILES:
{changed_files}

SCAN FOR:
1. Hardcoded secrets (passwords, API keys, tokens, connection strings)
2. SQL/NoSQL injection (user input in queries)
3. Auth/authz bypasses or weaknesses
4. Input validation gaps (missing sanitization, type checking)
5. Sensitive data exposure (PII in logs, errors, responses)
6. Cryptography issues (weak algorithms, hardcoded keys)
7. Insecure deserialization

REVIEW METHOD:
- Read each changed file completely
- Trace user input through code
- Check all DB queries for parameterization
- Review all logging for sensitive data

REPORT FORMAT:
## Critical Security Issues (fix immediately)
- file.py:line - Vulnerability, exploitation scenario, fix

## Security Concerns (should fix)
- file.py:line - Risk description, mitigation

REQUIREMENTS:
- ONLY report actual security issues
- NO theoretical "could be" suggestions
- Provide exploitation scenarios
