# Extending the Generic PR Review Workflow

This document shows how projects can extend the generic PR review workflow with project-specific agents and rules.

## Basic Usage (Generic Workflow)

```python
from pathlib import Path
from cc_orchestrations.workflows.pr_review import (
    create_pr_review_workflow,
    create_default_config,
)

# Use default generic configuration
ctx, handlers = create_pr_review_workflow(
    ticket_id='PROJ-123',
    source_branch='feature/my-feature',
    target_branch='develop',
    work_dir=Path('/path/to/repo'),
)

# Run phases
for phase_name, handler in handlers.items():
    result = handler()
    if not result.success:
        print(f"Phase {phase_name} failed: {result.error}")
        break
```

## Extension Pattern 1: Adding Project-Specific Agents

```python
from cc_orchestrations.workflows.pr_review import (
    PRReviewAgent,
    create_default_config,
)

# Create base config
config = create_default_config()

# Add project-specific agents
def _has_mongo_changes(context):
    """Trigger when MongoDB operations are present."""
    diff_files = context.get('diff_files', [])
    return any('mongo' in f.lower() for f in diff_files)

def _has_api_changes(context):
    """Trigger when API files are modified."""
    diff_files = context.get('diff_files', [])
    return any('api/' in f or 'fortress_api/' in f for f in diff_files)

project_agents = [
    PRReviewAgent(
        name='mongo-ops-reviewer',
        trigger=_has_mongo_changes,
        prompt_template="""Review MongoDB operations for correctness.

Files modified:
{diff_files}

Check:
1. subID filters on all businessObjects queries
2. retry_run() wrapping for operations
3. Proper error handling
4. Index usage

Report issues with MongoDB operations.""",
        model='opus',
        required=False,
        description='Review MongoDB operations',
    ),
    PRReviewAgent(
        name='api-security-reviewer',
        trigger=_has_api_changes,
        prompt_template="""Review API changes for security issues.

Files modified:
{diff_files}

Check:
1. Authentication required on all endpoints
2. Authorization checks for resource access
3. Input validation
4. No sensitive data exposure

Report security concerns.""",
        model='opus',
        required=False,
        description='Review API security',
    ),
]

# Add to config
config.agents.extend(project_agents)

# Now use this config when creating workflow
ctx, handlers = create_pr_review_workflow(
    ticket_id='PROJ-123',
    source_branch='feature/my-feature',
    target_branch='develop',
    work_dir=Path('/path/to/repo'),
    config=config,
)
```

## Extension Pattern 2: Custom Finding Classification

```python
from cc_orchestrations.workflows.pr_review import (
    FindingClassification,
    create_default_config,
)

class MyProjectClassification(FindingClassification):
    """Project-specific finding classification."""

    def __init__(self):
        super().__init__(
            severity_rules={
                'critical': [
                    'authentication bypass',
                    'SQL injection',
                    'data loss',
                ],
                'major': [
                    'missing validation',
                    'incorrect business logic',
                ],
            },
            false_positive_patterns=[
                'style issue',
                'formatting',
            ],
        )

    def classify_finding(self, finding):
        """Custom classification logic."""
        issue = finding.get('issue', '').lower()

        # Auto-upgrade security issues
        if any(word in issue for word in ['security', 'auth', 'permission']):
            finding['severity'] = 'critical'
            finding['classification_reason'] = 'Security issue auto-upgraded'

        # Auto-downgrade pre-existing issues
        if 'pre-existing' in issue:
            finding['severity'] = 'minor'
            finding['classification_reason'] = 'Pre-existing issue'

        return finding

# Apply to config
config = create_default_config()
config.finding_classification = MyProjectClassification()
```

## Extension Pattern 3: Custom Risk Configuration

```python
from cc_orchestrations.workflows.pr_review import (
    RiskLevel,
    create_default_config,
)

config = create_default_config()

# Customize risk thresholds
config.risk_config[RiskLevel.LOW] = {
    'required_agents': True,
    'conditional_agents': False,
    'validation_depth': 'basic',
    'second_round': False,
}

config.risk_config[RiskLevel.MEDIUM] = {
    'required_agents': True,
    'conditional_agents': True,
    'validation_depth': 'thorough',  # More thorough than default
    'second_round': True,
}

config.risk_config[RiskLevel.HIGH] = {
    'required_agents': True,
    'conditional_agents': True,
    'validation_depth': 'thorough',
    'second_round': True,
}
```

## Extension Pattern 4: Custom Extension Hooks

```python
from cc_orchestrations.workflows.pr_review import create_default_config

config = create_default_config()

def custom_pre_investigation_hook(ctx):
    """Run custom logic before investigation."""
    print(f"Starting investigation for {ctx.ticket_id}")
    # Add custom logging, notifications, etc.

def custom_post_validation_hook(ctx):
    """Run custom logic after validation."""
    print(f"Found {len(ctx.validated_findings)} validated findings")
    # Send notifications, update Jira, etc.

config.extension_hooks = {
    'pre_investigation': custom_pre_investigation_hook,
    'post_validation': custom_post_validation_hook,
}
```

## Complete Example: m32rimm-style Extension

```python
from pathlib import Path
from cc_orchestrations.workflows.pr_review import (
    PRReviewAgent,
    FindingClassification,
    create_default_config,
    create_pr_review_workflow,
)

# Create base config
config = create_default_config()

# Add m32rimm-specific agents
m32rimm_agents = [
    PRReviewAgent(
        name='schema-alignment-reviewer',
        trigger=lambda ctx: any('businessObject' in f for f in ctx.get('diff_files', [])),
        prompt_template="""Review schema alignment with Business Objects.

Files: {diff_files}

Check for proper field mappings, data types, and BO structure.""",
        model='opus',
        required=False,
    ),
    PRReviewAgent(
        name='test-plan-validator',
        trigger=lambda ctx: True,  # Always run
        prompt_template="""Validate Jira Test Plan completeness.

Ticket: {ticket_id}
Requirements: {requirements}

Check Test Plan exists and integration tests align.""",
        model='opus',
        required=True,
    ),
    # Add more m32rimm-specific agents...
]

config.agents.extend(m32rimm_agents)

# Custom finding classification
class M32RIMMClassification(FindingClassification):
    def classify_finding(self, finding):
        issue = finding.get('issue', '').lower()

        # m32rimm-specific patterns
        if 'subid' in issue or 'flush()' in issue:
            finding['severity'] = 'critical'
            finding['category'] = 'm32rimm_data_integrity'

        return finding

config.finding_classification = M32RIMMClassification()

# Create workflow
ctx, handlers = create_pr_review_workflow(
    ticket_id='M32R-123',
    source_branch='feature/M32R-123-my-feature',
    target_branch='develop',
    work_dir=Path('/home/user/repos/m32rimm'),
    config=config,
)

# Run workflow
for phase_name, handler in handlers.items():
    print(f"Running phase: {phase_name}")
    result = handler()
    if not result.success:
        print(f"Phase failed: {result.error}")
        break
```

## Key Extension Points

1. **Agents**: Add project-specific review agents with custom triggers
2. **Finding Classification**: Override classification logic for project patterns
3. **Risk Configuration**: Adjust thresholds and validation depth per risk level
4. **Extension Hooks**: Add custom logic at phase boundaries
5. **Report Template**: Customize report generation format

## Best Practices

1. **Keep Generic Base**: Don't modify the generic agents, extend them
2. **Specific Triggers**: Make conditional agents very specific to avoid false triggers
3. **Clear Prompts**: Agent prompts should be explicit about what to check
4. **Test Thoroughly**: Test agent triggers with different file patterns
5. **Document Extensions**: Document project-specific agents and their purpose
