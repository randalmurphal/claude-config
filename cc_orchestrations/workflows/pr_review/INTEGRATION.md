# Integration Guide

How to integrate the generic PR review workflow with existing orchestration infrastructure.

## Integration with cc_orchestrations

The PR review workflow is designed to work with the `cc_orchestrations` framework but can also run standalone.

### Option 1: Standalone Execution

Run phases directly without the full workflow engine:

```python
from pathlib import Path
from cc_orchestrations.core.runner import AgentRunner
from cc_orchestrations.workflows.pr_review import (
    create_pr_review_workflow,
    create_default_config,
)

# Setup
runner = AgentRunner(
    claude_path='claude',
    default_model='opus',
)

ctx, handlers = create_pr_review_workflow(
    ticket_id='PROJ-123',
    source_branch='feature/my-feature',
    target_branch='develop',
    work_dir=Path('/path/to/repo'),
    runner=runner,
)

# Run phases sequentially
for phase_name, handler in handlers.items():
    print(f"Running phase: {phase_name}")
    result = handler()

    if not result.success:
        print(f"Phase {phase_name} failed: {result.error}")
        if result.needs_user_input:
            print(f"User input needed: {result.user_prompt}")
        break

    print(f"Phase {phase_name} completed successfully")

# Access results
print(f"\nFindings: {len(ctx.validated_findings)}")
print(f"Report: {ctx.work_dir / f'pr_review_{ctx.ticket_id}.md'}")
```

### Option 2: WorkflowEngine Integration

Integrate with the full workflow engine for advanced features (state management, resumption, etc.):

```python
from pathlib import Path
from cc_orchestrations.core import Config, PhaseConfig
from cc_orchestrations.workflow import WorkflowEngine
from cc_orchestrations.workflows.pr_review import (
    create_pr_review_workflow,
    create_default_config,
    phase_triage,
    phase_investigation,
    phase_validation,
    phase_synthesis,
    phase_report,
)

# Create PR review context
pr_config = create_default_config()
pr_ctx, _ = create_pr_review_workflow(
    ticket_id='PROJ-123',
    source_branch='feature/my-feature',
    target_branch='develop',
    work_dir=Path('/path/to/repo'),
    config=pr_config,
)

# Create workflow config
workflow_config = Config(
    name='pr_review',
    version='1.0.0',
    phases=[
        PhaseConfig(name='triage', description='Setup and risk assessment'),
        PhaseConfig(name='investigation', description='Run reviewers', parallel=True),
        PhaseConfig(name='validation', description='Validate findings', parallel=True),
        PhaseConfig(name='synthesis', description='Consolidate findings'),
        PhaseConfig(name='report', description='Generate report'),
    ],
)

# Create engine
engine = WorkflowEngine(
    config=workflow_config,
    work_dir=Path('/path/to/repo'),
    handlers={
        'triage': lambda ctx: phase_triage(pr_ctx),
        'investigation': lambda ctx: phase_investigation(pr_ctx),
        'validation': lambda ctx: phase_validation(pr_ctx),
        'synthesis': lambda ctx: phase_synthesis(pr_ctx),
        'report': lambda ctx: phase_report(pr_ctx),
    },
)

# Run workflow
result = engine.run()
print(f"Workflow completed: {result.success}")
```

### Option 3: Slash Command Integration

Create a slash command for PR review:

```markdown
---
name: pr_review
description: Generic PR review workflow
---

# PR Review

Run a risk-scaled PR review on a pull request.

Usage: `/pr_review <ticket> [<target_branch>]`

Default target branch: `develop`

This command:
1. Sets up a worktree for the PR
2. Assesses risk and determines review depth
3. Runs appropriate reviewers in parallel
4. Validates findings with consensus
5. Generates a comprehensive report

Example:
```
/pr_review PROJ-123
/pr_review PROJ-456 main
```

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
from cc_orchestrations.core.runner import AgentRunner
from cc_orchestrations.workflows.pr_review import (
    create_pr_review_workflow,
    create_default_config,
)

# Parse args
if len(sys.argv) < 2:
    print("Usage: /pr_review <ticket> [<target_branch>]")
    sys.exit(1)

ticket_id = sys.argv[1]
target_branch = sys.argv[2] if len(sys.argv) > 2 else 'develop'

# Determine source branch from ticket
import subprocess
result = subprocess.run(
    ['git', 'branch', '-r', '--list', f'*{ticket_id}*'],
    capture_output=True,
    text=True,
)
source_branches = [b.strip().replace('origin/', '') for b in result.stdout.split('\n') if b.strip()]

if not source_branches:
    print(f"No branch found for ticket {ticket_id}")
    sys.exit(1)

source_branch = source_branches[0]
print(f"Reviewing {source_branch} → {target_branch}")

# Run workflow
runner = AgentRunner(claude_path='claude', default_model='opus')
ctx, handlers = create_pr_review_workflow(
    ticket_id=ticket_id,
    source_branch=source_branch,
    target_branch=target_branch,
    work_dir=Path.cwd(),
    runner=runner,
)

for phase_name, handler in handlers.items():
    result = handler()
    if not result.success:
        print(f"Phase {phase_name} failed: {result.error}")
        sys.exit(1)

print(f"\nReview complete! Report: pr_review_{ticket_id}.md")
```

## Project-Specific Integration

### m32rimm Example

```python
# m32rimm/.claude/pr_review_config.py

from cc_orchestrations.workflows.pr_review import (
    PRReviewAgent,
    create_default_config,
)

def create_m32rimm_config():
    """Create m32rimm-specific PR review config."""
    config = create_default_config()

    # Add m32rimm-specific agents
    m32rimm_agents = [
        PRReviewAgent(
            name='schema-alignment-reviewer',
            trigger=lambda ctx: any('businessObject' in f for f in ctx.get('diff_files', [])),
            prompt_template="""Review BO schema alignment.

Files: {diff_files}

Check:
1. Field mappings correct
2. Data types match schema
3. BO structure follows patterns

Report schema mismatches.""",
            model='opus',
            required=False,
        ),
        PRReviewAgent(
            name='mongo-ops-reviewer',
            trigger=lambda ctx: any('mongo' in f.lower() for f in ctx.get('diff_files', [])),
            prompt_template="""Review MongoDB operations.

Files: {diff_files}

Check:
1. subID filters on businessObjects queries
2. flush() before mark_for_aggregation()
3. retry_run() wrapping
4. Proper error handling

Report MongoDB issues.""",
            model='opus',
            required=False,
        ),
        PRReviewAgent(
            name='test-plan-validator',
            trigger=lambda ctx: True,
            prompt_template="""Validate Jira Test Plan.

Ticket: {ticket_id}
Requirements: {requirements}

Check:
1. Test Plan exists in Jira
2. Integration tests updated
3. Tests cover new functionality

Report test plan issues.""",
            model='opus',
            required=True,
        ),
    ]

    config.agents.extend(m32rimm_agents)
    return config
```

Then use it:

```python
# m32rimm/.claude/commands/pr_review.md

from pathlib import Path
from cc_orchestrations.workflows.pr_review import create_pr_review_workflow
from .pr_review_config import create_m32rimm_config

config = create_m32rimm_config()
ctx, handlers = create_pr_review_workflow(
    ticket_id='M32R-123',
    source_branch='feature/M32R-123',
    target_branch='develop',
    work_dir=Path.cwd(),
    config=config,
)

for phase_name, handler in handlers.items():
    result = handler()
    if not result.success:
        print(f"Failed: {result.error}")
        break
```

## CLI Integration

Create a CLI command for PR review:

```bash
# scripts/pr-review
#!/usr/bin/env bash

set -e

TICKET="$1"
TARGET="${2:-develop}"

if [[ -z "$TICKET" ]]; then
    echo "Usage: pr-review <ticket> [target_branch]"
    exit 1
fi

# Find source branch
SOURCE=$(git branch -r | grep -i "$TICKET" | head -1 | sed 's|.*origin/||' | xargs)

if [[ -z "$SOURCE" ]]; then
    echo "No branch found for ticket $TICKET"
    exit 1
fi

echo "Reviewing $SOURCE → $TARGET"

# Run Python workflow
python3 << EOF
from pathlib import Path
from cc_orchestrations.core.runner import AgentRunner
from cc_orchestrations.workflows.pr_review import create_pr_review_workflow

runner = AgentRunner(claude_path='claude', default_model='opus')
ctx, handlers = create_pr_review_workflow(
    ticket_id='$TICKET',
    source_branch='$SOURCE',
    target_branch='$TARGET',
    work_dir=Path.cwd(),
    runner=runner,
)

for phase_name, handler in handlers.items():
    result = handler()
    if not result.success:
        print(f"Phase {phase_name} failed: {result.error}")
        exit(1)

print(f"\nReview complete! Report: pr_review_$TICKET.md")
EOF
```

## State Management

For long-running reviews, persist state between phases:

```python
from cc_orchestrations.core.state import StateManager
from cc_orchestrations.workflows.pr_review import create_pr_review_workflow

state_manager = StateManager(state_dir=Path('.spec'))

ctx, handlers = create_pr_review_workflow(...)

for phase_name, handler in handlers.items():
    # Load state
    state = state_manager.load()

    # Run phase
    result = handler()

    # Save state after each phase
    state.phase_completed = phase_name
    state_manager.save(state)

    if not result.success:
        # Can resume from last completed phase
        break
```

## Parallel Execution

The workflow supports parallel agent execution:

```python
# In phase_investigation, agents run in parallel by default
tasks = [
    (agent.name, formatted_prompt, context)
    for agent in agents_to_run
]

# runner.run_parallel() handles the parallelization
results = runner.run_parallel(tasks)
```

## Extension Hooks

Add custom logic at phase boundaries:

```python
def notify_start(ctx):
    """Send notification when review starts."""
    send_slack_message(f"Starting PR review for {ctx.ticket_id}")

def update_jira(ctx):
    """Update Jira with findings."""
    critical = [f for f in ctx.validated_findings if f['severity'] == 'critical']
    if critical:
        jira.add_comment(ctx.ticket_id, f"Found {len(critical)} critical issues")

config = create_default_config()
config.extension_hooks = {
    'pre_investigation': notify_start,
    'post_validation': update_jira,
}
```

## Monitoring and Metrics

Track PR review performance:

```python
import time

start_time = time.time()
phase_times = {}

for phase_name, handler in handlers.items():
    phase_start = time.time()
    result = handler()
    phase_times[phase_name] = time.time() - phase_start

total_time = time.time() - start_time

print(f"\nTiming:")
for phase, duration in phase_times.items():
    print(f"  {phase}: {duration:.1f}s")
print(f"Total: {total_time:.1f}s")

# Log to metrics system
metrics.record('pr_review_duration', total_time)
metrics.record('pr_review_findings', len(ctx.validated_findings))
```

## Testing

Test the workflow with mock runners:

```python
from unittest.mock import Mock
from cc_orchestrations.workflows.pr_review import create_pr_review_workflow

# Mock runner
mock_runner = Mock()
mock_runner.run.return_value = Mock(
    success=True,
    data={'diff_files': ['a.py', 'b.py'], 'risk_level': 'medium'}
)
mock_runner.run_parallel.return_value = []

# Create workflow with mock
ctx, handlers = create_pr_review_workflow(
    ticket_id='TEST-123',
    source_branch='test',
    target_branch='main',
    work_dir=Path('/tmp/test'),
    runner=mock_runner,
)

# Test phases
result = handlers['triage']()
assert result.success
```

## Best Practices

1. **Use project-specific configs**: Don't modify generic agents, extend them
2. **Persist state**: Save state after each phase for resumability
3. **Monitor performance**: Track phase timing and findings
4. **Parallel by default**: Leverage parallel agent execution
5. **Extension hooks**: Use hooks for integrations (Slack, Jira, etc.)
6. **Test thoroughly**: Unit test custom agents and triggers
