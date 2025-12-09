---
name: code-review-patterns
description: Code review workflow and collaboration patterns including review contexts (architecture, detailed, quick, mentor), feedback tone guidelines, handling reviewer-author disagreements, and GitLab/GitHub integration. Use for review PROCESS and collaboration. For technical standards, see python-style and testing-standards skills.
allowed-tools:
  - Read
  - Grep
  - Glob
---

# Code Review Patterns

**Purpose:** Guide to effective code reviews with emphasis on constructive feedback, evidence-based findings, and collaborative improvement.

**When to use:** Reviewing pull requests, providing code feedback, responding to review comments, setting up review workflows, or training reviewers.

**For extended examples and detailed workflows:** See [reference.md](./reference.md)

---

## Core Principles

1. **Collaboration over criticism** - Reviews improve code AND build team knowledge
2. **Evidence-based findings** - Concrete examples, not vague suggestions
3. **Actionable feedback** - Specific fixes, not "make it better"
4. **Context matters** - Consider project stage, urgency, team experience
5. **Automate the boring** - Linting/tests run first, humans review substance
6. **Kind and specific** - Respectful tone, clear reasoning

---

## Review Contexts (Choose Your Approach)

| Context | Focus | Depth | Automation |
|---------|-------|-------|------------|
| **Architecture Review** | Design patterns, scalability, maintainability | High-level structure | Manual |
| **Detailed Code Review** | Logic, edge cases, performance, security | Line-by-line | Hybrid (auto checks + manual) |
| **Quick Review** | Critical bugs, breaking changes only | Targeted | Mostly automated |
| **Mentor Review** | Teaching opportunity, explain reasoning | Deep + educational | Manual with explanations |
| **Pre-merge Check** | Tests pass, no conflicts, standards met | Checklist verification | Fully automated |

**Choose based on:** PR size, risk level, author experience, project phase

---

## Review Workflow Pattern

### Phase 1: Automated Checks (Before Human Review)

```bash
ruff format --check .      # Code formatting
ruff check .               # Linting
pyright .                  # Type checking
pytest tests/ --cov=src    # Tests + coverage
bandit -r src/             # Security scanning
```

**Why first:** Machines catch style issues, humans review substance.

**Integration:** See gitlab-scripts skill for CI/CD patterns.

---

### Phase 2: Human Review Checklist

#### Step 1: Context Understanding (5 min)
- [ ] Read PR description and linked tickets
- [ ] Understand WHAT and WHY
- [ ] Check scope matches description

**Integration:** Use `gitlab-mr-comments` to fetch existing discussions.

#### Step 2: High-Level Review (10 min)
- [ ] Architecture makes sense
- [ ] Changes focused, no scope creep
- [ ] Backward compatibility maintained
- [ ] Dependencies justified

**Integration:** Use code-refactoring skill for complexity checks.

#### Step 3: Detailed Code Review (20-40 min)

**Functionality:**
- [ ] Logic correct (happy path + edge cases)
- [ ] Error handling appropriate
- [ ] No obvious bugs

**Security:**
- [ ] Input validation for external data
- [ ] No secrets in code/logs
- [ ] Auth/authz correct

**Performance:**
- [ ] No N+1 queries
- [ ] Caching appropriate
- [ ] Algorithm complexity reasonable

**Integration:** Use vulnerability-triage for security, python-style for code standards.

#### Step 4: Tests Review (10 min)
- [ ] Tests exist for new code
- [ ] Edge cases covered
- [ ] Coverage ≥95%

**Integration:** See testing-standards skill.

#### Step 5: Documentation (5 min)
- [ ] Public APIs documented
- [ ] Non-obvious logic explained
- [ ] README updated if needed

---

## Providing Constructive Feedback

### The Formula

```
OBSERVATION + EVIDENCE + IMPACT + SUGGESTION = Actionable Review
```

### Feedback Template

```markdown
**File:** path/to/file.py:LINE
**Issue:** [Specific problem]

**Evidence:**
[Code snippet showing issue]

**Impact:** [What breaks/degrades]

**Fix:**
[Exact code change]

**Severity:** [Critical/High/Medium/Low]
```

### Example: Security Issue

```markdown
**File:** src/api/auth.py:45
**Issue:** SQL injection vulnerability

**Evidence:**
```python
query = f"SELECT * FROM users WHERE id={user_id}"
```

**Impact:** Attacker can inject `user_id="1 OR 1=1"` to access all users

**Fix:**
```python
query = "SELECT * FROM users WHERE id=?"
cursor.execute(query, (user_id,))
```

**Severity:** Critical - Exploitable vulnerability
```

**For more examples:** See reference.md (logic bugs, performance, tests)

---

## Feedback Tone Guidelines

### Positive Framing

| Instead of | Use |
|------------|-----|
| "This is wrong" | "Consider this alternative" |
| "You forgot error handling" | "What happens if the API fails?" |
| "This won't work" | "This might have an issue when X happens" |

### Acknowledge Good Work

```
✅ Great extraction of validation logic - much easier to test
✅ Nice use of caching - will significantly improve performance
✅ Good error messages with context - debugging will be easier
```

### Ask Questions (Teaching)

```
💭 What's the reasoning for using list instead of set?
💭 Have we considered timeout scenarios?
💭 Could you explain the tradeoff here?
```

---

## Handling Review Comments (As Author)

### Decision Framework

| Comment Type | When to Accept | When to Push Back |
|--------------|----------------|-------------------|
| **Bugs** | Always | Never |
| **Security** | Always | If false positive with proof |
| **Standards** | Project standards | If standard outdated |
| **Style preferences** | If improves clarity | If subjective |
| **Scope creep** | If critical | If can be follow-up PR |

### Response Patterns

**Accepting:**
```
✅ Fixed in commit abc123. Changed to parameterized query.
Good catch - missed the None edge case.
```

**Pushing back:**
```
💭 I considered that but opted for X because Y.
Evidence: [proof]
Open to discussion if I'm missing something.
```

**Deferring:**
```
📌 Created follow-up ticket JIRA-1234.
Keeping current PR focused on original scope.
```

---

## Code Smells Checklist

### Critical Issues

| Pattern | Evidence | Severity |
|---------|----------|----------|
| **SQL Injection** | `f"SELECT * WHERE id={input}"` | Critical |
| **Auth Bypass** | Missing auth check on endpoint | Critical |
| **Secrets in Code** | Hardcoded API keys/passwords | Critical |
| **Uncaught Exceptions** | Broad try/except hiding errors | High |

### Quality Issues

| Pattern | Evidence | Severity |
|---------|----------|----------|
| **God Function** | 100+ lines, multiple responsibilities | Medium |
| **Magic Numbers** | `if count > 42:` (no explanation) | Low |
| **Commented Code** | Code in comments (use git) | Low |

### Performance Issues

| Pattern | Detection | Calculation |
|---------|-----------|-------------|
| **N+1 Queries** | DB query in loop | N items × 1 query |
| **Removed Caching** | Deleted `@lru_cache` | 1 calc → N calcs |
| **Algorithm Regression** | `O(n)` → `O(n²)` | 1000 items = 1M ops |

**For detailed patterns:** See code-refactoring skill.

---

## Review Severity Guidelines

| Severity | Examples | Action |
|----------|----------|--------|
| **Critical** | SQL injection, auth bypass, data corruption | MUST fix |
| **High** | Logic bugs, untested critical functions | SHOULD fix |
| **Medium** | Code quality, missing edge cases | Discuss |
| **Low** | Style preferences, optimizations | Optional |
| **Uncertain** | Can't confirm without context | Flag for discussion |

**Integration:** See vulnerability-triage for security severity, python-style for code quality.

---

## Automated Checks Integration

### CI Pipeline Pattern

```yaml
# .gitlab-ci.yml
code-quality:
  script:
    - ruff format --check .
    - ruff check .
    - pyright .

tests:
  script:
    - pytest tests/ --cov=src --cov-fail-under=95

security:
  script:
    - bandit -r src/
    - safety check
```

### GitLab MR Integration

```bash
# Fetch existing comments
gitlab-mr-comments INT-3877
```

**Use in review:** Build on existing discussions, avoid duplication.

**Integration:** See gitlab-scripts skill for complete workflow.

---

## Review Size Guidelines

| Lines Changed | Review Time | Approach |
|---------------|-------------|----------|
| **1-50** | 10-15 min | Quick focused review |
| **50-200** | 30-45 min | Detailed review |
| **200-500** | 1-2 hours | Break into chunks |
| **500+** | 2+ hours | Request split |

**Large PR strategy:** Review architectural overview, then chunks, focus on high-risk areas first.

---

## Common Pitfalls (Avoid These)

### Reviewer Pitfalls
❌ Nitpicking style (linter's job)
❌ Vague feedback ("Make better")
❌ Blocking on preferences
❌ Ignoring context (prototype ≠ production)
❌ No positive feedback

### Author Pitfalls
❌ Defensive responses
❌ Ignoring feedback
❌ Massive PRs
❌ No context in description
❌ Breaking CI before review

---

## Quick Reference Templates

### Bug Finding

```markdown
**File:** src/module/file.py:LINE
**Issue:** [Problem]
**Evidence:** [Code snippet]
**Impact:** [What breaks]
**Fix:** [Exact change]
**Severity:** [Level]
```

### Question

```markdown
💭 **Question:** src/module/file.py:LINE
[Specific question about approach/tradeoff]
**Context:** [Why asking]
```

### Positive Feedback

```markdown
✅ **Great pattern:** src/module/file.py:LINE
[What they did well and why]
[Optional: Suggest applying elsewhere]
```

---

## Integration with Other Skills

| Skill | Use For | Example |
|-------|---------|---------|
| **gitlab-scripts** | Fetch MR data | `gitlab-mr-comments <ticket>` |
| **code-refactoring** | Complexity checks | Flag functions >50 statements |
| **vulnerability-triage** | Security assessment | Use CVSS scoring |
| **python-style** | Code standards | try/except rules, logging patterns |
| **testing-standards** | Coverage requirements | 95%+ unit, 1:1 file mapping |

---

## Review Anti-Patterns Matrix

| Anti-Pattern | Example | Better Approach |
|--------------|---------|-----------------|
| **No evidence** | "This is bad" | Show code snippet |
| **Vague** | "Optimize this" | "N+1 query - use batch (see code)" |
| **Style blocking** | Block on 81-char line | Configure linter |
| **Theoretical** | "Could maybe fail if..." | Only flag actual issues |
| **Scope creep** | "Also add feature X" | Separate PR |

---

## Summary

### Review Phases

1. **Automated** - Linting, tests, security (CI/CD)
2. **Context** - Read description, tickets, existing comments
3. **High-level** - Architecture, scope, breaking changes
4. **Detailed** - Functionality, security, performance, tests
5. **Documentation** - Comments, README, migration guides

### The Golden Rules

1. **Be kind and specific** - Respectful, concrete examples
2. **Evidence-based** - Show code, don't just claim
3. **Actionable** - Exact fixes, not vague
4. **Context-aware** - Prototype ≠ production
5. **Automate boring** - Linters catch style
6. **Acknowledge good** - Positive reinforcement

### The Test

**Can author act on feedback immediately?** If not, be more specific.

**Would you want this feedback?** If not, reframe it.

**Remember:** Reviews improve code AND build team knowledge. Collaboration over criticism.

---

**For detailed examples, workflows, and troubleshooting:** See [reference.md](./reference.md)

**Related skills:**
- python-style (code quality standards)
- testing-standards (coverage requirements)
- vulnerability-triage (security assessment)
- code-refactoring (complexity patterns)
- agent-prompting (spawning review agents)
