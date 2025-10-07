# Agent Response Templates

## Implementation Agents

**skeleton-builder, implementation-executor:**
```markdown
## Status
COMPLETE | BLOCKED

## Files Created/Modified
- path/to/file.py: [brief description or line count]

## Gotchas Found
[List of issues discovered, or "None"]

## Blockers
[List of blockers, or "None"]

## Next
[What should happen next]
```

**test-implementer:**
```markdown
## Status
COMPLETE | BLOCKED

## Tests Implemented
- path/to/test_file.py: [X tests, Y assertions]

## Coverage
[X% if measurable, or "Not yet measured"]

## Gotchas Found
[Issues discovered during testing, or "None"]

## Blockers
[List of blockers, or "None"]

## Next
[Run tests to check for bugs]
```

---

## Review Agents (JSON Format)

**security-auditor, performance-optimizer, code-reviewer, code-beautifier, documentation-reviewer:**

```json
{
  "status": "COMPLETE",
  "critical": [
    {
      "file": "path/to/file.py",
      "line": 123,
      "issue": "Description of critical issue",
      "fix": "Suggested fix or mitigation"
    }
  ],
  "important": [
    {
      "file": "path/to/file.py",
      "line": 456,
      "issue": "Description of important issue",
      "fix": "Suggested fix"
    }
  ],
  "minor": [
    {
      "file": "path/to/file.py",
      "line": 789,
      "issue": "Description of minor issue",
      "fix": "Suggested improvement"
    }
  ]
}
```

**Note:** All review agents MUST return valid JSON. No prose, no markdown, just JSON.

---

## Fix Agents

**fix-executor:**
```markdown
## Status
COMPLETE | BLOCKED

## Fixes Applied
- path/to/file.py:45 - [what was fixed]
- path/to/file.py:67 - [what was fixed]

## Remaining Issues
[List of issues not fixed, or "None"]

## Blockers
[Why couldn't fix everything, or "None"]

## Next
[Re-run validation]
```

---

## Analysis Agents

**investigator:**
```markdown
## Topic
[What was investigated]

## Findings
- [Key finding 1]
- [Key finding 2]
- [Key finding 3]

## Relevant Code
- path/to/file.py:123-145 - [what it does]

## Recommendations
[What should be done based on findings]

## Next
[Suggested next steps]
```

**merge-coordinator:**
```markdown
## Status
COMPLETE | BLOCKED

## Files Merged
- path/to/file.py: [source variant, strategy used]

## Conflicts Resolved
- [Description of conflict and resolution]
- [Description of conflict and resolution]

## Validation Required
YES | NO

## Next
[Re-run tests and validation if YES]
```

---

## Spawning Agents with Templates

**How to embed template in agent prompt:**

```
Task(agent-name, """
[Task description and context]

RESPONSE TEMPLATE (use EXACTLY):
[paste template from above]

Do not add prose or explanations outside this template.
""")
```

**Example:**

```
Task(implementation-executor, """
Implement password reset service.

Context:
- Must use SendGrid for email
- Tokens expire in 1 hour
- Rate limit: 3 requests per hour

RESPONSE TEMPLATE (use EXACTLY):
## Status
COMPLETE | BLOCKED

## Files Created/Modified
- [list]

## Gotchas Found
- [list or "None"]

## Blockers
- [list or "None"]

## Next
[action]
""")
```
