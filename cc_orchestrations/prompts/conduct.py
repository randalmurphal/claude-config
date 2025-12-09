"""Prompts for the conduct (implementation orchestration) workflow.

These prompts drive the skeleton → implementation → validation loop.

With workspace enabled, context is injected via the Workspace system:
- Minimal context is injected automatically (see core/workspace.py)
- Additional context is available via Read tool from .workspace/

Template variables:
- {component}: Component file path
- {purpose}: Component purpose from spec
- {depends_on}: List of dependencies
- {completed_deps}: Dependencies that are already implemented
- {work_dir}: Working directory
- {existing_code}: Current file contents (for modifications)
- {issues_json}: JSON of validation issues to fix

Legacy variables (used when workspace is disabled):
- {spec_content}: Full spec content
- {project_context}: Project-specific context
"""

SKELETON_BUILDER_PROMPT = """You are creating a code skeleton for a component.

## Component Information

**File:** {component}
**Purpose:** {purpose}
**Dependencies:** {depends_on}
**Completed Dependencies:** {completed_deps}

## Your Task

Create a skeleton for this component with:
1. All class/function signatures defined
2. Type hints on all parameters and returns
3. Docstrings explaining purpose
4. `raise NotImplementedError()` in all function bodies
5. Import statements for dependencies

## Guidelines

- Follow project patterns visible in completed dependencies
- Don't implement any logic - just structure
- Include all methods needed to fulfill the spec
- Add TODO comments for complex logic that will need attention
- If you need more context, read files from `.workspace/spec/`

## Output Format

Create the file at {component} with the skeleton.

Then return JSON:
```json
{{
    "status": "complete",
    "file_created": "{component}",
    "classes": ["ClassName1", "ClassName2"],
    "functions": ["func1", "func2"],
    "imports": ["from x import y"],
    "notes": ["Any important notes for implementer"]
}}
```

If blocked (missing dependencies, unclear requirements), return:
```json
{{
    "status": "blocked",
    "blockers": ["What's blocking progress"],
    "questions": ["Questions that need answers"]
}}
```
"""

IMPLEMENTATION_PROMPT = """You are implementing a component from its skeleton.

## Component Information

**File:** {component}
**Purpose:** {purpose}
**Dependencies:** {depends_on}

## Current Skeleton

```python
{existing_code}
```

## Completed Dependencies

These files are already implemented and you can reference them:
{completed_deps}

## Your Task

Replace all `raise NotImplementedError()` with actual implementations.

## Guidelines

1. **Follow the spec exactly** - don't add features not requested
2. **Use existing patterns** - look at completed dependencies for style
3. **Handle errors properly** - don't catch and ignore exceptions
4. **Add logging** - use standard logging module
5. **Write testable code** - pure functions where possible
6. If you need more context, read files from `.workspace/spec/`

## Output Format

Update the file at {component} with full implementation.

Then return JSON:
```json
{{
    "status": "complete",
    "file_updated": "{component}",
    "methods_implemented": ["method1", "method2"],
    "discoveries": [
        "Any important findings during implementation"
    ],
    "concerns": [
        "Any concerns about the implementation"
    ]
}}
```

If blocked:
```json
{{
    "status": "blocked",
    "blockers": ["What's blocking"],
    "partial_progress": "What was accomplished before blocking"
}}
```
"""

VALIDATION_PROMPT = """You are validating an implemented component.

## Component Information

**File:** {component}
**Purpose:** {purpose}

## Current Implementation

```python
{existing_code}
```

## Your Task

Review this implementation for:

1. **Correctness**: Does it do what the spec says?
2. **Completeness**: Are all requirements met?
3. **Quality**: Is the code clean and maintainable?
4. **Security**: Any vulnerabilities?
5. **Performance**: Any obvious inefficiencies?
6. **Tests**: Are there tests? Do they cover important cases?

If you need the full requirements, read `.workspace/spec/requirements.md`.

## Output Format

Return JSON:
```json
{{
    "passed": true,
    "issues": [],
    "notes": ["Positive observations"]
}}
```

Or if issues found:
```json
{{
    "passed": false,
    "issues": [
        {{
            "severity": "critical|high|medium|low",
            "category": "correctness|completeness|quality|security|performance|tests",
            "location": "line number or method name",
            "description": "What's wrong",
            "suggestion": "How to fix"
        }}
    ],
    "blocking_issues": 2,
    "total_issues": 5
}}
```

## Severity Guidelines

- **CRITICAL**: Won't work, security hole, data loss risk
- **HIGH**: Major bugs, missing core functionality
- **MEDIUM**: Code quality, edge cases, incomplete
- **LOW**: Style, minor improvements

Only CRITICAL and HIGH issues block completion.
"""

FIX_PROMPT = """You are fixing validation issues in a component.

## Component Information

**File:** {component}

## Current Implementation

```python
{existing_code}
```

## Issues to Fix

{issues_json}

## Your Task

Fix each issue while:
1. Not introducing new bugs
2. Not changing unrelated code
3. Maintaining code style

## Output Format

Update the file with fixes.

Then return JSON:
```json
{{
    "fixed": [0, 1, 2],
    "unfixed": [
        {{"index": 3, "reason": "Requires architectural change"}}
    ],
    "changes_made": [
        "Added null check on line 42",
        "Fixed SQL injection in query builder"
    ]
}}
```
"""
