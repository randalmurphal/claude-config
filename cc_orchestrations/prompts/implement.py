"""Prompts for the implement (ticket-to-PR) workflow.

These prompts are self-contained and don't depend on external files.
They use template variables that get filled in at runtime.

Template variables:
- {ticket_id}: Jira ticket ID
- {ticket_content}: Full ticket content from Jira
- {project_name}: Name of the project
- {project_context}: Project-specific context (from AGENTS.md or extensions)
- {work_dir}: Working directory path
- {assumptions_json}: JSON of assumptions already made
- {spec_content}: Generated spec content
- {findings_json}: JSON of PR review findings
"""

INVESTIGATION_PROMPT = """You are investigating a Jira ticket to understand what needs to be built.

## Ticket Information

**Ticket ID:** {ticket_id}

{ticket_content}

## Project Context

**Project:** {project_name}
**Working Directory:** {work_dir}

{project_context}

## Your Task

Investigate this ticket and the codebase to understand:

1. **Intent**: What problem is being solved? What's the expected outcome?
2. **Relevant Code**: Search the codebase for related files, patterns, existing implementations
3. **Blast Radius**: What files/systems will be affected? What could break?
4. **Patterns to Follow**: What existing patterns should this implementation follow?
5. **Assumptions**: Document ANY decisions you make due to ambiguity

## Assumption Classification

For EACH assumption you make, classify its severity:

- **CRITICAL**: Core functionality decisions (what the feature does, business logic)
- **MODERATE**: Implementation approach decisions (which pattern, which library)
- **MINOR**: Detail decisions (naming, file locations, formatting)

## Output Format

Return a JSON object:

```json
{{
    "understanding": "Clear description of what the ticket wants to achieve",
    "relevant_files": [
        {{"path": "path/to/file.py", "relevance": "why this file matters"}}
    ],
    "patterns_to_follow": [
        {{"pattern": "description", "example_file": "path/to/example.py"}}
    ],
    "blast_radius": {{
        "files_to_modify": ["list of files"],
        "files_affected": ["files that import/depend on modified files"],
        "risk_assessment": "low|medium|high|critical"
    }},
    "assumptions": [
        {{
            "topic": "What's ambiguous",
            "options": ["Option A", "Option B"],
            "chosen": "What I chose",
            "rationale": "Why I chose this",
            "level": "critical|moderate|minor",
            "risk_if_wrong": "What happens if this assumption is wrong"
        }}
    ],
    "blockers": [
        "Any issues that prevent proceeding (empty if none)"
    ],
    "proceed": true,
    "confidence": 0.85
}}
```

## Important

- If the ticket lacks critical information, add it to assumptions
- If you find blockers that make implementation impossible, set proceed=false
- Be thorough in finding relevant code - missing context leads to bad implementations
- Document ALL assumptions, even obvious ones

## Blocker Guidelines

**Blockers should be EMPTY unless there's a concrete, verifiable technical issue.**

What IS a blocker:
- Missing infrastructure (e.g., "requires database table that doesn't exist")
- Circular dependencies that can't be resolved
- Architecture changes outside the scope of this ticket
- Missing required APIs/endpoints that this depends on and can't be created

What is NOT a blocker:
- Broken or empty Jira links in ticket content (common formatting artifact)
- Ticket dependency references like "must be merged first" without a verifiable ticket ID
- Incomplete ticket descriptions (add to assumptions instead)
- Ambiguous requirements (add to assumptions instead)
- Potential dependencies mentioned but not confirmed

**Key principle:** If you can't VERIFY a dependency exists and is actually blocking, don't report it as a blocker. Ticket content often has broken links or stale references. When in doubt, proceed=true and document uncertainty in assumptions.
"""

SPEC_GENERATION_PROMPT = """You are creating an executable specification from investigation results.

## Ticket Information

**Ticket ID:** {ticket_id}

{ticket_content}

## Investigation Results

{investigation_json}

## Assumptions Made

{assumptions_json}

## Your Task

Create a complete SPEC.md that can drive automated implementation.

## Required Sections

### 1. Problem Statement
What problem are we solving? Be specific about the current pain point.

### 2. User Impact
Who is affected and how? What happens when this is fixed?

### 3. Mission
The unchanging goal - 1-2 sentences.

### 4. Success Criteria
Measurable outcomes that define "done":
- [ ] Criterion 1
- [ ] Criterion 2

### 5. Requirements (IMMUTABLE)
Hard requirements that cannot change:
- Requirement 1
- Requirement 2

### 6. Proposed Approach (EVOLVABLE)
High-level strategy that can adapt:

**Components:**
- Component A: [purpose]
- Component B: [purpose]

**Dependencies:**
- A depends on: [B, C]

### 7. Implementation Phases
Break into phases with tasks.

### 8. Known Gotchas
From investigation - prevents surprises:
- Gotcha 1
- Gotcha 2

### 9. Quality Requirements
- Tests: coverage requirements
- Security: specific requirements
- Performance: specific requirements

### 10. Files to Create/Modify

#### New Files
- path/to/file.py
  - Purpose: [description]
  - Depends on: [other files]
  - Complexity: Low|Medium|High

#### Modified Files
- path/to/existing.py
  - Changes: [description]
  - Risk: Low|Medium|High

## Output Format

Return JSON with:
```json
{{
    "spec_content": "Full SPEC.md content as markdown string",
    "manifest": {{
        "name": "{ticket_id}-spec",
        "ticket": "{ticket_id}",
        "project": "{project_name}",
        "complexity": 7,
        "risk_level": "medium",
        "components": [
            {{
                "id": "component_a",
                "file": "path/to/file.py",
                "purpose": "description",
                "depends_on": [],
                "complexity": "medium"
            }}
        ],
        "execution": {{
            "mode": "standard",
            "parallel_components": true,
            "reviewers": 2
        }},
        "gotchas": ["list of gotchas"]
    }}
}}
```
"""

PR_REVIEW_PROMPT = """You are reviewing a merge request for a Jira ticket.

## Ticket Information

**Ticket ID:** {ticket_id}

{ticket_content}

## Merge Request

**Branch:** {branch_name}
**Target:** {target_branch}
**Files Changed:** {files_changed}

## Diff Content

{diff_content}

## Project Context

{project_context}

## Your Task

Review this MR against:
1. **Ticket Requirements**: Does it fulfill what was asked?
2. **Code Quality**: Is the code clean, maintainable, well-documented?
3. **Security**: Any security concerns (injection, auth, data exposure)?
4. **Tests**: Are there adequate tests? Do they test the right things?
5. **Patterns**: Does it follow project patterns and conventions?

## Output Format

Return JSON:
```json
{{
    "summary": "Overall assessment in 2-3 sentences",
    "requirements_met": true,
    "findings": [
        {{
            "severity": "critical|high|medium|low",
            "category": "security|quality|requirements|tests|patterns",
            "file": "path/to/file.py",
            "line": 42,
            "issue": "Clear description of the issue",
            "suggestion": "How to fix it",
            "code_snippet": "relevant code if helpful"
        }}
    ],
    "missing_requirements": [
        "Any requirements from ticket not addressed"
    ],
    "positive_notes": [
        "Things done well"
    ]
}}
```

## Severity Guidelines

- **CRITICAL**: Security vulnerabilities, data loss risk, broken functionality
- **HIGH**: Major bugs, significant performance issues, missing core requirements
- **MEDIUM**: Code quality issues, missing edge cases, incomplete tests
- **LOW**: Style issues, minor improvements, nice-to-haves
"""

FINDING_FIXER_PROMPT = """You are addressing PR review findings.

## Findings to Address

{findings_json}

## Working Directory

{work_dir}

## Your Task

For each finding:
1. Understand the issue
2. Make the necessary code changes
3. Verify the fix doesn't break anything else

## Guidelines

- Fix the actual issue, not just the symptom
- If a fix requires significant changes, note it but still attempt
- Run tests if possible to verify fixes
- Commit each logical fix separately for reviewability

## Output Format

After making fixes, return JSON:
```json
{{
    "fixed": [0, 1, 3],
    "unfixed": [
        {{
            "index": 2,
            "reason": "Why this couldn't be fixed automatically"
        }}
    ],
    "new_issues": [
        {{
            "severity": "medium",
            "category": "quality",
            "file": "path/to/file.py",
            "issue": "New issue discovered while fixing",
            "suggestion": "How to address"
        }}
    ],
    "commits": [
        "abc123: Fix security issue in auth handler",
        "def456: Add missing input validation"
    ]
}}
```

## Important

- Don't make unnecessary changes beyond what's needed to fix findings
- If unsure about a fix, mark as unfixed with clear reason
- Note any new issues discovered during fixing
"""
